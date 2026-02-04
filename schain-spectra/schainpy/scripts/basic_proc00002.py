# Ing. AVP
# 06/10/2021
# ARCHIVO DE LECTURA
import os, sys
import datetime
import time
from schainpy.controller import Project
import h5py



def isNumber(str):
    try:
        float(str)
        return True
    except:
        return False

def getfirstFilefromPath(path,meta,ext):
    validFilelist = []
    #print("SEARH",path)
    try:
        fileList      = os.listdir(path)
    except:
        print("check path - fileList")
    if len(fileList)<1:
     return None
    # meta    1234 567 8-18 BCDE
    # H,D,PE  YYYY DDD EPOC .ext

    for thisFile in fileList:
        #print("HI",thisFile)
        if meta =="PE":
            try:
                number= int(thisFile[len(meta)+7:len(meta)+17])
            except:
                 print("There is a file or folder with different format")
        if meta == "D":
            try:
                number= int(thisFile[8:11])
            except:
                print("There is a file or folder with different format")

        if not isNumber(str=number):
            continue
        if (os.path.splitext(thisFile)[-1].lower() != ext.lower()):
            continue
        validFilelist.sort()
        validFilelist.append(thisFile)
    if len(validFilelist)>0:
        validFilelist = sorted(validFilelist,key=str.lower)
        return validFilelist
    return None
def gettimeutcfromDirFilename(path,file):
    dir_file= path+"/"+file
    fp      = h5py.File(dir_file,'r')
    #epoc    = fp['Metadata'].get('utctimeInit')[()]
    epoc    = fp['Data'].get('utc')[()]
    fp.close()
    return epoc

path_ped='/DATA_RM/TEST_PEDESTAL/P20211111-173856'

list_pedestal=getfirstFilefromPath(path=path_ped,meta="PE",ext=".hdf5")


timestamp= gettimeutcfromDirFilename(path=path_ped,file=list_pedestal[0])
print("timestamp",timestamp)
#timestamp = 1339521878.04
value = datetime.datetime.fromtimestamp(timestamp)
print(value.strftime('%Y/%m/%d %H:%M:%S'))
startdate= value.strftime('%Y/%m/%d')
starttime= value.strftime('%H:%M:%S')
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
#V       = 10
mode    = 0
#--------------------------PATH -----------------------------
# path    = '/DATA_RM/23/6v'
# path    = '/DATA_RM/TEST_INTEGRACION_2M'
# path    = '/DATA_RM/TEST_19OCTUBRE/10MHZ'
# path    = '/DATA_RM/WR_20_OCT'
#### path_ped='/DATA_RM/TEST_PEDESTAL/P20211012-082745'
####path_ped='/DATA_RM/TEST_PEDESTAL/P20211019-192244'
#path ="/DATA_RM/10"
# path  = '/DATA_RM/WR_POT_09_1'
#path ="/DATA_RM/11"
path ="/DATA_RM/11"
#-------------------------PATH-PLOTEO------------------------------------
#figpath_pp  = "/home/soporte/Pictures/TEST_PP"
#figpath_spec = "/home/soporte/Pictures/TEST_MOM"
figpath_spec = "/home/soporte/Pictures/ppi"
figpath_ppi  = "/home/soporte/Pictures/ppi_SPEC_10DIC"
figpath_ppi_pp  = "/home/soporte/Pictures/ppi_PP_10_DIC"
figpath_pp  = "/home/soporte/Pictures/TEST_POT"
figpath_pp  = "/home/soporte/Pictures/TEST_POT2"

#path_ped='/DATA_RM/TEST_PEDESTAL/P20211012-082745'
#path_ped='/DATA_RM/TEST_PEDESTAL/P20211020-131248'
#path_ped='/DATA_RM/TEST_PEDESTAL/P20211110-171003'
path_ped=path_ped
#path_ped  =  "/DATA_RM/TEST_PEDESTAL/P20211110-171003"


figpath_pp  = "/home/soporte/Pictures/25TEST_PP"
figpath_mom = "/home/soporte/Pictures/TEST_MOM"
#--------------------------OPCIONES-----------------------------------
plot        = 0
integration = 1
save        = 0
if save == 1:
    if mode==0:
        path_save = '/DATA_RM/TEST_HDF5_PP_23/6v'
        path_save = '/DATA_RM/TEST_HDF5_PP'
        path_save = '/DATA_RM/TEST_HDF5_PP_100'
        path_save = '/DATA_RM/TEST_EMPTHY'
    else:
        path_save = '/DATA_RM/TEST_HDF5_SPEC_23_V2/6v'
        path_save = '/DATA_RM/TEST_EMPTHY_SPEC'
        path_save = '/DATA_RM/LAST_TEST_16_VACIO3'
        path_save = '/DATA_RM/LAST_TEST_30_360'

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
dBmin = '1'
dBmax = '85'
xmin = '17'
xmax = '17.25'
ymin = '0'
ymax = '600'
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
                                            startDate=startdate,#today,
                                            endDate="2021/12/30",#today,
                                            startTime=starttime,
                                            endTime='23:59:59',
                                            delay=0,
                                            #set=0,
                                            online=0,
                                            walk=1,
                                            ippKm = 60)

opObj11 = readUnitConfObj.addOperation(name='printInfo')

procUnitConfObjA = controllerObj.addProcUnit(datatype='VoltageProc',inputId=readUnitConfObj.getId())


#opObj11 = procUnitConfObjA.addOperation(name='setH0')
#opObj11.addParameter(name='h0', value='-2.8', format='float')

opObj11 = procUnitConfObjA.addOperation(name='selectHeights')
opObj11.addParameter(name='minIndex', value='1', format='int')
#    opObj11.addParameter(name='maxIndex', value='10000', format='int')
opObj11.addParameter(name='maxIndex', value='400', format='int')

if mode ==0:
    ####################### METODO PULSE PAIR ######################################################################
    opObj11 = procUnitConfObjA.addOperation(name='PulsePair', optype='other')
    opObj11.addParameter(name='n', value=int(n), format='int')#10 VOY A USAR 250 DADO  QUE LA VELOCIDAD ES 10 GRADOS
    #opObj11.addParameter(name='removeDC', value=1, format='int')
    ####################### METODO Parametros ######################################################################
    procUnitConfObjB= controllerObj.addProcUnit(datatype='ParametersProc',inputId=procUnitConfObjA.getId())
    if plot==1:
        opObj11 = procUnitConfObjB.addOperation(name='GenericRTIPlot',optype='external')
        opObj11.addParameter(name='attr_data', value='dataPP_POW')
        opObj11.addParameter(name='colormap', value='jet')
        opObj11.addParameter(name='xmin', value=xmin)
        opObj11.addParameter(name='xmax', value=xmax)
        opObj11.addParameter(name='zmin', value=dBmin)
        opObj11.addParameter(name='zmax', value=dBmax)
        opObj11.addParameter(name='save', value=figpath_pp)
        opObj11.addParameter(name='showprofile', value=0)
        opObj11.addParameter(name='save_period', value=50)

    ####################### METODO ESCRITURA #######################################################################

    if integration==1:
        V=V
        blocksPerfile=100
        print("* Velocidad del Pedestal:",V)
        tmp_blocksPerfile = 100
        f_a_p= int(tmp_blocksPerfile/V)

        opObj11 = procUnitConfObjB.addOperation(name='PedestalInformation')
        opObj11.addParameter(name='path_ped', value=path_ped)
        #opObj11.addParameter(name='path_adq', value=path_adq)
        opObj11.addParameter(name='t_Interval_p', value='0.01', format='float')
        opObj11.addParameter(name='wr_exp', value='PPI')
        #opObj11.addParameter(name='blocksPerfile', value=blocksPerfile, format='int')
        #opObj11.addParameter(name='n_Muestras_p', value='100', format='float')
        #opObj11.addParameter(name='f_a_p', value=f_a_p, format='int')
        #opObj11.addParameter(name='online', value='0', format='int')

        opObj11 = procUnitConfObjB.addOperation(name='Block360')
        opObj11.addParameter(name='n', value='10', format='int')
        opObj11.addParameter(name='mode', value=mode, format='int')

        # este bloque funciona bien con divisores de 360 no olvidar 0 10 20 30 40 60 90 120 180

        opObj11= procUnitConfObjB.addOperation(name='WeatherPlot',optype='other')
        opObj11.addParameter(name='save', value=figpath_ppi_pp)
        opObj11.addParameter(name='save_period', value=1)

    if save==1:
        opObj10 = procUnitConfObjB.addOperation(name='HDFWriter')
        opObj10.addParameter(name='path',value=path_save)
        #opObj10.addParameter(name='mode',value=0)
        opObj10.addParameter(name='blocksPerFile',value='100',format='int')
        opObj10.addParameter(name='metadataList',value='utctimeInit,timeZone,paramInterval,profileIndex,channelList,heightList,flagDataAsBlock',format='list')
        opObj10.addParameter(name='dataList',value='dataPP_POW,dataPP_DOP,azimuth,utctime',format='list')#,format='list'

else:
    ####################### METODO SPECTROS ######################################################################
    procUnitConfObjB = controllerObj.addProcUnit(datatype='SpectraProc', inputId=procUnitConfObjA.getId())
    procUnitConfObjB.addParameter(name='nFFTPoints', value=n, format='int')
    procUnitConfObjB.addParameter(name='nProfiles' , value=n, format='int')

    procUnitConfObjC = controllerObj.addProcUnit(datatype='ParametersProc',inputId=procUnitConfObjB.getId())
    procUnitConfObjC.addOperation(name='SpectralMoments')
    if plot==1:
        dBmin = '1'
        dBmax = '65'
        opObj11 = procUnitConfObjC.addOperation(name='PowerPlot',optype='external')
        opObj11.addParameter(name='xmin', value=xmin)
        opObj11.addParameter(name='xmax', value=xmax)
        opObj11.addParameter(name='zmin', value=dBmin)
        opObj11.addParameter(name='zmax', value=dBmax)
        opObj11.addParameter(name='save', value=figpath_mom)
        opObj11.addParameter(name='showprofile', value=0)
        opObj11.addParassmeter(name='save_period', value=100)


    if integration==1:
       V=V
       blocksPerfile=100
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
       opObj11.addParameter(name='n', value='20', format='int')
       opObj11.addParameter(name='mode', value=mode, format='int')

       # este bloque funciona bien con divisores de 360 no olvidar 0 10 20 30 40 60 90 120 180
       opObj11= procUnitConfObjC.addOperation(name='WeatherPlot',optype='other')
       opObj11.addParameter(name='save', value=figpath_ppi)
       opObj11.addParameter(name='save_period', value=1)

    if save==1:
       opObj10 = procUnitConfObjC.addOperation(name='HDFWriter')
       opObj10.addParameter(name='path',value=path_save)
       opObj10.addParameter(name='mode',value='weather')
       opObj10.addParameter(name='blocksPerFile',value='360',format='int')
       #opObj10.addParameter(name='metadataList',value='utctimeInit,heightList,nIncohInt,nCohInt,nProfiles,channelList',format='list')#profileIndex
       opObj10.addParameter(name='metadataList',value='utctimeInit,heightList,nIncohInt,nCohInt,nProfiles,channelList',format='list')#profileIndex
       #opObj10.addParameter(name='dataList',value='data_pow,data_dop,azimuth,utctime',format='list')#,format='list'
       opObj10.addParameter(name='dataList',value='data_360,data_azi,utctime',format='list')#,format='list'



       '''
       # este bloque funciona bien con divisores de 360 no olvidar 0 10 20 30 40 60 90 120 180
       opObj11= procUnitConfObjC.addOperation(name='WeatherPlot',optype='other')
       opObj11.addParameter(name='save', value=figpath_ppi)
       opObj11.addParameter(name='save_period', value=1)
       '''
controllerObj.start()
