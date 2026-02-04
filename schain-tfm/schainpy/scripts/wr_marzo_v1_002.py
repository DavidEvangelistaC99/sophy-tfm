# Ing. AVP
# 06/10/2021
# ARCHIVO DE LECTURA
import os, sys
import datetime
import time
from schainpy.controller import Project
#### NOTA###########################################
# INPUT :
# VELOCIDAD PARAMETRO :        V = 2°/seg
# MODO PULSE PAIR O MOMENTOS:  0 : Pulse Pair ,1 : Momentos
######################################################
##### PROCESAMIENTO ##################################
#####  OJO TENER EN CUENTA EL n= para el Pulse Pair ##
#####                   O EL n= nFFTPoints         ###
######################################################
######## BUSCAMOS EL numero de IPP equivalente 1°#####
######## Sea V la velocidad del Pedestal en °/seg#####
######## 1° sera Recorrido en un tiempo de  1/V ######
######## IPP del Radar 400 useg --> 60 Km ############
######## n   = 1/(V(°/seg)*IPP(Km)) , NUMERO DE IPP ##
######## n   = 1/(V*IPP) #############################

#-------------------------VELOCIDAD DEL PEDESTAL Y MODO ------------------------
print("SETUP- RADAR METEOROLOGICO")
IPP        = 400*1e-6
V          = 12
samp_rate  = 10# VERIFICAR
MODE_TABLE = 1             #  PUEDE SER 1 sO 0
AXIS       = [1,1,1,1]     #  AZIMUTH 1 ELEVACION 0
SPEED_AXIS = [10,10,10,10] #  VELOCIDAD
ANGLE_AXIS = [20,25,30,15] #  ANGULOS
mode_proc       = 0
#-----------------------------PATH ADQ Y PEDESTAL-------------------------------
path     = "/DATA_RM/DRONE2"
path_ped = "/DATA_RM/TEST_PEDESTAL/P20220329-174143"
#-------------------------------------------------------------------------------
figpath_pp     = "/home/soporte/Pictures/MARTES_29_PP_10M_.1us"
figpath_spec   = "/home/soporte/Pictures/MARTES_29_10M_.1us"
figpath_pp_ppi = "/home/soporte/Pictures/MARTES_29_10M_.1us_PPI"
#--------------------------OPCIONES---------------------------------------------
plot        = 1
plot_ppi    = 1
integration = 1
save        = 0
plot_spec   = 0
#---------------------------SAVE HDF5 PROCESADO/--------------------------------
if save == 1:
    if mode_proc==0:
        path_save = '/DATA_RM/TEST_HDF5_PP_MAR22/6v'
    else:
        path_save = '/DATA_RM/TEST_HDF5_SPEC_MAR22/6v'
print("[SETUP]-RADAR METEOROLOGICO-")
print("* PATH data ADQ        :", path)
print("* PATH data PED        :", path_ped)
print("* SAMPLE RATE ADQ Mhz  :", samp_rate)
print("* Velocidad Pedestal   :",V,"°/seg")
print("* Configuracion del Pedestal *")

print("*** AXIS      :",AXIS)
print("*** SPEED_AXIS:",SPEED_AXIS)
print("*** ANGLE_AXIS:",ANGLE_AXIS)
num_alturas  = int(samp_rate*IPP*1e6)
print("* Nro de Altura        :",num_alturas)

############################ NRO Perfiles PROCESAMIENTO ###################
V=V
n= int(1/(V*IPP))
print("* n - NRO Perfiles Proc:", n )
################################## MODE ###################################
print("* Modo de Operacion    :",mode_proc)
if mode_proc ==0:
    print("* Met. Seleccionado    : Pulse Pair")
else:
    print("* Met. Momentos        : Momentos")
################################## MODE ###################################
print("* Grabado de datos     :",save)
if save ==1:
    if mode_proc==0:
       print("[ ON ] MODE PULSEPAIR")

    else:
       print("[ ON ] MODE FREQUENCY")

print("* Integracion de datos :",integration)

print("* Ploteo de datos Parameters:", plot)
if plot==1:
    print("* Path PP plot    :", figpath_pp )

if plot_ppi==1:
    print("* Path PPI plot    :", figpath_pp_ppi )

time.sleep(5)
#remotefolder = "/home/wmaster/graficos"
################# RANGO DE PLOTEO######################################
dBmin = '20'
dBmax = '80'
xmin  = '17.6' #17.1,17.5
xmax  = '17.9' #17.2,17.8
ymin  = '0'    #### PONER A 0
ymax  = '8'    #### PONER A 8
########################FECHA##########################################
str1 = datetime.date.today()
today = str1.strftime("%Y/%m/%d")
str2 = str1 - datetime.timedelta(days=1)
yesterday = str2.strftime("%Y/%m/%d")

#------------------------SIGNAL CHAIN-------------------------------------------
desc = "USRP_test"
filename = "USRP_processing.xml"
controllerObj = Project()
controllerObj.setup(id = '191', name='Test_USRP', description=desc)
#------------------------ UNIDAD DE LECTURA-------------------------------------
readUnitConfObj = controllerObj.addReadUnit(datatype='DigitalRFReader',
                                            path=path,
                                            startDate="2022/03/29",#today,
                                            endDate="2022/03/29",#today,
                                            startTime='17:40:00',#'17:39:25',
                                            endTime='23:59:59',#23:59:59',
                                            delay=0,
                                            #set=0,
                                            online=0,
                                            walk=1,
                                            ippKm = 60,
                                            getByBlock=1,
                                            nProfileBlocks=250)

opObj11 = readUnitConfObj.addOperation(name='printInfo')

procUnitConfObjA = controllerObj.addProcUnit(datatype='VoltageProc', inputId=readUnitConfObj.getId())


###opObj11 = procUnitConfObjA.addOperation(name='setH0')
###opObj11.addParameter(name='h0', value='-1.5', format='float')

opObj11 = procUnitConfObjA.addOperation(name='selectHeights')
opObj11.addParameter(name='minIndex', value='1', format='int')
#opObj11.addParameter(name='maxIndex', value='1000', format='int')
#opObj11.addParameter(name='maxIndex', value=str(int(num_alturas/4.0)), format='int')
 # CUARTA PARTE de 60 Km POR ESO ENTRE 4  - 15 Km
opObj11.addParameter(name='maxIndex', value=str(int(num_alturas/10.0)), format='int')
 # CUARTA PARTE de 60 Km POR ESO ENTRE 10  - 6 Km


if mode_proc ==0:
    ####################### METODO PULSE PAIR ######################################################################
    opObj11 = procUnitConfObjA.addOperation(name='PulsePair', optype='other')
    opObj11.addParameter(name='n', value=int(n), format='int')#10 VOY A USAR 250 DADO  QUE LA VELOCIDAD ES 10 GRADOS
    #opObj11.addParameter(name='removeDC', value=1, format='int')
    ####################### METODO Parametros ######################################################################
    procUnitConfObjB= controllerObj.addProcUnit(datatype='ParametersProc',inputId=procUnitConfObjA.getId())
    if plot==1:
        opObj11 = procUnitConfObjB.addOperation(name='GenericRTIPlot',optype='external')
        opObj11.addParameter(name='attr_data', value='dataPP_POWER')
        opObj11.addParameter(name='colormap', value='jet')
        opObj11.addParameter(name='xmin', value=xmin)
        opObj11.addParameter(name='xmax', value=xmax)
        #opObj11.addParameter(name='ymin', value=ymin)
        #opObj11.addParameter(name='ymax', value=ymax)
        opObj11.addParameter(name='zmin', value=dBmin)
        opObj11.addParameter(name='zmax', value=dBmax)
        opObj11.addParameter(name='save', value=figpath_pp)
        opObj11.addParameter(name='showprofile', value=0)
        opObj11.addParameter(name='save_period', value=10)
    ####################### METODO ESCRITURA #######################################################################
    if save==1:
        opObj10 = procUnitConfObjB.addOperation(name='HDFWriter')
        opObj10.addParameter(name='path',value=path_save)
        #opObj10.addParameter(name='mode',value=0)
        opObj10.addParameter(name='blocksPerFile',value='100',format='int')
        opObj10.addParameter(name='metadataList',value='utctimeInit,timeZone,paramInterval,profileIndex,channelList,heightList,flagDataAsBlock',format='list')
        opObj10.addParhirameter(name='dataList',value='dataPP_POWER,dataPP_DOP,utctime',format='list')#,format='list'
    if integration==1:
        opObj11 = procUnitConfObjB.addOperation(name='PedestalInformation')
        opObj11.addParameter(name='path_ped', value=path_ped)
        opObj11.addParameter(name='t_Interval_p', value='0.01', format='float')
        opObj11.addParameter(name='wr_exp', value='PPI')
    if plot_ppi==1:
        opObj11 = procUnitConfObjB.addOperation(name='Block360')
        opObj11.addParameter(name='n', value='10', format='int')
        opObj11.addParameter(name='mode', value=mode_proc, format='int')
        # este bloque funciona bien con divisores de 360 no olvidar 0 10 20 30 40 60 90 120 180
        opObj11= procUnitConfObjB.addOperation(name='WeatherPlot',optype='other')
        opObj11.addParameter(name='save', value=figpath_pp_ppi)
        opObj11.addParameter(name='save_period', value=1)

controllerObj.start()
