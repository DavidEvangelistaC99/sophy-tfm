import os
import time
import datetime

import numpy
import h5py

import schainpy.admin
from schainpy.model.data.jrodata import *
from schainpy.model.proc.jroproc_base import ProcessingUnit, Operation, MPDecorator
from schainpy.model.io.jroIO_base import *
from schainpy.utils import log


class HDFReader(Reader, ProcessingUnit):
    """Processing unit to read HDF5 format files

    This unit reads HDF5 files created with `HDFWriter` operation contains
    by default two groups Data and Metadata all variables would be saved as `dataOut`
    attributes.
    It is possible to read any HDF5 file by given the structure in the `description`
    parameter, also you can add extra values to metadata with the parameter `extras`.

    Parameters:
    -----------
    path : str
        Path where files are located.
    startDate : date
        Start date of the files
    endDate : list
        End date of the files
    startTime : time
        Start time of the files
    endTime : time
        End time of the files
    description : dict, optional
        Dictionary with the description of the HDF5 file
    extras : dict, optional
        Dictionary with extra metadata to be be added to `dataOut`

    Examples
    --------

    desc = {
        'Data': {
            'data_output': ['u', 'v', 'w'],
            'utctime': 'timestamps',
        }  ,
        'Metadata': {
            'heightList': 'heights'
        }
    }

    desc = {
        'Data': {
            'data_output': 'winds',
            'utctime': 'timestamps'
        },
        'Metadata': {
            'heightList': 'heights'
        }
    }

    extras = {
        'timeZone': 300
    }

    reader = project.addReadUnit(
        name='HDFReader',
        path='/path/to/files',
        startDate='2019/01/01',
        endDate='2019/01/31',
        startTime='00:00:00',
        endTime='23:59:59',
        utcoffset='-18000'
        # description=json.dumps(desc),
        # extras=json.dumps(extras),
        )

    """

    __attrs__ = ['path', 'startDate', 'endDate', 'startTime', 'endTime', 'description', 'extras']

    def __init__(self):
        ProcessingUnit.__init__(self)
        self.dataOut = Parameters()
        self.ext = ".hdf5"
        self.optchar = "D"
        self.meta = {}
        self.data = {}
        self.open_file = h5py.File
        self.open_mode = 'r'
        self.description = {}
        self.extras = {}
        self.filefmt = "*%Y%j***"
        self.folderfmt = "*%Y%j"
        self.utcoffset = 0
        self.filter = None
        self.dparam = None


        ## Cambios AMISR
        self.flagUpdateDataOut = False
        self.dataOut = Parameters()
        self.dataOut.error=False            ## NOTE: Importante definir esto antes inicio
        self.dataOut.flagNoData = True


    def setup(self, **kwargs):

        self.set_kwargs(**kwargs)
        if not self.ext.startswith('.'):
            self.ext = '.{}'.format(self.ext)

        if self.online:
            log.log("Searching files in online mode...", self.name)

            for nTries in range(self.nTries):
                fullpath = self.searchFilesOnLine(self.path, self.startDate,
                    self.endDate, self.expLabel, self.ext, self.walk,
                    self.filefmt, self.folderfmt,self.filter)
                pathname, filename = os.path.split(fullpath)
                try:
                    fullpath = next(fullpath)
                except:
                    fullpath = None

                if fullpath:
                    break

                log.warning(
                    'Waiting {} sec for a valid file in {}: try {} ...'.format(
                        self.delay, self.path, nTries + 1),
                    self.name)
                time.sleep(self.delay)

            if not(fullpath):
                raise schainpy.admin.SchainError(
                    'There isn\'t any valid file in {}'.format(self.path))

            pathname, filename = os.path.split(fullpath)
            self.year = int(filename[1:5])
            self.doy = int(filename[5:8])
            self.set = int(filename[8:11]) - 1
        else:
            log.log("Searching files in {}".format(self.path), self.name)
            self.filenameList = self.searchFilesOffLine(self.path, self.startDate,
                self.endDate, self.expLabel, self.ext, self.walk, self.filefmt, self.folderfmt,self.filter)

        self.setNextFile()

        return

    def readFirstHeader(self):
        '''Read metadata and data'''

        self.__readMetadata()
        self.__readData()
        self.__setBlockList()     
        # similar to master
        if 'type' in self.meta:
            self.dataOut = eval(self.meta['type'])()
        if self.dparam:
            setattr(self.dataOut, "dparam", 1)  
        # similar to master
        for attr in self.meta:
            if "processingHeaderObj" in attr:
                self.flagUpdateDataOut=True
            at = attr.split('.')

            if len(at) > 1:
                setattr(eval("self.dataOut."+at[0]),at[1], self.meta[attr])
            else:
                setattr(self.dataOut, attr, self.meta[attr])

        self.blockIndex = 0

        if self.flagUpdateDataOut:
            self.updateDataOut()

        return
    
    def updateDataOut(self):
        
        self.dataOut.azimuthList = self.dataOut.processingHeaderObj.azimuthList
        self.dataOut.elevationList = self.dataOut.processingHeaderObj.elevationList
        self.dataOut.heightList = self.dataOut.processingHeaderObj.heightList
        self.dataOut.ippSeconds = self.dataOut.processingHeaderObj.ipp
        self.dataOut.elevationList = self.dataOut.processingHeaderObj.elevationList
        self.dataOut.channelList = self.dataOut.processingHeaderObj.channelList
        self.dataOut.nCohInt = self.dataOut.processingHeaderObj.nCohInt
        self.dataOut.nFFTPoints = self.dataOut.processingHeaderObj.nFFTPoints
        self.flagUpdateDataOut = False
        self.dataOut.frequency = self.dataOut.radarControllerHeaderObj.frequency
        #self.dataOut.heightList = self.dataOut.processingHeaderObj.heightList


    def __setBlockList(self):
        '''
        Selects the data within the times defined

        self.fp
        self.startTime
        self.endTime
        self.blockList
        self.blocksPerFile

        '''

        startTime = self.startTime
        endTime = self.endTime
        thisUtcTime = self.data['utctime'] + self.utcoffset
        try:
            self.interval = numpy.min(thisUtcTime[1:] - thisUtcTime[:-1])
        except:
            self.interval = 0
        
        thisDatetime = datetime.datetime.utcfromtimestamp(thisUtcTime[0])
        self.startFileDatetime = thisDatetime
        thisDate = thisDatetime.date()
        thisTime = thisDatetime.time()

        startUtcTime = (datetime.datetime.combine(thisDate, startTime) - datetime.datetime(1970, 1, 1)).total_seconds()
        endUtcTime = (datetime.datetime.combine(thisDate, endTime) - datetime.datetime(1970, 1, 1)).total_seconds()

        ind = numpy.where(numpy.logical_and(thisUtcTime >= startUtcTime, thisUtcTime < endUtcTime))[0]

        self.blockList = ind
        self.blocksPerFile = len(ind)
        # similar to master
        if len(ind)==0:
            print("[Reading] Block No. %d/%d -> %s [Skipping]" % (self.blockIndex,
                                                                      self.blocksPerFile,
                                                                      thisDatetime))
            self.setNextFile()
        # similar to master
        return

    def __readMetadata(self):
        '''
        Reads Metadata
        '''

        meta = {}

        if self.description:
            for key, value in self.description['Metadata'].items():
                meta[key] = self.fp[value][()]
        else:
            grp = self.fp['Metadata']
            for name in grp:
                meta[name] = grp[name][()]

        if self.extras:
            for key, value in self.extras.items():
                meta[key] = value
        self.meta = meta

        return
    
    def __readMetadata2(self):
        '''
        Reads Metadata
        '''
        meta = {}
        
        if self.description:
            for key, value in self.description['Metadata'].items():
                meta[key] = self.fp[value][()]
        else:
            grp = self.fp['Metadata']
            for item in grp.values():
                name = item.name
                if isinstance(item, h5py.Dataset):
                    name = name.split("/")[-1]
                    meta[name] = item[()]
                else:
                    grp2 = self.fp[name]
                    Obj = name.split("/")[-1]

                    for item2 in grp2.values():
                        name2 = Obj+"."+item2.name.split("/")[-1]
                        meta[name2] = item2[()]

        if self.extras:
            for key, value in self.extras.items():
                meta[key] = value
        self.meta = meta

        return

    def __readData(self):

        data = {}

        if self.description:
            for key, value in self.description['Data'].items():
                if isinstance(value, str):
                    if isinstance(self.fp[value], h5py.Dataset):
                        data[key] = self.fp[value][()]
                    elif isinstance(self.fp[value], h5py.Group):
                        array = []
                        for ch in self.fp[value]:
                            array.append(self.fp[value][ch][()])
                        data[key] = numpy.array(array)
                elif isinstance(value, list):
                    array = []
                    for ch in value:
                        array.append(self.fp[ch][()])
                    data[key] = numpy.array(array)
        else:
            grp = self.fp['Data']
            for name in grp:
                if isinstance(grp[name], h5py.Dataset):
                    array = grp[name][()]
                elif isinstance(grp[name], h5py.Group):
                    array = []
                    for ch in grp[name]:
                        array.append(grp[name][ch][()])
                    array = numpy.array(array)
                else:
                    log.warning('Unknown type: {}'.format(name))

                if name in self.description:
                    key = self.description[name]
                else:
                    key = name
                data[key] = array

        self.data = data
        return

    def getData(self):
        if not self.isDateTimeInRange(self.startFileDatetime, self.startDate, self.endDate, self.startTime, self.endTime):
            self.dataOut.flagNoData = True
            self.blockIndex = self.blocksPerFile
            self.dataOut.error = True     # TERMINA EL PROGRAMA
            return
        for attr in self.data:
            if self.data[attr].ndim == 1:
                setattr(self.dataOut, attr, self.data[attr][self.blockIndex])
            else:
                if self.dparam:
                    setattr(self.dataOut, attr, self.data[attr])
                else:
                    setattr(self.dataOut, attr, self.data[attr][:, self.blockIndex])

        self.dataOut.flagNoData = False
        self.blockIndex += 1

        if self.blockIndex == 1:

            log.log("Block No. {}/{} -> {}".format(
                self.blockIndex,
                self.blocksPerFile,
                self.dataOut.datatime.ctime()), self.name)
        else:
            log.log("Block No. {}/{} ".format(
                self.blockIndex,
                self.blocksPerFile),self.name)

        if self.blockIndex == self.blocksPerFile:
            self.setNextFile()

        self.dataOut.flagNoData = False

        return

    def run(self, **kwargs):

        if not(self.isConfig):
            self.setup(**kwargs)
            self.isConfig = True

        if self.blockIndex == self.blocksPerFile:
            self.setNextFile()

        self.getData()
        ''' # this block is missing in master.        
        if 'type' in self.meta:
            self.dataOut.type = self.meta['type'].decode('utf-8')
        '''
        return

@MPDecorator
class HDFWriter(Operation):
    """Operation to write HDF5 files.

    The HDF5 file contains by default two groups Data and Metadata where
    you can save any `dataOut` attribute specified by `dataList` and `metadataList`
    parameters, data attributes are normaly time dependent where the metadata
    are not.
    It is possible to customize the structure of the HDF5 file with the
    optional description parameter see the examples.

    Parameters:
    -----------
    path : str
        Path where files will be saved.
    blocksPerFile : int
        Number of blocks per file
    metadataList : list
        List of the dataOut attributes that will be saved as metadata
    dataList : int
        List of the dataOut attributes that will be saved as data
    setType : bool
        If True the name of the files corresponds to the timestamp of the data
    description : dict, optional
        Dictionary with the desired description of the HDF5 file

    Examples
    --------

    desc = {
        'data_output': {'winds': ['z', 'w', 'v']},
        'utctime': 'timestamps',
        'heightList': 'heights'
    }
    desc = {
        'data_output': ['z', 'w', 'v'],
        'utctime': 'timestamps',
        'heightList': 'heights'
    }
    desc = {
        'Data': {
            'data_output': 'winds',
            'utctime': 'timestamps'
        },
        'Metadata': {
            'heightList': 'heights'
        }
    }

    writer = proc_unit.addOperation(name='HDFWriter')
    writer.addParameter(name='path', value='/path/to/file')
    writer.addParameter(name='blocksPerFile', value='32')
    writer.addParameter(name='metadataList', value='heightList,timeZone')
    writer.addParameter(name='dataList',value='data_output,utctime')
    # writer.addParameter(name='description',value=json.dumps(desc))

    """

    ext = ".hdf5"
    optchar = "D"
    filename = None
    path = None
    setFile = None
    fp = None
    ds = None
    firsttime = True
    # Configurations
    blocksPerFile = None
    blockIndex = None
    dataOut = None
    # Data Arrays
    dataList = None
    metadataList = None
    currentDay = None
    lastTime = None
    last_Azipos  = None
    last_Elepos  = None
    mode         = None
    #-----------------------
    Typename   = None
    mask       = False
    setChannel = None

    ## amisr
    timeZone = "ut"
    hourLimit = 3
    breakDays = True

    def __init__(self):

        Operation.__init__(self)
        return

    def set_kwargs(self, **kwargs):

        for key, value in kwargs.items():
            setattr(self, key, value)

    def set_kwargs_obj(self, obj, **kwargs):

        for key, value in kwargs.items():
            setattr(obj, key, value)

    def setup(self, path=None, blocksPerFile=10, metadataList=None, dataList=None, setType=None, description=None,timeZone = "ut",hourLimit = 3, breakDays=True,type_data=None, localtime=True,setChannel=None, **kwargs):
        self.path = path
        self.blocksPerFile = blocksPerFile
        self.metadataList = metadataList
        self.dataList = [s.strip() for s in dataList]
        self.setChannel    = setChannel
        self.setType = setType
        if self.setType == "weather":
            self.set_kwargs(**kwargs)
            self.set_kwargs_obj(self.dataOut,**kwargs)
            self.weather_vars = {
                'S' : 0,
                'V' : 1,
                'W' : 2,
                'SNR' : 3,
                'Z' : 4,
                'D' : 5,
                'P' : 6,
                'R' : 7,
            }

        if localtime:
            self.getDateTime = datetime.datetime.fromtimestamp
        else:
            self.getDateTime = datetime.datetime.utcfromtimestamp
        self.description = description
        self.type_data=type_data
        self.timeZone = timeZone
        self.hourLimit = hourLimit
        self.breakDays = breakDays
        self.set_kwargs(**kwargs)        

        if self.metadataList is None:
            self.metadataList = self.dataOut.metadata_list

        self.metadataList = list(set(self.metadataList))
        tableList = []
        dsList = []

        for i in range(len(self.dataList)):
            dsDict = {}
            if hasattr(self.dataOut, self.dataList[i]):
                dataAux = getattr(self.dataOut, self.dataList[i])
                if self.setType == 'weather' and self.dataList[i] == 'data_param':
                    if self.setChannel is None: 
                        dataAux = dataAux[self.weather_vars[self.weather_var]]
                    else:
                        dataAux = dataAux[self.setChannel,self.weather_vars[self.weather_var],:]
                        dataAux = numpy.reshape(dataAux,(1,dataAux.shape[0],dataAux.shape[1]))
                dsDict['variable'] = self.dataList[i]
            else:
                log.warning('Attribute {} not found in dataOut', self.name)
                continue

            if dataAux is None:
                continue
            elif isinstance(dataAux, (int, float, numpy.integer, numpy.float32)):
                dsDict['nDim'] = 0
            else:
                pass
                #if self.uniqueChannel: #Creates extra dimension to avoid the creation of multiple channels
                #    dataAux = numpy.expand_dims(dataAux, axis=0)
                dsDict['nDim'] = len(dataAux.shape)
                dsDict['shape'] = dataAux.shape
                dsDict['dsNumber'] = dataAux.shape[0]
                dsDict['dtype'] = dataAux.dtype

            dsList.append(dsDict)

        self.blockIndex = 0
        self.dsList = dsList
        self.currentDay = self.dataOut.datatime.date()

    def timeFlag(self):
        currentTime = self.dataOut.utctime
        timeTuple = None
        if self.timeZone == "lt":
            timeTuple = time.localtime(currentTime)
        else :
            timeTuple = time.gmtime(currentTime)
        dataDay = timeTuple.tm_yday

        if self.lastTime is None:
            self.lastTime = currentTime
            self.currentDay = dataDay
            return False

        timeDiff = currentTime - self.lastTime

        # Si el dia es diferente o si la diferencia entre un dato y otro supera la hora
        if (dataDay != self.currentDay) and self.breakDays:
            self.currentDay = dataDay
            return True
        elif timeDiff > 3 * 60 * 60:
            self.lastTime = currentTime
            return True
        else:
            self.lastTime = currentTime
            return False

    def run(self, dataOut, path, blocksPerFile=10, metadataList=None,
            dataList=[], setType=None, description={}, mode= None, 
            type_data=None, Reset = False, localtime=True, **kwargs):

        if Reset:
            self.isConfig = False
            self.closeFile()
            self.lastTime = None
            self.blockIndex = 0
        
        self.dataOut = dataOut
        self.mode = mode
        self.set_kwargs_obj(self.dataOut, **kwargs)
        if not(self.isConfig):
            self.setup(path=path, blocksPerFile=blocksPerFile,
                       metadataList=metadataList, dataList=dataList,
                       setType=setType, description=description,type_data=type_data,
                       localtime=localtime, **kwargs)

            self.isConfig = True
            self.setNextFile()

        self.putData()
        return

    def setNextFile(self):

        ext = self.ext
        path = self.path
        setFile = self.setFile
        timeTuple = None

        dt = self.getDateTime(self.dataOut.utctime)

        if self.timeZone == "lt":
            timeTuple = time.localtime(self.dataOut.utctime)
        elif self.timeZone == "ut":
            timeTuple = time.gmtime(self.dataOut.utctime)
        subfolder = 'd%4.4d%3.3d' % (timeTuple.tm_year, timeTuple.tm_yday)

        if self.setType == 'weather':
            subfolder = dt.strftime('%Y-%m-%dT%H-00-00')
            subfolder = ''
        else: 
            subfolder = dt.strftime('d%Y%j')
        
        fullpath = os.path.join(path, subfolder)

        if os.path.exists(fullpath):
            filesList = os.listdir(fullpath)
            filesList = [k for k in filesList if k.startswith(self.optchar)]
            if len(filesList) > 0:
                filesList = sorted(filesList, key=str.lower)
                filen = filesList[-1]
                # el filename debera tener el siguiente formato
                # 0 1234 567 89A BCDE (hex)
                # x YYYY DDD SSS .ext
                if isNumber(filen[8:11]):
                    setFile = int(filen[8:11])  # inicializo mi contador de seteo al seteo del ultimo file
                else:
                    setFile = -1
            else:
                setFile = -1  # inicializo mi contador de seteo
        else:
            os.makedirs(fullpath)
            setFile = -1  # inicializo mi contador de seteo

        if self.setType is None:
            setFile += 1
            file = '%s%4.4d%3.3d%03d%s' % (self.optchar,
                                           timeTuple.tm_year,
                                           timeTuple.tm_yday,
                                           setFile,
                                           ext)
        elif self.setType == "weather":

            #SOPHY_20200505_140215_E10.0_Z.h5
            #SOPHY_20200505_140215_A40.0_Z.h5
            if self.dataOut.flagMode == 1: #'AZI' #PPI
                ang_type = 'EL'
                mode_type = 'PPI'
                len_aux = int(self.dataOut.data_ele.shape[0]/4)
                mean = numpy.mean(self.dataOut.data_ele[len_aux:-len_aux])
                ang_    = round(mean,1)
            elif self.dataOut.flagMode == 0: #'ELE' #RHI
                ang_type = 'AZ'
                mode_type = 'RHI'
                len_aux = int(self.dataOut.data_azi.shape[0]/4)
                mean = numpy.mean(self.dataOut.data_azi[len_aux:-len_aux])
                ang_    = round(mean,1)

            file = '%s_%2.2d%2.2d%2.2d_%2.2d%2.2d%2.2d_%s%2.1f_%s%s' % (
                'SOPHY',
                                           dt.year,
                                           dt.month,
                                           dt.day,
                                           dt.hour,
                                           dt.minute,
                                           dt.second,
                                           ang_type[0],
                                           ang_,
                                           self.weather_var,
                                           ext )
            subfolder = '{}_{}_{}_{:2.1f}'.format(self.weather_var, mode_type, ang_type, ang_)
            fullpath = os.path.join(path, subfolder)
            if not os.path.exists(fullpath):
                os.makedirs(fullpath)
        else:
            setFile = timeTuple.tm_hour * 60 + timeTuple.tm_min
            file = '%s%4.4d%3.3d%04d%s' % (self.optchar,
                                           timeTuple.tm_year,
                                           timeTuple.tm_yday,
                                           setFile,
                                           ext)

        self.filename = os.path.join(path, subfolder, file)

        # Setting HDF5 File
        self.fp = h5py.File(self.filename, 'w')
        # write metadata
        self.writeMetadata(self.fp)
        # Write data
        self.writeData(self.fp)

    def getLabel(self, name, x=None):

        if x is None:
            if 'Data' in self.description:
                data = self.description['Data']
                if 'Metadata' in self.description:
                    data.update(self.description['Metadata'])
            else:
                data = self.description
            if name in data:
                if isinstance(data[name], str):
                    return data[name]
                elif isinstance(data[name], list):
                    return None
                elif isinstance(data[name], dict):
                    for key, value in data[name].items():
                        return key
            return name
        else:
            if 'Data' in self.description:
                data = self.description['Data']
                if 'Metadata' in self.description:
                    data.update(self.description['Metadata'])
            else:
                data = self.description
            if name in data:
                if isinstance(data[name], list):
                    return data[name][x]
                elif isinstance(data[name], dict):
                    for key, value in data[name].items():
                        return value[x]
            if 'cspc' in name:
                return 'pair{:02d}'.format(x)
            else:
                return 'channel{:02d}'.format(x)

    def writeMetadata(self, fp):
        
        if self.description:
            if 'Metadata' in self.description:
                grp = fp.create_group('Metadata')
            else:
                grp = fp
        else:
            grp = fp.create_group('Metadata')

        for i in range(len(self.metadataList)):
            if not hasattr(self.dataOut, self.metadataList[i]):
                log.warning('Metadata: `{}` not found'.format(self.metadataList[i]), self.name)
                continue
            value = getattr(self.dataOut, self.metadataList[i])
            if isinstance(value, bool):
                if value is True:
                    value = 1
                else:
                    value = 0
            grp.create_dataset(self.getLabel(self.metadataList[i]), data=value)
        return
    
    def writeMetadata2(self, fp):

        if self.description:
            if 'Metadata' in self.description:
                grp = fp.create_group('Metadata')
            else:
                grp = fp
        else:
            grp = fp.create_group('Metadata')

        for i in range(len(self.metadataList)):

            attribute = self.metadataList[i]
            attr = attribute.split('.')
            if len(attr) > 1:
                if not hasattr(eval("self.dataOut."+attr[0]),attr[1]):
                    log.warning('Metadata: {}.{} not found'.format(attr[0],attr[1]), self.name)
                    continue
                value = getattr(eval("self.dataOut."+attr[0]),attr[1])
                if isinstance(value, bool):
                    if value is True:
                        value = 1
                    else:
                        value = 0
                if isinstance(value,type(None)):
                    log.warning("Invalid value detected, {} is None".format(attribute), self.name)
                    value = 0
                grp2 = None
                if not 'Metadata/'+attr[0] in fp:
                    grp2 = fp.create_group('Metadata/'+attr[0])
                else:
                    grp2 = fp['Metadata/'+attr[0]]
                grp2.create_dataset(attr[1], data=value)

            else:
                if not hasattr(self.dataOut, attr[0] ):
                    log.warning('Metadata: `{}` not found'.format(attribute), self.name)
                    continue
                value = getattr(self.dataOut, attr[0])
                if isinstance(value, bool):
                    if value is True:
                        value = 1
                    else:
                        value = 0
                if isinstance(value, type(None)):
                    log.error("Value {} is None".format(attribute),self.name)
                    
                grp.create_dataset(self.getLabel(attribute), data=value)

        return
    

    def writeData(self, fp):

        if self.description:
            if 'Data' in self.description:
                grp = fp.create_group('Data')
            else:
                grp = fp
        else:
            grp = fp.create_group('Data')

        dtsets = []
        data = []

        for dsInfo in self.dsList:
            if dsInfo['nDim'] == 0:
                ds = grp.create_dataset(
                    self.getLabel(dsInfo['variable']),
                    (self.blocksPerFile,),
                    chunks=True,
                    dtype=numpy.float64)
                dtsets.append(ds)
                data.append((dsInfo['variable'], -1))
            else:
                label = self.getLabel(dsInfo['variable'])
                if label is not None:
                    sgrp = grp.create_group(label)
                else:
                    sgrp = grp
                if self.blocksPerFile == 1:
                    shape = dsInfo['shape'][1:]
                else:
                    shape = (self.blocksPerFile, ) + dsInfo['shape'][1:]
                
                ## cambio para SOPHY, quitamos
                
                #if self.uniqueChannel: #Creates extra dimension to avoid the creation of multiple channels
                #    setattr(self.dataOut, dsInfo['variable'], numpy.expand_dims(getattr(self.dataOut, dsInfo['variable']), axis=0))
                for i in range(dsInfo['dsNumber']):
                    if dsInfo['dsNumber']==1:
                        if self.setChannel==1:
                            i=1
                    ds = sgrp.create_dataset(
                        self.getLabel(dsInfo['variable'], i),
                        (self.blocksPerFile,) + dsInfo['shape'][1:],
                        chunks=True,
                        dtype=dsInfo['dtype'],
                        compression='gzip',
                        )
                    dtsets.append(ds)
                    data.append((dsInfo['variable'], i))
        fp.flush()

        log.log('Creating file: {}'.format(fp.filename), self.name)

        self.ds = dtsets
        self.data = data
        self.firsttime = True
        self.blockIndex = 0
        return

    def putData(self):

        if (self.blockIndex == self.blocksPerFile) or self.timeFlag():
            self.closeFile()
            self.setNextFile()
            self.dataOut.flagNoData = False
            self.blockIndex = 0
            
        if self.blockIndex == 0:
            #Setting HDF5 File
            self.fp = h5py.File(self.filename, 'w')
            #write metadata
            self.writeMetadata2(self.fp)
            #Write data
            self.writeData(self.fp)
            log.log('Block No. {}/{} --> {}'.format(self.blockIndex+1, self.blocksPerFile,self.dataOut.datatime.ctime()), self.name)
        elif (self.blockIndex % 10 ==0):
            log.log('Block No. {}/{} --> {}'.format(self.blockIndex+1, self.blocksPerFile,self.dataOut.datatime.ctime()), self.name)
        else:

            log.log('Block No. {}/{}'.format(self.blockIndex+1, self.blocksPerFile), self.name)
            

        for i, ds in enumerate(self.ds):
            attr, ch = self.data[i]
            if ch == -1:
                ds[self.blockIndex] = getattr(self.dataOut, attr)
            else:
                #if self.uniqueChannel and self.blockIndex != 0: #Creates extra dimension to avoid the creation of multiple channels
                #    setattr(self.dataOut, attr, numpy.expand_dims(getattr(self.dataOut, attr), axis=0))
                if self.blocksPerFile == 1:
                    tmp = getattr(self.dataOut, attr)[self.weather_vars[self.weather_var]][ch]
                    if self.mask:
                        mask = self.dataOut.data_param[:,3,:][ch] < self.mask
                        tmp[mask] = numpy.nan
                    ds[:] = tmp
                else:
                    ds[self.blockIndex] = getattr(self.dataOut, attr)[ch]
                #if self.uniqueChannel: #Deletes extra dimension created to avoid the creation of multiple channels
                #    setattr(self.dataOut, attr, getattr(self.dataOut, attr)[0])

        self.fp.flush()
        self.blockIndex += 1
        log.log('Block No. {}/{}'.format(self.blockIndex, self.blocksPerFile), self.name)

        self.fp.flush()
        self.dataOut.flagNoData = True

        return

    def closeFile(self):

        if self.blockIndex != self.blocksPerFile:
            for ds in self.ds:
                ds.resize(self.blockIndex, axis=0)

        if self.fp:
            self.fp.flush()
            self.fp.close()

    def close(self):

        self.closeFile()


@MPDecorator
class ASCIIWriter(Operation):
    """Operation to write data in ascii files.

    Parameters:
    -----------
    path : str
        Path where files will be saved.
    blocksPerFile : int
        Number of blocks per file
    metadataList : list
        List of the dataOut attributes that will be saved as metadata
    dataDict : dict
        Dictionary with the varaibles to be saved
    setType : bool
        If True the name of the files corresponds to the timestamp of the data

    Examples
    --------

    data = {
        'data_output': ['z', 'w', 'v'],
        'utctime': 'time',
        'heightList': 'height'
    }

    writer = proc_unit.addOperation(name='ASCIIWriter')
    writer.addParameter(name='path', value='/path/to/file')
    writer.addParameter(name='blocksPerFile', value='32')
    writer.addParameter(name='dataDict',value=json.dumps(data))

    """

    ext = ".txt"
    optchar = "D"
    filename = None
    path = None
    setFile = None
    fp = None
    firsttime = True
    # Configurations
    blocksPerFile = None
    blockIndex = None
    dataOut = None
    # Data Arrays
    dataDict = None
    metadataList = None
    currentDay = None
    lastTime = None
    localtime = True

    def __init__(self):

        Operation.__init__(self)
        return

    def setup(self, path=None, blocksPerFile=10, metadataList=None, dataDict=None, setType=None, localtime=True):
        self.path = path
        self.blocksPerFile = blocksPerFile
        self.metadataList = metadataList
        self.dataDict = dataDict
        self.setType = setType
        self.localtime = localtime

        if self.metadataList is None:
            self.metadataList = self.dataOut.metadata_list

        dsList = []

        for key, value in self.dataDict.items():
            dsDict = {}
            if hasattr(self.dataOut, key):
                dataAux = getattr(self.dataOut, key)
                dsDict['variable'] = key
            else:
                log.warning('Attribute {} not found in dataOut', self.name)
                continue

            if dataAux is None:
                continue
            elif isinstance(dataAux, (int, float, numpy.integer, numpy.float32)):
                dsDict['nDim'] = 0
            else:
                dsDict['nDim'] = len(dataAux.shape)
                dsDict['shape'] = dataAux.shape
                dsDict['dsNumber'] = dataAux.shape[0]
                dsDict['dtype'] = dataAux.dtype

            dsList.append(dsDict)
        self.dsList = dsList
        self.currentDay = self.dataOut.datatime.date()

    def timeFlag(self):
        currentTime = self.dataOut.utctime
        if self.localtime:
            timeTuple = time.localtime(currentTime)
        else:
            timeTuple = time.gmtime(currentTime)

        dataDay = timeTuple.tm_yday

        if self.lastTime is None:
            self.lastTime = currentTime
            self.currentDay = dataDay
            return False

        timeDiff = currentTime - self.lastTime

        # Si el dia es diferente o si la diferencia entre un dato y otro supera la hora
        if dataDay != self.currentDay:
            self.currentDay = dataDay
            return True
        elif timeDiff > 3 * 60 * 60:
            self.lastTime = currentTime
            return True
        else:
            self.lastTime = currentTime
            return False

    def run(self, dataOut, path, blocksPerFile=10, metadataList=None,
            dataDict={}, setType=None, localtime=True):

        self.dataOut = dataOut
        if not(self.isConfig):
            self.setup(path=path, blocksPerFile=blocksPerFile,
                       metadataList=metadataList, dataDict=dataDict,
                       setType=setType, localtime=localtime)

            self.isConfig = True
            self.setNextFile()

        self.putData()
        return

    def setNextFile(self):

        ext = self.ext
        path = self.path
        setFile = self.setFile
        if self.localtime:
            timeTuple = time.localtime(self.dataOut.utctime)
        else:
            timeTuple = time.gmtime(self.dataOut.utctime)
        subfolder = 'd%4.4d%3.3d' % (timeTuple.tm_year, timeTuple.tm_yday)
        fullpath = os.path.join(path, subfolder)

        if os.path.exists(fullpath):
            filesList = os.listdir(fullpath)
            filesList = [k for k in filesList if k.startswith(self.optchar)]
            if len(filesList) > 0:
                filesList = sorted(filesList, key=str.lower)
                filen = filesList[-1]
                # el filename debera tener el siguiente formato
                # 0 1234 567 89A BCDE (hex)
                # x YYYY DDD SSS .ext
                if isNumber(filen[8:11]):
                    setFile = int(filen[8:11])  # inicializo mi contador de seteo al seteo del ultimo file
                else:
                    setFile = -1
            else:
                setFile = -1  # inicializo mi contador de seteo
        else:
            os.makedirs(fullpath)
            setFile = -1  # inicializo mi contador de seteo

        if self.setType is None:
            setFile += 1
            file = '%s%4.4d%3.3d%03d%s' % (self.optchar,
                                           timeTuple.tm_year,
                                           timeTuple.tm_yday,
                                           setFile,
                                           ext)
        else:
            setFile = timeTuple.tm_hour * 60 + timeTuple.tm_min
            file = '%s%4.4d%3.3d%04d%s' % (self.optchar,
                                           timeTuple.tm_year,
                                           timeTuple.tm_yday,
                                           setFile,
                                           ext)

        self.filename = os.path.join(path, subfolder, file)

        # Setting HDF5 File
        self.fp = open(self.filename, 'w')
        # write metadata
        self.writeMetadata(self.fp)
        # Write data
        self.writeData(self.fp)

    def writeMetadata(self, fp):

        line = ''
        for d in self.dsList:
            par = self.dataDict[d['variable']]
            if isinstance(par, (list,tuple)):
                for p in par:
                    line += '{:>16}'.format(p)
            else:
                line += '{:>16}'.format(par)

        line += '\n'
        fp.write(line)

    def writeData(self, fp):

        log.log('Creating file: {}'.format(self.filename), self.name)

        self.firsttime = True
        self.blockIndex = 0
        return

    def putData(self):

        if (self.blockIndex == self.blocksPerFile) or self.timeFlag():
            self.closeFile()
            self.setNextFile()

        line = ''
        for j in range(len(self.dataOut.heightList)):
            for ds in self.dsList:
                par = self.dataDict[ds['variable']]
                if ds['nDim'] == 2:
                    for i in range(len(par)):
                        line += '{:>16}'.format('%8.2f' % getattr(self.dataOut, ds['variable'])[i][j])
                elif ds['nDim'] == 1:
                    line += '{:>16}'.format('%8.2f' % getattr(self.dataOut, ds['variable'])[j])
                else:
                    line += '{:>16}'.format('%8.2f' % getattr(self.dataOut, ds['variable']))

            line += '\n'
        self.fp.write(line)

        self.blockIndex += 1
        log.log('Block No. {}/{}'.format(self.blockIndex, self.blocksPerFile), self.name)

        return

    def closeFile(self):

        if self.fp:
            self.fp.close()

    def close(self):

        self.closeFile()
