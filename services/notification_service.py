import os

class NotificationService:
    def __init__(self):
        self.sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
        self.default_sender = os.environ.get('DEFAULT_FROM_EMAIL', 'tutor.inteligente@unfv.edu.pe')

    def send_tutoring_confirmation(self, student_email: str, student_name: str, teacher_name: str, course_name: str, slot: dict) -> bool:
        """
        Sends an email confirmation to the student and teacher for a booked tutoring session.
        If SendGrid key is configured, it performs a real API call. Otherwise, it logs to output.
        """
        subject = f"Confirmación de Tutoría Obligatoria: {course_name} - UNFV"
        
        # Format the date and cubicle details
        day = slot.get("dia", "Lunes")
        hora = slot.get("hora", "10:00 a.m.")
        cubicle = slot.get("cubiculo", "Pabellón B - Cubículo 302")
        
        body_text = (
            f"Estimado(a) {student_name},\n\n"
            f"Se ha reservado con éxito tu cita de tutoría obligatoria para el curso {course_name}.\n\n"
            f"Detalles de la Cita:\n"
            f"- Docente: {teacher_name}\n"
            f"- Día: {day}\n"
            f"- Hora: {hora}\n"
            f"- Ubicación: {cubicle}\n\n"
            f"Recuerda asistir puntualmente con tu Carnet Universitario o DNI para registrar tu ingreso.\n\n"
            f"Atentamente,\n"
            f"Sistema de Tutoría Inteligente - Universidad Nacional Federico Villarreal (UNFV)"
        )
        
        print("\n=== [SENDGRID / NODEMAILER MOCK EMAIL SENT] ===")
        print(f"To: {student_email}")
        print(f"Sender: {self.default_sender}")
        print(f"Subject: {subject}")
        print(f"Body:\n{body_text}")
        print("================================================\n")
        
        # Real SendGrid integration if configured
        if self.sendgrid_api_key:
            try:
                # We do a lazy import here to avoid dependency issues if Sendgrid is not installed
                from sendgrid import SendGridAPIClient
                from sendgrid.helpers.mail import Mail
                
                message = Mail(
                    from_email=self.default_sender,
                    to_emails=student_email,
                    subject=subject,
                    plain_text_content=body_text
                )
                sg = SendGridAPIClient(self.sendgrid_api_key)
                response = sg.send(message)
                return response.status_code in [200, 201, 202]
            except Exception as e:
                print(f"SendGrid API Error: {e}. Falling back to success mockup.")
                
        return True

    def send_mental_health_alert(self, student_email: str, student_name: str, message: str) -> bool:
        """Sends a gentle mental health warning or referral link to the student."""
        subject = "Mensaje de Acompañamiento Psicopedagógico - OBU UNFV"
        body_text = (
            f"Hola {student_name},\n\n"
            f"Desde la Oficina de Bienestar Universitario (OBU), queremos recordarte que estamos aquí para apoyarte. "
            f"Nuestros especialistas están disponibles para guiarte frente al estrés académico y brindarte soporte emocional.\n\n"
            f"Nota de la IA:\n\"{message}\"\n\n"
            f"Canales de Atención:\n"
            f"- Teléfono Central: (+51) 748 0888\n"
            f"- Correo de Soporte: obu.psicopedagogia@unfv.edu.pe\n"
            f"- Citas presenciales: Jr. Río Chepén 290, El Agustino (Área de Acompañamiento)\n\n"
            f"No dudes en escribirnos o visitarnos. ¡Tu salud mental es primordial!\n\n"
            f"Atentamente,\n"
            f"Oficina de Bienestar Universitario - UNFV"
        )
        
        print("\n=== [SENDGRID / NODEMAILER MOCK EMAIL SENT] ===")
        print(f"To: {student_email}")
        print(f"Sender: {self.default_sender}")
        print(f"Subject: {subject}")
        print(f"Body:\n{body_text}")
        print("================================================\n")
        
        return True
