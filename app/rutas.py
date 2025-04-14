"""
Módulo de Python que contiene las rutas
"""
import datetime
from flask import current_app as app, render_template, redirect, url_for, flash, abort, request
from .formularios import GenerarQuizForm
from . import mongo
from .trivia import generar_n_preguntas_aleatoriamente
from .render_utils import render_pagination

@app.route("/")
@app.route("/ediciones")
def mostrar_ediciones():
    # Pagina actual de resultados
    pagina = int(request.args.get('page', 1))

    # Numero de elementos por pagina
    elementos_por_pagina = 5

    # Conexión y conteo de elementos
    coleccion_festivales = mongo.db["festivales"]
    total_elementos = coleccion_festivales.count_documents({})

    # Cargar solo los festivales de la página actual
    festivales = list(
        coleccion_festivales.find({}, {"_id": 0})
        .sort("anyo", -1)
        .skip((pagina - 1) * elementos_por_pagina)
        .limit(elementos_por_pagina)
    )

    # Cargamos la informacion
    paginacion = render_pagination(pagina, elementos_por_pagina, total_elementos, 'mostrar_ediciones')

    return render_template(
        "mostrar_ediciones.html",
        festivales=festivales,
        pagination=paginacion,
        pagina=pagina
    )


@app.route("/edicion/<int:anyo>")
def mostrar_festival(anyo: int):
    # Conexión
    coleccion_festivales = mongo.db["festivales"]

    # Buscar el festival por año
    festival = coleccion_festivales.find_one({"anyo": anyo})

    if not festival:
        # Si no se encuentra el festival, lanzar 404
        abort(404)

    # Extraer los detalles del festival
    pais_organizador = festival['pais']
    ciudad = festival['ciudad']
    participaciones = festival['concursantes']  # Lista de diccionarios de concursantes

    # Pasar estos parámetros al template
    return render_template(
        "mostrar_actuaciones_edicion.html",
        anyo=anyo,
        pais_organizador=pais_organizador,
        ciudad=ciudad,
        participaciones=participaciones
    )


@app.route('/jugar')
def jugar_quiz():
    # Jugar a un quiz. Esta funcion NO la teneis que modificar
    # (salvo probar diferentes num_preguntas si quereis un quiz mas largo).
    # Hay dos opciones: si no venimos de 'generar_quiz',
    # la lista de anyos y paises es vacia. Este caso se procesa en "OperacionesEurovision",
    # ya que si las listas son vacias, se asume que no hay ninguna restriccion.
    # Esta informacion se la proporcionamos al metodo "generar_n_preguntas_aleatoriamente", el cual devuelve
    # "n" preguntas que extienden a Trivia. Hay que proporcionar estas preguntas con el metodo "to_dict()" (para
    # convertir en diccionario) a la funcion "funcion_quiz_json"
    anyos = request.args.getlist("anyos", type=int)
    paises = request.args.getlist("paises")
    nombre = request.args.get("nombre", None)
    num_preguntas = 1

    preguntas_aleatorias = generar_n_preguntas_aleatoriamente(num_preguntas, anyos, paises, mongo.db["festivales"])

    preguntas = {"preguntas": [pregunta.to_dict() for pregunta in preguntas_aleatorias]}

    # Solo guardamos un nombre si no es nulo ni vacio
    if nombre:
        preguntas["_id"] = nombre

    return render_template("juego.html", preguntas=preguntas, guardable=nombre is not None)


@app.route('/quiz', methods=['GET', 'POST'])
def generar_quiz():
    # Conexión
    coleccion_festivales = mongo.db["festivales"]

    # Obtener lista de años y países desde la base de datos
    anyos = coleccion_festivales.distinct("anyo")
    anyos.sort(reverse=True)  # Ordenar los años de manera descendente
    paises = coleccion_festivales.distinct("pais")
    paises.sort()  # Ordenar los países de manera ascendente

    # Crear el formulario y pasar las listas de años y países
    form = GenerarQuizForm(anyos=anyos, paises=paises)

    # Si el formulario es válido
    if form.validate_on_submit():
        # Redirigir a 'jugar_quiz' con los parámetros
        return redirect(url_for('jugar_quiz', anyos=form.seleccion_anyos.data, paises=form.seleccion_paises.data, nombre=form.nombre.data))

    # Renderiza el formulario
    return render_template('crear_quiz.html', form=form)


@app.route("/pais/<id_pais>")
def mostrar_actuaciones_pais(id_pais: str):
    # Pagina actual de resultados
    pagina = int(request.args.get('page', 1))

    # Numero de elementos por pagina
    elementos_por_pagina = 10

    # Conexión y conteo de elementos
    coleccion_festivales = mongo.db["festivales"]
    total_elementos = coleccion_festivales.count_documents({"concursantes.id_pais": id_pais})

    # Comprobamos si el país existe (al menos un concursante con ese id_pais)
    existe_pais = coleccion_festivales.find_one({"concursantes.id_pais": id_pais})

    if not existe_pais:
        # Si no existe el país, lanzamos un error 404
        abort(404)

    # Paginación con datos reales de cada concursante
    pipeline = [
        {"$unwind": "$concursantes"},
        {"$match": {"concursantes.id_pais": id_pais}},
        {"$sort": {"anyo": -1}},
        {"$skip": (pagina - 1) * elementos_por_pagina},
        {"$limit": elementos_por_pagina},
        {"$project": {
            "_id": 0,
            "anyo": 1,
            "ciudad": 1,
            "pais_organizador": "$pais",
            "artista": "$concursantes.artista",
            "cancion": "$concursantes.cancion",
            "resultado": "$concursantes.resultado",
            "puntuacion": "$concursantes.puntuacion",
            "url_youtube": "$concursantes.url_youtube",
            "pais": "$concursantes.pais"
        }}
    ]

    participantes = list(coleccion_festivales.aggregate(pipeline))

    nombre_pais = participantes[0]["pais"]

    # Cargamos la informacion
    paginacion = render_pagination(pagina, elementos_por_pagina, total_elementos, 'mostrar_actuaciones_pais', id_pais=id_pais)

    return render_template("mostrar_actuaciones_pais.html", pagina=pagina, pagination=paginacion,
                           pais=nombre_pais, participaciones=participantes)


@app.route("/upload_contest", methods=["POST"])
def guardar_concurso():
    # data es el diccionario con la informacion
    data = request.get_json()

    # Eliminar el campo "seleccionado" de cada pregunta
    for pregunta in data.get("preguntas", []):
        pregunta.pop("seleccionado", None)

    # Añadir la fecha de creación
    data["creacion"] = datetime.datetime.now()

    # Acceder a la colección 'quizzes'
    coleccion_quizzes = mongo.db["quizzes"]

    # Insertar el documento en la colección
    coleccion_quizzes.insert_one(data)

    # Devolver respuesta con la URL a la que se debe redirigir
    return {'redirect': url_for('mostrar_quizzes')}


@app.route("/quizzes")
def mostrar_quizzes():
    # Pagina actual de resultados
    pagina = int(request.args.get('page', 1))

    # Numero de elementos por pagina
    elementos_por_pagina = 20

    # Conexion
    coleccion_quizzes = mongo.db["quizzes"]

    # Total de elementos
    total_elementos = coleccion_quizzes.count_documents({})

    # Cargar los quizzes ordenados por fecha de creación (descendente) con paginación
    quizzes = list(
        coleccion_quizzes.find()
        .sort("creacion", -1)  # Ordenar por la fecha de creación de manera descendente
        .skip((pagina - 1) * elementos_por_pagina)  # Saltar los elementos previos
        .limit(elementos_por_pagina)  # Limitar el número de elementos a mostrar
    )

    # Cargamos la informacion
    paginacion = render_pagination(pagina, elementos_por_pagina, total_elementos, 'mostrar_quizzes')

    return render_template("listar_quizzes.html", quizzes=quizzes,
                           pagination=paginacion, pagina=pagina)


@app.route("/jugar/<nombre_quiz>")
def jugar_quiz_personalizado(nombre_quiz: str):
    # Conexion
    coleccion_quizzes = mongo.db["quizzes"]

    # Buscar el quiz por nombre
    quiz = coleccion_quizzes.find_one({"_id": nombre_quiz})

    # Si no existe, lanzar error 404
    if quiz is None:
        abort(404)

    # Preparar las preguntas del quiz
    preguntas = {
        "preguntas": quiz.get("preguntas", [])
    }

    return render_template("juego.html", preguntas=preguntas, guardable=False)
