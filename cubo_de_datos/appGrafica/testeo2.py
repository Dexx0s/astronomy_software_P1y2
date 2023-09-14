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
from matplotlib.patches import Circle
from matplotlib.figure import Figure
from tkinter import Scale


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

# Variables para el circulo
centro_x, centro_y = None, None
dibujando_circulo = False
circulo_dibujado = None




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
            with fits.open(archivo_fits) as hdul:
                # Con esto podemos verificar que se tomen archivos FITS segun PRYMARY, IMAGE, DATA CUBE y ESPECTRUM
                extension_valida = None
                nombre_archivo = os.path.basename(archivo_fits)
                for ext in hdul:
                    if ext.name in ["PRIMARY", "IMAGE", "DATA CUBE", "SPECTRUM"]:
                        extension_valida = ext
                        # Con esto buscamos la extension buscada, para abrir solo estas.
                        break

                if extension_valida is None:
                    raise ValueError("No es posible abrir este tipo de archivo FITS, dado que no contiene imágenes.")

                if np.any(np.isnan(extension_valida.data)) or np.any(np.isinf(extension_valida.data)):
                    raise ValueError("El archivo FITS contiene datos inválidos (NaN o infinitos).")
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
def graficar():
    global linea_grafico, figura_grafico, axes_grafico, ventana_grafico, ventana_grafico_abierta
    if datos_cubo is not None:
        try:
            # Obtener las coordenadas del píxel desde las entradas
            x_str = entrada_coord_x.get()
            y_str = entrada_coord_y.get()

            # Verificar que las coordenadas estén dentro de los límites
            if x_str and y_str:
                x = int(x_str)
                y = int(y_str)
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
                    with fits.open(archivo_fits) as hdul:
                        extension_valida = next(
                            (ext for ext in hdul if ext.name in ["PRIMARY", "IMAGE", "DATA CUBE", "SPECTRUM"]), None)
                        if extension_valida is None:
                            raise ValueError(
                                "No es posible abrir este tipo de archivo FITS, dado que no contiene imágenes.")

                    # Base de datos = Graphics_Colletion
                    tipo_extension = extension_valida.name
                    selected_pixel = f"({x}, {y})"
                    graphics_info = {
                        "Graphic_id": graphic_id,                     # Identificador unico
                        "Header": tipo_extension,                     # Nombre archivo fits
                        "Imagen": imagen_actual + 1,
                        "Pixeles": selected_pixel,                    # Pixeles segun x e y
                        "Fecha": fecha_actual.strftime("%d/%m/%Y"),   # Fecha segun día/mes/año
                        "Hora": fecha_actual.strftime("%H:%M:%S"),    # Fecha segun Hora
                        "Data": str(espectro)                         # Representacion de los datos
                    }
                    graphics_collection.insert_one(graphics_info)

                else:
                    messagebox.showerror("Error", "Coordenadas fuera de los límites de la imagen.")
            else:
                messagebox.showerror("Error", "Por favor, ingresa coordenadas válidas.")
        except ValueError:
            messagebox.showerror("Error", "Por favor, ingresa coordenadas válidas.")

# Cambia esta parte en la función on_image_click
def on_image_click(event):
    global centro_x, centro_y, radio, circulo_dibujado, pixel_activado, movimiento_activado, circulo_activado, dibujando_circulo, ultimo_clic
    if circulo_activado and (pixel_activado == False and movimiento_activado == False) and event.x and event.y:
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

# Nueva función para cambiar el tamaño del círculo
def actualizar_radio(val):
    global radio, ultimo_circulo
    radio = float(val)
    if ultimo_circulo is not None:
        ultimo_circulo.set_radius(radio)
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

# Función para borrar todos los círculos dibujados
def borrar_circulos():
    for circulo in circulos_dibujados:
        circulo.remove()
    circulos_dibujados.clear()  # Limpia la lista de círculos dibujados
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
    #Agregar la opción "Eclipse" con la variable de control
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
        borrar_circulos()

def toggle_eclipse():
    global pixel_activado, movimiento_activado, circulo_activado, eclipse_activado, cuadrado_activado, area_activado
    eclipse_activado = not eclipse_activado
    movimiento_activado = False
    pixel_activado = False
    circulo_activado = False
    cuadrado_activado = False
    area_activado = False

def toggle_cuadrado():
    global pixel_activado, movimiento_activado, circulo_activado, eclipse_activado, cuadrado_activado, area_activado
    cuadrado_activado = not cuadrado_activado
    movimiento_activado = False
    pixel_activado = False
    circulo_activado = False
    eclipse_activado = False
    area_activado = False

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


ventana = tk.Tk()
ventana.title("Cargar Archivos Fits")
ventana.geometry("650x900")

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

# Crear un botón para borrar círculos
boton_borrar_circulos = tk.Button(ventana, text="Borrar Círculos", command=borrar_circulos)
boton_borrar_circulos.grid(row=3, column=6, padx=5, pady=10)  # Ajusta la ubicación del botón

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

# Nueva función para cambiar el tamaño del círculo
radio_scale = Scale(ventana, from_=1, to=100, orient="horizontal", label="Tamaño del Círculo", command=actualizar_radio)
radio_scale.grid(row=3, column=5, padx=5, pady=10)  # Cambia row a 3 y column a 5


ventana.mainloop()