from flask import Blueprint, jsonify, request, send_from_directory
from models import db, Docente, Alumno, Curso, CitaTutoria, AlumnoDebilidad, SolicitudTutoria, AlumnoUnidoTutoria, ReporteTutoria
from services.koha_service import KohaService
from services.notification_service import NotificationService
from services.rag_service import RAGService
from datetime import datetime
import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

resources_bp = Blueprint('resources', __name__)
koha_service = KohaService()
notification_service = NotificationService()
rag_service = RAGService()

@resources_bp.route('/koha/search', methods=['GET'])
def search_koha_books():
    """Queries Koha library catalog in real-time."""
    query = request.args.get('query', '')
    sede = request.args.get('sede', '')
    try:
        books_data = koha_service.search_books(query, sede=sede if sede else None)
        return jsonify(books_data)
    except Exception as e:
        import traceback
        print("ERROR IN KOHA SEARCH ENDPOINT:")
        traceback.print_exc()
        
        # Super-fallback to mock books if anything goes completely wrong
        from services.koha_service import MOCK_BOOKS
        from config.sedes_koha import SEDES_KOHA
        import unicodedata
        
        def clean_text(text):
            if not text:
                return ""
            return "".join(c for c in unicodedata.normalize('NFD', text.lower()) if unicodedata.category(c) != 'Mn')
            
        q_clean = clean_text(query)
        filtered = []
        for book in MOCK_BOOKS:
            # If query is empty or matches title/author
            if not q_clean or q_clean in clean_text(book.get("titulo", "")) or q_clean in clean_text(book.get("autor", "")):
                if sede:
                    sede_name = SEDES_KOHA.get(sede, "").lower()
                    match_sede = False
                    for s_info in book.get("sedes", []):
                        s_name = s_info.get("sede", "").lower()
                        if sede_name in s_name or s_name in sede_name:
                            match_sede = True
                            break
                    if not match_sede:
                        continue
                filtered.append(book)
                
        return jsonify({
            "resultados": filtered,
            "total": len(filtered),
            "fallback": True
        }), 200

@resources_bp.route('/tutors/<id_curso>', methods=['GET'])
def get_tutors_by_course(id_curso):
    """
    Fetches teachers and their tutoring slots for a specific course.
    """
    docentes = Docente.query.all()
    results = []
    
    for d in docentes:
        # Check if docente has blocks configured
        slots = d.bloques_disponibles or []
        
        # Filter slots that match the id_curso (or return all slots if none specified)
        course_slots = []
        for slot in slots:
            # If the slot JSON is marked with a specific course, match it; otherwise, include it as general
            if not slot.get("id_curso") or slot.get("id_curso") == id_curso:
                course_slots.append(slot)
                
        if course_slots:
            results.append({
                "id_profesor": d.id_docente,
                "nombre_docente": d.nombre_docente,
                "bloques_disponibles": course_slots,
                "correo": d.correo_institucional,
                "facultad": d.facultad
            })
            
    return jsonify(results)

@resources_bp.route('/tutor/availability', methods=['POST'])
def update_tutor_availability():
    """
    POST /api/resources/tutor/availability
    Allows teachers to configure their available slots.
    """
    data = request.json
    if not data or not all(k in data for k in ('id_docente', 'bloques_disponibles')):
        return jsonify({"error": "Faltan campos obligatorios: id_docente, bloques_disponibles"}), 400
        
    id_docente = data['id_docente']
    bloques = data['bloques_disponibles']
    
    tutor = Docente.query.get(id_docente)
    if not tutor:
        return jsonify({"error": "Docente no encontrado"}), 404
        
    try:
        tutor.bloques_disponibles = bloques
        db.session.commit()
        return jsonify({"message": "Disponibilidad horaria guardada con éxito", "bloques": bloques}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@resources_bp.route('/tutor/book', methods=['POST'])
def book_tutor_hour():
    """
    POST /api/resources/tutor/book
    Registers a booking request in 'citas_tutoria' and triggers a mock email dispatch.
    Computes a RAG-driven AI Diagnostics Sheet for the teacher.
    """
    data = request.json
    if not data or not all(k in data for k in ('id_alumno', 'id_profesor', 'dia', 'hora', 'id_curso')):
        return jsonify({"error": "Faltan campos: id_alumno, id_profesor, dia, hora, id_curso"}), 400
        
    id_alumno = data['id_alumno']
    id_profesor = int(data['id_profesor'])
    dia = data['dia']
    hora = data['hora']
    id_curso = data['id_curso']
    modalidad = data.get('modalidad', 'Presencial')
    
    alumno = Alumno.query.get(id_alumno)
    tutor = Docente.query.get(id_profesor)
    
    if not alumno or not tutor:
        return jsonify({"error": "Alumno o Docente no encontrado"}), 404
        
    # Get course details
    course = Curso.query.get(id_curso)
    course_name = course.nombre_curso if course else "Asesoría General"
    
    # 1. Resolve cubicle/link
    cubicle = "Cubículo de permanencia docente"
    if tutor.bloques_disponibles:
        for slot in tutor.bloques_disponibles:
            if slot.get("dia") == dia and slot.get("hora") == hora:
                cubicle = slot.get("cubiculo", cubicle)
                break
                
    # 2. AI Diagnostics summary compilation (RAG)
    weaknesses = AlumnoDebilidad.query.filter_by(id_alumno=id_alumno, id_curso=id_curso).all()
    weakness_list = [f"Semana: {w.tema_central} ({w.errores_count} fallas)" for w in weaknesses]
    
    diagnostico_ia = ""
    if weakness_list:
        weakness_str = ", ".join(weakness_list)
        # LLM structured call or local seeder fallback
        diagnostico_ia = (
            f"🤖 Ficha de Diagnóstico IA: El estudiante registra un rendimiento crítico en: {weakness_str}. "
            f"Se sugiere enfocar la sesión en resolver problemas prácticos directamente relacionados con "
            f"estos temas y evaluar si existen vacíos lógicos en las mallas de prerrequisitos."
        )
    else:
        diagnostico_ia = (
            f"🤖 Ficha de Diagnóstico IA: El estudiante no registra fallas críticas acumuladas en quizzes "
            f"para {course_name}. Se sugiere un repaso general y despejar dudas puntuales planteadas por el alumno."
        )
        
    try:
        # Create appointment record
        # Combine simulated day/hour. We will parse it or set a placeholder date for demo simplicity
        fecha_hora = datetime.now() # Default to today's date for simplicity
        
        cita = CitaTutoria(
            id_alumno=id_alumno,
            id_docente=id_profesor,
            id_curso=id_curso,
            fecha_hora=fecha_hora,
            modalidad=modalidad,
            ubicacion_detalle=cubicle,
            estado_cita='Pendiente',
            diagnostico_ia_previo=diagnostico_ia
        )
        db.session.add(cita)
        db.session.commit()
        
        # 3. Email dispatch mock
        notification_service.send_tutoring_confirmation(
            student_email=alumno.correo_institucional,
            student_name=alumno.nombre,
            teacher_name=tutor.nombre_docente,
            course_name=course_name,
            slot={"dia": dia, "hora": hora, "cubiculo": cubicle}
        )
        
        return jsonify({
            "message": "Cita de tutoría agendada con éxito. Se envió la confirmación por correo institucional.",
            "cita": {
                "id_cita": cita.id_cita,
                "docente": tutor.nombre_docente,
                "fecha_hora": fecha_hora.strftime("%Y-%m-%d %H:%M"),
                "modalidad": modalidad,
                "ubicacion": cubicle,
                "estado": cita.estado_cita
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@resources_bp.route('/appointments/docente/<int:id_docente>', methods=['GET'])
def get_docente_appointments(id_docente):
    """
    GET /api/resources/appointments/docente/<id_docente>
    Lists all booked tutoring appointments for a specific teacher.
    """
    appointments = CitaTutoria.query.filter_by(id_docente=id_docente).order_by(CitaTutoria.id_cita.desc()).all()
    
    return jsonify([{
        "id_cita": a.id_cita,
        "id_alumno": a.id_alumno,
        "alumno_nombre": a.alumno.nombre,
        "curso": a.curso.nombre_curso,
        "fecha_hora": a.fecha_hora.strftime("%Y-%m-%d %H:%M"),
        "modalidad": a.modalidad,
        "ubicacion": a.ubicacion_detalle,
        "estado": a.estado_cita,
        "diagnostico_ia": a.diagnostico_ia_previo
    } for a in appointments])

@resources_bp.route('/appointments/<int:id_cita>/status', methods=['POST'])
def update_appointment_status(id_cita):
    """
    POST /api/resources/appointments/<id_cita>/status
    Allows teachers to accept, finalize or cancel reservations.
    """
    data = request.json
    if not data or 'estado' not in data:
        return jsonify({"error": "Falta el campo 'estado'"}), 400
        
    nuevo_estado = data['estado']
    if nuevo_estado not in ('Pendiente', 'Confirmada', 'Cancelada', 'Asistida'):
        return jsonify({"error": "Estado inválido"}), 400
        
    cita = CitaTutoria.query.get(id_cita)
    if not cita:
        return jsonify({"error": "Cita no encontrada"}), 404
        
    try:
        cita.estado_cita = nuevo_estado
        db.session.commit()
        return jsonify({
            "message": f"Estado de cita actualizado a: {nuevo_estado}",
            "id_cita": id_cita,
            "estado": nuevo_estado
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# Helper to map faculty name to OTPS email
def get_otps_email_for_facultad(facultad):
    if not facultad:
        return "admin@unfv.edu.pe"
    import unicodedata
    norm = "".join(c for c in unicodedata.normalize('NFD', facultad.lower()) if unicodedata.category(c) != 'Mn')
    
    if "derecho" in norm or "fdcp" in norm:
        return "otps.fdcp@unfv.edu.pe"
    elif "social" in norm or "fccss" in norm:
        return "otps.fccss@unfv.edu.pe"
    elif "educacion" in norm or "fe" in norm:
        return "otps.fe@unfv.edu.pe"
    elif "humanidades" in norm or "fh" in norm:
        return "otps.fh@unfv.edu.pe"
    elif "economica" in norm or "fce" in norm:
        return "otps.fce@unfv.edu.pe"
    elif "financiera" in norm or "contable" in norm or "fcfc" in norm:
        return "otps.fcfc@unfv.edu.pe"
    elif "arquitectura" in norm or "fau" in norm:
        return "otps.fau@unfv.edu.pe"
    elif "oceanografia" in norm or "pesqueria" in norm or "fopca" in norm or "alimentaria" in norm:
        return "otps.fopca@unfv.edu.pe"
    elif "civil" in norm or "fic" in norm:
        return "otps.fic@unfv.edu.pe"
    elif "industrial" in norm or "sistemas" in norm or "fiis" in norm:
        return "otps.fiis@unfv.edu.pe"
    elif "administrac" in norm or "fa" in norm:
        return "otps.fa@unfv.edu.pe"
    elif "psicologia" in norm or "faps" in norm:
        return "otps.faps@unfv.edu.pe"
    elif "geografica" in norm or "ambiental" in norm or "figae" in norm:
        return "otps.figae@unfv.edu.pe"
    elif "electronica" in norm or "informatica" in norm or "fiei" in norm:
        return "otps.fiei@unfv.edu.pe"
    elif "odontologia" in norm or "fo" in norm:
        return "otps.fo@unfv.edu.pe"
    elif "natural" in norm or "matematica" in norm or "fcnm" in norm:
        return "otps.fcnm@unfv.edu.pe"
    elif "medicina" in norm or "fmhu" in norm:
        return "otps.fmhu@unfv.edu.pe"
    elif "tecnologia medica" in norm or "ftm" in norm:
        return "otps.ftm@unfv.edu.pe"
        
    return "admin@unfv.edu.pe"


@resources_bp.route('/tutoring-requests', methods=['POST'])
def create_tutoring_request():
    id_alumno = request.form.get('id_alumno')
    id_curso = request.form.get('id_curso')
    cantidad_estudiantes = request.form.get('cantidad_estudiantes')
    
    if not id_alumno or not id_curso or not cantidad_estudiantes:
        return jsonify({"error": "Faltan campos obligatorios: id_alumno, id_curso, cantidad_estudiantes"}), 400
        
    alumno = Alumno.query.get(id_alumno)
    if not alumno:
        return jsonify({"error": "Estudiante no encontrado"}), 404
        
    if alumno.sancionado:
        return jsonify({"error": "Acceso Restringido: Te encuentras sancionado por afectar la convivencia en tutorías grupales anteriores. No puedes crear solicitudes."}), 403
        
    # File upload handling
    filename = None
    if 'file' in request.files:
        file = request.files['file']
        if file.filename != '':
            if not (file.filename.lower().endswith('.doc') or file.filename.lower().endswith('.docx')):
                return jsonify({"error": "El archivo de solicitud debe ser un documento Word (.doc o .docx)"}), 400
            ext = os.path.splitext(file.filename)[1]
            filename = f"solicitud_{id_alumno}_{datetime.now().strftime('%Y%m%d%H%M%S')}{ext}"
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            
    try:
        sol = SolicitudTutoria(
            id_alumno=id_alumno,
            id_curso=id_curso,
            cantidad_estudiantes=int(cantidad_estudiantes),
            archivo_solicitud_path=filename,
            estado='Pendiente'
        )
        db.session.add(sol)
        db.session.commit()
        
        # Log this activity
        from blueprints.admin import registrar_actividad
        registrar_actividad(
            alumno.id_usuario,
            'Creación de Tutoría',
            f"El alumno {alumno.nombre} ({alumno.id_alumno}) creó una solicitud de tutoría para el curso {id_curso}"
        )
        
        return jsonify({"message": "Solicitud de tutoría registrada con éxito", "id_solicitud": sol.id_solicitud}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@resources_bp.route('/tutoring-requests', methods=['GET'])
def list_student_tutoring_requests():
    id_alumno = request.args.get('id_alumno')
    if not id_alumno:
        return jsonify({"error": "Falta el parámetro 'id_alumno'"}), 400
        
    alumno = Alumno.query.get(id_alumno)
    if not alumno:
        return jsonify({"error": "Estudiante no encontrado"}), 404
        
    # 1. Mis solicitudes creadas
    mis_sols = SolicitudTutoria.query.filter_by(id_alumno=id_alumno).order_by(SolicitudTutoria.fecha_solicitud.desc()).all()
    mis_solicitudes_res = []
    for r in mis_sols:
        alumno_unidos_list = []
        for au in r.alumnos_unidos:
            alumno_unidos_list.append({
                "id_alumno": au.alumno.id_alumno,
                "nombre": au.alumno.nombre
            })
        mis_solicitudes_res.append({
            "id_solicitud": r.id_solicitud,
            "id_curso": r.id_curso,
            "nombre_curso": r.curso.nombre_curso,
            "cantidad_estudiantes": r.cantidad_estudiantes,
            "archivo_solicitud_path": r.archivo_solicitud_path,
            "estado": r.estado,
            "motivo_rechazo": r.motivo_rechazo,
            "nombre_docente": r.docente.nombre_docente if r.docente else None,
            "dia": r.dia,
            "hora": r.hora,
            "link_llamada": r.link_llamada,
            "alumnos_unidos": alumno_unidos_list,
            "confirmada": r.confirmada,
            "puede_completar": calcular_puede_completar(r),
            "motivo_cancelacion_docente": r.motivo_cancelacion_docente,
        })
        
    # 2. Tutorías grupales disponibles a las que se puede unir
    all_approved = SolicitudTutoria.query.filter_by(estado='Aprobado').all()
    tutorias_grupales_res = []
    student_joined_sol_ids = [au.id_solicitud for au in AlumnoUnidoTutoria.query.filter_by(id_alumno=id_alumno).all()]
    
    for r in all_approved:
        if r.alumno.facultad != alumno.facultad:
            continue
        if r.id_alumno == id_alumno:
            continue
        if r.id_solicitud in student_joined_sol_ids:
            continue
            
        alumno_unidos_list = []
        for au in r.alumnos_unidos:
            alumno_unidos_list.append({
                "id_alumno": au.alumno.id_alumno,
                "nombre": au.alumno.nombre
            })
            
        tutorias_grupales_res.append({
            "id_solicitud": r.id_solicitud,
            "nombre_creador": r.alumno.nombre,
            "id_curso": r.id_curso,
            "nombre_curso": r.curso.nombre_curso,
            "cantidad_estudiantes": r.cantidad_estudiantes,
            "nombre_docente": r.docente.nombre_docente if r.docente else None,
            "dia": r.dia,
            "hora": r.hora,
            "link_llamada": r.link_llamada,
            "alumnos_unidos": alumno_unidos_list
        })
        
    # 3. Solicitudes a las que ya se unió
    mis_uniones = AlumnoUnidoTutoria.query.filter_by(id_alumno=id_alumno).all()
    uniones_res = []
    for u in mis_uniones:
        r = u.solicitud
        uniones_res.append({
            "id_solicitud": r.id_solicitud,
            "nombre_creador": r.alumno.nombre,
            "id_curso": r.id_curso,
            "nombre_curso": r.curso.nombre_curso,
            "cantidad_estudiantes": r.cantidad_estudiantes,
            "nombre_docente": r.docente.nombre_docente if r.docente else None,
            "dia": r.dia,
            "hora": r.hora,
            "link_llamada": r.link_llamada,
            "estado": r.estado
        })
        
    return jsonify({
        "mis_solicitudes": mis_solicitudes_res,
        "tutorias_grupales": tutorias_grupales_res,
        "mis_uniones": uniones_res,
        "sancionado": alumno.sancionado
    }), 200


@resources_bp.route('/tutoring-requests/<int:id_solicitud>/join', methods=['POST'])
def join_tutoring_session(id_solicitud):
    data = request.json
    if not data or 'id_alumno' not in data:
        return jsonify({"error": "Falta el campo 'id_alumno'"}), 400
        
    id_alumno = data['id_alumno']
    alumno = Alumno.query.get(id_alumno)
    if not alumno:
        return jsonify({"error": "Estudiante no encontrado"}), 404
        
    if alumno.sancionado:
        return jsonify({"error": "Acceso Restringido: Te encuentras sancionado por afectar la convivencia en tutorías grupales anteriores. No puedes unirte a sesiones."}), 403
        
    sol = SolicitudTutoria.query.get(id_solicitud)
    if not sol:
        return jsonify({"error": "La tutoría grupal solicitada no existe"}), 404
        
    if sol.estado != 'Aprobado':
        return jsonify({"error": "Solo puedes unirte a tutorías grupales en estado Aprobado"}), 400
        
    if sol.id_alumno == id_alumno:
        return jsonify({"error": "No puedes unirte a tu propia tutoría"}), 400
        
    existing = AlumnoUnidoTutoria.query.filter_by(id_solicitud=id_solicitud, id_alumno=id_alumno).first()
    if existing:
        return jsonify({"error": "Ya estás registrado en esta sesión de tutoría"}), 400
        
    try:
        union = AlumnoUnidoTutoria(
            id_solicitud=id_solicitud,
            id_alumno=id_alumno
        )
        db.session.add(union)
        db.session.commit()
        
        # Log this activity
        from blueprints.admin import registrar_actividad
        registrar_actividad(
            alumno.id_usuario,
            'Unión a Tutoría',
            f"El alumno {alumno.nombre} ({alumno.id_alumno}) se unió a la tutoría grupal {id_solicitud}"
        )
        
        return jsonify({"message": "Te has unido a la tutoría grupal con éxito"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


def calcular_puede_completar(sol):
    """Returns True if 2 hours have passed since the session start time."""
    import re
    from datetime import datetime, timedelta
    if not sol.hora or sol.estado not in ('Confirmado', 'Aprobado', 'Completado'):
        return False
    try:
        hora_str = sol.hora.strip()
        m = re.match(r'^(\d{1,2}):(\d{2})$', hora_str)
        if m:
            h, mn = int(m.group(1)), int(m.group(2))
        else:
            m2 = re.match(r'^(\d{1,2}):(\d{2})\s*(a\.?m\.?|p\.?m\.?)$', hora_str, re.IGNORECASE)
            if m2:
                h, mn = int(m2.group(1)), int(m2.group(2))
                ampm = m2.group(3).lower().replace('.', '')
                if ampm == 'pm' and h != 12:
                    h += 12
                elif ampm == 'am' and h == 12:
                    h = 0
            else:
                return False
        tutoring_date = get_next_date_for_weekday(sol.dia) if sol.dia else None
        if tutoring_date:
            import datetime as dt_module
            session_start = dt_module.datetime.combine(tutoring_date, dt_module.time(h, mn))
            session_end = session_start + timedelta(hours=2)
            return datetime.utcnow() >= session_end
        return False
    except Exception:
        return False


@resources_bp.route('/docente/tutoring-sessions', methods=['GET'])
def list_docente_tutoring_sessions():
    id_docente = request.args.get('id_docente')
    if not id_docente:
        return jsonify({"error": "Falta el parámetro 'id_docente'"}), 400
        
    sessions = SolicitudTutoria.query.filter(
        SolicitudTutoria.id_docente == int(id_docente),
        SolicitudTutoria.estado.in_(['Aprobado', 'Confirmado', 'Completado', 'Cancelación Solicitada', 'Cancelado'])
    ).order_by(SolicitudTutoria.fecha_solicitud.desc()).all()
    
    result = []
    for r in sessions:
        alumno_unidos_list = []
        for au in r.alumnos_unidos:
            alumno_unidos_list.append({
                "id_alumno": au.alumno.id_alumno,
                "nombre": au.alumno.nombre
            })
        result.append({
            "id_solicitud": r.id_solicitud,
            "id_alumno": r.id_alumno,
            "nombre_alumno": r.alumno.nombre,
            "id_curso": r.id_curso,
            "nombre_curso": r.curso.nombre_curso,
            "cantidad_estudiantes": r.cantidad_estudiantes,
            "dia": r.dia,
            "hora": r.hora,
            "link_llamada": r.link_llamada,
            "estado": r.estado,
            "escuela": r.escuela,
            "puede_completar": calcular_puede_completar(r),
            "motivo_cancelacion_docente": r.motivo_cancelacion_docente,
            "archivo_cancelacion_path": r.archivo_cancelacion_path,
            "alumnos_unidos": alumno_unidos_list
        })
        
    return jsonify(result), 200


@resources_bp.route('/docente/tutoring-sessions/<int:id_solicitud>/request-cancellation', methods=['POST'])
def request_cancellation_docente(id_solicitud):
    sol = SolicitudTutoria.query.get(id_solicitud)
    if not sol:
        return jsonify({"error": "Tutoría no encontrada"}), 404
        
    motivo = request.form.get('motivo_cancelacion_docente') or request.form.get('motivo_cancelacion')
    if not motivo or not motivo.strip():
        return jsonify({"error": "Debe proporcionar una justificación para la cancelación"}), 400
        
    filename = None
    if 'file' in request.files:
        file = request.files['file']
        if file.filename != '':
            ext = os.path.splitext(file.filename)[1]
            filename = f"evidencia_docente_{id_solicitud}_{datetime.now().strftime('%Y%m%d%H%M%S')}{ext}"
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            
    try:
        sol.estado = 'Cancelación Solicitada'
        sol.motivo_cancelacion_docente = motivo.strip()
        if filename:
            sol.archivo_cancelacion_path = filename
            
        db.session.commit()
        return jsonify({"message": "Solicitud de cancelación enviada al administrador con éxito"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@resources_bp.route('/tutoring-requests/download/<filename>', methods=['GET'])
def download_tutoring_file(filename):
    filename = secure_filename(filename)
    return send_from_directory(UPLOAD_FOLDER, filename)


def get_next_date_for_weekday(weekday_name):
    import datetime
    import unicodedata
    
    day_map = {
        'lunes': 1,
        'martes': 2,
        'miercoles': 3,
        'jueves': 4,
        'viernes': 5,
        'sabado': 6,
        'domingo': 7
    }
    
    norm = "".join(c for c in unicodedata.normalize('NFD', weekday_name.lower()) if unicodedata.category(c) != 'Mn')
    target_weekday = day_map.get(norm)
    if not target_weekday:
        return None
        
    today = datetime.date.today()
    today_weekday = today.isoweekday()
    
    days_ahead = target_weekday - today_weekday
    if days_ahead < 0:
        days_ahead += 7
        
    return today + datetime.timedelta(days=days_ahead)


@resources_bp.route('/tutoring-requests/<int:id_solicitud>/cancel', methods=['POST'])
def cancel_tutoring_request(id_solicitud):
    data = request.json
    if not data or 'id_alumno' not in data:
        return jsonify({"error": "Falta el campo 'id_alumno'"}), 400
        
    id_alumno = data['id_alumno']
    alumno = Alumno.query.get(id_alumno)
    if not alumno:
        return jsonify({"error": "Estudiante no encontrado"}), 404
        
    sol = SolicitudTutoria.query.get(id_solicitud)
    if not sol:
        return jsonify({"error": "La tutoría grupal solicitada no existe"}), 404
        
    if sol.id_alumno != id_alumno:
        return jsonify({"error": "No puedes cancelar una tutoría que no creaste"}), 403
        
    if sol.estado not in ('Pendiente', 'Aprobado'):
        return jsonify({"error": "Solo puedes cancelar tutorías en estado Pendiente o Aprobado"}), 400
        
    if sol.estado == 'Aprobado':
        if not sol.dia:
            return jsonify({"error": "La tutoría aprobada no tiene un día asignado"}), 400
            
        tutoring_date = get_next_date_for_weekday(sol.dia)
        if not tutoring_date:
            return jsonify({"error": "No se pudo determinar la fecha de la tutoría a partir de su día asignado"}), 400
            
        import datetime
        today = datetime.date.today()
        
        if today >= tutoring_date:
            return jsonify({
                "error": "Acceso Denegado: No puedes cancelar la tutoría el mismo día de la sesión o después. El plazo máximo de cancelación es hasta la medianoche del día anterior."
            }), 400
            
    try:
        sol.estado = 'Cancelado'
        db.session.commit()
        
        from blueprints.admin import registrar_actividad
        registrar_actividad(
            alumno.id_usuario,
            'Cancelación de Tutoría',
            f"El alumno {alumno.nombre} ({alumno.id_alumno}) canceló la tutoría grupal {id_solicitud} del curso {sol.curso.nombre_curso}"
        )
        
        return jsonify({"message": "Tutoría grupal cancelada con éxito"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@resources_bp.route('/tutoring-requests/<int:id_solicitud>/confirm-docente', methods=['POST'])
def confirm_tutoring_session(id_solicitud):
    """
    POST /api/resources/tutoring-requests/<id>/confirm-docente
    Teacher confirms they will carry out the tutoring session.
    Changes estado from 'Aprobado' to 'Confirmado'.
    """
    sol = SolicitudTutoria.query.get(id_solicitud)
    if not sol:
        return jsonify({"error": "Tutoría no encontrada"}), 404
    if sol.estado not in ('Aprobado', 'Pendiente'):
        return jsonify({"error": f"No se puede confirmar una tutoría en estado '{sol.estado}'"}), 400
    try:
        sol.estado = 'Confirmado'
        sol.confirmada = True
        db.session.commit()
        return jsonify({"message": "Tutoría confirmada con éxito"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@resources_bp.route('/tutoring-requests/<int:id_solicitud>/complete', methods=['POST'])
def complete_tutoring_session(id_solicitud):
    """
    POST /api/resources/tutoring-requests/<id>/complete
    Mark tutoring as complete. Only allowed 2 hours after the session start time.
    """
    from datetime import datetime, timedelta
    import re
    
    sol = SolicitudTutoria.query.get(id_solicitud)
    if not sol:
        return jsonify({"error": "Tutoría no encontrada"}), 404
    if sol.estado not in ('Confirmado', 'Aprobado'):
        return jsonify({"error": f"No se puede completar una tutoría en estado '{sol.estado}'"}), 400
    
    # Calculate if 2 hours have passed since the session start
    # sol.hora is a string like "14:00" or "2:00 p.m."
    puede_completar = False
    if sol.hora:
        try:
            hora_str = sol.hora.strip()
            # Try HH:MM format first
            m = re.match(r'^(\d{1,2}):(\d{2})$', hora_str)
            if m:
                h, mn = int(m.group(1)), int(m.group(2))
            else:
                # Try "2:00 p.m." format
                m2 = re.match(r'^(\d{1,2}):(\d{2})\s*(a\.?m\.?|p\.?m\.?)$', hora_str, re.IGNORECASE)
                if m2:
                    h, mn = int(m2.group(1)), int(m2.group(2))
                    ampm = m2.group(3).lower().replace('.', '')
                    if ampm == 'pm' and h != 12:
                        h += 12
                    elif ampm == 'am' and h == 12:
                        h = 0
                else:
                    h, mn = 14, 0  # default fallback
            
            # Get next occurrence of sol.dia weekday
            tutoring_date = get_next_date_for_weekday(sol.dia) if sol.dia else None
            if tutoring_date:
                import datetime as dt_module
                session_start = dt_module.datetime.combine(tutoring_date, dt_module.time(h, mn))
                session_end = session_start + timedelta(hours=2)
                puede_completar = datetime.utcnow() >= session_end
            else:
                puede_completar = True  # if no date info, allow completion
        except Exception:
            puede_completar = True  # on parse error, allow
    else:
        puede_completar = True
    
    if not puede_completar:
        return jsonify({"error": "La tutoría aún no ha finalizado. Solo puedes marcarla como completa 2 horas después del inicio de la sesión."}), 400
    
    try:
        sol.estado = 'Completado'
        db.session.commit()
        return jsonify({"message": "Tutoría marcada como completada con éxito"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@resources_bp.route('/tutoring-requests/<int:id_solicitud>/report', methods=['POST'])
def report_tutoring_incident(id_solicitud):
    """
    POST /api/resources/tutoring-requests/<id>/report
    Submit an incident report after a tutoring session.
    Expects JSON: { reportado_por: 'docente'|'alumno', tipo_reporte: str, descripcion: str }
    """
    data = request.json
    if not data or not all(k in data for k in ('reportado_por', 'tipo_reporte')):
        return jsonify({"error": "Faltan campos obligatorios: reportado_por, tipo_reporte"}), 400
    
    reportado_por = data['reportado_por']
    if reportado_por not in ('docente', 'alumno'):
        return jsonify({"error": "El campo 'reportado_por' debe ser 'docente' o 'alumno'"}), 400
    
    sol = SolicitudTutoria.query.get(id_solicitud)
    if not sol:
        return jsonify({"error": "Tutoría no encontrada"}), 404
    
    try:
        reporte = ReporteTutoria(
            id_solicitud=id_solicitud,
            reportado_por=reportado_por,
            tipo_reporte=data['tipo_reporte'],
            descripcion=data.get('descripcion', '')
        )
        db.session.add(reporte)
        db.session.commit()
        return jsonify({"message": "Reporte de incidente enviado con éxito", "id_reporte": reporte.id_reporte}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
