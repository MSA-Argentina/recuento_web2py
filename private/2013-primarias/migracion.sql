BEGIN;

/* script SQL para migrar datos publicos PASO 2013 a la app de recuento */

/* correr carga.sql para importar los datos antes de ejecutar este script */

/* NORMALIZACIÓN */

/* LISTAS (ignorar ELECTORES, VOTANTES, EMPADRONADOS) */

DELETE FROM listas;
CREATE TEMP SEQUENCE idx_fila;

INSERT INTO 
  listas (id_lista, nro_lista, descripcion, descripcion_corta, positivo, idx_fila) 
  SELECT codigo_partido, codigo_partido, 
         COALESCE(lista_interna, partido), 
         SUBSTRING(COALESCE(lista_interna, partido) FROM 1 FOR 25),
         CASE WHEN codigo_partido < 9000 THEN 'T' ELSE 'F' END,
         nextval('idx_fila')
  FROM tmp.partidos 
  WHERE codigo_partido NOT IN (9001, 9002, 9007)  
  ORDER BY codigo_partido;

/* CARGOS */

DELETE FROM cargos;
ALTER SEQUENCE cargos_id_cargo_seq RESTART 1; /* reinicio la secuencia autonumerica */
INSERT INTO cargos (descripcion, descripcion_corta, idx_col) VALUES 
    /* ('Presidente/Vice', 'PV', 1), */
    ('Senador Nacional', 'SN', 2),
    ('Diputado Nacional', 'DN', 3);
    
COMMIT;

