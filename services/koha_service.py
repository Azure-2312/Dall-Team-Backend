import re
import time
import urllib.parse
import requests
from bs4 import BeautifulSoup
from config.sedes_koha import SEDES_KOHA

class KohaService:
    def __init__(self):
        # Cache stores search queries with format: {cache_key: (timestamp, results_list)}
        self._cache = {}
        self._cache_ttl = 180  # 3 minutes cache lifetime
        self.base_url = "https://biblioteca.unfv.edu.pe"
        self.search_url = f"{self.base_url}/cgi-bin/koha/opac-search.pl"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        }

    def search_books(self, query: str, sede: str = None) -> dict:
        """
        Queries the real UNFV Koha catalog using BeautifulSoup to scrape and parse the search results.
        Returns a dictionary: { "resultados": list, "total": int }
        Uses an in-memory cache with a TTL of 3 minutes.
        """
        if not query:
            return {"resultados": [], "total": 0}

        query_cleaned = query.strip()
        query_lower = query_cleaned.lower()
        
        # Include sede filter in the cache key to partition search space
        cache_key = f"{query_lower}||{sede or ''}"

        # Check in-memory cache
        now = time.time()
        if cache_key in self._cache:
            cache_ts, cached_data = self._cache[cache_key]
            if now - cache_ts < self._cache_ttl:
                return cached_data

        # Build search URL with standard percent encoding (%20 for spaces)
        query_encoded = urllib.parse.quote(query_cleaned)
        target_url = f"{self.search_url}?q={query_encoded}"
        
        # If physical branch filter is provided, append limit parameter
        if sede:
            target_url += f"&limit=branch:{sede}"

        try:
            # Perform GET request with 10s timeout
            response = requests.get(target_url, headers=self.headers, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            # Re-raise to let the blueprint catch it and return 502
            raise RuntimeError(f"Error connecting to UNFV library catalog: {str(e)}") from e

        soup = BeautifulSoup(response.content, 'html.parser')
        rows = soup.select('table.table-striped tr')
        results = []

        for row in rows:
            # Filter rows: must contain the details column
            if not row.select_one('td.bibliocol'):
                continue

            # 1. Extract Biblionumber ID
            bib_input = row.find('input', {'name': 'biblionumber'})
            bib_id = bib_input['value'] if bib_input else None
            
            if not bib_id:
                # Fallback to bookcover div
                cover_div = row.find(class_='bookcover')
                if cover_div and cover_div.has_attr('data-biblionumber'):
                    bib_id = cover_div['data-biblionumber']

            # 2. Extract Title and Clean Responsibility Statement
            title_elem = row.select_one('a.title')
            title = ""
            if title_elem:
                # Remove responsibility statements and medium descriptors (e.g. "[Texto impreso]")
                resp_stmt = title_elem.select_one('span.title_resp_stmt')
                if resp_stmt:
                    resp_stmt.extract()
                medium_stmt = title_elem.select_one('span.title_medium')
                if medium_stmt:
                    medium_stmt.extract()
                title = title_elem.get_text(strip=True).strip(' /').strip()

            # 3. Extract Author Names
            authors = []
            author_ul = row.select_one('ul.author')
            if author_ul:
                for li in author_ul.find_all('li'):
                    a_tag = li.find('a')
                    if a_tag:
                        dates = a_tag.select_one('span.authordates')
                        if dates:
                            dates.extract()
                        relator = a_tag.select_one('span.relatorcode')
                        if relator:
                            relator.extract()
                        name = a_tag.get_text(strip=True).rstrip(',').strip()
                        if name:
                            authors.append(name)
            if not authors:
                cover_div = row.find(class_='bookcover')
                if cover_div and cover_div.has_attr('data-author'):
                    authors = [cover_div['data-author'].strip()]

            # 4. Extract Edition
            edition = ""
            edition_elem = row.select_one('.results_summary.edition')
            if edition_elem:
                label = edition_elem.select_one('span.label')
                if label:
                    label.extract()
                edition = edition_elem.get_text(strip=True)

            # 5. Extract Publisher and Publication Details
            publisher = ""
            pub_elem = row.select_one('.results_summary.publisher, .results_summary.rda264')
            if pub_elem:
                label = pub_elem.select_one('span.label')
                if label:
                    label.extract()
                publisher = pub_elem.get_text(separator=' ', strip=True)

            # 6. Extract Book Cover URL prioritizing: Local -> Amazon -> Google
            cover_url = None
            local_div = row.select_one('.cover-image.local-coverimg')
            if local_div:
                img = local_div.find('img')
                if img and img.has_attr('src'):
                    src = img['src']
                    cover_url = f"{self.base_url}{src}" if src.startswith('/') else src

            if not cover_url:
                amazon_div = row.select_one('.cover-image.amazon-coverimg')
                if amazon_div:
                    img = amazon_div.find('img')
                    if img and img.has_attr('src'):
                        cover_url = img['src']

            if not cover_url:
                google_div = row.select_one('.cover-image.googlejacket-coverimg')
                if google_div:
                    img = google_div.find('img')
                    if img and img.has_attr('src'):
                        cover_url = img['src']

            # 7. Parse Availability Details per Branch (Sede)
            sedes = []
            avail_elem = row.select_one('.results_summary.availability')
            if avail_elem:
                noitems = avail_elem.select_one('.noitems')
                if not noitems:
                    for item in avail_elem.select('.ItemSummary'):
                        branch_elem = item.select_one('.ItemBranch')
                        branch_name = branch_elem.get_text(strip=True) if branch_elem else "Biblioteca Central"
                        
                        # Parse copies count in trailing text
                        copies_count = 1
                        if branch_elem:
                            curr = branch_elem.next_sibling
                            while curr:
                                if isinstance(curr, str):
                                    m = re.search(r'\((\d+)\)', curr)
                                    if m:
                                        copies_count = int(m.group(1))
                                        break
                                curr = curr.next_sibling
                                
                        call_elem = item.select_one('.CallNumber')
                        call_number = call_elem.get_text(strip=True) if call_elem else "N/A"
                        
                        sedes.append({
                            "sede": branch_name,
                            "copias": copies_count,
                            "signatura": call_number
                        })

            # Derive primary signature and availability status for compatibility
            primary_sig = sedes[0]["signatura"] if sedes else "Sin Signatura"
            
            results.append({
                "id": bib_id,
                "titulo": title or "Título no especificado",
                "autor": ", ".join(authors) if authors else "Autor no especificado",
                "autores": authors,
                "edicion": edition,
                "publicacion": publisher,
                "portada": cover_url,
                "sedes": sedes,
                "disponible": len(sedes) > 0,
                "signatura": primary_sig
            })

        output_data = {
            "resultados": results,
            "total": len(results)
        }

        # Cache results
        self._cache[query_lower] = (now, output_data)
        return output_data

