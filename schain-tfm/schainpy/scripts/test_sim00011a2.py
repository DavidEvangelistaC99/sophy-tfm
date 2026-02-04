import os,sys,json
import datetime
import time
from schainpy.controller import Project
'''
NOTA:
Este script de prueba.
- Unidad del lectura 'HDFReader'.
- Unidad de procesamiento ParametersProc
- Operacion SpectralMomentsPlot

'''
#path       = '/home/soporte/Downloads/RAWDATA_PP'
#path       = '/DATA_RM/TEST_HDF5/d2021203'
#######################################################################
################# RANGO DE PLOTEO######################################
#######################################################################
dBmin = '1'
dBmax = '85'
xmin = '0'
xmax ='24'
tmmin = 12.2
tmmax = 12.40
ymin = '0'
ymax = '600'
#######################################################################
#######################################################################
# este script lee los archivos pre-procesados pulse-pair y permite el
# el ploteo del rti, mostrando los valores de potencia  de la senal.
# el resultado del grafico depende del programa USRP_ADQ_PP.py
# debido al procesamiento del Pulse Pair.

#######################################################################
#######################################################################
#path_pp = '/DATA_RM/TEST_HDF5_PP_22'
path='/DATA_RM/TEST_HDF5_PP_22/d2021265'
#path='/DATA_RM/TEST_HDF5/d2021231'
figpath    = '/home/soporte/Downloads/IMAGE'
desc       = "Simulator Test"
desc_data  = {
            'Data': {
                'dataPP_POW': ['Data/dataPP_POW/channel00','Data/dataPP_POW/channel01'],
                'dataPP_DOP': ['Data/dataPP_DOP/channel00','Data/dataPP_DOP/channel01'],
                'utctime':'Data/utctime'
            },
            'Metadata': {
                'heightList' :'Metadata/heightList',
                'flagDataAsBlock':'Metadata/flagDataAsBlock',
                'channelList' :'Metadata/channelList',
                'profileIndex' :'Metadata/profileIndex'
            }
        }

controllerObj   = Project()

controllerObj.setup(id='10',name='Test Simulator',description=desc)

readUnitConfObj = controllerObj.addReadUnit(datatype='HDFReader',
                                            path=path,
                                            startDate="2021/01/01",   #"2020/01/01",#today,
                                            endDate= "2021/12/01",  #"2020/12/30",#today,
                                            startTime='00:00:00',
                                            endTime='23:59:59',
                                            delay=0,
                                            #set=0,
                                            online=0,
                                            walk=0,
                                            description= json.dumps(desc_data))#1

procUnitConfObjA = controllerObj.addProcUnit(datatype='ParametersProc',inputId=readUnitConfObj.getId())

#opObj11 = procUnitConfObjA.addOperation(name='PulsepairPowerPlot', optype='other')#PulsepairPowerPlot
#opObj11 = procUnitConfObjA.addOperation(name='PulsepairSignalPlot', optype='other')
#opObj11 = procUnitConfObjA.addOperation(name='PulsepairVelocityPlot', optype='other')

opObj11 = procUnitConfObjA.addOperation(name='GenericRTIPlot',optype='external')

opObj11.addParameter(name='attr_data', value='dataPP_POW')
opObj11.addParameter(name='colormap', value='jet')

opObj11.addParameter(name='xmin', value=tmmin)
opObj11.addParameter(name='xmax', value=tmmax)
opObj11.addParameter(name='zmin', value=dBmin)
opObj11.addParameter(name='zmax', value=dBmax)
opObj11.addParameter(name='save', value=figpath)
opObj11.addParameter(name='showprofile', value=0)
opObj11.addParameter(name='save_period', value=10)


controllerObj.start()
