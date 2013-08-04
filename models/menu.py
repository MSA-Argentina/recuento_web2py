# -*- coding: utf-8 -*- 

#########################################################################
## Customize your APP title, subtitle and menus here
#########################################################################

response.title = TITULO
response.subtitle = SUBTITULO
response.meta.author = 'Mariano Reingart <reingart@gmail.com>'
response.meta.description = 'Aplicación para procesamiento de datos electorales'
response.meta.keywords = 'elecciones recuento resultado carga definitivo'

##########################################
## this is the main application menu
## add/remove items as required
##########################################

response.menu = [
    (T('Index'), False, URL(request.application,'default','index'), []),
    (T('Consultas'), False, URL(request.application,'definitivo','listado'), []),
    (T('Resultado'), False, URL(request.application,'resultado','index'), []),
    ]

##########################################
## this is here to provide shortcuts
## during development. remove in production 
##
## mind that plugins may also affect menu
##########################################

response.menu+=[
    (T('Admin'), False, URL('admin', 'default', 'design/%s' % request.application),
     [
            (T('Configuración'), False, 
             URL('admin', 'default', 'edit/%s/models/app_settings.py' \
                     % (request.application,))), 
            (T('Database'), False, 
             URL(request.application, 'appadmin', 'index')),
            ]
   ),
  ]
