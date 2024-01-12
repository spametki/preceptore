# -*- coding: utf-8 -*-

__author__ = "Alan Edmundo Etkin <spametki@gmail.com>"
__copyright__ = "(C) 2024 Alan Edmundo Etkin. GNU GPL 3."

#----------------------------------------------------------------------------------------------------------------------
# this is the main application menu add/remove items as required
#----------------------------------------------------------------------------------------------------------------------

response.menu = [(T('Menú'), False, URL('default', 'index'),
                    [('Inicio', False, URL('default', 'index'), []),
                     ('Lista estudiantes', False, URL('estudiantes', 'estudiantes'), []),
                     ('Notas', False, URL('administrativas', 'calificaciones'), []),
                     ('Consultar horarios', False, URL('horarios', 'horariosconsulta'), []),
                     ('Ausentes con aviso', False, URL('administrativas', 'docenteausencia'), []),
                     ('Suspensión de actividad', False, URL('administrativas', 'suspensionactividad'), []),
                     ('Asignaturas', False, URL('administrativas', 'asignaturas'), []),
                     ('Docentes', False, URL('administrativas', 'docentes'), []),
                     ('Designaciones', False, URL('administrativas', 'designaciones'), []),
                     ('Parte de aula', False, URL('presentismo', 'partedeaula'), []),
                     ('Asistencia', False, URL('presentismo', 'asistencia'), []),
                     ('Boletines', False, URL('academicas', 'boletin'), []),                     
                     ])]

