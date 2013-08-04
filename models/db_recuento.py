# coding: utf8

migrate = False     # cambiar a True para crear / modificar las tablas

# base de datos de postgresql! (esquema MSA) configurar en app_settings.py

msa = DAL(PG_CNNSTR, pool_size=10)

# Constantes generales
ESTADOS = ('Pendiente', 'Recibida', 'Verificar','OK', 'Publicada')
CLASES = ('Provincia', 'Circuito', 'Localidad', 'Establecimiento', 'Mesa')

# Valores predeterminados para los formularios:
UBICACION_RAIZ = "RN"
CARGO_PRINCIPAL = "GOB"
ESTADO_FINAL = ESTADOS[-1]

# Tablas:

msa.define_table('ubicaciones',
    Field('id_ubicacion', type='string', length=12),
    Field('id_ubicacion_padre', type='string', length=12),
    Field('clase', type='string', length=30),
    Field('descripcion', type='string', length=100),
    Field('sexo', ),
    ##Field('id_partido', type=msa.partidos.id),
    primarykey=['id_ubicacion'],
    migrate=migrate)

msa.define_table('cargos',
    Field('id_cargo', type='string', length=3),
    Field('descripcion', type='string', length=50),
    Field('idx_col', type='integer'),
    Field('descripcion_corta', type='string', length=16),
    primarykey=['id_cargo'],
    migrate=migrate)

msa.define_table('listas',
    Field('id_lista', type='string', length=3),
    Field('nro_lista', type='integer'),
    Field('descripcion', type='string', length=80),
    Field('idx_fila', type='integer', unique=True),
    Field('positivo', type='boolean'),
    Field('color', type='string', length=19),
    Field('descripcion_corta', type='string', length=25),
    Field('descripcion_grafico', type='string', length=16),
    ##Field('id_partido', type='reference partidos.id_partido'),
    primarykey=['id_lista'],
    migrate=migrate)

msa.define_table('carg_list_ubic',
    Field('id_ubicacion', type=msa.ubicaciones.id_ubicacion),
    Field('id_cargo', type=msa.cargos.id_cargo),
    Field('id_lista', type=msa.listas.id_lista),
    primarykey=['id_ubicacion', 'id_cargo', 'id_lista'],
    migrate=migrate)

msa.define_table('no_cargo_ubicacion',
    Field('id_ubicacion', type='string', length=12),
    Field('id_cargo', type='string', length=3),
    primarykey=['id_ubicacion', 'id_cargo'],
    migrate=migrate)

# Recuento:

msa.define_table('planillas',
    Field('id_ubicacion', type=msa.ubicaciones.id_ubicacion),
    Field('id_planilla', type='string', length=5),
    Field('id_estado', type='string', requires=IS_IN_SET(ESTADOS)),
    Field('definitivo', 'boolean', default=False),
    Field('ciudadanos_sufragaron', type='integer'),
    primarykey=['id_planilla'],
    migrate=migrate)

msa.define_table('planillas_det',
    Field('id_planilla', type=msa.planillas.id_planilla),
    Field('id_cargo', type=msa.cargos.id_cargo),
    Field('id_lista', type=msa.listas.id_lista),
    Field('votos1', type='integer'),
    Field('votos2', type='integer'),
    Field('votos_definitivos', type='integer'),
    primarykey=['id_planilla', 'id_cargo', 'id_lista'],
    migrate=migrate)

msa.define_table('telegramas',
    Field('id', type='id'),
    Field('timestamp', type='string', length=25),
    Field('path_raw', type='upload', length=256),
    Field('pagina_raw', type='string', length=20),
    Field('imagen', type='string'), #TODO: revisar blob
    Field('id_planilla', type=msa.planillas.id_planilla),
    Field('estado', ),
    Field('observaciones', type='string', length=255),
    Field('id_reconocido', type='string', length=5),
    migrate=migrate)

# Dhondt:

msa.define_table('dhont',
    Field('id_ubicacion', type=msa.ubicaciones.id_ubicacion, ondelete='CASCADE'),
    Field('id_cargo', type=msa.cargos.id_cargo, ondelete='CASCADE'),
    Field('piso', type='double'),
    Field('bancas', type='integer'),
    Field('listas_excluidas', type='string', length=30),
    Field('listas_sin_banca', type='string', length=30),
    primarykey=['id_ubicacion', 'id_cargo'],
    migrate=migrate)


