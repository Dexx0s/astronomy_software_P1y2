# visuPy

Herramientas de visualizacion de datos astronomicos.

## Datos
En la carpeta data esta el archivo "NGC2023N_cube.fits". Para verlo de
manera facil pueden instalar la aplicación "ds9"
(https://sites.google.com/cfa.harvard.edu/saoimageds9)

Si abren el cubo con ds9, veran que es una serie de 117 imagenes,
donde la mayoria solo contiene ruido. Sin embargo, hay algunos frames
con mucha señal (e.g. el 99). Abajo hay 2 imagenes que muestran lo que
veran. 

<!--- ![Alt text01](data/ds9_cube01.png?raw=true "Title") --->
<!--- ![Alt text99](data/ds9_cube99.png?raw=true "Title") --->
<img src="data/ds9_cube01.png" width="400" />
<img src="data/ds9_cube99.png" width="400" />
## Tutoriales buenos para manipulacion de datos FITS:


El formato ".fits" es un estandar en astronomía. Sirve para almacenar
datos que pueden ser imágenes, espectros, cubos, ets.  Los archivos
FITS son binarios que se puede abrir con diferentes herramientas, 'Ds9'
que mencionamos mas arriba y 'python' que usaremos acá. Les recomiendo
mirar estos tutoriales:

- Manipulación de imágenes 2D: https://learn.astropy.org/tutorials/FITS-images.html
- Manipulación de cubos 3D: https://learn.astropy.org/tutorials/FITS-cubes.html

