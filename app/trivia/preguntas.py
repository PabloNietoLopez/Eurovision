"""
Modulo que contiene diferentes modelos de consulta para la seccion de "trivia".
"""
import random
from typing import List
from abc import ABC, abstractmethod
from .operaciones_coleccion import OperacionesEurovision


# Clases para encapsular las preguntas y respuestas generadas aleatoriamente
class Trivia(ABC):
    """
    Clase abstracta con los metodos que deben implementar todas las preguntas de trivia.
    """
    @abstractmethod
    def __init__(self, parametros: OperacionesEurovision):
        # Obligamos a que todos los constructores les pasen un objeto con los parametros aleatorios
        pass

    @property
    @abstractmethod
    def pregunta(self) -> str:
        """
        Pregunta que se debe mostrar
        """
        pass

    @property
    @abstractmethod
    def opciones_invalidas(self) -> List[str]:
        """
        Lista de opciones invalidas. Deben ser exactamente 3
        """
        pass

    @property
    @abstractmethod
    def respuesta(self) -> str:
        """
        Respuesta correcta
        """
        pass

    @property
    @abstractmethod
    def puntuacion(self) -> int:
        """
        Puntuacion asociada a la pregunta
        """
        pass

    def to_dict(self):
        # Sorteamos aleatoriamente las respuestas
        respuestas = [self.respuesta, *self.opciones_invalidas]
        random.shuffle(respuestas)

        # Funcion que genera la informacion que pasamos al script de trivia en el formato adecuado
        return {"pregunta": self.pregunta,
                "correcta": respuestas.index(self.respuesta),
                "respuestas": respuestas,
                "puntuacion": self.puntuacion,
                "tipo": "pregunta"}


class PrimerAnyoParticipacion(Trivia):
    """
    Pregunta que anyo fue el primero en el que participo un pais seleccionado aleatoriamente
    """

    def __init__(self, parametros: OperacionesEurovision):

        self.pais = parametros.paises_participantes_aleatorios(1)[0]

        respuesta = parametros._coleccion.find_one(
            {"concursantes.pais": self.pais},
            {"anyo": 1},
            sort=[("anyo", 1)]
        )
        self._respuesta = respuesta["anyo"]

        opciones_invalidas = [anio for anio in (parametros.anyos if parametros.anyos else range(1956, 2023)) if
                              anio != int(self._respuesta)]
        self._opciones_invalidas = random.sample(opciones_invalidas, 3)

    @property
    def pregunta(self) -> str:
        return f"¿En qué año participó por primera vez {self.pais}?"

    @property
    def opciones_invalidas(self) -> List[str]:
        return self._opciones_invalidas

    @property
    def respuesta(self) -> str:
        return self._respuesta

    @property
    def puntuacion(self) -> int:
        """
        Puntuacion asociada a la pregunta
        """
        return 2


class CancionPais(Trivia):
    """
    Pregunta de que pais es el interprete de una cancion, dada el titulo de la cancion
    """

    def __init__(self, parametros: OperacionesEurovision):

        participacion = parametros.participacion_aleatoria(1)[0]
        self._respuesta = participacion["pais"]
        self._cancion = participacion["cancion"]

        paises_invalidos = list(parametros._coleccion.distinct("concursantes.pais"))
        paises_invalidos.remove(self._respuesta)  # Elimina el país correcto de la lista
        self._opciones_invalidas = random.sample(paises_invalidos, 3)

    @property
    def pregunta(self) -> str:
        return f"¿De que país es el intérprete de la canción '{self._cancion}'?"

    @property
    def opciones_invalidas(self) -> List[str]:
        return self._opciones_invalidas

    @property
    def respuesta(self) -> str:
        return self._respuesta

    @property
    def puntuacion(self) -> int:
        """
        Puntuacion asociada a la pregunta
        """
        return 1

class MejorClasificacion(Trivia):
    """
    Pregunta: ¿Que cancion/pais obtuvo la mejor posicion en un anyo dado?

    Respuesta: las respuestas deben ser de la forma cancion/pais.

    IMPORTANTE: la solucion debe ser unica. Ademas, todos las opciones
    deben haber participado el mismo anyo.
    """
    def __init__(self, parametros: OperacionesEurovision):

        # Seleccionar un año aleatorio entre los disponibles
        self._anyo = parametros.anyo_aleatorio(1)[0]

        # Agregación en MongoDB
        pipeline = [
            {"$match": {"anyo": self._anyo}},
            {"$unwind": "$concursantes"},
            {"$sample": {"size": 4}},
            {"$sort": {"concursantes.resultado": 1}},  # Asegura que el mejor posicionado sea el primero
            {"$project": {
                "cancion": "$concursantes.cancion",
                "pais": "$concursantes.pais",
                "resultado": "$concursantes.resultado"
            }}
        ]

        # Ejecutamos la agregación
        resultado = list(parametros.agregacion(pipeline))

        # Tomamos el ganador del resultado de la agregación
        ganador = resultado[0]

        self._respuesta =  ganador['cancion'] + " / " + ganador['pais']

        restantes = [
            concursante['cancion'] + " / " + concursante['pais'] for concursante in resultado[1:] # Excluimos al primero (ganador)
        ]

        self._opciones_invalidas = restantes

    @property
    def pregunta(self) -> str:
        return f"¿Que canción/país obtuvo la mejor posición en {self._anyo}?"

    @property
    def opciones_invalidas(self) -> List[str]:
        return self._opciones_invalidas

    @property
    def respuesta(self) -> str:
        return self._respuesta

    @property
    def puntuacion(self) -> int:
        return 3


class MejorMediaPuntos(Trivia):
    """
    Pregunta qué país ha tenido mejor media de resultados en un periodo determinado.

    IMPORTANTE: la solución debe ser única.
    """

    def __init__(self, parametros: OperacionesEurovision):

        self._anyo_inicial = parametros.anyo_aleatorio(1)[0]
        cond_mayor = [{"$match": {"anyo": {"$gte": self._anyo_inicial}}}]
        self._anyo_final = parametros.anyo_aleatorio(1, condiciones_extras=cond_mayor)[0]

        print(self._anyo_inicial)
        print(self._anyo_final)
        # Agregación para obtener la media de puntuación por país
        pipeline = [
            {"$match": {"anyo": {"$gte": self._anyo_inicial, "$lte": self._anyo_final}}},
            {"$unwind": "$concursantes"},
            {"$group": {
                "_id": "$concursantes.pais",
                "media_puntuacion": {"$avg": "$concursantes.puntuacion"}
            }},
            {"$sort": {"media_puntuacion": -1}},
            {"$limit": 10}
        ]

        resultados = list(parametros.agregacion(pipeline))

        self._respuesta = resultados[0]["_id"]
        self._opciones_invalidas = [r["_id"] for r in resultados[1:4]]

    @property
    def pregunta(self) -> str:
        return f"¿Qué país quedó mejor posicionado de media entre los años {self._anyo_inicial} y {self._anyo_final}?"

    @property
    def opciones_invalidas(self) -> List[str]:
        return self._opciones_invalidas

    @property
    def respuesta(self) -> str:
        return self._respuesta

    @property
    def puntuacion(self) -> int:
        return 4
