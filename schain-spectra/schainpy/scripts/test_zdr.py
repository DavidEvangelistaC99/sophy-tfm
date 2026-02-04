import numpy,os,time
import matplotlib
import argparse
import matplotlib.pyplot as plt
from wradlib.io import read_generic_hdf5
from wradlib.util import get_wradlib_data_file
from plotting_codes import sophy_cb_tables
from scipy import stats
import wradlib
from wradlib.io import read_generic_hdf5
from wradlib.util import get_wradlib_data_file
import warnings

warnings.filterwarnings('ignore')

for name, cb_table in sophy_cb_tables:
    ncmap = matplotlib.colors.ListedColormap(cb_table, name=name)
    matplotlib.pyplot.register_cmap(cmap=ncmap)
'''
NOTA:
#python test_zdr.py --parameters Z --grado 90 --mode 'PPI' --range 10 --type plot_WR --channel H

- python3.10
- Conda environment:
  WR_CONDA_JUN14        *  /home/soporte/anaconda3/envs/WR_CONDA_JUN14
  export WRADLIB_DATA="/media/soporte/TOSHIBAEXT/sophy/HYO_CC4_CC64_COMB@2022-12-26T00-00-32/param-EVENTO/"
- Update de plotting_codes
'''
PARAM = {
    'S': {'var': 'power'                    ,'vmin': -45, 'vmax': -15, 'cmap': 'jet'    ,'label': 'Power'         ,'unit': 'dBm'},
    'V': {'var': 'velocity'                 ,'vmin': -10, 'vmax': 10 , 'cmap': 'sophy_v','label': 'Velocity'      ,'unit': 'm/s'},
    'Z': {'var': 'reflectivity'             ,'vmin': -20, 'vmax': 80 , 'cmap': 'sophy_z','label': 'Reflectivity'  ,'unit': 'dBZ'},
    'W': {'var': 'spectral_width'           ,'vmin':  0 , 'vmax': 12 , 'cmap': 'sophy_w','label': 'Spectral Width','unit': 'm/s'},
    'R': {'var': 'rhoHV'                    ,'vmin': 0.2, 'vmax': 1  , 'cmap': 'sophy_r','label': 'RhoHV'         , 'unit': ' '},
    'D': {'var': 'differential_reflectivity','vmin': -9 , 'vmax': 12 , 'cmap': 'sophy_d','label': 'ZDR'           , 'unit': 'dB'}
    }

class Readsophy():
    def __init__(self):
        self.list_file = None
        self.grado     = None
        self.variable  = None
        self.save      = None
        self.range     = None
    def setup(self, path_file,mode,channel,type,grado,range,r_min,variable,save):
        self.path_file = path_file
        self.mode      = mode
        self.channel   = channel
        self.range     = range
        self.grado     = grado
        self.r_min     = r_min
        self.variable  = variable
        self.save      = save
        self.type_     = type
        self.list_file = self.read_files(path_file=self.path_file,mode=self.mode,grado=self.grado, variable=self.variable)
        #print("self.list_file",self.list_file)

    def read_files(self,path_file,mode=None,grado=None, variable=None):
        if mode =='PPI':
           filter= "_E"+str(grado)+".0_"+variable
        else:
           filter= "_A"+str(grado)+".0_"+variable
        #print("Filter     :",filter)
        validFilelist = []
        fileList= os.listdir(path_file)
        for thisFile in fileList:
            #print(thisFile)
            if  not os.path.splitext(thisFile)[0][-7:] in filter:
                #print("s_:",os.path.splitext(thisFile)[0][-7:])
                continue
            validFilelist.append(thisFile)
            validFilelist.sort()
        return validFilelist

    def readAttributes(self,obj,variable,channel,type_):
        var    = PARAM[variable]['var']
        unit   = PARAM[variable]['unit']
        cmap   = PARAM[variable]['cmap']
        vmin   = PARAM[variable]['vmin']
        vmax   = PARAM[variable]['vmax']
        label  = PARAM[variable]['label']

        utc_time   = numpy.array(obj['Data/time']['data'])
        data_azi   = numpy.array(obj['Metadata/azimuth']['data']) # th
        data_ele   = numpy.array(obj["Metadata/elevation"]['data'])
        heightList = numpy.array(obj["Metadata/range"]['data']) # r
        if type_ =='Diagonal':
           var_H    = 'Data/'+var+'/'+str('H')
           var_V    = 'Data/'+var+'/'+str('V')
           data_arr_H   = numpy.array(obj[var_H]['data']) # data
           data_arr_V   = numpy.array(obj[var_V]['data']) # data
           data_arr     = numpy.array([data_arr_H ,data_arr_V])		
        else:
             var_    = 'Data/'+var+'/'+str(channel)
             data_arr   = numpy.array(obj[var_]['data']) # data
        return data_arr, utc_time, data_azi,data_ele, heightList,unit,cmap,vmin,vmax,label
	

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

    def plot_RTI_PPI_RHI(self,count,x,y,z,cmap,my_time,vmin,vmax,label,unit,mode,grado):
        if count==1:
           fig = plt.figure(figsize=(8,6))
           plt.pcolormesh(x,y,z,cmap =cmap, vmin = vmin, vmax = vmax)
           title = 'Sophy Plot '+label+"-"+ my_time+" "+mode+" "+grado+" N° "+str(count)
           t = plt.title(title, fontsize=12,y=1.05)
           cbar = plt.colorbar()
           cbar.set_label(label+'[' + unit + ']')
        else:
           plt.pcolormesh(x,y,z, cmap =cmap, vmin = vmin, vmax = vmax)
           title = 'Sophy Plot '+label+"-"+ my_time+" "+mode+" "+grado+" N° "+str(count)
           t = plt.title(title, fontsize=12,y=1.05)
           cbar = plt.colorbar()
           cbar.set_label(label+'[' + unit + ']')

    def plot_PROFILE(self,count,z,y,my_time,label,mode,grado):
        if count==1:
           fig = plt.figure(figsize=(8,6))
           plt.plot(numpy.nanmean(z,1),y)
           title = 'Sophy Plot '+label+"-"+ my_time+" "+mode+" "+grado+" N° "+str(count)
           t = plt.title(title, fontsize=12,y=1.05)
           plt.ylim(0,self.range+1)
           plt.xlabel(label)
           plt.ylabel('Height(Km)')
           if self.variable=="R":
               plt.xlim(-1,3)
           if self.variable=='D':
               plt.xlim(-10,10)
           if self.variable=='Z':
               plt.xlim(-20,80)
        else:
           plt.plot(numpy.nanmean(z,1),y)
           title = 'Sophy Plot '+label+"-"+ my_time+" "+mode+" "+grado+" N° "+str(count)
           t = plt.title(title, fontsize=12,y=1.05)
           plt.ylim(0,self.range+1)
           plt.xlabel(label)
           plt.ylabel('Height(Km)')
           if self.variable=="R":
               plt.xlim(-1,3)
           if self.variable=='D':
               plt.xlim(-10,10)
           if self.variable=='Z':
               plt.xlim(-20,80)

    def save_PIC(self,count,time_save):
        print("save",count)
        if self.channel=='H':
            ch_='0'
        else:
            ch_='1'
        if count ==1:
            #filename     = "SOPHY"+"_"+time_save+"_"+self.mode+"_"+self.grado+"_"+self.variable+str(self.range)+".png"
            filename     = "SOPHY"+"_"+time_save+"_"+"E."+self.grado+"_"+self.variable+" "+self.channel+" "+str(self.range)+".png"
            dir =self.variable+"_"+self.mode+"_"+self.grado+"_"+"CH"+ch_+"/"
            filesavepath = os.path.join(self.path_file,dir)
            try:
              os.mkdir(filesavepath)
            except:
              pass
        else:
            dir =self.variable+"_"+self.mode+"_"+self.grado+"_"+"CH"+ch_+"/"
            filesavepath = os.path.join(self.path_file,dir)
            filename     = "SOPHY"+"_"+time_save+"_"+"E."+self.grado+"_"+self.variable+" "+self.channel+" "+str(self.range)+".png"
        plt.savefig(filesavepath+filename)

    def seleccion_roHV_min(self,count,z,y,arr_):
        ##print("y",y)
        if self.variable=='R':
            len_Z= z.shape[1]
            min_CC=numpy.zeros(len_Z)
            min_index_CC = numpy.zeros(len_Z)
            for i in range(len_Z):
                tmp=numpy.nanmin(z[:,i])
                tmp_index = numpy.nanargmin((z[:,i]))
                if  tmp <0.5:
                    tmp_index= numpy.nan
                    value = numpy.nan
                else:
                    value= y[tmp_index]
                min_CC[i] =value
            moda_,count_m_ = stats.mode(min_CC)
            #print("MODA",moda_)
            for i in range(len_Z):
                if min_CC[i]>moda_[0]+0.15 or min_CC[i]<moda_[0]-0.15:
                    min_CC[i]=numpy.nan
            #print("MIN_CC",min_CC)
            #print("y[0]",y[0])
            min_index_CC=((min_CC-y[0])/0.06)
            if count == 0:
                arr_ = min_index_CC
            else:
                arr_ = numpy.append(arr_,min_index_CC)
            #print("arr_",min_index_CC)
            return arr_
        else:
            print("Operation JUST for roHV - EXIT ")
            exit()

    def pp_BB(self,count,x,y,z,filename,c_max,prom_List):
        #print("z shape",z.shape)
        len_Z = z.shape[1]
        len_X = x.shape[0]
        try:
            min_CC = numpy.load(filename)
        except:
            print("There is no file")
            exit()

        if count ==1:
            c_min = 0
            c_max = c_max+ len_X
            plt.plot(x,y[0]+min_CC[c_min:c_max]*0.06,'yo')
        else:
            c_min = c_max
            c_max = c_min+len_X
            try:
                plt.plot(x,y[0]+min_CC[c_min:c_max]*0.06,'yo')
            except:
                print("Check number of file")
                return 0

        bb     = numpy.zeros(len_Z)
        min_READ_CC = min_CC[c_min:c_max]
        #print(min_READ_CC[0:50])
        for i in range(len_Z):
            if min_READ_CC[i]==numpy.nan:
                bb[i]=numpy.nan
            try:
                bb[i]=z[int(min_READ_CC[i])][i]
            except:
                bb[i]=numpy.nan
        print("bb _ prom_ZDR",numpy.nanmean(bb))
        prom_List.append(numpy.nanmean(bb))
        return c_max

    def plot_WR(self,count,fig,z,r,az,rf,my_time,label,unit,cmap,vmin,vmax):
        if count ==1:
            plt.rcParams['axes.facecolor']='black'
            cgax, pm = wradlib.vis.plot_ppi(data=z,r=r,az=az,rf=1,fig=fig,ax=111,proj='cg',cmap=cmap,vmin=vmin,vmax=vmax)
            caax     = cgax.parasites[0]
            title    = 'Sophy Plot'+"-"+label+"-"+ my_time+" "+self.mode+"_"+self.channel+"_"+self.grado+"_"+" N° "+str(count)
            t = plt.title(title, fontsize=10,y=1.05)
            cbar     = plt.gcf().colorbar(pm,ax=cgax,shrink=0.7)
            plt.text(1.0, 1.05, 'azimuth', transform=caax.transAxes, va='bottom',ha='right')
            cbar.set_label(label+'[' + unit + ']')
            caax.set_xlabel('x_range [km]')
            caax.set_ylabel('y_range [km]')
            gh = cgax.get_grid_helper()

        else:
            cgax, pm = wradlib.vis.plot_ppi(data=z,r=r,az=az,rf=1,fig=fig,ax=111,proj='cg',cmap=cmap,vmin=vmin,vmax=vmax)
            caax  = cgax.parasites[0]
            title    = 'Sophy Plot'+"-"+label+"-"+ my_time+" "+self.mode+"_"+self.channel+"_"+self.grado+"_"+" N° "+str(count)
            t = plt.title(title, fontsize=10,y=1.05)
            cbar = plt.gcf().colorbar(pm,ax=cgax,shrink=0.7)
            plt.text(1.0, 1.05, 'azimuth', transform=caax.transAxes, va='bottom',ha='right')
            cbar.set_label(label+'[' + unit + ']')
            caax.set_xlabel('x_range [km]')
            caax.set_ylabel('y_range [km]')
            gh = cgax.get_grid_helper()
            
    def plot_D(self,count,h,x,y,my_time,label,mode,grado):
        if count==1:
            fig  =plt.figure(figsize=(16,8))
            ax1=plt.subplot(1,2,1)
            ax2=plt.subplot(1,2,2)    
            ax1.plot(h,x,"bo",color="red", linestyle="dotted", lw=3,label='Zh')
            ax1.plot(h,y,"bo",color="blue", linestyle="dotted", lw=3,label='Zv')
            title = 'Sophy Plot '+ "Zh Zv"+"-"+ my_time+" "+mode+" "+grado+" N° "+str(count)
            fig.suptitle(title, fontsize=18)
            #plt.ylim(0,self.range+1)
            ax1.legend(loc=1,prop={'size': 16})
            ax1.set_title("Z- Reflectividad vs H(Km)", fontsize=15)
            ax1.set_ylabel('Z Reflectivity')
            ax1.set_xlabel('H(Km)')
            ax1.set_ylim(-20,70)
            
            m= numpy.arange(100)-20
            ax2.plot(x,y,"bo",color="red", linestyle="dotted", lw=3,label='Zh')
            ax2.plot(m,m,"bo",color="green", linestyle="dotted", lw=0.5,label='Zh')
            ax2.set_title('ZV vs ZH', fontsize=16)
            ax2.set_xlabel('Zh dBZ')
            ax2.set_xlim(-20,70)
            ax2.set_ylim(-20,70)
            ax2.set_ylabel('Zv dBZ')
            ax2.set_xlabel('Zh dBZ')
            ax2.legend(loc=1,prop={'size': 16})
        else:
            ax1=plt.subplot(1,2,1)
            ax2=plt.subplot(1,2,2)
            ax1.plot(h,x,"bo",color="red", linestyle="dotted", lw=3,label='Zh')
            ax1.plot(h,y,"bo",color="blue", linestyle="dotted", lw=3,label='Zv')
            title = 'Sophy Plot '+ "Zh Zv"+"-"+ my_time+" "+mode+" "+grado+" N° "+str(count)
            plt.suptitle(title, fontsize=18)
            ax1.legend(loc=1,prop={'size': 16})
            ax1.set_title("Z- Reflectividad vs H(Km)", fontsize=15)
            ax1.set_ylabel('Z Reflectivity')
            ax1.set_xlabel('H(Km)')
            ax1.set_ylim(-20,70)
            m= numpy.arange(100)-20
            ax2.plot(x,y,"bo",color="red", linestyle="dotted", lw=3,label='Zv vs Zh')
            ax2.plot(m,m,"bo",color="green", linestyle="dotted", lw=0.5,label='Zh=Zv')
            ax2.set_title('ZV vs ZH', fontsize=16)
            ax2.set_xlim(-20,70)
            ax2.set_ylim(-20,70)
            ax2.set_ylabel('Zv dBZ')
            ax2.set_xlabel('Zh dBZ')
            ax2.legend(loc=1,prop={'size': 16})

            #plt.gcf()

    def run(self):
        count     = 0
        len_files = len(self.list_file)
        SAVE_PARAM= []
        for thisFile in self.list_file:
            count= count +1
            print("Count :", count)
            fullpathfile = self.path_file + thisFile
            filename   = get_wradlib_data_file(fullpathfile)
            test_hdf5  = read_generic_hdf5(filename)
            # LECTURA
            data_arr, utc_time, data_azi,data_ele, heightList,unit,cmap,vmin,vmax,label = self.readAttributes(obj= test_hdf5,variable=self.variable,channel=self.channel,type_=self.type_)

            # SELECCION DE ALTURAS
            if self.range==0:
                self.range == heightList[-1]
            if self.r_min==0:
                self.r_min = 0.01
            new_heightList,minIndex,maxIndex = self.selectHeights(heightList,self.r_min,self.range)
            # TIEMPO
            utc_time[0] = utc_time[0]+60*60*5
            my_time    = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(utc_time[0]))
            time_save  = time.strftime('%Y%m%d_%H%M%S',time.localtime(utc_time[0]))
            # VARIABLES
            if self.type_=='Diagonal':
               x= numpy.nanmean(data_arr[0][:,minIndex:maxIndex].transpose(),1)
               y= numpy.nanmean(data_arr[1][:,minIndex:maxIndex].transpose(),1)
               h= new_heightList
            else:
               len_X= data_arr.shape[0]
               data_arr_= data_arr[:,minIndex:maxIndex].transpose()
               x=numpy.linspace(1,len_X,len_X)
               y= new_heightList
               z=data_arr_
               profile = numpy.mean(z,1)
            
            if count ==1:
               if self.type_ =="PROFILE":
                   self.plot_PROFILE(count=count ,z=z,y=y,my_time=my_time,label=label,mode=self.mode,grado=self.grado)
               if self.type_ =="RTI":
                   self.plot_RTI_PPI_RHI(count=count,x=x,y=y,z=z,cmap=cmap,my_time=my_time,vmin=vmin,vmax=vmax,label =label,unit=unit, mode=self.mode,grado=self.grado)
               if self.type_ =='roHV_MIN':
                   arr_= self.seleccion_roHV_min(count=count,z=z,y=y,arr_= 0)
               if self.type_ =='pp_BB':
                   self.plot_RTI_PPI_RHI(count=count,x=x,y=y,z=z,cmap=cmap,my_time=my_time,vmin=vmin,vmax=vmax,label =label,unit=unit, mode=self.mode,grado=self.grado)
                   c_max = self.pp_BB(count=count,x=x,y=y,z=z,filename='index.npy',c_max=0,prom_List=SAVE_PARAM)
               if self.type_ == "plot_WR":
                   fig =plt.figure(figsize=(10,8))
                   self.plot_WR(count=count,fig=fig,z=data_arr[:,minIndex:maxIndex],r=y,az=data_azi,rf=1,my_time=my_time,label=label,unit=unit,cmap=cmap,vmin=vmin,vmax=vmax)
               if self.type_ =="Diagonal":
                   self.plot_D(count=count,h=h,x=x,y=y,my_time=my_time,label="Zv vs Zh",mode=self.mode,grado=self.grado)
            else:
               if self.type_=="RTI":
                   self.plot_RTI_PPI_RHI(count=count,x=x,y=y,z=z,cmap=cmap,my_time=my_time,vmin=vmin,vmax=vmax,label =label,unit=unit, mode=self.mode,grado=self.grado)
               if self.type_ =="PROFILE":
                   self. plot_PROFILE(count=count,z=z,y=y,my_time=my_time,label=label,mode=self.mode,grado=self.grado)
               if self.type_ =='roHV_MIN':
                   arr_= self.seleccion_roHV_min(count=count,z=z,y=y,arr_= arr_)
               if self.type_ =='pp_BB':
                   self.plot_RTI_PPI_RHI(count=count,x=x,y=y,z=z,cmap=cmap,my_time=my_time,vmin=vmin,vmax=vmax,label =label,unit=unit, mode=self.mode,grado=self.grado)
                   c_max = self.pp_BB(count=count,x=x,y=y,z=z,filename='index.npy',c_max=c_max,prom_List=SAVE_PARAM)
                   if c_max ==0:
                       count=len_files
               if self.type_ == "plot_WR":
                   self.plot_WR(count=count,fig=fig,z=data_arr[:,minIndex:maxIndex],r=y,az=data_azi,rf=1,my_time=my_time,label=label,unit=unit,cmap=cmap,vmin=vmin,vmax=vmax)
               if self.type_ =="Diagonal":
                  self.plot_D(count=count,h=h,x=x,y=y,my_time=my_time,label="Zv vs Zh",mode=self.mode,grado=self.grado)
                   
            if self.save == 1:
                self.save_PIC(count=count,time_save=time_save)
            plt.pause(1)
            plt.clf()
            if  count == len_files:
                if self.type_ =='roHV_MIN':
                    numpy.save("/media/soporte/DATA/soporte/WRJAN2023/schain/schainpy/scripts/index.npy",arr_)
                if self.type_ =='pp_BB':
                    numpy.save("/media/soporte/DATA/soporte/WRJAN2023/schain/schainpy/scripts/index_"+self.variable+"_prom.npy",SAVE_PARAM)
                print("---------------------END---------------------")
                plt.close()
                exit()
        plt.show()


def main(args):
    grado      = args.grado
    parameters = args.parameters
    r_min      = args.r_min
    save       = args.save
    range      = args.range
    mode       = args.mode
    type       = args.type
    channel    = args.channel
    obj        = Readsophy()
    print("------------------START-------------------")
    print("MODE     :", mode)
    if  not mode =='PPI' and not mode =='RHI':
        print("Error - Choose Mode RHI or PPI")
        return None
    for param in parameters:
        print("Parameters : ", param)
        DIR_    = "NORMAL"
        if mode =='PPI':
           #PATH = "/media/soporte/TOSHIBAEXT/sophy/HYO_CC4_CC64_COMB@2022-12-26T00-00-32/param-EVENTO/"+str(param)+"_PPI_EL_"+str(grado)+".0/"
           #PATH = "/media/soporte/TOSHIBAEXT/sophy/HYO_CC4_CC64_COMB@2022-12-27T00-00-32/param-FIXIT/"+str(param)+"_PPI_EL_"+str(grado)+".0/"
           PATH  = "/media/soporte/DATA/sophy/HYO_CC4_CC64_COMB@2022-12-27T00-00-32/param-"+DIR_+"/"+str(param)+"_PPI_EL_"+str(grado)+".0/"
        else:
           #PATH = "/media/soporte/TOSHIBAEXT/sophy/HYO_CC4_CC64_COMB@2022-12-26T00-00-32/param-EVENTO/"+str(param)+"_RHI_AZ_"+str(grado)+".0/"
           PATH = "/media/soporte/DATA/sophy/HYO_CC4_CC64_COMB@2022-12-27T00-00-32/param-"+DIR_+"/"+str(param)+"_PPI_EL_"+str(grado)+".0/"

        print("Path       : ",PATH)
        obj.setup(path_file =PATH,mode=mode,channel=channel,type=type,grado = grado,range=range,r_min=r_min, variable=param,save=int(save))
        print("SETUP OK")
        obj.run()

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Script to process SOPHy data.')
    parser.add_argument('--parameters', nargs='*', default=['S'],
                        help='Variables to process: P, Z, V ,W,D')
    parser.add_argument('--grado', default=2,
                        help='Angle in Elev to plot')
    parser.add_argument('--mode',default='PPI',
                        help='MODE PPI or RHI')
    parser.add_argument('--save', default=0,
                        help='Save plot')
    parser.add_argument('--range', default=0, type=float,
                        help='Max range to plot')
    parser.add_argument('--r_min', default=0, type=float,
                        help='Min range to plot')
    parser.add_argument('--type', default='RTI',
                        help='TYPE Profile or RTI')
    parser.add_argument('--channel', default='H',
                        help='Choose H or V')

    args = parser.parse_args()

    main(args)

#python test_zdr.py --parameters Z --grado 90 --mode 'PPI' --range 6 --r_min 0.5 --type plot_WR --channel H --save 1