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
#path = '/DATA_RM/PRUEBA_USRP_RP'
#path = '/DATA_RM/PRUEBA_USRP_RP'

path = '/DATA_RM/TEST_2M'
path = '/DATA_RM/TEST_2M_UD'
path = '/DATA_RM/2MHZ17022022'
path = '/DATA_RM/10MHZTEST/'
path = '/DATA_RM/10MHZDRONE/'

#figpath = '/home/soporte/Pictures/TEST_RP_0001'
#figpath = '/home/soporte/Pictures/TEST_RP_6000'
figpath = '/home/soporte/Pictures/USRP_TEST_2M'
figpath = '/home/soporte/Pictures/USRP_TEST_2M_UD'
figpaht = '/home/soporte/Pictures/10MHZDRONE'
#remotefolder = "/home/wmaster/graficos"
#######################################################################
################# RANGO DE PLOTEO######################################
#######################################################################
dBmin = '20'
dBmax = '60'
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
                                            startDate="2022/02/18",#today,
                                            endDate="2022/02/18",#today,
                                            startTime='00:00:00',# inicio libre
                                            #startTime='00:00:00',
                                            endTime='23:59:59',
                                            delay=0,
                                            #set=0,
                                            online=1,
                                            walk=1,
                                            ippKm = 60)

opObj11 = readUnitConfObj.addOperation(name='printInfo')
#opObj11 = readUnitConfObj.addOperation(name='printNumberOfBlock')
#######################################################################
################ OPERACIONES DOMINIO DEL TIEMPO########################
#######################################################################

procUnitConfObjA = controllerObj.addProcUnit(datatype='VoltageProc', inputId=readUnitConfObj.getId())

'''
# OJO SCOPE
opObj10 = procUnitConfObjA.addOperation(name='ScopePlot', optype='external')
opObj10.addParameter(name='id', value='10', format='int')
##opObj10.addParameter(name='xmin', value='0', format='int')
##opObj10.addParameter(name='xmax', value='50', format='int')
opObj10.addParameter(name='type', value='iq')
opObj10.addParameter(name='ymin', value='-1200', format='int')
opObj10.addParameter(name='ymax', value='1200', format='int')
opObj10.addParameter(name='save', value=figpath, format='str')
opObj10.addParameter(name='save_period', value=10, format='int')
'''
'''
opObj11 = procUnitConfObjA.addOperation(name='selectHeights')
opObj11.addParameter(name='minIndex', value='1', format='int')
#    opObj11.addParameter(name='maxIndex', value='10000', format='int')
opObj11.addParameter(name='maxIndex', value='39980', format='int')
'''
#
# codigo64='1,1,1,0,1,1,0,1,1,1,1,0,0,0,1,0,1,1,1,0,1,1,0,1,0,0,0,1,1,1,0,1,1,1,1,0,1,1,0,1,1,1,1,0,0,0,1,0,0,0,0,1,0,0,1,0,1,1,1,0,0,0,1,0,'+\
#              '1,1,1,0,1,1,0,1,1,1,1,0,0,0,1,0,1,1,1,0,1,1,0,1,0,0,0,1,1,1,0,1,0,0,0,1,0,0,1,0,0,0,0,1,1,1,0,1,1,1,1,0,1,1,0,1,0,0,0,1,1,1,0,1'

#opObj11 = procUnitConfObjA.addOperation(name='setRadarFrequency')
#opObj11.addParameter(name='frequency', value='49920000')

'''
opObj11 = procUnitConfObjA.addOperation(name='PulsePair', optype='other')
opObj11.addParameter(name='n', value='625', format='int')#10
opObj11.addParameter(name='removeDC', value=1, format='int')
'''

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
#opObj10.addParameter(name='id', value='10', format='int')
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
#opObj11.addParameter(name='code', value=codigo, format='floatlist')
#opObj11.addParameter(name='nCode', value='1', format='int')
#opObj11.addParameter(name='nBaud', value='28', format='int')

#opObj11 = procUnitConfObjA.addOperation(name='CohInt', optype='other')
#opObj11.addParameter(name='n', value='100', format='int')

#######################################################################
########## OPERACIONES ParametersProc########################
#######################################################################
###procUnitConfObjB= controllerObj.addProcUnit(datatype='ParametersProc',inputId=procUnitConfObjA.getId())
'''

opObj11 = procUnitConfObjA.addOperation(name='PedestalInformation')
opObj11.addParameter(name='path_ped', value=path_ped)
opObj11.addParameter(name='path_adq', value=path_adq)
opObj11.addParameter(name='t_Interval_p', value='0.01', format='float')
opObj11.addParameter(name='n_Muestras_p', value='100', format='float')
opObj11.addParameter(name='blocksPerfile', value='100', format='int')
opObj11.addParameter(name='f_a_p', value='25', format='int')
opObj11.addParameter(name='online', value='0', format='int')

opObj11 = procUnitConfObjA.addOperation(name='Block360')
opObj11.addParameter(name='n', value='40', format='int')

opObj11= procUnitConfObjA.addOperation(name='WeatherPlot',optype='other')
opObj11.addParameter(name='save', value=figpath)
opObj11.addParameter(name='save_period', value=1)

8
'''



opObj11 = procUnitConfObjA.addOperation(name='CohInt', optype='other')
opObj11.addParameter(name='n', value='250', format='int')

#######################################################################
########## OPERACIONES DOMINIO DE LA FRECUENCIA########################
#######################################################################

procUnitConfObjB = controllerObj.addProcUnit(datatype='SpectraProc', inputId=procUnitConfObjA.getId())
procUnitConfObjB.addParameter(name='nFFTPoints', value='32', format='int')
procUnitConfObjB.addParameter(name='nProfiles', value='32', format='int')
'''
procUnitConfObjC = controllerObj.addProcUnit(datatype='SpectraHeisProc', inputId=procUnitConfObjA.getId())
#procUnitConfObjB.addParameter(name='nFFTPoints', value='64', format='int')
#procUnitConfObjB.addParameter(name='nProfiles', value='64', format='int')
opObj11 = procUnitConfObjC.addOperation(name='IncohInt4SpectraHeis', optype='other')
#opObj11.addParameter(name='timeInterval', value='4', format='int')
opObj11.addParameter(name='n', value='100', format='int')

#procUnitConfObjB.addParameter(name='pairsList', value='(0,0),(1,1),(0,1)', format='pairsList')

#opObj13 = procUnitConfObjB.addOperation(name='removeDC')
#opObj13.addParameter(name='mode', value='2', format='int')

#opObj11 = procUnitConfObjB.addOperation(name='IncohInt', optype='other')
#opObj11.addParameter(name='n', value='8', format='float')
#######################################################################
########## PLOTEO DOMINIO DE LA FRECUENCIA#############################
#######################################################################
#----
'''
'''
opObj11 = procUnitConfObjC.addOperation(name='SpectraHeisPlot')
opObj11.addParameter(name='id', value='10', format='int')
opObj11.addParameter(name='wintitle', value='Spectra_Alturas', format='str')
#opObj11.addParameter(name='xmin', value=-100000, format='float')
#opObj11.addParameter(name='xmax', value=100000, format='float')
opObj11.addParameter(name='oneFigure', value=False,format='bool')
#opObj11.addParameter(name='zmin', value=-10, format='int')
#opObj11.addParameter(name='zmax', value=40, format='int')
opObj11.addParameter(name='ymin', value=10, format='int')
opObj11.addParameter(name='ymax', value=55, format='int')
opObj11.addParameter(name='grid', value=True, format='bool')
#opObj11.addParameter(name='showprofile', value='1', format='int')
opObj11.addParameter(name='save', value=figpath, format='str')
#opObj11.addParameter(name='save_period', value=10, format='int')
'''
'''
opObj11 = procUnitConfObjC.addOperation(name='RTIHeisPlot')
opObj11.addParameter(name='id', value='10', format='int')
opObj11.addParameter(name='wintitle', value='RTI_Alturas', format='str')
opObj11.addParameter(name='xmin', value=11.0, format='float')
opObj11.addParameter(name='xmax', value=18.0, format='float')
opObj11.addParameter(name='zmin', value=10, format='int')
opObj11.addParameter(name='zmax', value=30, format='int')
opObj11.addParameter(name='ymin', value=5, format='int')
opObj11.addParameter(name='ymax', value=28, format='int')
opObj11.addParameter(name='showprofile', value='1', format='int')
opObj11.addParameter(name='save', value=figpath, format='str')
opObj11.addParameter(name='save_period', value=10, format='int')
'''

#SpectraPlot

opObj11 = procUnitConfObjB.addOperation(name='SpectraPlot', optype='external')
opObj11.addParameter(name='id', value='1', format='int')
opObj11.addParameter(name='wintitle', value='Spectra', format='str')
#opObj11.addParameter(name='xmin', value=-0.01, format='float')
#opObj11.addParameter(name='xmax', value=0.01, format='float')
opObj11.addParameter(name='zmin', value=dBmin, format='int')
opObj11.addParameter(name='zmax', value=dBmax, format='int')
#opObj11.addParameter(name='ymin', value=ymin, format='int')
#opObj11.addParameter(name='ymax', value=ymax, format='int')
opObj11.addParameter(name='showprofile', value='1', format='int')
opObj11.addParameter(name='save', value=figpath, format='str')
opObj11.addParameter(name='save_period', value=10, format='int')


#RTIPLOT

opObj11 = procUnitConfObjB.addOperation(name='RTIPlot', optype='external')
opObj11.addParameter(name='id', value='2', format='int')
opObj11.addParameter(name='wintitle', value='RTIPlot', format='str')
opObj11.addParameter(name='zmin', value=dBmin, format='int')
opObj11.addParameter(name='zmax', value=dBmax, format='int')
#opObj11.addParameter(name='ymin', value=ymin, format='int')
#opObj11.addParameter(name='ymax', value=ymax, format='int')
#opObj11.addParameter(name='xmin', value=15, format='int')
#opObj11.addParameter(name='xmax', value=16, format='int')

opObj11.addParameter(name='showprofile', value='1', format='int')
opObj11.addParameter(name='save', value=figpath, format='str')
opObj11.addParameter(name='save_period', value=10, format='int')

'''
# opObj11 = procUnitConfObjB.addOperation(name='CrossSpectraPlot', optype='other')
# opObj11.addParameter(name='id', value='3', format='int')
# opObj11.addParameter(name='wintitle', value='CrossSpectraPlot', format='str')
# opObj11.addParameter(name='ymin', value=ymin, format='int')
# opObj11.addParameter(name='ymax', value=ymax, format='int')
# opObj11.addParameter(name='phase_cmap', value='jet', format='str')
# opObj11.addParameter(name='zmin', value=dBmin, format='int')
# opObj11.addParameter(name='zmax', value=dBmax, format='int')
# opObj11.addParameter(name='figpath', value=figures_path, format='str')
# opObj11.addParameter(name='save', value=0, format='bool')
# opObj11.addParameter(name='pairsList', value='(0,1)', format='pairsList')
# #
# opObj11 = procUnitConfObjB.addOperation(name='CoherenceMap', optype='other')
# opObj11.addParameter(name='id', value='4', format='int')
# opObj11.addParameter(name='wintitle', value='Coherence', format='str')
# opObj11.addParameter(name='phase_cmap', value='jet', format='str')
# opObj11.addParameter(name='xmin', value=xmin, format='float')
# opObj11.addParameter(name='xmax', value=xmax, format='float')
# opObj11.addParameter(name='figpath', value=figures_path, format='str')
# opObj11.addParameter(name='save', value=0, format='bool')
# opObj11.addParameter(name='pairsList', value='(0,1)', format='pairsList')
#
'''
'''
#######################################################################
############### UNIDAD DE ESCRITURA ###################################
#######################################################################
#opObj11 = procUnitConfObjB.addOperation(name='SpectraWriter', optype='other')
#opObj11.addParameter(name='path', value=wr_path)
#opObj11.addParameter(name='blocksPerFile', value='50', format='int')
print ("Escribiendo el archivo XML")
print ("Leyendo el archivo XML")
'''


controllerObj.start()
