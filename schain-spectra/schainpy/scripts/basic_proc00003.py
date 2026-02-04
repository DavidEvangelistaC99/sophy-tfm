# Ing. AVP
# 04/01/2022
# ARCHIVO DE LECTURA
import os, sys
import datetime
import time
import numpy
import json
from  ext_met import  getfirstFilefromPath,getDatavaluefromDirFilename
from schainpy.controller import Project
#-----------------------------------------------------------------------------------------
# path_ped  = "/DATA_RM/TEST_PEDESTAL/P20211110-171003"
## print("PATH PEDESTAL :",path_ped)

print("[SETUP]-RADAR METEOROLOGICO-")
path_ped  = "/DATA_RM/TEST_PEDESTAL/P20211111-173856"
print("PATH PEDESTAL :",path_ped)
path_adq  = "/DATA_RM/11"
path_adq  = "/DATA_RM/10MHZDRONE/"
print("PATH DATA     :",path_adq)


figpath_pp_rti  = "/home/soporte/Pictures/TEST_PP_RTI"
print("PATH PP RTI   :",figpath_pp_rti)
figpath_pp_ppi  = "/home/soporte/Pictures/TEST_PP_PPI"
print("PATH PP PPI   :",figpath_pp_ppi)
path_pp_save_int  = "/DATA_RM/TEST_NEW_FORMAT"
print("PATH SAVE PP INT   :",path_pp_save_int)
print(" ")
#-------------------------------------------------------------------------------------------
print("SELECCIONAR MODO: PPI        (0) O RHI       (1)")
mode_wr     = 0
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
    V            = round(ele_vel[0])
    ele_vel      = getDatavaluefromDirFilename(path=path_ped,file=ff_pedestal,value="ele_vel")
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
#---------------------------------------------------------------------------------------
plot_rti    = 0
plot_ppi    = 1
integration = 1
save        = 0
#---------------------------RANGO DE PLOTEO----------------------------------
dBmin = '1'
dBmax = '85'
xmin = '14'
xmax = '16'
ymin = '0'
ymax = '600'
#----------------------------------------------------------------------------
time.sleep(3)
#---------------------SIGNAL CHAIN ------------------------------------
desc_wr= {
    'Data': {
        'dataPP_POW': 'Power',
        'utctime': 'Time',
        'azimuth': 'az',
        'elevation':'el'
    },
    'Metadata': {
        'heightList': 'range',
        'channelList': 'Channels'
    }
}


desc = "USRP_WEATHER_RADAR"
filename = "USRP_processing.xml"
controllerObj = Project()
controllerObj.setup(id = '191', name='Test_USRP', description=desc)
#---------------------UNIDAD DE LECTURA--------------------------------
readUnitConfObj = controllerObj.addReadUnit(datatype='DigitalRFReader',
                                            path=path_adq,
                                            startDate="2022/02/19",#today,
                                            endDate="2022/02/18",#today,
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
    # REVISAR EL test_sim00013.py
    if plot_rti==1:
        opObj11 = procUnitConfObjB.addOperation(name='GenericRTIPlot',optype='external')
        opObj11.addParameter(name='attr_data', value='dataPP_POW')
        opObj11.addParameter(name='colormap', value='jet')
        opObj11.addParameter(name='xmin', value=xmin)
        opObj11.addParameter(name='xmax', value=xmax)
        opObj11.addParameter(name='zmin', value=dBmin)
        opObj11.addParameter(name='zmax', value=dBmax)
        opObj11.addParameter(name='save', value=figpath_pp_rti)
        opObj11.addParameter(name='showprofile', value=0)
        opObj11.addParameter(name='save_period', value=50)
    if integration==1:
        opObj11 = procUnitConfObjB.addOperation(name='PedestalInformation')
        opObj11.addParameter(name='path_ped', value=path_ped)
        opObj11.addParameter(name='t_Interval_p', value='0.01', format='float')
        opObj11.addParameter(name='wr_exp', value='PPI')
        #------------------------------------------------------------------------------
        '''
        opObj11.addParameter(name='Datatype', value='RadialSet')
        opObj11.addParameter(name='Scantype', value='PPI')
        opObj11.addParameter(name='Latitude', value='-11.96')
        opObj11.addParameter(name='Longitud', value='-76.54')
        opObj11.addParameter(name='Heading', value='293')
        opObj11.addParameter(name='Height', value='293')
        opObj11.addParameter(name='Waveform', value='OFM')
        opObj11.addParameter(name='PRF', value='2000')
        opObj11.addParameter(name='CreatedBy', value='WeatherRadarJROTeam')
        opObj11.addParameter(name='ContactInformation', value='avaldez@igp.gob.pe')
        '''
    if plot_ppi==1:
        opObj11 = procUnitConfObjB.addOperation(name='Block360')
        opObj11.addParameter(name='n', value='10', format='int')
        opObj11.addParameter(name='mode', value=mode_proc, format='int')
        # este bloque funciona bien con divisores de 360 no olvidar 0 10 20 30 40 60 90 120 180
        opObj11= procUnitConfObjB.addOperation(name='WeatherPlot',optype='other')
        opObj11.addParameter(name='save', value=figpath_pp_ppi)
        opObj11.addParameter(name='save_period', value=1)

    if save==1:
        opObj10 = procUnitConfObjB.addOperation(name='HDFWriter')
        opObj10.addParameter(name='path',value=path_pp_save_int)
        opObj10.addParameter(name='mode',value="weather")
        opObj10.addParameter(name='type_data',value='F')
        opObj10.addParameter(name='blocksPerFile',value='360',format='int')
        #opObj10.addParameter(name='metadataList',value='utctimeInit,paramInterval,channelList,heightList,flagDataAsBlock',format='list')
        opObj10.addParameter(name='metadataList',value='heightList,channelList,Typename,Datatype,Scantype,Latitude,Longitud,Heading,Height,Waveform,PRF,CreatedBy,ContactInformation',format='list')
        #--------------------
        opObj10.addParameter(name='Typename', value='Differential_Reflectivity')
        opObj10.addParameter(name='Datatype', value='RadialSet')
        opObj10.addParameter(name='Scantype', value='PPI')
        opObj10.addParameter(name='Latitude', value='-11.96')
        opObj10.addParameter(name='Longitud', value='-76.54')
        opObj10.addParameter(name='Heading', value='293')
        opObj10.addParameter(name='Height', value='293')
        opObj10.addParameter(name='Waveform', value='OFM')
        opObj10.addParameter(name='PRF', value='2000')
        opObj10.addParameter(name='CreatedBy', value='WeatherRadarJROTeam')
        opObj10.addParameter(name='ContactInformation', value='avaldez@igp.gob.pe')
        #---------------------------------------------------
        #opObj10.addParameter(name='dataList',value='dataPP_POW,dataPP_DOP,azimuth,elevation,utctime',format='list')#,format='list'
        #opObj10.addParameter(name='metadataList',value='utctimeInit,timeZone,paramInterval,profileIndex,channelList,heightList,flagDataAsBlock',format='list')

        opObj10.addParameter(name='dataList',value='dataPP_POW,azimuth,elevation,utctime',format='list')#,format='list'
        opObj10.addParameter(name='description',value=json.dumps(desc_wr))

controllerObj.start()
