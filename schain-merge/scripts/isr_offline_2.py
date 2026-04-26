# 
# SCRIPT DESARROLLADO PARA PROCESAR DATOS DEL 06/04/2025
#
import os, sys, json
import time
import datetime
from multiprocessing import Process
from  shutil import rmtree
from schainpy.controller import Project
from multiprocessing.connection import wait
from schainpy.model.io.utilsIO import  MergeH5
import matplotlib
matplotlib.use('Agg')  # Usa un backend sin GUI

#path = '/mnt/data_amisr' # PATH REAL
#path = '/media/soporte/Expansion1/AMISR/2025'
#path = '/home/david/Documents/DATA/AMISR'
path = '/media/david/01AMISR/2024'

#path = '/media/soporte/Expansion/AMISR/2025/'
#path = '/media/soporte/DATA/DATA_AMISR/2024'
#path = '/media/soporte/DATA/DATA_AMISR/2024'
#path = '/media/soporte/TOSHIBA EXT1/DATA_AMISR/2024'



#path= '/home/soporte/Data/AMISR-rawdata/2022'

#outPath = '/home/soporte/Data/AMISR-procdata/AMISR-proc120/2022/ISR/'
outPath = '/home/david/Documents/DATA/AMISR_2/'


xmin = 7
xmax  = 18
localtime=1

day = datetime.date.today()- datetime.timedelta(days=0)
str0 =  day
str1 = str0 + datetime.timedelta(days=1)
str2 = str0 - datetime.timedelta(days=1)
today = str0.strftime("%Y/%m/%d")
tomorrow = str1.strftime("%Y/%m/%d")
yesterday = str2.strftime("%Y/%m/%d")

#startDate = yesterday
#endDate  = today
startDate = "2024/01/01"
endDate   = "2024/12/12"
print("----------------")
print(startDate)
print(endDate)
print("---------------")

#factors =[1.06, 1.06, 1.06, 1.06, 1.06]
factors =[1.06, 1.06]
#factors = [1.06]
#nChannels = 5 # 2 10?
nChannels = 2 #2 DESDE EL LUNES  01/09/2025 TENEMOS SOLO EL CANAL OBLICUO
IPPms =10
nFFT = 250

##.......................................................................................
##.......................................................................................
##.......................................................................................
##.......................................................................................
l = startDate.split('/')                        #adding day of the year to outPath
datelist = datetime.date(int(l[0]),int(l[1]),int(l[2]))
DOY = datelist.timetuple().tm_yday
year = l[0]
month = l[1].zfill(2)
day = l[2].zfill(2)
doy = str(DOY).zfill(3)

nipp = (1000/IPPms)/nChannels
ippP10sec = nipp*10
print("{} profiles in 10 seconds".format(ippP10sec))
def schain(channel, Outdata, factor=1):
    '''
    This method will be called many times so here you should put all your code
    '''

    if os.path.exists(Outdata):
        print("Outdata {}: ".format(channel), Outdata)
    else :
        os.mkdir(Outdata)

    controllerObj = Project()
    controllerObj.setup(id = channel, name='isr offline', description='desc')
    readUnitConfObj = controllerObj.addReadUnit(datatype='AMISRReader',
                                                path=path,
                                                startDate=startDate,#'2016/07/12',
                                                endDate=endDate,#'2016/07/13',
                                                startTime='00:00:00',#'18:00:00',
                                                endTime='23:59:59',#'07:00:00',
                                                walk='1',
                                                timezone='lt',
                                                nOsamp = 1,
                                                margin_days=1,
                                                online=0,
                                                nFFT = nFFT,
                                                nChannels = nChannels
                                                )

    proc_volts = controllerObj.addProcUnit(datatype='VoltageProc', inputId=readUnitConfObj.getId())

    #
    # opObj03 = proc_volts.addOperation(name='selectChannels', optype='other')
    # opObj03.addParameter(name='channelList', value=[channel], format='list')

    # opObj11 = proc_volts.addOperation(name='RemoveProfileSats2', optype='other')
    # opObj11.addParameter(name='n', value=ippP10sec, format='int') #funciona a 9600
    # opObj11.addParameter(name='minHei', value='200', format='int')
    # opObj11.addParameter(name='maxHei', value='550', format='int')
    # opObj11.addParameter(name='minRef', value='1300', format='int')
    # opObj11.addParameter(name='maxRef', value='1400', format='int')
    # opObj11.addParameter(name='profile_margin', value=10, format='int')
    # opObj11.addParameter(name='th_hist_outlier', value=5, format='int') #8
    # opObj11.addParameter(name='nProfilesOut', value=1, format='int')
    # opObj11.addParameter(name='navg', value=0.99)
    # opObj11.addParameter(name='thfactor', value=factor)
    # opObj11.addParameter(name='nBins', value=10 ) 
    # # opObj11.addParameter(name='debug', value=True )

    #opObj02 = proc_volts.addOperation(name='SSheightProfiles2', optype='other')
    #opObj02.addParameter(name='step', value=1, format='int')
    #opObj02.addParameter(name='nsamples', value=60, format='int')
    '''
    proc_spc = controllerObj.addProcUnit(datatype='SpectraProc', inputId=proc_volts.getId())
    proc_spc.addParameter(name='nFFTPoints', value=60, format='int')
    #proc_spc.addParameter(name='zeroPad', value=True)

    opObj13 = proc_spc.addOperation(name='IntegrationFaradaySpectra', optype='other')
    opObj13.addParameter(name='avg', value='1.0', format='int') #0.95 a 10 o 1 min
    opObj13.addParameter(name='minHei', value='100', format='int')
    opObj13.addParameter(name='maxHei', value='950', format='int')
    opObj13.addParameter(name='timeInterval', value=60, format='int')
    #opObj13.addParameter(name='n', value=1000, format='int')
    # # #
    #opObj13 = proc_spc.addOperation(name='IncohInt', optype='other')
    #opObj13.addParameter(name='n', value='5', format='int')
    # opObj13.addParameter(name='timeInterval', value='20', format='int')
    
    opObj03 = proc_spc.addOperation(name='getNoiseB', optype='other')
    opObj03.addParameter(name='offset', value='0.225', format='float')
    opObj03.addParameter(name='minHei', value='200', format='int')
    opObj03.addParameter(name='maxHei', value='350', format='int')
    opObj03.addParameter(name='minFreq', value='-40000', format='int')
    opObj03.addParameter(name='maxFreq', value='40000', format='int')

    
    #rti_plot = proc_spc.addOperation(name='NoiselessRTIPlot', optype='external')
    #rti_plot.addParameter(name='wintitle', value='RTI AMISR', format='str')
    #rti_plot.addParameter(name='showprofile', value='1', format='int')
    #rti_plot.addParameter(name='zmin', value=-0.01, format='int')
    #rti_plot.addParameter(name='zmax', value=0.3, format='int')
    #rti_plot.addParameter(name='xmin', value=xmin, format='int')
    #rti_plot.addParameter(name='xmax', value=xmax, format='int')
    #rti_plot.addParameter(name='localtime', value=1,format='int')
    #rti_plot.addParameter(name='save', value=Outdata, format='str')
    #rti_plot.addParameter(name='t_units', value='h', format='str')

    spc_plot = proc_spc.addOperation(name='NoiselessSpectraPlot', optype='external')
    spc_plot.addParameter(name='showprofile', value='1', format='int')
    spc_plot.addParameter(name='zmin', value=-0.00001, format='float')
    spc_plot.addParameter(name='zmax', value=5.0, format='float')
    spc_plot.addParameter(name='colormap', value='jet')
    spc_plot.addParameter(name='save', value=Outdata, format='str')
    spc_plot.addParameter(name='localtime', value=1, format='int')

        
    # opObj12 = proc_spc.addOperation(name='SpectraCutPlot', optype='external')
    # opObj12.addParameter(name='selectedHeightsList', value='250,300,350,400,450')
    # opObj12.addParameter(name='ymin', value=0.0001, format='float')
    # opObj12.addParameter(name='ymax', value=2.5, format='float')
    # opObj12.addParameter(name='xmin', value=-10, format='int')
    # opObj12.addParameter(name='xmax', value=10, format='int')
    # opObj12.addParameter(name='save', value=Outdata, format='str')
    # opObj12.addParameter(name='localtime', value=1,format='int')
    # opObj12.addParameter(name='show', value = 1, format='int')

    
    #procParam= controllerObj.addProcUnit(datatype='ParametersProc',inputId=proc_spc.getId())
    # # moments = procParam.addOperation(name='SpectralMoments',optype='other')
    #opObj12 = procParam.addOperation(name='setAttribute')
    #opObj12.addParameter(name='type', value='Spectra')
    '''
    '''
    writer = procParam.addOperation(name='HDFWriter',optype='other')
    writer.addParameter(name='path', value=Outdata)
    writer.addParameter(name='timeZone', value="ut")
    writer.addParameter(name='hourLimit', value=24)
    writer.addParameter(name='breakDays', value=False)
    writer.addParameter(name='blocksPerFile', value='12',format='int')
    writer.addParameter(name='metadataList', value='timeZone,type,unitsDescription,\
radarControllerHeaderObj.dtype,radarControllerHeaderObj.ipp,radarControllerHeaderObj.txA,radarControllerHeaderObj.frequency,\
radarControllerHeaderObj.sampleRate,radarControllerHeaderObj.heightList,radarControllerHeaderObj.elevationList,\
radarControllerHeaderObj.azimuthList,radarControllerHeaderObj.channelList,radarControllerHeaderObj.heightResolution,\
radarControllerHeaderObj.code,radarControllerHeaderObj.nCode,radarControllerHeaderObj.nBaud,\
processingHeaderObj.dtype,processingHeaderObj.ipp,processingHeaderObj.nCohInt,processingHeaderObj.nSamplesFFT,\
processingHeaderObj.nFFTPoints,processingHeaderObj.timeIncohInt,processingHeaderObj.heightList,processingHeaderObj.channelList,processingHeaderObj.elevationList,\
processingHeaderObj.azimuthList,processingHeaderObj.heightResolution',format='list')
    writer.addParameter(name='dataList',value='data_spc,nIncohInt,utctime',format='list')


    '''

    controllerObj.start()



if __name__ == '__main__':

    fpathOut = outPath+'d'+l[0]+doy
    outPaths = [outPath+l[0]+doy +"CH{}".format(ch) for ch in range(nChannels)]

    dataList = ['data_spc','nIncohInt','utctime']

    ###########################################################################
    ###########################################################################
    
    pool = []
    #for ch in range(nChannels):
    for ch in range(1):
        p = Process(target=schain, args=(ch,outPaths[ch], factors[ch]))
        pool.append(p)
        p.start()

    wait(p.sentinel for p in pool)
    
    #time.sleep(90)
    
    ############################################################################
    ############################################################################
    
    print("Starting merging proc...")
    if os.path.exists(fpathOut):
        print("final path Out: {}: ", fpathOut)
    else :
        os.makedirs(fpathOut)

    #merger = MergeH5(nChannels,fpathOut,dataList,*outPaths)
    #merger.run()
    #time.sleep(10)
    
    ############################################################################
    ############################################################################
    
    #print("Removing hdf5 files from channels...")
    #for pch in outPaths:
    #    rmtree(pch)

    print("Proc finished ! :)")
    
