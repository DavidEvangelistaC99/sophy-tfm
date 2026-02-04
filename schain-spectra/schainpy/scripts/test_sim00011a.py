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


path='/DATA_RM/TEST_HDF5/d2021231'
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
opObj11 = procUnitConfObjA.addOperation(name='PulsepairSignalPlot', optype='other')
opObj11 = procUnitConfObjA.addOperation(name='PulsepairVelocityPlot', optype='other')

controllerObj.start()
