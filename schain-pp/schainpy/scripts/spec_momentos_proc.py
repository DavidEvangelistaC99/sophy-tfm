#!python

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

path = '/DATA_RM/TEST_19OCTUBRE/10MHZ'
#path_pp = '/DATA_RM/TEST_HDF5'
path_pp = '/DATA_RM/TEST_HDF5_19OCT'

#######################################################################
################# RANGO DE PLOTEO######################################
#######################################################################
dBmin = '-5'
dBmax = '20'
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
#opObj11 = readUnitConfObj.addOperation(name='printNumberOfBlock')
#######################################################################
################ OPERACIONES DOMINIO DEL TIEMPO########################
#######################################################################
V=10 # aca se coloca la velocidad
IPP=400*1e-6
n= int(1/(V*IPP))
print("n numero de Perfiles a procesar con nFFTPoints ", n)

procUnitConfObjA = controllerObj.addProcUnit(datatype='VoltageProc', inputId=readUnitConfObj.getId())

procUnitConfObjB = controllerObj.addProcUnit(datatype='SpectraProc', inputId=procUnitConfObjA.getId())
procUnitConfObjB.addParameter(name='nFFTPoints', value=n, format='int')
procUnitConfObjB.addParameter(name='nProfiles' , value=n, format='int')

#######################################################################
########## OPERACIONES ParametersProc########################
#######################################################################

procUnitConfObjC= controllerObj.addProcUnit(datatype='ParametersProc',inputId=procUnitConfObjB.getId())

procUnitConfObjC.addOperation(name='SpectralMoments')

opObj10 = procUnitConfObjC.addOperation(name='HDFWriter')
opObj10.addParameter(name='path',value=path_pp)
#opObj10.addParameter(name='mode',value=0)
opObj10.addParameter(name='blocksPerFile',value='100',format='int')
#opObj10.addParameter(name='metadataList',value='utctimeInit,heightList,nIncohInt,nCohInt,nProfiles,channelList',format='list')#profileIndex
opObj10.addParameter(name='metadataList',value='utctimeInit,heightList,nIncohInt,nCohInt,nProfiles,channelList',format='list')#profileIndex

opObj10.addParameter(name='dataList',value='data_pow,data_dop,utctime',format='list')#,format='list'

controllerObj.start()
