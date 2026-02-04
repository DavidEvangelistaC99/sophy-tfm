import os,sys
import datetime
import time
from schainpy.controller import Project
path='/DATA_RM/TEST_HDF5'
path_adq=path
path_ped='/DATA_RM/TEST_PEDESTAL/P2021200'
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
                                            delay=5,
                                            #set=0,
                                            online=0,
                                            walk=1)#1

procUnitConfObjA = controllerObj.addProcUnit(datatype='ParametersProc',inputId=readUnitConfObj.getId())


controllerObj.start()
#online 1 utc_adq 1617490240.48
#online 0 utc_adq 1617489815.4804
