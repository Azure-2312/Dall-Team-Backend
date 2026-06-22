import os
from app import create_app
from models import db, Curso
from sqlalchemy import text

def insert_electives():
    app = create_app()
    with app.app_context():
        # 1. Load standard courses for Industrial, Agroindustria, and Transportes if they don't exist
        print("Verificando mallas curriculares estándar de otras escuelas...")
        sql_file = "mallas_adicionales.sql"
        if os.path.exists(sql_file):
            print(f"Asegurando carga de mallas estándar desde {sql_file}...")
            with open(sql_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            # Filter out comments and empty lines
            clean_lines = []
            for line in lines:
                stripped = line.strip()
                if stripped and not stripped.startswith("--"):
                    clean_lines.append(line)
            
            # Split queries by semicolon
            content = "".join(clean_lines)
            queries = content.split(";")
            
            # Execute standard courses inserts
            for query in queries:
                query = query.strip()
                if query:
                    try:
                        db.session.execute(text(query))
                    except Exception as e:
                        print(f"Error ejecutando query standard: {e}")
            try:
                db.session.commit()
                print("Mallas estándar actualizadas/cargadas correctamente.")
            except Exception as e:
                db.session.rollback()
                print("Error al confirmar la carga de mallas estándar:", e)
        else:
            print("El archivo SQL de mallas estándar no se encontró, procediendo solo con electivos.")

        # 2. Define the new elective courses to insert
        electives_to_insert = [
            # ==========================================================
            # ESCUELA: Ingeniería de Sistemas
            # ==========================================================
            # 5° CICLO (Menciones 1-5)
            {"id_curso": "CP511", "nombre_curso": "FUNDAMENTOS DE JAVA", "escuela": "Ingeniería de Sistemas", "ciclo_teorico": 5, "creditos": 2, "id_prerrequisito": "25", "tipo_estudio": "Especifico"},
            {"id_curso": "CP521", "nombre_curso": "DATABASE DESIGN", "escuela": "Ingeniería de Sistemas", "ciclo_teorico": 5, "creditos": 2, "id_prerrequisito": "25", "tipo_estudio": "Especifico"},
            {"id_curso": "CP531", "nombre_curso": "CABLEADO ESTRUCTURADO", "escuela": "Ingeniería de Sistemas", "ciclo_teorico": 5, "creditos": 2, "id_prerrequisito": "25", "tipo_estudio": "Especifico"},
            {"id_curso": "CP541", "nombre_curso": "GESTIÓN DE PROCESOS DE NEGOCIOS", "escuela": "Ingeniería de Sistemas", "ciclo_teorico": 5, "creditos": 2, "id_prerrequisito": "25", "tipo_estudio": "Especifico"},
            {"id_curso": "CP551", "nombre_curso": "ELECTRÓNICA BÁSICA Y SISTEMAS DIGITALES", "escuela": "Ingeniería de Sistemas", "ciclo_teorico": 5, "creditos": 2, "id_prerrequisito": "25", "tipo_estudio": "Especifico"},
            # 6° CICLO (Menciones 1-5)
            {"id_curso": "CP612", "nombre_curso": "PROGRAMACIÓN AVANZADA JAVA", "escuela": "Ingeniería de Sistemas", "ciclo_teorico": 6, "creditos": 2, "id_prerrequisito": "CP511", "tipo_estudio": "Especifico"},
            {"id_curso": "CP622", "nombre_curso": "PROGRAMMING WITH SQL", "escuela": "Ingeniería de Sistemas", "ciclo_teorico": 6, "creditos": 2, "id_prerrequisito": "CP521", "tipo_estudio": "Especifico"},
            {"id_curso": "CP632", "nombre_curso": "CONFIGURACIÓN DE ROUTERS Y SWITCHES", "escuela": "Ingeniería de Sistemas", "ciclo_teorico": 6, "creditos": 2, "id_prerrequisito": "CP531", "tipo_estudio": "Especifico"},
            {"id_curso": "CP642", "nombre_curso": "ANÁLISIS DE SISTEMAS: RUP Y UML", "escuela": "Ingeniería de Sistemas", "ciclo_teorico": 6, "creditos": 2, "id_prerrequisito": "CP541", "tipo_estudio": "Especifico"},
            {"id_curso": "CP652", "nombre_curso": "PROGRAMACIÓN EN ARDUINO", "escuela": "Ingeniería de Sistemas", "ciclo_teorico": 6, "creditos": 2, "id_prerrequisito": "CP551", "tipo_estudio": "Especifico"},
            # 7° CICLO (Menciones 1-5)
            {"id_curso": "CP713", "nombre_curso": "DESARROLLO DE APLICACIONES EMPRESARIALES WEB Y MÓVILES", "escuela": "Ingeniería de Sistemas", "ciclo_teorico": 7, "creditos": 2, "id_prerrequisito": "CP612", "tipo_estudio": "Especifico"},
            {"id_curso": "CP723", "nombre_curso": "PROGRAMMING WITH PL/SQL", "escuela": "Ingeniería de Sistemas", "ciclo_teorico": 7, "creditos": 2, "id_prerrequisito": "CP622", "tipo_estudio": "Especifico"},
            {"id_curso": "CP733", "nombre_curso": "INTERCONECTIVIDAD WAN", "escuela": "Ingeniería de Sistemas", "ciclo_teorico": 7, "creditos": 2, "id_prerrequisito": "CP632", "tipo_estudio": "Especifico"},
            {"id_curso": "CP743", "nombre_curso": "GESTIÓN DE PROYECTOS Y FUNDAMENTOS PMBOK", "escuela": "Ingeniería de Sistemas", "ciclo_teorico": 7, "creditos": 2, "id_prerrequisito": "CP642", "tipo_estudio": "Especifico"},
            {"id_curso": "CP753", "nombre_curso": "ROBÓTICA", "escuela": "Ingeniería de Sistemas", "ciclo_teorico": 7, "creditos": 2, "id_prerrequisito": "CP652", "tipo_estudio": "Especifico"},

            # ==========================================================
            # ESCUELA: Ingeniería Industrial
            # ==========================================================
            # 5° SEMESTRE (Menciones 1-3)
            {"id_curso": "INDCP511", "nombre_curso": "METROLOGÍA", "escuela": "Ingeniería Industrial", "ciclo_teorico": 5, "creditos": 2, "id_prerrequisito": "IND28", "tipo_estudio": "Especifico"},
            {"id_curso": "INDCP512", "nombre_curso": "SOFTWARE DE COSTOS Y PRESUPUESTOS", "escuela": "Ingeniería Industrial", "ciclo_teorico": 5, "creditos": 2, "id_prerrequisito": "IND26", "tipo_estudio": "Especifico"},
            {"id_curso": "INDCP513", "nombre_curso": "GESTIÓN POR PROCESO", "escuela": "Ingeniería Industrial", "ciclo_teorico": 5, "creditos": 2, "id_prerrequisito": "IND31", "tipo_estudio": "Especifico"},
            # 6° SEMESTRE (Menciones 1-3)
            {"id_curso": "INDCP621", "nombre_curso": "SIX SIGMA", "escuela": "Ingeniería Industrial", "ciclo_teorico": 6, "creditos": 2, "id_prerrequisito": "INDCP511", "tipo_estudio": "Especifico"},
            {"id_curso": "INDCP622", "nombre_curso": "GESTIÓN Y CONTABILIDAD GERENCIAL", "escuela": "Ingeniería Industrial", "ciclo_teorico": 6, "creditos": 2, "id_prerrequisito": "INDCP512", "tipo_estudio": "Especifico"},
            {"id_curso": "INDCP623", "nombre_curso": "INGENIERÍA DE LA PRODUCTIVIDAD", "escuela": "Ingeniería Industrial", "ciclo_teorico": 6, "creditos": 2, "id_prerrequisito": "INDCP513", "tipo_estudio": "Especifico"},
            # 7° SEMESTRE (Menciones 1-3)
            {"id_curso": "INDCP731", "nombre_curso": "SISTEMAS INTEGRADOS DE GESTIÓN", "escuela": "Ingeniería Industrial", "ciclo_teorico": 7, "creditos": 2, "id_prerrequisito": "INDCP621", "tipo_estudio": "Especifico"},
            {"id_curso": "INDCP732", "nombre_curso": "MERCADO DE CAPITALES", "escuela": "Ingeniería Industrial", "ciclo_teorico": 7, "creditos": 2, "id_prerrequisito": "INDCP622", "tipo_estudio": "Especifico"},
            {"id_curso": "INDCP733", "nombre_curso": "PRODUCTO Y ESTRATEGIA DE PRODUCCIÓN", "escuela": "Ingeniería Industrial", "ciclo_teorico": 7, "creditos": 2, "id_prerrequisito": "INDCP623", "tipo_estudio": "Especifico"},
            # 8° SEMESTRE (Electivos)
            {"id_curso": "INDE811", "nombre_curso": "INGLÉS TÉCNICO I", "escuela": "Ingeniería Industrial", "ciclo_teorico": 8, "creditos": 2, "id_prerrequisito": "IND21", "tipo_estudio": "Especifico"},
            {"id_curso": "INDE812", "nombre_curso": "AUTOMATIZACIÓN DE LA MANUFACTURA", "escuela": "Ingeniería Industrial", "ciclo_teorico": 8, "creditos": 2, "id_prerrequisito": "INDE811", "tipo_estudio": "Especifico"},
            # 9° SEMESTRE (Electivos)
            {"id_curso": "INDE921", "nombre_curso": "INGLÉS TÉCNICO II", "escuela": "Ingeniería Industrial", "ciclo_teorico": 9, "creditos": 2, "id_prerrequisito": "INDE811", "tipo_estudio": "Especifico"},
            {"id_curso": "INDE922", "nombre_curso": "CREATIVIDAD E INNOVACIÓN", "escuela": "Ingeniería Industrial", "ciclo_teorico": 9, "creditos": 2, "id_prerrequisito": "IND51", "tipo_estudio": "Especifico"},
            # 10° SEMESTRE (Electivos)
            {"id_curso": "INDE1031", "nombre_curso": "ENERGÍAS ALTERNATIVAS", "escuela": "Ingeniería Industrial", "ciclo_teorico": 10, "creditos": 2, "id_prerrequisito": "INDE921", "tipo_estudio": "Especializado"},
            {"id_curso": "INDE1032", "nombre_curso": "INGENIERÍA DE ENVASES Y EMBALAJES", "escuela": "Ingeniería Industrial", "ciclo_teorico": 10, "creditos": 2, "id_prerrequisito": "IND34", "tipo_estudio": "Especializado"},

            # ==========================================================
            # ESCUELA: Ingeniería Agroindustria
            # ==========================================================
            # CICLO V
            {"id_curso": "AGR38", "nombre_curso": "Administración para los Negocios", "escuela": "Ingeniería Agroindustria", "ciclo_teorico": 5, "creditos": 2, "id_prerrequisito": "AGR25", "tipo_estudio": "Especifico"},
            {"id_curso": "AGRCP521", "nombre_curso": "Fundamentos de Calidad", "escuela": "Ingeniería Agroindustria", "ciclo_teorico": 5, "creditos": 2, "id_prerrequisito": "AGR31", "tipo_estudio": "Especifico"},
            # CICLO VI
            {"id_curso": "AGR45", "nombre_curso": "Legislación Agroindustrial", "escuela": "Ingeniería Agroindustria", "ciclo_teorico": 6, "creditos": 2, "id_prerrequisito": "AGR38", "tipo_estudio": "Especifico"},
            {"id_curso": "AGRCP622", "nombre_curso": "Toxicología de los Alimentos", "escuela": "Ingeniería Agroindustria", "ciclo_teorico": 6, "creditos": 2, "id_prerrequisito": "AGRCP521", "tipo_estudio": "Especifico"},
            # CICLO VII
            {"id_curso": "AGR53", "nombre_curso": "Bionegocios y Manejo Forestal", "escuela": "Ingeniería Agroindustria", "ciclo_teorico": 7, "creditos": 2, "id_prerrequisito": "AGR45", "tipo_estudio": "Especifico"},
            {"id_curso": "AGRCP723", "nombre_curso": "Control de la Inocuidad", "escuela": "Ingeniería Agroindustria", "ciclo_teorico": 7, "creditos": 2, "id_prerrequisito": "AGRCP622", "tipo_estudio": "Especifico"},
            # NOVENO SEMESTRE
            {"id_curso": "AGR67", "nombre_curso": "Diseño de Plantas y Maquinarias Agroindustriales", "escuela": "Ingeniería Agroindustria", "ciclo_teorico": 9, "creditos": 2, "id_prerrequisito": None, "tipo_estudio": "Especializado"},
            {"id_curso": "AGR68", "nombre_curso": "Marketing Internacional", "escuela": "Ingeniería Agroindustria", "ciclo_teorico": 9, "creditos": 2, "id_prerrequisito": None, "tipo_estudio": "Especializado"},
            {"id_curso": "AGRE912", "nombre_curso": "Nutrición y Alimentación Humana", "escuela": "Ingeniería Agroindustria", "ciclo_teorico": 9, "creditos": 2, "id_prerrequisito": None, "tipo_estudio": "Especializado"},
            {"id_curso": "AGRE914", "nombre_curso": "Plan de Negocios Agroindustriales", "escuela": "Ingeniería Agroindustria", "ciclo_teorico": 9, "creditos": 2, "id_prerrequisito": None, "tipo_estudio": "Especializado"},
            # DÉCIMO SEMESTRE
            {"id_curso": "AGR75", "nombre_curso": "Gestión de la Producción y la Calidad", "escuela": "Ingeniería Agroindustria", "ciclo_teorico": 10, "creditos": 2, "id_prerrequisito": None, "tipo_estudio": "Especializado"},
            {"id_curso": "AGR76", "nombre_curso": "Diseño y Desarrollo de Nuevos Productos", "escuela": "Ingeniería Agroindustria", "ciclo_teorico": 10, "creditos": 2, "id_prerrequisito": None, "tipo_estudio": "Especializado"},
            {"id_curso": "AGRE1012", "nombre_curso": "Gestión de Recursos Hidrobiológicos", "escuela": "Ingeniería Agroindustria", "ciclo_teorico": 10, "creditos": 2, "id_prerrequisito": None, "tipo_estudio": "Especializado"},
            {"id_curso": "AGRE1014", "nombre_curso": "Cadenas Agroindustriales", "escuela": "Ingeniería Agroindustria", "ciclo_teorico": 10, "creditos": 2, "id_prerrequisito": None, "tipo_estudio": "Especializado"},

            # ==========================================================
            # ESCUELA: Ingeniería de Transportes
            # ==========================================================
            # MENCIÓN 1 — PROFESIONAL TÉCNICO EN GEODESIA VIAL
            {"id_curso": "TRACP511", "nombre_curso": "PLANIFICACIÓN TERRITORIAL URBANO RURAL", "escuela": "Ingeniería de Transportes", "ciclo_teorico": 5, "creditos": 2, "id_prerrequisito": "TRA32", "tipo_estudio": "Especifico"},
            {"id_curso": "TRACP612", "nombre_curso": "GEOTÉCNIA VIAL", "escuela": "Ingeniería de Transportes", "ciclo_teorico": 6, "creditos": 2, "id_prerrequisito": "TRACP511", "tipo_estudio": "Especifico"},
            {"id_curso": "TRACP713", "nombre_curso": "DISEÑO GEOMÉTRICO VIAL", "escuela": "Ingeniería de Transportes", "ciclo_teorico": 7, "creditos": 2, "id_prerrequisito": "TRACP612", "tipo_estudio": "Especifico"},
            {"id_curso": "TRAE811", "nombre_curso": "GESTIÓN DE FLOTAS DE TRANSPORTE DE CARGA TERRESTRE", "escuela": "Ingeniería de Transportes", "ciclo_teorico": 8, "creditos": 2, "id_prerrequisito": "TRA49", "tipo_estudio": "Especializado"},
            {"id_curso": "TRAE911", "nombre_curso": "MOVILIDAD URBANA SOSTENIBLE", "escuela": "Ingeniería de Transportes", "ciclo_teorico": 9, "creditos": 2, "id_prerrequisito": "TRA59", "tipo_estudio": "Especializado"},
            {"id_curso": "TRAE1011", "nombre_curso": "GOBERNABILIDAD Y GESTIÓN PÚBLICA", "escuela": "Ingeniería de Transportes", "ciclo_teorico": 10, "creditos": 2, "id_prerrequisito": "TRA45", "tipo_estudio": "Especializado"},
            # MENCIÓN 2 — PROFESIONAL TÉCNICO EN GESTIÓN LOGÍSTICA
            {"id_curso": "TRACP521", "nombre_curso": "COSTOS DEL TRANSPORTE", "escuela": "Ingeniería de Transportes", "ciclo_teorico": 5, "creditos": 2, "id_prerrequisito": "TRA26", "tipo_estudio": "Especifico"},
            {"id_curso": "TRACP622", "nombre_curso": "LOGÍSTICA DE DISTRIBUCIÓN Y TRANSPORTE", "escuela": "Ingeniería de Transportes", "ciclo_teorico": 6, "creditos": 2, "id_prerrequisito": "TRACP521", "tipo_estudio": "Especifico"},
            {"id_curso": "TRACP723", "nombre_curso": "COMERCIO INTERNACIONAL Y TRANSPORTE", "escuela": "Ingeniería de Transportes", "ciclo_teorico": 7, "creditos": 2, "id_prerrequisito": "TRACP622", "tipo_estudio": "Especifico"},
            {"id_curso": "TRAE812", "nombre_curso": "TRANSPORTE EN MINERÍA", "escuela": "Ingeniería de Transportes", "ciclo_teorico": 8, "creditos": 2, "id_prerrequisito": "TRA52", "tipo_estudio": "Especializado"},
            {"id_curso": "TRAE912", "nombre_curso": "GESTIÓN ADUANERA", "escuela": "Ingeniería de Transportes", "ciclo_teorico": 9, "creditos": 2, "id_prerrequisito": "TRA48", "tipo_estudio": "Especializado"},
            {"id_curso": "TRAE1012", "nombre_curso": "GESTIÓN DE PROYECTOS DE INGENIERÍA DE TRANSPORTE", "escuela": "Ingeniería de Transportes", "ciclo_teorico": 10, "creditos": 2, "id_prerrequisito": "TRA61", "tipo_estudio": "Especializado"},
        ]

        # First, build a map of ALL courses (both standard ones and new electives) by their id
        all_courses_by_id = {}
        for c in Curso.query.all():
            all_courses_by_id[c.id_curso] = c.nombre_curso

        # Add new electives names to the lookup map
        for c in electives_to_insert:
            all_courses_by_id[c["id_curso"]] = c["nombre_curso"]

        # Insert or update each elective course
        inserted_count = 0
        updated_count = 0
        for c in electives_to_insert:
            existing = db.session.get(Curso, c["id_curso"])
            
            # Resolve prerequisite name
            prereq_name = None
            if c["id_prerrequisito"]:
                prereq_name = all_courses_by_id.get(c["id_prerrequisito"])
                if not prereq_name:
                    print(f"Advertencia: No se encontró el nombre del prerrequisito para id {c['id_prerrequisito']}")
            
            if existing:
                existing.nombre_curso = c["nombre_curso"]
                existing.escuela = c["escuela"]
                existing.ciclo_teorico = c["ciclo_teorico"]
                existing.creditos = c["creditos"]
                existing.id_prerrequisito = c["id_prerrequisito"]
                existing.nombre_prerrequisito = prereq_name
                existing.tipo_estudio = c["tipo_estudio"]
                existing.tipo_curso = "Electivo"
                existing.es_electivo = True
                updated_count += 1
            else:
                new_c = Curso(
                    id_curso=c["id_curso"],
                    nombre_curso=c["nombre_curso"],
                    escuela=c["escuela"],
                    ciclo_teorico=c["ciclo_teorico"],
                    creditos=c["creditos"],
                    id_prerrequisito=c["id_prerrequisito"],
                    nombre_prerrequisito=prereq_name,
                    tipo_estudio=c["tipo_estudio"],
                    tipo_curso="Electivo",
                    es_electivo=True
                )
                db.session.add(new_c)
                inserted_count += 1
        
        try:
            db.session.commit()
            print(f"\n¡Proceso de inserción de electivos completado!")
            print(f" - Cursos nuevos creados: {inserted_count}")
            print(f" - Cursos existentes actualizados: {updated_count}")
        except Exception as e:
            db.session.rollback()
            print("Error al guardar los electivos:", e)

if __name__ == "__main__":
    insert_electives()
