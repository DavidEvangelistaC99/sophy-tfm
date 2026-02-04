
import os
import time
import math

import re
import datetime
import copy
import sys
import importlib
import itertools

from multiprocessing import Pool, TimeoutError
from multiprocessing.pool import ThreadPool
import numpy
import glob
import scipy
import h5py
from scipy.optimize import fmin_l_bfgs_b #optimize with bounds on state papameters
from .jroproc_base import ProcessingUnit, Operation, MPDecorator
from schainpy.model.data.jrodata import Parameters, hildebrand_sekhon
from scipy import asarray as ar,exp
from scipy.optimize import curve_fit
from schainpy.utils import log
import schainpy.admin
import warnings
from scipy import optimize, interpolate, signal, stats, ndimage
from scipy.optimize.optimize import OptimizeWarning
warnings.filterwarnings('ignore')

SPEED_OF_LIGHT = 299792458

'''solving pickling issue'''

def _pickle_method(method):
    func_name = method.__func__.__name__
    obj = method.__self__
    cls = method.__self__.__class__
    return _unpickle_method, (func_name, obj, cls)

def _unpickle_method(func_name, obj, cls):
    for cls in cls.mro():
        try:
            func = cls.__dict__[func_name]
        except KeyError:
            pass
        else:
            break
    return func.__get__(obj, cls)

def isNumber(str):
    try:
        float(str)
        return True
    except:
        return False

class ParametersProc(ProcessingUnit):

    METHODS = {}
    nSeconds = None

    def __init__(self):
        ProcessingUnit.__init__(self)

#         self.objectDict = {}
        self.buffer = None
        self.firstdatatime = None
        self.profIndex = 0
        self.dataOut = Parameters()
        self.setupReq = False #Agregar a todas las unidades de proc

    def __updateObjFromInput(self):

        self.dataOut.inputUnit = self.dataIn.type

        self.dataOut.timeZone = self.dataIn.timeZone
        self.dataOut.dstFlag = self.dataIn.dstFlag
        self.dataOut.errorCount = self.dataIn.errorCount
        self.dataOut.useLocalTime = self.dataIn.useLocalTime

        self.dataOut.radarControllerHeaderObj = self.dataIn.radarControllerHeaderObj.copy()
        self.dataOut.systemHeaderObj = self.dataIn.systemHeaderObj.copy()
        self.dataOut.channelList = self.dataIn.channelList
        self.dataOut.heightList = self.dataIn.heightList
        self.dataOut.dtype = numpy.dtype([('real','<f4'),('imag','<f4')])
#         self.dataOut.nHeights = self.dataIn.nHeights
#         self.dataOut.nChannels = self.dataIn.nChannels
        # self.dataOut.nBaud = self.dataIn.nBaud
        # self.dataOut.nCode = self.dataIn.nCode
        # self.dataOut.code = self.dataIn.code
#        self.dataOut.nProfiles = self.dataOut.nFFTPoints
        self.dataOut.flagDiscontinuousBlock = self.dataIn.flagDiscontinuousBlock
#         self.dataOut.utctime = self.firstdatatime
        self.dataOut.utctime = self.dataIn.utctime
        self.dataOut.flagDecodeData = self.dataIn.flagDecodeData #asumo q la data esta decodificada
        self.dataOut.flagDeflipData = self.dataIn.flagDeflipData #asumo q la data esta sin flip
        self.dataOut.nCohInt = self.dataIn.nCohInt
#        self.dataOut.nIncohInt = 1
#        self.dataOut.ippSeconds = self.dataIn.ippSeconds
#        self.dataOut.windowOfFilter = self.dataIn.windowOfFilter
        self.dataOut.timeInterval1 = self.dataIn.timeInterval
        self.dataOut.heightList = self.dataIn.heightList
        self.dataOut.frequency = self.dataIn.frequency
        # self.dataOut.noise = self.dataIn.noise
        self.dataOut.runNextUnit = self.dataIn.runNextUnit
        self.dataOut.h0 = self.dataIn.h0

    def run(self, runNextUnit = 0):

        self.dataIn.runNextUnit = runNextUnit
        #print("HOLA MUNDO SOY YO")
        #----------------------    Voltage Data    ---------------------------

        if self.dataIn.type == "Voltage":

            self.__updateObjFromInput()
            self.dataOut.data_pre = self.dataIn.data.copy()
            self.dataOut.flagNoData = False
            self.dataOut.utctimeInit = self.dataIn.utctime
            self.dataOut.paramInterval = self.dataIn.nProfiles*self.dataIn.nCohInt*self.dataIn.ippSeconds

            if hasattr(self.dataIn, 'flagDataAsBlock'):
                self.dataOut.flagDataAsBlock = self.dataIn.flagDataAsBlock

            if hasattr(self.dataIn, 'profileIndex'):
                self.dataOut.profileIndex = self.dataIn.profileIndex

            if hasattr(self.dataIn, 'dataPP_POW'):
                self.dataOut.dataPP_POW = self.dataIn.dataPP_POW

            if hasattr(self.dataIn, 'dataPP_POWER'):
                self.dataOut.dataPP_POWER = self.dataIn.dataPP_POWER

            if hasattr(self.dataIn, 'dataPP_DOP'):
                self.dataOut.dataPP_DOP = self.dataIn.dataPP_DOP

            if hasattr(self.dataIn, 'dataPP_SNR'):
                self.dataOut.dataPP_SNR = self.dataIn.dataPP_SNR

            if hasattr(self.dataIn, 'dataPP_WIDTH'):
                self.dataOut.dataPP_WIDTH = self.dataIn.dataPP_WIDTH

            if hasattr(self.dataIn, 'dataPP_CCF'):
                self.dataOut.dataPP_CCF = self.dataIn.dataPP_CCF

            if hasattr(self.dataIn, 'dataPP_NOISE'):
                self.dataOut.dataPP_NOISE = self.dataIn.dataPP_NOISE

            if hasattr(self.dataIn, 'flagAskMode'):
                self.dataOut.flagAskMode = self.dataIn.flagAskMode

            return

        #----------------------    Spectra Data    ---------------------------

        if self.dataIn.type == "Spectra":
            #print("que paso en spectra")
            self.dataOut.data_pre = [self.dataIn.data_spc, self.dataIn.data_cspc]
            self.dataOut.data_spc = self.dataIn.data_spc
            self.dataOut.data_cspc = self.dataIn.data_cspc
            self.dataOut.nProfiles = self.dataIn.nProfiles
            self.dataOut.nIncohInt = self.dataIn.nIncohInt
            self.dataOut.nFFTPoints = self.dataIn.nFFTPoints
            self.dataOut.ippFactor = self.dataIn.ippFactor
            self.dataOut.abscissaList = self.dataIn.getVelRange(1)
            self.dataOut.spc_noise = self.dataIn.getNoise()
            self.dataOut.spc_range = (self.dataIn.getFreqRange(1) , self.dataIn.getAcfRange(1) , self.dataIn.getVelRange(1))
            # self.dataOut.normFactor = self.dataIn.normFactor
            self.dataOut.pairsList = self.dataIn.pairsList
            self.dataOut.groupList = self.dataIn.pairsList
            self.dataOut.flagNoData = False

            if hasattr(self.dataIn, 'flagDataAsBlock'):
                self.dataOut.flagDataAsBlock = self.dataIn.flagDataAsBlock

            if hasattr(self.dataIn, 'ChanDist'): #Distances of receiver channels
                self.dataOut.ChanDist = self.dataIn.ChanDist
            else: self.dataOut.ChanDist = None

            #if hasattr(self.dataIn, 'VelRange'): #Velocities range
            #    self.dataOut.VelRange = self.dataIn.VelRange
            #else: self.dataOut.VelRange = None

            if hasattr(self.dataIn, 'RadarConst'): #Radar Constant
                self.dataOut.RadarConst = self.dataIn.RadarConst

            if hasattr(self.dataIn, 'NPW'): #NPW
                self.dataOut.NPW = self.dataIn.NPW

            if hasattr(self.dataIn, 'COFA'): #COFA
                self.dataOut.COFA = self.dataIn.COFA



        #----------------------    Correlation Data    ---------------------------

        if self.dataIn.type == "Correlation":
            acf_ind, ccf_ind, acf_pairs, ccf_pairs, data_acf, data_ccf = self.dataIn.splitFunctions()

            self.dataOut.data_pre = (self.dataIn.data_cf[acf_ind,:], self.dataIn.data_cf[ccf_ind,:,:])
            self.dataOut.normFactor = (self.dataIn.normFactor[acf_ind,:], self.dataIn.normFactor[ccf_ind,:])
            self.dataOut.groupList = (acf_pairs, ccf_pairs)

            self.dataOut.abscissaList = self.dataIn.lagRange
            self.dataOut.noise = self.dataIn.noise
            self.dataOut.data_snr = self.dataIn.SNR
            self.dataOut.flagNoData = False
            self.dataOut.nAvg = self.dataIn.nAvg

        #----------------------    Parameters Data    ---------------------------

        if self.dataIn.type == "Parameters":
            self.dataOut.copy(self.dataIn)
            self.dataOut.flagNoData = False
            #print("yo si entre")

            return True

        self.__updateObjFromInput()
        #print("yo si entre2")

        self.dataOut.utctimeInit = self.dataIn.utctime
        self.dataOut.paramInterval = self.dataIn.timeInterval
        #print("soy spectra ",self.dataOut.utctimeInit)
        return


def target(tups):

    obj, args = tups

    return obj.FitGau(args)

class RemoveWideGC(Operation):
    ''' This class remove the wide clutter and replace it with a simple interpolation points
        This mainly applies to CLAIRE radar

        ClutterWidth :    Width to look for the clutter peak

        Input:

        self.dataOut.data_pre :        SPC and CSPC
        self.dataOut.spc_range :       To select wind and rainfall velocities

        Affected:

        self.dataOut.data_pre :        It is used for the new SPC and CSPC ranges of wind

        Written by D. Scipión 25.02.2021
    '''
    def __init__(self):
        Operation.__init__(self)
        self.i = 0
        self.ich = 0
        self.ir = 0

    def run(self, dataOut, ClutterWidth=2.5):
        # print ('Entering RemoveWideGC ... ')

        self.spc = dataOut.data_pre[0].copy()
        self.spc_out = dataOut.data_pre[0].copy()
        self.Num_Chn = self.spc.shape[0]
        self.Num_Hei = self.spc.shape[2]
        VelRange = dataOut.spc_range[2][:-1]
        dv = VelRange[1]-VelRange[0]

        # Find the velocities that corresponds to zero
        gc_values = numpy.squeeze(numpy.where(numpy.abs(VelRange) <= ClutterWidth))

        # Removing novalid data from the spectra
        for ich in range(self.Num_Chn) :
            for ir in range(self.Num_Hei) :
                # Estimate the noise at each range
                HSn = hildebrand_sekhon(self.spc[ich,:,ir],dataOut.nIncohInt)

                # Removing the noise floor at each range
                novalid = numpy.where(self.spc[ich,:,ir] < HSn)
                self.spc[ich,novalid,ir] = HSn

                junk = numpy.append(numpy.insert(numpy.squeeze(self.spc[ich,gc_values,ir]),0,HSn),HSn)
                j1index = numpy.squeeze(numpy.where(numpy.diff(junk)>0))
                j2index = numpy.squeeze(numpy.where(numpy.diff(junk)<0))
                if ((numpy.size(j1index)<=1) | (numpy.size(j2index)<=1)) :
                    continue
                junk3 = numpy.squeeze(numpy.diff(j1index))
                junk4 = numpy.squeeze(numpy.diff(j2index))

                valleyindex = j2index[numpy.where(junk4>1)]
                peakindex = j1index[numpy.where(junk3>1)]

                isvalid = numpy.squeeze(numpy.where(numpy.abs(VelRange[gc_values[peakindex]]) <= 2.5*dv))
                if numpy.size(isvalid) == 0 :
                    continue
                if numpy.size(isvalid) >1 :
                    vindex = numpy.argmax(self.spc[ich,gc_values[peakindex[isvalid]],ir])
                    isvalid = isvalid[vindex]

                # clutter peak
                gcpeak = peakindex[isvalid]
                vl = numpy.where(valleyindex < gcpeak)
                if numpy.size(vl) == 0:
                    continue
                gcvl = valleyindex[vl[0][-1]]
                vr = numpy.where(valleyindex > gcpeak)
                if numpy.size(vr) == 0:
                    continue
                gcvr = valleyindex[vr[0][0]]

                # Removing the clutter
                interpindex = numpy.array([gc_values[gcvl], gc_values[gcvr]])
                gcindex = gc_values[gcvl+1:gcvr-1]
                self.spc_out[ich,gcindex,ir] = numpy.interp(VelRange[gcindex],VelRange[interpindex],self.spc[ich,interpindex,ir])

        dataOut.data_pre[0] = self.spc_out
        #print ('Leaving RemoveWideGC ... ')
        return dataOut

class SpectralFilters(Operation):
    ''' This class allows to replace the novalid values with noise for each channel
        This applies to CLAIRE RADAR

        PositiveLimit :    RightLimit of novalid data
        NegativeLimit :    LeftLimit of novalid data

        Input:

        self.dataOut.data_pre :        SPC and CSPC
        self.dataOut.spc_range :       To select wind and rainfall velocities

        Affected:

        self.dataOut.data_pre :        It is used for the new SPC and CSPC ranges of wind

        Written by D. Scipión 29.01.2021
    '''
    def __init__(self):
        Operation.__init__(self)
        self.i = 0

    def run(self, dataOut, ):

        self.spc = dataOut.data_pre[0].copy()
        self.Num_Chn = self.spc.shape[0]
        VelRange = dataOut.spc_range[2]

        # novalid corresponds to data within the Negative and PositiveLimit


        # Removing novalid data from the spectra
        for i in range(self.Num_Chn):
            self.spc[i,novalid,:] = dataOut.noise[i]
        dataOut.data_pre[0] = self.spc
        return dataOut

class GaussianFit(Operation):

    '''
        Function that fit of one and two generalized gaussians (gg) based
        on the PSD shape across an "power band" identified from a cumsum of
        the measured spectrum - noise.

        Input:
            self.dataOut.data_pre    :    SelfSpectra

        Output:
            self.dataOut.SPCparam :    SPC_ch1, SPC_ch2

    '''
    def __init__(self):
        Operation.__init__(self)
        self.i=0


    # def run(self, dataOut, num_intg=7, pnoise=1., SNRlimit=-9): #num_intg: Incoherent integrations, pnoise: Noise, vel_arr: range of velocities, similar to the ftt points
    def run(self, dataOut, SNRdBlimit=-9, method='generalized'):
        """This routine will find a couple of generalized Gaussians to a power spectrum
        methods: generalized, squared
        input: spc
        output:
            noise, amplitude0,shift0,width0,p0,Amplitude1,shift1,width1,p1
        """
        print ('Entering ',method,' double Gaussian fit')
        self.spc = dataOut.data_pre[0].copy()
        self.Num_Hei = self.spc.shape[2]
        self.Num_Bin = self.spc.shape[1]
        self.Num_Chn = self.spc.shape[0]

        start_time = time.time()

        pool = Pool(processes=self.Num_Chn)
        args = [(dataOut.spc_range[2], ich, dataOut.spc_noise[ich], dataOut.nIncohInt, SNRdBlimit) for ich in range(self.Num_Chn)]
        objs = [self for __ in range(self.Num_Chn)]
        attrs = list(zip(objs, args))
        DGauFitParam = pool.map(target, attrs)
        # Parameters:
        # 0. Noise, 1. Amplitude, 2. Shift, 3. Width 4. Power
        dataOut.DGauFitParams = numpy.asarray(DGauFitParam)

        # Double Gaussian Curves
        gau0 = numpy.zeros([self.Num_Chn,self.Num_Bin,self.Num_Hei])
        gau0[:] = numpy.NaN
        gau1 = numpy.zeros([self.Num_Chn,self.Num_Bin,self.Num_Hei])
        gau1[:] = numpy.NaN
        x_mtr = numpy.transpose(numpy.tile(dataOut.getVelRange(1)[:-1], (self.Num_Hei,1)))
        for iCh in range(self.Num_Chn):
            N0 = numpy.transpose(numpy.transpose([dataOut.DGauFitParams[iCh][0,:,0]] * self.Num_Bin))
            N1 = numpy.transpose(numpy.transpose([dataOut.DGauFitParams[iCh][0,:,1]] * self.Num_Bin))
            A0 = numpy.transpose(numpy.transpose([dataOut.DGauFitParams[iCh][1,:,0]] * self.Num_Bin))
            A1 = numpy.transpose(numpy.transpose([dataOut.DGauFitParams[iCh][1,:,1]] * self.Num_Bin))
            v0 = numpy.transpose(numpy.transpose([dataOut.DGauFitParams[iCh][2,:,0]] * self.Num_Bin))
            v1 = numpy.transpose(numpy.transpose([dataOut.DGauFitParams[iCh][2,:,1]] * self.Num_Bin))
            s0 = numpy.transpose(numpy.transpose([dataOut.DGauFitParams[iCh][3,:,0]] * self.Num_Bin))
            s1 = numpy.transpose(numpy.transpose([dataOut.DGauFitParams[iCh][3,:,1]] * self.Num_Bin))
            if method == 'genealized':
                p0 = numpy.transpose(numpy.transpose([dataOut.DGauFitParams[iCh][4,:,0]] * self.Num_Bin))
                p1 = numpy.transpose(numpy.transpose([dataOut.DGauFitParams[iCh][4,:,1]] * self.Num_Bin))
            elif method == 'squared':
                p0 = 2.
                p1 = 2.
            gau0[iCh] = A0*numpy.exp(-0.5*numpy.abs((x_mtr-v0)/s0)**p0)+N0
            gau1[iCh] = A1*numpy.exp(-0.5*numpy.abs((x_mtr-v1)/s1)**p1)+N1
        dataOut.GaussFit0 = gau0
        dataOut.GaussFit1 = gau1

        print('Leaving ',method ,' double Gaussian fit')
        return dataOut

    def FitGau(self, X):
        # print('Entering FitGau')
        # Assigning the variables
        Vrange, ch, wnoise, num_intg, SNRlimit = X
        # Noise Limits
        noisebl = wnoise * 0.9
        noisebh = wnoise * 1.1
        # Radar Velocity
        Va = max(Vrange)
        deltav = Vrange[1] - Vrange[0]
        x = numpy.arange(self.Num_Bin)

        # print ('stop 0')

        # 5 parameters, 2 Gaussians
        DGauFitParam = numpy.zeros([5, self.Num_Hei,2])
        DGauFitParam[:] = numpy.NaN

        # SPCparam = []
        # SPC_ch1 = numpy.zeros([self.Num_Bin,self.Num_Hei])
        # SPC_ch2 = numpy.zeros([self.Num_Bin,self.Num_Hei])
        # SPC_ch1[:] = 0 #numpy.NaN
        # SPC_ch2[:] = 0 #numpy.NaN
        # print ('stop 1')
        for ht in range(self.Num_Hei):
            # print (ht)
            # print ('stop 2')
            # Spectra at each range
            spc =  numpy.asarray(self.spc)[ch,:,ht]
            snr = ( spc.mean() - wnoise ) / wnoise
            snrdB = 10.*numpy.log10(snr)

            #print ('stop 3')
            if snrdB < SNRlimit :
                # snr = numpy.NaN
                # SPC_ch1[:,ht] = 0#numpy.NaN
                # SPC_ch1[:,ht] = 0#numpy.NaN
                # SPCparam = (SPC_ch1,SPC_ch2)
                # print ('SNR less than SNRth')
                continue
            # wnoise = hildebrand_sekhon(spc,num_intg)
            # print ('stop 2.01')
            #############################################
            # normalizing spc and noise
            # This part differs from gg1
            # spc_norm_max = max(spc) #commented by D. Scipión 19.03.2021
            #spc = spc / spc_norm_max
            # pnoise = pnoise #/ spc_norm_max #commented by D. Scipión 19.03.2021
            #############################################

            # print ('stop 2.1')
            fatspectra=1.0
            # noise per channel.... we might want to use the noise at each range

            # wnoise = noise_ #/ spc_norm_max #commented by D. Scipión 19.03.2021
                #wnoise,stdv,i_max,index =enoise(spc,num_intg) #noise estimate using Hildebrand Sekhon, only wnoise is used
                #if wnoise>1.1*pnoise: # to be tested later
                #    wnoise=pnoise
            # noisebl = wnoise*0.9
            # noisebh = wnoise*1.1
            spc = spc - wnoise # signal

            # print ('stop 2.2')
            minx = numpy.argmin(spc)
            #spcs=spc.copy()
            spcs = numpy.roll(spc,-minx)
            cum = numpy.cumsum(spcs)
            # tot_noise = wnoise * self.Num_Bin  #64;

            # print ('stop 2.3')
            # snr = sum(spcs) / tot_noise
            # snrdB = 10.*numpy.log10(snr)
            #print ('stop 3')
            # if snrdB < SNRlimit :
                # snr = numpy.NaN
                # SPC_ch1[:,ht] = 0#numpy.NaN
                # SPC_ch1[:,ht] = 0#numpy.NaN
                # SPCparam = (SPC_ch1,SPC_ch2)
                # print ('SNR less than SNRth')
                # continue


            #if snrdB<-18 or numpy.isnan(snrdB) or num_intg<4:
            #    return [None,]*4,[None,]*4,None,snrdB,None,None,[None,]*5,[None,]*9,None
            # print ('stop 4')
            cummax = max(cum)
            epsi = 0.08 * fatspectra # cumsum to narrow down the energy region
            cumlo = cummax * epsi
            cumhi = cummax * (1-epsi)
            powerindex = numpy.array(numpy.where(numpy.logical_and(cum>cumlo, cum<cumhi))[0])

            # print ('stop 5')
            if len(powerindex) < 1:# case for powerindex 0
                # print ('powerindex < 1')
                continue
            powerlo = powerindex[0]
            powerhi = powerindex[-1]
            powerwidth = powerhi-powerlo
            if powerwidth <= 1:
                # print('powerwidth <= 1')
                continue

            # print ('stop 6')
            firstpeak = powerlo + powerwidth/10.# first gaussian energy location
            secondpeak = powerhi - powerwidth/10. #second gaussian energy location
            midpeak = (firstpeak + secondpeak)/2.
            firstamp = spcs[int(firstpeak)]
            secondamp = spcs[int(secondpeak)]
            midamp = spcs[int(midpeak)]

            y_data = spc + wnoise

            '''    single Gaussian    '''
            shift0 = numpy.mod(midpeak+minx, self.Num_Bin )
            width0 = powerwidth/4.#Initialization entire power of spectrum divided by 4
            power0 = 2.
            amplitude0 = midamp
            state0 = [shift0,width0,amplitude0,power0,wnoise]
            bnds = ((0,self.Num_Bin-1),(1,powerwidth),(0,None),(0.5,3.),(noisebl,noisebh))
            lsq1 = fmin_l_bfgs_b(self.misfit1, state0, args=(y_data,x,num_intg), bounds=bnds, approx_grad=True)
            # print ('stop 7.1')
            # print (bnds)

            chiSq1=lsq1[1]

            # print ('stop 8')
            if fatspectra<1.0 and powerwidth<4:
                    choice=0
                    Amplitude0=lsq1[0][2]
                    shift0=lsq1[0][0]
                    width0=lsq1[0][1]
                    p0=lsq1[0][3]
                    Amplitude1=0.
                    shift1=0.
                    width1=0.
                    p1=0.
                    noise=lsq1[0][4]
                    #return (numpy.array([shift0,width0,Amplitude0,p0]),
                    #        numpy.array([shift1,width1,Amplitude1,p1]),noise,snrdB,chiSq1,6.,sigmas1,[None,]*9,choice)

            # print ('stop 9')
            '''    two Gaussians    '''
            #shift0=numpy.mod(firstpeak+minx,64); shift1=numpy.mod(secondpeak+minx,64)
            shift0 = numpy.mod(firstpeak+minx, self.Num_Bin )
            shift1 = numpy.mod(secondpeak+minx, self.Num_Bin )
            width0 = powerwidth/6.
            width1 = width0
            power0 = 2.
            power1 = power0
            amplitude0 = firstamp
            amplitude1 = secondamp
            state0 = [shift0,width0,amplitude0,power0,shift1,width1,amplitude1,power1,wnoise]
            #bnds=((0,63),(1,powerwidth/2.),(0,None),(0.5,3.),(0,63),(1,powerwidth/2.),(0,None),(0.5,3.),(noisebl,noisebh))
            bnds=((0,self.Num_Bin-1),(1,powerwidth/2.),(0,None),(0.5,3.),(0,self.Num_Bin-1),(1,powerwidth/2.),(0,None),(0.5,3.),(noisebl,noisebh))
            #bnds=(( 0,(self.Num_Bin-1) ),(1,powerwidth/2.),(0,None),(0.5,3.),( 0,(self.Num_Bin-1)),(1,powerwidth/2.),(0,None),(0.5,3.),(0.1,0.5))

            # print ('stop 10')
            lsq2 = fmin_l_bfgs_b( self.misfit2 , state0 , args=(y_data,x,num_intg) , bounds=bnds , approx_grad=True )

            # print ('stop 11')
            chiSq2 = lsq2[1]

            # print ('stop 12')

            oneG = (chiSq1<5 and chiSq1/chiSq2<2.0) and (abs(lsq2[0][0]-lsq2[0][4])<(lsq2[0][1]+lsq2[0][5])/3. or abs(lsq2[0][0]-lsq2[0][4])<10)

            # print ('stop 13')
            if snrdB>-12: # when SNR is strong pick the peak with least shift (LOS velocity) error
                if oneG:
                    choice = 0
                else:
                    w1 = lsq2[0][1]; w2 = lsq2[0][5]
                    a1 = lsq2[0][2]; a2 = lsq2[0][6]
                    p1 = lsq2[0][3]; p2 = lsq2[0][7]
                    s1 = (2**(1+1./p1))*scipy.special.gamma(1./p1)/p1
                    s2 = (2**(1+1./p2))*scipy.special.gamma(1./p2)/p2
                    gp1 = a1*w1*s1; gp2 = a2*w2*s2 # power content of each ggaussian with proper p scaling

                    if gp1>gp2:
                        if a1>0.7*a2:
                            choice = 1
                        else:
                            choice = 2
                    elif gp2>gp1:
                        if a2>0.7*a1:
                            choice = 2
                        else:
                            choice = 1
                    else:
                        choice = numpy.argmax([a1,a2])+1
                        #else:
                        #choice=argmin([std2a,std2b])+1

            else: # with low SNR go to the most energetic peak
                choice = numpy.argmax([lsq1[0][2]*lsq1[0][1],lsq2[0][2]*lsq2[0][1],lsq2[0][6]*lsq2[0][5]])

            # print ('stop 14')
            shift0 = lsq2[0][0]
            vel0 = Vrange[0] + shift0 * deltav
            shift1 = lsq2[0][4]
            # vel1=Vrange[0] + shift1 * deltav

            # max_vel = 1.0
            # Va = max(Vrange)
            # deltav = Vrange[1]-Vrange[0]
            # print ('stop 15')
            #first peak will be 0, second peak will be 1
            # if vel0 > -1.0 and vel0 < max_vel : #first peak is in the correct range # Commented by D.Scipión 19.03.2021
            if vel0 > -Va and vel0 < Va : #first peak is in the correct range
                shift0 = lsq2[0][0]
                width0 = lsq2[0][1]
                Amplitude0 = lsq2[0][2]
                p0 = lsq2[0][3]

                shift1 = lsq2[0][4]
                width1 = lsq2[0][5]
                Amplitude1 = lsq2[0][6]
                p1 = lsq2[0][7]
                noise = lsq2[0][8]
            else:
                shift1 = lsq2[0][0]
                width1 = lsq2[0][1]
                Amplitude1 = lsq2[0][2]
                p1 = lsq2[0][3]

                shift0 = lsq2[0][4]
                width0 = lsq2[0][5]
                Amplitude0 = lsq2[0][6]
                p0 = lsq2[0][7]
                noise = lsq2[0][8]

            if Amplitude0<0.05: # in case the peak is noise
                shift0,width0,Amplitude0,p0 = 4*[numpy.NaN]
            if Amplitude1<0.05:
                shift1,width1,Amplitude1,p1 = 4*[numpy.NaN]

            # print ('stop 16 ')
            # SPC_ch1[:,ht] = noise + Amplitude0*numpy.exp(-0.5*(abs(x-shift0)/width0)**p0)
            # SPC_ch2[:,ht] = noise + Amplitude1*numpy.exp(-0.5*(abs(x-shift1)/width1)**p1)
            # SPCparam = (SPC_ch1,SPC_ch2)

            DGauFitParam[0,ht,0] = noise
            DGauFitParam[0,ht,1] = noise
            DGauFitParam[1,ht,0] = Amplitude0
            DGauFitParam[1,ht,1] = Amplitude1
            DGauFitParam[2,ht,0] = Vrange[0] + shift0 * deltav
            DGauFitParam[2,ht,1] = Vrange[0] + shift1 * deltav
            DGauFitParam[3,ht,0] = width0 * deltav
            DGauFitParam[3,ht,1] = width1 * deltav
            DGauFitParam[4,ht,0] = p0
            DGauFitParam[4,ht,1] = p1

        # print (DGauFitParam.shape)
        # print ('Leaving FitGau')
        return DGauFitParam
        # return SPCparam
        # return GauSPC

    def y_model1(self,x,state):
        shift0, width0, amplitude0, power0, noise = state
        model0 = amplitude0*numpy.exp(-0.5*abs((x - shift0)/width0)**power0)
        model0u = amplitude0*numpy.exp(-0.5*abs((x - shift0 - self.Num_Bin)/width0)**power0)
        model0d = amplitude0*numpy.exp(-0.5*abs((x - shift0 + self.Num_Bin)/width0)**power0)
        return model0 + model0u + model0d + noise

    def y_model2(self,x,state): #Equation for two generalized Gaussians with Nyquist
        shift0, width0, amplitude0, power0, shift1, width1, amplitude1, power1, noise = state
        model0 = amplitude0*numpy.exp(-0.5*abs((x-shift0)/width0)**power0)
        model0u = amplitude0*numpy.exp(-0.5*abs((x - shift0 - self.Num_Bin)/width0)**power0)
        model0d = amplitude0*numpy.exp(-0.5*abs((x - shift0 + self.Num_Bin)/width0)**power0)

        model1 = amplitude1*numpy.exp(-0.5*abs((x - shift1)/width1)**power1)
        model1u = amplitude1*numpy.exp(-0.5*abs((x - shift1 - self.Num_Bin)/width1)**power1)
        model1d = amplitude1*numpy.exp(-0.5*abs((x - shift1 + self.Num_Bin)/width1)**power1)
        return model0 + model0u + model0d + model1 + model1u + model1d + noise

    def misfit1(self,state,y_data,x,num_intg): # This function compares how close real data is with the model data, the close it is, the better it is.

        return num_intg*sum((numpy.log(y_data)-numpy.log(self.y_model1(x,state)))**2)#/(64-5.) # /(64-5.) can be commented

    def misfit2(self,state,y_data,x,num_intg):
        return num_intg*sum((numpy.log(y_data)-numpy.log(self.y_model2(x,state)))**2)#/(64-9.)



class PrecipitationProc(Operation):

    '''
         Operator that estimates Reflectivity factor (Z), and estimates rainfall Rate (R)

         Input:
            self.dataOut.data_pre    :    SelfSpectra

         Output:

            self.dataOut.data_output :    Reflectivity factor, rainfall Rate


         Parameters affected:
    '''

    def __init__(self):
        Operation.__init__(self)
        self.i=0

    def run(self, dataOut, radar=None, Pt=5000, Gt=295.1209, Gr=70.7945, Lambda=0.6741, aL=2.5118,
            tauW=4e-06, ThetaT=0.1656317, ThetaR=0.36774087, Km2 = 0.93, Altitude=3350,SNRdBlimit=-30):

        # print ('Entering PrecepitationProc ... ')

        if radar == "MIRA35C" :

            self.spc = dataOut.data_pre[0].copy()
            self.Num_Hei = self.spc.shape[2]
            self.Num_Bin = self.spc.shape[1]
            self.Num_Chn = self.spc.shape[0]
            Ze = self.dBZeMODE2(dataOut)

        else:

            self.spc = dataOut.data_pre[0].copy()

            #NOTA SE DEBE REMOVER EL RANGO DEL PULSO TX
            self.spc[:,:,0:7]= numpy.NaN

            self.Num_Hei = self.spc.shape[2]
            self.Num_Bin = self.spc.shape[1]
            self.Num_Chn = self.spc.shape[0]

            VelRange = dataOut.spc_range[2]

            ''' Se obtiene la constante del RADAR '''

            self.Pt = Pt
            self.Gt = Gt
            self.Gr = Gr
            self.Lambda = Lambda
            self.aL = aL
            self.tauW = tauW
            self.ThetaT = ThetaT
            self.ThetaR = ThetaR
            self.GSys = 10**(36.63/10) # Ganancia de los LNA 36.63 dB
            self.lt = 10**(1.67/10) # Perdida en cables Tx 1.67 dB
            self.lr = 10**(5.73/10) # Perdida en cables Rx 5.73 dB

            Numerator = ( (4*numpy.pi)**3 * aL**2 * 16 * numpy.log(2) )
            Denominator = ( Pt * Gt * Gr * Lambda**2 * SPEED_OF_LIGHT * tauW * numpy.pi * ThetaT * ThetaR)
            RadarConstant = 10e-26 * Numerator / Denominator #
            ExpConstant = 10**(40/10) #Constante Experimental

            SignalPower = numpy.zeros([self.Num_Chn,self.Num_Bin,self.Num_Hei])
            for i in range(self.Num_Chn):
                SignalPower[i,:,:] = self.spc[i,:,:] - dataOut.noise[i]
                SignalPower[numpy.where(SignalPower < 0)] = 1e-20

            SPCmean = numpy.mean(SignalPower, 0)
            Pr = SPCmean[:,:]/dataOut.normFactor

            # Declaring auxiliary variables
            Range = dataOut.heightList*1000. #Range in m
            # replicate the heightlist to obtain a matrix [Num_Bin,Num_Hei]
            rMtrx = numpy.transpose(numpy.transpose([dataOut.heightList*1000.] * self.Num_Bin))
            zMtrx = rMtrx+Altitude
            # replicate the VelRange to obtain a matrix [Num_Bin,Num_Hei]
            VelMtrx = numpy.transpose(numpy.tile(VelRange[:-1], (self.Num_Hei,1)))

            # height dependence to air density Foote and Du Toit (1969)
            delv_z = 1 + 3.68e-5 * zMtrx + 1.71e-9 * zMtrx**2
            VMtrx = VelMtrx / delv_z #Normalized velocity
            VMtrx[numpy.where(VMtrx> 9.6)] = numpy.NaN
            # Diameter is related to the fall speed of falling drops
            D_Vz = -1.667 * numpy.log( 0.9369 - 0.097087 * VMtrx ) # D in [mm]
            # Only valid for D>= 0.16 mm
            D_Vz[numpy.where(D_Vz < 0.16)] = numpy.NaN

            #Calculate Radar Reflectivity ETAn
            ETAn = (RadarConstant *ExpConstant) * Pr * rMtrx**2  #Reflectivity (ETA)
            ETAd = ETAn * 6.18 * exp( -0.6 * D_Vz ) * delv_z
            # Radar Cross Section
            sigmaD = Km2 * (D_Vz * 1e-3 )**6 * numpy.pi**5 / Lambda**4
            # Drop Size Distribution
            DSD = ETAn / sigmaD
            # Equivalente Reflectivy
            Ze_eqn = numpy.nansum( DSD * D_Vz**6 ,axis=0)
            Ze_org = numpy.nansum(ETAn * Lambda**4, axis=0) / (1e-18*numpy.pi**5 * Km2) # [mm^6 /m^3]
            # RainFall Rate
            RR = 0.0006*numpy.pi * numpy.nansum( D_Vz**3 * DSD * VelMtrx ,0) #mm/hr

        # Censoring the data
        # Removing data with SNRth < 0dB se debe considerar el SNR por canal
        SNRth = 10**(SNRdBlimit/10) #-30dB
        novalid = numpy.where((dataOut.data_snr[0,:] <SNRth) | (dataOut.data_snr[1,:] <SNRth) | (dataOut.data_snr[2,:] <SNRth)) # AND condition. Maybe OR condition better
        W = numpy.nanmean(dataOut.data_dop,0)
        W[novalid] = numpy.NaN
        Ze_org[novalid] = numpy.NaN
        RR[novalid] = numpy.NaN

        dataOut.data_output = RR[8]
        dataOut.data_param = numpy.ones([3,self.Num_Hei])
        dataOut.channelList = [0,1,2]

        dataOut.data_param[0]=10*numpy.log10(Ze_org)
        dataOut.data_param[1]=-W
        dataOut.data_param[2]=RR

        # print ('Leaving PrecepitationProc ... ')
        return dataOut

    def dBZeMODE2(self, dataOut): #    Processing for MIRA35C

        NPW = dataOut.NPW
        COFA = dataOut.COFA

        SNR = numpy.array([self.spc[0,:,:] / NPW[0]]) #, self.spc[1,:,:] / NPW[1]])
        RadarConst = dataOut.RadarConst
        #frequency = 34.85*10**9

        ETA = numpy.zeros(([self.Num_Chn ,self.Num_Hei]))
        data_output = numpy.ones([self.Num_Chn , self.Num_Hei])*numpy.NaN

        ETA = numpy.sum(SNR,1)

        ETA = numpy.where(ETA != 0. , ETA, numpy.NaN)

        Ze = numpy.ones([self.Num_Chn, self.Num_Hei] )

        for r in range(self.Num_Hei):

            Ze[0,r] =  ( ETA[0,r] ) * COFA[0,r][0] * RadarConst * ((r/5000.)**2)
            #Ze[1,r] =  ( ETA[1,r] ) * COFA[1,r][0] * RadarConst * ((r/5000.)**2)

        return Ze

#     def GetRadarConstant(self):
#
#         """
#         Constants:
#
#         Pt:     Transmission Power               dB        5kW                5000
#         Gt:     Transmission Gain                dB        24.7 dB            295.1209
#         Gr:     Reception Gain                   dB        18.5 dB            70.7945
#         Lambda: Wavelenght                       m         0.6741 m           0.6741
#         aL:     Attenuation loses                dB        4dB                2.5118
#         tauW:   Width of transmission pulse      s         4us                4e-6
#         ThetaT: Transmission antenna bean angle  rad       0.1656317 rad      0.1656317
#         ThetaR: Reception antenna beam angle     rad       0.36774087 rad     0.36774087
#
#         """
#
#         Numerator = ( (4*numpy.pi)**3 * aL**2 * 16 * numpy.log(2) )
#         Denominator = ( Pt * Gt * Gr * Lambda**2 * SPEED_OF_LIGHT * TauW * numpy.pi * ThetaT * TheraR)
#         RadarConstant =  Numerator / Denominator
#
#         return RadarConstant



class FullSpectralAnalysis(Operation):

    """
        Function that implements Full Spectral Analysis technique.

        Input:
            self.dataOut.data_pre    :    SelfSpectra and CrossSpectra data
            self.dataOut.groupList   :    Pairlist of channels
            self.dataOut.ChanDist    :    Physical distance between receivers


        Output:

            self.dataOut.data_output :    Zonal wind, Meridional wind, and Vertical wind


        Parameters affected:    Winds, height range, SNR

    """
    def run(self, dataOut, Xi01=None, Xi02=None, Xi12=None, Eta01=None, Eta02=None, Eta12=None, SNRdBlimit=-30,
        minheight=None, maxheight=None, NegativeLimit=None, PositiveLimit=None):

        spc = dataOut.data_pre[0].copy()
        cspc = dataOut.data_pre[1]
        nHeights = spc.shape[2]

        # first_height = 0.75 #km (ref: data header 20170822)
        # resolution_height = 0.075 #km
        '''
            finding height range. check this when radar parameters are changed!
        '''
        if maxheight is not None:
            # range_max = math.ceil((maxheight - first_height) / resolution_height) # theoretical
            range_max = math.ceil(13.26 * maxheight - 3) # empirical, works better
        else:
            range_max = nHeights
        if minheight is not None:
            # range_min = int((minheight - first_height) / resolution_height) # theoretical
            range_min = int(13.26 * minheight - 5) # empirical, works better
            if range_min < 0:
                range_min = 0
        else:
            range_min = 0

        pairsList = dataOut.groupList
        if dataOut.ChanDist is not None :
            ChanDist = dataOut.ChanDist
        else:
            ChanDist = numpy.array([[Xi01, Eta01],[Xi02,Eta02],[Xi12,Eta12]])

        # 4 variables: zonal, meridional, vertical, and average SNR
        data_param = numpy.zeros([4,nHeights]) * numpy.NaN
        velocityX = numpy.zeros([nHeights]) * numpy.NaN
        velocityY = numpy.zeros([nHeights]) * numpy.NaN
        velocityZ = numpy.zeros([nHeights]) * numpy.NaN

        dbSNR = 10*numpy.log10(numpy.average(dataOut.data_snr,0))

        '''***********************************************WIND ESTIMATION**************************************'''
        for Height in range(nHeights):

            if Height >= range_min and Height < range_max:
                # error_code will be useful in future analysis
                [Vzon,Vmer,Vver, error_code] = self.WindEstimation(spc[:,:,Height], cspc[:,:,Height], pairsList,
                    ChanDist, Height, dataOut.noise, dataOut.spc_range, dbSNR[Height], SNRdBlimit, NegativeLimit, PositiveLimit,dataOut.frequency)

            if abs(Vzon) < 100. and abs(Vmer) < 100.:
                velocityX[Height] = Vzon
                velocityY[Height] = -Vmer
                velocityZ[Height] = Vver

        # Censoring data with SNR threshold
        dbSNR [dbSNR < SNRdBlimit] = numpy.NaN

        data_param[0] = velocityX
        data_param[1] = velocityY
        data_param[2] = velocityZ
        data_param[3] = dbSNR
        dataOut.data_param = data_param
        return dataOut

    def moving_average(self,x, N=2):
        """ convolution for smoothenig data. note that last N-1 values are convolution with zeroes """
        return numpy.convolve(x, numpy.ones((N,))/N)[(N-1):]

    def gaus(self,xSamples,Amp,Mu,Sigma):
        return Amp * numpy.exp(-0.5*((xSamples - Mu)/Sigma)**2)

    def Moments(self, ySamples, xSamples):
        Power = numpy.nanmean(ySamples)                                 # Power, 0th Moment
        yNorm = ySamples / numpy.nansum(ySamples)
        RadVel = numpy.nansum(xSamples * yNorm)                         # Radial Velocity, 1st Moment
        Sigma2 = numpy.nansum(yNorm * (xSamples - RadVel)**2)      # Spectral Width, 2nd Moment
        StdDev = numpy.sqrt(numpy.abs(Sigma2))                                            # Desv. Estandar, Ancho espectral
        return numpy.array([Power,RadVel,StdDev])

    def StopWindEstimation(self, error_code):
        Vzon = numpy.NaN
        Vmer = numpy.NaN
        Vver = numpy.NaN
        return Vzon, Vmer, Vver, error_code

    def AntiAliasing(self, interval, maxstep):
        """
            function to prevent errors from aliased values when computing phaseslope
        """
        antialiased = numpy.zeros(len(interval))
        copyinterval = interval.copy()

        antialiased[0] = copyinterval[0]

        for i in range(1,len(antialiased)):
            step = interval[i] - interval[i-1]
            if step > maxstep:
                copyinterval -= 2*numpy.pi
                antialiased[i] = copyinterval[i]
            elif step < maxstep*(-1):
                copyinterval += 2*numpy.pi
                antialiased[i] = copyinterval[i]
            else:
                antialiased[i] = copyinterval[i].copy()

        return antialiased

    def WindEstimation(self, spc, cspc, pairsList, ChanDist, Height, noise, AbbsisaRange, dbSNR, SNRlimit, NegativeLimit, PositiveLimit, radfreq):
        """
            Function that Calculates Zonal, Meridional and Vertical wind velocities.
            Initial Version by E. Bocanegra updated by J. Zibell until Nov. 2019.

            Input:
                spc, cspc       : self spectra and cross spectra data. In Briggs notation something like S_i*(S_i)_conj, (S_j)_conj respectively.
                pairsList       : Pairlist of channels
                ChanDist        : array of xi_ij and eta_ij
                Height          : height at which data is processed
                noise           : noise in [channels] format for specific height
                Abbsisarange    : range of the frequencies or velocities
                dbSNR, SNRlimit : signal to noise ratio in db, lower limit

            Output:
                Vzon, Vmer, Vver         : wind velocities
                error_code               : int that states where code is terminated

                    0 : no error detected
                    1 : Gaussian of mean spc exceeds widthlimit
                    2 : no Gaussian of mean spc found
                    3 : SNR to low or velocity to high -> prec. e.g.
                    4 : at least one Gaussian of cspc exceeds widthlimit
                    5 : zero out of three cspc Gaussian fits converged
                    6 : phase slope fit could not be found
                    7 : arrays used to fit phase have different length
                    8 : frequency range is either too short (len <= 5) or very long (> 30% of cspc)

        """

        error_code = 0

        nChan = spc.shape[0]
        nProf = spc.shape[1]
        nPair = cspc.shape[0]

        SPC_Samples = numpy.zeros([nChan, nProf])           # for normalized spc values for one height
        CSPC_Samples = numpy.zeros([nPair, nProf], dtype=numpy.complex_)      # for normalized cspc values
        phase = numpy.zeros([nPair, nProf])                 # phase between channels
        PhaseSlope = numpy.zeros(nPair)                     # slope of the phases, channelwise
        PhaseInter = numpy.zeros(nPair)                     # intercept to the slope of the phases, channelwise
        xFrec = AbbsisaRange[0][:-1]                        # frequency range
        xVel = AbbsisaRange[2][:-1]                         # velocity range
        xSamples = xFrec                                    # the frequency range is taken
        delta_x = xSamples[1] - xSamples[0]                 # delta_f or delta_x

        # only consider velocities with in NegativeLimit and PositiveLimit
        if (NegativeLimit is None):
            NegativeLimit = numpy.min(xVel)
        if (PositiveLimit is None):
            PositiveLimit = numpy.max(xVel)
        xvalid = numpy.where((xVel > NegativeLimit) & (xVel < PositiveLimit))
        xSamples_zoom = xSamples[xvalid]

        '''Getting Eij and Nij'''
        Xi01, Xi02, Xi12 = ChanDist[:,0]
        Eta01, Eta02, Eta12 = ChanDist[:,1]

        # spwd limit - updated by D. Scipión 30.03.2021
        widthlimit = 10
        '''************************* SPC is normalized ********************************'''
        spc_norm = spc.copy()
        # For each channel
        for i in range(nChan):
            spc_sub = spc_norm[i,:] - noise[i]  # only the signal power
            SPC_Samples[i] = spc_sub / (numpy.nansum(spc_sub) * delta_x)

        '''********************** FITTING MEAN SPC GAUSSIAN **********************'''

        """ the gaussian of the mean: first subtract noise, then normalize. this is legal because
            you only fit the curve and don't need the absolute value of height for calculation,
            only for estimation of width. for normalization of cross spectra, you need initial,
            unnormalized self-spectra With noise.

            Technically, you don't even need to normalize the self-spectra, as you only need the
            width of the peak. However, it was left this way. Note that the normalization has a flaw:
            due to subtraction of the noise, some values are below zero. Raw "spc" values should be
            >= 0, as it is the modulus squared of the signals (complex * it's conjugate)
        """
        # initial conditions
        popt = [1e-10,0,1e-10]
        # Spectra average
        SPCMean = numpy.average(SPC_Samples,0)
        # Moments in frequency
        SPCMoments = self.Moments(SPCMean[xvalid], xSamples_zoom)

        # Gauss Fit SPC in frequency domain
        if dbSNR > SNRlimit: # only if SNR > SNRth
            try:
                popt,pcov = curve_fit(self.gaus,xSamples_zoom,SPCMean[xvalid],p0=SPCMoments)
                if popt[2] <= 0 or popt[2] > widthlimit: # CONDITION
                    return self.StopWindEstimation(error_code = 1)
                FitGauss = self.gaus(xSamples_zoom,*popt)
            except :#RuntimeError:
                return self.StopWindEstimation(error_code = 2)
        else:
            return self.StopWindEstimation(error_code = 3)

        '''***************************** CSPC Normalization *************************
                The Spc spectra are used to normalize the crossspectra. Peaks from precipitation
                influence the norm which is not desired. First, a range is identified where the
                wind peak is estimated -> sum_wind is sum of those frequencies. Next, the area
                around it gets cut off and values replaced by mean determined by the boundary
                data -> sum_noise (spc is not normalized here, thats why the noise is important)

                The sums are then added and multiplied by range/datapoints, because you need
                an integral and not a sum for normalization.

                A norm is found according to Briggs 92.
        '''
        # for each pair
        for i in range(nPair):
            cspc_norm = cspc[i,:].copy()
            chan_index0 = pairsList[i][0]
            chan_index1 = pairsList[i][1]
            CSPC_Samples[i] = cspc_norm / (numpy.sqrt(numpy.nansum(spc_norm[chan_index0])*numpy.nansum(spc_norm[chan_index1])) * delta_x)
            phase[i] = numpy.arctan2(CSPC_Samples[i].imag, CSPC_Samples[i].real)

        CSPCmoments = numpy.vstack([self.Moments(numpy.abs(CSPC_Samples[0,xvalid]), xSamples_zoom),
                                    self.Moments(numpy.abs(CSPC_Samples[1,xvalid]), xSamples_zoom),
                                    self.Moments(numpy.abs(CSPC_Samples[2,xvalid]), xSamples_zoom)])

        popt01, popt02, popt12 = [1e-10,0,1e-10], [1e-10,0,1e-10] ,[1e-10,0,1e-10]
        FitGauss01, FitGauss02, FitGauss12 = numpy.zeros(len(xSamples)), numpy.zeros(len(xSamples)), numpy.zeros(len(xSamples))

        '''*******************************FIT GAUSS CSPC************************************'''
        try:
            popt01,pcov = curve_fit(self.gaus,xSamples_zoom,numpy.abs(CSPC_Samples[0][xvalid]),p0=CSPCmoments[0])
            if popt01[2] > widthlimit: # CONDITION
                return self.StopWindEstimation(error_code = 4)
            popt02,pcov = curve_fit(self.gaus,xSamples_zoom,numpy.abs(CSPC_Samples[1][xvalid]),p0=CSPCmoments[1])
            if popt02[2] > widthlimit: # CONDITION
                return self.StopWindEstimation(error_code = 4)
            popt12,pcov = curve_fit(self.gaus,xSamples_zoom,numpy.abs(CSPC_Samples[2][xvalid]),p0=CSPCmoments[2])
            if popt12[2] > widthlimit: # CONDITION
                return self.StopWindEstimation(error_code = 4)

            FitGauss01 = self.gaus(xSamples_zoom, *popt01)
            FitGauss02 = self.gaus(xSamples_zoom, *popt02)
            FitGauss12 = self.gaus(xSamples_zoom, *popt12)
        except:
            return self.StopWindEstimation(error_code = 5)


        '''************* Getting Fij ***************'''
        # x-axis point of the gaussian where the center is located from GaussFit of spectra
        GaussCenter = popt[1]
        ClosestCenter = xSamples_zoom[numpy.abs(xSamples_zoom-GaussCenter).argmin()]
        PointGauCenter = numpy.where(xSamples_zoom==ClosestCenter)[0][0]

        # Point where e^-1 is located in the gaussian
        PeMinus1 = numpy.max(FitGauss) * numpy.exp(-1)
        FijClosest = FitGauss[numpy.abs(FitGauss-PeMinus1).argmin()] # The closest point to"Peminus1" in "FitGauss"
        PointFij = numpy.where(FitGauss==FijClosest)[0][0]
        Fij = numpy.abs(xSamples_zoom[PointFij] - xSamples_zoom[PointGauCenter])

        '''********** Taking frequency ranges from mean SPCs **********'''
        GauWidth = popt[2] * 3/2        # Bandwidth of Gau01
        Range = numpy.empty(2)
        Range[0] = GaussCenter - GauWidth
        Range[1] = GaussCenter + GauWidth
        # Point in x-axis where the bandwidth is located (min:max)
        ClosRangeMin = xSamples_zoom[numpy.abs(xSamples_zoom-Range[0]).argmin()]
        ClosRangeMax = xSamples_zoom[numpy.abs(xSamples_zoom-Range[1]).argmin()]
        PointRangeMin = numpy.where(xSamples_zoom==ClosRangeMin)[0][0]
        PointRangeMax = numpy.where(xSamples_zoom==ClosRangeMax)[0][0]
        Range = numpy.array([ PointRangeMin, PointRangeMax ])
        FrecRange = xSamples_zoom[ Range[0] : Range[1] ]

        '''************************** Getting Phase Slope ***************************'''
        for i in range(nPair):
            if len(FrecRange) > 5:
                PhaseRange = phase[i, xvalid[0][Range[0]:Range[1]]].copy()
                mask = ~numpy.isnan(FrecRange) & ~numpy.isnan(PhaseRange)
                if len(FrecRange) == len(PhaseRange):
                    try:
                        slope, intercept, _, _, _ = stats.linregress(FrecRange[mask], self.AntiAliasing(PhaseRange[mask], 4.5))
                        PhaseSlope[i] = slope
                        PhaseInter[i] = intercept
                    except:
                        return self.StopWindEstimation(error_code = 6)
                else:
                    return self.StopWindEstimation(error_code = 7)
            else:
                return self.StopWindEstimation(error_code = 8)

        '''*** Constants A-H correspond to the convention as in Briggs and Vincent 1992 ***'''

        '''Getting constant C'''
        cC=(Fij*numpy.pi)**2

        '''****** Getting constants F and G ******'''
        MijEijNij = numpy.array([[Xi02,Eta02], [Xi12,Eta12]])
        # MijEijNij = numpy.array([[Xi01,Eta01], [Xi02,Eta02], [Xi12,Eta12]])
        # MijResult0 = (-PhaseSlope[0] * cC) / (2*numpy.pi)
        MijResult1 = (-PhaseSlope[1] * cC) / (2*numpy.pi)
        MijResult2 = (-PhaseSlope[2] * cC) / (2*numpy.pi)
        # MijResults = numpy.array([MijResult0, MijResult1, MijResult2])
        MijResults = numpy.array([MijResult1, MijResult2])
        (cF,cG) = numpy.linalg.solve(MijEijNij, MijResults)

        '''****** Getting constants A, B and H ******'''
        W01 = numpy.nanmax( FitGauss01 )
        W02 = numpy.nanmax( FitGauss02 )
        W12 = numpy.nanmax( FitGauss12 )

        WijResult01 = ((cF * Xi01 + cG * Eta01)**2)/cC - numpy.log(W01 / numpy.sqrt(numpy.pi / cC))
        WijResult02 = ((cF * Xi02 + cG * Eta02)**2)/cC - numpy.log(W02 / numpy.sqrt(numpy.pi / cC))
        WijResult12 = ((cF * Xi12 + cG * Eta12)**2)/cC - numpy.log(W12 / numpy.sqrt(numpy.pi / cC))
        WijResults = numpy.array([WijResult01, WijResult02, WijResult12])

        WijEijNij = numpy.array([ [Xi01**2, Eta01**2, 2*Xi01*Eta01] , [Xi02**2, Eta02**2, 2*Xi02*Eta02] , [Xi12**2, Eta12**2, 2*Xi12*Eta12] ])
        (cA,cB,cH) = numpy.linalg.solve(WijEijNij, WijResults)

        VxVy = numpy.array([[cA,cH],[cH,cB]])
        VxVyResults = numpy.array([-cF,-cG])
        (Vmer,Vzon) = numpy.linalg.solve(VxVy, VxVyResults)
        Vver =  -SPCMoments[1]*SPEED_OF_LIGHT/(2*radfreq)
        error_code = 0

        return Vzon, Vmer, Vver, error_code

class SpectralMoments(Operation):

    '''
        Function SpectralMoments()

        Calculates moments (power, mean, standard deviation) and SNR of the signal

        Type of dataIn:    Spectra

        Configuration Parameters:

            dirCosx    :     Cosine director in X axis
            dirCosy    :     Cosine director in Y axis

            elevation  :
            azimuth    :

        Input:
            channelList    :    simple channel list to select e.g. [2,3,7]
            self.dataOut.data_pre        :    Spectral data
            self.dataOut.abscissaList    :    List of frequencies
            self.dataOut.noise           :    Noise level per channel

        Affected:
            self.dataOut.moments        :    Parameters per channel
            self.dataOut.data_snr       :    SNR per channel

    '''

    def run(self, dataOut,wradar=False):

        data = dataOut.data_pre[0]
        absc = dataOut.abscissaList[:-1]
        noise = dataOut.noise
        nChannel = data.shape[0]
        data_param = numpy.zeros((nChannel, 4, data.shape[2]))

        for ind in range(nChannel):
            data_param[ind,:,:] = self.__calculateMoments( data[ind,:,:] , absc , noise[ind],wradar=wradar )

        dataOut.moments = data_param[:,1:,:]
        dataOut.data_snr = data_param[:,0]
        dataOut.data_pow = data_param[:,1]
        dataOut.data_dop = data_param[:,2]
        dataOut.data_width = data_param[:,3]
        return dataOut

    def __calculateMoments(self, oldspec, oldfreq, n0,
                           nicoh = None, graph = None, smooth = None, type1 = None, fwindow = None, snrth = None, dc = None, aliasing = None, oldfd = None, wwauto = None,wradar=None):

        if (nicoh is None): nicoh = 1
        if (graph is None): graph = 0
        if (smooth is None): smooth = 0
        elif (self.smooth < 3): smooth = 0

        if (type1 is None): type1 = 0
        if (fwindow is None): fwindow = numpy.zeros(oldfreq.size) + 1
        if (snrth is None): snrth = -3
        if (dc is None): dc = 0
        if (aliasing is None): aliasing = 0
        if (oldfd is None): oldfd = 0
        if (wwauto is None): wwauto = 0

        if (n0 < 1.e-20):   n0 = 1.e-20

        freq = oldfreq
        vec_power = numpy.zeros(oldspec.shape[1])
        vec_fd = numpy.zeros(oldspec.shape[1])
        vec_w = numpy.zeros(oldspec.shape[1])
        vec_snr = numpy.zeros(oldspec.shape[1])

        # oldspec = numpy.ma.masked_invalid(oldspec)
        for ind in range(oldspec.shape[1]):

            spec = oldspec[:,ind]
            aux = spec*fwindow
            max_spec = aux.max()
            m = aux.tolist().index(max_spec)

            # Smooth
            if (smooth == 0):
                spec2 = spec
            else:
                spec2 = scipy.ndimage.filters.uniform_filter1d(spec,size=smooth)

            # Moments Estimation
            bb = spec2[numpy.arange(m,spec2.size)]
            bb = (bb<n0).nonzero()
            bb = bb[0]

            ss = spec2[numpy.arange(0,m + 1)]
            ss = (ss<n0).nonzero()
            ss = ss[0]

            if (bb.size == 0):
                bb0 = spec.size - 1 - m
            else:
                bb0 = bb[0] - 1
                if (bb0 < 0):
                    bb0 = 0

            if (ss.size == 0):
                ss1 = 1
            else:
                ss1 = max(ss) + 1

            if (ss1 > m):
                ss1 = m

            #valid = numpy.arange(int(m + bb0 - ss1 + 1)) + ss1
            valid = numpy.arange(1,oldspec.shape[0])# valid perfil completo igual pulsepair
            signal_power = ((spec2[valid] - n0) * fwindow[valid]).mean()    # D. Scipión added with correct definition
            total_power = (spec2[valid] * fwindow[valid]).mean()            # D. Scipión added with correct definition
            power = ((spec2[valid] - n0) * fwindow[valid]).sum()
            fd = ((spec2[valid]- n0)*freq[valid] * fwindow[valid]).sum() / power
            w = numpy.sqrt(((spec2[valid] - n0)*fwindow[valid]*(freq[valid]- fd)**2).sum() / power)
            snr = (spec2.mean()-n0)/n0
            if (snr < 1.e-20) :
                snr = 1.e-20

            # vec_power[ind] = power    #D. Scipión replaced with the line below
            if wradar ==False:
                vec_power[ind] = total_power
            else:
                vec_power[ind] = signal_power

            vec_fd[ind] = fd
            vec_w[ind]  =  w
            vec_snr[ind] = snr
        return numpy.vstack((vec_snr, vec_power, vec_fd, vec_w))

    #------------------    Get SA Parameters    --------------------------

    def GetSAParameters(self):
        #SA en frecuencia
        pairslist = self.dataOut.groupList
        num_pairs = len(pairslist)

        vel = self.dataOut.abscissaList
        spectra = self.dataOut.data_pre
        cspectra = self.dataIn.data_cspc
        delta_v = vel[1] - vel[0]

        #Calculating the power spectrum
        spc_pow = numpy.sum(spectra, 3)*delta_v
        #Normalizing Spectra
        norm_spectra = spectra/spc_pow
        #Calculating the norm_spectra at peak
        max_spectra = numpy.max(norm_spectra, 3)

        #Normalizing Cross Spectra
        norm_cspectra = numpy.zeros(cspectra.shape)

        for i in range(num_chan):
            norm_cspectra[i,:,:] = cspectra[i,:,:]/numpy.sqrt(spc_pow[pairslist[i][0],:]*spc_pow[pairslist[i][1],:])

        max_cspectra = numpy.max(norm_cspectra,2)
        max_cspectra_index = numpy.argmax(norm_cspectra, 2)

        for i in range(num_pairs):
            cspc_par[i,:,:] = __calculateMoments(norm_cspectra)
    #-------------------    Get Lags    ----------------------------------

class SALags(Operation):
    '''
    Function GetMoments()

    Input:
        self.dataOut.data_pre
        self.dataOut.abscissaList
        self.dataOut.noise
        self.dataOut.normFactor
        self.dataOut.data_snr
        self.dataOut.groupList
        self.dataOut.nChannels

    Affected:
        self.dataOut.data_param

    '''
    def run(self, dataOut):
        data_acf = dataOut.data_pre[0]
        data_ccf = dataOut.data_pre[1]
        normFactor_acf = dataOut.normFactor[0]
        normFactor_ccf = dataOut.normFactor[1]
        pairs_acf = dataOut.groupList[0]
        pairs_ccf = dataOut.groupList[1]

        nHeights = dataOut.nHeights
        absc = dataOut.abscissaList
        noise = dataOut.noise
        SNR = dataOut.data_snr
        nChannels = dataOut.nChannels
#         pairsList = dataOut.groupList
#         pairsAutoCorr, pairsCrossCorr = self.__getPairsAutoCorr(pairsList, nChannels)

        for l in range(len(pairs_acf)):
            data_acf[l,:,:] = data_acf[l,:,:]/normFactor_acf[l,:]

        for l in range(len(pairs_ccf)):
            data_ccf[l,:,:] = data_ccf[l,:,:]/normFactor_ccf[l,:]

        dataOut.data_param = numpy.zeros((len(pairs_ccf)*2 + 1, nHeights))
        dataOut.data_param[:-1,:] = self.__calculateTaus(data_acf, data_ccf, absc)
        dataOut.data_param[-1,:] = self.__calculateLag1Phase(data_acf, absc)
        return

#     def __getPairsAutoCorr(self, pairsList, nChannels):
#
#         pairsAutoCorr = numpy.zeros(nChannels, dtype = 'int')*numpy.nan
#
#         for l in range(len(pairsList)):
#             firstChannel = pairsList[l][0]
#             secondChannel = pairsList[l][1]
#
#             #Obteniendo pares de Autocorrelacion
#             if firstChannel == secondChannel:
#                 pairsAutoCorr[firstChannel] = int(l)
#
#         pairsAutoCorr = pairsAutoCorr.astype(int)
#
#         pairsCrossCorr = range(len(pairsList))
#         pairsCrossCorr = numpy.delete(pairsCrossCorr,pairsAutoCorr)
#
#         return pairsAutoCorr, pairsCrossCorr

    def __calculateTaus(self, data_acf, data_ccf, lagRange):

        lag0 = data_acf.shape[1]/2
        #Funcion de Autocorrelacion
        mean_acf = stats.nanmean(data_acf, axis = 0)

        #Obtencion Indice de TauCross
        ind_ccf = data_ccf.argmax(axis = 1)
        #Obtencion Indice de TauAuto
        ind_acf = numpy.zeros(ind_ccf.shape,dtype = 'int')
        ccf_lag0 = data_ccf[:,lag0,:]

        for i in range(ccf_lag0.shape[0]):
            ind_acf[i,:] = numpy.abs(mean_acf - ccf_lag0[i,:]).argmin(axis = 0)

        #Obtencion de TauCross y TauAuto
        tau_ccf = lagRange[ind_ccf]
        tau_acf  = lagRange[ind_acf]

        Nan1, Nan2 = numpy.where(tau_ccf == lagRange[0])

        tau_ccf[Nan1,Nan2] = numpy.nan
        tau_acf[Nan1,Nan2] = numpy.nan
        tau = numpy.vstack((tau_ccf,tau_acf))

        return tau

    def __calculateLag1Phase(self, data, lagTRange):
        data1 = stats.nanmean(data, axis = 0)
        lag1 = numpy.where(lagTRange == 0)[0][0] + 1

        phase = numpy.angle(data1[lag1,:])

        return phase

class SpectralFitting(Operation):
    '''
        Function GetMoments()

        Input:
        Output:
        Variables modified:
    '''

    def run(self, dataOut, getSNR = True, path=None, file=None, groupList=None):


        if path != None:
            sys.path.append(path)
        self.dataOut.library = importlib.import_module(file)

        #To be inserted as a parameter
        groupArray = numpy.array(groupList)
#         groupArray = numpy.array([[0,1],[2,3]])
        self.dataOut.groupList = groupArray

        nGroups = groupArray.shape[0]
        nChannels = self.dataIn.nChannels
        nHeights=self.dataIn.heightList.size

        #Parameters Array
        self.dataOut.data_param = None

        #Set constants
        constants = self.dataOut.library.setConstants(self.dataIn)
        self.dataOut.constants = constants
        M = self.dataIn.normFactor
        N = self.dataIn.nFFTPoints
        ippSeconds = self.dataIn.ippSeconds
        K = self.dataIn.nIncohInt
        pairsArray = numpy.array(self.dataIn.pairsList)

        #List of possible combinations
        listComb = itertools.combinations(numpy.arange(groupArray.shape[1]),2)
        indCross = numpy.zeros(len(list(listComb)), dtype = 'int')

        if getSNR:
            listChannels = groupArray.reshape((groupArray.size))
            listChannels.sort()
            noise = self.dataIn.getNoise()
            self.dataOut.data_snr = self.__getSNR(self.dataIn.data_spc[listChannels,:,:], noise[listChannels])

        for i in range(nGroups):
            coord = groupArray[i,:]

            #Input data array
            data = self.dataIn.data_spc[coord,:,:]/(M*N)
            data = data.reshape((data.shape[0]*data.shape[1],data.shape[2]))

            #Cross Spectra data array for Covariance Matrixes
            ind = 0
            for pairs in listComb:
                pairsSel = numpy.array([coord[x],coord[y]])
                indCross[ind] = int(numpy.where(numpy.all(pairsArray == pairsSel, axis = 1))[0][0])
                ind += 1
            dataCross = self.dataIn.data_cspc[indCross,:,:]/(M*N)
            dataCross = dataCross**2/K

            for h in range(nHeights):

                #Input
                d = data[:,h]

                #Covariance Matrix
                D = numpy.diag(d**2/K)
                ind = 0
                for pairs in listComb:
                    #Coordinates in Covariance Matrix
                    x = pairs[0]
                    y = pairs[1]
                    #Channel Index
                    S12 = dataCross[ind,:,h]
                    D12 = numpy.diag(S12)
                    #Completing Covariance Matrix with Cross Spectras
                    D[x*N:(x+1)*N,y*N:(y+1)*N] = D12
                    D[y*N:(y+1)*N,x*N:(x+1)*N] = D12
                    ind += 1
                Dinv=numpy.linalg.inv(D)
                L=numpy.linalg.cholesky(Dinv)
                LT=L.T

                dp = numpy.dot(LT,d)

                #Initial values
                data_spc = self.dataIn.data_spc[coord,:,h]

                if (h>0)and(error1[3]<5):
                    p0 = self.dataOut.data_param[i,:,h-1]
                else:
                    p0 = numpy.array(self.dataOut.library.initialValuesFunction(data_spc, constants, i))

                try:
                    #Least Squares
                    minp,covp,infodict,mesg,ier = optimize.leastsq(self.__residFunction,p0,args=(dp,LT,constants),full_output=True)
#                   minp,covp = optimize.leastsq(self.__residFunction,p0,args=(dp,LT,constants))
                    #Chi square error
                    error0 = numpy.sum(infodict['fvec']**2)/(2*N)
                    #Error with Jacobian
                    error1 = self.dataOut.library.errorFunction(minp,constants,LT)
                except:
                    minp = p0*numpy.nan
                    error0 = numpy.nan
                    error1 = p0*numpy.nan

                #Save
                if self.dataOut.data_param is None:
                    self.dataOut.data_param = numpy.zeros((nGroups, p0.size, nHeights))*numpy.nan
                    self.dataOut.data_error = numpy.zeros((nGroups, p0.size + 1, nHeights))*numpy.nan

                self.dataOut.data_error[i,:,h] = numpy.hstack((error0,error1))
                self.dataOut.data_param[i,:,h] = minp
        return

    def __residFunction(self, p, dp, LT, constants):

        fm = self.dataOut.library.modelFunction(p, constants)
        fmp=numpy.dot(LT,fm)

        return  dp-fmp

    def __getSNR(self, z, noise):

        avg = numpy.average(z, axis=1)
        SNR = (avg.T-noise)/noise
        SNR = SNR.T
        return SNR

    def __chisq(p,chindex,hindex):
        #similar to Resid but calculates CHI**2
        [LT,d,fm]=setupLTdfm(p,chindex,hindex)
        dp=numpy.dot(LT,d)
        fmp=numpy.dot(LT,fm)
        chisq=numpy.dot((dp-fmp).T,(dp-fmp))
        return chisq

class WindProfiler(Operation):

    __isConfig = False

    __initime = None
    __lastdatatime = None
    __integrationtime = None

    __buffer = None

    __dataReady = False

    __firstdata = None

    n = None

    def __init__(self):
        Operation.__init__(self)

    def __calculateCosDir(self, elev, azim):
        zen = (90 - elev)*numpy.pi/180
        azim = azim*numpy.pi/180
        cosDirX = numpy.sqrt((1-numpy.cos(zen)**2)/((1+numpy.tan(azim)**2)))
        cosDirY = numpy.sqrt(1-numpy.cos(zen)**2-cosDirX**2)

        signX = numpy.sign(numpy.cos(azim))
        signY = numpy.sign(numpy.sin(azim))

        cosDirX = numpy.copysign(cosDirX, signX)
        cosDirY = numpy.copysign(cosDirY, signY)
        return cosDirX, cosDirY

    def __calculateAngles(self, theta_x, theta_y, azimuth):

        dir_cosw = numpy.sqrt(1-theta_x**2-theta_y**2)
        zenith_arr = numpy.arccos(dir_cosw)
        azimuth_arr = numpy.arctan2(theta_x,theta_y) + azimuth*math.pi/180

        dir_cosu = numpy.sin(azimuth_arr)*numpy.sin(zenith_arr)
        dir_cosv = numpy.cos(azimuth_arr)*numpy.sin(zenith_arr)

        return azimuth_arr, zenith_arr, dir_cosu, dir_cosv, dir_cosw

    def __calculateMatA(self, dir_cosu, dir_cosv, dir_cosw, horOnly):

#
        if horOnly:
            A = numpy.c_[dir_cosu,dir_cosv]
        else:
            A = numpy.c_[dir_cosu,dir_cosv,dir_cosw]
        A = numpy.asmatrix(A)
        A1 = numpy.linalg.inv(A.transpose()*A)*A.transpose()

        return A1

    def __correctValues(self, heiRang, phi, velRadial, SNR):
        listPhi = phi.tolist()
        maxid = listPhi.index(max(listPhi))
        minid = listPhi.index(min(listPhi))

        rango = list(range(len(phi)))
   #     rango = numpy.delete(rango,maxid)

        heiRang1 = heiRang*math.cos(phi[maxid])
        heiRangAux = heiRang*math.cos(phi[minid])
        indOut = (heiRang1 < heiRangAux[0]).nonzero()
        heiRang1 = numpy.delete(heiRang1,indOut)

        velRadial1 = numpy.zeros([len(phi),len(heiRang1)])
        SNR1 = numpy.zeros([len(phi),len(heiRang1)])

        for i in rango:
            x = heiRang*math.cos(phi[i])
            y1 = velRadial[i,:]
            f1 = interpolate.interp1d(x,y1,kind = 'cubic')

            x1 = heiRang1
            y11 = f1(x1)

            y2 = SNR[i,:]
            f2 = interpolate.interp1d(x,y2,kind = 'cubic')
            y21 = f2(x1)

            velRadial1[i,:] = y11
            SNR1[i,:] = y21

        return heiRang1, velRadial1, SNR1

    def __calculateVelUVW(self, A, velRadial):

        #Operacion Matricial
#         velUVW = numpy.zeros((velRadial.shape[1],3))
#         for ind in range(velRadial.shape[1]):
#             velUVW[ind,:] = numpy.dot(A,velRadial[:,ind])
#         velUVW = velUVW.transpose()
        velUVW = numpy.zeros((A.shape[0],velRadial.shape[1]))
        velUVW[:,:] = numpy.dot(A,velRadial)


        return velUVW

#     def techniqueDBS(self, velRadial0, dirCosx, disrCosy, azimuth, correct, horizontalOnly, heiRang, SNR0):

    def techniqueDBS(self, kwargs):
        """
        Function that implements Doppler Beam Swinging (DBS) technique.

        Input:    Radial velocities, Direction cosines (x and y) of the Beam, Antenna azimuth,
                    Direction correction (if necessary), Ranges and SNR

        Output:    Winds estimation (Zonal, Meridional and Vertical)

        Parameters affected:    Winds, height range, SNR
        """
        velRadial0 = kwargs['velRadial']
        heiRang = kwargs['heightList']
        SNR0 = kwargs['SNR']

        if 'dirCosx' in kwargs and 'dirCosy' in kwargs:
            theta_x = numpy.array(kwargs['dirCosx'])
            theta_y = numpy.array(kwargs['dirCosy'])
        else:
            elev = numpy.array(kwargs['elevation'])
            azim = numpy.array(kwargs['azimuth'])
            theta_x, theta_y = self.__calculateCosDir(elev, azim)
        azimuth = kwargs['correctAzimuth']
        if 'horizontalOnly' in kwargs:
            horizontalOnly = kwargs['horizontalOnly']
        else:   horizontalOnly = False
        if 'correctFactor' in kwargs:
            correctFactor = kwargs['correctFactor']
        else:   correctFactor = 1
        if 'channelList' in kwargs:
            channelList = kwargs['channelList']
            if len(channelList) == 2:
                horizontalOnly = True
            arrayChannel = numpy.array(channelList)
            param = param[arrayChannel,:,:]
            theta_x = theta_x[arrayChannel]
            theta_y = theta_y[arrayChannel]

        azimuth_arr, zenith_arr, dir_cosu, dir_cosv, dir_cosw = self.__calculateAngles(theta_x, theta_y, azimuth)
        heiRang1, velRadial1, SNR1 = self.__correctValues(heiRang, zenith_arr, correctFactor*velRadial0, SNR0)
        A = self.__calculateMatA(dir_cosu, dir_cosv, dir_cosw, horizontalOnly)

        #Calculo de Componentes de la velocidad con DBS
        winds = self.__calculateVelUVW(A,velRadial1)

        return winds, heiRang1, SNR1

    def __calculateDistance(self, posx, posy, pairs_ccf, azimuth = None):

        nPairs = len(pairs_ccf)
        posx = numpy.asarray(posx)
        posy = numpy.asarray(posy)

        #Rotacion Inversa para alinear con el azimuth
        if azimuth!= None:
            azimuth = azimuth*math.pi/180
            posx1 = posx*math.cos(azimuth) + posy*math.sin(azimuth)
            posy1 = -posx*math.sin(azimuth) + posy*math.cos(azimuth)
        else:
            posx1 = posx
            posy1 = posy

        #Calculo de Distancias
        distx = numpy.zeros(nPairs)
        disty = numpy.zeros(nPairs)
        dist = numpy.zeros(nPairs)
        ang = numpy.zeros(nPairs)

        for i in range(nPairs):
            distx[i] = posx1[pairs_ccf[i][1]] - posx1[pairs_ccf[i][0]]
            disty[i] = posy1[pairs_ccf[i][1]] - posy1[pairs_ccf[i][0]]
            dist[i] = numpy.sqrt(distx[i]**2 + disty[i]**2)
            ang[i] = numpy.arctan2(disty[i],distx[i])

        return distx, disty, dist, ang
        #Calculo de Matrices
#         nPairs = len(pairs)
#         ang1 = numpy.zeros((nPairs, 2, 1))
#         dist1 = numpy.zeros((nPairs, 2, 1))
#
#         for j in range(nPairs):
#             dist1[j,0,0] = dist[pairs[j][0]]
#             dist1[j,1,0] = dist[pairs[j][1]]
#             ang1[j,0,0] = ang[pairs[j][0]]
#             ang1[j,1,0] = ang[pairs[j][1]]
#
#         return distx,disty, dist1,ang1


    def __calculateVelVer(self, phase, lagTRange, _lambda):

        Ts = lagTRange[1] - lagTRange[0]
        velW = -_lambda*phase/(4*math.pi*Ts)

        return velW

    def __calculateVelHorDir(self, dist, tau1, tau2, ang):
        nPairs = tau1.shape[0]
        nHeights = tau1.shape[1]
        vel = numpy.zeros((nPairs,3,nHeights))
        dist1 = numpy.reshape(dist, (dist.size,1))

        angCos = numpy.cos(ang)
        angSin = numpy.sin(ang)

        vel0 = dist1*tau1/(2*tau2**2)
        vel[:,0,:] = (vel0*angCos).sum(axis = 1)
        vel[:,1,:] = (vel0*angSin).sum(axis = 1)

        ind = numpy.where(numpy.isinf(vel))
        vel[ind] = numpy.nan

        return vel

#     def __getPairsAutoCorr(self, pairsList, nChannels):
#
#         pairsAutoCorr = numpy.zeros(nChannels, dtype = 'int')*numpy.nan
#
#         for l in range(len(pairsList)):
#             firstChannel = pairsList[l][0]
#             secondChannel = pairsList[l][1]
#
#             #Obteniendo pares de Autocorrelacion
#             if firstChannel == secondChannel:
#                 pairsAutoCorr[firstChannel] = int(l)
#
#         pairsAutoCorr = pairsAutoCorr.astype(int)
#
#         pairsCrossCorr = range(len(pairsList))
#         pairsCrossCorr = numpy.delete(pairsCrossCorr,pairsAutoCorr)
#
#         return pairsAutoCorr, pairsCrossCorr

#     def techniqueSA(self, pairsSelected, pairsList, nChannels, tau, azimuth, _lambda, position_x, position_y, lagTRange, correctFactor):
    def techniqueSA(self, kwargs):

        """
        Function that implements Spaced Antenna (SA) technique.

        Input:    Radial velocities, Direction cosines (x and y) of the Beam, Antenna azimuth,
                    Direction correction (if necessary), Ranges and SNR

        Output:    Winds estimation (Zonal, Meridional and Vertical)

        Parameters affected:    Winds
        """
        position_x = kwargs['positionX']
        position_y = kwargs['positionY']
        azimuth = kwargs['azimuth']

        if 'correctFactor' in kwargs:
            correctFactor = kwargs['correctFactor']
        else:
            correctFactor = 1

        groupList = kwargs['groupList']
        pairs_ccf = groupList[1]
        tau = kwargs['tau']
        _lambda = kwargs['_lambda']

        #Cross Correlation pairs obtained
#         pairsAutoCorr, pairsCrossCorr = self.__getPairsAutoCorr(pairssList, nChannels)
#         pairsArray = numpy.array(pairsList)[pairsCrossCorr]
#         pairsSelArray = numpy.array(pairsSelected)
#         pairs = []
#
#         #Wind estimation pairs obtained
#         for i in range(pairsSelArray.shape[0]/2):
#             ind1 = numpy.where(numpy.all(pairsArray == pairsSelArray[2*i], axis = 1))[0][0]
#             ind2 = numpy.where(numpy.all(pairsArray == pairsSelArray[2*i + 1], axis = 1))[0][0]
#             pairs.append((ind1,ind2))

        indtau = tau.shape[0]/2
        tau1 = tau[:indtau,:]
        tau2 = tau[indtau:-1,:]
#         tau1 = tau1[pairs,:]
#         tau2 = tau2[pairs,:]
        phase1 = tau[-1,:]

        #---------------------------------------------------------------------
        #Metodo Directo
        distx, disty, dist, ang = self.__calculateDistance(position_x, position_y, pairs_ccf,azimuth)
        winds = self.__calculateVelHorDir(dist, tau1, tau2, ang)
        winds = stats.nanmean(winds, axis=0)
        #---------------------------------------------------------------------
        #Metodo General
#         distx, disty, dist = self.calculateDistance(position_x,position_y,pairsCrossCorr, pairsList, azimuth)
#         #Calculo Coeficientes de Funcion de Correlacion
#         F,G,A,B,H = self.calculateCoef(tau1,tau2,distx,disty,n)
#         #Calculo de Velocidades
#         winds = self.calculateVelUV(F,G,A,B,H)

        #---------------------------------------------------------------------
        winds[2,:] = self.__calculateVelVer(phase1, lagTRange, _lambda)
        winds = correctFactor*winds
        return winds

    def __checkTime(self, currentTime, paramInterval, outputInterval):

        dataTime = currentTime + paramInterval
        deltaTime = dataTime - self.__initime

        if deltaTime >= outputInterval or deltaTime < 0:
            self.__dataReady = True
        return

    def techniqueMeteors(self, arrayMeteor, meteorThresh, heightMin, heightMax):
        '''
        Function that implements winds estimation technique with detected meteors.

        Input:    Detected meteors, Minimum meteor quantity to wind estimation

        Output:    Winds estimation (Zonal and Meridional)

        Parameters affected:    Winds
        '''
        #Settings
        nInt = (heightMax - heightMin)/2
        nInt = int(nInt)
        winds = numpy.zeros((2,nInt))*numpy.nan

        #Filter errors
        error = numpy.where(arrayMeteor[:,-1] == 0)[0]
        finalMeteor = arrayMeteor[error,:]

        #Meteor Histogram
        finalHeights = finalMeteor[:,2]
        hist = numpy.histogram(finalHeights, bins = nInt, range = (heightMin,heightMax))
        nMeteorsPerI = hist[0]
        heightPerI = hist[1]

        #Sort of meteors
        indSort = finalHeights.argsort()
        finalMeteor2 = finalMeteor[indSort,:]

        #    Calculating winds
        ind1 = 0
        ind2 = 0

        for i in range(nInt):
            nMet = nMeteorsPerI[i]
            ind1 = ind2
            ind2 = ind1 + nMet

            meteorAux = finalMeteor2[ind1:ind2,:]

            if meteorAux.shape[0] >= meteorThresh:
                vel = meteorAux[:, 6]
                zen = meteorAux[:, 4]*numpy.pi/180
                azim = meteorAux[:, 3]*numpy.pi/180

                n = numpy.cos(zen)
        #         m = (1 - n**2)/(1 - numpy.tan(azim)**2)
        #         l = m*numpy.tan(azim)
                l = numpy.sin(zen)*numpy.sin(azim)
                m = numpy.sin(zen)*numpy.cos(azim)

                A = numpy.vstack((l, m)).transpose()
                A1 = numpy.dot(numpy.linalg.inv( numpy.dot(A.transpose(),A) ),A.transpose())
                windsAux = numpy.dot(A1, vel)

                winds[0,i] = windsAux[0]
                winds[1,i] = windsAux[1]

        return winds, heightPerI[:-1]

    def techniqueNSM_SA(self, **kwargs):
        metArray = kwargs['metArray']
        heightList = kwargs['heightList']
        timeList = kwargs['timeList']

        rx_location = kwargs['rx_location']
        groupList = kwargs['groupList']
        azimuth = kwargs['azimuth']
        dfactor = kwargs['dfactor']
        k = kwargs['k']

        azimuth1, dist = self.__calculateAzimuth1(rx_location, groupList, azimuth)
        d = dist*dfactor
        #Phase calculation
        metArray1 = self.__getPhaseSlope(metArray, heightList, timeList)

        metArray1[:,-2] = metArray1[:,-2]*metArray1[:,2]*1000/(k*d[metArray1[:,1].astype(int)]) #angles into velocities

        velEst = numpy.zeros((heightList.size,2))*numpy.nan
        azimuth1 = azimuth1*numpy.pi/180

        for i in range(heightList.size):
            h = heightList[i]
            indH = numpy.where((metArray1[:,2] == h)&(numpy.abs(metArray1[:,-2]) < 100))[0]
            metHeight = metArray1[indH,:]
            if metHeight.shape[0] >= 2:
                velAux = numpy.asmatrix(metHeight[:,-2]).T    #Radial Velocities
                iazim = metHeight[:,1].astype(int)
                azimAux = numpy.asmatrix(azimuth1[iazim]).T    #Azimuths
                A = numpy.hstack((numpy.cos(azimAux),numpy.sin(azimAux)))
                A = numpy.asmatrix(A)
                A1 = numpy.linalg.pinv(A.transpose()*A)*A.transpose()
                velHor = numpy.dot(A1,velAux)

                velEst[i,:] = numpy.squeeze(velHor)
        return velEst

    def __getPhaseSlope(self, metArray, heightList, timeList):
        meteorList = []
        #utctime sec1 height SNR velRad ph0 ph1 ph2 coh0 coh1 coh2
        #Putting back together the meteor matrix
        utctime = metArray[:,0]
        uniqueTime = numpy.unique(utctime)

        phaseDerThresh = 0.5
        ippSeconds = timeList[1] - timeList[0]
        sec = numpy.where(timeList>1)[0][0]
        nPairs = metArray.shape[1] - 6
        nHeights = len(heightList)

        for t in uniqueTime:
            metArray1 = metArray[utctime==t,:]
#         phaseDerThresh = numpy.pi/4 #reducir Phase thresh
            tmet = metArray1[:,1].astype(int)
            hmet = metArray1[:,2].astype(int)

            metPhase = numpy.zeros((nPairs, heightList.size, timeList.size - 1))
            metPhase[:,:] = numpy.nan
            metPhase[:,hmet,tmet] = metArray1[:,6:].T

            #Delete short trails
            metBool = ~numpy.isnan(metPhase[0,:,:])
            heightVect = numpy.sum(metBool, axis = 1)
            metBool[heightVect<sec,:] = False
            metPhase[:,heightVect<sec,:] = numpy.nan

            #Derivative
            metDer = numpy.abs(metPhase[:,:,1:] - metPhase[:,:,:-1])
            phDerAux = numpy.dstack((numpy.full((nPairs,nHeights,1), False, dtype=bool),metDer > phaseDerThresh))
            metPhase[phDerAux] = numpy.nan

            #--------------------------METEOR DETECTION    -----------------------------------------
            indMet = numpy.where(numpy.any(metBool,axis=1))[0]

            for p in numpy.arange(nPairs):
                phase = metPhase[p,:,:]
                phDer = metDer[p,:,:]

                for h in indMet:
                    height = heightList[h]
                    phase1 = phase[h,:] #82
                    phDer1 = phDer[h,:]

                    phase1[~numpy.isnan(phase1)] = numpy.unwrap(phase1[~numpy.isnan(phase1)])   #Unwrap

                    indValid = numpy.where(~numpy.isnan(phase1))[0]
                    initMet = indValid[0]
                    endMet = 0

                    for i in range(len(indValid)-1):

                        #Time difference
                        inow = indValid[i]
                        inext = indValid[i+1]
                        idiff = inext - inow
                        #Phase difference
                        phDiff = numpy.abs(phase1[inext] - phase1[inow])

                        if idiff>sec or phDiff>numpy.pi/4 or inext==indValid[-1]:   #End of Meteor
                            sizeTrail = inow - initMet + 1
                            if sizeTrail>3*sec:  #Too short meteors
                                x = numpy.arange(initMet,inow+1)*ippSeconds
                                y = phase1[initMet:inow+1]
                                ynnan = ~numpy.isnan(y)
                                x = x[ynnan]
                                y = y[ynnan]
                                slope, intercept, r_value, p_value, std_err = stats.linregress(x,y)
                                ylin = x*slope + intercept
                                rsq = r_value**2
                                if rsq > 0.5:
                                    vel = slope#*height*1000/(k*d)
                                    estAux = numpy.array([utctime,p,height, vel, rsq])
                                    meteorList.append(estAux)
                            initMet = inext
        metArray2 = numpy.array(meteorList)

        return metArray2

    def __calculateAzimuth1(self, rx_location, pairslist, azimuth0):

        azimuth1 = numpy.zeros(len(pairslist))
        dist = numpy.zeros(len(pairslist))

        for i in range(len(rx_location)):
            ch0 = pairslist[i][0]
            ch1 = pairslist[i][1]

            diffX = rx_location[ch0][0] - rx_location[ch1][0]
            diffY = rx_location[ch0][1] - rx_location[ch1][1]
            azimuth1[i] = numpy.arctan2(diffY,diffX)*180/numpy.pi
            dist[i] = numpy.sqrt(diffX**2 + diffY**2)

        azimuth1 -= azimuth0
        return azimuth1, dist

    def techniqueNSM_DBS(self, **kwargs):
        metArray = kwargs['metArray']
        heightList = kwargs['heightList']
        timeList = kwargs['timeList']
        azimuth = kwargs['azimuth']
        theta_x = numpy.array(kwargs['theta_x'])
        theta_y = numpy.array(kwargs['theta_y'])

        utctime = metArray[:,0]
        cmet = metArray[:,1].astype(int)
        hmet = metArray[:,3].astype(int)
        SNRmet = metArray[:,4]
        vmet = metArray[:,5]
        spcmet = metArray[:,6]

        nChan = numpy.max(cmet) + 1
        nHeights = len(heightList)

        azimuth_arr, zenith_arr, dir_cosu, dir_cosv, dir_cosw = self.__calculateAngles(theta_x, theta_y, azimuth)
        hmet = heightList[hmet]
        h1met = hmet*numpy.cos(zenith_arr[cmet])      #Corrected heights

        velEst = numpy.zeros((heightList.size,2))*numpy.nan

        for i in range(nHeights - 1):
            hmin = heightList[i]
            hmax = heightList[i + 1]

            thisH = (h1met>=hmin) & (h1met<hmax) & (cmet!=2) & (SNRmet>8) & (vmet<50) & (spcmet<10)
            indthisH = numpy.where(thisH)

            if numpy.size(indthisH) > 3:

                vel_aux = vmet[thisH]
                chan_aux = cmet[thisH]
                cosu_aux = dir_cosu[chan_aux]
                cosv_aux = dir_cosv[chan_aux]
                cosw_aux = dir_cosw[chan_aux]

                nch = numpy.size(numpy.unique(chan_aux))
                if  nch > 1:
                    A = self.__calculateMatA(cosu_aux, cosv_aux, cosw_aux, True)
                    velEst[i,:] = numpy.dot(A,vel_aux)

        return velEst

    def run(self, dataOut, technique, nHours=1, hmin=70, hmax=110, **kwargs):

        param = dataOut.data_param
        if dataOut.abscissaList != None:
            absc = dataOut.abscissaList[:-1]
        # noise = dataOut.noise
        heightList = dataOut.heightList
        SNR = dataOut.data_snr

        if technique == 'DBS':

            kwargs['velRadial'] = param[:,1,:] #Radial velocity
            kwargs['heightList'] = heightList
            kwargs['SNR'] = SNR

            dataOut.data_output, dataOut.heightList, dataOut.data_snr = self.techniqueDBS(kwargs) #DBS Function
            dataOut.utctimeInit = dataOut.utctime
            dataOut.outputInterval = dataOut.paramInterval

        elif technique == 'SA':

            #Parameters
#             position_x = kwargs['positionX']
#             position_y = kwargs['positionY']
#             azimuth = kwargs['azimuth']
#
#             if kwargs.has_key('crosspairsList'):
#                 pairs = kwargs['crosspairsList']
#             else:
#                 pairs = None
#
#             if kwargs.has_key('correctFactor'):
#                 correctFactor = kwargs['correctFactor']
#             else:
#                 correctFactor = 1

#             tau = dataOut.data_param
#             _lambda = dataOut.C/dataOut.frequency
#             pairsList = dataOut.groupList
#             nChannels = dataOut.nChannels

            kwargs['groupList'] = dataOut.groupList
            kwargs['tau'] = dataOut.data_param
            kwargs['_lambda'] = dataOut.C/dataOut.frequency
#             dataOut.data_output = self.techniqueSA(pairs, pairsList, nChannels, tau, azimuth, _lambda, position_x, position_y, absc, correctFactor)
            dataOut.data_output = self.techniqueSA(kwargs)
            dataOut.utctimeInit = dataOut.utctime
            dataOut.outputInterval = dataOut.timeInterval

        elif technique == 'Meteors':
            dataOut.flagNoData = True
            self.__dataReady = False

            if 'nHours' in kwargs:
                nHours = kwargs['nHours']
            else:
                nHours = 1

            if 'meteorsPerBin' in kwargs:
                meteorThresh = kwargs['meteorsPerBin']
            else:
                meteorThresh = 6

            if 'hmin' in kwargs:
                hmin = kwargs['hmin']
            else:   hmin = 70
            if 'hmax' in kwargs:
                hmax = kwargs['hmax']
            else:   hmax = 110

            dataOut.outputInterval = nHours*3600

            if self.__isConfig == False:
#                 self.__initime = dataOut.datatime.replace(minute = 0, second = 0, microsecond = 03)
                #Get Initial LTC time
                self.__initime = datetime.datetime.utcfromtimestamp(dataOut.utctime)
                self.__initime = (self.__initime.replace(minute = 0, second = 0, microsecond = 0) - datetime.datetime(1970, 1, 1)).total_seconds()

                self.__isConfig = True

            if self.__buffer is None:
                self.__buffer = dataOut.data_param
                self.__firstdata = copy.copy(dataOut)

            else:
                self.__buffer = numpy.vstack((self.__buffer, dataOut.data_param))

            self.__checkTime(dataOut.utctime, dataOut.paramInterval, dataOut.outputInterval) #Check if the buffer is ready

            if self.__dataReady:
                dataOut.utctimeInit = self.__initime

                self.__initime += dataOut.outputInterval #to erase time offset

                dataOut.data_output, dataOut.heightList = self.techniqueMeteors(self.__buffer, meteorThresh, hmin, hmax)
                dataOut.flagNoData = False
                self.__buffer = None

        elif technique == 'Meteors1':
            dataOut.flagNoData = True
            self.__dataReady = False

            if 'nMins' in kwargs:
                nMins = kwargs['nMins']
            else: nMins = 20
            if 'rx_location' in kwargs:
                rx_location = kwargs['rx_location']
            else: rx_location = [(0,1),(1,1),(1,0)]
            if 'azimuth' in kwargs:
                azimuth = kwargs['azimuth']
            else: azimuth = 51.06
            if 'dfactor' in kwargs:
                dfactor = kwargs['dfactor']
            if 'mode' in kwargs:
                mode = kwargs['mode']
            if 'theta_x' in kwargs:
                theta_x = kwargs['theta_x']
            if 'theta_y' in kwargs:
                theta_y = kwargs['theta_y']
            else: mode = 'SA'

            #Borrar luego esto
            if dataOut.groupList is None:
                dataOut.groupList = [(0,1),(0,2),(1,2)]
            groupList = dataOut.groupList
            C = 3e8
            freq = 50e6
            lamb = C/freq
            k = 2*numpy.pi/lamb

            timeList = dataOut.abscissaList
            heightList = dataOut.heightList

            if self.__isConfig == False:
                dataOut.outputInterval = nMins*60
#                 self.__initime = dataOut.datatime.replace(minute = 0, second = 0, microsecond = 03)
                #Get Initial LTC time
                initime = datetime.datetime.utcfromtimestamp(dataOut.utctime)
                minuteAux = initime.minute
                minuteNew = int(numpy.floor(minuteAux/nMins)*nMins)
                self.__initime = (initime.replace(minute = minuteNew, second = 0, microsecond = 0) - datetime.datetime(1970, 1, 1)).total_seconds()

                self.__isConfig = True

            if self.__buffer is None:
                self.__buffer = dataOut.data_param
                self.__firstdata = copy.copy(dataOut)

            else:
                self.__buffer = numpy.vstack((self.__buffer, dataOut.data_param))

            self.__checkTime(dataOut.utctime, dataOut.paramInterval, dataOut.outputInterval) #Check if the buffer is ready

            if self.__dataReady:
                dataOut.utctimeInit = self.__initime
                self.__initime += dataOut.outputInterval #to erase time offset

                metArray = self.__buffer
                if mode == 'SA':
                    dataOut.data_output = self.techniqueNSM_SA(rx_location=rx_location, groupList=groupList, azimuth=azimuth, dfactor=dfactor, k=k,metArray=metArray, heightList=heightList,timeList=timeList)
                elif mode == 'DBS':
                    dataOut.data_output = self.techniqueNSM_DBS(metArray=metArray,heightList=heightList,timeList=timeList, azimuth=azimuth, theta_x=theta_x, theta_y=theta_y)
                dataOut.data_output = dataOut.data_output.T
                dataOut.flagNoData = False
                self.__buffer = None

        return

class EWDriftsEstimation(Operation):

    def __init__(self):
        Operation.__init__(self)

    def __correctValues(self, heiRang, phi, velRadial, SNR):
        listPhi = phi.tolist()
        maxid = listPhi.index(max(listPhi))
        minid = listPhi.index(min(listPhi))

        rango = list(range(len(phi)))
   #     rango = numpy.delete(rango,maxid)

        heiRang1 = heiRang*math.cos(phi[maxid])
        heiRangAux = heiRang*math.cos(phi[minid])
        indOut = (heiRang1 < heiRangAux[0]).nonzero()
        heiRang1 = numpy.delete(heiRang1,indOut)

        velRadial1 = numpy.zeros([len(phi),len(heiRang1)])
        SNR1 = numpy.zeros([len(phi),len(heiRang1)])

        for i in rango:
            x = heiRang*math.cos(phi[i])
            y1 = velRadial[i,:]
            f1 = interpolate.interp1d(x,y1,kind = 'cubic')

            x1 = heiRang1
            y11 = f1(x1)

            y2 = SNR[i,:]
            f2 = interpolate.interp1d(x,y2,kind = 'cubic')
            y21 = f2(x1)

            velRadial1[i,:] = y11
            SNR1[i,:] = y21

        return heiRang1, velRadial1, SNR1

    def run(self, dataOut, zenith, zenithCorrection):
        heiRang = dataOut.heightList
        velRadial = dataOut.data_param[:,3,:]
        SNR = dataOut.data_snr

        zenith = numpy.array(zenith)
        zenith -= zenithCorrection
        zenith *= numpy.pi/180

        heiRang1, velRadial1, SNR1 = self.__correctValues(heiRang, numpy.abs(zenith), velRadial, SNR)

        alp = zenith[0]
        bet = zenith[1]

        w_w = velRadial1[0,:]
        w_e = velRadial1[1,:]

        w = (w_w*numpy.sin(bet) - w_e*numpy.sin(alp))/(numpy.cos(alp)*numpy.sin(bet) - numpy.cos(bet)*numpy.sin(alp))
        u = (w_w*numpy.cos(bet) - w_e*numpy.cos(alp))/(numpy.sin(alp)*numpy.cos(bet) - numpy.sin(bet)*numpy.cos(alp))

        winds = numpy.vstack((u,w))

        dataOut.heightList = heiRang1
        dataOut.data_output = winds
        dataOut.data_snr = SNR1

        dataOut.utctimeInit = dataOut.utctime
        dataOut.outputInterval = dataOut.timeInterval
        return

#---------------    Non Specular Meteor    ----------------

class NonSpecularMeteorDetection(Operation):

    def run(self, dataOut, mode, SNRthresh=8, phaseDerThresh=0.5, cohThresh=0.8, allData = False):
        data_acf = dataOut.data_pre[0]
        data_ccf = dataOut.data_pre[1]
        pairsList = dataOut.groupList[1]

        lamb = dataOut.C/dataOut.frequency
        tSamp = dataOut.ippSeconds*dataOut.nCohInt
        paramInterval = dataOut.paramInterval

        nChannels = data_acf.shape[0]
        nLags = data_acf.shape[1]
        nProfiles = data_acf.shape[2]
        nHeights = dataOut.nHeights
        nCohInt = dataOut.nCohInt
        sec = numpy.round(nProfiles/dataOut.paramInterval)
        heightList = dataOut.heightList
        ippSeconds = dataOut.ippSeconds*dataOut.nCohInt*dataOut.nAvg
        utctime = dataOut.utctime

        dataOut.abscissaList = numpy.arange(0,paramInterval+ippSeconds,ippSeconds)

        #------------------------    SNR    --------------------------------------
        power = data_acf[:,0,:,:].real
        noise = numpy.zeros(nChannels)
        SNR = numpy.zeros(power.shape)
        for i in range(nChannels):
            noise[i] = hildebrand_sekhon(power[i,:], nCohInt)
            SNR[i] = (power[i]-noise[i])/noise[i]
        SNRm = numpy.nanmean(SNR, axis = 0)
        SNRdB = 10*numpy.log10(SNR)

        if mode == 'SA':
            dataOut.groupList = dataOut.groupList[1]
            nPairs = data_ccf.shape[0]
            #----------------------    Coherence and Phase   --------------------------
            phase = numpy.zeros(data_ccf[:,0,:,:].shape)
#             phase1 = numpy.copy(phase)
            coh1 = numpy.zeros(data_ccf[:,0,:,:].shape)

            for p in range(nPairs):
                ch0 = pairsList[p][0]
                ch1 = pairsList[p][1]
                ccf = data_ccf[p,0,:,:]/numpy.sqrt(data_acf[ch0,0,:,:]*data_acf[ch1,0,:,:])
                phase[p,:,:] = ndimage.median_filter(numpy.angle(ccf), size = (5,1)) #median filter
#                 phase1[p,:,:] = numpy.angle(ccf) #median filter
                coh1[p,:,:] = ndimage.median_filter(numpy.abs(ccf), 5) #median filter
#                 coh1[p,:,:] = numpy.abs(ccf) #median filter
            coh = numpy.nanmax(coh1, axis = 0)
#             struc = numpy.ones((5,1))
#             coh = ndimage.morphology.grey_dilation(coh, size=(10,1))
            #----------------------    Radial Velocity    ----------------------------
            phaseAux = numpy.mean(numpy.angle(data_acf[:,1,:,:]), axis = 0)
            velRad = phaseAux*lamb/(4*numpy.pi*tSamp)

            if allData:
                boolMetFin = ~numpy.isnan(SNRm)
#                 coh[:-1,:] = numpy.nanmean(numpy.abs(phase[:,1:,:] - phase[:,:-1,:]),axis=0)
            else:
                #------------------------    Meteor mask    ---------------------------------
#                 #SNR mask
#                 boolMet = (SNRdB>SNRthresh)#|(~numpy.isnan(SNRdB))
#
#                 #Erase small objects
#                 boolMet1 = self.__erase_small(boolMet, 2*sec, 5)
#
#                 auxEEJ = numpy.sum(boolMet1,axis=0)
#                 indOver = auxEEJ>nProfiles*0.8  #Use this later
#                 indEEJ = numpy.where(indOver)[0]
#                 indNEEJ = numpy.where(~indOver)[0]
#
#                 boolMetFin = boolMet1
#
#                 if indEEJ.size > 0:
#                     boolMet1[:,indEEJ] = False  #Erase heights with EEJ
#
#                     boolMet2 = coh > cohThresh
#                     boolMet2 = self.__erase_small(boolMet2, 2*sec,5)
#
#                     #Final Meteor mask
#                     boolMetFin = boolMet1|boolMet2

                #Coherence mask
                boolMet1 = coh > 0.75
                struc = numpy.ones((30,1))
                boolMet1 = ndimage.morphology.binary_dilation(boolMet1, structure=struc)

                #Derivative mask
                derPhase = numpy.nanmean(numpy.abs(phase[:,1:,:] - phase[:,:-1,:]),axis=0)
                boolMet2 = derPhase < 0.2
#                 boolMet2 = ndimage.morphology.binary_opening(boolMet2)
#                 boolMet2 = ndimage.morphology.binary_closing(boolMet2, structure = numpy.ones((10,1)))
                boolMet2 = ndimage.median_filter(boolMet2,size=5)
                boolMet2 = numpy.vstack((boolMet2,numpy.full((1,nHeights), True, dtype=bool)))
#                 #Final mask
#                 boolMetFin = boolMet2
                boolMetFin = boolMet1&boolMet2
#                 boolMetFin = ndimage.morphology.binary_dilation(boolMetFin)
            #Creating data_param
            coordMet = numpy.where(boolMetFin)

            tmet = coordMet[0]
            hmet = coordMet[1]

            data_param = numpy.zeros((tmet.size, 6 + nPairs))
            data_param[:,0] = utctime
            data_param[:,1] = tmet
            data_param[:,2] = hmet
            data_param[:,3] = SNRm[tmet,hmet]
            data_param[:,4] = velRad[tmet,hmet]
            data_param[:,5] = coh[tmet,hmet]
            data_param[:,6:] = phase[:,tmet,hmet].T

        elif mode == 'DBS':
            dataOut.groupList = numpy.arange(nChannels)

            #Radial Velocities
            phase = numpy.angle(data_acf[:,1,:,:])
#             phase = ndimage.median_filter(numpy.angle(data_acf[:,1,:,:]), size = (1,5,1))
            velRad = phase*lamb/(4*numpy.pi*tSamp)

            #Spectral width
#             acf1 = ndimage.median_filter(numpy.abs(data_acf[:,1,:,:]), size = (1,5,1))
#             acf2 = ndimage.median_filter(numpy.abs(data_acf[:,2,:,:]), size = (1,5,1))
            acf1 = data_acf[:,1,:,:]
            acf2 = data_acf[:,2,:,:]

            spcWidth = (lamb/(2*numpy.sqrt(6)*numpy.pi*tSamp))*numpy.sqrt(numpy.log(acf1/acf2))
#             velRad = ndimage.median_filter(velRad, size = (1,5,1))
            if allData:
                boolMetFin = ~numpy.isnan(SNRdB)
            else:
                #SNR
                boolMet1 = (SNRdB>SNRthresh) #SNR mask
                boolMet1 = ndimage.median_filter(boolMet1, size=(1,5,5))

                #Radial velocity
                boolMet2 = numpy.abs(velRad) < 20
                boolMet2 = ndimage.median_filter(boolMet2, (1,5,5))

                #Spectral Width
                boolMet3 = spcWidth < 30
                boolMet3 = ndimage.median_filter(boolMet3, (1,5,5))
#                 boolMetFin = self.__erase_small(boolMet1, 10,5)
                boolMetFin = boolMet1&boolMet2&boolMet3

            #Creating data_param
            coordMet = numpy.where(boolMetFin)

            cmet = coordMet[0]
            tmet = coordMet[1]
            hmet = coordMet[2]

            data_param = numpy.zeros((tmet.size, 7))
            data_param[:,0] = utctime
            data_param[:,1] = cmet
            data_param[:,2] = tmet
            data_param[:,3] = hmet
            data_param[:,4] = SNR[cmet,tmet,hmet].T
            data_param[:,5] = velRad[cmet,tmet,hmet].T
            data_param[:,6] = spcWidth[cmet,tmet,hmet].T

#         self.dataOut.data_param = data_int
        if len(data_param) == 0:
            dataOut.flagNoData = True
        else:
            dataOut.data_param = data_param

    def __erase_small(self, binArray, threshX, threshY):
        labarray, numfeat = ndimage.measurements.label(binArray)
        binArray1 = numpy.copy(binArray)

        for i in range(1,numfeat + 1):
            auxBin = (labarray==i)
            auxSize = auxBin.sum()

            x,y = numpy.where(auxBin)
            widthX = x.max() - x.min()
            widthY = y.max() - y.min()

            #width X: 3 seg -> 12.5*3
            #width Y:

            if (auxSize < 50) or (widthX < threshX) or (widthY < threshY):
                binArray1[auxBin] = False

        return binArray1

#---------------    Specular Meteor    ----------------

class SMDetection(Operation):
    '''
        Function DetectMeteors()
            Project developed with paper:
            HOLDSWORTH ET AL. 2004

        Input:
            self.dataOut.data_pre

            centerReceiverIndex:      From the channels, which is the center receiver

            hei_ref:                  Height reference for the Beacon signal extraction
            tauindex:
            predefinedPhaseShifts:    Predefined phase offset for the voltge signals

            cohDetection:             Whether to user Coherent detection or not
            cohDet_timeStep:          Coherent Detection calculation time step
            cohDet_thresh:            Coherent Detection phase threshold to correct phases

            noise_timeStep:           Noise calculation time step
            noise_multiple:           Noise multiple to define signal threshold

            multDet_timeLimit:        Multiple Detection Removal time limit in seconds
            multDet_rangeLimit:       Multiple Detection Removal range limit in km

            phaseThresh:              Maximum phase difference between receiver to be consider a meteor
            SNRThresh:                Minimum SNR threshold of the meteor signal to be consider a meteor

            hmin:                     Minimum Height of the meteor to use it in the further wind estimations
            hmax:                     Maximum Height of the meteor to use it in the further wind estimations
            azimuth:                  Azimuth angle correction

        Affected:
            self.dataOut.data_param

        Rejection Criteria (Errors):
            0: No error; analysis OK
            1: SNR < SNR threshold
            2: angle of arrival (AOA) ambiguously determined
            3: AOA estimate not feasible
            4: Large difference in AOAs obtained from different antenna baselines
            5: echo at start or end of time series
            6: echo less than 5 examples long; too short for analysis
            7: echo rise exceeds 0.3s
            8: echo decay time less than twice rise time
            9: large power level before echo
            10: large power level after echo
            11: poor fit to amplitude for estimation of decay time
            12: poor fit to CCF phase variation for estimation of radial drift velocity
            13: height unresolvable echo: not valid height within 70 to 110 km
            14: height ambiguous echo: more then one possible height within 70 to 110 km
            15: radial drift velocity or projected horizontal velocity exceeds 200 m/s
            16: oscilatory echo, indicating event most likely not an underdense echo

            17: phase difference in meteor Reestimation

        Data Storage:
            Meteors for Wind Estimation   (8):
            Utc Time   |    Range    Height
            Azimuth    Zenith    errorCosDir
            VelRad    errorVelRad
            Phase0 Phase1 Phase2 Phase3
            TypeError

         '''

    def run(self, dataOut, hei_ref = None, tauindex = 0,
                      phaseOffsets = None,
                      cohDetection = False, cohDet_timeStep = 1, cohDet_thresh = 25,
                      noise_timeStep = 4, noise_multiple = 4,
                      multDet_timeLimit = 1, multDet_rangeLimit = 3,
                      phaseThresh = 20, SNRThresh = 5,
                      hmin = 50, hmax=150, azimuth = 0,
                      channelPositions = None) :


        #Getting Pairslist
        if channelPositions is None:
#             channelPositions = [(2.5,0), (0,2.5), (0,0), (0,4.5), (-2,0)]   #T
            channelPositions = [(4.5,2), (2,4.5), (2,2), (2,0), (0,2)]   #Estrella
        meteorOps = SMOperations()
        pairslist0, distances = meteorOps.getPhasePairs(channelPositions)
        heiRang = dataOut.heightList
        #Get Beacon signal - No Beacon signal anymore
#         newheis = numpy.where(self.dataOut.heightList>self.dataOut.radarControllerHeaderObj.Taus[tauindex])
#
#         if hei_ref != None:
#             newheis = numpy.where(self.dataOut.heightList>hei_ref)
#


        #****************REMOVING HARDWARE PHASE DIFFERENCES***************
        # see if the user put in pre defined phase shifts
        voltsPShift = dataOut.data_pre.copy()

#         if predefinedPhaseShifts != None:
#             hardwarePhaseShifts = numpy.array(predefinedPhaseShifts)*numpy.pi/180
#
# #         elif beaconPhaseShifts:
# #             #get hardware phase shifts using beacon signal
# #             hardwarePhaseShifts = self.__getHardwarePhaseDiff(self.dataOut.data_pre, pairslist, newheis, 10)
# #             hardwarePhaseShifts = numpy.insert(hardwarePhaseShifts,centerReceiverIndex,0)
#
#         else:
#             hardwarePhaseShifts = numpy.zeros(5)
#
#         voltsPShift = numpy.zeros((self.dataOut.data_pre.shape[0],self.dataOut.data_pre.shape[1],self.dataOut.data_pre.shape[2]), dtype = 'complex')
#         for i in range(self.dataOut.data_pre.shape[0]):
#             voltsPShift[i,:,:] = self.__shiftPhase(self.dataOut.data_pre[i,:,:], hardwarePhaseShifts[i])

        #******************END OF REMOVING HARDWARE PHASE DIFFERENCES*********

        #Remove DC
        voltsDC = numpy.mean(voltsPShift,1)
        voltsDC = numpy.mean(voltsDC,1)
        for i in range(voltsDC.shape[0]):
            voltsPShift[i] = voltsPShift[i] - voltsDC[i]

        #Don't considerate last heights, theyre used to calculate Hardware Phase Shift
#         voltsPShift = voltsPShift[:,:,:newheis[0][0]]

        #************ FIND POWER OF DATA W/COH OR NON COH DETECTION (3.4) **********
        #Coherent Detection
        if cohDetection:
            #use coherent detection to get the net power
            cohDet_thresh = cohDet_thresh*numpy.pi/180
            voltsPShift = self.__coherentDetection(voltsPShift, cohDet_timeStep, dataOut.timeInterval, pairslist0, cohDet_thresh)

        #Non-coherent detection!
        powerNet = numpy.nansum(numpy.abs(voltsPShift[:,:,:])**2,0)
        #********** END OF COH/NON-COH POWER CALCULATION**********************

        #********** FIND THE NOISE LEVEL AND POSSIBLE METEORS ****************
        #Get noise
        noise, noise1 = self.__getNoise(powerNet, noise_timeStep, dataOut.timeInterval)
#         noise = self.getNoise1(powerNet, noise_timeStep, self.dataOut.timeInterval)
        #Get signal threshold
        signalThresh = noise_multiple*noise
        #Meteor echoes detection
        listMeteors = self.__findMeteors(powerNet, signalThresh)
        #******* END OF NOISE LEVEL AND POSSIBLE METEORS CACULATION **********

        #************** REMOVE MULTIPLE DETECTIONS (3.5) ***************************
        #Parameters
        heiRange = dataOut.heightList
        rangeInterval = heiRange[1] - heiRange[0]
        rangeLimit = multDet_rangeLimit/rangeInterval
        timeLimit = multDet_timeLimit/dataOut.timeInterval
        #Multiple detection removals
        listMeteors1 = self.__removeMultipleDetections(listMeteors, rangeLimit, timeLimit)
        #************ END OF REMOVE MULTIPLE DETECTIONS **********************

        #*********************     METEOR REESTIMATION  (3.7, 3.8, 3.9, 3.10)   ********************
        #Parameters
        phaseThresh = phaseThresh*numpy.pi/180
        thresh = [phaseThresh, noise_multiple, SNRThresh]
        #Meteor reestimation  (Errors N 1, 6, 12, 17)
        listMeteors2, listMeteorsPower, listMeteorsVolts = self.__meteorReestimation(listMeteors1, voltsPShift, pairslist0, thresh, noise, dataOut.timeInterval, dataOut.frequency)
#         listMeteors2, listMeteorsPower, listMeteorsVolts = self.meteorReestimation3(listMeteors2, listMeteorsPower, listMeteorsVolts, voltsPShift, pairslist, thresh, noise)
        #Estimation of decay times (Errors N 7, 8, 11)
        listMeteors3 = self.__estimateDecayTime(listMeteors2, listMeteorsPower, dataOut.timeInterval, dataOut.frequency)
        #*******************     END OF METEOR REESTIMATION    *******************

        #*********************    METEOR PARAMETERS CALCULATION (3.11, 3.12, 3.13)    **************************
        #Calculating Radial Velocity (Error N 15)
        radialStdThresh = 10
        listMeteors4 = self.__getRadialVelocity(listMeteors3, listMeteorsVolts, radialStdThresh, pairslist0, dataOut.timeInterval)

        if len(listMeteors4) > 0:
            #Setting New Array
            date = dataOut.utctime
            arrayParameters = self.__setNewArrays(listMeteors4, date, heiRang)

            #Correcting phase offset
            if phaseOffsets != None:
                phaseOffsets = numpy.array(phaseOffsets)*numpy.pi/180
                arrayParameters[:,8:12] = numpy.unwrap(arrayParameters[:,8:12] + phaseOffsets)

            #Second Pairslist
            pairsList = []
            pairx = (0,1)
            pairy = (2,3)
            pairsList.append(pairx)
            pairsList.append(pairy)

            jph = numpy.array([0,0,0,0])
            h = (hmin,hmax)
            arrayParameters = meteorOps.getMeteorParams(arrayParameters, azimuth, h, pairsList, distances, jph)

#             #Calculate AOA (Error N 3, 4)
#             #JONES ET AL. 1998
#             error = arrayParameters[:,-1]
#             AOAthresh = numpy.pi/8
#             phases = -arrayParameters[:,9:13]
#             arrayParameters[:,4:7], arrayParameters[:,-1] = meteorOps.getAOA(phases, pairsList, error, AOAthresh, azimuth)
#
#             #Calculate Heights (Error N 13 and 14)
#             error = arrayParameters[:,-1]
#             Ranges = arrayParameters[:,2]
#             zenith = arrayParameters[:,5]
#             arrayParameters[:,3], arrayParameters[:,-1] = meteorOps.getHeights(Ranges, zenith, error, hmin, hmax)
#             error = arrayParameters[:,-1]
        #*********************    END OF PARAMETERS CALCULATION    **************************

        #***************************+     PASS DATA TO NEXT STEP    **********************
#             arrayFinal = arrayParameters.reshape((1,arrayParameters.shape[0],arrayParameters.shape[1]))
            dataOut.data_param = arrayParameters

            if arrayParameters is None:
                dataOut.flagNoData = True
        else:
            dataOut.flagNoData = True

        return

    def __getHardwarePhaseDiff(self, voltage0, pairslist, newheis, n):

        minIndex = min(newheis[0])
        maxIndex = max(newheis[0])

        voltage = voltage0[:,:,minIndex:maxIndex+1]
        nLength = voltage.shape[1]/n
        nMin = 0
        nMax = 0
        phaseOffset = numpy.zeros((len(pairslist),n))

        for i in range(n):
            nMax += nLength
            phaseCCF = -numpy.angle(self.__calculateCCF(voltage[:,nMin:nMax,:], pairslist, [0]))
            phaseCCF = numpy.mean(phaseCCF, axis = 2)
            phaseOffset[:,i] = phaseCCF.transpose()
            nMin = nMax
#         phaseDiff, phaseArrival = self.estimatePhaseDifference(voltage, pairslist)

        #Remove Outliers
        factor = 2
        wt = phaseOffset - signal.medfilt(phaseOffset,(1,5))
        dw = numpy.std(wt,axis = 1)
        dw = dw.reshape((dw.size,1))
        ind = numpy.where(numpy.logical_or(wt>dw*factor,wt<-dw*factor))
        phaseOffset[ind] = numpy.nan
        phaseOffset = stats.nanmean(phaseOffset, axis=1)

        return phaseOffset

    def __shiftPhase(self, data, phaseShift):
        #this will shift the phase of a complex number
        dataShifted = numpy.abs(data) * numpy.exp((numpy.angle(data)+phaseShift)*1j)
        return dataShifted

    def __estimatePhaseDifference(self, array, pairslist):
        nChannel = array.shape[0]
        nHeights = array.shape[2]
        numPairs = len(pairslist)
#         phaseCCF = numpy.zeros((nChannel, 5, nHeights))
        phaseCCF = numpy.angle(self.__calculateCCF(array, pairslist, [-2,-1,0,1,2]))

        #Correct phases
        derPhaseCCF = phaseCCF[:,1:,:] - phaseCCF[:,0:-1,:]
        indDer = numpy.where(numpy.abs(derPhaseCCF) > numpy.pi)

        if indDer[0].shape[0] > 0:
            for i in range(indDer[0].shape[0]):
                signo = -numpy.sign(derPhaseCCF[indDer[0][i],indDer[1][i],indDer[2][i]])
                phaseCCF[indDer[0][i],indDer[1][i]+1:,:] += signo*2*numpy.pi

#         for j in range(numSides):
#             phaseCCFAux = self.calculateCCF(arrayCenter, arraySides[j,:,:], [-2,1,0,1,2])
#             phaseCCF[j,:,:] = numpy.angle(phaseCCFAux)
#
        #Linear
        phaseInt = numpy.zeros((numPairs,1))
        angAllCCF = phaseCCF[:,[0,1,3,4],0]
        for j in range(numPairs):
            fit = stats.linregress([-2,-1,1,2],angAllCCF[j,:])
            phaseInt[j] = fit[1]
        #Phase Differences
        phaseDiff = phaseInt - phaseCCF[:,2,:]
        phaseArrival = phaseInt.reshape(phaseInt.size)

        #Dealias
        phaseArrival = numpy.angle(numpy.exp(1j*phaseArrival))
#         indAlias = numpy.where(phaseArrival > numpy.pi)
#         phaseArrival[indAlias] -= 2*numpy.pi
#         indAlias = numpy.where(phaseArrival < -numpy.pi)
#         phaseArrival[indAlias] += 2*numpy.pi

        return phaseDiff, phaseArrival

    def __coherentDetection(self, volts, timeSegment, timeInterval, pairslist, thresh):
        #this function will run the coherent detection used in Holdworth et al. 2004 and return the net power
        #find the phase shifts of each channel over 1 second intervals
        #only look at ranges below the beacon signal
        numProfPerBlock = numpy.ceil(timeSegment/timeInterval)
        numBlocks = int(volts.shape[1]/numProfPerBlock)
        numHeights = volts.shape[2]
        nChannel = volts.shape[0]
        voltsCohDet = volts.copy()

        pairsarray = numpy.array(pairslist)
        indSides = pairsarray[:,1]
#         indSides = numpy.array(range(nChannel))
#         indSides = numpy.delete(indSides, indCenter)
#
#         listCenter = numpy.array_split(volts[indCenter,:,:], numBlocks, 0)
        listBlocks = numpy.array_split(volts, numBlocks, 1)

        startInd = 0
        endInd = 0

        for i in range(numBlocks):
            startInd = endInd
            endInd = endInd + listBlocks[i].shape[1]

            arrayBlock = listBlocks[i]
#             arrayBlockCenter = listCenter[i]

            #Estimate the Phase Difference
            phaseDiff, aux = self.__estimatePhaseDifference(arrayBlock, pairslist)
            #Phase Difference RMS
            arrayPhaseRMS = numpy.abs(phaseDiff)
            phaseRMSaux = numpy.sum(arrayPhaseRMS < thresh,0)
            indPhase = numpy.where(phaseRMSaux==4)
            #Shifting
            if indPhase[0].shape[0] > 0:
                for j in range(indSides.size):
                    arrayBlock[indSides[j],:,indPhase] = self.__shiftPhase(arrayBlock[indSides[j],:,indPhase], phaseDiff[j,indPhase].transpose())
                voltsCohDet[:,startInd:endInd,:] = arrayBlock

        return voltsCohDet

    def __calculateCCF(self, volts, pairslist ,laglist):

        nHeights = volts.shape[2]
        nPoints = volts.shape[1]
        voltsCCF = numpy.zeros((len(pairslist), len(laglist), nHeights),dtype = 'complex')

        for i in range(len(pairslist)):
            volts1 = volts[pairslist[i][0]]
            volts2 = volts[pairslist[i][1]]

            for t in range(len(laglist)):
                idxT = laglist[t]
                if idxT >= 0:
                    vStacked = numpy.vstack((volts2[idxT:,:],
                                           numpy.zeros((idxT, nHeights),dtype='complex')))
                else:
                    vStacked = numpy.vstack((numpy.zeros((-idxT, nHeights),dtype='complex'),
                                           volts2[:(nPoints + idxT),:]))
                voltsCCF[i,t,:] = numpy.sum((numpy.conjugate(volts1)*vStacked),axis=0)

                vStacked = None
        return voltsCCF

    def __getNoise(self, power, timeSegment, timeInterval):
        numProfPerBlock = numpy.ceil(timeSegment/timeInterval)
        numBlocks = int(power.shape[0]/numProfPerBlock)
        numHeights = power.shape[1]

        listPower = numpy.array_split(power, numBlocks, 0)
        noise = numpy.zeros((power.shape[0], power.shape[1]))
        noise1 = numpy.zeros((power.shape[0], power.shape[1]))

        startInd = 0
        endInd = 0

        for i in range(numBlocks):             #split por canal
            startInd = endInd
            endInd = endInd + listPower[i].shape[0]

            arrayBlock = listPower[i]
            noiseAux = numpy.mean(arrayBlock, 0)
#             noiseAux = numpy.median(noiseAux)
#             noiseAux = numpy.mean(arrayBlock)
            noise[startInd:endInd,:] = noise[startInd:endInd,:] + noiseAux

            noiseAux1 = numpy.mean(arrayBlock)
            noise1[startInd:endInd,:] = noise1[startInd:endInd,:] + noiseAux1

        return noise, noise1

    def __findMeteors(self, power, thresh):
        nProf = power.shape[0]
        nHeights = power.shape[1]
        listMeteors = []

        for i in range(nHeights):
            powerAux = power[:,i]
            threshAux = thresh[:,i]

            indUPthresh = numpy.where(powerAux > threshAux)[0]
            indDNthresh = numpy.where(powerAux <= threshAux)[0]

            j = 0

            while (j < indUPthresh.size - 2):
                if (indUPthresh[j + 2] == indUPthresh[j] + 2):
                    indDNAux = numpy.where(indDNthresh > indUPthresh[j])
                    indDNthresh = indDNthresh[indDNAux]

                    if (indDNthresh.size > 0):
                        indEnd = indDNthresh[0] - 1
                        indInit = indUPthresh[j]

                        meteor = powerAux[indInit:indEnd + 1]
                        indPeak = meteor.argmax() + indInit
                        FLA = sum(numpy.conj(meteor)*numpy.hstack((meteor[1:],0)))

                        listMeteors.append(numpy.array([i,indInit,indPeak,indEnd,FLA])) #CHEQUEAR!!!!!
                        j = numpy.where(indUPthresh == indEnd)[0] + 1
                    else: j+=1
                else: j+=1

        return listMeteors

    def __removeMultipleDetections(self,listMeteors, rangeLimit, timeLimit):

        arrayMeteors = numpy.asarray(listMeteors)
        listMeteors1 = []

        while arrayMeteors.shape[0] > 0:
            FLAs = arrayMeteors[:,4]
            maxFLA = FLAs.argmax()
            listMeteors1.append(arrayMeteors[maxFLA,:])

            MeteorInitTime = arrayMeteors[maxFLA,1]
            MeteorEndTime = arrayMeteors[maxFLA,3]
            MeteorHeight = arrayMeteors[maxFLA,0]

            #Check neighborhood
            maxHeightIndex = MeteorHeight + rangeLimit
            minHeightIndex = MeteorHeight - rangeLimit
            minTimeIndex = MeteorInitTime - timeLimit
            maxTimeIndex = MeteorEndTime + timeLimit

            #Check Heights
            indHeight = numpy.logical_and(arrayMeteors[:,0] >= minHeightIndex, arrayMeteors[:,0] <= maxHeightIndex)
            indTime = numpy.logical_and(arrayMeteors[:,3] >= minTimeIndex, arrayMeteors[:,1] <= maxTimeIndex)
            indBoth = numpy.where(numpy.logical_and(indTime,indHeight))

            arrayMeteors = numpy.delete(arrayMeteors, indBoth, axis = 0)

        return listMeteors1

    def __meteorReestimation(self, listMeteors, volts, pairslist, thresh, noise, timeInterval,frequency):
        numHeights = volts.shape[2]
        nChannel = volts.shape[0]

        thresholdPhase = thresh[0]
        thresholdNoise = thresh[1]
        thresholdDB = float(thresh[2])

        thresholdDB1 = 10**(thresholdDB/10)
        pairsarray = numpy.array(pairslist)
        indSides = pairsarray[:,1]

        pairslist1 = list(pairslist)
        pairslist1.append((0,1))
        pairslist1.append((3,4))

        listMeteors1 = []
        listPowerSeries = []
        listVoltageSeries = []
        #volts has the war data

        if frequency == 30e6:
            timeLag = 45*10**-3
        else:
            timeLag = 15*10**-3
        lag = numpy.ceil(timeLag/timeInterval)

        for i in range(len(listMeteors)):

            ######################   3.6 - 3.7 PARAMETERS REESTIMATION    #########################
            meteorAux = numpy.zeros(16)

            #Loading meteor Data (mHeight, mStart, mPeak, mEnd)
            mHeight = listMeteors[i][0]
            mStart = listMeteors[i][1]
            mPeak = listMeteors[i][2]
            mEnd = listMeteors[i][3]

            #get the volt data between the start and end times of the meteor
            meteorVolts = volts[:,mStart:mEnd+1,mHeight]
            meteorVolts = meteorVolts.reshape(meteorVolts.shape[0], meteorVolts.shape[1], 1)

            #3.6. Phase Difference estimation
            phaseDiff, aux = self.__estimatePhaseDifference(meteorVolts, pairslist)

            #3.7. Phase difference removal & meteor start, peak and end times reestimated
            #meteorVolts0.- all Channels, all Profiles
            meteorVolts0 = volts[:,:,mHeight]
            meteorThresh = noise[:,mHeight]*thresholdNoise
            meteorNoise = noise[:,mHeight]
            meteorVolts0[indSides,:] = self.__shiftPhase(meteorVolts0[indSides,:], phaseDiff) #Phase Shifting
            powerNet0 = numpy.nansum(numpy.abs(meteorVolts0)**2, axis = 0)  #Power

            #Times reestimation
            mStart1 = numpy.where(powerNet0[:mPeak] < meteorThresh[:mPeak])[0]
            if mStart1.size > 0:
                mStart1 = mStart1[-1] + 1

            else:
                mStart1 = mPeak

            mEnd1 = numpy.where(powerNet0[mPeak:] < meteorThresh[mPeak:])[0][0] + mPeak - 1
            mEndDecayTime1 = numpy.where(powerNet0[mPeak:] < meteorNoise[mPeak:])[0]
            if mEndDecayTime1.size == 0:
                mEndDecayTime1 = powerNet0.size
            else:
                mEndDecayTime1 = mEndDecayTime1[0] + mPeak - 1
#             mPeak1 = meteorVolts0[mStart1:mEnd1 + 1].argmax()

            #meteorVolts1.- all Channels, from start to end
            meteorVolts1 = meteorVolts0[:,mStart1:mEnd1 + 1]
            meteorVolts2 = meteorVolts0[:,mPeak + lag:mEnd1 + 1]
            if meteorVolts2.shape[1] == 0:
                meteorVolts2 = meteorVolts0[:,mPeak:mEnd1 + 1]
            meteorVolts1 = meteorVolts1.reshape(meteorVolts1.shape[0], meteorVolts1.shape[1], 1)
            meteorVolts2 = meteorVolts2.reshape(meteorVolts2.shape[0], meteorVolts2.shape[1], 1)
            #####################    END PARAMETERS REESTIMATION    #########################

            #####################   3.8 PHASE DIFFERENCE REESTIMATION  ########################
#             if mEnd1 - mStart1 > 4:       #Error Number 6: echo less than 5 samples long; too short for analysis
            if meteorVolts2.shape[1] > 0:
                #Phase Difference re-estimation
                phaseDiff1, phaseDiffint = self.__estimatePhaseDifference(meteorVolts2, pairslist1)   #Phase Difference Estimation
#                 phaseDiff1, phaseDiffint = self.estimatePhaseDifference(meteorVolts2, pairslist)
                meteorVolts2 = meteorVolts2.reshape(meteorVolts2.shape[0], meteorVolts2.shape[1])
                phaseDiff11 = numpy.reshape(phaseDiff1, (phaseDiff1.shape[0],1))
                meteorVolts2[indSides,:] = self.__shiftPhase(meteorVolts2[indSides,:], phaseDiff11[0:4])     #Phase Shifting

                #Phase Difference RMS
                phaseRMS1 = numpy.sqrt(numpy.mean(numpy.square(phaseDiff1)))
                powerNet1 = numpy.nansum(numpy.abs(meteorVolts1[:,:])**2,0)
                #Data from Meteor
                mPeak1 = powerNet1.argmax() + mStart1
                mPeakPower1 = powerNet1.max()
                noiseAux = sum(noise[mStart1:mEnd1 + 1,mHeight])
                mSNR1 = (sum(powerNet1)-noiseAux)/noiseAux
                Meteor1 = numpy.array([mHeight, mStart1, mPeak1, mEnd1, mPeakPower1, mSNR1, phaseRMS1])
                Meteor1 = numpy.hstack((Meteor1,phaseDiffint))
                PowerSeries  = powerNet0[mStart1:mEndDecayTime1 + 1]
                #Vectorize
                meteorAux[0:7] = [mHeight, mStart1, mPeak1, mEnd1, mPeakPower1, mSNR1, phaseRMS1]
                meteorAux[7:11] = phaseDiffint[0:4]

                #Rejection Criterions
                if phaseRMS1 > thresholdPhase:  #Error Number 17: Phase variation
                    meteorAux[-1] = 17
                elif mSNR1 < thresholdDB1:      #Error Number 1: SNR < threshold dB
                    meteorAux[-1] = 1


            else:
                meteorAux[0:4] = [mHeight, mStart, mPeak, mEnd]
                meteorAux[-1] = 6 #Error Number 6: echo less than 5 samples long; too short for analysis
                PowerSeries = 0

            listMeteors1.append(meteorAux)
            listPowerSeries.append(PowerSeries)
            listVoltageSeries.append(meteorVolts1)

        return listMeteors1, listPowerSeries, listVoltageSeries

    def __estimateDecayTime(self, listMeteors, listPower, timeInterval, frequency):

        threshError = 10
        #Depending if it is 30 or 50 MHz
        if frequency == 30e6:
            timeLag = 45*10**-3
        else:
            timeLag = 15*10**-3
        lag = numpy.ceil(timeLag/timeInterval)

        listMeteors1 = []

        for i in range(len(listMeteors)):
            meteorPower = listPower[i]
            meteorAux = listMeteors[i]

            if meteorAux[-1] == 0:

                try:
                    indmax = meteorPower.argmax()
                    indlag = indmax + lag

                    y = meteorPower[indlag:]
                    x = numpy.arange(0, y.size)*timeLag

                    #first guess
                    a = y[0]
                    tau = timeLag
                    #exponential fit
                    popt, pcov = optimize.curve_fit(self.__exponential_function, x, y, p0 = [a, tau])
                    y1 = self.__exponential_function(x, *popt)
                    #error estimation
                    error = sum((y - y1)**2)/(numpy.var(y)*(y.size - popt.size))

                    decayTime = popt[1]
                    riseTime = indmax*timeInterval
                    meteorAux[11:13] = [decayTime, error]

                    #Table items 7, 8 and 11
                    if (riseTime > 0.3):            #Number 7: Echo rise exceeds 0.3s
                        meteorAux[-1] = 7
                    elif (decayTime < 2*riseTime) : #Number 8: Echo decay time less than than twice rise time
                        meteorAux[-1] = 8
                    if (error > threshError):       #Number 11: Poor fit to amplitude for estimation of decay time
                        meteorAux[-1] = 11


                except:
                    meteorAux[-1] = 11


            listMeteors1.append(meteorAux)

        return listMeteors1

    #Exponential Function

    def __exponential_function(self, x, a, tau):
        y = a*numpy.exp(-x/tau)
        return y

    def __getRadialVelocity(self, listMeteors, listVolts, radialStdThresh, pairslist,  timeInterval):

        pairslist1 = list(pairslist)
        pairslist1.append((0,1))
        pairslist1.append((3,4))
        numPairs = len(pairslist1)
        #Time Lag
        timeLag = 45*10**-3
        c = 3e8
        lag = numpy.ceil(timeLag/timeInterval)
        freq = 30e6

        listMeteors1 = []

        for i in range(len(listMeteors)):
            meteorAux = listMeteors[i]
            if meteorAux[-1] == 0:
                mStart = listMeteors[i][1]
                mPeak = listMeteors[i][2]
                mLag = mPeak - mStart + lag

                #get the volt data between the start and end times of the meteor
                meteorVolts = listVolts[i]
                meteorVolts = meteorVolts.reshape(meteorVolts.shape[0], meteorVolts.shape[1], 1)

                #Get CCF
                allCCFs = self.__calculateCCF(meteorVolts, pairslist1, [-2,-1,0,1,2])

                #Method 2
                slopes = numpy.zeros(numPairs)
                time = numpy.array([-2,-1,1,2])*timeInterval
                angAllCCF = numpy.angle(allCCFs[:,[0,1,3,4],0])

                #Correct phases
                derPhaseCCF = angAllCCF[:,1:] - angAllCCF[:,0:-1]
                indDer = numpy.where(numpy.abs(derPhaseCCF) > numpy.pi)

                if indDer[0].shape[0] > 0:
                    for i in range(indDer[0].shape[0]):
                        signo = -numpy.sign(derPhaseCCF[indDer[0][i],indDer[1][i]])
                        angAllCCF[indDer[0][i],indDer[1][i]+1:] += signo*2*numpy.pi

#                     fit = scipy.stats.linregress(numpy.array([-2,-1,1,2])*timeInterval, numpy.array([phaseLagN2s[i],phaseLagN1s[i],phaseLag1s[i],phaseLag2s[i]]))
                for j in range(numPairs):
                    fit = stats.linregress(time, angAllCCF[j,:])
                    slopes[j] = fit[0]

                #Remove Outlier
#                 indOut = numpy.argmax(numpy.abs(slopes - numpy.mean(slopes)))
#                 slopes = numpy.delete(slopes,indOut)
#                 indOut = numpy.argmax(numpy.abs(slopes - numpy.mean(slopes)))
#                 slopes = numpy.delete(slopes,indOut)

                radialVelocity = -numpy.mean(slopes)*(0.25/numpy.pi)*(c/freq)
                radialError = numpy.std(slopes)*(0.25/numpy.pi)*(c/freq)
                meteorAux[-2] = radialError
                meteorAux[-3] = radialVelocity

                #Setting Error
                #Number 15: Radial Drift velocity or projected horizontal velocity exceeds 200 m/s
                if numpy.abs(radialVelocity) > 200:
                    meteorAux[-1] = 15
                #Number 12: Poor fit to CCF variation for estimation of radial drift velocity
                elif radialError > radialStdThresh:
                    meteorAux[-1] = 12

            listMeteors1.append(meteorAux)
        return listMeteors1

    def __setNewArrays(self, listMeteors, date, heiRang):

        #New arrays
        arrayMeteors = numpy.array(listMeteors)
        arrayParameters = numpy.zeros((len(listMeteors), 13))

        #Date inclusion
#         date = re.findall(r'\((.*?)\)', date)
#         date = date[0].split(',')
#         date = map(int, date)
#
#         if len(date)<6:
#             date.append(0)
#
#         date = [date[0]*10000 + date[1]*100 + date[2], date[3]*10000 + date[4]*100 + date[5]]
#         arrayDate = numpy.tile(date, (len(listMeteors), 1))
        arrayDate = numpy.tile(date, (len(listMeteors)))

        #Meteor array
#         arrayMeteors[:,0] = heiRang[arrayMeteors[:,0].astype(int)]
#         arrayMeteors = numpy.hstack((arrayDate, arrayMeteors))

        #Parameters Array
        arrayParameters[:,0] = arrayDate #Date
        arrayParameters[:,1] = heiRang[arrayMeteors[:,0].astype(int)] #Range
        arrayParameters[:,6:8] = arrayMeteors[:,-3:-1] #Radial velocity and its error
        arrayParameters[:,8:12] = arrayMeteors[:,7:11]  #Phases
        arrayParameters[:,-1] = arrayMeteors[:,-1]  #Error


        return arrayParameters

class CorrectSMPhases(Operation):

    def run(self, dataOut, phaseOffsets, hmin = 50, hmax = 150, azimuth = 45, channelPositions = None):

        arrayParameters = dataOut.data_param
        pairsList = []
        pairx = (0,1)
        pairy = (2,3)
        pairsList.append(pairx)
        pairsList.append(pairy)
        jph = numpy.zeros(4)

        phaseOffsets = numpy.array(phaseOffsets)*numpy.pi/180
    #         arrayParameters[:,8:12] = numpy.unwrap(arrayParameters[:,8:12] + phaseOffsets)
        arrayParameters[:,8:12] = numpy.angle(numpy.exp(1j*(arrayParameters[:,8:12] + phaseOffsets)))

        meteorOps = SMOperations()
        if channelPositions is None:
    #             channelPositions = [(2.5,0), (0,2.5), (0,0), (0,4.5), (-2,0)]   #T
            channelPositions = [(4.5,2), (2,4.5), (2,2), (2,0), (0,2)]   #Estrella

        pairslist0, distances = meteorOps.getPhasePairs(channelPositions)
        h = (hmin,hmax)

        arrayParameters = meteorOps.getMeteorParams(arrayParameters, azimuth, h, pairsList, distances, jph)

        dataOut.data_param = arrayParameters
        return

class SMPhaseCalibration(Operation):

    __buffer = None

    __initime = None

    __dataReady = False

    __isConfig = False

    def __checkTime(self, currentTime, initTime, paramInterval, outputInterval):

        dataTime = currentTime + paramInterval
        deltaTime = dataTime - initTime

        if deltaTime >= outputInterval or deltaTime < 0:
            return True

        return False

    def __getGammas(self, pairs, d, phases):
        gammas = numpy.zeros(2)

        for i in range(len(pairs)):

            pairi = pairs[i]

            phip3 = phases[:,pairi[0]]
            d3 = d[pairi[0]]
            phip2 = phases[:,pairi[1]]
            d2 = d[pairi[1]]
            #Calculating gamma
#             jdcos = alp1/(k*d1)
#             jgamma = numpy.angle(numpy.exp(1j*(d0*alp1/d1 - alp0)))
            jgamma = -phip2*d3/d2 - phip3
            jgamma = numpy.angle(numpy.exp(1j*jgamma))
#             jgamma[jgamma>numpy.pi] -= 2*numpy.pi
#             jgamma[jgamma<-numpy.pi] += 2*numpy.pi

            #Revised distribution
            jgammaArray = numpy.hstack((jgamma,jgamma+0.5*numpy.pi,jgamma-0.5*numpy.pi))

            #Histogram
            nBins = 64
            rmin = -0.5*numpy.pi
            rmax = 0.5*numpy.pi
            phaseHisto = numpy.histogram(jgammaArray, bins=nBins, range=(rmin,rmax))

            meteorsY = phaseHisto[0]
            phasesX = phaseHisto[1][:-1]
            width = phasesX[1] - phasesX[0]
            phasesX += width/2

            #Gaussian aproximation
            bpeak = meteorsY.argmax()
            peak = meteorsY.max()
            jmin = bpeak - 5
            jmax = bpeak + 5 + 1

            if jmin<0:
                jmin = 0
                jmax = 6
            elif jmax > meteorsY.size:
                jmin = meteorsY.size - 6
                jmax = meteorsY.size

            x0 = numpy.array([peak,bpeak,50])
            coeff = optimize.leastsq(self.__residualFunction, x0, args=(meteorsY[jmin:jmax], phasesX[jmin:jmax]))

            #Gammas
            gammas[i] = coeff[0][1]

        return gammas

    def __residualFunction(self, coeffs, y, t):

        return y - self.__gauss_function(t, coeffs)

    def __gauss_function(self, t, coeffs):

        return coeffs[0]*numpy.exp(-0.5*((t - coeffs[1]) / coeffs[2])**2)

    def __getPhases(self, azimuth, h, pairsList, d, gammas, meteorsArray):
        meteorOps = SMOperations()
        nchan = 4
        pairx = pairsList[0] #x es 0
        pairy = pairsList[1] #y es 1
        center_xangle = 0
        center_yangle = 0
        range_angle = numpy.array([10*numpy.pi,numpy.pi,numpy.pi/2,numpy.pi/4])
        ntimes = len(range_angle)

        nstepsx = 20
        nstepsy = 20

        for iz in range(ntimes):
            min_xangle = -range_angle[iz]/2 + center_xangle
            max_xangle = range_angle[iz]/2 + center_xangle
            min_yangle = -range_angle[iz]/2 + center_yangle
            max_yangle = range_angle[iz]/2 + center_yangle

            inc_x = (max_xangle-min_xangle)/nstepsx
            inc_y = (max_yangle-min_yangle)/nstepsy

            alpha_y = numpy.arange(nstepsy)*inc_y + min_yangle
            alpha_x = numpy.arange(nstepsx)*inc_x + min_xangle
            penalty = numpy.zeros((nstepsx,nstepsy))
            jph_array = numpy.zeros((nchan,nstepsx,nstepsy))
            jph = numpy.zeros(nchan)

            # Iterations looking for the offset
            for iy in range(int(nstepsy)):
                for ix in range(int(nstepsx)):
                    d3 = d[pairsList[1][0]]
                    d2 = d[pairsList[1][1]]
                    d5 = d[pairsList[0][0]]
                    d4 = d[pairsList[0][1]]

                    alp2 = alpha_y[iy]  #gamma 1
                    alp4 = alpha_x[ix]  #gamma 0

                    alp3 = -alp2*d3/d2 - gammas[1]
                    alp5 = -alp4*d5/d4 - gammas[0]
#                     jph[pairy[1]] = alpha_y[iy]
#                     jph[pairy[0]] = -gammas[1] - alpha_y[iy]*d[pairy[1]]/d[pairy[0]]

#                     jph[pairx[1]] = alpha_x[ix]
#                     jph[pairx[0]] = -gammas[0] - alpha_x[ix]*d[pairx[1]]/d[pairx[0]]
                    jph[pairsList[0][1]] = alp4
                    jph[pairsList[0][0]] = alp5
                    jph[pairsList[1][0]] = alp3
                    jph[pairsList[1][1]] = alp2
                    jph_array[:,ix,iy] = jph
#                     d = [2.0,2.5,2.5,2.0]
                    #falta chequear si va a leer bien  los meteoros
                    meteorsArray1 = meteorOps.getMeteorParams(meteorsArray, azimuth, h, pairsList, d, jph)
                    error = meteorsArray1[:,-1]
                    ind1 = numpy.where(error==0)[0]
                    penalty[ix,iy] = ind1.size

            i,j = numpy.unravel_index(penalty.argmax(), penalty.shape)
            phOffset = jph_array[:,i,j]

            center_xangle = phOffset[pairx[1]]
            center_yangle = phOffset[pairy[1]]

        phOffset = numpy.angle(numpy.exp(1j*jph_array[:,i,j]))
        phOffset = phOffset*180/numpy.pi
        return phOffset


    def run(self, dataOut, hmin, hmax, channelPositions=None, nHours = 1):

        dataOut.flagNoData = True
        self.__dataReady = False
        dataOut.outputInterval = nHours*3600

        if self.__isConfig == False:
#                 self.__initime = dataOut.datatime.replace(minute = 0, second = 0, microsecond = 03)
            #Get Initial LTC time
            self.__initime = datetime.datetime.utcfromtimestamp(dataOut.utctime)
            self.__initime = (self.__initime.replace(minute = 0, second = 0, microsecond = 0) - datetime.datetime(1970, 1, 1)).total_seconds()

            self.__isConfig = True

        if self.__buffer is None:
            self.__buffer = dataOut.data_param.copy()

        else:
            self.__buffer = numpy.vstack((self.__buffer, dataOut.data_param))

        self.__dataReady = self.__checkTime(dataOut.utctime, self.__initime, dataOut.paramInterval, dataOut.outputInterval) #Check if the buffer is ready

        if self.__dataReady:
            dataOut.utctimeInit = self.__initime
            self.__initime += dataOut.outputInterval #to erase time offset

            freq = dataOut.frequency
            c = dataOut.C #m/s
            lamb = c/freq
            k = 2*numpy.pi/lamb
            azimuth = 0
            h = (hmin, hmax)
#             pairs = ((0,1),(2,3)) #Estrella
#             pairs = ((1,0),(2,3)) #T

            if channelPositions is None:
#             channelPositions = [(2.5,0), (0,2.5), (0,0), (0,4.5), (-2,0)]   #T
                channelPositions = [(4.5,2), (2,4.5), (2,2), (2,0), (0,2)]   #Estrella
            meteorOps = SMOperations()
            pairslist0, distances = meteorOps.getPhasePairs(channelPositions)

            #Checking correct order of pairs
            pairs = []
            if distances[1] > distances[0]:
                pairs.append((1,0))
            else:
                pairs.append((0,1))

            if distances[3] > distances[2]:
                pairs.append((3,2))
            else:
                pairs.append((2,3))
#             distances1 = [-distances[0]*lamb, distances[1]*lamb, -distances[2]*lamb, distances[3]*lamb]

            meteorsArray = self.__buffer
            error = meteorsArray[:,-1]
            boolError = (error==0)|(error==3)|(error==4)|(error==13)|(error==14)
            ind1 = numpy.where(boolError)[0]
            meteorsArray = meteorsArray[ind1,:]
            meteorsArray[:,-1] = 0
            phases = meteorsArray[:,8:12]

            #Calculate Gammas
            gammas = self.__getGammas(pairs, distances, phases)
#             gammas = numpy.array([-21.70409463,45.76935864])*numpy.pi/180
            #Calculate Phases
            phasesOff = self.__getPhases(azimuth, h, pairs, distances, gammas, meteorsArray)
            phasesOff = phasesOff.reshape((1,phasesOff.size))
            dataOut.data_output = -phasesOff
            dataOut.flagNoData = False
            self.__buffer = None


        return

class SMOperations():

    def __init__(self):

        return

    def getMeteorParams(self, arrayParameters0, azimuth, h, pairsList, distances, jph):

        arrayParameters = arrayParameters0.copy()
        hmin = h[0]
        hmax = h[1]

        #Calculate AOA (Error N 3, 4)
        #JONES ET AL. 1998
        AOAthresh = numpy.pi/8
        error = arrayParameters[:,-1]
        phases = -arrayParameters[:,8:12] + jph
#         phases = numpy.unwrap(phases)
        arrayParameters[:,3:6], arrayParameters[:,-1] = self.__getAOA(phases, pairsList, distances, error, AOAthresh, azimuth)

        #Calculate Heights (Error N 13 and 14)
        error = arrayParameters[:,-1]
        Ranges = arrayParameters[:,1]
        zenith = arrayParameters[:,4]
        arrayParameters[:,2], arrayParameters[:,-1] = self.__getHeights(Ranges, zenith, error, hmin, hmax)

        #----------------------- Get Final data    ------------------------------------
#         error = arrayParameters[:,-1]
#         ind1 = numpy.where(error==0)[0]
#         arrayParameters = arrayParameters[ind1,:]

        return arrayParameters

    def __getAOA(self, phases, pairsList, directions, error, AOAthresh, azimuth):

        arrayAOA = numpy.zeros((phases.shape[0],3))
        cosdir0, cosdir = self.__getDirectionCosines(phases, pairsList,directions)

        arrayAOA[:,:2] = self.__calculateAOA(cosdir, azimuth)
        cosDirError = numpy.sum(numpy.abs(cosdir0 - cosdir), axis = 1)
        arrayAOA[:,2] = cosDirError

        azimuthAngle = arrayAOA[:,0]
        zenithAngle = arrayAOA[:,1]

        #Setting Error
        indError = numpy.where(numpy.logical_or(error == 3, error == 4))[0]
        error[indError] = 0
        #Number 3: AOA not fesible
        indInvalid = numpy.where(numpy.logical_and((numpy.logical_or(numpy.isnan(zenithAngle), numpy.isnan(azimuthAngle))),error == 0))[0]
        error[indInvalid] = 3
        #Number 4: Large difference in AOAs obtained from different antenna baselines
        indInvalid = numpy.where(numpy.logical_and(cosDirError > AOAthresh,error == 0))[0]
        error[indInvalid] = 4
        return arrayAOA, error

    def __getDirectionCosines(self, arrayPhase, pairsList, distances):

        #Initializing some variables
        ang_aux = numpy.array([-8,-7,-6,-5,-4,-3,-2,-1,0,1,2,3,4,5,6,7,8])*2*numpy.pi
        ang_aux = ang_aux.reshape(1,ang_aux.size)

        cosdir = numpy.zeros((arrayPhase.shape[0],2))
        cosdir0 = numpy.zeros((arrayPhase.shape[0],2))


        for i in range(2):
            ph0 = arrayPhase[:,pairsList[i][0]]
            ph1 = arrayPhase[:,pairsList[i][1]]
            d0 = distances[pairsList[i][0]]
            d1 = distances[pairsList[i][1]]

            ph0_aux = ph0 + ph1
            ph0_aux = numpy.angle(numpy.exp(1j*ph0_aux))
#             ph0_aux[ph0_aux > numpy.pi] -= 2*numpy.pi
#             ph0_aux[ph0_aux < -numpy.pi] += 2*numpy.pi
            #First Estimation
            cosdir0[:,i] = (ph0_aux)/(2*numpy.pi*(d0 - d1))

            #Most-Accurate Second Estimation
            phi1_aux =  ph0 - ph1
            phi1_aux = phi1_aux.reshape(phi1_aux.size,1)
            #Direction Cosine 1
            cosdir1 = (phi1_aux + ang_aux)/(2*numpy.pi*(d0 + d1))

            #Searching the correct Direction Cosine
            cosdir0_aux = cosdir0[:,i]
            cosdir0_aux = cosdir0_aux.reshape(cosdir0_aux.size,1)
            #Minimum Distance
            cosDiff = (cosdir1 - cosdir0_aux)**2
            indcos = cosDiff.argmin(axis = 1)
            #Saving Value obtained
            cosdir[:,i] = cosdir1[numpy.arange(len(indcos)),indcos]

        return cosdir0, cosdir

    def __calculateAOA(self, cosdir, azimuth):
        cosdirX = cosdir[:,0]
        cosdirY = cosdir[:,1]

        zenithAngle = numpy.arccos(numpy.sqrt(1 - cosdirX**2 - cosdirY**2))*180/numpy.pi
        azimuthAngle = numpy.arctan2(cosdirX,cosdirY)*180/numpy.pi + azimuth#0 deg north, 90 deg east
        angles = numpy.vstack((azimuthAngle, zenithAngle)).transpose()

        return angles

    def __getHeights(self, Ranges, zenith, error, minHeight, maxHeight):

        Ramb = 375  #Ramb = c/(2*PRF)
        Re = 6371   #Earth Radius
        heights = numpy.zeros(Ranges.shape)

        R_aux = numpy.array([0,1,2])*Ramb
        R_aux = R_aux.reshape(1,R_aux.size)

        Ranges = Ranges.reshape(Ranges.size,1)

        Ri = Ranges + R_aux
        hi = numpy.sqrt(Re**2 + Ri**2 + (2*Re*numpy.cos(zenith*numpy.pi/180)*Ri.transpose()).transpose()) - Re

        #Check if there is a height between 70 and 110 km
        h_bool = numpy.sum(numpy.logical_and(hi > minHeight, hi < maxHeight), axis = 1)
        ind_h = numpy.where(h_bool == 1)[0]

        hCorr = hi[ind_h, :]
        ind_hCorr = numpy.where(numpy.logical_and(hi > minHeight, hi < maxHeight))

        hCorr = hi[ind_hCorr][:len(ind_h)]
        heights[ind_h] = hCorr

        #Setting Error
        #Number 13: Height unresolvable echo: not valid height within 70 to 110 km
        #Number 14: Height ambiguous echo: more than one possible height within 70 to 110 km
        indError = numpy.where(numpy.logical_or(error == 13, error == 14))[0]
        error[indError] = 0
        indInvalid2 = numpy.where(numpy.logical_and(h_bool > 1, error == 0))[0]
        error[indInvalid2] = 14
        indInvalid1 = numpy.where(numpy.logical_and(h_bool == 0, error == 0))[0]
        error[indInvalid1] = 13

        return heights, error

    def getPhasePairs(self, channelPositions):
        chanPos = numpy.array(channelPositions)
        listOper = list(itertools.combinations(list(range(5)),2))

        distances = numpy.zeros(4)
        axisX = []
        axisY = []
        distX = numpy.zeros(3)
        distY = numpy.zeros(3)
        ix = 0
        iy = 0

        pairX = numpy.zeros((2,2))
        pairY = numpy.zeros((2,2))

        for i in range(len(listOper)):
            pairi = listOper[i]

            posDif = numpy.abs(chanPos[pairi[0],:] - chanPos[pairi[1],:])

            if posDif[0] == 0:
                axisY.append(pairi)
                distY[iy] = posDif[1]
                iy += 1
            elif posDif[1] == 0:
                axisX.append(pairi)
                distX[ix] = posDif[0]
                ix += 1

        for i in range(2):
            if i==0:
                dist0 = distX
                axis0 = axisX
            else:
                dist0 = distY
                axis0 = axisY

            side = numpy.argsort(dist0)[:-1]
            axis0 = numpy.array(axis0)[side,:]
            chanC = int(numpy.intersect1d(axis0[0,:], axis0[1,:])[0])
            axis1 = numpy.unique(numpy.reshape(axis0,4))
            side = axis1[axis1 != chanC]
            diff1 = chanPos[chanC,i] - chanPos[side[0],i]
            diff2 = chanPos[chanC,i] - chanPos[side[1],i]
            if diff1<0:
                chan2 = side[0]
                d2 = numpy.abs(diff1)
                chan1 = side[1]
                d1 = numpy.abs(diff2)
            else:
                chan2 = side[1]
                d2 = numpy.abs(diff2)
                chan1 = side[0]
                d1 = numpy.abs(diff1)

            if i==0:
                chanCX = chanC
                chan1X = chan1
                chan2X = chan2
                distances[0:2] = numpy.array([d1,d2])
            else:
                chanCY = chanC
                chan1Y = chan1
                chan2Y = chan2
                distances[2:4] = numpy.array([d1,d2])
#         axisXsides = numpy.reshape(axisX[ix,:],4)
#
#         channelCentX = int(numpy.intersect1d(pairX[0,:], pairX[1,:])[0])
#         channelCentY = int(numpy.intersect1d(pairY[0,:], pairY[1,:])[0])
#
#         ind25X = numpy.where(pairX[0,:] != channelCentX)[0][0]
#         ind20X = numpy.where(pairX[1,:] != channelCentX)[0][0]
#         channel25X = int(pairX[0,ind25X])
#         channel20X = int(pairX[1,ind20X])
#         ind25Y = numpy.where(pairY[0,:] != channelCentY)[0][0]
#         ind20Y = numpy.where(pairY[1,:] != channelCentY)[0][0]
#         channel25Y = int(pairY[0,ind25Y])
#         channel20Y = int(pairY[1,ind20Y])

#         pairslist = [(channelCentX, channel25X),(channelCentX, channel20X),(channelCentY,channel25Y),(channelCentY, channel20Y)]
        pairslist = [(chanCX, chan1X),(chanCX, chan2X),(chanCY,chan1Y),(chanCY, chan2Y)]

        return pairslist, distances
#     def __getAOA(self, phases, pairsList, error, AOAthresh, azimuth):
#
#         arrayAOA = numpy.zeros((phases.shape[0],3))
#         cosdir0, cosdir = self.__getDirectionCosines(phases, pairsList)
#
#         arrayAOA[:,:2] = self.__calculateAOA(cosdir, azimuth)
#         cosDirError = numpy.sum(numpy.abs(cosdir0 - cosdir), axis = 1)
#         arrayAOA[:,2] = cosDirError
#
#         azimuthAngle = arrayAOA[:,0]
#         zenithAngle = arrayAOA[:,1]
#
#         #Setting Error
#         #Number 3: AOA not fesible
#         indInvalid = numpy.where(numpy.logical_and((numpy.logical_or(numpy.isnan(zenithAngle), numpy.isnan(azimuthAngle))),error == 0))[0]
#         error[indInvalid] = 3
#         #Number 4: Large difference in AOAs obtained from different antenna baselines
#         indInvalid = numpy.where(numpy.logical_and(cosDirError > AOAthresh,error == 0))[0]
#         error[indInvalid] = 4
#         return arrayAOA, error
#
#     def __getDirectionCosines(self, arrayPhase, pairsList):
#
#         #Initializing some variables
#         ang_aux = numpy.array([-8,-7,-6,-5,-4,-3,-2,-1,0,1,2,3,4,5,6,7,8])*2*numpy.pi
#         ang_aux = ang_aux.reshape(1,ang_aux.size)
#
#         cosdir = numpy.zeros((arrayPhase.shape[0],2))
#         cosdir0 = numpy.zeros((arrayPhase.shape[0],2))
#
#
#         for i in range(2):
#             #First Estimation
#             phi0_aux = arrayPhase[:,pairsList[i][0]] + arrayPhase[:,pairsList[i][1]]
#             #Dealias
#             indcsi = numpy.where(phi0_aux > numpy.pi)
#             phi0_aux[indcsi] -= 2*numpy.pi
#             indcsi = numpy.where(phi0_aux < -numpy.pi)
#             phi0_aux[indcsi] += 2*numpy.pi
#             #Direction Cosine 0
#             cosdir0[:,i] = -(phi0_aux)/(2*numpy.pi*0.5)
#
#             #Most-Accurate Second Estimation
#             phi1_aux =  arrayPhase[:,pairsList[i][0]] - arrayPhase[:,pairsList[i][1]]
#             phi1_aux = phi1_aux.reshape(phi1_aux.size,1)
#             #Direction Cosine 1
#             cosdir1 = -(phi1_aux + ang_aux)/(2*numpy.pi*4.5)
#
#             #Searching the correct Direction Cosine
#             cosdir0_aux = cosdir0[:,i]
#             cosdir0_aux = cosdir0_aux.reshape(cosdir0_aux.size,1)
#             #Minimum Distance
#             cosDiff = (cosdir1 - cosdir0_aux)**2
#             indcos = cosDiff.argmin(axis = 1)
#             #Saving Value obtained
#             cosdir[:,i] = cosdir1[numpy.arange(len(indcos)),indcos]
#
#         return cosdir0, cosdir
#
#     def __calculateAOA(self, cosdir, azimuth):
#         cosdirX = cosdir[:,0]
#         cosdirY = cosdir[:,1]
#
#         zenithAngle = numpy.arccos(numpy.sqrt(1 - cosdirX**2 - cosdirY**2))*180/numpy.pi
#         azimuthAngle = numpy.arctan2(cosdirX,cosdirY)*180/numpy.pi + azimuth #0 deg north, 90 deg east
#         angles = numpy.vstack((azimuthAngle, zenithAngle)).transpose()
#
#         return angles
#
#     def __getHeights(self, Ranges, zenith, error, minHeight, maxHeight):
#
#         Ramb = 375  #Ramb = c/(2*PRF)
#         Re = 6371   #Earth Radius
#         heights = numpy.zeros(Ranges.shape)
#
#         R_aux = numpy.array([0,1,2])*Ramb
#         R_aux = R_aux.reshape(1,R_aux.size)
#
#         Ranges = Ranges.reshape(Ranges.size,1)
#
#         Ri = Ranges + R_aux
#         hi = numpy.sqrt(Re**2 + Ri**2 + (2*Re*numpy.cos(zenith*numpy.pi/180)*Ri.transpose()).transpose()) - Re
#
#         #Check if there is a height between 70 and 110 km
#         h_bool = numpy.sum(numpy.logical_and(hi > minHeight, hi < maxHeight), axis = 1)
#         ind_h = numpy.where(h_bool == 1)[0]
#
#         hCorr = hi[ind_h, :]
#         ind_hCorr = numpy.where(numpy.logical_and(hi > minHeight, hi < maxHeight))
#
#         hCorr = hi[ind_hCorr]
#         heights[ind_h] = hCorr
#
#         #Setting Error
#         #Number 13: Height unresolvable echo: not valid height within 70 to 110 km
#         #Number 14: Height ambiguous echo: more than one possible height within 70 to 110 km
#
#         indInvalid2 = numpy.where(numpy.logical_and(h_bool > 1, error == 0))[0]
#         error[indInvalid2] = 14
#         indInvalid1 = numpy.where(numpy.logical_and(h_bool == 0, error == 0))[0]
#         error[indInvalid1] = 13
#
#         return heights, error


class WeatherRadar(Operation):
    '''
    Function tat implements Weather Radar operations-
    Input:
    Output:
    Parameters affected:

    Conversion Watt
    Referencia
    https://www.tek.com/en/blog/calculating-rf-power-iq-samples

    data_param = (nCh, 8, nHeis)
    S, V, W, SNR, Z, D, P, R
    Power, Velocity, Spectral width, SNR, Reflectivity, Differential reflectivity, PHI DP, RHO HV
    '''
    isConfig  = False
    variableList = None

    def __init__(self):
        Operation.__init__(self)

    def setup(self,dataOut,variableList= None,Pt=0,Gt=0,Gr=0,Glna=0,lambda_=0, aL=0,
                tauW= 0,thetaT=0,thetaR=0,Km =0,CR_Flag=False,min_index=0,sesgoZD=0):

        self.nCh      = dataOut.nChannels
        self.nHeis    = dataOut.nHeights
        self.min_index= min_index
        deltaHeight   = dataOut.heightList[1] - dataOut.heightList[0]
        #self.Range    = numpy.arange(dataOut.nHeights)*deltaHeight + dataOut.heightList[0]+min_index*deltaHeight
        self.Range    = dataOut.heightList
        self.Range    = self.Range.reshape(1,self.nHeis)
        self.Range    = numpy.tile(self.Range,[self.nCh,1])
        '''-----------1 Constante del Radar----------'''
        self.Pt       = Pt # Pmax =200 W x DC=(0.2 useg/400useg)
        self.Gt       = Gt  # 38 db
        self.Gr       = Gr  # 38 dB
        self.Glna     = Glna # 60 dB
        self.lambda_  = lambda_ # 3.2 cm 0.032 m.
        self.aL       = aL # Perdidas
        self.tauW     = tauW #ancho de pulso 0.2useg pulso corto.
        self.thetaT   = thetaT # 1.8º -- 0.0314 rad
        self.thetaR   = thetaR # 1.8ª --0.0314 rad
        self.Km       = Km
        self.CR_Flag  = CR_Flag
        self.sesgoZD  = sesgoZD
        Numerator     = ((4*numpy.pi)**3 * aL**2 * 16 *numpy.log(2)*(10**18))
        Denominator   = (Pt *(10**(Gt/10.0))*(10**(Gr/10.0))*(10**(Glna/10.0))* lambda_**2 * SPEED_OF_LIGHT * tauW * numpy.pi*thetaT*thetaR)
        self.RadarConstant = Numerator/Denominator
        self.variableList  = variableList
        if self.variableList== None:
            self.variableList= ['Z','D','R','P']

    def setMoments(self, dataOut):
        # S, V, W, SNR, Z, D, P, R
        type  = dataOut.inputUnit
        nCh   = dataOut.nChannels
        nHeis = dataOut.nHeights
        data_param = numpy.zeros((nCh, 8, nHeis))
        if type == "Voltage":
            factor            = 1
            #print("SHAPE:",dataOut.dataPP_POW.shape)
            data_param[:,0,:] = dataOut.dataPP_POW/(factor)#dataOut.dataPP_POWER/(factor)
            data_param[:,1,:] = dataOut.dataPP_DOP
            data_param[:,2,:] = dataOut.dataPP_WIDTH
            data_param[:,3,:] = dataOut.dataPP_SNR
        if type == "Spectra":
            factor = dataOut.normFactor
            data_param[:,0,:] = dataOut.data_pow/(factor)
            data_param[:,1,:] = dataOut.data_dop
            data_param[:,2,:] = dataOut.data_width
            data_param[:,3,:] = dataOut.data_snr
        return data_param

    def getCoeficienteCorrelacionROhv_R(self,dataOut):
        type  = dataOut.inputUnit
        nHeis = dataOut.nHeights
        data_RhoHV_R = numpy.zeros((nHeis))
        if type == "Voltage":
            avgcoherenceComplex= dataOut.dataPP_CCF
            data_RhoHV_R = numpy.abs(avgcoherenceComplex)
        if type == "Spectra":
            data_RhoHV_R = dataOut.getCoherence()

        return data_RhoHV_R

    def getFasediferencialPhiD_P(self,dataOut,phase= True):
        type  = dataOut.inputUnit
        nHeis = dataOut.nHeights
        data_PhiD_P = numpy.zeros((nHeis))
        if type == "Voltage":
            avgcoherenceComplex= dataOut.dataPP_CCF
            if phase:
                data_PhiD_P = numpy.arctan2(avgcoherenceComplex.imag,
                                     avgcoherenceComplex.real) * 180 / numpy.pi
        if type == "Spectra":
            data_PhiD_P = dataOut.getCoherence(phase = phase)

        return data_PhiD_P

    def getReflectividad_D(self,dataOut,type):
        '''-----------------------------Potencia de Radar -Signal S-----------------------------'''

        Pr = dataOut.data_param[:,0,:]
        '''---------------------------- Calculo de Noise y threshold para Reflectividad---------'''

        Pr = Pr/100.0 # Conversion Watt
        '''-----------2 Reflectividad del Radar y Factor de Reflectividad------'''
        if not self.CR_Flag:
            self.n_radar       = numpy.zeros((self.nCh,self.nHeis))
            self.Z_radar       = numpy.zeros((self.nCh,self.nHeis))
            #for R in range(self.nHeis):
            #    self.n_radar[:,R] = self.RadarConstant*Pr[:,R]* (self.Range[:,R]*(10**3))**2

            #    self.Z_radar[:,R] = self.n_radar[:,R]* self.lambda_**4/( numpy.pi**5 * self.Km**2)

            self.n_radar[:,:] = self.RadarConstant*Pr[:,:]* (self.Range[:,:]*(10**3))**2
            self.Z_radar[:,:] = self.n_radar[:,:]* self.lambda_**4/( numpy.pi**5 * self.Km**2)
            
            '''----------- Factor de Reflectividad Equivalente lamda_ < 10 cm , lamda_= 3.2cm-------'''
            Zeh  =  self.Z_radar

            if self.Pt<0.3:
                factor=1
            else:
                factor=28#23.072

            dBZeh = 10*numpy.log10(Zeh) + factor
        else:
            self.Z_radar       = numpy.zeros((self.nCh,self.nHeis))

            #for R in range(self.nHeis):
            #    self.Z_radar[0,R]= 10*numpy.log10(Pr[0,R])+20*numpy.log10(self.Range[0,R]*10**3)+67.41-10*numpy.log10(self.Pt)-59-10*numpy.log10(self.tauW)#63.58,65.26,68.91
            #    self.Z_radar[1,R]= 10*numpy.log10(Pr[1,R])+20*numpy.log10(self.Range[1,R]*10**3)+67.17-10*numpy.log10(self.Pt)-59-10*numpy.log10(self.tauW)#64.26,65.79,62.33
            
            self.Z_radar[0,:]= 10*numpy.log10(Pr[0,:])+20*numpy.log10(self.Range[0,:]*10**3)+67.41-10*numpy.log10(self.Pt)-59-10*numpy.log10(self.tauW)#63.58,65.26,68.91
            self.Z_radar[1,:]= 10*numpy.log10(Pr[1,:])+20*numpy.log10(self.Range[1,:]*10**3)+67.17-10*numpy.log10(self.Pt)-59-10*numpy.log10(self.tauW)#63.58,65.26,68.91

            dBZeh= self.Z_radar

        if type=='N':
            return dBZeh
        elif type=='D':
            Zdb_D = dBZeh[0] - dBZeh[1]- self.sesgoZD
            return Zdb_D

    def getRadialVelocity_V(self,dataOut):
        velRadial_V = dataOut.data_param[:,1,:]
        return velRadial_V

    def getAnchoEspectral_W(self,dataOut):
        Sigmav_W = dataOut.data_param[:,2,:]
        return Sigmav_W


    def run(self,dataOut,variableList=None,Pt=1.58,Gt=38.5,Gr=38.5,Glna=59.0,lambda_=0.032, aL=1,
                tauW= 0.2,thetaT=0.0314,thetaR=0.0314,Km =0.93,CR_Flag=0,min_index=0,sesgoZD=0):
        if not self.isConfig:
            self.setup(dataOut= dataOut, variableList=variableList,Pt=Pt,Gt=Gt,Gr=Gr,Glna=Glna,lambda_=lambda_, aL=aL,
                        tauW= tauW,thetaT=thetaT,thetaR=thetaR,Km =Km,CR_Flag=CR_Flag,min_index=min_index,sesgoZD=sesgoZD)
            self.isConfig = True

        dataOut.data_param = self.setMoments(dataOut)

        for i in range(len(self.variableList)):
            if self.variableList[i] == 'Z':
                dataOut.data_param[:,4,:] = self.getReflectividad_D(dataOut=dataOut,type='N')
            if self.variableList[i] == 'D' and dataOut.nChannels>1:
                dataOut.data_param[:,5,:] = self.getReflectividad_D(dataOut=dataOut,type='D')
            if self.variableList[i] == 'P' and dataOut.nChannels>1:
                dataOut.data_param[:,6,:] = self.getFasediferencialPhiD_P(dataOut=dataOut, phase=True)
            if self.variableList[i] == 'R' and dataOut.nChannels>1:
                dataOut.data_param[:,7,:] = self.getCoeficienteCorrelacionROhv_R(dataOut)

        return dataOut

class PedestalInformation(Operation):

    def __init__(self):
        Operation.__init__(self)
        self.filename = False
        self.delay = 32
        self.nTries = 3
        self.nFiles = 5
        self.flagAskMode = False

    def find_file(self, timestamp):

        dt = datetime.datetime.utcfromtimestamp(timestamp)
        path = os.path.join(self.path, dt.strftime('%Y-%m-%dT%H-00-00'))

        if not os.path.exists(path):
            return False
        fileList = glob.glob(os.path.join(path, '*.h5'))
        fileList.sort()
        return fileList

    def find_next_file(self):

        while True:
            if self.utctime < self.utcfile:
                self.flagNoData = True
                break
            self.flagNoData = False
            file_size = len(self.fp['Data']['utc'])
            if self.utctime < self.utcfile+file_size*self.interval:
                break
            dt = datetime.datetime.utcfromtimestamp(self.utcfile)
            if dt.second > 0:
                self.utcfile -= dt.second
            self.utcfile += self.samples*self.interval
            dt = datetime.datetime.utcfromtimestamp(self.utcfile)
            path = os.path.join(self.path, dt.strftime('%Y-%m-%dT%H-00-00'))
            self.filename = os.path.join(path, 'pos@{}.000.h5'.format(int(self.utcfile)))

            for i in range(self.nFiles):
                ok = False
                for j in range(self.nTries):
                    ok = False
                    try:
                        if not os.path.exists(self.filename):
                            log.warning('Waiting {}s for position files...'.format(self.delay), self.name)
                            time.sleep(1)
                            continue
                        self.fp.close()
                        self.fp = h5py.File(self.filename, 'r')
                        self.ele = self.fp['Data']['ele_pos'][:]
                        self.azi = self.fp['Data']['azi_pos'][:] + 26.27 #+ self.heading
                        self.azi[self.azi>360] = self.azi[self.azi>360] - 360
                        self.time_pedestal = self.fp['Data']['utc'][:] # N 1.5
                        log.log('Opening file: {}'.format(self.filename), self.name)
                        ok = True
                        break
                    except Exception as e:
                        log.warning('Waiting {}s for position file to be ready...'.format(self.delay), self.name)
                        time.sleep(self.delay)
                        continue
                if ok:
                    break
                log.warning('Trying next file...', self.name)
                self.utcfile += self.samples*self.interval
                dt = datetime.datetime.utcfromtimestamp(self.utcfile)
                path = os.path.join(self.path, dt.strftime('%Y-%m-%dT%H-00-00'))
                self.filename = os.path.join(path, 'pos@{}.000.h5'.format(int(self.utcfile)))
            if not ok:
                log.error('No new position files found in {}'.format(path))
                raise IOError('No new position files found in {}'.format(path))

    def get_values(self):

        if self.flagNoData:
            return numpy.nan, numpy.nan, numpy.nan, numpy.nan #,numpy.nan #Should be self.mode? N 2
        else:
            index = int((self.utctime-self.utcfile)/self.interval)
            try:
                return self.azi[index], self.ele[index], None, self.time_pedestal[index] #,self.time_pedesal[index]    N 3
            except:
                return numpy.nan, numpy.nan, numpy.nan, numpy.nan #,numpy.nan N 4

    def setup(self, dataOut, path, conf, samples, interval, mode, heading):

        self.path = path
        self.conf = conf
        self.samples = samples
        self.interval = interval
        self.mode = mode
        self.heading = heading
        if mode is None:
            self.flagAskMode = True
        N = 0
        while True:
            if N == self.nTries+1:
                log.error('No position files found in {}'.format(path), self.name)
                raise IOError('No position files found in {}'.format(path))
            filelist = self.find_file(dataOut.utctime)

            if filelist == 0:
                N += 1
                log.warning('Waiting {}s for position files...'.format(self.delay), self.name)
                time.sleep(self.delay)
                continue
            self.filename = filelist[0]
            try:
                self.fp = h5py.File(self.filename, 'r')
                self.utcfile = int(self.filename.split('/')[-1][4:14])

                self.ele = self.fp['Data']['ele_pos'][:]
                self.azi = self.fp['Data']['azi_pos'][:] + 26.27 + self.heading
                self.azi[self.azi>360] = self.azi[self.azi>360] - 360
                self.time_pedestal = self.fp['Data']['utc'][:] # N 1
                break
            except:
                log.warning('Waiting {}s for position file to be ready...'.format(self.delay), self.name)
                time.sleep(self.delay)

    def run(self, dataOut, path, conf=None, samples=1500, interval=0.04, time_offset=0, mode=None, heading=0):

        if not self.isConfig:
            self.setup(dataOut, path, conf, samples, interval, mode, heading)
            self.isConfig   = True

        self.utctime = dataOut.utctime + time_offset

        self.find_next_file()

        #az, el, scan = self.get_values()
        az, el, scan,time_pedestal = self.get_values() # N 5

        dataOut.flagNoData = False
        if numpy.isnan(az) or numpy.isnan(el) :
            dataOut.flagNoData = True
            return dataOut

        dataOut.azimuth =  round(az, 2)
        dataOut.elevation = round(el, 2)
        dataOut.mode_op = scan
        dataOut.time_pedestal = round(time_pedestal,2)   # N 6
        #log.log("TIME-----------------{}".format(self.delay),dataOut.time_pedestal)
        return dataOut

class Block360(Operation):
    '''
    '''
    isConfig       = False
    __profIndex    = 0
    __initime      = None
    __lastdatatime = None
    __buffer       = None
    __dataReady    = False
    n              = None
    index          = 0
    mode           = None

    def __init__(self,**kwargs):
        Operation.__init__(self,**kwargs)

    def setup(self, dataOut, attr, angles,horario,heading,bottom):
        '''
        n= Numero de PRF's de entrada
        '''
        self.__initime        = None
        self.__lastdatatime   = 0
        self.__dataReady      = False
        self.__buffer         = 0
        self.index            = 0
        self.attr = attr
        self.__buffer  = []
        self.azi       = []
        self.ele       = []
        self.__noise   = []
        self.__time_pedestal = [] # c1
        self.angles = angles
        self.horario= horario
        self.heading = heading
        self.bottom  = bottom

    def putData(self, data, attr):
        '''
        Add a profile to he __buffer and increase in one the __profiel Index
        '''
        tmp= getattr(data, attr)
        self.__buffer.append(tmp)
        self.azi.append(data.azimuth)
        self.ele.append(data.elevation)
        self.__time_pedestal.append(data.time_pedestal) # c2        
        try:
            #print("SHOW ------", type(data.dataPP_NOISE),data.dataPP_NOISE.shape,"value:",data.dataPP_NOISE)
            self.__noise.append(data.dataPP_NOISE)
        except:
            #print("SHOW ------", type(data.noise),data.noise.shape,"value:",data.noise)
            self.__noise.append(data.noise)
        self.__profIndex  += 1

    def pushData(self, data, case_flag):
        '''
        '''

        data_360 = numpy.array(self.__buffer).transpose(1, 2, 0, 3)
        data_p   = numpy.array(self.azi)
        data_e   = numpy.array(self.ele)
        data_n   = numpy.array(self.__noise)
        time_pedestal  = numpy.array(self.__time_pedestal) #c3
        n   = self.__profIndex

        self.__buffer = []
        self.azi      = []
        self.ele      = []
        self.__noise  = []
        self.__time_pedestal = [] # c4
        self.__profIndex = 0

        if case_flag in (0, 1, -1):
            self.putData(data=data, attr = self.attr)

        return data_360, n, data_p, data_e, data_n ,time_pedestal #time_pedestal c5

    def byProfiles(self, dataOut):

        self.__dataReady = False
        data_360 =  []
        data_p = None
        data_e = None
        data_n = None
        time_pedestal = None # c6

        self.putData(data=dataOut, attr = self.attr)

        if self.__profIndex > 5:
            case_flag = self.checkcase()

            if self.flagMode == 1: #'AZI':
                if case_flag == 0: #Ya giró
                    self.__buffer.pop() #Erase last data
                    self.azi.pop()
                    self.ele.pop()
                    self.__time_pedestal.pop() # c7
                    data_360 ,n,data_p,data_e,data_n,time_pedestal = self.pushData(dataOut, case_flag) # time_pedestal c8
                    if len(data_p)>350:
                        self.__dataReady = True
            elif self.flagMode == 0: #'ELE'
                if case_flag == 1: #Bajada
                    self.__buffer.pop() #Erase last data
                    self.azi.pop()
                    self.ele.pop()
                    self.__time_pedestal.pop() #c9
                    data_360, n, data_p, data_e, data_n,time_pedestal  = self.pushData(dataOut, case_flag) # time_pedestal c10
                    self.__dataReady = True
                if case_flag == -1: #Subida
                    self.__buffer.pop() #Erase last data
                    self.azi.pop()
                    self.ele.pop()
                    self.__time_pedestal.pop() # time_pedestal c11
                    data_360, n, data_p, data_e, data_n, time_pedestal  = self.pushData(dataOut, case_flag) # time_pedestal c12
                    #self.__dataReady = True

        return data_360, data_p, data_e, data_n ,time_pedestal  #time_pedestal c13


    def blockOp(self, dataOut, datatime= None):
        if self.__initime == None:
            self.__initime = datatime
        data_360, data_p, data_e, data_n,time_pedestal = self.byProfiles(dataOut) # time_pedestal c14
        self.__lastdatatime = datatime

        avgdatatime = self.__initime
        if self.n==1:
            avgdatatime = datatime

        self.__initime = datatime
        return data_360, avgdatatime, data_p, data_e, data_n ,time_pedestal # time_pedestal c15

    def checkcase(self):

        sigma_ele = numpy.nanstd(self.ele[-5:])
        sigma_azi = numpy.nanstd(self.azi[-5:])

        if sigma_ele<.5 and sigma_azi<.5:
            if sigma_ele<sigma_azi:
                self.flagMode = 1
                self.mode_op = 'PPI'
            else:
                self.flagMode = 0
                self.mode_op = 'RHI'
        elif sigma_ele < .5:
            self.flagMode = 1
            self.mode_op = 'PPI'
        elif sigma_azi < .5:
            self.flagMode = 0
            self.mode_op = 'RHI'
        else:
            self.flagMode = None
            self.mode_op = 'None'

        if self.flagMode == 1: #'AZI'
            start  = self.azi[-2]
            end    = self.azi[-1]
            diff_angle = (end-start)
            if self.horario== True:
               if diff_angle < 0: #Ya giró
                   return 0
            else:
               if diff_angle > 0: #Ya giró
                   return 0
        elif self.flagMode == 0: #'ELE'

            start  = self.ele[-3]
            middle = self.ele[-2]
            end    = self.ele[-1]

            if end < self.bottom:
                return 1
            elif (middle>start and end<middle):
                return -1

    def run(self, dataOut, attr_data='dataPP_POWER', runNextOp = False, angles=[],horario=True,heading=0,bottom=0,**kwargs):

        dataOut.attr_data = attr_data
        dataOut.runNextOp = runNextOp

        if not self.isConfig:
            self.setup(dataOut=dataOut, attr=attr_data, angles=angles,horario=horario, heading=heading,bottom=bottom,**kwargs)
            self.isConfig   = True

        data_360, avgdatatime, data_p, data_e, data_n,time_pedestal = self.blockOp(dataOut, dataOut.utctime) # time_pedestal c16

        dataOut.flagNoData = True
        if self.__dataReady:
            mean_az = numpy.mean(data_p[25:-25])
            mean_el = numpy.mean(data_e[25:-25])
            if round(mean_az,1) in angles or round(mean_el,1) in angles:
                setattr(dataOut, attr_data, data_360 )
                dataOut.data_azi   = data_p+self.heading
                dataOut.data_azi[dataOut.data_azi>360]=dataOut.data_azi[dataOut.data_azi>360]-360
                dataOut.data_ele   = data_e
                dataOut.radar_sweep_time  = time_pedestal # time_pedestal c17
                dataOut.utctime    = avgdatatime
                dataOut.data_noise = data_n
                dataOut.flagNoData = False
                dataOut.flagMode   = self.flagMode
                dataOut.mode_op    = self.mode_op
            else:
                log.warning('Skipping angle {} / {}'.format(round(mean_az,1), round(mean_el,1)))

        return dataOut

class MergeProc(ProcessingUnit):

    def __init__(self):
        ProcessingUnit.__init__(self)

    def run(self, attr_data, mode=0, index=0):

        #exit(1)
        self.dataOut = getattr(self, self.inputs[0])
        data_inputs = [getattr(self, attr) for attr in self.inputs]
        #print(data_inputs)
        #print(numpy.shape([getattr(data, attr_data) for data in data_inputs][1]))
        #exit(1)
        if mode==0:
            data = numpy.concatenate([getattr(data, attr_data) for data in data_inputs])
            setattr(self.dataOut, attr_data, data)

        if mode==1: #Hybrid
            #data = numpy.concatenate([getattr(data, attr_data) for data in data_inputs],axis=1)
            #setattr(self.dataOut, attr_data, data)
            setattr(self.dataOut, 'dataLag_spc', [getattr(data, attr_data) for data in data_inputs][0])
            setattr(self.dataOut, 'dataLag_spc_LP', [getattr(data, attr_data) for data in data_inputs][1])
            setattr(self.dataOut, 'dataLag_cspc', [getattr(data, attr_data_2) for data in data_inputs][0])
            setattr(self.dataOut, 'dataLag_cspc_LP', [getattr(data, attr_data_2) for data in data_inputs][1])
            #setattr(self.dataOut, 'nIncohInt', [getattr(data, attr_data_3) for data in data_inputs][0])
            #setattr(self.dataOut, 'nIncohInt_LP', [getattr(data, attr_data_3) for data in data_inputs][1])
            '''
            print(self.dataOut.dataLag_spc_LP.shape)
            print(self.dataOut.dataLag_cspc_LP.shape)
            exit(1)
            '''

            #self.dataOut.dataLag_spc_LP = numpy.transpose(self.dataOut.dataLag_spc_LP[0],(2,0,1))
            #self.dataOut.dataLag_cspc_LP = numpy.transpose(self.dataOut.dataLag_cspc_LP,(3,1,2,0))
            '''
            print("Merge")
            print(numpy.shape(self.dataOut.dataLag_spc))
            print(numpy.shape(self.dataOut.dataLag_spc_LP))
            print(numpy.shape(self.dataOut.dataLag_cspc))
            print(numpy.shape(self.dataOut.dataLag_cspc_LP))
            exit(1)
            '''
            #print(numpy.sum(self.dataOut.dataLag_spc_LP[2,:,164])/128)
            #print(numpy.sum(self.dataOut.dataLag_cspc_LP[0,:,30,1])/128)
            #exit(1)
            #print(self.dataOut.NDP)
            #print(self.dataOut.nNoiseProfiles)

            #self.dataOut.nIncohInt_LP = 128
            self.dataOut.nProfiles_LP = 128#self.dataOut.nIncohInt_LP
            self.dataOut.nIncohInt_LP = self.dataOut.nIncohInt
            self.dataOut.NLAG = 16
            self.dataOut.NRANGE = 200
            self.dataOut.NSCAN = 128
            #print(numpy.shape(self.dataOut.data_spc))

        if mode==2: #HAE 2022
            data = numpy.sum([getattr(data, attr_data) for data in data_inputs],axis=0)
            setattr(self.dataOut, attr_data, data)

            self.dataOut.nIncohInt *= 2
            self.dataOut.freqRange = self.dataOut.getFreqRange(1)/1000.

        if mode==7: #RM

            f = [getattr(data, attr_data) for data in data_inputs][0][:,:,:,0:index]
            g = [getattr(data, attr_data) for data in data_inputs][1][:,:,:,index:]
            data = numpy.concatenate((f,g), axis=3)
            setattr(self.dataOut, attr_data, data)

            # snr
            # self.dataOut.data_snr = numpy.concatenate((data_inputs[0].data_snr, data_inputs[1].data_snr), axis=2)

            # ranges
            # dh = self.dataOut.heightList[1]-self.dataOut.heightList[0]
            # heightList_2  = (self.dataOut.heightList[-1]+dh) + numpy.arange(g.shape[-1], dtype=numpy.float) * dh

            # self.dataOut.heightList = numpy.concatenate((self.dataOut.heightList,heightList_2))
