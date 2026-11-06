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

    class ReporductorMusica:
        def __init__(self, ventana):
            self.ventana = ventana
            self.ventana.title("Reproductor de Música")
            self.ventana.geometry("950x620")
            self.ventana.minsize(760,500)

            self.ventana.configure(bg="#125204")

            self.lista_canciones = ListaDobleCircular()
            self.pausado = False
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