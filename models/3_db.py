# -*- coding: utf-8 -*-

__author__ = "Alan Edmundo Etkin <spametki@gmail.com>"
__copyright__ = "(C) 2024 Alan Edmundo Etkin. GNU GPL 3."

###########################################
# Código de la app de andamiaje de web2py #
###########################################

# -------------------------------------------------------------------------
# AppConfig configuration made easy. Look inside private/appconfig.ini
# Auth is for authenticaiton and access control
# -------------------------------------------------------------------------
from gluon.contrib.appconfig import AppConfig
from gluon.tools import Auth

# -------------------------------------------------------------------------
# This scaffolding model makes your app work on Google App Engine too
# File is released under public domain and you can use without limitations
# -------------------------------------------------------------------------

if request.global_settings.web2py_version < "2.15.5":
    raise HTTP(500, "Requires web2py 2.15.5 or newer")

# -------------------------------------------------------------------------
# if SSL/HTTPS is properly configured and you want all HTTP requests to
# be redirected to HTTPS, uncomment the line below:
# -------------------------------------------------------------------------
# request.requires_https()

# -------------------------------------------------------------------------
# once in production, remove reload=True to gain full speed
# -------------------------------------------------------------------------
configuration = AppConfig(reload=True)

if not request.env.web2py_runtime_gae:
    # ---------------------------------------------------------------------
    # if NOT running on Google App Engine use SQLite or other DB
    # ---------------------------------------------------------------------
    db = DAL(configuration.get('db.uri'),
             pool_size=configuration.get('db.pool_size'),
             migrate_enabled=configuration.get('db.migrate'),
             check_reserved=['all'])
else:
    # ---------------------------------------------------------------------
    # connect to Google BigTable (optional 'google:datastore://namespace')
    # ---------------------------------------------------------------------
    db = DAL('google:datastore+ndb')
    # ---------------------------------------------------------------------
    # store sessions and tickets there
    # ---------------------------------------------------------------------
    session.connect(request, response, db=db)
    # ---------------------------------------------------------------------
    # or store session in Memcache, Redis, etc.
    # from gluon.contrib.memdb import MEMDB
    # from google.appengine.api.memcache import Client
    # session.connect(request, response, db = MEMDB(Client()))
    # ---------------------------------------------------------------------

# -------------------------------------------------------------------------
# by default give a view/generic.extension to all actions from localhost
# none otherwise. a pattern can be 'controller/function.extension'
# -------------------------------------------------------------------------
response.generic_patterns = [] 
if request.is_local and not configuration.get('app.production'):
    response.generic_patterns.append('*')

# -------------------------------------------------------------------------
# choose a style for forms
# -------------------------------------------------------------------------
response.formstyle = 'bootstrap4_inline'
response.form_label_separator = ''

# -------------------------------------------------------------------------
# (optional) optimize handling of static files
# -------------------------------------------------------------------------
# response.optimize_css = 'concat,minify,inline'
# response.optimize_js = 'concat,minify,inline'

# -------------------------------------------------------------------------
# (optional) static assets folder versioning
# -------------------------------------------------------------------------
# response.static_version = '0.0.0'

# -------------------------------------------------------------------------
# Here is sample code if you need for
# - email capabilities
# - authentication (registration, login, logout, ... )
# - authorization (role based authorization)
# - services (xml, csv, json, xmlrpc, jsonrpc, amf, rss)
# - old style crud actions
# (more options discussed in gluon/tools.py)
# -------------------------------------------------------------------------

# host names must be a list of allowed host names (glob syntax allowed)
auth = Auth(db, host_names=configuration.get('host.names'))

# -------------------------------------------------------------------------
# create all tables needed by auth, maybe add a list of extra fields
# -------------------------------------------------------------------------
auth.settings.extra_fields['auth_user'] = []
auth.define_tables(username=False, signature=False)

# -------------------------------------------------------------------------
# configure email
# -------------------------------------------------------------------------
mail = auth.settings.mailer
mail.settings.server = 'logging' if request.is_local else configuration.get('smtp.server')
mail.settings.sender = configuration.get('smtp.sender')
mail.settings.login = configuration.get('smtp.login')
mail.settings.tls = configuration.get('smtp.tls') or False
mail.settings.ssl = configuration.get('smtp.ssl') or False

# -------------------------------------------------------------------------
# configure auth policy
# -------------------------------------------------------------------------
auth.settings.registration_requires_verification = False
auth.settings.registration_requires_approval = False
auth.settings.reset_password_requires_verification = True

# -------------------------------------------------------------------------  
# read more at http://dev.w3.org/html5/markup/meta.name.html               
# -------------------------------------------------------------------------
response.meta.author = configuration.get('app.author')
response.meta.description = configuration.get('app.description')
response.meta.keywords = configuration.get('app.keywords')
response.meta.generator = configuration.get('app.generator')
response.show_toolbar = configuration.get('app.toolbar')

# -------------------------------------------------------------------------
# your http://google.com/analytics id                                      
# -------------------------------------------------------------------------
response.google_analytics_id = configuration.get('google.analytics_id')

# -------------------------------------------------------------------------
# maybe use the scheduler
# -------------------------------------------------------------------------
if configuration.get('scheduler.enabled'):
    from gluon.scheduler import Scheduler
    scheduler = Scheduler(db, heartbeat=configuration.get('scheduler.heartbeat'))

# -------------------------------------------------------------------------
# Define your tables below (or better in another model file) for example
#
# >>> db.define_table('mytable', Field('myfield', 'string'))
#
# Fields can be 'string','text','password','integer','double','boolean'
#       'date','time','datetime','blob','upload', 'reference TABLENAME'
# There is an implicit 'id integer autoincrement' field
# Consult manual for more options, validators, etc.
#
# More API examples for controllers:
#
# >>> db.mytable.insert(myfield='value')
# >>> rows = db(db.mytable.myfield == 'value').select(db.mytable.ALL)
# >>> for row in rows: print row.id, row.myfield
# -------------------------------------------------------------------------

# -------------------------------------------------------------------------
# after defining tables, uncomment below to enable auditing
# -------------------------------------------------------------------------
# auth.enable_record_versioning(db)

###########################
# código de la aplicación #
###########################

#### Definiciones de tablas de la aplicación

db.define_table("asignatura",
               Field("titulo", "integer", requires=IS_EMPTY_OR(IS_IN_SET(PLAN_ABREVIACIONES)),
               label="Plan",
               compute=plan_establecer),
               Field("nivel", "integer",
               requires=IS_IN_SET(NIVELES)),
               Field("materia",
               requires=IS_IN_SET(MATERIAS)),
               Field("division",
               requires=IS_EMPTY_OR(IS_IN_SET(DIVISIONES))),
               Field("cuatrimestral", "boolean"),
               Field("cuatrimestre", "integer", 
                     requires=IS_EMPTY_OR(IS_IN_SET(
                     CUATRIMESTRES))),
               Field("comision", requires=IS_EMPTY_OR(IS_IN_SET(COMISIONES))),
               Field("turno", requires=IS_IN_SET(TURNOS)),
               Field("contraturno", requires=IS_EMPTY_OR(IS_IN_SET(TURNOS)),
                     default=None,
                     comment="Turno de cursada. Dejar en blanco si se cursa en igual horario"),
               # lista de horas en números
               Field("lunes", type="list:integer", comment="Lista de horas de clase",
               label=DIAS_ROTULOS[0].capitalize()),
               Field("martes", type="list:integer", comment="Lista de horas de clase",
               label=DIAS_ROTULOS[1].capitalize()),
               Field("miercoles", type="list:integer", comment="Lista de horas de clase",
               label=DIAS_ROTULOS[2].capitalize()),
               Field("jueves", type="list:integer", comment="Lista de horas de clase",
               label=DIAS_ROTULOS[3].capitalize()),
               Field("viernes", type="list:integer", comment="Lista de horas de clase",
               label=DIAS_ROTULOS[4].capitalize()),
               Field("sabado", type="list:integer", comment="Lista de horas de clase",
               label=DIAS_ROTULOS[5].capitalize()),
               Field("domingo", type="list:integer", comment="Lista de horas de clase",
               label=DIAS_ROTULOS[6].capitalize()),
               Field("detalle"))

db.define_table("docente", Field("nombre"),
                Field("documento_tipo",
                requires=IS_IN_SET(DOCUMENTOS)),
                Field("documento_numero"),
                Field("mail"),
               format="%(nombre)s")

db.define_table("estudiante",
                Field("nombre"),
                Field("documento_tipo",
                requires=IS_IN_SET(DOCUMENTOS)),
                Field("documento_numero"),
                # ciclo de primera inscripción
                Field("ingreso", "integer",
                default=CICLOS[1], requires=IS_IN_SET(CICLOS)),
                Field("fecha_nacimiento", "date"),
                Field("lugar_nacimiento"),
                Field("nacionalidad"),
                Field("genero",
                requires=IS_IN_SET(GENEROS),
                label="Género"),
                Field("domicilio_direccion"),
                Field("domicilio_localidad"),
                Field("domicilio_partido"),
                Field("domicilio_provincia"),
                # piso, departamento y otras informaciones
                Field("domicilio_datos"),
                Field("domicilio_cp"),
                Field("telefono"),
                Field("mail"),
                Field("responsable_nombre"),
                Field("responsable_documento_tipo",
                requires=IS_IN_SET(DOCUMENTOS)),
                Field("responsable_documento_numero"),
                Field("responsable_domicilio_direccion"),
                Field("responsable_domicilio_localidad"),
                Field("responsable_domicilio_partido"),
                Field("responsable_domicilio_provincia"),                
                # piso, departamento y otras informaciones
                Field("responsable_domicilio_datos"),
                Field("responsable_domicilio_cp"),
                Field("responsable_telefono"),
                Field("responsable_mail"),
                Field("observaciones", "text"),
               format="%(nombre)s")
                
db.define_table("inscripcion",
                Field("estudiante",
                "reference estudiante"),
                Field("ciclo", "integer", 
                      requires=IS_IN_SET(CICLOS)),
                Field("fecha", "date", default=request.now),
                Field("turno", requires=IS_IN_SET(TURNOS)),
                Field("nivel", "integer",
                      requires=IS_IN_SET(NIVELES)),
                Field("division",
                requires=IS_IN_SET(DIVISIONES)),
                Field("baja", "boolean", default=False),
                Field("baja_motivo", "string"),
                Field("baja_fecha", "date"),
                Field("observaciones", "text"))

db.define_table("concepto",
                Field("ciclo", "integer", requires=IS_IN_SET(CICLOS)),
                Field("turno", requires=IS_IN_SET(TURNOS)),
                Field("nivel", "integer", requires=IS_IN_SET(NIVELES)),
                Field("division", requires=IS_IN_SET(DIVISIONES)),
                Field("boletin", "integer",
                requires=IS_IN_SET(BOLETINES)),
                Field("inscripciones", "list:reference inscripcion"),
                Field("concepto_01", "list:string"),
                Field("concepto_02", "list:string"),
                Field("concepto_03", "list:string"),
                Field("concepto_04", "list:string"),
                Field("concepto_05", "list:string"),
                Field("concepto_06", "list:string"),
                Field("concepto_07", "list:string"),
                Field("concepto_08", "list:string"),
                Field("concepto_09", "list:string"),
                Field("concepto_10", "list:string"))

db.define_table("calificacion",
                Field("estudiante", "reference estudiante"),
                Field("titulo", "integer", requires=IS_EMPTY_OR(IS_IN_SET(PLAN_ABREVIACIONES)),
                label="Plan",
                compute=plan_establecer),
                Field("materia",
                requires=IS_EMPTY_OR(IS_IN_SET(MATERIAS))),
                Field("nivel",
                requires=IS_EMPTY_OR(IS_IN_SET(NIVELES))),                
                Field("ciclo", "integer",
                requires=IS_IN_SET(CICLOS)),
                Field("turno",
                requires=IS_EMPTY_OR(IS_IN_SET(TURNOS))),
                Field("division",
                requires=IS_EMPTY_OR(IS_IN_SET(DIVISIONES))),
                Field("comision", requires=IS_EMPTY_OR(IS_IN_SET(COMISIONES))),
                Field("cuatrimestre", "integer",
                      requires=IS_EMPTY_OR(IS_IN_SET(
                      CUATRIMESTRES))),
                Field("docente", "reference docente"),
                Field("alta_fecha", "date", default=request.now),
                Field("fecha", "datetime", comment="Hora y fecha de última modificación"),
                Field("nota_01"),
                Field("nota_02"),
                Field("nota_03"),
                Field("nota_04"),
                Field("nota_05"),
                Field("nota_06"),
                Field("nota_07"),
                Field("nota_08"),
                Field("nota_09"),
                Field("nota_10"),
                Field("nota_11"),
                Field("nota_12"),
                Field("definitiva"),
                Field("condicion", requires=IS_EMPTY_OR(IS_IN_SET(
                CONDICIONES)), default=CONDICION_POR_DEFECTO),
                Field("promocion", requires=IS_EMPTY_OR(IS_IN_SET(PROMOCIONES)),
                default=PROMOCION_POR_DEFECTO),
                Field("acredito", "boolean"),
                Field("promueve", "boolean"),
                Field("plazo", "date"),
                Field("observaciones"),
                Field("baja_fecha", "date"),
                Field("baja_motivo", "string"))

db.define_table("taller_inscripcion",
                Field("taller", requires=IS_IN_SET(TALLERES)),
                Field("docente", "reference docente"),
                Field("estudiante", "reference estudiante"),
                Field("ciclo", "integer", requires=IS_IN_SET(CICLOS)))

db.define_table("taller_calificacion",
                Field("inscripcion", "reference taller_inscripcion"),
                Field("calificacion", requires=IS_IN_SET(TALLER_CALIFICACIONES)),
                Field("boletin", "integer", requires=IS_IN_SET(BOLETINES)))

db.define_table("designacion",
               Field("docente", "reference docente"),
               Field("asignatura", "reference asignatura"),
               Field("situacion", requires=IS_IN_SET(
               SITUACIONES)),
               Field("alta", "date", requires=IS_DATE(),
               default=request.now),
               Field("baja", "date", requires=IS_EMPTY_OR(IS_DATE())))

db.define_table("docente_ausencia",
               Field("docente", "reference docente"),
               Field("desde", "datetime"),
               Field("hasta", "datetime"),
               Field("motivo"))

db.define_table("suspension_actividad",
               Field("turno", requires=IS_EMPTY_OR(IS_IN_SET(
               TURNOS))),
               Field("nivel", "integer", 
                     requires=IS_EMPTY_OR(IS_IN_SET(
                     NIVELES))),
               Field("division",
                     requires=IS_EMPTY_OR(IS_IN_SET(
                     DIVISIONES))),
               Field("materia", requires=IS_EMPTY_OR(IS_IN_SET(MATERIAS))),
               Field("comision", requires=IS_EMPTY_OR(IS_IN_SET(COMISIONES))),
               Field("desde", "datetime"),
               Field("hasta", "datetime"),               
               Field("motivo"))
                
db.define_table("nota",
                Field("estudiante", "reference estudiante"),
                Field("fecha", "datetime", default=request.now),
                Field("motivo", requires=IS_IN_SET(NOTA_MOTIVOS),
                default="Administrativa"),
                Field("detalle", "text"))

db.define_table("asistencia",
               Field("ciclo", "integer", requires=IS_IN_SET(
               (CICLOS))),
               Field("turno", requires=IS_IN_SET((
               "M", "T", "N"))),
               Field("contraturno", requires=IS_EMPTY_OR(IS_IN_SET(TURNOS)),
                     default=None,
                     comment="Turno de cursada. Dejar en blanco si se cursa en igual horario"),
               Field("materia", requires=IS_EMPTY_OR(IS_IN_SET(
               MATERIAS))),
               Field("fecha", "date", requires=IS_NOT_EMPTY()),
               Field("categoria_01", "list:reference estudiante"),
               Field("categoria_02", "list:reference estudiante"),
               Field("categoria_03", "list:reference estudiante"),
               Field("categoria_04", "list:reference estudiante"),
               Field("categoria_05", "list:reference estudiante"),
               Field("categoria_06", "list:reference estudiante"),
               Field("categoria_07", "list:reference estudiante"),
               Field("categoria_08", "list:reference estudiante"),
               Field("categoria_09", "list:reference estudiante"),
               Field("categoria_10", "list:reference estudiante"),
               Field("categoria_11", "list:reference estudiante"),
               Field("categoria_12", "list:reference estudiante"),
               Field("categoria_13", "list:reference estudiante"),
               Field("categoria_14", "list:reference estudiante"),
               Field("categoria_15", "list:reference estudiante"),
               Field("categoria_16", "list:reference estudiante"),
               Field("categoria_17", "list:reference estudiante"),
               Field("categoria_18", "list:reference estudiante"),
               Field("categoria_19", "list:reference estudiante"),
               Field("categoria_20", "list:reference estudiante"))

db.designacion.docente.requires = IS_IN_DB(db, 
    "docente.id", "%(nombre)s")

db.designacion.asignatura.requires = IS_IN_DB(db,
    "asignatura.id",
    "%(materia)s %(detalle)s %(nivel)s - %(division)s %(comision)s \
    T%(turno)s")
db.docente_ausencia.docente.requires = IS_IN_DB(db,
"docente.id", "%(nombre)s")
db.calificacion.docente.requires = IS_IN_DB(db,
    "docente.id", "%(nombre)s")
db.inscripcion.estudiante.requires = IS_IN_DB(db,
    "estudiante.id", "%(nombre)s Doc %(documento_numero)s")
db.calificacion.estudiante.requires = IS_IN_DB(db,
    "estudiante.id", "%(nombre)s Doc %(documento_numero)s")
db.nota.estudiante.requires = IS_IN_DB(db,
    "estudiante.id", "%(nombre)s Doc %(documento_numero)s")

# Campos virtuales calculados para mostrar el plan asociado
# a la división
db.inscripcion.virtualfields.append(inscripcionTituloVirtualField())
db.concepto.virtualfields.append(conceptoTituloVirtualField())
db.suspension_actividad.virtualfields.append(suspensionActividadTituloVirtualField())

for f in NOTAS_FORMATO:
    if NOTAS_FORMATO[f]["tipo"] == "concepto":
        db.calificacion[f].requires = IS_EMPTY_OR(IS_IN_SET(CONCEPTOS))
    elif NOTAS_FORMATO[f]["tipo"] == "numero":
        db.calificacion[f].requires = IS_EMPTY_OR(IS_IN_SET(CALIFICACIONES))
    if "rotulo" in NOTAS_FORMATO[f] and (not NOTAS_FORMATO[f]["rotulo"] in (None, "")):
        db.calificacion[f].label=NOTAS_FORMATO[f]["rotulo"]

for k in ASISTENCIA:
    db.asistencia[ASISTENCIA_CATEGORIAS[k]].label = ASISTENCIA[k]

