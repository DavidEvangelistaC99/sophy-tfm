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
######## VELOCIDAD DEL PEDESTAL ######################
print("SETUP- RADAR METEOROLOGICO")
V       = 6
mode    = 1
#--------------------------PATH -----------------------------
# path    = '/DATA_RM/23/6v'
# path    = '/DATA_RM/TEST_INTEGRACION_2M'
# path    = '/DATA_RM/TEST_19OCTUBRE/10MHZ'
# path    = '/DATA_RM/WR_20_OCT'
#### path_ped='/DATA_RM/TEST_PEDESTAL/P20211012-082745'
####path_ped='/DATA_RM/TEST_PEDESTAL/P20211019-192244'
#path  = '/DATA_RM/WR_POT_09_1'
#path  = '/DATA_RM/WR_POT_09_2'
#path ="/DATA_RM/10"
#path ="/DATA_RM/11"
#path ="/DATA_RM/DRONE/2MHZ_6V"
path ="/DATA_RM/DRONE/2MHZ_10V_ELEVACION"
path ="/DATA_RM/DRONE/2MHZ_6V_AZIMUTH"
#-------------------------PATH-PLOTEO------------------------------------
#figpath_pp  = "/home/soporte/Pictures/TEST_PP"
#figpath_spec = "/home/soporte/Pictures/TEST_MOM_15"
#figpath_spec = "/home/soporte/Pictures/11_"
figpath_spec = "/home/soporte/Pictures/23NOV"
figpath_spec = "/home/soporte/Pictures/23NOV_TEST_AZI"
figpath_pp  = "/home/soporte/Pictures/TEST_POT"
figpath_pp  = "/home/soporte/Pictures/TEST_POT_10_"


#--------------------------OPCIONES-----------------------------------
plot        = 0
integration = 0
save        = 0
plot_spec   = 1
#-------------------------------------------------------------------------
if save == 1:
    if mode==0:
        path_save = '/DATA_RM/TEST_HDF5_PP_23/6v'
        path_save = '/DATA_RM/TEST_HDF5_PP'
        path_save = '/DATA_RM/TEST_HDF5_PP_100'
    else:
        path_save = '/DATA_RM/TEST_HDF5_SPEC_23_V2/6v'

print("* PATH data ADQ        :", path)
print("* Velocidad Pedestal   :",V,"°/seg")
############################ NRO Perfiles PROCESAMIENTO ###################
V=V
IPP=400*1e-6
n= int(1/(V*IPP))
print("* n - NRO Perfiles Proc:", n )
################################## MODE ###################################
print("* Modo de Operacion    :",mode)
if mode ==0:
    print("* Met. Seleccionado    : Pulse Pair")
else:
    print("* Met. Momentos        : Momentos")

################################## MODE ###################################
print("* Grabado de datos     :",save)
if save ==1:
    if mode==0:
        ope= "Pulse Pair"
    else:
        ope= "Momentos"
    print("* Path-Save Data -", ope , path_save)

print("* Integracion de datos :",integration)

time.sleep(3)
#remotefolder = "/home/wmaster/graficos"
#######################################################################
################# RANGO DE PLOTEO######################################
dBmin = '8'
dBmax = '35'
xmin = '12.1'#17.1,17.5
xmax = '12.2'#17.2,17.8
ymin = '0'#### PONER A 0
ymax = '8'#### PONER A 8
#######################################################################
########################FECHA##########################################
str = datetime.date.today()
today = str.strftime("%Y/%m/%d")
str2 = str - datetime.timedelta(days=1)
yesterday = str2.strftime("%Y/%m/%d")
#######################################################################
########################SIGNAL CHAIN ##################################
#######################################################################
desc = "USRP_test"
filename = "USRP_processing.xml"
controllerObj = Project()
controllerObj.setup(id = '191', name='Test_USRP', description=desc)
#######################################################################
######################## UNIDAD DE LECTURA#############################
#######################################################################
readUnitConfObj = controllerObj.addReadUnit(datatype='DigitalRFReader',
                                            path=path,
                                            startDate="2021/11/23",#today,
                                            endDate="2021/12/23",#today,
                                            startTime='15:00:00',#'17:39:25',
                                            endTime='16:00:59',#23:59:59',
                                            delay=0,
                                            #set=0,
                                            online=1,
                                            walk=1,
                                            ippKm = 60)

opObj11 = readUnitConfObj.addOperation(name='printInfo')

procUnitConfObjA = controllerObj.addProcUnit(datatype='VoltageProc', inputId=readUnitConfObj.getId())

opObj11 = procUnitConfObjA.addOperation(name='setH0')
opObj11.addParameter(name='h0', value='-3.3', format='float')
#-2.8 5MHZ
#-3.3 2MHZ

###opObj11 = procUnitConfObjA.addOperation(name='selectChannels')
###opObj11.addParameter(name='channelList', value='[1]',format='intList')


opObj11 = procUnitConfObjA.addOperation(name='selectHeights')
opObj11.addParameter(name='minIndex', value='1', format='int')
###opObj11.addParameter(name='maxIndex', value='10000', format='int')
opObj11.addParameter(name='maxIndex', value='160', format='int')
## 400 PARA 5MHZ 12KM 2000
## 160 ṔARA 2MHZ 12KM 800

if mode ==0:
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
        opObj10.addParameter(name='dataList',value='dataPP_POWER,dataPP_DOP,utctime',format='list')#,format='list'
    if integration==1:
        V=10
        blocksPerfile=360
        print("* Velocidad del Pedestal:",V)
        tmp_blocksPerfile = 100
        f_a_p= int(tmp_blocksPerfile/V)

        opObj11 = procUnitConfObjB.addOperation(name='PedestalInformation')
        opObj11.addParameter(name='path_ped', value=path_ped)
        #opObj11.addParameter(name='path_adq', value=path_adq)
        opObj11.addParameter(name='t_Interval_p', value='0.01', format='float')
        opObj11.addParameter(name='blocksPerfile', value=blocksPerfile, format='int')
        opObj11.addParameter(name='n_Muestras_p', value='100', format='float')
        opObj11.addParameter(name='f_a_p', value=f_a_p, format='int')
        opObj11.addParameter(name='online', value='0', format='int')

        opObj11 = procUnitConfObjB.addOperation(name='Block360')
        opObj11.addParameter(name='n', value='10', format='int')
        opObj11.addParameter(name='mode', value=mode, format='int')

        # este bloque funciona bien con divisores de 360 no olvidar 0 10 20 30 40 60 90 120 180

        opObj11= procUnitConfObjB.addOperation(name='WeatherPlot',optype='other')


else:
    ####################### METODO SPECTROS ######################################################################
    procUnitConfObjB = controllerObj.addProcUnit(datatype='SpectraProc', inputId=procUnitConfObjA.getId())
    procUnitConfObjB.addParameter(name='nFFTPoints', value=n, format='int')
    procUnitConfObjB.addParameter(name='nProfiles' , value=n, format='int')
    if plot_spec==1:
        '''
        opObj11 = procUnitConfObjB.addOperation(name='SpectraPlot', optype='external')
        #.addParameter(name='id', value='2', format='int')
        opObj11.addParameter(name='wintitle', value='SpectraPlot', format='str')
        opObj11.addParameter(name='channelList', value='1', format='intlist')
        #opObj11.addParameter(name='xmin', value=xmin)
        #opObj11.addParameter(name='xmax', value=xmax)
        opObj11.addParameter(name='ymin', value=ymin)
        opObj11.addParameter(name='ymax', value=ymax)
        opObj11.addParameter(name='zmin', value=dBmin, format='int')
        opObj11.addParameter(name='zmax', value=dBmax, format='int')
        opObj11.addParameter(name='save', value=figpath_spec)
        opObj11.addParameter(name='showprofile', value=0)
        opObj11.addParameter(name='save_period', value=1)
        '''
        opObj11 = procUnitConfObjB.addOperation(name='RTIPlot', optype='external')
        #.addParameter(name='id', value='2', format='int')
        opObj11.addParameter(name='wintitle', value='RTIPlot', format='str')
        opObj11.addParameter(name='channelList', value='1', format='intlist')
        opObj11.addParameter(name='xmin', value=xmin)
        opObj11.addParameter(name='xmax', value=xmax)
        opObj11.addParameter(name='ymin', value=ymin)
        opObj11.addParameter(name='ymax', value=ymax)
        opObj11.addParameter(name='zmin', value=dBmin, format='int')
        opObj11.addParameter(name='zmax', value=dBmax, format='int')
        opObj11.addParameter(name='save', value=figpath_spec)
        opObj11.addParameter(name='showprofile', value=0)
        opObj11.addParameter(name='save_period', value=1)

    procUnitConfObjC = controllerObj.addProcUnit(datatype='ParametersProc',inputId=procUnitConfObjB.getId())
    procUnitConfObjC.addOperation(name='SpectralMoments')
    if plot==1:
        opObj11 = procUnitConfObjC.addOperation(name='PowerPlot',optype='external')
        opObj11.addParameter(name='xmin', value=xmin)
        opObj11.addParameter(name='xmax', value=xmax)
        opObj11.addParameter(name='ymin', value=ymin)
        opObj11.addParameter(name='ymax', value=ymax)
        opObj11.addParameter(name='zmin', value=dBmin)
        opObj11.addParameter(name='zmax', value=dBmax)
        opObj11.addParameter(name='save', value=figpath_spec)
        opObj11.addParameter(name='showprofile', value=0)
        opObj11.addParameter(name='save_period', value=1)

    if save==1:
        opObj10 = procUnitConfObjC.addOperation(name='HDFWriter')
        opObj10.addParameter(name='path',value=path_save)
        #opObj10.addParameter(name='mode',value=0)
        opObj10.addParameter(name='blocksPerFile',value='360',format='int')
        #opObj10.addParameter(name='metadataList',value='utctimeInit,heightList,nIncohInt,nCohInt,nProfiles,channelList',format='list')#profileIndex
        opObj10.addParameter(name='metadataList',value='utctimeInit,heightList,nIncohInt,nCohInt,nProfiles,channelList',format='list')#profileIndex
        opObj10.addParameter(name='dataList',value='data_pow,data_dop,utctime',format='list')#,format='list'

    if integration==1:
       V=10
       blocksPerfile=360
       print("* Velocidad del Pedestal:",V)
       tmp_blocksPerfile = 100
       f_a_p= int(tmp_blocksPerfile/V)

       opObj11 = procUnitConfObjC.addOperation(name='PedestalInformation')
       opObj11.addParameter(name='path_ped', value=path_ped)
       #opObj11.addParameter(name='path_adq', value=path_adq)
       opObj11.addParameter(name='t_Interval_p', value='0.01', format='float')
       opObj11.addParameter(name='blocksPerfile', value=blocksPerfile, format='int')
       opObj11.addParameter(name='n_Muestras_p', value='100', format='float')
       opObj11.addParameter(name='f_a_p', value=f_a_p, format='int')
       opObj11.addParameter(name='online', value='0', format='int')

       opObj11 = procUnitConfObjC.addOperation(name='Block360')
       opObj11.addParameter(name='n', value='10', format='int')
       opObj11.addParameter(name='mode', value=mode, format='int')

       # este bloque funciona bien con divisores de 360 no olvidar 0 10 20 30 40 60 90 120 180
       opObj11= procUnitConfObjC.addOperation(name='WeatherPlot',optype='other')
controllerObj.start()
