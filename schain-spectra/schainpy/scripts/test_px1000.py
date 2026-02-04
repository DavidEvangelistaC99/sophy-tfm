import numpy as np
import matplotlib.pyplot as pl
import warnings
#export WRADLIB_DATA=/path/to/wradlib-data
warnings.filterwarnings('ignore')

from wradlib.io import read_generic_netcdf
from wradlib.util import get_wradlib_data_file
import os



# A little helper function for repeated tasks
def read_and_overview(filename):
    """Read NetCDF using read_generic_netcdf and print upper level dictionary keys
    """
    test = read_generic_netcdf(filename)
    print("\nPrint keys for file %s" % os.path.basename(filename))
    for key in test.keys():
        print("\t%s" % key)
    return test


filename = '/home/soporte/Downloads/PX1000/PX-20180220-174014-E0.0-Z.nc'
filename = get_wradlib_data_file(filename)
test= read_and_overview(filename)
print("Height",test['Height'])
print("Azimuth",test['Azimuth'])
print("Elevation",test['Elevation'])
print("CalibH-value",test['CalibH-value'])
print("attributes",test['attributes'])
print("-------------------------------------------------------------------------------------")
for key in test.keys():
    print(key,test[str(key)])

'''
try:
    get_ipython().magic('matplotlib inline')
except:
    pl.ion()
img, meta = wradlib.io.read_dx(filename)
print("Shape of polar array: %r\n" % (img.shape,))
print("Some meta data of the DX file:")
#print("\tdatetime: %r" % (meta["datetime"],))
#print("\tRadar ID: %s" % (meta["radarid"],))

img[200:250,:]= np.ones([50,img.shape[1]])*np.nan

img[300:360,:]= np.ones([60,img.shape[1]])*np.nan

cgax, pm= wradlib.vis.plot_ppi(img)
txt = pl.title('Simple PPI')
print("coordenada angular",img[:,0],len(img[:,0]))
print("COORDENADA 0",img[0],len(img[0]))
cbar = pl.gcf().colorbar(pm, pad=0.075)

#r = np.arange(40, 80)
#az = np.arange(200, 250)
#ax, pm = wradlib.vis.plot_ppi(img[200:250, 40:80], r, az, autoext=False)
#ax, pm = wradlib.vis.plot_ppi(img[200:250, 40:80], r, az)

#txt = pl.title('Sector PPI')
pl.show()
'''
