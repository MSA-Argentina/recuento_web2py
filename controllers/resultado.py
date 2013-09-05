# coding: utf8

def index():
    "Página inical de búsqueda"
    # preparo ubicaciones a elegir: [(id_ubicacion, descripcion)]
    ubicaciones = msa(msa.ubicaciones.id_ubicacion!=None).select()
    ubicaciones = sorted([(row.id_ubicacion, "%s (%s)" % (row.descripcion, row.clase)) 
                          for row in ubicaciones] + [(None, "")])

    # busco todos las cargos y armo un diccionario {id_cargo: descripcion}
    cargos = dict([(c.id_cargo, c.descripcion) 
                   for c in msa().select(msa.cargos.ALL)])

    # armo formulario
    form = SQLFORM.factory(
        Field("id_ubicacion", "string", default=UBICACION_RAIZ,
            label="Ubicación",requires=IS_IN_SET(ubicaciones)),
        Field('id_cargo', type='string', default=CARGO_PRINCIPAL,
            label="Cargo", requires=IS_IN_SET(cargos)),
        Field('id_estado', type='string', default=ESTADO_FINAL,
            label="Estado", requires=IS_IN_SET(ESTADOS)), 
        )

    # proceso el formulario (valida si ha sido completado)
    if form.accepts(request.vars, session, keepvalues=True):
        id_ubicacion = form.vars.id_ubicacion.strip()
        id_cargo = form.vars.id_cargo
        id_partido = None #request.args[2]
        id_estado = form.vars.id_estado
        redirect(URL("reporte", args=[id_ubicacion, id_cargo, id_partido, id_estado]))

    return {'form': form}
    
def reporte():
    "Página de resultados: datos totalizados por ubicación y cargo"
    # obtengo las variables del requerimiento (URL)
    id_ubicacion = request.args[0]
    id_cargo = request.args[1]
    id_partido = None #request.args[2]
    id_estado = request.args[3]

    # obtengo los datos básicos para el encabezado del reporte
    ubicacion = msa(msa.ubicaciones.id_ubicacion==id_ubicacion).select().first()
    cargo = msa(msa.cargos.id_cargo==id_cargo).select().first()
    partido = None #msa(msa.partidos.id_partido==id_partido).select().first()

    # inicializar las variables de trabajo
    tabla_resultado = []
    dhont_votos = {}
    dhont_candidatos = {}
    tabla_dhont = {}
    listas = {}
    total = 0
    total_m = 0
    total_f = 0
    total_porc = 0
    dhont_total = 0
    dhont_bancas = None
    dhont_piso = None
    dhont_electos = {}
    
    # alias de tablas:       
    p = msa.planillas
    d = msa.planillas_det
    l = msa.listas

    # armo la consulta base
    query = p.id_planilla == d.id_planilla
    query &= d.id_lista == l.id_lista
    query &= p.id_estado == id_estado
    query &= d.id_cargo == id_cargo
    query &= l.positivo == True
    ##query &= l.id_partido == id_partido

    # armo la consulta recursiva (árbol) para tener las ubicaciones y planillas
    # (up -> ubicación padre, uh -> ubicación hija)
    # p/ el alias de cada tabla se usa el nombre de la clase (depto, mesa, etc.)
    up = msa.ubicaciones.with_alias(ubicacion.clase)
    query &= up.id_ubicacion == id_ubicacion
    for clase in CLASES[CLASES.index(ubicacion.clase)+1:]: 
        uh = msa.ubicaciones.with_alias(clase)
        query &= uh.id_ubicacion_padre == up.id_ubicacion
        up = uh
    query &= p.id_ubicacion == up.id_ubicacion
        
    # campo suma total:
    suma_votos = d.votos_definitivos.sum()
    
    # ejecuto la consulta:
    resultado = msa(query).select( 
              d.id_lista.with_alias("id_lista"),
              l.nro_lista.with_alias("nro_lista"), 
              l.descripcion.with_alias("descripcion"), 
              l.idx_fila.with_alias("idx_fila"), 
              l.descripcion_corta.with_alias("descripcion_corta"),
              l.color.with_alias("color"),
              suma_votos.with_alias("suma_votos"),
              groupby=(d.id_lista |
                        l.nro_lista | 
                        l.descripcion |
                        l.idx_fila |
                        l.descripcion_corta |
                        l.color),
              orderby= ~suma_votos | l.idx_fila
             )
    
    return msa._lastsql   # muestro query para depuración
    
    # Calculo el total y preparo datos para dhont

    for registro in resultado:
        id_lista = str(registro.id_lista)
        votos = int(registro.suma_votos or 0)
        total += votos
        total_porc += votos
        # Genero diccionarios D'Hondt para las listas positivas (resultado)
        dhont_total += votos
        if registro.nro_lista: # si no es blanco, suma al total 
            dhont_votos[id_lista] = votos
            # nesesito nombre y sexo de los catidatos!
            dhont_candidatos[id_lista] = [
                (id_lista,'%d: %s, %s Sexo: %s' % (r.termino, r.apellidos, 
                                                   r.nombres, r.sexo), r.sexo)
                 for r in []]
            
    # Calculo el dhont
    dhont_total = sum(dhont_votos.values())
    dhont_piso = 0.05
    dhont_bancas = 0 #len(dhont_candidatos.values()[0])
    dhont_electos = calcula_dhont_electos(dhont_votos, dhont_total, dhont_piso, 
                                          dhont_bancas, dhont_candidatos)
    if dhont_electos:
        tabla_dhont, dhont_electos = dhont_electos
    else:
        tabla_dhont, dhont_electos = [],[] # no ha datos disponibles

    # Genero las filas de la tabla (votos positivos)
    for registro in resultado:
        id_lista = str(registro.id_lista)
        if registro.nro_lista is not None:
            nro_lista = registro.nro_lista
        else:
            nro_lista = ''
        desc_lista = registro.descripcion
        listas[id_lista] = {'nro_lista': nro_lista, 'desc_lista': desc_lista}
        votos = registro.suma_votos  or 0
        if total_porc:
            porc = float(votos) / float(total_porc) * 100.00
            porc = '%3.2f%%' % porc
        else:
            porc = "---"
        
        bancas_obtenidas = '--'
        if id_lista in tabla_dhont:
            bancas_obtenidas = str(tabla_dhont[id_lista])
        tabla_resultado.append(dict(nro_lista=nro_lista, desc_lista=desc_lista, 
                                    votos=votos, porc=porc, 
                                    bancas_obtenidas=bancas_obtenidas))

    # devuelvo los datos a la vista
    return dict(
        tabla_resultado=tabla_resultado, 
        total=total,
        dhont_total=dhont_total,
        dhont_bancas=dhont_bancas,
        dhont_piso=dhont_piso,
        dhont_votos=dhont_votos,
        dhont_electos=dhont_electos,
        tabla_dhont=tabla_dhont,
        listas=listas,
        ubicacion=ubicacion,
        cargo=cargo,
        partido=partido,
        )


def calcula_dhont_electos(votos, total, piso, bancas, candidatos=None):
    """ 
    Calcula la cantidad de bancas obtenidas por cada lista y devuelve una lista
    de los candidatos electos teniendo en cuenta cupos por genero.

    votos: diccionario de votos. votos[lista]: Cantidad de votos para la lista
    total: total de votos. Se pasa porque podria incluir votos en blanco
    piso: porcentaje minimo de votos para participar en el D'Hont
    bancas: cantidad de bancas a repartir
    candidatos: diccionario con una lista de candidatos por cada lista que a su
                vez se compone de una tupla con los datos de los candidatos.
                candidatos[lista] = [(id candidato, descripcion, genero)]
    """
    
    # ADVERTENCIA: código experimental - no terminado ni probado
    
    sobre_piso = {}
    cocientes= {}
    resultado = {}
    electos = []

    # cortar por el piso (%)
    for k,v in votos.iteritems():
        porc = float(v) / float(total)
        if porc > piso:
            sobre_piso[k] = int(v)

    # verifico que no haya dos listas con la misma cantidad de votos:
    if len(set(sobre_piso.values())) != len(sobre_piso.values()):
        # hay empate, corresponde sorteo! (no mostrar bancas)
        return {}  #  (en blanco)

    # calculo y ordeno los cocientes
    for k,v in sobre_piso.iteritems():
        for i in range(bancas):
            coc = float(v) / float(i + 1)
            if coc not in cocientes:
                cocientes[coc] = []
            cocientes[coc].append(k)
    cocs = cocientes.keys()
    cocs.sort(reverse=True)

    ult_genero = None
    genero_acum = 0

    # busco los primeros cocientes hasta completar las bancas
    for k in cocs:
        for lista in cocientes[k]:
            if lista not in resultado:
                resultado[lista] = 0
            resultado[lista] += 1

            # Este bloque calcula el D'Hont teniendo en cuenta el cupo por genero
            if candidatos <> None:
                electo = 0

                # En el caso que los ultimos 2 sean del mismo genero busca el
                # primero de la lista que no lo sea y reinicio 
                # el contador de genero
                if genero_acum == 2:
                    while candidatos[lista][electo][2] == ult_genero:
                        electo += 1
                    genero_acum = 0

                # Si cambia el genero, reinicio el contador
                if ult_genero <> candidatos[lista][electo][2]:
                    genero_acum = 0

                # Guardo el ultimo genero
                ult_genero = candidatos[lista][electo][2]
                genero_acum += 1
                electos.append(candidatos[lista].pop(electo))

            bancas -= 1
            if bancas == 0:
                    return (resultado, electos)

    # Si me quedan bancas sin asginar, las devuelvo con clave None
    if bancas > 0:
        resultado[None] = bancas
    
    return (resultado, electos)





