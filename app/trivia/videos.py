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

        # Generar opciones inválidas (otros países)
        self._opciones_invalidas = self.generar_opciones_invalidas(self._respuesta, parametros)

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

    def generar_opciones_invalidas(self, correcto: str, parametros: OperacionesEurovision) -> List[str]:
        """
        Genera 3 países incorrectos que no sean la respuesta correcta.
        Utiliza el método de agregación.
        """
        pipeline = [
            {"$unwind": "$concursantes"},
            {"$match": {"concursantes.pais": {"$ne": correcto}}},
            {"$group": {"_id": "$concursantes.pais"}},
            {"$sample": {"size": 3}}
        ]

        result = list(parametros.agregacion(pipeline))

        return [r["_id"] for r in result]


class NombreCancion(TriviaVideo):
    """
    Pregunta: ¿Cuál es el título de esta canción?

    NOTA: Para dificultar la respuesta, se deben seleccionar canciones del mismo país.
    """

    def __init__(self, parametros: OperacionesEurovision):

        # Obtener una participación aleatoria
        participacion = parametros.participacion_aleatoria(1)[0]  # Asumiendo que devuelve un diccionario

        # Extraer datos relevantes
        self._respuesta = participacion["cancion"]
        self._url = participacion["url_youtube"]
        self._pais = participacion["pais"]

        # Generar opciones inválidas (otras canciones del mismo país)
        self._opciones_invalidas = self.generar_opciones_invalidas(self._respuesta, self._pais, parametros)

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

    def generar_opciones_invalidas(self, correcto: str, pais: str, parametros: OperacionesEurovision) -> List[str]:
        """
        Genera 3 canciones incorrectas que provengan del mismo país que la canción correcta.
        """
        # Creamos el pipeline de agregación para seleccionar canciones del mismo país
        pipeline = [
            {"$unwind": "$concursantes"},  # Descomponemos la lista de concursantes
            {"$match": {"concursantes.pais": pais}},  # Filtramos por el país
            {"$match": {"concursantes.cancion": {"$ne": correcto}}},  # Excluimos la canción correcta
            {"$group": {"_id": "$concursantes.cancion"}},  # Agrupamos por canción
            {"$sample": {"size": 3}}  # Seleccionamos 3 canciones aleatorias
        ]

        result = list(parametros.agregacion(pipeline))

        # Retornamos las canciones seleccionadas como opciones inválidas
        return [r["_id"] for r in result]

class InterpreteCancion(TriviaVideo):
    """
    Pregunta: ¿Quién interpretó esta canción?

    NOTA: Para dificultar la respuesta, se deben seleccionar intérpretes del mismo país.
    """

    def __init__(self, parametros: OperacionesEurovision):
        # Obtener una participación aleatoria
        participacion = parametros.participacion_aleatoria(1)[0]  # Asumiendo que devuelve un diccionario

        # Extraer datos relevantes
        self._respuesta = participacion["artista"]
        self._url = participacion["url_youtube"]
        self._pais = participacion["pais"]

        # Generar opciones inválidas (otros intérpretes del mismo país)
        self._opciones_invalidas = self.generar_opciones_invalidas(self._respuesta, self._pais, parametros)

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

    def generar_opciones_invalidas(self, correcto: str, pais: str, parametros: OperacionesEurovision) -> List[str]:
        """
        Genera 3 intérpretes incorrectos que provengan del mismo país que el intérprete correcto.
        """
        # Creamos el pipeline de agregación para seleccionar intérpretes del mismo país
        pipeline = [
            {"$unwind": "$concursantes"},  # Descomponemos la lista de concursantes
            {"$match": {"concursantes.pais": pais}},  # Filtramos por el país
            {"$match": {"concursantes.artista": {"$ne": correcto}}},  # Excluimos al intérprete correcto
            {"$group": {"_id": "$concursantes.artista"}},  # Agrupamos por intérprete
            {"$sample": {"size": 3}}  # Seleccionamos 3 intérpretes aleatorios
        ]

        result = list(parametros.agregacion(pipeline))

        # Retornamos los intérpretes seleccionados como opciones inválidas
        return [r["_id"] for r in result]
