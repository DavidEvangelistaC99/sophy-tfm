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

#######################################################################
################# RANGO DE PLOTEO######################################
#######################################################################
dBmin = '1'
dBmax = '65'
xmin = '0'
xmax ='24'
#tmmin = 16.2
#tmmax = 16.25
tmmin =15
tmmax =15.5
ymin = '0'
ymax = '600'
#######################################################################
#######################################################################
#######################################################################
#path       = '/DATA_RM/TEST_HDF5_SPEC'
#path       = '/DATA_RM/TEST_HDF5_SPEC_23/6v/'
path       = '/DATA_RM/TEST_HDF5_19OCT'
figpath    = '/home/soporte/Downloads/23/6v'
desc       = "Simulator Test"
desc_data  =  {
                'Data': {
                    'data_pow': ['Data/data_pow/channel00','Data/data_pow/channel01'],
                    'data_dop': ['Data/data_dop/channel00','Data/data_dop/channel01'],
                    'utctime':'Data/utctime'
                },
                'Metadata': {
                    'heightList':'Metadata/heightList',
                    'nIncohInt' :'Metadata/nIncohInt',
                    'nCohInt' :'Metadata/nCohInt',
                    'nProfiles' :'Metadata/nProfiles',
                    'channelList' :'Metadata/channelList',
                    'utctimeInit' :'Metadata/utctimeInit'

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
                                            walk=1,
                                            description= json.dumps(desc_data))#1

procUnitConfObjA = controllerObj.addProcUnit(datatype='ParametersProc',inputId=readUnitConfObj.getId())

opObj11 = procUnitConfObjA.addOperation(name='PowerPlot',optype='external')
opObj11.addParameter(name='xmin', value=tmmin)
opObj11.addParameter(name='xmax', value=tmmax)
opObj11.addParameter(name='zmin', value=dBmin)
opObj11.addParameter(name='zmax', value=dBmax)
opObj11.addParameter(name='save', value=figpath)
opObj11.addParameter(name='showprofile', value=0)
opObj11.addParameter(name='save_period', value=10)

controllerObj.start()
