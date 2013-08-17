BEGIN;

/* script SQL para migrar datos publicos PASO 2013 a la app de recuento */

/* correr carga.sql para importar los datos antes de ejecutar este script */

/* elimintar todos los resultados previos para acelerar la importación */

TRUNCATE planillas CASCADE;
TRUNCATE carg_list_ubic CASCADE;

/* NORMALIZACIÓN */

/* PARTIDOS (aka agrupaciones, ignorar ELECTORES, VOTANTES, EMPADRONADOS) */

DELETE FROM partidos;
INSERT INTO 
  partidos (id_partido, nro_partido, descripcion) 
  SELECT DISTINCT agrupacion, agrupacion, partido
  FROM tmp.partidos 
  WHERE codigo_partido NOT IN (9001, 9002, 9007)
  ORDER BY agrupacion;
  
/* LISTAS (ignorar ELECTORES, VOTANTES, EMPADRONADOS) */

DELETE FROM listas;
CREATE TEMP SEQUENCE idx_fila;

INSERT INTO 
  listas (id_lista, nro_lista, descripcion, descripcion_corta, positivo, idx_fila, id_partido) 
  SELECT codigo_partido, 
         CASE WHEN codigo_partido < 9000 THEN agrupacion ELSE NULL END, 
         COALESCE(lista_interna, partido), 
         SUBSTRING(COALESCE(lista_interna, partido) FROM 1 FOR 25),
         CASE WHEN codigo_partido < 9000 THEN 'T'  /* agrupaciones */
              WHEN codigo_partido = 9004 THEN 'T'  /* votos en blanco */
              ELSE 'F' END,
         nextval('idx_fila'), agrupacion
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
  FROM tmp.mesas;
  
/* mesas - reinicio la secuencia autonumerica para el id */

ALTER SEQUENCE ubicaciones_id_ubicacion_seq RESTART 200000;

INSERT INTO ubicaciones (descripcion, clase, id_ubicacion_padre)
  SELECT DISTINCT codigo_mesa, 'Mesa', U.id_ubicacion
  FROM tmp.mesas, ubicaciones U
  WHERE U.clase='Circuito' AND U.descripcion=codigo_circuito
    AND U.id_ubicacion_padre = codigo_provincia*1000 + codigo_departamento
  ORDER BY U.id_ubicacion, codigo_mesa::INTEGER;

/* actualizo tabla temporal de mesas para simplificar consultas de inserción */

UPDATE tmp.mesas SET id_ubicacion = M.id_ubicacion
  FROM ubicaciones M INNER JOIN ubicaciones C 
                             ON M.id_ubicacion_padre = C.id_ubicacion
  WHERE tmp.mesas.codigo_mesa = M.descripcion::INTEGER
    AND M.clase = 'Mesa'
    AND C.clase = 'Circuito'
    AND C.id_ubicacion_padre = codigo_provincia*1000 + codigo_departamento;

/* PLANILLAS (datos generales de cada telegrama) */

DELETE FROM planillas;
ALTER SEQUENCE planillas_id_planilla_seq RESTART 1; 
INSERT INTO planillas (id_ubicacion, id_estado, definitivo)
     SELECT T.id_ubicacion, 'Publicada', 'F'
     FROM tmp.mesas T;

/* DETALLE PLANILLA (resultados: votos para sendores y diputados nacionales) */

ALTER SEQUENCE planillas_det_id_seq RESTART 1;

INSERT INTO planillas_det (id_planilla, id_cargo, id_lista, votos_definitivos)
  SELECT P.id_planilla, C.id_cargo, L.id_lista, T.votos
  FROM tmp.senadores T INNER JOIN tmp.mesas M 
                               ON T.codigo_mesa = M.codigo_mesa
                              AND T.codigo_departamento = M.codigo_departamento
                              AND T.codigo_provincia = M.codigo_provincia
                       INNER JOIN planillas P ON P.id_ubicacion = M.id_ubicacion
                       INNER JOIN cargos C ON C.descripcion_corta = 'SN'
                       INNER JOIN listas L ON L.id_lista = T.codigo_partido
  ORDER BY P.id_ubicacion, T.codigo_partido;

INSERT INTO planillas_det (id_planilla, id_cargo, id_lista, votos_definitivos)
  SELECT P.id_planilla, C.id_cargo, L.id_lista, T.votos
  FROM tmp.diputados T INNER JOIN tmp.mesas M 
                               ON T.codigo_mesa = M.codigo_mesa
                              AND T.codigo_departamento = M.codigo_departamento
                              AND T.codigo_provincia = M.codigo_provincia
                       INNER JOIN planillas P ON P.id_ubicacion = M.id_ubicacion
                       INNER JOIN cargos C ON C.descripcion_corta = 'DN'
                       INNER JOIN listas L ON L.id_lista = T.codigo_partido
  ORDER BY P.id_ubicacion, T.codigo_partido;

/* Listas y cargos habilitados por ubicación (por ahora, copia de planillas) */ 

DELETE FROM carg_list_ubic;
ALTER SEQUENCE carg_list_ubic_id_seq RESTART 1;
INSERT INTO carg_list_ubic (id_ubicacion, id_cargo, id_lista)
  SELECT P.id_ubicacion, PD.id_cargo, PD.id_lista  
    FROM planillas P 
         INNER JOIN planillas_det PD ON P.id_planilla = PD.id_planilla;

COMMIT;

