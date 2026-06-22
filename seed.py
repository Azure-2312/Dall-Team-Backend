from app import create_app
from models import db, Usuario, Alumno, Docente, Curso, HistorialAcademico, SilaboTimeline, CitaTutoria, AuditoriaRAG, AlumnoDebilidad, SolicitudTutoria, AlumnoUnidoTutoria

def seed_database():
    app = create_app()
    
    with app.app_context():
        print("Limpiando base de datos para inicio limpio...")
        db.drop_all()
        db.create_all()
        
        print("Creando credenciales de prueba con dominio institucional (@unfv.edu.pe)...")
        
        # 1. Admin Profile
        u_admin = Usuario(
            username="admin",
            email="admin@unfv.edu.pe",
            rol="Admin",
            activo=True,
            cargo="Administrador General"
        )
        u_admin.set_password("admin")
        db.session.add(u_admin)
        
        # Seeding OTPS Faculty Admins
        otps_admins = [
            ("otps.fdcp", "otps.fdcp@unfv.edu.pe", "Facultad de Derecho y Ciencia Política"),
            ("otps.fccss", "otps.fccss@unfv.edu.pe", "Facultad de Ciencias Sociales"),
            ("otps.fe", "otps.fe@unfv.edu.pe", "Facultad de Educación"),
            ("otps.fh", "otps.fh@unfv.edu.pe", "Facultad de Humanidades"),
            ("otps.fce", "otps.fce@unfv.edu.pe", "Facultad de Ciencias Económicas"),
            ("otps.fcfc", "otps.fcfc@unfv.edu.pe", "Facultad de Ciencias Financieras y Contables"),
            ("otps.fau", "otps.fau@unfv.edu.pe", "Facultad de Arquitectura y Urbanismo"),
            ("otps.fopca", "otps.fopca@unfv.edu.pe", "Facultad de Oceanografía, Pesquería, Ciencias Alimentarias y Acuicultura"),
            ("otps.fic", "otps.fic@unfv.edu.pe", "Facultad de Ingeniería Civil"),
            ("otps.fiis", "otps.fiis@unfv.edu.pe", "Facultad de Ingeniería Industrial y de Sistemas (FIIS)"),
            ("otps.fa", "otps.fa@unfv.edu.pe", "Facultad de Administración"),
            ("otps.faps", "otps.faps@unfv.edu.pe", "Facultad de Psicología"),
            ("otps.figae", "otps.figae@unfv.edu.pe", "Facultad de Ingeniería Geográfica, Ambiental y Ecoturismo"),
            ("otps.fiei", "otps.fiei@unfv.edu.pe", "Facultad de Ingeniería Electronica e Informatica"),
            ("otps.fo", "otps.fo@unfv.edu.pe", "Facultad de Odontología"),
            ("otps.fcnm", "otps.fcnm@unfv.edu.pe", "Facultad de Ciencias y Naturales y Matemáticas"),
            ("otps.fmhu", "otps.fmhu@unfv.edu.pe", "Facultad de Medicina \"Hipólito Unanue\""),
            ("otps.ftm", "otps.ftm@unfv.edu.pe", "Facultad de Tecnología Medica"),
        ]
        
        for username, email, fac_name in otps_admins:
            u_otps = Usuario(
                username=username,
                email=email,
                rol="Admin",
                activo=True,
                cargo="Tutoría y Psicopedagogía",
                facultad=fac_name
            )
            u_otps.set_password("admin")
            db.session.add(u_otps)
            
        # Seeding Biblioteca Admins
        biblio_admins = [
            ("biblio.central", "biblio.central@unfv.edu.pe", "Biblioteca Central"),
            ("biblio.fiis", "biblio.fiis@unfv.edu.pe", "Facultad de Ingeniería Industrial y de Sistemas (FIIS)"),
            ("biblio.faps", "biblio.faps@unfv.edu.pe", "Facultad de Psicología"),
            ("biblio.fce", "biblio.fce@unfv.edu.pe", "Facultad de Ciencias Económicas")
        ]
        
        for username, email, fac_name in biblio_admins:
            u_biblio = Usuario(
                username=username,
                email=email,
                rol="Admin",
                activo=True,
                cargo="Biblioteca",
                facultad=fac_name
            )
            u_biblio.set_password("admin")
            db.session.add(u_biblio)
        
        # 2. Teacher Profile
        u_docente = Usuario(
            username="docente",
            email="docente@unfv.edu.pe",
            rol="Docente",
            activo=True
        )
        u_docente.set_password("docente")
        db.session.add(u_docente)
        db.session.commit() # Save to get ID
        
        p_docente = Docente(
            id_usuario=u_docente.id_usuario,
            nombres="Percy Alfonso",
            apellidos="Delgado Rojas",
            sede_codigo="SL07",
            facultad="FIIS",
            escuela_principal="Ingeniería de Sistemas",
            correo_institucional="docente@unfv.edu.pe",
            tipo_docente="Permanente"
        )
        db.session.add(p_docente)
        
        # 3. Student Profile
        u_alumno = Usuario(
            username="estudiante",
            email="estudiante@unfv.edu.pe",
            rol="Estudiante",
            activo=True
        )
        u_alumno.set_password("student")
        db.session.add(u_alumno)
        db.session.commit()
        
        p_alumno = Alumno(
            id_alumno="2021001234",
            id_usuario=u_alumno.id_usuario,
            nombres="Estudiante",
            apellidos="UNFV",
            sede_codigo="SL07",
            facultad="FIIS",
            escuela="Ingeniería de Sistemas",
            ciclo=5
        )
        db.session.add(p_alumno)
        
        db.session.commit()
        print("¡Base de datos limpia e inicializada con perfiles de prueba con éxito!")
        print("Credenciales:")
        print(" - Estudiante: estudiante@unfv.edu.pe / student (ID Alumno: 2021001234)")
        print(" - Docente: docente@unfv.edu.pe / docente")
        print(" - Admin: admin@unfv.edu.pe / admin")

if __name__ == '__main__':
    seed_database()
