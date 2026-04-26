import sys
import numpy,math
from scipy import interpolate
from schainpy.model.proc.jroproc_base import ProcessingUnit, Operation, MPDecorator
from schainpy.model.data.jrodata import Voltage,hildebrand_sekhon
from schainpy.utils import log
from schainpy.model.io.utilsIO import getHei_index
from time import time
import datetime
import numpy
# voltage proc master

class VoltageProc(ProcessingUnit):

    def __init__(self):

        ProcessingUnit.__init__(self)

        self.dataOut = Voltage()
        self.flip = 1
        self.setupReq = False

    def run(self, runNextUnit = 0):

        if self.dataIn.type == 'AMISR':
            self.__updateObjFromAmisrInput()

        if  self.dataOut.buffer_empty:
            if self.dataIn.type == 'Voltage':
                self.dataOut.copy(self.dataIn)
                self.dataOut.radarControllerHeaderObj = self.dataIn.radarControllerHeaderObj.copy()
                self.dataOut.ippSeconds = self.dataIn.ippSeconds
                self.dataOut.ipp = self.dataIn.ipp

                #update Processing Header:
                self.dataOut.processingHeaderObj.heightList = self.dataOut.heightList
                self.dataOut.processingHeaderObj.ipp =  self.dataOut.ipp
                self.dataOut.processingHeaderObj.nCohInt =  self.dataOut.nCohInt
                self.dataOut.processingHeaderObj.dtype =  self.dataOut.type
                self.dataOut.processingHeaderObj.channelList =  self.dataOut.channelList
                self.dataOut.processingHeaderObj.azimuthList =  self.dataOut.azimuthList
                self.dataOut.processingHeaderObj.elevationList =  self.dataOut.elevationList
                self.dataOut.processingHeaderObj.codeList =  self.dataOut.nChannels
                self.dataOut.processingHeaderObj.heightList =  self.dataOut.heightList
                self.dataOut.processingHeaderObj.heightResolution  = self.dataOut.heightList[1] - self.dataOut.heightList[0]
                

    def __updateObjFromAmisrInput(self):

        self.dataOut.timeZone = self.dataIn.timeZone
        self.dataOut.dstFlag = self.dataIn.dstFlag
        self.dataOut.errorCount = self.dataIn.errorCount
        self.dataOut.useLocalTime = self.dataIn.useLocalTime

        self.dataOut.flagNoData = self.dataIn.flagNoData
        self.dataOut.data = self.dataIn.data
        self.dataOut.utctime = self.dataIn.utctime
        self.dataOut.channelList = self.dataIn.channelList
        #self.dataOut.timeInterval = self.dataIn.timeInterval
        self.dataOut.heightList = self.dataIn.heightList
        self.dataOut.nProfiles = self.dataIn.nProfiles

        self.dataOut.nCohInt = self.dataIn.nCohInt
        self.dataOut.ippSeconds = self.dataIn.ippSeconds
        self.dataOut.frequency = self.dataIn.frequency

        self.dataOut.azimuth = self.dataIn.azimuth
        self.dataOut.zenith = self.dataIn.zenith

        self.dataOut.beam.codeList = self.dataIn.beam.codeList
        self.dataOut.beam.azimuthList = self.dataIn.beam.azimuthList
        self.dataOut.beam.zenithList = self.dataIn.beam.zenithList


class selectChannels(Operation):

    def run(self, dataOut, channelList=[]):
        
        if  isinstance(channelList, int):
            channelList = [channelList]

        self.channelList = channelList
        if len(self.channelList) == 0:
            print("Missing channelList")
            return dataOut
        channelIndexList = []
        if not dataOut.buffer_empty: # cuando se usa proc volts como buffer de datos
            return dataOut
        if  type(dataOut.channelList) is not list:    #leer array desde HDF5
            try:
                dataOut.channelList = dataOut.channelList.tolist()
            except Exception as e:
                print("Select Channels: ",e)
        for channel in self.channelList:
            if channel not in dataOut.channelList:
                raise ValueError("Channel %d is not in %s" %(channel, str(dataOut.channelList)))

            index = dataOut.channelList.index(channel)
            channelIndexList.append(index)
        
        dataOut = self.selectChannelsByIndex(dataOut,channelIndexList)
        
        #update Processing Header:
        dataOut.processingHeaderObj.channelList = dataOut.channelList
        dataOut.processingHeaderObj.elevationList = dataOut.elevationList
        dataOut.processingHeaderObj.azimuthList = dataOut.azimuthList
        dataOut.processingHeaderObj.codeList = dataOut.codeList
        dataOut.processingHeaderObj.nChannels = len(dataOut.channelList)
        
        return dataOut

    def selectChannelsByIndex(self, dataOut, channelIndexList):
        """
        Selecciona un bloque de datos en base a canales segun el channelIndexList

        Input:
            channelIndexList    :    lista sencilla de canales a seleccionar por ej. [2,3,7]

        Affected:
            self.dataOut.data
            self.dataOut.channelIndexList
            self.dataOut.nChannels
            self.dataOut.m_ProcessingHeader.totalSpectra
            self.dataOut.systemHeaderObj.numChannels
            self.dataOut.m_ProcessingHeader.blockSize

        Return:
            None
        """
        # for channelIndex in channelIndexList:
        #     if channelIndex not in dataOut.channelIndexList:
        #         raise ValueError("The value %d in channelIndexList is not valid" %channelIndex)

        if dataOut.type == 'Voltage':
            if dataOut.flagDataAsBlock:
                """
                Si la data es obtenida por bloques, dimension = [nChannels, nProfiles, nHeis]
                """
                data = dataOut.data[channelIndexList,:,:]
            else:
                data = dataOut.data[channelIndexList,:]

            dataOut.data = data
            # dataOut.channelList = [dataOut.channelList[i] for i in channelIndexList]
            dataOut.channelList = [n for n in range(len(channelIndexList))]
            
        elif dataOut.type == 'Spectra':
            if hasattr(dataOut, 'data_spc'):
                if dataOut.data_spc is None:
                    raise ValueError("data_spc is None")
                    return dataOut
                else:
                    data_spc = dataOut.data_spc[channelIndexList, :]
                    dataOut.data_spc = data_spc

            # if hasattr(dataOut, 'data_dc') :# and
            #     if dataOut.data_dc is None:
            #         raise ValueError("data_dc is None")
            #         return dataOut
            #     else:
            #         data_dc = dataOut.data_dc[channelIndexList, :]
            #         dataOut.data_dc = data_dc
            # dataOut.channelList = [dataOut.channelList[i] for i in channelIndexList]
            dataOut.channelList = channelIndexList
            dataOut = self.__selectPairsByChannel(dataOut,channelIndexList)
         

        dataOut.elevationList = numpy.asarray(dataOut.elevationList)
        dataOut.azimuthList = numpy.asarray(dataOut.azimuthList)
        dataOut.codeList = numpy.asarray(dataOut.codeList)
        if (len(dataOut.elevationList) > 0):
            dataOut.elevationList = dataOut.elevationList[channelIndexList]
            dataOut.azimuthList = dataOut.azimuthList[channelIndexList]
            dataOut.codeList = dataOut.codeList[channelIndexList]
            
        return dataOut

    def __selectPairsByChannel(self, dataOut, channelList=None):
   
        if channelList == None:
            return

        pairsIndexListSelected = []
        for pairIndex in dataOut.pairsIndexList:
            # First pair
            if dataOut.pairsList[pairIndex][0] not in channelList:
                continue
            # Second pair
            if dataOut.pairsList[pairIndex][1] not in channelList:
                continue

            pairsIndexListSelected.append(pairIndex)
        if not pairsIndexListSelected:
            dataOut.data_cspc = None
            dataOut.pairsList = []
            return

        dataOut.data_cspc = dataOut.data_cspc[pairsIndexListSelected]
        dataOut.pairsList = [dataOut.pairsList[i]
                                  for i in pairsIndexListSelected]

        return dataOut

class selectHeights(Operation):

    def run(self, dataOut, minHei=None, maxHei=None, minIndex=None, maxIndex=None):
        """
        Selecciona un bloque de datos en base a un grupo de valores de alturas segun el rango
        minHei <= height <= maxHei

        Input:
            minHei    :    valor minimo de altura a considerar
            maxHei    :    valor maximo de altura a considerar

        Affected:
            Indirectamente son cambiados varios valores a travez del metodo selectHeightsByIndex

        Return:
            1 si el metodo se ejecuto con exito caso contrario devuelve 0
        """

        self.dataOut = dataOut

        if type(minHei) == int or type(minHei) == float:
            v_minHei= True 
        else:
            v_minHei= False

        if v_minHei and maxHei:
            if (minHei < self.dataOut.heightList[0]):
                minHei = self.dataOut.heightList[0]

            if (maxHei > self.dataOut.heightList[-1]):
                maxHei = self.dataOut.heightList[-1]

            minIndex = 0
            maxIndex = 0
            heights = self.dataOut.heightList
            inda = numpy.where(heights >= minHei)
            indb = numpy.where(heights <= maxHei)

            try:
                minIndex = inda[0][0]
            except:
                minIndex = 0

            try:
                maxIndex = indb[0][-1]
            except:
                maxIndex = len(heights)
        self.selectHeightsByIndex(minIndex, maxIndex)

        #update Processing Header:
        dataOut.processingHeaderObj.heightList = dataOut.heightList

        return self.dataOut

    def selectHeightsByIndex(self, minIndex, maxIndex):
        """
        Selecciona un bloque de datos en base a un grupo indices de alturas segun el rango
        minIndex <= index <= maxIndex

        Input:
            minIndex    :    valor de indice minimo de altura a considerar
            maxIndex    :    valor de indice maximo de altura a considerar

        Affected:
            self.dataOut.data
            self.dataOut.heightList

        Return:
            1 si el metodo se ejecuto con exito caso contrario devuelve 0
        """

        if self.dataOut.type == 'Voltage':
            if (minIndex < 0) or (minIndex > maxIndex):
                raise ValueError("Height index range (%d,%d) is not valid" % (minIndex, maxIndex))

            if (maxIndex >= self.dataOut.nHeights):
                maxIndex = self.dataOut.nHeights

            #voltage
            if self.dataOut.flagDataAsBlock:
                """
                Si la data es obtenida por bloques, dimension = [nChannels, nProfiles, nHeis]
                """
                data = self.dataOut.data[:,:, minIndex:maxIndex]
            else:
                data = self.dataOut.data[:, minIndex:maxIndex]

            #         firstHeight = self.dataOut.heightList[minIndex]

            self.dataOut.data = data
            self.dataOut.heightList = self.dataOut.heightList[minIndex:maxIndex]

            if self.dataOut.nHeights <= 1:
                raise ValueError("selectHeights: Too few heights. Current number of heights is %d" %(self.dataOut.nHeights))
        elif self.dataOut.type == 'Spectra':
            if (minIndex < 0) or (minIndex > maxIndex):
                raise ValueError("Error selecting heights: Index range (%d,%d) is not valid" % (
                    minIndex, maxIndex))

            if (maxIndex >= self.dataOut.nHeights):
                maxIndex = self.dataOut.nHeights - 1

            # Spectra
            data_spc = self.dataOut.data_spc[:, :, minIndex:maxIndex + 1]

            data_cspc = None
            if self.dataOut.data_cspc is not None:
                data_cspc = self.dataOut.data_cspc[:, :, minIndex:maxIndex + 1]

            data_dc = None
            if self.dataOut.data_dc is not None:
                data_dc = self.dataOut.data_dc[:, minIndex:maxIndex + 1]

            self.dataOut.data_spc = data_spc
            self.dataOut.data_cspc = data_cspc
            self.dataOut.data_dc = data_dc

            self.dataOut.heightList = self.dataOut.heightList[minIndex:maxIndex + 1]

        return 1


class filterByHeights(Operation):

    ifConfig=False
    deltaHeight = None
    newdelta=None
    newheights=None
    r=None
    h0=None
    nHeights=None

    def run(self, dataOut, window):
    
        if window == None:
            window = (dataOut.radarControllerHeaderObj.txA/dataOut.radarControllerHeaderObj.nBaud) / self.deltaHeight
	
        if not self.ifConfig: #and dataOut.useInputBuffer:
            self.deltaHeight = dataOut.heightList[1] - dataOut.heightList[0]
            self.ifConfig = True
            self.newdelta = self.deltaHeight * window
            self.r = dataOut.nHeights % window
            self.newheights = (dataOut.nHeights-self.r)/window
            self.h0 = dataOut.heightList[0]
            self.nHeights = dataOut.nHeights
            if self.newheights <= 1:
                raise ValueError("filterByHeights: Too few heights. Current number of heights is %d and window is %d" %(dataOut.nHeights, window))

        if dataOut.flagDataAsBlock:
            """
            Si la data es obtenida por bloques, dimension = [nChannels, nProfiles, nHeis]
            """
            buffer = dataOut.data[:, :, 0:int(self.nHeights-self.r)]
            buffer = buffer.reshape(dataOut.nChannels, dataOut.nProfiles, int(self.nHeights/window), window)
            buffer = numpy.sum(buffer,3)

        else:
            buffer = dataOut.data[:,0:int(self.nHeights-self.r)]
            buffer = buffer.reshape(dataOut.nChannels,int(self.nHeights/window),int(window))
            buffer = numpy.sum(buffer,2)

        dataOut.data = buffer
        dataOut.heightList = self.h0 + numpy.arange( self.newheights )*self.newdelta
        dataOut.windowOfFilter = window

        #update Processing Header:
        dataOut.processingHeaderObj.heightList = dataOut.heightList
        dataOut.processingHeaderObj.nWindows = window
        
        return dataOut


class setH0(Operation):

    def run(self, dataOut, h0, deltaHeight = None):

        if not deltaHeight:
            deltaHeight = dataOut.heightList[1] - dataOut.heightList[0]

        nHeights = dataOut.nHeights

        newHeiRange = h0 + numpy.arange(nHeights)*deltaHeight

        dataOut.heightList = newHeiRange

        return dataOut


class deFlip(Operation):

    def run(self, dataOut, channelList = []):

        data = dataOut.data.copy()

        if dataOut.flagDataAsBlock:
            flip = self.flip
            profileList = list(range(dataOut.nProfiles))

            if not channelList:
                for thisProfile in profileList:
                    data[:,thisProfile,:] = data[:,thisProfile,:]*flip
                    flip *= -1.0
            else:
                for thisChannel in channelList:
                    if thisChannel not in dataOut.channelList:
                        continue

                    for thisProfile in profileList:
                        data[thisChannel,thisProfile,:] = data[thisChannel,thisProfile,:]*flip
                        flip *= -1.0

            self.flip = flip

        else:
            if not channelList:
                data[:,:] = data[:,:]*self.flip
            else:
                for thisChannel in channelList:
                    if thisChannel not in dataOut.channelList:
                        continue

                    data[thisChannel,:] = data[thisChannel,:]*self.flip

            self.flip *= -1.

        dataOut.data = data

        return dataOut


class setAttribute(Operation):
    '''
    Set an arbitrary attribute(s) to dataOut
    '''

    def __init__(self):

        Operation.__init__(self)
        self._ready = False

    def run(self, dataOut, **kwargs):

        for key, value in kwargs.items():
            setattr(dataOut, key, value)

        return dataOut


@MPDecorator
class printAttribute(Operation):
    '''
    Print an arbitrary attribute of dataOut
    '''

    def __init__(self):

        Operation.__init__(self)

    def run(self, dataOut, attributes):

        if isinstance(attributes, str):
            attributes = [attributes]
        for attr in attributes:
            if hasattr(dataOut, attr):
                log.log(getattr(dataOut, attr), attr)


class interpolateHeights(Operation):

    def run(self, dataOut, topLim, botLim):
        #69 al 72 para julia
        #82-84 para meteoros
        if len(numpy.shape(dataOut.data))==2:
            sampInterp = (dataOut.data[:,botLim-1] + dataOut.data[:,topLim+1])/2
            sampInterp = numpy.transpose(numpy.tile(sampInterp,(topLim-botLim + 1,1)))
            #dataOut.data[:,botLim:limSup+1] = sampInterp
            dataOut.data[:,botLim:topLim+1] = sampInterp
        else:
            nHeights = dataOut.data.shape[2]
            x = numpy.hstack((numpy.arange(botLim),numpy.arange(topLim+1,nHeights)))
            y = dataOut.data[:,:,list(range(botLim))+list(range(topLim+1,nHeights))]
            f = interpolate.interp1d(x, y, axis = 2)
            xnew = numpy.arange(botLim,topLim+1)
            ynew = f(xnew)
            dataOut.data[:,:,botLim:topLim+1]  = ynew

        return dataOut


class CohInt(Operation):

    isConfig = False
    __profIndex = 0
    __byTime = False
    __initime = None
    __lastdatatime = None
    __integrationtime = None
    __buffer = None
    __bufferStride = []
    __dataReady = False
    __profIndexStride = 0
    __dataToPutStride = False
    n = None

    def __init__(self, **kwargs):

        Operation.__init__(self, **kwargs)

    def setup(self, n=None, timeInterval=None, stride=None, overlapping=False, byblock=False):
        """
        Set the parameters of the integration class.

        Inputs:

            n               :    Number of coherent integrations
            timeInterval    :    Time of integration. If the parameter "n" is selected this one does not work
            overlapping     :
        """

        self.__initime = None
        self.__lastdatatime = 0
        self.__buffer = None
        self.__dataReady = False
        self.byblock = byblock
        self.stride = stride

        if n == None and timeInterval == None:
            raise ValueError("n or timeInterval should be specified ...")

        if n != None:
            self.n = n
            self.__byTime = False
        else:
            self.__integrationtime = timeInterval #* 60. #if (type(timeInterval)!=integer) -> change this line
            self.n = 9999
            self.__byTime = True

        if overlapping:
            self.__withOverlapping = True
            self.__buffer = None
        else:
            self.__withOverlapping = False
            self.__buffer = 0

        self.__profIndex = 0

    def putData(self, data):

        """
        Add a profile to the __buffer and increase in one the __profileIndex

        """

        if not self.__withOverlapping:
            self.__buffer += data.copy()
            self.__profIndex += 1
            return

        #Overlapping data
        nChannels, nHeis = data.shape
        data = numpy.reshape(data, (1, nChannels, nHeis))

        #If the buffer is empty then it takes the data value
        if self.__buffer is None:
            self.__buffer = data
            self.__profIndex += 1
            return

        #If the buffer length is lower than n then stakcing the data value
        if self.__profIndex < self.n:
            self.__buffer = numpy.vstack((self.__buffer, data))
            self.__profIndex += 1
            return

        #If the buffer length is equal to n then replacing the last buffer value with the data value
        self.__buffer = numpy.roll(self.__buffer, -1, axis=0)
        self.__buffer[self.n-1] = data
        self.__profIndex = self.n
        return


    def pushData(self):
        """
        Return the sum of the last profiles and the profiles used in the sum.

        Affected:

        self.__profileIndex

        """

        if not self.__withOverlapping:
            data = self.__buffer
            n = self.__profIndex

            self.__buffer = 0
            self.__profIndex = 0

            return data, n

        #Integration with Overlapping
        data = numpy.sum(self.__buffer, axis=0)
        # print data
        # raise
        n = self.__profIndex

        return data, n

    def byProfiles(self, data):

        self.__dataReady = False
        avgdata = None
        #         n = None
        # print data
        # raise
        self.putData(data)

        if self.__profIndex == self.n:
            avgdata, n = self.pushData()
            self.__dataReady = True

        return avgdata

    def byTime(self, data, datatime):

        self.__dataReady = False
        avgdata = None
        n = None

        self.putData(data)

        if (datatime - self.__initime) >= self.__integrationtime:
            avgdata, n = self.pushData()
            self.n = n
            self.__dataReady = True

        return avgdata

    def integrateByStride(self, data, datatime):
        # print data
        if self.__profIndex == 0:
            self.__buffer = [[data.copy(), datatime]]
        else:
            self.__buffer.append([data.copy(),datatime])
        self.__profIndex += 1
        self.__dataReady = False

        if self.__profIndex == self.n * self.stride :
            self.__dataToPutStride = True
            self.__profIndexStride = 0
            self.__profIndex = 0
            self.__bufferStride = []
            for i in range(self.stride):
                current = self.__buffer[i::self.stride]
                data = numpy.sum([t[0] for t in current], axis=0)
                avgdatatime = numpy.average([t[1] for t in current])
                # print data
                self.__bufferStride.append((data, avgdatatime))

        if self.__dataToPutStride:
            self.__dataReady = True
            self.__profIndexStride += 1
            if self.__profIndexStride == self.stride:
                self.__dataToPutStride = False
            # print self.__bufferStride[self.__profIndexStride - 1]
            # raise
            return self.__bufferStride[self.__profIndexStride - 1]


        return None, None

    def integrate(self, data, datatime=None):

        if self.__initime == None:
            self.__initime = datatime

        if self.__byTime:
            avgdata = self.byTime(data, datatime)
        else:
            avgdata = self.byProfiles(data)


        self.__lastdatatime = datatime

        if avgdata is None:
            return None, None

        avgdatatime = self.__initime

        deltatime = datatime - self.__lastdatatime

        if not self.__withOverlapping:
            self.__initime = datatime
        else:
            self.__initime += deltatime

        return avgdata, avgdatatime

    def integrateByBlock(self, dataOut):

        times = int(dataOut.data.shape[1]/self.n)
        avgdata = numpy.zeros((dataOut.nChannels, times, dataOut.nHeights), dtype=numpy.complex_)

        id_min = 0
        id_max = self.n

        for i in range(times):
            junk = dataOut.data[:,id_min:id_max,:]
            avgdata[:,i,:] = junk.sum(axis=1)
            id_min += self.n
            id_max += self.n

        timeInterval = dataOut.ippSeconds*self.n
        avgdatatime = (times - 1) * timeInterval + dataOut.utctime
        self.__dataReady = True
        return avgdata, avgdatatime

    def run(self, dataOut, n=None, timeInterval=None, stride=None, overlapping=False, byblock=False, **kwargs):

        if not self.isConfig:
            self.setup(n=n, stride=stride, timeInterval=timeInterval, overlapping=overlapping, byblock=byblock, **kwargs)
            self.isConfig = True
        if dataOut.flagDataAsBlock:
            """
            Si la data es leida por bloques, dimension = [nChannels, nProfiles, nHeis]
            """
            avgdata, avgdatatime = self.integrateByBlock(dataOut)
            dataOut.nProfiles /= self.n
        else:
            if stride is None:
                avgdata, avgdatatime = self.integrate(dataOut.data, dataOut.utctime)
            else:
                avgdata, avgdatatime = self.integrateByStride(dataOut.data, dataOut.utctime)


        #   dataOut.timeInterval *= n
        dataOut.flagNoData = True

        if self.__dataReady:
            dataOut.data = avgdata
            if not dataOut.flagCohInt:
                dataOut.nCohInt *= self.n
                dataOut.flagCohInt = True
            dataOut.utctime = avgdatatime
            # print avgdata, avgdatatime
            # raise
            #   dataOut.timeInterval = dataOut.ippSeconds * dataOut.nCohInt
            dataOut.flagNoData = False
        return dataOut

class Decoder(Operation):

    isConfig = False
    __profIndex = 0

    code = None

    nCode = None
    nBaud = None

    def __init__(self, **kwargs):

        Operation.__init__(self, **kwargs)

        self.times = None
        self.osamp = None
    #         self.__setValues = False
        self.isConfig = False
        self.setupReq = False
    def setup(self, code, osamp, dataOut):

        self.__profIndex = 0

        self.code = code

        self.nCode = len(code)
        self.nBaud = len(code[0])

        if (osamp != None) and (osamp >1):
            self.osamp = osamp
            self.code = numpy.repeat(code, repeats=self.osamp, axis=1)
            self.nBaud = self.nBaud*self.osamp

        self.__nChannels = dataOut.nChannels
        self.__nProfiles = dataOut.nProfiles
        self.__nHeis = dataOut.nHeights

        if self.__nHeis < self.nBaud:
            raise ValueError('Number of heights (%d) should be greater than number of bauds (%d)' %(self.__nHeis, self.nBaud))

        #Frequency
        __codeBuffer = numpy.zeros((self.nCode, self.__nHeis), dtype=numpy.complex_)

        __codeBuffer[:,0:self.nBaud] = self.code

        self.fft_code = numpy.conj(numpy.fft.fft(__codeBuffer, axis=1))

        if dataOut.flagDataAsBlock:

            self.ndatadec = self.__nHeis #- self.nBaud + 1

            self.datadecTime = numpy.zeros((self.__nChannels, self.__nProfiles, self.ndatadec), dtype=numpy.complex_)

        else:

            #Time
            self.ndatadec = self.__nHeis #- self.nBaud + 1

            self.datadecTime = numpy.zeros((self.__nChannels, self.ndatadec), dtype=numpy.complex_)

    def __convolutionInFreq(self, data):

        fft_code = self.fft_code[self.__profIndex].reshape(1,-1)

        fft_data = numpy.fft.fft(data, axis=1)

        conv = fft_data*fft_code

        data = numpy.fft.ifft(conv,axis=1)

        return data

    def __convolutionInFreqOpt(self, data):

        raise NotImplementedError

    def __convolutionInTime(self, data):

        code = self.code[self.__profIndex]
        for i in range(self.__nChannels):
            self.datadecTime[i,:] = numpy.correlate(data[i,:], code, mode='full')[self.nBaud-1:]

        return self.datadecTime

    def __convolutionByBlockInTime(self, data):

        repetitions = int(self.__nProfiles / self.nCode)
        junk = numpy.lib.stride_tricks.as_strided(self.code, (repetitions, self.code.size), (0, self.code.itemsize))
        junk = junk.flatten()
        code_block = numpy.reshape(junk, (self.nCode*repetitions, self.nBaud))
        profilesList = range(self.__nProfiles)

        for i in range(self.__nChannels):
            for j in profilesList:
                self.datadecTime[i,j,:] = numpy.correlate(data[i,j,:], code_block[j,:], mode='full')[self.nBaud-1:]
        return self.datadecTime

    def __convolutionByBlockInFreq(self, data):

        raise NotImplementedError("Decoder by frequency fro Blocks not implemented")


        fft_code = self.fft_code[self.__profIndex].reshape(1,-1)

        fft_data = numpy.fft.fft(data, axis=2)

        conv = fft_data*fft_code

        data = numpy.fft.ifft(conv,axis=2)

        return data


    def run(self, dataOut, code=None, nCode=None, nBaud=None, mode = 0, osamp=None, times=None):

        if dataOut.flagDecodeData:
            print("This data is already decoded, recoding again ...")

        if not self.isConfig:

            if code is None:
                if dataOut.code is None:
                    raise ValueError("Code could not be read from %s instance. Enter a value in Code parameter" %dataOut.type)

                code = dataOut.code
            else:
                code = numpy.array(code).reshape(nCode,nBaud)
            self.setup(code, osamp, dataOut)

            self.isConfig = True

            if mode == 3:
                sys.stderr.write("Decoder Warning: mode=%d is not valid, using mode=0\n" %mode)

            if times != None:
                sys.stderr.write("Decoder Warning: Argument 'times' in not used anymore\n")

        if self.code is None:
            print("Fail decoding: Code is not defined.")
            return

        self.__nProfiles = dataOut.nProfiles
        datadec = None

        if mode == 3:
            mode = 0

        if dataOut.flagDataAsBlock:
            """
            Decoding when data have been read as block,
            """

            if mode == 0:
                datadec = self.__convolutionByBlockInTime(dataOut.data)
            if mode == 1:
                datadec = self.__convolutionByBlockInFreq(dataOut.data)
        else:
            """
            Decoding when data have been read profile by profile
            """
            if mode == 0:
                datadec = self.__convolutionInTime(dataOut.data)

            if mode == 1:
                datadec = self.__convolutionInFreq(dataOut.data)

            if mode == 2:
                datadec = self.__convolutionInFreqOpt(dataOut.data)

        if datadec is None:
            raise ValueError("Codification mode selected is not valid: mode=%d. Try selecting 0 or 1" %mode)

        dataOut.code = self.code
        dataOut.nCode = self.nCode
        dataOut.nBaud = self.nBaud

        dataOut.data = datadec
        dataOut.heightList = dataOut.heightList[0:datadec.shape[-1]]

        dataOut.flagDecodeData = True #asumo q la data esta decodificada
        #update Processing Header:
        dataOut.radarControllerHeaderObj.code = self.code
        dataOut.radarControllerHeaderObj.nCode = self.nCode
        dataOut.radarControllerHeaderObj.nBaud = self.nBaud
        dataOut.radarControllerHeaderObj.nOsamp = osamp
        #update Processing Header:
        dataOut.processingHeaderObj.heightList = dataOut.heightList
        dataOut.processingHeaderObj.heightResolution = dataOut.heightList[1]-dataOut.heightList[0]

        if self.__profIndex == self.nCode-1:
            self.__profIndex = 0
            return dataOut

        self.__profIndex += 1

        return dataOut


class ProfileConcat(Operation):

    isConfig = False
    buffer = None

    def __init__(self, **kwargs):

        Operation.__init__(self, **kwargs)
        self.profileIndex = 0

    def reset(self):
        self.buffer = numpy.zeros_like(self.buffer)
        self.start_index = 0
        self.times = 1

    def setup(self, data, m, n=1):
        self.buffer = numpy.zeros((data.shape[0],data.shape[1]*m),dtype=type(data[0,0]))
        self.nHeights = data.shape[1]#.nHeights
        self.start_index = 0
        self.times = 1

    def concat(self, data):

        self.buffer[:,self.start_index:self.nHeights*self.times] = data.copy()
        self.start_index = self.start_index + self.nHeights

    def run(self, dataOut, m):
        dataOut.flagNoData = True

        if not self.isConfig:
            self.setup(dataOut.data, m, 1)
            self.isConfig = True

        if dataOut.flagDataAsBlock:
            raise ValueError("ProfileConcat can only be used when voltage have been read profile by profile, getBlock = False")

        else:
            self.concat(dataOut.data)
            self.times += 1
            if self.times > m:
                dataOut.data = self.buffer
                self.reset()
                dataOut.flagNoData = False
                # se deben actualizar mas propiedades del header y del objeto dataOut, por ejemplo, las alturas
                deltaHeight = dataOut.heightList[1] - dataOut.heightList[0]
                xf = dataOut.heightList[0] + dataOut.nHeights * deltaHeight * m
                dataOut.heightList = numpy.arange(dataOut.heightList[0], xf, deltaHeight)
                dataOut.ippSeconds *= m
                #update Processing Header:
                dataOut.processingHeaderObj.heightList = dataOut.heightList
                dataOut.processingHeaderObj.ipp = dataOut.ippSeconds

        return dataOut

class ProfileSelector(Operation):

    profileIndex = None
    # Tamanho total de los perfiles
    nProfiles = None

    def __init__(self, **kwargs):

        Operation.__init__(self, **kwargs)
        self.profileIndex = 0

    def incProfileIndex(self):

        self.profileIndex += 1

        if self.profileIndex >= self.nProfiles:
            self.profileIndex = 0

    def isThisProfileInRange(self, profileIndex, minIndex, maxIndex):

        if profileIndex < minIndex:
            return False

        if profileIndex > maxIndex:
            return False

        return True

    def isThisProfileInList(self, profileIndex, profileList):

        if profileIndex not in profileList:
            return False

        return True

    def run(self, dataOut, profileList=None, profileRangeList=None, beam=None, byblock=False, rangeList = None, nProfiles=None):

        """
        ProfileSelector:

        Inputs:
            profileList        :    Index of profiles selected. Example: profileList = (0,1,2,7,8)

            profileRangeList    :    Minimum and maximum profile indexes. Example: profileRangeList = (4, 30)

            rangeList            :    List of profile ranges. Example: rangeList = ((4, 30), (32, 64), (128, 256))

        """

        if rangeList is not None:
            if type(rangeList[0]) not in (tuple, list):
                rangeList = [rangeList]

        dataOut.flagNoData = True

        if dataOut.flagDataAsBlock:
            """
            data dimension  = [nChannels, nProfiles, nHeis]
            """
            if profileList != None:
                dataOut.data = dataOut.data[:,profileList,:]

            if profileRangeList != None:
                minIndex = profileRangeList[0]
                maxIndex = profileRangeList[1]
                profileList = list(range(minIndex, maxIndex+1))

                dataOut.data = dataOut.data[:,minIndex:maxIndex+1,:]

            if rangeList != None:

                profileList = []

                for thisRange in rangeList:
                    minIndex = thisRange[0]
                    maxIndex = thisRange[1]

                    profileList.extend(list(range(minIndex, maxIndex+1)))

                dataOut.data = dataOut.data[:,profileList,:]

            dataOut.nProfiles = len(profileList)
            dataOut.profileIndex = dataOut.nProfiles - 1
            dataOut.flagNoData = False

            return dataOut

        """
        data dimension  = [nChannels, nHeis]
        """

        if profileList != None:

            if self.isThisProfileInList(dataOut.profileIndex, profileList):

                self.nProfiles = len(profileList)
                dataOut.nProfiles = self.nProfiles
                dataOut.profileIndex = self.profileIndex
                dataOut.flagNoData = False

                self.incProfileIndex()
            return dataOut

        if profileRangeList != None:

            minIndex = profileRangeList[0]
            maxIndex = profileRangeList[1]

            if self.isThisProfileInRange(dataOut.profileIndex, minIndex, maxIndex):

                self.nProfiles = maxIndex - minIndex + 1
                dataOut.nProfiles = self.nProfiles
                dataOut.profileIndex = self.profileIndex
                dataOut.flagNoData = False

                self.incProfileIndex()
            return dataOut

        if rangeList != None:

            nProfiles = 0

            for thisRange in rangeList:
                minIndex = thisRange[0]
                maxIndex = thisRange[1]

                nProfiles += maxIndex - minIndex + 1

            for thisRange in rangeList:

                minIndex = thisRange[0]
                maxIndex = thisRange[1]

                if self.isThisProfileInRange(dataOut.profileIndex, minIndex, maxIndex):

                    self.nProfiles = nProfiles
                    dataOut.nProfiles = self.nProfiles
                    dataOut.profileIndex = self.profileIndex
                    dataOut.flagNoData = False

                    self.incProfileIndex()

                    break

            return dataOut


        if beam != None: #beam is only for AMISR data
            if self.isThisProfileInList(dataOut.profileIndex, dataOut.beamRangeDict[beam]):
                dataOut.flagNoData = False
                dataOut.profileIndex = self.profileIndex

                self.incProfileIndex()

            return dataOut

        raise ValueError("ProfileSelector needs profileList, profileRangeList or rangeList parameter")


class Reshaper(Operation):

    def __init__(self, **kwargs):

        Operation.__init__(self, **kwargs)

        self.__buffer = None
        self.__nitems = 0

    def __appendProfile(self, dataOut, nTxs):

        if self.__buffer is None:
            shape = (dataOut.nChannels, int(dataOut.nHeights/nTxs) )
            self.__buffer = numpy.empty(shape, dtype = dataOut.data.dtype)

        ini = dataOut.nHeights * self.__nitems
        end = ini + dataOut.nHeights

        self.__buffer[:, ini:end] = dataOut.data

        self.__nitems += 1

        return int(self.__nitems*nTxs)

    def __getBuffer(self):

        if self.__nitems == int(1./self.__nTxs):

            self.__nitems = 0

            return self.__buffer.copy()

        return None

    def __checkInputs(self, dataOut, shape, nTxs):

        if shape is None and nTxs is None:
            raise ValueError("Reshaper: shape of factor should be defined")

        if nTxs:
            if nTxs < 0:
                raise ValueError("nTxs should be greater than 0")

            if nTxs < 1 and dataOut.nProfiles % (1./nTxs) != 0:
                raise ValueError("nProfiles= %d is not divisibled by (1./nTxs) = %f" %(dataOut.nProfiles, (1./nTxs)))

            shape = [dataOut.nChannels, dataOut.nProfiles*nTxs, dataOut.nHeights/nTxs]

            return shape, nTxs

        if len(shape) != 2 and len(shape) !=  3:
            raise ValueError("shape dimension should be equal to 2 or 3. shape = (nProfiles, nHeis) or (nChannels, nProfiles, nHeis). Actually shape = (%d, %d, %d)" %(dataOut.nChannels, dataOut.nProfiles, dataOut.nHeights))

        if len(shape) == 2:
            shape_tuple = [dataOut.nChannels]
            shape_tuple.extend(shape)
        else:
            shape_tuple = list(shape)

        nTxs = 1.0*shape_tuple[1]/dataOut.nProfiles

        return shape_tuple, nTxs

    def run(self, dataOut, shape=None, nTxs=None):

        shape_tuple, self.__nTxs = self.__checkInputs(dataOut, shape, nTxs)

        dataOut.flagNoData = True
        profileIndex = None

        if dataOut.flagDataAsBlock:

            dataOut.data = numpy.reshape(dataOut.data, shape_tuple)
            dataOut.flagNoData = False

            profileIndex = int(dataOut.nProfiles*self.__nTxs) - 1

        else:

            if self.__nTxs < 1:

                self.__appendProfile(dataOut, self.__nTxs)
                new_data = self.__getBuffer()

                if new_data is not None:
                    dataOut.data = new_data
                    dataOut.flagNoData = False

                    profileIndex = dataOut.profileIndex*nTxs

            else:
                raise ValueError("nTxs should be greater than 0 and lower than 1, or use VoltageReader(..., getblock=True)")

        deltaHeight = dataOut.heightList[1] - dataOut.heightList[0]

        dataOut.heightList = numpy.arange(dataOut.nHeights/self.__nTxs) * deltaHeight + dataOut.heightList[0]

        dataOut.nProfiles = int(dataOut.nProfiles*self.__nTxs)

        dataOut.profileIndex = profileIndex

        dataOut.ippSeconds /= self.__nTxs

        return dataOut

class SplitProfiles(Operation):

    def __init__(self, **kwargs):

        Operation.__init__(self, **kwargs)

    def run(self, dataOut, n):

        dataOut.flagNoData = True
        profileIndex = None

        if dataOut.flagDataAsBlock:

            #nchannels, nprofiles, nsamples
            shape = dataOut.data.shape

            if shape[2] % n != 0:
                raise ValueError("Could not split the data, n=%d has to be multiple of %d" %(n, shape[2]))

            new_shape = shape[0], shape[1]*n, int(shape[2]/n)

            dataOut.data = numpy.reshape(dataOut.data, new_shape)
            dataOut.flagNoData = False

            profileIndex = int(dataOut.nProfiles/n) - 1

        else:

            raise ValueError("Could not split the data when is read Profile by Profile. Use VoltageReader(..., getblock=True)")

        deltaHeight = dataOut.heightList[1] - dataOut.heightList[0]

        dataOut.heightList = numpy.arange(dataOut.nHeights/n) * deltaHeight + dataOut.heightList[0]

        dataOut.nProfiles = int(dataOut.nProfiles*n)

        dataOut.profileIndex = profileIndex

        dataOut.ippSeconds /= n

        return dataOut

class CombineProfiles(Operation):
    def __init__(self, **kwargs):

        Operation.__init__(self, **kwargs)

        self.__remData = None
        self.__profileIndex = 0

    def run(self, dataOut, n):

        dataOut.flagNoData = True
        profileIndex = None

        if dataOut.flagDataAsBlock:

            #nchannels, nprofiles, nsamples
            shape = dataOut.data.shape
            new_shape = shape[0], shape[1]/n, shape[2]*n

            if shape[1] % n != 0:
                raise ValueError("Could not split the data, n=%d has to be multiple of %d" %(n, shape[1]))

            dataOut.data = numpy.reshape(dataOut.data, new_shape)
            dataOut.flagNoData = False

            profileIndex = int(dataOut.nProfiles*n) - 1

        else:

            #nchannels, nsamples
            if self.__remData is None:
                newData = dataOut.data
            else:
                newData = numpy.concatenate((self.__remData, dataOut.data), axis=1)

            self.__profileIndex += 1

            if self.__profileIndex < n:
                self.__remData = newData
                #continue
                return

            self.__profileIndex = 0
            self.__remData = None

            dataOut.data = newData
            dataOut.flagNoData = False

            profileIndex = dataOut.profileIndex/n


        deltaHeight = dataOut.heightList[1] - dataOut.heightList[0]

        dataOut.heightList = numpy.arange(dataOut.nHeights*n) * deltaHeight + dataOut.heightList[0]

        dataOut.nProfiles = int(dataOut.nProfiles/n)

        dataOut.profileIndex = profileIndex

        dataOut.ippSeconds *= n

        return dataOut

class PulsePairVoltage(Operation):
    '''
    Function PulsePair(Signal Power, Velocity)
    The real component of Lag[0] provides Intensity Information
    The imag component of Lag[1] Phase provides Velocity Information

    Configuration Parameters:
    nPRF = Number of Several PRF
    theta = Degree Azimuth angel Boundaries

    Input:
          self.dataOut
          lag[N]
    Affected:
          self.dataOut.spc
    '''
    isConfig       = False
    __profIndex    = 0
    __initime      = None
    __lastdatatime = None
    __buffer       = None
    noise          = None
    __dataReady    = False
    n              = None
    __nch          = 0
    __nHeis        = 0
    removeDC       = False
    ipp            = None
    lambda_        = 0

    def __init__(self,**kwargs):
        Operation.__init__(self,**kwargs)

    def setup(self, dataOut, n = None, removeDC=False):
        '''
        n= Numero de PRF's de entrada
        '''
        self.__initime        = None
        self.__lastdatatime   = 0
        self.__dataReady      = False
        self.__buffer         = 0
        self.__profIndex      = 0
        self.noise            = None
        self.__nch            = dataOut.nChannels
        self.__nHeis          = dataOut.nHeights
        self.removeDC         = removeDC
        self.lambda_          = 3.0e8/(9345.0e6)
        self.ippSec           = dataOut.ippSeconds
        self.nCohInt          = dataOut.nCohInt
        print("IPPseconds",dataOut.ippSeconds)

        print("ELVALOR DE n es:", n)
        if n == None:
            raise ValueError("n should be specified.")

        if n != None:
            if n<2:
                raise ValueError("n should be greater than 2")

        self.n       = n
        self.__nProf = n

        self.__buffer = numpy.zeros((dataOut.nChannels,
                                           n,
                                           dataOut.nHeights),
                                          dtype='complex')

    def putData(self,data):
        '''
        Add a profile to he __buffer and increase in one the __profiel Index
        '''
        self.__buffer[:,self.__profIndex,:]= data
        self.__profIndex      += 1
        return

    def pushData(self,dataOut):
        '''
        Return the PULSEPAIR and the profiles used in the operation
        Affected :  self.__profileIndex
        '''
        #----------------- Remove DC-----------------------------------
        if self.removeDC==True:
            mean    = numpy.mean(self.__buffer,1)
            tmp     = mean.reshape(self.__nch,1,self.__nHeis)
            dc= numpy.tile(tmp,[1,self.__nProf,1])
            self.__buffer = self.__buffer -  dc
        #------------------Calculo de Potencia ------------------------
        pair0       = self.__buffer*numpy.conj(self.__buffer)
        pair0       = pair0.real
        lag_0       = numpy.sum(pair0,1)
        #------------------Calculo de Ruido x canal--------------------
        self.noise  = numpy.zeros(self.__nch)
        for i in range(self.__nch):
            daux         = numpy.sort(pair0[i,:,:],axis= None)
            self.noise[i]=hildebrand_sekhon( daux ,self.nCohInt)

        self.noise       = self.noise.reshape(self.__nch,1)
        self.noise       = numpy.tile(self.noise,[1,self.__nHeis])
        noise_buffer     = self.noise.reshape(self.__nch,1,self.__nHeis)
        noise_buffer     = numpy.tile(noise_buffer,[1,self.__nProf,1])
        #------------------ Potencia recibida= P , Potencia senal = S , Ruido= N--
        #------------------   P= S+N  ,P=lag_0/N ---------------------------------
        #-------------------- Power --------------------------------------------------
        data_power       = lag_0/(self.n*self.nCohInt)
        #------------------  Senal  ---------------------------------------------------
        data_intensity   = pair0 - noise_buffer
        data_intensity   = numpy.sum(data_intensity,axis=1)*(self.n*self.nCohInt)#*self.nCohInt)
        #data_intensity   = (lag_0-self.noise*self.n)*(self.n*self.nCohInt)
        for i in range(self.__nch):
            for j in range(self.__nHeis):
                if data_intensity[i][j]  < 0:
                    data_intensity[i][j] = numpy.min(numpy.absolute(data_intensity[i][j]))

        #----------------- Calculo de Frecuencia y Velocidad doppler--------
        pair1            = self.__buffer[:,:-1,:]*numpy.conjugate(self.__buffer[:,1:,:])
        lag_1            = numpy.sum(pair1,1)
        data_freq        = (-1/(2.0*math.pi*self.ippSec*self.nCohInt))*numpy.angle(lag_1)
        data_velocity    = (self.lambda_/2.0)*data_freq

        #---------------- Potencia promedio estimada de la Senal-----------
        lag_0            = lag_0/self.n
        S                = lag_0-self.noise

        #---------------- Frecuencia Doppler promedio ---------------------
        lag_1            = lag_1/(self.n-1)
        R1               = numpy.abs(lag_1)

        #---------------- Calculo del SNR----------------------------------
        data_snrPP       = S/self.noise
        for i in range(self.__nch):
            for j in range(self.__nHeis):
                if data_snrPP[i][j]  < 1.e-20:
                    data_snrPP[i][j] = 1.e-20

        #----------------- Calculo del ancho espectral ----------------------
        L                = S/R1
        L                = numpy.where(L<0,1,L)
        L                = numpy.log(L)
        tmp              = numpy.sqrt(numpy.absolute(L))
        data_specwidth   = (self.lambda_/(2*math.sqrt(2)*math.pi*self.ippSec*self.nCohInt))*tmp*numpy.sign(L)
        n                = self.__profIndex

        self.__buffer    = numpy.zeros((self.__nch, self.__nProf,self.__nHeis),  dtype='complex')
        self.__profIndex = 0
        return data_power,data_intensity,data_velocity,data_snrPP,data_specwidth,n


    def pulsePairbyProfiles(self,dataOut):

        self.__dataReady     =  False
        data_power           =  None
        data_intensity       =  None
        data_velocity        =  None
        data_specwidth       =  None
        data_snrPP           =  None
        self.putData(data=dataOut.data)
        if self.__profIndex  == self.n:
            data_power,data_intensity, data_velocity,data_snrPP,data_specwidth, n   = self.pushData(dataOut=dataOut)
            self.__dataReady                   = True

        return data_power, data_intensity, data_velocity, data_snrPP, data_specwidth


    def pulsePairOp(self, dataOut, datatime= None):

        if self.__initime == None:
            self.__initime = datatime
        data_power, data_intensity, data_velocity, data_snrPP, data_specwidth = self.pulsePairbyProfiles(dataOut)
        self.__lastdatatime           = datatime

        if data_power is None:
            return None, None, None,None,None,None

        avgdatatime    = self.__initime
        deltatime      = datatime - self.__lastdatatime
        self.__initime = datatime

        return data_power, data_intensity, data_velocity, data_snrPP, data_specwidth, avgdatatime

    def run(self, dataOut,n = None,removeDC= False, overlapping= False,**kwargs):

        if not self.isConfig:
            self.setup(dataOut = dataOut, n    = n , removeDC=removeDC , **kwargs)
            self.isConfig   = True
        data_power, data_intensity, data_velocity,data_snrPP,data_specwidth, avgdatatime = self.pulsePairOp(dataOut, dataOut.utctime)
        dataOut.flagNoData                         = True

        if self.__dataReady:
            dataOut.nCohInt        *= self.n
            dataOut.dataPP_POW      = data_intensity # S
            dataOut.dataPP_POWER    = data_power     # P
            dataOut.dataPP_DOP      = data_velocity
            dataOut.dataPP_SNR      = data_snrPP
            dataOut.dataPP_WIDTH    = data_specwidth
            dataOut.PRFbyAngle      = self.n         #numero de PRF*cada angulo rotado que equivale a un tiempo.
            dataOut.utctime         = avgdatatime
            dataOut.flagNoData      = False
        return dataOut



# import collections
# from scipy.stats import mode
#
# class Synchronize(Operation):
#
#     isConfig = False
#     __profIndex = 0
#
#     def __init__(self, **kwargs):
#
#         Operation.__init__(self, **kwargs)
# #         self.isConfig = False
#         self.__powBuffer = None
#         self.__startIndex = 0
#         self.__pulseFound = False
#
#     def __findTxPulse(self, dataOut, channel=0, pulse_with = None):
#
#         #Read data
#
#         powerdB = dataOut.getPower(channel = channel)
#         noisedB = dataOut.getNoise(channel = channel)[0]
#
#         self.__powBuffer.extend(powerdB.flatten())
#
#         dataArray = numpy.array(self.__powBuffer)
#
#         filteredPower = numpy.correlate(dataArray, dataArray[0:self.__nSamples], "same")
#
#         maxValue = numpy.nanmax(filteredPower)
#
#         if maxValue < noisedB + 10:
#             #No se encuentra ningun pulso de transmision
#             return None
#
#         maxValuesIndex = numpy.where(filteredPower > maxValue - 0.1*abs(maxValue))[0]
#
#         if len(maxValuesIndex) < 2:
#             #Solo se encontro un solo pulso de transmision de un baudio, esperando por el siguiente TX
#             return None
#
#         phasedMaxValuesIndex = maxValuesIndex - self.__nSamples
#
#         #Seleccionar solo valores con un espaciamiento de nSamples
#         pulseIndex = numpy.intersect1d(maxValuesIndex, phasedMaxValuesIndex)
#
#         if len(pulseIndex) < 2:
#             #Solo se encontro un pulso de transmision con ancho mayor a 1
#             return None
#
#         spacing = pulseIndex[1:] - pulseIndex[:-1]
#
#         #remover senales que se distancien menos de 10 unidades o muestras
#         #(No deberian existir IPP menor a 10 unidades)
#
#         realIndex = numpy.where(spacing > 10 )[0]
#
#         if len(realIndex) < 2:
#             #Solo se encontro un pulso de transmision con ancho mayor a 1
#             return None
#
#         #Eliminar pulsos anchos (deja solo la diferencia entre IPPs)
#         realPulseIndex = pulseIndex[realIndex]
#
#         period = mode(realPulseIndex[1:] - realPulseIndex[:-1])[0][0]
#
#         print "IPP = %d samples" %period
#
#         self.__newNSamples = dataOut.nHeights #int(period)
#         self.__startIndex = int(realPulseIndex[0])
#
#         return 1
#
#
#     def setup(self, nSamples, nChannels, buffer_size = 4):
#
#         self.__powBuffer = collections.deque(numpy.zeros( buffer_size*nSamples,dtype=numpy.float),
#                                           maxlen = buffer_size*nSamples)
#
#         bufferList = []
#
#         for i in range(nChannels):
#             bufferByChannel = collections.deque(numpy.zeros( buffer_size*nSamples, dtype=numpy.complex) +  numpy.NAN,
#                                           maxlen = buffer_size*nSamples)
#
#             bufferList.append(bufferByChannel)
#
#         self.__nSamples = nSamples
#         self.__nChannels = nChannels
#         self.__bufferList = bufferList
#
#     def run(self, dataOut, channel = 0):
#
#         if not self.isConfig:
#             nSamples = dataOut.nHeights
#             nChannels = dataOut.nChannels
#             self.setup(nSamples, nChannels)
#             self.isConfig = True
#
#         #Append new data to internal buffer
#         for thisChannel in range(self.__nChannels):
#             bufferByChannel = self.__bufferList[thisChannel]
#             bufferByChannel.extend(dataOut.data[thisChannel])
#
#         if self.__pulseFound:
#             self.__startIndex -= self.__nSamples
#
#         #Finding Tx Pulse
#         if not self.__pulseFound:
#             indexFound = self.__findTxPulse(dataOut, channel)
#
#             if indexFound == None:
#                 dataOut.flagNoData = True
#                 return
#
#             self.__arrayBuffer = numpy.zeros((self.__nChannels, self.__newNSamples), dtype = numpy.complex)
#             self.__pulseFound = True
#             self.__startIndex = indexFound
#
#         #If pulse was found ...
#         for thisChannel in range(self.__nChannels):
#             bufferByChannel = self.__bufferList[thisChannel]
#             #print self.__startIndex
#             x = numpy.array(bufferByChannel)
#             self.__arrayBuffer[thisChannel] = x[self.__startIndex:self.__startIndex+self.__newNSamples]
#
#         deltaHeight = dataOut.heightList[1] - dataOut.heightList[0]
#         dataOut.heightList = numpy.arange(self.__newNSamples)*deltaHeight
# #             dataOut.ippSeconds = (self.__newNSamples / deltaHeight)/1e6
#
#         dataOut.data = self.__arrayBuffer
#
#         self.__startIndex += self.__newNSamples
#
#         return
    

class SSheightProfiles(Operation):
    step          = None
    nsamples      = None
    bufferShape   = None
    profileShape  = None
    sshProfiles   = None
    profileIndex  = None
    def __init__(self, **kwargs):
        Operation.__init__(self, **kwargs)
        self.isConfig = False
    def setup(self,dataOut ,step = None , nsamples = None):
        if step == None and nsamples == None:
            raise ValueError("step or nheights should be specified ...")
        self.step         = step
        self.nsamples     = nsamples
        self.__nChannels  = dataOut.nChannels
        self.__nProfiles  = dataOut.nProfiles
        self.__nHeis      = dataOut.nHeights
        shape             = dataOut.data.shape #nchannels, nprofiles, nsamples
        residue     =  (shape[1] - self.nsamples) % self.step
        if residue != 0:
            print("The residue is %d, step=%d should be multiple of %d to avoid loss of %d samples"%(residue,step,shape[1] - self.nsamples,residue))
        deltaHeight      =  dataOut.heightList[1] - dataOut.heightList[0]
        numberProfile    =  self.nsamples
        numberSamples    =  (shape[1] - self.nsamples)/self.step
        self.bufferShape  = int(shape[0]), int(numberSamples), int(numberProfile)  # nchannels, nsamples , nprofiles
        self.profileShape = int(shape[0]), int(numberProfile), int(numberSamples)  # nchannels, nprofiles, nsamples
        self.buffer       = numpy.zeros(self.bufferShape , dtype=numpy.complex_)
        self.sshProfiles  = numpy.zeros(self.profileShape, dtype=numpy.complex_)
    def run(self, dataOut, step, nsamples, code = None, repeat = None):
        dataOut.flagNoData      = True
        profileIndex            = None
        #print("nProfiles, nHeights ",dataOut.nProfiles, dataOut.nHeights)
        #print(dataOut.getFreqRange(1)/1000.)
        #exit(1)
        if dataOut.flagDataAsBlock:
            dataOut.data = numpy.average(dataOut.data,axis=1)
            #print("jee")
        dataOut.flagDataAsBlock = False
        if not self.isConfig:
            self.setup(dataOut, step=step , nsamples=nsamples)
            #print("Setup done")
            self.isConfig = True
        if code is not None:
            code = numpy.array(code)
            code_block = code
            if repeat is not None:
                code_block = numpy.repeat(code_block, repeats=repeat, axis=1)
                #print(code_block.shape)
        for i in range(self.buffer.shape[1]):
            if code is not None:
                self.buffer[:,i] = dataOut.data[:,i*self.step:i*self.step + self.nsamples]*code_block
            else:
                self.buffer[:,i]    = dataOut.data[:,i*self.step:i*self.step + self.nsamples]#*code[dataOut.profileIndex,:]
            #self.buffer[:,j,self.__nHeis-j*self.step - self.nheights:self.__nHeis-j*self.step] = numpy.flip(dataOut.data[:,j*self.step:j*self.step + self.nheights])
        for j in range(self.buffer.shape[0]):
            self.sshProfiles[j] = numpy.transpose(self.buffer[j])
        profileIndex  =  self.nsamples
        deltaHeight   =  dataOut.heightList[1] - dataOut.heightList[0]
        ippSeconds    =  (deltaHeight*1.0e-6)/(0.15)
        #print("ippSeconds, dH: ",ippSeconds,deltaHeight)
        try:
            if dataOut.concat_m  is not None:
                ippSeconds= ippSeconds/float(dataOut.concat_m)
                #print "Profile concat %d"%dataOut.concat_m
        except:
            pass
        dataOut.data            = self.sshProfiles
        dataOut.flagNoData      = False
        dataOut.heightList      = numpy.arange(self.buffer.shape[1]) *self.step*deltaHeight + dataOut.heightList[0]
        dataOut.nProfiles       = int(dataOut.nProfiles*self.nsamples)
        dataOut.profileIndex    = profileIndex
        dataOut.flagDataAsBlock = True
        dataOut.ippSeconds      = ippSeconds
        dataOut.step            = self.step
        #print(numpy.shape(dataOut.data))
        #exit(1)
        #print("new data shape and time:", dataOut.data.shape, dataOut.utctime)
        return dataOut
################################################################################3############################3
################################################################################3############################3
################################################################################3############################3
################################################################################3############################3

class cleanHeightsInterf(Operation):
    """
    Escrito: Joab Apaza, creado para eliminar interferencias en alturas específicas

    :param heightsList  :   Listado de alturas a eliminar
    :param repeats      :   Numero de repeticiones del listado en el rango del IPP
    :param step         :   Distancia en km hasta la prox repeticion del listado
    :param factor       :   Fator de atenuación
    :param idate        :   fecha de la interferencia
    :param startH       :   hora de inicio de la interferencia
    :param endH         :   hora de finalización de la interferencia

    :return: dataOut
    
    """
    
    __slots__ =('heights_indx', 'repeats', 'step', 'factor', 'idate', 'idxs','config','wMask')
    def __init__(self):
        self.repeats = 0
        self.factor=1
        self.wMask = None
        self.config = False
        self.idxs = None
        self.heights_indx = None

    def run(self, dataOut, heightsList, repeats=0, step=0, factor=1, idate=None, startH=None, endH=None):

        #print(dataOut.data.shape)

        startTime = datetime.datetime.combine(idate,startH)
        endTime =  datetime.datetime.combine(idate,endH)
        currentTime = datetime.datetime.fromtimestamp(dataOut.utctime)

        if currentTime < startTime or currentTime > endTime:
            return dataOut
        if not self.config:

            #print(wMask)
            heights = [float(hei) for hei in heightsList]
            for r in range(repeats):
                 heights += [ (h+(step*(r+1))) for h in heights]
            #print(heights)
            heiList = dataOut.heightList
            self.heights_indx = [getHei_index(h,h,heiList)[0] for h in heights]

            self.wMask = numpy.asarray(factor)
            self.wMask = numpy.tile(self.wMask,(repeats+2))
            self.config = True

        """
        getNoisebyHildebrand(self, channel=None, ymin_index=None, ymax_index=None)
        """
        #print(self.noise =10*numpy.log10(dataOut.getNoisebyHildebrand(ymin_index=self.min_ref, ymax_index=self.max_ref)))


        for ch in range(dataOut.data.shape[0]):
            i = 0


            for hei in self.heights_indx:
                h = hei - 1


                if dataOut.data.ndim < 3:
                    module = numpy.absolute(dataOut.data[ch,h])
                    prev_h1 = numpy.absolute(dataOut.data[ch,h-1])
                    dataOut.data[ch,h] = (dataOut.data[ch,h])/module * prev_h1

                    #dataOut.data[ch,hei-1] = (dataOut.data[ch,hei-1])*self.wMask[i]
                else:
                    module = numpy.absolute(dataOut.data[ch,:,h])
                    prev_h1 = numpy.absolute(dataOut.data[ch,:,h-1])
                    dataOut.data[ch,:,h] = (dataOut.data[ch,:,h])/module * prev_h1
                    #dataOut.data[ch,:,hei-1] = (dataOut.data[ch,:,hei-1])*self.wMask[i]
                    #print("done")
                i += 1


        return dataOut
    
class SSheightProfiles2(Operation):
    
    """
    Escrito: Joab Apaza, basado en la Operación SSheightProfiles
    Procesa por perfiles y por bloques, Para procesar pulso largo
    Versión corregida y actualizada para trabajar con RemoveProfileSats2

    :param step     :   Pasos en la selección de alturas, equivalente a filtrar por alturas, incrementar disminuye la resolución
    :param nsamples :   Numero de altura a seleccionar
    :param code     :   En caso de codificación del pulso, tambien se decodifica
    :param repeat   :   Numero de repeticiones del codigo


    :return: dataOut
    
    
    """
   
    bufferShape   = None
    profileShape  = None
    sshProfiles   = None
    profileIndex  = None
    #nsamples      = None
    #step          = None
    #deltaHeight = None
    #init_range  = None
    __slots__ = ('step', 'nsamples', 'deltaHeight', 'init_range', 'isConfig', '__nChannels',
                '__nProfiles', '__nHeis', 'deltaHeight', 'new_nHeights')
    def __init__(self, **kwargs):
        Operation.__init__(self, **kwargs)
        self.isConfig = False
    def setup(self,dataOut ,step = None , nsamples = None):
        if step == None and nsamples == None:
            raise ValueError("step or nheights should be specified ...")
        self.step         = step
        self.nsamples     = nsamples
        self.__nChannels  = int(dataOut.nChannels)
        self.__nProfiles  = int(dataOut.nProfiles)
        self.__nHeis      = int(dataOut.nHeights)
        residue     =  (self.__nHeis - self.nsamples) % self.step
        if residue != 0:
            print("The residue is %d, step=%d should be multiple of %d to avoid loss of %d samples"%(residue,step,self.__nProfiles - self.nsamples,residue))
        self.deltaHeight      =  dataOut.heightList[1] - dataOut.heightList[0]
        self.init_range = dataOut.heightList[0]
        #numberProfile    =  self.nsamples
        numberSamples    =  (self.__nHeis - self.nsamples)/self.step
        self.new_nHeights    =  numberSamples
        self.bufferShape  = int(self.__nChannels), int(numberSamples), int(self.nsamples)  # nchannels, nsamples , nprofiles
        self.profileShape = int(self.__nChannels), int(self.nsamples), int(numberSamples)  # nchannels, nprofiles, nsamples
        self.buffer       = numpy.zeros(self.bufferShape , dtype=numpy.complex_)
        self.sshProfiles  = numpy.zeros(self.profileShape, dtype=numpy.complex_)
    def getNewProfiles(self, data, code=None, repeat=None):
        if code is not None:
            code = numpy.array(code)
            code_block = code
            if repeat is not None:
                code_block = numpy.repeat(code_block, repeats=repeat, axis=1)
        if data.ndim < 3:
            data = data.reshape(self.__nChannels,1,self.__nHeis )
        #print("buff, data, :",self.buffer.shape, data.shape,self.sshProfiles.shape, code_block.shape)
        for ch in range(self.__nChannels):
            for i in range(int(self.new_nHeights)): #nuevas alturas
                if code is not None:
                    self.buffer[ch,i,:] = data[ch,:,i*self.step:i*self.step + self.nsamples]*code_block
                else:
                    self.buffer[ch,i,:] = data[ch,:,i*self.step:i*self.step + self.nsamples]#*code[dataOut.profileIndex,:]
        for j in range(self.__nChannels): #en los cananles
            self.sshProfiles[j,:,:] = numpy.transpose(self.buffer[j,:,:])
        #print("new profs Done")
    def run(self, dataOut, step, nsamples, code = None, repeat = None):
        # print("running")
        if dataOut.flagNoData == True:
            return dataOut
        dataOut.flagNoData = True
        #print("init  data shape:", dataOut.data.shape)
        #print("ch: {}  prof: {}  hs: {}".format(int(dataOut.nChannels),
        #                int(dataOut.nProfiles),int(dataOut.nHeights)))
        profileIndex            = None
        # if not dataOut.flagDataAsBlock:
        #     dataOut.nProfiles = 1
        if not self.isConfig:
            self.setup(dataOut, step=step , nsamples=nsamples)
            #print("Setup done")
            self.isConfig = True
        dataBlock = None
        nprof = 1
        if dataOut.flagDataAsBlock:
            nprof = int(dataOut.nProfiles)
        #print("dataOut nProfiles:", dataOut.nProfiles)
        for profile in range(nprof):
            if dataOut.flagDataAsBlock:
                #print("read blocks")
                self.getNewProfiles(dataOut.data[:,profile,:], code=code, repeat=repeat)
            else:
                #print("read profiles")
                self.getNewProfiles(dataOut.data, code=code, repeat=repeat) #only one channe
            if profile == 0:
                dataBlock = self.sshProfiles.copy()
            else:   #by blocks
                dataBlock = numpy.concatenate((dataBlock,self.sshProfiles), axis=1) #profile axis
                #print("by blocks: ",dataBlock.shape, self.sshProfiles.shape)
        profileIndex  =  self.nsamples
        #deltaHeight   =  dataOut.heightList[1] - dataOut.heightList[0]
        ippSeconds    =  (self.deltaHeight*1.0e-6)/(0.15)
        dataOut.data            = dataBlock
        #print("show me: ",self.step,self.deltaHeight, dataOut.heightList, self.new_nHeights)
        dataOut.heightList      = numpy.arange(int(self.new_nHeights)) *self.step*self.deltaHeight + self.init_range
        dataOut.sampled_heightsFFT = self.nsamples
        dataOut.ippSeconds      = ippSeconds
        dataOut.step            = self.step
        dataOut.deltaHeight     = self.step*self.deltaHeight
        dataOut.flagNoData      = False
        if dataOut.flagDataAsBlock:
            dataOut.nProfiles       = int(dataOut.nProfiles*self.nsamples)
        else:
            dataOut.nProfiles       = int(self.nsamples)
        dataOut.profileIndex    = dataOut.nProfiles
        dataOut.flagDataAsBlock = True
        dataBlock = None
        #print("new data shape:", dataOut.data.shape, dataOut.utctime)
        #update Processing Header:
        dataOut.processingHeaderObj.heightList = dataOut.heightList
        dataOut.processingHeaderObj.ipp = ippSeconds
        dataOut.processingHeaderObj.heightResolution = dataOut.deltaHeight
        #dataOut.processingHeaderObj.profilesPerBlock = nProfiles
        
        # # dataOut.data = CH, PROFILES, HEIGHTS
        #print(dataOut.data .shape)
        if dataOut.flagProfilesByRange:
            # #assuming the same remotion for all channels
            aux = [ self.nsamples - numpy.count_nonzero(dataOut.data[0, :, h]==0)  for h in range(len(dataOut.heightList))]
            dataOut.nProfilesByRange = (numpy.asarray(aux)).reshape((1,len(dataOut.heightList) ))
            #print(dataOut.nProfilesByRange.shape)
        else:
            dataOut.nProfilesByRange = numpy.ones((1, len(dataOut.heightList)))*dataOut.nProfiles
        return dataOut
class RemoveProfileSats(Operation):
    '''
    Escrito: Joab Apaza
    Omite los perfiles contaminados con señal de satélites, usando una altura de referencia (Operacion Obsoleta)
    In: minHei = min_sat_range
        max_sat_range
        min_hei_ref
        max_hei_ref
        th = diference between profiles mean, ref and sats
    Out:
        profile clean
    '''
    __buffer_data = []
    __buffer_times = []
    buffer = None
    outliers_IDs_list = []
    __slots__ = ('n','navg','profileMargin','thHistOutlier','minHei_idx','maxHei_idx','nHeights',
        'first_utcBlock','__profIndex','init_prof','end_prof','lenProfileOut','nChannels',
        '__count_exec','__initime','__dataReady','__ipp', 'minRef', 'maxRef', 'thdB')
    def __init__(self, **kwargs):
        Operation.__init__(self, **kwargs)
        self.isConfig = False
    def setup(self,dataOut, n=None , navg=0.8, profileMargin=50,thHistOutlier=15,
                        minHei=None, maxHei=None, minRef=None, maxRef=None, thdB=10):
        if n == None and timeInterval == None:
            raise ValueError("nprofiles or timeInterval should be specified ...")
        if n != None:
            self.n = n
        self.navg = navg
        self.profileMargin = profileMargin
        self.thHistOutlier = thHistOutlier
        self.__profIndex = 0
        self.buffer = None
        self._ipp = dataOut.ippSeconds
        self.n_prof_released = 0
        self.heightList = dataOut.heightList
        self.init_prof = 0
        self.end_prof = 0
        self.__count_exec = 0
        self.__profIndex = 0
        self.first_utcBlock = None
        #self.__dh = dataOut.heightList[1] - dataOut.heightList[0]
        minHei = minHei
        maxHei = maxHei
        if minHei==None :
            minHei = dataOut.heightList[0]
        if maxHei==None :
            maxHei = dataOut.heightList[-1]
        self.minHei_idx,self.maxHei_idx =  getHei_index(minHei, maxHei, dataOut.heightList)
        self.min_ref, self.max_ref = getHei_index(minRef, maxRef, dataOut.heightList)
        self.nChannels = dataOut.nChannels
        self.nHeights = dataOut.nHeights
        self.test_counter = 0
        self.thdB = thdB
    def filterSatsProfiles(self):
        data = self.__buffer_data
        #print(data.shape)
        nChannels, profiles, heights = data.shape
        indexes=numpy.zeros([], dtype=int)
        outliers_IDs=[]
        for c in range(nChannels):
            #print(self.min_ref,self.max_ref)
            noise_ref = 10* numpy.log10((data[c,:,self.min_ref:self.max_ref] * numpy.conjugate(data[c,:,self.min_ref:self.max_ref])).real)
            #print("Noise ",numpy.percentile(noise_ref,95))
            p95 = numpy.percentile(noise_ref,95)
            noise_ref = noise_ref.mean()
            #print("Noise ",noise_ref
            for h in range(self.minHei_idx, self.maxHei_idx):
                power = 10* numpy.log10((data[c,:,h] * numpy.conjugate(data[c,:,h])).real)
                #th = noise_ref + self.thdB
                th = noise_ref + 1.5*(p95-noise_ref)
                index = numpy.where(power > th )
                if index[0].size > 10 and index[0].size < int(self.navg*profiles):
                    indexes = numpy.append(indexes, index[0])
                #print(index[0])
                #print(index[0])
                # fig,ax = plt.subplots()
                # #ax.set_title(str(k)+" "+str(j))
                # x=range(len(power))
                # ax.scatter(x,power)
                # #ax.axvline(index)
                # plt.grid()
                # plt.show()
            #print(indexes)
        #outliers_IDs = outliers_IDs.astype(numpy.dtype('int64'))
        #outliers_IDs = numpy.unique(outliers_IDs)
        outs_lines = numpy.unique(indexes)
        #Agrupando el histograma de outliers,
        my_bins = numpy.linspace(0,int(profiles), int(profiles/100), endpoint=True)
        hist, bins =  numpy.histogram(outs_lines,bins=my_bins)
        hist_outliers_indexes = numpy.where(hist > self.thHistOutlier)       #es outlier
        hist_outliers_indexes = hist_outliers_indexes[0]
        # if len(hist_outliers_indexes>0):
        #     hist_outliers_indexes = numpy.append(hist_outliers_indexes,hist_outliers_indexes[-1]+1)
        #print(hist_outliers_indexes)
        #print(bins, hist_outliers_indexes)
        bins_outliers_indexes = [int(i) for i in (bins[hist_outliers_indexes])] #
        outlier_loc_index = []
        # for n in range(len(bins_outliers_indexes)):
        #     for e in range(bins_outliers_indexes[n]-self.profileMargin,bins_outliers_indexes[n]+ self.profileMargin):
        #         outlier_loc_index.append(e)
        outlier_loc_index = [e for n in range(len(bins_outliers_indexes)) for e in range(bins_outliers_indexes[n]-self.profileMargin,bins_outliers_indexes[n]+ profiles//100 + self.profileMargin) ]
        outlier_loc_index = numpy.asarray(outlier_loc_index)
        #print("outliers Ids: ", outlier_loc_index, outlier_loc_index.shape)
        outlier_loc_index = outlier_loc_index[ (outlier_loc_index >= 0) & (outlier_loc_index<profiles)]
        #print("outliers final: ", outlier_loc_index)
        from matplotlib import pyplot as plt
        x, y = numpy.meshgrid(numpy.arange(profiles), self.heightList)
        fig, ax = plt.subplots(1,2,figsize=(8, 6))
        dat = data[0,:,:].real
        dat = 10* numpy.log10((data[0,:,:] * numpy.conjugate(data[0,:,:])).real)
        m = numpy.nanmean(dat)
        o = numpy.nanstd(dat)
        #print(m, o, x.shape, y.shape)
        #c = ax[0].pcolormesh(x, y, dat.T, cmap ='YlGnBu', vmin = (m-2*o), vmax = (m+2*o))
        c = ax[0].pcolormesh(x, y, dat.T, cmap ='YlGnBu', vmin = 50, vmax = 75)
        ax[0].vlines(outs_lines,200,600, linestyles='dashed', label = 'outs', color='w')
        fig.colorbar(c)
        ax[0].vlines(outlier_loc_index,650,750, linestyles='dashed', label = 'outs', color='r')
        ax[1].hist(outs_lines,bins=my_bins)
        plt.show()
        self.outliers_IDs_list = outlier_loc_index
        #print("outs list: ", self.outliers_IDs_list)
        return data
    def fillBuffer(self, data, datatime):
        if self.__profIndex == 0:
            self.__buffer_data = data.copy()
        else:
            self.__buffer_data = numpy.concatenate((self.__buffer_data,data), axis=1)#en perfiles
        self.__profIndex += 1
        self.__buffer_times.append(datatime)
    def getData(self, data, datatime=None):
        if self.__profIndex  == 0:
            self.__initime = datatime
        self.__dataReady = False
        self.fillBuffer(data, datatime)
        dataBlock = None
        if self.__profIndex == self.n:
            #print("apnd : ",data)
            dataBlock = self.filterSatsProfiles()
            self.__dataReady = True
        return dataBlock
        if dataBlock is None:
            return None, None
        return dataBlock
    def releaseBlock(self):
        if self.n % self.lenProfileOut != 0:
            raise ValueError("lenProfileOut %d must be submultiple of nProfiles %d" %(self.lenProfileOut, self.n))
            return None
        data = self.buffer[:,self.init_prof:self.end_prof:,:]  #ch, prof, alt
        self.init_prof = self.end_prof
        self.end_prof += self.lenProfileOut
        #print("data release shape: ",dataOut.data.shape, self.end_prof)
        self.n_prof_released += 1
        return data
    def run(self, dataOut, n=None, navg=0.8, nProfilesOut=1, profile_margin=50,
                th_hist_outlier=15,minHei=None, maxHei=None, minRef=None, maxRef=None, thdB=10):
        if not self.isConfig:
            #print("init p idx: ", dataOut.profileIndex )
            self.setup(dataOut,n=n, navg=navg,profileMargin=profile_margin,thHistOutlier=th_hist_outlier,
                        minHei=minHei, maxHei=maxHei, minRef=minRef, maxRef=maxRef, thdB=thdB)
            self.isConfig = True
        dataBlock = None
        if not dataOut.buffer_empty: #hay datos acumulados
            if self.init_prof == 0:
                self.n_prof_released = 0
                self.lenProfileOut = nProfilesOut
                dataOut.flagNoData = False
                #print("tp 2 ",dataOut.data.shape)
                self.init_prof = 0
                self.end_prof = self.lenProfileOut
                dataOut.nProfiles = self.lenProfileOut
            if nProfilesOut == 1:
                dataOut.flagDataAsBlock = False
            else:
                dataOut.flagDataAsBlock = True
            #print("prof: ",self.init_prof)
            dataOut.flagNoData = False
            if numpy.isin(self.n_prof_released, self.outliers_IDs_list):
                #print("omitting: ", self.n_prof_released)
                dataOut.flagNoData = True
            dataOut.ippSeconds = self._ipp
            dataOut.utctime = self.first_utcBlock + self.init_prof*self._ipp
            # print("time: ", dataOut.utctime, self.first_utcBlock, self.init_prof,self._ipp,dataOut.ippSeconds)
            #dataOut.data = self.releaseBlock()
            #########################################################3
            if self.n % self.lenProfileOut != 0:
                raise ValueError("lenProfileOut %d must be submultiple of nProfiles %d" %(self.lenProfileOut, self.n))
                return None
            dataOut.data = None
            if nProfilesOut == 1:
                dataOut.data = self.buffer[:,self.end_prof-1,:]  #ch, prof, alt
            else:
                dataOut.data = self.buffer[:,self.init_prof:self.end_prof,:]  #ch, prof, alt
            self.init_prof = self.end_prof
            self.end_prof += self.lenProfileOut
            #print("data release shape: ",dataOut.data.shape, self.end_prof, dataOut.flagNoData)
            self.n_prof_released += 1
            if self.end_prof >= (self.n +self.lenProfileOut):
                self.init_prof = 0
                self.__profIndex = 0
                self.buffer = None
                dataOut.buffer_empty = True
                self.outliers_IDs_list = []
                self.n_prof_released = 0
                dataOut.flagNoData = False #enviar ultimo aunque sea outlier :(
                #print("cleaning...", dataOut.buffer_empty)
            dataOut.profileIndex    = 0 #self.lenProfileOut
            ####################################################################
            return dataOut
        #print("tp 223 ",dataOut.data.shape)
        dataOut.flagNoData = True
        try:
            #dataBlock = self.getData(dataOut.data.reshape(self.nChannels,1,self.nHeights), dataOut.utctime)
            dataBlock = self.getData(numpy.reshape(dataOut.data,(self.nChannels,1,self.nHeights)), dataOut.utctime)
            self.__count_exec +=1
        except Exception as e:
            print("Error getting profiles data",self.__count_exec )
            print(e)
            sys.exit()
        if self.__dataReady:
            #print("omitting: ", len(self.outliers_IDs_list))
            self.__count_exec = 0
            #dataOut.data =
            #self.buffer = numpy.flip(dataBlock, axis=1)
            self.buffer = dataBlock
            self.first_utcBlock = self.__initime
            dataOut.utctime = self.__initime
            dataOut.nProfiles  = self.__profIndex
            #dataOut.flagNoData = False
            self.init_prof = 0
            self.__profIndex = 0
            self.__initime = None
            dataBlock = None
            self.__buffer_times = []
            dataOut.error = False
            dataOut.useInputBuffer = True
            dataOut.buffer_empty = False
            #print("1 ch: {}  prof: {}  hs: {}".format(int(dataOut.nChannels),int(dataOut.nProfiles),int(dataOut.nHeights)))
        #print(self.__count_exec)
        return dataOut
class RemoveProfileSats2(Operation):
    '''
    Escrito: Joab Apaza
    Omite los perfiles contaminados con señal de satélites, usando una altura de referencia y
    promedia todas las alturas para los cálculos
    In: 
        n       =   Cantidad de perfiles que se acumularan, usualmente 10 segundos
        navg    =   Porcentaje de perfiles que puede considerarse como satélite, máximo 90%
        minHei  =   mínima altura de donde se considera datos a eliminar (km)
        minRef  =   mínima altura de referencia (km)
        maxRef  =   máxima altura de referencia (km)
        nBins   =   Cantidad de bins en el histograma de detección, usar debug para entender mejor
        profile_margin  =   Numero de perfiles extra a considerar antes y depués de los detectados con la operación
        th_hist_outlier =   Umbral de número de detecciones  
        nProfilesOut    =   Cantidad de perfiles en la salida, por bloques o perfiles(1) 
        
        Pensado para remover interferencias de las YAGI, se puede adaptar a otras interferencias
        remYagi     =  Activa la funcion de remoción de interferencias de la YAGI
        nProfYagi   =  Cantidad de perfiles que son afectados, acorde NTX de la YAGI
        offYagi     =  
        minHJULIA   =  Altura mínima donde aparece la señal referencia de JULIA (-50)
        maxHJULIA   =  Altura máxima donde aparece la señal referencia de JULIA (-15)
        debug       = Activa los gráficos, recomendable ejecutar para ajustar los parámetros
                      para un experimento en específico.

    ** se modifica para remover interferencias puntuales, es decir, desde otros radares.
    Inicialmente se ha configurado para omitir también los perfiles de la YAGI en los datos
    de AMISR-ISR.
    Out:
        profile clean
    '''
    __buffer_data = []
    __buffer_times = []
    buffer = None
    outliers_IDs_list = []
    __slots__ = ('n','navg','profileMargin','thHistOutlier','minHei_idx','maxHei_idx','nHeights',
        'first_utcBlock','__profIndex','init_prof','end_prof','lenProfileOut','nChannels','cohFactor',
        '__count_exec','__initime','__dataReady','__ipp', 'minRef', 'maxRef', 'debug','prev_pnoise','thfactor')
    def __init__(self, **kwargs):
        Operation.__init__(self, **kwargs)
        self.isConfig = False
        self.currentTime = None
    def setup(self,dataOut, n=None , navg=0.9, profileMargin=50,thHistOutlier=15,minHei=None, maxHei=None, nBins=10,
        minRef=None, maxRef=None, debug=False, remYagi=False, nProfYagi = 0, offYagi=0,  minHJULIA=None,  maxHJULIA=None,
        idate=None,startH=None,endH=None, thfactor=1 ):
        if n == None and timeInterval == None:
            raise ValueError("nprofiles or timeInterval should be specified ...")
        if n != None:
            self.n = n
        self.navg = navg
        self.profileMargin = profileMargin
        self.thHistOutlier = thHistOutlier
        self.__profIndex = 0
        self.buffer = None
        self._ipp = dataOut.ippSeconds
        self.n_prof_released = 0
        self.heightList = dataOut.heightList
        self.init_prof = 0
        self.end_prof = 0
        self.__count_exec = 0
        self.__profIndex = 0
        self.first_utcBlock = None
        self.prev_pnoise = None
        self.nBins  = nBins
        self.thfactor = thfactor
        #self.__dh = dataOut.heightList[1] - dataOut.heightList[0]
        minHei = minHei
        maxHei = maxHei
        if minHei==None :
            minHei = dataOut.heightList[0]
        if maxHei==None :
            maxHei = dataOut.heightList[-1]
        self.minHei_idx,self.maxHei_idx =  getHei_index(minHei, maxHei, dataOut.heightList)
        self.min_ref, self.max_ref = getHei_index(minRef, maxRef, dataOut.heightList)
        self.nChannels = dataOut.nChannels
        self.nHeights = dataOut.nHeights
        self.test_counter = 0
        self.debug = debug
        self.remYagi = remYagi
        self.cohFactor = dataOut.nCohInt
        if self.remYagi :
            if minHJULIA==None or maxHJULIA==None:
                raise ValueError("Parameters minHYagi and minHYagi are necessary!")
                return 
            if idate==None or startH==None or endH==None:
                raise ValueError("Date and hour parameters are necessary!")
                return 
            self.minHJULIA_idx,self.maxHJULIA_idx =  getHei_index(minHJULIA, maxHJULIA, dataOut.heightList)
            self.offYagi = offYagi
            self.nTxYagi = nProfYagi
            self.startTime = datetime.datetime.combine(idate,startH)
            self.endTime =  datetime.datetime.combine(idate,endH)
        log.warning("Be careful with the selection of parameters for sats removal! It is avisable to \
activate the debug parameter in this operation for calibration", self.name)
    def filterSatsProfiles(self):
        data = self.__buffer_data.copy()
        #print(data.shape)
        nChannels, profiles, heights = data.shape
        indexes=numpy.zeros([], dtype=int)
        indexes = numpy.delete(indexes,0)
        indexesYagi=numpy.zeros([], dtype=int)
        indexesYagi = numpy.delete(indexesYagi,0)
        indexesYagi_up=numpy.zeros([], dtype=int)
        indexesYagi_up = numpy.delete(indexesYagi_up,0)
        indexesYagi_down=numpy.zeros([], dtype=int)
        indexesYagi_down = numpy.delete(indexesYagi_down,0)
        indexesJULIA=numpy.zeros([], dtype=int)
        indexesJULIA = numpy.delete(indexesJULIA,0)
        outliers_IDs=[]
      
        div = profiles//self.nBins
        for c in range(nChannels):
            #print(self.min_ref,self.max_ref)
            import scipy.signal
            b, a = scipy.signal.butter(3, 0.5)
            #noise_ref = (data[c,:,self.min_ref:self.max_ref] * numpy.conjugate(data[c,:,self.min_ref:self.max_ref]))
            noise_ref = numpy.abs(data[c,:,self.min_ref:self.max_ref])
            lnoise = len(noise_ref[0,:])
            #print(noise_ref.shape)
            noise_ref = noise_ref.mean(axis=1)
            #fnoise = noise_ref
            fnoise  = scipy.signal.filtfilt(b, a, noise_ref)
            #noise_refdB = 10* numpy.log10(noise_ref)
            #print("Noise ",numpy.percentile(noise_ref,95))
            p95 = numpy.percentile(fnoise,95)
            mean_noise = fnoise.mean()
            
            if self.prev_pnoise != None:
                if mean_noise < (1.1 * self.prev_pnoise) and mean_noise > (0.9 * self.prev_pnoise):
                    mean_noise = 0.9*mean_noise + 0.1*self.prev_pnoise
                    self.prev_pnoise = mean_noise
                else:
                    mean_noise = self.prev_pnoise
            else:
                self.prev_pnoise = mean_noise
            std = fnoise.std()+ fnoise.mean()
            #power = (data[c,:,self.minHei_idx:self.maxHei_idx] * numpy.conjugate(data[c,:,self.minHei_idx:self.maxHei_idx]))
            power = numpy.abs(data[c,:,self.minHei_idx:self.maxHei_idx])
            npower = len(power[0,:])
            #print(power.shape)
            power = power.mean(axis=1) 
            fpower = scipy.signal.filtfilt(b, a, power)
            #print(power.shape)
            #powerdB = 10* numpy.log10(power)
            #th = p95 * self.thfactor
            th = mean_noise * self.thfactor
            
            index = numpy.where(fpower > th )
            #print("Noise ",mean_noise, p95)
            #print(index)
            
            if  index[0].size <= int(self.navg*profiles):       #outliers from sats
                indexes = numpy.append(indexes, index[0])
            index2low = numpy.where(fpower < (th*0.5 ))          #outliers from no TX
            if  index2low[0].size <= int(self.navg*profiles):
                indexes = numpy.append(indexes, index2low[0])
            #print("sdas ", noise_ref.mean())
            
            if self.remYagi :
                #print(self.minHJULIA_idx, self.maxHJULIA_idx)
                powerJULIA = (data[c,:,self.minHJULIA_idx:self.maxHJULIA_idx] * numpy.conjugate(data[c,:,self.minHJULIA_idx:self.maxHJULIA_idx])).real
                powerJULIA = powerJULIA.mean(axis=1)
                th_JULIA = powerJULIA.mean()*0.85
                indexJULIA = numpy.where(powerJULIA >= th_JULIA )
                indexesJULIA= numpy.append(indexesJULIA, indexJULIA[0])
                # fig, ax = plt.subplots()
                # ax.plot(powerJULIA)  
                # ax.axhline(th_JULIA, color='r')
                # plt.grid()
                # plt.show()
            if self.debug:
                fig, ax = plt.subplots()
                ax.plot(fpower, label="power")
                #ax.plot(fnoise, label="noise ref")
                ax.axhline(th, color='g', label="th")
                #ax.axhline(std, color='b', label="mean")
                ax.legend()
                plt.grid()
                plt.show()
            #print(indexes)
        #outliers_IDs = outliers_IDs.astype(numpy.dtype('int64'))
        #outliers_IDs = numpy.unique(outliers_IDs)
        # print(indexesJULIA)
        if len(indexesJULIA > 1):
            iJ = indexesJULIA
            locs = [ (iJ[n]-iJ[n-1]) > 5  for n in range(len(iJ))]
            locs_2 = numpy.where(locs)[0]
            #print(locs_2, indexesJULIA[locs_2-1])
            indexesYagi_up = numpy.append(indexesYagi_up, indexesJULIA[locs_2-1])
            indexesYagi_down = numpy.append(indexesYagi_down, indexesJULIA[locs_2])
            
            indexesYagi_up = numpy.append(indexesYagi_up,indexesJULIA[-1])
            indexesYagi_down = numpy.append(indexesYagi_down,indexesJULIA[0])
            indexesYagi_up = numpy.unique(indexesYagi_up)
            indexesYagi_down = numpy.unique(indexesYagi_down)
            aux_ind = [ numpy.arange( (self.offYagi + k)+1, (self.offYagi + k + self.nTxYagi)+1, 1, dtype=int) for k in indexesYagi_up]
            indexesYagi_up = (numpy.asarray(aux_ind)).flatten()
            
            aux_ind2 = [ numpy.arange( (k - self.nTxYagi)+1, k+1 , 1, dtype=int) for k in indexesYagi_down]
            indexesYagi_down = (numpy.asarray(aux_ind2)).flatten()
            indexesYagi = numpy.append(indexesYagi,indexesYagi_up)
            indexesYagi = numpy.append(indexesYagi,indexesYagi_down)
            
            indexesYagi = indexesYagi[ (indexesYagi >= 0) & (indexesYagi<profiles)]
            indexesYagi = numpy.unique(indexesYagi)
        #print("indexes: " ,indexes)
        outs_lines = numpy.unique(indexes)
        #print(outs_lines)
        #Agrupando el histograma de outliers,
        my_bins = numpy.linspace(0,int(profiles), div, endpoint=True)
        hist, bins =  numpy.histogram(outs_lines,bins=my_bins)
        #print("hist: ",hist)
        hist_outliers_indexes = numpy.where(hist >= self.thHistOutlier)[0]      #es outlier
        # print(hist_outliers_indexes)
        if len(hist_outliers_indexes>0):
            hist_outliers_indexes = numpy.append(hist_outliers_indexes,hist_outliers_indexes[-1]+1)
        bins_outliers_indexes = [int(i)+1 for i in (bins[hist_outliers_indexes])] #
        outlier_loc_index = []
        #print("out indexes ", bins_outliers_indexes)
        # if len(bins_outliers_indexes) <= 2:
        #     extprof = 0
        # else:
        #     extprof = self.profileMargin
        
        extprof = self.profileMargin
        outlier_loc_index = [e for n in range(len(bins_outliers_indexes)) for e in range(bins_outliers_indexes[n]-extprof,bins_outliers_indexes[n] + extprof) ]
        outlier_loc_index = numpy.asarray(outlier_loc_index)
        # if len(outlier_loc_index)>1:
        #     ipmax = numpy.where(fpower==fpower.max())[0]
        #     print("pmax: ",ipmax)
        
        #print("outliers Ids: ", outlier_loc_index, outlier_loc_index.shape)
        outlier_loc_index = outlier_loc_index[ (outlier_loc_index >= 0) & (outlier_loc_index<profiles)]
        #print("outliers final: ", outlier_loc_index)
        
        if self.debug:
            x, y = numpy.meshgrid(numpy.arange(profiles), self.heightList)
            fig, ax = plt.subplots(nChannels,2,figsize=(8, 6))
            
            for i in range(nChannels):
                dat = data[i,:,:].real
                dat = 10* numpy.log10((data[i,:,:] * numpy.conjugate(data[i,:,:])).real)
                m = numpy.nanmean(dat)
                o = numpy.nanstd(dat)
                if nChannels>1:
                    c = ax[i][0].pcolormesh(x, y, dat.T, cmap ='jet', vmin = 60, vmax = 70)
                    ax[i][0].vlines(outs_lines,650,700, linestyles='dashed', label = 'outs', color='w')
                    #fig.colorbar(c)
                    ax[i][0].vlines(outlier_loc_index,700,750, linestyles='dashed', label = 'outs', color='r')
                    ax[i][1].hist(outs_lines,bins=my_bins)
                    if self.remYagi :
                        ax[0].vlines(indexesYagi,750,850, linestyles='dashed', label = 'yagi', color='m')
                else:
                    c = ax[0].pcolormesh(x, y, dat.T, cmap ='jet', vmin = 60, vmax = (70+2*self.cohFactor))
                    ax[0].vlines(outs_lines,650,700, linestyles='dashed', label = 'outs', color='w')
                    #fig.colorbar(c)
                    ax[0].vlines(outlier_loc_index,700,750, linestyles='dashed', label = 'outs', color='r')
                    
                    ax[1].hist(outs_lines,bins=my_bins)
                    if self.remYagi :
                        ax[0].vlines(indexesYagi,750,850, linestyles='dashed', label = 'yagi', color='m')
            plt.show()
        
        if self.remYagi and (self.currentTime < self.startTime and self.currentTime < self.endTime):
            outlier_loc_index = numpy.append(outlier_loc_index,indexesYagi)
        self.outliers_IDs_list = numpy.unique(outlier_loc_index)
        
        #print("outs list: ", self.outliers_IDs_list)
        return self.__buffer_data
    def fillBuffer(self, data, datatime):
        if self.__profIndex == 0:
            self.__buffer_data = data.copy()
        else:
            self.__buffer_data = numpy.concatenate((self.__buffer_data,data), axis=1)#en perfiles
        self.__profIndex += 1
        self.__buffer_times.append(datatime)
    def getData(self, data, datatime=None):
        if self.__profIndex  == 0:
            self.__initime = datatime
        self.__dataReady = False
        self.fillBuffer(data, datatime)
        dataBlock = None
        if self.__profIndex == self.n:
            #print("apnd : ",data)
            dataBlock = self.filterSatsProfiles()
            self.__dataReady = True
        return dataBlock
        if dataBlock is None:
            return None, None
        return dataBlock
    def releaseBlock(self):
        if self.n % self.lenProfileOut != 0:
            raise ValueError("lenProfileOut %d must be submultiple of nProfiles %d" %(self.lenProfileOut, self.n))
            return None
        data = self.buffer[:,self.init_prof:self.end_prof:,:]  #ch, prof, alt
        self.init_prof = self.end_prof
        self.end_prof += self.lenProfileOut
        #print("data release shape: ",dataOut.data.shape, self.end_prof)
        self.n_prof_released += 1
        return data
    def run(self, dataOut, n=None, navg=0.9, nProfilesOut=1, profile_margin=50, th_hist_outlier=15,minHei=None,nBins=10,
            maxHei=None, minRef=None, maxRef=None, debug=False, remYagi=False, nProfYagi = 0, offYagi=0, minHJULIA=None, maxHJULIA=None,
            idate=None,startH=None,endH=None, thfactor=1):
        if not self.isConfig:
            #print("init p idx: ", dataOut.profileIndex )
            self.setup(dataOut,n=n, navg=navg,profileMargin=profile_margin,thHistOutlier=th_hist_outlier,minHei=minHei,
                nBins=10, maxHei=maxHei, minRef=minRef, maxRef=maxRef, debug=debug, remYagi=remYagi, nProfYagi = nProfYagi, 
                offYagi=offYagi, minHJULIA=minHJULIA,maxHJULIA=maxHJULIA,idate=idate,startH=startH,endH=endH, thfactor=thfactor)
            self.isConfig = True
        dataBlock = None
        self.currentTime = datetime.datetime.fromtimestamp(dataOut.utctime)
        if not dataOut.buffer_empty: #hay datos acumulados
            if self.init_prof == 0:
                self.n_prof_released = 0
                self.lenProfileOut = nProfilesOut
                dataOut.flagNoData = False
                #print("tp 2 ",dataOut.data.shape)
                self.init_prof = 0
                self.end_prof = self.lenProfileOut
                dataOut.nProfiles = self.lenProfileOut
            if nProfilesOut == 1:
                dataOut.flagDataAsBlock = False
            else:
                dataOut.flagDataAsBlock = True
            #print("prof: ",self.init_prof)
            dataOut.flagNoData = False
            if numpy.isin(self.n_prof_released, self.outliers_IDs_list):
                #print("omitting: ", self.n_prof_released)
                dataOut.flagNoData = True
            dataOut.ippSeconds = self._ipp
            dataOut.utctime = self.first_utcBlock + self.init_prof*self._ipp
            # print("time: ", dataOut.utctime, self.first_utcBlock, self.init_prof,self._ipp,dataOut.ippSeconds)
            #dataOut.data = self.releaseBlock()
            #########################################################3
            if self.n % self.lenProfileOut != 0:
                raise ValueError("lenProfileOut %d must be submultiple of nProfiles %d" %(self.lenProfileOut, self.n))
                return None
            dataOut.data = None
            if nProfilesOut == 1:
                dataOut.data = self.buffer[:,self.end_prof-1,:]  #ch, prof, alt
            else:
                dataOut.data = self.buffer[:,self.init_prof:self.end_prof,:]  #ch, prof, alt
            self.init_prof = self.end_prof
            self.end_prof += self.lenProfileOut
            #print("data release shape: ",dataOut.data.shape, self.end_prof, dataOut.flagNoData)
            self.n_prof_released += 1
            if self.end_prof >= (self.n +self.lenProfileOut):
                self.init_prof = 0
                self.__profIndex = 0
                self.buffer = None
                dataOut.buffer_empty = True
                self.outliers_IDs_list = []
                self.n_prof_released = 0
                dataOut.flagNoData = False #enviar ultimo aunque sea outlier :(
                #print("cleaning...", dataOut.buffer_empty)
            dataOut.profileIndex    = self.__profIndex
            ####################################################################
            return dataOut
        #print("tp 223 ",dataOut.data.shape)
        dataOut.flagNoData = True
        try:
            #dataBlock = self.getData(dataOut.data.reshape(self.nChannels,1,self.nHeights), dataOut.utctime)
            dataBlock = self.getData(numpy.reshape(dataOut.data,(self.nChannels,1,self.nHeights)), dataOut.utctime)
            self.__count_exec +=1
        except Exception as e:
            print("Error getting profiles data",self.__count_exec )
            print(e)
            sys.exit()
        if self.__dataReady:
            #print("omitting: ", len(self.outliers_IDs_list))
            self.__count_exec = 0
            #dataOut.data =
            #self.buffer = numpy.flip(dataBlock, axis=1)
            self.buffer = dataBlock
            self.first_utcBlock = self.__initime
            dataOut.utctime = self.__initime
            dataOut.nProfiles  = self.__profIndex
            #dataOut.flagNoData = False
            self.init_prof = 0
            self.__profIndex = 0
            self.__initime = None
            dataBlock = None
            self.__buffer_times = []
            dataOut.error = False
            dataOut.useInputBuffer = True
            dataOut.buffer_empty = False
            #print("1 ch: {}  prof: {}  hs: {}".format(int(dataOut.nChannels),int(dataOut.nProfiles),int(dataOut.nHeights)))
        #print(self.__count_exec)
        return dataOut
class remHeightsIppInterf(Operation):
    def __init__(self, **kwargs):
        
        Operation.__init__(self, **kwargs)
        self.isConfig = False
        self.heights_indx = None
        self.heightsList = []
        
        self.ipp1 = None
        self.ipp2 = None
        self.tx1 = None
        self.tx2 = None 
        self.dh1 = None
    def setup(self, dataOut, ipp1=None, ipp2=None, tx1=None, tx2=None, dh1=None, 
                     idate=None, startH=None, endH=None):
        self.ipp1 = ipp1
        self.ipp2 = ipp2
        self.tx1 = tx1
        self.tx2 = tx2 
        self.dh1 = dh1
       
        _maxIpp1R = dataOut.heightList.max()
        _n_repeats = int(_maxIpp1R / ipp2)
        _init_hIntf = (tx1 + ipp2/2)+ dh1
        _n_hIntf = int(tx2 / dh1)
        self.heightsList = [_init_hIntf+n*ipp2 for n in range(_n_repeats) ]
        heiList = dataOut.heightList
        self.heights_indx = [getHei_index(h,h,heiList)[0] for h in self.heightsList]
        
        self.heights_indx = [ numpy.asarray([k for k in range(_n_hIntf+2)])+(getHei_index(h,h,heiList)[0] -1) for h in self.heightsList]
        self.heights_indx  = numpy.asarray(self.heights_indx )
        self.isConfig = True
        self.startTime = datetime.datetime.combine(idate,startH)
        self.endTime =  datetime.datetime.combine(idate,endH)
        #print(self.startTime, self.endTime)
        #print("nrepeats: ", _n_repeats, " _nH: ",_n_hIntf )
    
        log.warning("Heights set to zero (km): ",  self.name)
        log.warning(str((dataOut.heightList[self.heights_indx].flatten())),  self.name)
        log.warning("Be careful with the selection of heights for noise calculation!")
    def run(self, dataOut, ipp1=None, ipp2=None, tx1=None, tx2=None, dh1=None, idate=None,
                     startH=None, endH=None):
        #print(locals().values())
        if None in locals().values():
            log.warning('Missing kwargs, invalid values """None""" ', self.name)
            return dataOut
        if not self.isConfig:
            self.setup(dataOut, ipp1=ipp1, ipp2=ipp2, tx1=tx1, tx2=tx2, dh1=dh1, 
                 idate=idate, startH=startH, endH=endH)
        dataOut.flagProfilesByRange = False
        currentTime = datetime.datetime.fromtimestamp(dataOut.utctime)
        if currentTime < self.startTime or currentTime > self.endTime:
            return dataOut
        for ch in range(dataOut.data.shape[0]):
            for hk in self.heights_indx.flatten():
                if dataOut.data.ndim < 3:
                    dataOut.data[ch,hk] = 0.0 + 0.0j
                else:
                    dataOut.data[ch,:,hk] =  0.0 + 0.0j
        dataOut.flagProfilesByRange = True
        
        return dataOut
class profiles2Block(Operation):
    '''
    Escrito: Joab Apaza
    genera un bloque de perfiles, AMISR normalmente entrega datos perfil a perfil
    
        
    Out:
        block
    '''
    isConfig = False
    __buffer_data = []
    __buffer_times = []
    __profIndex = 0
    __byTime = False
    __initime = None
    __lastdatatime = None
    buffer = None
    n = None
    __dataReady = False
    __nChannels = None
    __nHeis = None
    
    def __init__(self, **kwargs):
        Operation.__init__(self, **kwargs)
        self.isConfig = False
    def setup(self,n=None, timeInterval=None):
        if n == None and timeInterval == None:
            raise ValueError("n or timeInterval should be specified ...")
        if n != None:
            self.n = n
            self.__byTime = False
        else:
            self.__integrationtime = timeInterval #* 60. #if (type(timeInterval)!=integer) -> change this line
            self.n = 9999
            self.__byTime = True
        self.__profIndex = 0
    def fillBuffer(self, data, datatime):
        if self.__profIndex == 0:
            self.__buffer_data = data.copy()
        else:
            self.__buffer_data = numpy.concatenate((self.__buffer_data,data), axis=1)#en perfiles
        self.__profIndex += 1
        self.__buffer_times.append(datatime)
    def getData(self, data, datatime=None):
        if self.__initime == None:
            self.__initime = datatime
        if data.ndim < 3:
                data = data.reshape(self.__nChannels,1,self.__nHeis )
        if self.__byTime:
            dataBlock = self.byTime(data, datatime)
        else:
            dataBlock = self.byProfiles(data, datatime)
        self.__lastdatatime = datatime
        if dataBlock is None:
            return None, None
        return dataBlock, self.__buffer_times
    
    def byProfiles(self, data, datatime):
        self.__dataReady = False
        dataBlock = None
        #         n = None
        # print data
        # raise
        self.fillBuffer(data, datatime)
        if self.__profIndex == self.n:
            dataBlock = self.__buffer_data
            self.__dataReady = True
        return dataBlock
    def byTime(self, data, datatime):
        self.__dataReady = False
        dataBlock = None
        n = None
        self.fillBuffer(data, datatime)
        if (datatime - self.__initime) >= self.__integrationtime:
            dataBlock = self.__buffer_data
            self.n = self.__profIndex
            self.__dataReady = True
        return dataBlock
    
    def run(self, dataOut, n=None, timeInterval=None, **kwargs):
        if not self.isConfig:
            self.setup(n=n, timeInterval=timeInterval, **kwargs)
            self.__nChannels = dataOut.nChannels
            self.__nHeis = len(dataOut.heightList)
            self.isConfig = True
        if dataOut.flagDataAsBlock:
            """
            Si la data es leida por bloques, dimension = [nChannels, nProfiles, nHeis]
            """
            raise ValueError("The data is already a block")
            return
        else:
            
            dataBlock, timeBlock = self.getData(dataOut.data, dataOut.utctime)
            
        # print(dataOut.data.shape)
        #   dataOut.timeInterval *= n
        dataOut.flagNoData = True
        if self.__dataReady:
            dataOut.data = dataBlock
            dataOut.flagDataAsBlock = True
            dataOut.utctime = timeBlock[-1]
            dataOut.nProfiles = self.__profIndex
            # print avgdata, avgdatatime
            # raise
            dataOut.flagNoData = False
            self.__profIndex = 0
            self.__initime = None
            #update Processing Header:
            # print(dataOut.data.shape)
        return dataOut
class remFaradayProfiles(Operation):
    """
    This Operation eliminates the profiles affected by the Taus transmitted in the Faraday DP experiment, this class
    creates a boolean array where the affected AMISR profiles are previously identified and filters them during processing.

    :param channel  :   Main channel to clean
    :param nChannels:   Number of channels in AMISR
    :param nProfiles:   Number of profiles per Blck in AMISR
    :param nBlocks  :   NUmber of blocks in AMISR
    :param nIpp1    :   NTX in AMISR
    :param nIpp2    :   NTX in JRO
    :param nTx2     :   Efective NTX in JRO (NTX -nNoise) (200 - 68 )
    :param nTaus    :   Number of Delay TxB 
    :param offTaus  :   Offset to start removing Taus, some taus are in the Tx pulse of AMISR, so they do not need to be removed.
    :param iTaus    :   Lenght of the interference, number of heights affected in each Tau.
    :param nfft     :   Repetitions per beam in AMISR
    :param offIpp   :   To synchronize the 1PPS of AMISR with the xPPS of JRO

    :return: dataOut
    
    :author : Joab Apaza
    """
    def __init__(self, **kwargs):
        
        Operation.__init__(self, **kwargs)
        self.isConfig = False
        self.nprofile2 = 0
        self.profile = 0
        self.flagRun = False
        self.flagRemove = False
        self.k = 0
    def setup(self, channel,nChannels=5, nProfiles=300,nBlocks=100, nIpp2=300, nTx2=132, nTaus=22, offTaus=14, iTaus=8,
                     nfft=1):

        self.nIpp2 = nIpp2
        self.channel = channel
        self.nChannels = nChannels
        self.nTx2 = nTx2
        self.nTaus = nTaus
        
        booldataset = numpy.ones( (nBlocks, nProfiles) )
        self.profilesFlag = None
        #marking the afected profiles
        f_iTaus=False
        f_ntx = False
        fi = 0
        k = 0
        kt =0
        fi_reps = 0
        for i in range(nBlocks):
            for j in range(nProfiles):
                # fi 0---nTaus
                #
                if k%nIpp2==0:  #each sync PPs or 2, 3, or 5
                    f_ntx = True
                    kt = 0
                if f_ntx:
                    
                    if kt%nTaus==0: #each sequence of Taus
                        f_iTaus = True
                        fi = 0
                    if f_iTaus:
                        if fi > offTaus:
                            booldataset[i, j]=0   #Afected profile
                        fi += 1
                        if fi == nTaus: #restart the taus sequence
                            fi = 0
                            f_iTaus = False
                            fi_reps += 1
                    if fi_reps == (nTx2/nTaus):
                        fi = 0
                        fi_reps = 0
                        f_ntx=False
                        #break
                    kt += 1
                k += 1
        # fig = plt.figure()
        # ax = fig.add_subplot(111)
        # cax = ax.pcolormesh(booldataset, cmap='plasma')
        # cbar = fig.colorbar(cax)
        # plt.show()
        #reshape the Flag as AMISR reader 
        
        profPerCH = int( (nProfiles) / (nfft*nChannels))
        new_block = numpy.empty( (nBlocks, nChannels, int(nProfiles/nChannels) ) )
        # print(new_block.shape, profPerCH)
        for thisChannel in range(nChannels):
            ich = thisChannel
            idx_ch = [nfft*(ich + nChannels*k) for k in range(profPerCH)]
            #print(idx_ch)
            if nfft > 1:
                aux = [numpy.arange(i, i+nfft) for i in idx_ch]
                idx_ch  = None
                idx_ch =aux
                idx_ch = numpy.array(idx_ch, dtype=int).flatten()
            else:
                idx_ch = numpy.array(idx_ch, dtype=int)
            new_block[:,ich,:] = booldataset[:,idx_ch]
        
        new_block = numpy.transpose(new_block, (1,0,2))
        new_block = numpy.reshape(new_block, (nChannels,-1))
        #new_block = numpy.reshape(new_block, (nChannels,profPerCH*nBlocks))
        self.profilesFlag = new_block.copy()
        # fig = plt.figure()
        # ax = fig.add_subplot(111)
        # cax = ax.pcolormesh(new_block, cmap='plasma')
        # cbar = fig.colorbar(cax)
        # plt.show()
        self.isConfig = True
        
    def run(self,dataOut, channel=0, nChannels=5, nProfiles=300,nBlocks=100,nIpp1=100,
             nIpp2=300, nTx2=132, nTaus=22, offTaus=12, iTaus=10, nfft=1 ,offIpp=0):
        dataOut.flagNoData = False
        if not self.isConfig:
            self.setup(channel,nChannels=nChannels, nProfiles=nProfiles,nBlocks=nBlocks, nIpp2=nIpp2, 
                    nTx2=nTx2, nTaus=nTaus, offTaus=offTaus, iTaus=iTaus, nfft=nfft)
            #print("Setup Done")
        #print(offIpp*nIpp1/nChannels)
        if  not self.flagRun:
            if self.nprofile2 < offIpp*nIpp1/nChannels :
                self.nprofile2 += 1
                return dataOut
            else:
                self.flagRun = True
                self.profile = 0
        
        #check profile          ## Faraday interference
        if self.profilesFlag[channel, self.profile]==0:
            dataOut.flagNoData = True   # do not pass this profile
        self.profile +=1
        self.nprofile2 +=1 
        if self.nprofile2 == int((nProfiles*nBlocks)/self.nChannels):
            self.nprofile2 = 0
            self.profile = 0
            self.flagRun = False
        return dataOut
  
