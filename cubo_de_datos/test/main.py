import io
import matplotlib.patches as mpatches
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox, Toplevel, Menu, simpledialog
from PIL import Image, ImageTk
from scipy.optimize import optimize, curve_fit
from astropy.io import fits
import pymongo
from datetime import datetime
import matplotlib
from astropy.modeling import models, fitting
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import os
import uuid
from matplotlib.patches import Circle, Ellipse, Rectangle
from matplotlib.figure import Figure
from tkinter import Scale
import matplotlib.pyplot as plt
import matplotlib.path as mpath
import numpy as np
from tkinter import ttk
from matplotlib.widgets import Slider

data_id = str(uuid.uuid4())
graphic_id = str(uuid.uuid4())
matplotlib.use("TkAgg")

# Variables globales
archivo_fits = None
hdul = None
datos_cubo = None
num_frames = 0
imagen_actual = 0
coordenadas_label = None
entrada_coord_x = None
entrada_coord_y = None
ventana_grafico = None  # Ventana para el gráfico
ventana_grafico_abierta = False
last_mouse_x = 0
last_mouse_y = 0
########################################################################################################################
####################################### Activaciones movimientos/figuras ###############################################
########################################################################################################################
movimiento_activado = False  # Variable para rastrear el estado del movimiento
pixel_seleccionado = None  # Variable para el pixel seleccionado
pixel_activado = False  # Variable para rastrear el estado de la opción "Pixel"
circulo_activado = False  # Variable para rastrear el estado de la opción "Círculo"
eclipse_activado = False  # Variable para rastrear el estado del movimiento
cuadrado_activado = False  # Variable para rastrear el estado de la opción "Cuadrado"
area_activado = False  # Variable para rastrear el estado de la opción "Area"
ultimo_clic = None
dragging = False  # Variables para el seguimiento del arrastre del ratón

# Variables para la creación del área libre
area_libre_activa = False
puntos = []
lineas_figura = []
puntos_dibujados = []
puntos_area_libre = []
coordenadas_mascara_seleccionada = []
# Variable para rastrear si el área libre está activa
lineas_grafico = []
# Variables globales
espectros_area_libre = []
# Variables globales
areas_libres = []
area_libre_seleccionada = None  # Variable para el área libre seleccionada

figuras_dibujadas = []

# Variables relacionadas con Matplotlib
fig = None
ax = None
canvas = None
linea_grafico = None
barra_desplazamiento = None
circulos_dibujados = []  # Lista para almacenar los círculos dibujados
circulo_seleccionado = None  # Variable para el círculo seleccionado

radio_scale = None  # Variable para el scrollbar del radio del círculo
radio = 5  # Valor predeterminado del radio del círculo
ultimo_circulo = None  # Variable para el último círculo dibujado

# Variables Elipse
ultima_elipse = None
elipses_dibujadas = []  # Lista para almacenar los círculos dibujados
dibujando_elipse = False
elipse_seleccionada = None  # Variable para la elipse seleccionada

# Variables Circulo
centro_x, centro_y = None, None
dibujando_circulo = False
circulo_dibujado = None

# Variables Cuadrado
cuadrados_dibujados = []  # Lista para almacenar los cuadrados dibujados
ultimo_cuadrado = None  # Variable para mantener un seguimiento del último cuadrado dibujado
dibujando_cuadrado = False
cuadrado_seleccionado = None
cuadrados_visibles = []  # Lista para almacenar los cuadrados visibles
cuadrados_invisibles = []  # Lista para almacenar los cuadrados invisibles

# Variables Pixel
ultimo_pixel = None
pixeles_seleccionados = []
pixeles_dibujados = []
path_collections = []

# Base de datos MongoDB
# switch_pymongo=0
# if switch_pymongo:
cliente = pymongo.MongoClient("mongodb://localhost:27017/")
base_datos = cliente["Astronomy3"]
# File_collection
file_collection = base_datos["File_collection"]
# Data_collection
data_collection = base_datos["Data_collection"]
# Graphics
graphics_collection = base_datos["Graphics"]
# Mascaras de area libre guardadas
mask_collection = base_datos["masks"]

ventanas_grafico = []

########################################################################################################################
########################################################################################################################
# Función para cargar la imagen FITS actual #
########################################################################################################################
########################################################################################################################
def cargar_imagen_actual():
    global imagen_actual
    ax.clear()
    ax.imshow(datos_cubo[imagen_actual], cmap='gray')
    # Vuelve a dibujar todas las figuras
    for figura_info in figuras_dibujadas:
        # Extrae la figura de la tupla
        tipo_figura, info_figura = figura_info
        if tipo_figura == 'area_libre':
            puntos_dibujados, lineas_figura = info_figura
            for linea in lineas_figura:
                ax.add_line(linea)
        else:
            if isinstance(info_figura, tuple):
                info_figura = info_figura[0]
            if isinstance(info_figura, matplotlib.patches.Patch):
                ax.add_patch(info_figura)
            elif isinstance(info_figura, matplotlib.collections.PathCollection):
                ax.add_collection(info_figura)
    ax.set_title(f"Imagen {imagen_actual + 1}/{num_frames}")
    canvas.draw()

def cargar_imagen_actual_2d():
    global imagen_actual, boton_graficar, boton_anterior, boton_siguiente
    print("llegue aca")
    naxis = hdul[0].header['NAXIS']
    if naxis == 2:
        messagebox.showinfo("Advertencia",
                            "El archivo FITS que ha seleccionado tiene solo 2 dimensiones. Solo se mostrará la imagen actual.")

    ax.clear()
    ax.imshow(datos_cubo[:, :], cmap='gray')
    ax.set_title(f"Imagen {imagen_actual + 1}/{num_frames}")
    canvas.draw()
    boton_anterior.config(state=tk.DISABLED)
    boton_siguiente.config(state=tk.DISABLED)
    boton_graficar.config(state=tk.DISABLED)

# funcion para cargar imagen desde entrada de texto
def cargar_imagen():
    global imagen_actual
    entry = int(entrada_coord_z.get())
    if entry >= 1 and entry <= num_frames:
        imagen_actual = entry - 1
        cargar_imagen_actual()
        actualizar_barra_desplazamiento()


# Función para actualizar la etiqueta de coordenadas
def actualizar_etiqueta_coordenadas():
    global coordenadas_label
    global imagen_actual
    global numero_imagen
    global entero
    numero_imagen = entrada_coord_z.get()  # Captura el valor como una cadena de caracteres
    try:
        entero = int(numero_imagen)  # Convierte la cadena en un entero
    except ValueError:
        tk.messagebox.showerror("Error", "¡Entrada no válida!")
    entrada_coord_z.delete(0, tk.END)
    entrada_coord_z.insert(1, imagen_actual + 1)
    if coordenadas_label is not None:
        coordenadas_label.config(text=f"Píxel Seleccionado: ({entrada_coord_x.get()}, {entrada_coord_y.get()})")


# Función para cargar la imagen anterior
def cargar_imagen_anterior():
    global imagen_actual
    if imagen_actual > 0:
        imagen_actual -= 1
        cargar_imagen_actual()
        actualizar_barra_desplazamiento()


# Función para cargar la siguiente imagen
def cargar_siguiente_imagen():
    global imagen_actual
    if imagen_actual < num_frames - 1:
        imagen_actual += 1
        cargar_imagen_actual()
        actualizar_barra_desplazamiento()


# Función para cargar la imagen actual en función del valor de la barra de desplazamiento
def cargar_imagen_desde_barra(event):
    global imagen_actual
    nueva_posicion = int(barra_desplazamiento.get())
    if nueva_posicion >= 1 and nueva_posicion <= num_frames:
        imagen_actual = nueva_posicion - 1
        cargar_imagen_actual()


# Función para crear una ventana emergente para el gráfico
def crear_ventana_grafico():
    global ventana_grafico, figura_grafico, axes_grafico, canvas_grafico

    ventana_grafico = tk.Toplevel()
    ventana_grafico.title("Gráfico del Espectro")
    # Crear un marco para el gráfico similar al segundo código que proporcionaste
    marco_grafico = tk.Frame(ventana_grafico)
    marco_grafico.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Crear un gráfico de Matplotlib similar al segundo código que proporcionaste
    figura_grafico, axes_grafico = plt.subplots(figsize=(8, 5))
    canvas_grafico = FigureCanvasTkAgg(figura_grafico, master=marco_grafico)
    canvas_grafico.draw()
    canvas_grafico.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    # Agregar la barra de herramientas de navegación de Matplotlib
    toolbar = NavigationToolbar2Tk(canvas_grafico, marco_grafico)
    toolbar.update()
    canvas_grafico.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    # Crear un marco para los botones y la caja de comentarios
    marco_botones_comentarios = tk.Frame(marco_grafico)
    marco_botones_comentarios.pack(side=tk.TOP, fill=tk.BOTH)

    # Crear un cuadro de comentarios al final
    cuadro_comentarios = tk.Text(marco_botones_comentarios, height=2, width=40)
    cuadro_comentarios.pack(side=tk.TOP, fill=tk.BOTH)
    texto_inicial = "Escribe aquí tus comentarios..."
    cuadro_comentarios.insert("1.0", texto_inicial)

    def borrar_texto_inicial(event):
        if cuadro_comentarios.get("1.0", "end-1c") == texto_inicial:
            cuadro_comentarios.delete("1.0", "end-1c")
            cuadro_comentarios.config(fg="black")  # Cambia el color del texto a negro

    def restaurar_texto_inicial(event):
        if cuadro_comentarios.get("1.0", "end-1c") == "":
            cuadro_comentarios.insert("1.0", texto_inicial)
            cuadro_comentarios.config(fg="grey")

    # Asocia los eventos para borrar y restaurar el texto inicial
    cuadro_comentarios.bind("<FocusIn>", borrar_texto_inicial)
    cuadro_comentarios.bind("<FocusOut>", restaurar_texto_inicial)

    # Botón de "Guardar"
    boton_guardar = tk.Button(marco_botones_comentarios, text="Guardar",
                              command=lambda: guardar_grafico(cuadro_comentarios),bg="#87CEEB", fg="black")
    boton_guardar.pack(side=tk.LEFT, padx=5, pady=5)

    # Botón de "Ajuste gausiano"
    boton_ajuste_gausiano = tk.Button(marco_botones_comentarios, text="Ajuste gausiano",
                                      command=lambda: ajustes_grafico(), bg="dim gray", fg="white")
    boton_ajuste_gausiano.pack(side=tk.LEFT, padx=5, pady=5)

    # Botón de "Guardar mascara"
    boton_guardar_mascara = tk.Button(marco_botones_comentarios, text="Guardar mascara",
                                      command=lambda: guardar_ultima_area_libre_en_mongodb(),bg="beige", fg="black")
    boton_guardar_mascara.pack(side=tk.LEFT, padx=5, pady=5)

    ventanas_grafico.append(ventana_grafico)

    # Cuando ya no se necesite la figura, esta función la cierra
    plt.close(figura_grafico)


def crear_ventana_grafico_frecuencia():
    global ventana_grafico_frecuencia, figura_grafico, axes_grafico, canvas_grafico

    ventana_grafico_frecuencia = tk.Toplevel()
    ventana_grafico_frecuencia.title("Gráfico del Espectro - Frecuencia")

    # Crear un marco para el gráfico similar al código anterior
    marco_grafico = tk.Frame(ventana_grafico_frecuencia)
    marco_grafico.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Crear un gráfico de Matplotlib similar al código que proporcionaste
    figura_grafico, axes_grafico = plt.subplots(figsize=(8, 5))
    canvas_grafico = FigureCanvasTkAgg(figura_grafico, master=marco_grafico)
    canvas_grafico.draw()
    canvas_grafico.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    # Agregar la barra de herramientas de navegación de Matplotlib
    toolbar = NavigationToolbar2Tk(canvas_grafico, marco_grafico)
    toolbar.update()
    canvas_grafico.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    # Crear un marco para los botones y el cuadro de comentarios
    marco_botones_comentarios = tk.Frame(marco_grafico)
    marco_botones_comentarios.pack(side=tk.TOP, fill=tk.BOTH)

    # Crear un cuadro de comentarios al final
    cuadro_comentarios = tk.Text(marco_botones_comentarios, height=2, width=40)
    cuadro_comentarios.pack(side=tk.TOP, fill=tk.BOTH)
    texto_inicial = "Escribe aquí tus comentarios..."
    cuadro_comentarios.insert("1.0", texto_inicial)

    def borrar_texto_inicial(event):
        if cuadro_comentarios.get("1.0", "end-1c") == texto_inicial:
            cuadro_comentarios.delete("1.0", "end-1c")
            cuadro_comentarios.config(fg="black")  # Cambia el color del texto a negro

    def restaurar_texto_inicial(event):
        if cuadro_comentarios.get("1.0", "end-1c") == "":
            cuadro_comentarios.insert("1.0", texto_inicial)
            cuadro_comentarios.config(fg="grey")

    # Asocia los eventos para borrar y restaurar el texto inicial
    cuadro_comentarios.bind("<FocusIn>", borrar_texto_inicial)
    cuadro_comentarios.bind("<FocusOut>", restaurar_texto_inicial)

    # Botón de "Guardar Gráfico"
    boton_guardar_grafico = tk.Button(ventana_grafico_frecuencia, text="Guardar Gráfico",
                                      command=lambda: guardar_grafico(cuadro_comentarios), bg="#87CEEB", fg="black")
    boton_guardar_grafico.pack(side=tk.TOP, padx=5, pady=5)

    # Botón de "Ajuste Gaussiano"
    boton_ajuste_gaussiano = tk.Button(ventana_grafico_frecuencia, text="Ajuste Gaussiano",
                                       command=lambda: ajuste_gaussiano_frecuencia(frecuencias,espectro),
                                       bg="dim gray", fg="white")
    boton_ajuste_gaussiano.pack(side=tk.TOP, padx=5, pady=5)

    # Cuando ya no se necesite la figura, esta función la cierra
    plt.close(figura_grafico)

def guardar_ultima_area_libre_en_mongodb():
    global puntos_area_libre, mask_collection

    # Verifica si hay puntos de área libre para guardar
    if puntos_area_libre:
        # Utiliza un cuadro de diálogo para pedir el nombre de la máscara
        nombre_mascara = simpledialog.askstring("Nombre de la Máscara", "Ingresa un nombre para la máscara:")

        # Si el usuario presiona cancelar, no hace nada
        if nombre_mascara is None:
            return

        if nombre_mascara.strip() != "":
            # Inserta las coordenadas en la colección con el nombre proporcionado
            data = {"nombre": nombre_mascara, "coordenadas": puntos_area_libre}
            mask_collection.insert_one(data)
            puntos_area_libre.clear()  # Vacía la lista de puntos
            # Mostrar un mensaje de guardado exitoso
            messagebox.showinfo("Guardado", f"Coordenadas de la máscara '{nombre_mascara}' guardadas correctamente.")
        else:
            messagebox.showerror("Error", "Debes ingresar un nombre para la máscara.")
    else:
        messagebox.showerror("Error", "No hay puntos de área libre para guardar.")


def guardar_grafico(cuadro_comentarios):
    global figura_grafico  # Asegúrate de que la figura sea global y accesible aquí

    # Pide al usuario que ingrese un nombre para el gráfico
    nombre_grafico = simpledialog.askstring("Guardar Gráfico", "Ingresa un nombre para el gráfico:")

    # Si el usuario presiona cancelar, no hace nada
    if nombre_grafico is None:
        return

    # Crear un objeto de bytes en memoria para guardar la imagen
    buf = io.BytesIO()
    figura_grafico.savefig(buf, format='png')
    buf.seek(0)

    # Obtener el comentario del cuadro de texto
    comentario = cuadro_comentarios.get("1.0", "end-1c")

    # Insertar el objeto de bytes en la colección "Graphics" junto con el nombre y el comentario
    graphics_collection.insert_one({'nombre': nombre_grafico, 'imagen': buf.read(), 'comentario': comentario})

    # Mostrar un mensaje de confirmación al usuario
    messagebox.showinfo("Guardar", f"Gráfico '{nombre_grafico}' y comentario guardados en MongoDB.")


# Función para cerrar la ventana emergente del gráfico
def cerrar_ventana_grafico():
    global ventana_grafico
    ventana_grafico.destroy()

def iniciar_arrastre(event):
    global dragging
    dragging = True
    # Guardar las coordenadas iniciales del ratón
    global last_mouse_x, last_mouse_y
    last_mouse_x = event.x
    last_mouse_y = event.y


def detener_arrastre(event):
    global dragging
    dragging = False


# Función para manejar el arrastre de la imagen
def mover_imagen(event):
    global dragging, last_mouse_x, last_mouse_y
    if dragging and movimiento_activado:
        # Calcular el desplazamiento del ratón
        dx = (event.x - last_mouse_x) * 0.1  # Ajusta este factor según tu preferencia
        dy = (event.y - last_mouse_y) * 0.1  # Ajusta este factor según tu preferencia

        # Obtener los límites actuales de los ejes
        x_min, x_max = ax.get_xlim()
        y_min, y_max = ax.get_ylim()

        # Actualizar los límites de los ejes con el desplazamiento
        new_x_min = x_min - dx
        new_x_max = x_max - dx
        new_y_min = y_min - dy
        new_y_max = y_max - dy

        # Establecer los nuevos límites de los ejes
        ax.set_xlim(new_x_min, new_x_max)
        ax.set_ylim(new_y_min, new_y_max)

        canvas.draw()

        # Actualizar las coordenadas del ratón
        last_mouse_x = event.x
        last_mouse_y = event.y


def remove_nans(extension_valida):
    hdul = fits.open(archivo_fits, ext=2)
    extension_valida.data[np.isnan(extension_valida.data)] = 0
    extension_valida.data[np.isinf(extension_valida.data)] = 0

########################################################################################################################
########################################################################################################################
# FUNCION ABRIR ARCHIVO #
########################################################################################################################
########################################################################################################################
def abrir_archivo():
    global archivo_fits, hdul, datos_cubo, num_frames, boton_anterior, boton_siguiente, boton_graficar, boton_area_libre

    # Resetea el archivo FITS y los datos del cubo
    archivo_fits = None
    hdul = None
    datos_cubo = None
    num_frames = 0

    archivo_fits = filedialog.askopenfilename(filetypes=[("FITS files", "*.fits")])
    if archivo_fits:
        try:
            # Abrir el archivo FITS
            hdul = fits.open(archivo_fits, ext=1)

            # Con esto podemos verificar que se tomen archivos FITS segun PRYMARY, IMAGE, DATA CUBE y ESPECTRUM
            extension_valida = None
            nombre_archivo = os.path.basename(archivo_fits)

            for ext in hdul:
                if ext.name in ["PRIMARY", "IMAGE", "DATA CUBE", "SPECTRUM", "STANDARD"]:
                    extension_valida = ext
                    # print(extension_valida)
                    # remueve dimensiones innecesarias (por ejemplo,
                    # para datos de ALMA) si las hubiese
                    extension_valida.data = extension_valida.data.squeeze()

                    # Con esto buscamos la extension buscada, para abrir solo estas.
                    break

                if extension_valida is None:
                    raise ValueError("No es posible abrir este tipo de archivo FITS, dado que no contiene imágenes.")

            # chequeo de datos NANs. No es necesario modificar pues
            # tkinter lidia bien con ellos

            if np.any(np.isnan(extension_valida.data)) or np.any(np.isinf(extension_valida.data)):
                 respuesta = messagebox.askquestion("Datos Inválidos",
                                                    "El archivo FITS contiene datos inválidos (NaN o infinitos). ¿Desea convertirlos a 0?")

                 if respuesta == 'yes':
                     data = remove_nans(extension_valida)
                     print("nans sacados")

            header = extension_valida.header
            # Imprimir el encabezado para ver la información
            print(header)
            naxis = hdul[0].header['NAXIS']
            if naxis == 2:
                print("paso por el naxis ==2")
                datos_cubo = extension_valida.data
                cargar_imagen_actual_2d()
            else:
                datos_cubo = extension_valida.data
                cargar_imagen_actual()
                tipo_extension = extension_valida.name
                fecha_actual = datetime.now()
                num_frames, num_rows, num_columns = datos_cubo.shape
                print(f"Número de cuadros: {num_frames}")
                print(f"Número de filas: {num_rows}")
                print(f"Número de columnas: {num_columns}")
                # Habilitar los botones "Anterior" y "Siguiente"
                boton_anterior.config(state=tk.NORMAL)
                boton_siguiente.config(state=tk.NORMAL)
                # Habilitar el botón "Graficar"
                boton_graficar.config(state=tk.NORMAL)
                actualizar_etiqueta_coordenadas()  # Agregado para actualizar coordenadas al cargar el archivo
                actualizar_barra_desplazamiento()

            # if switch_pymongo:
                # Base de datos = File_Collection
                file_info = {
                    "Data_id": data_id,  # Identificador
                    "File_name": nombre_archivo,  # File
                    "Fecha": fecha_actual.strftime("%d/%m/%Y"),  # Fecha segun día/mes/año
                    "Hora": fecha_actual.strftime("%H:%M:%S")  # Fecha segun Hora
                }
                file_collection.insert_one(file_info)

                # Base de datos = Data_Collection
                data_info = {
                    "Data_id": data_id,  # Identificador
                    "Filename": nombre_archivo,  # File
                    "Header": tipo_extension,  # Encabezado
                    "Fecha": fecha_actual.strftime("%d/%m/%Y"),  # Fecha segun día/mes/año
                    "Hora": fecha_actual.strftime("%H:%M:%S"),  # Fecha segun Hora
                    "Data": str(datos_cubo)  # Datos
                }
                data_collection.insert_one(data_info)

            actualizar_estado_menu()
            borrar_figuras()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el archivo FITS: {str(e)}")
            boton_graficar.config(state=tk.DISABLED)
            actualizar_estado_menu()
    else:
        # Si no se selecciona un archivo FITS válido, deshabilita el botón "Graficar"
        boton_graficar.config(state=tk.DISABLED)

########################################################################################################################
########################################################################################################################
# FUNCION GRAFICAR #
########################################################################################################################
########################################################################################################################
def graficar(x=None, y=None, ancho=None, alto=None, angulo=None):
    global espectro, circulos_dibujados, datos_cubo, figura_grafico, axes_grafico, ventana_grafico_abierta, linea_grafico, espectro_promedio
    global linea_grafico, figura_grafico, axes_grafico, ventana_grafico, ventana_grafico_abierta, centro_y,centro_x,radio
    global area_libre_activa, puntos
    ventana_grafico_abierta = False
    if datos_cubo is not None:
        try:
            if pixel_activado:
                for i, (x, y) in enumerate(pixeles_seleccionados):
                    if x and y:
                        x = int(x)
                        y = int(y)
                        if 0 <= x < datos_cubo.shape[2] and 0 <= y < datos_cubo.shape[1]:
                            espectro = datos_cubo[:, y, x]

                            # Crea una nueva ventana para el gráfico
                            crear_ventana_grafico()
                            ventana_grafico_abierta = True

                            # Crea una nueva línea para el gráfico
                            linea_grafico, = axes_grafico.plot(espectro, lw=2)

                            # Establecer los límites de los ejes x e y
                            axes_grafico.set_xlim(0, len(espectro) - 1)
                            axes_grafico.set_ylim(-0.0002, max(espectro))

                            # Actualiza el título del gráfico con las coordenadas
                            axes_grafico.set_title(f'Espectro del píxel ({x}, {y})')
                            figura_grafico.canvas.draw()
                        else:
                            messagebox.showerror("Error", "Coordenadas fuera de los límites de la imagen.")
                    else:
                        messagebox.showerror("Error", "Por favor, ingresa coordenadas válidas.")
            elif circulo_activado:
                for i, circulo in enumerate(circulos_dibujados):
                    centro_x, centro_y = circulo.center
                    radio = circulo.radius
                    y, x = np.ogrid[-centro_y:datos_cubo.shape[1] - centro_y, -centro_x:datos_cubo.shape[2] - centro_x]
                    mascara = x ** 2 + y ** 2 <= radio ** 2
                    espectro = datos_cubo[:, mascara]

                    # Calcula el promedio del espectro por píxel dentro del área circular
                    espectro_promedio = np.mean(espectro, axis=1)

                    # Crea una nueva ventana para el gráfico
                    crear_ventana_grafico()
                    ventana_grafico_abierta = True

                    # Crea una nueva línea para el gráfico
                    linea_grafico, = axes_grafico.plot(espectro_promedio, lw=2)

                    # Establecer los límites de los ejes x e y
                    axes_grafico.set_xlim(0, len(espectro_promedio) - 1)
                    axes_grafico.set_ylim(np.min(espectro_promedio) - 0.0002, np.max(espectro_promedio))

                    # Actualiza el título del gráfico con las coordenadas
                    axes_grafico.set_title(
                        f'Espectro por píxel en el área circular (Centro: ({centro_x:.2f}, {centro_y:.2f}), Radio: {radio:.2f})')
                    figura_grafico.canvas.draw()
            elif cuadrado_activado:
                for i, cuadrado in enumerate(cuadrados_dibujados):
                    x_cuadrado, y_cuadrado = cuadrado.get_x(), cuadrado.get_y()
                    lado_cuadrado = cuadrado.get_width()
                    x1, x2 = int(x_cuadrado), int(x_cuadrado + lado_cuadrado)
                    y1, y2 = int(y_cuadrado), int(y_cuadrado + lado_cuadrado)

                    if 0 <= x1 < datos_cubo.shape[2] and 0 <= y1 < datos_cubo.shape[1] and \
                            0 <= x2 < datos_cubo.shape[2] and 0 <= y2 < datos_cubo.shape[1]:
                        espectro = datos_cubo[:, y1:y2, x1:x2]

                        # Calcula el promedio del espectro por píxel dentro del área del cuadrado
                        espectro_promedio = np.mean(espectro, axis=(1, 2))

                        # Crea una nueva ventana para el gráfico
                        crear_ventana_grafico()
                        ventana_grafico_abierta = True

                        # Crea una nueva línea para el gráfico
                        linea_grafico, = axes_grafico.plot(espectro_promedio, lw=2)

                        # Establecer los límites de los ejes x e y
                        axes_grafico.set_xlim(0, len(espectro_promedio) - 1)
                        axes_grafico.set_ylim(np.min(espectro_promedio) - 0.0002, np.max(espectro_promedio))

                        # Actualiza el título del gráfico con la información del cuadrado y el promedio
                        axes_grafico.set_title(
                            f'Promedio del Espectro por píxel en el área cuadrada (Inicio: ({x1}, {y1}), Lado: {lado_cuadrado})')
                        figura_grafico.canvas.draw()
                    else:
                        messagebox.showerror("Error", "Coordenadas del cuadrado fuera de los límites de la imagen.")
            elif eclipse_activado:
                print("grafico")
                for i, elipse in enumerate(elipses_dibujadas):
                    centro_x, centro_y = elipse.center
                    ancho = elipse.width
                    alto = elipse.height
                    # Calcula la máscara para el área dentro de la elipse
                    y, x = np.ogrid[-centro_y:datos_cubo.shape[1] - centro_y, -centro_x:datos_cubo.shape[2] - centro_x]
                    mascara = ((x / (ancho / 2)) ** 2 + (y / (alto / 2)) ** 2) <= 1
                    espectro = datos_cubo[:, mascara]
                    # Calcula el promedio del espectro por píxel dentro del área de la elipse
                    espectro_promedio = np.mean(espectro, axis=1)
                    # Crea una nueva ventana para el gráfico
                    crear_ventana_grafico()
                    # Agrega la línea del gráfico a la ventana
                    linea_grafico, = axes_grafico.plot(espectro_promedio, lw=2)
                    axes_grafico.set_xlabel('Frame')
                    axes_grafico.set_ylabel('Intensidad')
                    # Actualiza el título del gráfico con la información de la elipse y el promedio
                    axes_grafico.set_title(
                        'Espectro por píxel en el área de la elipse (Centro: ({:.2f}, {:.2f}), Ancho: {:.2f}, Alto: {:.2f})'.format(
                            centro_x, centro_y, ancho, alto))
                    figura_grafico.canvas.draw()
                    ventanas_grafico.append(ventana_grafico)

            elif espectros_area_libre:  # Verifica si la lista de espectros no está vacía antes de intentar graficar los espectros
                for i, espectro in enumerate(espectros_area_libre):
                    # Crea una nueva ventana para el gráfico
                    crear_ventana_grafico()
                    ventana_grafico_abierta = True

                    # Crea una nueva línea para el gráfico
                    linea_grafico, = axes_grafico.plot(espectro, lw=2)

                    # Establecer los límites de los ejes x e y
                    axes_grafico.set_xlim(0, len(espectro) - 1)
                    axes_grafico.set_ylim(np.min(espectro) - 0.0002, np.max(espectro))

                    # Actualiza el título del gráfico con las coordenadas
                    axes_grafico.set_title(f'Espectro del área libre {i + 1}')
                    figura_grafico.canvas.draw()
        except ValueError:
            messagebox.showerror("Error", "Por favor, ingresa coordenadas válidas.")

########################################################################################################################
########################################################################################################################
# FUNCION AJUSTE GAUSIANNO #
########################################################################################################################
########################################################################################################################
def ajuste_gausiano(espectro):
    global area_libre_activa, pixel_activado, cuadrado_activado, eclipse_activado

    # Crear un array con valores x para el ajuste
    x = np.arange(len(espectro))

    # Definir un modelo gaussiano
    gaussiano_init = models.Gaussian1D(amplitude=np.max(espectro), mean=np.argmax(espectro), stddev=1.0)

    # Inicializar el ajuste
    fitter = fitting.LevMarLSQFitter()

    # Realizar el ajuste del modelo a los datos
    gaussian_fit = fitter(gaussiano_init, x, espectro)

    # Extraer los parámetros del ajuste
    amplitude_opt = gaussian_fit.amplitude.value
    mean_opt = gaussian_fit.mean.value
    stddev_opt = gaussian_fit.stddev.value

    # Graficar el espectro y el ajuste
    plt.figure()
    plt.plot(x, espectro, 'b', label='Espectro')
    plt.plot(x, gaussian_fit(x), 'r', label='Ajuste Gaussiano')
    plt.legend(loc='best')
    plt.title('Ajuste Gaussiano del Espectro')
    plt.xlabel('Índice del Píxel')
    plt.ylabel('Intensidad')

        # Imprimir los parámetros del ajuste
    print(f'Amplitud óptima: {amplitude_opt}')
    print(f'Valor medio óptimo: {mean_opt}')
    print(f'Desviación estándar óptima: {stddev_opt}')

    plt.show()

def ajuste_circulo(espectro_promedio):
    # Crear un array con valores x para el ajuste
    x = np.arange(len(espectro_promedio))

    # Definir un modelo gaussiano
    gaussiano_init = models.Gaussian1D(amplitude=np.max(espectro_promedio), mean=np.argmax(espectro_promedio), stddev=1.0)

    # Inicializar el ajuste
    fitter = fitting.LevMarLSQFitter()

    # Realizar el ajuste del modelo a los datos
    gaussian_fit = fitter(gaussiano_init, x, espectro_promedio)

    # Extraer los parámetros del ajuste
    amplitude_opt = gaussian_fit.amplitude.value
    mean_opt = gaussian_fit.mean.value
    stddev_opt = gaussian_fit.stddev.value

    # Graficar el espectro y el ajuste
    plt.figure()
    plt.plot(x, espectro_promedio, 'b', label='Espectro Promedio')
    plt.plot(x, gaussian_fit(x), 'r', label='Ajuste Gaussiano')
    plt.legend(loc='best')
    plt.title('Ajuste Gaussiano del Espectro Promedio')
    plt.xlabel('Índice del Píxel')
    plt.ylabel('Intensidad')

    # Imprimir los parámetros del ajuste
    print(f'Amplitud óptima: {amplitude_opt}')
    print(f'Valor medio óptimo: {mean_opt}')
    print(f'Desviación estándar óptima: {stddev_opt}')

    plt.show()

def ajuste_cuadrado(espectro_promedio):
    # Crear un array con valores x para el ajuste
    x = np.arange(len(espectro_promedio))

    # Definir un modelo gaussiano
    gaussiano_init = models.Gaussian1D(amplitude=np.max(espectro_promedio), mean=np.argmax(espectro_promedio), stddev=1.0)

    # Inicializar el ajuste
    fitter = fitting.LevMarLSQFitter()

    # Realizar el ajuste del modelo a los datos
    gaussian_fit = fitter(gaussiano_init, x, espectro_promedio)

    # Extraer los parámetros del ajuste
    amplitude_opt = gaussian_fit.amplitude.value
    mean_opt = gaussian_fit.mean.value
    stddev_opt = gaussian_fit.stddev.value

    # Graficar el espectro y el ajuste
    plt.figure()
    plt.plot(x, espectro_promedio, 'b', label='Espectro Promedio')
    plt.plot(x, gaussian_fit(x), 'r', label='Ajuste Gaussiano')
    plt.legend(loc='best')
    plt.title('Ajuste Gaussiano del Espectro Promedio')
    plt.xlabel('Índice del Píxel')
    plt.ylabel('Intensidad')

    # Imprimir los parámetros del ajuste
    print(f'Amplitud óptima: {amplitude_opt}')
    print(f'Valor medio óptimo: {mean_opt}')
    print(f'Desviación estándar óptima: {stddev_opt}')

    plt.show()

def ajuste_elipse(espectro_promedio):
    # Crear un array con valores x para el ajuste
    x = np.arange(len(espectro_promedio))

    # Definir un modelo gaussiano
    gaussiano_init = models.Gaussian1D(amplitude=np.max(espectro_promedio), mean=np.argmax(espectro_promedio), stddev=1.0)

    # Inicializar el ajuste
    fitter = fitting.LevMarLSQFitter()

    # Realizar el ajuste del modelo a los datos
    gaussian_fit = fitter(gaussiano_init, x, espectro_promedio)

    # Extraer los parámetros del ajuste
    amplitude_opt = gaussian_fit.amplitude.value
    mean_opt = gaussian_fit.mean.value
    stddev_opt = gaussian_fit.stddev.value

    # Graficar el espectro y el ajuste
    plt.figure()
    plt.plot(x, espectro_promedio, 'b', label='Espectro Promedio')
    plt.plot(x, gaussian_fit(x), 'r', label='Ajuste Gaussiano')
    plt.legend(loc='best')
    plt.title('Ajuste Gaussiano del Espectro Promedio')
    plt.xlabel('Índice del Píxel')
    plt.ylabel('Intensidad')

    # Imprimir los parámetros del ajuste
    print(f'Amplitud óptima: {amplitude_opt}')
    print(f'Valor medio óptimo: {mean_opt}')
    print(f'Desviación estándar óptima: {stddev_opt}')

    plt.show()
def ajuste_area_libre(espectros):
    for i, espectro in enumerate(espectros):
        # Crear un array con valores x para el ajuste
        x = np.arange(len(espectro))

        # Definir un modelo gaussiano
        gaussiano_init = models.Gaussian1D(amplitude=np.max(espectro), mean=np.argmax(espectro), stddev=1.0)

        # Inicializar el ajuste
        fitter = fitting.LevMarLSQFitter()

        # Realizar el ajuste del modelo a los datos
        gaussian_fit = fitter(gaussiano_init, x, espectro)

        # Extraer los parámetros del ajuste
        amplitude_opt = gaussian_fit.amplitude.value
        mean_opt = gaussian_fit.mean.value
        stddev_opt = gaussian_fit.stddev.value

        # Graficar el espectro y el ajuste
        plt.figure()
        plt.plot(x, espectro, 'b', label=f'Espectro del área libre {i + 1}')
        plt.plot(x, gaussian_fit(x), 'r', label='Ajuste Gaussiano')
        plt.legend(loc='best')
        plt.title(f'Ajuste Gaussiano del Espectro del área libre {i + 1}')
        plt.xlabel('Índice del Píxel')
        plt.ylabel('Intensidad')

        # Imprimir los parámetros del ajuste
        print(f'Amplitud óptima: {amplitude_opt}')
        print(f'Valor medio óptimo: {mean_opt}')
        print(f'Desviación estándar óptima: {stddev_opt}')

        plt.show()


def ajuste_gaussiano_frecuencia(frecuencias, espectro):
    # Crear un array con valores x para el ajuste
    x = frecuencias

    # Valores iniciales para los parámetros del modelo gaussiano
    amplitud_inicial = np.max(espectro)
    media_inicial = np.mean(frecuencias)  # Media inicial basada en las frecuencias
    desviacion_inicial = np.std(frecuencias)  # Desviación estándar inicial basada en las frecuencias

    # Definir un modelo gaussiano con los valores iniciales
    gaussiano_init = models.Gaussian1D(amplitude=amplitud_inicial, mean=media_inicial, stddev=desviacion_inicial)

    # Inicializar el ajuste
    fitter = fitting.LevMarLSQFitter()

    # Realizar el ajuste del modelo a los datos
    gaussian_fit = fitter(gaussiano_init, x, espectro)

    # Extraer los parámetros del ajuste
    amplitude_opt = gaussian_fit.amplitude.value
    mean_opt = gaussian_fit.mean.value
    stddev_opt = gaussian_fit.stddev.value

    # Graficar el espectro y el ajuste
    plt.figure()
    plt.plot(x, espectro, 'b', label='Espectro Promedio')
    plt.plot(x, gaussian_fit(x), 'r', label='Ajuste Gaussiano')
    plt.legend(loc='best')
    plt.title('Ajuste Gaussiano del Espectro Promedio')
    plt.xlabel('Frecuencia (GHz)')
    plt.ylabel('Intensidad')

    # Imprimir los parámetros del ajuste
    print(f'Amplitud óptima: {amplitude_opt}')
    print(f'Valor medio óptimo: {mean_opt}')
    print(f'Desviación estándar óptima: {stddev_opt}')

    plt.show()
def ajustes_grafico():
    global espectro, espectro_promedio, espectros_area_libre
    if pixel_activado:
        ajuste_gausiano(espectro)
    elif circulo_activado:
        ajuste_circulo(espectro_promedio)
    elif cuadrado_activado:
        ajuste_cuadrado(espectro_promedio)
    elif eclipse_activado:
        ajuste_elipse(espectro_promedio)
    elif area_libre_activa:
        ajuste_area_libre(espectros_area_libre)


########################################################################################################################
########################################################################################################################
# GRAFICO FRECUENCIAS #
########################################################################################################################
########################################################################################################################
def graficar_con_frecuencia(hdul):
    global frecuencias, espectro, figura_grafico, axes_grafico, ventana_grafico_abierta

    ventana_grafico_abierta = False

    if datos_cubo is not None and hdul is not None:
        try:
            espectro = datos_cubo.mean(axis=(1, 2))  # Espectro promedio de todos los píxeles

            # Comprobar si los datos de espectro contienen valores no finitos
            if np.any(np.isnan(espectro)) or np.any(np.isinf(espectro)):
                messagebox.showerror("Error", "Los datos de espectro contienen valores no finitos.")
            else:
                # Obtener los valores del header FITS
                header = hdul[0].header
                crval3 = header['CRVAL3']
                cdelt3 = header['CDELT3']

                # Calcular las frecuencias correspondientes
                frecuencias = crval3 + np.arange(len(espectro)) * cdelt3

                # Comprobar si los datos de frecuencia contienen valores no finitos
                if np.any(np.isnan(frecuencias)) or np.any(np.isinf(frecuencias)):
                    messagebox.showerror("Error", "Los datos de frecuencia contienen valores no finitos.")
                else:
                    # Crear una nueva ventana para el gráfico
                    crear_ventana_grafico_frecuencia()
                    ventana_grafico_abierta = True

                    # Crear una nueva línea para el gráfico con frecuencia en el eje X
                    figura_grafico.clear()
                    axes_grafico = figura_grafico.add_subplot(111)
                    linea_grafico, = axes_grafico.plot(frecuencias, espectro, lw=2)

                    # Establecer los límites de los ejes x e y
                    min_freq = np.nanmin(frecuencias)
                    max_freq = np.nanmax(frecuencias)
                    max_spectro = np.nanmax(espectro)
                    if not np.isnan(min_freq) and not np.isnan(max_freq) and not np.isnan(max_spectro):
                        axes_grafico.set_xlim(min_freq, max_freq)
                        axes_grafico.set_ylim(0, max_spectro)

                    # Actualizar el título del gráfico
                    axes_grafico.set_title('Espectro Promedio - Frecuencia')
                    axes_grafico.set_xlabel('Frecuencia (GHz)')
                    figura_grafico.canvas.draw()
        except Exception as e:
            messagebox.showerror("Error", str(e))

def graficar_con_frecuencia_aux():
    graficar_con_frecuencia(hdul)

########################################################################################################################
########################################################################################################################
# COMPARAR GRAFICOS #
########################################################################################################################
########################################################################################################################
def comparar_graficos(x=None, y=None, ancho=None, alto=None, angulo=None):
    global circulos_dibujados, cuadrados_dibujados, elipses_dibujadas, datos_cubo, figura_grafico, axes_grafico, ventana_grafico_abierta, linea_grafico
    global ventana_grafico, ventanas_grafico
    global circulo_activado, cuadrado_activado, eclipse_activado, pixel_activado, puntos

    ventana_grafico_abierta = False

    if datos_cubo is not None:
        try:
            figuras_a_graficar = []

            if pixel_activado:
                for i, (x, y) in enumerate(pixeles_seleccionados):
                    if x and y:
                        x = int(x)
                        y = int(y)
                        if 0 <= x < datos_cubo.shape[2] and 0 <= y < datos_cubo.shape[1]:
                            espectro = datos_cubo[:, y, x]
                            figura_a_graficar = {
                                'espectro': espectro,
                                'titulo': f'Espectro del píxel ({x}, {y})'
                            }
                            figuras_a_graficar.append(figura_a_graficar)

            elif circulo_activado:
                for i, circulo in enumerate(circulos_dibujados):
                    centro_x, centro_y = circulo.center
                    radio = circulo.radius
                    y, x = np.ogrid[-centro_y:datos_cubo.shape[1] - centro_y, -centro_x:datos_cubo.shape[2] - centro_x]
                    mascara = x ** 2 + y ** 2 <= radio ** 2
                    espectro = datos_cubo[:, mascara]

                    # Calcula el promedio del espectro por píxel dentro del área circular
                    espectro_promedio = np.mean(espectro, axis=1)
                    figura_a_graficar = {
                        'espectro': espectro_promedio,
                        'titulo': f'Área circular (Centro: ({centro_x}, {centro_y}), Radio: {radio})'
                    }
                    figuras_a_graficar.append(figura_a_graficar)

            elif cuadrado_activado:
                for i, cuadrado in enumerate(cuadrados_dibujados):
                    x_cuadrado, y_cuadrado = cuadrado.get_x(), cuadrado.get_y()
                    lado_cuadrado = cuadrado.get_width()
                    x1, x2 = int(x_cuadrado), int(x_cuadrado + lado_cuadrado)
                    y1, y2 = int(y_cuadrado), int(y_cuadrado + lado_cuadrado)

                    if 0 <= x1 < datos_cubo.shape[2] and 0 <= y1 < datos_cubo.shape[1] and \
                            0 <= x2 < datos_cubo.shape[2] and 0 <= y2 < datos_cubo.shape[1]:
                        espectro = datos_cubo[:, y1:y2, x1:x2]
                        espectro_promedio = np.mean(espectro, axis=(1, 2))
                        figura_a_graficar = {
                            'espectro': espectro_promedio,
                            'titulo': f'Área cuadrada (Inicio: ({x1}, {y1}), Lado: {lado_cuadrado})'
                        }
                        figuras_a_graficar.append(figura_a_graficar)

            elif eclipse_activado:
                for i, elipse in enumerate(elipses_dibujadas):
                    centro_x, centro_y = elipse.center
                    ancho = elipse.width
                    alto = elipse.height
                    y, x = np.ogrid[-centro_y:datos_cubo.shape[1] - centro_y, -centro_x:datos_cubo.shape[2] - centro_x]
                    mascara = ((x / (ancho / 2)) ** 2 + (y / (alto / 2)) ** 2) <= 1
                    espectro = datos_cubo[:, mascara]
                    espectro_promedio = np.mean(espectro, axis=1)
                    figura_a_graficar = {
                        'espectro': espectro_promedio,
                        'titulo': f'Área de la elipse (Centro: ({centro_x}, {centro_y}), Ancho: {ancho}, Alto: {alto})'
                    }
                    figuras_a_graficar.append(figura_a_graficar)

            if figuras_a_graficar:
                # Crear una nueva ventana para el gráfico
                crear_ventana_grafico()
                ventana_grafico_abierta = True

                for figura in figuras_a_graficar:
                    espectro = figura['espectro']
                    titulo = figura['titulo']

                    # Crear una nueva línea para el gráfico
                    linea_grafico, = axes_grafico.plot(espectro, lw=2, label=titulo)  # Agregar etiqueta a la línea

                    # Establecer los límites de los ejes x e y
                    axes_grafico.set_xlim(0, len(espectro) - 1)
                    axes_grafico.set_ylim(np.min(espectro) - 0.0002, np.max(espectro))

                # Añadir la leyenda al gráfico
                axes_grafico.legend(loc='upper right')  # Puedes cambiar la ubicación de la leyenda según lo necesites

                # Añadir la barra de desplazamiento (slider) para el zoom
                ax_zoom = plt.axes([0.1, 0.02, 0.65, 0.03])
                slider_zoom = Slider(ax_zoom, 'Zoom', 1, 10, valinit=1)

                def actualizar_zoom(val):
                    factor_zoom = slider_zoom.val
                    ax = linea_grafico.axes
                    ax.set_ylim(np.min(espectro) - 0.0002, np.max(espectro) * factor_zoom)
                    ax.figure.canvas.draw()

                slider_zoom.on_changed(actualizar_zoom)

                figura_grafico.canvas.draw()
        except ValueError:
            messagebox.showerror("Error", "Por favor, ingresa coordenadas válidas.")


def graficar_coordenadas():
    global datos_cubo, pixeles_seleccionados, pixeles_dibujados
    x = entrada_coord_x.get()
    y = entrada_coord_y.get()
    if x and y:
        x = int(x)
        y = int(y)
        if 0 <= x < datos_cubo.shape[2] and 0 <= y < datos_cubo.shape[1]:
            espectro = datos_cubo[:, y, x]

            # Dibuja el pixel en la gráfica
            tamaño_punto = 4
            pixel = ax.scatter(x, y, color='red', s=tamaño_punto)
            pixeles_dibujados.append(pixel)
            canvas.draw()

            # Grafica el espectro del pixel
            crear_ventana_grafico()
            linea_grafico, = axes_grafico.plot(espectro, lw=2)
            axes_grafico.set_xlim(0, len(espectro) - 1)
            axes_grafico.set_ylim(-0.0002, max(espectro))
            axes_grafico.set_title(f'Espectro del píxel ({x}, {y})')
            figura_grafico.canvas.draw()
        else:
            messagebox.showerror("Error", "Coordenadas fuera de los límites de la imagen.")
    else:
        messagebox.showerror("Error", "Por favor, ingresa coordenadas válidas.")


def on_image_click(event):
    global area_libre_activa, puntos
    global circulo_activado, centro_x, centro_y, radio, dibujando_circulo, ultimo_clic
    global pixel_activado, movimiento_activado

    if datos_cubo is not None and hasattr(event, 'xdata') and hasattr(event,
                                                                      'ydata') and event.xdata is not None and event.ydata is not None:
        x, y = int(event.xdata), int(event.ydata)

        # Modo "Área Libre"
        if area_libre_activa and not circulo_activado:
            puntos.append((x, y))
            punto = ax.plot(x, y,'o-', color='#39FF14', markersize=5)  # 'ro' representa un punto rojo
            puntos_dibujados.append(punto[0])  # Agrega el punto a la lista de puntos dibujados
            canvas.draw()

        if circulo_activado:
            # MECANISMO PARA CÍRCULO
            if (pixel_activado == False and movimiento_activado == False) and event.x and event.y:
                # Verificar que no sea un doble clic
                if ultimo_clic == (event.x, event.y):
                    return

                # Habilitar/deshabilitar el dibujo de círculos
                dibujando_circulo = not dibujando_circulo
                if not dibujando_circulo:
                    # Restablecer variables si se cancela el dibujo del círculo
                    centro_x, centro_y, radio = None, None, None
                # Actualizar el estado del último clic
                ultimo_clic = (event.x, event.y)

                if dibujando_circulo:
                    if centro_x is None and centro_y is None:
                        # Primer clic: establece el centro del círculo
                        centro_x, centro_y = event.x, event.y
                    else:
                        # Segundo clic: calcula el radio y dibuja el círculo
                        radio = ((event.x - centro_x) ** 2 + (event.y - centro_y) ** 2) ** 0.5
                        dibujar_circulo(event)
                        # Restablece las variables del círculo después de dibujarlo
                        centro_x, centro_y, radio = None, None, None


            elif pixel_activado and datos_cubo is not None:
                # Obtén las coordenadas de datos a partir de las coordenadas del evento
                coords_data = ax.transData.inverted().transform((event.x, event.y))
                x, y = int(coords_data[0]), int(coords_data[1])
                # Actualizar las entradas de las coordenadas
                entrada_coord_x.delete(0, tk.END)
                entrada_coord_x.insert(0, str(x))
                entrada_coord_y.delete(0, tk.END)
                entrada_coord_y.insert(0, str(y))
                # Llamar a la función para graficar el espectro
                graficar()
                actualizar_etiqueta_coordenadas()

        # Verificar si está activada la creación de elipses
        elif eclipse_activado:
            # MECANISMO PARA ELIPSE
            if (pixel_activado == False and movimiento_activado == False) and event.x and event.y:
                # Verificar que no sea un doble clic
                if ultimo_clic == (event.x, event.y):
                    return

                if not dibujando_elipse:
                    # Restablecer variables si se cancela el dibujo de la elipse
                    centro_x, centro_y, ancho, alto = None, None, None, None
                # Actualizar el estado del último clic
                ultimo_clic = (event.x, event.y)

                if dibujando_elipse:
                    if centro_x is None and centro_y is None:
                        # Primer clic: establece el centro de la elipse
                        centro_x, centro_y = event.x, event.y
                    else:
                        # Segundo clic: calcula el ancho, alto y dibuja la elipse
                        ancho = abs(event.x - centro_x) * 2
                        alto = abs(event.y - centro_y) * 2
                        dibujar_elipse(event)
                        # Restablece las variables de la elipse después de dibujarla
                        centro_x, centro_y, ancho, alto = None, None, None, None
        elif cuadrado_activado:
            # MECANISMO PARA CUADRADO
            if (pixel_activado == False and movimiento_activado == False) and event.x and event.y:
                # Verificar que no sea un doble clic
                if ultimo_clic == (event.x, event.y):
                    return

                if not dibujando_cuadrado:
                    # Restablecer variables si se cancela el dibujo del cuadrado
                    centro_x, centro_y, lado = None, None, None
                # Actualizar el estado del último clic
                ultimo_clic = (event.x, event.y)

                if dibujando_cuadrado:
                    if centro_x is None and centro_y is None:
                        # Primer clic: establece el centro del cuadrado
                        centro_x, centro_y = event.x, event.y
                    else:
                        # Segundo clic: calcula el lado y dibuja el cuadrado
                        lado = abs(event.x - centro_x) * 2
                        dibujar_cuadrado(event)
                        # Restablece las variables del cuadrado después de dibujarlo
                        centro_x, centro_y, lado = None, None, None

########################################################################################################################
########################################################################################################################
# DIBUJAR FIGURAS #
########################################################################################################################
########################################################################################################################

# FUNCION PARA DIBUJAR UNA ELIPSE #
########################################################################################################################
def dibujar_elipse(event):
    global eclipse_activado, ultima_elipse, figuras_dibujadas
    # Graficar
    global centro_x, centro_y, ancho_elipse, alto_elipse, angulo_elipse
    if eclipse_activado and event.xdata is not None and event.ydata is not None:
        x, y = event.xdata, event.ydata
        ancho = 20
        alto = 10
        elipse = Ellipse((x, y), width=ancho, height=alto, angle=0, color=(0 / 255, 255 / 255, 255 / 255), fill=False)
        ax.add_patch(elipse)
        elipses_dibujadas.append(elipse)
        ultima_elipse = elipse
        figuras_dibujadas.append(('elipse', elipse))  # Añade la elipse a la lista de figuras dibujadas

        # Para el grafico
        centro_x, centro_y = elipse.center
        ancho_elipse = elipse.width
        alto_elipse = elipse.height
        angulo_elipse = elipse.angle
    canvas.draw()

# FUNCION PARA DIBUJAR UN CUADRADO #
########################################################################################################################
def dibujar_cuadrado(event):
    global cuadrado_activado, ultimo_cuadrado, figuras_dibujadas

    if cuadrado_activado and event.xdata is not None and event.ydata is not None:
        x, y = event.xdata, event.ydata
        lado = 10  # Puedes ajustar el tamaño del cuadrado según tus preferencias
        cuadrado = Rectangle((x - lado / 2, y - lado / 2), lado, lado, color='yellow', fill=False)
        ax.add_patch(cuadrado)
        cuadrados_dibujados.append(cuadrado)  # Agrega el cuadrado a la lista de cuadrados dibujados
        ultimo_cuadrado = cuadrado  # Actualiza el último cuadrado dibujado
        figuras_dibujadas.append(('cuadrado', cuadrado))  # Añade el cuadrado a la lista de figuras dibujadas

    canvas.draw()

# FUNCION PARA DIBUJAR UN CIRCULO #
########################################################################################################################
def dibujar_circulo(event):
    global radio, ultimo_circulo, figuras_dibujadas

    if circulo_activado and event.xdata is not None and event.ydata is not None:
        x, y = event.xdata, event.ydata
        radio = 5  # Puedes ajustar el tamaño del círculo según tus preferencias
        circulo = Circle((x, y), radio, color='#FFA500', fill=False)
        ax.add_patch(circulo)

        circulos_dibujados.append(circulo)  # Agrega el círculo a la lista de círculos dibujados
        ultimo_circulo = circulo  # Actualiza el último círculo dibujado
        figuras_dibujadas.append(('circulo', circulo))  # Añade el círculo a la lista de figuras dibujadas

        # Parametros para la funcion graficar
        centro_x, centro_y = circulo.center
        radio_circulo = circulo.radius
    canvas.draw()

# FUNCION PARA DIBUJAR UN PIXEL #
########################################################################################################################
def dibujar_pixel(event):
    global pixel_activado, ultimo_pixel, pixeles_seleccionados, pixeles_dibujados, figuras_dibujadas

    if pixel_activado and event.xdata is not None and event.ydata is not None:
        x, y = event.xdata, event.ydata
        print(f"x: {x}, y: {y}")  # Agrega esta línea para imprimir las coordenadas
        # Solo para que el punto sea visible segun el pixel seleccionado por el usuario
        tamaño_punto = 0.5  # Tamaño del "píxel"
        pixel = mpatches.Circle((x, y), tamaño_punto, color='red')
        ax.add_patch(pixel)

        pixeles_dibujados.append(pixel)
        ultimo_pixel = pixel
        figuras_dibujadas.append(('pixel', pixel))  # Añade el pixel y sus coordenadas a la lista de figuras dibujadas
        # Agrega las coordenadas del pixel a la lista de pixeles seleccionados
        pixeles_seleccionados.append((x, y))

    canvas.draw()

def on_press(event):
    global cuadrado_seleccionado, circulo_seleccionado, elipse_seleccionada, pixel_seleccionado
    if event.inaxes is None: return
    for cuadrado in cuadrados_dibujados:
        if cuadrado.contains(event)[0]:
            cuadrado_seleccionado = cuadrado
            return
    for circulo in circulos_dibujados:
        if circulo.contains(event)[0]:
            circulo_seleccionado = circulo
            return
    for elipse in elipses_dibujadas:
        if elipse.contains(event)[0]:
            elipse_seleccionada = elipse
            return
    for pixel in pixeles_dibujados:
        if pixel.contains(event)[0]:
            pixel_seleccionado = pixel
            return


def on_motion(event):
    global cuadrado_seleccionado, circulo_seleccionado, elipse_seleccionada, pixel_seleccionado
    if event.inaxes is None: return
    if event.button != 1: return
    x, y = event.xdata, event.ydata
    if cuadrado_seleccionado is not None:
        lado = 10  # El tamaño del cuadrado
        cuadrado_seleccionado.set_xy((x - lado / 2, y - lado / 2))
    elif circulo_seleccionado is not None:
        radio = 5  # El tamaño del círculo
        circulo_seleccionado.center = x, y
    elif elipse_seleccionada is not None:
        ancho = 20  # El ancho de la elipse
        alto = 10  # El alto de la elipse
        elipse_seleccionada.center = x, y
    elif pixel_seleccionado is not None:
        tamaño_punto = 4  # El tamaño del punto
        #pixel_seleccionado.set_offsets([x, y])
    canvas.draw()


def on_release(event):
    global cuadrado_seleccionado, circulo_seleccionado, elipse_seleccionada, pixel_seleccionado
    cuadrado_seleccionado = None
    circulo_seleccionado = None
    elipse_seleccionada = None
    pixel_seleccionado = None

def graficar_area_libre():
    global puntos, ventana_grafico_abierta, linea_grafico, espectros_area_libre
    if len(puntos) >= 3:  # Necesitamos al menos 3 puntos para formar un polígono
        # Convierte los puntos (x, y) en una ruta (path) para el polígono
        ruta_polígono = mpath.Path(puntos)

        # Crea una grilla de coordenadas
        y_grid, x_grid = np.mgrid[0:datos_cubo.shape[1], 0:datos_cubo.shape[2]]
        coords = np.column_stack((x_grid.ravel(), y_grid.ravel()))

        # Usa la ruta del polígono para determinar qué píxeles están dentro del polígono
        mascara = ruta_polígono.contains_points(coords).reshape(datos_cubo.shape[1], datos_cubo.shape[2])

        # Calcula el espectro de los píxeles dentro del polígono
        espectro = datos_cubo[:, mascara]

        # Calcula el promedio del espectro por píxel dentro del área del polígono
        espectro_promedio = np.mean(espectro, axis=1)

        # Almacena el espectro en la lista global
        espectros_area_libre.append(espectro_promedio)
    else:
        messagebox.showerror("Error", "Dibuja al menos 3 puntos para formar un polígono.")


def calcular_espectro(puntos):
    # Convierte los puntos (x, y) en una ruta (path) para el polígono
    ruta_poligono = mpath.Path(puntos)

    # Crea una grilla de coordenadas
    y_grid, x_grid = np.mgrid[0:datos_cubo.shape[1], 0:datos_cubo.shape[2]]
    coords = np.column_stack((x_grid.ravel(), y_grid.ravel()))

    # Usa la ruta del polígono para determinar qué píxeles están dentro del polígono
    mascara = ruta_poligono.contains_points(coords).reshape(datos_cubo.shape[1], datos_cubo.shape[2])

    # Calcula el espectro de los píxeles dentro del polígono
    espectro = datos_cubo[:, mascara]

    # Calcula el promedio del espectro por píxel dentro del área del polígono
    espectro_promedio = np.mean(espectro, axis=1)

    return espectro_promedio


def conectar_puntos():
    global puntos, lineas_figura, area_libre_activa, areas_libres, espectros_area_libre, puntos_dibujados
    # Asegúrate de usar la variable global lineas_figura
    if len(puntos) >= 2:
        # Conectar los puntos en orden
        for i in range(len(puntos) - 1):
            x1, y1 = puntos[i]
            x2, y2 = puntos[i + 1]
            linea = ax.plot([x1, x2], [y1, y2],'o-', color='#39FF14')  # Conecta los puntos con una línea roja
            lineas_figura.append(linea[0])  # Agrega la línea a la lista

        # Conectar el último punto con el primer punto para cerrar el área
        x1, y1 = puntos[-1]
        x2, y2 = puntos[0]
        linea = ax.plot([x1, x2], [y1, y2], 'o-', color='#39FF14')  # Conecta el último punto con el primer punto
        lineas_figura.append(linea[0])  # Agrega la línea a la lista

        # Calcula el espectro del área libre
        espectro = calcular_espectro(puntos)

        # Almacena el espectro en la lista global
        espectros_area_libre.append(espectro)

        # Almacena la figura de área libre en la lista global
        areas_libres.append((puntos_dibujados[:], lineas_figura[:]))  # Asegúrate de copiar las listas

        # Agrega los puntos del área libre a la lista global
        puntos_area_libre.extend(puntos)

        figuras_dibujadas.append(('area_libre', (
        puntos_dibujados[:], lineas_figura[:])))  # Añade el área libre a la lista de figuras dibujadas

        # Limpia las listas para la próxima figura
        puntos = []
        puntos_dibujados = []
        lineas_figura = []
    canvas.draw()


def desactivar_area_libre():
    global area_libre_activa
    area_libre_activa = False  # Desactivar el área libre
    conectar_puntos()  # Conectar los puntos cuando se desactiva el área libre


# Función para activar/desactivar el modo de área libre
def alternar_area_libre():
    global area_libre_activa, puntos
    if area_libre_activa:
        area_libre_activa = False
        conectar_puntos()
        puntos = []  # Restablecer la lista de puntos
    else:
        area_libre_activa = True


"""        
def on_canvas_click(event):
    if event.button == 3:  # Verificar si es un clic derecho
        abrir_menu_desplegable(event)

def abrir_menu_desplegable(event):
    # Crear el menú desplegable
    menu = Menu(ventana, tearoff=0)
    # Agregar la opción "Movimiento" con el marcado correcto
    if movimiento_activado:
        menu.add_command(label="• Movimiento (activado)", command=toggle_movimiento)
    else:
        menu.add_command(label="Movimiento (desactivado)", command=toggle_movimiento)
    # Agregar la opción "Circulo"
    if circulo_activado:
        menu.add_command(label="• Circulo (activado)", command=toggle_circulo)
    else:
        menu.add_command(label="Circulo (desactivado)", command=toggle_circulo)
    # Agregar la opción "Pixel" con la variable de control
    if pixel_activado:
        menu.add_command(label="• Pixel (activado)", command=toggle_pixel)
    else:
        menu.add_command(label="Pixel (desactivado)", command=toggle_pixel)
    # Agregar la opción "Eclipse" con la variable de control
    if eclipse_activado:
        menu.add_command(label="• Eclipse (activado)", command=toggle_eclipse)
    else:
        menu.add_command(label="Eclipse (desactivado)", command=toggle_eclipse)
    # Agregar la opción "Cuadrado"
    if cuadrado_activado:
        menu.add_command(label="• Cuadrado (activado)", command=toggle_cuadrado)
    else:
        menu.add_command(label="Cuadrado (desactivado)", command=toggle_cuadrado)
    # Agregar la opción "Area libre" con la variable de control
    if area_activado:
        menu.add_command(label="• Area libre (activado)", command=toggle_area)
    else:
        menu.add_command(label="Area libre (desactivado)", command=toggle_area)

    # Mostrar el menú en la posición del clic derecho
    menu.post(event.x_root, event.y_root)

"""


def toggle_movimiento():
    global movimiento_activado, pixel_activado, circulo_activado, eclipse_activado, cuadrado_activado, area_activado, area_libre_activa
    movimiento_activado = not movimiento_activado
    pixel_activado = False
    circulo_activado = False
    eclipse_activado = False
    cuadrado_activado = False
    area_activado = False
    area_libre_activa = False
    # Desconectar los eventos de arrastre si "Movimiento" está desactivado
    if movimiento_activado:
        canvas.get_tk_widget().bind("<ButtonPress-1>", iniciar_arrastre)
        canvas.get_tk_widget().bind("<B1-Motion>", mover_imagen)
        canvas.get_tk_widget().bind("<ButtonRelease-1>", detener_arrastre)
    else:
        canvas.get_tk_widget().unbind("<ButtonPress-1>")
        canvas.get_tk_widget().unbind("<B1-Motion>")
        canvas.get_tk_widget().unbind("<ButtonRelease-1>")


# Nueva función para cambiar el estado de la opción "Pixel"
def toggle_pixel():
    global pixel_activado, movimiento_activado, circulo_activado, eclipse_activado, cuadrado_activado, area_activado, area_libre_activa
    pixel_activado = not pixel_activado
    movimiento_activado = False
    circulo_activado = False
    eclipse_activado = False
    cuadrado_activado = False
    area_activado = False
    area_libre_activa = False


# Nueva función para cambiar el estado de la opción "Círculo"
def toggle_circulo():
    global pixel_activado, movimiento_activado, circulo_activado, eclipse_activado, cuadrado_activado, area_activado, area_libre_activa
    circulo_activado = not circulo_activado
    movimiento_activado = False
    pixel_activado = False
    eclipse_activado = False
    cuadrado_activado = False
    area_activado = False
    area_libre_activa = False
    # Si desactivas la opción "Círculo", borra todos los círculos dibujados
    if not circulo_activado:
        borrar_figuras()


def toggle_eclipse():
    global pixel_activado, movimiento_activado, circulo_activado, eclipse_activado, cuadrado_activado, area_activado, area_libre_activa
    eclipse_activado = not eclipse_activado
    movimiento_activado = False
    pixel_activado = False
    circulo_activado = False
    cuadrado_activado = False
    area_activado = False
    area_libre_activa = False
    if not eclipse_activado:
        borrar_figuras()


def toggle_cuadrado():
    global cuadrado_activado, pixel_activado, movimiento_activado, circulo_activado, eclipse_activado, area_activado, area_libre_activa
    cuadrado_activado = not cuadrado_activado
    movimiento_activado = False
    pixel_activado = False
    circulo_activado = False
    eclipse_activado = False
    area_activado = False
    area_libre_activa = False
    # Si desactivas la opción "Cuadrado", borra todos los cuadrados dibujados
    if not cuadrado_activado:
        borrar_figuras()


def toggle_area():
    global pixel_activado, movimiento_activado, circulo_activado, eclipse_activado, cuadrado_activado, area_activado
    area_activado = not area_activado
    movimiento_activado = False
    pixel_activado = False
    circulo_activado = False
    eclipse_activado = False
    cuadrado_activado = False


# Función para manejar el evento de zoom con la rueda del ratón
def on_scroll(event):
    global ax
    if datos_cubo is not None:
        try:
            scale_factor = 1.1  # Puedes ajustar este valor según tus preferencias
            if event.step > 0:
                scale_factor = 1 / scale_factor  # Zoom in cuando la rueda se desplaza hacia abajo

            x_min, x_max = ax.get_xlim()
            y_min, y_max = ax.get_ylim()
            x_range = x_max - x_min
            y_range = y_max - y_min

            # Calcular los nuevos límites de los ejes
            new_x_min = x_min - x_range * 0.5 * (scale_factor - 1)
            new_x_max = x_max + x_range * 0.5 * (scale_factor - 1)
            new_y_min = y_min - y_range * 0.5 * (scale_factor - 1)
            new_y_max = y_max + y_range * 0.5 * (scale_factor - 1)

            ax.set_xlim(new_x_min, new_x_max)
            ax.set_ylim(new_y_min, new_y_max)

            canvas.draw()

        except Exception as e:
            print(f"Error en el zoom: {e}")


# Función para actualizar la barra de desplazamiento
def actualizar_barra_desplazamiento():
    global barra_desplazamiento, num_frames
    if barra_desplazamiento is not None:
        barra_desplazamiento.config(from_=1, to=num_frames, command=cargar_imagen_desde_barra)
        barra_desplazamiento.set(imagen_actual + 1)


def cerrar_ventana_principal():
    ventana.quit()  # Finalizar el bucle principal de Tkinter
    ventana.destroy()  # Destruir la ventana principal

# FUNCION PARA BORRAR TODAS LAS FIGURAS #
########################################################################################################################
def borrar_figuras():
    global cuadrados_dibujados, ultima_elipse, ultimo_circulo, ultimo_punto, pixeles_dibujados, pixeles_seleccionados, areas_libres

    # Borrar círculos
    for circulo in circulos_dibujados:
        circulo.remove()
    circulos_dibujados.clear()  # Limpia la lista de círculos dibujados

    # Borrar píxeles
    for pixel in pixeles_dibujados:
        pixel.remove()
    pixeles_dibujados.clear()  # Limpia la lista de píxeles dibujados
    pixeles_seleccionados.clear()  # Limpia la lista de píxeles seleccionados

    # Borrar elipses
    for elipse in elipses_dibujadas:
        elipse.remove()
    elipses_dibujadas.clear()  # Limpia la lista de elipses dibujadas

    # Borrar cuadrados
    for cuadrado in cuadrados_dibujados:
        cuadrado.remove()
    cuadrados_dibujados.clear()  # Limpia la lista de cuadrados dibujados

    # Limpia las líneas de la figura creada mediante la unión de puntos
    for ultimos_puntos_dibujados, ultimas_lineas_figura in areas_libres:
        for punto in ultimos_puntos_dibujados:
            punto.remove()
        for linea in ultimas_lineas_figura:
            linea.remove()
    areas_libres.clear()  # Limpia la lista de áreas libres
    puntos_area_libre.clear()

    # Limpia los espectros de las áreas libres
    espectros_area_libre.clear()

    # Añade esta línea para vaciar la lista figuras_dibujadas
    figuras_dibujadas.clear()

    canvas.draw()


# FUNCION PARA BORRAR ULTIMA FIGURA #
########################################################################################################################
def borrar_ultima_figura():
    global ultimo_circulo, ultimo_cuadrado, ultima_elipse, ultimo_pixel
    if figuras_dibujadas:
        tipo_figura, ultima_figura = figuras_dibujadas.pop()
        if tipo_figura == 'pixel':
            ultima_figura.remove()
            pixeles_dibujados.remove(ultima_figura)
            ultimo_pixel = pixeles_dibujados[-1] if pixeles_dibujados else None
            # Obtiene las coordenadas del pixel
            coordenadas_pixel = ultima_figura.center
            pixeles_seleccionados.remove(coordenadas_pixel)
        elif tipo_figura == 'circulo':
            ultima_figura.remove()
            circulos_dibujados.remove(ultima_figura)
            ultimo_circulo = circulos_dibujados[-1] if circulos_dibujados else None
        elif tipo_figura == 'elipse':
            ultima_figura.remove()
            elipses_dibujadas.remove(ultima_figura)
            ultima_elipse = elipses_dibujadas[-1] if elipses_dibujadas else None
        elif tipo_figura == 'cuadrado':
            ultima_figura.remove()
            cuadrados_dibujados.remove(ultima_figura)
            ultimo_cuadrado = cuadrados_dibujados[-1] if cuadrados_dibujados else None
        elif tipo_figura == 'area_libre':
            ultimos_puntos_dibujados, ultimas_lineas_figura = ultima_figura
            for punto in ultimos_puntos_dibujados:
                punto.remove()
                if punto in puntos_area_libre:
                    puntos_area_libre.remove(punto)
            for linea in ultimas_lineas_figura:
                linea.remove()
            areas_libres.remove((ultimos_puntos_dibujados, ultimas_lineas_figura))
            if espectros_area_libre:
                espectros_area_libre.pop()
            puntos_area_libre.clear()  # Limpia la lista de puntos de área libre
    canvas.draw()


def botones_actualizados():
    if circulo_activado:
        boton_borrar_figuras.config(state=tk.NORMAL)
        boton_borrar_ultima_figura.config(state=tk.NORMAL)
    elif pixel_activado:
        boton_borrar_figuras.config(state=tk.NORMAL)
        boton_borrar_ultima_figura.config(state=tk.NORMAL)
    elif eclipse_activado:
        boton_borrar_figuras.config(state=tk.NORMAL)
        boton_borrar_ultima_figura.config(state=tk.NORMAL)
    elif cuadrado_activado:  # Agregar lógica para cuadrados
        boton_borrar_figuras.config(state=tk.NORMAL)
        boton_borrar_ultima_figura.config(state=tk.NORMAL)

# MENU - TAMAÑO DE LA FIGURA - EQUIVALENTE - ALTO - ANCHO #
########################################################################################################################
def menu_tamano(opcion):
    global s_x, s_y
    if opcion == "Equivalente":
        s_x = s_y = t_escala.get()
        tamano_figura(t_escala.get())
    elif opcion == "Alto":
        s_y = t_escala.get()
        s_x = 1
        tamano_figura(t_escala.get())
    elif opcion == "Ancho":
        s_x = t_escala.get()
        s_y = 1
        tamano_figura(t_escala.get())
    # Establecer un límite al valor del control deslizante
    t_escala.configure(from_=1, to=100, resolution=1)

# FUNCION PARA MODIFICAR EL TAMAÑO DE LA FIGURA #
########################################################################################################################
def tamano_figura(val):
    global lado, s_x, s_y, ultima_elipse, ultimo_circulo, ultimo_cuadrado, relacion_aspecto_original
    tamano = float(val)
    # Obtener el tipo de cambio de tamaño
    opcion = menu_figura.get()
    if opcion == "Equivalente":
        if circulo_activado:
            radio = float(val)
            if ultimo_circulo is not None:
                ultimo_circulo.set_radius(radio)
        elif cuadrado_activado:  # Agregar lógica para cambiar el tamaño del cuadrado
            lado = tamano
            if ultimo_cuadrado is not None:
                # Obtén las coordenadas actuales del centro del cuadrado
                x_centro = ultimo_cuadrado.get_x() + ultimo_cuadrado.get_width() / 2
                y_centro = ultimo_cuadrado.get_y() + ultimo_cuadrado.get_height() / 2

                # Establece el nuevo ancho y alto
                ultimo_cuadrado.set_width(lado)
                ultimo_cuadrado.set_height(lado)

                # Recalcula las coordenadas de la esquina superior izquierda basándote en el centro
                ultimo_cuadrado.set_x(x_centro - lado / 2)
                ultimo_cuadrado.set_y(y_centro - lado / 2)
        elif eclipse_activado:
            if ultima_elipse is not None:
                # Obtén la relación de aspecto original de la elipse
                relacion_aspecto = ancho_elipse / alto_elipse
                # Establece el nuevo tamaño de la elipse
                ultima_elipse.set_width(tamano * relacion_aspecto)
                ultima_elipse.set_height(tamano)
        canvas.draw()
    elif opcion == "Alto":
        if circulo_activado:
            radio = tamano
            if ultimo_circulo is not None:
                ultimo_circulo.set_radius(radio)
        elif cuadrado_activado:
            lado = tamano
            if ultimo_cuadrado is not None:
                # Establece el nuevo alto
                ultimo_cuadrado.set_height(tamano)
                # Calcula el nuevo ancho
                lado = tamano * ultimo_cuadrado.get_width() / ultimo_cuadrado.get_height()
                # Establece el nuevo ancho
                ultimo_cuadrado.set_width(lado)

        elif eclipse_activado:
            if ultima_elipse is not None:
                # Establece el nuevo alto
                ultima_elipse.set_height(tamano)
        canvas.draw()

    elif opcion == "Ancho":
        if circulo_activado:
            radio = tamano
            if ultimo_circulo is not None:
                ultimo_circulo.set_radius(radio)

        elif cuadrado_activado:
            lado = tamano
            if ultimo_cuadrado is not None:
                # Establece el nuevo ancho
                ultimo_cuadrado.set_width(tamano)

                # Establece el nuevo alto
                ultimo_cuadrado.set_height(lado / tamano * ultimo_cuadrado.get_height())

        elif eclipse_activado:
            if ultima_elipse is not None:
                # Obtén la relación de aspecto original de la elipse
                relacion_aspecto = ancho_elipse / alto_elipse
                # Establece el nuevo tamaño de la elipse
                ultima_elipse.set_width(tamano * relacion_aspecto)
        canvas.draw()
########################################################################################################################
########################################################################################################################
# FUNCION VER ENCABEZADO/GRAFICO/MASCARAS #
########################################################################################################################
########################################################################################################################

# FUNCION PARA MOSTRAR EL HEADER O ENCABEZADO #
########################################################################################################################
def mostrar_encabezado():
    global hdul
    if hdul is None:
        tk.messagebox.showerror("Error", "No hay archivo FITS abierto.")
    else:
        # Muestra el encabezado en una ventana emergente con un widget Text
        header = hdul[0].header
        ventana_encabezado = tk.Toplevel(ventana)
        ventana_encabezado.title("Header del Archivo FITS")

        # Crea un widget Text para mostrar el encabezado
        texto_encabezado = tk.Text(ventana_encabezado, wrap=tk.NONE)
        texto_encabezado.insert(tk.END, repr(header))
        texto_encabezado.pack(side=tk.LEFT, padx=15, pady=15, fill=tk.BOTH, expand=True)

        # Agrega una barra de desplazamiento vertical para el widget Text
        scrollbar = tk.Scrollbar(ventana_encabezado, command=texto_encabezado.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        texto_encabezado.config(yscrollcommand=scrollbar.set)


def actualizar_estado_menu():
    global hdul, ver_menu
    if hdul is None:
        ver_menu.entryconfig("Ver Encabezado", state=tk.DISABLED)
    else:
        ver_menu.entryconfig("Ver Encabezado", state=tk.NORMAL)

# FUNCION PARA MOSTRAR LOS GRAFICOS ALMACENADOS #
########################################################################################################################
def ver_graficos():
    # Obtener todos los nombres de los gráficos de la colección "Graphics"
    nombres_graficos = [info["nombre"] for info in graphics_collection.find({}, {"_id": 0, "nombre": 1})]

    if not nombres_graficos:
        messagebox.showinfo("No hay gráficos", "No se encontraron gráficos en la base de datos.")
        return

    # Crear una nueva ventana para mostrar la lista de nombres de gráficos
    ventana_graficos = tk.Toplevel()
    ventana_graficos.title("Lista de Gráficos")
    ventana_graficos.geometry("390x230")
    ventana_graficos.configure(bg='#E6F3FF', borderwidth=2)  # Color de fondo ventana
    ventana_graficos.resizable(False, False)

    # Crear una lista desplegable para seleccionar los nombres de los gráficos
    lista_graficos = tk.Listbox(ventana_graficos)
    lista_graficos.config(width=60, height=10)
    lista_graficos.grid(row=0, column=0)

    # Crea un objeto Scrollbar
    barra_desplazamiento = tk.Scrollbar(ventana_graficos, orient="vertical")
    barra_desplazamiento.grid(row=0, column=1, sticky="nsew")

    # Establece el scroll command del cuadro de texto
    lista_graficos.config(yscrollcommand=barra_desplazamiento.set)
    # Vincula el objeto Scrollbar al cuadro de texto
    barra_desplazamiento.config(command=lista_graficos.yview)

    for nombre_grafico in nombres_graficos:
        lista_graficos.insert(tk.END, nombre_grafico)

    # Función para mostrar el gráfico seleccionado
    def mostrar_grafico_seleccionado():
        seleccion = lista_graficos.curselection()
        if seleccion:
            indice_seleccionado = seleccion[0]  # Obtener el índice de la selección
            nombre_seleccionado = nombres_graficos[indice_seleccionado]

            # Obtener los datos del gráfico seleccionado de la colección "Graphics"
            grafico_info = graphics_collection.find_one({"nombre": nombre_seleccionado})

            # Crear una nueva ventana para mostrar el gráfico y el comentario
            ventana_grafico_seleccionado = tk.Toplevel()
            ventana_grafico_seleccionado.title(f"Gráfico: {nombre_seleccionado}")

            # Convertir los datos de imagen en una imagen PIL
            imagen_data = grafico_info.get("imagen", b"")
            imagen_pil = Image.open(io.BytesIO(imagen_data))

            # Mostrar la imagen utilizando ImageTk para tkinter
            imagen_tk = ImageTk.PhotoImage(imagen_pil)
            etiqueta_imagen = tk.Label(ventana_grafico_seleccionado, image=imagen_tk)
            etiqueta_imagen.image = imagen_tk  # Evita que la imagen se elimine por la recolección de basura
            etiqueta_imagen.pack()

            # Mostrar el comentario del gráfico
            comentario = grafico_info.get("comentario", "Sin comentario")
            etiqueta_comentario = tk.Label(ventana_grafico_seleccionado, text=f"Comentario: {comentario}")
            etiqueta_comentario.pack()

            # Agregar un botón de descarga
            boton_descargar = tk.Button(
                ventana_grafico_seleccionado,
                text="Descargar",
                command=lambda: descargar_imagen(imagen_data, nombre_seleccionado)
            )
            boton_descargar.pack()

    def descargar_imagen(imagen_data, nombre_grafico):
        if not imagen_data:
            messagebox.showinfo("Sin imagen", "No hay imagen para descargar.")
            return

        # Pedir al usuario una ubicación de archivo para guardar la imagen
        archivo_destino = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("Archivos PNG", "*.png"), ("Todos los archivos", "*.*")],
            title="Guardar Imagen"
        )

        if archivo_destino:
            with open(archivo_destino, "wb") as archivo:
                archivo.write(imagen_data)

            messagebox.showinfo("Descargado", f"Imagen '{nombre_grafico}.png' descargada con éxito.")

    def eliminar_grafico_seleccionado():
        # Obtener la lista de nombres de gráficos
        nombres_graficos = [info["nombre"] for info in graphics_collection.find({}, {"_id": 0, "nombre": 1})]

        seleccion = lista_graficos.curselection()
        if seleccion:
            indice_seleccionado = seleccion[0]  # Obtener el índice de la selección
            nombre_seleccionado = nombres_graficos[indice_seleccionado]

            # Eliminar el gráfico seleccionado de la colección "Graphics"
            graphics_collection.delete_one({"nombre": nombre_seleccionado})

            # Eliminar el gráfico de la lista
            lista_graficos.delete(indice_seleccionado)

            # Actualizar la lista de nombres de gráficos
            nombres_graficos = [info["nombre"] for info in graphics_collection.find({}, {"_id": 0, "nombre": 1})]

            # Actualizar la lista
            lista_graficos.delete(0, lista_graficos.size())
            for nombre_grafico in nombres_graficos:
                lista_graficos.insert(tk.END, nombre_grafico)

            # messagebox.showinfo("Eliminado", f"Gráfico '{nombre_seleccionado}' eliminado con éxito.")


    # Agregar un botón para ver el gráfico seleccionado
    boton_ver = tk.Button(ventana_graficos, text="Ver Gráfico", command=mostrar_grafico_seleccionado)
    boton_ver.config(bg="green", fg="white")
    boton_ver.grid(row=1, column=0)

    # Agregar un botón para eliminar el gráfico seleccionado
    boton_eliminar = tk.Button(ventana_graficos, text="Eliminar", command=eliminar_grafico_seleccionado)
    boton_eliminar.config(bg="red", fg="white")
    boton_eliminar.grid(row=2, column=0)

# FUNCION PARA MOSTRAR LAS MASCARAS ALMACENADAS #
########################################################################################################################
def ver_mascaras():
    global mask_collection

    # Recupera todas las máscaras de la colección
    mascaras = mask_collection.find()

    # Crea una ventana emergente para mostrar los nombres de las máscaras
    ventana_mascaras = tk.Toplevel()
    ventana_mascaras.title("Máscaras Guardadas")
    ventana_mascaras.geometry("390x230")
    ventana_mascaras.configure(bg='#E6F3FF', borderwidth=2) #Color de fondo ventana
    ventana_mascaras.resizable(False, False)

    # Crea un cuadro de texto para mostrar los nombres de las máscaras
    cuadro_mascaras = tk.Listbox(ventana_mascaras, selectmode=tk.SINGLE)
    cuadro_mascaras.config(width=60, height=10)
    cuadro_mascaras.grid(row=0, column=0)

    # Crea un objeto Scrollbar
    barra_desplazamiento = tk.Scrollbar(ventana_mascaras, orient="vertical")
    barra_desplazamiento.grid(row=0, column=1, sticky="nsew")

    # Establece el scroll command del cuadro de texto
    cuadro_mascaras.config(yscrollcommand=barra_desplazamiento.set)
    # Vincula el objeto Scrollbar al cuadro de texto
    barra_desplazamiento.config(command=cuadro_mascaras.yview)

    # cuadro_mascaras.place(anchor="center")

    # Crea una lista de máscaras junto con sus nombres
    lista_mascaras = []

    # Agrega los nombres de las máscaras al cuadro de texto y a la lista
    for mascara in mascaras:
        nombre = mascara.get("nombre", "Sin Nombre")
        lista_mascaras.append((nombre, mascara))  # Agrega la máscara y su nombre a la lista
        cuadro_mascaras.insert(tk.END, nombre)

    def obtener_coordenadas_seleccionada():
        seleccion = cuadro_mascaras.curselection()  # Obtiene la máscara seleccionada
        if seleccion:
            indice_seleccionado = seleccion[0]
            nombre_seleccionado = cuadro_mascaras.get(indice_seleccionado)  # Obtiene el nombre seleccionado
            for nombre, mascara in lista_mascaras:
                if nombre == nombre_seleccionado:
                    coordenadas = mascara.get("coordenadas", [])
                    puntos.extend(coordenadas)  # Agrega las coordenadas a la lista de puntos
                    conectar_puntos()  # Conecta los puntos y calcula el espectro
                    area_libre_activa = True  # Habilita el modo de área libre
                    print("Área Libre Activada")  # Muestra un mensaje en la consola
                    messagebox.showinfo("Coordenadas de la Máscara",
                                        f"Coordenadas de la máscara '{nombre}': {coordenadas}")

    def eliminar_mascara_seleccionada():
        seleccion = cuadro_mascaras.curselection()  # Obtiene la máscara seleccionada
        if seleccion:
            indice_seleccionado = seleccion[0]
            nombre_seleccionado = cuadro_mascaras.get(indice_seleccionado)  # Obtiene el nombre seleccionado
            for nombre, mascara in lista_mascaras:
                if nombre == nombre_seleccionado:
                    # Elimina la máscara de la colección de máscaras
                    mask_collection.delete_one({"nombre": nombre})
                    # Elimina la máscara del cuadro de texto
                    cuadro_mascaras.delete(indice_seleccionado)

    # Crea un botón para obtener las coordenadas de la máscara seleccionada
    boton_obtener_coordenadas = tk.Button(ventana_mascaras, text="Obtener Coordenadas", command=obtener_coordenadas_seleccionada)
    boton_obtener_coordenadas.config(bg="green", fg="white")
    boton_obtener_coordenadas.grid(row=1, column=0)

    # Crea un botón para eliminar la máscara seleccionada
    boton_eliminar_mascara = tk.Button(ventana_mascaras, text="Eliminar", command=eliminar_mascara_seleccionada)
    boton_eliminar_mascara.config(bg='red', fg="white")
    boton_eliminar_mascara.grid(row=2, column=0)


def dibujar_puntos_mascara(coordenadas, ax, canvas):
    # Convierte las coordenadas en listas separadas de X e Y
    x_coords = [coord[0] for coord in coordenadas]
    y_coords = [coord[1] for coord in coordenadas]

    # Dibuja los puntos en el gráfico sin borrar el gráfico anterior
    ax.plot(x_coords, y_coords, 'ro')  # 'ro' representa círculos rojos

    # Conecta los puntos para formar un área libre
    ax.plot(x_coords + [x_coords[0]], y_coords + [y_coords[0]], 'r-')  # 'r-' representa una línea sólida roja

    # Actualiza el lienzo
    canvas.draw()


# Crear una función para configurar el menú
def configurar_menu():
    global ver_menu
    menu = tk.Menu(ventana)
    ventana.config(menu=menu)

    # Crear un menú "Archivo" con opciones
    archivo_menu = tk.Menu(menu, tearoff=0)  # Agregar tearoff=0 para eliminar la mini ventana
    menu.add_cascade(label="Archivo", menu=archivo_menu)
    archivo_menu.add_command(label="Abrir archivo", command=lambda: abrir_archivo())
    archivo_menu.add_command(label="Salir", command=ventana.destroy)

    # Crear un menú "Ver" con opciones
    ver_menu = tk.Menu(menu, tearoff=0)  # Agregar tearoff=0 para eliminar la mini ventana
    menu.add_cascade(label="Ver", menu=ver_menu)
    ver_menu.add_command(label="Ver Gráficos", command=lambda: ver_graficos())
    ver_menu.add_command(label="Ver Encabezado", command=lambda: mostrar_encabezado(),
                         state=tk.DISABLED)  # Agrega la opción de menú para ver el encabezado
    ver_menu.add_command(label="Ver Máscaras", command=lambda: ver_mascaras())



########################################################################################################################
# ELEMENTOS DE LA INTERFAZ BOTONES/SCROLLS/ETIQUETAS "
########################################################################################################################
ventana = tk.Tk()
ventana.title("Cargar Archivos Fits")
ventana.geometry("870x900")
ventana.configure(bg='#E6F3FF')
ventana.resizable(False, False)
ventana.protocol("WM_DELETE_WINDOW", cerrar_ventana_principal)
########################################################################################################################
# ETIQUETA X #
etiqueta_coord_x = tk.Label(ventana, text="Coordenada X:", bg='#E6F3FF')
etiqueta_coord_x.grid(row=1, column=1, padx=5, pady=5, sticky="e")

entrada_coord_x = tk.Entry(ventana, bd=2, relief="solid")
entrada_coord_x.grid(row=1, column=2, padx=5, pady=5)
# ETIQUETA Y #
etiqueta_coord_y = tk.Label(ventana, text="Coordenada Y:", bg='#E6F3FF')
etiqueta_coord_y.grid(row=1, column=3, padx=5, pady=5, sticky="e")

entrada_coord_y = tk.Entry(ventana, bd=2, relief="solid")
entrada_coord_y.grid(row=1, column=4, padx=5, pady=5)

########################################################################################################################
# Entry para ir directamente a un frame #
etiqueta_coord_z = tk.Label(ventana, text="imagen:", bg='#E6F3FF')
etiqueta_coord_z.grid(row=2, column=0, padx=5, pady=5, sticky="e")

entrada_coord_z = tk.Entry(ventana, bd=2, relief="solid")
entrada_coord_z.grid(row=2, column=1, padx=5, pady=5)

boton_frame = tk.Button(ventana, text="ir a imagen", command=cargar_imagen, bg='#808080', fg='white')
boton_frame.grid(row=2, column=2, padx=5, pady=10)

########################################################################################################################
# GRAFICAR SEGUN COORDENADAS #
boton_graficar_coordenadas = tk.Button(ventana, text="Graficar Coordenadas", command=graficar_coordenadas, bg='#808080', fg='white')
boton_graficar_coordenadas.grid(row=1, column=0, padx=5, pady=5)
########################################################################################################################
# CREAR MARCO PRINCIPAL #
marco_principal = tk.Frame(ventana, bg="#808080", height=900, bd=2, relief="solid")
marco_principal.grid(row=4, column=5, padx=5, pady=5)
########################################################################################################################
# MARCO: OPCIONES GRAFICAR: GRAFICAR/COMPARAR/GRAFICAR FRECUENCIAS #
########################################################################################################################
marco = tk.Frame(marco_principal, bg="#A9A9A9", width=200, height=100, bd=2, relief="solid")
marco.grid(row=2, column=0, padx=10, pady=20)
label_marco = tk.Label(marco, text="Opciones para graficar",bg="black", fg="white")
label_marco.pack(fill='x')

# Agregar el botón "Graficar" al marco
boton_graficar = tk.Button(marco, text="Graficar", command=graficar, bg="green", fg="white", state=tk.DISABLED)
boton_graficar.pack(padx=5, pady=5)

# Agregar el botón "Comparar Gráficos" al marco
boton_comparar_graficos = tk.Button(marco, text="Comparar Gráficos", command=comparar_graficos, bg='#008000', fg='white')
boton_comparar_graficos.pack(padx=5, pady=5)

# Agregar el botón "Comparar Gráficos" al marco
boton_graficarFrecuencia = tk.Button(marco, text="Grafico de frecuencia", command=graficar_con_frecuencia_aux, bg='#008000', fg='white')
boton_graficarFrecuencia.pack(padx=5, pady=5)
########################################################################################################################
# MARCO: OPCIONES DE BORRAR/ BORRAR ULTIMMA FIGURA #
########################################################################################################################

# Crear un marco para las opciones de borrado #
marco_borrado = tk.Frame(marco_principal, bg="#A9A9A9", width=200, height=100, bd=2, relief="solid")
marco_borrado.grid(row=1, column=0, padx=10, pady=20)
label_borrado = tk.Label(marco_borrado, text="Opciones de borrar",bg="black", fg="white")
label_borrado.pack(fill='x')

# BORRAR FIGURAS #
boton_borrar_figuras = tk.Button(marco_borrado, text="Borrar Figuras", command=borrar_figuras, bg='#8B0000', fg='white')
boton_borrar_figuras.pack(padx=5, pady=5)

# BORRAR ULTIMA FIGURA #
boton_borrar_ultima_figura = tk.Button(marco_borrado, text="Borrar Última Figura", command=borrar_ultima_figura, bg='#8B0000', fg='white')
boton_borrar_ultima_figura.pack(padx=5, pady=5)
########################################################################################################################
# inicio en 0  para no tener errores
entrada_coord_z.insert(0, "0")

########################################################################################################################
# SCROLL Y BOTONOS SIGUIENTE/ANTERIOR PARA ARCHIVO FITS #

# BOTON ANTERIOR #
boton_anterior = tk.Button(ventana, text="Anterior", command=cargar_imagen_anterior, state=tk.DISABLED, bg='#808080', fg='white')
boton_anterior.grid(row=3, column=0, padx=5, pady=5)

# BOTON SIGUIENTE #
boton_siguiente = tk.Button(ventana, text="Siguiente", command=cargar_siguiente_imagen, state=tk.DISABLED, bg='#808080', fg='white')
boton_siguiente.grid(row=3, column=4, padx=5, pady=5)

# BARRA HORIZONTAL O SCROLL #
barra_desplazamiento = tk.Scale(ventana, orient="horizontal", command=cargar_imagen_desde_barra, bg='#E6F3FF')
barra_desplazamiento.grid(row=3, column=1, columnspan=3, padx=5, pady=5, sticky="ew")
########################################################################################################################

# Crear una figura de Matplotlib y canvas
fig = Figure(figsize=(6, 6))
ax = fig.add_subplot(111)
canvas = FigureCanvasTkAgg(fig, master=ventana)
canvas_widget = canvas.get_tk_widget()
canvas_widget.config(bd=2, relief="solid")  # Agregar un borde
canvas_widget.grid(row=4, column=0, columnspan=5, padx=5, pady=10)

"""canvas.get_tk_widget().bind("<Button-3>", abrir_menu_desplegable)"""
canvas.get_tk_widget().bind("<Button-1>", on_image_click)

# Conectar la función on_scroll al evento de desplazamiento de la rueda del ratón
fig.canvas.mpl_connect('scroll_event', on_scroll)

# Configurar el evento de clic del ratón en la imagen
fig.canvas.mpl_connect('button_press_event', on_image_click)

# Configurar el evento de clic del ratón en la imagen
fig.canvas.mpl_connect('button_press_event', on_image_click)

# Configurar el evento de clic izquierdo en el canvas para dibujar un círculo
canvas.mpl_connect('button_press_event', dibujar_circulo)

# Configurar el evento de clic izquierdo en el canvas para dibujar una elipse
canvas.mpl_connect('button_press_event', dibujar_elipse)

canvas.mpl_connect('button_press_event', dibujar_cuadrado)

canvas.mpl_connect('button_press_event', dibujar_pixel)

# Conecta los eventos con las funciones correspondientes
canvas.mpl_connect('button_press_event', on_press)
canvas.mpl_connect('motion_notify_event', on_motion)
canvas.mpl_connect('button_release_event', on_release)

# combobox selector
def cambiar_tipo_figura(event):
    global movimiento_activado, pixel_activado, circulo_activado, eclipse_activado, cuadrado_activado, area_activado, area_libre_activa
    seleccion = combooptions.get()

    # Si la opción de área libre estaba activada, conecta los puntos antes de cambiar a la nueva opción
    if area_activado:
        alternar_area_libre()

    # Restablecer todas las opciones a False
    movimiento_activado = False
    pixel_activado = False
    circulo_activado = False
    eclipse_activado = False
    cuadrado_activado = False
    area_activado = False

    if seleccion == "Movimiento":
        movimiento_activado = True
        # Habilitar eventos relacionados con el movimiento
        canvas.get_tk_widget().bind("<ButtonPress-1>", iniciar_arrastre)
        canvas.get_tk_widget().bind("<B1-Motion>", mover_imagen)
        canvas.get_tk_widget().bind("<ButtonRelease-1>", detener_arrastre)
    elif seleccion == "Pixel":
        pixel_activado = True
        desactivar_area_libre()
    elif seleccion == "Circulo":
        circulo_activado = True
        desactivar_area_libre()
    elif seleccion == "Elipse":
        eclipse_activado = True
        desactivar_area_libre()
    elif seleccion == "Cuadrado":
        cuadrado_activado = True
        desactivar_area_libre()
    elif seleccion == "Area Libre":
        alternar_area_libre()  # Llama a alternar_area_libre cuando se selecciona "Area Libre"

    # Deshabilitar eventos relacionados con el movimiento si no está seleccionado
    if seleccion != "Movimiento":
        canvas.get_tk_widget().unbind("<ButtonPress-1>")
        canvas.get_tk_widget().unbind("<B1-Motion>")
        canvas.get_tk_widget().unbind("<ButtonRelease-1>")


########################################################################################################################
# MARCO: MENU DE OPCIONES: MOVIMIENTO/CUADRADO/PIXEL/CIRCULO/ELIPSE/AREALIBRE #
########################################################################################################################

# Crear un marco para las opciones de figura
marco_figura = tk.Frame(marco_principal, bg="#A9A9A9", width=200, height=100, bd=2, relief="solid")
marco_figura.grid(row=0, column=0, padx=10, pady=20)
label_figura = tk.Label(marco_figura, text="Menú de opciones",  bg="black", fg="white")
label_figura.pack(fill='x')

# Agregar el ComboBox al marco
combooptions = ttk.Combobox(marco_figura, values=["--select items--", "Movimiento", "Cuadrado", "Pixel", "Circulo", "Elipse", "Area Libre"])
combooptions.pack(padx=5, pady=5)
combooptions.configure(state="readonly")
combooptions.current(0)

# Enlazar la función cambiar_tipo_figura al ComboBox
combooptions.bind("<<ComboboxSelected>>", cambiar_tipo_figura)
configurar_menu()

########################################################################################################################
# MARCO: TAMAÑO DE LA FIGURA #
########################################################################################################################

# Crear un marco para las opciones de tamaño de figura
marco_tamano = tk.Frame(marco_principal, bg="#A9A9A9", width=200, height=100, bd=2, relief="solid")
marco_tamano.grid(row=3, column=0, padx=10, pady=20)
label_tamano = tk.Label(marco_tamano, text="Opciones de tamaño figura", bg="black", fg="white")
label_tamano.pack(fill='x')
    
# Agregar el menú de opciones de tamaño al marco
menu_figura = ttk.Combobox(marco_tamano, values=["Equivalente", "Alto", "Ancho"])
menu_figura.pack(padx=5, pady=5)
menu_figura.configure(state="readonly")
menu_figura.current(0)
########################################################################################################################
# Configurar el combobox para llamar a la función adecuada cuando cambie el valor
menu_figura.bind("<<ComboboxSelected>>", lambda e: menu_tamano(menu_figura.get()))
# Crear un control deslizante para cambiar el tamaño de las figuras

# Agregar la barra de desplazamiento al marco
t_escala = tk.Scale(marco_tamano, from_=1, to=100, orient="horizontal", command=tamano_figura, width=20)
t_escala.pack(padx=5, pady=5)
ventana.mainloop()