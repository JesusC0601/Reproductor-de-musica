import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pygame

class NodoCancion:
    def __init__(self, ruta):
        self.ruta = ruta
        self.titulo = os.path.splitext(os.path.basename(ruta))[0]
        self.anterior = None
        self.siguiente = None

class ListaDobleCircular:
    def __init__(self):
        self.primero = None
        self.actual = None
        self.tamaño = 0

    def esta_vacia(self):
        return self.primero is None

    def agregar(self, ruta):
        nuevo = NodoCancion(ruta)

        if self.esta_vacia():
            nuevo.siguiente = nuevo
            nuevo.anterior = nuevo
            self.primero = nuevo
            self.actual = nuevo

        else:
            ultimo = self.primero.anterior
            ultimo.siguiente = nuevo
            nuevo.anterior = ultimo
            nuevo.siguiente = self.primero
            self.primero.anterior = nuevo

        self.tamaño += 1
        return nuevo

    def recorrer(self):
        nodos=[]
        if self.esta_vacia():
            return nodos
        nodo = self.primero

        while True:
            nodos.append(nodo)
            nodo = nodo.siguiente

            if nodo == self.primero:
                break
        return nodos

    def siguiente(self):
        if self.actual is not None:
            self.actual = self.actual.siguiente
        return self.actual

    def anterior(self):
        if self.actual is not None:
            self.actual = self.actual.anterior
        return self.actual

    def buscar_por_indice(self, indice):
        nodos = self.recorrer()
        if 0 <= indice < len(nodos):
            return nodos[indice]
        return None

    def seleccionar(self, nodo):
        if nodo in self.recorrer():
            self.actual = nodo
            return True
        return False

    def eliminar(self, nodo):
        if nodo is None or self.esta_vacia():
            return False
        if self.tamaño == 1:
            self.primero = None
            self.actual = None
        else:
            nodo.anterior.siguiente = nodo.siguiente
            nodo.siguiente.anterior = nodo.anterior

        if nodo == self.primero:
            self.primero = nodo.siguiente

        if nodo == self.actual:
            self.actual = nodo.siguiente 

        nodo.anterior = None
        nodo.siguiente = None
        self.tamaño -= 1
        return True


class ReproductorMusica:
    def __init__(self, ventana):
        self.ventana = ventana
        self.ventana.title("Reproductor de Música")
        self.ventana.geometry("950x620")
        self.ventana.minsize(760,500)

        self.ventana.configure(bg="#125204")

        self.lista_canciones = ListaDobleCircular()
        self.pausado = False
        self.reproduciendo = False
        self.nodos_visibles = {}   # relaciona cada fila de la tabla con su nodo
        self.volumen = tk.DoubleVar(value=0.5)  # Volumen inicial (50%)
        self.mensaje = tk.StringVar(value="Agregar archivos mp3 para reproducir")
        self.cancion_actual = tk.StringVar(value="Ninguna canción seleccionada")

        try:
            pygame.mixer.init()
            self.audio_disponible = True
        except pygame.error as error:
            self.audio_disponible = False
            messagebox.showerror("Error de audio", 
                                 "No se puede iniciar el audio \n"
                                 "Compruebe la salida de sonido del equipo\n"
                                 f"Detalle: {error}")

        self.crear_interfaz()
        self.ventana.protocol("WM_DELETE_WINDOW", self.cerrar)
        self.actualizar_progreso()

    # ------------------------------------------------------------------
    # INTERFAZ
    # ------------------------------------------------------------------
    def crear_interfaz(self):

        estilo = ttk.Style()
        estilo.theme_use("clam")
        estilo.configure(
            "Treeview",
            background = "#17243a",
            foreground = "#f1f5f9",
            fieldbackground = "#17243a",
            rowheight = 30,
            borderwidth = 0
        )
        estilo.configure(
            "Treeview.Heading",
            background = "#17243a",
            foreground = "#f1f5f9",
            font = ("Segoe UI", 10, "bold")
        )
        estilo.map(
            "Treeview",
            background = [("selected", "#1e293b")],
            foreground = [("selected", "#f1f5f9")]
        )
        estilo.configure(
            "Horizontal.TScale",
            background = "#17243a",
            troughcolor = "#0f172a"
        )

        encabezado = tk.Frame(self.ventana, bg="#101827")
        encabezado.pack(fill=tk.X, padx=24, pady=(20, 10))

        tk.Label(
            encabezado,
            text="Reproductor de Música",
            font=("Segoe UI", 21, "bold"),
            fg ="#ffffff",
            bg = "#101827"
        ).pack(anchor="w")

        tk.Label(
            encabezado,
            text="Lista doblemente enlazada circular",
            font=("Segoe UI", 10),
            fg="#aab8d0",
            bg="#101827"
        ).pack(anchor="w", pady=(4, 0))

        contenido = tk.Frame(self.ventana, bg="#1e293b")
        contenido.pack(fill="both", expand=True, padx=24, pady=8)

        # ---------- Panel izquierdo: lista de reproducción ----------
        panel_lista = tk.Frame(contenido, bg="#1e293b")
        panel_lista.pack(side=tk.LEFT, fill="both", expand=True, padx=(14, 7), pady=14)

        tk.Label(
            panel_lista,
            text="Lista de reproducción",
            font=("Segoe UI", 13, "bold"),
            fg="#f1f5f9",
            bg="#1e293b"
        ).pack(anchor="w", pady=(0, 8))

        marco_tabla = tk.Frame(panel_lista, bg="#1e293b")
        marco_tabla.pack(fill="both", expand=True)

        self.tabla = ttk.Treeview(
            marco_tabla,
            columns=("num", "titulo"),
            show="headings",
            selectmode="browse"
        )
        self.tabla.heading("num", text="#")
        self.tabla.heading("titulo", text="Título")
        self.tabla.column("num", width=55, anchor="center", stretch=False)
        self.tabla.column("titulo", width=420, anchor="w")
        self.tabla.tag_configure("actual", foreground="#4ade80")

        barra = ttk.Scrollbar(marco_tabla, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=barra.set)
        self.tabla.pack(side=tk.LEFT, fill="both", expand=True)
        barra.pack(side=tk.RIGHT, fill=tk.Y)

        self.tabla.bind("<Double-1>", self.doble_clic)

        # ---------- Panel derecho: canción actual y volumen ----------
        panel_info = tk.Frame(contenido, bg="#17243a", width=290)
        panel_info.pack(side=tk.RIGHT, fill=tk.Y, padx=(7, 14), pady=14)
        panel_info.pack_propagate(False)

        tk.Label(
            panel_info,
            text="♫",
            font=("Segoe UI", 48),
            fg="#4ade80",
            bg="#17243a"
        ).pack(pady=(22, 4))

        tk.Label(
            panel_info,
            text="Reproduciendo ahora",
            font=("Segoe UI", 10),
            fg="#aab8d0",
            bg="#17243a"
        ).pack()

        tk.Label(
            panel_info,
            textvariable=self.cancion_actual,
            font=("Segoe UI", 13, "bold"),
            fg="#ffffff",
            bg="#17243a",
            wraplength=250,
            justify="center"
        ).pack(pady=(6, 10), padx=12)

        self.etiqueta_tiempo = tk.Label(
            panel_info,
            text="00:00",
            font=("Segoe UI", 18, "bold"),
            fg="#4ade80",
            bg="#17243a"
        )
        self.etiqueta_tiempo.pack(pady=(0, 18))

        tk.Label(
            panel_info,
            text="Volumen",
            font=("Segoe UI", 10),
            fg="#aab8d0",
            bg="#17243a"
        ).pack()

        self.etiqueta_volumen = tk.Label(
            panel_info,
            text="50%",
            font=("Segoe UI", 10, "bold"),
            fg="#f1f5f9",
            bg="#17243a"
        )
        self.etiqueta_volumen.pack()

        ttk.Scale(
            panel_info,
            from_=0,
            to=1,
            orient="horizontal",
            variable=self.volumen,
            command=self.cambiar_volumen
        ).pack(fill=tk.X, padx=26, pady=(4, 0))

        # ---------- Barra de botones ----------
        controles = tk.Frame(self.ventana, bg="#101827")
        controles.pack(fill=tk.X, padx=24, pady=(8, 6))

        def crear_boton(texto, comando, color):
            return tk.Button(
                controles,
                text=texto,
                command=comando,
                font=("Segoe UI", 10, "bold"),
                fg="#ffffff",
                bg=color,
                activebackground="#475569",
                activeforeground="#ffffff",
                relief="flat",
                bd=0,
                padx=12,
                pady=8,
                cursor="hand2"
            )

        crear_boton("＋ Agregar canciones", self.agregar_canciones, "#16a34a").pack(
            side=tk.LEFT, padx=(10, 6), pady=10)
        crear_boton("Eliminar", self.eliminar_cancion, "#b91c1c").pack(
            side=tk.LEFT, padx=6, pady=10)

        crear_boton("⏭ Siguiente", self.siguiente_cancion, "#334155").pack(
            side=tk.RIGHT, padx=(6, 10), pady=10)
        crear_boton("⏹ Detener", self.detener, "#334155").pack(
            side=tk.RIGHT, padx=6, pady=10)
        self.boton_play = crear_boton("▶ Reproducir", self.alternar_reproduccion, "#2563eb")
        self.boton_play.pack(side=tk.RIGHT, padx=6, pady=10)
        crear_boton("⏮ Anterior", self.anterior_cancion, "#334155").pack(
            side=tk.RIGHT, padx=6, pady=10)

        # ---------- Línea de mensajes ----------
        tk.Label(
            self.ventana,
            textvariable=self.mensaje,
            font=("Segoe UI", 10),
            fg="#e2e8f0",
            bg="#125204",
            anchor="w"
        ).pack(fill=tk.X, padx=26, pady=(0, 12))

    # ------------------------------------------------------------------
    # UTILIDADES
    # ------------------------------------------------------------------
    def formato_tiempo(self, milisegundos):
        segundos = max(milisegundos, 0) // 1000
        return f"{segundos // 60:02d}:{segundos % 60:02d}"

    def refrescar_lista(self):
        """Vuelve a dibujar la tabla recorriendo la lista circular."""
        self.tabla.delete(*self.tabla.get_children())
        self.nodos_visibles = {}
        actual = self.lista_canciones.actual

        for posicion, nodo in enumerate(self.lista_canciones.recorrer()):
            fila = str(posicion)
            self.nodos_visibles[fila] = nodo
            es_actual = self.reproduciendo and nodo is actual
            self.tabla.insert(
                "",
                tk.END,
                iid=fila,
                values=("▶" if es_actual else posicion + 1, nodo.titulo),
                tags=("actual",) if es_actual else ()
            )
            if nodo is actual:
                self.tabla.selection_set(fila)
                self.tabla.see(fila)

    # ------------------------------------------------------------------
    # ACCIONES SOBRE LA LISTA
    # ------------------------------------------------------------------
    def agregar_canciones(self):
        rutas = filedialog.askopenfilenames(
            title="Seleccionar archivos mp3",
            filetypes=[("Archivos MP3", "*.mp3")]
        )
        if not rutas:
            return

        existentes = {nodo.ruta for nodo in self.lista_canciones.recorrer()}
        agregadas = 0
        repetidas = 0

        for ruta in rutas:
            if not ruta.lower().endswith(".mp3"):
                continue
            if ruta in existentes:
                repetidas += 1
                continue
            self.lista_canciones.agregar(ruta)
            existentes.add(ruta)
            agregadas += 1

        self.refrescar_lista()

        texto = f"Se agregaron {agregadas} canción(es)."
        if repetidas:
            texto += f" {repetidas} ya estaban en la lista."
        self.mensaje.set(texto)

    def eliminar_cancion(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            self.mensaje.set("Seleccione una canción de la lista para eliminarla")
            return

        nodo = self.nodos_visibles.get(seleccion[0])
        if nodo is None:
            return

        titulo = nodo.titulo
        era_actual = nodo is self.lista_canciones.actual
        if era_actual:
            self.detener()
            self.cancion_actual.set("Ninguna canción seleccionada")

        self.lista_canciones.eliminar(nodo)
        self.refrescar_lista()
        self.mensaje.set(f"Se eliminó: {titulo}")

    def doble_clic(self, evento):
        fila = self.tabla.identify_row(evento.y)
        if not fila:
            return
        nodo = self.nodos_visibles.get(fila)
        if nodo is not None and self.lista_canciones.seleccionar(nodo):
            self.reproducir_actual()

    # ------------------------------------------------------------------
    # REPRODUCCIÓN
    # ------------------------------------------------------------------
    def reproducir_actual(self):
        nodo = self.lista_canciones.actual
        if nodo is None:
            self.mensaje.set("Agregar archivos mp3 para reproducir")
            return

        if not self.audio_disponible:
            messagebox.showwarning("Sin audio", "El audio no está disponible en este equipo.")
            return

        try:
            pygame.mixer.music.load(nodo.ruta)
            pygame.mixer.music.set_volume(self.volumen.get())
            pygame.mixer.music.play()
        except pygame.error as error:
            self.reproduciendo = False
            self.pausado = False
            self.boton_play.config(text="▶ Reproducir")
            self.refrescar_lista()
            messagebox.showerror(
                "Error al reproducir",
                f"No se pudo reproducir:\n{nodo.titulo}\n\nDetalle: {error}"
            )
            return

        self.reproduciendo = True
        self.pausado = False
        self.cancion_actual.set(nodo.titulo)
        self.boton_play.config(text="⏸ Pausar")
        self.mensaje.set(f"Reproduciendo: {nodo.titulo}")
        self.refrescar_lista()

    def alternar_reproduccion(self):
        if self.lista_canciones.esta_vacia():
            self.mensaje.set("Agregar archivos mp3 para reproducir")
            return

        if not self.reproduciendo:
            self.reproducir_actual()
        elif self.pausado:
            pygame.mixer.music.unpause()
            self.pausado = False
            self.boton_play.config(text="⏸ Pausar")
            self.mensaje.set(f"Reproduciendo: {self.cancion_actual.get()}")
        else:
            pygame.mixer.music.pause()
            self.pausado = True
            self.boton_play.config(text="▶ Reanudar")
            self.mensaje.set("Reproducción en pausa")

    def detener(self):
        if self.audio_disponible:
            pygame.mixer.music.stop()
        self.reproduciendo = False
        self.pausado = False
        self.boton_play.config(text="▶ Reproducir")
        self.etiqueta_tiempo.config(text="00:00")
        self.mensaje.set("Reproducción detenida")
        self.refrescar_lista()

    def siguiente_cancion(self):
        if self.lista_canciones.esta_vacia():
            return
        self.lista_canciones.siguiente()
        self.reproducir_actual()

    def anterior_cancion(self):
        if self.lista_canciones.esta_vacia():
            return
        self.lista_canciones.anterior()
        self.reproducir_actual()

    def cambiar_volumen(self, valor):
        nivel = float(valor)
        self.etiqueta_volumen.config(text=f"{int(nivel * 100)}%")
        if self.audio_disponible:
            pygame.mixer.music.set_volume(nivel)

    def actualizar_progreso(self):
        """Se ejecuta cada 300 ms: actualiza el tiempo y pasa a la siguiente
        canción cuando la actual termina (al llegar a la última vuelve a la primera)."""
        if self.audio_disponible and self.reproduciendo and not self.pausado:
            if pygame.mixer.music.get_busy():
                self.etiqueta_tiempo.config(
                    text=self.formato_tiempo(pygame.mixer.music.get_pos())
                )
            else:
                self.siguiente_cancion()
        self.ventana.after(300, self.actualizar_progreso)

    def cerrar(self):
        if self.audio_disponible:
            pygame.mixer.music.stop()
            pygame.mixer.quit()
        self.ventana.destroy()


if __name__ == "__main__":
    ventana = tk.Tk()
    app = ReproductorMusica(ventana)
    ventana.mainloop()
