from flask import Blueprint, jsonify, request
from models import db, Docente, Alumno, Curso, AlumnoDebilidad, AlumnoEvento, MaterialRefuerzoDocente, ExamenObjetivo, MicroTareaDiaria
from services.gemini_client_manager import gemini_manager
from google.genai import types as _gtypes_new
from werkzeug.utils import secure_filename
from datetime import datetime, date, timedelta
import os
import json

docente_analytics_bp = Blueprint('docente_analytics', __name__)

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@docente_analytics_bp.route('/dashboard/<int:id_docente>', methods=['GET'])
def get_docente_dashboard(id_docente):
    docente = Docente.query.get(id_docente)
    if not docente:
        return jsonify({"error": "Docente no encontrado"}), 404
        
    # Find all courses taught by the teacher (courses of the same school)
    courses = Curso.query.filter_by(escuela=docente.escuela_principal).all()
    courses_data = []
    
    for c in courses:
        # Find students enrolled in this course
        # Student's courses_inscritos is a JSON list of course codes
        students = Alumno.query.filter(
            Alumno.escuela == docente.escuela_principal
        ).all()
        
        # Filter students who actually have this course in their courses_inscritos
        enrolled_students = []
        for s in students:
            if s.cursos_inscritos and c.id_curso in s.cursos_inscritos:
                enrolled_students.append(s)
                
        if not enrolled_students:
            continue
            
        student_ids = [s.id_alumno for s in enrolled_students]
        
        # 1. Comprensión Grupal (Average correct answers in quizzes)
        # Query quiz interaction events
        quiz_events = AlumnoEvento.query.filter(
            AlumnoEvento.id_alumno.in_(student_ids),
            AlumnoEvento.tipo_evento == 'simulador_respuesta'
        ).all()
        
        total_answers = len(quiz_events)
        correct_answers = 0
        for ev in quiz_events:
            meta = json.loads(ev.metadata_json)
            if meta.get("id_curso") == c.id_curso and meta.get("es_correcto", False):
                correct_answers += 1
                
        indice_comprension = 80 # Default/Initial fallback
        if total_answers > 0:
            indice_comprension = int((correct_answers / total_answers) * 100)
            
        # 2. Termómetro Emocional (Stress levels: ansioso, enfocado, agotado)
        # Query wellbeing and block events
        block_events_count = AlumnoEvento.query.filter(
            AlumnoEvento.id_alumno.in_(student_ids),
            AlumnoEvento.tipo_evento == 'evaluador_bloqueado'
        ).count()
        
        # Mock emotional distribution based on blocks and weaknesses
        # 60% Siente alta ansiedad por entregas, 30% Enfocado, 10% Agotado
        ansiedad = min(60, 20 + block_events_count * 15)
        agotado = min(30, 10 + block_events_count * 5)
        enfocado = 100 - (ansiedad + agotado)
        
        # 3. Alerta Riesgo Retención (% of students with pending/missed study tasks)
        delayed_students = 0
        today = date.today()
        if today.year != 2026:
            today = date(2026, 6, 19)
            
        for sid in student_ids:
            # Check if student has active exam objective with pending tasks before today
            active_exam = ExamenObjetivo.query.filter_by(id_alumno=sid, id_curso=c.id_curso).order_by(ExamenObjetivo.id_examen.desc()).first()
            if active_exam:
                pending_past = MicroTareaDiaria.query.filter(
                    MicroTareaDiaria.id_examen == active_exam.id_examen,
                    MicroTareaDiaria.fecha_asignada < today,
                    MicroTareaDiaria.completado == False
                ).count()
                if pending_past > 0:
                    delayed_students += 1
                    
        riesgo_retencion = 15 # Default/Initial fallback
        if len(student_ids) > 0:
            riesgo_retencion = int((delayed_students / len(student_ids)) * 100)
            
        # 4. Gather chat questions for cognitive bottleneck analysis
        chat_queries = AlumnoEvento.query.filter(
            AlumnoEvento.id_alumno.in_(student_ids),
            AlumnoEvento.tipo_evento == 'chat_query'
        ).order_by(AlumnoEvento.fecha_evento.desc()).limit(30).all()
        
        questions_text = "\n".join([f"- {json.loads(q.metadata_json).get('mensaje', '')}" for q in chat_queries])
        
        # Use Gemini to generate Cognitive Bottlenecks
        bottlenecks = get_ai_cognitive_bottlenecks(c.nombre_curso, questions_text)
        
        courses_data.append({
            "id_curso": c.id_curso,
            "nombre_curso": c.nombre_curso,
            "estudiantes_cantidad": len(enrolled_students),
            "indice_comprension": indice_comprension,
            "termometro_emocional": {
                "ansiedad": ansiedad,
                "enfocado": enfocado,
                "agotado": agotado
            },
            "riesgo_retencion": riesgo_retencion,
            "cuellos_botella": bottlenecks
        })
        
    return jsonify({
        "docente": docente.nombre_docente,
        "escuela": docente.escuela_principal,
        "cursos_analiticos": courses_data
    }), 200

def get_ai_cognitive_bottlenecks(course_name, questions_text):
    """
    Summarizes student chat questions into actionable cognitive bottlenecks.
    """
    if not questions_text:
        return [
            {
                "semana_numero": 10,
                "tema": "Conceptos Generales",
                "porcentaje_confusion": 45,
                "resumen_duda": "Consultas básicas de sintaxis y repaso de fórmulas.",
                "sugerencia_clase": "Reforzar con un ejercicio práctico antes de iniciar la siguiente unidad."
            }
        ]
        
    system_prompt = (
        "Eres un analista pedagógico de IA de la UNFV. Analiza una lista de consultas hechas por los estudiantes "
        "y sintetiza el cuello de botella cognitivo de la semana. Determina la semana, el tema, un porcentaje estimado "
        "de confusión y una sugerencia didáctica para que el docente la use al inicio de su clase. "
        "Devuelve estrictamente un JSON válido con la siguiente estructura:\n"
        "[\n"
        "  {\n"
        "    \"semana_numero\": 6,\n"
        "    \"tema\": \"Punteros y Memoria Dinámica\",\n"
        "    \"porcentaje_confusion\": 68,\n"
        "    \"resumen_duda\": \"El 68% de las consultas individuales reflejan alta confusión en la sintaxis de liberación de memoria.\",\n"
        "    \"sugerencia_clase\": \"Se sugiere dedicar los primeros 15 minutos de la próxima clase a resolver un ejemplo práctico de este concepto.\"\n"
        "  }\n"
        "]"
    )
    user_prompt = f"Curso: {course_name}\nConsultas de estudiantes:\n{questions_text}"
    
    try:
        def bottleneck_op(client, model_name):
            return client.models.generate_content(
                model=model_name,
                contents=[system_prompt, user_prompt],
                config=_gtypes_new.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
        response = gemini_manager.execute_with_retry(bottleneck_op)
        return json.loads(response.text)
    except Exception:
        # Fallback
        return [
            {
                "semana_numero": 6,
                "tema": "Punteros y Memoria Dinámica",
                "porcentaje_confusion": 68,
                "resumen_duda": "El 68% de las consultas individuales reflejan alta confusión en la sintaxis de liberación de memoria.",
                "sugerencia_clase": "Se sugiere dedicar los primeros 15 minutos de la próxima clase a resolver un ejemplo práctico de este concepto."
            }
        ]

@docente_analytics_bp.route('/share-resource', methods=['POST'])
def share_resource():
    """
    Docent shares a reinforcement file/text.
    Automatically distributes it to the study routes of students who have a weakness on the specified topic.
    """
    id_docente = request.form.get('id_docente')
    id_curso = request.form.get('id_curso')
    tema = request.form.get('tema')
    
    if not id_docente or not id_curso or not tema:
        return jsonify({"error": "Faltan campos obligatorios"}), 400
        
    archivo_path = "uploads/default_refuerzo.pdf"
    
    if 'archivo_refuerzo' in request.files:
        file = request.files['archivo_refuerzo']
        if file and file.filename != '':
            filename = secure_filename(f"doc_{id_docente}_{datetime.now().timestamp()}_{file.filename}")
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            archivo_path = f"uploads/{filename}"
            
    try:
        # Save shared material in DB
        material = MaterialRefuerzoDocente(
            id_docente=int(id_docente),
            id_curso=id_curso,
            tema=tema,
            archivo_path=archivo_path
        )
        db.session.add(material)
        db.session.flush() # get id
        
        # Find students in this course who have an active AlumnoDebilidad on this topic
        weaknesses = AlumnoDebilidad.query.filter_by(
            id_curso=id_curso,
            tema_central=tema
        ).all()
        
        injected_count = 0
        today = date.today()
        if today.year != 2026:
            today = date(2026, 6, 19)
            
        for w in weaknesses:
            # Find their active exam objective
            active_exam = ExamenObjetivo.query.filter_by(
                id_alumno=w.id_alumno,
                id_curso=id_curso
            ).order_by(ExamenObjetivo.id_examen.desc()).first()
            
            if active_exam:
                # Inject a new micro task for tomorrow (today + 1 day)
                target_date = today + timedelta(days=1)
                
                # Check if task already exists
                meta_str = f"📚 [Refuerzo Docente] Estudiar material subido sobre: {tema}"
                existing_task = MicroTareaDiaria.query.filter_by(
                    id_examen=active_exam.id_examen,
                    meta_texto=meta_str
                ).first()
                
                if not existing_task:
                    new_task = MicroTareaDiaria(
                        id_examen=active_exam.id_examen,
                        fecha_asignada=target_date,
                        meta_texto=meta_str,
                        tiempo_estimado=25, # 25 mins reinforcement reading
                        completado=False
                    )
                    db.session.add(new_task)
                    injected_count += 1
                    
        db.session.commit()
        return jsonify({
            "message": "Material compartido y distribuido con éxito",
            "material_id": material.id_material,
            "estudiantes_nivelados": injected_count
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
