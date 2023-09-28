import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox, Toplevel, Menu
from astropy.io import fits
import pymongo
from datetime import datetime
import matplotlib
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
import uuid
from matplotlib.patches import Circle, Ellipse, Rectangle
from matplotlib.figure import Figure
from tkinter import Scale


data_id = str(uuid.uuid4())
graphic_id = str(uuid.uuid4())
matplotlib.use("TkAgg")

###########para lo de el area libre####################################

# Variables para la creación del área libre
area_libre_activa = False
puntos = []
lineas_figura = []
puntos_dibujados = []

###########para lo de el area libre####################################





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
movimiento_activado = False  # Variable para rastrear el estado del movimiento
pixel_activado = False  # Variable para rastrear el estado de la opción "Pixel"
circulo_activado = False  # Variable para rastrear el estado de la opción "Círculo"
eclipse_activado = False  # Variable para rastrear el estado del movimiento
cuadrado_activado = False  # Variable para rastrear el estado de la opción "Pixel"
area_activado = False  # Variable para rastrear el estado de la opción "Círculo"
ultimo_clic = None

# Variables para el seguimiento del arrastre del ratón
dragging = False



# Variables relacionadas con Matplotlib
fig = None
ax = None
canvas = None
linea_grafico = None
barra_desplazamiento = None
circulos_dibujados = []  # Lista para almacenar los círculos dibujados
radio_scale = None  # Variable para el scrollbar del radio del círculo
radio = 5  # Valor predeterminado del radio del círculo
ultimo_circulo = None  # Variable para el último círculo dibujado

# Variables Elipse
e_inicio = None
e_fin = None
ultima_elipse = None
s_x = 1.0
s_y = 1.0
elipses_dibujadas = []  # Lista para almacenar los círculos dibujados

# Variables para el circulo
centro_x, centro_y = None, None
dibujando_circulo = False
circulo_dibujado = None

#variables para cuadrado
cuadrado_activado = False
cuadrados_dibujados = []  # Lista para almacenar los cuadrados dibujados
ultimo_cuadrado = None  # Variable para mantener un seguimiento del último cuadrado dibujado



cliente = pymongo.MongoClient("mongodb://localhost:27017/")
base_datos = cliente["Astronomy"]
# File_collection
file_collection = base_datos["File_collection"]
# Data_collection
data_collection = base_datos["Data_collection"]
# Graphics
graphics_collection = base_datos["Graphics"]
# Comments
comments_collection = base_datos["Comments"]


# Función para cargar la imagen FITS actual
def cargar_imagen_actual():
    global imagen_actual
    ax.clear()
    ax.imshow(datos_cubo[imagen_actual], cmap='gray')
    ax.set_title(f"Imagen {imagen_actual + 1}/{num_frames}")
    canvas.draw()
    actualizar_etiqueta_coordenadas()


# Función para actualizar la etiqueta de coordenadas
def actualizar_etiqueta_coordenadas():
    global coordenadas_label
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
    global ventana_grafico, figura_grafico, axes_grafico, canvas_grafico, ventana_grafico_abierta
    if not ventana_grafico_abierta:
        ventana_grafico = Toplevel()
        ventana_grafico.title("Gráfico del Espectro")
        figura_grafico, axes_grafico = plt.subplots(figsize=(6, 4))
        canvas_grafico = FigureCanvasTkAgg(figura_grafico, master=ventana_grafico)
        canvas_grafico.get_tk_widget().pack()
        ventana_grafico.protocol("WM_DELETE_WINDOW", cerrar_ventana_grafico)
        ventana_grafico_abierta = True


# Función para cerrar la ventana emergente del gráfico
def cerrar_ventana_grafico():
    global ventana_grafico, ventana_grafico_abierta
    if ventana_grafico:
        ventana_grafico.destroy()
        # Restablecer las variables de la figura y los ejes
        figura_grafico.clf()
        axes_grafico = figura_grafico.add_subplot(111)
        figura_grafico.canvas.draw()
        ventana_grafico_abierta = False

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



# Función para cargar un archivo FITS
def abrir_archivo():
    global archivo_fits, hdul, datos_cubo, num_frames, boton_anterior, boton_siguiente, boton_graficar

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
                    # Con esto buscamos la extension buscada, para abrir solo estas.
                    break

            if extension_valida is None:
                raise ValueError("No es posible abrir este tipo de archivo FITS, dado que no contiene imágenes.")

            if np.any(np.isnan(extension_valida.data)) or np.any(np.isinf(extension_valida.data)):
                respuesta = messagebox.askquestion("Datos Inválidos",
                                                   "El archivo FITS contiene datos inválidos (NaN o infinitos). ¿Desea convertirlos a 0?")

                if respuesta == 'yes':
                    data = remove_nans(extension_valida)

            header = extension_valida.header
            print(header)  # Imprimir el encabezado para ver la información

            datos_cubo = extension_valida.data
            tipo_extension = extension_valida.name
            fecha_actual = datetime.now()

            num_frames, num_rows, num_columns = datos_cubo.shape
            print(f"Número de cuadros: {num_frames}")
            print(f"Número de filas: {num_rows}")
            print(f"Número de columnas: {num_columns}")
            cargar_imagen_actual()  # Cargar la primera imagen
            # Habilitar los botones "Anterior" y "Siguiente"
            boton_anterior.config(state=tk.NORMAL)
            boton_siguiente.config(state=tk.NORMAL)
            # Habilitar el botón "Graficar"
            boton_graficar.config(state=tk.NORMAL)
            actualizar_etiqueta_coordenadas()  # Agregado para actualizar coordenadas al cargar el archivo
            actualizar_barra_desplazamiento()
            # Base de datos = File_Collection
            file_info = {
                "Data_id": data_id,                          # Identificador
                "File_name": nombre_archivo,                 # File
                "Fecha": fecha_actual.strftime("%d/%m/%Y"),  # Fecha segun día/mes/año
                "Hora": fecha_actual.strftime("%H:%M:%S")    # Fecha segun Hora
            }
            file_collection.insert_one(file_info)

            # Base de datos = Data_Collection
            data_info = {
                "Data_id": data_id,                          # Identificador
                "Filename": nombre_archivo,                  # File
                "Header": tipo_extension,                    # Encabezado
                "Fecha": fecha_actual.strftime("%d/%m/%Y"),  # Fecha segun día/mes/año
                "Hora": fecha_actual.strftime("%H:%M:%S"),   # Fecha segun Hora
                "Data": str(datos_cubo)  # Datos
            }
            data_collection.insert_one(data_info)

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el archivo FITS: {str(e)}")
            boton_graficar.config(state=tk.DISABLED)
    else:
        # Si no se selecciona un archivo FITS válido, deshabilita el botón "Graficar"
        boton_graficar.config(state=tk.DISABLED)


# Función para graficar el espectro del píxel seleccionado
def graficar(x=None,y=None, ancho=None, alto= None, angulo = None):
    global circulos_dibujados, datos_cubo, figura_grafico, axes_grafico, ventana_grafico_abierta, linea_grafico
    global linea_grafico, figura_grafico, axes_grafico, ventana_grafico, ventana_grafico_abierta
    if datos_cubo is not None:
        try:
            if pixel_activado:
                print("iff")
                if x and y:
                    print("iff")
                    x = int(x)
                    y = int(y)
                    if 0 <= x < datos_cubo.shape[2] and 0 <= y < datos_cubo.shape[1]:
                        espectro = datos_cubo[:, y, x]
                        if not ventana_grafico_abierta:
                            crear_ventana_grafico()
                            linea_grafico, = axes_grafico.plot(espectro, lw=2)
                            axes_grafico.set_xlabel('Frame')
                            axes_grafico.set_ylabel('Intensidad')
                            ventana_grafico_abierta = True
                        else:
                            # Si ya existe la línea, actualiza sus datos
                            linea_grafico.set_ydata(espectro)

                        # Establecer los límites de los ejes x e y
                        axes_grafico.set_xlim(0, len(espectro) - 1)
                        axes_grafico.set_ylim(-0.0002, max(espectro))

                        # Actualiza el título del gráfico con las coordenadas
                        axes_grafico.set_title(f'Espectro del píxel ({x}, {y})')
                        figura_grafico.canvas.draw()
                        fecha_actual = datetime.now()
                    else:
                        messagebox.showerror("Error", "Coordenadas fuera de los límites de la imagen.")

                    # Base de datos = Graphics_Colletion
                    selected_pixel = f"({x}, {y})"
                    graphics_info = {
                        "Graphic_id": graphic_id,                     # Identificador unico
                        "Imagen": imagen_actual + 1,
                        "Pixeles": selected_pixel,                    # Pixeles segun x e y
                        "Fecha": fecha_actual.strftime("%d/%m/%Y"),   # Fecha segun día/mes/año
                        "Hora": fecha_actual.strftime("%H:%M:%S"),    # Fecha segun Hora
                        "Data": str(espectro)                         # Representacion de los datos
                    }
                    graphics_collection.insert_one(graphics_info)

                else:
                    messagebox.showerror("Error", "Por favor, ingresa coordenadas válidas.")
            elif circulo_activado:
                if len(circulos_dibujados) == 1:
                    circulo = circulos_dibujados[0]
                    centro_x, centro_y = circulo.center
                    radio = circulo.radius
                    y, x = np.ogrid[-centro_y:datos_cubo.shape[1] - centro_y, -centro_x:datos_cubo.shape[2] - centro_x]
                    mascara = x ** 2 + y ** 2 <= radio ** 2
                    espectro = datos_cubo[:, mascara]

                    # Calcula el promedio del espectro por píxel dentro del área circular
                    espectro_promedio = np.mean(espectro, axis=1)

                    if not ventana_grafico_abierta:
                        crear_ventana_grafico()
                        linea_grafico, = axes_grafico.plot(espectro_promedio, lw=2)
                        axes_grafico.set_xlabel('Frame')
                        axes_grafico.set_ylabel('Intensidad')
                        ventana_grafico_abierta = True
                    else:
                        linea_grafico.set_ydata(espectro_promedio)

                    axes_grafico.set_xlim(0, len(espectro_promedio) - 1)
                    axes_grafico.set_ylim(np.min(espectro_promedio) - 0.0002, np.max(espectro_promedio))

                    # Actualiza el título del gráfico con la información del círculo y el promedio
                    axes_grafico.set_title(
                        f'Promedio del Espectro por píxel en el área circular (Centro: ({centro_x}, {centro_y}), Radio: {radio})')
                    figura_grafico.canvas.draw()
                else:
                    messagebox.showerror("Error",
                                        "Selecciona exactamente un círculo para graficar el promedio del espectro por píxel.")
            elif cuadrado_activado:
                if len(cuadrados_dibujados) == 1:
                    cuadrado = cuadrados_dibujados[0]
                    x_cuadrado, y_cuadrado = cuadrado.get_x(), cuadrado.get_y()
                    lado_cuadrado = cuadrado.get_width()
                    x1, x2 = int(x_cuadrado), int(x_cuadrado + lado_cuadrado)
                    y1, y2 = int(y_cuadrado), int(y_cuadrado + lado_cuadrado)

                    if 0 <= x1 < datos_cubo.shape[2] and 0 <= y1 < datos_cubo.shape[1] and \
                            0 <= x2 < datos_cubo.shape[2] and 0 <= y2 < datos_cubo.shape[1]:
                        espectro = datos_cubo[:, y1:y2, x1:x2]

                        # Calcula el promedio del espectro por píxel dentro del área del cuadrado
                        espectro_promedio = np.mean(espectro, axis=(1, 2))

                        if not ventana_grafico_abierta:
                            crear_ventana_grafico()
                            linea_grafico, = axes_grafico.plot(espectro_promedio, lw=2)
                            axes_grafico.set_xlabel('Frame')
                            axes_grafico.set_ylabel('Intensidad')
                            ventana_grafico_abierta = True
                        else:
                            linea_grafico.set_ydata(espectro_promedio)

                        axes_grafico.set_xlim(0, len(espectro_promedio) - 1)
                        axes_grafico.set_ylim(np.min(espectro_promedio) - 0.0002, np.max(espectro_promedio))

                        # Actualiza el título del gráfico con la información del cuadrado y el promedio
                        axes_grafico.set_title(
                            f'Promedio del Espectro por píxel en el área cuadrada (Inicio: ({x1}, {y1}), Lado: {lado_cuadrado})')
                        figura_grafico.canvas.draw()
                    else:
                        messagebox.showerror("Error", "Coordenadas del cuadrado fuera de los límites de la imagen.")
                else:
                    messagebox.showerror("Error",
                                         "Selecciona exactamente un cuadrado para graficar el promedio del espectro por píxel.")

            elif eclipse_activado:
                print("grafico")
                if len(elipses_dibujadas) == 1:
                    elipse = elipses_dibujadas[0]
                    centro_x, centro_y = elipse.center
                    ancho = elipse.width
                    alto = elipse.height

                    # Calcula la máscara para el área dentro de la elipse
                    y, x = np.ogrid[-centro_y:datos_cubo.shape[1] - centro_y, -centro_x:datos_cubo.shape[2] - centro_x]
                    mascara = ((x / (ancho / 2)) ** 2 + (y / (alto / 2)) ** 2) <= 1
                    espectro = datos_cubo[:, mascara]

                    # Calcula el promedio del espectro por píxel dentro del área de la elipse
                    espectro_promedio = np.mean(espectro, axis=1)

                    if not ventana_grafico_abierta:
                        crear_ventana_grafico()
                        linea_grafico, = axes_grafico.plot(espectro_promedio, lw=2)
                        axes_grafico.set_xlabel('Frame')
                        axes_grafico.set_ylabel('Intensidad')
                        ventana_grafico_abierta = True
                    else:
                        linea_grafico.set_ydata(espectro_promedio)

                    axes_grafico.set_xlim(0, len(espectro_promedio) - 1)
                    axes_grafico.set_ylim(np.min(espectro_promedio) - 0.0002, np.max(espectro_promedio))

                    # Actualiza el título del gráfico con la información de la elipse y el promedio
                    axes_grafico.set_title(
                        f'Promedio del Espectro por píxel en el área de la elipse (Centro: ({centro_x}, {centro_y}), Ancho: {ancho}, Alto: {alto})')
                    figura_grafico.canvas.draw()
                else:
                    messagebox.showerror("Error",
                                         "Selecciona exactamente una elipse para graficar el promedio del espectro por píxel.")

            elif area_libre_activa:
                if len(puntos) >= 3:  # Necesitamos al menos 3 puntos para formar un polígono
                    # Crea un objeto Path a partir de los puntos
                    path = matplotlib.path.Path(puntos)

                    # Crea una grilla de coordenadas
                    y_grid, x_grid = np.mgrid[0:datos_cubo.shape[1], 0:datos_cubo.shape[2]]
                    coords = np.column_stack((x_grid.ravel(), y_grid.ravel()))

                    # Usa el objeto Path para determinar qué píxeles están dentro del polígono
                    mascara = path.contains_points(coords).reshape(datos_cubo.shape[1], datos_cubo.shape[2])

                    # Calcula el espectro de los píxeles dentro del polígono
                    espectro = datos_cubo[:, mascara]

                    # Calcula el promedio del espectro por píxel dentro del área del polígono
                    espectro_promedio = np.mean(espectro, axis=1)

        except ValueError:
            messagebox.showerror("Error", "Por favor, ingresa coordenadas válidas.")



###########para lo de el area libre####################################
# Función para conectar los puntos y formar la figura
def conectar_puntos():
    global puntos, lineas_figura  # Asegúrate de usar la variable global lineas_figura
    if len(puntos) >= 2:
        # Conectar los puntos en orden
        for i in range(len(puntos) - 1):
            x1, y1 = puntos[i]
            x2, y2 = puntos[i + 1]
            linea = ax.plot([x1, x2], [y1, y2], 'ro-')  # Conecta los puntos con una línea roja
            lineas_figura.append(linea[0])  # Agrega la línea a la lista

        # Conectar el último punto con el primer punto para cerrar el área
        x1, y1 = puntos[-1]
        x2, y2 = puntos[0]
        linea = ax.plot([x1, x2], [y1, y2], 'ro-')  # Conecta el último punto con el primer punto
        lineas_figura.append(linea[0])  # Agrega la línea a la lista

        canvas.draw()

# Función para activar/desactivar el modo de área libre
def alternar_area_libre():
    global area_libre_activa, puntos
    if area_libre_activa:
        area_libre_activa = False
        # Aquí puedes conectar los puntos para formar la figura
        conectar_puntos()
        puntos = []  # Restablecer la lista de puntos
        boton_area_libre.config(text="Activar Área Libre")
    else:
        area_libre_activa = True
        boton_area_libre.config(text="Desactivar Área Libre")

###########para lo de el area libre####################################

def on_image_click(event):
    global area_libre_activa, puntos
    global circulo_activado, centro_x, centro_y, radio, dibujando_circulo, ultimo_clic
    global pixel_activado, movimiento_activado

    if datos_cubo is not None and hasattr(event, 'xdata') and hasattr(event, 'ydata') and event.xdata is not None and event.ydata is not None:
        x, y = int(event.xdata), int(event.ydata)
        if area_libre_activa:
            if not circulo_activado:  # Modo "Área Libre"
                puntos.append((x, y))
                punto = ax.plot(x, y, 'ro', markersize=5)  # 'ro' representa un punto rojo
                puntos_dibujados.append(punto[0])  # Agrega el punto a la lista de puntos dibujados
                canvas.draw()
            elif pixel_activado:  # Modo de selección de píxeles
                entrada_coord_x.delete(0, tk.END)
                entrada_coord_x.insert(0, str(x))
                entrada_coord_y.delete(0, tk.END)
                entrada_coord_y.insert(0, str(y))
                graficar()
                actualizar_etiqueta_coordenadas()
            elif not movimiento_activado:  # Modo de dibujo de círculo
                if ultimo_clic == (x, y):
                    return

                dibujando_circulo = not dibujando_circulo
                if not dibujando_circulo:
                    centro_x, centro_y, radio = None, None, None

                ultimo_clic = (x, y)

                if dibujando_circulo:
                    if centro_x is None and centro_y is None:
                        centro_x, centro_y = x, y
                    else:
                        radio = ((x - centro_x) ** 2 + (y - centro_y) ** 2) ** 0.5
                        dibujar_circulo(event)
                        centro_x, centro_y, radio = None, None, None

    # Verificar si está activada la creación de elipses
    elif eclipse_activado:
        # MECANISMO PARA ELIPSE
        if (pixel_activado == False and movimiento_activado == False) and event.x and event.y:
            # Verificar que no sea un doble clic
            if ultimo_clic == (event.x, event.y):
                return

            # Habilitar/deshabilitar el dibujo de elipses
            dibujando_elipse = not dibujando_elipse
            if not dibujando_elipse:
                # Restablecer variables si se cancela el dibujo de la elipse
                centro_elipse_x, centro_elipse_y, s_x, s_y = None, None, None, None
            # Actualizar el estado del último clic
            ultimo_clic = (event.x, event.y)

            if dibujando_elipse:
                if centro_elipse_x is None and centro_elipse_y is None:
                    # Primer clic: establece el centro de la elipse
                    centro_elipse_x, centro_elipse_y = event.x, event.y
                else:
                    # Segundo clic: establece los semiejes y dibuja la elipse
                    e_fin = (event.x, event.y)
                    dibujar_elipse_segun_puntos((centro_elipse_x, centro_elipse_y), e_fin)
                    # Restablece las variables de la elipse después de dibujarla
                    centro_elipse_x, centro_elipse_y, s_x, s_y = None, None, None, None

###########para lo de el area libre####################################


# Funcion para dibujar una elipse
def dibujando_elipse(event):
    global e_inicio, e_fin, ultima_elipse

    if eclipse_activado and event.xdata is not None and event.ydata is not None:
        x, y = event.xdata, event.ydata
        if e_inicio is None:
            # Primer clic: establece el punto de inicio de la elipse
            e_inicio = (x, y)
        else:
            # Segundo clic: establece el punto final de la elipse
            # Dibuja la elipse
            e_fin = (x, y)
            dibujar_elipse_segun_puntos(e_inicio, e_fin)

            # Restablece las variables de la elipse después de dibujarla
            e_inicio = None
            e_fin = None
def dibujar_elipse_segun_puntos(inicio, fin):
    global ultima_elipse
    s_x = 1.0
    s_y = 1.0
    x1, y1 = inicio
    x2, y2 = fin

    # Calcula los semiejes a y b
    s_x = abs(e_fin[0] - e_inicio[0]) / 2
    s_y = abs(e_fin[1] - e_inicio[1]) / 2
    # Centro de la elipse
    centro_elipse_x = (x1 + x2) / 2
    centro_elipse_y = (y1 + y2) / 2

    elipse = Ellipse((centro_elipse_x, centro_elipse_y), s_x, s_y, color='blue', fill=False)
    ax.add_patch(elipse)
    elipses_dibujadas.append(elipse)  # Agrega la elipse a la lista de elipses dibujadas
    ultima_elipse = elipse  # Actualiza la última elipse dibujada

    canvas.draw()


def dibujar_cuadrado(event):
    global cuadrado_activado, ultimo_cuadrado

    if cuadrado_activado and event.xdata is not None and event.ydata is not None:
        x, y = event.xdata, event.ydata
        lado = 10  # Puedes ajustar el tamaño del cuadrado según tus preferencias
        cuadrado = Rectangle((x - lado / 2, y - lado / 2), lado, lado, color='green', fill=False)
        ax.add_patch(cuadrado)
        cuadrados_dibujados.append(cuadrado)  # Agrega el cuadrado a la lista de cuadrados dibujados
        ultimo_cuadrado = cuadrado  # Actualiza el último cuadrado dibujado

    canvas.draw()



# Función para dibujar un círculo en el subplot de Matplotlib
def dibujar_circulo(event):
    global radio, ultimo_circulo

    if circulo_activado and event.xdata is not None and event.ydata is not None:
        x, y = event.xdata, event.ydata
        radio = 5  # Puedes ajustar el tamaño del círculo según tus preferencias
        circulo = Circle((x, y), radio, color='red', fill=False)
        ax.add_patch(circulo)
        circulos_dibujados.append(circulo)  # Agrega el círculo a la lista de círculos dibujados
        ultimo_circulo = circulo  # Actualiza el último círculo dibujado

    canvas.draw()

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


def toggle_movimiento():
    global movimiento_activado, pixel_activado, circulo_activado, eclipse_activado, cuadrado_activado, area_activado
    movimiento_activado = not movimiento_activado
    pixel_activado = False
    circulo_activado = False
    eclipse_activado = False
    cuadrado_activado = False
    area_activado = False
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
    global pixel_activado, movimiento_activado, circulo_activado, eclipse_activado, cuadrado_activado, area_activado
    pixel_activado = not pixel_activado
    movimiento_activado = False
    circulo_activado = False
    eclipse_activado = False
    cuadrado_activado = False
    area_activado = False

# Nueva función para cambiar el estado de la opción "Círculo"
def toggle_circulo():
    global pixel_activado, movimiento_activado, circulo_activado, eclipse_activado, cuadrado_activado, area_activado
    circulo_activado = not circulo_activado
    movimiento_activado = False
    pixel_activado = False
    eclipse_activado = False
    cuadrado_activado = False
    area_activado = False
    # Si desactivas la opción "Círculo", borra todos los círculos dibujados
    if not circulo_activado:
        borrar_figuras()

def toggle_eclipse():
    global pixel_activado, movimiento_activado, circulo_activado, eclipse_activado, cuadrado_activado, area_activado
    eclipse_activado = not eclipse_activado
    movimiento_activado = False
    pixel_activado = False
    circulo_activado = False
    cuadrado_activado = False
    area_activado = False
    if not eclipse_activado:
        borrar_figuras()

def toggle_cuadrado():
    global cuadrado_activado, pixel_activado, movimiento_activado, circulo_activado, eclipse_activado, area_activado
    cuadrado_activado = not cuadrado_activado
    movimiento_activado = False
    pixel_activado = False
    circulo_activado = False
    eclipse_activado = False
    area_activado = False
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


# ...

def borrar_figuras():
    global cuadrados_dibujados, ultima_elipse, ultimo_circulo, lineas_figura, puntos

    if circulo_activado:
        for circulo in circulos_dibujados:
            circulo.remove()
        circulos_dibujados.clear()  # Limpia la lista de círculos dibujados
    elif eclipse_activado:
        for elipse in elipses_dibujadas:
            elipse.remove()
        elipses_dibujadas.clear()  # Limpia la lista de elipses dibujadas
    elif cuadrado_activado:  # Agregar lógica para borrar cuadrados
        for cuadrado in cuadrados_dibujados:
            cuadrado.remove()
        cuadrados_dibujados.clear()  # Limpia la lista de cuadrados dibujados

    # Limpia las líneas de la figura creada mediante la unión de puntos
    for linea in lineas_figura:
        linea.remove()
    lineas_figura.clear()  # Limpia la lista de líneas de la figura

    # Limpia los puntos que se agregaron durante el dibujo del área libre
    for punto in puntos_dibujados:
        punto.remove()
    puntos_dibujados.clear()  # Limpia la lista de puntos dibujados
    puntos.clear()

    canvas.draw()




def borrar_ultima_figura():
    global circulos_dibujados, elipses_dibujadas, cuadrados_dibujados, ultima_elipse, ultimo_circulo, ultimo_cuadrado

    if circulo_activado:
        if circulos_dibujados:
            ultimo_circulo.remove()
            circulos_dibujados.pop()  # Elimina el último círculo de la lista
            if circulos_dibujados:  # Si todavía hay círculos en la lista, actualiza el último círculo
                ultimo_circulo = circulos_dibujados[-1]
            else:
                ultimo_circulo = None  # Si no hay más círculos, establece el último_círculo a None
            canvas.draw()
    elif eclipse_activado:
        if elipses_dibujadas:
            ultima_elipse.remove()
            elipses_dibujadas.pop()  # Elimina la última elipse de la lista
            if elipses_dibujadas:  # Si todavía hay elipses en la lista, actualiza la última elipse
                ultima_elipse = elipses_dibujadas[-1]
            else:
                ultima_elipse = None  # Si no hay más elipses, establece la última_elipse a None
            canvas.draw()
    elif cuadrado_activado:  # Agregar lógica para borrar cuadrados
        if cuadrados_dibujados:
            ultimo_cuadrado.remove()
            cuadrados_dibujados.pop()  # Elimina el último cuadrado de la lista
            if cuadrados_dibujados:  # Si todavía hay cuadrados en la lista, actualiza el último cuadrado
                ultimo_cuadrado = cuadrados_dibujados[-1]
            else:
                ultimo_cuadrado = None  # Si no hay más cuadrados, establece el último_cuadrado a None
            canvas.draw()

def botones_actualizados():
    if circulo_activado:
        boton_borrar_figuras.config(state=tk.NORMAL)
        boton_borrar_ultima_figura.config(state=tk.NORMAL)
    elif eclipse_activado:
        boton_borrar_figuras.config(state=tk.NORMAL)
        boton_borrar_ultima_figura.config(state=tk.NORMAL)
    elif cuadrado_activado:  # Agregar lógica para cuadrados
        boton_borrar_figuras.config(state=tk.NORMAL)
        boton_borrar_ultima_figura.config(state=tk.NORMAL)

def tamano_figura(val):
    global lado, s_x, s_y, ultima_elipse, ultimo_circulo, ultimo_cuadrado, relacion_aspecto_original
    tamano = float(val)
    if circulo_activado:
        radio = float(val)
        if ultimo_circulo is not None:
            ultimo_circulo.set_radius(radio)
    elif eclipse_activado:
        if ultima_elipse is not None and isinstance(ultima_elipse, Ellipse):
            s_x = tamano
            s_y = tamano
            ultima_elipse.set_width(2 * s_x)
            ultima_elipse.set_height(2 * s_y)
    elif cuadrado_activado:  # Agregar lógica para cambiar el tamaño del cuadrado
        lado = tamano
        if ultimo_cuadrado is not None:
            ultimo_cuadrado.set_width(lado)
            ultimo_cuadrado.set_height(lado)
    canvas.draw()




ventana = tk.Tk()
ventana.title("Cargar Archivos Fits")
ventana.geometry("1050x900")

ventana.protocol("WM_DELETE_WINDOW", cerrar_ventana_principal)

etiqueta1 = tk.Label(ventana, text="Subir Archivo:")
etiqueta1.grid(row=0, column=0, padx=5, pady=5, sticky="w")

select_archivo = tk.Button(ventana, text="Seleccionar Archivo", command=abrir_archivo)
select_archivo.grid(row=0, column=1, padx=5, pady=1)

etiqueta_seleccionar_pixel = tk.Label(ventana, text="Seleccionar pixel:")
etiqueta_seleccionar_pixel.grid(row=1, column=0, padx=5, pady=5, sticky="w")

etiqueta_coord_x = tk.Label(ventana, text="Coordenada X:")
etiqueta_coord_x.grid(row=1, column=1, padx=5, pady=5, sticky="e")

entrada_coord_x = tk.Entry(ventana)
entrada_coord_x.grid(row=1, column=2, padx=5, pady=5)

etiqueta_coord_y = tk.Label(ventana, text="Coordenada Y:")
etiqueta_coord_y.grid(row=1, column=3, padx=5, pady=5, sticky="e")

entrada_coord_y = tk.Entry(ventana)
entrada_coord_y.grid(row=1, column=4, padx=5, pady=5)

boton_graficar = tk.Button(ventana, text="Graficar", command=graficar, bg="green", fg="white", state=tk.DISABLED)
boton_graficar.grid(row=2, column=0, columnspan=5, padx=5, pady=10)

boton_anterior = tk.Button(ventana, text="Anterior", command=cargar_imagen_anterior, state=tk.DISABLED)
boton_anterior.grid(row=3, column=0, padx=5, pady=5)

boton_siguiente = tk.Button(ventana, text="Siguiente", command=cargar_siguiente_imagen, state=tk.DISABLED)
boton_siguiente.grid(row=3, column=4, padx=5, pady=5)

# Crear una barra de desplazamiento horizontal
barra_desplazamiento = tk.Scale(ventana, orient="horizontal", command=cargar_imagen_desde_barra)
barra_desplazamiento.grid(row=3, column=1, columnspan=3, padx=5, pady=5, sticky="ew")

# Crear un botón para borrar figuras (círculos o elipses)
boton_borrar_figuras = tk.Button(ventana, text="Borrar Figuras", command=borrar_figuras)
boton_borrar_figuras.grid(row=3, column=6, padx=5, pady=10)

# Crear un botón para borrar la última figura dibujada (círculo o elipse)
boton_borrar_ultima_figura = tk.Button(ventana, text="Borrar Última Figura", command=borrar_ultima_figura)
boton_borrar_ultima_figura.grid(row=3, column=7, padx=5, pady=10)

# Crear una figura de Matplotlib y canvas
fig = Figure(figsize=(6, 6))
ax = fig.add_subplot(111)
canvas = FigureCanvasTkAgg(fig, master=ventana)
canvas.get_tk_widget().grid(row=4, column=0, columnspan=5, padx=5, pady=10)


# Conectar eventos del ratón para el arrastre
#canvas.get_tk_widget().bind("<ButtonPress-1>", iniciar_arrastre)
#canvas.get_tk_widget().bind("<B1-Motion>", mover_imagen)
#canvas.get_tk_widget().bind("<ButtonRelease-1>", detener_arrastre)
canvas.get_tk_widget().bind("<Button-3>", abrir_menu_desplegable)
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
canvas.mpl_connect('button_press_event', dibujando_elipse)

canvas.mpl_connect('button_press_event', dibujar_cuadrado)


# Crear un control deslizante para cambiar el tamaño de la figura (círculo o elipse)
tamano_scale = Scale(ventana, from_=1, to=100, orient="horizontal", label="Tamaño de la Figura", command=tamano_figura, width=20)
tamano_scale.grid(row=3, column=8, padx=5, pady=10)  # Ajusta la ubicación del control deslizante


###########para lo de el area libre####################################

boton_area_libre = tk.Button(ventana, text="Activar Área Libre", command=alternar_area_libre)
boton_area_libre.grid(row=2, column=8, padx=5, pady=10, sticky="e")

###########para lo de el area libre####################################



ventana.mainloop()