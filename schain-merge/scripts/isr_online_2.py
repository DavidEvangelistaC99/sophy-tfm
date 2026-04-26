import os, sys
import time
import datetime

'''
    ISR-ESF 1 BEAM ONLINE
'''
path = os.path.dirname(os.getcwd())
path = os.path.dirname(path)
sys.path.insert(0, path)

from schainpy.controller import Project
from shutil import rmtree

def main():
    desc = "AMISR ISR-ESF 1 Beam Experiment"



    inPath = '/home/david/Documentos/DATA/AMISR'
    #inpath= '/home/soporte/Data/AMISR-rawdata/2022'
    outPath = '/home/david/Documentos/DATA/AMISR/'


    #outPath = '/mnt/DATA/AMISR14/2026/ISR'
    #*outPath = '/mnt/DATA/AMISR14/2025/ISR'
    #outPath = '/home/soporte/Data/AMISR14/2024/ISR'
    #outPath = '/home/soporte/Data/AMISR-procdata/AMISR-proc120/2022/ISR/'


    realtime_server='10.10.120.138:4444'



    localtime='1' #para ajustar el horario en las gráficas '0' para dejar en utc

    dty = datetime.date.today()                   #ONLINE
    str1 = dty + datetime.timedelta(days=1)
    str2 = dty - datetime.timedelta(days=1)
    today = dty.strftime("%Y/%m/%d")
    tomorrow = str1.strftime("%Y/%m/%d")
    yesterday = str2.strftime("%Y/%m/%d")
    startDate=today
    #startDate="2022/11/12"
    endDate=tomorrow
    
    startDate = "2024/08/01"
    endDate   = "2024/09/30"


    ##.......................................................................................
    ##.......................................................................................
    l = startDate.split('/')                        #adding day of the year to outPath
    datelist = datetime.date(int(l[0]),int(l[1]),int(l[2]))
    DOY = datelist.timetuple().tm_yday
    outPath= outPath+"/online/"+l[0]+str(DOY).zfill(3)
    if os.path.exists(outPath):
        print("outPath", outPath)
    else :
        os.makedirs(outPath)
        print("Creating...", outPath)
    ##.......................................................................................

    controllerObj = Project()
    controllerObj.setup(id = '21', name='esf_proc', description=desc)
    ##....................................................................................... 
    xmin = 7
    xmax = 18
    IPPms = 10
    nChannels = 5
    nFFT=1
    nipp = (1000/IPPms)/nChannels
    ippP10sec = nipp*10
    print("{} profiles in 10 seconds".format(ippP10sec))

    readUnitConfObj = controllerObj.addReadUnit(datatype='AMISRReader',
                                                path=inPath,
                                                startDate=startDate,#'2016/07/12',
                                                endDate=endDate,#'2016/07/13',
                                                startTime='00:00:01',#'07:00:00',
                                                endTime='23:59:59',#'15:00:00',
                                                walk=1,
                                                timezone='lt',
                                                online=0,#1
                                                nOsamp = 1,
                                                #nChannels=2, # ojo comentario para saber cuantos canales tiene
                                                nFFT=1,
                                                #margin_days=1,
                                                ignStartDate=startDate,
                                                ignEndDate=startDate) #,
                                                #ignStartTime='11:59:59',
                                                #ignEndTime='12:25:01')

    #AMISR Processing Unit
    ##.......................................................................................
    ##.......................................................................................

    #Voltage Processing Unit
    volts_proc = controllerObj.addProcUnit(datatype='VoltageProc', inputId=readUnitConfObj.getId())
    #opv = volts_proc.addOperation(name='ScopePlot')

    # opObj11 = volts_proc.addOperation(name='RemoveProfileSats2', optype='other')
    # opObj11.addParameter(name='n', value=ippP10sec, format='int') #funciona a 9600
    # opObj11.addParameter(name='minHei', value='200', format='int')
    # opObj11.addParameter(name='maxHei', value='900', format='int')
    # opObj11.addParameter(name='minRef', value='900', format='int')
    # opObj11.addParameter(name='maxRef', value='1000', format='int')
    # opObj11.addParameter(name='profile_margin', value=int(ippP10sec/10), format='int')
    # opObj11.addParameter(name='th_hist_outlier', value=11, format='int') #10<12
    # opObj11.addParameter(name='nProfilesOut', value=1, format='int')


    opObj02 = volts_proc.addOperation(name='SSheightProfiles2', optype='other')
    opObj02.addParameter(name='step', value=1, format='int')
    opObj02.addParameter(name='nsamples', value=120, format='int')
    
    ##.......................................................................................
    ##.......................................................................................
    # opObj12 = volts_proc.addOperation(name='selectHeights', optype='self')
    # opObj12.addParameter(name='minHei', value='90', format='float')
    # opObj12.addParameter(name='maxHei', value='500', format='float')


    #Spectra Unit Processing, getting spectras with nProfiles and nFFTPoints
    spc_proc = controllerObj.addProcUnit(datatype='SpectraProc', inputId=volts_proc.getId())
    spc_proc.addParameter(name='nFFTPoints', value=120, format='int')
    #spc_proc.addParameter(name='zeroPad', value=True)
    #


    opObj11 =  spc_proc.addOperation(name='IncohInt', optype='other')
    opObj11.addParameter(name='timeInterval', value='60', format='int')

    opObj03 = spc_proc.addOperation(name='getNoiseB', optype='other')
    opObj03.addParameter(name='offset', value='0.55', format='float')
    opObj03.addParameter(name='minHei', value='200', format='int')
    opObj03.addParameter(name='maxHei', value='350', format='int')
    opObj03.addParameter(name='minFreq', value='-40000', format='float')
    opObj03.addParameter(name='maxFreq', value='40000', format='float')

    ##.......................................................................................
    ##.......................................................................................

    #SpectraPlot

    opObj12 = spc_proc.addOperation(name='SpectraPlot', optype='external')
    opObj12.addParameter(name='wintitle', value='SPC ISR-AMISR', format='str')
    opObj12.addParameter(name='showprofile', value='0', format='int')
    opObj12.addParameter(name='zmin', value=48, format='int')
    opObj12.addParameter(name='zmax', value=53, format='int')
    opObj12.addParameter(name='save', value=outPath, format='str')
    opObj12.addParameter(name='localtime', value=localtime,format='int')
    opObj12.addParameter(name='show', value = 1, format='int')
    opObj12.addParameter(name='colormap', value='jet', format='str')
    opObj12.addParameter(name='exp_code', value='208', format='int')
    
    
    #opObj12.addParameter(name='server', value=realtime_server)
    #opObj12.addParameter(name='sender_period', value='60')
    #opObj12.addParameter(name='tag', value='AMISR')


    opObj13 = spc_proc.addOperation(name='NoiselessRTIPlot', optype='external')
    # opObj13.addParameter(name='id', value='3', format='int')
    opObj13.addParameter(name='wintitle', value='RTI noiseless ISR-AMISR', format='str')
    opObj13.addParameter(name='showprofile', value='1', format='int')
    opObj13.addParameter(name='xmin', value=xmin, format='int')
    opObj13.addParameter(name='xmax', value=xmax,format='int')
    opObj13.addParameter(name='zmin', value=-0.005, format='int')
    opObj13.addParameter(name='zmax', value=0.3, format='int')
    opObj13.addParameter(name='save', value=outPath, format='str')
    opObj13.addParameter(name='localtime', value=localtime,format='int')
    opObj13.addParameter(name='show', value = 1, format='int')
    opObj13.addParameter(name='colormap', value='jet', format='str')
    opObj13.addParameter(name='exp_code', value='208', format='int')
    
    
    
    #opObj13.addParameter(name='server', value=realtime_server)
    #opObj13.addParameter(name='sender_period', value='60')
    #opObj13.addParameter(name='tag', value='AMISR')

    #
    opObj13 = spc_proc.addOperation(name='NoiselessSpectraPlot', optype='external')
    opObj13.addParameter(name='wintitle', value='SPC noiseless ISR-AMISR', format='str')
    opObj13.addParameter(name='zmin', value=-0.25, format='int')
    opObj13.addParameter(name='zmax', value=1, format='int')
    opObj13.addParameter(name='save', value=outPath, format='str')
    opObj13.addParameter(name='localtime', value=localtime,format='int')
    opObj13.addParameter(name='show', value = 1, format='int')
    opObj13.addParameter(name='colormap', value='jet', format='str')
    #opObj13.addParameter(name='exp_code', value='208', format='int')
    #opObj13.addParameter(name='server', value=realtime_server)
    #opObj13.addParameter(name='sender_period', value='60')
    #opObj13.addParameter(name='tag', value='AMISR')


    #
    #
    # # #
    # # #Noise
    # #title0 = 'RTI AMISR Beam 0'
    # opObj14 = spc_proc.addOperation(name='NoisePlot', optype='external')
    # #opObj14.addParameter(name='id', value='3', format='int')
    # opObj14.addParameter(name='wintitle', value='NOISE AMISR', format='str')
    # opObj14.addParameter(name='showprofile', value='0', format='int')
    # opObj14.addParameter(name='tmin', value=xmin, format='int')
    # opObj14.addParameter(name='tmax', value=xmax, format='int')
    # # opObj14.addParameter(name='ymin', value=60, format='int')
    # # opObj14.addParameter(name='ymax', value=65.0, format='int')
    # opObj14.addParameter(name='save', value=outPath, format='str')
    # opObj14.addParameter(name='show', value = 1, format='int')#
    # opObj14.addParameter(name='localtime', value=localtime,format='int')
    # opObj14.addParameter(name='exp_code', value='208', format='int')
    # opObj14.addParameter(name='server', value=realtime_server)
    # opObj14.addParameter(name='sender_period', value='60')
    # opObj14.addParameter(name='tag', value='AMISR')


    controllerObj.start()
    controllerObj.join()

    time.sleep(60) #1 min
    # ##.......................................................................................
    # ##.......................................................................................
    # ##.......................................................................................
    # ##.......................................................................................
    rtiPath = outPath + "/noiseless_rti"
    noisePath = outPath +"/noise"
    spcPath = outPath +"/spc"
    figPaths = [rtiPath,noisePath]
    #print("Removing hdf5 files from channels...")
    for pch in figPaths:
        rmtree(pch)
    print("Proc finished ! :)")

if __name__ == '__main__':
    import time
    start_time = time.time()
    main()
    print("--- %s seconds ---" % (time.time() - start_time))
