from flask import Blueprint, jsonify, request
from models import db, ExamenObjetivo, MicroTareaDiaria, Alumno, Curso, SilaboTimeline, AlumnoEvento
from blueprints.timeline import get_current_academic_week
from services.gemini_client_manager import gemini_manager
from google.genai import types as _gtypes_new
from datetime import datetime, date, timedelta
import json

study_routes_bp = Blueprint('study_routes', __name__)

def get_simulated_today():
    today_val = date.today()
    if today_val.year != 2026:
        # Fallback date for demo consistency
        return date(2026, 6, 19)
    return today_val

@study_routes_bp.route('/plan', methods=['POST'])
def create_study_route():
    data = request.json
    if not data or not all(k in data for k in ('id_alumno', 'id_curso', 'fecha_limite', 'nivel_dificultad', 'disponibilidad_horas')):
        return jsonify({"error": "Faltan campos obligatorios"}), 400
        
    id_alumno = data['id_alumno']
    id_curso = data['id_curso']
    fecha_limite_str = data['fecha_limite']
    nivel_dificultad = int(data['nivel_dificultad'])
    disponibilidad_horas = float(data['disponibilidad_horas'])
    
    try:
        fecha_limite = datetime.strptime(fecha_limite_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Formato de fecha inválido. Usar AAAA-MM-DD"}), 400
        
    today = get_simulated_today()
    days_remaining = (fecha_limite - today).days
    
    if days_remaining <= 0:
        return jsonify({"error": "La fecha límite debe ser posterior a la fecha actual."}), 400
        
    # Limit planning to a maximum of 30 days to avoid token explosion
    days_to_plan = min(30, days_remaining)
    
    # Query syllabus timeline to find topics to study
    week = get_current_academic_week()
    entries = SilaboTimeline.query.filter(
        SilaboTimeline.id_curso == id_curso,
        SilaboTimeline.semana_numero >= week
    ).all()
    
    if not entries:
        # Fallback to general review topics if syllabus not set
        topics = ["Repaso General de Unidades", "Práctica de Ejercicios Pasados", "Simulación de Examen"]
    else:
        topics = [f"Semana {e.semana_numero}: {e.tema_central}" for e in entries]
        
    # Run Gemini planning
    system_prompt = (
        "Eres un programador académico experto en micro-learning. Divide una lista de temas del curso "
        "en tareas diarias cortas (micro-learning) ajustadas al número de días disponibles y la disponibilidad "
        "diaria de estudio del alumno. Cada día debe tener una meta concisa y práctica y un tiempo estimado en minutos. "
        "Devuelve estrictamente un JSON válido con la siguiente estructura:\n"
        "{\n"
        "  \"tasks\": [\n"
        "    {\n"
        "      \"dia_offset\": 0,\n"
        "      \"meta_texto\": \"Nombre/acción de la meta corta (ej: Aprender a calcular la matriz inversa por el método de Gauss-Jordan)\",\n"
        "      \"tiempo_estimado\": 45\n"
        "    }\n"
        "  ]\n"
        "}"
    )
    user_prompt = (
        f"Temas a cubrir: {json.dumps(topics)}\n"
        f"Días de estudio: {days_to_plan}\n"
        f"Horas disponibles por día: {disponibilidad_horas} horas.\n"
        f"Dificultad autopercibida: {nivel_dificultad}/5."
    )
    
    try:
        def plan_op(client, model_name):
            return client.models.generate_content(
                model=model_name,
                contents=[system_prompt, user_prompt],
                config=_gtypes_new.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
        response = gemini_manager.execute_with_retry(plan_op)
        tasks_data = json.loads(response.text).get("tasks", [])
        
        # Deactivate old exams for this course & student
        old_exams = ExamenObjetivo.query.filter_by(id_alumno=id_alumno, id_curso=id_curso).all()
        for oe in old_exams:
            # We can delete them or keep them, let's delete to prevent cluttering
            db.session.delete(oe)
            
        # Create new ExamenObjetivo
        exam_obj = ExamenObjetivo(
            id_alumno=id_alumno,
            id_curso=id_curso,
            fecha_limite=datetime.combine(fecha_limite, datetime.min.time()),
            nivel_dificultad=nivel_dificultad,
            temas_asociados=topics
        )
        db.session.add(exam_obj)
        db.session.flush() # get id_examen
        
        # Insert daily tasks
        inserted_tasks = []
        for t in tasks_data:
            offset = int(t.get("dia_offset", 0))
            task_date = today + timedelta(days=offset)
            
            # Avoid placing tasks after the deadline
            if task_date >= fecha_limite:
                continue
                
            task = MicroTareaDiaria(
                id_examen=exam_obj.id_examen,
                fecha_asignada=task_date,
                meta_texto=t.get("meta_texto", "Repasar apuntes"),
                tiempo_estimado=min(int(disponibilidad_horas * 60), int(t.get("tiempo_estimado", 30))),
                completado=False
            )
            db.session.add(task)
            inserted_tasks.append(task)
            
        db.session.commit()
        
        return jsonify({
            "message": "Ruta de estudio generada con éxito",
            "id_examen": exam_obj.id_examen,
            "tareas_generadas": len(inserted_tasks)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@study_routes_bp.route('/dashboard/<id_alumno>/<id_curso>', methods=['GET'])
def get_student_route_dashboard(id_alumno, id_curso):
    # Find current active route
    exam_obj = ExamenObjetivo.query.filter_by(id_alumno=id_alumno, id_curso=id_curso).order_by(ExamenObjetivo.id_examen.desc()).first()
    if not exam_obj:
        return jsonify({"activo": False, "mensaje": "No tienes una ruta de estudio activa para este curso."}), 200
        
    today = get_simulated_today()
    
    # Get all tasks for this route
    tasks = MicroTareaDiaria.query.filter_by(id_examen=exam_obj.id_examen).order_by(MicroTareaDiaria.fecha_asignada.asc()).all()
    
    # Check if there are incomplete tasks from previous days (before today)
    incomplete_past_tasks = [t for t in tasks if t.fecha_asignada < today and not t.completado]
    needs_recalculation = len(incomplete_past_tasks) > 0
    
    # Format tasks list
    tasks_list = []
    for t in tasks:
        tasks_list.append({
            "id_tarea": t.id_tarea,
            "fecha_asignada": t.fecha_asignada.strftime("%Y-%m-%d"),
            "meta_texto": t.meta_texto,
            "tiempo_estimado": t.tiempo_estimado,
            "completado": t.completado,
            "es_hoy": t.fecha_asignada == today,
            "es_pasada": t.fecha_asignada < today
        })
        
    return jsonify({
        "activo": True,
        "id_examen": exam_obj.id_examen,
        "fecha_limite": exam_obj.fecha_limite.strftime("%Y-%m-%d"),
        "nivel_dificultad": exam_obj.nivel_dificultad,
        "necesita_recalculo": needs_recalculation,
        "tareas": tasks_list,
        "dias_restantes": (exam_obj.fecha_limite.date() - today).days
    }), 200

@study_routes_bp.route('/tasks/<int:id_tarea>/toggle', methods=['POST'])
def toggle_task(id_tarea):
    task = MicroTareaDiaria.query.get(id_tarea)
    if not task:
        return jsonify({"error": "Tarea no encontrada"}), 404
        
    task.completado = not task.completado
    try:
        db.session.commit()
        return jsonify({"message": "Estado de la tarea actualizado", "completado": task.completado}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@study_routes_bp.route('/recalculate', methods=['POST'])
def recalculate_route():
    data = request.json
    if not data or 'id_examen' not in data:
        return jsonify({"error": "Falta id_examen"}), 400
        
    id_examen = data['id_examen']
    exam_obj = ExamenObjetivo.query.get(id_examen)
    if not exam_obj:
        return jsonify({"error": "Ruta de estudio no encontrada"}), 404
        
    today = get_simulated_today()
    fecha_limite = exam_obj.fecha_limite.date()
    
    # Get all tasks
    all_tasks = MicroTareaDiaria.query.filter_by(id_examen=exam_obj.id_examen).all()
    
    # Find incomplete past tasks (marked as missed) and mark them as complete/skipped so they don't trigger alerts
    past_incomplete = [t for t in all_tasks if t.fecha_asignada < today and not t.completado]
    for t in past_incomplete:
        # Mark as completed (or skipped) to clear alert
        t.completado = True
        
    # Find future/today tasks
    future_tasks = [t for t in all_tasks if t.fecha_asignada >= today]
    
    if not future_tasks:
        db.session.commit()
        return jsonify({
            "notificacion": "Vimos que ayer tuviste un día ocupado. No te preocupes, tu temario ya está completo o no quedan días de estudio.",
            "updated_tasks": []
        }), 200
        
    # We will use Gemini to synthesize the remaining future tasks
    # Describe remaining tasks to study
    remaining_tasks_text = "\n".join([f"- {t.meta_texto} ({t.tiempo_estimado} mins)" for t in future_tasks])
    
    system_prompt = (
        "El estudiante tuvo un día ocupado ayer y no pudo estudiar. Su plan de estudio debe ser recalculado. "
        "Para evitar saturarlo, debes sintetizar y resumir los temas de las tareas restantes para que quepan "
        "en los días de estudio que quedan antes del examen. Reduce el tiempo estimado de estudio y haz los temas "
        "más enfocados a resúmenes sintéticos. Genera una meta resumida adaptada para cada uno de los días restantes. "
        "Devuelve estrictamente un JSON válido con la siguiente estructura:\n"
        "{\n"
        "  \"notificacion\": \"Mensaje amigable para el estudiante explicándole la reprogramación (ej: Vimos que ayer tuviste un día ocupado. No te preocupes, reajustamos tu ruta para que completes el temario sin estresarte. Tu nueva meta de hoy es X.)\",\n"
        "  \"tasks\": [\n"
        "    {\n"
        "      \"id_tarea\": 0,\n"
        "      \"meta_texto\": \"Nueva meta sintetizada y resumida\",\n"
        "      \"tiempo_estimado\": 30\n"
        "    }\n"
        "  ]\n"
        "}"
    )
    
    # Map future tasks with their database IDs
    task_mapping = [{"id_tarea": t.id_tarea, "meta_original": t.meta_texto, "tiempo_original": t.tiempo_estimado} for t in future_tasks]
    user_prompt = (
        f"Tareas pendientes restantes:\n{remaining_tasks_text}\n"
        f"Mapeo de IDs de tareas:\n{json.dumps(task_mapping)}\n"
        f"Por favor devuelve la lista de tareas actualizadas utilizando sus correspondientes IDs de base de datos."
    )
    
    try:
        def recalculate_op(client, model_name):
            return client.models.generate_content(
                model=model_name,
                contents=[system_prompt, user_prompt],
                config=_gtypes_new.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
        response = gemini_manager.execute_with_retry(recalculate_op)
        response_data = json.loads(response.text)
        
        notification = response_data.get("notificacion", "Ajustamos tu ruta para evitar sobrecargas. ¡Ánimo!")
        updated_tasks_list = response_data.get("tasks", [])
        
        # Apply updates to database
        db_tasks_map = {t.id_tarea: t for t in future_tasks}
        for ut in updated_tasks_list:
            tid = int(ut.get("id_tarea", 0))
            if tid in db_tasks_map:
                db_tasks_map[tid].meta_texto = ut.get("meta_texto", db_tasks_map[tid].meta_texto)
                db_tasks_map[tid].tiempo_estimado = int(ut.get("tiempo_estimado", db_tasks_map[tid].tiempo_estimado))
                
        # Register a student event for recalculation
        evt = AlumnoEvento(
            id_alumno=exam_obj.id_alumno,
            tipo_evento="ruta_recalculada",
            metadata_json=json.dumps({"notificacion": notification, "id_examen": exam_obj.id_examen})
        )
        db.session.add(evt)
        db.session.commit()
        
        # Format response
        result_tasks = []
        for t in future_tasks:
            result_tasks.append({
                "id_tarea": t.id_tarea,
                "meta_texto": t.meta_texto,
                "tiempo_estimado": t.tiempo_estimado,
                "fecha_asignada": t.fecha_asignada.strftime("%Y-%m-%d")
            })
            
        return jsonify({
            "notificacion": notification,
            "tareas": result_tasks
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
