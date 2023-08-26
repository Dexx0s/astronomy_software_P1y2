import numpy as np
# Set up matplotlib
import matplotlib.pyplot as plt
#%matplotlib inline

from astropy.io import fits

from astropy.utils.data import download_file
image_file = download_file('http://data.astropy.org/tutorials/FITS-images/HorseHead.fits', cache=True )

hdu_list = fits.open(image_file)
hdu_list.info()

image_data = hdu_list[0].data


print(type(image_data))
print(image_data.shape)



hdu_list.close()

