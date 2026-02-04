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
#path_pp = '/DATA_RM/TEST_HDF5'

#figpath = '/home/soporte/Pictures/TEST_INTEGRACION_IMG'
###path = '/DATA_RM/TEST_INTEGRACION/ADQ_OFFLINE/'
###path_pp = '/DATA_RM/TEST_HDF5_SPEC'

#path = '/DATA_RM/USRP_22'
###path = '/DATA_RM/23/6v'
path = '/DATA_RM/TEST_19OCTUBRE/10MHZ'
#path_pp = '/DATA_RM/TEST_HDF5'
path_pp = '/DATA_RM/TEST_HDF5_19OCT' 
# UTIMO TEST 22 DE SEPTIEMBRE
#path_pp = '/DATA_RM/TEST_HDF5_SPEC_22'
#path_pp = '/DATA_RM/TEST_HDF5_SPEC_3v'
###path_pp = '/DATA_RM/TEST_HDF5_SPEC_23/6v'


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


V=10
IPP=400*1e-6
n= int(1/(V*IPP))
print("n numero de Perfiles a procesar con nFFTPoints ", n)

procUnitConfObjA = controllerObj.addProcUnit(datatype='VoltageProc', inputId=readUnitConfObj.getId())

procUnitConfObjB = controllerObj.addProcUnit(datatype='SpectraProc', inputId=procUnitConfObjA.getId())
procUnitConfObjB.addParameter(name='nFFTPoints', value=n, format='int')
procUnitConfObjB.addParameter(name='nProfiles' , value=n, format='int')



#
# codigo64='1,1,1,0,1,1,0,1,1,1,1,0,0,0,1,0,1,1,1,0,1,1,0,1,0,0,0,1,1,1,0,1,1,1,1,0,1,1,0,1,1,1,1,0,0,0,1,0,0,0,0,1,0,0,1,0,1,1,1,0,0,0,1,0,'+\
#              '1,1,1,0,1,1,0,1,1,1,1,0,0,0,1,0,1,1,1,0,1,1,0,1,0,0,0,1,1,1,0,1,0,0,0,1,0,0,1,0,0,0,0,1,1,1,0,1,1,1,1,0,1,1,0,1,0,0,0,1,1,1,0,1'

#opObj11 = procUnitConfObjA.addOperation(name='setRadarFrequency')
#opObj11.addParameter(name='frequency', value='70312500')
#opObj11 = procUnitConfObjA.addOperation(name='PulsePair', optype='other')
#opObj11.addParameter(name='n', value='625', format='int')#10
#opObj11.addParameter(name='removeDC', value=1, format='int')

# Ploteo TEST
'''
opObj11 = procUnitConfObjA.addOperation(name='PulsepairPowerPlot', optype='other')
opObj11 = procUnitConfObjA.addOperation(name='PulsepairSignalPlot', optype='other')
opObj11 = procUnitConfObjA.addOperation(name='PulsepairVelocityPlot', optype='other')
#opObj11.addParameter(name='xmax', value=8)
opObj11 = procUnitConfObjA.addOperation(name='PulsepairSpecwidthPlot', optype='other')
'''
# OJO SCOPE
#opObj10 = procUnitConfObjA.addOperation(name='ScopePlot', optype='external')
#opObj10.addParameter(name='buffer_sizeid', value='10', format='int')
##opObj10.addParameter(name='xmin', value='0', format='int')
##opObj10.addParameter(name='xmax', value='50', format='int')
#opObj10.addParameter(name='type', value='iq')
##opObj10.addParameter(name='ymin', value='-5000', format='int')
##opObj10.addParameter(name='ymax', value='8500', format='int')
#opObj11.addParameter(name='save', value=figpath, format='str')
#opObj11.addParameter(name='save_period', value=10, format='int')

#opObj10 = procUnitConfObjA.addOperation(name='setH0')
#opObj10.addParameter(name='h0', value='-5000', format='float')

#opObj11 =  procUnitConfObjA.addOperation(name='filterByHeights')
#opObj11.addParameter(name='window', value='1', format='int')

#codigo='1,1,-1,1,1,-1,1,-1,-1,1,-1,-1,-1,1,-1,-1,-1,1,-1,-1,-1,1,1,1,1,-1,-1,-1'
#opObj11 = procUnitConfObjSousy.addOperation(name='Decoder', optype='other')
#opObj11.addParameter(name='code', value=codigo, formatyesterday='floatlist')
#opObj11.addParameter(name='nCode', value='1', format='int')
#opObj11.addParameter(name='nBaud', value='28', format='int')

#opObj11 = procUnitConfObjA.addOperation(name='CohInt', optype='other')
#opObj11.addParameter(name='n', value='100', format='int')

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
