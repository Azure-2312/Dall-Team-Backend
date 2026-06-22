from flask import Blueprint, jsonify, request
from models import db, SilaboTimeline, Alumno, Curso, AlumnoDebilidad, AlumnoEvento
from blueprints.timeline import get_current_academic_week
from services.gemini_client_manager import gemini_manager
from google.genai import types as _gtypes_new
import json

copilot_bp = Blueprint('copilot', __name__)

@copilot_bp.route('/generate-script', methods=['POST'])
def generate_script():
    data = request.json
    if not data or not all(k in data for k in ('id_alumno', 'id_curso', 'tiempo_trayecto', 'modalidad')):
        return jsonify({"error": "Faltan campos obligatorios"}), 400
        
    id_alumno = data['id_alumno']
    id_curso = data['id_curso']
    tiempo = int(data['tiempo_trayecto']) # in minutes
    modalidad = data['modalidad'] # 'resumen' or 'trivia'
    
    # Calculate academic week
    week = get_current_academic_week()
    
    # Get syllabus entries up to this week
    entries = SilaboTimeline.query.filter(
        SilaboTimeline.id_curso == id_curso,
        SilaboTimeline.semana_numero <= week
    ).order_by(SilaboTimeline.semana_numero.asc()).all()
    
    if not entries:
        return jsonify({"error": "No hay temas cargados en el sílabo para este curso."}), 400
        
    # Gather syllabus content
    syllabus_content = []
    for e in entries:
        syllabus_content.append(f"Semana {e.semana_numero}: Tema: {e.tema_central}. Lecturas: {e.lecturas_obligatorias or 'Ninguna'}")
    context_str = "\n".join(syllabus_content)
    
    if modalidad == 'resumen':
        system_prompt = (
            "Eres un locutor de un podcast educativo de la UNFV de tono muy coloquial, fluido, directo y amigable. "
            "Genera un guión estructurado de podcast de repaso basado en los temas del curso provistos. "
            "El guión debe durar aproximadamente el tiempo estimado por el alumno y estar dividido en secciones con títulos llamativos. "
            "Devuelve estrictamente un JSON válido con la siguiente estructura:\n"
            "{\n"
            "  \"titulo\": \"Título del Podcast\",\n"
            "  \"secciones\": [\n"
            "    {\n"
            "      \"seccion_titulo\": \"Título de la sección\",\n"
            "      \"texto_locucion\": \"Texto coloquial y explicativo para ser leído por un sintetizador de voz.\"\n"
            "    }\n"
            "  ]\n"
            "}"
        )
        user_prompt = f"Temario del curso:\n{context_str}\nTiempo estimado del traslado: {tiempo} minutos."
        
        try:
            def summarize_op(client, model_name):
                return client.models.generate_content(
                    model=model_name,
                    contents=[system_prompt, user_prompt],
                    config=_gtypes_new.GenerateContentConfig(
                        response_mime_type="application/json"
                    )
                )
            response = gemini_manager.execute_with_retry(summarize_op)
            result = json.loads(response.text)
            return jsonify(result), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
            
    else: # trivia
        system_prompt = (
            "Eres un evaluador interactivo socrático de la UNFV. Genera una lista de 5 preguntas de trivia (opciones de respuesta corta u opción múltiple) "
            "basadas en los temas del curso provistos. Las preguntas deben ser directas y adecuadas para ser respondidas con audio hablado. "
            "Devuelve estrictamente un JSON válido con la siguiente estructura:\n"
            "{\n"
            "  \"preguntas\": [\n"
            "    {\n"
            "      \"id_pregunta\": 1,\n"
            "      \"pregunta\": \"¿Texto de la pregunta?\",\n"
            "      \"opciones\": [\"A) Opción A\", \"B) Opción B\", \"C) Opción C\"],\n"
            "      \"respuesta_correcta\": \"Texto exacto o clave de la respuesta correcta\",\n"
            "      \"concepto_evaluado\": \"Concepto clave evaluado (ej: Matriz Inversa por Gauss)\"\n"
            "    }\n"
            "  ]\n"
            "}"
        )
        user_prompt = f"Temario del curso:\n{context_str}\nTiempo de trayecto: {tiempo} minutos."
        
        try:
            def trivia_op(client, model_name):
                return client.models.generate_content(
                    model=model_name,
                    contents=[system_prompt, user_prompt],
                    config=_gtypes_new.GenerateContentConfig(
                        response_mime_type="application/json"
                    )
                )
            response = gemini_manager.execute_with_retry(trivia_op)
            result = json.loads(response.text)
            return jsonify(result), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@copilot_bp.route('/verify-answer', methods=['POST'])
def verify_answer():
    data = request.json
    if not data or not all(k in data for k in ('id_alumno', 'id_curso', 'pregunta_texto', 'respuesta_alumno', 'respuesta_correcta', 'concepto_evaluado')):
        return jsonify({"error": "Faltan campos obligatorios"}), 400
        
    id_alumno = data['id_alumno']
    id_curso = data['id_curso']
    pregunta = data['pregunta_texto']
    alumno_ans = data['respuesta_alumno']
    correct_ans = data['respuesta_correcta']
    concepto = data['concepto_evaluado']
    
    system_prompt = (
        "Compara la respuesta oral transcrita del estudiante con la respuesta correcta declarada usando coincidencia semántica. "
        "Sé comprensivo con errores leves de transcripción de voz. "
        "Devuelve estrictamente un JSON válido con la siguiente estructura:\n"
        "{\n"
        "  \"es_correcto\": true|false,\n"
        "  \"coincidencia_porcentaje\": 0-100,\n"
        "  \"retroalimentacion_hablada\": \"Breve feedback hablado de una oración para indicarle al alumno si acertó y por qué (ej: 'Correcto, TCP está orientado a conexión y UDP no.')\"\n"
        "}"
    )
    user_prompt = f"Pregunta: {pregunta}\nRespuesta Correcta Esperada: {correct_ans}\nRespuesta Transcrita del Alumno: {alumno_ans}"
    
    try:
        def verify_op(client, model_name):
            return client.models.generate_content(
                model=model_name,
                contents=[system_prompt, user_prompt],
                config=_gtypes_new.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
        response = gemini_manager.execute_with_retry(verify_op)
        result = json.loads(response.text)
        
        # If incorrect, automatically save as a weakness
        if not result.get("es_correcto", False):
            # Check if weakness exists
            weakness = AlumnoDebilidad.query.filter_by(
                id_alumno=id_alumno,
                id_curso=id_curso,
                tema_central=concepto
            ).first()
            if weakness:
                weakness.errores_count += 1
            else:
                weakness = AlumnoDebilidad(
                    id_alumno=id_alumno,
                    id_curso=id_curso,
                    tema_central=concepto,
                    errores_count=1
                )
                db.session.add(weakness)
            db.session.commit()
            
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
