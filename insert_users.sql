-- SQL Script to create User Accounts for each Teacher and link them in the docentes table
-- Resolves the email conflict for Noemí Ramírez Saavedra (setting to 'nramirez@unfv.edu.pe')

-- 1. Correct email for Noemí Ramírez Saavedra in docentes to avoid unique constraint conflict on usuarios.email
UPDATE docentes 
SET correo_institucional = 'nramirez@unfv.edu.pe' 
WHERE nombres = 'Noemí' AND apellidos = 'Ramírez Saavedra';

DO $$
DECLARE
    new_user_id INT;
    pass_hash VARCHAR(255) := 'scrypt:32768:8:1$pijiuEIlt7EPAVJa$e770261834e81da0e7131ba4f4af2558238f85871bf1e5c0249c799a2f2cc60992306855c2d233d0766cfdc5941fb3fe75e461cd94ad0d0fed6d1ce45972c793';
BEGIN
    -- 1. Diana Chela Inga Lindo
    IF NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'dinga@unfv.edu.pe') THEN
        INSERT INTO usuarios (username, email, password_hash, rol, activo, facultad)
        VALUES ('dinga', 'dinga@unfv.edu.pe', pass_hash, 'Docente', TRUE, 'FIIS')
        RETURNING id_usuario INTO new_user_id;

        UPDATE docentes SET id_usuario = new_user_id WHERE correo_institucional = 'dinga@unfv.edu.pe';
    END IF;

    -- 2. Esther Barriga
    IF NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'mbarrigar@unfv.edu.pe') THEN
        INSERT INTO usuarios (username, email, password_hash, rol, activo, facultad)
        VALUES ('mbarrigar', 'mbarrigar@unfv.edu.pe', pass_hash, 'Docente', TRUE, 'FIIS')
        RETURNING id_usuario INTO new_user_id;

        UPDATE docentes SET id_usuario = new_user_id WHERE correo_institucional = 'mbarrigar@unfv.edu.pe';
    END IF;

    -- 3. Isaac Sanchez Caceres
    IF NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'isanchez@unfv.edu.pe') THEN
        INSERT INTO usuarios (username, email, password_hash, rol, activo, facultad)
        VALUES ('isanchez', 'isanchez@unfv.edu.pe', pass_hash, 'Docente', TRUE, 'FIIS')
        RETURNING id_usuario INTO new_user_id;

        UPDATE docentes SET id_usuario = new_user_id WHERE correo_institucional = 'isanchez@unfv.edu.pe';
    END IF;

    -- 4. Jaime Cano Espada
    IF NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'jcano@unfv.edu.pe') THEN
        INSERT INTO usuarios (username, email, password_hash, rol, activo, facultad)
        VALUES ('jcano', 'jcano@unfv.edu.pe', pass_hash, 'Docente', TRUE, 'FIIS')
        RETURNING id_usuario INTO new_user_id;

        UPDATE docentes SET id_usuario = new_user_id WHERE correo_institucional = 'jcano@unfv.edu.pe';
    END IF;

    -- 5. Emilio Ignacio Carbonel Alhuay
    IF NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'ecarbonel@unfv.edu.pe') THEN
        INSERT INTO usuarios (username, email, password_hash, rol, activo, facultad)
        VALUES ('ecarbonel', 'ecarbonel@unfv.edu.pe', pass_hash, 'Docente', TRUE, 'FIIS')
        RETURNING id_usuario INTO new_user_id;

        UPDATE docentes SET id_usuario = new_user_id WHERE correo_institucional = 'ecarbonel@unfv.edu.pe';
    END IF;

    -- 6. Jose Alberto Huiman Sandoval
    IF NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'jhuiman@unfv.edu.pe') THEN
        INSERT INTO usuarios (username, email, password_hash, rol, activo, facultad)
        VALUES ('jhuiman', 'jhuiman@unfv.edu.pe', pass_hash, 'Docente', TRUE, 'FIIS')
        RETURNING id_usuario INTO new_user_id;

        UPDATE docentes SET id_usuario = new_user_id WHERE correo_institucional = 'jhuiman@unfv.edu.pe';
    END IF;

    -- 7. Pablo Ernesto Escobar Rodriguez
    IF NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'pescobar@unfv.edu.pe') THEN
        INSERT INTO usuarios (username, email, password_hash, rol, activo, facultad)
        VALUES ('pescobar', 'pescobar@unfv.edu.pe', pass_hash, 'Docente', TRUE, 'FIIS')
        RETURNING id_usuario INTO new_user_id;

        UPDATE docentes SET id_usuario = new_user_id WHERE correo_institucional = 'pescobar@unfv.edu.pe';
    END IF;

    -- 8. Marleni Vilma Bautista Espinoza
    IF NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'mbautista@unfv.edu.pe') THEN
        INSERT INTO usuarios (username, email, password_hash, rol, activo, facultad)
        VALUES ('mbautista', 'mbautista@unfv.edu.pe', pass_hash, 'Docente', TRUE, 'FIIS')
        RETURNING id_usuario INTO new_user_id;

        UPDATE docentes SET id_usuario = new_user_id WHERE correo_institucional = 'mbautista@unfv.edu.pe';
    END IF;

    -- 9. Henry Rojas Carretero
    IF NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'hrojas@unfv.edu.pe') THEN
        INSERT INTO usuarios (username, email, password_hash, rol, activo, facultad)
        VALUES ('hrojas', 'hrojas@unfv.edu.pe', pass_hash, 'Docente', TRUE, 'FIIS')
        RETURNING id_usuario INTO new_user_id;

        UPDATE docentes SET id_usuario = new_user_id WHERE correo_institucional = 'hrojas@unfv.edu.pe';
    END IF;

    -- 10. Maribel Margot Huatuco Lozano
    IF NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'mhuatuco@unfv.edu.pe') THEN
        INSERT INTO usuarios (username, email, password_hash, rol, activo, facultad)
        VALUES ('mhuatuco', 'mhuatuco@unfv.edu.pe', pass_hash, 'Docente', TRUE, 'FIIS')
        RETURNING id_usuario INTO new_user_id;

        UPDATE docentes SET id_usuario = new_user_id WHERE correo_institucional = 'mhuatuco@unfv.edu.pe';
    END IF;

    -- 11. Maria Renee Alfaro Bardales de Ontaneda
    IF NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'malfaro@unfv.edu.pe') THEN
        INSERT INTO usuarios (username, email, password_hash, rol, activo, facultad)
        VALUES ('malfaro', 'malfaro@unfv.edu.pe', pass_hash, 'Docente', TRUE, 'FIIS')
        RETURNING id_usuario INTO new_user_id;

        UPDATE docentes SET id_usuario = new_user_id WHERE correo_institucional = 'malfaro@unfv.edu.pe';
    END IF;

    -- 12. Lucio Jara Bautista
    IF NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'ljara@unfv.edu.pe') THEN
        INSERT INTO usuarios (username, email, password_hash, rol, activo, facultad)
        VALUES ('ljara', 'ljara@unfv.edu.pe', pass_hash, 'Docente', TRUE, 'FIIS')
        RETURNING id_usuario INTO new_user_id;

        UPDATE docentes SET id_usuario = new_user_id WHERE correo_institucional = 'ljara@unfv.edu.pe';
    END IF;

    -- 13. Violeta Leonor Romero Carrión
    IF NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'vromero@unfv.edu.pe') THEN
        INSERT INTO usuarios (username, email, password_hash, rol, activo, facultad)
        VALUES ('vromero', 'vromero@unfv.edu.pe', pass_hash, 'Docente', TRUE, 'FIIS')
        RETURNING id_usuario INTO new_user_id;

        UPDATE docentes SET id_usuario = new_user_id WHERE correo_institucional = 'vromero@unfv.edu.pe';
    END IF;

    -- 14. Wilber Quispe Prado
    IF NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'wquispe@unfv.edu.pe') THEN
        INSERT INTO usuarios (username, email, password_hash, rol, activo, facultad)
        VALUES ('wquispe', 'wquispe@unfv.edu.pe', pass_hash, 'Docente', TRUE, 'FIIS')
        RETURNING id_usuario INTO new_user_id;

        UPDATE docentes SET id_usuario = new_user_id WHERE correo_institucional = 'wquispe@unfv.edu.pe';
    END IF;

    -- 15. Luz Noemí Ramírez
    IF NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'lramirez@unfv.edu.pe') THEN
        INSERT INTO usuarios (username, email, password_hash, rol, activo, facultad)
        VALUES ('lramirez', 'lramirez@unfv.edu.pe', pass_hash, 'Docente', TRUE, 'FIIS')
        RETURNING id_usuario INTO new_user_id;

        UPDATE docentes SET id_usuario = new_user_id WHERE correo_institucional = 'lramirez@unfv.edu.pe' AND nombres = 'Luz Noemí';
    END IF;

    -- 16. Angélica Ysabel Miranda Jara
    IF NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'amiranda@unfv.edu.pe') THEN
        INSERT INTO usuarios (username, email, password_hash, rol, activo, facultad)
        VALUES ('amiranda', 'amiranda@unfv.edu.pe', pass_hash, 'Docente', TRUE, 'FIIS')
        RETURNING id_usuario INTO new_user_id;

        UPDATE docentes SET id_usuario = new_user_id WHERE correo_institucional = 'amiranda@unfv.edu.pe';
    END IF;

    -- 17. Luxi Benites Cerna
    IF NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'lbenites@unfv.edu.pe') THEN
        INSERT INTO usuarios (username, email, password_hash, rol, activo, facultad)
        VALUES ('lbenites', 'lbenites@unfv.edu.pe', pass_hash, 'Docente', TRUE, 'FIIS')
        RETURNING id_usuario INTO new_user_id;

        UPDATE docentes SET id_usuario = new_user_id WHERE correo_institucional = 'lbenites@unfv.edu.pe';
    END IF;

    -- 18. Maria Luisa Apolinario Peña
    IF NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'mapolinario@unfv.edu.pe') THEN
        INSERT INTO usuarios (username, email, password_hash, rol, activo, facultad)
        VALUES ('mapolinario', 'mapolinario@unfv.edu.pe', pass_hash, 'Docente', TRUE, 'FIIS')
        RETURNING id_usuario INTO new_user_id;

        UPDATE docentes SET id_usuario = new_user_id WHERE correo_institucional = 'mapolinario@unfv.edu.pe';
    END IF;

    -- 19. Oscar Benavides Cavero
    IF NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'obenavides@unfv.edu.pe') THEN
        INSERT INTO usuarios (username, email, password_hash, rol, activo, facultad)
        VALUES ('obenavides', 'obenavides@unfv.edu.pe', pass_hash, 'Docente', TRUE, 'FIIS')
        RETURNING id_usuario INTO new_user_id;

        UPDATE docentes SET id_usuario = new_user_id WHERE correo_institucional = 'obenavides@unfv.edu.pe';
    END IF;

    -- 20. José Luis Bazan Briceño
    IF NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'jbazan@unfv.edu.pe') THEN
        INSERT INTO usuarios (username, email, password_hash, rol, activo, facultad)
        VALUES ('jbazan', 'jbazan@unfv.edu.pe', pass_hash, 'Docente', TRUE, 'FIIS')
        RETURNING id_usuario INTO new_user_id;

        UPDATE docentes SET id_usuario = new_user_id WHERE correo_institucional = 'jbazan@unfv.edu.pe';
    END IF;

    -- 21. Julián Ccasani Allende
    IF NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'jccasani@unfv.edu.pe') THEN
        INSERT INTO usuarios (username, email, password_hash, rol, activo, facultad)
        VALUES ('jccasani', 'jccasani@unfv.edu.pe', pass_hash, 'Docente', TRUE, 'FIIS')
        RETURNING id_usuario INTO new_user_id;

        UPDATE docentes SET id_usuario = new_user_id WHERE correo_institucional = 'jccasani@unfv.edu.pe';
    END IF;

    -- 22. Alí Epifanio Díaz Cama
    IF NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'adiazc@unfv.edu.pe') THEN
        INSERT INTO usuarios (username, email, password_hash, rol, activo, facultad)
        VALUES ('adiazc', 'adiazc@unfv.edu.pe', pass_hash, 'Docente', TRUE, 'FIIS')
        RETURNING id_usuario INTO new_user_id;

        UPDATE docentes SET id_usuario = new_user_id WHERE correo_institucional = 'adiazc@unfv.edu.pe';
    END IF;

    -- 23. Patricia Milagros Quispe Barrantes
    IF NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'pquispe@unfv.edu.pe') THEN
        INSERT INTO usuarios (username, email, password_hash, rol, activo, facultad)
        VALUES ('pquispe', 'pquispe@unfv.edu.pe', pass_hash, 'Docente', TRUE, 'FIIS')
        RETURNING id_usuario INTO new_user_id;

        UPDATE docentes SET id_usuario = new_user_id WHERE correo_institucional = 'pquispe@unfv.edu.pe';
    END IF;

    -- 24. Pedro Pablo Arteaga Llacza
    IF NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'parteaga@unfv.edu.pe') THEN
        INSERT INTO usuarios (username, email, password_hash, rol, activo, facultad)
        VALUES ('parteaga', 'parteaga@unfv.edu.pe', pass_hash, 'Docente', TRUE, 'FIIS')
        RETURNING id_usuario INTO new_user_id;

        UPDATE docentes SET id_usuario = new_user_id WHERE correo_institucional = 'parteaga@unfv.edu.pe';
    END IF;

    -- 25. César Gerardo León Velarde
    IF NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'cleon@unfv.edu.pe') THEN
        INSERT INTO usuarios (username, email, password_hash, rol, activo, facultad)
        VALUES ('cleon', 'cleon@unfv.edu.pe', pass_hash, 'Docente', TRUE, 'FIIS')
        RETURNING id_usuario INTO new_user_id;

        UPDATE docentes SET id_usuario = new_user_id WHERE correo_institucional = 'cleon@unfv.edu.pe';
    END IF;

    -- 26. Manuel Narro Andrade
    IF NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'mnarro@unfv.edu.pe') THEN
        INSERT INTO usuarios (username, email, password_hash, rol, activo, facultad)
        VALUES ('mnarro', 'mnarro@unfv.edu.pe', pass_hash, 'Docente', TRUE, 'FIIS')
        RETURNING id_usuario INTO new_user_id;

        UPDATE docentes SET id_usuario = new_user_id WHERE correo_institucional = 'mnarro@unfv.edu.pe';
    END IF;

    -- 27. Jorge Víctor Mayhuasca Guerra
    IF NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'jmayhuasca@unfv.edu.pe') THEN
        INSERT INTO usuarios (username, email, password_hash, rol, activo, facultad)
        VALUES ('jmayhuasca', 'jmayhuasca@unfv.edu.pe', pass_hash, 'Docente', TRUE, 'FIIS')
        RETURNING id_usuario INTO new_user_id;

        UPDATE docentes SET id_usuario = new_user_id WHERE correo_institucional = 'jmayhuasca@unfv.edu.pe';
    END IF;

    -- 28. Carmen Salazar Deza
    IF NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'csalazar@unfv.edu.pe') THEN
        INSERT INTO usuarios (username, email, password_hash, rol, activo, facultad)
        VALUES ('csalazar', 'csalazar@unfv.edu.pe', pass_hash, 'Docente', TRUE, 'FIIS')
        RETURNING id_usuario INTO new_user_id;

        UPDATE docentes SET id_usuario = new_user_id WHERE correo_institucional = 'csalazar@unfv.edu.pe';
    END IF;

    -- 29. Oscar Hugo Mujica Ruiz
    IF NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'omujica@unfv.edu.pe') THEN
        INSERT INTO usuarios (username, email, password_hash, rol, activo, facultad)
        VALUES ('omujica', 'omujica@unfv.edu.pe', pass_hash, 'Docente', TRUE, 'FIIS')
        RETURNING id_usuario INTO new_user_id;

        UPDATE docentes SET id_usuario = new_user_id WHERE correo_institucional = 'omujica@unfv.edu.pe';
    END IF;

    -- 30. Jorge Alberto Vales Carrillo
    IF NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'jvales@unfv.edu.pe') THEN
        INSERT INTO usuarios (username, email, password_hash, rol, activo, facultad)
        VALUES ('jvales', 'jvales@unfv.edu.pe', pass_hash, 'Docente', TRUE, 'FIIS')
        RETURNING id_usuario INTO new_user_id;

        UPDATE docentes SET id_usuario = new_user_id WHERE correo_institucional = 'jvales@unfv.edu.pe';
    END IF;

    -- 31. Noemí Ramírez Saavedra (uses corrected email 'nramirez@unfv.edu.pe')
    IF NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'nramirez@unfv.edu.pe') THEN
        INSERT INTO usuarios (username, email, password_hash, rol, activo, facultad)
        VALUES ('nramirez', 'nramirez@unfv.edu.pe', pass_hash, 'Docente', TRUE, 'FIIS')
        RETURNING id_usuario INTO new_user_id;

        UPDATE docentes SET id_usuario = new_user_id WHERE correo_institucional = 'nramirez@unfv.edu.pe';
    END IF;

    -- 32. Armando Ricardo Huapaya Sotero
    IF NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'ahuapaya@unfv.edu.pe') THEN
        INSERT INTO usuarios (username, email, password_hash, rol, activo, facultad)
        VALUES ('ahuapaya', 'ahuapaya@unfv.edu.pe', pass_hash, 'Docente', TRUE, 'FIIS')
        RETURNING id_usuario INTO new_user_id;

        UPDATE docentes SET id_usuario = new_user_id WHERE correo_institucional = 'ahuapaya@unfv.edu.pe';
    END IF;

    -- 33. José Orlando Alvarado Alvarado
    IF NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'jalvaradoa@unfv.edu.pe') THEN
        INSERT INTO usuarios (username, email, password_hash, rol, activo, facultad)
        VALUES ('jalvaradoa', 'jalvaradoa@unfv.edu.pe', pass_hash, 'Docente', TRUE, 'FIIS')
        RETURNING id_usuario INTO new_user_id;

        UPDATE docentes SET id_usuario = new_user_id WHERE correo_institucional = 'jalvaradoa@unfv.edu.pe';
    END IF;

    -- 34. Heddy Colca García
    IF NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'hcolca@unfv.edu.pe') THEN
        INSERT INTO usuarios (username, email, password_hash, rol, activo, facultad)
        VALUES ('hcolca', 'hcolca@unfv.edu.pe', pass_hash, 'Docente', TRUE, 'FIIS')
        RETURNING id_usuario INTO new_user_id;

        UPDATE docentes SET id_usuario = new_user_id WHERE correo_institucional = 'hcolca@unfv.edu.pe';
    END IF;

    -- 35. Luis Avelino Muñoz Ramos
    IF NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'lmunozr@unfv.edu.pe') THEN
        INSERT INTO usuarios (username, email, password_hash, rol, activo, facultad)
        VALUES ('lmunozr', 'lmunozr@unfv.edu.pe', pass_hash, 'Docente', TRUE, 'FIIS')
        RETURNING id_usuario INTO new_user_id;

        UPDATE docentes SET id_usuario = new_user_id WHERE correo_institucional = 'lmunozr@unfv.edu.pe';
    END IF;

    -- 36. Iván Carlo Petrlik Azabache
    IF NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'ipetrlik@unfv.edu.pe') THEN
        INSERT INTO usuarios (username, email, password_hash, rol, activo, facultad)
        VALUES ('ipetrlik', 'ipetrlik@unfv.edu.pe', pass_hash, 'Docente', TRUE, 'FIIS')
        RETURNING id_usuario INTO new_user_id;

        UPDATE docentes SET id_usuario = new_user_id WHERE correo_institucional = 'ipetrlik@unfv.edu.pe';
    END IF;

    -- 37. Luis Soto Soto
    IF NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'lsotos@unfv.edu.pe') THEN
        INSERT INTO usuarios (username, email, password_hash, rol, activo, facultad)
        VALUES ('lsotos', 'lsotos@unfv.edu.pe', pass_hash, 'Docente', TRUE, 'FIIS')
        RETURNING id_usuario INTO new_user_id;

        UPDATE docentes SET id_usuario = new_user_id WHERE correo_institucional = 'lsotos@unfv.edu.pe';
    END IF;

    -- 38. Javier Arturo Gamboa Cruzado
    IF NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'jgamboa@unfv.edu.pe') THEN
        INSERT INTO usuarios (username, email, password_hash, rol, activo, facultad)
        VALUES ('jgamboa', 'jgamboa@unfv.edu.pe', pass_hash, 'Docente', TRUE, 'FIIS')
        RETURNING id_usuario INTO new_user_id;

        UPDATE docentes SET id_usuario = new_user_id WHERE correo_institucional = 'jgamboa@unfv.edu.pe';
    END IF;

    -- 39. Martín Sabino Gavino Ramos
    IF NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'mgavino@unfv.edu.pe') THEN
        INSERT INTO usuarios (username, email, password_hash, rol, activo, facultad)
        VALUES ('mgavino', 'mgavino@unfv.edu.pe', pass_hash, 'Docente', TRUE, 'FIIS')
        RETURNING id_usuario INTO new_user_id;

        UPDATE docentes SET id_usuario = new_user_id WHERE correo_institucional = 'mgavino@unfv.edu.pe';
    END IF;

    -- 40. Santos Ciriaco Sotelo Antaurco
    IF NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'ssoteloa@unfv.edu.pe') THEN
        INSERT INTO usuarios (username, email, password_hash, rol, activo, facultad)
        VALUES ('ssoteloa', 'ssoteloa@unfv.edu.pe', pass_hash, 'Docente', TRUE, 'FIIS')
        RETURNING id_usuario INTO new_user_id;

        UPDATE docentes SET id_usuario = new_user_id WHERE correo_institucional = 'ssoteloa@unfv.edu.pe';
    END IF;

    -- 41. Carlos Miguel Franco Del Carpio
    IF NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'cfranco@unfv.edu.pe') THEN
        INSERT INTO usuarios (username, email, password_hash, rol, activo, facultad)
        VALUES ('cfranco', 'cfranco@unfv.edu.pe', pass_hash, 'Docente', TRUE, 'FIIS')
        RETURNING id_usuario INTO new_user_id;

        UPDATE docentes SET id_usuario = new_user_id WHERE correo_institucional = 'cfranco@unfv.edu.pe';
    END IF;

    -- 42. Wilfredo E. Carranza Barrena
    IF NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'wcarranza@unfv.edu.pe') THEN
        INSERT INTO usuarios (username, email, password_hash, rol, activo, facultad)
        VALUES ('wcarranza', 'wcarranza@unfv.edu.pe', pass_hash, 'Docente', TRUE, 'FIIS')
        RETURNING id_usuario INTO new_user_id;

        UPDATE docentes SET id_usuario = new_user_id WHERE correo_institucional = 'wcarranza@unfv.edu.pe';
    END IF;

    -- 43. Orestes Cachay Boza
    IF NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'ocachay@unfv.edu.pe') THEN
        INSERT INTO usuarios (username, email, password_hash, rol, activo, facultad)
        VALUES ('ocachay', 'ocachay@unfv.edu.pe', pass_hash, 'Docente', TRUE, 'FIIS')
        RETURNING id_usuario INTO new_user_id;

        UPDATE docentes SET id_usuario = new_user_id WHERE correo_institucional = 'ocachay@unfv.edu.pe';
    END IF;

    -- 44. Pedro Martín Lezama Gonzales
    IF NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'plezama@unfv.edu.pe') THEN
        INSERT INTO usuarios (username, email, password_hash, rol, activo, facultad)
        VALUES ('plezama', 'plezama@unfv.edu.pe', pass_hash, 'Docente', TRUE, 'FIIS')
        RETURNING id_usuario INTO new_user_id;

        UPDATE docentes SET id_usuario = new_user_id WHERE correo_institucional = 'plezama@unfv.edu.pe';
    END IF;

    -- 45. Bertha Beatriz López Juárez
    IF NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'blopez@unfv.edu.pe') THEN
        INSERT INTO usuarios (username, email, password_hash, rol, activo, facultad)
        VALUES ('blopez', 'blopez@unfv.edu.pe', pass_hash, 'Docente', TRUE, 'FIIS')
        RETURNING id_usuario INTO new_user_id;

        UPDATE docentes SET id_usuario = new_user_id WHERE correo_institucional = 'blopez@unfv.edu.pe';
    END IF;

END $$;
