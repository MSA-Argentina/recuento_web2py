BEGIN;

/* script SQL para importar datos publicos Elecciones PASO Nacionales 2013 */

/* creo un esquema para alojar las tablas "temporales" */

DROP SCHEMA IF EXISTS tmp CASCADE;
CREATE SCHEMA tmp;

/* provincias: crear tabla e importar datos publicos */

CREATE TABLE tmp.provincias (
    codigo_provincia INTEGER PRIMARY KEY,
    provincia VARCHAR(50)
);

COPY tmp.provincias
    FROM '/home/reingart/web2py/applications/recuento_web2py/private/2013-primarias/electoral-paso-2013-provincias.csv' 
    WITH ( FORMAT CSV, HEADER );

/* departamentos: crear tabla e importar datos publicos */

CREATE TABLE tmp.departamentos (
    codigo_provincia INTEGER,
    provincia VARCHAR(50),
    codigo_departamento INTEGER,
    departamento VARCHAR(50),
    PRIMARY KEY (codigo_provincia, codigo_departamento)
);

COPY tmp.departamentos
    FROM '/home/reingart/web2py/applications/recuento_web2py/private/2013-primarias/electoral-paso-2013-departamentos.csv' 
    WITH ( FORMAT CSV, HEADER );

/* partidos: crear tabla e importar datos publicos */

CREATE TABLE tmp.partidos (
    codigo_partido INTEGER PRIMARY KEY,
    partido VARCHAR(250),
    lista_interna VARCHAR(250),
    agrupacion INTEGER REFERENCES tmp.partidos(codigo_partido)
);

COPY tmp.partidos
    FROM '/home/reingart/web2py/applications/recuento_web2py/private/2013-primarias/electoral-paso-2013-partidos.csv' 
    WITH ( FORMAT CSV, HEADER );


COMMIT;

