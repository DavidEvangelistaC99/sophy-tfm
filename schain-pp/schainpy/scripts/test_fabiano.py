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
path       = '/DATA_RM/TEST_HDF5_SPEC_23/6v/'
figpath    = '/home/soporte/Downloads/23/6v'
path="/home/soporte/Downloads/params-20211015T174046Z-001/params"
desc       = "Simulator Test"
desc_data  =  {
                'Data': {
                    'data_spc': ['Data/data_spc/channel00','Data/data_spc/channel01'\
                                ,'Data/data_spc/channel02','Data/data_spc/channel03'\
                                ,'Data/data_spc/channel04','Data/data_spc/channel05'\
                                ,'Data/data_spc/channel06','Data/data_spc/channel07'\
                                ,'Data/data_spc/channel08','Data/data_spc/channel09'],
                    'utctime':'Data/utctime'
                },
                'Metadata': {
                    'type'          :'Metadata/type',
                    'channelList'   :'Metadata/channelList',
                    'heightList'    :'Metadata/heightList',
                    'ippSeconds'    :'Metadata/ippSeconds',
                    'nProfiles'     :'Metadata/nProfiles',
                    'codeList'      :'Metadata/codeList',
                    'timeZone'      :'Metadata/timeZone',
                    'azimuthList'   :'Metadata/azimuthList',
                    'elevationList' :'Metadata/elevationList',
                    'nCohInt'       :'Metadata/nCohInt',
                    'nIncohInt'     :'Metadata/nIncohInt',
                    'nFFTPoints'   :'Metadata/nFFTPoints'

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
procUnitConfObjA.addOperation(name='SpectralMoments')

'''
opObj11 = readUnitConfObj.addOperation(name='SpectraPlot',optype='external')
opObj11.addParameter(name='xmin', value=tmmin)
opObj11.addParameter(name='xmax', value=tmmax)
opObj11.addParameter(name='zmin', value=dBmin)
opObj11.addParameter(name='zmax', value=dBmax)
opObj11.addParameter(name='save', value=figpath)
opObj11.addParameter(name='showprofile', value=0)
opObj11.addParameter(name='save_period', value=10)
'''
controllerObj.start()
