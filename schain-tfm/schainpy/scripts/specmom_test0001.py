# Ing. AVP
# 06/10/2021
# ARCHIVO DE LECTURA
import os, sys
import datetime
import time
from schainpy.controller import Project

print("SETUP- RADAR METEOROLOGICO")
V       = 10
#######################################################################
################# RANGO DE PLOTEO######################################
dBmin = '1'
dBmax = '65'
xmin = '13.2'
xmax = '13.5'
ymin = '0'
ymax = '60'

path    = '/DATA_RM/WR_20_OCT'
figpath_spec = "/home/soporte/Pictures/TEST_MOM"


IPP=400*1e-6
n= int(1/(V*IPP))
print("* n - NRO Perfiles Proc:", n )
time.sleep(5)
desc = "USRP_test"
filename = "USRP_processing.xml"
controllerObj = Project()
controllerObj.setup(id = '191', name='Test_USRP', description=desc)
#######################################################################
######################## UNIDAD DE LECTURA#############################
#######################################################################
readUnitConfObj = controllerObj.addReadUnit(datatype='DigitalRFReader',
                                            path=path,
                                            startDate="2021/01/01",#today,
                                            endDate="2021/12/30",#today,
                                            startTime='00:00:00',
                                            endTime='23:59:59',
                                            delay=0,
                                            #set=0,
                                            online=0,
                                            walk=1,
                                            ippKm = 60)

opObj11 = readUnitConfObj.addOperation(name='printInfo')

procUnitConfObjA = controllerObj.addProcUnit(datatype='VoltageProc', inputId=readUnitConfObj.getId())

procUnitConfObjB = controllerObj.addProcUnit(datatype='SpectraProc', inputId=procUnitConfObjA.getId())
procUnitConfObjB.addParameter(name='nFFTPoints', value=n, format='int')
procUnitConfObjB.addParameter(name='nProfiles' , value=n, format='int')
'''
opObj11 = procUnitConfObjB.addOperation(name='RTIPlot', optype='external')
#.addParameter(name='id', value='2', format='int')
opObj11.addParameter(name='wintitle', value='RTIPlot', format='str')
opObj11.addParameter(name='xmin', value=xmin)
opObj11.addParameter(name='xmax', value=xmax)
opObj11.addParameter(name='zmin', value=dBmin, format='int')
opObj11.addParameter(name='zmax', value=dBmax, format='int')
'''
#opObj13 = procUnitConfObjB.addOperation(name='removeDC')
#opObj13.addParameter(name='mode', value='2', format='int')

procUnitConfObjC = controllerObj.addProcUnit(datatype='ParametersProc',inputId=procUnitConfObjB.getId())
procUnitConfObjC.addOperation(name='SpectralMoments')

dBmin = '1'
dBmax = '65'
opObj11 = procUnitConfObjC.addOperation(name='PowerPlot',optype='external')
opObj11.addParameter(name='xmin', value=xmin)
opObj11.addParameter(name='xmax', value=xmax)
opObj11.addParameter(name='zmin', value=dBmin)
opObj11.addParameter(name='zmax', value=dBmax)
opObj11.addParameter(name='save', value=figpath_spec)
opObj11.addParameter(name='showprofile', value=0)
#opObj11.addParameter(name='save_period', value=10)

controllerObj.start()
