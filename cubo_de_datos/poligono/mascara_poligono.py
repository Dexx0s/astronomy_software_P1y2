"""

programa para crear una mascara arbitraria con forma de poligono a
partir de puntos (x,y) o tambien de regiones definidas en otros
softwares (ds9, imviewer de CASA).

Requiere algunos paquetes de python que se pueden instalar con pip:

desde la linea de comando hacer:

pip install regions



"""
import sys
import numpy as np
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy import wcs
#from regions import Regions,PixCoord, PolygonSkyRegion, PolygonPixelRegion
import regions as Reg
from regions.core import PixCoord
#import matplotlib.pyplot as plt
#import glob

#######################################################################
# cargo los datos fits
filename = 'NGC2023K.fits'
hdulist = fits.open(filename)
hdu=hdulist[0]

# leo los datos. 
data=hdu.data

# informacion WCS (World Coordinate System) que permite pasar desde
# coordenadas de pixeles a coordenadas astronomicas y viceversa
# esto solo se usa si se leen regiones desde ds9 o CASA
wcs = wcs.WCS(hdu.header)



#######################################################################
# crea una region a partir de una lista de pixeles

# lista de pixeles en coordenadas fisicas
x=[150,279,347,354,232]
y=[293,296,323,268,243]

# crea un uobjeto PixCoord necesario para usar el proximo comando
xy=PixCoord(x,y)
# crea una region poligonal con los pixeles anteriores
reg_pix=Reg.PolygonPixelRegion(xy)

# esta parte es para definir regiones a partir de otros programas (Ds9 y CASA)
# formato ds9
# reg_sky = Regions.read('filamentwcs.reg', format='ds9')

# formato de imviwer de CASA
# reg_sky = Regions.read('filament.crtf', format='crtf')

# convierte la region desde coordenadas astronomicas a coord. de
# pixeles usando la info del header
# reg_pix = reg_sky[0].to_pixel(wcs)



#######################################################################0
# crea una mascara a partir de la region
mask = reg_pix.to_mask(mode='center')

# crea una imagen con las mismas dimensiones que la imagen original
shape=(int(hdu.header['NAXIS1']),int(hdu.header['NAXIS2']))

# convierte la mascara en la imagen nueva
mask_ima=mask.to_image(shape)
output="mascara.fits"
fits.writeto(output, mask_ima, hdu.header,overwrite=True)

# si uno quisiera obtener los valores de los pixeles dentro de la mascara
#vals=mask.get_values(data)

# Divido la imagen original por la mascara 
data*=mask_ima

# Guardo en un archivo fits nuevo
output='NGC2023K_poligono.fits'
fits.writeto(output, data, hdu.header,overwrite=True)



























