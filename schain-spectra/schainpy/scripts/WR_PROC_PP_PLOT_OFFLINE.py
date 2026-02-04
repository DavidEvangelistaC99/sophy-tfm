import os,sys
import datetime
import time
from schainpy.controller import Project
#path='/DATA_RM/TEST_HDF5/d2021200'
#path='/DATA_RM/TEST_HDF5/d2021200'
#path='/DATA_RM/TEST_HDF5/d2021214'
#path='/DATA_RM/TEST_HDF5/d2021229'

#path='/DATA_RM/TEST_HDF5/d2021231'
#path='/DATA_RM/TEST_HDF5/ADQ_OFFLINE/d2021231'
path='/DATA_RM/TEST_HDF5/d2021231'
#path='/DATA_RM/TEST_14_HDF5/d2021257'
## TEST ULTIMA PRUEBA 22 DE SEPTIEMBRE
path = '/DATA_RM/TEST_HDF5_PP_22/d2021265'
#path = '/DATA_RM/TEST_HDF5_PP_100/d2021285'
path = '/DATA_RM/TEST_HDF5_PP/d2021285'


path_adq=path
#path_ped='/DATA_RM/TEST_PEDESTAL/P2021200'
#path_ped='/DATA_RM/TEST_PEDESTAL/P2021214'
#path_ped='/DATA_RM/TEST_PEDESTAL/P2021230'
#path_ped='/DATA_RM/TEST_PEDESTAL/P20210819'
#path_ped='/DATA_RM/TEST_PEDESTAL/P20210819-154315'
#path_ped='/DATA_RM/TEST_PEDESTAL/P20210914-162434'
#path_ped='/DATA_RM/TEST_PEDESTAL/PEDESTAL_OFFLINE/P20210819-161524'
#pruebas con perdida de datos
#path_ped='/DATA_RM/TEST_PEDESTAL/PEDESTAL_OFFLINE/P20210819-161524_TEST'
## TEST ULTIMA PRUEBA 22 DE SEPTIEMBRE
path_ped='/DATA_RM/TEST_PEDESTAL/P20211012-082745'


figpath = '/home/soporte/Pictures'
desc            = "Simulator Test"

controllerObj   = Project()
controllerObj.setup(id='10',name='Test Simulator',description=desc)
readUnitConfObj = controllerObj.addReadUnit(datatype='HDFReader',
                                            path=path,
                                            startDate="2021/01/01",   #"2020/01/01",#today,
                                            endDate= "2021/12/01",  #"2020/12/30",#today,
                                            startTime='00:00:00',
                                            endTime='23:59:59',
                                            t_Interval_p=0.01,
                                            n_Muestras_p=100,
                                            delay=30,
                                            #set=0,
                                            online=0,
                                            walk=0,
                                            nTries=6)#1

procUnitConfObjA = controllerObj.addProcUnit(datatype='ParametersProc',inputId=readUnitConfObj.getId())
V=10
blocksPerfile=360
print("Velocidad del Pedestal",V)
tmp_blocksPerfile=100
f_a_p= int(tmp_blocksPerfile/V)

opObj11 = procUnitConfObjA.addOperation(name='PedestalInformation')
opObj11.addParameter(name='path_ped', value=path_ped)
#opObj11.addParameter(name='path_adq', value=path_adq)
opObj11.addParameter(name='t_Interval_p', value='0.01', format='float')
opObj11.addParameter(name='blocksPerfile', value=blocksPerfile, format='int')
opObj11.addParameter(name='n_Muestras_p', value='100', format='float')
opObj11.addParameter(name='f_a_p', value=f_a_p, format='int')
opObj11.addParameter(name='online', value='0', format='int')# habilitar el enable aqui tambien


opObj11 = procUnitConfObjA.addOperation(name='Block360')
opObj11.addParameter(name='n', value='10', format='int')
opObj11.addParameter(name='mode', value=0, format='int')
# este bloque funciona bien con divisores de 360 no olvidar 0 10 20 30 40 60 90 120 180

opObj11= procUnitConfObjA.addOperation(name='WeatherPlot',optype='other')
#opObj11.addParameter(name='save', value=figpath)
#opObj11.addParameter(name='save_period', value=1)

controllerObj.start()
#online 1 utc_adq 1617490240.48
#online 0 utc_adq 1617489815.4804
