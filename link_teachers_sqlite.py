from app import create_app
from models import db, Docente, Usuario

def link_teachers():
    app = create_app()
    with app.app_context():
        print("Starting user account creation and link process for docentes...")
        
        # Correct email for Noemí Ramírez Saavedra to avoid duplicates
        noemi = Docente.query.filter_by(nombres='Noemí', apellidos='Ramírez Saavedra').first()
        if noemi and noemi.correo_institucional == 'lramirez@unfv.edu.pe':
            print("Correcting Noemí Ramírez Saavedra's email to avoid duplicates...")
            noemi.correo_institucional = 'nramirez@unfv.edu.pe'
            db.session.commit()
            
        docentes = Docente.query.all()
        created_count = 0
        linked_count = 0
        
        for d in docentes:
            # Check if user already exists
            user = Usuario.query.filter_by(email=d.correo_institucional).first()
            if not user:
                # Generate username from email prefix
                username = d.correo_institucional.split('@')[0]
                user = Usuario(
                    username=username,
                    email=d.correo_institucional,
                    rol="Docente",
                    activo=True,
                    facultad=d.facultad
                )
                user.set_password("123456")  # password default 123456
                db.session.add(user)
                db.session.commit()
                created_count += 1
                
            if d.id_usuario != user.id_usuario:
                d.id_usuario = user.id_usuario
                linked_count += 1
                
        db.session.commit()
        print(f"Process finished successfully. Created {created_count} user accounts. Linked {linked_count} docentes.")

if __name__ == '__main__':
    link_teachers()
