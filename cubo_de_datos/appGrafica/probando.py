from astropy.io import fits

# Reemplaza 'archivo.fits' con la ruta de tu archivo FITS
archivo_fits = 'C:/Users/david/Downloads/visupy/data/NGC2023N_cube.fits'

# Abre el archivo FITS
with fits.open(archivo_fits) as hdul:
    header = hdul[0].header  # Accede al encabezado del primer HDU (Header Data Unit)

# Imprime todo el encabezado
for card in header.cards:
    print(card)