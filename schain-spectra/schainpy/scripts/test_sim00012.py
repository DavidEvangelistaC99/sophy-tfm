import os,sys
import datetime
import time
from schainpy.controller import Project

#*************************************************************************
#**************************LECTURA config_WR.txt**************************
#*************************************************************************
from readFileconfig import ReadfileWR
filename= "/home/soporte/schainv3/schain/schainpy/scripts/config_WR.txt"
dict=  ReadfileWR(filename).getDict()

FixRCP_IPP  = dict['ipp']*0.15 #equivalencia
dataBlocksPerFile= dict['b_f_adq']
profilesPerBlock= int(dict['n'])
pulsepair  = int(dict['n'])
#*************************************************************************
path    = '/home/soporte/Downloads/RAWDATA_PP_C'
figpath = path
desc            = "Simulator Test"
controllerObj   = Project()
controllerObj.setup(id='10',name='Test Simulator',description=desc)
readUnitConfObj = controllerObj.addReadUnit(datatype='SimulatorReader',
                                            frequency=9.345e9,
                                            FixRCP_IPP= FixRCP_IPP,
                                            Tau_0 = 30,
                                            AcqH0_0=0,
                                            samples=330,
                                            AcqDH_0=0.15,
                                            FixRCP_TXA=0.15,
                                            FixRCP_TXB=0.15,
                                            Fdoppler=600.0,
                                            Hdoppler=36,
                                            Adoppler=300,#300
                                            delay=0,
                                            online=0,
                                            walk=0,
                                            profilesPerBlock=profilesPerBlock,
                                            dataBlocksPerFile=dataBlocksPerFile)#,#nTotalReadFiles=2)
#opObj11         = readUnitConfObj.addOperation(name='printInfo')
procUnitConfObjA = controllerObj.addProcUnit(datatype='VoltageProc', inputId=readUnitConfObj.getId())

opObj11 = procUnitConfObjA.addOperation(name='PulsePair')
opObj11.addParameter(name='n', value=pulsepair, format='int')#10

procUnitConfObjB= controllerObj.addProcUnit(datatype='ParametersProc',inputId=procUnitConfObjA.getId())

opObj10 = procUnitConfObjB.addOperation(name='HDFWriter')
opObj10.addParameter(name='path',value=figpath)
#opObj10.addParameter(name='mode',value=2)
opObj10.addParameter(name='blocksPerFile',value='100',format='int')
opObj10.addParameter(name='metadataList',value='utctimeInit,paramInterval,heightList,profileIndex,flagDataAsBlock',format='list')
opObj10.addParameter(name='dataList',value='dataPP_POW,dataPP_DOP,utctime',format='list')#,format='list'

controllerObj.start()
