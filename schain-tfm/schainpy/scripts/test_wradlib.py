import numpy as np
import matplotlib.pyplot as pl
import wradlib
import warnings
#export WRADLIB_DATA=/path/to/wradlib-data
warnings.filterwarnings('ignore')
'''
try:
    get_ipython().magic('matplotlib inline')
except:
    pl.ion()
'''
filename = wradlib.util.get_wradlib_data_file("/home/soporte/Downloads/raa00-dx_10908-0806021735-fbg---bin.gz")
img, meta = wradlib.io.read_dx(filename)
print("Shape of polar array: %r\n" % (img.shape,))
print("Some meta data of the DX file:")
print("\tdatetime: %r" % (meta["datetime"],))
print("\tRadar ID: %s" % (meta["radarid"],))

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


### PARA MULTIPLE PloteO REVISAR EL LINK
#https://docs.wradlib.org/en/stable/notebooks/visualisation/wradlib_plot_curvelinear_grids.html
'''
subplots = [221, 222, 223, 224]
fig = pl.figure(figsize=(10,8))
fig.subplots_adjust(wspace=0.2, hspace=0.35)
for sp in subplots:
    cgax, pm = wrl.vis.plot_rhi(ma1, r, th, rf=1e3, ax=sp, proj='cg')
    caax = cgax.parasites[0]
    paax = cgax.parasites[1]
    t = pl.title('CG RHI #%(sp)d' %locals(), y=1.1)
    cgax.set_ylim(0, 15)
    cbar = pl.gcf().colorbar(pm, pad=0.125, ax=paax)
    caax.set_xlabel('range [km]')
    caax.set_ylabel('height [km]')
    gh = cgax.get_grid_helper()
    # set theta to some nice values
    locs = [0., 5., 10., 15., 20., 30., 40., 60., 90.]
    gh.grid_finder.grid_locator1 = FixedLocator(locs)
    gh.grid_finder.tick_formatter1 = DictFormatter(dict([(i, r"${0:.0f}^\circ$".format(i)) for i in locs]))
    cbar.set_label('reflectivity [dBZ]')
'''
