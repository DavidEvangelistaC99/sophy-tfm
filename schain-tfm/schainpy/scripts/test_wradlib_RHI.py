import numpy as np
import matplotlib.pyplot as plt
import wradlib as wrl
import warnings
# libreia nueva
#export WRADLIB_DATA="/home/soporte/Downloads/2014-06-09--185000.rhi.mvol"
from mpl_toolkits.axisartist.grid_finder import FixedLocator, DictFormatter
warnings.filterwarnings('ignore')
# lectura de gaMIC hdf5 file
filename        = wrl.util.get_wradlib_data_file("/home/soporte/Downloads/2014-06-09--185000.rhi.mvol")
#filename        = wrl.util.get_wradlib_data_file("2014-06-09--185000.rhi.mvol")

data1, metadata = wrl.io.read_gamic_hdf5(filename)
print(data1)
data1 = data1['SCAN0']['ZH']['data']
print(data1)
print("SHAPE Data",np.array(data1).shape)
r = metadata['SCAN0']['r']
print("r",r)
print("longitud r",len(r))
th = metadata['SCAN0']['el']
print("th",th)
print("longitud th",len(th))
az = metadata['SCAN0']['az']
print("az",az)
site = (metadata['VOL']['Longitude'], metadata['VOL']['Latitude'],
        metadata['VOL']['Height'])

print("Longitud,Latitud,Altura",site)
ma1 =  np.array(data1)
for i in range(3):
    print("dark",ma1[i])
'''
mask_ind = np.where(data1 <= np.nanmin(data1))
data1[mask_ind] = np.nan
ma1 = np.ma.array(data1, mask=np.isnan(data1))
'''
####################### test ####################s
th=(np.arange(450)/10.0)+5
#th= np.roll(th,-2)
#th=np.where(a<7,np.nan,a)
ma1=np.roll(ma1,-2,axis=0)
for i in range(3):
    print("green",ma1[i])
print("a",th)
#th = [i for i in reversed(a)]
######################### test
#cgax, pm = wrl.vis.plot_rhi(ma1,r=r,th=th,rf=1e3)
fig = plt.figure(figsize=(10,8))
cgax, pm = wrl.vis.plot_rhi(ma1,r=r,th=th,rf=1e3,fig=fig, ax=111,proj='cg')
caax = cgax.parasites[0]
paax = cgax.parasites[1]
cgax.set_ylim(0, 14)
#caax = cgax.parasites[0]
#paax = cgax.parasites[1]
#cgax, pm = wrl.vis.plot_rhi(ma1, r=r, th=th, rf=1e3, fig=fig, ax=111, proj='cg')
txt = plt.title('Simple RHI',y=1.05)
#cbar = plt.gcf().colorbar(pm, pad=0.05, ax=paax)
cbar = plt.gcf().colorbar(pm, pad=0.05)
cbar.set_label('reflectivity [dBZ]')
caax.set_xlabel('x_range [km]')
caax.set_ylabel('y_range [km]')
plt.text(1.0, 1.05, 'azimuth', transform=caax.transAxes, va='bottom',ha='right')
gh = cgax.get_grid_helper()

# set theta to some nice values
locs = [0., 1., 2., 3., 4., 5., 6., 7., 8., 9., 10., 11., 12., 13., 14.,
                15., 16., 17., 18., 20., 22., 25., 30., 35.,  40., 50., 60., 70., 80., 90.]
gh.grid_finder.grid_locator1 = FixedLocator(locs)
gh.grid_finder.tick_formatter1 = DictFormatter(dict([(i, r"${0:.0f}^\circ$".format(i)) for i in locs]))

plt.show()
