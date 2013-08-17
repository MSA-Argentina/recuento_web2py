recuento_web2py
===============

Aplicación web para procesamiento de datos electorales

[DEMO Recuento 2007!](http://www.web2py.com.ar/recuento2007)

Instalación:
------------

 1. Descargar y descomprimir el framework [web2py](http://www.web2py.com.ar/)
 2. Descargar esta aplicacion de [zip](https://github.com/MSA-Argentina/recuento_web2py/archive/master.zip)
 3. Descomprimir el zip dentro de la carpeta applications de web2py
 3. Crear una base de datos postgresql
 4. Importar los datos (ver carpeta private)
 5. Probar!

Datos de prueba:
----------------

En el [Hackaton Program.AR](http://datospublicos.gob.ar/hackatonprogramar/) 
se procesaron los set de datos electorales del futuro portal de 
[Datos Públicos](http://www.datospublicos.gov.ar/), en particular de la elección
nacional de 2007 (presidente, senadores y diputados).

Ver la carpeta private:
 * [electoral-2003-2011-completo.csv](private/electoral-2003-2011-completo.csv): set de datos completo utilizado
 * [migracion_elecciones_nacionales_2007.sql](private/migracion_elecciones_nacionales_2007.sql): script para procesamiento / normalización
 * [dump_recuento_2007.sql](private/dump_recuento_2007.sql): volcado de la base de datos ya procesada (PostgreSQL)

Sobre la aplicación:
--------------------

Esta aplicación esta basada en una demo desarrollada para un recuento definitivo provincial realizado en 2011.

Se generalizaron los esquemas de datos y consultas para que pueda ser utilizada para cualquier otro tipo de
escrutinio (nacional, provincial o municipal) y/o elecciones menores.

Se ha simplificado su estructura con fines educativos y experimentales, por lo que no contempla en principio
cuestiones de seguridad ni rendimiento.

Si bien contempla la funcionalidad de previsualización de telegramas, estos no están cargados y el nivel de
detalle de datos solo llega hasta departamento.

Para más información ver [ABOUT](ABOUT)
