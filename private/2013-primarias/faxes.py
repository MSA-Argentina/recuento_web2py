#!/bin/python
# coding: utf8

import psycopg2
import os

FAX_DIR = "faxes"

# abrir conexion a la base de datos:
con = psycopg2.connect(dbname="recuento")
cur = con.cursor()

cur.execute("UPDATE telegramas SET estado='Inactiva'")
        
# recorrer los faxes:
for filename in os.listdir(FAX_DIR):
    # leer la imagen:
    f = open(os.path.join(FAX_DIR, filename), "rb")
    bytes = f.read()
    f.close()    
    # extraer datos del nombre de archivo: "010010001_0001.pdf-img-000.tiff"
    prov = filename[0:2]
    dpto = filename[2:5]
    i = filename.index(".")
    mesa = filename[i-4:i]
    # busco el id_planilla / id_ubicacion según la mesa
    ##cur.execute("SELECT id_ubicacion FROM ubicaciones U WHERE clase = ...')
    id_ubicacion = 31414
    # insertar el registro en la b.d.
    print "insertando", prov, dpto, mesa, filename, len(bytes)
    cur.execute(
        "INSERT INTO telegramas (path, imagen, id_planilla, estado, ts) "
        "VALUES (%s, %s, %s, 'Activa', now())", 
        [filename, psycopg2.Binary(bytes), id_ubicacion])
    # confirmar ...
    cur.execute("commit")
    
# cerrar cursor y base de datos
cur.close()
con.close()
