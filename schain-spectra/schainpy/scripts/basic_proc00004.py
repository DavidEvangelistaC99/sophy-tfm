# Ing. AVP
# 04/01/2022
# ARCHIVO DE LECTURA
#---- DATA RHI --- 23 DE NOVIEMBRE DEL 2021 --- 23/11/2021---
#---- PEDESTAL ----------------------------------------------
#------- HORA 143826 /DATA_RM/TEST_PEDESTAL/P20211123-143826 14:38-15:10
#---- RADAR ----------------------------------------------
#-------  14:26-15:00
#-------  /DATA_RM/DRONE/2MHZ_5V_ELEVACION/
#-------  /DATA_RM/DRONE/2MHZ_5V_ELEVACION/ch0/2021-11-23T19-00-00

import os, sys
import datetime
import time
import numpy
from  ext_met import  getfirstFilefromPath,getDatavaluefromDirFilename
from schainpy.controller import Project
#-----------------------------------------------------------------------------------------
print("[SETUP]-RADAR METEOROLOGICO-")
path_ped  = "/DATA_RM/TEST_PEDESTAL/P20211123-143826"
path_ped  = "/DATA_RM/TEST_PEDESTAL/P20220217-172216"
print("PATH PEDESTAL :",path_ped)
path_adq  = "/DATA_RM/DRONE/2MHZ_5V_ELEVACION/"
path_adq  = "/DATA_RM/2MHZTEST/"
print("PATH DATA     :",path_adq)
figpath_pp_rti  = "/home/soporte/Pictures/TEST_PP_RHI"
print("PATH PP RTI   :",figpath_pp_rti)
figpath_pp_rhi  = "/home/soporte/Pictures/TEST_PP_RHI"
print("PATH PP RHI   :",figpath_pp_rhi)
path_pp_save_int  = "/DATA_RM/TEST_SAVE_PP_INT_RHI"
print("PATH SAVE PP INT   :",path_pp_save_int)
print(" ")
#-------------------------------------------------------------------------------------------
print("SELECCIONAR MODO: PPI        (0) O RHI       (1)")
mode_wr     = 1
if mode_wr==0:
    print("[ ON ] MODE PPI")
    list_ped     = getfirstFilefromPath(path=path_ped,meta="PE",ext=".hdf5")
    ff_pedestal  = list_ped[2]
    azi_vel      = getDatavaluefromDirFilename(path=path_ped,file=ff_pedestal,value="azi_vel")
    V            = round(azi_vel[0])
    print("VELOCIDAD AZI :", int(numpy.mean(azi_vel)),"°/seg")
else:
    print("[ ON ] MODE RHI")
    list_ped     = getfirstFilefromPath(path=path_ped,meta="PE",ext=".hdf5")
    ff_pedestal  = list_ped[2]
    ele_vel      = getDatavaluefromDirFilename(path=path_ped,file=ff_pedestal,value="ele_vel")
    V            = round(ele_vel[0])
    V            = 8.0#10.0
    print("VELOCIDAD ELE :", int(numpy.mean(ele_vel)),"°/seg")
print(" ")
#---------------------------------------------------------------------------------------
print("SELECCIONAR MODO: PULSE PAIR (0) O FREQUENCY (1)")
mode_proc   = 0
if mode_proc==0:
    print("[ ON ] MODE PULSEPAIR")
else:
    print("[ ON ] MODE FREQUENCY")
ipp  = 60.0
print("IPP(Km.)      :  %1.2f"%ipp)
ipp_sec = (ipp*1.0e3/150.0)*1.0e-6
print("IPP(useg.)    : %1.2f"%(ipp_sec*(1.0e6)))
VEL=V
n= int(1/(VEL*ipp_sec))
print("N° Profiles   : ", n)
#--------------------------------------------
plot_rti    = 0
plot_rhi    = 1
integration = 1
save        = 0
#---------------------------RANGO DE PLOTEO----------------------------------
dBmin = '1'
dBmax = '85'
xmin = '17'
xmax = '17.25'
ymin = '0'
ymax = '600'
#----------------------------------------------------------------------------
time.sleep(3)
#---------------------SIGNAL CHAIN ------------------------------------
desc = "USRP_WEATHER_RADAR"
filename = "USRP_processing.xml"
controllerObj = Project()
controllerObj.setup(id = '191', name='Test_USRP', description=desc)
#---------------------UNIDAD DE LECTURA--------------------------------
readUnitConfObj = controllerObj.addReadUnit(datatype='DigitalRFReader',
                                            path=path_adq,
                                            startDate="2022/02/17",#today,
                                            endDate="2022/02/17",#today,
                                            startTime='00:00:00',
                                            endTime='23:59:59',
                                            delay=0,
                                            #set=0,
                                            online=0,
                                            walk=1,
                                            ippKm=ipp)

procUnitConfObjA = controllerObj.addProcUnit(datatype='VoltageProc',inputId=readUnitConfObj.getId())

opObj11 = procUnitConfObjA.addOperation(name='selectHeights')
opObj11.addParameter(name='minIndex', value='1', format='int')
#    opObj11.addParameter(name='maxIndex', value='10000', format='int')
opObj11.addParameter(name='maxIndex', value='400', format='int')

if mode_proc==0:
    opObj11 = procUnitConfObjA.addOperation(name='PulsePair', optype='other')
    opObj11.addParameter(name='n', value=int(n), format='int')
    procUnitConfObjB= controllerObj.addProcUnit(datatype='ParametersProc',inputId=procUnitConfObjA.getId())

    if integration==1:
        opObj11 = procUnitConfObjB.addOperation(name='PedestalInformation')
        opObj11.addParameter(name='path_ped', value=path_ped)
        opObj11.addParameter(name='t_Interval_p', value='0.01', format='float')
        opObj11.addParameter(name='wr_exp', value='RHI')

    if plot_rhi==1:
        opObj11 = procUnitConfObjB.addOperation(name='Block360')
        opObj11.addParameter(name='n', value='10', format='int')
        opObj11.addParameter(name='mode', value=mode_proc, format='int')
        # este bloque funciona bien con divisores de 360 no olvidar 0 10 20 30 40 60 90 120 180
        opObj11= procUnitConfObjB.addOperation(name='WeatherRHIPlot',optype='other')
        opObj11.addParameter(name='save', value=figpath_pp_rhi)
        opObj11.addParameter(name='save_period', value=1)

controllerObj.start()
