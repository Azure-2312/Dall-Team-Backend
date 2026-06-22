from flask import Blueprint, jsonify, request
from models import db, SilaboTimeline, AlumnoDebilidad, Curso
from services.rag_service import RAGService
from blueprints.timeline import get_current_academic_week

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
