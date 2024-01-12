# -*- coding: utf-8 -*-

__author__ = "Alan Edmundo Etkin <spametki@gmail.com>"
__copyright__ = "(C) 2024 Alan Edmundo Etkin. GNU GPL 3."

# Parámetros que requieren funciones en 3_funciones.py

# Objeto CRUD para ABM
from gluon.tools import Crud # TODO: no se usa más
crud = Crud(db) # TODO: no se usa más

import datetime
import os
import csv

# Deshabilitar para evitar excepción por falta de librería en
# web2py windows standalone
from dateutil.relativedelta import relativedelta
import difflib

# lista de avisos para el usuario
session.avisos = []


#### Conversores de datos para carga automatizada

CORRELATIVIDADES = {
1:{},
2:{},
3:{},
4:{},
5:{},
6:{}
}

REGISTRO_CONVERSORES = {
"nombre": lambda t: normalizar_nombre(", ".join(t)),
"documento_numero": lambda n: int("".join(n.split(".")
)) if "." in n else int(n),
"ingreso": lambda s: int(s) if s != "" else None,
"fecha_nacimiento": lambda s: datetime.date(int(s.split("/")[2]),
                                            int(s.split("/")[1]),
                                            int(s.split("/")[0]))\
                                            if s else None
}

NOTAS_CONVERSORES = {
"estudiante": lambda t: notas_conversores_estudiante(t),
"nota_03": lambda s: int(s) if s.isnumeric() else None,
"nota_06": lambda s: int(s) if s.isnumeric() else None,
"nota_07": lambda s: int(s) if s.isnumeric() else None,
"nota_08": lambda s: int(s) if s.isnumeric() else None,
"nota_09": lambda s: int(s) if s.isnumeric() else None}

# Funciones ad-hoc por tipo de escuela
# son funciones de models/3_funciones.py

PREVIAS_ESTABLECER_FUNCION = previas_establecer
