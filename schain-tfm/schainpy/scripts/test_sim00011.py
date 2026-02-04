import os,sys
import datetime
import time
from schainpy.controller import Project
'''
NOTA:
Este script de prueba.
- Unidad del lectura 'HDFReader'.
- Unidad de procesamiento VoltageProc
- Unidad de procesamiento SpectraProc
- Operacion removeDC.
- Unidad de procesamiento ParametersProc
- Operacion SpectralMoments
- Operacion SpectralMomentsPlot
- Unidad de escrituda 'HDFWriter'.
'''
path='/home/developer/Downloads/HDF5_WR'
figpath = path
desc            = "Simulator Test"

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
                                            walk=0)#1

procUnitConfObjA = controllerObj.addProcUnit(datatype='ParametersProc',inputId=readUnitConfObj.getId())

opObj11 = procUnitConfObjA.addOperation(name='Block360')
opObj11.addParameter(name='n', value='40', format='int')

opObj11= procUnitConfObjA.addOperation(name='WeatherPlot',optype='other')
opObj11.addParameter(name='save', value=figpath)
opObj11.addParameter(name='save_period', value=1)
#opObj11 = procUnitConfObjA.addOperation(name='PowerPlot', optype='other')#PulsepairPowerPlot
#opObj11 = procUnitConfObjA.addOperation(name='PPSignalPlot', optype='other')

controllerObj.start()
