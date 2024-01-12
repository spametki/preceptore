# -*- coding: utf-8 -*-

__author__ = "Alan Edmundo Etkin <spametki@gmail.com>"
__copyright__ = "(C) 2024 Alan Edmundo Etkin. GNU GPL 3."

@auth.requires_membership('consultas')
def estudiantes():
    links = (lambda registro: A("Menú trayecto", _href=URL(
    f="estudiante", args=(registro.estudiante.id,),
    vars=dict(visualizar="true"))),
             lambda registro: A("Menú estudiante",
             _href=URL(f="estudiantemenu",
             args=(registro.estudiante.id,),
             vars=dict(visualizar="true"))))
    
    grid = SQLFORM.grid(
    db.estudiante.id == db.inscripcion.estudiante,
    links = links, editable=False, deletable=False,
    details=False, buttons_placement="left")
    return dict(grid = grid)


@auth.requires_membership('administradores')
def estudiante():
    estudiante = None
    estudiante_id = None
    creado = False
    duplicado = None
    modificado = False

    visualizar = False
    if "visualizar" in request.vars:
        if request.vars["visualizar"] == "true":
            visualizar = True

    if len(request.args) == 1:
        estudiante_id = int(request.args[0])
    if estudiante_id == None:
        form = SQLFORM(db.estudiante)
    else:
        form = SQLFORM(db.estudiante, record=estudiante_id,
        readonly = visualizar)
    if form.process().accepted:
        estudiante = db(db.estudiante.id == form.vars.id).select(
        ).first()
    
        if estudiante_id == None:
            creado = True
            estudiante_id = estudiante.id
            query = db.estudiante.documento_tipo == \
            form.vars.documento_tipo
            query &= db.estudiante.documento_numero == \
            form.vars.documento_numero
            query &= db.estudiante.id != estudiante.id
            duplicado = db(query).select().first()
        
            if duplicado != None:
                estudiante_id = duplicado.id        
                estudiante.delete_record()
                response.flash = \
                "El estudiante ya existe en la BDD"
        else:
            modificado = True

    return dict(form = form, estudiante = estudiante,
                estudiante_id = estudiante_id,
                creado = creado, duplicado = duplicado,
                modificado = modificado)
                
@auth.requires_membership('administradores')
def estudiantemenu():
    estudiante_id = request.args[0]
    estudiante = db(db.estudiante.id == estudiante_id).select(
                    ).first()
                    
    inscripciones = db(db.inscripcion.estudiante == estudiante_id).select()
    if estudiante.fecha_nacimiento != None:
        edad = relativedelta(datetime.datetime.now(),
                             datetime.datetime(
                             estudiante.fecha_nacimiento.year,
                             estudiante.fecha_nacimiento.month,
                             estudiante.fecha_nacimiento.day
                             )).years
    else:
        edad = None
    dia_hora = datetime.datetime.today()    
    hoy = datetime.date(dia_hora.year, dia_hora.month,
    dia_hora.day)
    form = SQLFORM.factory(Field("fecha", "date",
    default=hoy), Field("suspension", "boolean",
    default=False, label="",
    comment="Mostrar suspensiones de actividad"))
    if form.process().accepted:
        fecha = form.vars.fecha
        suspension="false"
        if form.vars.suspension:
            suspension="true"
        redirect(URL("horarios", "estudiantehorarios",
        args=(estudiante_id,),
        vars=dict(fecha=fecha.isoformat().replace("-", ""),
        suspension=suspension)))
    return dict(estudiante=estudiante, edad=edad, form=form, inscripciones=inscripciones)

@auth.requires_membership('administradores')
def inscripcion():
    # args: 0 -> estudiante
    #       1 -> ciclo
    
    estudiante_id = int(request.args[0])
    estudiante = estudiante_recuperar(estudiante_id)
    ciclo = int(request.args[1])
    previa_id = None
    finalizado = False

    # autocompletar formulario
    db.inscripcion.estudiante.default = estudiante_id
    db.inscripcion.ciclo.default = int(ciclo)

    # buscar inscripción anterior
    query = db.inscripcion.estudiante == estudiante_id
    query &= db.inscripcion.ciclo < ciclo
    query &= db.inscripcion.turno != None
    inscripcion_anterior = db(query).select(
    orderby=db.inscripcion.id).last()

    if inscripcion_anterior != None:
        db.inscripcion.turno.default = \
        inscripcion_anterior.turno

    # buscar inscripciones duplicadas
    query = db.inscripcion.estudiante == estudiante_id
    query &= db.inscripcion.baja != True
    query &= db.inscripcion.ciclo == ciclo

    inscripciones = db(query).select(
    orderby=db.inscripcion.id)
    
    if len(inscripciones) > 0:
        previa_id = inscripciones.last().id
    db.inscripcion.estudiante.writable = \
    db.inscripcion.nivel.writable = \
    db.inscripcion.division.writable = \
    db.inscripcion.baja.writable = \
    db.inscripcion.baja_motivo.writable = \
    db.inscripcion.baja_fecha.writable = False
    db.inscripcion.estudiante.readable = \
    db.inscripcion.baja.readable = \
    db.inscripcion.baja_motivo.readable = \
    db.inscripcion.baja_fecha.readable = False
    
    if previa_id != None:
        form = SQLFORM(db.inscripcion, previa_id)
    else:
        form = SQLFORM(db.inscripcion)

    if form.process().accepted:
        finalizado = True
        
    # si el formulario valida,
    # crear inscripción y devolver información
    # no volver a inscribir en el mismo ciclo
    # a menos que la anterior se haya dado de baja
    return dict(form = form, estudiante = estudiante,
    finalizado = finalizado)

@auth.requires_membership('administradores')
def inscripcion_baja():
    inscripcion_id = int(request.args[0])
    db.inscripcion.estudiante.writable = False
    db.inscripcion.baja_fecha.requires = IS_DATE()
    db.inscripcion.baja_motivo.requires = IS_NOT_EMPTY()
    db.inscripcion.baja.writable = False
    form = SQLFORM(db.inscripcion, inscripcion_id ,
    fields=["baja", "estudiante", "baja_fecha", "baja_motivo"])
    form.vars.baja = True
    form.vars.baja_fecha = datetime.date.today()
    if form.process().accepted:

        inscripcion = db(db.inscripcion.id == inscripcion_id
                     ).select().first()

        # Buscar todas las calificaciones
        # del alumno en el ciclo
        # dar de baja, indicar motivo con información
        # en inscripcion si se completó
        # usar fecha de baja de inscripcion

        cuatrimestre_cambio = datetime.date(int(inscripcion.ciclo), CUATRIMESTRE_CAMBIO[1], CUATRIMESTRE_CAMBIO[0])
        qc = (db.calificacion.estudiante == inscripcion.estudiante) & (db.calificacion.baja_fecha == None) & (db.calificacion.ciclo == inscripcion.ciclo)
        
        # Comprobar cambio de cuatrimestre
        # en fecha de baja y filtrar 1er cuatrimestre
        # si la baja es posterior

        if form.vars.baja_fecha >= cuatrimestre_cambio:
            # DAL requiere la opción null=True
            # si la lista contiene None (ver web2py API)
            qc &= (db.calificacion.cuatrimestre.belongs((2, None), null=True))
        calificaciones = db(qc)
        resultado_de_update = calificaciones.update(baja_fecha=form.vars.baja_fecha, baja_motivo=form.vars.baja_motivo)
        session.flash = "La baja se realizó correctamente"
        redirect(URL("inscripcion", args=[inscripcion.estudiante, inscripcion.ciclo]))
    return dict(form=form)
    
