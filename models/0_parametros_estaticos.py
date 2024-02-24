# -*- coding: utf-8 -*-

__author__ = "Alan Edmundo Etkin <spametki@gmail.com>"
__copyright__ = "(C) 2024 Alan Edmundo Etkin. GNU GPL 3."

# Librerías externas
import json
import datetime
import os
import csv
import difflib

# módulos web2py
# Objeto CRUD para ABM
from gluon.tools import Crud # TODO: no se usa más

# Clases para x_clases.py
from gluon.sqlhtml import OptionsWidget, add_class

# Deshabilitar para evitar excepción por falta de librería en
# web2py windows standalone
from dateutil.relativedelta import relativedelta

""" Parámetros estáticos que no requieren otros objetos
"""

# TODO: cómputo de faltas por materia:
# no se computa si la materia está promocionada
# y finalizó el período regular

ESCUELA = "E.T. Nº 15 D.E. 5to"
ESCUELA_NOMBRE = "Maipú"
ESCUELA_CUE = ""


# TODO: cambiar _cambio y _fin según el ciclo
CICLOS = (2023, 2024)
CICLO_CAMBIO = (1, 3) # día, mes
CICLO_FIN = (31, 12) # TODO: es fin de clases regulares
CUATRIMESTRE_CAMBIO = (1, 8)
TURNOS = ("M", "T", "N")
TURNOS_ETIQUETAS = {"M": "mañana", "T": "tarde", "N": "Noche"}
NIVELES = (1, 2, 3, 4)

NUMEROS_ROMANOS = {1: "I", 2: "II", 3:"III",
4:"IV", 5:"V", 6:"VI", 7:"VII", 8:"VIII",
9:"IX", 10:"X"}

# Máximo de niveles simultáneos por ciclo
NIVELES_SIMULTANEOS = 3
DIVISIONES = ("1", "2", "3", "4")
CUATRIMESTRES = (1, 2)
COMISIONES = ("A", "B", "C", "D")

GENEROS = ("Hombre", "Mujer", "No binario")

SITUACIONES = ("Interina/o", "Suplente", "Titular", "Otra")
CONDICIONES = ("Libre", "Regular", "No regular", "Baja")
CONDICION_POR_DEFECTO = "Regular"
PROMOCIONES = ("P.D", "P.A.", "P.E.P.", "Previa", "Nivelación",
               "Equivalencia", "Movilidad",
               "Resolución interna")
PROMOCION_POR_DEFECTO = "P.D."
PROMOCIONES_PRESENCIALES = ("P.D.",)

# No se califican pero deben figurar en el horario
ESPACIOS_COMUNES = ("Tutoría",)

DOCUMENTOS = ("DNI", "DU", "CI", "Pasaporte", "Otro")

HORARIOS = {
 "M": (("7:45", "8:45"), ("8:55", "9:55"), ("10:10", "10:50"),
       ("10:50", "11:30"), ("11:35", "12:15")),
 "T": (("13:30", "14:20"), ("14:30", "15:20"), ("15:35", "16:20"),
       ("16:20", "17:00"), ("17:05", "17:50")),
 "N": (("18:00", "18:30"), ("18:30", "19:00"), ("19:00", "19:30"),
       ("19:30", "20:00"), ("20:10", "20:40"), ("20:40", "21:10"),
       ("21:20", "21:50"), ("21:50", "22:20"), ("22:20", "22:50"))
}

RECREOS = (("8:45", "8:55"), ("9:55", "10:10"),
           ("11:30", "11:35"), ("14:20", "14:30"),
           ("15:20", "15:35"), ("17:00", "17:05"))



MATERIAS = ("Matemática", "Lengua y Literatura", "Historia",
            "Geografía", "Biología", "Inglés", "Informática", 
            "Desarrollo y Salud", "Tutoría", "Taller", "Apoyo",
            "Física", "Química", "Economía",
            "Ciencias de la Vida y de la Tierra", "Proyecto",
            "Formación Ética y Ciudadana")

# Indica a qué división pasa según el nivel
DIVISIONES_SECUENCIA = (
("1", "1", "1", "1"),
("2", "2", "2", "2")
)


MATERIAS_TRAYECTO_EXCLUIR = ("Inglés", "Informática")

ABREVIACIONES = {"Mate": "Matemática", "LyL": "Lengua y Literatura", "Hist": "Historia",
            "Geo": "Geografía", "Bio": "Biología", "Ing": "Inglés", "Inf": "Informática", 
            "DyS": "Desarrollo y Salud", "Tut": "Tutoría", "Tall": "Taller", "Ap": "Apoyo",
            "Fis": "Física", "Quim": "Química", "Eco": "Economía",
            "CVT": "Ciencias de la Vida y de la Tierra", "Proy": "Proyecto",
            "FEC": "Formación Ética y Ciudadana", "Tut": "Tutoría",
            "Tall": "Taller", "Ap": "Apoyo"}

DIAS = ("lunes", "martes", "miercoles", "jueves", "viernes")

DIAS_PYTHON = {"lunes":0, "martes":1, "miercoles":2, "jueves":3, "viernes":4, "sabado": 5, "domingo": 6}
DIAS_PYTHON_REVERSO = {0:"lunes", 1:"martes", 2:"miercoles", 3:"jueves", 4:"viernes", 5:"sabado", 6:"domingo"}

DIAS_ROTULOS = ("lunes", "martes", "miércoles", "jueves",
"viernes", "sábado", "domingo")

MESES = {1:"enero", 2:"febrero", 3:"marzo", 4:"abril", 5:"mayo", 6:"junio", 7:"julio", 8:"agosto", 9:"septiembre", 10:"octubre", 11:"noviembre", 12:"diciembre"}

CALIFICACIONES = ("1", "2", "3", "4", "5", "6", "7",
"8", "9", "10")
CONCEPTOS = ("Suficiente", "Avanzado", "En proceso")

NOTAS_FORMATO = {"nota_01":{"tipo": "concepto",
                    "rotulo": "1er bimestre",
                    "utilizar": True},
                 "nota_02":{"tipo": "concepto",
                    "rotulo": "2do bimestre",
                    "utilizar": True},
                 "nota_03":{"tipo": "numero",
                    "rotulo": "1er cuatrimestre",
                    "utilizar": True},                           
                 "nota_04":{"tipo": "concepto",
                    "rotulo": "3er bimestre",
                    "utilizar": True},                           
                 "nota_05":{"tipo": "concepto",
                    "rotulo": "4to bimestre",
                    "utilizar": True},                           
                 "nota_06":{"tipo": "numero",
                    "rotulo": "2do cuatrimestre",
                    "utilizar": True},
                 "nota_07":{"tipo": "numero",
                    "rotulo": "Promedio anual",
                    "utilizar": True},
                 "nota_08":{"tipo": "numero",
                    "rotulo": "Diciembre",
                    "utilizar": True},
                 "nota_09":{"tipo": "numero",
                    "rotulo": "Febrero",
                    "utilizar": True},
                 "nota_10":{"tipo": None,
                     "rotulo": None,
                     "utilizar": False},
                 "nota_11":{"tipo": None,
                     "rotulo": None,
                     "utilizar": False},
                 "nota_12":{"tipo": None,
                     "rotulo": None,
                     "utilizar": False},
                 "definitiva": {"tipo": "numero",
                                "rotulo": "Definitiva",
                    "utilizar": True}}

# TODO: soporte para múltiples planes.
# Hay que adaptar todos los listados por
# defecto con mayúsculas para contemplar
# distintos planes, por ej. los cambios
# de las correlatividades, etc.
# Tabién hay que modificar el modelo
# para que la inscripción incluya plan

PLAN = {
1 : {
        1:("Mate", "LyL", "Hist",
           "Geo", "Bio", "Inf", "Ing"),
        2:("Mate", "LyL", "Hist",
           "Geo", "Bio", "DyS",
           "Inf", "Ing"),
        3:("Mate", "LyL", "Hist",
           "Geo", "Quim", "Eco", "Ing"),
        4:("Mate", "LyL", "Fis",
           "FEC", "Proy",
           "CVT", "Ing")
       }
}

PLAN_NOMBRES = {1: "Bachiller"}
PLAN_ABREVIACIONES = {1: "Bachiller"}

# Correlatividades: "Materia": ((Nivel, nro. de índice), ...)
#                   Nivel se indica 1, 2, 3,...
#                   Número de índice de materia según lista
#                   en PLAN tomando 0 como la primera

#                   Nota: La sintaxis de Python
#                   requiere usar coma al final en las tuplas
#                   de un elemento

DIVISIONES_PLAN = (
(None,None,None,None, None),
(None,1,1,1,1),
(None,1,1,1,1),
(None,1,1,1,1),
(None,1,1,1,1)
)

DIVISIONES_TURNOS = (
(None,None,None,None,None),
(None,"M","M","M","M"),
(None,"M","M","M","M"),
(None,"M","M","M","M"),
(None,"M","M","M","M")
)

ASISTENCIA = {"p": "Presente", "t": "Tarde", "tj": "Tarde justificado", "ap": "Ausente con presencia",
"aj": "Ausente justificado",
              "a": "Ausente", "n/a": "No se computa"}

ASISTENCIA_CATEGORIAS = {"p": "categoria_01", "a": "categoria_02", "t": "categoria_03", "ap": "categoria_04", "aj": "categoria_05", "tj": "categoria_06", "n/a": "categoria_07"}

ASISTENCIA_POR_DEFECTO = "a"

# el primer elemento es asistencia, el segundo inasistencia
ASISTENCIA_VALORES = {
"p": (1, 0), "a": (0, 1), "t": (0.5, 0.5), "ap": (0, 1), "aj": (0, 1), "tj": (1, 0), "n/a": (0, 0)
}

FECHA_CORTE_EDAD = (31, 6) # día, mes

BAJA_MOTIVOS = ("Pase de turno", "Solicitud", "Resolución",
"Pase de escuela", "Cambio de comisión", "Otro")

CSV_DELIMITADOR = ","
CSV_COMILLAS = '"'
CSV_CODIFICACION = "utf-8"

ALFABETO = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

REGISTRO_PARAMETROS = {
"primera_linea": 5,
"columna_verificacion": "E", # verificar fin del listado
"nombre": ("A", "B"),
"documento_numero": "E",
"ingreso": "C",
"fecha_nacimiento": "F",
"nacionalidad": "H",
"domicilio_datos": "J",
"telefono": "L",
"mail": "K",
"responsable_nombre": "M",
"responsable_domicilio_datos": "J",
"responsable_telefono": "N",
"responsable_mail": "O",
}

NOTAS_PARAMETROS = {
"estudiante_nombre": ("C", "D"),
"primera_linea": 5,
"columna_verificacion": "C",
"estudiante": ("C", "D"),
"nota_01": "E",
"nota_02": "F",
"nota_03": "G",
"nota_04": "H",
"nota_05": "I",
"nota_06": "J",
"nota_07": "K",
"nota_08": "L",
"nota_09": "M",
"definitiva": "N"
}

NOTA_MOTIVOS = ("Asistencia", "Convivencia", "Administrativa", "Comunicación", "Calificaciones", "Otros")

# Talleres extracurriculares
TALLERES = ()
TALLER_CALIFICACIONES = {}

# períodos de entrega de notas
BOLETINES = {1:"Primer bimestre", 2: "Primer cuatrimestre", 3: "Tercer bimestre", 4: "Cierre anual", 5: "Diciembre", 6: "Definitivo"}

BOLETINES_NOTAS = {
1: ("nota_01",),
2: ("nota_01", "nota_02", "nota_03"),
3: ("nota_01", "nota_02", "nota_03", "nota_04"),
4: ("nota_01", "nota_02", "nota_03", "nota_04", "nota_05", "nota_06", "nota_07", "definitiva"),
5: ("nota_01", "nota_02", "nota_03", "nota_04", "nota_05", "nota_06", "nota_07", "nota_08", "definitiva"),
6: ("nota_01", "nota_02", "nota_03", "nota_04", "nota_05", "nota_06", "nota_07", "nota_08", "nota_09", "definitiva")}

# Fechas de corte para cálculo
# de inasistencias en formato (dia, mes, diferencia año)
# 3er item: 0 es ciclo igual que año, 1 es año siguiente

BOLETINES_PLAZOS = {
1:(15, 5, 0), 2:(15, 7, 0) , 3:(15, 9, 0) , 4:(15, 11, 0), 5:(15, 12, 0), 6:(1, 3, 1)}

# Conceptos de alumnos para boletín
BOLETIN_CONCEPTOS_MOSTRAR = {1:False, 2:False, 3:False, 4:False, 5:False, 6:False}

BOLETIN_CONCEPTOS_TIPOS = {"concepto_01": "Relación con docentes y personal de la escuela", "concepto_02": "Relación con sus compañeros", "concepto_03": "Cumplimiento de normas de convivencia"}
BOLETIN_CONCEPTOS = {"MB": "Muy bueno", "B": "Bien", "R": "Regular", "I": "Insuficiente"}

BOLETIN_PREVIAS_MOSTRAR = {1:True, 2:True, 3:True, 4:True, 5:True, 6:True}
BOLETIN_TALLERES_MOSTRAR = {1:False, 2:False , 3:False , 4:False, 5:False, 6:False}

BOLETIN_ASISTENCIA_MATERIA_MOSTRAR = {1:False, 2:False , 3:False , 4:False, 5:False, 6:False}
BOLETIN_MOSTRAR_NIVEL = False # Mostrar nivel en cada materia

# Valor aceptable de similitud
# al comparar nombres de estudiantes
APROXIMACION_ESTUDIANTE = 0.9

# Etiqueta personalizada para generar código en el
# cliente que muestre automáticamente el plan según
# el nivel y división seleccionados
TITULO_MOSTRAR = H3("Plan: sin datos", _id="titulo_mostrar")

TITULO_SCRIPT = """
// Declarar arrays con información

// a) nombres de planes
var planes = %s;

// b) matriz por división
var divisionesPlan = %s;

var tituloEstablecer = function(){
// Si división y nivel no coincide
// con el título seleccionado en la action
// de plan, advertir con cartel o ventana.

// Recuperar nivel
var nivel = parseInt(jQuery('[name=nivel]').val());

// Recuperar division
var division = parseInt(jQuery('[name=division]').val());

// Si ambos son números, buscar el plan
// y mostrarlo
if (!(isNaN(nivel) || isNaN(division))){
jQuery('#titulo_mostrar').html('Plan: ' + planes[divisionesPlan[nivel][division]]);
} else {
jQuery('#titulo_mostrar').html('Plan: sin datos');
};
};

// Al cargar el documento o al cambiar el formulario,
// establecer el plan
jQuery(document).ready(function(){
   tituloEstablecer();
   jQuery('[name=nivel]').change(tituloEstablecer);
   jQuery('[name=division]').change(tituloEstablecer);
});
""" % (json.dumps(PLAN_ABREVIACIONES), json.dumps(DIVISIONES_PLAN))

# Elemento que actualiza el plan cuando se cambian nivel y división
TITULO_AUTOCOMPLETAR = SCRIPT(TITULO_SCRIPT, _type="text/javascript")
