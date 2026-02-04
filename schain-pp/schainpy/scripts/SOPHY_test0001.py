# Ing. AVP
# 01/11/2021
# ARCHIVO DE LECTURA
import os, sys
import datetime
import time
from schainpy.controller import Project
print("----[Setup]-RadarMeteorologico--------")
Vel       =  10
modo_proc =  0 # 0 Pulse Pair 1 Spectros
#-----------PATH DE DATOS-----------------------#
#------------VERIFICAR SIEMPRE LA FECHA DE LA DATA
path      =  "/DATA_RM/10"
path_ped  =  "/DATA_RM/TEST_PEDESTAL/P20211110-171003"
figpath_pp  = "/home/soporte/Pictures/TEST_POT"
figpath_ppi_pp  = "/home/soporte/Pictures/ppi_PP_30DIC_4"
#-------------------------------------------------------------------
print("----[OPCIONES]------------------------")
op_plot        = 0
op_integration = 1
op_save        = 1
op_plot_spec   = 0
#-------------------------------------
################# RANGO DE PLOTEO######################################
dBmin = '1'
dBmax = '85'
xmin = '17.1'
xmax = '17.25'
ymin = '0'
ymax = '600'
#-------------------NRO Perfiles PROCESAMIENTO --------------------
V=Vel
IPP=400*1e-6
n= int(1/(V*IPP))
print("* n - NRO Perfiles Proc:", n )
time.sleep(3)

#------------------------SIGNAL CHAIN ------------------------------
desc          = "USRP_test"
filename      = "USRP_processing.xml"
controllerObj = Project()
controllerObj.setup(id = '191', name='Test_USRP', description=desc)
######################## UNIDAD DE LECTURA#############################
readUnitConfObj = controllerObj.addReadUnit(datatype = 'DigitalRFReader',
                                            path     = path,
                                            startDate= "2021/11/10",#today,
                                            endDate  = "2021/12/30",#today,
                                            startTime= '00:00:25',
                                            endTime  = '23:59:59',
                                            delay    = 0,
                                            online   = 0,
                                            walk     = 1,
                                            ippKm    = 60)

opObj11          = readUnitConfObj.addOperation(name='printInfo')
procUnitConfObjA = controllerObj.addProcUnit(datatype='VoltageProc',inputId=readUnitConfObj.getId())

opObj11 = procUnitConfObjA.addOperation(name='selectHeights')
opObj11.addParameter(name='minIndex', value='1', format='int')
#    opObj11.addParameter(name='maxIndex', value='10000', format='int')
opObj11.addParameter(name='maxIndex', value='400', format='int')

if modo_proc ==0:
    #----------------------------------------PULSE PAIR --------------------------------------------------#
    opObj11 = procUnitConfObjA.addOperation(name='PulsePair', optype='other')
    opObj11.addParameter(name='n', value=int(n), format='int')#10 VOY A USAR 250 DADO  QUE LA VELOCIDAD ES 10 GRADOS
    #opObj11.addParameter(name='removeDC', value=1, format='int')
    #------------------------ METODO Parametros -----------------------------------------------------------
    procUnitConfObjB= controllerObj.addProcUnit(datatype='ParametersProc',inputId=procUnitConfObjA.getId())
    if op_plot==1:
        opObj11 = procUnitConfObjB.addOperation(name='GenericRTIPlot',optype='external')
        opObj11.addParameter(name='attr_data', value='dataPP_POW')
        opObj11.addParameter(name='colormap', value='jet')
        #opObj11.addParameter(name='xmin', value=xmin)
        #opObj11.addParameter(name='xmax', value=xmax)
        opObj11.addParameter(name='zmin', value=dBmin)
        opObj11.addParameter(name='zmax', value=dBmax)
        opObj11.addParameter(name='save', value=figpath_pp)
        opObj11.addParameter(name='showprofile', value=0)
        opObj11.addParameter(name='save_period', value=50)

    ####################### METODO ESCRITURA #######################################################################

    if op_integration==1:
        V=V
        blocksPerfile=100
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
        opObj11.addParameter(name='mode', value=modo_proc, format='int')

        # este bloque funciona bien con divisores de 360 no olvidar 0 10 20 30 40 60 90 120 180

        opObj11= procUnitConfObjB.addOperation(name='WeatherPlot',optype='other')
        opObj11.addParameter(name='save', value=figpath_ppi_pp)
        opObj11.addParameter(name='save_period', value=1)

    if op_save==1:
        opObj10 = procUnitConfObjB.addOperation(name='HDFWriter')
        opObj10.addParameter(name='path',value=figpath_ppi_pp)
        #opObj10.addParameter(name='mode',value=0)
        opObj10.addParameter(name='blocksPerFile',value='100',format='int')
        opObj10.addParameter(name='metadataList',value='utctimeInit,timeZone,paramInterval,profileIndex,channelList,heightList,flagDataAsBlock',format='list')
        opObj10.addParameter(name='dataList',value='dataPP_POW,dataPP_DOP,azimuth,utctime',format='list')#,format='list'

controllerObj.start()
