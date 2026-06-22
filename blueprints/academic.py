from flask import Blueprint, jsonify, request
from models import db, Alumno, Curso, HistorialAcademico

academic_bp = Blueprint('academic', __name__)

@academic_bp.route('/student/<id_alumno>', methods=['GET'])
def get_student_academic_status(id_alumno):
    """
    Dynamically computes the student's current active course enrollment based on their
    academic cycle, prerequisites met, and failed courses prioritizations.
    """
    alumno = Alumno.query.get(id_alumno)
    if not alumno:
        return jsonify({"error": "Estudiante no encontrado"}), 404
        
    # Get all history
    history = HistorialAcademico.query.filter_by(id_alumno=id_alumno).all()
    
    approved_ids = [h.id_curso for h in history if h.estado == 'Aprobado']
    failed_ids = list(set([h.id_curso for h in history if h.estado == 'Jalado']) - set(approved_ids))
    
    # helper lists for response
    approved = []
    failed = []
    for h in history:
        course_info = {
            "id_curso": h.id_curso,
            "nombre": h.curso.nombre_curso,
            "ciclo": h.curso.ciclo_teorico,
            "creditos": h.curso.creditos,
            "prerrequisito": h.curso.id_prerrequisito
        }
        if h.estado == 'Aprobado':
            approved.append(course_info)
        elif h.estado == 'Jalado' and h.id_curso not in approved_ids:
            failed.append(course_info)

    # Full Malla Curricular for student's school (normalized school comparison)
    escuela_norm = alumno.escuela.replace("Escuela Profesional de ", "").strip()
    malla = Curso.query.filter(
        (Curso.escuela == alumno.escuela) |
        (Curso.escuela == f"Escuela Profesional de {escuela_norm}") |
        (Curso.escuela == escuela_norm)
    ).order_by(Curso.ciclo_teorico).all()
    
    # Check if prerequisites are resolved
    def prereq_met(course):
        if not course.id_prerrequisito:
            return True
        return course.id_prerrequisito in approved_ids

    # Enrollment list mapping
    enrolled_ids = alumno.cursos_inscritos
    if enrolled_ids is None or len(enrolled_ids) == 0:
        # Default initialization: all courses of student's current cycle
        enrolled_ids = [
            c.id_curso for c in malla
            if c.ciclo_teorico == alumno.ciclo
        ]
        alumno.cursos_inscritos = enrolled_ids
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()

    enrolled_courses = [c for c in malla if c.id_curso in enrolled_ids]
    total_credits = sum(c.creditos for c in enrolled_courses)

    # Prerequisite blocking logic (Recursive check for UI)
    locked_ids = _get_locked_courses_recursive(failed_ids)
    locked_courses = []
    if locked_ids:
        db_locked = Curso.query.filter(Curso.id_curso.in_(locked_ids)).all()
        locked_courses = [{
            "id_curso": c.id_curso,
            "nombre": c.nombre_curso,
            "ciclo": c.ciclo_teorico,
            "creditos": c.creditos,
            "prerrequisito": c.id_prerrequisito
        } for c in db_locked]

    # Format full malla with status
    malla_completa = []
    for c in malla:
        status = "Pendiente"
        if c.id_curso in approved_ids:
            status = "Aprobado"
        elif c.id_curso in enrolled_ids:
            status = "Cursando"
        elif c.id_curso in failed_ids:
            status = "Jalado"
        elif c.id_curso in locked_ids or (c.id_prerrequisito and c.id_prerrequisito not in approved_ids):
            status = "Bloqueado"

        malla_completa.append({
            "id_curso": c.id_curso,
            "nombre": c.nombre_curso,
            "ciclo": c.ciclo_teorico,
            "creditos": c.creditos,
            "prerrequisito": c.id_prerrequisito,
            "nombre_prerrequisito": c.nombre_prerrequisito or (c.prerrequisito.nombre_curso if c.prerrequisito else None),
            "es_electivo": c.es_electivo,
            "tipo_estudio": c.tipo_estudio,
            "tipo_curso": c.tipo_curso,
            "estado": status
        })

    # Prepare active course JSON for student workspace
    cursos_activos = []
    for c in enrolled_courses:
        cursos_activos.append({
            "id_curso": c.id_curso,
            "nombre": c.nombre_curso,
            "ciclo": c.ciclo_teorico,
            "creditos": c.creditos,
            "prerrequisito": c.id_prerrequisito,
            "nombre_prerrequisito": c.nombre_prerrequisito or (c.prerrequisito.nombre_curso if c.prerrequisito else None),
            "es_priorizado": c.id_curso in failed_ids,
            "es_electivo": c.es_electivo,
            "tipo_estudio": c.tipo_estudio,
            "tipo_curso": c.tipo_curso
        })

    is_lagging = len(failed_ids) > 0
    
    addable_candidates = [
        c for c in malla
        if c.ciclo_teorico <= alumno.ciclo and c.id_curso not in approved_ids and c.id_curso not in enrolled_ids
    ]
    
    return jsonify({
        "alumno": {
            "id_alumno": alumno.id_alumno,
            "nombre": alumno.nombre,
            "correo": alumno.correo_institucional,
            "sede": alumno.sede_codigo,
            "facultad": alumno.facultad,
            "escuela": alumno.escuela,
            "ciclo": alumno.ciclo,
            "cursos_inscritos": enrolled_ids,
            "cursos_excluidos": []
        },
        "historial": {
            "aprobados": approved,
            "jalados": failed,
            "cursando": cursos_activos,
            "bloqueados": locked_courses
        },
        "malla_completa": malla_completa,
        "dashboard_restructurado": {
            "es_atrasado": is_lagging,
            "cursos_activos": cursos_activos,
            "total_creditos": total_credits,
            "total_credits": total_credits,
            "excede_creditos": total_credits > 22,
            "excede_credits": total_credits > 22,
            # List of all available courses to add (cycle <= student.ciclo, met prereqs, not approved, not enrolled)
            "opciones_ciclo": [{
                "id_curso": c.id_curso,
                "nombre": c.nombre_curso,
                "ciclo": c.ciclo_teorico,
                "creditos": c.creditos,
                "prerrequisito": c.id_prerrequisito,
                "nombre_prerrequisito": c.nombre_prerrequisito or (c.prerrequisito.nombre_curso if c.prerrequisito else None),
                "tipo_estudio": c.tipo_estudio,
                "tipo_curso": c.tipo_curso,
                "es_electivo": c.es_electivo
            } for c in addable_candidates]
        }
    })

@academic_bp.route('/student/<id_alumno>/exclusions', methods=['POST'])
def save_student_exclusions(id_alumno):
    """
    Saves student's carrying course enrollment list.
    """
    alumno = Alumno.query.get(id_alumno)
    if not alumno:
        return jsonify({"error": "Estudiante no encontrado"}), 404
        
    data = request.json
    if not data:
        return jsonify({"error": "Falta payload"}), 400
        
    # Support both enrolled_course_ids and legacy excluded_course_ids
    enrolled_list = data.get('enrolled_course_ids')
    if enrolled_list is None and 'excluded_course_ids' in data:
        # Legacy compatibility: if they send excluded, we could compute but in our new
        # frontend we always send enrolled_course_ids.
        pass
        
    try:
        if enrolled_list is not None:
            alumno.cursos_inscritos = enrolled_list
        db.session.commit()
        return jsonify({
            "message": "Matrícula actualizada con éxito",
            "cursos_inscritos": alumno.cursos_inscritos
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@academic_bp.route('/student/<id_alumno>/history', methods=['POST'])
def add_academic_history(id_alumno):
    """Allows seeding or modifying student history (approved, failed, taking)."""
    alumno = Alumno.query.get(id_alumno)
    if not alumno:
        return jsonify({"error": "Estudiante no encontrado"}), 404
        
    data = request.json
    if not data or 'records' not in data:
        return jsonify({"error": "Payload inválido. Se espera 'records' (lista de cursos y estados)"}), 400
        
    try:
        # Clear previous history for simulation purity
        HistorialAcademico.query.filter_by(id_alumno=id_alumno).delete()
        
        for record in data['records']:
            id_curso = record.get('id_curso')
            estado = record.get('estado')
            if estado == 'Jalado':
                return jsonify({"error": "No está permitido registrar cursos como jalados"}), 400
            
            # Verify course exists
            course = Curso.query.get(id_curso)
            if not course:
                return jsonify({"error": f"Curso {id_curso} no existe en la malla"}), 400
                
            ha = HistorialAcademico(
                id_alumno=id_alumno,
                id_curso=id_curso,
                estado=estado
            )
            db.session.add(ha)
            
        db.session.commit()
        return jsonify({"message": "Historial académico actualizado con éxito"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

def _get_locked_courses_recursive(failed_course_ids):
    """
    Recursively scans and finds all courses in the curriculum that depend
    directly or indirectly on the list of failed courses.
    """
    locked = set()
    to_scan = list(failed_course_ids)
    
    while to_scan:
        current_failed = to_scan.pop(0)
        # Find all courses that have current_failed as a prerequisite
        dependent_courses = Curso.query.filter_by(id_prerrequisito=current_failed).all()
        for course in dependent_courses:
            if course.id_curso not in locked:
                locked.add(course.id_curso)
                to_scan.append(course.id_curso)
                
    return list(locked)
