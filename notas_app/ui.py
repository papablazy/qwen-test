"""Interfaz gráfica de NotasPro (tkinter, sin dependencias externas)."""

import json
import os
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from storage import Almacen, DB_FILE
from tema import PALETAS

APP_NOMBRE = "NotasPro"
VERSION = "1.0"
CONFIG_FILE = os.path.join(os.path.dirname(DB_FILE), "config.json")

# ---------------------------------------------------------------------------
# Utilidades de fecha
# ---------------------------------------------------------------------------

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
         "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def fecha_legible(ts: float) -> str:
    """Fecha en estilo 'hoy', 'ayer' o '5 marzo 2026'."""
    if not ts:
        return ""
    dt = time.localtime(ts)
    hoy = time.localtime(time.time())
    if dt.tm_year == hoy.tm_year and dt.tm_yday == hoy.tm_yday:
        return f"hoy {dt.tm_hour:02d}:{dt.tm_min:02d}"
    ayer = time.localtime(time.time() - 86400)
    if dt.tm_year == ayer.tm_year and dt.tm_yday == ayer.tm_yday:
        return "ayer"
    if dt.tm_year == hoy.tm_year:
        return f"{dt.tm_mday} {MESES[dt.tm_mon - 1]}"
    return f"{dt.tm_mday} {MESES[dt.tm_mon - 1]} {dt.tm_year}"


def preview(texto: str, maximo: int = 90) -> str:
    t = " ".join(texto.split())
    if len(t) > maximo:
        return t[:maximo].rstrip() + "…"
    return t or "Sin contenido"


# ---------------------------------------------------------------------------
# Widgets personalizados
# ---------------------------------------------------------------------------

class Boton(tk.Canvas):
    """Botón redondeado dibujado en un Canvas (estética moderna)."""

    def __init__(self, master, texto, comando, color=None, color_texto=None,
                 ancho=110, alto=34, radio=10, fuente=(None, 10, "bold"), **kw):
        super().__init__(master, width=ancho, height=alto, highlightthickness=0,
                         bd=0, bg=master.cget("bg"), **kw)
        self._bg_forzado = master.cget("bg")
        self.comando = comando
        self.ancho, self.alto, self.radio = ancho, alto, radio
        self._color = color or "#2f6fed"
        self._color_hover = self._aclarar(self._color, 0.12)
        self._color_texto = color_texto or "#ffffff"
        self._texto = texto
        self._fuente = fuente
        self._dibujar(self._color)
        self.bind("<Enter>", lambda e: self._dibujar(self._color_hover))
        self.bind("<Leave>", lambda e: self._dibujar(self._color))
        self.bind("<Button-1>", self._click)

    @staticmethod
    def _aclarar(hexcolor: str, frac: float) -> str:
        c = hexcolor.lstrip("#")
        r, g, b = (int(c[i:i + 2], 16) for i in (0, 2, 4))
        r = min(255, int(r + (255 - r) * frac))
        g = min(255, int(g + (255 - g) * frac))
        b = min(255, int(b + (255 - b) * frac))
        return f"{r:02x}{g:02x}{b:02x}"

    def _redondo(self, x1, y1, x2, y2, r, **kw):
        pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
               x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
        self.create_polygon(pts, smooth=True, **kw)

    def _dibujar(self, color):
        self.delete("all")
        self._redondo(1, 1, self.ancho - 1, self.alto - 1, self.radio,
                      fill=color, outline=color)
        self.create_text(self.ancho / 2, self.alto / 2, text=self._texto,
                         fill=self._color_texto, font=self._fuente)

    def _click(self, _evento):
        if self.comando:
            self.comando()

    def reconfigurar(self, color=None, color_texto=None, texto=None):
        if color:
            self._color = color
            self._color_hover = self._aclarar(color, 0.12)
        if color_texto:
            self._color_texto = color_texto
        if texto is not None:
            self._texto = texto
        self._dibujar(self._color)


class EntradaBusqueda(tk.Frame):
    """Campo de búsqueda con placeholder y acción por Enter."""

    def __init__(self, master, paleta, al_buscar, ancho=32):
        super().__init__(master, bg=paleta.cabecera)
        self.paleta = paleta
        self.al_buscar = al_buscar
        self.var = tk.StringVar()
        self.entry = tk.Entry(self, textvariable=self.var, width=ancho,
                              bg=paleta.panel, fg=paleta.texto,
                              insertbackground=paleta.texto, relief="flat",
                              font=("TkDefaultFont", 10))
        self._placeholder("🔍  Buscar notas…")
        self.entry.pack(fill="both", expand=True, padx=2, pady=2)
        self.entry.bind("<FocusIn>", self._enfoque)
        self.entry.bind("<FocusOut>", self._desenfoque)
        self.entry.bind("<Return>", lambda e: self.al_buscar(self.consulta()))
        # Búsqueda en vivo
        self.var.trace_add("write", lambda *_: self._vivo())
        self._trasera = None

    def _placeholder(self, texto):
        self._ph = True
        self.var.set(texto)
        self.entry.config(fg=self.paleta.texto_suave)

    def _enfoque(self, _e):
        if getattr(self, "_ph", False):
            self._ph = False
            self.var.set("")
            self.entry.config(fg=self.paleta.texto)

    def _desenfoque(self, _e):
        if not self.var.get().strip():
            self._placeholder("🔍  Buscar notas…")
            self.al_buscar("")

    def consulta(self) -> str:
        return "" if getattr(self, "_ph", False) else self.var.get().strip()

    def _vivo(self):
        if getattr(self, "_after_id", None):
            self.after_cancel(self._after_id)
        self._after_id = self.after(250, lambda: self.al_buscar(self.consulta()))

    def aplicar_paleta(self, paleta):
        self.paleta = paleta
        self.config(bg=paleta.cabecera)
        self.entry.config(bg=paleta.panel, fg=paleta.texto,
                          insertbackground=paleta.texto)
        if getattr(self, "_ph", False):
            self.entry.config(fg=paleta.texto_suave)


class ElementoNota(tk.Frame):
    """Fila de la lista de notas."""

    def __init__(self, master, nota, paleta, seleccionada, al_clic, al_fijar, al_borrar):
        super().__init__(master, cursor="hand2")
        self._bg_forzado = None  # se calcula con _fondo()
        self._paleta_ref = paleta
        self.nota = nota
        self.paleta = paleta
        self.seleccionada = seleccionada
        self._repintar()

        titulo = ("📌 " if nota.fijada else "") + (nota.titulo or "Sin título")
        lbl_t = tk.Label(self, text=titulo, anchor="w", font=("TkDefaultFont", 11, "bold"),
                         bg=self._fondo(), fg=paleta.texto)
        lbl_t.pack(fill="x", padx=12, pady=(8, 0))
        lbl_p = tk.Label(self, text=preview(nota.contenido), anchor="w", justify="left",
                         wraplength=250, font=("TkDefaultFont", 9),
                         bg=self._fondo(), fg=paleta.texto_suave)
        lbl_p.pack(fill="x", padx=12)
        lbl_f = tk.Label(self, text=fecha_legible(nota.modificada), anchor="w",
                         font=("TkDefaultFont", 8), bg=self._fondo(), fg=paleta.texto_suave)
        lbl_f.pack(fill="x", padx=12, pady=(0, 8))

        self._widgets = (lbl_t, lbl_p, lbl_f)
        for w in (self, lbl_t, lbl_p, lbl_f):
            w.bind("<Button-1>", lambda e: al_clic(nota.id))
            w.bind("<Double-Button-3>", lambda e: al_fijar(nota.id))
        self.bind("<Button-3>", lambda e: self._menu(e, al_fijar, al_borrar))

    def _fondo(self):
        return self.paleta.tarjeta if self.seleccionada else self.paleta.panel

    def _menu(self, evento, al_fijar, al_borrar):
        m = tk.Menu(self, tearoff=0)
        fijar_txt = "Quitar de fijadas" if self.nota.fijada else "Fijar nota"
        m.add_command(label=fijar_txt, command=lambda: al_fijar(self.nota.id))
        m.add_command(label="Eliminar", foreground=self.paleta.peligro,
                      command=lambda: al_borrar(self.nota.id))
        m.tk_popup(evento.x_root, evento.y_root)

    def seleccionar(self, activa: bool):
        self.seleccionada = activa
        self._repintar()

    def _repintar(self):
        fondo = self._fondo()
        self.config(bg=fondo)
        for w in getattr(self, "_widgets", ()):
            w.config(bg=fondo)


# ---------------------------------------------------------------------------
# Ventana principal
# ---------------------------------------------------------------------------

class AppTK:
    def __init__(self, raiz: tk.Tk):
        self.raiz = raiz
        self.almacen = Almacen()
        self.conf = self._cargar_conf()
        self.clave_tema = self.conf.get("tema", "claro")
        self.paleta = PALETAS[self.clave_tema]
        self.nota_activa = None
        self.consulta = ""
        self._autosave_id = None

        raiz.title(f"{APP_NOMBRE} {VERSION}")
        raiz.geometry("1024x640")
        raiz.minsize(860, 520)
        raiz.configure(bg=self.paleta.fondo)

        self._construir_menu()
        self._construir()
        self._aplicar_tema()
        self._refrescar_lista()
        self._atajos()

    # ---------------- configuración ----------------
    def _cargar_conf(self):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _guardar_conf(self):
        try:
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({"tema": self.clave_tema}, f)
        except OSError:
            pass

    def _construir_menu(self):
        menu = tk.Menu(self.raiz)
        archivo = tk.Menu(menu, tearoff=0)
        archivo.add_command(label="Nueva nota", accelerator="Ctrl+N", command=self.nueva_nota)
        archivo.add_command(label="Duplicar nota", accelerator="Ctrl+D", command=self.duplicar_activa)
        archivo.add_separator()
        archivo.add_command(label="Exportar a Markdown…", command=self.exportar_markdown)
        archivo.add_separator()
        archivo.add_command(label="Salir", command=self.raiz.destroy)
        menu.add_cascade(label="Archivo", underline=0, menu=archivo)
        ayuda = tk.Menu(menu, tearoff=0)
        ayuda.add_command(label="Atajos de teclado", command=self._mostrar_atajos)
        ayuda.add_command(label="Acerca de NotasPro", command=self._acerca_de)
        menu.add_cascade(label="Ayuda", underline=0, menu=ayuda)
        self.raiz.config(menu=menu)

    def _mostrar_atajos(self):
        messagebox.showinfo(
            APP_NOMBRE,
            "Ctrl+N  Nueva nota\n"
            "Ctrl+D  Duplicar la nota actual\n"
            "Ctrl+F  Buscar\n"
            "Ctrl+G  Negrita (markdown)\n"
            "Ctrl+I  Cursiva (markdown)\n"
            "Esc     Limpiar la búsqueda\n"
            "Clic derecho en una nota: fijar / eliminar",
            parent=self.raiz)

    def _acerca_de(self):
        messagebox.showinfo(
            APP_NOMBRE,
            f"{APP_NOMBRE} {VERSION}\n\n"
            "Editor de notas para escritorio, rápido y sin conexión.\n"
            "Tus notas se guardan automáticamente en:\n"
            f"{DB_FILE}",
            parent=self.raiz)

    # ---------------- construcción ----------------
    def _construir(self):
        p = self.paleta

        # ---- Cabecera ----
        cab = tk.Frame(self.raiz, bg=p.cabecera, height=56)
        cab._bg_forzado = p.cabecera
        cab.pack(fill="x", side="top")
        cab.pack_propagate(False)
        tk.Label(cab, text="✎  NotasPro", font=("TkDefaultFont", 15, "bold"),
                 bg=p.cabecera, fg=p.acento).pack(side="left", padx=16)

        self.boton_nueva = Boton(cab, "＋ Nueva nota", self.nueva_nota,
                                 color=p.acento, ancho=120, alto=32)
        self.boton_nueva.pack(side="right", padx=(4, 14), pady=10)

        self.boton_tema = Boton(cab, "", self.alternar_tema, color=p.panel,
                                color_texto=p.texto, ancho=100, alto=32)
        self.boton_tema.pack(side="right", padx=4, pady=10)

        self.boton_exportar = Boton(cab, "⭳ Exportar", self.exportar_markdown,
                                     color=p.panel, color_texto=p.texto, ancho=100, alto=32)
        self.boton_exportar.pack(side="right", padx=4, pady=10)

        self.busqueda = EntradaBusqueda(cab, p, self._buscar)
        self.busqueda.pack(side="right", padx=10, pady=12)

        # ---- Cuerpo: panel izquierdo (lista) + editor ----
        cuerpo = tk.Frame(self.raiz, bg=p.fondo)
        cuerpo._bg_forzado = p.fondo
        cuerpo.pack(fill="both", expand=True)

        izq = tk.Frame(cuerpo, bg=p.panel, width=300)
        izq._bg_forzado = p.panel
        izq.pack(side="left", fill="y")
        izq.pack_propagate(False)

        tk.Label(izq, text="Mis notas", font=("TkDefaultFont", 12, "bold"),
                 bg=p.panel, fg=p.texto).pack(anchor="w", padx=14, pady=(12, 4))
        self.lbl_conteo = tk.Label(izq, text="", font=("TkDefaultFont", 9),
                                   bg=p.panel, fg=p.texto_suave)
        self.lbl_conteo.pack(anchor="w", padx=14)

        contenedor = tk.Frame(izq, bg=p.panel)
        contenedor._bg_forzado = p.panel
        contenedor.pack(fill="both", expand=True, pady=6)
        self.canvas_lista = tk.Canvas(contenedor, bg=p.panel, highlightthickness=0, bd=0)
        scroll = ttk.Scrollbar(contenedor, orient="vertical", command=self.canvas_lista.yview)
        self.frame_listaN = tk.Frame(self.canvas_lista, bg=p.panel)
        self._window_id = self.canvas_lista.create_window(
            (0, 0), window=self.frame_listaN, anchor="nw")
        self.canvas_lista.configure(yscrollcommand=scroll.set)
        self.canvas_lista.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.frame_listaN.bind(
            "<Configure>",
            lambda e: self.canvas_lista.configure(scrollregion=self.canvas_lista.bbox("all")))
        self.canvas_lista.bind(
            "<Configure>",
            lambda e: self.canvas_lista.itemconfig(self._window_id, width=e.width))
        self._unir_rueda(self.canvas_lista, self.frame_listaN)

        # ---- Editor ----
        der = tk.Frame(cuerpo, bg=p.fondo)
        der._bg_forzado = p.fondo
        der.pack(side="left", fill="both", expand=True)

        self.zona_vacia = tk.Frame(der, bg=p.fondo)
        self.zona_vacia._bg_forzado = p.fondo
        tk.Label(self.zona_vacia, text="🗒", font=("TkDefaultFont", 48),
                 bg=p.fondo, fg=p.texto_suave).pack(pady=(90, 10))
        tk.Label(self.zona_vacia,
                 text="Selecciona una nota de la izquierda\no crea una nueva con el botón «＋ Nueva nota»",
                 font=("TkDefaultFont", 12), bg=p.fondo, fg=p.texto_suave,
                 justify="center").pack()
        self.btn_vacia = Boton(self.zona_vacia, "＋ Crear mi primera nota",
                               self.nueva_nota, color=p.acento, ancho=210, alto=40)
        self.btn_vacia.pack(pady=24)

        self.zona_editor = tk.Frame(der, bg=p.fondo)
        self.zona_editor._bg_forzado = p.fondo

        barra_tools = tk.Frame(self.zona_editor, bg=p.fondo)
        barra_tools._bg_forzado = p.fondo
        barra_tools.pack(fill="x", padx=18, pady=(14, 2))
        self.botones_tools = []
        for txt, fn in (("B", self._md_negrita), ("I", self._md_cursiva),
                        ("≡ Lista", self._md_lista), ("–––", self._md_separador)):
            b = tk.Button(barra_tools, text=txt, command=fn, relief="flat",
                          bg=p.panel, fg=p.texto, activebackground=p.tarjeta,
                          font=("TkDefaultFont", 10, "bold"), padx=8, cursor="hand2")
            b.pack(side="left", padx=2)
            self.botones_tools.append(b)

        tk.Label(barra_tools, text="Ctrl+G: negrita · Ctrl+I: cursiva",
                 font=("TkDefaultFont", 8), bg=p.fondo, fg=p.texto_suave
                 ).pack(side="right")

        self.ent_titulo = tk.Entry(self.zona_editor, font=("TkDefaultFont", 16, "bold"),
                                   relief="flat", bg=p.fondo, fg=p.texto,
                                   insertbackground=p.texto)
        self.ent_titulo.pack(fill="x", padx=18, pady=(8, 2))
        self.ent_titulo.bind("<KeyRelease>", lambda e: self._programar_guardado())

        sep = tk.Frame(self.zona_editor, bg=p.borde, height=1)
        sep._bg_forzado = p.borde
        sep.pack(fill="x", padx=18)

        cont_txt = tk.Frame(self.zona_editor, bg=p.fondo)
        cont_txt._bg_forzado = p.fondo
        cont_txt.pack(fill="both", expand=True, padx=18, pady=(6, 4))
        self.txt_contenido = tk.Text(cont_txt, wrap="word", relief="flat",
                                     bg=p.entrada_fondo, fg=p.texto,
                                     insertbackground=p.texto, font=("TkDefaultFont", 12),
                                     padx=12, pady=10, undo=True, autoseparators=True,
                                     maxundo=-1000)
        scroll_txt = ttk.Scrollbar(cont_txt, orient="vertical", command=self.txt_contenido.yview)
        self.txt_contenido.configure(yscrollcommand=scroll_txt.set)
        self.txt_contenido.pack(side="left", fill="both", expand=True)
        scroll_txt.pack(side="right", fill="y")
        self.txt_contenido.bind("<<Modified>>", self._modificado)
        self.txt_contenido.tag_configure("grande", font=("TkDefaultFont", 15, "bold"))

        pie = tk.Frame(self.zona_editor, bg=p.fondo)
        pie._bg_forzado = p.fondo
        pie.pack(fill="x", padx=18, pady=(2, 12))
        self.lbl_info = tk.Label(pie, text="", font=("TkDefaultFont", 9),
                                 bg=p.fondo, fg=p.texto_suave)
        self.lbl_info.pack(side="left")
        self.boton_fijar = Boton(pie, "📌 Fijar", self.alternar_fijar,
                                 color=p.panel, color_texto=p.texto, ancho=100, alto=30)
        self.boton_fijar.pack(side="right", padx=(6, 0))
        self.boton_borrar = Boton(pie, "🗑 Eliminar", self.borrar_activa,
                                  color=p.peligro, ancho=110, alto=30)
        self.boton_borrar.pack(side="right")

        # ---- Barra de estado ----
        self.barra_estado = tk.Label(self.raiz, text="Listo", anchor="w",
                                     font=("TkDefaultFont", 9), bg=p.cabecera,
                                     fg=p.texto_suave, padx=12, pady=3)
        self.barra_estado.pack(fill="x", side="bottom")

    def _unir_rueda(self, *widgets):
        def rueda(e):
            delta = -1 if e.delta > 0 else 1
            self.canvas_lista.yview_scroll(delta, "units")
        for w in widgets:
            w.bind_all("<MouseWheel>", rueda)          # Windows/mac
            w.bind_all("<Button-4>", lambda e: self.canvas_lista.yview_scroll(-1, "units"))
            w.bind_all("<Button-5>", lambda e: self.canvas_lista.yview_scroll(1, "units"))

    # ---------------- atajos ----------------
    def _atajos(self):
        r = self.raiz
        r.bind("<Control-n>", lambda e: self.nueva_nota())
        r.bind("<Control-f>", lambda e: (self.busqueda.entry.focus_set(), "break")[1])
        r.bind("<Control-g>", lambda e: self._md_negrita())
        r.bind("<Control-i>", lambda e: self._md_cursiva())
        r.bind("<Control-d>", lambda e: self.duplicar_activa())
        r.bind("<Escape>", lambda e: self._limpiar_busqueda())

    # ---------------- temas ----------------
    def alternar_tema(self):
        self.clave_tema = "oscuro" if self.clave_tema == "claro" else "claro"
        self.paleta = PALETAS[self.clave_tema]
        self._guardar_conf()
        self._aplicar_tema()
        self._refrescar_lista()
        self._estado(f"Tema {self.paleta.nombre.lower()} activado")

    def _aplicar_tema(self):
        p = self.paleta
        r = self.raiz
        r.configure(bg=p.fondo)
        # Recorrer todos los frames/labels para repintar
        self._pintar_arbol(r)
        self.boton_tema.reconfigurar(color=p.panel, color_texto=p.texto,
                                     texto="☾ Oscuro" if p is PALETAS["claro"] else "☀ Claro")
        self.boton_nueva.reconfigurar(color=p.acento)
        self.busqueda.aplicar_paleta(p)
        for b in self.botones_tools:
            b.config(bg=p.panel, fg=p.texto, activebackground=p.tarjeta)
        self.ent_titulo.config(bg=p.fondo, fg=p.texto, insertbackground=p.texto)
        self.txt_contenido.config(bg=p.entrada_fondo, fg=p.texto, insertbackground=p.texto)
        self.barra_estado.config(bg=p.cabecera, fg=p.texto_suave)
        self.btn_vacia.reconfigurar(color=p.acento)
        self.boton_exportar.reconfigurar(color=p.panel, color_texto=p.texto)
        self.boton_fijar.reconfigurar(color=p.panel, color_texto=p.texto)
        self.boton_borrar.reconfigurar(color=p.peligro)

    def _pintar_arbol(self, w):
        p = self.paleta
        try:
            if hasattr(w, "_bg_forzado"):
                fondo = w._bg_forzado if w._bg_forzado else getattr(w, "_fondo", lambda: p.panel)()
                w.configure(bg=fondo)
            elif w.winfo_class() == "Frame":
                w.configure(bg=p.fondo)
        except tk.TclError:
            pass
        for hijo in w.winfo_children():
            self._pintar_arbol(hijo)

    # ---------------- lista ----------------
    def _buscar(self, q):
        self.consulta = q
        self._refrescar_lista()

    def _limpiar_busqueda(self):
        self.busqueda.var.set("")
        self._buscar("")

    def _refrescar_lista(self):
        for h in self.frame_listaN.winfo_children():
            h.destroy()
        notas = self.almacen.lista(self.consulta)
        p = self.paleta
        for n in notas:
            sel = self.nota_activa is not None and n.id == self.nota_activa.id
            ElementoNota(self.frame_listaN, n, p, sel,
                         self.abrir_nota, self.alternar_fijar_id, self.borrar_id)
        total = len(self.almacen.todas())
        if self.consulta:
            self.lbl_conteo.config(text=f"{len(notas)} de {total} notas · «{self.consulta}»")
        else:
            self.lbl_conteo.config(text=f"{total} nota{'s' if total != 1 else ''}")
        if not notas:
            vacio = "Sin resultados" if self.consulta else "Aún no hay notas"
            tk.Label(self.frame_listaN, text=vacio, bg=p.panel, fg=p.texto_suave,
                     font=("TkDefaultFont", 10, "italic")).pack(pady=24)

    # ---------------- acciones ----------------
    def nueva_nota(self):
        nota = self.almacen.crear()
        self._refrescar_lista()
        self.abrir_nota(nota.id)
        # El título "Sin título" es solo un marcador: se selecciona para reemplazarlo al escribir
        self.ent_titulo.select_range(0, "end")
        self.ent_titulo.icursor("end")
        self.ent_titulo.focus_set()
        self._estado("Nota nueva creada")

    def abrir_nota(self, nota_id):
        self._guardar_activa(silencioso=True)
        nota = self.almacen.obtener(nota_id)
        if nota is None:
            return
        self.nota_activa = nota
        self.zona_vacia.pack_forget()
        self.zona_editor.pack(fill="both", expand=True)
        self.ent_titulo.delete(0, "end")
        self.ent_titulo.insert(0, nota.titulo)
        self.txt_contenido.edit_reset()
        self.txt_contenido.delete("1.0", "end")
        self.txt_contenido.insert("1.0", nota.contenido)
        self.txt_contenido.edit_modified(False)
        self._marcar_md()
        self._actualizar_boton_fijar()
        self._actualizar_info()
        self._refrescar_lista()

    def duplicar_activa(self):
        if not self.nota_activa:
            return
        self._guardar_activa(silencioso=True)
        copia = self.almacen.crear(self.nota_activa.titulo + " (copia)",
                                   self.nota_activa.contenido)
        self._refrescar_lista()
        self.abrir_nota(copia.id)
        self._estado("Nota duplicada")

    def alternar_fijar(self):
        if self.nota_activa:
            self.nota_activa.fijada = not self.nota_activa.fijada
            self.almacen.guardar()
            self._actualizar_boton_fijar()
            self._refrescar_lista()

    def alternar_fijar_id(self, nota_id):
        nota = self.almacen.obtener(nota_id)
        if nota:
            nota.fijada = not nota.fijada
            self.almacen.guardar()
            if self.nota_activa and self.nota_activa.id == nota_id:
                self._actualizar_boton_fijar()
            self._refrescar_lista()

    def _actualizar_boton_fijar(self):
        if self.nota_activa:
            txt = "📌 Quitar fijado" if self.nota_activa.fijada else "📌 Fijar"
            self.boton_fijar.reconfigurar(texto=txt)

    def borrar_activa(self):
        if self.nota_activa:
            self.borrar_id(self.nota_activa.id)

    def borrar_id(self, nota_id):
        nota = self.almacen.obtener(nota_id)
        if nota is None:
            return
        nombre = nota.titulo or "Sin título"
        if not messagebox.askyesno(APP_NOMBRE,
                                   f"¿Eliminar la nota «{nombre}»?\nEsta acción no se puede deshacer.",
                                   parent=self.raiz):
            return
        era_activa = self.nota_activa and self.nota_activa.id == nota_id
        self.almacen.eliminar(nota_id)
        if era_activa:
            self.nota_activa = None
            self.zona_editor.pack_forget()
            self.zona_vacia.pack(fill="both", expand=True)
        self._refrescar_lista()
        self._estado("Nota eliminada")

    # ---------------- guardado ----------------
    def _modificado(self, _e=None):
        if self.txt_contenido.edit_modified():
            self._programar_guardado()

    def _programar_guardado(self):
        if self._autosave_id:
            self.raiz.after_cancel(self._autosave_id)
        self._autosave_id = self.raiz.after(700, self._autosave)

    def _autosave(self):
        self._autosave_id = None
        self._guardar_activa()
        self._actualizar_info()

    def _guardar_activa(self, silencioso=False):
        if not self.nota_activa:
            return
        titulo = self.ent_titulo.get().strip() or "Sin título"
        # Si el usuario no tocó el título pre-seleccionado, queda "Sin título"
        contenido = self.txt_contenido.get("1.0", "end-1c")
        if titulo == self.nota_activa.titulo and contenido == self.nota_activa.contenido:
            return
        self.nota_activa.titulo = titulo
        self.nota_activa.contenido = contenido
        self.almacen.actualizar(self.nota_activa)
        self._refrescar_lista()
        if not silencioso:
            self._estado(f"Guardado automáticamente · {time.strftime('%H:%M:%S')}")

    def _actualizar_info(self):
        if not self.nota_activa:
            return
        texto = self.txt_contenido.get("1.0", "end-1c")
        palabras = len([x for x in texto.split() if x])
        try:
            c = self.txt_contenido.count("1.0", "end-1c", "displaylines")
            lineas = int(c[0]) if isinstance(c, (tuple, list)) and c else 0
        except tk.TclError:
            lineas = texto.count("\n") + 1
        self.lbl_info.config(
            text=f"{palabras} palabras · {len(texto)} caracteres · ~{lineas} líneas · "
                 f"Creada: {fecha_legible(self.nota_activa.creada)}")

    # ---------------- markdown básico ----------------
    def _md_negrita(self):
        self._md_envolver("**")

    def _md_cursiva(self):
        self._md_envolver("*")

    def _md_envolver(self, marca):
        try:
            ini = self.txt_contenido.index("sel.first")
            fin = self.txt_contenido.index("sel.last")
        except tk.TclError:
            ini = fin = self.txt_contenido.index("insert")
        texto = self.txt_contenido.get(ini, fin)
        self.txt_contenido.delete(ini, fin)
        self.txt_contenido.insert(ini, f"{marca}{texto}{marca}")
        if ini == fin:
            self.txt_contenido.mark_set("insert", f"{ini}+{len(marca)}c")
        self._programar_guardado()

    def _md_lista(self):
        pos = self.txt_contenido.index("insert").split(".")[0]
        linea = self.txt_contenido.get(f"{pos}.0", f"{pos}.end")
        self.txt_contenido.delete(f"{pos}.0", f"{pos}.end")
        self.txt_contenido.insert(f"{pos}.0", linea if linea.startswith("- ") else "- " + linea)
        self._programar_guardado()

    def _md_separador(self):
        self.txt_contenido.insert("insert", "\n---\n")
        self._programar_guardado()

    def _marcar_md(self):
        """Resalta títulos markdown (#) en el editor."""
        p = self.paleta
        self.txt_contenido.tag_remove("grande", "1.0", "end")
        idx = "1.0"
        while True:
            idx = self.txt_contenido.search("# ", idx, "end", regexp=False)
            if not idx:
                break
            if idx.endswith(".0"):
                self.txt_contenido.tag_add("grande", idx, f"{idx} lineend")
            idx = f"{idx}+1c"

    # ---------------- exportar ----------------
    def exportar_markdown(self):
        if not self.nota_activa:
            messagebox.showinfo(APP_NOMBRE, "Abre primero una nota para exportarla.",
                                parent=self.raiz)
            return
        self._guardar_activa(silencioso=True)
        ruta = filedialog.asksaveasfilename(
            parent=self.raiz, defaultextension=".md",
            filetypes=[("Markdown", "*.md"), ("Texto", "*.txt")],
            initialfile=(self.nota_activa.titulo or "nota") + ".md")
        if not ruta:
            return
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(f"# {self.nota_activa.titulo}\n\n{self.nota_activa.contenido}\n")
        self._estado(f"Exportada a {os.path.basename(ruta)}")

    # ---------------- varios ----------------
    def _estado(self, mensaje):
        self.barra_estado.config(text=mensaje)


def ejecutar(raiz: tk.Tk) -> AppTK:
    return AppTK(raiz)
