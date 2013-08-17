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


/* resultados para senadores: crear tabla e importar datos publicos */

CREATE TABLE tmp.senadores (
    codigo_provincia INTEGER REFERENCES tmp.provincias(codigo_provincia),
    codigo_departamento INTEGER,
    codigo_circuito VARCHAR(5),
    codigo_mesa INTEGER,
    codigo_partido INTEGER REFERENCES tmp.partidos(codigo_partido),
    votos INTEGER NOT NULL CHECK (votos BETWEEN 0 AND 999),
    PRIMARY KEY (codigo_provincia, codigo_mesa, codigo_partido),
    FOREIGN KEY (codigo_provincia, codigo_departamento) 
     REFERENCES tmp.departamentos(codigo_provincia, codigo_departamento)
);

COPY tmp.senadores
    FROM '/home/reingart/web2py/applications/recuento_web2py/private/2013-primarias/electoral-paso-2013-senadores-01-a-02.csv' 
    WITH ( FORMAT CSV, HEADER );

COPY tmp.senadores
    FROM '/home/reingart/web2py/applications/recuento_web2py/private/2013-primarias/electoral-paso-2013-senadores-03-a-24.csv' 
    WITH ( FORMAT CSV, HEADER );


/* resultados para diputados: crear tabla e importar datos publicos */

CREATE TABLE tmp.diputados (
    codigo_provincia INTEGER REFERENCES tmp.provincias(codigo_provincia),
    codigo_departamento INTEGER,
    codigo_circuito VARCHAR(6), /* 1008.0 */
    codigo_mesa INTEGER,
    codigo_partido INTEGER REFERENCES tmp.partidos(codigo_partido),
    votos INTEGER NOT NULL CHECK (votos BETWEEN 0 AND 999),
    PRIMARY KEY (codigo_provincia, codigo_departamento, codigo_mesa, codigo_partido),
    FOREIGN KEY (codigo_provincia, codigo_departamento)
     REFERENCES tmp.departamentos(codigo_provincia, codigo_departamento)
);

COPY tmp.diputados
    FROM '/home/reingart/web2py/applications/recuento_web2py/private/2013-primarias/electoral-paso-2013-diputados-01-a-02.csv' 
    WITH ( FORMAT CSV, HEADER );

COPY tmp.diputados
    FROM '/home/reingart/web2py/applications/recuento_web2py/private/2013-primarias/electoral-paso-2013-diputados-03-a-24.csv' 
    WITH ( FORMAT CSV, HEADER );

/* elimino .0 y 0 a la izquierda en codigo de circuitos */

UPDATE tmp.senadores SET codigo_circuito = REPLACE(codigo_circuito, '.0', '') WHERE codigo_circuito LIKE '%\.%';
UPDATE tmp.diputados SET codigo_circuito = REPLACE(codigo_circuito, '.0', '') WHERE codigo_circuito LIKE '%\.%';

UPDATE tmp.senadores SET codigo_circuito = TRIM(LEADING '0' FROM codigo_circuito) WHERE codigo_circuito LIKE '0%';
UPDATE tmp.diputados SET codigo_circuito = TRIM(LEADING '0' FROM codigo_circuito) WHERE codigo_circuito LIKE '0%';


/* creo algunas vistas para extraer los circuitos */

CREATE VIEW tmp.circuitos_senadores AS 
  SELECT DISTINCT codigo_provincia, codigo_departamento, codigo_circuito, codigo_mesa FROM tmp.senadores;
CREATE VIEW tmp.circuitos_diputados AS 
  SELECT DISTINCT codigo_provincia, codigo_departamento, codigo_circuito, codigo_mesa FROM tmp.diputados;

CREATE VIEW tmp.circuitos AS 
  SELECT DISTINCT C.* FROM (SELECT * FROM tmp.circuitos_diputados UNION SELECT * FROM tmp.circuitos_senadores) C;

COMMIT;

