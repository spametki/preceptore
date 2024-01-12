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

