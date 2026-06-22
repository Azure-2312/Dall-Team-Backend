import re
import time
import urllib.parse
import requests
from bs4 import BeautifulSoup
from config.sedes_koha import SEDES_KOHA

MOCK_BOOKS = [
    {
        "id": "mock_01",
        "titulo": "Cálculo Infinitesimal y Geometría Analítica",
        "autor": "George B. Thomas",
        "edicion": "12ª edición",
        "publicacion": "Pearson Educación, 2010",
        "portada": "https://images.unsplash.com/photo-1543002588-bfa74002ed7e?auto=format&fit=crop&q=80&w=200",
        "sedes": [
            {"sede": "Biblioteca Central", "copias": 3, "signatura": "515.15 T45 2010"},
            {"sede": "Facultad de Ingeniería Industrial y de Sistemas", "copias": 2, "signatura": "515.15 T45 2010"}
        ],
        "disponible": True,
        "signatura": "515.15 T45 2010"
    },
    {
        "id": "mock_02",
        "titulo": "Cálculo: Trascendentes Tempranas",
        "autor": "James Stewart",
        "edicion": "7ª edición",
        "publicacion": "Cengage Learning, 2012",
        "portada": "https://images.unsplash.com/photo-1509062522246-3755977927d7?auto=format&fit=crop&q=80&w=200",
        "sedes": [
            {"sede": "Biblioteca Central", "copias": 5, "signatura": "515.15 S81 2012"},
            {"sede": "Facultad de Ingeniería Industrial y de Sistemas", "copias": 4, "signatura": "515.15 S81 2012"}
        ],
        "disponible": True,
        "signatura": "515.15 S81 2012"
    },
    {
        "id": "mock_03",
        "titulo": "Química General",
        "autor": "Raymond Chang, Kenneth A. Goldsby",
        "edicion": "11ª edición",
        "publicacion": "McGraw-Hill, 2013",
        "portada": "https://images.unsplash.com/photo-1532187643603-ba119ca4109e?auto=format&fit=crop&q=80&w=200",
        "sedes": [
            {"sede": "Biblioteca Central", "copias": 4, "signatura": "540 C45 2013"},
            {"sede": "Facultad de Ingeniería de Transportes", "copias": 2, "signatura": "540 C45 2013"}
        ],
        "disponible": True,
        "signatura": "540 C45 2013"
    },
    {
        "id": "mock_04",
        "titulo": "Química Orgánica",
        "autor": "L. G. Wade Jr.",
        "edicion": "7ª edición",
        "publicacion": "Pearson Educación, 2011",
        "portada": "https://images.unsplash.com/photo-1532187863486-abf9d39d66e8?auto=format&fit=crop&q=80&w=200",
        "sedes": [
            {"sede": "Biblioteca Central", "copias": 2, "signatura": "547 W12 2011"}
        ],
        "disponible": True,
        "signatura": "547 W12 2011"
    },
    {
        "id": "mock_05",
        "titulo": "Física para Ciencias e Ingeniería - Vol. 1",
        "autor": "Raymond A. Serway, John W. Jewett",
        "edicion": "9ª edición",
        "publicacion": "Cengage Learning, 2015",
        "portada": "https://images.unsplash.com/photo-1507668077129-56e32842fceb?auto=format&fit=crop&q=80&w=200",
        "sedes": [
            {"sede": "Biblioteca Central", "copias": 6, "signatura": "530 S42 2015"},
            {"sede": "Facultad de Ingeniería de Transportes", "copias": 3, "signatura": "530 S42 2015"}
        ],
        "disponible": True,
        "signatura": "530 S42 2015"
    },
    {
        "id": "mock_06",
        "titulo": "Introducción a los Sistemas de Bases de Datos",
        "autor": "C. J. Date",
        "edicion": "8ª edición",
        "publicacion": "Pearson Educación, 2004",
        "portada": "https://images.unsplash.com/photo-1544383835-bda2bc66a55d?auto=format&fit=crop&q=80&w=200",
        "sedes": [
            {"sede": "Facultad de Ingeniería Industrial y de Sistemas", "copias": 3, "signatura": "005.74 D23 2004"}
        ],
        "disponible": True,
        "signatura": "005.74 D23 2004"
    },
    {
        "id": "mock_07",
        "titulo": "Cómo Programar en C++",
        "autor": "Harvey M. Deitel, Paul J. Deitel",
        "edicion": "6ª edición",
        "publicacion": "Pearson Educación, 2008",
        "portada": "https://images.unsplash.com/photo-1515879218367-8466d910aaa4?auto=format&fit=crop&q=80&w=200",
        "sedes": [
            {"sede": "Facultad de Ingeniería Industrial y de Sistemas", "copias": 4, "signatura": "005.133 D32 2008"}
        ],
        "disponible": True,
        "signatura": "005.133 D32 2008"
    },
    {
        "id": "mock_08",
        "titulo": "Administración",
        "autor": "Stephen P. Robbins, Mary Coulter",
        "edicion": "12ª edición",
        "publicacion": "Pearson Educación, 2014",
        "portada": "https://images.unsplash.com/photo-1434030216411-0b793f4b4173?auto=format&fit=crop&q=80&w=200",
        "sedes": [
            {"sede": "Biblioteca Central", "copias": 3, "signatura": "658 R69 2014"},
            {"sede": "Facultad de Ingeniería Industrial y de Sistemas", "copias": 2, "signatura": "658 R69 2014"}
        ],
        "disponible": True,
        "signatura": "658 R69 2014"
    },
    {
        "id": "mock_09",
        "titulo": "Contabilidad de Costos: Un enfoque gerencial",
        "autor": "Charles T. Horngren, Srikant M. Datar",
        "edicion": "14ª edición",
        "publicacion": "Pearson Educación, 2012",
        "portada": "https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?auto=format&fit=crop&q=80&w=200",
        "sedes": [
            {"sede": "Biblioteca Central", "copias": 4, "signatura": "657.42 H78 2012"},
            {"sede": "Facultad de Ingeniería Industrial y de Sistemas", "copias": 2, "signatura": "657.42 H78 2012"}
        ],
        "disponible": True,
        "signatura": "657.42 H78 2012"
    },
    {
        "id": "mock_10",
        "titulo": "Geopolítica y Realidad Nacional",
        "autor": "Julio R. Córdova",
        "edicion": "1ª edición",
        "publicacion": "Editorial Universitaria UNFV, 2018",
        "portada": "https://images.unsplash.com/photo-1524661135-423995f22d0b?auto=format&fit=crop&q=80&w=200",
        "sedes": [
            {"sede": "Biblioteca Central", "copias": 5, "signatura": "320.12 C78 2018"}
        ],
        "disponible": True,
        "signatura": "320.12 C78 2018"
    }
]

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
        If any connection or parsing exception occurs, it falls back to a mock books catalog.
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

        try:
            # Build search URL with standard percent encoding (%20 for spaces)
            query_encoded = urllib.parse.quote(query_cleaned)
            target_url = f"{self.search_url}?q={query_encoded}"
            
            # If physical branch filter is provided, append limit parameter
            if sede:
                target_url += f"&limit=branch:{sede}"

            # Disable urllib3 insecure request warnings to clean up backend logs
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            # Perform GET request with 10s timeout, bypassing SSL verification
            response = requests.get(target_url, headers=self.headers, timeout=10, verify=False)
            response.raise_for_status()

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
            self._cache[cache_key] = (now, output_data)
            return output_data

        except Exception as e:
            import traceback
            print(f"--- KOHA REAL QUERY FAILED (falling back to MOCK_BOOKS) ---")
            traceback.print_exc()
            
            # Fallback local search over MOCK_BOOKS
            import unicodedata
            def clean_text(text):
                if not text:
                    return ""
                return "".join(c for c in unicodedata.normalize('NFD', text.lower()) if unicodedata.category(c) != 'Mn')

            q_clean = clean_text(query_cleaned)
            filtered_results = []
            
            for book in MOCK_BOOKS:
                # Text matching
                titulo_clean = clean_text(book.get("titulo", ""))
                autor_clean = clean_text(book.get("autor", ""))
                
                if q_clean in titulo_clean or q_clean in autor_clean:
                    # Sede filter
                    if sede:
                        sede_name = SEDES_KOHA.get(sede, "").lower()
                        # Check if matches any sede
                        match_sede = False
                        for s_info in book.get("sedes", []):
                            s_name = s_info.get("sede", "").lower()
                            if sede_name in s_name or s_name in sede_name:
                                match_sede = True
                                break
                        if not match_sede:
                            continue
                    filtered_results.append(book)

            fallback_data = {
                "resultados": filtered_results,
                "total": len(filtered_results)
            }
            # Cache the fallback results for fast response
            self._cache[cache_key] = (now, fallback_data)
            return fallback_data

