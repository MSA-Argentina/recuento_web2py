# coding: utf8

import os, uuid, cStringIO


##@auth.requires_login()
def listado():
    # registros para paginaciòn
    reg_por_pagina = 100
    
    # preparo ubicaciones a elegir: [(id_ubicacion, descripcion)] 
    # solo provincias (para listar departamentos dentro de ellas)
    ubicaciones = msa(msa.ubicaciones.clase == CLASES[-2]).select()
    ubicaciones = sorted([(row.id_ubicacion, 
                           "%s (%s)" % (row.descripcion, row.clase)) 
                          for row in ubicaciones]+[(None, "")])

    form = SQLFORM.factory(
        Field("id_ubicacion", "string", 
            label="Ubicación",requires=IS_IN_SET(ubicaciones),
            default=session.id_ubicacion or UBICACION_RAIZ, ),
        Field('id_estado', type='string', 
            label="Estado", requires=IS_IN_SET([""] + list(ESTADOS)),
            default=session.id_estado or ESTADO_FINAL,),
        Field('definitivo', type='boolean', default=session.definitivo,
            label="Definitivo", comment="(datos cargados finales y revisados)"), 
        )
           
    if form.accepts(request.vars, session, keepvalues=True):
        # formulario completado correctamente
        # grabo en la sesión los datos del filtro (para paginación)
        session.id_ubicacion = form.vars.id_ubicacion.strip() 
        session.id_estado = form.vars.id_estado
        pagina = 1
        ok = True
    elif request.args:
        # cambio de pagina (link apretado)
        pagina = int(request.args[0] or 1)
        ok = True
    else:
        # formulario mal completado o primera vez
        ok = False
        
    if ok:
        # listo, q es la consulta base que voy agregando condiciones
        q = msa.ubicaciones.id_ubicacion==msa.planillas.id_ubicacion
        if session.id_ubicacion:
            q &=  msa.ubicaciones.id_ubicacion_padre == session.id_ubicacion
        if session.id_estado:
            q &= msa.planillas.id_estado==session.id_estado

        # cuento los registros y calculo la paginación:
        cant = msa(q).count()
        paginas = cant / reg_por_pagina + 1
        limitby=((pagina - 1) * reg_por_pagina, (pagina) * reg_por_pagina + 1)
        
        # obtengo los registros segun el filtro (q)
        rows = msa(q).select(
            msa.planillas.id_planilla,
            msa.ubicaciones.clase,
            msa.ubicaciones.descripcion,
            msa.planillas.id_estado,
            msa.planillas.definitivo,
            #orderby=msa.planillas.id_planilla,
            limitby=limitby,
            )
        # armo un listado con link a esta funcion
        table = SQLTABLE(rows, linkto=URL(f="cargar"), headers="fieldname:capitalize")
        response.flash = "%s registros (página %s de %s)" % (cant,pagina, paginas)
    else: 
        table = pagina = paginas = None
    return dict(form=form, table=table, pagina=pagina, paginas=paginas)


def cargar():
    "Página para cargar votos (miniatura de la planilla y campos entrada)"
    # obtengo el parámetro pasado por variable en la url
    id_planilla = request.vars.id_planilla or request.args[1]
    # busco los datos generales:
    q = msa.ubicaciones.id_ubicacion==msa.planillas.id_ubicacion
    q &= msa.planillas.id_planilla == id_planilla
    ubicacion = msa(q).select(msa.ubicaciones.ALL).first()
    planilla = msa(msa.planillas.id_planilla==id_planilla).select().first()
    # busco el detalle y armo un dict para accederlo mas facilmente por id_cargo, id_lista
    dets = msa(msa.planillas_det.id_planilla==id_planilla).select()
    detalles = dict([((det.id_cargo, det.id_lista), det.votos_definitivos) for det in dets])

    # busco recursivamente los cargo_list_ubic (jerarquias con postulantes) 
    clus = []
    id_ubicacion = planilla.id_ubicacion
    while id_ubicacion: 
        clu = msa(msa.carg_list_ubic.id_ubicacion==id_ubicacion).select()
        clus.extend(clu)
        hijo = msa(msa.ubicaciones.id_ubicacion==id_ubicacion).select().first()
        id_ubicacion = hijo.id_ubicacion_padre
    
    # armo un diccionario {(id_cargo, id_lista): id_ubicacion
    carg_list_ubics = dict([((clu.id_cargo, clu.id_lista), clu.id_ubicacion) for clu in clus])
    # armo sets de cargos y listas
    id_cargos = set([clu.id_cargo for clu in clus])
    id_listas = set([clu.id_lista for clu in clus])
    
    # busco todas las listas, las filtro y ordeno
    listas = msa().select(msa.listas.ALL)
    listas = sorted([l for l in listas if l.id_lista in id_listas], key=lambda x: x.idx_fila)
    # busco todos los cargos
    cargos = msa().select(msa.cargos.ALL)
    cargos = sorted([c for c in cargos if c.id_cargo in id_cargos], key=lambda x: x.idx_col)

    # encabezado de la tabla:
    fields = [TR(
                TD(A(IMG(_src=URL('thumbnail',args=id_planilla)), 
                        _href=URL('download',args=id_planilla), ), 
                   _width="60%", _rowspan=len(listas)+1),
                TH("Nº"),
                TH("Descripción"),
                [TH(cargo.descripcion_corta)
                    for cargo in cargos],
            )]
    # recorro las listas y cargos armando la tabla
    for lista in listas:
        fields.extend([
            TR(
                TD(lista.nro_lista or ''),
                TD(lista.descripcion_corta), [TD(
                    (cargo.id_cargo, lista.id_lista) in carg_list_ubics
                    and INPUT(requires=IS_EMPTY_OR(IS_INT_IN_RANGE(0,400)),
                              _name='voto.%s.%s' % (cargo.id_cargo, lista.id_lista), 
                              _value=detalles.get((cargo.id_cargo, lista.id_lista), ""), 
                              _size="3", _style="width: 30px;")
                    or "") 
                    for cargo in cargos],
            )])
    fields.append(TR(TD(INPUT(_type="submit"), _colspan=3+len(id_cargos), 
                                               _style="text-align: center;")))
    
    # armo el formulario
    form = FORM(TABLE(fields, _class="compacta", _width="100%", 
                              _cellpadding="0", _cellspacing="0", 
                              _style="padding: 0; margin: 0;"), 
                      _style="padding: 0; margin: 0;")

    # valido el formulario:
    if form.accepts(request.vars, session):
        # recorro los campos del formulario y guardo:
        for var in form.vars.keys():
            if "." in var:
                # divido el nombre del campo (ver INPUT)
                n, id_cargo, id_lista = var.split(".")  
                # obtengo el valor ingresado para este campo
                val = form.vars[var]
                # busco el registro actual para actualizarlo (si existe)
                q  = msa.planillas_det.id_planilla==planilla.id_planilla
                q &= msa.planillas_det.id_cargo==id_cargo
                q &= msa.planillas_det.id_lista==id_lista
                # actualizao el registro (si no existe devuelve 0 filas)
                affected = msa(q).update(votos_definitivos=val)
                if not affected:                                    
                    # inserto el registro ya que no existe
                    msa.planillas_det.insert(
                        id_planilla=planilla.id_planilla,
                        id_cargo=id_cargo, id_lista=id_lista,
                        votos_definitivos=val)
        # marco la planilla como definitivo
        msa(msa.planillas.id_planilla==planilla.id_planilla).update(definitivo=True)
        # mesnaje para el usuario y redirijo al listado
        session.flash = "Planilla %s (%s %s) aceptada!" % ( 
                         id_planilla, ubicacion.clase, ubicacion.descripcion)
        redirect(URL("listado"))
    elif form.errors:
        response.flash = 'revise los errores!'

    return dict(planilla=planilla, ubicacion=ubicacion, detalles=detalles, 
                form=form)


def download():
    "Descargar la imágen del telegraa que corresponde a la planilla de votos"
    # obtengo el parámetro pasado por variable en la url
    id_planilla = request.args[0]
    # busco la imagen del telegrama para la planilla:
    q = msa.telegramas.id_planilla==id_planilla
    q &= msa.telegramas.estado=='Activa'
    img = msa(q).select().first()
    # establezco los encabezados para la descarga
    response.headers['Content-Disposition']='attachment; filename=%s.tiff' % id_planilla
    response.headers['Content-Type']='image/tiff'
    #response.headers['Last-Modified'] = mtime 
    response.headers['Pragma'] = 'cache' 
    response.headers['Cache-Control'] = 'private' 
    stream = cStringIO.StringIO(img.imagen)
    # devuelvo el flujo a los datos crusds  de la imagen (para descargas parciales)
    return response.stream(stream, request=request) 


def thumbnail():
    "Descargar una miniatura del teleagrama para la planilla de votos"
    # obtengo el parámetro pasado por variable en la url
    id_planilla = request.args[0]
    # ancho y alto máximo
    nx, ny = 500, 3000
    # busco la imagen del telegrama para la planilla:
    q = msa.telegramas.id_planilla==id_planilla
    q &= msa.telegramas.estado=='Activa'
    img = msa(q).select().first()
    if img:
        # redimensiono la imagen (en memoria, usando Python Imaging Library)
        from PIL import Image
        im=Image.open(cStringIO.StringIO(img.imagen))   
        im.thumbnail((nx,ny), Image.ANTIALIAS) 
        s=cStringIO.StringIO() 
        # y la convierto de formato 
        im.save(s, 'PNG', quality=86) 
        s.seek(0)
        png = s.getvalue() 
    else:
        f = open(os.path.join(request.folder, 'private', 'sintelegrama.png'))
        png = f.read()
        f.close()
    # establezco los encabezados para la descarga
    response.headers['Content-Disposition']='attachment; filename=%s.png' % id_planilla
    response.headers['Content-Type']='image/png'
    # devuelvo los datos de la imagen
    return png

