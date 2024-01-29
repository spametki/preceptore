# -*- coding: utf-8 -*-

__author__ = "Alan Edmundo Etkin <spametki@gmail.com>"
__copyright__ = "(C) 2024 Alan Edmundo Etkin. GNU GPL 3."

@auth.requires_membership('consultas')
def analitico():
    # args: [id del estudiante][actualizar <opcional>]

    # - Actualiza notas (cierre automático): opcional
    # - Lista materias indicando si aprobó
    
    estudiante_id = int(request.args[0])
    actualizar = False
    if len(request.args) == 2:
        if request.args[1] == "actualizar":
            actualizar = True

    estudiante = estudiante_recuperar(db, estudiante_id)
    
    # hay que recuperar última inscripción válida
    # para establecer plan del analítico
    plan = plan_recuperar(db, estudiante_id)
    
    notas = notas_recuperar(db, estudiante_id, plan=plan)
    
    if actualizar and (notas != None):
        notas = notas_actualizar(notas)

    tabla_encabezados = ["Materia", "Condición", "Aprobada",
                         "Nota", "Fecha", "Observaciones"]

    tabla_datos = dict()
    for n in NIVELES:
        tabla_datos[n] = []
        for v in PLAN[plan][n]:
            materia_datos = [ABREVIACIONES[v], "N/A",
            "--------", "----", "--------", ""]
            for nota in notas:
                if (nota.materia == ABREVIACIONES[v]
                ) and (int(nota.nivel) == n):
                    if nota.condicion:
                        materia_datos[1] = nota.condicion
                    if nota.acredito:
                        materia_datos[2] = "APROBADA"
                        if nota.definitiva != None:
                            materia_datos[3] = nota.definitiva
                    if nota.fecha != None:
                        materia_datos[4] = nota.fecha
                    if nota.observaciones:
                        materia_datos[5] = nota.observaciones
                        
            tabla_datos[n].append(materia_datos)
            
    return dict(notas = notas, estudiante = estudiante,
                tabla_datos = tabla_datos,
                tabla_encabezados = tabla_encabezados)


@auth.requires_membership('consultas')
def pendientes():
    # Idem analítico pero
    # presenta las materias pendientes de cursar por año
    # teniendo en cuenta la promoción sin acreditar

    estudiante_id = int(request.args[0])
    actualizar = False
    if len(request.args) == 2:
        if request.args[1] == "actualizar":
            actualizar = True

    estudiante = estudiante_recuperar(db, estudiante_id)
    
    # hay que recuperar última inscripción válida
    # para establecer plan del analítico
    plan = plan_recuperar(db, estudiante_id)
        
    notas = notas_recuperar(db, estudiante_id, plan=plan)
    
    if actualizar and (notas != None):
        notas = notas_actualizar(notas)

    tabla_datos = dict()
    for nivel in NIVELES:
        tabla_datos[nivel] = []
        for materia in PLAN[plan][nivel]:
            tabla_datos[nivel].append(ABREVIACIONES[materia])
            for nota in notas:
                if (nota.materia == ABREVIACIONES[materia]) and (
                    int(nota.nivel) == nivel) and (
                    nota.acredito == True):
                    resultado = tabla_datos[nivel].pop()

    return dict(estudiante = estudiante,
    tabla_datos = tabla_datos)


@auth.requires_membership('consultas')
def trayectocalcular():
    # presenta las materias a cursar filtrando las que el
    # estudiante no puede cursar por correlatividad

    # recupera parámetros
    estudiante_id = int(request.args[0])
    actualizar = False
    if len(request.args) == 2:
        if request.args[1] == "actualizar":
            actualizar = True
    
    # recupera alumno y notas
    estudiante = estudiante_recuperar(db, estudiante_id)
    
    # hay que recuperar última inscripción válida
    # para establecer plan del analítico
    plan = plan_recuperar(db, estudiante_id)

    notas = notas_recuperar(db, estudiante_id, plan=plan)
    
    if actualizar and (notas != None):
        notas = notas_actualizar(notas)

    # recupera materias que puede cursar
    materias = trayecto_calcular(plan, notas)
                
    return dict(estudiante = estudiante, materias = materias)

@auth.requires_membership('administradores')
def aprobadasingresar():
    # args: 0 -> estudiante_id

    # formulario para ingresar materias
    # aprobadas que no están en las
    # calificaciones
    # ejemplos: equivalencia por pase,
    # resolución interna por nivelación

    enviado = False

    estudiante_id = int(request.args[0])
    estudiante = estudiante_recuperar(db, estudiante_id)

    # hay que recuperar última inscripción válida
    # para establecer plan del analítico
    plan = plan_recuperar(db, estudiante_id)
    
    if plan is None:
        session.flash = "Para ingresar materias hay que seleccionar previamente el plan"
        redirect(URL(c="estudiantes", f="estudiante", args=(estudiante_id,), vars={"visualizar": "true"}))

    notas = notas_recuperar(db, estudiante_id, plan=plan)
    notas = notas_actualizar(notas)

    # a) recuperar el plan
    plan_aprobadas = dict()
    for n in PLAN[plan]:
        plan_aprobadas[n] = [False for item in PLAN[plan][n]]


    # b) recuperar listado de materias
    # acreditadas por la/el estudiante
    for nota in notas:
        nivel = int(nota.nivel)
        if nota.acredito == True:
            plan_aprobadas[nivel][PLAN[plan][nivel].index(materia_abreviar(
            nota.materia))] = True

    # Generar tabla con campos para ingresar condición,
    # etc con materias pendientes
    # c) generar formulario al vuelo
        
    campos = []
    
    for nivel in plan_aprobadas:
        for x in range(len(plan_aprobadas[nivel])):
            if plan_aprobadas[nivel][x] == False:
                campos.append(Field("materia_%s_%s" % (nivel, x),
                "boolean", label="%s %s" % (
                ABREVIACIONES[PLAN[plan][nivel][x]],
                NUMEROS_ROMANOS[nivel])))
                campos.append(Field(
                "condicion_%s_%s" % (nivel, x), 
                requires=IS_EMPTY_OR(IS_IN_SET(CONDICIONES
                )), label="Condición"))
                campos.append(Field("definitiva_%s_%s" % (
                nivel, x), label="Nota definitiva",
                requires=IS_EMPTY_OR(IS_IN_SET(CALIFICACIONES))))
                campos.append(Field("fecha_%s_%s" % (nivel, x),
                "date", requires=IS_EMPTY_OR(IS_DATE()),
                label="Fecha"))
                campos.append(Field("observaciones_%s_%s" % (
                nivel, x), label="Observaciones"))
                
    form = SQLFORM.factory(*[f for f in campos])

    # d) procesar cambios y generar
    # los registros con la calificación
    # y los detalles
    notasnuevas = dict()
    if form.process().accepted:
        enviado = True
        for f in form.vars:
           nivel, materia = f.split("_")[1:]
           nivel, materia = int(nivel), int(materia)
           nivelymateria = "%s_%s" % (nivel, materia)
           if not nivelymateria in notasnuevas:
               notasnuevas[nivelymateria] = dict()
               notasnuevas[nivelymateria]["estudiante"] = \
               estudiante_id
               notasnuevas[nivelymateria]["plan"] = plan
               notasnuevas[nivelymateria]["nivel"] = nivel
               notasnuevas[nivelymateria]["materia"] = \
               ABREVIACIONES[PLAN[plan][nivel][materia]]
           if "materia" in f:
               notasnuevas[nivelymateria]["acredito"] = \
               form.vars[f]
           elif "fecha" in f:
               notasnuevas[nivelymateria]["fecha"] = \
               form.vars[f]               
           elif "condicion" in f:
               notasnuevas[nivelymateria]["condicion"] = \
               form.vars[f]
           elif "definitiva" in f:
               notasnuevas[nivelymateria]["definitiva"] = \
               form.vars[f]
           elif "observaciones" in f:
               notasnuevas[nivelymateria]["observaciones"] = \
               form.vars[f]

        for nota in notasnuevas:
            if notasnuevas[nota]["acredito"]:
                nota_id = db.calificacion.insert(
                **notasnuevas[nota])
    return dict(form=form, estudiante=estudiante,
    notasnuevas = notasnuevas, enviado = enviado)

@auth.requires_membership('consultas')
def trayecto():
    # Muestra un listado de materias
    # en las que el estudiante está
    # inscripto en el ciclo especificado
    # indicando nivel, división y comisión
    
    # Argumentos:
    # 0: inscripcion id
    q = db.inscripcion.estudiante == db.estudiante.id
    q &= db.inscripcion.id == int(request.args[0])
    alumno = db(q).select().first()
    inscripcion = alumno.inscripcion
    if not (alumno is None):
        try:
            plan = DIVISIONES_PLAN[int(inscripcion.nivel)][int(inscripcion.division)]
        except TypeError:
            plan = None
            
        estudiante = alumno.estudiante
        inscripcion = alumno.inscripcion
        qc = db.calificacion.estudiante == estudiante.id
        qc &= db.calificacion.titulo == plan
        qc &= db.calificacion.ciclo == int(inscripcion.ciclo)
        qc &= db.calificacion.baja_fecha == None
        calificaciones = db(qc).select()
        
        return dict(estudiante=estudiante, inscripcion=inscripcion,
        calificaciones=calificaciones, plan=plan)
    else:
        raise HTTP(500, "No se encontró la inscripción especificada")

@auth.requires_membership('administradores')
def trayectonuevo():
    # idem trayecto pero permite crear
    # los registros de las notas
    # eliminar materias desmarcadas

    enviado = False

    # recupera estudiante y notas
    estudiante_id = int(request.args[0])

    estudiante = estudiante_recuperar(db, estudiante_id)

    # hay que recuperar última inscripción válida
    # para establecer plan del analítico
    plan = plan_recuperar(db, estudiante_id)

    if plan is None:
        session.flash = "Para armar el trayecto hay que seleccionar previamente el plan"
        redirect(URL(c="estudiantes", f="estudiante", args=(estudiante_id,), vars={"visualizar": "true"}))

    
    notas = notas_recuperar(db, estudiante_id, plan=plan)

    inscripcion = db(db.inscripcion.estudiante == \
    estudiante_id).select(orderby=db.inscripcion.id).last()

    ciclo = inscripcion.ciclo
    turno = inscripcion.turno

    # recuperar las materias que puede cursar
    notas = notas_actualizar(notas)
    materias = trayecto_calcular(plan, notas)
    
    # si la inscripcion no tiene nivel actualizarlo
    # al de la materia de nivel mayor

    if inscripcion.nivel == None:
        if len(notas) > 0:
            nivel = max([int(nota.nivel) for nota in notas \
            if nota.nivel != None])
        else:
            nivel = NIVELES[0]
    else:
        nivel = int(inscripcion.nivel)

    division = inscripcion.division
    
    if type(division) == int:
        division = str(division)

    divisiones = divisiones_por_nivel(nivel, division)
    
    # listado de creación de registros de
    # nuevo trayecto
    
    trayecto = list()
    eliminadas = list()

    # campos del formulario con las materias a cursar
    materias_formulario = list()

    # establecer el máximo año sin especificar división
    nivel_maximo = NIVELES[0]
    
    # niveles a elegir
    niveles = []
    
    # valor de control para el nivel mínimo
    nivel_primero = NIVELES[0]
    nivel_maximo = NIVELES
    nivel_establecido = False
    
    for n in NIVELES:
        if (len(materias[n]) > 0):
            if not nivel_establecido:
                nivel_primero = n
                nivel_maximo = nivel_primero + \
                NIVELES_SIMULTANEOS -1
                nivel_establecido = True

            if n <= nivel_maximo:
                nivel = n
                niveles.append(n)
                for m in materias[n]:
                    if not m in MATERIAS_TRAYECTO_EXCLUIR:
                        materias_formulario.append(
                        Field("materia_%d_%d" % (n,
                        MATERIAS.index(m)),
                        "boolean", default=True,
                        label="%s %s" % (m, NUMEROS_ROMANOS[n])))

    # establecer división por recorrido
    if divisiones != None:
        division = divisiones[nivel-1]

    form = SQLFORM.factory(
        Field("turno", requires=IS_IN_SET(TURNOS),
        default=turno),
        Field("nivel", default=nivel,
        requires=IS_IN_SET(niveles)),
        Field("division", requires=IS_IN_SET(DIVISIONES),
        default=division),
        *[field for field in materias_formulario])

    form.vars["estudiante"] = estudiante_id

    if form.process(onvalidation=plan_comprobar).accepted:
        enviado = True
        # actualizar inscripción
        inscripcion.update_record(nivel=form.vars.nivel,
        division=form.vars.division)

        nivel = int(form.vars.nivel)
        division = form.vars.division
        divisiones = divisiones_por_nivel(nivel, division)

        # recuperar materias aceptadas del formulario
        # si se deselecciona la materia eliminar
        # calificación
        for f in form.vars:
            if "materia_" in f:
                prefijo, n, materia = f.split("_")
                n = int(n)
                materia = MATERIAS[int(materia)]
                # buscar coincidencia y filtrar
                # para calificaciones ya creadas
                query = db.calificacion.ciclo == ciclo
                query &= db.calificacion.nivel == n
                query &= db.calificacion.materia == materia
                query &= db.calificacion.titulo == plan
                query &= db.calificacion.estudiante == \
                estudiante_id
               
                calificacion = db(query).select().first()
                
                if calificacion == None:
                    # crear calificacion
                    nota = {
                    "estudiante": estudiante_id,
                    "ciclo": ciclo,
                    "turno": turno,
                    "nivel": n,
                    "plan": plan,
                    "division": divisiones[n-1],
                    "materia": materia,
                    "condicion": CONDICION_POR_DEFECTO}
                    # insertar registro
                    if (form.vars[f] == True) and (n <= int(
                    inscripcion.nivel)):
                        db.calificacion.insert(**nota)
                        trayecto.append(nota)
                else:
                    # se desmarcó la materia, eliminar
                    if form.vars[f] == False:
                        eliminadas.append(
                        dict(materia = calificacion.materia,
                        nivel = calificacion.nivel))
                        calificacion.delete_record()

    return dict(form = form, estudiante = estudiante,
                trayecto = trayecto, eliminadas = eliminadas,
                ciclo = ciclo, enviado = enviado)

@auth.requires_membership('consultas')
def boletin():
    form = SQLFORM.factory(
        Field("ciclo", "integer", requires=IS_IN_SET(CICLOS), default=CICLOS[0]),
        Field("periodo", "integer", requires=IS_IN_SET(BOLETINES)),        
        Field("turno", requires=IS_IN_SET(TURNOS)),
        Field("nivel", requires=IS_IN_SET(NIVELES)),
        Field("division", requires=IS_IN_SET(DIVISIONES)))

    if form.process(onvalidation=plan_actualizar).accepted:
        # generar listado
        # de inscripciones
        # redirigir a listado
        session.boletin_opciones = form.vars
        redirect(URL("boletinlista"))
    return dict(form=form)

@auth.requires_membership('consultas')
def boletinlista():
    nivel = int(session.boletin_opciones.nivel)
    division = int(session.boletin_opciones.division)
    # recuperar listado de inscripcion
    # generar en cada item el link a mostrar el boletin
    qi = db.inscripcion.ciclo == session.boletin_opciones.ciclo
    qi &= db.inscripcion.turno == session.boletin_opciones.turno
    qi &= db.inscripcion.nivel == nivel
    qi &= db.inscripcion.division == division
    inscripciones = db(qi).select()
    lista = inscripciones
    return dict(lista=lista, nivel=nivel, division=division)

@auth.requires_membership('consultas')
def boletinmostrar():

    # 1) establecer si se incluye asistencia por materia,
    # conceptos, talleres y previas
    
    ciclo = int(session.boletin_opciones.ciclo)
    turno = session.boletin_opciones.turno
    boletin = int(session.boletin_opciones.periodo)
    
    apm_mostrar = BOLETIN_ASISTENCIA_MATERIA_MOSTRAR[boletin]
    conceptos_mostrar = BOLETIN_CONCEPTOS_MOSTRAR[boletin]
    previas_mostrar = BOLETIN_PREVIAS_MOSTRAR[boletin]
    talleres_mostrar = BOLETIN_TALLERES_MOSTRAR[boletin]

    # recuperar alumna/o
    # y join estudiante
    alumno = db((db.estudiante.id == db.inscripcion.estudiante) & (db.inscripcion.id == request.args[1])).select().last()
    inscripcion = alumno.inscripcion
    estudiante = alumno.estudiante
    
    try:
        plan = DIVISIONES_PLAN[int(inscripcion.nivel)][int(inscripcion.division)]
    except TypeError:
        plan = None

    # obtener las materias del alumno para el ciclo elegido
    qc = db.calificacion.estudiante == estudiante.id
    qc &= db.calificacion.ciclo == ciclo
    qc &= db.calificacion.turno == turno
    qc &= db.calificacion.titulo == plan
    calificaciones = db(qc).select()
    actualizadas = notas_actualizar(calificaciones)

    # 2) recuperar por llamados a funciones asistencia general
    # Obtener límites de fecha según el periodo especificado
    
    inicio_clases = datetime.date(ciclo, CICLO_CAMBIO[1], CICLO_CAMBIO[0])
    fin_clases = datetime.date(ciclo, CICLO_FIN[1], CICLO_FIN[0])
    fin_periodo = datetime.date(ciclo + BOLETINES_PLAZOS[boletin][2], BOLETINES_PLAZOS[boletin][1], BOLETINES_PLAZOS[boletin][0])
    fin_cuatrimestre = datetime.date(ciclo, CUATRIMESTRE_CAMBIO[1], CUATRIMESTRE_CAMBIO[0])

    asistencia = asistencia_alumno(db, alumno, inicio_clases, fin_periodo)

    # notas: Objeto que almacena las notas a mostrar
    # ordenado por nivel y materia y datos de asistencia
    notas = dict()
    # talleres: Rows de consulta join con calificaciones
    # de talleres
    talleres = None
    
    for calificacion in calificaciones:
        if calificacion.cuatrimestre == 2:
            if fin_periodo <= fin_cuatrimestre:
                # no informar la materia
                # por no estar en el periodo especificado
                continue

        notas[calificacion.id] = dict()
        notas[calificacion.id]["nota"] = calificacion

        if apm_mostrar:
            # - Obtener resumen de asistencia por materia            
            # Establecer fecha de inicio y fin de materia
            # Es cuatrimestral?
            # primer o segundo cuatrimestre?
            if calificacion.cuatrimestre == 1:
                inicio = inicio_clases
                if fin_periodo >= fin_cuatrimestre:
                    fin = fin_cuatrimestre
                else:
                    fin = fin_periodo
            elif calificacion.cuatrimestre == 2:
                inicio = fin_cuatrimestre
                fin = fin_periodo
            else:
                # Es anual
                inicio = inicio_clases
                fin = fin_periodo

            query_asignatura = db.asignatura.materia == calificacion.materia
            query_asignatura &= db.asignatura.nivel == calificacion.nivel
            query_asignatura &= db.asignatura.division == calificacion.division
            query_asignatura &= db.asignatura.titulo == calificacion.titulo
            query_asignatura &= db.asignatura.turno == calificacion.turno
            query_asignatura &= db.asignatura.comision == calificacion.comision                
            query_asignatura &= db.asignatura.cuatrimestre == calificacion.cuatrimestre
            asignatura = db(query_asignatura).select().first()

            notas[calificacion.id]["asistencia"] = asistenciamateria_alumno(db, asignatura, calificacion, alumno, inicio, fin)
    
    # - obtener resumen de calificaciones de talleres
    # 1) establecer si se informan talleres
    if talleres_mostrar:
        # 2) recuperar calificaciones de talleres si los hubiera
        # especificando período
        qt = db.taller_inscripcion.id == db.taller_calificacion.inscripcion
        qt &= db.taller_inscripcion.ciclo == ciclo
        qt &= db.taller_calificacion.boletin == boletin
        qt &= db.taller_inscripcion.estudiante == estudiante.id
        talleres = db(qt).select()
        
    # 1) Establecer si se muestran previas
    # 2) Recuperar previas de ciclos anteriores
    if previas_mostrar:
        previas = PREVIAS_ESTABLECER_FUNCION(db, alumno, plan, boletin)
    else:
        previas = None

    concepto = None
        
    if conceptos_mostrar:
        # Recuperar conceptos
        qcon = db.concepto.ciclo == inscripcion.ciclo
        qcon &= db.concepto.turno == inscripcion.turno
        qcon &= db.concepto.nivel == inscripcion.nivel
        qcon &= db.concepto.division == inscripcion.division
        qcon &= db.concepto.boletin == boletin
        conceptos = db(qcon).select().first()
        if not (conceptos is None):
            if inscripcion.id in conceptos.inscripciones:
                concepto = dict()
                for k, v in BOLETIN_CONCEPTOS_TIPOS.items():
                    concepto[v] = conceptos[k][conceptos.inscripciones.index(inscripcion.id)]
    return dict(notas=notas, asistencia=asistencia, talleres=talleres,
    previas=previas, concepto=concepto, inscripcion=inscripcion, estudiante=estudiante, boletin=boletin)

@auth.requires_membership('administradores')  
def tallerinscripcion():
    # Formulario de filtro
    # por ciclo, taller y docente
    form = SQLFORM.factory(
    Field("ciclo", requires=IS_IN_SET(CICLOS)), 
    Field("taller", requires=IS_IN_SET(TALLERES)),
    Field("docente", requires=IS_IN_DB(db, db.docente, "%(nombre)s")),
    Field("turno", requires=IS_EMPTY_OR(IS_IN_SET(TURNOS)), comment="Filtro opcional"), # filtro optativo
    Field("nivel", requires=IS_EMPTY_OR(IS_IN_SET(NIVELES)), comment="Filtro opcional"), # filtro optativo
    Field("division", requires=IS_EMPTY_OR(IS_IN_SET(DIVISIONES)), comment="Filtro opcional")) # filtro optativo
    if form.process().accepted:
        session.talleropciones = form.vars
        redirect(URL("tallerinscripcionlista"))
    return dict(form=form)

@auth.requires_membership('administradores')
def tallerinscripcionlista():
    # Filtra inscripciones por datos de
    # formulario de inicio
    # permite altas y bajas por
    # lista con tilde
    altas = 0
    bajas = 0
    completo = False
    
    docente = db(db.docente.id == session.talleropciones.docente).select().first()
    
    qi = db.taller_inscripcion.ciclo == session.talleropciones.ciclo
    qi &= db.taller_inscripcion.taller == session.talleropciones.taller
    qi &= db.taller_inscripcion.docente == session.talleropciones.docente
    inscripciones = db(qi).select()
    
    inscriptos = [inscripcion.estudiante for inscripcion in inscripciones]
    
    qa = db.inscripcion.estudiante == db.estudiante.id
    qa &= db.inscripcion.ciclo == session.talleropciones.ciclo
    if session.talleropciones.turno:
        qa &= db.inscripcion.turno == session.talleropciones.turno
    if session.talleropciones.nivel:
        qa &= db.inscripcion.nivel == session.talleropciones.nivel
    if session.talleropciones.division:
        qa &= db.inscripcion.division == session.talleropciones.division

    alumnos = db(qa).select()
    estudiantes = [alumno.inscripcion.estudiante for alumno in alumnos]
    campos = list()
    for alumno in alumnos:
        campo = Field("estudiante_%s" % alumno.inscripcion.estudiante, "boolean", label=alumno.estudiante.nombre, default=alumno.inscripcion.estudiante in inscriptos)
        campos.append(campo)
    form = SQLFORM.factory(*campos)
    
    if form.process().accepted:
        # recorrer opciones del formulario
        # realizar las altas y bajas 
        for k in form.vars:
            estudiante = int(k.split("_")[1])
            if form.vars[k]:
                if not estudiante in inscriptos:
                    # alta de inscripción a taller
                    db.taller_inscripcion.insert(
                    ciclo=session.talleropciones.ciclo,
                    taller=session.talleropciones.taller,
                    docente=session.talleropciones.docente,
                    estudiante=estudiante)
                    altas += 1
            else:
                if estudiante in inscriptos:
                    # baja de inscripción a taller
                    for inscripcion in inscripciones:
                        if inscripcion.estudiante == estudiante:
                            inscripcion.delete_record()
                    bajas += 1
        # devolver un informe session.flash
        # "Se crearon x inscripciones"
        # "Se eliminaron y inscripciones"
        response.flash = "Se ingresaron %s registros y se eliminaron %s" % (altas, bajas)
        completo = True
        # mostrar link para regresar a tallerinscripcion

    return dict(form=form, completo=completo, docente=docente)

@auth.requires_membership('administradores')
def tallercalificar():
    # formulario de filtro
    # por ciclo, taller y docente
    
    form = SQLFORM.factory(
    Field("ciclo", requires=IS_IN_SET(CICLOS)), 
    Field("taller", requires=IS_IN_SET(TALLERES)),
    Field("docente", requires=IS_IN_DB(db, db.docente, "%(nombre)s")),
    Field("boletin", requires=IS_IN_SET(BOLETINES)))
    if form.process().accepted:
        # Guardar parametros en session
        session.tallercalificaropciones = form.vars
        
        # Recuperar inscripciones a taller
        qi = db.taller_inscripcion.ciclo == form.vars.ciclo
        qi &= db.taller_inscripcion.taller == form.vars.taller
        qi &= db.taller_inscripcion.docente == form.vars.docente
        inscripciones = db(qi).select()
        inscriptos = [inscripcion.id for inscripcion in inscripciones]

        # Recuperar calificaciones previas
        qc = db.taller_calificacion.inscripcion.belongs(inscriptos)
        qc &= db.taller_calificacion.boletin == form.vars.boletin
        calificaciones = db(qc).select()
        session.tallercalificarregistros = [calificacion.id for calificacion in calificaciones]
        calificados = [calificacion.inscripcion for calificacion in calificaciones]

        # Si no hay registro del boletin seleccionado,
        # crearlo

        registros_nuevos = 0
        for inscripto in inscriptos:
            if not inscripto in calificados:
                session.tallercalificarregistros.append(db.taller_calificacion.insert(inscripcion = inscripto, boletin=form.vars.boletin))
                registros_nuevos += 1
        # session.flash "Se crearon x registros de calificaciones"
        session.flash = "Se crearon %s nuevas calificaciones" % registros_nuevos        
        # Redirigir a lista de calificaciones
        redirect(URL("tallercalificarlista"))
    return dict(form=form)

@auth.requires_membership('administradores')    
def tallercalificarlista():
    # Crear formulario al vuelo
    # autocompletando la nota con registros
    # previos

    campos = list()
    completo = False
    docente = db(db.docente.id == session.tallercalificaropciones.docente).select().first()
    q = db.taller_calificacion.inscripcion == db.taller_inscripcion.id
    q &= db.taller_inscripcion.estudiante == db.estudiante.id
    q &= db.taller_calificacion.id.belongs(session.tallercalificarregistros)
    notas = db(q).select()
    for nota in notas:
        campo = Field("nota_%s" % nota.taller_calificacion.id, label=nota.estudiante.nombre,
        requires=IS_EMPTY_OR(IS_IN_SET(TALLER_CALIFICACIONES)), default=nota.taller_calificacion.calificacion)
        campos.append(campo)

    form = SQLFORM.factory(*campos)
    if form.process().accepted:
        for k in form.vars:
            calificacion = int(k.split("_")[1])
            db(db.taller_calificacion.id == calificacion).select().first().update_record(calificacion=form.vars[k])
        completo = True
    return dict(form=form, completo=completo, docente=docente)

@auth.requires_membership('administradores')
def conceptos():
    # Formulario inicial
    # para carga de conceptos
    # por ciclo, turno, nivel y division
    form = SQLFORM.factory(
        Field("ciclo", requires=IS_IN_SET(CICLOS)),
        Field("turno", requires=IS_IN_SET(TURNOS)),
        Field("nivel" ,"integer", requires=IS_IN_SET(NIVELES)),
        Field("division", requires=IS_IN_SET(DIVISIONES)),
        Field("boletin", requires=IS_IN_SET(BOLETINES)))
    if form.process(onvalidation=plan_actualizar).accepted:
        session.conceptosopciones = form.vars
        redirect(URL("conceptoscompletar"))
    return dict(form=form)

@auth.requires_membership('administradores')    
def conceptoscompletar():
    # Muestra el curso seleccionado
    # para editar los conceptos
    # por alumno

    ciclo = int(session.conceptosopciones.ciclo)
    turno = session.conceptosopciones.turno
    nivel = int(session.conceptosopciones.nivel)
    division = int(session.conceptosopciones.division)
    boletin = int(session.conceptosopciones.boletin)

    # Recuperar todas las inscripciones
    fecha_limite = datetime.date(ciclo, BOLETINES_PLAZOS[boletin][1], BOLETINES_PLAZOS[boletin][0])
    qa = db.estudiante.id == db.inscripcion.estudiante
    qa &= db.inscripcion.ciclo == ciclo
    qa &= db.inscripcion.turno == turno
    qa &= db.inscripcion.nivel == nivel
    qa &= db.inscripcion.division == division
    qa &= ((db.inscripcion.baja == False) | (db.inscripcion.baja_fecha > fecha_limite))
    qa &= db.inscripcion.fecha < fecha_limite
    alumnos = db(qa).select()
    
    # Listado de indices de inscripcion
    inscripciones = [alumno.inscripcion.id for alumno in alumnos]

    # Objeto para almacenar cambios
    listados = dict()
    listados["inscripciones"] = inscripciones

    # Recuperar o crear registro de concepto
    # con los datos ingresados

    qc = db.concepto.ciclo == ciclo
    qc &= db.concepto.turno == turno
    qc &= db.concepto.nivel == nivel
    qc &= db.concepto.division == division
    qc &= db.concepto.boletin == boletin
    concepto = db(qc).select().first()

    # Armar arreglo de alumnos con conceptos y valores por defecto
    datos = dict()
    for alumno in alumnos:
        datos[alumno.inscripcion.id] = dict()
        datos[alumno.inscripcion.id]["nombre"] = alumno.estudiante.nombre
        datos[alumno.inscripcion.id]["documento"] = alumno.estudiante.documento_numero
        for k in BOLETIN_CONCEPTOS_TIPOS:
            datos[alumno.inscripcion.id][k] = None
        
    if concepto is None:
        for k in BOLETIN_CONCEPTOS_TIPOS:
            listados[k] = [None for inscripcion in inscripciones]

        concepto_id = db.concepto.insert(ciclo=ciclo, turno=turno, nivel=nivel, division=division, boletin=boletin, **listados)
    else:
        concepto_id = concepto.id
        # Recorrer concepto completando valores
        # previos del registro en datos
        for x in range(len(concepto.inscripciones)):
            inscripcion = int(concepto.inscripciones[x])
            if inscripcion in datos:
                for k in BOLETIN_CONCEPTOS_TIPOS:
                    datos[inscripcion][k] = concepto[k][x]
    campos = list()
    for inscripcion in datos:
        for k in BOLETIN_CONCEPTOS_TIPOS:
            default = None
            if not (concepto is None):
                if not (concepto["inscripciones"] is None):
                    if inscripcion in concepto["inscripciones"]:
                        if not (concepto[k] is None):
                            default = concepto[k][concepto["inscripciones"].index(inscripcion)]
            campo = Field("%s_%s" % (k, inscripcion), label="%s (%s)" % (datos[inscripcion]["nombre"], datos[inscripcion]["documento"]), comment=BOLETIN_CONCEPTOS_TIPOS[k], requires=IS_IN_SET(BOLETIN_CONCEPTOS), default=default)
            campos.append(campo)
    form = SQLFORM.factory(*campos)
    if form.process().accepted:
        # Actualizar listado con valores
        # del formulario
        for var in form.vars:
            tmp = var.split("_")
            concepto = "_".join((tmp[0], tmp[1]))
            inscripcion = int(tmp[2])
            datos[inscripcion][concepto] = form.vars[var]
        
        concepto = db(db.concepto.id == concepto_id).select().first()
        for k in BOLETIN_CONCEPTOS_TIPOS:
            listados[k] = [datos[inscripcion][k] for inscripcion in inscripciones]
        concepto.update_record(**listados)
        session.flash = "Se actualizaron los conceptos"
        redirect(URL("conceptos"))
    return dict(form=form, datos=datos)


def planseleccionar():
    estudiante_id = int(request.args[1])
    estudiante = db(db.estudiante.id == estudiante_id).select().first()
    qp = db.inscripcion.estudiante == estudiante_id
    qp &= db.inscripcion.ciclo == CICLOS[0]
    previa = db(qp).select().last()
    seleccion = False

    if not (previa is None):
        try:
            nivel = int(previa.nivel)
            division = int(previa.division)
            plan = DIVISIONES_PLAN[nivel][division]
            ultimo_plan = PLAN_ABREVIACIONES[plan]
        except TypeError:
            plan = None
            ultimo_plan = "Sin información"
    else:
        plan = None
        ultimo_plan = "Sin información"

    if "planes" in session:
        if estudiante_id in session.planes:
            plan = int(session.planes[estudiante_id])

    previa = db(db.inscripcion.estudiante == estudiante_id)
    form = SQLFORM.factory(
        Field("titulo", "integer",
              label="Plan",
              comment="Seleccione un plan. Plan del último ciclo: %s" % ultimo_plan,
              default=plan,
              requires=IS_IN_SET(PLAN_ABREVIACIONES)),
    )
    if form.process().accepted:
        if not ("planes" in session):
            session.planes = dict()
        session.planes[estudiante_id] = int(form.vars.titulo)
        seleccion = True
    return dict(form=form, estudiante=estudiante,
    seleccion=seleccion)

