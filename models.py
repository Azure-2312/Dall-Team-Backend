from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import TypeDecorator, TEXT
from werkzeug.security import generate_password_hash, check_password_hash
import json
from datetime import datetime

db = SQLAlchemy()

class SafeVector(TypeDecorator):
    """
    A custom type that uses pgvector's Vector type on PostgreSQL (if enabled)
    and falls back to TEXT (storing JSON-serialized lists) on SQLite or when pgvector is disabled.
    """
    impl = TEXT
    cache_ok = True

    def load_dialect_impl(self, dialect):
        import os
        if dialect.name == 'postgresql' and os.environ.get('DISABLE_PGVECTOR') != 'true':
            try:
                from pgvector.sqlalchemy import Vector
                return dialect.type_descriptor(Vector(1536))
            except ImportError:
                return dialect.type_descriptor(TEXT())
        else:
            return dialect.type_descriptor(TEXT())

    def process_bind_param(self, value, dialect):
        import os
        if value is None:
            return None
        if dialect.name == 'postgresql' and os.environ.get('DISABLE_PGVECTOR') != 'true':
            return value
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        import os
        if value is None:
            return None
        if dialect.name == 'postgresql' and os.environ.get('DISABLE_PGVECTOR') != 'true':
            return value
        try:
            return json.loads(value)
        except Exception:
            return []

# 1. Base Users Table (RBAC Credentials)
class Usuario(db.Model):
    __tablename__ = 'usuarios'
    
    id_usuario = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), nullable=False) # 'Estudiante', 'Docente', 'Admin'
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    foto_perfil = db.Column(db.Text, nullable=True)
    codigo_recuperacion = db.Column(db.String(10), nullable=True)
    recuperacion_expiracion = db.Column(db.DateTime, nullable=True)
    cargo = db.Column(db.String(100), nullable=True)
    facultad = db.Column(db.String(100), nullable=True)
    
    __table_args__ = (
        db.CheckConstraint("rol IN ('Estudiante', 'Docente', 'Admin')", name='check_rol_usuario'),
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# 2. Alumnos Table (Extends Usuario)
class Alumno(db.Model):
    __tablename__ = 'alumnos'
    
    id_alumno = db.Column(db.String(10), primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario', ondelete='CASCADE'), nullable=True)
    nombres = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    sede_codigo = db.Column(db.String(50), nullable=False) # e.g. Central, El Agustino
    facultad = db.Column(db.String(100), nullable=False) # e.g. FIIS, Economicas
    escuela = db.Column(db.String(100), nullable=False) # e.g. Sistemas, Industrial
    ciclo = db.Column(db.Integer, default=1, nullable=False)
    cursos_inscritos = db.Column(db.JSON, default=list, nullable=True)
    sancionado = db.Column(db.Boolean, default=False, nullable=False)
    
    usuario = db.relationship('Usuario', backref=db.backref('alumno_perfil', uselist=False, cascade='all,delete'))

    @property
    def nombre(self):
        return f"{self.nombres} {self.apellidos}"

    @property
    def correo_institucional(self):
        return self.usuario.email if self.usuario else ""

# 3. Docentes Table (Extends Usuario)
class Docente(db.Model):
    __tablename__ = 'docentes'
    
    id_docente = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario', ondelete='CASCADE'), nullable=True)
    nombres = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    sede_codigo = db.Column(db.String(50), nullable=True)
    facultad = db.Column(db.String(100), nullable=False)
    escuela_principal = db.Column(db.String(100), nullable=False)
    correo_institucional = db.Column(db.String(100), nullable=False)
    tipo_docente = db.Column(db.String(50), nullable=True) # 'Permanente' o 'Contratado'
    bloques_disponibles = db.Column(db.JSON, nullable=True) # Permanent tutoring hours defined by docent
    
    usuario = db.relationship('Usuario', backref=db.backref('docente_perfil', uselist=False, cascade='all,delete'))

    @property
    def nombre_docente(self):
        return f"{self.nombres} {self.apellidos}"

# 4. Cursos Table (Curriculum & General Catalog)
class Curso(db.Model):
    __tablename__ = 'cursos'
    
    id_curso = db.Column(db.String(10), primary_key=True)
    nombre_curso = db.Column(db.String(150), nullable=False)
    escuela = db.Column(db.String(100), nullable=False)
    ciclo_teorico = db.Column(db.Integer, nullable=False) # 1 to 10
    creditos = db.Column(db.Integer, nullable=False)
    id_prerrequisito = db.Column(db.String(10), db.ForeignKey('cursos.id_curso'), nullable=True)
    nombre_prerrequisito = db.Column(db.String(150), nullable=True) # Prerequisite name inherited from parent course
    tipo_estudio = db.Column(db.String(50), default='General', nullable=False) # 'General', 'Especifico', 'Especializado'
    tipo_curso = db.Column(db.String(50), default='Estándar', nullable=False) # 'Estándar', 'Electivo'
    es_electivo = db.Column(db.Boolean, default=False, nullable=False) # Kept for backward compatibility
    
    prerrequisito = db.relationship('Curso', remote_side=[id_curso], backref='dependientes')

# 5. Historial Academico Table
class HistorialAcademico(db.Model):
    __tablename__ = 'historial_academico'
    
    id_historial = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_alumno = db.Column(db.String(10), db.ForeignKey('alumnos.id_alumno', ondelete='CASCADE'), nullable=False)
    id_curso = db.Column(db.String(10), db.ForeignKey('cursos.id_curso', ondelete='CASCADE'), nullable=False)
    estado = db.Column(db.String(20), nullable=False) # 'Aprobado', 'Jalado', 'Cursando'
    
    __table_args__ = (
        db.CheckConstraint("estado IN ('Aprobado', 'Jalado', 'Cursando')", name='check_estado_historial'),
    )
    
    alumno = db.relationship('Alumno', backref=db.backref('historial', lazy=True, cascade='all,delete-orphan'))
    curso = db.relationship('Curso', backref=db.backref('historiales', lazy=True))

# 6. Silabos Timeline Table
class SilaboTimeline(db.Model):
    __tablename__ = 'silabos_timeline'
    
    id_silabo = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_curso = db.Column(db.String(10), db.ForeignKey('cursos.id_curso', ondelete='CASCADE'), nullable=False)
    semana_numero = db.Column(db.Integer, nullable=False) # 1 to 16
    tema_central = db.Column(db.Text, nullable=False)
    lecturas_obligatorias = db.Column(db.Text, nullable=True)
    contenido_vector = db.Column(SafeVector, nullable=True)
    
    __table_args__ = (
        db.CheckConstraint("semana_numero BETWEEN 1 AND 16", name='check_semana_limite'),
    )
    
    curso = db.relationship('Curso', backref=db.backref('silabos', lazy=True))

# 7. Citas de Tutoria Humana (Appointments Booking)
class CitaTutoria(db.Model):
    __tablename__ = 'citas_tutoria'
    
    id_cita = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_alumno = db.Column(db.String(10), db.ForeignKey('alumnos.id_alumno', ondelete='CASCADE'), nullable=False)
    id_docente = db.Column(db.Integer, db.ForeignKey('docentes.id_docente', ondelete='CASCADE'), nullable=False)
    id_curso = db.Column(db.String(10), db.ForeignKey('cursos.id_curso', ondelete='CASCADE'), nullable=False)
    fecha_hora = db.Column(db.DateTime, nullable=False)
    modalidad = db.Column(db.String(20), nullable=False) # 'Presencial', 'Virtual'
    ubicacion_detalle = db.Column(db.String(150), nullable=True) # Pabellon cubicle or Teams link
    estado_cita = db.Column(db.String(20), default='Pendiente', nullable=False) # 'Pendiente', 'Confirmada', 'Cancelada', 'Asistida'
    diagnostico_ia_previo = db.Column(db.Text, nullable=True)
    
    __table_args__ = (
        db.CheckConstraint("modalidad IN ('Presencial', 'Virtual')", name='check_modalidad_cita'),
        db.CheckConstraint("estado_cita IN ('Pendiente', 'Confirmada', 'Cancelada', 'Asistida')", name='check_estado_cita'),
    )
    
    alumno = db.relationship('Alumno', backref=db.backref('citas', lazy=True, cascade='all,delete-orphan'))
    docente = db.relationship('Docente', backref=db.backref('citas', lazy=True, cascade='all,delete-orphan'))
    curso = db.relationship('Curso', backref=db.backref('citas', lazy=True))

# 8. RAG Ingestion Audit Logging
class AuditoriaRAG(db.Model):
    __tablename__ = 'auditoria_rag'
    
    id_log = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario_admin = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario', ondelete='SET NULL'), nullable=True)
    tipo_documento = db.Column(db.String(50), nullable=False) # 'Sílabo', 'Malla', 'Calendario', 'Biblioteca'
    origen_documento = db.Column(db.String(150), nullable=False)
    registros_afectados = db.Column(db.Integer, nullable=False)
    fecha_indexacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    admin = db.relationship('Usuario', backref=db.backref('logs_rag', lazy=True))

# 9. Alumno Debilidades
class AlumnoDebilidad(db.Model):
    __tablename__ = 'alumno_debilidades'
    
    id_debilidad = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_alumno = db.Column(db.String(10), db.ForeignKey('alumnos.id_alumno', ondelete='CASCADE'), nullable=False)
    id_curso = db.Column(db.String(10), db.ForeignKey('cursos.id_curso', ondelete='CASCADE'), nullable=False)
    tema_central = db.Column(db.String(255), nullable=False)
    errores_count = db.Column(db.Integer, default=1, nullable=False)
    
    alumno = db.relationship('Alumno', backref=db.backref('debilidades', lazy=True, cascade='all,delete-orphan'))
    curso = db.relationship('Curso', backref=db.backref('debilidades', lazy=True))


# 10. Solicitudes de Tutoría
class SolicitudTutoria(db.Model):
    __tablename__ = 'solicitudes_tutoria'
    
    id_solicitud = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_alumno = db.Column(db.String(10), db.ForeignKey('alumnos.id_alumno', ondelete='CASCADE'), nullable=False)
    id_curso = db.Column(db.String(10), db.ForeignKey('cursos.id_curso', ondelete='CASCADE'), nullable=False)
    cantidad_estudiantes = db.Column(db.Integer, nullable=False)
    archivo_solicitud_path = db.Column(db.String(255), nullable=True)
    estado = db.Column(db.String(30), default='Pendiente', nullable=False) # 'Pendiente', 'Aprobado', 'Rechazado', 'Cancelación Solicitada', 'Cancelado'
    motivo_rechazo = db.Column(db.Text, nullable=True)
    
    # Asignaciones al aprobar
    id_docente = db.Column(db.Integer, db.ForeignKey('docentes.id_docente', ondelete='SET NULL'), nullable=True)
    dia = db.Column(db.String(20), nullable=True)
    hora = db.Column(db.String(20), nullable=True)
    link_llamada = db.Column(db.String(255), nullable=True)
    escuela = db.Column(db.String(100), nullable=True)
    
    # Cancelación por parte del docente
    motivo_cancelacion_docente = db.Column(db.Text, nullable=True)
    archivo_cancelacion_path = db.Column(db.String(255), nullable=True)
    
    fecha_solicitud = db.Column(db.DateTime, default=datetime.utcnow)
    confirmada = db.Column(db.Boolean, default=False, nullable=False)
    
    alumno = db.relationship('Alumno', backref=db.backref('solicitudes_tutoria', lazy=True, cascade='all,delete-orphan'))
    curso = db.relationship('Curso', backref=db.backref('solicitudes_tutoria', lazy=True))
    docente = db.relationship('Docente', backref=db.backref('solicitudes_tutoria', lazy=True))


# 11. Alumnos Unidos a Tutoría Grupal
class AlumnoUnidoTutoria(db.Model):
    __tablename__ = 'alumnos_unidos_tutoria'
    
    id_registro = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_solicitud = db.Column(db.Integer, db.ForeignKey('solicitudes_tutoria.id_solicitud', ondelete='CASCADE'), nullable=False)
    id_alumno = db.Column(db.String(10), db.ForeignKey('alumnos.id_alumno', ondelete='CASCADE'), nullable=False)
    fecha_union = db.Column(db.DateTime, default=datetime.utcnow)
    
    alumno = db.relationship('Alumno', backref=db.backref('uniones_tutoria', lazy=True))
    solicitud = db.relationship('SolicitudTutoria', backref=db.backref('alumnos_unidos', lazy=True, cascade='all,delete-orphan'))


# 12. General Activity Log for Admins
class AuditoriaActividad(db.Model):
    __tablename__ = 'auditoria_actividad'
    
    id_log = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario', ondelete='SET NULL'), nullable=True)
    username = db.Column(db.String(50), nullable=True)
    rol = db.Column(db.String(20), nullable=True)
    accion = db.Column(db.String(100), nullable=False)
    detalles = db.Column(db.Text, nullable=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    
    usuario = db.relationship('Usuario', backref=db.backref('logs_actividad', lazy=True))


# 13. Apuntes y Pizarra Digital del Estudiante
class ApunteEstudiante(db.Model):
    __tablename__ = 'apuntes_estudiantes'
    
    id_apunte = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_alumno = db.Column(db.String(10), db.ForeignKey('alumnos.id_alumno', ondelete='CASCADE'), nullable=False)
    id_curso = db.Column(db.String(10), db.ForeignKey('cursos.id_curso', ondelete='CASCADE'), nullable=False)
    semana = db.Column(db.Integer, nullable=True)
    nombre_hoja = db.Column(db.String(100), nullable=True)
    texto_notas = db.Column(db.Text, default='', nullable=False)
    canvas_data = db.Column(db.Text, nullable=True) # transparent Base64 PNG drawings layer
    background_url = db.Column(db.Text, nullable=True) # uploaded background image/file path/url
    fecha_modificacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    alumno = db.relationship('Alumno', backref=db.backref('apuntes_cursos', lazy=True, cascade='all,delete-orphan'))
    curso = db.relationship('Curso', backref=db.backref('apuntes_estudiantes', lazy=True, cascade='all,delete-orphan'))

# 12b. ReporteTutoria Table - incident reports after sessions
class ReporteTutoria(db.Model):
    __tablename__ = 'reportes_tutoria'
    id_reporte = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_solicitud = db.Column(db.Integer, db.ForeignKey('solicitudes_tutoria.id_solicitud', ondelete='CASCADE'), nullable=False)
    reportado_por = db.Column(db.String(10), nullable=False)  # 'docente' or 'alumno'
    tipo_reporte = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    fecha_reporte = db.Column(db.DateTime, default=datetime.utcnow)


# 14. AlumnoEvento Table - user events tracking
class AlumnoEvento(db.Model):
    __tablename__ = 'alumno_eventos'
    id_evento = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_alumno = db.Column(db.String(10), db.ForeignKey('alumnos.id_alumno', ondelete='CASCADE'), nullable=False)
    tipo_evento = db.Column(db.String(100), nullable=False)
    metadata_json = db.Column(db.Text, nullable=True)
    fecha_evento = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    alumno = db.relationship('Alumno', backref=db.backref('eventos', lazy=True, cascade='all,delete-orphan'))


# 15. ExamenObjetivo Table - exam objectives for study routes
class ExamenObjetivo(db.Model):
    __tablename__ = 'examenes_objetivos'
    id_examen = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_alumno = db.Column(db.String(10), db.ForeignKey('alumnos.id_alumno', ondelete='CASCADE'), nullable=False)
    id_curso = db.Column(db.String(10), db.ForeignKey('cursos.id_curso', ondelete='CASCADE'), nullable=False)
    fecha_limite = db.Column(db.DateTime, nullable=False)
    nivel_dificultad = db.Column(db.Integer, default=3, nullable=False) # 1 to 5
    temas_asociados = db.Column(db.JSON, default=list, nullable=True) # list of strings
    
    alumno = db.relationship('Alumno', backref=db.backref('examenes_objetivos', lazy=True, cascade='all,delete-orphan'))
    curso = db.relationship('Curso', backref=db.backref('examenes_objetivos', lazy=True))


# 16. MicroTareaDiaria Table - individual daily tasks of a study route
class MicroTareaDiaria(db.Model):
    __tablename__ = 'micro_tareas_diarias'
    id_tarea = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_examen = db.Column(db.Integer, db.ForeignKey('examenes_objetivos.id_examen', ondelete='CASCADE'), nullable=False)
    fecha_asignada = db.Column(db.Date, nullable=False)
    meta_texto = db.Column(db.Text, nullable=False)
    tiempo_estimado = db.Column(db.Integer, nullable=False) # in minutes
    completado = db.Column(db.Boolean, default=False, nullable=False)
    
    examen = db.relationship('ExamenObjetivo', backref=db.backref('tareas_diarias', lazy=True, cascade='all,delete-orphan'))


# 17. PreguntaComunitaria Table - crowdsourced exam questions
class PreguntaComunitaria(db.Model):
    __tablename__ = 'preguntas_comunitarias'
    id_pregunta = db.Column(db.Integer, primary_key=True, autoincrement=True)
    aportante_id = db.Column(db.String(10), db.ForeignKey('alumnos.id_alumno', ondelete='SET NULL'), nullable=True)
    facultad = db.Column(db.String(100), nullable=False)
    id_curso = db.Column(db.String(10), db.ForeignKey('cursos.id_curso', ondelete='CASCADE'), nullable=False)
    profesor = db.Column(db.String(100), nullable=True)
    imagen_path = db.Column(db.String(255), nullable=True)
    pregunta_texto = db.Column(db.Text, nullable=False)
    respuesta_correcta = db.Column(db.Text, nullable=False)
    score_confianza = db.Column(db.Float, default=0.0, nullable=False)
    estado = db.Column(db.String(30), default='En Revision', nullable=False) # 'Publicada', 'En Revision'
    nivel_dificultad = db.Column(db.String(20), default='Intermedio', nullable=False) # 'Facil', 'Intermedio', 'Dificil'
    temas_clave = db.Column(db.JSON, default=list, nullable=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    aportante = db.relationship('Alumno', backref=db.backref('preguntas_aportadas', lazy=True))
    curso = db.relationship('Curso', backref=db.backref('preguntas_comunitarias', lazy=True))


# 18. CelulaEstudio Table - student study groups
class CelulaEstudio(db.Model):
    __tablename__ = 'celulas_estudio'
    id_celula = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_curso = db.Column(db.String(10), db.ForeignKey('cursos.id_curso', ondelete='CASCADE'), nullable=False)
    tema_comun = db.Column(db.String(255), nullable=False)
    ubicacion_reunion = db.Column(db.String(255), nullable=True) # physical meeting point
    enlace_virtual = db.Column(db.String(255), nullable=True) # temporary virtual room link
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    activo = db.Column(db.Boolean, default=True, nullable=False)
    
    curso = db.relationship('Curso', backref=db.backref('celulas_estudio', lazy=True))


# 19. AlumnoCelula Table - association of students inside study cells
class AlumnoCelula(db.Model):
    __tablename__ = 'alumnos_celula'
    id_registro = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_celula = db.Column(db.Integer, db.ForeignKey('celulas_estudio.id_celula', ondelete='CASCADE'), nullable=False)
    id_alumno = db.Column(db.String(10), db.ForeignKey('alumnos.id_alumno', ondelete='CASCADE'), nullable=False)
    pseudonimo = db.Column(db.String(100), nullable=False)
    aceptado = db.Column(db.Boolean, default=False, nullable=False)
    fecha_union = db.Column(db.DateTime, default=datetime.utcnow)
    
    celula = db.relationship('CelulaEstudio', backref=db.backref('miembros', lazy=True, cascade='all,delete-orphan'))
    alumno = db.relationship('Alumno', backref=db.backref('celulas_participa', lazy=True))


# 20. MaterialRefuerzoDocente Table - reinforcement material shared by teachers
class MaterialRefuerzoDocente(db.Model):
    __tablename__ = 'materiales_refuerzo_docente'
    id_material = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_docente = db.Column(db.Integer, db.ForeignKey('docentes.id_docente', ondelete='CASCADE'), nullable=False)
    id_curso = db.Column(db.String(10), db.ForeignKey('cursos.id_curso', ondelete='CASCADE'), nullable=False)
    tema = db.Column(db.String(255), nullable=False)
    archivo_path = db.Column(db.String(255), nullable=False)
    fecha_subida = db.Column(db.DateTime, default=datetime.utcnow)
    
    docente = db.relationship('Docente', backref=db.backref('materiales_refuerzo', lazy=True, cascade='all,delete-orphan'))
    curso = db.relationship('Curso', backref=db.backref('materiales_refuerzo', lazy=True))


