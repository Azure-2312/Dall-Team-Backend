from flask import Blueprint, jsonify, request
from models import db, PreguntaComunitaria, Alumno, Curso, AlumnoEvento
from services.gemini_client_manager import gemini_manager
from google.genai import types as _gtypes_new
from werkzeug.utils import secure_filename
import os
import json

crowdsourcing_bp = Blueprint('crowdsourcing', __name__)

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

@crowdsourcing_bp.route('/upload', methods=['POST'])
def upload_question():
    id_alumno = request.form.get('id_alumno')
    id_curso = request.form.get('id_curso')
    facultad = request.form.get('facultad')
    profesor = request.form.get('profesor', '')
    pregunta_texto = request.form.get('pregunta_texto', '')
    respuesta_correcta_declarada = request.form.get('respuesta_correcta_declarada', '')
    
    if not id_alumno or not id_curso or not facultad or not respuesta_correcta_declarada:
        return jsonify({"error": "Faltan campos obligatorios en el formulario"}), 400
        
    ocr_extracted_text = ""
    imagen_path = None
    
    # Check if image was uploaded
    if 'imagen_soporte' in request.files:
        file = request.files['imagen_soporte']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(f"{id_alumno}_{datetime.now().timestamp()}_{file.filename}")
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            imagen_path = f"uploads/{filename}"
            
            # Perform OCR via Gemini
            try:
                with open(filepath, 'rb') as f:
                    image_bytes = f.read()
                    
                def ocr_op(client, model_name):
                    image_part = _gtypes_new.Part.from_bytes(
                        data=image_bytes,
                        mime_type="image/jpeg" if filename.lower().endswith(('.jpg', '.jpeg')) else "image/png"
                    )
                    prompt = (
                        "Extrae el texto completo de esta pregunta de examen. Si contiene ecuaciones o fórmulas matemáticas, "
                        "transcríbelas en formato de texto legible o notación LaTeX limpia. No agregues comentarios introductorios, "
                        "solo devuelve la pregunta transcrita."
                    )
                    return client.models.generate_content(
                        model=model_name,
                        contents=[prompt, image_part]
                    )
                response = gemini_manager.execute_with_retry(ocr_op)
                ocr_extracted_text = response.text.strip()
            except Exception as e:
                print(f"OCR Error: {e}")
                ocr_extracted_text = "[Error extrayendo texto de la imagen]"
                
    # Final text is either OCR result or form input
    final_pregunta_texto = ocr_extracted_text if ocr_extracted_text and ocr_extracted_text != "[Error extrayendo texto de la imagen]" else pregunta_texto
    
    if not final_pregunta_texto:
        return jsonify({"error": "No se detectó texto en la pregunta ni se pudo realizar el OCR de la imagen."}), 400
        
    # Gemini Academic Validation & Moderation
    system_prompt = (
        "Eres un evaluador académico del comité de la UNFV. Valida la veracidad, calidad y contenido de la pregunta "
        "y su respuesta propuesta. Debes resolver el problema tú mismo y compararlo con la respuesta declarada. "
        "Calcula un puntaje de confianza académica (0 a 100) según la corrección técnica. Asigna dificultad "
        "('Facil', 'Intermedio', 'Dificil') y temas clave. "
        "Devuelve estrictamente un JSON válido con la siguiente estructura:\n"
        "{\n"
        "  \"score_confianza\": 90,\n"
        "  \"respuesta_correcta_verificada\": \"Texto o explicación de la solución correcta\",\n"
        "  \"dificultad\": \"Intermedio\",\n"
        "  \"temas_clave\": [\"matrices\", \"gauss-jordan\"],\n"
        "  \"comentario_moderacion\": \"Comentario didáctico sobre la pregunta\"\n"
        "}"
    )
    user_prompt = (
        f"Pregunta del Alumno: {final_pregunta_texto}\n"
        f"Respuesta Declarada por Alumno: {respuesta_correcta_declarada}"
    )
    
    try:
        def validate_op(client, model_name):
            return client.models.generate_content(
                model=model_name,
                contents=[system_prompt, user_prompt],
                config=_gtypes_new.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
        response = gemini_manager.execute_with_retry(validate_op)
        val_result = json.loads(response.text)
        
        score = float(val_result.get("score_confianza", 0))
        # Publish if score >= 85%
        estado = "Publicada" if score >= 85.0 else "En Revision"
        
        # Save to Database
        preg = PreguntaComunitaria(
            aportante_id=id_alumno,
            facultad=facultad,
            id_curso=id_curso,
            profesor=profesor,
            imagen_path=imagen_path,
            pregunta_texto=final_pregunta_texto,
            respuesta_correcta=val_result.get("respuesta_correcta_verificada", respuesta_correcta_declarada),
            score_confianza=score,
            estado=estado,
            nivel_dificultad=val_result.get("dificultad", "Intermedio"),
            temas_clave=val_result.get("temas_clave", [])
        )
        db.session.add(preg)
        db.session.commit()
        
        # Save activity log
        log = AlumnoEvento(
            id_alumno=id_alumno,
            tipo_evento="pregunta_aportada",
            metadata_json=json.dumps({
                "id_pregunta": preg.id_pregunta,
                "score_confianza": score,
                "estado": estado
            })
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            "message": "Pregunta subida y procesada por la IA con éxito",
            "id_pregunta": preg.id_pregunta,
            "pregunta_texto": final_pregunta_texto,
            "score_confianza": score,
            "estado": estado,
            "nivel_dificultad": preg.nivel_dificultad,
            "temas_clave": preg.temas_clave,
            "comentario": val_result.get("comentario_moderacion", "")
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@crowdsourcing_bp.route('/questions/<id_curso>', methods=['GET'])
def get_published_questions(id_curso):
    questions = PreguntaComunitaria.query.filter_by(id_curso=id_curso, estado='Publicada').order_by(PreguntaComunitaria.fecha_creacion.desc()).all()
    
    result = []
    for q in questions:
        result.append({
            "id_pregunta": q.id_pregunta,
            "aportante_id": q.aportante_id,
            "facultad": q.facultad,
            "profesor": q.profesor,
            "imagen_path": q.imagen_path,
            "pregunta_texto": q.pregunta_texto,
            "respuesta_correcta": q.respuesta_correcta,
            "nivel_dificultad": q.nivel_dificultad,
            "temas_clave": q.temas_clave,
            "score_confianza": q.score_confianza
        })
        
    return jsonify(result), 200

@crowdsourcing_bp.route('/questions/pending', methods=['GET'])
def get_pending_questions():
    questions = PreguntaComunitaria.query.filter_by(estado='En Revision').order_by(PreguntaComunitaria.fecha_creacion.desc()).all()
    
    result = []
    for q in questions:
        result.append({
            "id_pregunta": q.id_pregunta,
            "aportante_id": q.aportante_id,
            "facultad": q.facultad,
            "id_curso": q.id_curso,
            "profesor": q.profesor,
            "imagen_path": q.imagen_path,
            "pregunta_texto": q.pregunta_texto,
            "respuesta_correcta": q.respuesta_correcta,
            "score_confianza": q.score_confianza
        })
        
    return jsonify(result), 200

# Endpoint to manually approve/reject questions by admin or docentes
@crowdsourcing_bp.route('/questions/<int:id_pregunta>/moderate', methods=['POST'])
def moderate_question(id_pregunta):
    data = request.json
    if not data or 'action' not in data:
        return jsonify({"error": "Falta la acción a tomar ('aprobar' o 'rechazar')"}), 400
        
    action = data['action']
    preg = PreguntaComunitaria.query.get(id_pregunta)
    if not preg:
        return jsonify({"error": "Pregunta no encontrada"}), 404
        
    try:
        if action == 'aprobar':
            preg.estado = 'Publicada'
        elif action == 'rechazar':
            # Soft delete or keep as rejected
            preg.estado = 'Rechazada'
        else:
            return jsonify({"error": "Acción no soportada"}), 400
            
        db.session.commit()
        return jsonify({"message": f"Pregunta moderada con éxito. Nuevo estado: {preg.estado}"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
