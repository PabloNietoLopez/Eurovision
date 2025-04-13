"""
Módulo de Python que contiene las rutas
"""
import datetime
from flask import current_app as app, render_template, redirect, url_for, flash, abort, request
from .formularios import GenerarQuizForm
from . import mongo
from .trivia import generar_n_preguntas_aleatoriamente
from .render_utils import render_pagination
from config import ConfiguracionFlask
from pymongo import MongoClient, DESCENDING
from app.trivia.operaciones_coleccion import OperacionesEurovision

# Crear cliente Mongo
client = MongoClient(ConfiguracionFlask.MONGO_URI)
db = client.get_default_database()
coleccion_festivales = db["festivales"]
operaciones = OperacionesEurovision(coleccion_festivales, [], [])

@app.route("/")
@app.route("/ediciones")
def mostrar_ediciones():
    pagina = int(request.args.get('page', 1))
    elementos_por_pagina = 5

    # Número total de ediciones
    total_elementos = coleccion_festivales.count_documents({})

    # Cargar solo los festivales de la página actual
    festivales = list(
        coleccion_festivales.find({}, {"_id": 0})
        .sort("anyo", -1)
        .skip((pagina - 1) * elementos_por_pagina)
        .limit(elementos_por_pagina)
    )

    # Generar la estructura de paginación
    paginacion = render_pagination(pagina, elementos_por_pagina, total_elementos, 'mostrar_ediciones')

    return render_template(
        "mostrar_ediciones.html",
        festivales=festivales,
        pagination=paginacion,
        pagina=pagina
    )


@app.route("/edicion/<int:anyo>")
def mostrar_festival(anyo: int):
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
    # Obtener lista de años y países desde la base de datos
    anyos = coleccion_festivales.distinct("anyo")
    anyos.sort(reverse=True)  # Ordenar los años de manera descendente
    paises = coleccion_festivales.distinct("pais")
    paises.sort()  # Ordenar los países de manera ascendente

    # Crear el formulario y pasar las listas de años y países
    form = GenerarQuizForm(anyos=anyos, paises=paises)

    # Si el formulario es válido
    if form.validate_on_submit():
        # Redirigir a 'jugar_quiz' con los parámetros seleccionados
        return redirect(url_for('jugar_quiz', anyos=form.seleccion_anyos.data, paises=form.seleccion_paises.data, nombre=form.nombre.data))

    # Si el formulario no es válido o es un GET, renderiza el formulario
    return render_template('crear_quiz.html', form=form)


@app.route("/pais/<id_pais>")
def mostrar_actuaciones_pais(id_pais: str):
    # Obtener la página actual desde los parámetros de la solicitud (por defecto 1)
    pagina = int(request.args.get('page', 1))
    elementos_por_pagina = 5  # Número de resultados por página

    # Filtrar las participaciones por país dentro de los concursantes
    participaciones = coleccion_festivales.find({"concursantes.id_pais": id_pais})

    # Obtener el total de participaciones para el país
    total_elementos = coleccion_festivales.count_documents({"concursantes.id_pais": id_pais})

    # Filtrar las participaciones de la página actual
    participaciones = list(
        participaciones.sort("anyo", -1)  # Ordenar por año de manera descendente
        .skip((pagina - 1) * elementos_por_pagina)  # Saltar los elementos previos
        .limit(elementos_por_pagina)  # Limitar el número de elementos
    )

    # Extraer la información de los concursantes para el país en la página actual
    participantes_filtrados = []
    for participacion in participaciones:
        for concursante in participacion['concursantes']:
            if concursante['id_pais'] == id_pais:
                participantes_filtrados.append({
                    'anyo': participacion['anyo'],
                    'pais_organizador': participacion['pais'],
                    'ciudad': participacion['ciudad'],
                    'artista': concursante['artista'],
                    'cancion': concursante['cancion'],
                    'resultado': concursante['resultado'],
                    'puntuacion': concursante['puntuacion'],
                    'url_youtube': concursante['url_youtube']
                })

    # Generar la paginación
    paginacion = render_pagination(pagina, elementos_por_pagina, total_elementos, 'mostrar_actuaciones_pais',
                                   id_pais=id_pais)

    # Si no se encuentran participaciones, devolver un error 404
    if not participantes_filtrados:
        abort(404)

    # Pasar los resultados al template
    return render_template("mostrar_actuaciones_pais.html", pais=id_pais, participaciones=participantes_filtrados,
                           pagination=paginacion, pagina=pagina)



@app.route("/upload_contest", methods=["POST"])
def guardar_concurso():
    # Obtener los datos del JSON que llega desde el frontend
    data = request.get_json()
    print(data)
    # Eliminar el campo "seleccionado" de cada pregunta
    for pregunta in data.get("preguntas", []):
        pregunta.pop("seleccionado", None)

    # Añadir la fecha de creación
    data["creacion"] = datetime.datetime.now()

    # Acceder a la colección 'quizzes'
    quizzes_collection = db["quizzes"]

    # Insertar el documento en la colección
    quizzes_collection.insert_one(data)

    # Devolver respuesta con la URL a la que se debe redirigir
    return {'redirect': url_for('mostrar_quizzes')}


@app.route("/quizzes")
def mostrar_quizzes():
    # Página actual
    pagina = int(request.args.get('page', 1))

    # Elementos por página
    elementos_por_pagina = 20

    # Colección de quizzes
    quizzes_collection = db["quizzes"]

    # Total de elementos
    total_elementos = quizzes_collection.count_documents({})

    # Cargar los quizzes ordenados por fecha de creación (descendente) con paginación
    quizzes_cursor = quizzes_collection.find().sort("creacion", DESCENDING).skip((pagina - 1) * elementos_por_pagina).limit(elementos_por_pagina)
    quizzes = list(quizzes_cursor)

    # Generar el componente de paginación
    paginacion = render_pagination(pagina, elementos_por_pagina, total_elementos, 'mostrar_quizzes')

    # Renderizar el template
    return render_template("listar_quizzes.html", quizzes=quizzes,
                           pagination=paginacion, pagina=pagina)

import json

@app.route("/jugar/<nombre_quiz>")
def jugar_quiz_personalizado(nombre_quiz: str):
    quizzes_collection = db["quizzes"]
    quiz = quizzes_collection.find_one({"_id": nombre_quiz})

    if quiz is None:
        abort(404)

    preguntas = quiz.get("preguntas", [])

    return render_template(
        "juego.html",
        preguntas=preguntas,
        guardable=False
    )

