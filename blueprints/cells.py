from flask import Blueprint, jsonify, request
from models import db, CelulaEstudio, AlumnoCelula, Alumno, Curso, AlumnoDebilidad, AlumnoEvento
from services.gemini_client_manager import gemini_manager
from google.genai import types as _gtypes_new
from datetime import datetime
import random
import json

cells_bp = Blueprint('cells', __name__)

PSEUDONYMS = [
    "Matemático Socrático", "Químico Algorítmico", "Físico Newtoniano",
    "Programador Cuántico", "Ingeniero Gaussiano", "Biólogo Computacional",
    "Analista Discreto", "Estadístico Bayesiano", "Geómetra Euclidiano"
]

@cells_bp.route('/matchmaking/trigger', methods=['POST'])
def trigger_matchmaking():
    """
    Runs the clustering algorithm:
    - Finds students with the same Course AND same Weakness Tema AND same Sede.
    - Groups them if count between 3 and 6.
    - Creates a CelulaEstudio and AlumnoCelula invitations with pseudonyms.
    """
    try:
        # 1. Fetch all student weaknesses
        debilidades = AlumnoDebilidad.query.all()
        
        # Group students by (id_curso, tema_central, sede)
        groups = {}
        for deb in debilidades:
            alumno = Alumno.query.get(deb.id_alumno)
            if not alumno:
                continue
            key = (deb.id_curso, deb.tema_central, alumno.sede_codigo)
            if key not in groups:
                groups[key] = []
            if deb.id_alumno not in groups[key]:
                groups[key].append(deb.id_alumno)
                
        cells_created = 0
        
        # 2. Iterate groups to find clusters between 3 and 6
        for key, student_ids in groups.items():
            id_curso, tema_central, sede = key
            
            # Check size limits
            if 3 <= len(student_ids) <= 6:
                # Check if a cell already exists for this topic and curso
                existing = CelulaEstudio.query.filter_by(
                    id_curso=id_curso,
                    tema_central=tema_central,
                    activo=True
                ).first()
                
                if existing:
                    continue
                    
                # Create study cell
                virtual_room = f"https://meet.jit.si/TutorUNFV-Celula-{id_curso}-{random.randint(1000, 9999)}"
                physical_spot = f"Mesa {random.randint(1, 10)} - Biblioteca de la Sede {sede}"
                
                cell = CelulaEstudio(
                    id_curso=id_curso,
                    tema_comun=tema_central,
                    ubicacion_reunion=physical_spot,
                    enlace_virtual=virtual_room,
                    activo=True
                )
                db.session.add(cell)
                db.session.flush() # get id_celula
                
                # Assign members
                used_pseuds = set()
                for sid in student_ids:
                    # Select unique pseudonym
                    pseud = random.choice([p for p in PSEUDONYMS if p not in used_pseuds])
                    used_pseuds.add(pseud)
                    
                    member = AlumnoCelula(
                        id_celula=cell.id_celula,
                        id_alumno=sid,
                        pseudonimo=pseud,
                        aceptado=False
                    )
                    db.session.add(member)
                    
                cells_created += 1
                
        db.session.commit()
        return jsonify({
            "message": f"Algoritmo de clustering ejecutado con éxito. Se crearon {cells_created} nuevas células.",
            "celulas_creadas": cells_created
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@cells_bp.route('/invitations/<id_alumno>', methods=['GET'])
def get_invitations(id_alumno):
    """
    Returns pending study cell invitations for a student.
    Anonymized profiles are displayed using pseudonyms.
    """
    invitations = AlumnoCelula.query.filter_by(id_alumno=id_alumno, aceptado=False).all()
    
    result = []
    for inv in invitations:
        cell = inv.celula
        if not cell or not cell.activo:
            continue
            
        course = Curso.query.get(cell.id_curso)
        course_name = course.nombre_curso if course else "Curso Desconocido"
        
        # Get count of other members and list of their pseudonyms
        other_members = AlumnoCelula.query.filter(
            AlumnoCelula.id_celula == cell.id_celula,
            AlumnoCelula.id_alumno != id_alumno
        ).all()
        
        pseuds_list = [m.pseudonimo for m in other_members]
        
        result.append({
            "id_registro": inv.id_registro,
            "id_celula": cell.id_celula,
            "curso_nombre": course_name,
            "tema_comun": cell.tema_comun,
            "mi_pseudonimo": inv.pseudonimo,
            "miembros_cantidad": len(other_members) + 1,
            "miembros_pseudonimos": pseuds_list,
            "sede": Alumno.query.get(id_alumno).sede_codigo
        })
        
    return jsonify(result), 200

@cells_bp.route('/invitations/<int:id_registro>/accept', methods=['POST'])
def accept_invitation(id_registro):
    member = AlumnoCelula.query.get(id_registro)
    if not member:
        return jsonify({"error": "Invitación no encontrada"}), 404
        
    member.aceptado = True
    try:
        db.session.commit()
        
        # Log event
        log = AlumnoEvento(
            id_alumno=member.id_alumno,
            tipo_evento="celula_aceptada",
            metadata_json=json.dumps({"id_celula": member.id_celula})
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({"message": "Invitación aceptada con éxito", "id_celula": member.id_celula}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@cells_bp.route('/invitations/<int:id_registro>/reject', methods=['POST'])
def reject_invitation(id_registro):
    member = AlumnoCelula.query.get(id_registro)
    if not member:
        return jsonify({"error": "Invitación no encontrada"}), 404
        
    try:
        db.session.delete(member)
        db.session.commit()
        return jsonify({"message": "Invitación rechazada con éxito"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@cells_bp.route('/active/<id_alumno>', methods=['GET'])
def get_active_cells(id_alumno):
    """
    Returns active accepted study cells.
    Includes real names of users who accepted, and the AI Suggested syllabus review topics.
    """
    memberships = AlumnoCelula.query.filter_by(id_alumno=id_alumno, aceptado=True).all()
    
    result = []
    for mem in memberships:
        cell = mem.celula
        if not cell or not cell.activo:
            continue
            
        course = Curso.query.get(cell.id_curso)
        course_name = course.nombre_curso if course else "Curso Desconocido"
        
        # Get all members of this cell
        all_members = AlumnoCelula.query.filter_by(id_celula=cell.id_celula).all()
        
        members_data = []
        for m in all_members:
            al = Alumno.query.get(m.id_alumno)
            if not al:
                continue
                
            # If the member has accepted, reveal their real name, otherwise keep anonymous pseudonym
            name = al.nombre if m.aceptado else f"Miembro Anónimo ({m.pseudonimo})"
            members_data.append({
                "id_alumno": m.id_alumno,
                "nombre": name,
                "pseudonimo": m.pseudonimo,
                "aceptado": m.aceptado
            })
            
        # Get AI Suggested study checklist (3 items)
        ai_topics = get_ai_suggested_syllabus(cell.id_curso, cell.tema_comun)
        
        result.append({
            "id_celula": cell.id_celula,
            "curso_nombre": course_name,
            "id_curso": cell.id_curso,
            "tema_comun": cell.tema_comun,
            "mi_pseudonimo": mem.pseudonimo,
            "ubicacion_reunion": cell.ubicacion_reunion,
            "enlace_virtual": cell.enlace_virtual,
            "miembros": members_data,
            "temario_sugerido": ai_topics
        })
        
    return jsonify(result), 200

def get_ai_suggested_syllabus(id_curso, tema_comun):
    """
    Generates 3 specific review points for the group based on their common weakness.
    Uses Gemini to synthesize study subtopics.
    """
    system_prompt = (
        "Eres un tutor de IA de la UNFV. Genera una lista corta de 3 puntos específicos "
        "o subtemas de repaso que un grupo de estudio debe resolver en conjunto, basándote en el tema "
        "principal en el que todos tienen dificultades. "
        "Devuelve estrictamente un JSON válido con la siguiente estructura:\n"
        "{\n"
        "  \"review_points\": [\n"
        "    \"1. Subtema de repaso (ej: Practicar la reducción de filas en Gauss-Jordan)\",\n"
        "    \"2. Segundo subtema de repaso\",\n"
        "    \"3. Tercer subtema de repaso\"\n"
        "  ]\n"
        "}"
    )
    user_prompt = f"Curso: {id_curso}\nTema común de falla: {tema_comun}"
    
    try:
        def review_op(client, model_name):
            return client.models.generate_content(
                model=model_name,
                contents=[system_prompt, user_prompt],
                config=_gtypes_new.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
        response = gemini_manager.execute_with_retry(review_op)
        data = json.loads(response.text)
        return data.get("review_points", [
            f"1. Definición conceptual de {tema_comun}",
            f"2. Resolución de ejercicios prácticos básicos",
            f"3. Simulación conjunta de preguntas de examen"
        ])
    except Exception:
        # Fallback
        return [
            f"1. Definición conceptual de {tema_comun}",
            f"2. Resolución de ejercicios prácticos básicos",
            f"3. Simulación conjunta de preguntas de examen"
        ]
