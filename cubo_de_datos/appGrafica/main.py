import tkinter as tk
from tkinter import filedialog, messagebox, Toplevel
from astropy.io import fits

import matplotlib
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

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

# Variables relacionadas con Matplotlib
fig = None
ax = None
canvas = None
linea_grafico = None  # Variable para almacenar la línea del gráfico
barra_desplazamiento = None  # Variable para la barra de desplazamiento

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
    if nueva_posicion >= 0 and nueva_posicion < num_frames:
        imagen_actual = nueva_posicion
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
        with fits.open(archivo_fits) as hdul:
            hdul.info()
            datos_cubo = hdul['PRIMARY'].data
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
                else:
                    messagebox.showerror("Error", "Coordenadas fuera de los límites de la imagen.")
            else:
                messagebox.showerror("Error", "Por favor, ingresa coordenadas válidas.")
        except ValueError:
            messagebox.showerror("Error", "Por favor, ingresa coordenadas válidas.")

# Función para manejar el clic del ratón en la imagen
def on_image_click(event):
    if datos_cubo is not None and event.xdata is not None and event.ydata is not None:
        # Obtener las coordenadas del píxel seleccionado
        x, y = int(event.xdata), int(event.ydata)

        # Actualizar las entradas de las coordenadas
        entrada_coord_x.delete(0, tk.END)
        entrada_coord_x.insert(0, str(x))
        entrada_coord_y.delete(0, tk.END)
        entrada_coord_y.insert(0, str(y))

        # Llamar a la función para graficar el espectro
        graficar()

        actualizar_etiqueta_coordenadas()

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
        barra_desplazamiento.config(from_=0, to=num_frames - 1)
        barra_desplazamiento.set(imagen_actual)

def cerrar_ventana_principal():
    ventana.quit()  # Finalizar el bucle principal de Tkinter
    ventana.destroy()  # Destruir la ventana principal

# Crear ventana principal
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
#boton anterior
boton_anterior = tk.Button(ventana, text="Anterior", command=cargar_imagen_anterior, state=tk.DISABLED)
boton_anterior.grid(row=3, column=0, padx=5, pady=5)
#boton siguiente
boton_siguiente = tk.Button(ventana, text="Siguiente", command=cargar_siguiente_imagen, state=tk.DISABLED)
boton_siguiente.grid(row=3, column=4, padx=5, pady=5)

# Crear una barra de desplazamiento horizontal
barra_desplazamiento = tk.Scale(ventana, orient="horizontal", command=cargar_imagen_desde_barra)
barra_desplazamiento.grid(row=3, column=1, columnspan=3, padx=5, pady=5, sticky="ew")

# Crear una figura de Matplotlib y canvas
fig, ax = plt.subplots(figsize=(6, 6))
canvas = FigureCanvasTkAgg(fig, master=ventana)
canvas.get_tk_widget().grid(row=4, column=0, columnspan=5, padx=5, pady=10)

# Conectar la función on_scroll al evento de desplazamiento de la rueda del ratón
fig.canvas.mpl_connect('scroll_event', on_scroll)

# Configurar el evento de clic del ratón en la imagen
fig.canvas.mpl_connect('button_press_event', on_image_click)

ventana.mainloop()