# -*- coding: utf-8 -*-

__author__ = "Alan Edmundo Etkin <spametki@gmail.com>"
__copyright__ = "(C) 2024 Alan Edmundo Etkin. GNU GPL 3."

@auth.requires_membership('administradores')
def notas():
    grid = SQLFORM.grid(db.nota,
    buttons_placement="left")
    return dict(grid=grid)

@auth.requires_membership('administradores')
def suspensionactividad():
    grid = SQLFORM.grid(db.suspension_actividad,
    buttons_placement="left")
    return dict(grid=grid)
    
@auth.requires_membership('administradores')    
def docenteausencia():
    grid = SQLFORM.grid(db.docente_ausencia,
    buttons_placement="left")
    return dict(grid=grid)

@auth.requires_membership('administradores')
def designaciones():
    fields = (db.docente.nombre, db.asignatura.materia,
    db.asignatura.detalle, db.asignatura.nivel,
    db.asignatura.division, db.asignatura.turno,
    db.asignatura.cuatrimestre, db.asignatura.comision,
    db.designacion.alta, db.designacion.baja,
    *[db.asignatura[dia] for dia in DIAS])
    grid = SQLFORM.grid((db.designacion.docente == \
    db.docente.id) & (db.designacion.asignatura == \
    db.asignatura.id), fields=fields,
    buttons_placement="left")
    return dict(grid = grid)

@auth.requires_membership('administradores')
def calificaciones():
    if (len(request.args) > 0) and request.args[0].isnumeric():
        estudiante_id = int(request.args[0])
        query = db.calificacion.estudiante == estudiante_id
    else:
        query = db.estudiante.id == db.calificacion.estudiante
    fields = (db.estudiante.nombre, db.estudiante.documento_numero,
    db.calificacion.materia, db.calificacion.nivel, db.calificacion.division,
    db.calificacion.cuatrimestre, db.calificacion.comision)
    for f in db.calificacion:
        if f.name in NOTAS_FORMATO:
            if NOTAS_FORMATO[f.name]["utilizar"]:
                fields += (f,)
    grid = SQLFORM.grid(query, buttons_placement="left",
    user_signature=False, fields=fields, field_id=db.calificacion.id)
    return dict(grid = grid)

@auth.requires_membership('administradores')
def docentes():
    grid = SQLFORM.grid(db.docente, buttons_placement="left")
    return dict(grid = grid)

@auth.requires_membership('administradores')
def asignaturas():
    grid = SQLFORM.grid(db.asignatura, buttons_placement="left")
    return dict(grid = grid)

@auth.requires_membership('administradores')
def comisionesarmado():
    # Formulario para filtrar opciones
    # de distribución de comisiones
    form = SQLFORM.factory(
        Field("plan", "integer", requires=IS_IN_SET(PLAN_ABREVIACIONES)),   
        Field("ciclo", "integer", default=request.now.year, requires=IS_IN_SET(CICLOS)),
        Field("turno", requires=IS_IN_SET(TURNOS)),
        Field("contraturno", requires=IS_EMPTY_OR(IS_IN_SET(TURNOS)), comment="Dejar en blanco si no es contraturno"),
        Field("cuatrimestre", "integer", requires=IS_EMPTY_OR(IS_IN_SET(CUATRIMESTRES)),
              comment="Si es anual dejar en blanco"),        
        Field("materia", requires=IS_IN_SET(MATERIAS)),
        Field("nivel", "integer", requires=IS_IN_SET(NIVELES)),
        Field("division", "integer", requires=IS_EMPTY_OR(IS_IN_SET(DIVISIONES)),
              comment="Dejar en blanco si no corresponde")
        )
    if form.process().accepted:
        session.comisionesarmado = form.vars
        if not (form.vars.division in ("", None)):
            nivel = int(form.vars.nivel)
            division = int(form.vars.division)
            plan = int(form.vars.plan)
            if (plan != DIVISIONES_PLAN[nivel][division]):
                response.flash = "El nivel y división seleccionados no coinciden con el plan"
                redirect(URL("comisionesarmado"))
        redirect(URL("comisionesarmadopanel"))
    return dict(form=form)

@auth.requires_membership('administradores')
def comisionesarmadopanel():
    # TODO: El panel debe tener información de
    # - horarios de todas las asignaturas del plan y el turno
    # - en qué asignaturas está inscripto cada estudiante
    # Objetos js: estudiantes, asignaturas, horarios, inscripciones
    # El formulario debe enviar un objeto json para ser procesado
    # en el servidor. El servidor actualiza las altas y bajas de
    # inscripciones a la materia y sus comisiones
    
    # Hay que filtrar los estudiantes por estos criterios
    # - que las inscripciones cumplan con los filtros
    # de plan, ciclo, turno y division. Nivel y División se filtra
    # si se marcó en el formulario división. Para filtrar el plan,
    # hay que hacer un bucle posterior a la consulta porque las
    # inscripciones no tienen plan
    # - que las inscripciones no estén dadas de baja
    # - que cada estudiante cumpla con la correlatividad para
    # la materia. Para este filtro puede hacer falta otra consulta
    # con las calificaciones aprobadas de las correlativas
    
    # Debe haber otra consulta con los estudiantes inscriptos a cada comision
    # y que no estén dados de baja

    plan = int(session.comisionesarmado["plan"])
    ciclo = int(session.comisionesarmado["ciclo"])
    turno = session.comisionesarmado["turno"]
    contraturno = session.comisionesarmado["contraturno"]
    if not (session.comisionesarmado.cuatrimestre in (None, "")):
        cuatrimestre = int(session.comisionesarmado["cuatrimestre"])
    else:
        cuatrimestre = None
    materia = session.comisionesarmado["materia"]
    nivel = int(session.comisionesarmado["nivel"])
    if not (session.comisionesarmado.division in (None, "")):
        division = int(session.comisionesarmado["division"])
    else:
        division = None

    # Consulta de datos de estudiante
    q = db.estudiante.id == db.inscripcion.estudiante
    q &= db.inscripcion.baja != True
    q &= db.inscripcion.ciclo == ciclo
    q &= db.inscripcion.turno == turno

    if division is None:
        pass
    else:
        q &= db.inscripcion.nivel == nivel
        q &= db.inscripcion.division == division

    # Consulta de notas de estudiante
    ql = db.calificacion.estudiante == db.inscripcion.estudiante
    ql &= db.inscripcion.ciclo == ciclo
    ql &= db.inscripcion.turno == turno
    ql &= db.calificacion.titulo == plan
    ql &= db.calificacion.baja_fecha == None

    datos_rows = db(q).select()
    datos = dict()
    notas = dict()
    
    for elemento in datos_rows:
        estudiante = elemento.estudiante.id
        
        if not estudiante in datos:
            notas[estudiante] = list()
            datos[estudiante] = dict()
            # datos estudiante
            datos[estudiante]["id"] = estudiante
            datos[estudiante]["nombre"] = elemento.estudiante.nombre
            datos[estudiante]["documentoTipo"] = elemento.estudiante.documento_tipo
            datos[estudiante]["documentoNumero"] = elemento.estudiante.documento_numero
            datos[estudiante]["nivel"] = elemento.inscripcion.nivel
            datos[estudiante]["division"] = elemento.inscripcion.division
            datos[estudiante]["notas"] = list()
            # comisión en la que figura si está inscripto
            datos[estudiante]["comision"] = None

    notas_rows = db(ql).select()

    for nota in notas_rows:
        calificacion = nota.calificacion
        estudiante = calificacion.estudiante
        notas[estudiante].append(calificacion)
        # Si coincide el ciclo y/o el cuatrimestre
        # agregar nota a datos del alumno
        if (calificacion.ciclo == ciclo) and (
        calificacion.cuatrimestre in (None, cuatrimestre)):
            datos[estudiante]["notas"].append(dict(
                calificacion = calificacion.id,
                materia = calificacion.materia,
                nivel = calificacion.nivel,
                division = calificacion.division,
                comision = calificacion.comision,
                cuatrimestre = calificacion.cuatrimestre))

        # Si se comprueba que está inscripto registrar comisión
        if (calificacion.materia == materia) and (
        int(calificacion.nivel) == int(nivel)) and (
        calificacion.cuatrimestre == cuatrimestre) and (
        calificacion.ciclo == ciclo):
            datos[estudiante]["comision"] = calificacion.comision

    # comprueba si está habilitado para cursar
    borrar = list()
    for estudiante in datos:
        # usar información del dict datos para notas
        trayecto = trayecto_calcular(plan, notas[estudiante])
        if not materia in trayecto[nivel]:
            borrar.append(estudiante)
    for estudiante in borrar:            
        del(datos[estudiante])

    # Recuperar comisiones
    qc = db.asignatura.id == db.designacion.asignatura
    qc &= db.designacion.docente == db.docente.id
    qc &= db.asignatura.titulo == plan
    qc &= db.asignatura.turno == turno
    qc &= db.asignatura.materia == materia
    qc &= db.asignatura.nivel == nivel
    qc &= db.asignatura.cuatrimestre == cuatrimestre
    qc &= db.asignatura.division == division
    
    # Objeto Rows: hay que convertirlo con .as_json()
    comisiones = db(qc).select()

    # Asignaturas del turno
    qa = db.asignatura.titulo == plan
    qa &= db.asignatura.turno == turno
    qa &= db.asignatura.contraturno == contraturno
    asignaturas = db(qa).select()

    docentes = db(db.docente).select()
    designaciones = db(db.designacion.baja == None).select()
    
    variables = dict(ciclo=ciclo, turno=turno, plan=plan,
                     materia=materia, nivel=nivel,
                     division=division,
                     cuatrimestre=cuatrimestre,datos=datos,
                     planes=PLAN_ABREVIACIONES, horarios=HORARIOS)
                
    variables_js = dict()

    for key in variables:
        variables_js[key] = json.dumps(variables[key])

    variables["asignaturas"] = asignaturas
    variables["comisiones"] = comisiones
    variables["docentes"] = docentes
    variables["designaciones"] = designaciones

    variables_js["asignaturas"] = asignaturas.as_json()
    variables_js["comisiones"] = comisiones.as_json()
    variables_js["docentes"] = docentes.as_json()
    variables_js["designaciones"] = designaciones.as_json()
    
    campos = list()
    session.comisiones = list()
    for row in comisiones:
        session.comisiones.append(row.asignatura.comision)
        campos.append(Field(
            row.asignatura.comision,
            "integer",
            requires=IS_IN_SET({}, multiple=True)))
    form = SQLFORM.factory(Field("listado", "integer", label="Listado de alumnas/os", requires=IS_IN_SET({}, multiple=True)), *campos, Field("mensajes", "text"))
    if form.process().accepted:
        session.comisionesarmado_form = form.vars
        redirect(URL("comisionesarmadoprocesar"))
    return dict(variables_js=variables_js, form=form, variables=variables)

@auth.requires_membership('administradores')
def comisionesarmadoprocesar():
    # Procesa los cambios en comisionesarmadopanel
    # Hay que recorrer los registros y eliminando las
    # calificaciones de alumnos sin comision
    # También hay que recorrer el formulario creando
    # el registro de cada calificacion que no se haya creado
    # Además hay que cambiar la comisión en casos que se hayan
    # pasado alumnos de comisión.

    # TODO: en cada envío de forumulario
    # los registros de alumnos que estaban
    # inscriptos en una comisión se vuelven
    # a insertar en la BDD

    mensajes = list()

    if not ("comisionesarmado_form" in session):
        response.flash = "Datos no disponibles. Los cambios ya se procesaron"
        return dict(mensajes=mensajes)
    
    # a) Consulta a BDD de todas las calificaciones actuales
    
    variables = session.comisionesarmado
    
    qa = db.calificacion.titulo == variables.plan
    qa &= db.calificacion.ciclo == variables.ciclo
    qa &= db.calificacion.turno == variables.turno
    qa &= db.calificacion.cuatrimestre == variables.cuatrimestre
    qa &= db.calificacion.materia == variables.materia
    qa &= db.calificacion.nivel == variables.nivel
    qa &= db.calificacion.division == variables.division
    qa &= db.calificacion.baja_fecha == None
    
    calificaciones = db(qa).select()
    
    comisiones_previas = dict()

    qe = db.inscripcion.estudiante == db.estudiante.id
    qe &= db.inscripcion.ciclo == int(variables.ciclo)
    qe &= db.inscripcion.turno == variables.turno
    qe &= db.inscripcion.baja != True
    
    alumnos = dict()

    no_inscriptos = [int(estudiante) for estudiante in session.comisionesarmado_form.listado]
    
    for alumno in db(qe).select():
        alumnos[alumno.estudiante.id] = (alumno.estudiante.nombre, alumno.estudiante.documento_tipo, alumno.estudiante.documento_numero)
    # b) Crear objeto por alumna/o con comisiones
    indice = 0
    for calificacion in calificaciones:
        if not (calificacion.estudiante in comisiones_previas):
            comisiones_previas[int(calificacion.estudiante)] = (indice, calificacion.comision)
        if int(calificacion.estudiante) in no_inscriptos:
            calificacion.delete_record()
            mensajes.append("Se eliminó a %s %s %s de la comisión %s" % (*alumnos[int(calificacion.estudiante)], calificacion.comision))
        indice += 1

    # c) Recorrer formulario para altas/bajas/modificaciones
    for comision in session.comisiones:
       for estudiante in session.comisionesarmado_form[comision]:
            if int(estudiante) in comisiones_previas:
                indice, comision_previa = comisiones_previas[int(estudiante)]
                if comision_previa == comision:
                    pass
                else:
                    # update record actualizando comisión
                    calificaciones[indice].update_record(comision=comision)
                    mensajes.append("Se se cambió a %s %s %s a la comisión %s" % (*alumnos[int(estudiante)], comision))
            else:
                # crear comision nueva
                db.calificacion.insert(
                    estudiante = int(estudiante),
                    titulo = int(variables.plan),
                    ciclo = int(variables.ciclo),
                    turno = variables.turno,
                    cuatrimestre = variables.cuatrimestre,
                    materia = variables.materia,
                    nivel = int(variables.nivel),
                    division = variables.division,
                    comision = comision)
                mensajes.append("Se agregó a %s %s %s a la comisión %s" % (*alumnos[int(estudiante)], comision))
    # d) Devolver resultados de cambios en la BDD
    # e) Eliminar registros en session para evitar
    # procesar de nuevo con F5
    del(session.comisionesarmado_form)
    del(session.comisiones)
    return dict(mensajes=mensajes)
