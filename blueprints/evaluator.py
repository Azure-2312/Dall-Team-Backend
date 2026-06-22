from flask import Blueprint, jsonify, request
from models import db, SilaboTimeline, AlumnoDebilidad, Curso, AlumnoEvento
from services.rag_service import RAGService
from blueprints.timeline import get_current_academic_week
from services.gemini_client_manager import gemini_manager
from google.genai import types as _gtypes_new
from datetime import datetime, timedelta
import json

evaluator_bp = Blueprint('evaluator', __name__)
rag_service = RAGService()

@evaluator_bp.route('/quiz/generate/<id_alumno>/<id_curso>', methods=['GET'])
def generate_quiz(id_alumno, id_curso):
    """
    Generates a spaced repetition quiz:
    - Strictly filters WHERE week < current_week.
    - 70% content from (current_week - 1).
    - 20% content from (current_week - 2).
    - 10% content from (current_week - 3 or older, including foundation concepts).
    - Injects past weaknesses with higher priority.
    """
    week = get_current_academic_week()
    
    # 1. Chronological limit: we can only test topics taught BEFORE the current week (or up to last week)
    max_testable_week = week - 1
    if max_testable_week < 1:
        # If it's Week 1, allow testing Week 1 topics as a diagnostic
        max_testable_week = 1
        
    course = Curso.query.get(id_curso)
    if not course:
        return jsonify({"error": "Curso no encontrado"}), 404
        
    # Get all syllabus/timeline entries up to max_testable_week
    entries = SilaboTimeline.query.filter(
        SilaboTimeline.id_curso == id_curso,
        SilaboTimeline.semana_numero <= max_testable_week
    ).all()
    
    if not entries:
        return jsonify({
            "error": "No hay suficientes materiales cargados en el sílabo para generar un quiz aún.",
            "semana_actual": week,
            "max_evaluable": max_testable_week
        }), 400

    # Categorize entries by weeks for Spaced Repetition
    week_prev_1 = week - 1
    week_prev_2 = week - 2
    
    group_70 = [e for e in entries if e.semana_numero == week_prev_1]
    group_20 = [e for e in entries if e.semana_numero == week_prev_2]
    group_10 = [e for e in entries if e.semana_numero < week_prev_2]
    
    # Fallbacks if some groups are empty (e.g. early weeks)
    if not group_70:
        group_70 = entries # Use whatever is available
    if not group_20:
        group_20 = group_70
    if not group_10:
        group_10 = entries
        
    # Fetch weaknesses for this student in this course
    weaknesses = AlumnoDebilidad.query.filter_by(id_alumno=id_alumno, id_curso=id_curso).order_by(AlumnoDebilidad.errores_count.desc()).all()
    weakness_topics = [w.tema_central for w in weaknesses]

    # Generate questions based on the distribution
    questions = []
    
    # Question 1 & 2: 70% group (Most recent week)
    q1_entry = group_70[0]
    # Check if we should override with a weakness topic
    q1_topic = weakness_topics[0] if len(weakness_topics) > 0 else q1_entry.tema_central
    q1_qs = rag_service.generate_quiz_questions(
        topic=q1_topic,
        context=f"Semana {q1_entry.semana_numero} - {q1_entry.lecturas_obligatorias or ''}",
        count=2
    )
    questions.extend(q1_qs)
    
    # Question 3: 20% group (Two weeks prior)
    q3_entry = group_20[0] if len(group_20) > 0 else q1_entry
    q3_topic = weakness_topics[1] if len(weakness_topics) > 1 else q3_entry.tema_central
    q3_qs = rag_service.generate_quiz_questions(
        topic=q3_topic,
        context=f"Semana {q3_entry.semana_numero} - {q3_entry.lecturas_obligatorias or ''}",
        count=1
    )
    questions.extend(q3_qs)
    
    # Question 4: 10% group (Foundation weeks / early weeks)
    q4_entry = group_10[0] if len(group_10) > 0 else q1_entry
    q4_qs = rag_service.generate_quiz_questions(
        topic=q4_entry.tema_central,
        context=f"Semana {q4_entry.semana_numero} - Conceptos básicos.",
        count=1
    )
    questions.extend(q4_qs)

    # Clean up and ensure we have unique questions
    unique_questions = []
    seen_texts = set()
    for q in questions:
        q_text = q.get("question")
        if q_text not in seen_texts:
            seen_texts.add(q_text)
            unique_questions.append(q)
            
    return jsonify({
        "semana_actual": week,
        "limite_cronologico": max_testable_week,
        "distribucion": {
            "reciente_70": [e.semana_numero for e in group_70],
            "intermedio_20": [e.semana_numero for e in group_20],
            "fundacional_10": [e.semana_numero for e in group_10]
        },
        "debilidades_inyectadas": len(weaknesses),
        "preguntas": unique_questions[:4] # Return exactly 4 questions
    })

@evaluator_bp.route('/quiz/fail', methods=['POST'])
def log_quiz_failure():
    """
    Saves a concept or topic of a failed question in the student's weaknesses registry.
    """
    data = request.json
    if not data or not all(k in data for k in ('id_alumno', 'id_curso', 'tema_fallado')):
        return jsonify({"error": "Faltan campos obligatorios: id_alumno, id_curso, tema_fallado"}), 400
        
    id_alumno = data['id_alumno']
    id_curso = data['id_curso']
    tema = data['tema_fallado']
    
    try:
        # Check if weakness already exists
        weakness = AlumnoDebilidad.query.filter_by(
            id_alumno=id_alumno,
            id_curso=id_curso,
            tema_central=tema
        ).first()
        
        if weakness:
            weakness.errores_count += 1
        else:
            weakness = AlumnoDebilidad(
                id_alumno=id_alumno,
                id_curso=id_curso,
                tema_central=tema,
                errores_count=1
            )
            db.session.add(weakness)
            
        db.session.commit()
        return jsonify({
            "message": "Punto crítico de falla registrado",
            "tema": tema,
            "errores_count": weakness.errores_count
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@evaluator_bp.route('/submit-answer', methods=['POST'])
def submit_answer():
    """
    Saves response telemetry, checks fatigue rules, and flags if screen lock is needed.
    """
    data = request.json
    if not data or not all(k in data for k in ('id_alumno', 'id_curso', 'es_correcto', 'tiempo_respuesta_segundos')):
        return jsonify({"error": "Faltan campos obligatorios"}), 400
        
    id_alumno = data['id_alumno']
    id_curso = data['id_curso']
    es_correcto = data['es_correcto']
    tiempo = int(data['tiempo_respuesta_segundos'])
    sesion_duracion_minutos = int(data.get('sesion_duracion_minutos', 0))
    clicks_repetitivos = bool(data.get('clicks_repetitivos', False))
    
    # Log event
    event_metadata = {
        "id_curso": id_curso,
        "es_correcto": es_correcto,
        "tiempo_respuesta_segundos": tiempo,
        "clicks_repetitivos": clicks_repetitivos
    }
    
    evt = AlumnoEvento(
        id_alumno=id_alumno,
        tipo_evento="simulador_respuesta",
        metadata_json=json.dumps(event_metadata)
    )
    db.session.add(evt)
    db.session.commit()
    
    # Check fatigue rules
    congelar = False
    motivo = ""
    tiempo_bloqueo_minutos = 5
    
    # RULE 1: Frustration
    # If consecutive incorrect answers >= 4 in the last 10 minutes
    ten_minutes_ago = datetime.utcnow() - timedelta(minutes=10)
    recent_events = AlumnoEvento.query.filter(
        AlumnoEvento.id_alumno == id_alumno,
        AlumnoEvento.tipo_evento == "simulador_respuesta",
        AlumnoEvento.fecha_evento >= ten_minutes_ago
    ).order_by(AlumnoEvento.fecha_evento.desc()).all()
    
    incorrect_consecutive = 0
    for re in recent_events:
        meta = json.loads(re.metadata_json)
        if not meta.get("es_correcto", False):
            incorrect_consecutive += 1
        else:
            # Broken sequence
            break
            
    if incorrect_consecutive >= 4:
        congelar = True
        motivo = "frustracion"
        tiempo_bloqueo_minutos = 5
        
    # RULE 2: Night Fatigue
    # Server hour between 01:00 AM and 05:00 AM AND session duration >= 120 minutes
    now_hour = datetime.now().hour
    if 1 <= now_hour <= 5 and sesion_duracion_minutos >= 120:
        congelar = True
        motivo = "fatiga_nocturna"
        tiempo_bloqueo_minutos = 10
        
    # If blocked, log a block event
    if congelar:
        block_evt = AlumnoEvento(
            id_alumno=id_alumno,
            tipo_evento="evaluador_bloqueado",
            metadata_json=json.dumps({"motivo": motivo, "tiempo_bloqueo_minutos": tiempo_bloqueo_minutos})
        )
        db.session.add(block_evt)
        db.session.commit()
        
    return jsonify({
        "es_correcto": es_correcto,
        "congelar": congelar,
        "motivo": motivo,
        "tiempo_bloqueo_minutos": tiempo_bloqueo_minutos,
        "incorrectas_consecutivas": incorrect_consecutive
    }), 200

@evaluator_bp.route('/explain', methods=['POST'])
def explain_incorrect_answer():
    """
    Generates an empathetic step-by-step explanation for an incorrect answer using Gemini.
    """
    data = request.json
    if not data or not all(k in data for k in ('pregunta_texto', 'respuesta_correcta', 'respuesta_alumno')):
        return jsonify({"error": "Faltan campos obligatorios"}), 400
        
    pregunta = data['pregunta_texto']
    correcta = data['respuesta_correcta']
    alumno = data['respuesta_alumno']
    
    system_prompt = (
        "Eres un tutor empático y comprensivo de la UNFV. Explica paso a paso por qué la respuesta "
        "seleccionada por el estudiante es incorrecta y cómo llegar a la respuesta correcta de manera didáctica. "
        "Usa un tono alentador y evita palabras punitivas como 'fallaste', 'error grave', 'incorrecto'. "
        "Devuelve la respuesta en formato Markdown con subtítulos."
    )
    user_prompt = f"Pregunta: {pregunta}\nRespuesta Correcta: {correcta}\nRespuesta del Alumno: {alumno}"
    
    try:
        def explain_op(client, model_name):
            return client.models.generate_content(
                model=model_name,
                contents=[system_prompt, user_prompt]
            )
        response = gemini_manager.execute_with_retry(explain_op)
        return jsonify({"explicacion": response.text}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@evaluator_bp.route('/quiz/weaknesses/<id_alumno>/<id_curso>', methods=['GET'])
def get_weaknesses(id_alumno, id_curso):
    """Retrieves all tracked weaknesses for a student in a course."""
    weaknesses = AlumnoDebilidad.query.filter_by(
        id_alumno=id_alumno,
        id_curso=id_curso
    ).order_by(AlumnoDebilidad.errores_count.desc()).all()
    
    return jsonify([{
        "tema": w.tema_central,
        "errores_count": w.errores_count
    } for w in weaknesses])
