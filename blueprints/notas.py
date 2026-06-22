from flask import Blueprint, jsonify, request
from models import db, Alumno, Curso, NotasCurso

notas_bp = Blueprint('notas', __name__)

@notas_bp.route('/alumno/<id_alumno>/curso/<id_curso>', methods=['GET'])
def get_nota_curso(id_alumno, id_curso):
    nota = NotasCurso.query.filter_by(id_alumno=id_alumno, id_curso=id_curso).first()
    if not nota:
        return jsonify({
            "id_nota": None,
            "id_alumno": id_alumno,
            "id_curso": id_curso,
            "practica_calificada_1": None,
            "practica_calificada_2": None,
            "examen_parcial": None,
            "examen_final": None,
            "ta": 0.0,
            "promedio_final": 0.0,
            "nota_minima_para_aprobar": 10.5
        }), 200
    return jsonify(nota.to_dict()), 200

@notas_bp.route('/alumno/<id_alumno>/curso/<id_curso>', methods=['PUT'])
def update_nota_curso(id_alumno, id_curso):
    data = request.json or {}
    nota = NotasCurso.query.filter_by(id_alumno=id_alumno, id_curso=id_curso).first()
    
    if not nota:
        nota = NotasCurso(id_alumno=id_alumno, id_curso=id_curso)
        db.session.add(nota)
        
    def to_float(val):
        if val is None or val == "":
            return None
        try:
            return float(val)
        except ValueError:
            return None

    if 'practica_calificada_1' in data:
        nota.practica_calificada_1 = to_float(data['practica_calificada_1'])
    if 'practica_calificada_2' in data:
        nota.practica_calificada_2 = to_float(data['practica_calificada_2'])
    if 'examen_parcial' in data:
        nota.examen_parcial = to_float(data['examen_parcial'])
    if 'examen_final' in data:
        nota.examen_final = to_float(data['examen_final'])
        
    try:
        db.session.commit()
        return jsonify(nota.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@notas_bp.route('/alumno/<id_alumno>', methods=['GET'])
def get_alumno_notas(id_alumno):
    alumno = Alumno.query.get(id_alumno)
    if not alumno:
        return jsonify({"error": "Alumno no encontrado"}), 404
        
    inscritos = alumno.cursos_inscritos or []
    result = []
    for c_id in inscritos:
        curso = Curso.query.get(c_id)
        curso_nombre = curso.nombre_curso if curso else c_id
        nota = NotasCurso.query.filter_by(id_alumno=id_alumno, id_curso=c_id).first()
        if nota:
            nota_dict = nota.to_dict()
        else:
            nota_dict = {
                "id_nota": None,
                "id_alumno": id_alumno,
                "id_curso": c_id,
                "practica_calificada_1": None,
                "practica_calificada_2": None,
                "examen_parcial": None,
                "examen_final": None,
                "ta": 0.0,
                "promedio_final": 0.0,
                "nota_minima_para_aprobar": 10.5
            }
        nota_dict["curso_nombre"] = curso_nombre
        result.append(nota_dict)
        
    return jsonify(result), 200

@notas_bp.route('/alumno/<id_alumno>/resumen', methods=['GET'])
def get_alumno_resumen(id_alumno):
    alumno = Alumno.query.get(id_alumno)
    if not alumno:
        return jsonify({"error": "Alumno no encontrado"}), 404
        
    inscritos = alumno.cursos_inscritos or []
    total_promedio = 0.0
    count_valid = 0
    cursos_aprobados = 0
    cursos_desaprobados = 0
    alertas = []
    detalles = []
    
    for c_id in inscritos:
        curso = Curso.query.get(c_id)
        curso_nombre = curso.nombre_curso if curso else c_id
        nota = NotasCurso.query.filter_by(id_alumno=id_alumno, id_curso=c_id).first()
        
        if nota:
            p_final = nota.promedio_final
            ta_val = nota.ta
            ep = nota.examen_parcial
            ef = nota.examen_final
            min_final = nota.nota_minima_para_aprobar
            
            # Determine risk
            if p_final >= 10.5:
                risk = "Sin Riesgo"
                cursos_aprobados += 1
            else:
                cursos_desaprobados += 1
                if min_final > 14.0:
                    risk = "Riesgo Alto"
                    alertas.append(f"En {curso_nombre} tienes Riesgo Alto: necesitas al menos {min_final} en el examen final para aprobar.")
                else:
                    risk = "Riesgo Medio"
                    alertas.append(f"En {curso_nombre} tienes Riesgo Medio: necesitas al menos {min_final} en el examen final para aprobar.")
            
            detalles.append({
                "id_curso": c_id,
                "curso_nombre": curso_nombre,
                "promedio_final": round(p_final, 2),
                "riesgo": risk,
                "nota_minima_para_aprobar": min_final,
                "practica_calificada_1": nota.practica_calificada_1,
                "practica_calificada_2": nota.practica_calificada_2,
                "examen_parcial": ep,
                "examen_final": ef,
                "ta": round(ta_val, 2)
            })
            total_promedio += p_final
            count_valid += 1
        else:
            # Default empty note
            cursos_desaprobados += 1
            detalles.append({
                "id_curso": c_id,
                "curso_nombre": curso_nombre,
                "promedio_final": 0.0,
                "riesgo": "Sin Notas",
                "nota_minima_para_aprobar": 10.5,
                "practica_calificada_1": None,
                "practica_calificada_2": None,
                "examen_parcial": None,
                "examen_final": None,
                "ta": 0.0
            })
            
    promedio_general = (total_promedio / count_valid) if count_valid > 0 else 0.0
    
    return jsonify({
        "promedio_general": round(promedio_general, 2),
        "cursos_aprobados": cursos_aprobados,
        "cursos_desaprobados": cursos_desaprobados,
        "alertas": alertas,
        "detalles": detalles
    }), 200
