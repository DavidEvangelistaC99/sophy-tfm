#!python
'''
'''

import os, sys
import datetime
import time


from schainpy.controller import Project

desc = "USRP_test"
filename = "USRP_processing.xml"
controllerObj = Project()
controllerObj.setup(id = '191', name='Test_USRP', description=desc)

############## USED TO PLOT IQ VOLTAGE, POWER AND SPECTRA #############

#######################################################################
######PATH DE LECTURA, ESCRITURA, GRAFICOS Y ENVIO WEB#################
#######################################################################
# path JHON
path = '/home/soporte/jars2'

figpath = '/home/soporte/Pictures/JHON'
#remotefolder = "/home/wmaster/graficos"
#######################################################################
################# RANGO DE PLOTEO######################################
#######################################################################
dBmin = '0'
dBmax = '50'
xmin = '0'
xmax ='24'
ymin = '0'
ymax = '600'
#######################################################################
########################FECHA##########################################
#######################################################################
str = datetime.date.today()
today = str.strftime("%Y/%m/%d")
str2 = str - datetime.timedelta(days=1)
yesterday = str2.strftime("%Y/%m/%d")
#######################################################################
######################## UNIDAD DE LECTURA#############################
#######################################################################
readUnitConfObj = controllerObj.addReadUnit(datatype='VoltageReader',
                                            path=path,
                                            startDate="2021/07/02",#today,
                                            endDate="2021/07/02",#today,
                                            startTime='19:45:00',# inicio libre
                                            endTime='19:50:59',
                                            delay=0,
                                            #set=0,
                                            online=0,
                                            walk=0)

opObj11 = readUnitConfObj.addOperation(name='printInfo')
#opObj11 = readUnitConfObj.addOperation(name='printNumberOfBlock')
#######################################################################
################ OPERACIONES DOMINIO DEL TIEMPO########################
#######################################################################

procUnitConfObjA = controllerObj.addProcUnit(datatype='VoltageProc', inputId=readUnitConfObj.getId())

opObj11 = procUnitConfObjA.addOperation(name='selectHeights')
opObj11.addParameter(name='minIndex', value='1', format='int')
#    opObj11.addParameter(name='maxIndex', value='10000', format='int')
opObj11.addParameter(name='maxIndex', value='39980', format='int')


#######################################################################
########## OPERACIONES DOMINIO DE LA FRECUENCIA########################
#######################################################################

#procUnitConfObjB = controllerObj.addProcUnit(datatype='SpectraProc', inputId=procUnitConfObjA.getId())
#procUnitConfObjB.addParameter(name='nFFTPoints', value='32', format='int')
#procUnitConfObjB.addParameter(name='nProfiles', value='32', format='int')

procUnitConfObjC = controllerObj.addProcUnit(datatype='SpectraHeisProc', inputId=procUnitConfObjA.getId())

#opObj11 = procUnitConfObjC.addOperation(name='IncohInt4SpectraHeis', optype='other')
#opObj11.addParameter(name='timeInterval', value='4', format='int')
opObj11 = procUnitConfObjC.addOperation(name='IncohInt4SpectraHeis', optype='other')
#opObj11.addParameter(name='timeInterval', value='4', format='int')
opObj11.addParameter(name='n', value='100', format='int')


opObj11 = procUnitConfObjC.addOperation(name='SpectraHeisPlot')
opObj11.addParameter(name='id', value='10', format='int')
opObj11.addParameter(name='wintitle', value='Spectra_Alturas', format='str')
#opObj11.addParameter(name='xmin', value=-100000, format='float')
#opObj11.addParameter(name='xmax', value=100000, format='float')
opObj11.addParameter(name='oneFigure', value=False,format='bool')
#opObj11.addParameter(name='zmin', value=-10, format='int')
#opObj11.addParameter(name='zmax', value=40, format='int')
opObj11.addParameter(name='ymin', value=dBmin, format='int')
opObj11.addParameter(name='ymax', value=dBmax, format='int')
opObj11.addParameter(name='grid', value=True, format='bool')
#opObj11.addParameter(name='showprofile', value='1', format='int')
opObj11.addParameter(name='save', value=figpath, format='str')
#opObj11.addParameter(name='save_period', value=10, format='int')

controllerObj.start()
