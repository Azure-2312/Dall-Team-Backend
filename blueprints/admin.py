import os
import json
import requests
from flask import Blueprint, jsonify, request
from models import db, Usuario, Alumno, Docente, Curso, HistorialAcademico, SilaboTimeline, CitaTutoria, AlumnoDebilidad, AuditoriaRAG, SolicitudTutoria, AlumnoUnidoTutoria, AuditoriaActividad
from blueprints.auth import role_required, generar_prefijos_validos
from services.rag_service import RAGService
from datetime import datetime
from flask_jwt_extended import get_jwt_identity

admin_bp = Blueprint('admin', __name__)
rag_service = RAGService()

def registrar_actividad(id_usuario, accion, detalles):
    try:
        user = Usuario.query.get(id_usuario)
        log = AuditoriaActividad(
            id_usuario=id_usuario,
            username=user.username if user else "Desconocido",
            rol=user.rol if user else "Desconocido",
            accion=accion,
            detalles=detalles
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print("Error registrando actividad:", e)

@admin_bp.route('/metrics', methods=['GET'])
@role_required(['Admin'])
def get_admin_metrics():
    """
    GET /api/admin/metrics
    Aggregates statistical indices across schools and colleges:
    - High-failure courses.
    - Sede student distributions.
    - Sede OBU referral alerts count.
    """
    total_estudiantes = Alumno.query.count()
    total_docentes = Docente.query.count()
    total_citas = CitaTutoria.query.count()
    
    # 1. Failure stats per course
    history = HistorialAcademico.query.all()
    course_stats = {}
    for h in history:
        cid = h.id_curso
        cname = h.curso.nombre_curso
        if cid not in course_stats:
            course_stats[cid] = {"nombre": cname, "aprobados": 0, "jalados": 0}
        if h.estado == 'Aprobado':
            course_stats[cid]["aprobados"] += 1
        elif h.estado == 'Jalado':
            course_stats[cid]["jalados"] += 1
            
    # Calculate failure rates
    high_failure_courses = []
    for cid, stats in course_stats.items():
        total = stats["aprobados"] + stats["jalados"]
        rate = (stats["jalados"] / total * 100) if total > 0 else 0
        high_failure_courses.append({
            "id_curso": cid,
            "nombre": stats["nombre"],
            "tasa_reprobacion": round(rate, 1),
            "reprobados": stats["jalados"]
        })
    # Sort by rate desc
    high_failure_courses.sort(key=lambda x: x["tasa_reprobacion"], reverse=True)

    # 2. Burnout alerts by Sede (grouped from student weaknesses / stress checks)
    # We aggregate student counts by Sede
    sedes = Alumno.query.with_entities(Alumno.sede_codigo).distinct().all()
    burnout_stats = []
    for (sede,) in sedes:
        # Count high stress students in this sede (for mock demonstration, aggregate based on debilidades counts)
        student_ids = [a.id_alumno for a in Alumno.query.filter_by(sede_codigo=sede).all()]
        stress_count = AlumnoDebilidad.query.filter(
            AlumnoDebilidad.id_alumno.in_(student_ids),
            AlumnoDebilidad.errores_count >= 3
        ).count() if student_ids else 0
        
        burnout_stats.append({
            "sede": sede,
            "alertas_obu": stress_count,
            "riesgo": "Alto" if stress_count > 2 else ("Medio" if stress_count > 0 else "Bajo")
        })

    # Return structured dashboard payload
    return jsonify({
        "resumen": {
            "total_estudiantes": total_estudiantes,
            "total_docentes": total_docentes,
            "total_citas_tutoria": total_citas,
            "auditoria_rag_logs": AuditoriaRAG.query.count()
        },
        "cursos_criticos": high_failure_courses[:4], # Top 4
        "estres_por_sede": burnout_stats
    })



# ─── USER MANAGEMENT ENDPOINTS ───────────────────────────────────────────────

@admin_bp.route('/users', methods=['GET'])
@role_required(['Admin'])
def list_users():
    """GET /api/admin/users - Returns all system users with status."""
    users = Usuario.query.order_by(Usuario.rol, Usuario.fecha_creacion.desc()).all()
    result = []
    for u in users:
        result.append({
            "id_usuario": u.id_usuario,
            "username": u.username,
            "email": u.email,
            "rol": u.rol,
            "activo": u.activo,
            "fecha_creacion": u.fecha_creacion.strftime("%Y-%m-%d") if u.fecha_creacion else None,
            "foto_perfil": u.foto_perfil,
            "cargo": u.cargo,
            "facultad": u.facultad,
            "sancionado": u.alumno_perfil.sancionado if (u.rol == 'Estudiante' and u.alumno_perfil) else False
        })
    return jsonify(result), 200

@admin_bp.route('/users/<int:id_usuario>/status', methods=['PUT'])
@role_required(['Admin'])
def toggle_user_status(id_usuario):
    """PUT /api/admin/users/<id>/status - Enable or disable a user account."""
    user = Usuario.query.get(id_usuario)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
    data = request.json
    if data is None or 'activo' not in data:
        return jsonify({"error": "Se requiere el campo 'activo' (true/false)"}), 400
    try:
        user.activo = bool(data['activo'])
        db.session.commit()
        registrar_actividad(
            get_jwt_identity(),
            'Habilitación/Inhabilitación de Usuario',
            f"Se {'habilitó' if user.activo else 'inhabilitó'} al usuario: {user.username} (Rol: {user.rol})"
        )
        return jsonify({
            "message": f"Usuario {'habilitado' if user.activo else 'inhabilitado'} con éxito",
            "id_usuario": user.id_usuario,
            "activo": user.activo
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/users/<int:id_usuario>', methods=['DELETE'])
@role_required(['Admin'])
def delete_user(id_usuario):
    """DELETE /api/admin/users/<id> - Permanently deletes a user account."""
    user = Usuario.query.get(id_usuario)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
    try:
        username = user.username
        rol = user.rol
        email = user.email
        db.session.delete(user)
        db.session.commit()
        registrar_actividad(
            get_jwt_identity(),
            'Eliminación de Usuario',
            f"Se eliminó permanentemente al usuario: {username} (Rol: {rol}, Email: {email})"
        )
        return jsonify({"message": "Usuario eliminado permanentemente del sistema"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/users/<int:id_usuario>', methods=['PUT'])
@role_required(['Admin'])
def update_user(id_usuario):
    """PUT /api/admin/users/<id> - Modifies an existing user account."""
    user = Usuario.query.get(id_usuario)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
    data = request.json
    if not data:
        return jsonify({"error": "Faltan datos para actualizar"}), 400
        
    try:
        if 'username' in data:
            username = data['username'].strip()
            if username:
                existing = Usuario.query.filter_by(username=username).first()
                if existing and existing.id_usuario != id_usuario:
                    return jsonify({"error": f"El nombre de usuario '{username}' ya está en uso"}), 400
                user.username = username
                
        if 'email' in data:
            email = data['email'].strip()
            if email:
                existing = Usuario.query.filter_by(email=email).first()
                if existing and existing.id_usuario != id_usuario:
                    return jsonify({"error": f"El correo electrónico '{email}' ya está en uso"}), 400
                user.email = email
                
        if 'rol' in data:
            rol = data['rol'].strip()
            if rol in ['Admin', 'Docente', 'Estudiante']:
                user.rol = rol
                
        if 'activo' in data:
            user.activo = bool(data['activo'])
            
        if 'password' in data:
            password = data['password'].strip()
            if password:
                user.set_password(password)
                
        db.session.commit()
        registrar_actividad(
            get_jwt_identity(),
            'Modificación de Usuario',
            f"Se actualizó el usuario: {user.username}. Cambios: {json.dumps(data)}"
        )
        return jsonify({
            "message": f"Usuario '{user.username}' actualizado con éxito",
            "user": {
                "id_usuario": user.id_usuario,
                "username": user.username,
                "email": user.email,
                "rol": user.rol,
                "activo": user.activo
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/ingesta/malla', methods=['POST'])
@role_required(['Admin'])
def ingest_malla_curricular():
    """
    POST /api/admin/ingesta/malla
    Allows uploading a batch of courses for curriculum design.
    """
    data = request.json
    if not data or 'cursos' not in data:
        return jsonify({"error": "Faltan cursos en el payload"}), 400
        
    current_user_id = request.headers.get('X-User-Id') # Mock log ID
    
    try:
        registros_afectados = 0
        for c in data['cursos']:
            # Create or update course
            course = Curso.query.get(c['id_curso'])
            if not course:
                course = Curso(id_curso=c['id_curso'])
                db.session.add(course)
                
            course.nombre_curso = c['nombre_curso']
            course.escuela = c['escuela']
            course.ciclo_teorico = int(c['ciclo_teorico'])
            course.creditos = int(c['creditos'])
            course.id_prerrequisito = c.get('id_prerrequisito')
            registros_afectados += 1
            
        # Log to RAG audit table
        audit = AuditoriaRAG(
            id_usuario_admin=current_user_id,
            tipo_documento="Malla",
            origen_documento="consola_admin_ingesta",
            registros_afectados=registros_afectados
        )
        db.session.add(audit)
        db.session.commit()
        
        current_jwt_user = get_jwt_identity() or current_user_id
        registrar_actividad(
            current_jwt_user,
            'Ingesta de Malla Curricular',
            f"Se importaron {registros_afectados} asignaturas para la malla curricular"
        )
        
        return jsonify({
            "message": "Malla curricular indexada correctamente",
            "registros_procesados": registros_afectados
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/ingesta/silabo', methods=['POST'])
@role_required(['Admin', 'Estudiante'])
def ingest_silabo_rag():
    """
    POST /api/admin/ingesta/silabo
    RAG ingestion pipeline. Parses syllabus text, generates 16 weeks of structured topics
    with LLM (or seeder fallback), vectorizes content, and updates silabos_timeline.
    Supports both JSON and Multipart file upload (PDF).
    """
    if request.is_json:
        data = request.json
        if not data or not all(k in data for k in ('id_curso', 'texto_silabo', 'origen')):
            return jsonify({"error": "Faltan campos obrigatórios: id_curso, texto_silabo, origen"}), 400
        id_curso = data['id_curso']
        texto_silabo = data['texto_silabo']
        origen = data['origen']
    else:
        if 'id_curso' not in request.form:
            return jsonify({"error": "Falta el campo id_curso en el formulario"}), 400
        id_curso = request.form['id_curso'].strip()
        origen = request.form.get('origen', 'Estudiante_PDF')
        
        if 'file' not in request.files:
            return jsonify({"error": "No se subió ningún archivo PDF"}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "Nombre de archivo vacío"}), 400
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({"error": "El archivo debe ser un PDF"}), 400
            
        try:
            import pypdf
            reader = pypdf.PdfReader(file)
            texto_silabo = ""
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    texto_silabo += text + "\n"
            texto_silabo = texto_silabo.strip()
            if not texto_silabo:
                return jsonify({"error": "No se pudo extraer texto del PDF del sílabo"}), 400
        except Exception as pdf_err:
            return jsonify({"error": f"Error leyendo el archivo PDF del sílabo: {str(pdf_err)}"}), 400

    course = Curso.query.get(id_curso)
    if not course:
        return jsonify({"error": "El curso de malla destino no existe"}), 404
        
    try:
        # Prompt LLM to parse syllabus text into 16 weeks or use structured fallback
        print("Segmentando syllabus con pipeline RAG...")
        
        # Simple local chunking based on paragraphs if no LLM config
        lines = [line.strip() for line in texto_silabo.split('\n') if line.strip()]
        weeks_generated = []
        
        # Generate 16 weeks
        for week in range(1, 17):
            # Select line or generate concept
            line_idx = (week - 1) % len(lines) if lines else 0
            tema = lines[line_idx] if lines else f"Tema de Unidad - Semana {week}"
            lectura = f"Lectura complementaria {week} para {course.nombre_curso}"
            
            # Vectorize
            vector = rag_service.get_embedding(f"{tema} {lectura}")
            
            # Save
            timeline_entry = SilaboTimeline.query.filter_by(id_curso=id_curso, semana_numero=week).first()
            if timeline_entry:
                timeline_entry.tema_central = tema
                timeline_entry.lecturas_obligatorias = lectura
                timeline_entry.contenido_vector = vector
            else:
                timeline_entry = SilaboTimeline(
                    id_curso=id_curso,
                    semana_numero=week,
                    tema_central=tema,
                    lecturas_obligatorias=lectura,
                    contenido_vector=vector
                )
                db.session.add(timeline_entry)
            weeks_generated.append(week)
            
        # Log audit
        audit = AuditoriaRAG(
            tipo_documento="Sílabo",
            origen_documento=origen,
            registros_afectados=len(weeks_generated)
        )
        db.session.add(audit)
        db.session.commit()
        
        registrar_actividad(
            get_jwt_identity(),
            'Ingesta de Sílabo RAG',
            f"Se indexaron y vectorizaron {len(weeks_generated)} semanas del sílabo para el curso {id_curso} desde {origen}"
        )
        
        return jsonify({
            "message": "Sílabo procesado, segmentado y vectorizado con éxito",
            "curso": course.nombre_curso,
            "semanas_creadas": len(weeks_generated)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/auditoria', methods=['GET'])
@role_required(['Admin'])
def get_rag_audit_logs():
    """Lists recent RAG audit logs."""
    logs = AuditoriaRAG.query.order_by(AuditoriaRAG.id_log.desc()).all()
    return jsonify([{
        "id_log": l.id_log,
        "tipo": l.tipo_documento,
        "origen": l.origen_documento,
        "registros": l.registros_afectados,
        "fecha": l.fecha_indexacion.strftime("%Y-%m-%d %H:%M")
    } for l in logs])

# Endpoint to create a new administrator access from inside admin panel
@admin_bp.route('/create-admin', methods=['POST'])
@role_required(['Admin'])
def create_admin():
    data = request.json
    if not data or not all(k in data for k in ('nombres', 'apellidos', 'email', 'password')):
        return jsonify({"error": "Faltan campos obligatorios para registrar administrador"}), 400
        
    nombres = data['nombres'].strip()
    apellidos = data['apellidos'].strip()
    email = data['email'].strip()
    password = data['password']
    cargo = data.get('cargo', 'Tutoría y Psicopedagogía').strip()
    facultad = data.get('facultad', '').strip()
    
    nombre_completo = f"{nombres} {apellidos}"
    
    if not email.endswith('@unfv.edu.pe'):
        return jsonify({"error": "El correo debe pertenecer al dominio institucional (@unfv.edu.pe)"}), 400
        
    email_prefix = email.split('@')[0]
    
    is_otps = email_prefix.startswith('otps.')
    if not is_otps:
        valid_prefixes = generar_prefijos_validos(nombre_completo)
        if not valid_prefixes:
            return jsonify({"error": "No se pudo validar el formato del nombre ingresado"}), 400
            
        if email_prefix not in valid_prefixes:
            sugerencias = " o ".join([f"{p}@unfv.edu.pe" for p in valid_prefixes])
            return jsonify({"error": f"El correo institucional no coincide con la nomenclatura reglamentaria. Debe ser: {sugerencias}"}), 400
        
    if Usuario.query.filter_by(email=email).first() or Usuario.query.filter_by(username=email_prefix).first():
        return jsonify({"error": "El correo o usuario ya se encuentra registrado"}), 400
        
    try:
        user = Usuario(
            username=email_prefix,
            email=email,
            rol='Admin',
            activo=True,
            cargo=cargo,
            facultad=facultad
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        registrar_actividad(
            get_jwt_identity(),
            'Creación de Administrador',
            f"Se creó el administrador: {email_prefix} para la facultad {facultad} con cargo {cargo}"
        )
        
        return jsonify({"message": f"Acceso administrativo para {nombre_completo} creado con éxito"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# Endpoint to create a new teacher access from inside admin panel
@admin_bp.route('/create-docente', methods=['POST'])
@role_required(['Admin'])
def create_docente():
    data = request.json
    if not data or not all(k in data for k in ('nombres', 'apellidos', 'email', 'password', 'sede_codigo', 'facultad', 'escuela_principal', 'tipo_docente')):
        return jsonify({"error": "Faltan campos obligatorios para registrar docente"}), 400
        
    nombres = data['nombres'].strip()
    apellidos = data['apellidos'].strip()
    email = data['email'].strip()
    password = data['password']
    sede_codigo = data['sede_codigo'].strip()
    facultad = data['facultad'].strip()
    escuela_principal = data['escuela_principal'].strip()
    tipo_docente = data['tipo_docente'].strip()
    
    nombre_completo = f"{nombres} {apellidos}"
    
    if tipo_docente not in ('Permanente', 'Contratado'):
        return jsonify({"error": "El tipo de docente debe ser 'Permanente' o 'Contratado'"}), 400
        
    if not email.endswith('@unfv.edu.pe'):
        return jsonify({"error": "El correo debe pertenecer al dominio institucional (@unfv.edu.pe)"}), 400
        
    email_prefix = email.split('@')[0]
    
    valid_prefixes = generar_prefijos_validos(nombre_completo)
    if not valid_prefixes:
        return jsonify({"error": "No se pudo validar el formato del nombre ingresado"}), 400
        
    if email_prefix not in valid_prefixes:
        sugerencias = " o ".join([f"{p}@unfv.edu.pe" for p in valid_prefixes])
        return jsonify({"error": f"El correo institucional no coincide con la nomenclatura reglamentaria. Debe ser: {sugerencias}"}), 400
        
    if Usuario.query.filter_by(email=email).first() or Usuario.query.filter_by(username=email_prefix).first():
        return jsonify({"error": "El correo institucional ya se encuentra registrado"}), 400
        
    try:
        user = Usuario(
            username=email_prefix,
            email=email,
            rol='Docente',
            activo=True
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        docente = Docente(
            id_usuario=user.id_usuario,
            nombres=nombres,
            apellidos=apellidos,
            sede_codigo=sede_codigo,
            facultad=facultad,
            escuela_principal=escuela_principal,
            correo_institucional=email,
            tipo_docente=tipo_docente
        )
        db.session.add(docente)
        db.session.commit()
        
        registrar_actividad(
            get_jwt_identity(),
            'Creación de Docente',
            f"Se creó el docente: {email_prefix} para la facultad {facultad}"
        )
        
        return jsonify({"message": f"Acceso docente para {nombre_completo} creado con éxito"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/malla-ia', methods=['POST'])
@role_required(['Admin'])
def ingest_malla_ia():
    """
    POST /api/admin/malla-ia
    Uses Gemini API to parse curricular plan text into structured courses,
    inserts them into malla_curricular, and automatically enrolls students.
    """
    if request.is_json:
        data = request.json
        if not data or not all(k in data for k in ('escuela', 'malla_texto')):
            return jsonify({"error": "Faltan campos obligatorios: escuela, malla_texto"}), 400
        escuela = data['escuela'].strip()
        malla_texto = data['malla_texto'].strip()
    else:
        if 'escuela' not in request.form:
            return jsonify({"error": "Falta el campo escuela en el formulario"}), 400
        escuela = request.form['escuela'].strip()
        
        if 'file' not in request.files:
            return jsonify({"error": "No se subió ningún archivo PDF"}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "Nombre de archivo vacío"}), 400
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({"error": "El archivo debe ser un PDF"}), 400
            
        try:
            import pypdf
            reader = pypdf.PdfReader(file)
            malla_texto = ""
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    malla_texto += text + "\n"
            malla_texto = malla_texto.strip()
            if not malla_texto:
                return jsonify({"error": "No se pudo extraer texto del PDF (el archivo podría estar vacío o contener imágenes sin texto digital)"}), 400
        except Exception as pdf_err:
            return jsonify({"error": f"Error leyendo el archivo PDF: {str(pdf_err)}"}), 400
    
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_key:
        return jsonify({"error": "La clave de API de Gemini no está configurada en el servidor"}), 500
        
    gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
    
    prompt = (
        f"Eres un experto en mallas curriculares universitarias para la Universidad Nacional Federico Villarreal (UNFV).\n"
        f"Tu tarea es analizar el siguiente texto de un plan de estudios (malla curricular) de la '{escuela}' y extraer todos sus cursos.\n"
        f"Retorna ÚNICAMENTE un arreglo JSON de objetos que representen los cursos, sin explicaciones ni formato markdown (sin ```json, etc.).\n"
        f"Cada objeto de curso debe tener exactamente la siguiente estructura:\n"
        f"- 'id_curso': código de curso de máximo 10 caracteres (ej. INF01, INF02). Si no existe en el texto, invéntalo de forma lógica y secuencial.\n"
        f"- 'nombre_curso': nombre del curso (ej. Algoritmos, Física I).\n"
        f"- 'ciclo_teorico': número entero del ciclo (del 1 al 10).\n"
        f"- 'creditos': número entero de créditos.\n"
        f"- 'id_prerrequisito': el código del curso que es prerrequisito (ej. INF01). Pon null si no tiene prerrequisito.\n\n"
        f"Texto de la malla:\n{malla_texto}"
    )
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }
    
    try:
        response = requests.post(gemini_url, json=payload, timeout=180)
        if response.status_code != 200:
            return jsonify({"error": f"Error de Gemini API: {response.text}"}), response.status_code
            
        res_data = response.json()
        text_response = res_data['candidates'][0]['content']['parts'][0]['text']
        
        # Clean any accidental markdown format (just in case)
        text_response = text_response.strip()
        if text_response.startswith("```json"):
            text_response = text_response.split("```json")[1].split("```")[0].strip()
        elif text_response.startswith("```"):
            text_response = text_response.split("```")[1].split("```")[0].strip()
            
        cursos_extraidos = json.loads(text_response)
        if not isinstance(cursos_extraidos, list):
            return jsonify({"error": "La respuesta de Gemini no es un arreglo JSON"}), 500
            
        # First Pass: Insert/Update courses without prerequisites to avoid FK errors
        for c in cursos_extraidos:
            cid = c['id_curso'].strip()
            nombre = c['nombre_curso'].strip()
            ciclo = int(c['ciclo_teorico'])
            creditos = int(c['creditos'])
            
            course = Curso.query.get(cid)
            if not course:
                course = Curso(id_curso=cid)
                db.session.add(course)
            course.nombre_curso = nombre
            course.escuela = escuela
            course.ciclo_teorico = ciclo
            course.creditos = creditos
            course.tipo_estudio = 'General'
            course.tipo_curso = 'Estándar'
            course.es_electivo = False
            
        db.session.commit()
        
        # Second Pass: Set prerequisites
        for c in cursos_extraidos:
            cid = c['id_curso'].strip()
            prereq_id = c.get('id_prerrequisito')
            if prereq_id:
                prereq_id = prereq_id.strip()
                # Verify prerequisite exists
                prereq_course = Curso.query.get(prereq_id)
                if prereq_course:
                    course = Curso.query.get(cid)
                    course.id_prerrequisito = prereq_id
                    course.nombre_prerrequisito = prereq_course.nombre_curso
                    
        db.session.commit()
        
        enrolled_count = 0
            
        # Log to audit RAG
        audit = AuditoriaRAG(
            tipo_documento="Malla",
            origen_documento=f"gemini_ia_upload_{escuela[:30]}",
            registros_afectados=len(cursos_extraidos)
        )
        db.session.add(audit)
        db.session.commit()
        
        registrar_actividad(
            get_jwt_identity(),
            'Ingesta de Malla con IA',
            f"Se indexó la malla de {escuela} mediante IA, creando/actualizando cursos"
        )
        
        return jsonify({
            "message": f"Malla curricular para la escuela '{escuela}' procesada con éxito con IA.",
            "cursos_creados": len(cursos_extraidos),
            "alumnos_matriculados": enrolled_count,
            "cursos": [{
                "id_curso": c.id_curso,
                "nombre_curso": c.nombre_curso,
                "ciclo": c.ciclo_teorico,
                "creditos": c.creditos,
                "prerrequisito": c.id_prerrequisito
            } for c in Curso.query.filter_by(escuela=escuela).all()]
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error procesando la malla curricular: {str(e)}"}), 500


@admin_bp.route('/malla/<escuela>', methods=['GET'])
@role_required(['Admin'])
def get_malla_by_escuela(escuela):
    """
    GET /api/admin/malla/<escuela>
    Returns all courses for the specified school (escuela).
    """
    courses = Curso.query.filter_by(escuela=escuela).order_by(Curso.ciclo_teorico).all()
    return jsonify([{
        "id_curso": c.id_curso,
        "nombre_curso": c.nombre_curso,
        "ciclo_teorico": c.ciclo_teorico,
        "creditos": c.creditos,
        "id_prerrequisito": c.id_prerrequisito,
        "nombre_prerrequisito": c.nombre_prerrequisito or (c.prerrequisito.nombre_curso if c.prerrequisito else None),
        "tipo_estudio": c.tipo_estudio,
        "tipo_curso": c.tipo_curso,
        "es_electivo": c.es_electivo
    } for c in courses]), 200


@admin_bp.route('/malla', methods=['POST'])
@role_required(['Admin'])
def add_malla_course():
    """
    POST /api/admin/malla
    Creates or updates a course manually in the curriculum (malla).
    """
    data = request.json
    if not data or not all(k in data for k in ('id_curso', 'nombre_curso', 'escuela', 'ciclo_teorico', 'creditos')):
        return jsonify({"error": "Faltan campos obligatorios para registrar asignatura"}), 400
        
    id_curso = data['id_curso'].strip().upper()
    nombre_curso = data['nombre_curso'].strip()
    escuela = data['escuela'].strip()
    ciclo_teorico = int(data['ciclo_teorico'])
    creditos = int(data['creditos'])
    id_prerrequisito = data.get('id_prerrequisito')
    
    nombre_prerrequisito = None
    if id_prerrequisito:
        id_prerrequisito = id_prerrequisito.strip().upper()
        if not id_prerrequisito:
            id_prerrequisito = None
        else:
            prereq = Curso.query.get(id_prerrequisito)
            if prereq:
                nombre_prerrequisito = prereq.nombre_curso
            else:
                return jsonify({"error": f"El prerrequisito '{id_prerrequisito}' no está registrado aún en el sistema"}), 400

    # Resolve tipo_estudio
    tipo_estudio = data.get('tipo_estudio')
    if not tipo_estudio:
        old_tipo = data.get('tipo_curso', 'General').strip()
        if old_tipo in ['General', 'Especifico', 'Especializado', 'Específico']:
            tipo_estudio = old_tipo
        else:
            tipo_estudio = 'General'

    # Resolve tipo_curso (Estándar vs Electivo)
    tipo_curso = data.get('tipo_curso')
    if not tipo_curso:
        es_electivo_val = bool(data.get('es_electivo', False))
        tipo_curso = 'Electivo' if es_electivo_val else 'Estándar'
    else:
        tipo_curso = tipo_curso.strip()
        if tipo_curso not in ['Estándar', 'Electivo', 'Estandar', 'electivo']:
            # Fallback based on es_electivo
            es_electivo_val = bool(data.get('es_electivo', False))
            tipo_curso = 'Electivo' if es_electivo_val else 'Estándar'

    try:
        course = Curso.query.get(id_curso)
        is_new = False
        if not course:
            course = Curso(id_curso=id_curso)
            db.session.add(course)
            is_new = True
            
        course.nombre_curso = nombre_curso
        course.escuela = escuela
        course.ciclo_teorico = ciclo_teorico
        course.creditos = creditos
        course.id_prerrequisito = id_prerrequisito
        course.nombre_prerrequisito = nombre_prerrequisito
        course.tipo_estudio = tipo_estudio
        course.tipo_curso = tipo_curso
        course.es_electivo = (tipo_curso.lower() in ['electivo', 'es_electivo'])
        
        db.session.commit()
        
        enrolled_count = 0
                
        # Log to audit RAG
        current_user_id = get_jwt_identity() or request.headers.get('X-User-Id')
        audit = AuditoriaRAG(
            id_usuario_admin=current_user_id if isinstance(current_user_id, int) or (isinstance(current_user_id, str) and current_user_id.isdigit()) else None,
            tipo_documento="Malla",
            origen_documento="consola_admin_manual",
            registros_afectados=1
        )
        db.session.add(audit)
        db.session.commit()
        
        registrar_actividad(
            current_user_id,
            'Creación de Asignatura Manual',
            f"Se {'creó' if is_new else 'actualizó'} la asignatura {nombre_curso} ({id_curso})"
        )
        
        status_msg = "creada" if is_new else "actualizada"
        return jsonify({
            "message": f"Asignatura '{nombre_curso}' ({id_curso}) {status_msg} con éxito",
            "course": {
                "id_curso": course.id_curso,
                "nombre_curso": course.nombre_curso,
                "ciclo_teorico": course.ciclo_teorico,
                "creditos": course.creditos,
                "id_prerrequisito": course.id_prerrequisito,
                "nombre_prerrequisito": course.nombre_prerrequisito,
                "tipo_estudio": course.tipo_estudio,
                "tipo_curso": course.tipo_curso,
                "es_electivo": course.es_electivo
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@admin_bp.route('/malla/<id_curso>', methods=['PUT'])
@role_required(['Admin'])
def update_malla_course(id_curso):
    """
    PUT /api/admin/malla/<id_curso>
    Updates an existing course in the curriculum (malla).
    """
    id_curso = id_curso.strip().upper()
    course = Curso.query.get(id_curso)
    if not course:
        return jsonify({"error": f"La asignatura con código '{id_curso}' no existe"}), 404
        
    data = request.json
    if not data:
        return jsonify({"error": "Faltan datos para actualizar"}), 400
        
    # Optional field updates:
    if 'nombre_curso' in data:
        course.nombre_curso = data['nombre_curso'].strip()
    if 'ciclo_teorico' in data:
        course.ciclo_teorico = int(data['ciclo_teorico'])
    if 'creditos' in data:
        course.creditos = int(data['creditos'])
        
    # Handle Study Type
    if 'tipo_estudio' in data:
        course.tipo_estudio = data['tipo_estudio'].strip()
    elif 'tipo_curso' in data and data['tipo_curso'] in ['General', 'Especifico', 'Especializado', 'Específico']:
        # Legacy support
        course.tipo_estudio = data['tipo_curso'].strip()

    # Handle Course Type (Standard vs Elective)
    if 'tipo_curso' in data and data['tipo_curso'] in ['Estándar', 'Electivo', 'Estandar']:
        course.tipo_curso = data['tipo_curso'].strip()
        course.es_electivo = (course.tipo_curso.lower() == 'electivo')
    elif 'es_electivo' in data:
        course.es_electivo = bool(data['es_electivo'])
        course.tipo_curso = 'Electivo' if course.es_electivo else 'Estándar'
        
    if 'id_prerrequisito' in data:
        id_prerrequisito = data['id_prerrequisito']
        if id_prerrequisito:
            id_prerrequisito = id_prerrequisito.strip().upper()
            if id_prerrequisito == id_curso:
                return jsonify({"error": "Una asignatura no puede ser prerrequisito de sí misma"}), 400
            # Verify it exists
            prereq_course = Curso.query.get(id_prerrequisito)
            if not prereq_course:
                return jsonify({"error": f"El prerrequisito '{id_prerrequisito}' no está registrado"}), 400
            course.id_prerrequisito = id_prerrequisito
            course.nombre_prerrequisito = prereq_course.nombre_curso
        else:
            course.id_prerrequisito = None
            course.nombre_prerrequisito = None

    try:
        db.session.commit()
        registrar_actividad(
            get_jwt_identity(),
            'Modificación de Asignatura',
            f"Se actualizó la asignatura {course.nombre_curso} ({id_curso})"
        )
        return jsonify({
            "message": f"Asignatura '{course.nombre_curso}' ({id_curso}) actualizada con éxito",
            "course": {
                "id_curso": course.id_curso,
                "nombre_curso": course.nombre_curso,
                "ciclo_teorico": course.ciclo_teorico,
                "creditos": course.creditos,
                "id_prerrequisito": course.id_prerrequisito,
                "nombre_prerrequisito": course.nombre_prerrequisito,
                "tipo_estudio": course.tipo_estudio,
                "tipo_curso": course.tipo_curso,
                "es_electivo": course.es_electivo
            }
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


# Check for scheduling overlap (2h duration + 15m gap = 2.25 hours)
def has_scheduling_conflict(id_docente, dia, hora_str, exclude_solicitud_id=None):
    try:
        h, m = map(int, hora_str.split(':'))
        new_start = h + m / 60.0
    except Exception:
        return True # Invalid format
    
    # Query all approved requests for this teacher on this day
    approved = SolicitudTutoria.query.filter_by(
        id_docente=id_docente, dia=dia, estado='Aprobado'
    ).all()
    
    for app in approved:
        if exclude_solicitud_id and app.id_solicitud == exclude_solicitud_id:
            continue
        try:
            eh, em = map(int, app.hora.split(':'))
            exist_start = eh + em / 60.0
        except Exception:
            continue
            
        if abs(new_start - exist_start) < 2.25:
            return True
    return False


@admin_bp.route('/tutoring-requests', methods=['GET'])
@role_required(['Admin'])
def list_admin_tutoring_requests():
    from flask_jwt_extended import get_jwt_identity
    identity = get_jwt_identity()
    admin_user = Usuario.query.get(identity)
    if not admin_user:
        return jsonify({"error": "Admin no encontrado"}), 404
        
    if admin_user.username == 'admin':
        return jsonify([]), 200
        
    # Get all requests
    requests = SolicitudTutoria.query.order_by(SolicitudTutoria.fecha_solicitud.desc()).all()
    
    # Filter by faculty if it's an OTPS admin
    is_otps = admin_user.email.startswith('otps.')
    result = []
    
    for r in requests:
        mapped_email = get_otps_email_for_facultad(r.alumno.facultad)
        if is_otps and mapped_email != admin_user.email:
            continue
            
        # Compile info
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
            "facultad_alumno": r.alumno.facultad,
            "escuela_alumno": r.alumno.escuela,
            "id_curso": r.id_curso,
            "nombre_curso": r.curso.nombre_curso,
            "cantidad_estudiantes": r.cantidad_estudiantes,
            "archivo_solicitud_path": r.archivo_solicitud_path,
            "estado": r.estado,
            "motivo_rechazo": r.motivo_rechazo,
            "id_docente": r.id_docente,
            "nombre_docente": r.docente.nombre_docente if r.docente else None,
            "dia": r.dia,
            "hora": r.hora,
            "link_llamada": r.link_llamada,
            "escuela": r.escuela,
            "motivo_cancelacion_docente": r.motivo_cancelacion_docente,
            "archivo_cancelacion_path": r.archivo_cancelacion_path,
            "fecha_solicitud": r.fecha_solicitud.strftime("%Y-%m-%d %H:%M") if r.fecha_solicitud else None,
            "alumnos_unidos": alumno_unidos_list
        })
        
    return jsonify(result), 200


@admin_bp.route('/tutoring-requests/<int:id_solicitud>/approve', methods=['POST'])
@role_required(['Admin'])
def approve_tutoring_request(id_solicitud):
    sol = SolicitudTutoria.query.get(id_solicitud)
    if not sol:
        return jsonify({"error": "Solicitud no encontrada"}), 404
        
    data = request.json
    if not data or not all(k in data for k in ('escuela', 'id_docente', 'dia', 'hora', 'link_llamada')):
        return jsonify({"error": "Faltan campos para la aprobación: escuela, id_docente, dia, hora, link_llamada"}), 400
        
    escuela = data['escuela'].strip()
    id_docente = int(data['id_docente'])
    dia = data['dia'].strip()
    hora = data['hora'].strip()
    link_llamada = data['link_llamada'].strip()
    
    # Check scheduling conflict
    if has_scheduling_conflict(id_docente, dia, hora, exclude_solicitud_id=id_solicitud):
        return jsonify({"error": "Conflicto de horario: El docente ya tiene asignada una tutoría en un intervalo menor a 2 horas y 15 minutos."}), 409
        
    try:
        sol.estado = 'Aprobado'
        sol.id_docente = id_docente
        sol.dia = dia
        sol.hora = hora
        sol.link_llamada = link_llamada
        sol.escuela = escuela
        sol.motivo_rechazo = None
        
        # Create legacy CitaTutoria record for compatibility
        cita = CitaTutoria(
            id_alumno=sol.id_alumno,
            id_docente=id_docente,
            id_curso=sol.id_curso,
            fecha_hora=datetime.now(),
            modalidad='Virtual',
            ubicacion_detalle=link_llamada,
            estado_cita='Confirmada',
            diagnostico_ia_previo=f"Tutoría grupal aprobada por OTPS para el curso {sol.curso.nombre_curso}."
        )
        db.session.add(cita)
        
        db.session.commit()
        registrar_actividad(
            get_jwt_identity(),
            'Aprobación de Tutoría',
            f"Se aprobó la tutoría {id_solicitud} para el curso {sol.curso.nombre_curso} con el docente ID {id_docente} el {dia} {hora}"
        )
        return jsonify({"message": "Solicitud de tutoría aprobada y programada con éxito"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@admin_bp.route('/tutoring-requests/<int:id_solicitud>/reject', methods=['POST'])
@role_required(['Admin'])
def reject_tutoring_request(id_solicitud):
    sol = SolicitudTutoria.query.get(id_solicitud)
    if not sol:
        return jsonify({"error": "Solicitud no encontrada"}), 404
        
    data = request.json
    if not data or 'motivo_rechazo' not in data:
        return jsonify({"error": "Debe especificar el motivo de rechazo"}), 400
        
    motivo = data['motivo_rechazo'].strip()
    if not motivo:
        return jsonify({"error": "El motivo de rechazo no puede estar vacío"}), 400
        
    try:
        sol.estado = 'Rechazado'
        sol.motivo_rechazo = motivo
        sol.id_docente = None
        sol.dia = None
        sol.hora = None
        sol.link_llamada = None
        
        db.session.commit()
        registrar_actividad(
            get_jwt_identity(),
            'Rechazo de Tutoría',
            f"Se rechazó la tutoría {id_solicitud} para el curso {sol.curso.nombre_curso}. Motivo: {motivo}"
        )
        return jsonify({"message": "Solicitud de tutoría rechazada"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@admin_bp.route('/tutoring-requests/<int:id_solicitud>/resolve-cancellation', methods=['POST'])
@role_required(['Admin'])
def resolve_cancellation(id_solicitud):
    sol = SolicitudTutoria.query.get(id_solicitud)
    if not sol:
        return jsonify({"error": "Solicitud no encontrada"}), 404
        
    data = request.json
    if not data or 'decision' not in data:
        return jsonify({"error": "Debe enviar la decisión ('Aprobar' o 'Rechazar')"}), 400
        
    decision = data['decision'].strip()
    
    try:
        if decision.lower() == 'aprobar':
            sol.estado = 'Cancelado'
        else:
            # Revert status back to Approved
            sol.estado = 'Aprobado'
            sol.motivo_cancelacion_docente = None
            sol.archivo_cancelacion_path = None
            
        db.session.commit()
        registrar_actividad(
            get_jwt_identity(),
            'Resolución de Cancelación',
            f"Se resolvió la solicitud de cancelación de la tutoría {id_solicitud} como: {decision}"
        )
        return jsonify({"message": f"Solicitud de cancelación resuelta como: {decision}"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@admin_bp.route('/users/<int:id_usuario>/toggle-sanction', methods=['POST'])
@role_required(['Admin'])
def toggle_student_sanction(id_usuario):
    alumno = Alumno.query.filter_by(id_usuario=id_usuario).first()
    if not alumno:
        return jsonify({"error": "Perfil de estudiante no encontrado"}), 404
        
    try:
        alumno.sancionado = not alumno.sancionado
        db.session.commit()
        registrar_actividad(
            get_jwt_identity(),
            'Sanción de Estudiante',
            f"Se {'activó' if alumno.sancionado else 'desactivó'} la sanción del estudiante con ID de usuario {id_usuario}"
        )
        return jsonify({
            "message": f"Sanción del estudiante {'activada' if alumno.sancionado else 'desactivada'} con éxito",
            "sancionado": alumno.sancionado
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@admin_bp.route('/actividad', methods=['GET'])
@role_required(['Admin'])
def get_activity_logs():
    logs = AuditoriaActividad.query.order_by(AuditoriaActividad.fecha.desc()).all()
    result = []
    for log in logs:
        result.append({
            "id_log": log.id_log,
            "id_usuario": log.id_usuario,
            "username": log.username,
            "rol": log.rol,
            "accion": log.accion,
            "detalles": log.detalles,
            "fecha": log.fecha.strftime("%Y-%m-%d %H:%M:%S") if log.fecha else None
        })
    return jsonify(result), 200



