-2) Ordenar repositorio

-1) Revisar cubo de datos que no carga. Subir ejemplo a git. Testear
 fundion que cambia nans por 0.


0) Eje x del espectro cambiar unidades a frecuencia a traves de un
swich en la interfaz. Obtener informacion del header para convertir
desde no de frame a frecuencia en GHz

      hdul = fits.open(fits_image_filename)
      hdr = hdul[0].header
      crpix3=hdr['CRPIX3']
      cdelt3=hdr['CDELT3']
      crval3=hdr['CRVAL3']


1) agregar caja para elegir numero de plano (eje z) dentro del cubo
  (e.g. 90)
  
2- barrita desplazadora ----- LISTO

3.1- agregar posibilidad de definir regiones:
					- circulo  (x0, y0, R)
					- elipse   (x0, y0, R_maj, R_min)
					- cuadrado/rectangulo
					- poligono a partir de puntos

3.2- graficar espectro promediado para región

4. realizar un ajuste de una curva a un sector del espectro.

