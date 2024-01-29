# -*- coding: utf-8 -*-

__author__ = "Alan Edmundo Etkin <spametki@gmail.com>"
__copyright__ = "(C) 2024 Alan Edmundo Etkin. GNU GPL 3."

@auth.requires_membership('administradores')
def partedeaula():
    form = SQLFORM.factory(
        Field("ciclo", "integer", requires=IS_IN_SET(CICLOS),
              default=ciclo_determinar(datetime.date.today())),
        Field("turno", requires=IS_IN_SET(TURNOS)),
        Field("nivel", "integer", requires=IS_IN_SET(NIVELES)),
        Field("division", requires=IS_EMPTY_OR(IS_IN_SET(DIVISIONES))),
        Field("cuatrimestre", requires=IS_EMPTY_OR(IS_IN_SET(CUATRIMESTRES)),
        comment="Si es anual dejar en blanco"),
        Field("comision", requires=IS_EMPTY_OR(IS_IN_SET(COMISIONES)),
        comment="Si no tiene comisiones dejar en blanco"),
        Field("contraturno", requires=IS_EMPTY_OR(IS_IN_SET(TURNOS)),
              default=None,
              comment="Turno de cursada. Dejar en blanco si se cursa en igual horario"),
        Field("materia", requires=IS_EMPTY_OR(IS_IN_SET(
        MATERIAS)), comment="Asistencia general dejar en blanco",
        default=None),
        Field("fecha", "date",
        default=datetime.date.today(),
        requires=IS_DATE()),
    )
    if form.process(onvalidation=plan_actualizar).accepted:
        session.parte = form.vars
        redirect(URL("partecompletar"))
    return dict(form=form)
    
@auth.requires_membership('administradores')
def partecompletar():
    # Arreglo de incompatibilidad de fecha en texto
    # como argumento de Query
    if type(session.parte.fecha) == str:
        fecha_tmp = convertir_a_datetime(session.parte.fecha)
        fecha = datetime.date(fecha_tmp.year, fecha_tmp.month, fecha_tmp.day)
    else:
        fecha = session.parte.fecha

    q = db.asistencia.fecha == fecha
    q &= db.asistencia.ciclo == session.parte.ciclo
    q &= db.asistencia.turno == session.parte.turno
    q &= db.asistencia.contraturno == session.parte.contraturno
    
    # buscar estudiantes por materia o por división
    # según el caso

    if not session.parte.materia is None:
        q &= db.asistencia.materia == session.parte.materia

        qe = db.calificacion.materia == session.parte.materia
        qe &= db.calificacion.ciclo == session.parte.ciclo
        qe &= db.calificacion.turno == session.parte.turno
        qe &= db.calificacion.nivel == session.parte.nivel
        qe &= db.calificacion.division == session.parte.division
        qe &= db.calificacion.comision == session.parte.comision
        qe &= db.calificacion.cuatrimestre == session.parte.cuatrimestre
        
        estudiantes_id = [calificacion.estudiante for calificacion in db(qe).select()]
        
        # recuperar asignatura
        qa = db.asignatura.materia == session.parte.materia
        qa &= db.asignatura.turno == session.parte.turno
        qa &= db.asignatura.nivel == session.parte.nivel
        qa &= db.asignatura.division == session.parte.division
        qa &= db.asignatura.comision == session.parte.comision
        qa &= db.asignatura.cuatrimestre == session.parte.cuatrimestre
        asignatura = db(qa).select().first()
        if asignatura is None:
            raise HTTP(500, "No se encontró la asignatura con los datos especificados")
        diadeclase = asignatura[DIAS_PYTHON_REVERSO[fecha.weekday()]]
        if (diadeclase is None) or (len(diadeclase) == 0):
            raise HTTP(500, "La fecha no corresponde a un día de la asignatura")
        if asignatura.contraturno != session.parte.contraturno:
            raise HTTP(500, "La información de contraturno no coincide con la asignatura")        

    else:
        qe = db.inscripcion.ciclo == session.parte.ciclo
        qe &= db.inscripcion.turno == session.parte.turno                
        qe &= db.inscripcion.nivel == session.parte.nivel
        qe &= db.inscripcion.division == session.parte.division
        
        estudiantes_id = [inscripcion.estudiante for inscripcion in db(qe).select()]


    # Recuperar los estudiantes de la BBDD
    estudiantes = db(db.estudiante.id.belongs(estudiantes_id)).select()
    
    # crear o recuperar el registro de asistencia
    asistencia = db(q).select().first()

    asistencia_previa = dict()

    if asistencia is None:
        session.asistencia_id = db.asistencia.insert(**session.parte)
        for estudiante in estudiantes:
            asistencia_previa[estudiante.id] = ASISTENCIA_POR_DEFECTO
    else:
        session.asistencia_id = asistencia.id
        # recuperar parte para autocompletar presentes
        # generar lista con valores previos
        for estudiante in estudiantes:
            asistencia_previa[estudiante.id] = ASISTENCIA_POR_DEFECTO
            for k in ASISTENCIA_CATEGORIAS:
                if (not asistencia[ASISTENCIA_CATEGORIAS[k]] is None) and (estudiante.id in asistencia[ASISTENCIA_CATEGORIAS[k]]):
                    asistencia_previa[estudiante.id] = k
                    
    # para cambiar a "radio" en opciones de formulario
    # hay que utilizar la opción
    # widget=SQLFORM.widgets.radio.widget
    # en Field()

    form = SQLFORM.factory(*[Field("estudiante_%s" % (estudiante.id), requires=IS_IN_SET(ASISTENCIA.keys()),
    label=estudiante.nombre[0:25],
    comment="Doc. %s %s" % (estudiante.documento_tipo or "", estudiante.documento_numero),
    default=asistencia_previa[estudiante.id], widget=RadioWidgetAlternative.widget) for estudiante in estudiantes])
          
    if form.process().accepted:
        if asistencia is None:
            # recuperar registro de asistencia
            asistencia = db(db.asistencia.id == session.asistencia_id).select().first()
            
        # recorrer cada item de asistencia por id del estudiante
        for estudiante in estudiantes:
            for k in ASISTENCIA:
                if asistencia[ASISTENCIA_CATEGORIAS[k]] is None:
                    asistencia[ASISTENCIA_CATEGORIAS[k]] = list()
            
                if form.vars["estudiante_%s" % estudiante.id] == k:
                    if not (estudiante.id in asistencia[ASISTENCIA_CATEGORIAS[k]]):
                        asistencia[ASISTENCIA_CATEGORIAS[k]].append(estudiante.id)
                else:
                    # eliminar registros previos
                    if estudiante.id in asistencia[ASISTENCIA_CATEGORIAS[k]]:
                        asistencia[ASISTENCIA_CATEGORIAS[k]].remove(estudiante.id)
        
        asistencia.update_record()
        redirect("partefinalizar")
                        
    return dict(form=form, datos=session.parte)

@auth.requires_membership('administradores')
def partefinalizar():
    asistencia = db(db.asistencia.id == session.asistencia_id).select().first()
    
    if asistencia is None:
        raise HTTP(500, "No se encontró el registro en la BBDD")

    campos = ["ciclo", "turno", "contraturno", "materia", "fecha"]
    categorias = [v for k, v in ASISTENCIA_CATEGORIAS.items()]
    campos = campos + categorias
    form = SQLFORM(db.asistencia, asistencia.id, readonly=True, fields=campos)

    return dict(form=form)

@auth.requires_membership('consultas')
def asistencia():
    # muestra la asistencia de materia o curso
    # en el rango de fechas indicado
    
    hoy = datetime.date.today()
    # Determinar ciclo
    ciclo = ciclo_determinar(hoy)
    # Calcular fecha de inicio del ciclo actual
    if ciclo == hoy.year:
        inicio = datetime.date(ciclo, CICLO_CAMBIO[1], CICLO_CAMBIO[0])
    else:
        inicio = datetime.date(ciclo -1, CICLO_CAMBIO[1], CICLO_CAMBIO[0])
        
    form = SQLFORM.factory(
        Field("ciclo", "integer", requires=IS_IN_SET(CICLOS),
              default=ciclo_determinar(datetime.date.today())),
        Field("turno", requires=IS_IN_SET(TURNOS)),
        Field("nivel", "integer", requires=IS_IN_SET(NIVELES)),
        Field("division", requires=IS_EMPTY_OR(IS_IN_SET(DIVISIONES))),
        Field("cuatrimestre", requires=IS_EMPTY_OR(IS_IN_SET(CUATRIMESTRES)),
        comment="Si es anual dejar en blanco"),
        Field("comision", requires=IS_EMPTY_OR(IS_IN_SET(COMISIONES)),
        comment="Si no tiene comisiones dejar en blanco"),
        Field("contraturno", requires=IS_EMPTY_OR(IS_IN_SET(TURNOS)),
              default=None,
              comment="Turno de cursada. Dejar en blanco si se cursa en igual horario"),
        Field("materia", requires=IS_EMPTY_OR(IS_IN_SET(
        MATERIAS)), comment="Asistencia general dejar en blanco",
        default=None),
        Field("desde", "date",
        default=inicio,
        requires=IS_DATE()),
        Field("hasta", "date",
        default=hoy,
        requires=IS_DATE()),
    )
    if form.process().accepted:
        session.asistencia_control = form.vars
        if form.vars.materia is None:
            # asistencia por jornada
            redirect("asistenciamostrar")            
        else:
            # asistencia por materia
            redirect("asistenciamateriamostrar")
    return dict(form=form)


@auth.requires_membership('consultas')
def asistenciamostrar():
    # asistencia por jornada

    # - Indicar altas y bajas por mes con
    # n alumnos el primer día y n alumnos el último

    # - Almacenar total asistencia por mes para mostrar
    # en las tablas.

    totales_por_mes = dict()
    totales_inasistencias_por_mes = dict()
    medias = dict()
    porcentajes = dict()
    inscriptos = dict()
    altas = dict()
    bajas = dict()

    # - Almacenar dias de clase sin suspensión por mes para
    # cálculo de inasistencias

    dias_normales = dict()
    
    # - Calcular y mostrar promedio y asistencia media por mes
    
    # En formato weekday
    diasdeclase = [DIAS_PYTHON[dia] for dia in DIAS]

    # mapea ordinal con date
    fechas = dict()    

    # objeto para almacenar registro
    registro = dict()

    if session.asistencia_control is None:
        response.flash = "No se especificó curso o materia"
        redirect("asistencia")

    # legibilidad de variables
    desde = session.asistencia_control.desde
    hasta = session.asistencia_control.hasta
    ciclo = session.asistencia_control.ciclo
    turno = session.asistencia_control.turno
    division = session.asistencia_control.division
    nivel = session.asistencia_control.nivel

    # corregir fecha límite
    # hasta = hasta + datetime.timedelta(days=1)

    # 0) Obtener todos los estudiantes comprendidos
    
    qe = db.estudiante.id == db.inscripcion.estudiante
    qe &= db.inscripcion.ciclo == ciclo
    qe &= db.inscripcion.turno == turno
    qe &= db.inscripcion.nivel == nivel
    qe &= db.inscripcion.division == division

    estudiantes = db(qe).select()

    # 1) Establecer fechas límite por datos
    # del formulario

    estudiantes_ids = list()
    estudiantes_altas = dict()
    estudiantes_bajas = dict()
    for estudiante in estudiantes:
        estudiantes_ids.append(estudiante.estudiante.id)
        estudiantes_altas[estudiante.estudiante.id] = estudiante.inscripcion.fecha
        estudiantes_bajas[estudiante.estudiante.id] = estudiante.inscripcion.baja_fecha

    # 2) Recuperar registros de asistencia
    # usando los criterios del formulario
    
    qa = db.asistencia.ciclo == ciclo
    qa &= db.asistencia.turno == turno
    qa &= db.asistencia.materia == None
    qa &= db.asistencia.fecha >= desde
    qa &= db.asistencia.fecha <= hasta

    asistencias = db(qa).select()

    # 3) Recuperar los registros de suspensiones
    # de actividad en el rango especificado

    # filtro de suspensiones que abarcan la division
    # hay que filtrar campos que:
    
    # 1) no sean de este ciclo
    # 2) materia no sea NULL
    # 3) no estén comprendidos por las fechas
    # 2) si no son NULL, no tengan esta division
    # 3) si no son NULL, no sean de este turno
    # 3) si no son NULL, no sean de este nivel

    qs = db.suspension_actividad.desde <= hasta
    qs &= db.suspension_actividad.hasta >= desde
    
    subquery = (db.suspension_actividad.turno == None) | (db.suspension_actividad.turno == turno)
    subquery &= (db.suspension_actividad.nivel == None) | (db.suspension_actividad.nivel == nivel)
    subquery &= (db.suspension_actividad.division == None) | (db.suspension_actividad.division == division)
    
    qs &= subquery
    
    suspensiones = db(qs).select()
    
    # Hay que armar una tabla para establecer
    # suspensiones por día/fecha/turno/hora

    # genero horas por turno en formato time    
    horarios = horas_a_time(HORARIOS)

    # almacena las suspensiones
    grilla = dict()
    
    d = desde
    while d <= hasta:
        ordinal = d.toordinal()
        fechas[ordinal] = d

        if not d.month in dias_normales:
            dias_normales[d.month] = 0
        
        # agregar dia/mes al registro
        if not d.month in registro:
            registro[d.month] = dict()
        if not d.day in registro[d.month]:
            registro[d.month][d.day] = dict()
            registro[d.month][d.day]["turnos"] = tuple()
            registro[d.month][d.day]["partes"] = 0

        # mapear mes/dia a ordinal
        registro[d.month][d.day]["ordinal"] = ordinal
        
        if d.weekday() in diasdeclase:
            registro[d.month][d.day]["semana"] = True
        else:
            registro[d.month][d.day]["semana"] = False

        # agregar día a las suspensiones
        grilla[ordinal] = dict()
        d += datetime.timedelta(days=1)

    # los objetos time límite horario por turno
    limites = dict()
    
    for k in horarios:   
        limites[k] = (horarios[k][0][0], horarios[k][-1][-1])

    for suspension in suspensiones:
        # establecer los días que comprende
        # la suspension en ordinal
        dia_inicial = datetime.date.fromordinal(suspension.desde.toordinal())
        hora_inicial = datetime.time(suspension.desde.hour, suspension.desde.minute)
        dia_final = datetime.date.fromordinal(suspension.hasta.toordinal())
        hora_final = datetime.time(23, 59)
        dia = dia_inicial
        
        while dia <= dia_final:
            if dia == dia_final:
                hora_final = datetime.time(suspension.hasta.hour, suspension.hasta.minute)

            ordinal = dia.toordinal()
            if ordinal in grilla:
                for k in horarios:
                    if (limites[k][0] >= hora_inicial) and (limites[k][1] <= hora_final):
                        grilla[ordinal][k] = suspension.motivo

            dia += datetime.timedelta(days=1)
            hora_inicial = datetime.time(0, 0)
    
    # 4) Componer tabla de alumnos por día
    # completando asistencia/inasistencia
    # y no computando partes que coincidan
    # con suspensiones de actividad.

    # datos es un objeto dict de dos dimensiones
    # con alumnos y dias de cursada
    
    datos = dict()
   
    for row in estudiantes:
        datos[row.estudiante.id] = dict(nombre=row.estudiante.nombre,
                                        documento="%s %s" % (row.estudiante.documento_tipo or "",
                                                             row.estudiante.documento_numero),
                                        asistencia=dict(),
                                        totales=dict(),
                                        totales_inasistencias=dict(),
                                        total=0,
                                        total_inasistencias=0)

    categorias = dict()
    for k, v in ASISTENCIA_CATEGORIAS.items():
        categorias[v] = k

    for parte in asistencias:
        # Completar objeto datos
        # recorriendo cada parte indicando
        # en el item por estudiante la fecha
        # en ordinal y asociada una tupla con
        # asistencia a turno y contraturno
        ordinal = parte.fecha.toordinal()
        registro[parte.fecha.month][parte.fecha.day]["partes"] += 1
        if parte.contraturno is None:
            registro[parte.fecha.month][parte.fecha.day]["turnos"] += (parte.turno,)
        else:
            registro[parte.fecha.month][parte.fecha.day]["turnos"] += (parte.contraturno,)

        if parte.contraturno is None:
            parteturno = parte.turno
        else:
            parteturno = parte.contraturno
        
        for k in categorias:
            if type(parte[k]) is list:
                for e in parte[k]:
                    if e in datos:
                        # se encontró un registro
                        # de asistencia del curso
                        if not (ordinal in datos[e]["asistencia"]):
                            datos[e]["asistencia"][ordinal] = (None, None)

                        # completar asistencia por estudiante
                        # si hubo suspensión no se computa al inasistencia
                        
                        if parteturno == parte.turno:
                            # igual turno
                            if parteturno in grilla[ordinal]:
                                t = None
                            else:
                                t = categorias[k]
                            ct = datos[e]["asistencia"][ordinal][1]
                        else:
                            # contraturno                            
                            if parteturno in grilla[ordinal]:
                                ct = None
                            else:
                                ct = categorias[k]
                            t = datos[e]["asistencia"][ordinal][0]

                        datos[e]["asistencia"][ordinal] = (t, ct)
        
    # Agrupar días por mes indicando subtotales
    # por renglón. Contemplar contraturno y
    # dividir por dos las inasistencias en caso
    # de dos partes por día.
    # Utilizar conjunto de variables que especifiquen
    # cómo se computa tarde y ausente en turno simple
    # y doble.
    
    for ordinal, dia in fechas.items():
        turnos_suspendidos = 0
        for t in registro[dia.month][dia.day]["turnos"]:
            if t in grilla[ordinal]:
                turnos_suspendidos += 1
        if turnos_suspendidos >= registro[dia.month][dia.day]["partes"]:
            registro[dia.month][dia.day]["suspension"] = True
        else:
            registro[dia.month][dia.day]["suspension"] = False
            
        if not registro[dia.month][dia.day]["suspension"]:
            if registro[dia.month][dia.day]["semana"]:
                if registro[dia.month][dia.day]["partes"] > 0:
                    # se calcula el día
                    dias_normales[dia.month] += 1

    datos_descarte = list()

    # recorrer registro calculando la asistencia
    # y sumando a los totales por columna/fila
    # Registrar en inscriptos qué día fueron
    # alumnos y qué días no

    # Si la alta o baja coincide con el día
    # agregar al objeto dict en el mes/día
    
    for e in datos:
    
        # agregar información de altas y bajas por mes
        alta = estudiantes_altas[e]
        baja = estudiantes_bajas[e]
        if desde <= alta <= hasta:
            if not alta.month in altas:
                altas[alta.month] = set()
            altas[alta.month].add(e)
        if not (estudiantes_bajas[e] is None):
            if desde <= baja <= hasta:
                if not baja.month in bajas:
                    bajas[baja.month] = set()
                bajas[baja.month].add(e)
    
        for ordinal in datos[e]["asistencia"]:
            dia = fechas[ordinal]
            if not dia.month in inscriptos:
                inscriptos[dia.month] = dict()
            if not dia.day in inscriptos[dia.month]:
                inscriptos[dia.month][dia.day] = set()

            computar = False
            descartar = False

            if (estudiantes_altas[e] is None) or (estudiantes_altas[e] <= dia):
                computar = True
                inscriptos[dia.month][dia.day].add(e)
                
                if not (estudiantes_bajas[e] is None):
                    if estudiantes_bajas[e] <= dia:
                        inscriptos[dia.month][dia.day].discard(e)
                        computar = False
                        descartar = True
            else:
                descartar = True

            if descartar:
                # preparar el item para eliminar
                # al finalizar el bucle
                datos_descarte.append((e, ordinal))

            if not dia.month in totales_por_mes:
                totales_por_mes[dia.month] = 0

            if not dia.month in totales_inasistencias_por_mes:
                totales_inasistencias_por_mes[dia.month] = 0

            if not dia.month in datos[e]["totales"]:
                datos[e]["totales"][dia.month] = 0

            if not dia.month in datos[e]["totales_inasistencias"]:
                datos[e]["totales_inasistencias"][dia.month] = 0

            if not "total" in registro[dia.month][dia.day]:
                registro[dia.month][dia.day]["total"] = 0

            if registro[dia.month][dia.day]["suspension"]:
                computar = False
                
            if computar:
                # - calcular asistencia del día/alumno
                alumno_dia = asistencia_calcular(datos[e]["asistencia"][ordinal])

                # - sumar a total dia/mes y almacenar
                registro[dia.month][dia.day]["total"] += alumno_dia

                # - sumar a total mes/alumno y almacenar
                datos[e]["totales"][dia.month] += alumno_dia

                # - sumar a total inasistencias mes/alumno y almacenar
                datos[e]["totales_inasistencias"][dia.month] += 1 - alumno_dia
                
                # - sumar a total rango/alumno y almacenar
                datos[e]["total"] += alumno_dia

                # - sumar a total inasistencias rango/alumno y almacenar
                datos[e]["total_inasistencias"] += 1 - alumno_dia

                # - Sumar a totales por mes
                totales_por_mes[dia.month] += alumno_dia

                # - Sumar a totales inasistencias por mes
                totales_inasistencias_por_mes[dia.month] += 1 - alumno_dia

    # eliminar registros de asistencia fuera de fecha de inscripción o baja
    for item in datos_descarte:
        del(datos[item[0]]["asistencia"][item[1]])
   
    # recorrer registro calculando totales por mes
    for mes in registro:
        if not mes in totales_por_mes:
            totales_por_mes[mes] = 0
            totales_inasistencias_por_mes[mes] = 0
        
        medias[mes] = asistencia_media(dias_normales[mes], totales_por_mes[mes])
        porcentajes[mes] = asistencia_porcentaje(totales_por_mes[mes], totales_inasistencias_por_mes[mes])

    return dict(limites=limites, grilla=grilla, horarios=horarios,
                suspensiones=suspensiones, datos=datos,
                registro=registro, totales_por_mes=totales_por_mes,
                dias_normales = dias_normales,
                totales_inasistencias_por_mes = totales_inasistencias_por_mes,
                medias=medias, porcentajes=porcentajes,
                inscriptos=inscriptos, altas=altas, bajas=bajas)

@auth.requires_membership('consultas')
def asistenciamateriamostrar():
    # Asistencia por materia
    # Indicar altas y bajas por mes con
    # n alumnos el primer día y n alumnos el último
    # - Almacenar total asistencia por mes para mostrar
    # en las tablas.
    
    totales_por_mes = dict()
    totales_inasistencias_por_mes = dict()
    medias = dict()
    porcentajes = dict()
    inscriptos = dict()
    altas = dict()
    bajas = dict()

    # - Almacenar dias de clase sin suspensión por mes para
    # cálculo de inasistencias

    dias_normales = dict()
    asignatura_horas = dict()
    
    # - Cálcular y mostrar promedio y asistencia media por mes
    
    # En formato weekday
    diasdeclase = [DIAS_PYTHON[dia] for dia in DIAS]

    # mapea ordinal con date
    fechas = dict()    

    # objeto para almacenar registro
    registro = dict()

    if session.asistencia_control is None:
        response.flash = "No se especificó curso o materia"
        redirect("asistencia")

    # legibilidad de variables
    desde = session.asistencia_control.desde
    hasta = session.asistencia_control.hasta
    ciclo = session.asistencia_control.ciclo
    turno = session.asistencia_control.turno
    nivel = session.asistencia_control.nivel
    division = session.asistencia_control.division
    materia = session.asistencia_control.materia
    cuatrimestre = session.asistencia_control.cuatrimestre
    comision = session.asistencia_control.comision
    contraturno = session.asistencia_control.contraturno

    # -1) Obtener horarios de la materia en la BDD
    qa = db.asignatura.materia == materia
    qa &= db.asignatura.nivel == nivel
    qa &= db.asignatura.division == division
    qa &= db.asignatura.comision == comision
    qa &= db.asignatura.cuatrimestre == cuatrimestre

    asignatura = db(qa).select().first()
    
    for dia in DIAS:
        if not (asignatura[dia] is None):
            if type(asignatura[dia]) is int:
                asignatura_horas[DIAS_PYTHON[dia]] = set((asignatura[dia],))
            elif len(asignatura[dia]) == 0:
                pass
            else:
                asignatura_horas[DIAS_PYTHON[dia]] = set(asignatura[dia])

    asignatura_turno = None

    if asignatura is None:
        response.flash = "No se encontraron datos de la asignatura"
        redirect("asistencia")
    else:
        if asignatura.contraturno is None:
            asignatura_turno = asignatura.turno
        else:
            asignatura_turno = asignatura.contraturno
    
    # 0) Obtener todos los estudiantes comprendidos
    
    # filtrar criterio de cuatrimestrales: cuatrimestre y comisión
    qe = db.estudiante.id == db.calificacion.estudiante
    qe &= db.calificacion.ciclo == ciclo
    qe &= db.calificacion.turno == turno
    qe &= db.calificacion.nivel == nivel
    qe &= db.calificacion.division == division
    qe &= db.calificacion.materia == materia
    qe &= db.calificacion.comision == comision
    qe &= db.calificacion.cuatrimestre == cuatrimestre
    
    estudiantes = db(qe).select()

    # 1) Establecer fechas límite por datos
    # del formulario

    estudiantes_ids = list()
    estudiantes_altas = dict()
    estudiantes_bajas = dict()
    for estudiante in estudiantes:
        estudiantes_ids.append(estudiante.estudiante.id)
        estudiantes_altas[estudiante.estudiante.id] = estudiante.calificacion.alta_fecha
        estudiantes_bajas[estudiante.estudiante.id] = estudiante.calificacion.baja_fecha

    # 2) Recuperar registros de asistencia
    # usando los criterios del formulario
    
    qa = db.asistencia.ciclo == ciclo
    qa &= db.asistencia.turno == turno
    qa &= db.asistencia.contraturno == contraturno
    qa &= db.asistencia.materia == materia
    qa &= db.asistencia.fecha >= desde
    qa &= db.asistencia.fecha <= hasta

    asistencias = db(qa).select()
    
    # 3) Recuperar los registros de suspensiones
    # de actividad en el rango especificado

    # filtro de suspensiones que abarcan la division
    # hay que filtrar campos que:
    
    # Adaptar a materias/cuatrimestres/comisiones
    
    # 1) no sean de este ciclo
    # 2) materia no sea NULL
    # 3) no estén comprendidos por las fechas
    # 2) si no son NULL, no tengan esta division
    # 3) si no son NULL, no sean de este turno
    # 3) si no son NULL, no sean de este nivel

    if not (contraturno is None):
        criterio_turno = contraturno
    else:
        criterio_turno = turno

    qs = db.suspension_actividad.desde <= hasta
    qs &= db.suspension_actividad.hasta >= desde
    subquery = (db.suspension_actividad.turno == None) | (db.suspension_actividad.turno == criterio_turno)
    subquery &= (db.suspension_actividad.nivel == None) | (db.suspension_actividad.nivel == nivel)
    subquery &= (db.suspension_actividad.materia == None) | (db.suspension_actividad.materia == materia)
    subquery &= (db.suspension_actividad.comision == None) | (db.suspension_actividad.comision == comision)    
    qs &= subquery
    
    suspensiones = db(qs).select()
    
    # Hay que armar una tabla para establecer
    # suspensiones por día/fecha/turno/hora

    # genero horas por turno en formato time    
    horarios = horas_a_time(HORARIOS)

    # almacena las suspensiones
    grilla = dict()

    # - Para los arreglos de asistencia por materia
    # hay que filtrar días/horas por un objeto
    # horarios por materia tomando la información
    # del objeto asignatura
    
    d = desde
    while d <= hasta:
        ordinal = d.toordinal()
        
        if (d.weekday() in asignatura_horas):
            fechas[ordinal] = d
            
            if not d.month in dias_normales:
                dias_normales[d.month] = 0
        
            # agregar dia/mes al registro
            if not d.month in registro:
                registro[d.month] = dict()
            if not d.day in registro[d.month]:
                registro[d.month][d.day] = dict()
                registro[d.month][d.day]["turnos"] = tuple()
                registro[d.month][d.day]["partes"] = 0

            # mapear mes/dia a ordinal
            registro[d.month][d.day]["ordinal"] = ordinal
        
            if d.weekday() in diasdeclase:
                registro[d.month][d.day]["semana"] = True
            else:
                registro[d.month][d.day]["semana"] = False

            # agregar día a las suspensiones
            grilla[ordinal] = dict()

        d += datetime.timedelta(days=1)

    # Objeto especial por materia que especifica los límites
    # según el día de clase.
    materia_limites = dict()
 
    for dia in asignatura_horas:
        # - hay que generar una tupla con los límites inferior y superior
        # en objetos datetime.time de horarios
        # - requiere ver la extensión de ese día en horas y tomar
        # la hora de inicio de la primera hora y la hora de final
        # de la última. SEGUIR CÓDIGO DESDE ACÁ

        dia_horas = tuple(asignatura_horas[dia])
        materia_limites[dia] = (horarios[criterio_turno][dia_horas[0]][0],
                                horarios[criterio_turno][dia_horas[-1]][-1])

    # Modificar algoritmo para que establezca chequeando las
    # horas de la materia del día si la suspensión abarca todo el
    # horario de ese día. También hay que establecer el turno
    # teniendo en cuenta si es materia a contraturno.
    
    for suspension in suspensiones:
        # establecer los días que comprende
        # la suspension en ordinal
        dia_inicial = datetime.date.fromordinal(suspension.desde.toordinal())
        hora_inicial = datetime.time(suspension.desde.hour, suspension.desde.minute)
        dia_final = datetime.date.fromordinal(suspension.hasta.toordinal())
        hora_final = datetime.time(23, 59)
        dia = dia_inicial
        
        while dia <= dia_final:
            if dia == dia_final:
                hora_final = datetime.time(suspension.hasta.hour, suspension.hasta.minute)

            dia_numero = dia.weekday()
            ordinal = dia.toordinal()
            
            if ordinal in grilla:
                if (materia_limites[dia_numero][0] >= hora_inicial) and (materia_limites[dia_numero][-1] <= hora_final):
                    grilla[ordinal][asignatura_turno] = suspension.motivo
                        
            dia += datetime.timedelta(days=1)
            hora_inicial = datetime.time(0, 0)
    
    # 4) Componer tabla de alumnos por día
    # completando asistencia/inasistencia
    # y no computando partes que coincidan
    # con suspensiones de actividad.

    # datos es un objeto dict de dos dimensiones
    # con alumnos y dias de cursada
    
    datos = dict()
   
    for row in estudiantes:
        datos[row.estudiante.id] = dict(nombre=row.estudiante.nombre,
                                        documento="%s %s" % (row.estudiante.documento_tipo or "",
                                                             row.estudiante.documento_numero),
                                        asistencia=dict(),
                                        totales=dict(),
                                        totales_inasistencias=dict(),
                                        total=0,
                                        total_inasistencias=0)

    categorias = dict()
    for k, v in ASISTENCIA_CATEGORIAS.items():
        categorias[v] = k

    for parte in asistencias:
        # Completar objeto datos
        # recorriendo cada parte indicando
        # en el item por estudiante la fecha
        # en ordinal y asociada una tupla con
        # asistencia a turno y contraturno
        ordinal = parte.fecha.toordinal()
        registro[parte.fecha.month][parte.fecha.day]["partes"] += 1
        
        if parte.contraturno is None:
            registro[parte.fecha.month][parte.fecha.day]["turnos"] += (parte.turno,)
        else:
            registro[parte.fecha.month][parte.fecha.day]["turnos"] += (parte.contraturno,)

        for k in categorias:
            if type(parte[k]) is list:
                for e in parte[k]:
                    if e in datos:
                        # se encontró un registro
                        # de asistencia del curso
                        
                        # Esto no va, código de asistencia general
                        # if not (ordinal in datos[e]["asistencia"]):
                        #    datos[e]["asistencia"][ordinal] = None

                        # completar asistencia por estudiante
                        # si hubo suspensión no se computa la inasistencia
                        # se almacena la asistencia como tupla para compatibilidad
                        # con la función de cálculo para asistencia general
                        # if grilla[ordinal] is None:
                        #    datos[e]["asistencia"][ordinal] = (categorias[k], None)                        
                        # else:
                        #    datos[e]["asistencia"][ordinal] = (None, None)
                        if asignatura_turno in grilla[ordinal]:
                            datos[e]["asistencia"][ordinal] = (None, None)                        
                        else:
                            datos[e]["asistencia"][ordinal] = (categorias[k], None)
        
    # Agrupar días por mes indicando subtotales
    # por renglón. Contemplar contraturno y
    # dividir por dos las inasistencias en caso
    # de dos partes por día.
    # Utilizar conjunto de variables que especifiquen
    # cómo se computa tarde y ausente en turno simple
    # y doble.

    for ordinal, dia in fechas.items():
        turnos_suspendidos = 0
        for t in registro[dia.month][dia.day]["turnos"]:
            if t in grilla[ordinal]:
                turnos_suspendidos += 1
        if turnos_suspendidos >= registro[dia.month][dia.day]["partes"]:
            registro[dia.month][dia.day]["suspension"] = True
        else:
            registro[dia.month][dia.day]["suspension"] = False
        if not registro[dia.month][dia.day]["suspension"]:
            if registro[dia.month][dia.day]["semana"]:
                if registro[dia.month][dia.day]["partes"] > 0:
                    # se calcula el día
                    dias_normales[dia.month] += 1

    datos_descarte = list()

    # recorrer registro calculando la asistencia
    # y sumando a los totales por columna/fila
    # Registrar en inscriptos qué día fueron
    # alumnos y qué días no

    # Si la alta o baja coincide con el día
    # agregar al objeto dict en el mes/día

    for e in datos:
        # agregar información de altas y bajas por mes
        alta = estudiantes_altas[e]
        baja = estudiantes_bajas[e]
        
        if not (alta is None):
            if desde <= alta <= hasta:
                if not alta.month in altas:
                    altas[alta.month] = set()
                altas[alta.month].add(e)
            
        if not (baja is None):
            if desde <= baja <= hasta:
                if not baja.month in bajas:
                    bajas[baja.month] = set()
                bajas[baja.month].add(e)
    
        for ordinal in datos[e]["asistencia"]:
            dia = fechas[ordinal]
            if not dia.month in inscriptos:
                inscriptos[dia.month] = dict()
            if not dia.day in inscriptos[dia.month]:
                inscriptos[dia.month][dia.day] = set()

            computar = False
            descartar = False

            if not (alta is None):
                if alta <= dia:
                    computar = True
                    inscriptos[dia.month][dia.day].add(e)

                    if not (baja is None):
                        if baja <= dia:
                            inscriptos[dia.month][dia.day].discard(e)
                            computar = False
                            descartar = True
                else:
                    descartar = True
            else:
                # si no hay información de alta
                # se considera al alumno de alta
                # en todo el ciclo
                computar = True

            # No sumar asistencias/inasistencias si en ese día
            # hubo suspension

            if descartar:
                # preparar el item para eliminar
                # al finalizar el bucle
                datos_descarte.append((e, ordinal))

            if not dia.month in totales_por_mes:
                totales_por_mes[dia.month] = 0

            if not dia.month in totales_inasistencias_por_mes:
                totales_inasistencias_por_mes[dia.month] = 0

            if not dia.month in datos[e]["totales"]:
                datos[e]["totales"][dia.month] = 0

            if not dia.month in datos[e]["totales_inasistencias"]:
                datos[e]["totales_inasistencias"][dia.month] = 0

            if not "total" in registro[dia.month][dia.day]:
                registro[dia.month][dia.day]["total"] = 0

            if registro[dia.month][dia.day]["suspension"]:
                computar = False

            if computar:
                # - calcular asistencia del día/alumno
                alumno_dia = asistencia_calcular(datos[e]["asistencia"][ordinal])

                # - sumar a total dia/mes y almacenar
                registro[dia.month][dia.day]["total"] += alumno_dia

                # - sumar a total mes/alumno y almacenar
                datos[e]["totales"][dia.month] += alumno_dia

                # - sumar a total inasistencias mes/alumno y almacenar
                datos[e]["totales_inasistencias"][dia.month] += 1 - alumno_dia
                
                # - sumar a total rango/alumno y almacenar
                datos[e]["total"] += alumno_dia

                # - sumar a total inasistencias rango/alumno y almacenar

                datos[e]["total_inasistencias"] += 1 - alumno_dia

                # - Sumar a totales por mes
                totales_por_mes[dia.month] += alumno_dia

                # - Sumar a totales inasistencias por mes
                totales_inasistencias_por_mes[dia.month] += 1 - alumno_dia

    # eliminar registros de asistencia fuera de fecha de inscripción o baja
    for item in datos_descarte:
        del(datos[item[0]]["asistencia"][item[1]])

    # recorrer registro calculando totales por mes
    for mes in registro:
        medias[mes] = asistencia_media(dias_normales[mes], totales_por_mes[mes])
        porcentajes[mes] = asistencia_porcentaje(totales_por_mes[mes], totales_inasistencias_por_mes[mes])

    return dict(materia_limites=materia_limites, grilla=grilla, horarios=horarios, suspensiones=suspensiones, query=qs, datos=datos, registro=registro, totales_por_mes=totales_por_mes, dias_normales = dias_normales, totales_inasistencias_por_mes = totales_inasistencias_por_mes, medias=medias, porcentajes=porcentajes, inscriptos=inscriptos, altas=altas, bajas=bajas)

