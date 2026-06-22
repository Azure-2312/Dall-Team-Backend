from flask import Blueprint, jsonify, request, send_from_directory
from datetime import datetime, date
from models import db, SilaboTimeline, Curso, Alumno, ApunteEstudiante, AlumnoDebilidad
from services.rag_service import RAGService
from services.koha_service import KohaService
from services.event_tracker import get_engagement_signals, get_recent_events
import os
from werkzeug.utils import secure_filename

timeline_bp = Blueprint('timeline', __name__)
rag_service = RAGService()
koha_service = KohaService()


# UNFV 2026-I Regular Cycle calendar limits
CYCLE_START = date(2026, 4, 6)
CYCLE_END = date(2026, 7, 25)

def get_current_academic_week(simulated_date_str=None) -> int:
    """
    Calculates the current academic week (1 to 16) based on Resolution R. N° 6119-2025-CU-UNFV.
    """
    if simulated_date_str:
        try:
            today_val = datetime.strptime(simulated_date_str, "%Y-%m-%d").date()
        except ValueError:
            today_val = date.today()
    else:
        # Get current date
        today_val = date.today()
        # Fallback safeguard: If today's year is not 2026, simulate June 19, 2026 (Week 11) for hackathon demo consistency
        if today_val.year != 2026:
            today_val = date(2026, 6, 19)
            
    if today_val < CYCLE_START:
        return 1
    elif today_val > CYCLE_END:
        return 16
        
    delta = today_val - CYCLE_START
    week_number = (delta.days // 7) + 1
    
    # Cap at 16 weeks
    return min(16, max(1, week_number))

@timeline_bp.route('/week', methods=['GET'])
def get_week_info():
    """Returns current date and calculated academic week."""
    week = get_current_academic_week()
    # Fallback date for frontend
    today_val = date.today()
    if today_val.year != 2026:
        today_val = date(2026, 6, 19)
    return jsonify({
        "fecha_actual": today_val.strftime("%Y-%m-%d"),
        "semana_actual": week,
        "ciclo": "2026-I",
        "dias_restantes": (CYCLE_END - today_val).days
    })

@timeline_bp.route('/focus-banner/<id_curso>', methods=['GET'])
def get_focus_banner(id_curso):
    """
    Renders daily focus topic banner corresponding to the current academic week.
    """
    week = get_current_academic_week()
    
    # Query theme for the course in that week
    timeline_entry = SilaboTimeline.query.filter_by(id_curso=id_curso, semana_numero=week).first()
    
    if not timeline_entry:
        return jsonify({
            "semana_numero": week,
            "tema": "Tema de estudio general y repaso",
            "lecturas": "Revisar lecturas complementarias de la biblioteca",
            "banner_texto": f"Esta semana (Semana {week}) concéntrate en tus apuntes generales y consultas al tutor."
        })
        
    banner_texto = (
        f"Esta semana tu profesor está dictando el tema \"{timeline_entry.tema_central}\" "
        f"de la unidad correspondiente a la Semana {week}. Concentra tus apuntes aquí hoy."
    )
    
    return jsonify({
        "semana_numero": week,
        "tema": timeline_entry.tema_central,
        "lecturas": timeline_entry.lecturas_obligatorias,
        "banner_texto": banner_texto
    })

@timeline_bp.route('/notes/upload', methods=['POST'])
def upload_class_notes():
    """
    Receives notes text (or uploaded document content) and indexes them into the timeline
    with RAG embeddings.
    """
    data = request.json
    if not data or not all(k in data for k in ('id_curso', 'semana_numero', 'texto_apuntes')):
        return jsonify({"error": "Faltan campos obligatorios: id_curso, semana_numero, texto_apuntes"}), 400
        
    id_curso = data['id_curso']
    semana = int(data['semana_numero'])
    texto = data['texto_apuntes']
    lecturas = data.get('lecturas_obligatorias', '')
    
    try:
        # Check course exists
        course = Curso.query.get(id_curso)
        if not course:
            return jsonify({"error": "Curso no encontrado"}), 404
            
        # Get embedding vector
        vector = rag_service.get_embedding(texto)
        
        # Check if timeline entry already exists for that week to update or create
        entry = SilaboTimeline.query.filter_by(id_curso=id_curso, semana_numero=semana).first()
        if entry:
            entry.tema_central = entry.tema_central + " | " + texto[:100] + "..." if len(entry.tema_central) < 150 else entry.tema_central
            entry.lecturas_obligatorias = (entry.lecturas_obligatorias or "") + "\n" + lecturas
            entry.contenido_vector = vector
        else:
            entry = SilaboTimeline(
                id_curso=id_curso,
                semana_numero=semana,
                tema_central=texto[:100] + "...",
                lecturas_obligatorias=lecturas,
                contenido_vector=vector
            )
            db.session.add(entry)
            
        db.session.commit()
        return jsonify({
            "message": "Apuntes vectorizados e indexados con éxito",
            "id_silabo": entry.id_silabo,
            "semana": semana
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@timeline_bp.route('/notes/search', methods=['GET'])
def search_notes():
    """
    Performs semantic search over the timeline class notes.
    Uses SQLAlchemy fallback loop if running on SQLite.
    """
    query = request.args.get('query')
    id_curso = request.args.get('id_curso')
    
    if not query or not id_curso:
        return jsonify({"error": "Faltan parámetros query y id_curso"}), 400
        
    query_vector = rag_service.get_embedding(query)
    
    # Query all notes for the course
    all_notes = SilaboTimeline.query.filter_by(id_curso=id_curso).all()
    
    scored_results = []
    for note in all_notes:
        if note.contenido_vector:
            sim = rag_service.cosine_similarity(query_vector, note.contenido_vector)
            scored_results.append({
                "semana_numero": note.semana_numero,
                "tema_central": note.tema_central,
                "lecturas_obligatorias": note.lecturas_obligatorias,
                "similitud": sim
            })
            
    # Sort by similarity desc
    scored_results.sort(key=lambda x: x["similitud"], reverse=True)
    
    return jsonify({
        "query": query,
        "resultados": scored_results[:3] # Return top 3 matches
    })


# --- NUEVOS ENDPOINTS: ESPACIO DE TRABAJO TRÍPTICO, APUNTES Y CHAT IA ---

def get_koha_branch_for_faculty(facultad_name: str) -> str:
    if not facultad_name:
        return ""
    fac_lower = facultad_name.lower()
    if "industrial" in fac_lower or "sistemas" in fac_lower or "fiis" in fac_lower:
        return "8248"
    elif "psicolog" in fac_lower or "faps" in fac_lower:
        return "8249"
    elif "econom" in fac_lower or "fce" in fac_lower:
        return "1209"
    elif "derecho" in fac_lower or "politica" in fac_lower or "fdcp" in fac_lower:
        return "10266"
    elif "humanidades" in fac_lower or "fh" in fac_lower:
        return "10267"
    elif "medicina" in fac_lower or "fmhu" in fac_lower:
        return "16285"
    elif "sociales" in fac_lower or "fccss" in fac_lower:
        return "10268"
    elif "educaci" in fac_lower or "fe" in fac_lower:
        return "10265"
    elif "administraci" in fac_lower or "fa" in fac_lower:
        return "8245"
    elif "arquitectura" in fac_lower or "fau" in fac_lower:
        return "3220"
    elif "financieras" in fac_lower or "contables" in fac_lower or "fcfc" in fac_lower:
        return "1210"
    elif "naturales" in fac_lower or "matematica" in fac_lower or "fcnm" in fac_lower:
        return "16276"
    elif "civil" in fac_lower or "fic" in fac_lower:
        return "7240"
    elif "oceanografia" in fac_lower or "pesqueria" in fac_lower or "alimentarias" in fac_lower or "fopca" in fac_lower:
        return "4225"
    elif "odontolog" in fac_lower or "fo" in fac_lower:
        return "13275"
    elif "tecnologia medica" in fac_lower or "ftm" in fac_lower:
        return "16270"
    elif "geografica" in fac_lower or "ambiental" in fac_lower or "figae" in fac_lower:
        return "8246"
    elif "electronica" in fac_lower or "informatica" in fac_lower or "fiei" in fac_lower:
        return "12247"
    return ""

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')

@timeline_bp.route('/course-timeline/<id_curso>', methods=['GET'])
def get_course_timeline(id_curso):
    try:
        course = Curso.query.get(id_curso)
        if not course:
            return jsonify({"error": "Curso no encontrado"}), 404
            
        existing = {s.semana_numero: s for s in SilaboTimeline.query.filter_by(id_curso=id_curso).all()}
        
        weeks = []
        for w in range(1, 17):
            if w in existing:
                weeks.append({
                    "semana_numero": w,
                    "tema_central": existing[w].tema_central,
                    "lecturas_obligatorias": existing[w].lecturas_obligatorias
                })
            else:
                weeks.append({
                    "semana_numero": w,
                    "tema_central": f"Semana {w}: Continuación y repaso de los temas de la asignatura",
                    "lecturas_obligatorias": "Revisar bibliografía principal en biblioteca"
                })
                
        return jsonify(weeks), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@timeline_bp.route('/notes/<id_alumno>/<id_curso>/<int:semana>', methods=['GET'])
def get_student_notes(id_alumno, id_curso, semana):
    try:
        apunte = ApunteEstudiante.query.filter_by(id_alumno=id_alumno, id_curso=id_curso, semana=semana).first()
        if not apunte:
            return jsonify({
                "texto_notas": "",
                "canvas_data": None,
                "background_url": None
            }), 200
            
        return jsonify({
            "texto_notas": apunte.texto_notas,
            "canvas_data": apunte.canvas_data,
            "background_url": apunte.background_url
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@timeline_bp.route('/notes/<id_alumno>/<id_curso>/<int:semana>', methods=['POST'])
def save_student_notes(id_alumno, id_curso, semana):
    data = request.json
    if not data:
        return jsonify({"error": "No se recibieron datos"}), 400
        
    texto_notas = data.get('texto_notas', '')
    canvas_data = data.get('canvas_data')
    background_url = data.get('background_url')
    
    try:
        apunte = ApunteEstudiante.query.filter_by(id_alumno=id_alumno, id_curso=id_curso, semana=semana).first()
        if apunte:
            apunte.texto_notas = texto_notas
            apunte.canvas_data = canvas_data
            apunte.background_url = background_url
        else:
            apunte = ApunteEstudiante(
                id_alumno=id_alumno,
                id_curso=id_curso,
                semana=semana,
                texto_notas=texto_notas,
                canvas_data=canvas_data,
                background_url=background_url
            )
            db.session.add(apunte)
            
        db.session.commit()
        return jsonify({
            "message": "Apuntes guardados con éxito",
            "semana": semana
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@timeline_bp.route('/notes/<id_alumno>/<id_curso>/sheets', methods=['GET'])
def list_student_sheets(id_alumno, id_curso):
    try:
        apuntes = ApunteEstudiante.query.filter_by(
            id_alumno=id_alumno, id_curso=id_curso, semana=None
        ).filter(ApunteEstudiante.nombre_hoja != None).all()
        sheets = [a.nombre_hoja for a in apuntes]
        return jsonify(sheets), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@timeline_bp.route('/notes/<id_alumno>/<id_curso>/sheet/<nombre_hoja>', methods=['GET'])
def get_student_sheet_notes(id_alumno, id_curso, nombre_hoja):
    try:
        apunte = ApunteEstudiante.query.filter_by(
            id_alumno=id_alumno, id_curso=id_curso, semana=None, nombre_hoja=nombre_hoja
        ).first()
        if not apunte:
            return jsonify({
                "texto_notas": "",
                "canvas_data": None,
                "background_url": None
            }), 200
        return jsonify({
            "texto_notas": apunte.texto_notas,
            "canvas_data": apunte.canvas_data,
            "background_url": apunte.background_url
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@timeline_bp.route('/notes/<id_alumno>/<id_curso>/sheet/<nombre_hoja>', methods=['POST'])
def save_student_sheet_notes(id_alumno, id_curso, nombre_hoja):
    data = request.json or {}
    texto_notas = data.get('texto_notas', '')
    canvas_data = data.get('canvas_data')
    background_url = data.get('background_url')
    try:
        apunte = ApunteEstudiante.query.filter_by(
            id_alumno=id_alumno, id_curso=id_curso, semana=None, nombre_hoja=nombre_hoja
        ).first()
        if apunte:
            apunte.texto_notas = texto_notas
            apunte.canvas_data = canvas_data
            apunte.background_url = background_url
        else:
            apunte = ApunteEstudiante(
                id_alumno=id_alumno,
                id_curso=id_curso,
                semana=None,
                nombre_hoja=nombre_hoja,
                texto_notas=texto_notas,
                canvas_data=canvas_data,
                background_url=background_url
            )
            db.session.add(apunte)
        db.session.commit()
        return jsonify({"message": "Apuntes de hoja guardados con éxito"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@timeline_bp.route('/notes/<id_alumno>/<id_curso>/sheet/<nombre_hoja>', methods=['DELETE'])
def delete_student_sheet(id_alumno, id_curso, nombre_hoja):
    try:
        apunte = ApunteEstudiante.query.filter_by(
            id_alumno=id_alumno, id_curso=id_curso, semana=None, nombre_hoja=nombre_hoja
        ).first()
        if not apunte:
            return jsonify({"error": "Hoja no encontrada"}), 404
        db.session.delete(apunte)
        db.session.commit()
        return jsonify({"message": "Hoja eliminada con éxito"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@timeline_bp.route('/notes/upload-bg', methods=['POST'])
def upload_notes_bg():
    if 'file' not in request.files:
        return jsonify({"error": "No se encontró ningún archivo"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Nombre de archivo vacío"}), 400
        
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ['.png', '.jpg', '.jpeg', '.gif', '.pdf']:
        return jsonify({"error": "Formato de archivo no permitido. Solo imágenes y PDFs."}), 400
        
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    filename = f"bg_{timestamp}{ext}"
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    
    if ext == '.pdf':
        try:
            import fitz
            doc = fitz.open(filepath)
            page_urls = []
            for i in range(len(doc)):
                page = doc.load_page(i)
                # Render page to high-quality image (150 DPI)
                pix = page.get_pixmap(dpi=150)
                page_filename = f"bg_{timestamp}_page_{i}.png"
                page_filepath = os.path.join(UPLOAD_FOLDER, page_filename)
                pix.save(page_filepath)
                page_urls.append(f"/api/timeline/uploads/{page_filename}")
            
            return jsonify({
                "filename": filename,
                "is_pdf": True,
                "pages": page_urls
            }), 200
        except Exception as e:
            return jsonify({"error": f"Error al procesar el PDF: {str(e)}"}), 500
    else:
        return jsonify({
            "filename": filename,
            "is_pdf": False,
            "url": f"/api/timeline/uploads/{filename}"
        }), 200

@timeline_bp.route('/uploads/<filename>', methods=['GET'])
def serve_notes_bg(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@timeline_bp.route('/chat', methods=['POST'])
def timeline_chat():
    data = request.json
    if not data or not all(k in data for k in ('id_alumno', 'id_curso', 'semana', 'mensaje')):
        return jsonify({"error": "Faltan parámetros obligatorios: id_alumno, id_curso, semana, mensaje"}), 400
        
    id_alumno = data['id_alumno']
    id_curso = data['id_curso']
    semana = int(data['semana'])
    mensaje = data['mensaje']
    historial = data.get('historial', [])
    nombre_hoja = data.get('nombre_hoja')
    
    alumno = Alumno.query.get(id_alumno)
    if not alumno:
        return jsonify({"error": "Estudiante no encontrado"}), 404
        
    curso = Curso.query.get(id_curso)
    if not curso:
        return jsonify({"error": "Curso no encontrado"}), 404
        
    silabo = SilaboTimeline.query.filter_by(id_curso=id_curso, semana_numero=semana).first()
    tema_central = silabo.tema_central if silabo else f"Tema de la semana {semana}"
    lecturas = silabo.lecturas_obligatorias if silabo else "Revisar sílabo de la asignatura"
    
    # 1. Fetch full syllabus context
    silabo_entries = SilaboTimeline.query.filter_by(id_curso=id_curso).order_by(SilaboTimeline.semana_numero).all()
    silabo_context = ""
    for s_entry in silabo_entries:
        silabo_context += f"- Semana {s_entry.semana_numero}: {s_entry.tema_central} (Lecturas: {s_entry.lecturas_obligatorias or ''})\n"
        
    # 2. Fetch all student notes and canvas data for this course (multi-week context)
    all_apuntes = ApunteEstudiante.query.filter_by(id_alumno=id_alumno, id_curso=id_curso).all()
    notes_context = ""
    all_canvas_texts = []
    all_canvas_images_paths = []
    
    for ap in all_apuntes:
        label = f"Semana {ap.semana}" if ap.semana else f"Hoja '{ap.nombre_hoja}'"
        if ap.texto_notas:
            notes_context += f"[{label}]: {ap.texto_notas}\n"
        if ap.canvas_data:
            try:
                import json
                state = json.loads(ap.canvas_data)
                if isinstance(state, dict):
                    texts_list = state.get('texts', [])
                    for t in texts_list:
                        if isinstance(t, dict) and t.get('text'):
                            all_canvas_texts.append(f"({label}) {t['text']}")
                    images_list = state.get('images', [])
                    for img in images_list:
                        if isinstance(img, dict) and img.get('url'):
                            filename = os.path.basename(img['url'])
                            filepath = os.path.join(UPLOAD_FOLDER, filename)
                            if os.path.exists(filepath):
                                all_canvas_images_paths.append(filepath)
            except Exception as e:
                print(f"Error parsing canvas_data for {label}: {e}")
        if ap.background_url:
            filename = os.path.basename(ap.background_url)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.exists(filepath) and filepath not in all_canvas_images_paths:
                all_canvas_images_paths.append(filepath)
                
    # Limit to the last 5 whiteboard/uploaded image files for Gemini context efficiency
    all_canvas_images_paths = all_canvas_images_paths[-5:]
    
    # 3. Fetch student weaknesses
    debilidades = AlumnoDebilidad.query.filter_by(id_alumno=id_alumno, id_curso=id_curso).all()
    debilidades_context = ""
    if debilidades:
        debilidades_context = "El estudiante ha tenido dificultades en los siguientes conceptos/evaluaciones:\n"
        for deb in debilidades:
            debilidades_context += f"- '{deb.tema_central}' (errores registrados: {deb.errores_count})\n"
            
    branch_code = get_koha_branch_for_faculty(alumno.facultad)
    
    # 4. Classify query: study-related vs. chit-chat / admin / welfare
    is_study_related = True
    gemini_key = os.environ.get('GEMINI_API_KEY')
    
    if gemini_key:
        try:
            from google import genai as _genai
            from google.genai import types as _gtypes
            _client = _genai.Client(api_key=gemini_key)
            classification_prompt = (
                f"Clasifica si el siguiente mensaje de un alumno es una consulta de contenido académico directo, es decir, sobre temas de estudio, "
                f"explicación de conceptos teóricos, resolución de ejercicios o dudas de la materia (responde 'ESTUDIO'), o si es un saludo, despedida, "
                f"charla informal, agradecimiento, pregunta administrativa o de ayuda sobre cómo funciona la plataforma (como cómo solicitar tutorías o cómo usar la pizarra) "
                f"(responde 'CHIT-CHAT').\n"
                f"Mensaje del alumno: \"{mensaje}\"\n"
                f"Responde únicamente con una de estas palabras en mayúsculas: 'ESTUDIO' o 'CHIT-CHAT'."
            )
            class_res = _client.models.generate_content(
                model='gemini-2.0-flash-lite',
                contents=classification_prompt
            )
            class_text = class_res.text.strip().upper()
            if 'CHIT-CHAT' in class_text:
                is_study_related = False
        except Exception as classification_ex:
            print(f"Error in study classification: {classification_ex}")
            greetings = ['hola', 'buenos dias', 'buenas tardes', 'buenas noches', 'saludos', 'hi', 'hello', 'chau', 'adios', 'gracias', 'gracias ia']
            msg_lower = mensaje.lower().strip()
            if any(msg_lower.startswith(g) or msg_lower == g for g in greetings):
                is_study_related = False
    else:
        greetings = ['hola', 'buenos dias', 'buenas tardes', 'buenas noches', 'saludos', 'hi', 'hello', 'chau', 'adios', 'gracias', 'gracias ia']
        msg_lower = mensaje.lower().strip()
        if any(msg_lower.startswith(g) or msg_lower == g for g in greetings):
            is_study_related = False

    # 5. Load recommended books if study related
    libros_recomendados = []
    if is_study_related:
        try:
            clean_theme = tema_central.split('|')[0].split('.')[0].strip()
            words = clean_theme.split()
            search_query = " ".join(words[:3]) if len(words) > 3 else clean_theme
            
            books_res = koha_service.search_books(query=search_query, sede=branch_code)
            koha_results = books_res.get("resultados", [])
            
            if not koha_results:
                books_res = koha_service.search_books(query=curso.nombre_curso, sede=branch_code)
                koha_results = books_res.get("resultados", [])
                
            libros_recomendados = koha_results[:3]
        except Exception as e:
            print(f"Koha Search Error: {e}")
            
    options = []
    gemini_success = False
    respuesta_texto = ""
    
    if gemini_key:
        try:
            from google import genai as _genai
            from google.genai import types as _gtypes
            _client = _genai.Client(api_key=gemini_key)
            signals = get_engagement_signals(id_alumno)
            recent_events = get_recent_events(id_alumno, limit=5)
            
            signals_str = (
                f"- Tutorías canceladas este mes: {signals['tutorias_canceladas_ultimo_mes']}\n"
                f"- Días sin interactuar con la pizarra: {signals['dias_sin_abrir_pizarra']}\n"
                f"- Racha de días activos en la semana: {signals['racha_dias_activos']}/7\n"
                f"- Último libro buscado: {signals['ultima_busqueda_libro'] or 'Ninguno'}\n"
            )
            
            events_str = ""
            for ev in recent_events:
                events_str += f"- Acción '{ev['tipo_evento']}' realizada el {ev['fecha_evento']}\n"
            if not events_str:
                events_str = "- Sin actividad reciente registrada.\n"

            context_prompt = (
                f"Eres el Tutor de Inteligencia Artificial (Gemini) de la Universidad Nacional Federico Villarreal (UNFV).\n"
                f"Estás ayudando al estudiante {alumno.nombre} en el curso '{curso.nombre_curso}' (Escuela: {alumno.escuela}).\n"
                f"El alumno se encuentra actualmente revisando la **Semana {semana}** del curso.\n"
            )
            
            # Syllabus context
            context_prompt += f"\n[SÍLABO COMPLETO DEL CURSO]:\n{silabo_context}\n"
            
            # Student notes across all weeks
            if notes_context:
                context_prompt += f"\n[APUNTES ESCRITOS POR EL ALUMNO (OTRAS SEMANAS/HOJAS)]:\n{notes_context}\n"
                
            # Canvas texts
            if all_canvas_texts:
                context_prompt += "\n[TEXTOS EN LAS PIZARRAS/LIENZOS DEL ALUMNO]:\n"
                for t in all_canvas_texts:
                    context_prompt += f"- {t}\n"
                    
            # Weaknesses context
            if debilidades_context:
                context_prompt += f"\n{debilidades_context}\n"
                
            # Behavioral signals context
            context_prompt += (
                f"\n[SEÑALES DE COMPORTAMIENTO Y ENGAGEMENT DEL ESTUDIANTE]:\n"
                f"{signals_str}\n"
                f"[HISTORIAL RECIENTE DE ACCIONES]:\n"
                f"{events_str}\n"
            )

            if all_canvas_images_paths:
                context_prompt += f"\nEl alumno ha subido {len(all_canvas_images_paths)} imágenes/archivos a sus pizarras (que se adjuntan a este mensaje).\n"
                
            if is_study_related and libros_recomendados:
                context_prompt += "\nPara el tema actual y facultad, contamos con los siguientes libros físicos en la biblioteca:\n"
                for lib in libros_recomendados:
                    context_prompt += f"- '{lib['titulo']}' de {lib['autor']} (Signatura: {lib['signatura']}, Publicación: {lib['publicacion']})\n"
                    
            platform_guide = (
                "\n[GUÍA DE FUNCIONALIDADES DE LA PLATAFORMA DE ESTUDIOS UNFV]:\n"
                "Para responder de manera precisa y evitar alucinaciones, ten en cuenta cómo funciona cada sección de la plataforma:\n"
                "1. MIS CURSOS (Espacio de Trabajo Tríptico):\n"
                "   - Barra del Sílabo por semanas (1 a 16): Muestra el tema central y lecturas sugeridas de la semana.\n"
                "   - Hojas de apuntes (Notebook Sheets): El estudiante puede crear nuevas hojas, darles el nombre que desee y eliminarlas.\n"
                "   - Pizarra Digital Vectorial (Whiteboard): Soporta dibujos transparentes (lápiz, resaltador), inserción de texto, arrastre/redimensión de imágenes, subida de fondos de imagen o páginas de PDF en vertical, y botones de Retroceder (Undo) y Avanzar (Redo) del historial (hasta 50 trazos).\n"
                "   - Editor de texto: Ubicado debajo de la pizarra para que redacte y guarde apuntes persistentes.\n"
                "2. AUTOEVALUACIÓN (Quizzes adaptativos):\n"
                "   - Genera cuestionarios interactivos dinámicos de los temas del sílabo cargados hasta la semana anterior a la actual.\n"
                "   - Prioriza de forma adaptativa los conceptos en los que el estudiante haya tenido errores en quizzes pasados.\n"
                "   - Si se equivoca, la plataforma registra el concepto en su lista de 'Debilidades Activas' para priorizarlo en futuros exámenes.\n"
                "3. BIBLIOTECA KOHA (Buscador físico):\n"
                "   - Permite buscar libros físicos de su facultad en las diferentes bibliotecas (sedes) de la UNFV.\n"
                "   - Retorna títulos, autores y su signatura o clasificación topográfica (código de ubicación) para que el alumno pueda retirarlo físicamente de la sede.\n"
                "4. TUTORÍAS (Proceso de Solicitud OTPS):\n"
                "   - El estudiante NO agenda de forma directa seleccionando fecha/hora libres ni con un calendario interactivo propio.\n"
                "   - Para solicitar una tutoría grupal, el alumno debe seleccionar el curso, ingresar la cantidad de alumnos participantes, y subir obligatoriamente un archivo Word (.doc/.docx) con las firmas y la solicitud firmada.\n"
                "   - Debe aceptar los términos regulatorios de conducta y sanciones antes de enviar.\n"
                "   - Una vez enviada, la solicitud pasa a estado 'Pendiente' esperando revisión del administrador OTPS.\n"
                "   - Si el administrador la aprueba, se le asigna un docente tutor, un horario (día y hora), escuela/pabellón y un enlace de videollamada para reunirse.\n"
                "   - El alumno también puede unirse a tutorías grupales de su facultad creadas por otros compañeros en la sección 'Tutorías de la Facultad'.\n"
                "   - Para completarla, el alumno puede marcar la tutoría como completada 2 horas después de la hora de inicio.\n"
                "5. SOPORTE OBU (Bienestar Universitario):\n"
                "   - Permite al estudiante realizar consultas de orientación de bienestar, salud mental o derivación institucional.\n"
                "6. MI PERFIL:\n"
                "   - Permite cambiar la contraseña o subir una foto de perfil.\n"
            )

            general_instructions = (
                "\nREGLAS DE TONO ADICIONALES (BASADAS EN EL COMPORTAMIENTO RECIENTE):\n"
                "- Usa el contexto de comportamiento del estudiante únicamente para adaptar tu tono de forma sutil, cálida y empática. ¡NUNCA menciones que tienes acceso a estos datos de tracking de manera explícita o robótica (evita decir 'veo en tus datos que cancelaste', 'llevas Z días inactivo' o 'buscaste X libro').\n"
                "- Si detectas baja actividad o cancelaciones repetidas, anímalo a retomar con una sola pregunta breve y motivadora, sin sermones ni reproches. Suena como un tutor humano que se preocupa genuinamente.\n"
                "- Si detectas alta actividad, refuerza positivamente su esfuerzo.\n"
            )

            format_instructions = (
                "\n\n[FORMATO DE RESPUESTA OBLIGATORIO]:\n"
                "Responde ÚNICAMENTE con un objeto JSON válido con exactamente dos campos:\n"
                "1. 'respuesta': Tu mensaje en formato Markdown. Debe ser la respuesta completa que el alumno verá.\n"
                "2. 'opciones': Una lista de 2 a 3 opciones de respuesta MUY CORTAS (máximo 5 palabras cada una) para que el alumno haga clic. "
                "Si no aplica opciones interactivas (ej: respuesta es terminal, o la consulta es informal/saludo/despedida/agradecimiento/administrativa), usa una lista vacía [].\n"
                "Ejemplo de formato: {\"respuesta\": \"Texto en **Markdown**...\", \"opciones\": [\"Opción A\", \"Opción B\"]}\n"
                "NO incluyas ningún texto fuera del objeto JSON."
            )

            if is_study_related:
                context_prompt += (
                    "\nINSTRUCCIONES DE COMPORTAMIENTO:\n"
                    "1. MÉTODO SOCRÁTICO INTERACTIVO: NO des la explicación completa de inmediato. Primero haz UNA pregunta abierta y corta para explorar el conocimiento previo del alumno sobre el concepto. Ofrece 2-3 opciones de respuesta en el campo 'opciones' para que pueda responder haciendo clic.\n"
                    "2. Solo después de que el alumno responda (o si pide la explicación directa), desglosa el tema con: una definición formal del concepto, una analogía cotidiana y un ejemplo práctico.\n"
                    "3. Si el alumno se equivoca o pregunta cómo resolver un ejercicio, desglosa el problema en pasos pequeños y hazle preguntas guía para que descubra su error o el camino correcto. Siempre ofrece opciones interactivas en el campo 'opciones'.\n"
                    "4. Si el estudiante tiene debilidades o errores registrados (indicados en la sección de dificultades arriba), adapta tu estilo de enseñanza para reforzar activamente esos puntos y verificar su comprensión con preguntas y opciones.\n"
                    "5. Si el estudiante muestra dificultades persistentes o bajo rendimiento, recomiéndale amablemente que solicite una tutoría presencial o virtual con un docente tutor en la sección 'Tutorías' de su panel izquierdo, explicando claramente que debe subir su solicitud firmada en formato Word.\n"
                    "6. REGLA DE RECOMENDACIÓN DE LIBROS: Recomienda de forma natural alguno de los libros físicos de la biblioteca UNFV listados anteriormente, indicando su Signatura topográfica, ÚNICAMENTE cuando el alumno realice consultas directas sobre conceptos teóricos o temas académicos del curso. Si el alumno hace preguntas administrativas, de saludo, o sobre cómo funciona la plataforma (como solicitar tutorías), NUNCA recomiendes libros de la biblioteca.\n"
                    "7. Escribe el texto de la respuesta ('respuesta') en formato Markdown claro."
                    + platform_guide
                    + general_instructions
                    + format_instructions
                )
            else:
                context_prompt += (
                    "\nINSTRUCCIONES DE COMPORTAMIENTO:\n"
                    "1. Responde de manera sumamente corta, concisa y cordial a este saludo, despedida, agradecimiento o charla casual (máximo 2 o 3 líneas).\n"
                    "2. NO incluyas explicaciones académicas largas ni recomendaciones de libros en esta respuesta.\n"
                    "3. Si el estudiante muestra estrés, frustración, o pregunta por trámites administrativos o apoyo psicológico/personal, demuéstrale empatía y oriéntalo claramente a las dependencias de la UNFV correspondientes:\n"
                    "   - Apoyo Psicológico: Consultorio Psicológico de la Facultad de Psicología o la Oficina de Bienestar Universitario.\n"
                    "   - Homologaciones/Trámites: Oficina de Registro Académico (ORA) o la Secretaría Académica de su facultad.\n"
                    "   - Tutorías Académicas presenciales: Departamento de Tutoría de su Facultad.\n"
                    "4. Escribe el texto de la respuesta ('respuesta') en formato Markdown claro. Para respuestas informales, usa 'opciones': [] (lista vacía)."
                    + platform_guide
                    + general_instructions
                    + format_instructions
                )
                
            # Build contents list for the new SDK
            import json as _json, mimetypes as _mimetypes
            from google.genai import types as _gtypes
            
            contents = []
            # System context as first user message
            first_parts = [_gtypes.Part(text=context_prompt)]
            for img_path in all_canvas_images_paths:
                try:
                    mime_type, _ = _mimetypes.guess_type(img_path)
                    if not mime_type:
                        mime_type = 'image/png'
                    with open(img_path, 'rb') as f:
                        img_data = f.read()
                    if len(img_data) < 15 * 1024 * 1024:
                        first_parts.append(_gtypes.Part(
                            inline_data=_gtypes.Blob(mime_type=mime_type, data=img_data)
                        ))
                except Exception as img_err:
                    print(f"Error loading image {img_path} for Gemini: {img_err}")
            
            contents.append(_gtypes.Content(role='user', parts=first_parts))
            # Add model acknowledgment so conversation history builds correctly
            contents.append(_gtypes.Content(role='model', parts=[_gtypes.Part(text='{"respuesta": "Entendido. Estoy listo para ayudarte.", "opciones": []}')])) 
            
            # Add conversation history
            for h in historial:
                role = 'user' if h['sender'] == 'user' else 'model'
                contents.append(_gtypes.Content(role=role, parts=[_gtypes.Part(text=h['text'])]))
            
            # Add current user message
            contents.append(_gtypes.Content(role='user', parts=[_gtypes.Part(text=mensaje)]))
            
            response = _client.models.generate_content(
                model='gemini-2.0-flash-lite',
                contents=contents,
                config=_gtypes.GenerateContentConfig(
                    response_mime_type='application/json'
                )
            )
            raw_text = response.text.strip()
            try:
                parsed = _json.loads(raw_text)
                respuesta_texto = parsed.get("respuesta") or parsed.get("message") or ""
                options = parsed.get("opciones") or parsed.get("options") or []
                if not isinstance(options, list):
                    options = []
                if not respuesta_texto:
                    respuesta_texto = raw_text
            except Exception:
                respuesta_texto = raw_text
                options = []
            gemini_success = True
            
        except Exception as ex:
            print(f"Gemini timeline chat error: {ex}")
            
    if not gemini_success:
        if is_study_related:
            respuesta_texto = (
                f"¡Hola {alumno.nombre}! Soy tu Tutor IA UNFV (modo local).\n\n"
                f"Actualmente estás estudiando la **Semana {semana}** del curso **{curso.nombre_curso}**.\n\n"
                "He revisado el sílabo y tus notas de las semanas anteriores. Para ayudarte a comprender el tema actual, "
                "te sugiero repasar tus apuntes en la pizarra y resolver el cuestionario de autoevaluación. "
                "Si encuentras temas difíciles, recuerda que puedes solicitar una sesión de tutoría con tu docente en la sección 'Tutorías'.\n\n"
            )
            if libros_recomendados:
                respuesta_texto += "### Bibliografía Recomendada en tu Biblioteca:\n"
                for lib in libros_recomendados:
                    respuesta_texto += f"- 📖 **{lib['titulo']}** - *{lib['autor']}* (Clasificación/Signatura: `{lib['signatura']}`).\n"
                respuesta_texto += "\n*Nota: Esta respuesta fue generada por el modo local alternativo debido a la desconexión temporal del servicio de IA.*"
        else:
            respuesta_texto = (
                f"¡Hola {alumno.nombre}! Soy tu Tutor IA UNFV (modo local).\n\n"
                "¿En qué puedo ayudarte hoy? Si tienes alguna duda sobre el curso o necesitas orientación sobre trámites o bienestar, cuéntame."
            )
            
    return jsonify({
        "respuesta": respuesta_texto,
        "libros_recomendados": libros_recomendados,
        "options": options
    }), 200

