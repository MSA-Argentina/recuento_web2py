#!/bin/bash

# Script para convertir los telegramas de documento PDF a imagen TIFF

# busco y proceso todos los archivos:
for PDF in `find -name "*.pdf"`; do
    echo "procesando $PDF"
    # extraigo la imagen del documento PDF (uso como base el mismo nombre)
    pdfimages $PDF $PDF 
    # comprimo la primer imagen -img-000 (mismo encoding ccitt grupo 4)
    ppm2tiff -c g4 $PDF-000.pbm $PDF-img-000.tiff
    # muevo a la carpeta faxes y limpio el archivo temporal
    mv $PDF-img-000.tiff faxes
    rm $PDF-000.pbm
done
