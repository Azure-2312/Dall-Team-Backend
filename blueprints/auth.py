from flask import Blueprint, jsonify, request, make_response
from flask_jwt_extended import (
    create_access_token, create_refresh_token, 
    set_refresh_cookies, jwt_required, get_jwt_identity, get_jwt
)
from functools import wraps
from models import db, Usuario, Alumno, Docente
import os
import re
import unicodedata
import random
import string
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
import json

def normalizar_nombre(nombre):
    if not nombre:
        return ""
    nombre = nombre.lower().strip()
    nombre = nombre.replace("ñ", "n")
    nombre = "".join(
        c for c in unicodedata.normalize('NFD', nombre)
        if unicodedata.category(c) != 'Mn'
    )
    nombre = re.sub(r'[^a-z0-9\s]', '', nombre)
    return nombre

def generar_prefijos_validos(nombre_completo):
    nombre_norm = normalizar_nombre(nombre_completo)
    parts = [p for p in nombre_norm.split() if p]
    if len(parts) < 2:
        return []
    
    first_name = parts[0]
    first_surname = parts[-2]
    second_surname = parts[-1]
    
    prefix_1 = first_name[0] + first_surname
    prefix_2 = first_name[0] + first_surname + second_surname[0]
    
    return [prefix_1, prefix_2]

def enviar_correo_codigo(email, code):
    codes_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'recovery_codes.json')
    os.makedirs(os.path.dirname(codes_file), exist_ok=True)
    
    codes_data = {}
    if os.path.exists(codes_file):
        try:
            with open(codes_file, 'r') as f:
                codes_data = json.load(f)
        except Exception:
            pass
            
    codes_data[email] = {
        "code": code,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    try:
        with open(codes_file, 'w') as f:
            json.dump(codes_data, f, indent=4)
    except Exception as e:
        print(f"Error escribiendo en recovery_codes.json: {e}")
        
    print(f"\n[RECOVERY CODE FOR {email}]: {code}\n", flush=True)
    
    sender = "apazamiguel88@gmail.com"
    mail_pass = os.environ.get("SMTP_PASSWORD") or os.environ.get("MAIL_PASSWORD")
    
    if not mail_pass:
        print("SMTP password not configured. Simulated recovery email written to recovery_codes.json", flush=True)
        return False
        
    msg = MIMEText(f"Tu codigo de recuperacion de contrasena para el Tutor Inteligente UNFV es: {code}\n\nEste codigo expira en 15 minutos.")
    msg['Subject'] = 'Codigo de Recuperacion - Tutor Inteligente UNFV'
    msg['From'] = sender
    msg['To'] = email
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender, mail_pass)
        server.sendmail(sender, email, msg.as_string())
        server.quit()
        print(f"Email sent successfully to {email}", flush=True)
        return True
    except Exception as e:
        print(f"Failed to send email to {email}: {str(e)}", flush=True)
        return False

auth_bp = Blueprint('auth', __name__)

def role_required(allowed_roles):
    """
    Custom decorator to restrict endpoints to specific roles.
    Intercepts claims, checks role value, and outputs HTTP 403 if unauthorized.
    """
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            user_role = claims.get("role")
            if user_role not in allowed_roles:
                return jsonify({"error": f"Forbidden: Acceso restringido a roles {allowed_roles}"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    POST /api/auth/login
    Authenticates user, verifies corporate institutional domain,
    and returns JWT tokens and profile credentials.
    """
    data = request.json
    if not data or not all(k in data for k in ('email_or_username', 'password')):
        return jsonify({"error": "Faltan credenciales obligatorias: email_or_username, password"}), 400
        
    identifier = data['email_or_username']
    password = data['password']
    
    # 1. Resolve user by username or email
    user = Usuario.query.filter((Usuario.email == identifier) | (Usuario.username == identifier)).first()
    
    if not user or not user.check_password(password):
        return jsonify({"error": "Credenciales inválidas"}), 401
        
    if not user.activo:
        return jsonify({"error": "Usuario inactivo en el sistema institucional"}), 403
        
    # 2. Check corporate email domain
    if not user.email.endswith('@unfv.edu.pe'):
        return jsonify({"error": "Acceso restringido: requiere correo institucional UNFV (@unfv.edu.pe)"}), 403
        
    # 3. Create tokens with embedded claims
    claims = {
        "role": user.rol,
        "email": user.email,
        "username": user.username
    }
    
    # Add profile key depending on role
    profile_id = None
    profile_name = user.username
    sede = None
    facultad = None
    escuela = None
    ciclo = None
    tipo_docente = None
    if user.rol == 'Estudiante':
        profile = Alumno.query.filter_by(id_usuario=user.id_usuario).first()
        if profile:
            profile_id = profile.id_alumno
            profile_name = profile.nombre
            sede = profile.sede_codigo
            facultad = profile.facultad
            escuela = profile.escuela
            ciclo = profile.ciclo
    elif user.rol == 'Docente':
        profile = Docente.query.filter_by(id_usuario=user.id_usuario).first()
        if profile:
            profile_id = profile.id_docente
            profile_name = profile.nombre_docente
            sede = profile.sede_codigo
            facultad = profile.facultad
            escuela = profile.escuela_principal
            tipo_docente = profile.tipo_docente

    access_token = create_access_token(identity=user.id_usuario, additional_claims=claims)
    refresh_token = create_refresh_token(identity=user.id_usuario)
    
    # 4. Return access token and set refresh token in HttpOnly secure cookie
    response_payload = {
        "access_token": access_token,
        "usuario": {
            "id_usuario": user.id_usuario,
            "username": user.username,
            "email": user.email,
            "rol": user.rol,
            "profile_id": profile_id,
            "nombre": profile_name,
            "foto_perfil": user.foto_perfil,
            "sede": sede,
            "facultad": facultad,
            "escuela": escuela,
            "ciclo": ciclo,
            "tipo_docente": tipo_docente,
            "gemini_api_key": os.environ.get('GEMINI_API_KEY', '')
        }
    }
    
    response = make_response(jsonify(response_payload), 200)
    set_refresh_cookies(response, refresh_token)
    return response

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    POST /api/auth/refresh
    Generates a new access token from a valid refresh token cookie.
    """
    identity = get_jwt_identity()
    user = Usuario.query.get(identity)
    
    if not user or not user.activo:
        return jsonify({"error": "Usuario inválido o inactivo"}), 401
        
    claims = {
        "role": user.rol,
        "email": user.email,
        "username": user.username
    }
    
    access_token = create_access_token(identity=identity, additional_claims=claims)
    return jsonify({"access_token": access_token}), 200

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_current_profile():
    """GET /api/auth/profile"""
    identity = get_jwt_identity()
    user = Usuario.query.get(identity)
    
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
        
    profile_payload = {
        "id_usuario": user.id_usuario,
        "username": user.username,
        "email": user.email,
        "rol": user.rol,
        "foto_perfil": user.foto_perfil,
        "gemini_api_key": os.environ.get('GEMINI_API_KEY', '')
    }
    
    if user.rol == 'Estudiante':
        profile = Alumno.query.filter_by(id_usuario=user.id_usuario).first()
        if profile:
            profile_payload["alumno"] = {
                "id_alumno": profile.id_alumno,
                "nombre": profile.nombre,
                "sede": profile.sede_codigo,
                "facultad": profile.facultad,
                "escuela": profile.escuela,
                "ciclo": profile.ciclo
            }
    elif user.rol == 'Docente':
        profile = Docente.query.filter_by(id_usuario=user.id_usuario).first()
        if profile:
            profile_payload["docente"] = {
                "id_docente": profile.id_docente,
                "nombre_docente": profile.nombre_docente,
                "sede": profile.sede_codigo,
                "facultad": profile.facultad,
                "escuela_principal": profile.escuela_principal,
                "correo": profile.correo_institucional,
                "tipo_docente": profile.tipo_docente
            }
            
    return jsonify(profile_payload), 200

# Endpoint to register Student
@auth_bp.route('/register/student', methods=['POST'])
def register_student():
    data = request.json
    if not data or not all(k in data for k in ('nombres', 'apellidos', 'email', 'id_alumno', 'password', 'sede_codigo', 'facultad', 'escuela')):
        return jsonify({"error": "Faltan campos obligatorios para el registro de alumno"}), 400
        
    nombres = data['nombres'].strip()
    apellidos = data['apellidos'].strip()
    email = data['email'].strip()
    id_alumno = data['id_alumno'].strip()
    password = data['password']
    sede_codigo = data['sede_codigo'].strip()
    facultad = data['facultad'].strip()
    escuela = data['escuela'].strip()
    
    if not email.endswith('@unfv.edu.pe'):
        return jsonify({"error": "El correo debe pertenecer al dominio institucional (@unfv.edu.pe)"}), 400
        
    if not re.match(r'^\d{10}$', id_alumno):
        return jsonify({"error": "El código de alumno debe constar de exactamente 10 dígitos numéricos"}), 400
        
    email_prefix = email.split('@')[0]
    if email_prefix != id_alumno:
        return jsonify({"error": f"El correo institucional para el código {id_alumno} debe ser {id_alumno}@unfv.edu.pe"}), 400
        
    if Usuario.query.filter_by(email=email).first() or Usuario.query.filter_by(username=id_alumno).first():
        return jsonify({"error": "El correo o código de alumno ya se encuentra registrado"}), 400
        
    try:
        user = Usuario(
            username=id_alumno,
            email=email,
            rol='Estudiante',
            activo=True
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        alumno = Alumno(
            id_alumno=id_alumno,
            id_usuario=user.id_usuario,
            nombres=nombres,
            apellidos=apellidos,
            sede_codigo=sede_codigo,
            facultad=facultad,
            escuela=escuela
        )
        db.session.add(alumno)
        
        # Auto-enrollment removed per user request
            
        db.session.commit()
        
        return jsonify({"message": "Alumno registrado con éxito"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500



# Endpoint to update profile
@auth_bp.route('/profile/update', methods=['POST'])
@jwt_required()
def update_profile():
    identity = get_jwt_identity()
    user = Usuario.query.get(identity)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
        
    data = request.json
    if not data:
        return jsonify({"error": "No se recibieron datos para actualizar"}), 400
        
    try:
        if 'foto_perfil' in data:
            user.foto_perfil = data['foto_perfil']
            
        if 'new_password' in data and data['new_password']:
            user.set_password(data['new_password'])
            
        if 'gemini_api_key' in data:
            key = data['gemini_api_key'].strip()
            os.environ['GEMINI_API_KEY'] = key
            
            # Write to the backend/.env file
            env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
            lines = []
            key_written = False
            if os.path.exists(env_path):
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line_strip = line.strip()
                        if line_strip.startswith('GEMINI_API_KEY='):
                            lines.append(f"GEMINI_API_KEY={key}\n")
                            key_written = True
                        else:
                            lines.append(line)
            
            if not key_written:
                lines.append(f"\nGEMINI_API_KEY={key}\n")
                
            with open(env_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
        db.session.commit()
        return jsonify({"message": "Perfil actualizado correctamente"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# Password Recovery Endpoints
@auth_bp.route('/recovery/request', methods=['POST'])
def recovery_request():
    data = request.json
    if not data or 'email' not in data:
        return jsonify({"error": "Debe proporcionar el correo institucional"}), 400
        
    email = data['email'].strip()
    user = Usuario.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "El correo ingresado no se encuentra registrado en la plataforma"}), 404
        
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    try:
        user.codigo_recuperacion = code
        user.recuperacion_expiracion = datetime.utcnow() + timedelta(minutes=15)
        db.session.commit()
        
        enviar_correo_codigo(email, code)
        
        return jsonify({"message": "Código de verificación generado y enviado en segundo plano"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@auth_bp.route('/recovery/verify', methods=['POST'])
def recovery_verify():
    data = request.json
    if not data or not all(k in data for k in ('email', 'code')):
        return jsonify({"error": "Faltan datos obligatorios: email, code"}), 400
        
    email = data['email'].strip()
    code = data['code'].strip().upper()
    
    user = Usuario.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
        
    if not user.codigo_recuperacion or user.codigo_recuperacion != code:
        return jsonify({"error": "El código ingresado es incorrecto"}), 400
        
    if datetime.utcnow() > user.recuperacion_expiracion:
        return jsonify({"error": "El código ha expirado. Solicite uno nuevo"}), 400
        
    return jsonify({"message": "Código verificado con éxito"}), 200

@auth_bp.route('/recovery/reset', methods=['POST'])
def recovery_reset():
    data = request.json
    if not data or not all(k in data for k in ('email', 'code', 'new_password')):
        return jsonify({"error": "Faltan datos obligatorios"}), 400
        
    email = data['email'].strip()
    code = data['code'].strip().upper()
    new_password = data['new_password']
    
    user = Usuario.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
        
    if not user.codigo_recuperacion or user.codigo_recuperacion != code:
        return jsonify({"error": "El código ingresado es incorrecto"}), 400
        
    if datetime.utcnow() > user.recuperacion_expiracion:
        return jsonify({"error": "El código ha expirado"}), 400
        
    try:
        user.set_password(new_password)
        user.codigo_recuperacion = None
        user.recuperacion_expiracion = None
        db.session.commit()
        return jsonify({"message": "Contraseña restablecida con éxito. Ya puede iniciar sesión"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
