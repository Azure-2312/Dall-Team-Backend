import os
import sys
from datetime import datetime, timedelta, date

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from models import (
    db, Usuario, Alumno, Docente, Curso, NotasCurso, 
    ApunteEstudiante, SolicitudTutoria, AlumnoUnidoTutoria, 
    AlumnoDebilidad, ExamenObjetivo, MicroTareaDiaria, AlumnoEvento
)

def create_large_demo():
    app = create_app()
    with app.app_context():
        print("Checking if student 2024023989 already exists...")
        student_id = "2024023989"
        student_email = "2024023989@unfv.edu.pe"
        
        # Clean existing demo records for this student to allow re-runs
        print("Cleaning existing demo records for student 2024023989...")
        db.session.query(AlumnoEvento).filter_by(id_alumno=student_id).delete()
        db.session.query(MicroTareaDiaria).filter(
            MicroTareaDiaria.id_examen.in_(
                db.session.query(ExamenObjetivo.id_examen).filter_by(id_alumno=student_id)
            )
        ).delete()
        db.session.query(ExamenObjetivo).filter_by(id_alumno=student_id).delete()
        db.session.query(AlumnoDebilidad).filter_by(id_alumno=student_id).delete()
        db.session.query(AlumnoUnidoTutoria).filter_by(id_alumno=student_id).delete()
        db.session.query(SolicitudTutoria).filter_by(id_alumno=student_id).delete()
        db.session.query(ApunteEstudiante).filter_by(id_alumno=student_id).delete()
        db.session.query(NotasCurso).filter_by(id_alumno=student_id).delete()
        
        student_profile = Alumno.query.get(student_id)
        if student_profile:
            db.session.delete(student_profile)
            
        student_user = Usuario.query.filter_by(email=student_email).first()
        if student_user:
            db.session.delete(student_user)
            
        db.session.commit()
        
        # 1. Create User
        print("Creating user account...")
        u = Usuario(
            username=student_id,
            email=student_email,
            rol="Estudiante",
            activo=True,
            facultad="FIIS"
        )
        u.set_password("123456")  # default password is '123456'
        db.session.add(u)
        db.session.commit()
        
        # 2. Create Student
        print("Creating student record...")
        courses_enrolled = ["26", "28", "31", "32", "33", "34"] # Cycle 5 Systems Engineering courses
        a = Alumno(
            id_alumno=student_id,
            id_usuario=u.id_usuario,
            nombres="Carlos Alberto",
            apellidos="Bermúdez Mendoza",
            sede_codigo="SL07",
            facultad="FIIS",
            escuela="Ingeniería de Sistemas",
            ciclo=5,
            cursos_inscritos=courses_enrolled
        )
        db.session.add(a)
        db.session.commit()
        
        # 3. Create Course Grades (NotasCurso)
        print("Adding grades for courses...")
        
        # Course 28 (Investigación Operativa) -> Risk: High (TA=8.5, Parcial=7, Needs 16.3 on Final)
        n28 = NotasCurso(
            id_alumno=student_id,
            id_curso="28",
            practica_calificada_1=8.0,
            practica_calificada_2=9.0,
            examen_parcial=7.0,
            examen_final=None
        )
        db.session.add(n28)
        
        # Course 31 (Programación Aplicada II) -> Risk: Medium (TA=11.5, Parcial=10)
        n31 = NotasCurso(
            id_alumno=student_id,
            id_curso="31",
            practica_calificada_1=12.0,
            practica_calificada_2=11.0,
            examen_parcial=10.0,
            examen_final=None
        )
        db.session.add(n31)
        
        # Course 33 (Fundamentos de Bases de Datos) -> Risk: High (TA=9.5, Parcial=8)
        n33 = NotasCurso(
            id_alumno=student_id,
            id_curso="33",
            practica_calificada_1=9.0,
            practica_calificada_2=10.0,
            examen_parcial=8.0,
            examen_final=None
        )
        db.session.add(n33)
        
        # Course 26 (Gestión Contable) -> Risk: None (TA=14.5, Parcial=13)
        n26 = NotasCurso(
            id_alumno=student_id,
            id_curso="26",
            practica_calificada_1=15.0,
            practica_calificada_2=14.0,
            examen_parcial=13.0,
            examen_final=None
        )
        db.session.add(n26)
        
        # Course 32 (Ingeniería de Costos y Presupuestos) -> Risk: None (TA=17.5, Parcial=16)
        n32 = NotasCurso(
            id_alumno=student_id,
            id_curso="32",
            practica_calificada_1=18.0,
            practica_calificada_2=17.0,
            examen_parcial=16.0,
            examen_final=None
        )
        db.session.add(n32)
        
        # Course 34 (Ingeniería de Procesos de Negocios) -> Risk: None (TA=13.5, Parcial=12)
        n34 = NotasCurso(
            id_alumno=student_id,
            id_curso="34",
            practica_calificada_1=14.0,
            practica_calificada_2=13.0,
            examen_parcial=12.0,
            examen_final=None
        )
        db.session.add(n34)
        
        db.session.commit()
        
        # 4. Create past weeks notebook sheets (ApunteEstudiante) (weeks 1 to 10)
        # We will add realistic study notes and AI summaries for Course 28 and 33
        print("Generating weekly study notes history (weeks 1 to 10)...")
        
        # Course 28 (Investigación Operativa)
        notes_28 = {
            1: ("Concepto de Programación Lineal (PL). Variables de decisión, restricciones de capacidad, función objetivo de maximización.",
                "### Resumen IA - Semana 1: Modelado de PL\nSe revisó el modelamiento matemático básico. Las variables representan decisiones y las restricciones representan límites físicos de recursos. Clave: definir correctamente las unidades de medida."),
            2: ("Método gráfico de optimización. Región factible, puntos esquina y líneas de isocosto/isoganancia.",
                "### Resumen IA - Semana 2: Método Gráfico\nResolución visual de problemas con 2 variables. La solución óptima siempre se encuentra en una de las esquinas extremas del polígono de la región factible."),
            3: ("Forma estándar de un modelo de programación lineal. Adición de variables de holgura (slack) y exceso (surplus).",
                "### Resumen IA - Semana 3: Forma Estándar de PL\nPreparación del modelo para el algoritmo Simplex. Se transforman desigualdades en igualdades usando variables de holgura para restricciones '<=' y exceso para '>='."),
            4: ("Método Simplex tabular inicial. Determinación de la variable que entra (criterio de optimalidad) y la que sale (criterio de factibilidad).",
                "### Resumen IA - Semana 4: Simplex Tabular Inicial\nIntroducción a las iteraciones simplex. Se identifica el pivote mediante el cociente mínimo para garantizar que no se viole la no-negatividad."),
            5: ("Casos especiales en el método Simplex: soluciones múltiples, degeneración académica e infactibilidad.",
                "### Resumen IA - Semana 5: Casos Especiales de Simplex\nSe analizó la degeneración (empate en cociente mínimo) y la infactibilidad (cuando no hay región factible que satisfaga todas las restricciones concurrentes)."),
            6: ("Método de la M Grande (penalización) y método de dos fases para modelos con restricciones de igualdad o '>='.",
                "### Resumen IA - Semana 6: Variables Artificiales\nResolución de modelos complejos mediante penalización artificial (M) para forzar variables iniciales fuera de la base en la solución final."),
            7: ("Teoría de dualidad en Programación Lineal. Relación primal-dual y teoremas de dualidad fuerte/débil.",
                "### Resumen IA - Semana 7: Dualidad Matemática\nEl problema dual ofrece una perspectiva económica del primal. Sus variables representan los precios sombra de los recursos limitados."),
            8: ("Análisis de sensibilidad y post-optimización. Cambios en la disponibilidad de recursos y coeficientes de costo.",
                "### Resumen IA - Semana 8: Análisis de Sensibilidad\nEvaluación de rangos de tolerancia en los cuales la base actual óptima se mantiene. Permite predecir cambios sin necesidad de volver a correr todo el simplex."),
            9: ("Modelo de Transporte. Métodos de solución inicial: esquina noroeste y costo mínimo.",
                "### Resumen IA - Semana 9: Algoritmos de Transporte\nModelos de distribución logística de fábricas a almacenes. La esquina noroeste es rápida pero ineficiente; el costo mínimo da una mejor aproximación inicial."),
            10: ("Método de aproximación de Vogel y método MODI para la optimización final del transporte.",
                "### Resumen IA - Semana 10: Optimización del Transporte\nEl método MODI (Multiplicadores) evalúa los costos marginales de celdas vacías para iterar hacia el costo logístico mínimo absoluto.")
        }
        
        for wk, (txt, sum_ia) in notes_28.items():
            ap = ApunteEstudiante(
                id_alumno=student_id,
                id_curso="28",
                semana=wk,
                nombre_hoja=f"Semana {wk} - Repaso",
                texto_notas=txt,
                resumen_ia=sum_ia,
                fecha_modificacion=datetime.utcnow() - timedelta(weeks=11-wk)
            )
            db.session.add(ap)
            
        # Course 33 (Fundamentos de Bases de Datos)
        notes_33 = {
            1: ("Introducción a los Sistemas de Gestión de Bases de Datos (SGBD). Diferencia entre archivos planos y bases de datos relacionales.",
                "### Resumen IA - Semana 1: SGBD y Arquitectura\nSe cubrió la independencia de datos física y lógica. Los SGBD estructuran y resguardan la concurrencia, seguridad e integridad transaccional de los datos."),
            2: ("Modelo Entidad-Relación (MER). Entidades, atributos (clave, compuesto, multivaluado) y relaciones de cardinalidad.",
                "### Resumen IA - Semana 2: Modelo Entidad-Relación\nModelado conceptual. Se identificaron las entidades fuertes y débiles y cómo representar restricciones de cardinalidad (1:1, 1:N, N:M)."),
            3: ("Modelo Relacional. Pasaje del MER al esquema de tablas relacionales. Llaves primarias y foráneas.",
                "### Resumen IA - Semana 3: Esquema Relacional\nTransformación de diagramas conceptuales a esquemas relacionales tabulares. Las relaciones N:M crean tablas asociativas intermedias."),
            4: ("Álgebra Relacional. Operaciones de selección, proyección, unión, diferencia y producto cartesiano.",
                "### Resumen IA - Semana 4: Álgebra Relacional\nFundamento matemático del lenguaje SQL. Operaciones de consulta teóricas para manipular relaciones binarias y unarias."),
            5: ("Introducción a SQL. Sentencias DDL: CREATE TABLE, ALTER TABLE y restricciones de integridad (CHECK, UNIQUE).",
                "### Resumen IA - Semana 5: SQL DDL\nLenguaje de Definición de Datos. Creación de esquemas robustos aplicando restricciones de clave primaria, ajena e integridad de dominio."),
            6: ("Sentencias DML en SQL. Inserción, actualización y consultas básicas usando SELECT, WHERE y ORDER BY.",
                "### Resumen IA - Semana 6: Consultas SQL DML\nManipulación y recuperación de datos de forma declarativa básica. Uso de operadores lógicos de comparación."),
            7: ("Consultas multi-tabla. INNER JOIN, LEFT JOIN, RIGHT JOIN y producto cartesiano explícito.",
                "### Resumen IA - Semana 7: Joins en SQL\nConsultas avanzadas para unificar información distribuida en varias tablas relacionadas por claves foráneas."),
            8: ("Funciones de agregación (SUM, AVG, COUNT, MAX, MIN) y cláusulas GROUP BY y HAVING.",
                "### Resumen IA - Semana 8: Agrupamiento SQL\nConsultas estadísticas avanzadas. La cláusula HAVING se aplica después del agrupamiento, a diferencia de WHERE que filtra filas previas."),
            9: ("Subconsultas y operaciones de conjunto (UNION, INTERSECT, EXCEPT) en SQL.",
                "### Resumen IA - Semana 9: Subconsultas Anidadas\nConsultas dentro de cláusulas WHERE o SELECT. Permite recuperar conjuntos dinámicos de forma compleja."),
            10: ("Teoría de Normalización. Primera (1FN), Segunda (2FN) y Tercera Forma Normal (3FN).",
                "### Resumen IA - Semana 10: Normalización Relacional\nProceso de optimización para eliminar redundancias y anomalías de actualización. Se resuelven dependencias parciales y transitivas.")
        }
        
        for wk, (txt, sum_ia) in notes_33.items():
            ap = ApunteEstudiante(
                id_alumno=student_id,
                id_curso="33",
                semana=wk,
                nombre_hoja=f"Clase Sem {wk}",
                texto_notas=txt,
                resumen_ia=sum_ia,
                fecha_modificacion=datetime.utcnow() - timedelta(weeks=11-wk)
            )
            db.session.add(ap)
            
        db.session.commit()
        
        # 5. Create Tutoring Requests (Solicitudes de Tutoría)
        print("Creating tutoring requests history...")
        
        # Docente 1 is Percy Delgado
        # Request 1: Approved and Confirmed, Course 28 (Investigación Operativa)
        s1 = SolicitudTutoria(
            id_alumno=student_id,
            id_curso="28",
            cantidad_estudiantes=5,
            archivo_solicitud_path="uploads/solicitud_simplex_firmada.docx",
            estado="Confirmado",
            id_docente=1,
            dia="Lunes",
            hora="15:00",
            link_llamada="https://teams.microsoft.com/l/meetup-join/19%3ameeting_Y2E0NDg1...",
            escuela="Ingeniería de Sistemas",
            fecha_solicitud=datetime.utcnow() - timedelta(weeks=4),
            confirmada=True
        )
        db.session.add(s1)
        
        # Request 2: Approved and Confirmed, Course 33 (Fundamentos de Bases de Datos)
        s2 = SolicitudTutoria(
            id_alumno=student_id,
            id_curso="33",
            cantidad_estudiantes=4,
            archivo_solicitud_path="uploads/solicitud_bd_normalizacion.docx",
            estado="Confirmado",
            id_docente=1,
            dia="Miércoles",
            hora="10:00",
            link_llamada="https://teams.microsoft.com/l/meetup-join/19%3ameeting_M2NlMmYy...",
            escuela="Ingeniería de Sistemas",
            fecha_solicitud=datetime.utcnow() - timedelta(weeks=2),
            confirmada=True
        )
        db.session.add(s2)
        
        # Request 3: Pending Approval, Course 31 (Programación Aplicada II)
        s3 = SolicitudTutoria(
            id_alumno=student_id,
            id_curso="31",
            cantidad_estudiantes=3,
            archivo_solicitud_path="uploads/solicitud_java_web.docx",
            estado="Pendiente",
            escuela="Ingeniería de Sistemas",
            fecha_solicitud=datetime.utcnow() - timedelta(days=2),
            confirmada=False
        )
        db.session.add(s3)
        
        db.session.commit()
        
        # Add members to tutoring requests to simulate group collaboration
        print("Linking group members to tutoring sessions...")
        # Link student himself to unions
        db.session.add(AlumnoUnidoTutoria(id_solicitud=s1.id_solicitud, id_alumno=student_id))
        db.session.add(AlumnoUnidoTutoria(id_solicitud=s2.id_solicitud, id_alumno=student_id))
        
        # Add mock students to s1
        db.session.add(AlumnoUnidoTutoria(id_solicitud=s1.id_solicitud, id_alumno="2021001234"))
        
        db.session.commit()
        
        # 6. Add Student Weaknesses (AlumnoDebilidad)
        print("Registering learning weaknesses...")
        w1 = AlumnoDebilidad(
            id_alumno=student_id,
            id_curso="28",
            tema_central="Análisis de Sensibilidad",
            errores_count=3
        )
        db.session.add(w1)
        
        w2 = AlumnoDebilidad(
            id_alumno=student_id,
            id_curso="33",
            tema_central="Normalización 3FN",
            errores_count=2
        )
        db.session.add(w2)
        db.session.commit()
        
        # 7. Create Study Plan (ExamenObjetivo and MicroTareaDiaria)
        print("Creating Study Route Plan (ExamenObjetivo)...")
        eo = ExamenObjetivo(
            id_alumno=student_id,
            id_curso="28",
            fecha_limite=datetime.now() + timedelta(days=6),
            nivel_dificultad=4,
            temas_asociados=["Programación Lineal", "Método Simplex", "Dualidad", "Análisis de Sensibilidad"]
        )
        db.session.add(eo)
        db.session.commit()
        
        # Generate 6 days of tasks
        print("Populating daily micro tasks schedule...")
        task_list = [
            ("Repasar formulación de modelos de programación lineal", 40, True, -3),
            ("Resolver ejercicios del método gráfico de maximización", 45, True, -2),
            ("Estudiar construcción de tablas simplex y variables holgura", 50, True, -1),
            ("Ejercicios prácticos del método simplex e infactibilidad", 60, False, 0),
            ("Revisión de problemas duales y teorema de holgura complementaria", 45, False, 1),
            ("Análisis de sensibilidad y post-optimización simplex", 55, False, 2)
        ]
        
        for meta, mins, done, offset in task_list:
            task_date = (datetime.now() + timedelta(days=offset)).date()
            mt = MicroTareaDiaria(
                id_examen=eo.id_examen,
                fecha_asignada=task_date,
                meta_texto=meta,
                tiempo_estimado=mins,
                completado=done
            )
            db.session.add(mt)
            
        db.session.commit()
        
        # 8. Create Telemetry Events (AlumnoEvento)
        print("Injecting academic activity telemetry logs...")
        events_mock = [
            ('pizarra_guardada', {"semana": 1, "curso": "28"}, timedelta(weeks=10)),
            ('autoevaluacion_completada', {"curso": "28", "nota": 8, "correcto": 2, "incorrecto": 8}, timedelta(weeks=8)),
            ('pizarra_guardada', {"semana": 5, "curso": "28"}, timedelta(weeks=6)),
            ('autoevaluacion_completada', {"curso": "33", "nota": 10, "correcto": 4, "incorrecto": 6}, timedelta(weeks=4)),
            ('pizarra_guardada', {"semana": 8, "curso": "28"}, timedelta(weeks=2)),
            ('pizarra_guardada', {"semana": 10, "curso": "33"}, timedelta(days=4)),
            ('pizarra_guardada', {"semana": 10, "curso": "28"}, timedelta(days=2))
        ]
        
        for ev_type, meta_j, offset_time in events_mock:
            ev = AlumnoEvento(
                id_alumno=student_id,
                tipo_evento=ev_type,
                metadata_json=str(meta_j),
                fecha_evento=datetime.utcnow() - offset_time
            )
            db.session.add(ev)
            
        db.session.commit()
        
        print("\n=======================================================")
        print(f"LARGE EXAMPLE SEEDED SUCCESSFULLY FOR STUDENT: {student_id}")
        print("Details:")
        print(f" - Student Email: {student_email} (Password: student)")
        print(" - School: Ingeniería de Sistemas, Facultad: FIIS")
        print(" - Active Courses Enrolled: 6 courses (Gestión Contable, Investigación Operativa, etc.)")
        print(" - Note History: Weeks 1 to 10 notes + AI Summaries successfully pre-populated.")
        print(" - Tutoring Sessions: 2 approved/confirmed (Percy Delgado), 1 pending.")
        print(" - Active Weaknesses: 2 mapped (Análisis de Sensibilidad, Normalización 3FN).")
        print(" - Study Plan: ExamenObjetivo active for Investigación Operativa with daily schedule.")
        print("=======================================================")

if __name__ == '__main__':
    create_large_demo()
