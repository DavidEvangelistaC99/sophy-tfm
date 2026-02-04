#!python
'''
'''

import os, sys
import datetime
import time

#path = os.path.dirname(os.getcwd())
#path = os.path.dirname(path)
#sys.path.insert(0, path)

from schainpy.controller import Project

desc = "USRP_test"
filename = "USRP_processing.xml"
controllerObj = Project()
controllerObj.setup(id = '191', name='Test_USRP', description=desc)

############## USED TO PLOT IQ VOLTAGE, POWER AND SPECTRA #############

#######################################################################
######PATH DE LECTURA, ESCRITURA, GRAFICOS Y ENVIO WEB#################
#######################################################################
#path = '/media/data/data/vientos/57.2063km/echoes/NCO_Woodman'
#path = '/DATA_RM/TEST_INTEGRACION'
#path = '/DATA_RM/TEST_ONLINE'
#path = '/DATA_RM/TEST_INTEGRACION/ADQ_OFFLINE/'
# ULTIMO TEST 22 DE SEPTIEMBRE
path = '/DATA_RM/USRP_22'
#path_pp = '/DATA_RM/TEST_HDF5'
# UTIMO TEST 22 DE SEPTIEMBRE
path_pp = '/DATA_RM/TEST_HDF5_PP_22'
######################################################
##### OJO TENER EN CUENTA EL n= para el Pulse Pair ###
######################################################
######## BUSCAMOS EL numero de IPP equivalente 1°#####
######## Sea V la velocidad del Pedestal en °/seg#####
######## 1° sera Recorrido en un tiempo de  1/V ######
######## IPP del Radar 400 useg --> 60 Km ############
######## n   = 1/(V*IPP) , NUMERO DE IPP #############
######## n   = 1/(V*IPP) #############################
V=2
IPP=400*1e-6
n= 1/(V*IPP)
print("n numero de Perfiles a procesar con Pulse Pair: ", n)




figpath = '/home/soporte/Pictures/TEST_INTEGRACION_IMG'
#remotefolder = "/home/wmaster/graficos"
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

procUnitConfObjA = controllerObj.addProcUnit(datatype='VoltageProc', inputId=readUnitConfObj.getId())

#
# codigo64='1,1,1,0,1,1,0,1,1,1,1,0,0,0,1,0,1,1,1,0,1,1,0,1,0,0,0,1,1,1,0,1,1,1,1,0,1,1,0,1,1,1,1,0,0,0,1,0,0,0,0,1,0,0,1,0,1,1,1,0,0,0,1,0,'+\
#              '1,1,1,0,1,1,0,1,1,1,1,0,0,0,1,0,1,1,1,0,1,1,0,1,0,0,0,1,1,1,0,1,0,0,0,1,0,0,1,0,0,0,0,1,1,1,0,1,1,1,1,0,1,1,0,1,0,0,0,1,1,1,0,1'

#opObj11 = procUnitConfObjA.addOperation(name='setRadarFrequency')
#opObj11.addParameter(name='frequency', value='70312500')
opObj11 = procUnitConfObjA.addOperation(name='PulsePair', optype='other')
opObj11.addParameter(name='n', value=int(n), format='int')#10 VOY A USAR 250 DADO  QUE LA VELOCIDAD ES 10 GRADOS
opObj11.addParameter(name='removeDC', value=1, format='int')


#######################################################################
########## OPERACIONES ParametersProc########################
#######################################################################

procUnitConfObjB= controllerObj.addProcUnit(datatype='ParametersProc',inputId=procUnitConfObjA.getId())
opObj10 = procUnitConfObjB.addOperation(name='HDFWriter')
opObj10.addParameter(name='path',value=path_pp)
#opObj10.addParameter(name='mode',value=0)
opObj10.addParameter(name='blocksPerFile',value='100',format='int')
opObj10.addParameter(name='metadataList',value='utctimeInit,timeZone,paramInterval,profileIndex,channelList,heightList,flagDataAsBlock',format='list')
opObj10.addParameter(name='dataList',value='dataPP_POW,dataPP_DOP,utctime',format='list')#,format='list'

controllerObj.start()
