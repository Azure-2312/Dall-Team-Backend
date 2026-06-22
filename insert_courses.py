import os
from app import create_app
from models import db, Curso

def insert_courses():
    app = create_app()
    with app.app_context():
        print("Eliminando cursos existentes para evitar duplicados...")
        # Optional: uncomment if you want a clean slate
        # db.session.query(Curso).delete()
        
        courses_to_insert = [
            # 1° CICLO
            {"id_curso": "01", "nombre_curso": "INGLÉS I", "ciclo_teorico": 1, "creditos": 1, "id_prerrequisito": None, "tipo_estudio": "General"},
            {"id_curso": "02", "nombre_curso": "LENGUAJE Y COMUNICACIÓN", "ciclo_teorico": 1, "creditos": 3, "id_prerrequisito": None, "tipo_estudio": "General"},
            {"id_curso": "03", "nombre_curso": "FILOSOFÍA Y ÉTICA", "ciclo_teorico": 1, "creditos": 3, "id_prerrequisito": None, "tipo_estudio": "General"},
            {"id_curso": "04", "nombre_curso": "FUNDAMENTOS DE CÁLCULO", "ciclo_teorico": 1, "creditos": 3, "id_prerrequisito": None, "tipo_estudio": "General"},
            {"id_curso": "05", "nombre_curso": "METODOLOGÍA DE TRABAJO UNIVERSITARIO", "ciclo_teorico": 1, "creditos": 2, "id_prerrequisito": None, "tipo_estudio": "General"},
            {"id_curso": "06", "nombre_curso": "ACTIVIDADES CULTURALES Y DEPORTIVAS", "ciclo_teorico": 1, "creditos": 1, "id_prerrequisito": None, "tipo_estudio": "General"},
            {"id_curso": "07", "nombre_curso": "MATEMÁTICA", "ciclo_teorico": 1, "creditos": 5, "id_prerrequisito": None, "tipo_estudio": "Especifico"},
            {"id_curso": "08", "nombre_curso": "INTRODUCCIÓN A LA INGENIERÍA DE SISTEMAS", "ciclo_teorico": 1, "creditos": 4, "id_prerrequisito": None, "tipo_estudio": "Especifico"},

            # 2° CICLO
            {"id_curso": "09", "nombre_curso": "INGLÉS II", "ciclo_teorico": 2, "creditos": 1, "id_prerrequisito": "01", "tipo_estudio": "General"},
            {"id_curso": "10", "nombre_curso": "LIDERAZGO Y DESARROLLO PERSONAL", "ciclo_teorico": 2, "creditos": 3, "id_prerrequisito": "02", "tipo_estudio": "General"},
            {"id_curso": "11", "nombre_curso": "MEDIO AMBIENTE Y DESARROLLO SOSTENIBLE", "ciclo_teorico": 2, "creditos": 3, "id_prerrequisito": None, "tipo_estudio": "General"},
            {"id_curso": "12", "nombre_curso": "TECNOLOGÍAS DE LA INFORMACIÓN Y COMUNICACIÓN", "ciclo_teorico": 2, "creditos": 2, "id_prerrequisito": "08", "tipo_estudio": "General"},
            {"id_curso": "13", "nombre_curso": "SOCIOLOGÍA", "ciclo_teorico": 2, "creditos": 2, "id_prerrequisito": "03", "tipo_estudio": "General"},
            {"id_curso": "14", "nombre_curso": "TEORÍA DE SISTEMAS", "ciclo_teorico": 2, "creditos": 3, "id_prerrequisito": "08", "tipo_estudio": "Especifico"},
            {"id_curso": "15", "nombre_curso": "CÁLCULO DIFERENCIAL E INTEGRAL", "ciclo_teorico": 2, "creditos": 5, "id_prerrequisito": "07", "tipo_estudio": "Especifico"},
            {"id_curso": "16", "nombre_curso": "FUNDAMENTOS DE PROGRAMACIÓN I", "ciclo_teorico": 2, "creditos": 3, "id_prerrequisito": None, "tipo_estudio": "Especifico"},

            # 3° CICLO
            {"id_curso": "17", "nombre_curso": "INGLÉS III", "ciclo_teorico": 3, "creditos": 1, "id_prerrequisito": "09", "tipo_estudio": "General"},
            {"id_curso": "18", "nombre_curso": "PSICOLOGÍA ORGANIZACIONAL", "ciclo_teorico": 3, "creditos": 2, "id_prerrequisito": "10", "tipo_estudio": "General"},
            {"id_curso": "19", "nombre_curso": "ESTADÍSTICA", "ciclo_teorico": 3, "creditos": 3, "id_prerrequisito": "04", "tipo_estudio": "General"},
            {"id_curso": "20", "nombre_curso": "GEOPOLÍTICA Y REALIDAD NACIONAL", "ciclo_teorico": 3, "creditos": 3, "id_prerrequisito": "11", "tipo_estudio": "General"},
            {"id_curso": "21", "nombre_curso": "METODOLOGÍA DE LA INVESTIGACIÓN CIENTÍFICA", "ciclo_teorico": 3, "creditos": 3, "id_prerrequisito": "05", "tipo_estudio": "General"},
            {"id_curso": "22", "nombre_curso": "FÍSICA", "ciclo_teorico": 3, "creditos": 3, "id_prerrequisito": "15", "tipo_estudio": "Especifico"},
            {"id_curso": "23", "nombre_curso": "ECUACIONES DIFERENCIALES", "ciclo_teorico": 3, "creditos": 4, "id_prerrequisito": "15", "tipo_estudio": "Especifico"},
            {"id_curso": "24", "nombre_curso": "FUNDAMENTOS DE PROGRAMACIÓN II", "ciclo_teorico": 3, "creditos": 3, "id_prerrequisito": "16", "tipo_estudio": "Especifico"},

            # 4° CICLO
            {"id_curso": "25", "nombre_curso": "PROGRAMACIÓN APLICADA I", "ciclo_teorico": 4, "creditos": 4, "id_prerrequisito": "24", "tipo_estudio": "Especifico"},
            {"id_curso": "26", "nombre_curso": "GESTIÓN CONTABLE", "ciclo_teorico": 4, "creditos": 3, "id_prerrequisito": None, "tipo_estudio": "Especifico"},
            {"id_curso": "27", "nombre_curso": "ESTADÍSTICA II", "ciclo_teorico": 4, "creditos": 3, "id_prerrequisito": "19", "tipo_estudio": "Especifico"},
            {"id_curso": "28", "nombre_curso": "INVESTIGACIÓN OPERATIVA", "ciclo_teorico": 4, "creditos": 4, "id_prerrequisito": "19", "tipo_estudio": "Especifico"},
            {"id_curso": "29", "nombre_curso": "ELECTROMAGNETISMO Y ELECTRÓNICA BÁSICA", "ciclo_teorico": 4, "creditos": 4, "id_prerrequisito": "22", "tipo_estudio": "Especifico"},
            {"id_curso": "30", "nombre_curso": "MATEMÁTICAS DISCRETAS", "ciclo_teorico": 4, "creditos": 4, "id_prerrequisito": "23", "tipo_estudio": "Especifico"},

            # 5° CICLO
            {"id_curso": "31", "nombre_curso": "PROGRAMACIÓN APLICADA II", "ciclo_teorico": 5, "creditos": 4, "id_prerrequisito": "25", "tipo_estudio": "Especifico"},
            {"id_curso": "32", "nombre_curso": "INGENIERÍA DE COSTOS Y PRESUPUESTOS", "ciclo_teorico": 5, "creditos": 3, "id_prerrequisito": "26", "tipo_estudio": "Especifico"},
            {"id_curso": "33", "nombre_curso": "FUNDAMENTOS DE BASES DE DATOS", "ciclo_teorico": 5, "creditos": 3, "id_prerrequisito": None, "tipo_estudio": "Especifico"},
            {"id_curso": "34", "nombre_curso": "INGENIERÍA DE PROCESOS DE NEGOCIOS", "ciclo_teorico": 5, "creditos": 3, "id_prerrequisito": "28", "tipo_estudio": "Especifico"},
            {"id_curso": "35", "nombre_curso": "SISTEMAS DIGITALES Y ARQUITECTURA DE COMPUTADORAS", "ciclo_teorico": 5, "creditos": 3, "id_prerrequisito": "29", "tipo_estudio": "Especifico"},
            {"id_curso": "36", "nombre_curso": "SISTEMAS OPERATIVOS", "ciclo_teorico": 5, "creditos": 3, "id_prerrequisito": "30", "tipo_estudio": "Especifico"},
            {"id_curso": "37", "nombre_curso": "DINÁMICA DE SISTEMAS", "ciclo_teorico": 5, "creditos": 2, "id_prerrequisito": "30", "tipo_estudio": "Especifico"},

            # 6° CICLO
            {"id_curso": "39", "nombre_curso": "PROGRAMACIÓN APLICADA III", "ciclo_teorico": 6, "creditos": 3, "id_prerrequisito": "31", "tipo_estudio": "Especifico"},
            {"id_curso": "40", "nombre_curso": "ADMINISTRACIÓN FINANCIERA", "ciclo_teorico": 6, "creditos": 3, "id_prerrequisito": "32", "tipo_estudio": "Especifico"},
            {"id_curso": "41", "nombre_curso": "DISEÑO DE BASES DE DATOS", "ciclo_teorico": 6, "creditos": 4, "id_prerrequisito": "33", "tipo_estudio": "Especifico"},
            {"id_curso": "42", "nombre_curso": "INGENIERÍA DE REQUERIMIENTOS", "ciclo_teorico": 6, "creditos": 3, "id_prerrequisito": "34", "tipo_estudio": "Especifico"},
            {"id_curso": "43", "nombre_curso": "FUNDAMENTOS DE REDES Y CONECTIVIDAD", "ciclo_teorico": 6, "creditos": 4, "id_prerrequisito": "35", "tipo_estudio": "Especifico"},
            {"id_curso": "44", "nombre_curso": "ARQUITECTURA DE SOFTWARE", "ciclo_teorico": 6, "creditos": 3, "id_prerrequisito": "36", "tipo_estudio": "Especifico"},

            # 7° CICLO
            {"id_curso": "46", "nombre_curso": "INGENIERÍA DE SOFTWARE", "ciclo_teorico": 7, "creditos": 3, "id_prerrequisito": "42", "tipo_estudio": "Especifico"},
            {"id_curso": "47", "nombre_curso": "INVESTIGACIÓN APLICADA", "ciclo_teorico": 7, "creditos": 3, "id_prerrequisito": "21", "tipo_estudio": "Especifico"},
            {"id_curso": "48", "nombre_curso": "ADMINISTRACIÓN Y GESTIÓN DE BASES DE DATOS", "ciclo_teorico": 7, "creditos": 3, "id_prerrequisito": "41", "tipo_estudio": "Especifico"},
            {"id_curso": "49", "nombre_curso": "PLANEAMIENTO DE RECURSOS EMPRESARIALES", "ciclo_teorico": 7, "creditos": 3, "id_prerrequisito": "42", "tipo_estudio": "Especifico"},
            {"id_curso": "50", "nombre_curso": "ARQUITECTURA Y CONECTIVIDAD DE REDES", "ciclo_teorico": 7, "creditos": 3, "id_prerrequisito": "43", "tipo_estudio": "Especifico"},
            {"id_curso": "51", "nombre_curso": "INGENIERÍA DEL CONOCIMIENTO", "ciclo_teorico": 7, "creditos": 2, "id_prerrequisito": "44", "tipo_estudio": "Especifico"},
            {"id_curso": "52", "nombre_curso": "SIMULACIÓN DE SISTEMAS", "ciclo_teorico": 7, "creditos": 3, "id_prerrequisito": "37", "tipo_estudio": "Especifico"},

            # 8° CICLO
            {"id_curso": "54", "nombre_curso": "TALLER DE TESIS I", "ciclo_teorico": 8, "creditos": 3, "id_prerrequisito": "47", "tipo_estudio": "Especializado"},
            {"id_curso": "55", "nombre_curso": "TALLER DE INTEGRACIÓN DE SISTEMAS", "ciclo_teorico": 8, "creditos": 3, "id_prerrequisito": "46", "tipo_estudio": "Especifico"},
            {"id_curso": "56", "nombre_curso": "TÓPICOS ESPECIALES DE INTERNET DE LAS COSAS", "ciclo_teorico": 8, "creditos": 4, "id_prerrequisito": "48", "tipo_estudio": "Especifico"},
            {"id_curso": "57", "nombre_curso": "INTELIGENCIA DE NEGOCIOS", "ciclo_teorico": 8, "creditos": 3, "id_prerrequisito": "49", "tipo_estudio": "Especifico"},
            {"id_curso": "58", "nombre_curso": "SEGURIDAD EN REDES Y SISTEMAS DE INFORMACIÓN", "ciclo_teorico": 8, "creditos": 3, "id_prerrequisito": "50", "tipo_estudio": "Especifico"},
            {"id_curso": "59", "nombre_curso": "INTELIGENCIA ARTIFICIAL", "ciclo_teorico": 8, "creditos": 3, "id_prerrequisito": "51", "tipo_estudio": "Especifico"},

            # 9° CICLO
            {"id_curso": "60", "nombre_curso": "TALLER DE TESIS II", "ciclo_teorico": 9, "creditos": 3, "id_prerrequisito": "54", "tipo_estudio": "Especializado"},
            {"id_curso": "61", "nombre_curso": "EVALUACIÓN DE PROYECTOS DE TI", "ciclo_teorico": 9, "creditos": 3, "id_prerrequisito": "55", "tipo_estudio": "Especializado"},
            {"id_curso": "62", "nombre_curso": "TÓPICOS ESPECIALES DE BIGDATA", "ciclo_teorico": 9, "creditos": 3, "id_prerrequisito": "56", "tipo_estudio": "Especializado"},
            {"id_curso": "63", "nombre_curso": "ARQUITECTURA EMPRESARIAL", "ciclo_teorico": 9, "creditos": 2, "id_prerrequisito": "57", "tipo_estudio": "Especializado"},
            {"id_curso": "64", "nombre_curso": "CIBERSEGURIDAD", "ciclo_teorico": 9, "creditos": 3, "id_prerrequisito": "58", "tipo_estudio": "Especializado"},
            {"id_curso": "65", "nombre_curso": "PRÁCTICAS PRE-PROFESIONALES I", "ciclo_teorico": 9, "creditos": 4, "id_prerrequisito": None, "tipo_estudio": "Especializado"},

            # 10° CICLO
            {"id_curso": "66", "nombre_curso": "AUDITORÍA DE SISTEMAS DE INFORMACIÓN", "ciclo_teorico": 10, "creditos": 3, "id_prerrequisito": "64", "tipo_estudio": "Especializado"},
            {"id_curso": "67", "nombre_curso": "GERENCIA DE PROYECTOS DE TI", "ciclo_teorico": 10, "creditos": 4, "id_prerrequisito": "61", "tipo_estudio": "Especializado"},
            {"id_curso": "68", "nombre_curso": "FUNDAMENTOS DE BUSINESS ANALYTICS", "ciclo_teorico": 10, "creditos": 3, "id_prerrequisito": "56", "tipo_estudio": "Especializado"},
            {"id_curso": "69", "nombre_curso": "TECNOLOGÍAS EMERGENTES E INNOVACIÓN TECNOLÓGICA", "ciclo_teorico": 10, "creditos": 3, "id_prerrequisito": "59", "tipo_estudio": "Especializado"},
            {"id_curso": "70", "nombre_curso": "PRÁCTICAS PRE-PROFESIONALES II", "ciclo_teorico": 10, "creditos": 4, "id_prerrequisito": "65", "tipo_estudio": "Especializado"},
        ]
        
        # Build courses lookup by id
        courses_by_id = {c["id_curso"]: c for c in courses_to_insert}
        
        # Insert or update each course
        for c in courses_to_insert:
            # Check if course already exists
            existing_course = Curso.query.get(c["id_curso"])
            
            # Find prerequisite name
            prereq_name = None
            if c["id_prerrequisito"]:
                pr = courses_by_id.get(c["id_prerrequisito"])
                if pr:
                    prereq_name = pr["nombre_curso"]
            
            if existing_course:
                # Update existing
                existing_course.nombre_curso = c["nombre_curso"]
                existing_course.escuela = "Ingeniería de Sistemas"
                existing_course.ciclo_teorico = c["ciclo_teorico"]
                existing_course.creditos = c["creditos"]
                existing_course.id_prerrequisito = c["id_prerrequisito"]
                existing_course.nombre_prerrequisito = prereq_name
                existing_course.tipo_estudio = c["tipo_estudio"]
                print(f"Actualizado curso: [{c['id_curso']}] {c['nombre_curso']}")
            else:
                # Create new
                new_c = Curso(
                    id_curso=c["id_curso"],
                    nombre_curso=c["nombre_curso"],
                    escuela="Ingeniería de Sistemas",
                    ciclo_teorico=c["ciclo_teorico"],
                    creditos=c["creditos"],
                    id_prerrequisito=c["id_prerrequisito"],
                    nombre_prerrequisito=prereq_name,
                    tipo_estudio=c["tipo_estudio"],
                    tipo_curso="Estándar",
                    es_electivo=False
                )
                db.session.add(new_c)
                print(f"Creado curso: [{c['id_curso']}] {c['nombre_curso']}")
        
        try:
            db.session.commit()
            print("\n¡Inserción de cursos completada exitosamente!")
        except Exception as e:
            db.session.rollback()
            print("Error al guardar los cursos:", e)

if __name__ == "__main__":
    insert_courses()
