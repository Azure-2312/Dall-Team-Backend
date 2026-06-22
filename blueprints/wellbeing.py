from flask import Blueprint, jsonify, request
from datetime import datetime, date
from services.rag_service import RAGService
from services.notification_service import NotificationService

wellbeing_bp = Blueprint('wellbeing', __name__)
rag_service = RAGService()
notification_service = NotificationService()

# UNFV 2026-I Academic calendar deadline
WITHDRAWAL_DEADLINE = date(2026, 5, 22)

# Official OBU referral payload (from mock data instructions)
OBU_INFO_MOCK = {
    "institucion": "Universidad Nacional Federico Villarreal",
    "oficina_central": "Oficina de Bienestar Universitario (OBU)",
    "servicio": "Área de Acompañamiento Psicopedagógico y Soporte Emocional",
    "canales_atencion_mvp": {
        "telefono_central": "(+51) 748 0888",
        "correo_soporte": "obu.psicopedagogia@unfv.edu.pe",
        "mensaje_empatia_ia": "Detectamos que estás experimentando una alta carga de estrés académico en este momento del ciclo. Recuerda que tu rendimiento en los exámenes no define tu valor. Respira profundo, haz una pausa de 15 minutos y, si lo necesitas, puedes solicitar una cita gratuita de orientación presencial o virtual con los especialistas de Bienestar de tu sede."
    }
}

@wellbeing_bp.route('/obu/info', methods=['GET'])
def get_obu_info():
    """Returns official OBU channels and default empathy message."""
    return jsonify(OBU_INFO_MOCK)

@wellbeing_bp.route('/check-stress', methods=['POST'])
def check_student_stress():
    """
    NLP stress / burnout detector. Checks student text queries.
    If stress level is high, triggers OBU referral block.
    """
    data = request.json
    if not data or 'mensaje' not in data:
        return jsonify({"error": "Falta el campo 'mensaje'"}), 400
        
    mensaje = data['mensaje']
    correo_estudiante = data.get('correo_institucional')
    nombre_estudiante = data.get('nombre_estudiante', 'Estudiante')
    
    # Analyze text
    analysis = rag_service.analyze_sentiment_and_stress(mensaje)
    
    # If high stress, trigger mock email alert in background to OBU/Student
    if analysis.get("nivel_estres") == "alto" and correo_estudiante:
        notification_service.send_mental_health_alert(
            student_email=correo_estudiante,
            student_name=nombre_estudiante,
            message=analysis.get("consejo_empatico")
        )
        
    return jsonify(analysis)
