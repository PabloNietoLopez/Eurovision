"""
Modulo para hacer cuestiones de trivia relacionadas con videos de Youtube. Creamos una clase TriviaVideo que extiende
a Trivia y almacena el id de reproduccion de video
"""

from abc import ABC, abstractmethod
from typing import List
from pathlib import Path

from.operaciones_coleccion import OperacionesEurovision
from .preguntas import Trivia


def extraer_id_url(url) -> str:
    """
    Para renderizar el juego, necesitamos extraer el id desde la url del video.
    Utilizamos expresiones regulares
    """
    try:
        return Path(url).name
    except:
        # Return id for Rick Roll
        return "dQw4w9WgXcQ"


class TriviaVideo(Trivia, ABC):
    """
    Clase abstracta que contiene los metodos que deben incorporar las preguntas asociadas a videos.
    """
    @property
    @abstractmethod
    def url(self) -> str:
        pass

    def to_dict(self):
        # Modifica el diccionario de Trivia con la url del video
        # y el tipo "video"
        super_dict = super().to_dict()
        super_dict["url"] = self.url
        # Extraemos el id de la URL
        super_dict["url_id"] = extraer_id_url(self.url)
        super_dict["tipo"] = "video"
        return super_dict


class PaisActuacion(TriviaVideo):
    """
    ¿Qué país representó esta canción?
    """

    def __init__(self, parametros: OperacionesEurovision):

        # Obtener una participación aleatoria
        participacion = parametros.participacion_aleatoria(1)[0]

        # Extraer datos relevantes
        self._respuesta = participacion["pais"]
        self._url = participacion["url_youtube"]

        # Generar opciones inválidas directamente aquí (otros países)
        pipeline = [
            {"$unwind": "$concursantes"},
            {"$match": {"concursantes.pais": {"$ne": self._respuesta}}},  # Excluye el país correcto
            {"$group": {"_id": "$concursantes.pais"}},  # Agrupamos por país
            {"$sample": {"size": 3}}  # Seleccionamos 3 países aleatorios
        ]

        result = list(parametros.agregacion(pipeline))
        self._opciones_invalidas = [r["_id"] for r in result]

    @property
    def url(self) -> str:
        return self._url

    @property
    def pregunta(self) -> str:
        return "¿A qué país representó esta canción?"

    @property
    def opciones_invalidas(self) -> List[str]:
        return self._opciones_invalidas

    @property
    def respuesta(self) -> str:
        return self._respuesta

    @property
    def puntuacion(self) -> float:
        return 3


class NombreCancion(TriviaVideo):
    """
    Pregunta: ¿Cuál es el título de esta canción?

    NOTA: Para dificultar la respuesta, se deben seleccionar canciones del mismo país.
    """

    def __init__(self, parametros: OperacionesEurovision):

        # Obtener una participación aleatoria
        participacion = parametros.participacion_aleatoria(1)[0]

        # Extraer datos relevantes
        self._respuesta = participacion["cancion"]
        self._url = participacion["url_youtube"]
        self._pais = participacion["pais"]

        # Generar opciones inválidas directamente aquí (otras canciones del mismo país)
        pipeline = [
            {"$unwind": "$concursantes"},  # Descomponemos la lista de concursantes
            {"$match": {"concursantes.pais": self._pais}},  # Filtramos por el país
            {"$match": {"concursantes.cancion": {"$ne": self._respuesta}}},  # Excluimos la canción correcta
            {"$group": {"_id": "$concursantes.cancion"}},  # Agrupamos por canción
            {"$sample": {"size": 3}}  # Seleccionamos 3 canciones aleatorias
        ]

        result = list(parametros.agregacion(pipeline))

        # Asignamos las opciones inválidas
        self._opciones_invalidas = [r["_id"] for r in result]

    @property
    def url(self) -> str:
        return self._url

    @property
    def pregunta(self) -> str:
        return "¿Cuál es el título de esta canción?"

    @property
    def opciones_invalidas(self) -> List[str]:
        return self._opciones_invalidas

    @property
    def respuesta(self) -> str:
        return self._respuesta

    @property
    def puntuacion(self) -> float:
        return 2


class InterpreteCancion(TriviaVideo):
    """
    Pregunta: ¿Quién interpretó esta canción?

    NOTA: Para dificultar la respuesta, se deben seleccionar intérpretes del mismo país.
    """

    def __init__(self, parametros: OperacionesEurovision):

        # Obtener una participación aleatoria
        participacion = parametros.participacion_aleatoria(1)[0]

        # Extraer datos relevantes
        self._respuesta = participacion["artista"]
        self._url = participacion["url_youtube"]
        self._pais = participacion["pais"]

        # Generar opciones inválidas directamente aquí (otros intérpretes del mismo país)
        pipeline = [
            {"$unwind": "$concursantes"},  # Descomponemos la lista de concursantes
            {"$match": {"concursantes.pais": self._pais}},  # Filtramos por el país
            {"$match": {"concursantes.artista": {"$ne": self._respuesta}}},  # Excluimos al intérprete correcto
            {"$group": {"_id": "$concursantes.artista"}},  # Agrupamos por intérprete
            {"$sample": {"size": 3}}  # Seleccionamos 3 intérpretes aleatorios
        ]

        result = list(parametros.agregacion(pipeline))

        # Asignamos las opciones inválidas
        self._opciones_invalidas = [r["_id"] for r in result]

    @property
    def url(self) -> str:
        return self._url

    @property
    def pregunta(self) -> str:
        return "¿Quién interpretó esta canción?"

    @property
    def opciones_invalidas(self) -> List[str]:
        return self._opciones_invalidas

    @property
    def respuesta(self) -> str:
        return self._respuesta

    @property
    def puntuacion(self) -> float:
        return 4