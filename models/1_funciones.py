# -*- coding: utf-8 -*-

__author__ = "Alan Edmundo Etkin <spametki@gmail.com>"
__copyright__ = "(C) 2024 Alan Edmundo Etkin. GNU GPL 3."

def normalizar_nombre(nombre):
    nombre_lista = [s.strip() for s in nombre.split(",")]
    if len(nombre_lista) > 1:
        apellidos, nombres = nombre_lista[0], nombre_lista[1]
        apellidos = [a.strip().lower().capitalize(
        ) for a in apellidos.split(" ")]
        nombres = [n.strip().lower().capitalize(
        ) for n in nombres.split(" ")]
        normalizado = ", ".join((" ".join(apellidos), " ".join(
        nombres)))
    else:
        normalizado = [n.strip().lower().capitalize(
        ) for n in nombre.split(" ")]
    return normalizado

def buscar_estudiante(db, nombre, documento):
    # Crear un listado de nombres no encontrados
    # al finalizar la carga y almacenarlo en session.avisos

    if not documento:
        q = db.estudiante.nombre == normalizar_nombre(nombre)
    else:
        # identificar por número de documento
        # para cualquier tipo
        # TODO: prevenir errores por mismo número
        # con distinto tipo de documento. parámetro tipo
        q = db.estudiante.documento_numero == documento

    estudiante = db(q).select(db.estudiante.id,
    db.estudiante.nombre).first()

    if estudiante is None:
        session.avisos.append(
        "Búsqueda de estudiante: no se encontró a %s \
        documento: %s en la BDD" % (nombre,
        documento or "N/A"))
        return None
    else:
        return estudiante.id

def estudiante_identificar(inscriptos, parametros):
    # devuelve el registro de estudiante
    # de mayor semejanza sin conocer el documento
    # y el coeficiente de semejanza

    if type(parametros) == tuple:
        nombre = ", ".join(parametros)
    else:
        nombre = parametros

    normalizado = normalizar_nombre(nombre)
    coeficientes = list()
    
    for registro in inscriptos:
        sm = difflib.SequenceMatcher(None, registro.nombre,
        normalizado)
        coeficientes.append(sm.quick_ratio())
    coeficiente = max(coeficientes)

    estudiante_id = inscriptos[coeficientes.index(coeficiente)].id
    inscripto_nombre = inscriptos[coeficientes.index(coeficiente)].nombre
    
    if coeficiente > APROXIMACION_ESTUDIANTE:
        session.aproximaciones[estudiante_id] = (normalizado, inscripto_nombre)
        return inscriptos[coeficientes.index(coeficiente)].id
    else:
        session.aproximaciones_excluidas[estudiante_id] = (normalizado, inscripto_nombre)
        return None

def convertir_a_time(cadena):
    hour=int(cadena.split(":")[0])
    minute=int(cadena.split(":")[1])
    t = datetime.time(hour=hour, minute=minute)
    return t

def convertir_a_datetime(cadena):
    try:
        return datetime.datetime.fromisoformat(cadena)
    except ValueError:
        cadena = "-".join((cadena[0:4], cadena[4:6], cadena[6:]))
        return datetime.datetime.fromisoformat(cadena)        

def calificar(calificacion):
    """ Resuelve la calificación
    según el criterio establecido.
    
    Completa automáticamente campos
    de la calificación si hay notas
    suficientes.
    
    Esta función se debe adecuar
    a la reglamentación de cada
    escuela """

    # TODO: agregar fecha de actualización

    promedio = None
    definitiva = None
    acredito = None
    promueve = None

    resultado = dict()

    if calificacion.cuatrimestre == 1:
        if calificacion.nota_03 is None:
            pass
        elif int(calificacion.nota_03) >= 6:
                promedio = calificacion.nota_03
                definitiva = calificacion.nota_03,
                acredito = True
                promueve = True
        else:
                promedio = calificacion.nota_03
                definitiva = calificacion.nota_03
                acredito = False
                promueve = False

    elif calificacion.cuatrimestre == 2:
        if calificacion.nota_06 is None:
            pass
        elif int(calificacion.nota_06) >= 6:
                promedio = calificacion.nota_06
                definitiva = calificacion.nota_06
                acredito = True
                promueve = True
        elif int(calificacion.nota_06) in (4, 5):
                promedio = calificacion.nota_06

                if (int(calificacion.nota_08) >= 4):
                    definitiva = calificacion.nota_08
                    acredito = True
                    promueve = True
                elif (int(calificacion.nota_09) >= 4):
                    definitiva = calificacion.nota_09
                    acredito = True
                    promueve = True
        else:
                promedio = calificacion.nota_06
                definitiva = calificacion.nota_06
                acredito = False
                promueve = False
    else:
        if calificacion.nota_06 is None:
            pass
        elif int(calificacion.nota_06) >= 6:
            promedio = calificacion.nota_06
            definitiva = calificacion.nota_06
            acredito = True
            promueve = True
        else:
            promedio = calificacion.nota_06
            if calificacion.nota_08 != None:
                if int(calificacion.nota_08) >= 4:
                    definitiva = calificacion.nota_08
                    acredito = True
                    promueve = True
                elif calificacion.nota_09 != None:
                    if int(calificacion.nota_09) >= 4:
                        definitiva = calificacion.nota_09
                        acredito = True
                        promueve = True

    if promedio != None:
        resultado["nota_07"] = promedio
    if definitiva != None:
        resultado["definitiva"] = definitiva
    if acredito != None:
        resultado["acredito"] = acredito
    if promueve != None:
        resultado["promueve"] = promueve

    return resultado


def estudiante_recuperar(db, estudiante_id):
    estudiante = db(db.estudiante.id == estudiante_id
    ).select().first()
    return estudiante

def plan_recuperar(db, estudiante_id):
    inscripcion = db(db.inscripcion.estudiante == estudiante_id).select().last()
    if not (inscripcion is None):
        try:
            nivel = int(inscripcion.nivel)
            division = int(inscripcion.division)
        except TypeError:
            if "planes" in session:
                if estudiante_id in session.planes:
                    return session.planes[estudiante_id]
            return None    
        return DIVISIONES_PLAN[nivel][division]
    else:
        raise HTTP(500, "No se encontró inscripción para el estudiante")

def notas_recuperar(db, estudiante_id, ciclo=None, plan=None):
    query = db.calificacion.estudiante == estudiante_id
    if ciclo:
        query &= db.calificacion.ciclo == ciclo
    if plan:
        query &= db.calificacion.titulo == plan
    notas = db(query).select(orderby=db.calificacion.id)
    return notas

def notas_actualizar(notas):
    for nota in notas:
        resultado = calificar(nota)
        if len(resultado) > 0:
            nota.update_record(**resultado)
    return notas

def cuatrimestre_determinar(fecha=None):
    # establece cuatrimestre
    if not fecha:
        fecha = datetime.datetime.today()
    if fecha.month == CUATRIMESTRE_CAMBIO[1]:
        if fecha.day < CUATRIMESTRE_CAMBIO[0]:
            cuatrimestre = 1
        else:
            cuatrimestre = 2
    elif fecha.month < CUATRIMESTRE_CAMBIO[1]:
        cuatrimestre = 1
    else:
        cuatrimestre = 2
    return cuatrimestre

def ciclo_determinar(fecha):
    cambio = datetime.date(fecha.year,
    CICLO_CAMBIO[1], CICLO_CAMBIO[0])
    # Si la fecha es igual o superior al cambio,
    # es el mismo ciclo que el año de la fecha
    if fecha >= cambio:
        return fecha.year
    # Si no, es el ciclo anterior
    else:
        return fecha.year -1

def trayecto_calcular(plan, notas):
    
    # lista de materias a cursar
    materias = dict()

    # recorrer cada nivel del plan de estudios
    for nivel in NIVELES:
        materias[nivel] = []
        #    recorrer cada materia del nivel
        for materia in PLAN[plan][nivel]:
            # ¿la aprobó o promovió?
            promueve = acredito = False
            for nota in notas:
                if int(nota["nivel"]) == nivel:
                    if nota["materia"] == ABREVIACIONES[
                    materia]:
                        if nota["promueve"]:
                            promueve = True
                        if nota["acredito"]:
                            acredito = True

            # si: no la debe cursar
            # no: la debe cursar
            if acredito or promueve:
                puedecursar = False
            else:
                # ¿la puede cursar?
                aprobadas = 0
                # si la materia no está en CORRELATIVIDADES,
                # la puede cursar (no tiene correlativas)
                if not materia in CORRELATIVIDADES[plan][nivel]:
                    puedecursar = True
                else:
                    if callable(CORRELATIVIDADES[plan][nivel][
                    materia]):
                        puedecursar = CORRELATIVIDADES[plan][nivel][
                        materia](nivel, notas)
                    else:
                        for t in CORRELATIVIDADES[plan][nivel][
                        materia]:
                            for nota in notas:
                                if (int(nota["nivel"]) == t[0]
                                ) and (nota["materia"] == \
                                ABREVIACIONES[PLAN[plan][t[0]][t[1]]]
                                ) and ((nota["promueve"] == True
                                ) or (nota["acredito"] == True)):
                                    aprobadas += 1
                                    if nota["acredito"] != True:
                                        # TODO: informar que
                                        # cursa sin acreditar
                                        pass
                        # si: agregar a lista
                        if aprobadas >= len(CORRELATIVIDADES[plan][
                        nivel][materia]):
                            puedecursar = True
                        else:
                            puedecursar = False

            if not (promueve or acredito):
                if puedecursar or (nivel == NIVELES[0]):
                    materias[nivel].append(ABREVIACIONES[
                    materia])
    return materias

def horarios_grilla(db, fecha, turno, nivel, division,
                    estudiante_id = None, suspension = False):

    # TODO: soporte para mútiples turnos
    # TODO: calcular ciclo y cuatrimestre

    ciclo = ciclo_determinar(fecha)
    cuatrimestre = cuatrimestre_determinar(fecha)
    plan = DIVISIONES_PLAN[int(nivel)][int(division)]
    
    if estudiante_id != None:
        # caso 1) obtener todas las asignaturas
        # en las que curse la/el estudiante
        
        notas = notas_recuperar(estudiante_id, ciclo = ciclo)

        asignaturas = list()

        # recuperar asignaturas por cada nota
        for nota in notas:
            filtrar = True
            if (nota.promocion in (None,
            *PROMOCIONES_PRESENCIALES)):
                if nota.cuatrimestre != None:
                    if nota.cuatrimestre == cuatrimestre:
                        filtrar = False
                else:
                    filtrar = False
            if not filtrar:
                query = db.asignatura.materia == nota.materia
                query &= db.asignatura.nivel == nota.nivel
                query &= db.asignatura.titulo == nota.titulo
                if nota.cuatrimestre != None:
                    query &= db.asignatura.cuatrimestre == \
                    cuatrimestre
                if nota.division != None:
                    query &= db.asignatura.division == \
                    nota.division
                if nota.comision != None:
                    query &= db.asignatura.comision == \
                    nota.comision
                if nota.turno != None:
                    query &= db.asignatura.turno == nota.turno
                    
                asignatura = db(query).select().first()
                
                if asignatura != None: asignaturas.append(
                asignatura)
                
        # recuperar espacios comunes que no tienen nota
        query = db.asignatura.turno == turno
        query &= db.asignatura.nivel == nivel
        query &= db.asignatura.division == division
        query &= db.asignatura.titulo == plan
        
        query &= db.asignatura.materia.belongs(
        ESPACIOS_COMUNES)
        asignaturas_comunes = db(query).select()
        if asignaturas_comunes != None:
            for asignatura in asignaturas_comunes:
                asignaturas.append(asignatura)

    else:
        # caso 2) obtener todas las asignaturas
        # según turno, nivel y división
        query = db.asignatura.turno == turno
        query &= db.asignatura.nivel == nivel
        query &= db.asignatura.division == division
        query &= db.asignatura.titulo == plan

        # para ordenar por hora en .select()
        # ejemplo: orderby=db.asignatura.lunes 
        asignaturas = db(query).select()

    asignaturas_ids = [row.id for row in asignaturas]
    
    qd = db.designacion.asignatura.belongs(asignaturas_ids)
    qd &= db.designacion.baja == None
    designaciones = db(qd).select()

    docentes_ids = [row.docente for row in designaciones]

    docentes = db(db.docente.id.belongs(
                  docentes_ids)).select()

    docentes_dict = dict()
    for d in docentes:
        docentes_dict[d.id] = d.nombre

    # establecer primer dia de la semana y convertir
    # a objetos datetime
    
    diferencia_fecha = datetime.timedelta(
    days=fecha.weekday())
    diferencia_viernes = datetime.timedelta(days=4)
    
    fecha_lunes = fecha - diferencia_fecha
    fecha_viernes = fecha_lunes + diferencia_viernes
    
    fecha_lunes_dia = datetime.datetime(fecha_lunes.year,
                                    fecha_lunes.month,
                                    fecha_lunes.day)
    fecha_viernes_dia = datetime.datetime(fecha_viernes.year,
                                      fecha_viernes.month,
                                      fecha_viernes.day,
                                      23,
                                      59)

    # armar una grilla por turno con horarios y docentes
    horarios_semana = dict()
    horas_cubiertas = dict()
    for t in TURNOS:
        horarios_semana[t] = [[dict(
                             espacio="",
                             nivel="",
                             docentes=[],
                             docentes_ids=[],
                             comisiones={},
                             comisiones_ausentes={},
                             suspension=False,
                             motivo="",
                             desde=None,
                             ausentes=0,                              
                             hasta=None
                             ) for x in HORARIOS[t]
                             ] for x in range(len(DIAS))]
        horas_cubiertas[t] = 0
                       
    for t in horarios_semana:
        contador_dias = 0
        incremento_un_dia = datetime.timedelta(days=1)
        dia_pythonico = fecha_lunes_dia
    
        for dia in horarios_semana[t]:
            contador_dias += 1
            contador_horas = 0
        
            for hora in dia:
                contador_horas += 1
            
                # establecer rango horario
                hora_inicio = convertir_a_time(
                    HORARIOS[t][contador_horas -1][0])
                hora_finalizacion = convertir_a_time(
                    HORARIOS[t][contador_horas -1][1])
                hora["desde"] = datetime.datetime(
                dia_pythonico.year,
                dia_pythonico.month,
                dia_pythonico.day,
                hora_inicio.hour,
                hora_inicio.minute)
                                
                hora["hasta"] = datetime.datetime(
                dia_pythonico.year, dia_pythonico.month,
                dia_pythonico.day, hora_finalizacion.hour,
                hora_finalizacion.minute)

                # agregar nombre de materia y docentes          
                for asignatura in asignaturas:
                    if (contador_horas in asignatura[
                    DIAS[contador_dias -1]]) and (
                        ((not asignatura.contraturno
                        ) and (turno == t)) or (
                        asignatura.contraturno == t)):
                        horas_cubiertas[t] += 1
                        hora["espacio"] = asignatura.materia
                        hora["nivel"] = asignatura.nivel
                    
                        for d in designaciones:
                            if d.asignatura == asignatura.id:
                                hora["docentes"].append(
                                docentes_dict[d.docente])
                                hora["docentes_ids"].append(
                                d.docente)
                            
                                if not (asignatura.comision is None):
                                    if not (
                                    asignatura.comision in hora[
                                    "comisiones"]):
                                        hora["comisiones"][
                                        asignatura.comision] = list()
                                        hora["comisiones_ausentes"][
                                        asignatura.comision] = 0

                                    hora["comisiones"][
                                    asignatura.comision].append(
                                    d.docente)

            dia_pythonico += incremento_un_dia

    # Eliminar turnos que no contienen horas de clase
    for t in horas_cubiertas:
        if horas_cubiertas[t] == 0:
            del horarios_semana[t]

    if suspension:
        # obtener todos ausentes y suspensiones de
        # actividad de la semana
    
        ausentes = db((
        db.docente_ausencia.desde <= fecha_viernes_dia
        ) & (
        db.docente_ausencia.hasta >= fecha_lunes_dia)).select()

        suspensiones_actividad = db(
        ((db.suspension_actividad.turno.belongs(TURNOS)) |
        (db.suspension_actividad.turno == None)) &
        ((db.suspension_actividad.nivel == nivel) |
        (db.suspension_actividad.nivel == None)) &
        ((db.suspension_actividad.division == division) |
        (db.suspension_actividad.division == None)) &
        (db.suspension_actividad.desde <= fecha_viernes_dia) &
        (db.suspension_actividad.hasta >= fecha_lunes_dia)
        ).select()

        # para cada suspensión:
        # recorrer cada hora de clase y establecer si está 
        # comprendida
        # caso que esté, agregar información a dictionary
        for t in horarios_semana:
            for sa in suspensiones_actividad:
                for dia in horarios_semana[t]:
                    for hora in dia:
                        if sa.desde <= hora["desde"] and \
                        sa.hasta >= hora["hasta"]:
                            hora["suspension"] = True
                            hora["motivo"] = sa.motivo

        # para cada ausente:
        # recorrer cada hora de clase y establecer si está
        # comprendida
        # caso que esté, agregar información a dictionary

        for t in horarios_semana:
            for a in ausentes:
                for dia in horarios_semana[t]:
                    for hora in dia:
                        if (a.docente in hora["docentes_ids"]) and \
                        (a.desde <= hora["desde"]) and \
                        (a.hasta >= hora["hasta"]):
                            if len(hora["comisiones"]) <= 0:
                                hora["ausentes"] += 1
                                if hora["ausentes"] >= len(hora[
                                "docentes"]):
                                    hora["suspension"] = True
                                    hora["motivo"] = a.motivo
                            else:
                                # caso de varias comisiones para
                                # la misma materia
                                for k in hora["comisiones"]:
                                    if a.docente in hora[
                                    "comisiones"][k]:
                                        hora["comisiones_ausentes"][
                                        k] += 1
                                        if hora["comisiones_ausentes"
                                        ][k] >= len(hora[
                                        "comisiones"][k]):
                                            hora["suspension"] = True
                                            if hora["motivo"] == "":
                                                hora["motivo"] = \
                                                "Comisión " + \
                                                k + " sin docentes"
                                            else:
                                                hora["motivo"] += \
                                                "; Comisión " + k + \
                                                " sin docentes"
    return horarios_semana


def divisiones_por_nivel(nivel, division):
    # según nivel y división
    # recupera la secuencia de divisiones
    # por nivel

    divisiones = None
   
    if not (None in (nivel, division)):
        for t in DIVISIONES_SECUENCIA:
            contador = 0
            for d in t:
                contador += 1
                if (contador == nivel) and (d == division):
                    return t
    return divisiones
    
def materia_abreviar(materia):
    for a in ABREVIACIONES:
        if ABREVIACIONES[a] == materia:
            return a
    return None
    
def correlativasdys(nivel, notas):
    contador = 0
    for nota in notas:
        if (int(nota["nivel"]) == 1) and (True in (nota["promueve"],
        nota["acredito"])) and (not (nota["materia"] in ("Inglés",
        "Informática"))):
            contador += 1
    if contador >= 2:
        return True
    else:
        return False

def correlativasproy(nivel, notas):
    contador = 0
    for nota in notas:
        if (int(nota["nivel"]) in (1, 2)) and (True in (
        nota["promueve"], nota["acredito"])) and (
        not (nota["materia"] in ("Inglés", "Informática"))):
            contador += 1
    if contador >= 9:
        return True
    else:
        return False

def correlativasmedia(plan, nivel, notas):
    # para educación media
    # sin trayectos de reingreso
    anteriores = len(PLAN[plan](nivel))
    acreditadas = 0
    if int(nivel) > 1:
        for nota in notas:
            if nota["acredito"] == True:
                acreditadas += 1
        if acreditadas >= anteriores -2:
            return True
        else:
            return False
    else:
        return True
    
def notas_conversores_estudiante(t):
    documento = None
    if "," in t[0]:
        nombre = t[0]
    else:
        nombre = ", ".join(t)
    if t[1].strip().isnumeric():
        documento = t[1].strip()
    estudiante_id = buscar_estudiante(nombre, documento)
    return estudiante_id

def cuatrimestres_listar(inicial, final):
    # Establece qué cuatrimestres están
    # comprendidos. Devuelve una tupla
    # ((ciclo, número), ...)
    
    l = list()
    
    cambio_ciclo = datetime.date(inicial.year, CICLO_CAMBIO[1], CICLO_CAMBIO[0])
    cambio_cuatrimestre = datetime.date(inicial.year, CUATRIMESTRE_CAMBIO[1],
     CUATRIMESTRE_CAMBIO[0])

    ciclos = final.year - inicial.year +1
    
    ciclo = inicial.year
    
    if cambio_ciclo > inicial:
        l.append((ciclo -1, 2))

    for c in range(ciclos):
        if final > cambio_ciclo:
            l.append((ciclo, 1))
        if final > cambio_cuatrimestre:
            l.append((ciclo, 2))
        ciclo += 1
        cambio_ciclo = datetime.date(ciclo, CICLO_CAMBIO[1], CICLO_CAMBIO[0])
        cambio_cuatrimestre = datetime.date(ciclo, CUATRIMESTRE_CAMBIO[1], CUATRIMESTRE_CAMBIO[0])
    return l

def horas_a_time(horario):
    # devuelve HORAS convirtiendo
    # a objetos datetime.time
    obj = dict()
    for turno in horario:
        obj[turno] = list()
        for hora in horario[turno]:
            inicio = hora[0].split(":")
            fin = hora[1].split(":")
            obj[turno].append((
                datetime.time(int(inicio[0]), int(inicio[1])),
                datetime.time(int(fin[0]), int(fin[1]))))
    return obj

def asistencia_calcular(par):
    # el primer elemento es turno
    # el segundo elemento contraturno
    
    multiplicador = 0
    
    # ningún turno?
    if (par[0] in (None, "n/a")) and (par[1] in (None, "n/a")):
        multiplicador = 0

    # ambos turnos
    elif (not (par[0] in (None, "n/a"))) and (not (par[1] in (None, "n/a"))):
        multiplicador = 0.5
    # un turno
    else:
        multiplicador = 1
    
    total = 0
    for elemento in par:
        if not (elemento in (None, "n/a")):
            total += ASISTENCIA_VALORES[elemento][0]
    return multiplicador*total

def asistencia_porcentaje(asistencias, inasistencias):
    # porcentaje de asistencia en relación con inasistencias
    # se multiplica por 100 la asistencia y se divide por la
    # suma de asistencias e inasistencias
    if asistencias + inasistencias == 0:
        return "n/a"
    else:
        return round(asistencias*100/(asistencias + inasistencias), 2)
    
def asistencia_media(dias, asistencias):
    # cuántos alumnos por día en n días
    if dias == 0:
        return "n/a"
    else:
        return round(asistencias/dias)

def asistencia_alumno(db, estudiante, desde, hasta):
    # Devuelve las asistencias e inasistencias
    # en un período determinado por alumno    
    # asistencias -> "total"
    # inasistencias -> "total_inasistencias"    
    
    # Argumentos:
    # 0: un objeto Row de join de tablas inscripcion y estudiante
    # 1: date
    # 2: date

    # - Almacenar dias de clase sin suspensión por mes para
    # cálculo de inasistencias

    dias_normales = dict()
    fechas = dict()
    registro = dict()
    totales_por_mes = dict()
    totales_inasistencias_por_mes = dict()
        
    # TODO: Agrupar objetos y optimizar bucles
    
    # - Calcular y mostrar promedio y asistencia media por mes
    
    # En formato weekday
    diasdeclase = [DIAS_PYTHON[dia] for dia in DIAS]

    # 1) Establecer fechas límite por datos
    # del formulario

    ciclo = estudiante.inscripcion.ciclo
    turno = estudiante.inscripcion.turno
    nivel = estudiante.inscripcion.nivel
    division = estudiante.inscripcion.division    
    alta = estudiante.inscripcion.fecha
    baja = estudiante.inscripcion.baja_fecha

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
    
    datos = dict(nombre=estudiante.estudiante.nombre,
                 documento="%s %s" % (estudiante.estudiante.documento_tipo or "",
                                      estudiante.estudiante.documento_numero),
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
                    if e == estudiante.estudiante.id:
                        # se encontró un registro
                        # de asistencia del curso
                        
                        if not (ordinal in datos["asistencia"]):
                            datos["asistencia"][ordinal] = (None, None)

                        # completar asistencia por estudiante
                        # si hubo suspensión no se computa al inasistencia
                        
                        if parteturno == parte.turno:
                            # igual turno
                            if parteturno in grilla[ordinal]:
                                t = None
                            else:
                                t = categorias[k]
                            ct = datos["asistencia"][ordinal][1]
                        else:
                            # contraturno                            
                            if parteturno in grilla[ordinal]:
                                ct = None
                            else:
                                ct = categorias[k]
                            t = datos["asistencia"][ordinal][0]

                        datos["asistencia"][ordinal] = (t, ct)
        
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
    
    for ordinal in datos["asistencia"]:
        dia = fechas[ordinal]
        computar = False
        descartar = False

        if (alta is None) or (alta <= dia):
            computar = True

            if not (baja is None):
                if baja <= dia:
                    computar = False
                    descartar = True
        else:
            descartar = True

        if descartar:
            # preparar el item para eliminar
            # al finalizar el bucle
            datos_descarte.append(ordinal)

        if not dia.month in totales_por_mes:
            totales_por_mes[dia.month] = 0

        if not dia.month in totales_inasistencias_por_mes:
            totales_inasistencias_por_mes[dia.month] = 0

        if not dia.month in datos["totales"]:
            datos["totales"][dia.month] = 0

        if not dia.month in datos["totales_inasistencias"]:
            datos["totales_inasistencias"][dia.month] = 0

        if not "total" in registro[dia.month][dia.day]:
            registro[dia.month][dia.day]["total"] = 0

        if registro[dia.month][dia.day]["suspension"]:
            computar = False
        
        if computar:
            # - calcular asistencia del día/alumno
            alumno_dia = asistencia_calcular(datos["asistencia"][ordinal])

            # - sumar a total dia/mes y almacenar
            registro[dia.month][dia.day]["total"] += alumno_dia

            # - sumar a total mes/alumno y almacenar
            datos["totales"][dia.month] += alumno_dia

            # - sumar a total inasistencias mes/alumno y almacenar
            datos["totales_inasistencias"][dia.month] += 1 - alumno_dia
                
            # - sumar a total rango/alumno y almacenar
            datos["total"] += alumno_dia

            # - sumar a total inasistencias rango/alumno y almacenar
            datos["total_inasistencias"] += 1 - alumno_dia

            # - Sumar a totales por mes
            totales_por_mes[dia.month] += alumno_dia

            # - Sumar a totales inasistencias por mes
            totales_inasistencias_por_mes[dia.month] += 1 - alumno_dia

    # eliminar registros de asistencia fuera de fecha de inscripción o baja
    for ordinal in datos_descarte:
        del(datos["asistencia"][ordinal])

    # recorrer registro calculando totales por mes
    for mes in registro:
        if not mes in totales_por_mes:
            totales_por_mes[mes] = 0
            totales_inasistencias_por_mes[mes] = 0
            
    return datos["total"], datos["total_inasistencias"]


def asistenciamateria_alumno(db, asignatura, calificacion, estudiante, desde, hasta):
    # Devuelve las asistencias e inasistencias
    # asistencias -> "total"
    # inasistencias -> "total_inasistencias"
    # en un período determinado por alumno

    # TODO: error en bucle de registro al sumar un parte
    # al contador; no existe el elemento en el diccionario

    # Argumentos:
    # 0: row db.asignatura
    # 1: row db.calificacion
    # 2: row join db.estudiante y db.inscripcion
    # 3: date
    # 4: date
    
    # Asistencia por materia
    # Indicar altas y bajas por mes con
    # n alumnos el primer día y n alumnos el último
    # - Almacenar total asistencia por mes para mostrar
    # en las tablas.
    
    totales_por_mes = dict()
    totales_inasistencias_por_mes = dict()
    inscriptos = dict()
    altas = dict()

    # - Almacenar dias de clase sin suspensión por mes para
    # cálculo de inasistencias

    dias_normales = dict()
    asignatura_horas = dict()
    
    # TODO: Agrupar objetos y optimizar bucles
    # - Cálcular y mostrar promedio y asistencia media por mes
    
    # En formato weekday
    diasdeclase = [DIAS_PYTHON[dia] for dia in DIAS]

    # mapea ordinal con date
    fechas = dict()    

    # objeto para almacenar registro
    registro = dict()

    # legibilidad de variables
    ciclo = estudiante.inscripcion.ciclo
    turno = estudiante.inscripcion.turno
    nivel = estudiante.inscripcion.nivel
    division = estudiante.inscripcion.division
    materia = asignatura.materia
    comision = asignatura.comision
    contraturno = asignatura.contraturno

    # -1) Obtener horarios de la materia en la BDD

    for dia in DIAS:
        if not (asignatura[dia] is None):
            if type(asignatura[dia]) is int:
                asignatura_horas[DIAS_PYTHON[dia]] = set((asignatura[dia],))
            elif len(asignatura[dia]) == 0:
                pass
            else:
                asignatura_horas[DIAS_PYTHON[dia]] = set(asignatura[dia])

    asignatura_turno = None

    if asignatura.contraturno is None:
        asignatura_turno = asignatura.turno
    else:
        asignatura_turno = asignatura.contraturno
    
    # 1) Establecer fechas límite por datos
    # del formulario

    estudiante_id = estudiante.estudiante.id
    
    # alta y baja de materia se consulta
    # en registro de calificación
    
    estudiante_alta = calificacion.alta_fecha
    estudiante_baja = calificacion.baja_fecha

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
        materia_limites[dia] = (horarios[criterio_turno][dia_horas[0]-1][0],
                                horarios[criterio_turno][dia_horas[-1]-1][-1])

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

    # datos es un objeto dict
    # con dias de cursada del estudiante
    
    datos = dict(nombre=estudiante.estudiante.nombre,
                 documento="%s %s" % (
                 estudiante.estudiante.documento_tipo \
                 or "",
                 estudiante.estudiante.documento_numero),
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
        
        if (parte.fecha.weekday() in asignatura_horas):
            ordinal = parte.fecha.toordinal()
            registro[parte.fecha.month][parte.fecha.day]["partes"] += 1
        
            if parte.contraturno is None:
                registro[parte.fecha.month][parte.fecha.day]["turnos"] += (parte.turno,)
            else:
                registro[parte.fecha.month][parte.fecha.day]["turnos"] += (parte.contraturno,)

            for k in categorias:
                if type(parte[k]) is list:
                    if estudiante_id in parte[k]:
                        # se encontró un registro
                        # de asistencia del curso
                        if asignatura_turno in grilla[ordinal]:
                            datos["asistencia"][ordinal] = (None, None)
                        else:
                            datos["asistencia"][ordinal] = (categorias[k], None)

    # Agrupar días por mes indicando subtotales
    # por renglón. Contemplar contraturno y
    # dividir por dos las inasistencias en caso
    # de dos partes por día.
    # Utilizar conjunto de variables que especifiquen
    # cómo se computa tarde y ausente en turno simple
    # y doble.

    for ordinal, dia in fechas.items():
        turnos_suspendidos = 0
        if (dia.weekday() in asignatura_horas):
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

    # agregar información de alta y baja por mes
    alta = estudiante_alta
    baja = estudiante_baja

    if not (alta is None):
        if desde <= alta <= hasta:
            if not alta.month in altas:
                altas[alta.month] = set()
            altas[alta.month].add(estudiante_id)

    if not (baja is None):
        if desde <= baja <= hasta:
            if not baja.month in bajas:
                bajas[baja.month] = set()
            bajas[baja.month].add(estudiante_id)
    
    for ordinal in datos["asistencia"]:
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
            datos_descarte.append(ordinal)

        if not dia.month in totales_por_mes:
            totales_por_mes[dia.month] = 0

        if not dia.month in totales_inasistencias_por_mes:
            totales_inasistencias_por_mes[dia.month] = 0

        if not dia.month in datos["totales"]:
            datos["totales"][dia.month] = 0

        if not dia.month in datos["totales_inasistencias"]:
            datos["totales_inasistencias"][dia.month] = 0

        if not "total" in registro[dia.month][dia.day]:
            registro[dia.month][dia.day]["total"] = 0

        if registro[dia.month][dia.day]["suspension"]:
            computar = False

        if computar:
            # - calcular asistencia del día/alumno
            alumno_dia = asistencia_calcular(datos["asistencia"][ordinal])

            # - sumar a total dia/mes y almacenar
            registro[dia.month][dia.day]["total"] += alumno_dia

            # - sumar a total mes/alumno y almacenar
            datos["totales"][dia.month] += alumno_dia

            # - sumar a total inasistencias mes/alumno y almacenar
            datos["totales_inasistencias"][dia.month] += 1 - alumno_dia
               
            # - sumar a total rango/alumno y almacenar
            datos["total"] += alumno_dia

            # - sumar a total inasistencias rango/alumno y almacenar

            datos["total_inasistencias"] += 1 - alumno_dia

            # - Sumar a totales por mes
            totales_por_mes[dia.month] += alumno_dia

            # - Sumar a totales inasistencias por mes
            totales_inasistencias_por_mes[dia.month] += 1 - alumno_dia

    # eliminar registros de asistencia fuera de fecha de inscripción o baja
    for item in datos_descarte:
        del(datos["asistencia"][item])

    return datos["total"], datos["total_inasistencias"]

def previas_establecer(db, alumno, plan, boletin):

    # - implementar control de previas:
    # se puede reutilizar el código de la action pendientes.
    # TODO: implementar algoritmo que aplique
    # automáticamente la condición de previa
    # Ej. Si previas_mostrar es True y la materia
    # se cursó y no se aprobó y no es parte de la
    # cursada actual, entonces es previa.

    # TODO: Ver algoritmo de eliminacion de aprobadas
    # Función ad hoc para cálculo de previas
    # para secundarias no reingreso
    
    # argumentos: 0 alumno (join estudiante e inscripcion)
    # 1: boletin (instancia de notas)
    # resultado: dict donde las claves son los niveles y
    # los valores tuplas de materias

    # En reingreso no existen las previas.
    # return None
    
    # Algoritmo de ejemplo técnica:
    # a) recuperar ciclo de inscripción
    ciclo = alumno.inscripcion.ciclo
    
    # b) recuperar nivel de inscripcion
    nivel = alumno.inscripcion.nivel
    
    # c) si el nivel es 1 salir con resultado None
    if nivel == 1:
        return None

    # previas almacena el resultado
    # por defecto todas la materias del plan
    # son previa
    previas = dict()
    for n in NIVELES:
        if n < nivel:
            previas[n] = list()
            for materia in PLAN[plan][n]:
                previas[n].append(ABREVIACIONES[materia])
        else:
            break

    # d) recuperar todas las calificaciones del alumno
    # con fecha igual o menor que fecha de boletín
    
    # establecer fecha del boletin
    boletin_fecha = datetime.date(ciclo + BOLETINES_PLAZOS[boletin][2], BOLETINES_PLAZOS[boletin][1], BOLETINES_PLAZOS[boletin][0])

    qc = db.calificacion.estudiante == alumno.estudiante.id
    qc &= db.calificacion.titulo == plan
    qc &= db.calificacion.alta_fecha <= boletin_fecha
    qc &= db.calificacion.nivel < nivel
    calificaciones = db(qc).select()
    
    # d) recorrer calificaciones
    #    - por cada calificacion registrar si es aprobada,
    #        en P.A. o P.E.P. (en estos dos casos no es
    #        previa)

    for calificacion in calificaciones:
        # Materias 2020 P.E.P. por resolución del Ministerio;
        # no es previa.

        if calificacion.acredito or (calificacion.ciclo == 2020):
            # Si la materia corresponde al mismo ciclo
            # tampoco es previa
            previas[calificacion.nivel].remove(calificacion.materia)
    
    # e) devolver un listado por nivel con las previas
    return previas

def plan_establecer(row):
    """ Para el campo calculado "titulo"
    en las tablas asignatura y calificación
    """
    if (type(row.nivel) in (str, int)) and (type(row.division) in (str, int)):
        if row.nivel.isdigit() and row.division.isdigit():
            nivel = int(row.nivel)
            division = int(row.division)
            return DIVISIONES_PLAN[nivel][division]
        else:
            return None
    else:
        return None

def plan_comprobar(form):
    # Comprueba que coincida el plan
    # del nivel seleccionado con el
    # que se configuró para la inscripción
    try:
        estudiante = int(form.vars.estudiante)
        nivel = int(form.vars.nivel)
        division = int(form.vars.division)
    except TypeError:
        form.errors.division = "Seleccione nivel y división"
        return

    if "planes" in session:
        if estudiante in session.planes:
            configurado = session.planes[estudiante]
            seleccionado = DIVISIONES_PLAN[nivel][division]
            if not (configurado == seleccionado):
                form.errors.division = "La división corresponde a %s pero el plan seleccionado es %s" % (PLAN_ABREVIACIONES[seleccionado], PLAN_ABREVIACIONES[configurado])
        else:
            form.errors.division = "No se configuró un plan"
    else:
        form.errors.division = "No se configuró un plan"

def plan_actualizar(form):
    # Actualiza el plan seleccionado (sin referencia
    # a un alumno) en session al aceptar un formulario
    # con nivel y división
    try:
        nivel = int(form.vars.nivel)
        division = int(form.vars.division)
        session.plan = DIVISIONES_PLAN[nivel][division]
    except (TypeError, KeyError, AttributeError):
        return

def titulo_mostrar_actualizar():
    # Recupera el plan (sin referencia
    # a un alumno) en session y devuelve
    # una etiqueta con el plan para mostrar
    # en las vistas
    if "plan" in session:
        if session.plan is None:
            texto = "sin datos"
        else:
            texto = PLAN_ABREVIACIONES[int(session.plan)]
    else:
        texto = "sin datos"
    TITULO_MOSTRAR[0] = "Plan: %s" % texto
