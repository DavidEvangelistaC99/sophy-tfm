
import os, sys

#from controller import *
from schainpy.controller import Project

desc = "EW DRIFTS Experiment"
filename = "EWDrifts.xml"

controllerObj = Project()

controllerObj.setup(id = '191', name='test01', description=desc)

#Experimentos

path = "/home/soporte/minotauro/2023_06/Drifts_Faraday/main_radar/rawdata/"
#path = '/home/pcondor/Database/temp'
pathFigure = '/home/soporte/Documents/Database/ewdriftsschain2023'
pathFile   = '/home/soporte/Documents/Database/ewdriftsschain2023'

xmin = 0
xmax = 24
#------------------------------------------------------------------------------------------------
readUnitConfObj = controllerObj.addReadUnit(datatype='VoltageReader',
                                            path=path,
                                            startDate='2023/06/23',
                                            endDate='2023/06/23',
                                            startTime='00:00:00',
                                            endTime='23:59:59',
                                            online=0,
                                            walk=1)

#--------------------------------------------------------------------------------------------------

procUnitConfObj0 = controllerObj.addProcUnit(datatype='VoltageProc', inputId=readUnitConfObj.getId())

opObj11 = procUnitConfObj0.addOperation(name='selectChannels')
opObj11.addParameter(name='channelList', value='2,3,4,5', format='intlist')

opObj11 = procUnitConfObj0.addOperation(name='ProfileSelector', optype='other')
opObj11.addParameter(name='profileRangeList', value='172,299', format='intlist')
 
opObj11 = procUnitConfObj0.addOperation(name='filterByHeights')
opObj11.addParameter(name='window', value='3', format='int')

code = [[1, 1, -1], [-1, -1, 1], [1, 1, -1], [1, 1, -1], [1, 1, -1], [-1, -1, 1], [1, 1, -1], [1, 1, -1], [1, 1, -1], [1, 1, -1], [-1, -1, 1], [1, 1, -1], [1, 1, -1], [1, 1, -1], [-1, -1, 1], [-1, -1, 1], [1, 1, -1], [-1, -1, 1], [1, 1, -1], [-1, -1, 1], [1, 1, -1], [1, 1, -1], [-1, -1, 1], [1, 1, -1], [-1, -1, 1], [-1, -1, 1], [1, 1, -1], [1, 1, -1], [1, 1, -1], [1, 1, -1], [1, 1, -1], [1, 1, -1], [-1, -1, 1], [1, 1, -1], [-1, -1, 1], [-1, -1, 1], [1, 1, -1], [-1, -1, 1], [1, 1, -1], [1, 1, -1], [1, 1, -1], [1, 1, -1], [-1, -1, 1], [1, 1, -1], [-1, -1, 1], [-1, -1, 1], [-1, -1, 1], [-1, -1, 1], [1, 1, -1], [1, 1, -1], [1, 1, -1], [-1, -1, 1], [1, 1, -1], [-1, -1, 1], [-1, -1, 1], [-1, -1, 1], [1, 1, -1], [1, 1, -1], [-1, -1, 1], [1, 1, -1], [-1, -1, 1], [1, 1, -1], [1, 1, -1], [1, 1, -1], [1, 1, -1], [1, 1, -1], [1, 1, -1], [-1, -1, 1], [1, 1, -1], [-1, -1, 1], [1, 1, -1], [-1, -1, 1], [-1, -1, 1], [-1, -1, 1], [-1, -1, 1], [1, 1, -1], [-1, -1, 1], [-1, -1, 1], [1, 1, -1], [-1, -1, 1], [1, 1, -1], [1, 1, -1], [1, 1, -1], [-1, -1, 1], [1, 1, -1], [1, 1, -1], [-1, -1, 1], [-1, -1, 1], [1, 1, -1], [-1, -1, 1], [-1, -1, 1], [-1, -1, 1], [-1, -1, 1], [-1, -1, 1], [1, 1, -1], [-1, -1, 1], [1, 1, -1], [1, 1, -1], [1, 1, -1], [1, 1, -1], [-1, -1, 1], [-1, -1, 1], [1, 1, -1], [1, 1, -1], [-1, -1, 1], [-1, -1, 1], [-1, -1, 1], [-1, -1, 1], [-1, -1, 1], [-1, -1, 1], [1, 1, -1], [1, 1, -1], [1, 1, -1], [1, 1, -1], [1, 1, -1], [-1, -1, 1], [-1, -1, 1], [1, 1, -1], [-1, -1, 1], [-1, -1, 1], [-1, -1, 1], [1, 1, -1], [-1, -1, 1], [1, 1, -1], [-1, -1, 1], [-1, -1, 1], [-1, -1, 1], [1, 1, -1]]
opObj11 = procUnitConfObj0.addOperation(name='Decoder', optype='other')
opObj11.addParameter(name='code', value=code, format='floatlist')
opObj11.addParameter(name='nCode', value='128', format='int')
opObj11.addParameter(name='nBaud', value='3', format='int')

opObj11 = procUnitConfObj0.addOperation(name='selectHeights')
opObj11.addParameter(name='minHei', value='0.0', format='float')
opObj11.addParameter(name='maxHei', value='960', format='float')

procUnitConfObj1 = controllerObj.addProcUnit(datatype='SpectraProc', inputId=procUnitConfObj0.getId())
procUnitConfObj1.addParameter(name='nFFTPoints', value='128', format='int')
procUnitConfObj1.addParameter(name='nProfiles', value='128', format='int')
#procUnitConfObj1.addParameter(name='pairsList', value='(2,3),(4,5)', format='pairsList')#,(2,3)
procUnitConfObj1.addParameter(name='pairsList', value='(0,1),(2,3)', format='pairsList')
  
opObj11 = procUnitConfObj1.addOperation(name='IncohInt', optype='other')
opObj11.addParameter(name='n', value='1', format='float')
#opObj11.addParameter(name='timeInterval', value='300.0', format='float')

#opObj13 = procUnitConfObj1.addOperation(name='removeDC')

#opObj14 = procUnitConfObj1.addOperation(name='SpectraPlot', optype='other')
#opObj14.addParameter(name='id', value='65', format='int')
## # opObj14.addParameter(name='wintitle', value='Con interf', format='str')
#opObj14.addParameter(name='save', value=pathFigure, format='str')
##opObj14.addParameter(name='save_period', value=1, format='int')
#opObj14.addParameter(name='zmin', value='20', format='int')
#opObj14.addParameter(name='zmax', value='36', format='int')
# 

#opObj12 = procUnitConfObj1.addOperation(name='RTIPlot', optype='other')
#opObj12.addParameter(name='id', value='63', format='int')
#opObj12.addParameter(name='wintitle', value='RTI Plot', format='str')
#opObj12.addParameter(name='save', value=pathFigure, format='str')
#opObj12.addParameter(name='save_period', value=10, format='int')
##opObj12.addParameter(name='figpath', value = pathFigure, format='str')
#opObj12.addParameter(name='xmin', value=xmin, format='float')
#opObj12.addParameter(name='xmax', value=xmax, format='float')
#opObj12.addParameter(name='zmin', value='20', format='int')
#opObj12.addParameter(name='zmax', value='36', format='int')

#--------------------------------------------------------------------------------------------------

procUnitConfObj2 = controllerObj.addProcUnit(datatype='ParametersProc', inputId=procUnitConfObj1.getId())
opObj20 = procUnitConfObj2.addOperation(name='SpectralFitting', optype='other')
opObj20.addParameter(name='path', value='/home/soporte/UPDATE_SCHAIN/schain/schainpy/model/proc', format='str')
opObj20.addParameter(name='file', value='modelSpectralFitting', format='str')
opObj20.addParameter(name='groupList', value='(0,1),(2,3)',format='multiList')
#opObj20.addParameter(name='filec', value='weightfit', format='str')

#opObj12 = procUnitConfObj2.addOperation(name='HDF5Writer', optype='other')
#opObj12.addParameter(name='path', value=pathFile)
#opObj12.addParameter(name='blocksPerFile', value='3', format='int')

opObj21 = procUnitConfObj2.addOperation(name='EWDriftsEstimation', optype='other')
opObj21.addParameter(name='zenith', value='-1.64908,  3.36063', format='floatlist')
opObj21.addParameter(name='zenithCorrection', value='0.0', format='float')
opObj21.addParameter(name='fileDrifts', value=pathFile)

opObj24 = procUnitConfObj2.addOperation(name='SpectralMomentsPlot', optype='other')
opObj24.addParameter(name='id', value='1', format='int')
## # opObj14.addParameter(name='wintitle', value='Con interf', format='str')
opObj24.addParameter(name='save', value=pathFigure, format='str')
##opObj24.addParameter(name='save_period', value=1, format='int')
opObj24.addParameter(name='zmin', value='4', format='int')
opObj24.addParameter(name='zmax', value='20', format='int')
opObj24.addParameter(name='xaxis', value='Velocity', format='str')
# 
titles=('SNR,Vertical Drifts,Zonal Drifts')
#titles=('Zonal Drifts,Vertical Drifts')
opObj23 = procUnitConfObj2.addOperation(name='GenericRTIPlot')
opObj23.addParameter(name='colormaps', value='jet,RdBu_r,RdBu_r')
opObj23.addParameter(name='attr_data', value='data_snr1,data_output')
#opObj23.addParameter(name='colormaps', value='RdBu,RdBu')
#opObj23.addParameter(name='attr_data', value='data_output')
opObj23.addParameter(name='wintitle', value='EW Drifts')
opObj23.addParameter(name='save', value=pathFigure)
opObj23.addParameter(name='titles', value=titles)
opObj23.addParameter(name='zfactors', value='1,1,1')
opObj23.addParameter(name='zlimits', value='(20,36),(-50,50),(-150,150)')
opObj23.addParameter(name='cb_labels', value='dB,m/s,m/s')
#opObj23.addParameter(name='titles', value=titles)
#opObj23.addParameter(name='zfactors', value='1,1')
#opObj23.addParameter(name='zlimits', value='(-150,150),(-40,40)')
#opObj23.addParameter(name='cb_labels', value='m/s,m/s')
opObj23.addParameter(name='throttle', value='1')
opObj23.addParameter(name='xmin', value=xmin)
opObj23.addParameter(name='xmax', value=xmax)
#--------------------------------------------------------------------------------------------------

controllerObj.start()
