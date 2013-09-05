# coding: utf8

migrate = False     # cambiar a True para crear / modificar las tablas

# base de datos de postgresql! (esquema MSA) configurar en app_settings.py

msa = DAL(PG_CNNSTR, pool_size=10)

# Constantes generales
ESTADOS = ['Pendiente', 'Recibida', 'Verificar','OK', 'Publicada']
CLASES = ['Pais', 'Provincia', 'Departamento', 'Circuito', 'Mesa']

# Valores predeterminados para los formularios:
UBICACION_RAIZ = 1
CARGO_PRINCIPAL = 1
ESTADO_FINAL = ESTADOS[-1]

# Tablas:

msa.define_table('ubicaciones',
    Field('id_ubicacion', type='id'),
    Field('id_ubicacion_padre', type='reference ubicaciones'),
    Field('clase', type='string', length=30),
    Field('descripcion', type='string', length=100),
    Field('sexo', ),
    ##Field('id_partido', type=msa.partidos.id),
    migrate=migrate)

msa.define_table('cargos',
    Field('id_cargo', type='id'),
    Field('descripcion', type='string', length=50),
    Field('idx_col', type='integer'),
    Field('descripcion_corta', type='string', length=16),
    migrate=migrate)

msa.define_table('partidos',
    Field('id_partido', type='id', length=3),
    Field('nro_partido', type='string', length=10),
    Field('descripcion', type='string', length=80),
    migrate=migrate)

msa.define_table('listas',
    Field('id_lista', type='id', length=3),
    Field('nro_lista', type='string', length=10),
    Field('descripcion', type='string', length=80),
    Field('idx_fila', type='integer', unique=True),
    Field('positivo', type='boolean'),
    Field('color', type='string', length=19),
    Field('descripcion_corta', type='string', length=25),
    Field('descripcion_grafico', type='string', length=16),
    Field('id_partido', type=msa.partidos),
    migrate=migrate)

msa.define_table('carg_list_ubic',
    Field('id_ubicacion', type=msa.ubicaciones),
    Field('id_cargo', type=msa.cargos),
    Field('id_lista', type=msa.listas),
    migrate=migrate)

msa.define_table('no_cargo_ubicacion',
    Field('id_ubicacion', type='string', length=12),
    Field('id_cargo', type='string', length=3),
    migrate=migrate)

# Recuento:

msa.define_table('planillas',
    Field('id_ubicacion', type=msa.ubicaciones),
    Field('id_planilla', type='id'),
    Field('id_estado', type='string', requires=IS_IN_SET(ESTADOS)),
    Field('definitivo', 'boolean', default=False),
    Field('ciudadanos_sufragaron', type='integer'),
    migrate=migrate)

msa.define_table('planillas_det',
    Field('id_planilla', type=msa.planillas),
    Field('id_cargo', type=msa.cargos),
    Field('id_lista', type=msa.listas),
    Field('votos1', type='integer'),
    Field('votos2', type='integer'),
    Field('votos_definitivos', type='integer'),
    migrate=migrate)

msa.define_table('telegramas',
    Field('id', type='id'),
    Field('ts', type='datetime', default=request.now),
    Field('path', type='upload', length=256),
    Field('imagen', type='text'),  # bytea TODO: blob_decode
    Field('id_planilla', type=msa.planillas),
    Field('estado', ),
    Field('observaciones', type='text'),
    Field('id_reconocido', type='string', length=5),
    migrate=migrate)

# Dhondt:

msa.define_table('dhont',
    Field('id_ubicacion', type=msa.ubicaciones, ondelete='CASCADE'),
    Field('id_cargo', type=msa.cargos, ondelete='CASCADE'),
    Field('piso', type='double'),
    Field('bancas', type='integer'),
    Field('listas_excluidas', type='string', length=30),
    Field('listas_sin_banca', type='string', length=30),
    migrate=migrate)


