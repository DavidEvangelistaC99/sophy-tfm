#!/usr/bin/env python
# Ing. AVP
# 22/06/2022
# ARCHIVO DE LECTURA y PLOT
import matplotlib.pyplot as pl
import matplotlib
import wradlib
import numpy
import warnings
import argparse
from wradlib.io import read_generic_hdf5
from wradlib.util import get_wradlib_data_file
from plotting_codes import sophy_cb_tables
import os,time

for name, cb_table in sophy_cb_tables:
    ncmap = matplotlib.colors.ListedColormap(cb_table, name=name)
    matplotlib.pyplot.register_cmap(cmap=ncmap)
#LINUX bash: export WRADLIB_DATA=/path/to/wradlib-data
#example
#export WRADLIB_DATA="/home/soporte/Documents/EVENTO/HYO_PM@2022-06-09T15-05-12/paramC0N36.0/2022-06-09T18-00-00/"
warnings.filterwarnings('ignore')
PARAM = {
    'S': {'var': 'power','vmin': -45, 'vmax': -15, 'cmap': 'jet', 'label': 'Power','unit': 'dBm'},
    'V': {'var': 'velocity', 'vmin': -10, 'vmax': 10 , 'cmap': 'sophy_v', 'label': 'Velocity','unit': 'm/s'},
    'Z': {'var': 'reflectivity','vmin': -30, 'vmax': 80 , 'cmap': 'sophy_r','label': 'Reflectivity','unit': 'dBZ'},
    'W': {'var': 'spectral_width',    'vmin': 0  , 'vmax': 12 , 'cmap': 'sophy_w','label': 'Spectral Width','unit': 'm/s'}
    }
class Readsophy():
    def __init__(self):
        self.list_file = None
        self.grado     = None
        self.variable  = None
        self.save      = None
        self.range     = None

    def read_files(self,path_file,grado=None, variable=None):
        filter= "_E"+str(grado)+".0_"+variable
        validFilelist = []
        fileList= os.listdir(path_file)
        for thisFile in fileList:
            if (os.path.splitext(thisFile)[0][-7:] != filter):
                #print("s_:",os.path.splitext(thisFile)[0][-7:])
                continue
            validFilelist.append(thisFile)
            validFilelist.sort()
        return validFilelist

    def setup(self, path_file,grado,range,variable,save):
        self.path_file = path_file
        self.range     = range
        self.grado     = grado
        self.variable  = variable
        self.save      = save
        self.list_file = self.read_files(path_file=self.path_file,grado=self.grado, variable=self.variable)

    def selectHeights(self,heightList,minHei,maxHei):

        if minHei and maxHei:
            if (minHei < heightList[0]):
                minHei = heightList[0]
            if (maxHei > heightList[-1]):
                maxHei = heightList[-1]
            minIndex = 0
            maxIndex = 0
            heights = heightList

            inda = numpy.where(heights >= minHei)
            indb = numpy.where(heights <= maxHei)

            try:
                minIndex = inda[0][0]
            except:
                minIndex = 0

            try:
                maxIndex = indb[0][-1]
            except:
                maxIndex = len(heights)

            new_heightList= self.selectHeightsByIndex(heightList=heightList,minIndex=minIndex, maxIndex=maxIndex)

        return new_heightList, minIndex,maxIndex

    def selectHeightsByIndex(self,heightList,minIndex, maxIndex):

        if (minIndex < 0) or (minIndex > maxIndex):
            raise ValueError("Height index range (%d,%d) is not valid" % (minIndex, maxIndex))

        if (maxIndex >= len(heightList)):
            maxIndex = len(heightList)

        new_h = heightList[minIndex:maxIndex]
        return new_h

    def readAttributes(self,obj,variable):
        var    = PARAM[variable]['var']
        unit   = PARAM[variable]['unit']
        cmap   = PARAM[variable]['cmap']
        vmin   = PARAM[variable]['vmin']
        vmax   = PARAM[variable]['vmax']
        label  = PARAM[variable]['label']
        var_    = 'Data/'+var+'/H'
        data_arr   = numpy.array(obj[var_]['data']) # data
        utc_time   = numpy.array(obj['Data/time']['data'])
        data_azi   = numpy.array(obj['Metadata/azimuth']['data']) # th
        data_ele   = numpy.array(obj["Metadata/elevation"]['data'])
        heightList = numpy.array(obj["Metadata/range"]['data']) # r

        return data_arr, utc_time, data_azi,data_ele, heightList,unit,cmap,vmin,vmax,label

    def run(self):
        count= 0
        len_files = len(self.list_file)

        for thisFile in self.list_file:
            count = count +1
            fullpathfile = self.path_file + thisFile
            filename   = get_wradlib_data_file(fullpathfile)
            test_hdf5  = read_generic_hdf5(filename)

            # LECTURA
            data_arr, utc_time, data_azi,data_ele, heightList,unit,cmap,vmin,vmax,label = self.readAttributes(obj= test_hdf5,variable=self.variable)

            if self.range==0:
                self.range == heightList[-1]
            new_heightList,minIndex,maxIndex = self.selectHeights(heightList,0.06,self.range)

            # TIEMPO
            my_time    = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(utc_time[0]))
            time_save  = time.strftime('%Y%m%d_%H%M%S',time.localtime(utc_time[0]))

            # PLOT DATA WITH ANNOTATION
            if count ==1:
                fig = pl.figure(figsize=(10,8))
                cgax, pm = wradlib.vis.plot_ppi(data_arr[:,minIndex:maxIndex],r=new_heightList,az=data_azi,rf=1,fig=fig, ax=111,proj='cg',cmap=cmap,vmin=vmin, vmax=vmax)
                caax  = cgax.parasites[0]
                title = 'Simple PPI'+"-"+ my_time+"  E."+self.grado
                t = pl.title(title, fontsize=12,y=1.05)
                cbar = pl.gcf().colorbar(pm, pad=0.075)
                pl.text(1.0, 1.05, 'azimuth', transform=caax.transAxes, va='bottom',ha='right')
                cbar.set_label(label+'[' + unit + ']')
                gh = cgax.get_grid_helper()
            else:
                cgax, pm = wradlib.vis.plot_ppi(data_arr[:,minIndex:maxIndex],r=new_heightList,az=data_azi,rf=1,fig=fig, ax=111,proj='cg',cmap=cmap,vmin=vmin, vmax=vmax)
                caax  = cgax.parasites[0]
                title = 'Simple PPI'+"-"+my_time+"  E."+self.grado
                t = pl.title(title, fontsize=12,y=1.05)
                cbar = pl.gcf().colorbar(pm, pad=0.075)
                pl.text(1.0, 1.05, 'azimuth', transform=caax.transAxes, va='bottom',ha='right')
                cbar.set_label(label+'[' + unit + ']')
                gh = cgax.get_grid_helper()
            if self.save == 1:
                if count ==1:
                    filename     = "SOPHY"+"_"+time_save+"_"+"E."+self.grado+"_"+self.variable+".png"
                    dir =self.variable+"_"+"E."+self.grado+"CH0/"
                    filesavepath = os.path.join(self.path_file,dir)
                    try:
                        os.mkdir(filesavepath)
                    except:
                        pass
                else:
                    filename     = "SOPHY"+"_"+time_save+"_"+"E."+self.grado+"_"+self.variable+".png"
                pl.savefig(filesavepath+filename)

            pl.pause(1)
            pl.clf()
        if count==len_files:
            pl.close()
        pl.show()

PATH = "/home/soporte/Documents/EVENTO/HYO_PM@2022-06-09T15-05-12/paramC0N36.0/2022-06-09T18-00-00/"
#PATH = "/home/soporte/Documents/EVENTO/HYO_PM@2022-06-09T15-05-12/paramC0N36.0/2022-06-09T19-00-00/"

#PATH = "/home/soporte/Documents/EVENTO/HYO_PM@2022-05-31T12-00-17/paramC0N36.0/2022-05-31T16-00-00/"

def main(args):
    grado      = args.grado
    parameters = args.parameters
    save       = args.save
    range      = args.range
    obj        = Readsophy()
    for param in parameters:
        obj.setup(path_file = PATH,grado = grado,range=range, variable=param,save=int(save))
        obj.run()

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Script to process SOPHy data.')
    parser.add_argument('--parameters', nargs='*', default=['S'],
                        help='Variables to process: P, Z, V ,W')
    parser.add_argument('--grado', default=2,
                        help='Angle in Elev to plot')
    parser.add_argument('--save', default=0,
                        help='Save plot')
    parser.add_argument('--range', default=0, type=float,
                        help='Max range to plot')
    args = parser.parse_args()

    main(args)

#python sophy_proc_rev006.py  --parameters Z --grado 8 --save 1 --range 28
'''
def read_and_overview(filename):
    """Read HDF5 using read_generic_hdf5 and print upper level dictionary keys
    """
    test = read_generic_hdf5(filename)
    print("\nPrint keys for file %s" % os.path.basename(filename))
    for key in test.keys():
        print("\t%s" % key)
    return test

file__ = "/home/soporte/Documents/EVENTO/HYO_PM@2022-06-09T15-05-12/paramC0_FD_PL_R15.0km/2022-06-09T18-00-00/SOPHY_20220609_180229_E2.0_Z.hdf5"


filename = get_wradlib_data_file(file__)

print("filename:\n",filename )

test= read_and_overview(filename)
# ANADIR INFORMACION
# informacion de los pulsos de TX
# informacion de los ruidos
# informacion de los SNR ¿?
# Aumentar la amplitud de la USRP
LAST_UPDATE
---- Noise
---- Mapas
'''
