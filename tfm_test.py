###---Spectra Test TFM tecnique by profiles---###

import modFreq as modf

import os, sys
import datetime
import time
from schainpy.controller import Project
import numpy as np
import matplotlib.pyplot as plt

desc = "USRP_test"
filename = "USRP_processing.xml"

path = '/home/david/Documents/DATA_2/CHIRP_TFM@2026-01-27T20-36-02/rawdata/'
figpath = '/home/david/Documents/DATA_2/CHIRP_TFM@2026-01-27T20-36-02/rawdata'

## REVISION ##
## 1 ##
controllerObj = Project()
controllerObj.setup(id = '192', name='Test_USRP', description="Spectra test TFM tecnique")

#######################################################################
########################### PLOTTING RANGE ############################
#######################################################################

# Graphics parameters
## 2 ##
dBmin = 0
dBmax = 120
xmin = '0'
xmax = '24'
ymin = '0'
ymax = '60'

#######################################################################
############################ READING UNIT #############################
#######################################################################

readUnitConfObj = controllerObj.addReadUnit(datatype='DigitalRFReader',
                                            path=path,
                                            startDate="2026/01/01",
                                            endDate="2026/12/30",
                                            startTime='00:00:00',
                                            endTime='23:59:59',
                                            delay=0,
                                            # set=0,
                                            # online=0,
                                            # walk=1,
                                            getByBlock = 1,
                                            nProfileBlocks = 500,
                                            # Important for use with the SOPHy radar
                                            ippKm = 60)

opObj11 = readUnitConfObj.addOperation(name='printInfo')
# opObj11 = readUnitConfObj.addOperation(name='printNumberOfBlock')

# voltage -> procUnitConfObjA 
# Add a processing unit

## 3 ##
procUnitConfObjA = controllerObj.addProcUnit(datatype='VoltageProc', inputId=readUnitConfObj.getId())

op =  procUnitConfObjA.addOperation(name='setAttribute')
op.addParameter(name='frequency', value='9.345e9', format='float')

op1 = procUnitConfObjA.addOperation(name='ProfileSelector')
# Change the value of the number of profiles to a fixed value (nProfiles)
# op1.addParameter(name='profileRangeList', value='0,249')
op1.addParameter(name='profileRangeList', value='0,499')

# Parameters
A_1 = 1.0
A_2 = 1.0
ipp = 400.0e-6
dc_1 = 10.0
dc_2 = 1.0
sr_tx = 20.0e6
sr_rx = 5.0e6
# The central frequency will define the Chirp sweep (ascending or descending)
fc_1 = 0.0e6
fc_2 = 1.625e6
bw_1 = 1.0e6
bw_2 = 0.25e6
td_ = 0.0
window_1 = 'B'
window_2 = 'B'
mode_f_ = 0
phi_ = 0
rep_ = 250.0

H0 = -1.75
RMIX = 5.45

chirp_tx_1 = modf.chirpModUnion_1(  ipp,
                                    sr_rx, 
                                    sr_rx, 
                                    A_1, 
                                    A_2, 
                                    dc_1, 
                                    dc_2, 
                                    fc_1, 
                                    fc_2, 
                                    bw_1, 
                                    bw_2, 
                                    td_, 
                                    window_1, 
                                    window_2)

_, chirp_tx_large = modf.chirpMod(A_1, ipp, dc_1, sr_rx, sr_rx, fc_1, bw_1, t_d = 0.0, window = window_1, mode_f = 0)
_, chirp_tx_short = modf.chirpMod(A_2, ipp, dc_2, sr_rx, sr_rx, fc_2, bw_2, t_d = 0.0, window = window_2, mode_f = 0)

code_ = chirp_tx_short
code = [code_]

## 4 ##
op2 = procUnitConfObjA.addOperation(name='Decoder', optype='other')

## 5 ##
op2.addParameter(name='code', value=code)
op2.addParameter(name='nCode', value=len(code), format='int')
op2.addParameter(name='nBaud', value=len(code[0]), format='int')

# New parameters for TFM experiments
op2.addParameter(name='code_1', value = chirp_tx_large, format='list')
op2.addParameter(name='code_2', value = chirp_tx_short, format='list')
op2.addParameter(name='DC_1', value = dc_1, format='int')
op2.addParameter(name='H0', value = H0, format='float')
op2.addParameter(name='RMIX', value = RMIX, format='float')

# At least two profiles must be integrated since they are complementary codes
# For the chirp, this is not necessary because it is not continuous and does not have two codes

# op3 = procUnitConfObjA.addOperation(name='CohInt', optype='other')
# op3.addParameter(name='n', value=2, format='int')

#######################################################################
#################### FREQUENCY-DOMAIN OPERATIONS ######################
#######################################################################

procUnitConfObjSousySpectra = controllerObj.addProcUnit(datatype='SpectraProc', inputId=procUnitConfObjA.getId())
procUnitConfObjSousySpectra.addParameter(name='nFFTPoints', value='500', format='int')
procUnitConfObjSousySpectra.addParameter(name='nProfiles', value='500', format='int')

# DC removal

opObj13 = procUnitConfObjSousySpectra.addOperation(name='removeDC')
opObj13.addParameter(name='mode', value='2', format='int')

#######################################################################
####################### FREQUENCY-DOMAIN PLOTTING #####################
#######################################################################

# SpectraPlot

opObj11 = procUnitConfObjSousySpectra.addOperation(name='SpectraPlot', optype='external')
opObj11.addParameter(name='id', value='1', format='int')
opObj11.addParameter(name='wintitle', value='Spectra NEW', format='str')
opObj11.addParameter(name='zmin', value=dBmin)
opObj11.addParameter(name='zmax', value=dBmax)
opObj11.addParameter(name='ymin', value=ymin, format='int')
opObj11.addParameter(name='ymax', value=ymax, format='int')
opObj11.addParameter(name='showprofile', value='1', format='int')
opObj11.addParameter(name='save', value=figpath, format='str')
opObj11.addParameter(name='xaxis', value='velocity', format='str')

controllerObj.start()
