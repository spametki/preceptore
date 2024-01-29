# -*- coding: utf-8 -*-

__author__ = "Alan Edmundo Etkin <spametki@gmail.com>"
__copyright__ = "(C) 2024 Alan Edmundo Etkin. GNU GPL 3."

import datetime
import os

@auth.requires_membership('administradores')
def cargaregistro():
    # formulario
    # campos:
    #    - ciclo
    #    - turno
    #    - nivel
    #    - division
    #    - subir archivo CSV

    # el CSV debe adecuarse a
    # campos de tabla

    # crear objeto que almacene los datos a registrar
    # para las tablas estudiante e inscripcion

    estudiantes = list()
    inscripciones = list()
    filtro = None
    enviado = False

    form = SQLFORM.factory(Field("ciclo", "integer",
                           requires = IS_IN_SET(CICLOS)),
                           Field("turno",
                           requires = IS_IN_SET(TURNOS)),
                           Field("nivel", "integer",
                           requires = IS_IN_SET(NIVELES)),
                           Field("division",
                           requires = IS_IN_SET(DIVISIONES)),
                           Field("inscribir", "boolean",
                           default=False),
                           Field("archivo", "upload",
                           requires = IS_NOT_EMPTY()))

    if form.process().accepted:
        enviado = True
        # datos en form.vars
        # por ejemplo ubicacion del archivo:
        # form.vars.archivo (sin ruta a directorio)
        # directorio: [request.folder]/uploads/

        # abrir el archivo especificado para lectura

        with open(os.path.join(request.folder,
                               "uploads", 
                               form.vars.archivo),
                               newline='',
                               encoding=CSV_CODIFICACION) \
                               as archivo:
            lector = csv.reader(archivo,
                                delimiter=CSV_DELIMITADOR,
                                quotechar=CSV_COMILLAS)

            # recorrer líneas haciendo las conversiones por tipo
            # de dato y almacenando cada línea en el objeto para
            # registro
            
            lineas = 0
            for linea in lector:
                lineas += 1
                if lineas >= REGISTRO_PARAMETROS[
                "primera_linea"]:
                    if linea[ALFABETO.index(
                    REGISTRO_PARAMETROS[
                    "columna_verificacion"])] == "":
                        break
                    d = {}
                    for f in db.estudiante.fields:
                        if f in REGISTRO_PARAMETROS:
                            if f in REGISTRO_CONVERSORES:
                                if type(
                                REGISTRO_PARAMETROS[f]) == tuple:
                                    parametros = []
                                    for e in \
                                    REGISTRO_PARAMETROS[f]:
                                        parametros.append(linea[
                                        ALFABETO.index(e)])
                                    d[f] = REGISTRO_CONVERSORES[
                                    f](parametros)
                                else:
                                    d[f] = REGISTRO_CONVERSORES[
                                    f](linea[
                                    ALFABETO.index(
                                    REGISTRO_PARAMETROS[f])]
                                    )
                            else:
                                d[f] = linea[ALFABETO.index(
                                REGISTRO_PARAMETROS[f])]
                    estudiantes.append(d)
            
        # filtrar tipo y número de documento redundante previo
        # a actualización de BDD

        dnies = [d["documento_numero"] for d in estudiantes]
        nombres = [d["nombre"] for d in estudiantes]

        filtro = db(db.estudiante.documento_numero.belongs(
        dnies) & db.estudiante.nombre.belongs(nombres)).select(
        db.estudiante.id, db.estudiante.documento_numero,
        db.estudiante.nombre)

        # Aplicar cambios a la base de datos creando los
        # registros de la tabla estudiante
        
        # Crear inscripciones para el año en curso
        # en caso de opción inscribir
        
        # Mostrar datos almacenados
                
        for estudiante in filtro:
            contador = 0
            for e in estudiantes:
                if (estudiante.nombre == e["nombre"]
                ) and (estudiante.documento_numero == str(
                e["documento_numero"])):
                    e2 = estudiantes.pop(contador)
                    db(db.estudiante.id == estudiante.id
                    ).update(**e2)
                    if form.vars.inscribir == True:
                        inscripcion_id = db.inscripcion.insert(
                                      estudiante=estudiante.id,
                                      ciclo=form.vars.ciclo,
                                      turno=form.vars.turno,
                                      nivel=form.vars.nivel,
                                      division=form.vars.division,
                                      baja=False)
                        e2["inscripcion"] = inscripcion_id
                        inscripciones.append(e2)
                contador += 1
                
        for estudiante in estudiantes:
            estudiante_id = db.estudiante.insert(**estudiante)
            if form.vars.inscribir == True:
                inscripcion_id = db.inscripcion.insert(
                                      estudiante=estudiante_id,
                                      ciclo=form.vars.ciclo,
                                      turno=form.vars.turno,
                                      nivel=form.vars.nivel,
                                      division=form.vars.division,
                                      baja=False)
                estudiante["inscripcion"] = inscripcion_id
                inscripciones.append(estudiante)

    return dict(form = form, estudiantes = estudiantes, 
    inscripciones = inscripciones, enviado = enviado)


@auth.requires_membership('administradores')
def carganotas():
    # formulario
    # campos:
    #    - ciclo
    #    - turno
    #    - nivel
    #    - division
    #    - comision
    #    - docente
    #    - subir archivo CSV

    # el CSV debe adecuarse a
    # campos de tabla

    # crear objeto que almacene las notas

    # Se puede agregar una columna para buscar alumno por
    # número de documento. Configurar campos en NOTAS_PARAMETROS

    session.notas = list()
    session.notas_excluidas = list()
    session.aproximaciones = dict()
    session.aproximaciones_excluidas = dict()
    session.aproximaciones_aceptados = list()
    session.aproximaciones_rechazados = list()
    session.notas_datos = dict()
    
    form = SQLFORM.factory(Field("ciclo", "integer",
                           requires = IS_IN_SET(CICLOS)),
                           Field("turno",
                           requires = IS_IN_SET(TURNOS)),
                           Field("cuatrimestre", "integer",
                           requires=IS_EMPTY_OR(IS_IN_SET(
                           CUATRIMESTRES))),
                           Field("nivel", "integer",
                           requires = IS_IN_SET(NIVELES)),
                           Field("division",
                           requires = IS_EMPTY_OR(IS_IN_SET(
                           DIVISIONES))),
                           Field("plan",
                           requires = IS_IN_SET(
                           PLAN_ABREVIACIONES)),
                           Field("materia",
                           requires=IS_IN_SET(MATERIAS)),
                           Field("comision", 
                           requires=IS_EMPTY_OR(IS_IN_SET(
                           COMISIONES))),
                           Field("docente", requires=IS_IN_DB(db,
                           "docente.id", "%(nombre)s")),
                           Field("aproximar", "boolean",
                           default=True,
                           comment="Nombres de estudiantes \
                           aproximados"),
                           Field("archivo", "upload",
                           requires = IS_NOT_EMPTY()))


    if form.process().accepted:
        session.notas_datos = form.vars
        # datos en form.vars
        # por ejemplo ubicacion del archivo:
        # form.vars.archivo (sin ruta a directorio)
        # directorio: [request.folder]/uploads/

        # abrir el archivo especificado para lectura

        # NOTA: las planillas deben tener cargados los
        # nombres iguales que en el registro. La carga
        # automatizada omite los nombres que no coinciden
        # exactamente
        
        with open(os.path.join(request.folder,
                               "uploads", 
                               form.vars.archivo),
                               newline='',
                               encoding=CSV_CODIFICACION) \
                               as archivo:
            lector = csv.reader(archivo,
                                delimiter=CSV_DELIMITADOR,
                                quotechar=CSV_COMILLAS)

            # obtener todos los estudiantes
            # del ciclo correspondiente
            if form.vars.aproximar:
                query = db.estudiante.id == \
                db.inscripcion.estudiante
                query &= db.inscripcion.ciclo == \
                form.vars.ciclo
                inscriptos = db(query).select(
                db.estudiante.id, db.estudiante.nombre)

            # recorrer líneas haciendo las conversiones por tipo
            # de dato y almacenando cada línea en el objeto para
            # registro
            
            lineas = 0
            for linea in lector:
                lineas += 1
                if lineas >= NOTAS_PARAMETROS[
                "primera_linea"]:
                    if linea[ALFABETO.index(
                    NOTAS_PARAMETROS[
                    "columna_verificacion"])] == "":
                        break
                    nota = {}
                    for f in db.calificacion.fields:
                        if f in NOTAS_PARAMETROS:
                            if f in NOTAS_CONVERSORES:
                                if type(
                                NOTAS_PARAMETROS[f]) == tuple:
                                    parametros = []
                                    for e in \
                                    NOTAS_PARAMETROS[f]:
                                        parametros.append(linea[
                                        ALFABETO.index(e)])
                                    nota[f] = NOTAS_CONVERSORES[
                                    f](parametros)
                                else:
                                    nota[f] = NOTAS_CONVERSORES[
                                    f](linea[
                                    ALFABETO.index(
                                    NOTAS_PARAMETROS[f])]
                                    )
                            else:
                                nota[f] = linea[ALFABETO.index(
                                NOTAS_PARAMETROS[f])]

                    if (nota["estudiante"] is None) and \
                    form.vars.aproximar:
                        if "estudiante_nombre" in \
                        NOTAS_PARAMETROS:
                            if type(
                            NOTAS_PARAMETROS["estudiante_nombre"]
                            ) == tuple:
                                parametros = []
                                for e in NOTAS_PARAMETROS[
                                "estudiante_nombre"]:
                                    parametros.append(linea[
                                    ALFABETO.index(e)])
                                parametros = tuple(parametros)
                            else:
                                parametros = linea[
                                ALFABETO.index(
                                NOTAS_PARAMETROS[
                                "estudiante_nombre"])]
                        nota["estudiante"
                        ] = estudiante_identificar(
                        inscriptos, parametros)

                    if not (nota["estudiante"] is None):
                        session.notas.append(nota)
                    else:
                        session.notas_excluidas.append(nota)

        if len(session.notas) > 0:
            # recuperar notas ya cargadas para
            # actualizar los datos
            filtro_lista = list()
            criterios = ("materia", "ciclo", "turno",
            "cuatrimestre", "nivel", "division", "plan", "comision",
            "docente")
            
            for f in db.calificacion.fields:
                if (f in criterios) and (
                form.vars[f] != None):
                    filtro_lista.append((
                    db.calificacion[f],
                    form.vars[f]))
                    for nota in session.notas:
                       nota[f] = form.vars[f]
                       
            if len(filtro_lista) >= 1:
                filtro_query = db.calificacion.id > 0
                for f in filtro_lista:
                    filtro_query &= f[0] == f[1]
                session.filtro_rows = db(filtro_query).select()
                
            if not form.vars.aproximar:
                for nota in session.notas:
                    actualizado = False

                    for row in session.filtro_rows:
                        if nota["estudiante"] == row.estudiante:
                            row.update_record(**nota)
                            actualizado = True
                            
                    if not actualizado:
                        nota_id = db.calificacion.insert(**nota)
                        nota["id"] = nota_id
                redirect(URL("carganotasresultado"))
            else:
                redirect(URL("carganotasconfirmar"))
        else:
            redirect(URL("carganotasresultado"))
    return dict(form = form)


@auth.requires_membership('administradores')
def carganotasconfirmar():
    fields = [Field("estudiante_%s" % aproximacion,
                    "boolean",
                    default=True,
                    label="%s ---> %s" % (session.aproximaciones[aproximacion][0], session.aproximaciones[aproximacion][1])) for aproximacion in session.aproximaciones]
    form = SQLFORM.factory(*fields)
    session.aproximaciones_aceptados = []
    session.aproximaciones_rechazados = []
    if form.process().accepted:
        for k in form.vars.keys():
            estudiante_id = int(k.split("_")[1])
            if form.vars[k] == True:
                session.aproximaciones_aceptados.append(estudiante_id)
            else:
                session.aproximaciones_rechazados.append(estudiante_id)

        for nota in session.notas:
            if not ((nota["estudiante"] in session.aproximaciones_rechazados) or (nota["estudiante"] is None)):
                actualizado = False
                for row in session.filtro_rows:
                    if nota["estudiante"] == row.estudiante:
                        row.update_record(**nota)
                        actualizado = True
                if not actualizado:
                    nota_id = db.calificacion.insert(**nota)
                    nota["id"] = nota_id

        redirect(URL("carganotasresultado"))
    return dict(form=form)

@auth.requires_membership('administradores')
def carganotasresultado():
    return dict(datos=session.notas_datos,
                notas=session.notas,
                notas_excluidas=session.notas_excluidas,
                aproximaciones=session.aproximaciones,
                excluidas=session.aproximaciones_excluidas,
                aceptados=session.aproximaciones_aceptados,
                rechazados=session.aproximaciones_rechazados)

@auth.requires_membership('administradores')
def estudiantescargardeei():
    """ Action para pasar la planilla de eficiencia interna
    como listado de alumnos a la BBDD"""
    form = SQLFORM.factory(Field("archivo", "upload", label="Archivo CSV"))
    if form.process().accepted:
        session.errores = list()
        session.estudiantescargardeei_registros = list()
        with open(os.path.join(request.folder,
                               "uploads", 
                               form.vars.archivo),
                               newline='',
                               encoding=CSV_CODIFICACION) \
                               as archivo:
            lector = csv.reader(archivo,
                                delimiter=CSV_DELIMITADOR,
                                quotechar=CSV_COMILLAS)
            contador = 0
            # apellidos 0, nombres 1
            # fecha de nacimiento 11 dd/mm/aa
            campos = ("nombre", "documento_tipo", "documento_numero", "nacionalidad", "domicilio_datos", "localidad", "responsable_nombre", "responsable_telefono", "responsable_mail", "fecha_nacimiento")
            for fila in lector:
                contador += 1
                # pasar valores a campos e insertar registro                    
                if contador > 1:
                    valores = list()
                    valores.append(", ".join((fila[0], fila[1])))
                    contador_2 = 0                      
                    for columna in fila:
                        if (contador_2 > 1) and (contador_2 < 10):
                            valores.append(fila[contador_2])
                        contador_2 += 1
                    fecha_datos = fila[10].split("/")
                    a_n = int(fecha_datos[2])
                    if a_n <= 23:
                        a_n += 2000
                    elif a_n <= 100:
                        a_n += 1900
                    else:
                        pass
                    try:
                        fecha = datetime.date((a_n),
                                          int(fecha_datos[1]),
                                          int(fecha_datos[0]))
                    except ValueError:
                        fecha = None
                    valores.append(fecha)
                    estudiante_datos = dict()
                    contador_3 = 0
                    
                    inscripcion_datos = {"ciclo": CICLOS[0]}
                    
                    try:
                        texto_curso = fila[12].split("°")
                        inscripcion_datos["nivel"] = int(texto_curso[0])
                        inscripcion_datos["division"] = int(texto_curso[1])
                    except (ValueError, TypeError, IndexError) as error:
                        inscripcion_datos["nivel"] = None
                        inscripcion_datos["division"] = None
                        session.errores.append((error, valores, fila[12]))
                    try:
                        inscripcion_datos["turno"] = fila[11][1]
                    except (ValueError, TypeError, IndexError) as error:
                        inscripcion_datos["turno"] = None
                        session.errores.append((error, valores, fila[11]))


                    for campo in campos:
                        estudiante_datos[campo] = valores[contador_3]
                        contador_3 += 1

                    estudiante_id = db.estudiante.insert(**estudiante_datos)
                    inscripcion_datos["estudiante"] = estudiante_id
                    session.estudiantescargardeei_registros.append(estudiante_id)
                    db.inscripcion.insert(**inscripcion_datos)
        redirect(URL("estudiantescargardeeiresultado"))
    return dict(form=form)

@auth.requires_membership('administradores')    
def estudiantescargardeeiresultado():
    return dict(resultado=session.estudiantescargardeei_registros, errores=session.errores)
    
@auth.requires_membership('administradores')
def notascargardeei():
    """ Action para pasar la planilla de eficiencia interna
    como listado de notas a la BBDD"""
    
    form = SQLFORM.factory(Field("archivo", "upload", label="Archivo CSV"))
    if form.process().accepted:
        session.errores = list()
        session.notascargardeei_registros = list()
        
        # - Definir un arreglo indicando materia y nivel por columna
        columnas = {4: ("Biología", 1),
                    5: ("Geografía", 1),
                    6: ("Historia", 1),
                    7: ("Informática", 1),
                    8: ("Inglés", 1),
                    9: ("Lengua y Literatura", 1),
                    10: ("Matemática", 1),
                    11: ("Biología", 2),
                    12: ("Desarrollo y Salud", 2),
                    13: ("Geografía", 2),
                    14: ("Historia", 2),
                    15: ("Informática", 2),
                    16: ("Inglés", 2),
                    17: ("Lengua y Literatura", 2),
                    18: ("Matemática", 2),
                    19: ("Economía", 3),
                    20: ("Geografía", 3),
                    21: ("Historia", 3),
                    22: ("Inglés", 3),
                    23: ("Lengua y Literatura", 3),
                    24: ("Matemática", 3),
                    25: ("Química", 3),
                    26: ("Ciencias de la Vida y de la Tierra", 4),
                    27: ("Física", 4),
                    28: ("Formación Ética y Ciudadana", 4),
                    29: ("Inglés", 4),
                    30: ("Lengua y Literatura", 4),
                    31: ("Matemática", 4),
                    32: ("Proyecto", 4)}
        # - Crear un objeto para asociar doctipo_numero -> id de la BBDD,
        # con una consulta a db.estudiante
        rows = db(db.estudiante).select()
        estudiantes = dict()
        for estudiante in rows:
            estudiantes["-".join((estudiante.documento_tipo, estudiante.documento_numero))] = estudiante.id
            
        with open(os.path.join(request.folder,
                               "uploads", 
                               form.vars.archivo),
                               newline='',
                               encoding=CSV_CODIFICACION) \
                               as archivo:
            lector = csv.reader(archivo,
                                delimiter=CSV_DELIMITADOR,
                                quotechar=CSV_COMILLAS)

            # algoritmo:
            # 1) Recorrer el .csv
            contador = 0
            for fila in lector:
                # a) En cada fila que no sea encabezado,
                if contador > 1:
                    estudiante = "-".join((fila[2], fila[3]))
                    try:
                        estudiante_id = estudiantes[estudiante]
                        plan = plan_recuperar(db, estudiante_id)
                    except KeyError:
                        estudiante_id = None
                    contador_2 = 0
                    for campo in fila:
                        if contador_2 > 3:
                            # buscar notas mayores que 5 (aprobado),
                            # filtrando columnas que no contienen notas
                            if campo.isdigit():
                                nota = int(campo)
                                # b) Si la nota es mayor que 5, insertar en BDD,
                                # usando id almacenada en objeto y arreglo
                                if (nota > 5) and (estudiante_id != None):
                                    nota_id = db.calificacion.insert(
                                        estudiante = estudiante_id,
                                        materia = columnas[contador_2][0],
                                        nivel = columnas[contador_2][1],
                                        plan = plan,
                                        definitiva = nota,
                                        observaciones = "Tomada de Eficiencia Interna",
                                        acredito = True,
                                        promueve = True,
                                        condicion = CONDICION_POR_DEFECTO,
                                        promocion = PROMOCION_POR_DEFECTO,
                                        fecha = datetime.date.today())
                                    session.notascargardeei_registros.append(nota_id)
                        contador_2 += 1
                contador += 1
            
        redirect(URL("notascargardeeiresultado"))
    return dict(form=form)

@auth.requires_membership('administradores')    
def notascargardeeiresultado():
    return dict(resultado=session.notascargardeei_registros, errores=session.errores)

@auth.requires_membership('administradores')
def backup():
    form = SQLFORM.factory()
    resultado = None
    if form.process().accepted:
        with open("applications/%s/private/backup.csv" % request.application, "w", encoding="utf-8") as mibackup:
            db.export_to_csv_file(mibackup)
            resultado = "Backup finalizado"
    return dict(form=form, resultado=resultado)

@auth.requires_membership('administradores')
def restaurar():
    form = SQLFORM.factory()
    resultado = None
    if form.process().accepted:
        with open("applications/%s/private/backup.csv" % request.application, "r", encoding="utf-8") as mibackup:
            db.import_from_csv_file(mibackup)
            resultado = "Restauración finalizada"
    return dict(form=form, resultado=resultado)

@auth.requires_membership('administradores')
def estudiantescargarlistado():
    aceptado = False
    errores = list()
    registros = list()
    
    # a) Dictionary con campo/columna
    estudiante_campos = {
    "nombre":2,
    "fecha_nacimiento":3,
    "documento_numero":5,
    "domicilio_datos":6,
    "responsable_telefono":7,
    "responsable_mail":8,
    "nacionalidad":9,
    "responsable_nombre":10}
    inscripcion_campos = {
    "nivel":0,
    "division":1,
    }
    
    # b) Formulario para subir archivo

    form = SQLFORM.factory(Field("archivo", "upload",
                           label="Archivo CSV"))
    if form.process().accepted:
        aceptado = True
        with open(os.path.join(request.folder,
                               "uploads", 
                               form.vars.archivo),
                               newline='',
                               encoding=CSV_CODIFICACION) \
                               as archivo:
            lector = csv.reader(archivo,
                                delimiter=CSV_DELIMITADOR,
                                quotechar=CSV_COMILLAS)

            # c) Recorrer .csv
            for fila in lector:
                # c i) Generar objetos estudiante e inscripción por registro
                estudiante = dict()
                inscripcion = dict()
                try:
                    for k, v in estudiante_campos.items():
                        estudiante[k] = fila[v]
                    # Convertir fecha de str a date
                    fecha_str = estudiante["fecha_nacimiento"].split("/")
                    estudiante["fecha_nacimiento"] = datetime.date(int(fecha_str[2]), int(fecha_str[1]), int(fecha_str[0]))
                    estudiante["documento_tipo"] = "DNI"
                    estudiante_id = db.estudiante.insert(**estudiante)
                    for k, v in inscripcion_campos.items():
                        inscripcion[k] = fila[v]
                    inscripcion["estudiante"] = estudiante_id
                    inscripcion["ciclo"] = CICLOS[0]
                    inscripcion["turno"] = "N"
                    # c iii) db.estudiante.insert(**objeto)
                    inscripcion_id = db.inscripcion.insert(**inscripcion)
                    registros.append("Nuevos registros: estudiante %s; inscripcion %s" % (estudiante_id, inscripcion_id))
                except (ValueError, KeyError, IndexError) as error:
                    errores.append(error)
    return dict(aceptado=aceptado, form=form, resultado=registros, errores=errores)

@auth.requires_membership('administradores')
def notascargarlistado():
    aceptado = False
    resultado = list()
    errores = list()
    
    # invertir abreviaciones de materias
    abreviaciones = dict()
    for k, v in ABREVIACIONES.items():
        abreviaciones[v] = k
    
    # nombre del estudiante -> 0
    # nota_definitiva -> 5
    # materia -> 6
    # nivel -> 7

    # Generar objeto con nombres de alumnos
    rows = db(db.estudiante).select()
    estudiantes = dict()
    ciclo = CICLOS[0]
    observaciones = "Carga automática desde calificaciones 2023"
    for row in rows:
        estudiantes[row.nombre] = row.id

    # Formulario para subir archivo
    form = SQLFORM.factory(Field("archivo", "upload",
                           label="Archivo CSV"))
    if form.process().accepted:
        aceptado = True
        with open(os.path.join(request.folder,
                               "uploads", 
                               form.vars.archivo),
                               newline='',
                               encoding=CSV_CODIFICACION) \
                               as archivo:
            lector = csv.reader(archivo,
                                delimiter=CSV_DELIMITADOR,
                                quotechar=CSV_COMILLAS)
    
            # d) Recorrer .csv
            for fila in lector:
                try:
                    # d i) Identificar registro de estudiante
                    estudiante_id = estudiantes[fila[0]]
                    plan = plan_recuperar(db, estudiante_id)
                except KeyError as error:
                    errores.append("%s: no se encontró el estudiante" % fila[0])
                    continue
                try:
                    nivel = int(fila[7])
                except ValueError as error:
                    errores.append("%s: error al convertir el nivel %s" % (fila[0], fila[7]))
                    continue
                try:
                    materia = fila[6]

                    # Si está aprobada y pertenece al plan
                    # db.calificacion.insert(**objeto)
                    if abreviaciones[materia] in PLAN[plan][nivel]:
                        if fila[5].isdigit():
                            nota = int(fila[5])
                            if nota > 5:
                                calificacion_id = db.calificacion.insert(
                                estudiante = estudiante_id,
                                definitiva = nota,
                                promueve = True,
                                acredito = True,
                                alta_fecha = datetime.date.today(),
                                plan = plan,
                                nivel = nivel,
                                materia = materia,
                                ciclo = ciclo,
                                observaciones = observaciones
                                )
                                resultado.append("%s: nueva nota; %s %s" % (fila[0], materia, nota))
                    else:
                        errores.append("%s: no se encontró la materia %s en nivel %s" % (fila[0], materia, nivel))
                except (ValueError, IndexError, KeyError) as error:
                    errores.append("%s: Error al cargar nota: %s" % (fila[0], error))
    return dict(aceptado=aceptado, form=form, resultado=resultado, errores=errores)
