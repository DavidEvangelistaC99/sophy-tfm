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
figpath_pp  = "/home/soporte/Pictures/TEST_PP"


IPP=400*1e-6
n= int(1/(V*IPP))
#n=250
print("* n - NRO Perfiles Proc:", n )

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

opObj11 = procUnitConfObjA.addOperation(name='PulsePair', optype='other')
opObj11.addParameter(name='n', value=int(n), format='int')#10 VOY A USAR 250 DADO  QUE LA VELOCIDAD ES 10 GRADOS
#opObj11.addParameter(name='removeDC', value=1, format='int')

procUnitConfObjB= controllerObj.addProcUnit(datatype='ParametersProc',inputId=procUnitConfObjA.getId())

opObj11 = procUnitConfObjB.addOperation(name='GenericRTIPlot',optype='external')
opObj11.addParameter(name='attr_data', value='dataPP_POWER')
opObj11.addParameter(name='colormap', value='jet')
opObj11.addParameter(name='xmin', value=xmin)
opObj11.addParameter(name='xmax', value=xmax)
opObj11.addParameter(name='zmin', value=dBmin)
opObj11.addParameter(name='zmax', value=dBmax)
opObj11.addParameter(name='save', value=figpath_pp)
opObj11.addParameter(name='showprofile', value=0)
#opObj11.addParameter(name='save_period', value=10)

controllerObj.start()
