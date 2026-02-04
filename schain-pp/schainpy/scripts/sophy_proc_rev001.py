
#!python
'''
'''

import os, sys
import datetime
import time,json

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
path = '/home/soporte/Documents/EVENTO/HYO_PM@2022-05-31T12-00-17/rawdata'
figpath = '/home/soporte/Documents/EVENTO/Pictures'

PATH= '/home/soporte/Documents/EVENTO/'
experiment= 'HYO_PM@2022-05-31T12-00-17'
fp = open(os.path.join(PATH, experiment, 'experiment.conf'))
conf = json.loads(fp.read())
#######################################################################
################# RANGO DE PLOTEO######################################
#######################################################################
dBmin = '-55'#'-20'
dBmax = '-35'#'-85'
xmin = '0'
xmax ='24'
ymin = '0'
ymax = '15'
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
                                            startDate="2022/05/31",#today,
                                            endDate="2022/05/31",#today,
                                            startTime='16:26:00',# inicio libre
                                            #startTime='00:00:00',
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
#------------------------

op = procUnitConfObjA.addOperation(name='ProfileSelector')
op.addParameter(name='profileRangeList', value='{},{}'.format(conf['usrp_tx']['repetitions_1'], conf['usrp_tx']['repetitions_1']+conf['usrp_tx']['repetitions_2']-1))

if conf['usrp_tx']['code_type_2']:
    codes = [ c.strip() for c in conf['usrp_tx']['code_2'].split(',')]
    code = []
    for c in codes:
        code.append([int(x) for x in c])
    op = procUnitConfObjA.addOperation(name='Decoder', optype='other')
    op.addParameter(name='code', value=code)
    op.addParameter(name='nCode', value=len(code), format='int')
    op.addParameter(name='nBaud', value=len(code[0]), format='int')

    op =procUnitConfObjA.addOperation(name='CohInt', optype='other') #Minimo integrar 2 perfiles por ser codigo complementario
    op.addParameter(name='n', value=len(code), format='int')
    ncode = len(code)
else:
    ncode = 1

#------------------------

#op3 = procUnitConfObjA.addOperation(name='ProfileSelector', optype='other')
#op3.addParameter(name='profileRangeList', value='0,121')
#code=[[1]]
#opObj11 = procUnitConfObjA.addOperation(name='Decoder', optype='other')
#opObj11.addParameter(name='code', value=code)
#opObj11.addParameter(name='nCode', value='1', format='int')
#opObj11.addParameter(name='nBaud', value='1', format='int')

op = procUnitConfObjA.addOperation(name='setH0')
op.addParameter(name='h0', value='-1.62')

#op = procUnitConfObjA.addOperation(name='CohInt', optype='other') #Minimo integrar 2 perfiles por ser codigo complementario
#op.addParameter(name='n', value=2, format='int')


# OJO SCOPE
'''
opObj10 = procUnitConfObjA.addOperation(name='ScopePlot', optype='external')
opObj10.addParameter(name='id', value='10', format='int')
opObj10.addParameter(name='xmin', value='0', format='int')
opObj10.addParameter(name='xmax', value='10', format='int')
opObj10.addParameter(name='type', value='iq')
opObj10.addParameter(name='ymin', value='-4', format='int')
opObj10.addParameter(name='ymax', value='4', format='int')
opObj10.addParameter(name='save', value=figpath, format='str')
opObj10.addParameter(name='save_period', value=1, format='int')
'''
'''
opObj11 = procUnitConfObjA.addOperation(name='selectHeights')
opObj11.addParameter(name='minIndex', value='1', format='int')
#    opObj11.addParameter(name='maxIndex', value='10000', format='int')
opObj11.addParameter(name='maxIndex', value='200', format='int')
'''

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

#######################################################################
########## OPERACIONES DOMINIO DE LA FRECUENCIA########################
#######################################################################

#procUnitConfObjB = controllerObj.addProcUnit(datatype='SpectraProc', inputId=procUnitConfObjA.getId())
#procUnitConfObjB.addParameter(name='nFFTPoints', value='64', format='int')
#procUnitConfObjB.addParameter(name='nProfiles', value='64', format='int')


procUnitConfObjB = controllerObj.addProcUnit(datatype='SpectraProc', inputId=procUnitConfObjA.getId())
procUnitConfObjB.addParameter(name='nFFTPoints', value='64', format='int')
procUnitConfObjB.addParameter(name='nProfiles', value='64', format='int')

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
opObj11.addParameter(name='grid', value=True, format
[Reading] 2022-05-23 12:27:32.732775: 21333 samples <> 0.010667 sec
='bool')
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
procUnitConfObjC= controllerObj.addProcUnit(datatype='ParametersProc',inputId=procUnitConfObjB.getId())
procUnitConfObjC.addOperation(name='SpectralMoments')
#opObj11 = procUnitConfObjC.addOperation(name='PowerPlot')

'''
opObj11 = procUnitConfObjC.addOperation(name='SpectralMomentsPlot')
#opObj11.addParameter(name='xmin', value=14)
#opObj11.addParameter(name='xmax', value=15)
opObj11.addParameter(name='save', value=figpath)
opObj11.addParameter(name='showprofile', value=1)
opObj11.addParameter(name='save_period', value=10)

'''
opObj11 = procUnitConfObjC.addOperation(name='SpectralWidthPlot')
opObj11.addParameter(name='showprofile', value=1)



#SpectraPlot
'''
opObj11 = procUnitConfObjB.addOperation(name='SpectraPlot', optype='external')
opObj11.addParameter(name='id', value='1', format='int')
opObj11.addParameter(name='wintitle', value='Spectra', format='str')
#opObj11.addParameter(name='xmin', value=-0.01, format='float')
#opObj11.addParameter(name='xmax', value=0.01, format='float')
opObj11.addParameter(name='zmin', value=dBmin, format='int')
opObj11.addParameter(name='zmax', value=dBmax, format='int')
opObj11.addParameter(name='ymin', value=ymin, format='int')
opObj11.addParameter(name='ymax', value=ymax, format='int')
opObj11.addParameter(name='showprofile', value='1', format='int')
opObj11.addParameter(name='save', value=figpath, format='str')
'''
#RTIPLOT
'''
opObj11 = procUnitConfObjB.addOperation(name='RTIPlot', optype='external')
opObj11.addParameter(name='id', value='2', format='int')
opObj11.addParameter(name='wintitle', value='RTIPlot', format='str')
opObj11.addParameter(name='zmin', value=dBmin, format='int')
opObj11.addParameter(name='zmax', value=dBmax, format='int')
#opObj11.addParameter(name='ymin', value=ymin, format='int')
#opObj11.addParameter(name='ymax', value=ymax, format='int')
#opObj11.addParameter(name='xmin', value=15, format='int')
#opObj11.addParameter(name='xmax', value=16, format='int')
opObj11.addParameter(name='zmin', value=dBmin, format='int')
opObj11.addParameter(name='zmax', value=dBmax, format='int')

opObj11.addParameter(name='showprofile', value='1', format='int')
opObj11.addParameter(name='save', value=figpath, format='str')
opObj11.addParameter(name='save_period', value=10, format='int')
'''
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
