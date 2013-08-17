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
    
/* UBICACIONES -arbol jerarquico PAIS/PROVINCIA/DEPARTAMENTO-  */

DELETE FROM ubicaciones;
INSERT INTO ubicaciones (id_ubicacion, descripcion, clase) VALUES (0, 'ARGENTINA', 'Pais');
 
INSERT INTO ubicaciones (id_ubicacion, descripcion, clase, id_ubicacion_padre)  
  SELECT codigo_provincia, provincia, 'Provincia', 0 
  FROM tmp.provincias ORDER BY codigo_provincia;

INSERT INTO ubicaciones (id_ubicacion, descripcion, clase, id_ubicacion_padre)
  SELECT codigo_provincia*1000 + codigo_departamento,
         departamento, 'Departamento', codigo_provincia
  FROM tmp.departamentos ORDER BY codigo_provincia, codigo_departamento;

/* circuitos - reinicio la secuencia autonumerica para el id */

ALTER SEQUENCE ubicaciones_id_ubicacion_seq RESTART 100000;

INSERT INTO ubicaciones (descripcion, clase, id_ubicacion_padre)
  SELECT DISTINCT codigo_circuito, 'Circuito', codigo_provincia*1000 + codigo_departamento
  FROM tmp.circuitos;
  
/* mesas - reinicio la secuencia autonumerica para el id */

ALTER SEQUENCE ubicaciones_id_ubicacion_seq RESTART 200000;

INSERT INTO ubicaciones (descripcion, clase, id_ubicacion_padre)
  SELECT DISTINCT codigo_mesa, 'Mesa', U.id_ubicacion
  FROM tmp.circuitos, ubicaciones U
  WHERE U.clase='Circuito' AND U.descripcion=codigo_circuito
    AND U.id_ubicacion_padre=codigo_provincia*1000 + codigo_departamento
  ORDER BY U.id_ubicacion, codigo_mesa::INTEGER;
    
COMMIT;

