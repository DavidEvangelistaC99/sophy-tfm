''''
Created on Set 9, 2015

@author: roj-idl71 Karim Kuyeng

@upgrade: 2021, Joab Apaza

'''

import os
import sys
import glob
import fnmatch
import datetime
import time
import re
import h5py
import numpy

try:
    from gevent import sleep
except:
    from time import sleep

from schainpy.model.data.jroheaderIO import RadarControllerHeader, SystemHeader,ProcessingHeader
from schainpy.model.data.jrodata import Voltage
from schainpy.model.proc.jroproc_base import ProcessingUnit, Operation, MPDecorator
from numpy import imag
from schainpy.utils import log


class AMISRReader(ProcessingUnit):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''

        ProcessingUnit.__init__(self)

        self.set = None
        self.subset = None
        self.extension_file = '.h5'
        self.dtc_str = 'dtc'
        self.dtc_id = 0
        self.status = True
        self.isConfig = False
        self.dirnameList = []
        self.filenameList = []
        self.fileIndex = None
        self.flagNoMoreFiles = False
        self.flagIsNewFile = 0
        self.filename = ''
        self.amisrFilePointer = None

        self.beamCodeMap = None
        self.azimuthList = []
        self.elevationList = []
        self.dataShape = None
        self.flag_old_beams = False
        
        self.flagAsync = False        #Use when the experiment has no syncronization
        self.shiftChannels = 0
        self.profileIndex = 0


        self.beamCodeByFrame = None
        self.radacTimeByFrame = None

        self.dataset = None

        self.__firstFile = True

        self.buffer = None

        self.timezone = 'ut'

        self.__waitForNewFile = 20
        self.__filename_online = None
        #Is really necessary create the output object in the initializer
        self.dataOut = Voltage()
        self.dataOut.error=False
        self.margin_days = 1
        self.flag_ignoreFiles = False  #to activate the ignoring Files flag
        self.flag_standby = False # just keep waiting, use when ignoring files
        self.ignStartDateTime=None
        self.ignEndDateTime=None
        
    def setup(self,path=None,
                    startDate=None,
                    endDate=None,
                    startTime=None,
                    endTime=None,
                    walk=True,
                    timezone='ut',
                    all=0,
                    code = 1,
                    nCode = 1,
                    nBaud = 0,
                    nOsamp = 0,
                    online=False,
                    old_beams=False,
                    margin_days=1,
                    nFFT = None,
                    nChannels = None,
                    ignStartDate=None,
                    ignEndDate=None,
                    ignStartTime=None,
                    ignEndTime=None,
                    syncronization=True,
                    shiftChannels=0
                    ):



        self.timezone = timezone
        self.all = all
        self.online = online
        self.flag_old_beams = old_beams
        self.code = code
        self.nCode = int(nCode)
        self.nBaud = int(nBaud)
        self.nOsamp = int(nOsamp)
        self.margin_days = margin_days
        self.__sampleRate = None
        self.flagAsync = not syncronization
        self.shiftChannels = shiftChannels
        self.nFFT = nFFT
        self.nChannels = nChannels
        if ignStartTime!=None and ignEndTime!=None:
            if ignStartDate!=None and ignEndDate!=None:
                self.ignStartDateTime=datetime.datetime.combine(ignStartDate,ignStartTime)
                self.ignEndDateTime=datetime.datetime.combine(ignEndDate,ignEndTime)
            else:
                self.ignStartDateTime=datetime.datetime.combine(startDate,ignStartTime)
                self.ignEndDateTime=datetime.datetime.combine(endDate,ignEndTime)
            self.flag_ignoreFiles = True

        #self.findFiles()
        if not(online):
            #Busqueda de archivos offline
            self.searchFilesOffLine(path, startDate, endDate, startTime, endTime, walk,)
        else:
            self.searchFilesOnLine(path, startDate, endDate, startTime,endTime,walk)

        if not(self.filenameList):
            raise schainpy.admin.SchainWarning("There is no files into the folder: %s"%(path))
            #sys.exit(0)
            self.dataOut.error = True

        self.fileIndex = 0

        self.readNextFile(online)

        '''
        Add code
        '''
        self.isConfig = True
        # print("Setup Done")
        pass


    def readAMISRHeader(self,fp):

        if self.isConfig and (not self.flagNoMoreFiles):
            newShape = fp.get('Raw11/Data/Samples/Data').shape[1:]
            if self.dataShape != newShape and newShape != None and not self.flag_standby:
                raise schainpy.admin.SchainError("NEW FILE HAS A DIFFERENT SHAPE: ")
                print(self.dataShape,newShape,"\n")
                return 0
        else:
            self.dataShape = fp.get('Raw11/Data/Samples/Data').shape[1:]


        header = 'Raw11/Data/RadacHeader'
        if self.nChannels == None:
            expFile = fp['Setup/Experimentfile'][()].decode()
            linesExp = expFile.split("\n")
            a = [line for line in linesExp if "nbeamcodes" in line]
            self.nChannels = int(a[0][11:])

        if not self.flagAsync:  #for experiments with no syncronization
           self.shiftChannels = 0



        self.beamCodeByPulse = fp.get(header+'/BeamCode') # LIST OF BEAMS PER PROFILE, TO BE USED ON REARRANGE

        
        if (self.startDate > datetime.date(2021, 7, 15)) or self.flag_old_beams: #Se cambió la forma de extracción de Apuntes el 17 o forzar con flag de reorganización
            self.beamcodeFile = fp['Setup/Beamcodefile'][()].decode()
            self.trueBeams = self.beamcodeFile.split("\n")
            self.trueBeams.pop()#remove last
            if self.nFFT == None:
                log.error("FFT or number of repetitions per channels is needed",self.name)
            beams_idx = [k*self.nFFT for k in range(self.nChannels)]
            beams = [self.trueBeams[b] for b in beams_idx]
            self.beamCode = [int(x, 16) for x in beams]

            if(self.flagAsync and self.shiftChannels == 0):
                initBeam = self.beamCodeByPulse[0, 0]
                self.shiftChannels = numpy.argwhere(self.beamCode ==initBeam)[0,0]

        else:
            _beamCode= fp.get('Raw11/Data/Beamcodes') #se usa la manera previa al cambio de apuntes
            self.beamCode = _beamCode[0,:]

        
            

        if self.beamCodeMap == None:
            self.beamCodeMap = fp['Setup/BeamcodeMap']
            for beam in self.beamCode:
                beamAziElev = numpy.where(self.beamCodeMap[:,0]==beam)
                beamAziElev = beamAziElev[0].squeeze()
                self.azimuthList.append(self.beamCodeMap[beamAziElev,1])
                self.elevationList.append(self.beamCodeMap[beamAziElev,2])
                #print("Beamssss: ",self.beamCodeMap[beamAziElev,1],self.beamCodeMap[beamAziElev,2])
        #print(self.beamCode)
        #self.code = fp.get(header+'/Code') # NOT USE FOR THIS
        self.frameCount = fp.get(header+'/FrameCount')# NOT USE FOR THIS
        self.modeGroup = fp.get(header+'/ModeGroup')# NOT USE FOR THIS
        self.nsamplesPulse = fp.get(header+'/NSamplesPulse')# TO GET NSA OR USING DATA FOR THAT
        self.pulseCount = fp.get(header+'/PulseCount')# NOT USE FOR THIS
        self.radacTime = fp.get(header+'/RadacTime')# 1st TIME ON FILE ANDE CALCULATE THE REST WITH IPP*nindexprofile
        self.timeCount = fp.get(header+'/TimeCount')# NOT USE FOR THIS
        self.timeStatus = fp.get(header+'/TimeStatus')# NOT USE FOR THIS
        self.rangeFromFile = fp.get('Raw11/Data/Samples/Range')
        self.frequency =  fp.get('Rx/Frequency')
        txAus = fp.get('Raw11/Data/Pulsewidth') #seconds
        self.baud = fp.get('Raw11/Data/TxBaud')
        sampleRate = fp.get('Rx/SampleRate')
        self.__sampleRate = sampleRate[()]
        self.nblocks = self.pulseCount.shape[0] #nblocks
        self.profPerBlockRAW = self.pulseCount.shape[1] #profiles per block in raw data
        self.nprofiles = self.pulseCount.shape[1] #nprofile
        #self.nsa = self.nsamplesPulse[0,0] #ngates
        self.nsa = len(self.rangeFromFile[0])
        self.nchannels = len(self.beamCode)
        self.ippSeconds = (self.radacTime[0][1] -self.radacTime[0][0]) #Ipp in seconds
        #print("IPPS secs: ",self.ippSeconds)
        #self.__waitForNewFile = self.nblocks  # wait depending on the number of blocks since each block is 1 sec
        self.__waitForNewFile = self.nblocks * self.nprofiles * self.ippSeconds # wait until new file is created

        #filling radar controller header parameters
        self.__ippKm = self.ippSeconds *.15*1e6 # in km
        #self.__txA = txAus[()]*.15 #(ipp[us]*.15km/1us) in km
        self.__txA = txAus[()] #seconds
        self.__txAKm = self.__txA*1e6*.15
        self.__txB = 0
        nWindows=1
        self.__nSamples = self.nsa
        self.__firstHeight = self.rangeFromFile[0][0]/1000 #in km
        self.__deltaHeight = (self.rangeFromFile[0][1] - self.rangeFromFile[0][0])/1000
        #print("amisr-ipp:",self.ippSeconds, self.__ippKm)
        #for now until understand why the code saved is different (code included even though code not in tuf file)
        #self.__codeType = 0
       # self.__nCode = None
       # self.__nBaud = None
        self.__code = self.code
        self.__codeType = 0
        if self.code != None:
            self.__codeType = 1
        self.__nCode = self.nCode
        self.__nBaud = self.nBaud
        self.__baudTX = self.__txA/(self.nBaud)
        #self.__code = 0

        #filling system header parameters
        self.__nSamples = self.nsa
        self.newProfiles = self.nprofiles/self.nchannels
        self.__channelList = [n for n in range(self.nchannels)]

        self.__frequency = self.frequency[0][0]


        return 1


    def createBuffers(self):

        pass

    def __setParameters(self,path='', startDate='',endDate='',startTime='', endTime='', walk=''):
        self.path = path
        self.startDate = startDate
        self.endDate = endDate
        self.startTime = startTime
        self.endTime = endTime
        self.walk = walk
        

    def __checkPath(self):
        if os.path.exists(self.path):
            self.status = 1
        else:
            self.status = 0
            print('Path:%s does not exists'%self.path)

        return


    def __selDates(self, amisr_dirname_format):
        try:
            year = int(amisr_dirname_format[0:4])
            month = int(amisr_dirname_format[4:6])
            dom = int(amisr_dirname_format[6:8])
            thisDate = datetime.date(year,month,dom)
            #margen de un día extra, igual luego se filtra for fecha y hora
            if (thisDate>=(self.startDate - datetime.timedelta(days=self.margin_days)) and thisDate <= (self.endDate)+ datetime.timedelta(days=1)):
                return amisr_dirname_format
        except:
            return None


    def __findDataForDates(self,online=False):

        if not(self.status):
            return None

        pat = '\d+.\d+'
        dirnameList = [re.search(pat,x) for x in os.listdir(self.path)]
        dirnameList = [x for x in dirnameList if x!=None]
        dirnameList = [x.string for x in dirnameList]
        if not(online):
            dirnameList = [self.__selDates(x) for x in dirnameList]
            dirnameList = [x for x in dirnameList if x!=None]
        if len(dirnameList)>0:
            self.status = 1
            self.dirnameList = dirnameList
            self.dirnameList.sort()
        else:
            self.status = 0
            return None

    def __getTimeFromData(self):
        startDateTime_Reader = datetime.datetime.combine(self.startDate,self.startTime)
        endDateTime_Reader = datetime.datetime.combine(self.endDate,self.endTime)

        print('Filtering Files from %s to %s'%(startDateTime_Reader, endDateTime_Reader))
        print('........................................')
        filter_filenameList = []
        self.filenameList.sort()
        total_files = len(self.filenameList)
        #for i in range(len(self.filenameList)-1):
        for i in range(total_files):
            filename = self.filenameList[i]
            #print("file-> ",filename)
            try:
                fp = h5py.File(filename,'r')
                time_str = fp.get('Time/RadacTimeString')

                startDateTimeStr_File = time_str[0][0].decode('UTF-8').split('.')[0]
                #startDateTimeStr_File = "2019-12-16 09:21:11"
                junk = time.strptime(startDateTimeStr_File, '%Y-%m-%d %H:%M:%S')
                startDateTime_File = datetime.datetime(junk.tm_year,junk.tm_mon,junk.tm_mday,junk.tm_hour, junk.tm_min, junk.tm_sec)

                #endDateTimeStr_File = "2019-12-16 11:10:11"
                endDateTimeStr_File = time_str[-1][-1].decode('UTF-8').split('.')[0]
                junk = time.strptime(endDateTimeStr_File, '%Y-%m-%d %H:%M:%S')
                endDateTime_File = datetime.datetime(junk.tm_year,junk.tm_mon,junk.tm_mday,junk.tm_hour, junk.tm_min, junk.tm_sec)

                fp.close()

                #print("check time", startDateTime_File)
                if self.timezone == 'lt':
                    startDateTime_File = startDateTime_File - datetime.timedelta(minutes = 300)
                    endDateTime_File = endDateTime_File - datetime.timedelta(minutes = 300)
                if (startDateTime_File >=startDateTime_Reader and endDateTime_File<=endDateTime_Reader):
                    filter_filenameList.append(filename)

                if (startDateTime_File>endDateTime_Reader):
                    break
            except Exception as e:
                log.warning("Error opening file {} -> {}".format(os.path.split(filename)[1],e))

        filter_filenameList.sort()
        self.filenameList = filter_filenameList

        return 1

    def __filterByGlob1(self, dirName):
        filter_files = glob.glob1(dirName, '*.*%s'%self.extension_file)
        filter_files.sort()
        filterDict = {}
        filterDict.setdefault(dirName)
        filterDict[dirName] = filter_files
        return filterDict

    def __getFilenameList(self, fileListInKeys, dirList):
        for value in fileListInKeys:
            dirName = list(value.keys())[0]
            for file in value[dirName]:
                filename = os.path.join(dirName, file)
                self.filenameList.append(filename)


    def __selectDataForTimes(self, online=False):
        #aun no esta implementado el filtro for tiempo-> implementado en readNextFile
        if not(self.status):
            return None

        dirList = [os.path.join(self.path,x) for x in self.dirnameList]
        fileListInKeys = [self.__filterByGlob1(x) for x in dirList]
        self.__getFilenameList(fileListInKeys, dirList)
        if not(online):
            #filtro por tiempo
            if not(self.all):
                self.__getTimeFromData()

            if len(self.filenameList)>0:
                self.status = 1
                self.filenameList.sort()
            else:
                self.status = 0
                return None

        else:
            #get the last file - 1
            self.filenameList = [self.filenameList[-2]]
        new_dirnameList = []
        for dirname in self.dirnameList:
            junk = numpy.array([dirname in x for x in self.filenameList])
            junk_sum = junk.sum()
            if junk_sum > 0:
                new_dirnameList.append(dirname)
        self.dirnameList = new_dirnameList
        return 1

    def searchFilesOnLine(self, path, startDate, endDate, startTime=datetime.time(0,0,0),
                            endTime=datetime.time(23,59,59),walk=True):

        if endDate ==None:
         startDate = datetime.datetime.utcnow().date()
         endDate = datetime.datetime.utcnow().date()

        self.__setParameters(path=path, startDate=startDate, endDate=endDate,startTime = startTime,endTime=endTime, walk=walk)

        self.__checkPath()

        self.__findDataForDates(online=True)

        self.dirnameList = [self.dirnameList[-1]]

        self.__selectDataForTimes(online=True)

        return


    def searchFilesOffLine(self,
                            path,
                            startDate,
                            endDate,
                            startTime=datetime.time(0,0,0),
                            endTime=datetime.time(23,59,59),
                            walk=True):

        self.__setParameters(path, startDate, endDate, startTime, endTime, walk)

        self.__checkPath()

        self.__findDataForDates()

        self.__selectDataForTimes()

        for i in range(len(self.filenameList)):
            print("%s" %(self.filenameList[i]))

        return

    def __setNextFileOffline(self):

        try:
            self.filename = self.filenameList[self.fileIndex]
            self.amisrFilePointer = h5py.File(self.filename,'r')
            self.fileIndex += 1
        except:
            self.flagNoMoreFiles = 1
            raise schainpy.admin.SchainError('No more files to read')
            return 0

        self.flagIsNewFile = 1
        print("Setting the file: %s"%self.filename)

        return 1


    def __setNextFileOnline(self):
        filename = self.filenameList[0]
        if self.__filename_online != None:
            self.__selectDataForTimes(online=True)
            filename = self.filenameList[0]
            wait = 0
            self.__waitForNewFile=300 ## DEBUG:
            while self.__filename_online == filename:
                print('waiting %d seconds to get a new file...'%(self.__waitForNewFile))
                if wait == 5:
                    self.flagNoMoreFiles = 1
                    return 0
                sleep(self.__waitForNewFile)
                self.__selectDataForTimes(online=True)
                filename = self.filenameList[0]
                wait += 1

        self.__filename_online = filename

        self.amisrFilePointer = h5py.File(filename,'r')
        self.flagIsNewFile = 1
        self.filename = filename
        print("Setting the file: %s"%self.filename)
        return 1


    def readData(self):
        buffer = self.amisrFilePointer.get('Raw11/Data/Samples/Data')
        re = buffer[:,:,:,0]
        im = buffer[:,:,:,1]
        dataset = re + im*1j

        self.radacTime = self.amisrFilePointer.get('Raw11/Data/RadacHeader/RadacTime')
        timeset = self.radacTime[:,0]

        return dataset,timeset

    def reshapeData(self):
        #print(self.beamCodeByPulse, self.beamCode, self.nblocks, self.nprofiles, self.nsa)
        channels = self.beamCodeByPulse[0,:]
        nchan = self.nchannels
        #self.newProfiles = self.nprofiles/nchan #must be defined on filljroheader
        nblocks = self.nblocks
        nsamples = self.nsa
        #print("Channels: ",self.nChannels)
        #Dimensions : nChannels, nProfiles, nSamples
        new_block = numpy.empty((nblocks, nchan, numpy.int_(self.newProfiles), nsamples), dtype="complex64")
        ############################################
        profPerCH = int(self.profPerBlockRAW / (self.nFFT* self.nChannels))
        #profPerCH = int(self.profPerBlockRAW /  self.nChannels)
        for thisChannel in range(nchan):

            ich = thisChannel

            idx_ch = [self.nFFT*(ich + nchan*k) for k in range(profPerCH)]
            #print(idx_ch)
            if self.nFFT > 1:
                aux = [numpy.arange(i, i+self.nFFT) for i in idx_ch]
                idx_ch  = None
                idx_ch =aux
                idx_ch = numpy.array(idx_ch, dtype=int).flatten()
            else:
                idx_ch = numpy.array(idx_ch, dtype=int)

            #print(ich,profPerCH,idx_ch)
            #print(numpy.where(channels==self.beamCode[ich])[0])
            #new_block[:,ich,:,:] = self.dataset[:,numpy.where(channels==self.beamCode[ich])[0],:]
            new_block[:,ich,:,:] = self.dataset[:,idx_ch,:]

        new_block = numpy.transpose(new_block, (1,0,2,3))
        new_block = numpy.reshape(new_block, (nchan,-1, nsamples))
        if  self.flagAsync:
            new_block = numpy.roll(new_block,  self.shiftChannels, axis=0)
        return new_block

    def updateIndexes(self):

        pass

    def fillJROHeader(self):

        #fill radar controller header

        #fill system header
        self.dataOut.systemHeaderObj = SystemHeader(nSamples=self.__nSamples,
                                                    nProfiles=self.newProfiles,
                                                    nChannels=len(self.__channelList),
                                                    adcResolution=14,
                                                    pciDioBusWidth=32)

        self.dataOut.type = "Voltage"
        self.dataOut.data = None
        self.dataOut.dtype = numpy.dtype([('real','<i8'),('imag','<i8')])
#        self.dataOut.nChannels = 0

#        self.dataOut.nHeights = 0

        self.dataOut.nProfiles = self.newProfiles*self.nblocks
        #self.dataOut.heightList = self.__firstHeigth + numpy.arange(self.__nSamples, dtype = numpy.float)*self.__deltaHeigth
        ranges = numpy.reshape(self.rangeFromFile[()],(-1))
        self.dataOut.heightList =  ranges/1000.0 #km
        self.dataOut.channelList = self.__channelList

        self.dataOut.blocksize = self.dataOut.nChannels * self.dataOut.nHeights

#        self.dataOut.channelIndexList = None


        # #self.dataOut.azimuthList = numpy.roll( numpy.array(self.azimuthList) ,self.shiftChannels)
        # #self.dataOut.elevationList = numpy.roll(numpy.array(self.elevationList) ,self.shiftChannels)
        # #self.dataOut.codeList = numpy.roll(numpy.array(self.beamCode), self.shiftChannels)
        
        self.dataOut.azimuthList = self.azimuthList 
        self.dataOut.elevationList = self.elevationList
        self.dataOut.codeList = self.beamCode



        #print(self.dataOut.elevationList)
        self.dataOut.flagNoData = True

        #Set to TRUE if the data is discontinuous
        self.dataOut.flagDiscontinuousBlock = False

        self.dataOut.utctime = None

        #self.dataOut.timeZone = -5 #self.__timezone/60  #timezone like jroheader, difference in minutes between UTC and localtime
        if self.timezone == 'lt':
            self.dataOut.timeZone = time.timezone / 60. #get the timezone in minutes
        else:
            self.dataOut.timeZone = 0 #by default time is UTC
  
        self.dataOut.dstFlag = 0
        self.dataOut.errorCount = 0
        self.dataOut.nCohInt = 1
        self.dataOut.flagDecodeData = False #asumo que la data esta decodificada
        self.dataOut.flagDeflipData = False #asumo que la data esta sin flip
        self.dataOut.flagShiftFFT = False
        self.dataOut.ippSeconds = self.ippSeconds
        self.dataOut.ipp = self.__ippKm
        self.dataOut.nCode = self.__nCode
        self.dataOut.code = self.__code
        self.dataOut.nBaud = self.__nBaud


        self.dataOut.frequency = self.__frequency
        self.dataOut.realtime = self.online

        self.dataOut.radarControllerHeaderObj = RadarControllerHeader(ipp=self.__ippKm,
                                                                      txA=self.__txAKm,
                                                                      txB=0,
                                                                      nWindows=1,
                                                                      nHeights=self.__nSamples,
                                                                      firstHeight=self.__firstHeight,
                                                                      codeType=self.__codeType,
                                                                      nCode=self.__nCode, nBaud=self.__nBaud,
                                                                      code = self.__code,
                                                                      nOsamp=self.nOsamp,
                                                                      frequency = self.__frequency,
                                                                      sampleRate= self.__sampleRate,
                                                                      fClock=self.__sampleRate)


        self.dataOut.radarControllerHeaderObj.heightList = ranges/1000.0 #km
        self.dataOut.radarControllerHeaderObj.heightResolution = self.__deltaHeight
        self.dataOut.radarControllerHeaderObj.rangeIpp = self.__ippKm   #km
        self.dataOut.radarControllerHeaderObj.rangeTxA = self.__txA*1e6*.15 #km
        self.dataOut.radarControllerHeaderObj.nChannels = self.nchannels
        self.dataOut.radarControllerHeaderObj.channelList = self.__channelList
        self.dataOut.radarControllerHeaderObj.azimuthList = self.azimuthList
        self.dataOut.radarControllerHeaderObj.elevationList = self.elevationList
        self.dataOut.radarControllerHeaderObj.dtype = "Voltage"
        self.dataOut.ippSeconds = self.ippSeconds
        self.dataOut.ippFactor = self.nFFT
        pass

    def readNextFile(self,online=False):

        if not(online):
            newFile = self.__setNextFileOffline()
        else:
            newFile = self.__setNextFileOnline()

        if not(newFile):
            self.dataOut.error = True
            return 0

        if not self.readAMISRHeader(self.amisrFilePointer):
            self.dataOut.error = True
            return 0

        #self.createBuffers()
        self.fillJROHeader()

        #self.__firstFile = False

        self.dataset,self.timeset = self.readData()
        if self.endDate!=None:
            endDateTime_Reader = datetime.datetime.combine(self.endDate,self.endTime)
            time_str = self.amisrFilePointer.get('Time/RadacTimeString')
            startDateTimeStr_File = time_str[0][0].decode('UTF-8').split('.')[0]
            junk = time.strptime(startDateTimeStr_File, '%Y-%m-%d %H:%M:%S')
            startDateTime_File = datetime.datetime(junk.tm_year,junk.tm_mon,junk.tm_mday,junk.tm_hour, junk.tm_min, junk.tm_sec)
            if self.timezone == 'lt':
                startDateTime_File = startDateTime_File - datetime.timedelta(minutes = 300)
            if (startDateTime_File>endDateTime_Reader):
                self.flag_standby = False
                return 0
            if self.flag_ignoreFiles and (startDateTime_File >= self.ignStartDateTime and startDateTime_File <= self.ignEndDateTime):
                print("Ignoring...")
                self.flag_standby = True
                self.profileIndex = 99999999999999999
                return 1
            self.flag_standby = False

        self.jrodataset = self.reshapeData()
        #----self.updateIndexes()
        self.profileIndex = 0

        return 1


    def __hasNotDataInBuffer(self):
        if self.profileIndex >= (self.newProfiles*self.nblocks):
            return 1
        return 0


    def getData(self):

        if self.flagNoMoreFiles:
            self.dataOut.flagNoData = True
            return 0
        if self.profileIndex >= (self.newProfiles*self.nblocks): #
        #if self.__hasNotDataInBuffer():
            if not (self.readNextFile(self.online)):
                print("Profile Index break...")
                return 0

        if self.flag_standby: #Standby mode, if files are being ignoring, just return with no error flag
            return 0
        
        if self.dataset is None: # setear esta condicion cuando no hayan datos por leer
            self.dataOut.flagNoData = True
            print("No more data break...")
            return 0

        #self.dataOut.data = numpy.reshape(self.jrodataset[self.profileIndex,:],(1,-1))

        self.dataOut.data = self.jrodataset[:,self.profileIndex,:]

        #print("R_t",self.timeset)

        #self.dataOut.utctime = self.jrotimeset[self.profileIndex]
        #verificar basic header de jro data y ver si es compatible con este valor
        #self.dataOut.utctime = self.timeset + (self.profileIndex * self.ippSeconds * self.nchannels)
        indexprof = numpy.mod(self.profileIndex, self.newProfiles)
        indexblock = self.profileIndex/self.newProfiles
        #print (indexblock, indexprof)
        diffUTC = 0
        t_comp = (indexprof * self.ippSeconds * self.nchannels) + diffUTC #

        #print("utc :",indexblock," __ ",t_comp)
        #print(numpy.shape(self.timeset))
        self.dataOut.utctime = self.timeset[numpy.int_(indexblock)] + t_comp
        #self.dataOut.utctime = self.timeset[self.profileIndex] + t_comp

        self.dataOut.profileIndex = self.profileIndex
        #print("N profile:",self.profileIndex,self.newProfiles,self.nblocks,self.dataOut.utctime)
        self.dataOut.flagNoData = False
        # if indexprof == 0:
        #     print("kamisr: ",self.dataOut.utctime)

        self.profileIndex += 1
        
        return self.dataOut.data #retorno necesario??


    def run(self, **kwargs):
        '''
        This method will be called many times so here you should put all your code
        '''
        #print("running kamisr")
        if not self.isConfig:
            self.setup(**kwargs)
            self.isConfig = True

        self.getData()
