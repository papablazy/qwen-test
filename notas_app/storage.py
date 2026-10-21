"""Capa de persistencia: guarda las notas en un archivo JSON."""

import json
import os
import sys
import tempfile
import time
from dataclasses import dataclass, asdict, field


def _app_data_dir() -> str:
    """Devuelve la carpeta de datos según el sistema operativo."""
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
        return os.path.join(base, "NotasPro")
    if sys.platform == "darwin":
        return os.path.join(os.path.expanduser("~/Library/Application Support"), "NotasPro")
    # Linux y otros
    xdg = os.environ.get("XDG_DATA_HOME", os.path.join(os.path.expanduser("~"), ".local/share"))
    return os.path.join(xdg, "notas-pro")


DB_DIR = _app_data_dir()
DB_FILE = os.path.join(DB_DIR, "notas.json")


@dataclass
class Nota:
    id: int
    titulo: str = ""
    contenido: str = ""
    fijada: bool = False
    creada: float = 0.0
    modificada: float = 0.0
    etiquetas: list = field(default_factory=list)

    def texto_busqueda(self) -> str:
        return f"{self.titulo}\n{self.contenido}\n{' '.join(self.etiquetas)}".lower()


class Almacen:
    """Acceso simple a la base de datos de notas (archivo JSON)."""

    def __init__(self, ruta: str = DB_FILE):
        self.ruta = ruta
        self.notas: list[Nota] = []
        self._next_id = 1
        self.cargar()

    # ---------- Persistencia ----------
    def cargar(self) -> None:
        try:
            with open(self.ruta, "r", encoding="utf-8") as f:
                datos = json.load(f)
            self.notas = [Nota(**d) for d in datos.get("notas", [])]
            self._next_id = datos.get("next_id", 1)
        except (FileNotFoundError, json.JSONDecodeError, TypeError):
            self.notas = []
            self._next_id = 1

    def guardar(self) -> None:
        os.makedirs(os.path.dirname(self.ruta), exist_ok=True)
        datos = {
            "version": 1,
            "next_id": self._next_id,
            "notas": [asdict(n) for n in self.notas],
        }
        # Escritura atómica para no perder datos si algo falla a mitad
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(self.ruta))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(datos, f, ensure_ascii=False, indent=2)
            os.replace(tmp, self.ruta)
        finally:
            if os.path.exists(tmp):
                try:
                    os.remove(tmp)
                except OSError:
                    pass

    # ---------- Operaciones CRUD ----------
    def crear(self, titulo: str = "Sin título", contenido: str = "") -> Nota:
        nota = Nota(id=self._next_id, titulo=titulo, contenido=contenido,
                    creada=time.time(), modificada=time.time())
        self._next_id += 1
        self.notas.append(nota)
        self.guardar()
        return nota

    def obtener(self, nota_id: int):
        for n in self.notas:
            if n.id == nota_id:
                return n
        return None

    def actualizar(self, nota: Nota) -> None:
        nota.modificada = time.time()
        self.guardar()

    def eliminar(self, nota_id: int) -> None:
        self.notas = [n for n in self.notas if n.id != nota_id]
        self.guardar()

    def lista(self, consulta: str = "") -> list:
        q = consulta.strip().lower()
        notas = list(self.notas)
        if q:
            notas = [n for n in notas if q in n.texto_busqueda()]
        # Fijadas primero, luego por fecha de modificación descendente
        notas.sort(key=lambda n: (not n.fijada, -n.modificada))
        return notas

    def todas(self) -> list:
        return list(self.notas)
