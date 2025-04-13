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
        self._respuesta = self.encontrar_respuesta(parametros._coleccion)
        self._opciones_invalidas = self.generar_opciones_invalidas(int(self._respuesta))

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

    def encontrar_respuesta (self, _coleccion) -> str:
        """
           Encuentra el primer año en que el país participó.
           Devuelve el año como string.
        """
        respuesta = _coleccion.find_one(
            {"concursantes.pais": self.pais},
            {"anyo": 1},
            sort=[("anyo", 1)]
        )
        return str(respuesta["anyo"])

    def generar_opciones_invalidas(self, correcto: int) -> List[str]:
        """
        Genera 3 años incorrectos que no sean el correcto.
        """
        opciones = set()
        while len(opciones) < 3:
            año = random.randint(1956, 2022)
            if año != correcto:
                opciones.add(str(año))
        return list(opciones)

class CancionPais(Trivia):
    """
    Pregunta de que pais es el interprete de una cancion, dada el titulo de la cancion
    """

    def __init__(self, parametros: OperacionesEurovision):
        self.parametros = parametros
        # Obtenemos una participación aleatoria
        participacion = parametros.participacion_aleatoria(1)[0]  # <- Corrección aquí
        # Extraer datos relevantes
        self._respuesta = participacion["pais"]
        self._cancion = participacion["cancion"]

        # Generar opciones inválidas
        self._opciones_invalidas = self.generar_opciones_invalidas(self._respuesta)

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

    def generar_opciones_invalidas(self, correcto: str) -> List[str]:
        """
        Genera 3 países incorrectos que no sean la respuesta correcta.
        """
        opciones = set()
        while len(opciones) < 3:
            paises = self.parametros._coleccion.distinct("concursantes.pais")
            pais = random.choice(paises)
            print(pais)
            if pais != correcto:
                opciones.add(pais)
        return list(opciones)

class MejorClasificacion(Trivia):
    """
    Pregunta: ¿Que cancion/pais obtuvo la mejor posicion en un anyo dado?

    Respuesta: las respuestas deben ser de la forma cancion/pais.

    IMPORTANTE: la solucion debe ser unica. Ademas, todos las opciones
    deben haber participado el mismo anyo.
    """
    def __init__(self, parametros: OperacionesEurovision):
        self.parametros = parametros

        # Seleccionar un año aleatorio entre los disponibles
        self._anyo = parametros.anyo_aleatorio(1)[0]

        # Obtener el documento del festival de ese año
        festival = parametros._coleccion.find_one({"anyo": self._anyo}, {"concursantes": 1})

        concursantes = festival["concursantes"]

        # Buscar el ganador (posición 1)
        ganador = next((c for c in concursantes if c["resultado"] == 1), None)

        self._respuesta = f"{ganador['cancion']} / {ganador['pais']}"

        # Generar 3 concursantes incorrectos del mismo año
        restantes = [
            c for c in concursantes
            if f"{c['cancion']} / {c['pais']}" != self._respuesta
        ]

        seleccionados = random.sample(restantes, 3)
        self._opciones_invalidas = [
            f"{c['cancion']} / {c['pais']}" for c in seleccionados
        ]

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
    Pregunta que pais ha tenido mejor media de resultados en un periodo determinado.

    IMPORTANTE: la solucion debe ser unica.
    """
    def __init__(self, parametros: OperacionesEurovision):
        self._anyo_inicial = None
        self._anyo_final = None
        self._opciones_invalidas = None
        self._respuesta = None

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
