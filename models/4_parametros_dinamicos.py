# -*- coding: utf-8 -*-

__author__ = "Alan Edmundo Etkin <spametki@gmail.com>"
__copyright__ = "(C) 2024 Alan Edmundo Etkin. GNU GPL 3."

# objetos que dependen de db
crud = Crud(db) # TODO: no se usa más

# Parámetros que requieren funciones en x_funciones.py

# lista de avisos para el usuario
session.avisos = []


#### Conversores de datos para carga automatizada

CORRELATIVIDADES = {
1: {
1:{},
2:{"Mate": ((1, 0),), "LyL": ((1, 1),),
"Hist": ((1, 2),), "Geo": ((1, 3),), "Bio": ((1, 4),),
"DyS": correlativasdys, "Ing": ((1, 6),), "Inf": ((1, 5),)},
3:{"Mate": ((2, 0),), "LyL": ((2, 1),), "Hist": ((2, 2),),
"Geo": ((2, 3),), "Ing": ((2, 7),), "Inf": ((2, 6),),
"Quim": ((2, 5),), "Eco": ((2, 4),)},
4:{"Mate": ((3, 0),), "LyL": ((3, 1),),
"Fis": ((3, 3), (3, 4), (3, 5)),
"FEC": ((3, 3), (3, 5), (3, 0)), "CVT": ((3, 4),),
"Proy": correlativasproy, "Ing": ((3, 6),)}
}
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
