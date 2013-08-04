BEGIN;

/* script SQL para importar datos publicos elecciones nacionales 2011 */


/* Crear tabla "temporal" de trabajo */

DROP TABLE IF EXISTS tmp_datos_publicos;
CREATE TABLE tmp_datos_publicos (
    id SERIAL,
    anio INTEGER,
    eleccion TEXT,
    provinciaId INTEGER,
    provincia TEXT,
    departamentoId INTEGER,
    departamento TEXT,
    partidoId TEXT,
    partido TEXT,
    votos TEXT
);

/* Importar datos publicos */

COPY tmp_datos_publicos (anio, eleccion, provinciaId, provincia, departamentoId, departamento, partidoId, partido, votos)
    FROM '/home/reingart/web2py/applications/recuento_web2py/private/electoral-2003-2011-completo.csv' 
    WITH ( FORMAT CSV, HEADER );

/* limpiar datos (dejar solo 2007) */

DELETE FROM tmp_datos_publicos WHERE anio != '2007' OR eleccion ILIKE '%PASO%';

/* corregir caracteres extraños en campo votos y convertir a numero entero */

UPDATE tmp_datos_publicos SET votos = REPLACE(votos, '.', '') WHERE votos LIKE '%\.%';
UPDATE tmp_datos_publicos SET votos = REPLACE(votos, 'w', '') WHERE votos LIKE '%w%';
UPDATE tmp_datos_publicos SET votos = TRIM(both ' ' FROM votos);
ALTER TABLE tmp_datos_publicos ALTER COLUMN votos TYPE INTEGER USING votos::int;

/* corregir partidos sin nro de lista (0) -buscar alguno con el mismo nombre- */

UPDATE tmp_datos_publicos SET partidoid = PP.partidoid 
FROM tmp_datos_publicos PP 
WHERE PP.partidoid != '0' 
  AND PP.partido=tmp_datos_publicos.partido 
  AND tmp_datos_publicos.partidoid='0';

/* borrar votos totales y votos positivos (datos calculables) */

DELETE FROM tmp_datos_publicos WHERE partido IN ('VOTOS POSITIVOS', 'VOTOS TOTALES');

/* unificar cargo Presidente -> PV (presidente/vice) */
UPDATE tmp_datos_publicos SET eleccion = 'PV' WHERE eleccion='Presidente';

/* convertir campo partidoid a numero entero */
ALTER TABLE tmp_datos_publicos ALTER COLUMN partidoid TYPE INTEGER USING partidoid::int;

/* ajustar partidoid (nro de lista) para que sea unívoco (cuando la lista no 
   tiene candidato a presidente, se puede repetir en distintas provincias) */

ALTER TABLE tmp_datos_publicos ADD COLUMN nro_lista TEXT; 
UPDATE tmp_datos_publicos SET nro_lista = partidoid || '@' || provinciaid 
WHERE partidoid BETWEEN 151 AND 900;
UPDATE tmp_datos_publicos SET nro_lista = partidoid 
WHERE partidoid<= 151 or partidoid> 900;


/* NORMALIZACIÓN */

/* LISTAS */

DELETE FROM listas;
ALTER SEQUENCE listas_id_lista_seq RESTART 1; /* reinicio la secuencia autonumerica */
INSERT INTO listas (nro_lista) SELECT DISTINCT nro_lista 
                               FROM  tmp_datos_publicos ORDER BY nro_lista;
UPDATE listas SET descripcion = (SELECT MIN(T.partido) FROM  tmp_datos_publicos T 
                                 WHERE T.nro_lista = listas.nro_lista);
UPDATE listas SET idx_fila = id_lista, descripcion_corta=SUBSTRING(descripcion FROM 1 FOR 25);
/* votos nulos / blancos */
UPDATE listas SET positivo = 'T' WHERE nro_lista NOT IN ('992', '991'); 
UPDATE listas SET positivo = 'F' WHERE nro_lista IN ('992', '991'); 


/* CARGOS */

DELETE FROM cargos;
ALTER SEQUENCE cargos_id_cargo_seq RESTART 1; /* reinicio la secuencia autonumerica */
INSERT INTO cargos (descripcion, descripcion_corta, idx_col) VALUES 
    ('Presidente/Vice', 'PV', 1),
    ('Senador Nacional', 'SN', 2),
    ('Diputado Nacional', 'DN', 3);

/* UBICACIONES -arbol jerarquico PAIS/PROVINCIA/DEPARTAMENTO-  */

DELETE FROM ubicaciones;
ALTER SEQUENCE ubicaciones_id_ubicacion_seq RESTART 1; /* reinicio la secuencia autonumerica */
INSERT INTO ubicaciones (descripcion, clase) VALUES ('ARGENTINA', 'Pais');
 
INSERT INTO ubicaciones (descripcion, clase, id_ubicacion_padre)  
SELECT P.provincia, 'Provincia', 1 FROM
    (SELECT DISTINCT provinciaid, provincia
     FROM tmp_datos_publicos ORDER BY provinciaid) P;

INSERT INTO ubicaciones (descripcion, clase, id_ubicacion_padre)  
SELECT D.departamento, 'Departamento', D.id_ubicacion FROM
(SELECT DISTINCT provinciaid, provincia, departamentoid, departamento, U.id_ubicacion
           FROM tmp_datos_publicos 
                INNER JOIN ubicaciones U ON U.descripcion = provincia 
                                        AND U.clase='Provincia'
           ORDER BY provinciaid, departamentoid) D;

/* PLANILLAS (datos generales de cada telegrama, debería ser por mesa...) */

DELETE FROM planillas;
ALTER SEQUENCE planillas_id_planilla_seq RESTART 1; /* reinicio la secuencia autonumerica */
INSERT INTO planillas (id_ubicacion, id_estado, definitivo, ciudadanos_sufragaron)
SELECT U.id_ubicacion, 'Publicada', 'T', SUM(votos)
  FROM tmp_datos_publicos T
  INNER JOIN ubicaciones U ON U.descripcion = T.departamento 
         AND U.id_ubicacion_padre = (SELECT UP.id_ubicacion FROM ubicaciones UP 
                                      WHERE UP.descripcion=T.provincia 
                                        AND UP.clase='Provincia')
GROUP BY U.id_ubicacion
ORDER BY U.id_ubicacion;

/* DETALLE PLANILLA (votos) */

DELETE FROM planillas_det;
ALTER SEQUENCE planillas_det_id_seq RESTART 1; /* reinicio la secuencia autonumerica */
INSERT INTO planillas_det (id_planilla, id_cargo, id_lista, votos_definitivos)
SELECT P.id_planilla, C.id_cargo, L.id_lista, T.votos
  FROM tmp_datos_publicos T
  INNER JOIN listas L ON T.nro_lista = L.nro_lista
  INNER JOIN cargos C ON T.eleccion = C.descripcion_corta
  INNER JOIN ubicaciones U ON U.descripcion = T.departamento 
         AND U.id_ubicacion_padre = (SELECT UP.id_ubicacion FROM ubicaciones UP 
                                      WHERE UP.descripcion=T.provincia 
                                        AND UP.clase='Provincia') 
  INNER JOIN planillas P on P.id_ubicacion = U.id_ubicacion
ORDER BY U.id_ubicacion;


/* Listas y cargos habilitados por ubicación (por ahora, copia de planillas) */ 

DELETE FROM carg_list_ubic;
ALTER SEQUENCE carg_list_ubic_id_seq RESTART 1; /* reinicio la secuencia autonumerica */
INSERT INTO carg_list_ubic (id_ubicacion, id_cargo, id_lista)
SELECT P.id_ubicacion, PD.id_cargo, PD.id_lista  
FROM planillas P 
INNER JOIN planillas_det PD ON P.id_planilla = PD.id_planilla;


COMMIT;

