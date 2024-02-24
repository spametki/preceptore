/*
Acá hay que declarar las funciones que:
- Recorren los objetos de js y completan los select según inscripciones
de cada estudiante. En la lista de estudiantes solo van los que no están
inscriptos a una comisión.
- Calculan los horarios de clase de cada estudiante
y comprueban la incompatibilidad horaria de inscripciones
- Agregan un estudiante del listado a una comisión
- Quitan a un estudiante del listado de una comisión

- Recorrer el listado de estudiantes en datos
- para cada estudiante:
- ver si está anotado en una comisión
- si no está anotado en comisión,
- agregar a listado de alumnos con alumnoAgregar
- si está anotado en comisión, agregar a comisión
- con alumnoAgregar
*/

/*
TODO:
- La búsqueda de materia no coincide entre las notas
del estudiante y no puede comprobar la superposición horaria.
Hecho: si no se encuentra la asignatura se omite la comprobación
de superposición.
- El formulario tiene que mostrar un cuadro de texto donde
se agreguen las superposiciones de horario al agregar estudiantes
- No se verifica la comparación de notas en cargarListados. Al recorrer
el array las propiedades devuelven undefined. Nuevo comportamiento después
de modificaciones en el modelo y el controlador.
*/


var mensajeAgregar = function(mensaje){
  // Agrega un mensaje a la caja de texto
  jQuery("#no_table_mensajes").text(jQuery("#no_table_mensajes").text() + mensaje + "\n");
};

var alumnoAgregar = function(listado, id){
  // Crea un option para el alumno
  var estudiante = datos[id];
  var option = "<option id=estudiante_" + id + " value=" + id + ">" + estudiante.nombre + " - " + estudiante.documentoTipo + " " + estudiante.documentoNumero + " - " + estudiante.nivel + "º " + estudiante.division + " ª" + "</option>";
  // Lo agrega al select del listado
  jQuery(listado).append(option);
};

var alumnoQuitar = function(id){
  // Busca select del listado
  // elimina el option que corresponde al id
  jQuery("#estudiante_" + id).remove();
};

var buscarAsignatura = function(calificacion){
  var asignatura;
  for (index in asignaturas){
    asignatura = asignaturas[index]
    if ((asignatura.materia == calificacion.materia) &&
        (asignatura.nivel == calificacion.nivel) &&
        (asignatura.division == calificacion.division) &&
        (asignatura.cuatrimestre == calificacion.cuatrimestre) &&
        (asignatura.comision == calificacion.comision)){
        return asignatura;
        };
  };
};

var superposicion = function(comision, id){
  var dias = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"];
  var dia;
  var estudiante = datos[id];
  var notas = estudiante["notas"];
  var comisionAsignatura;
  var asignatura;
  var calificacion;  
  // Recuperar horarios de la comision
  for (index in comisiones){
    if (comisiones[index].asignatura.comision == comision){
      comisionAsignatura = comisiones[index].asignatura;
    };
  };
  // Recorrer calificaciones del estudiante
  for (index in notas){
    calificacion = notas[index];
    asignatura = buscarAsignatura(calificacion);
    // Si es la misma materia, omitir
    if (!(calificacion.materia == comisionAsignatura.materia) && (asignatura != undefined)){
      // Recorrer horarios y comprobar si
      // hay coincidencia de turno/contraturno y hora
      if ((comisionAsignatura.turno == asignatura.turno) &&
           (comisionAsignatura.contraturno == asignatura.contraturno)){
             for (index in dias){
               dia = dias[index];
               if((comisionAsignatura[dia] != null) && (asignatura[dia] != null)){
                 for (indexHora in comisionAsignatura[dia]){
                   if (comisionAsignatura[dia][indexHora] in asignatura[dia]){
                     mensajeAgregar("Superposición horaria. Alumna/o: " + estudiante.nombre + ". Materia: " + calificacion.materia);
                     return true;
                   };
                 };
               };
             };

      };
    };
  };    
  return false;
};

// Agregar un alumno a una comisión
var comisionAgregar = function(comision, id){
  // Comprobar que no haya superposición de horarios
  // Si hay superposición, devolver un mensaje con el error
  // y salir sin agregar al estudiante
  if (superposicion(comision, id)){
    return;
  }
  else {
  // Recuperar el select que corresponde a la comisión
  var comisionSelect = "#no_table_" + comision;
  // Recuperar el select del listado de alumnos
  var listadoSelect = "#no_table_listado";
  // llamar a alumnoAgregar con id = alumno y el select
  // recuperado
  alumnoAgregar(comisionSelect, id);
  // llamar a alumnoQuitar con id = alumno
  // del listado de alumnos
  alumnoQuitar(id);
  seleccionarTodo();
  };
};

// Quitar un alumno de una comisión
var comisionQuitar = function(comision, id){
// Recuperar el select que corresponde a la comisión
  var comisionSelect = "#no_table_" + comision;
  // Recuperar el select del listado de alumnos
  var listadoSelect = "#no_table_listado";
  // llamar a alumnoQuitar con id = alumno
  // del listado de la comisión
  alumnoQuitar(id);
  // llamar a alumnoAgregar con id = alumno y select
  // del listado de alumnos
  alumnoAgregar(listadoSelect, id);
  seleccionarTodo();  
};

var recuperarComision = function(id){
  return id.split("_")[1];
};

// Responde a evento de click en botón
// de agregar alumnos de una comisión
var seleccionAgregar = function(event){
  // event.target -> elemento asociado al click
  // Recuperar la comisión que corresponde al botón
  var comision = recuperarComision(event.target.id);
  // Recuperar los estudiantes seleccionados
  // del listado y recorrer la lista llamando a comisionAgregar
  jQuery("#no_table_listado option:selected").each(
    function(index, element){
      comisionAgregar(comision, element.value);
    });
};

// Responde a evento de click en botón
// de quitar alumnos de una comisión
var seleccionQuitar = function(event){
  // Recuperar la comisión que corresponde al botón
  var comision = recuperarComision(event.target.id);
  // Recuperar los estudiantes seleccionados
  // del listado de la comisión y recorrer la lista llamando a comisionQuitar
  jQuery("#no_table_" + comision + " option:selected").each(
    function(index, element){
      comisionQuitar(comision, element.value);
    });
};

// Carga los listados por primera vez
var cargarListados = function(){
  // por cada elemento estudiante de datos
  // recorrer calificaciones
  var agregado;
  var listado;
  for (alumno in datos){
    agregado = false;
    console.log("datos[alumno].comision");
    console.log(datos[alumno].comision);
    if (datos[alumno].comision != null){
      listado = "#no_table_" + datos[alumno].comision;
      console.log(listado);
      alumnoAgregar(listado, datos[alumno].id);
      agregado = true;
    };

    /* No va! Hay que buscar por propiedad comision en datos[alumno]
    for (nota in datos[alumno].notas){
      notaObjeto = datos[alumno].notas[nota];
      // si la calificacion coincide con una comision
      // agregar el alumno al listado que corresponde
      if ((notaObjeto.ciclo == ciclo) &&
          (notaObjeto.cuatrimestre == cuatrimestre) &&
          (notaObjeto.materia == materia) &&
          (notaObjeto.nivel == nivel)){
        alumnoAgregar("#no_table_" + notaObjeto.comision, datos[alumno].id);
        agregado = true;
      };
    }; */

      if (!agregado) {
        // agregar a lista de estudiantes
        alumnoAgregar("#no_table_listado", datos[alumno].id);
      };
  };
};

jQuery(document).ready(function(){
// asociar botones a acciones
  for (row in comisiones){
    jQuery("#agregar_" + comisiones[row].asignatura.comision).on("click", seleccionAgregar);
    jQuery("#quitar_" + comisiones[row].asignatura.comision).on("click", seleccionQuitar);
  };
  // carga de datos en los select
  cargarListados();
});

var seleccionarTodo = function(){
  // Autoselecciona todos los item de las
  // comisiones para que al aceptar el
  // formulario se incluyan los valores
  // en cada campo
  var comision;
  for (index in comisiones){
    comision = comisiones[index].asignatura.comision;
    jQuery("option").prop("selected", true);
  };
};
