-- SQL Script to insert FIIS Teachers directly into the docentes table
-- Derived from the provided code block

INSERT INTO docentes (nombres, apellidos, sede_codigo, facultad, escuela_principal, correo_institucional, tipo_docente)
SELECT 'Diana Chela', 'Inga Lindo', 'SL07', 'FIIS', 'Ingeniería de Sistemas', 'dinga@unfv.edu.pe', 'Permanente'
WHERE NOT EXISTS (SELECT 1 FROM docentes WHERE correo_institucional = 'dinga@unfv.edu.pe' AND nombres = 'Diana Chela');

INSERT INTO docentes (nombres, apellidos, sede_codigo, facultad, escuela_principal, correo_institucional, tipo_docente)
SELECT 'Esther', 'Barriga', 'SL07', 'FIIS', 'Ingeniería de Sistemas', 'mbarrigar@unfv.edu.pe', 'Permanente'
WHERE NOT EXISTS (SELECT 1 FROM docentes WHERE correo_institucional = 'mbarrigar@unfv.edu.pe' AND nombres = 'Esther');

INSERT INTO docentes (nombres, apellidos, sede_codigo, facultad, escuela_principal, correo_institucional, tipo_docente)
SELECT 'Isaac', 'Sanchez Caceres', 'SL07', 'FIIS', 'Ingeniería de Sistemas', 'isanchez@unfv.edu.pe', 'Permanente'
WHERE NOT EXISTS (SELECT 1 FROM docentes WHERE correo_institucional = 'isanchez@unfv.edu.pe' AND nombres = 'Isaac');

INSERT INTO docentes (nombres, apellidos, sede_codigo, facultad, escuela_principal, correo_institucional, tipo_docente)
SELECT 'Jaime', 'Cano Espada', 'SL07', 'FIIS', 'Ingeniería de Sistemas', 'jcano@unfv.edu.pe', 'Permanente'
WHERE NOT EXISTS (SELECT 1 FROM docentes WHERE correo_institucional = 'jcano@unfv.edu.pe' AND nombres = 'Jaime');

INSERT INTO docentes (nombres, apellidos, sede_codigo, facultad, escuela_principal, correo_institucional, tipo_docente)
SELECT 'Emilio Ignacio', 'Carbonel Alhuay', 'SL07', 'FIIS', 'Ingeniería de Sistemas', 'ecarbonel@unfv.edu.pe', 'Permanente'
WHERE NOT EXISTS (SELECT 1 FROM docentes WHERE correo_institucional = 'ecarbonel@unfv.edu.pe' AND nombres = 'Emilio Ignacio');

INSERT INTO docentes (nombres, apellidos, sede_codigo, facultad, escuela_principal, correo_institucional, tipo_docente)
SELECT 'Jose Alberto', 'Huiman Sandoval', 'SL07', 'FIIS', 'Ingeniería de Sistemas', 'jhuiman@unfv.edu.pe', 'Permanente'
WHERE NOT EXISTS (SELECT 1 FROM docentes WHERE correo_institucional = 'jhuiman@unfv.edu.pe' AND nombres = 'Jose Alberto');

INSERT INTO docentes (nombres, apellidos, sede_codigo, facultad, escuela_principal, correo_institucional, tipo_docente)
SELECT 'Pablo Ernesto', 'Escobar Rodriguez', 'SL07', 'FIIS', 'Ingeniería de Sistemas', 'pescobar@unfv.edu.pe', 'Permanente'
WHERE NOT EXISTS (SELECT 1 FROM docentes WHERE correo_institucional = 'pescobar@unfv.edu.pe' AND nombres = 'Pablo Ernesto');

INSERT INTO docentes (nombres, apellidos, sede_codigo, facultad, escuela_principal, correo_institucional, tipo_docente)
SELECT 'Marleni Vilma', 'Bautista Espinoza', 'SL07', 'FIIS', 'Ingeniería de Sistemas', 'mbautista@unfv.edu.pe', 'Permanente'
WHERE NOT EXISTS (SELECT 1 FROM docentes WHERE correo_institucional = 'mbautista@unfv.edu.pe' AND nombres = 'Marleni Vilma');

INSERT INTO docentes (nombres, apellidos, sede_codigo, facultad, escuela_principal, correo_institucional, tipo_docente)
SELECT 'Henry', 'Rojas Carretero', 'SL07', 'FIIS', 'Ingeniería de Sistemas', 'hrojas@unfv.edu.pe', 'Permanente'
WHERE NOT EXISTS (SELECT 1 FROM docentes WHERE correo_institucional = 'hrojas@unfv.edu.pe' AND nombres = 'Henry');

INSERT INTO docentes (nombres, apellidos, sede_codigo, facultad, escuela_principal, correo_institucional, tipo_docente)
SELECT 'Maribel Margot', 'Huatuco Lozano', 'SL07', 'FIIS', 'Ingeniería de Sistemas', 'mhuatuco@unfv.edu.pe', 'Permanente'
WHERE NOT EXISTS (SELECT 1 FROM docentes WHERE correo_institucional = 'mhuatuco@unfv.edu.pe' AND nombres = 'Maribel Margot');

INSERT INTO docentes (nombres, apellidos, sede_codigo, facultad, escuela_principal, correo_institucional, tipo_docente)
SELECT 'Maria Renee', 'Alfaro Bardales de Ontaneda', 'SL07', 'FIIS', 'Ingeniería de Sistemas', 'malfaro@unfv.edu.pe', 'Permanente'
WHERE NOT EXISTS (SELECT 1 FROM docentes WHERE correo_institucional = 'malfaro@unfv.edu.pe' AND nombres = 'Maria Renee');

INSERT INTO docentes (nombres, apellidos, sede_codigo, facultad, escuela_principal, correo_institucional, tipo_docente)
SELECT 'Lucio', 'Jara Bautista', 'SL07', 'FIIS', 'Ingeniería de Sistemas', 'ljara@unfv.edu.pe', 'Permanente'
WHERE NOT EXISTS (SELECT 1 FROM docentes WHERE correo_institucional = 'ljara@unfv.edu.pe' AND nombres = 'Lucio');

INSERT INTO docentes (nombres, apellidos, sede_codigo, facultad, escuela_principal, correo_institucional, tipo_docente)
SELECT 'Violeta Leonor', 'Romero Carrión', 'SL07', 'FIIS', 'Ingeniería de Sistemas', 'vromero@unfv.edu.pe', 'Permanente'
WHERE NOT EXISTS (SELECT 1 FROM docentes WHERE correo_institucional = 'vromero@unfv.edu.pe' AND nombres = 'Violeta Leonor');

INSERT INTO docentes (nombres, apellidos, sede_codigo, facultad, escuela_principal, correo_institucional, tipo_docente)
SELECT 'Wilber', 'Quispe Prado', 'SL07', 'FIIS', 'Ingeniería de Sistemas', 'wquispe@unfv.edu.pe', 'Permanente'
WHERE NOT EXISTS (SELECT 1 FROM docentes WHERE correo_institucional = 'wquispe@unfv.edu.pe' AND nombres = 'Wilber');

INSERT INTO docentes (nombres, apellidos, sede_codigo, facultad, escuela_principal, correo_institucional, tipo_docente)
SELECT 'Luz Noemí', 'Ramírez', 'SL07', 'FIIS', 'Ingeniería de Sistemas', 'lramirez@unfv.edu.pe', 'Permanente'
WHERE NOT EXISTS (SELECT 1 FROM docentes WHERE correo_institucional = 'lramirez@unfv.edu.pe' AND nombres = 'Luz Noemí');

INSERT INTO docentes (nombres, apellidos, sede_codigo, facultad, escuela_principal, correo_institucional, tipo_docente)
SELECT 'Angélica Ysabel', 'Miranda Jara', 'SL07', 'FIIS', 'Ingeniería de Sistemas', 'amiranda@unfv.edu.pe', 'Permanente'
WHERE NOT EXISTS (SELECT 1 FROM docentes WHERE correo_institucional = 'amiranda@unfv.edu.pe' AND nombres = 'Angélica Ysabel');

INSERT INTO docentes (nombres, apellidos, sede_codigo, facultad, escuela_principal, correo_institucional, tipo_docente)
SELECT 'Luxi', 'Benites Cerna', 'SL07', 'FIIS', 'Ingeniería de Sistemas', 'lbenites@unfv.edu.pe', 'Permanente'
WHERE NOT EXISTS (SELECT 1 FROM docentes WHERE correo_institucional = 'lbenites@unfv.edu.pe' AND nombres = 'Luxi');

INSERT INTO docentes (nombres, apellidos, sede_codigo, facultad, escuela_principal, correo_institucional, tipo_docente)
SELECT 'Maria Luisa', 'Apolinario Peña', 'SL07', 'FIIS', 'Ingeniería de Sistemas', 'mapolinario@unfv.edu.pe', 'Permanente'
WHERE NOT EXISTS (SELECT 1 FROM docentes WHERE correo_institucional = 'mapolinario@unfv.edu.pe' AND nombres = 'Maria Luisa');

INSERT INTO docentes (nombres, apellidos, sede_codigo, facultad, escuela_principal, correo_institucional, tipo_docente)
SELECT 'Oscar', 'Benavides Cavero', 'SL07', 'FIIS', 'Ingeniería de Sistemas', 'obenavides@unfv.edu.pe', 'Permanente'
WHERE NOT EXISTS (SELECT 1 FROM docentes WHERE correo_institucional = 'obenavides@unfv.edu.pe' AND nombres = 'Oscar');

INSERT INTO docentes (nombres, apellidos, sede_codigo, facultad, escuela_principal, correo_institucional, tipo_docente)
SELECT 'José Luis', 'Bazan Briceño', 'SL07', 'FIIS', 'Ingeniería de Sistemas', 'jbazan@unfv.edu.pe', 'Permanente'
WHERE NOT EXISTS (SELECT 1 FROM docentes WHERE correo_institucional = 'jbazan@unfv.edu.pe' AND nombres = 'José Luis');

INSERT INTO docentes (nombres, apellidos, sede_codigo, facultad, escuela_principal, correo_institucional, tipo_docente)
SELECT 'Julián', 'Ccasani Allende', 'SL07', 'FIIS', 'Ingeniería de Sistemas', 'jccasani@unfv.edu.pe', 'Permanente'
WHERE NOT EXISTS (SELECT 1 FROM docentes WHERE correo_institucional = 'jccasani@unfv.edu.pe' AND nombres = 'Julián');

INSERT INTO docentes (nombres, apellidos, sede_codigo, facultad, escuela_principal, correo_institucional, tipo_docente)
SELECT 'Alí Epifanio', 'Díaz Cama', 'SL07', 'FIIS', 'Ingeniería de Sistemas', 'adiazc@unfv.edu.pe', 'Permanente'
WHERE NOT EXISTS (SELECT 1 FROM docentes WHERE correo_institucional = 'adiazc@unfv.edu.pe' AND nombres = 'Alí Epifanio');

INSERT INTO docentes (nombres, apellidos, sede_codigo, facultad, escuela_principal, correo_institucional, tipo_docente)
SELECT 'Patricia Milagros', 'Quispe Barrantes', 'SL07', 'FIIS', 'Ingeniería de Sistemas', 'pquispe@unfv.edu.pe', 'Permanente'
WHERE NOT EXISTS (SELECT 1 FROM docentes WHERE correo_institucional = 'pquispe@unfv.edu.pe' AND nombres = 'Patricia Milagros');

INSERT INTO docentes (nombres, apellidos, sede_codigo, facultad, escuela_principal, correo_institucional, tipo_docente)
SELECT 'Pedro Pablo', 'Arteaga Llacza', 'SL07', 'FIIS', 'Ingeniería de Sistemas', 'parteaga@unfv.edu.pe', 'Permanente'
WHERE NOT EXISTS (SELECT 1 FROM docentes WHERE correo_institucional = 'parteaga@unfv.edu.pe' AND nombres = 'Pedro Pablo');

INSERT INTO docentes (nombres, apellidos, sede_codigo, facultad, escuela_principal, correo_institucional, tipo_docente)
SELECT 'César Gerardo', 'León Velarde', 'SL07', 'FIIS', 'Ingeniería de Sistemas', 'cleon@unfv.edu.pe', 'Permanente'
WHERE NOT EXISTS (SELECT 1 FROM docentes WHERE correo_institucional = 'cleon@unfv.edu.pe' AND nombres = 'César Gerardo');

INSERT INTO docentes (nombres, apellidos, sede_codigo, facultad, escuela_principal, correo_institucional, tipo_docente)
SELECT 'Manuel', 'Narro Andrade', 'SL07', 'FIIS', 'Ingeniería de Sistemas', 'mnarro@unfv.edu.pe', 'Permanente'
WHERE NOT EXISTS (SELECT 1 FROM docentes WHERE correo_institucional = 'mnarro@unfv.edu.pe' AND nombres = 'Manuel');

INSERT INTO docentes (nombres, apellidos, sede_codigo, facultad, escuela_principal, correo_institucional, tipo_docente)
SELECT 'Jorge Víctor', 'Mayhuasca Guerra', 'SL07', 'FIIS', 'Ingeniería de Sistemas', 'jmayhuasca@unfv.edu.pe', 'Permanente'
WHERE NOT EXISTS (SELECT 1 FROM docentes WHERE correo_institucional = 'jmayhuasca@unfv.edu.pe' AND nombres = 'Jorge Víctor');

INSERT INTO docentes (nombres, apellidos, sede_codigo, facultad, escuela_principal, correo_institucional, tipo_docente)
SELECT 'Carmen', 'Salazar Deza', 'SL07', 'FIIS', 'Ingeniería de Sistemas', 'csalazar@unfv.edu.pe', 'Permanente'
WHERE NOT EXISTS (SELECT 1 FROM docentes WHERE correo_institucional = 'csalazar@unfv.edu.pe' AND nombres = 'Carmen');

INSERT INTO docentes (nombres, apellidos, sede_codigo, facultad, escuela_principal, correo_institucional, tipo_docente)
SELECT 'Oscar Hugo', 'Mujica Ruiz', 'SL07', 'FIIS', 'Ingeniería de Sistemas', 'omujica@unfv.edu.pe', 'Permanente'
WHERE NOT EXISTS (SELECT 1 FROM docentes WHERE correo_institucional = 'omujica@unfv.edu.pe' AND nombres = 'Oscar Hugo');

INSERT INTO docentes (nombres, apellidos, sede_codigo, facultad, escuela_principal, correo_institucional, tipo_docente)
SELECT 'Jorge Alberto', 'Vales Carrillo', 'SL07', 'FIIS', 'Ingeniería de Sistemas', 'jvales@unfv.edu.pe', 'Permanente'
WHERE NOT EXISTS (SELECT 1 FROM docentes WHERE correo_institucional = 'jvales@unfv.edu.pe' AND nombres = 'Jorge Alberto');

INSERT INTO docentes (nombres, apellidos, sede_codigo, facultad, escuela_principal, correo_institucional, tipo_docente)
SELECT 'Noemí', 'Ramírez Saavedra', 'SL07', 'FIIS', 'Ingeniería de Sistemas', 'lramirez@unfv.edu.pe', 'Permanente'
WHERE NOT EXISTS (SELECT 1 FROM docentes WHERE correo_institucional = 'lramirez@unfv.edu.pe' AND nombres = 'Noemí');

INSERT INTO docentes (nombres, apellidos, sede_codigo, facultad, escuela_principal, correo_institucional, tipo_docente)
SELECT 'Armando Ricardo', 'Huapaya Sotero', 'SL07', 'FIIS', 'Ingeniería de Sistemas', 'ahuapaya@unfv.edu.pe', 'Permanente'
WHERE NOT EXISTS (SELECT 1 FROM docentes WHERE correo_institucional = 'ahuapaya@unfv.edu.pe' AND nombres = 'Armando Ricardo');

INSERT INTO docentes (nombres, apellidos, sede_codigo, facultad, escuela_principal, correo_institucional, tipo_docente)
SELECT 'José Orlando', 'Alvarado Alvarado', 'SL07', 'FIIS', 'Ingeniería de Sistemas', 'jalvaradoa@unfv.edu.pe', 'Permanente'
WHERE NOT EXISTS (SELECT 1 FROM docentes WHERE correo_institucional = 'jalvaradoa@unfv.edu.pe' AND nombres = 'José Orlando');

INSERT INTO docentes (nombres, apellidos, sede_codigo, facultad, escuela_principal, correo_institucional, tipo_docente)
SELECT 'Heddy', 'Colca García', 'SL07', 'FIIS', 'Ingeniería de Sistemas', 'hcolca@unfv.edu.pe', 'Permanente'
WHERE NOT EXISTS (SELECT 1 FROM docentes WHERE correo_institucional = 'hcolca@unfv.edu.pe' AND nombres = 'Heddy');

INSERT INTO docentes (nombres, apellidos, sede_codigo, facultad, escuela_principal, correo_institucional, tipo_docente)
SELECT 'Luis Avelino', 'Muñoz Ramos', 'SL07', 'FIIS', 'Ingeniería de Sistemas', 'lmunozr@unfv.edu.pe', 'Permanente'
WHERE NOT EXISTS (SELECT 1 FROM docentes WHERE correo_institucional = 'lmunozr@unfv.edu.pe' AND nombres = 'Luis Avelino');

INSERT INTO docentes (nombres, apellidos, sede_codigo, facultad, escuela_principal, correo_institucional, tipo_docente)
SELECT 'Iván Carlo', 'Petrlik Azabache', 'SL07', 'FIIS', 'Ingeniería de Sistemas', 'ipetrlik@unfv.edu.pe', 'Permanente'
WHERE NOT EXISTS (SELECT 1 FROM docentes WHERE correo_institucional = 'ipetrlik@unfv.edu.pe' AND nombres = 'Iván Carlo');

INSERT INTO docentes (nombres, apellidos, sede_codigo, facultad, escuela_principal, correo_institucional, tipo_docente)
SELECT 'Luis', 'Soto Soto', 'SL07', 'FIIS', 'Ingeniería de Sistemas', 'lsotos@unfv.edu.pe', 'Permanente'
WHERE NOT EXISTS (SELECT 1 FROM docentes WHERE correo_institucional = 'lsotos@unfv.edu.pe' AND nombres = 'Luis');

INSERT INTO docentes (nombres, apellidos, sede_codigo, facultad, escuela_principal, correo_institucional, tipo_docente)
SELECT 'Javier Arturo', 'Gamboa Cruzado', 'SL07', 'FIIS', 'Ingeniería de Sistemas', 'jgamboa@unfv.edu.pe', 'Permanente'
WHERE NOT EXISTS (SELECT 1 FROM docentes WHERE correo_institucional = 'jgamboa@unfv.edu.pe' AND nombres = 'Javier Arturo');

INSERT INTO docentes (nombres, apellidos, sede_codigo, facultad, escuela_principal, correo_institucional, tipo_docente)
SELECT 'Martín Sabino', 'Gavino Ramos', 'SL07', 'FIIS', 'Ingeniería de Sistemas', 'mgavino@unfv.edu.pe', 'Permanente'
WHERE NOT EXISTS (SELECT 1 FROM docentes WHERE correo_institucional = 'mgavino@unfv.edu.pe' AND nombres = 'Martín Sabino');

INSERT INTO docentes (nombres, apellidos, sede_codigo, facultad, escuela_principal, correo_institucional, tipo_docente)
SELECT 'Santos Ciriaco', 'Sotelo Antaurco', 'SL07', 'FIIS', 'Ingeniería de Sistemas', 'ssoteloa@unfv.edu.pe', 'Permanente'
WHERE NOT EXISTS (SELECT 1 FROM docentes WHERE correo_institucional = 'ssoteloa@unfv.edu.pe' AND nombres = 'Santos Ciriaco');

INSERT INTO docentes (nombres, apellidos, sede_codigo, facultad, escuela_principal, correo_institucional, tipo_docente)
SELECT 'Carlos Miguel', 'Franco Del Carpio', 'SL07', 'FIIS', 'Ingeniería de Sistemas', 'cfranco@unfv.edu.pe', 'Permanente'
WHERE NOT EXISTS (SELECT 1 FROM docentes WHERE correo_institucional = 'cfranco@unfv.edu.pe' AND nombres = 'Carlos Miguel');

INSERT INTO docentes (nombres, apellidos, sede_codigo, facultad, escuela_principal, correo_institucional, tipo_docente)
SELECT 'Wilfredo E.', 'Carranza Barrena', 'SL07', 'FIIS', 'Ingeniería de Sistemas', 'wcarranza@unfv.edu.pe', 'Permanente'
WHERE NOT EXISTS (SELECT 1 FROM docentes WHERE correo_institucional = 'wcarranza@unfv.edu.pe' AND nombres = 'Wilfredo E.');

INSERT INTO docentes (nombres, apellidos, sede_codigo, facultad, escuela_principal, correo_institucional, tipo_docente)
SELECT 'Orestes', 'Cachay Boza', 'SL07', 'FIIS', 'Ingeniería de Sistemas', 'ocachay@unfv.edu.pe', 'Permanente'
WHERE NOT EXISTS (SELECT 1 FROM docentes WHERE correo_institucional = 'ocachay@unfv.edu.pe' AND nombres = 'Orestes');

INSERT INTO docentes (nombres, apellidos, sede_codigo, facultad, escuela_principal, correo_institucional, tipo_docente)
SELECT 'Pedro Martín', 'Lezama Gonzales', 'SL07', 'FIIS', 'Ingeniería de Sistemas', 'plezama@unfv.edu.pe', 'Permanente'
WHERE NOT EXISTS (SELECT 1 FROM docentes WHERE correo_institucional = 'plezama@unfv.edu.pe' AND nombres = 'Pedro Martín');

INSERT INTO docentes (nombres, apellidos, sede_codigo, facultad, escuela_principal, correo_institucional, tipo_docente)
SELECT 'Bertha Beatriz', 'López Juárez', 'SL07', 'FIIS', 'Ingeniería de Sistemas', 'blopez@unfv.edu.pe', 'Permanente'
WHERE NOT EXISTS (SELECT 1 FROM docentes WHERE correo_institucional = 'blopez@unfv.edu.pe' AND nombres = 'Bertha Beatriz');
