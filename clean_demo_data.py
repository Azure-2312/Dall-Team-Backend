from app import create_app
from models import (
    db,
    ReporteTutoria,
    SolicitudTutoria,
    AlumnoUnidoTutoria,
    CitaTutoria,
    AlumnoDebilidad,
    AuditoriaRAG,
    AuditoriaActividad,
    ApunteEstudiante,
    HistorialAcademico
)

def clean_data():
    app = create_app()
    with app.app_context():
        print("Starting cleanup of mock demo data...")
        try:
            # 1. Alumnos Unidos a Tutoría
            num_deleted = AlumnoUnidoTutoria.query.delete()
            print(f"Deleted {num_deleted} records from AlumnoUnidoTutoria")

            # 2. Reportes Tutoría
            num_deleted = ReporteTutoria.query.delete()
            print(f"Deleted {num_deleted} records from ReporteTutoria")

            # 3. Solicitudes Tutoría
            num_deleted = SolicitudTutoria.query.delete()
            print(f"Deleted {num_deleted} records from SolicitudTutoria")

            # 4. Citas Tutoría
            num_deleted = CitaTutoria.query.delete()
            print(f"Deleted {num_deleted} records from CitaTutoria")

            # 5. Alumno Debilidades
            num_deleted = AlumnoDebilidad.query.delete()
            print(f"Deleted {num_deleted} records from AlumnoDebilidad")

            # 6. Apuntes Estudiantes (Canvas and Notes)
            num_deleted = ApunteEstudiante.query.delete()
            print(f"Deleted {num_deleted} records from ApunteEstudiante")

            # 7. Auditoría RAG
            num_deleted = AuditoriaRAG.query.delete()
            print(f"Deleted {num_deleted} records from AuditoriaRAG")

            # 8. Auditoría Actividad
            num_deleted = AuditoriaActividad.query.delete()
            print(f"Deleted {num_deleted} records from AuditoriaActividad")

            # 9. Historial Academico (optional cleanup of academic records)
            num_deleted = HistorialAcademico.query.delete()
            print(f"Deleted {num_deleted} records from HistorialAcademico")

            db.session.commit()
            print("Database cleanup completed successfully! Created user accounts and course catalog were preserved.")
        except Exception as e:
            db.session.rollback()
            print("Error during cleanup:", e)

if __name__ == "__main__":
    clean_data()
