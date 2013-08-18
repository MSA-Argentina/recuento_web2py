#!/bin/python
# coding: utf8

import psycopg2
import os
import sys

FAX_DIR = sys.argv[1:] and sys.argv[1] or "faxes"

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
    # busco el id_planilla / id_ubicacion según la mesa (si existe)
    cur.execute("SELECT P.id_planilla, T.id FROM tmp.mesas M "
                " INNER JOIN planillas P ON M.id_ubicacion = P.id_ubicacion "
                " LEFT JOIN telegramas T ON T.id_planilla = P.id_planilla "
                "WHERE M.codigo_provincia=%s AND M.codigo_departamento=%s "
                "  AND M.codigo_mesa=%s", [prov, dpto, mesa])
    row = cur.fetchone()
    # si hay registros y ya esta cargado el id de telegrama, paso al siguiente:
    if row and row[1]:
        print "ya insertado", filename
        continue
    id_ubicacion = row and row[0] or None
    # insertar el registro en la b.d.
    print "insertando", prov, dpto, mesa, filename, id_ubicacion, len(bytes)
    cur.execute(
        "INSERT INTO telegramas (path, imagen, id_planilla, estado, ts) "
        "VALUES (%s, %s, %s, 'Activa', now())", 
        [filename, psycopg2.Binary(bytes), id_ubicacion])
    # confirmar ...
    cur.execute("commit")
    
# cerrar cursor y base de datos
cur.close()
con.close()
