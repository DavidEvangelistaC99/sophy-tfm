
import os, sys
import time
import datetime

'''
    ESF EW 10 BEAM ONLINE
'''
path = os.path.dirname(os.getcwd())
path = os.path.dirname(path)
sys.path.insert(0, path)

from schainpy.controller import Project
from shutil import rmtree

def main():
    desc = "AMISR ESF 10 Beam Experiment"




    inPath = '/mnt/data_amisr'

    outPath = '/mnt/DATA/AMISR14/2026/ESF'
    #outPath = '/mnt/DATA/AMISR14/2025/ESF'
    #outPath = '/home/soporte/Data/AMISR14/2025/ESF'
	
    realtime_server='10.10.120.138:4444'

    xmin = '18'
    xmax = '31'

    dbmin = '60' #'60'#'55' #'40' #noise  esf  eej
    dbmax = '70' #'70' #'55'
    showSPC = '1' #view plot Spectra
    showRTI = '1' #view plot RTI
    showNOISE = '1' #view plot NOISE

    code = [[1,-1,-1,-1,1,1,1,1,-1,-1,-1,1,-1,-1,-1,1,-1,-1,-1,1,-1,-1,1,-1,1,1,-1,1]]
    nCode = '1'
    nBaud = '28'
    nosamp = '3' # oversample
    localtime='1' #para ajustar el horario en las gráficas '0' para dejar en utc

    dty = datetime.date.today()                   #ONLINE
    str1 = dty + datetime.timedelta(days=1)
    str2 = dty - datetime.timedelta(days=1)
    today = dty.strftime("%Y/%m/%d")
    tomorrow = str1.strftime("%Y/%m/%d")
    yesterday = str2.strftime("%Y/%m/%d")
    startDate=today
    endDate=tomorrow
    #startDate='2021/07/16'
    #endDate='2021/07/17'
    ##.......................................................................................
    ##.......................................................................................
    l = startDate.split('/')                        #adding day of the year to outPath
    datelist = datetime.date(int(l[0]),int(l[1]),int(l[2]))
    DOY = datelist.timetuple().tm_yday
    outPath= outPath+"/online/"+l[0]+str(DOY).zfill(3)
    if os.path.exists(outPath):
        print("outPath", outPath)
    else :
        os.mkdir(outPath)
        print("Creating...", outPath)
    ##.......................................................................................
    ##.......................................................................................

    controllerObj = Project()
    controllerObj.setup(id = '21', name='esf_proc', description=desc)
    ##.......................................................................................
    ##.......................................................................................

    readUnitConfObj = controllerObj.addReadUnit(datatype='AMISRReader',
                                                path=inPath,
                                                startDate=startDate,#'2016/07/12',
                                                endDate=endDate,#'2016/07/13',
                                                startTime='18:00:00',#'07:00:00',
                                                endTime='06:59:00',#'15:00:00',
                                                walk=0,
                                                code = code,
                                                nCode = nCode,
                                                nBaud = nBaud,
                                                timezone='lt',
                                                nOsamp = nosamp,
                                                nChannels=10,
                                                nFFT=10,
                                                online=1,
                                                margin_days=1)

    #AMISR Processing Unit
    ##.......................................................................................
    ##.......................................................................................

    #Voltage Processing Unit
    procUnitConfObjBeam0 = controllerObj.addProcUnit(datatype='VoltageProc', inputId=readUnitConfObj.getId())

    #Noise--> no code
    
    
    opObj11 = procUnitConfObjBeam0.addOperation(name='Decoder', optype='other')
    opObj11.addParameter(name='code', value=code, format='floatlist')
    opObj11.addParameter(name='nCode', value=nCode, format='int')
    opObj11.addParameter(name='nBaud', value=nBaud, format='int')
    opObj11.addParameter(name='osamp', value=nosamp, format='int')



    ##.......................................................................................
    ##.......................................................................................

    #Spectra Unit Processing, getting spectras with nProfiles and nFFTPoints
    procUnitConfObjSpectraBeam0 = controllerObj.addProcUnit(datatype='SpectraProc', inputId=procUnitConfObjBeam0.getId())
    procUnitConfObjSpectraBeam0.addParameter(name='nFFTPoints', value=10, format='int')
    #
    opObj11 =  procUnitConfObjSpectraBeam0.addOperation(name='IncohInt', optype='other')
    opObj11.addParameter(name='n', value='60', format='int')


    ##.......................................................................................
    ##.......................................................................................

    #SpectraPlot
    opObj12 = procUnitConfObjSpectraBeam0.addOperation(name='SpectraPlot', optype='external')
    opObj12.addParameter(name='id', value='1', format='int')
    opObj12.addParameter(name='wintitle', value='ESF AMISR', format='str')
    opObj12.addParameter(name='showprofile', value='1', format='int')
    opObj12.addParameter(name='zmin', value=dbmin, format='int')
    opObj12.addParameter(name='zmax', value=dbmax, format='int')
    opObj12.addParameter(name='save', value=outPath, format='str')
    opObj12.addParameter(name='localtime', value=localtime,format='int')
    opObj12.addParameter(name='show', value = showSPC, format='int')
    opObj12.addParameter(name='colormap', value='jet', format='str')
    opObj12.addParameter(name='exp_code', value='207', format='int')
    opObj12.addParameter(name='server', value=realtime_server)
    opObj12.addParameter(name='sender_period', value='120')
    opObj12.addParameter(name='tag', value='AMISR')

    #RTIPlot
    #title0 = 'RTI AMISR Beam 0'
    opObj13 = procUnitConfObjSpectraBeam0.addOperation(name='RTIPlot', optype='external')
    opObj13.addParameter(name='id', value='2', format='int')
    opObj13.addParameter(name='wintitle', value='ESF AMISR', format='str')
    opObj13.addParameter(name='showprofile', value='0', format='int')
    opObj13.addParameter(name='xmin', value=xmin, format='int')
    opObj13.addParameter(name='xmax', value=xmax,format='int')
    opObj13.addParameter(name='zmin', value=dbmin, format='int')
    opObj13.addParameter(name='zmax', value=dbmax, format='int')
    opObj13.addParameter(name='save', value=outPath, format='str')
    opObj13.addParameter(name='localtime', value=localtime,format='int')
    opObj13.addParameter(name='show', value = showRTI, format='int')
    opObj13.addParameter(name='colormap', value='jet', format='str')
    opObj13.addParameter(name='exp_code', value='207', format='int')
    opObj13.addParameter(name='server', value=realtime_server)
    opObj13.addParameter(name='sender_period', value='120')
    opObj13.addParameter(name='tag', value='AMISR')

    # # #
    # #Noise
    #title0 = 'RTI AMISR Beam 0'
    opObj14 = procUnitConfObjSpectraBeam0.addOperation(name='NoisePlot', optype='external')
    opObj14.addParameter(name='id', value='3', format='int')
    opObj14.addParameter(name='wintitle', value='ESF AMISR', format='str')
    opObj14.addParameter(name='showprofile', value='0', format='int')
    opObj14.addParameter(name='tmin', value=xmin, format='int')
    opObj14.addParameter(name='tmax', value=xmax, format='int')
    opObj14.addParameter(name='save', value=outPath, format='str')
    opObj14.addParameter(name='show', value = showNOISE, format='int')
    opObj14.addParameter(name='localtime', value=localtime,format='int')
    opObj14.addParameter(name='exp_code', value='207', format='int')
    opObj14.addParameter(name='server', value=realtime_server)
    opObj14.addParameter(name='sender_period', value='120')
    opObj14.addParameter(name='tag', value='AMISR')

    controllerObj.start()
    controllerObj.join()

    time.sleep(60) #1 min
    # ##.......................................................................................
    # ##.......................................................................................
    # ##.......................................................................................
    # ##.......................................................................................
    rtiPath = outPath +"/rti"
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
