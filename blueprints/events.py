from flask import Blueprint, jsonify, request
from models import db, Alumno, Curso, SilaboTimeline
from services.event_tracker import track_event, get_engagement_signals, get_recent_events
import os

events_bp = Blueprint('events', __name__)

@events_bp.route('/track', methods=['POST'])
def api_track_event():
    data = request.json
    if not data or not all(k in data for k in ('id_alumno', 'tipo_evento')):
        return jsonify({"error": "Faltan parámetros obligatorios: id_alumno, tipo_evento"}), 400
        
    id_alumno = data['id_alumno']
    tipo_evento = data['tipo_evento']
    metadata = data.get('metadata')
    
    evento = track_event(id_alumno, tipo_evento, metadata)
    if evento:
        return jsonify({"message": "Evento registrado con éxito", "id_evento": evento.id_evento}), 201
    else:
        return jsonify({"error": "Error al registrar el evento"}), 500

@events_bp.route('/signals/<id_alumno>', methods=['GET'])
def api_get_signals(id_alumno):
    signals = get_engagement_signals(id_alumno)
    return jsonify(signals), 200

@events_bp.route('/tutor/quick-message', methods=['POST'])
def api_get_quick_message():
    import json
    data = request.json
    if not data or not all(k in data for k in ('id_alumno', 'tipo_evento')):
        return jsonify({"error": "Faltan parámetros obligatorios: id_alumno, tipo_evento"}), 400
        
    id_alumno = data['id_alumno']
    tipo_evento = data['tipo_evento']
    metadata = data.get('metadata') or {}
    
    id_curso = data.get('id_curso')
    semana = data.get('semana')
    
    # 1. Register the event first in background
    track_event(id_alumno, tipo_evento, metadata)
    
    # 2. Query theme if course and week are provided
    tema_central = "repaso general"
    if id_curso and semana:
        try:
            silabo = SilaboTimeline.query.filter_by(id_curso=id_curso, semana_numero=int(semana)).first()
            if silabo:
                tema_central = silabo.tema_central
        except Exception:
            pass
            
    # 3. Retrieve student and signals context
    alumno = Alumno.query.get(id_alumno)
    nombre_alumno = alumno.nombre if alumno else "Estudiante"
    signals = get_engagement_signals(id_alumno)
    
    # Default fallbacks based on event type (exactly 2 options)
    if tipo_evento == 'cancelar_tutoria':
        message = f"Hola {nombre_alumno}. Veo que se canceló la tutoría. ¿Estás muy ocupado con tus asignaturas o prefieres repasar en otro momento?"
        options = ["Estoy ocupado", "Prefiero luego"]
    elif tipo_evento == 'busqueda_libro':
        query = metadata.get('query') or 'este tema'
        message = f"¿Buscaste libros sobre '{query}'? ¿Te gustaría que repasemos los conceptos clave de este tema o prefieres hacer preguntas directas?"
        options = ["Explicar conceptos", "Hacer preguntas"]
    elif tipo_evento == 'subida_pizarra':
        message = f"Veo que subiste un archivo a la pizarra. ¿Quieres que analicemos su contenido juntos o prefieres trabajar por tu cuenta?"
        options = ["Analizar juntos", "Trabajar solo"]
    elif tipo_evento == 'tiempo_inactivo_pizarra':
        message = "Llevas un tiempo sin realizar trazos. ¿Estás atascado en algún ejercicio o estás leyendo los materiales?"
        options = ["Estoy atascado", "Solo leo"]
    elif tipo_evento == 'click_tutorias':
        message = "¿Ingresaste a la sección de tutorías, estás buscando agendar una sesión nueva o quieres revisar el estado de tus solicitudes?"
        options = ["Agendar tutoría", "Ver solicitudes"]
    elif tipo_evento == 'cambio_semana':
        semana_val = metadata.get('semana') or semana or 'esta semana'
        message = f"¿Cambiaste al tema de la semana {semana_val}? ¿Quieres ver un resumen de los contenidos o resolver tus dudas específicas?"
        options = ["Ver resumen", "Resolver dudas"]
    elif tipo_evento == 'autoevaluacion_iniciada':
        message = "Acabas de iniciar la autoevaluación. ¿Te sientes preparado y con confianza o prefieres hacer un breve repaso antes de empezar?"
        options = ["Estoy listo", "Repasar antes"]
    elif tipo_evento == 'autoevaluacion_completada':
        nota = metadata.get('nota') or 0
        message = f"Completaste el quiz con nota {nota}/20. ¿Te gustaría que revisemos juntos tus debilidades o prefieres intentar otra prueba?"
        options = ["Ver debilidades", "Intentar otra"]
    else:
        message = "¡Hola! ¿Listo para continuar con tus apuntes de hoy? Recuerda que estoy aquí para ayudarte."
        options = ["¡Listo!", "Más tarde"]

    # Specific action instruction for didactical LLM generation
    action_instruction = f"El alumno acaba de realizar la acción '{tipo_evento}' con metadatos: {metadata}."
    if tipo_evento == 'click_tutorias':
        action_instruction = (
            "El alumno ha ingresado a la sección de tutorías. Respóndele de manera sumamente amable recordándole que "
            "te tiene a ti (Tutor IA) como una opción de estudio inmediata las 24 horas para repasar dudas, explicar "
            "conceptos o formularle preguntas de práctica mientras se aprueba o programa su tutoría. Invítalo a interactuar. "
            "Ejemplo de mensaje: '¡Hola! Recuerda que mientras se programa tu tutoría, puedes consultarme tus dudas aquí mismo para estudiar juntos. ¿Quieres repasar algún concepto o prefieres que te haga una pregunta práctica?'"
        )
    elif tipo_evento == 'cancelar_tutoria':
        action_instruction = (
            "El alumno acaba de cancelar una tutoría. Respóndele de forma sumamente comprensiva y empática (por ejemplo, "
            "preguntándole si está muy ocupado o si el tema le resulta muy difícil), ofreciéndole repasar el tema actual a su "
            "propio ritmo cuando se sienta listo. NUNCA digas datos robóticos (evita decir 'veo que cancelaste una tutoría')."
        )
    elif tipo_evento == 'agendar_tutoria':
        action_instruction = (
            "El alumno ha solicitado o se ha unido a una tutoría. Felicítalo brevemente por su iniciativa de estudiar "
            "y pregúntale si quiere que vayan preparando el tema de la tutoría juntos para que llegue listo."
        )
    elif tipo_evento == 'busqueda_libro':
        query_str = metadata.get('query') or 'este tema'
        action_instruction = (
            f"El alumno ha realizado una búsqueda en el catálogo Koha de la biblioteca con el término '{query_str}'. Pregúntale didácticamente sobre "
            "el tema o término buscado, ofreciéndote a explicarle los conceptos clave de manera sencilla. NUNCA recomiendes "
            "libros físicos aquí (el alumno ya está en la biblioteca física)."
        )
    elif tipo_evento == 'subida_pizarra':
        action_instruction = (
            "El alumno ha subido una imagen o archivo de fondo a su pizarra. Ofrécete de forma entusiasta a analizar el "
            "contenido o a resolver juntos algún ejercicio de ese material."
        )
    elif tipo_evento == 'tiempo_inactivo_pizarra':
        action_instruction = (
            "El alumno lleva 10 minutos inactivo en la pizarra. Pregúntale amablemente si está atascado con algún concepto "
            "o ejercicio del curso para poder ayudarle a destrabarlo."
        )
    elif tipo_evento == 'cambio_semana':
        semana_val = metadata.get('semana') or semana or 'esta semana'
        action_instruction = (
            f"El alumno cambió de semana en el sílabo a la semana {semana_val} con el tema central '{tema_central}'. Hazle una pregunta didáctica o curiosa sobre el tema central de "
            "esa semana para despertar su interés o pregúntale si quiere ver un resumen del tema."
        )
    elif tipo_evento == 'autoevaluacion_iniciada':
        action_instruction = (
            "El alumno inició una autoevaluación (quiz). Dale ánimos breves y pregúntale si se siente preparado o "
            "prefiere repasar rápidamente alguna de sus debilidades registradas antes de comenzar."
        )
    elif tipo_evento == 'autoevaluacion_completada':
        nota_val = metadata.get('nota') or 0
        action_instruction = (
            f"El alumno ha completado un quiz con una nota de {nota_val}/20. Coméntale brevemente sobre su desempeño de manera didáctica y "
            "pregúntale si desea revisar los temas en los que tuvo errores o debilidades para reforzarlos."
        )

    # Detailed platform guide to prevent hallucinations
    platform_guide = (
        "La plataforma de la UNFV tiene estas secciones:\n"
        "- MIS CURSOS: Pizarra transparente vectorizada (dibujos, texto, PDF/imágenes, Undo/Redo) y editor de notas.\n"
        "- AUTOEVALUACIÓN: Quizzes interactivos adaptativos de los temas del sílabo cargados hasta la semana anterior. Si se equivoca, registra debilidades.\n"
        "- BIBLIOTECA KOHA: Buscador físico de libros disponibles en sedes de la UNFV.\n"
        "- TUTORÍAS: El alumno NO agenda de forma directa seleccionando fecha/hora libres. Debe solicitar la tutoría grupal subiendo obligatoriamente un archivo Word firmado con cantidad de alumnos. El administrador OTPS la aprueba o rechaza. Una vez aprobada, se asigna docente, horario (día y hora) y enlace de Teams. También puede unirse a tutorías grupales de sus compañeros.\n"
        "- SOPORTE OBU: Consultas de bienestar mental, social o trámites."
    )

    gemini_key = os.environ.get('GEMINI_API_KEY')
    if gemini_key:
        try:
            from google import genai as _genai
            from google.genai import types as _gtypes
            _client = _genai.Client(api_key=gemini_key)
            
            prompt = (
                f"Eres el Tutor IA de la Universidad Nacional Federico Villarreal (UNFV).\n"
                f"El alumno {nombre_alumno} está interactuando con la plataforma de estudios.\n"
                f"Tema de estudio de esta semana: '{tema_central}'\n\n"
                f"[GUÍA DE FUNCIONALIDADES DE LA PLATAFORMA (Usa esto para responder de forma precisa)]:\n"
                f"{platform_guide}\n\n"
                f"INSTRUCCIÓN ESPECÍFICA DE LA ACCIÓN ACTUAL:\n"
                f"{action_instruction}\n\n"
                f"Señales de comportamiento recientes del alumno (como contexto sutil, NUNCA los repitas textualmente):\n"
                f"- Tutorías canceladas este mes: {signals['tutorias_canceladas_ultimo_mes']}\n"
                f"- Días sin interactuar con la pizarra: {signals['dias_sin_abrir_pizarra']}\n"
                f"- Racha de días activos en la semana: {signals['racha_dias_activos']}/7\n"
                f"- Último libro buscado: {signals['ultima_busqueda_libro'] or 'Ninguno'}\n\n"
                f"TAREA:\n"
                f"Genera un objeto JSON con exactamente dos campos:\n"
                f"1. 'mensaje': Una pregunta didáctica/Socrática sumamente CORTA (máximo 15-22 palabras, una sola oración directa) dirigida al estudiante, "
                f"buscando interactuar y obtener una respuesta en base a su acción actual.\n"
                f"2. 'opciones': Una lista con exactamente 2 opciones de respuesta muy cortas (máximo 3-4 palabras cada una) "
                f"para que el alumno responda haciendo clic en un botón.\n\n"
                f"REGLAS DE TONO:\n"
                f"1. Debe ser cálido, empático, humano y nunca inquisitivo o acusador.\n"
                f"2. NUNCA digas datos robóticos de forma literal (evita 'Veo que cancelaste X tutorías' o 'Llevas Y días sin abrir la pizarra').\n"
                f"3. Responde únicamente con el objeto JSON válido, sin delimitadores adicionales."
            )
            
            res = _client.models.generate_content(
                model='gemini-2.0-flash-lite',
                contents=prompt,
                config=_gtypes.GenerateContentConfig(
                    response_mime_type='application/json'
                )
            )
            text_resp = res.text.strip()
            try:
                parsed = json.loads(text_resp)
                message = parsed.get("mensaje") or parsed.get("message") or message
                options = parsed.get("opciones") or parsed.get("options") or options
            except Exception:
                print("Failed parsing Gemini JSON, fallback to default event message")
        except Exception as e:
            print(f"Error generating quick message from Gemini: {e}")

            
    # Ensure options is exactly a list of 2 strings
    if not isinstance(options, list) or len(options) != 2:
        options = ["Sí, claro", "Más tarde"]
    else:
        options = [str(o) for o in options]

    # Return structured JSON
    return jsonify({
        "message": message,
        "options": options,
        "signals": signals
    }), 200
