def crear_ventana_grafico():
    global ventana_grafico, figura_grafico, axes_grafico, canvas_grafico

    # Usar el estilo predeterminado de Matplotlib
    plt.style.use('default')

    ventana_grafico = tk.Toplevel()
    ventana_grafico.title("Gráfico del Espectro")
    figura_grafico, axes_grafico = plt.subplots(figsize=(8, 5))

    # Ubica el gráfico en la fila 0 y columna 0
    canvas_grafico = FigureCanvasTkAgg(figura_grafico, master=ventana_grafico)
    canvas_grafico.get_tk_widget().grid(row=0, column=0, padx=10, pady=10)

    # Agregar un cuadro de texto para ingresar comentarios
    cuadro_comentarios = tk.Text(ventana_grafico, height=5, width=60)
    cuadro_comentarios.grid(row=1, column=0, padx=10, pady=10)

    # Inserta el texto inicial en el cuadro de comentarios
    texto_inicial = "Escribe aquí tus comentarios..."
    cuadro_comentarios.insert("1.0", texto_inicial)

    # Crear el botón de "Guardar" y ubicarlo a la derecha del gráfico
    boton_guardar = tk.Button(ventana_grafico, text="Guardar", command=lambda: guardar_grafico(cuadro_comentarios))
    boton_guardar.grid(row=0, column=1, padx=10, pady=10)  # Ubica el botón en la misma fila y columna 1 al lado derecho

    boton_guardar_mascara = tk.Button(ventana_grafico, text="Guardar mascara", command=lambda: guardar_ultima_area_libre_en_mongodb())
    boton_guardar_mascara.grid(row=0, column=2, padx=10, pady=10)  # Ubica el botón en la misma fila y columna 1 al lado derecho

    # Crear el botón de "Ajuste gausiano" y asociarlo a la función de ajuste
    boton_ajuste_gausiano = tk.Button(ventana_grafico, text="Ajuste gausiano",
                                      command=lambda: ajustes_grafico())
    boton_ajuste_gausiano.grid(row=0, column=3, padx=10, pady=10)  # Ajusta la ubicación del botón

    ventana_grafico.button_salir = tk.Button(ventana_grafico, text="Salir", command=ventana_grafico.destroy)
    ventana_grafico.button_salir.grid(row=2, column=0,
                                      columnspan=2)  # Ubica el botón de salir en la fila 2 y columnas 0 y 1
    ventana_grafico.protocol("WM_DELETE_WINDOW", ventana_grafico.button_salir.invoke)

    ventanas_grafico.append(ventana_grafico)

    # Cuando ya no se necesite la figura, esta función la cierra
    plt.close(figura_grafico)