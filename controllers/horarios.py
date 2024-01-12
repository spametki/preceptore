# -*- coding: utf-8 -*-

__author__ = "Alan Edmundo Etkin <spametki@gmail.com>"
__copyright__ = "(C) 2024 Alan Edmundo Etkin. GNU GPL 3."

@auth.requires_membership('consultas')
def horarios():
    """
    Recupera información
    de toda la semana sobre horarios de clase,
    , docentes asignados, ausentes y
    suspensiones de clases
    
    args: [turno]/[nivel]/[division]
    vars: fecha -> "aaaammdd"; suspension -> "true"
    """

    # 1) recuperar turno, curso y fecha
    
    if request.vars["fecha"]:
        fecha = convertir_a_datetime(request.vars["fecha"])
        fecha = datetime.date(year=fecha.year, month=fecha.month, day=fecha.day)
    else:
        fecha = datetime.date.today()
        
    turno = request.args[0]
    nivel = int(request.args[1])
    division = request.args[2]

    suspension = False
    if "suspension" in request.vars:
        if request.vars["suspension"] == "true":
            suspension = True

    horarios_semana = horarios_grilla(fecha, turno,
    nivel, division, suspension=suspension)

    return dict(fecha = fecha, turno = turno, nivel = nivel,
    division = division, horarios_semana = horarios_semana)

@auth.requires_membership('administradores')
def horariosconsulta():
    form = SQLFORM.factory(
    Field("fecha", "date", default=datetime.date.today()),
    Field("turno", requires=IS_IN_SET(TURNOS)),
    Field("nivel", requires=IS_IN_SET(NIVELES)),
    Field("division", requires=IS_IN_SET(DIVISIONES)),
    Field("horaslibres", "boolean", default=False,
    label="Horas libres",
    comment="Mostrar suspensiones de actividad"))
    if form.process().accepted:
        opciones = dict(fecha=form.vars.fecha.isoformat(
        ).replace("-", ""))
        if form.vars.horaslibres:
            opciones["suspension"] = "true"
        redirect(URL("horarios", args=(form.vars.turno,
        form.vars.nivel, form.vars.division),
        vars=opciones))
    return dict(form=form)

@auth.requires_membership('consultas')
def estudiantehorarios():
    # argumentos: 0 -> estudiante_id
    # variables: fecha -> "aaaammdd", suspension -> "true"

    # recupera fecha
    if "fecha" in request.vars:
        fechayhora = convertir_a_datetime(request.vars["fecha"])
        fecha = datetime.date(fechayhora.year, fechayhora.month, fechayhora.day)
    else:
        fecha = datetime.date.today()

    suspension = False
    if "suspension" in request.vars:
        if request.vars["suspension"] == "true":
            suspension = True

    # recuperar id de estudiante
    estudiante_id = int(request.args[0])

    estudiante = estudiante_recuperar(estudiante_id)

    turno = nivel = division = None
    
    # recuperar inscripción
    
    query = db.inscripcion.estudiante == estudiante_id
    query &= db.inscripcion.ciclo == ciclo_determinar(fecha)
    inscripcion = db(query).select().first()
    
    if inscripcion != None:
        turno = inscripcion.turno
        nivel = inscripcion.nivel
        division = inscripcion.division
    else:
        # la/el estudiante no tiene inscripción en la BDD
        raise HTTP(501,
        "No se encontró inscripción para la/el estudiante")

    horarios_semana = horarios_grilla(fecha, turno, nivel,
    division, estudiante_id = estudiante_id,
    suspension = suspension)

    return dict(estudiante = estudiante, fecha = fecha,
    turno = turno, nivel = nivel, division = division,
    horarios_semana = horarios_semana)
