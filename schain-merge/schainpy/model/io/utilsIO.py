"""
Utilities for IO modules
@modified: Joab Apaza
@email: roj-op01@igp.gob.pe, joab.apaza32@gmail.com
"""
################################################################################
################################################################################
import os
from datetime import datetime
import numpy
from schainpy.model.data.jrodata import Parameters
import itertools
import numpy
import h5py
import re
import time
from schainpy.utils import log
################################################################################
################################################################################
################################################################################
def folder_in_range(folder, start_date, end_date, pattern):
    """
    Check whether folder is bettwen start_date and end_date
    Args:
        folder (str): Folder to check
        start_date (date): Initial date
        end_date (date): Final date
        pattern (str): Datetime format of the folder
    Returns:
        bool: True for success, False otherwise
    """
    try:
        dt = datetime.strptime(folder, pattern)
    except:
        raise ValueError('Folder {} does not match {} format'.format(folder, pattern))
    return start_date <= dt.date() <= end_date
################################################################################
################################################################################
################################################################################
def getHei_index( minHei, maxHei, heightList):
    try:
        if (minHei < heightList[0]):
            minHei = heightList[0]
        if (maxHei > heightList[-1]):
            maxHei = heightList[-1]
        minIndex = 0
        maxIndex = 0
        heights = numpy.asarray(heightList)
        inda = numpy.where(heights >= minHei)
        indb = numpy.where(heights <= maxHei)
        try:
            minIndex = inda[0][0]
        except:
            minIndex = 0
        try:
            maxIndex = indb[0][-1]
        except:
            maxIndex = len(heightList)
        return minIndex,maxIndex
    except Exception as e:
        log.error("In getHei_index: ", __name__)
        log.error(e , __name__)
################################################################################
################################################################################
################################################################################
class MergeH5(object):
    """Processing unit to read HDF5 format files
    This unit reads HDF5 files created with `HDFWriter` operation when channels area
    processed by separated. Then merge all channels in a single files.
    "example"
    nChannels = 4
    pathOut = "/home/soporte/Data/OutTest/clean2D/perpAndObliq/byChannels/merged"
    p0 = "/home/soporte/Data/OutTest/clean2D/perpAndObliq/byChannels/d2022240_Ch0"
    p1 = "/home/soporte/Data/OutTest/clean2D/perpAndObliq/byChannels/d2022240_Ch1"
    p2 = "/home/soporte/Data/OutTest/clean2D/perpAndObliq/byChannels/d2022240_Ch2"
    p3 = "/home/soporte/Data/OutTest/clean2D/perpAndObliq/byChannels/d2022240_Ch3"
    list = ['data_spc','data_cspc','nIncohInt','utctime']
    merger = MergeH5(nChannels,pathOut,list, p0, p1,p2,p3)
    merger.run()
    The file example_FULLmultiprocessing_merge.txt show an application for AMISR data
    """
    # #__attrs__ = ['paths', 'nChannels']
    isConfig = False
    inPaths = None
    nChannels = None
    ch_dataIn = []
    channelList = []
    def __init__(self,nChannels, pOut, dataList, *args):
        self.inPaths = [p for p in args]
        #print(self.inPaths)
        if len(self.inPaths) != nChannels:
            print("ERROR, number of channels different from iput paths {} != {}".format(nChannels, len(args)))
            return
        self.pathOut = pOut
        self.dataList = dataList
        self.nChannels = len(self.inPaths)
        self.ch_dataIn = [Parameters() for p in args]
        self.dataOut = Parameters()
        self.channelList = [n for n in range(nChannels)]
        self.blocksPerFile = None
        self.date = None
        self.ext = ".hdf5$"
        self.dataList = dataList
        self.optchar = "D"
        self.meta = {}
        self.data = {}
        self.open_file = h5py.File
        self.open_mode = 'r'
        self.description = {}
        self.extras = {}
        self.filefmt = "*%Y%j***"
        self.folderfmt = "*%Y%j"
        self.flag_spc = False
        self.flag_pow = False
        self.flag_snr = False
        self.flag_nIcoh = False
        self.flagProcessingHeader = False
        self.flagControllerHeader = False
    def setup(self):
        # if not self.ext.startswith('.'):
        #     self.ext = '.{}'.format(self.ext)
        self.filenameList = self.searchFiles(self.inPaths, None)
        self.nfiles = len(self.filenameList[0])
    def searchFiles(self, paths, date, walk=True):
        # self.paths = path
        #self.date = startDate
        #self.walk = walk
        filenameList = [[] for n in range(self.nChannels)]
        ch = 0
        for path in paths:
            if os.path.exists(path):
                print("Searching files in {}".format(path))
                filenameList[ch] = self.getH5files(path, walk)
                print("Found: ")
                for f in filenameList[ch]:
                    print(f)
            else:
                self.status = 0
                print('Path:%s does not exists'%path)
                return 0
            ch+=1
        return filenameList
    def getH5files(self, path, walk):
        dirnameList = []
        pat = '(\d)+.'+self.ext
        if walk:
            for root, dirs, files in os.walk(path):
                for dir in dirs:
                    #print(os.path.join(root,dir))
                    files = [re.search(pat,x) for x in os.listdir(os.path.join(root,dir))]
                    #print(files)
                    files = [x for x in files if x!=None]
                    files = [x.string for x in files]
                    files = [os.path.join(root,dir,x) for x in files if x!=None]
                    files.sort()
                    dirnameList += files
            return dirnameList
        else:
            dirnameList = [re.search(pat,x) for x in os.listdir(path)]
            dirnameList = [x for x in dirnameList if x!=None]
            dirnameList = [x.string for x in dirnameList]
            dirnameList = [x for x in dirnameList if x!=None]
            dirnameList.sort()
        return dirnameList
    def readFile(self,fp,ch):
        '''Read metadata and data'''
        self.readMetadata(fp,ch)
        # print(self.metadataList)
        data = self.readData(fp)
        for attr in self.meta:
            if "processingHeaderObj" in attr:
                self.flagProcessingHeader=True
            if "radarControllerHeaderObj" in attr:
                self.flagControllerHeader=True
            at = attr.split('.')
            # print("AT ", at)
            if len(at) > 1:
                setattr(eval("self.ch_dataIn[ch]."+at[0]),at[1], self.meta[attr])
            else:
                setattr(self.ch_dataIn[ch], attr, self.meta[attr])
        self.fill_dataIn(data, self.ch_dataIn[ch])
        return
    def readMetadata(self, fp, ch):
        '''
        Reads Metadata
        '''
        meta = {}
        self.metadataList = []
        grp = fp['Metadata']
        for item in grp.values():
            name = item.name
            if isinstance(item, h5py.Dataset):
                name = name.split("/")[-1]
                if 'List' in name:
                    meta[name] = item[()].tolist()
                else:
                    meta[name] = item[()]
                self.metadataList.append(name)
            else:
                grp2 = fp[name]
                Obj = name.split("/")[-1]
                #print(Obj)
                for item2 in grp2.values():
                    name2 = Obj+"."+item2.name.split("/")[-1]
                    if 'List' in name2:
                        meta[name2] = item2[()].tolist()
                    else:
                        meta[name2] = item2[()]
                    self.metadataList.append(name2)
        if not self.meta:
            self.meta = meta.copy()
            for key in list(self.meta.keys()):
                if "channelList" in key:
                    self.meta["channelList"] =[n for n in range(self.nChannels)]
                if "processingHeaderObj" in key:
                    self.meta["processingHeaderObj.channelList"] =[n for n in range(self.nChannels)]
                if "radarControllerHeaderObj" in key:
                    self.meta["radarControllerHeaderObj.channelList"] =[n for n in range(self.nChannels)]
            return 1
        else:
            for k in list(self.meta.keys()):
                if 'List' in k and 'channel' not in k and "height" not in k and "radarControllerHeaderObj" not in k:
                    self.meta[k] += meta[k]
        #print("Metadata: ",self.meta)
        return 1
    def fill_dataIn(self,data, dataIn):
        for attr in data:
            if data[attr].ndim == 1:
                setattr(dataIn, attr, data[attr][:])
            else:
                setattr(dataIn, attr, numpy.squeeze(data[attr][:,:]))
        # print("shape in", dataIn.data_spc.shape, len(dataIn.data_spc))
        if self.flag_spc:
            if dataIn.data_spc.ndim > 3:
                dataIn.data_spc = dataIn.data_spc[0]
                #print("shape in", dataIn.data_spc.shape)
    def getBlocksPerFile(self):
        b = numpy.zeros(self.nChannels)
        for i in range(self.nChannels):
            if self.flag_spc:
                b[i] = self.ch_dataIn[i].data_spc.shape[0] #number of blocks
            elif self.flag_pow:
                b[i] = self.ch_dataIn[i].data_pow.shape[0] #number of blocks
            elif self.flag_snr:
                b[i] = self.ch_dataIn[i].data_snr.shape[0] #number of blocks
        self.blocksPerFile = int(b.min())
        iresh_ch = numpy.where(b > self.blocksPerFile)[0]
        if len(iresh_ch) > 0:
            for ich in iresh_ch:
                for i in range(len(self.dataList)):
                    if hasattr(self.ch_dataIn[ich], self.dataList[i]):
                        # print("reshaping ", self.dataList[i])
                        # print(getattr(self.ch_dataIn[ich], self.dataList[i]).shape)
                        dataAux = getattr(self.ch_dataIn[ich], self.dataList[i])
                        setattr(self.ch_dataIn[ich], self.dataList[i], None)
                        setattr(self.ch_dataIn[ich], self.dataList[i], dataAux[0:self.blocksPerFile])
                        # print(getattr(self.ch_dataIn[ich], self.dataList[i]).shape)
        else:
            # log.error("Channels number error,iresh_ch=", iresh_ch)
            return
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
            if 'Metadata' in self.description:
                meta = self.description['Metadata']
            else:
                meta = self.description
            if name in meta:
                if isinstance(meta[name], list):
                    return meta[name][x]
                elif isinstance(meta[name], dict):
                    for key, value in meta[name].items():
                        return value[x]
            if 'cspc' in name:
                return 'pair{:02d}'.format(x)
            else:
                return 'channel{:02d}'.format(x)
            
    def readData(self, fp):
        # print("read fp: ", fp)
        data = {}
        grp = fp['Data']
        for name in grp:
            if "spc" in name:
                self.flag_spc = True
            if "pow" in name:
                self.flag_pow = True
            if "snr" in name:
                self.flag_snr = True
            if "nIncohInt" in name:
                self.flag_nIcoh = True
            # print("spc:",self.flag_spc," pow:",self.flag_pow," snr:", self.flag_snr)
            if isinstance(grp[name], h5py.Dataset):
                array = grp[name][()]
            elif isinstance(grp[name], h5py.Group):
                array = []
                for ch in grp[name]:
                    array.append(grp[name][ch][()])
                array = numpy.array(array)
            else:
                print('Unknown type: {}'.format(name))
            data[name] = array
        return data
    
    def getDataOut(self):
        # print("Getting DataOut")
        self.dataOut = self.ch_dataIn[0].copy()  #dataIn    #blocks, fft, hei for metadata
        if self.flagProcessingHeader:
            self.dataOut.processingHeaderObj = self.ch_dataIn[0].processingHeaderObj.copy()
            self.dataOut.heightList = self.dataOut.processingHeaderObj.heightList
            self.dataOut.ippSeconds = self.dataOut.processingHeaderObj.ipp
            self.dataOut.channelList = self.dataOut.processingHeaderObj.channelList
            self.dataOut.nCohInt = self.dataOut.processingHeaderObj.nCohInt
            self.dataOut.nFFTPoints = self.dataOut.processingHeaderObj.nFFTPoints
        if self.flagControllerHeader:
            self.dataOut.radarControllerHeaderObj = self.ch_dataIn[0].radarControllerHeaderObj.copy()
            self.dataOut.frequency = self.dataOut.radarControllerHeaderObj.frequency
        #--------------------------------------------------------------------
        #--------------------------------------------------------------------
        if self.flag_spc:
            if self.dataOut.data_spc.ndim < 3:
                print("shape spc in: ",self.dataOut.data_spc.shape )
                return 0
        if self.flag_pow:
            if self.dataOut.data_pow.ndim < 2:
                print("shape pow in: ",self.dataOut.data_pow.shape )
                return 0
        if self.flag_snr:
            if self.dataOut.data_snr.ndim < 2:
                print("shape snr in: ",self.dataOut.data_snr.shape )
                return 0
        self.dataOut.data_spc = None
        self.dataOut.data_cspc = None
        self.dataOut.data_pow = None
        self.dataOut.data_snr = None
        self.dataOut.utctime = None
        self.dataOut.nIncohInt = None
        #--------------------------------------------------------------------
        if self.flag_spc:
            spc = [data.data_spc for data in self.ch_dataIn]
            self.dataOut.data_spc = numpy.stack(spc, axis=1)  #blocks, ch, fft, hei
        #--------------------------------------------------------------------
        if self.flag_pow:
            pow = [data.data_pow for data in self.ch_dataIn]
            self.dataOut.data_pow = numpy.stack(pow, axis=1)  #blocks, ch, fft, hei
        #--------------------------------------------------------------------
        if self.flag_snr:
            snr = [data.data_snr for data in self.ch_dataIn]
            self.dataOut.data_snr = numpy.stack(snr, axis=1)  #blocks, ch, fft, hei
        #--------------------------------------------------------------------
        time = [data.utctime for data in self.ch_dataIn]
        time = numpy.asarray(time).mean(axis=0)
        time = numpy.squeeze(time)
        self.dataOut.utctime = time
        #--------------------------------------------------------------------
        if self.flag_nIcoh:
            ints = [data.nIncohInt for data in self.ch_dataIn]
            self.dataOut.nIncohInt = numpy.stack(ints, axis=1)
            if self.dataOut.nIncohInt.ndim > 3:
                aux = self.dataOut.nIncohInt
                self.dataOut.nIncohInt = None
                self.dataOut.nIncohInt = aux[0]
            if self.dataOut.nIncohInt.ndim < 3:
                nIncohInt = numpy.repeat(self.dataOut.nIncohInt, self.dataOut.nHeights).reshape(self.blocksPerFile,self.nChannels, self.dataOut.nHeights)
                #nIncohInt = numpy.reshape(nIncohInt, (self.blocksPerFile,self.nChannels, self.dataOut.nHeights))
                self.dataOut.nIncohInt = None
                self.dataOut.nIncohInt = nIncohInt
            if (self.dataOut.nIncohInt.shape)[0]==self.nChannels:   ## ch,blocks, hei
                self.dataOut.nIncohInt =  numpy.swapaxes(self.dataOut.nIncohInt, 0, 1) ## blocks,ch, hei
        else:
             self.dataOut.nIncohInt = self.ch_dataIn[0].nIncohInt
        #--------------------------------------------------------------------
        # print("utcTime: ", time.shape)
        # print("data_spc ",self.dataOut.data_spc.shape)
        if "data_cspc" in self.dataList:
            pairsList = [pair for pair in itertools.combinations(self.channelList, 2)]
            #print("PairsList: ", pairsList)
            self.dataOut.pairsList = pairsList
            cspc = []
            for i, j in pairsList:
                cspc.append(self.ch_dataIn[i].data_spc*numpy.conjugate(self.ch_dataIn[j].data_spc)) #blocks, fft, hei
            cspc = numpy.asarray(cspc) # #  pairs, blocks, fft, hei
            #print("cspc: ",cspc.shape)
            self.dataOut.data_cspc = numpy.swapaxes(cspc, 0, 1) ## blocks, pairs, fft, hei
            #print("dataOut.data_cspc: ",self.dataOut.data_cspc.shape)
        #if "data_pow" in self.dataList:
        return 1
    # def writeMetadata(self, fp):
    #
    #
    #     grp = fp.create_group('Metadata')
    #
    #     for i in range(len(self.metadataList)):
    #         if not hasattr(self.dataOut, self.metadataList[i]):
    #             print('Metadata: `{}` not found'.format(self.metadataList[i]))
    #             continue
    #         value = getattr(self.dataOut, self.metadataList[i])
    #         if isinstance(value, bool):
    #             if value is True:
    #                 value = 1
    #             else:
    #                 value = 0
    #         grp.create_dataset(self.getLabel(self.metadataList[i]), data=value)
    #     return
    def writeMetadata(self, fp):
        grp = fp.create_group('Metadata')
        for i in range(len(self.metadataList)):
            attribute = self.metadataList[i]
            attr = attribute.split('.')
            if '' in attr:
                attr.remove('')
            #print(attr)
            if len(attr) > 1:
                if not hasattr(eval("self.dataOut."+attr[0]),attr[1]):
                    print('Metadata: {}.{} not found'.format(attr[0],attr[1]))
                    continue
                value = getattr(eval("self.dataOut."+attr[0]),attr[1])
                if isinstance(value, bool):
                    if value is True:
                        value = 1
                    else:
                        value = 0
                grp2 = None
                if not 'Metadata/'+attr[0] in fp:
                    grp2 = fp.create_group('Metadata/'+attr[0])
                else:
                    grp2 = fp['Metadata/'+attr[0]]
                grp2.create_dataset(attr[1], data=value)
            else:
                if not hasattr(self.dataOut, attr[0] ):
                    print('Metadata: `{}` not found'.format(attribute))
                    continue
                value = getattr(self.dataOut, attr[0])
                if isinstance(value, bool):
                    if value is True:
                        value = 1
                    else:
                        value = 0
                if isinstance(value, type(None)):
                    print("------ERROR, value {} is None".format(attribute))
                    
                grp.create_dataset(self.getLabel(attribute), data=value)
        return
    
    def getDsList(self):
        # print("Getting DS List", self.dataList)
        dsList =[]
        dataAux = None
        for i in range(len(self.dataList)):
            dsDict = {}
            if hasattr(self.dataOut, self.dataList[i]):
                dataAux = getattr(self.dataOut, self.dataList[i])
                dsDict['variable'] = self.dataList[i]
            else:
                print('Attribute {} not found in dataOut'.format(self.dataList[i]))
                continue
            if dataAux is None:
                continue
            elif isinstance(dataAux, (int, float, numpy.int_, numpy.float_)):
                dsDict['nDim'] = 0
            else:
                dsDict['nDim'] = len(dataAux.shape) -1
                dsDict['shape'] = dataAux.shape
                if len(dsDict['shape'])>=2:
                    dsDict['dsNumber'] = dataAux.shape[1]
                else:
                    dsDict['dsNumber'] = 1
                dsDict['dtype'] = dataAux.dtype
                # if len(dataAux.shape) == 4:
                #     dsDict['nDim'] = len(dataAux.shape) -1
                #     dsDict['shape'] = dataAux.shape
                #     dsDict['dsNumber'] = dataAux.shape[1]
                #     dsDict['dtype'] = dataAux.dtype
                # else:
                #     dsDict['nDim'] = len(dataAux.shape)
                #     dsDict['shape'] = dataAux.shape
                #     dsDict['dsNumber'] = dataAux.shape[0]
                #     dsDict['dtype'] = dataAux.dtype
            dsList.append(dsDict)
        # print("dsList: ", dsList)
        self.dsList = dsList

    def clean_dataIn(self):
        for ch in range(self.nChannels):
            self.ch_dataIn[ch].data_spc = None
            self.ch_dataIn[ch].utctime = None
            self.ch_dataIn[ch].nIncohInt = None
        self.meta ={}
        self.blocksPerFile = None

    def writeData(self, outFilename):
        self.getDsList()
        fp = h5py.File(outFilename, 'w')
        # print("--> Merged file: ",fp)
        self.writeMetadata(fp)
        grp = fp.create_group('Data')
        dtsets = []
        data = []
        for dsInfo in self.dsList:
            if dsInfo['nDim'] == 0:
                ds = grp.create_dataset(
                    self.getLabel(dsInfo['variable']),(self.blocksPerFile, ),chunks=True,dtype=numpy.float64)
                dtsets.append(ds)
                data.append((dsInfo['variable'], -1))
            else:
                label = self.getLabel(dsInfo['variable'])
                if label is not None:
                    sgrp = grp.create_group(label)
                else:
                    sgrp = grp
                k = -1*(dsInfo['nDim'] - 1)
                # print(k, dsInfo['shape'], dsInfo['shape'][k:])
                for i in range(dsInfo['dsNumber']):
                    ds = sgrp.create_dataset(
                        self.getLabel(dsInfo['variable'], i),(self.blocksPerFile, ) + dsInfo['shape'][k:],
                        chunks=True,
                        dtype=dsInfo['dtype'])
                    dtsets.append(ds)
                    data.append((dsInfo['variable'], i))
        #print("\n",dtsets)
        print('Creating merged file: {}'.format(fp.filename))
        for i, ds in enumerate(dtsets):
            attr, ch = data[i]
            if ch == -1:
                ds[:] = getattr(self.dataOut, attr)
            else:
                #print(ds, getattr(self.dataOut, attr)[ch].shape)
                aux = getattr(self.dataOut, attr)# block, ch, ...
                aux = numpy.swapaxes(aux,0,1) # ch, blocks, ...
                #print(ds.shape, aux.shape)
                #ds[:] = getattr(self.dataOut, attr)[ch]
                ds[:] = aux[ch]
        fp.flush()
        fp.close()
        self.clean_dataIn()
        return
    
    def run(self):
        if not(self.isConfig):
            self.setup()
            self.isConfig = True
        for nf in range(self.nfiles):
            name = None
            for ch in range(self.nChannels):
                name = self.filenameList[ch][nf]
                filename = os.path.join(self.inPaths[ch], name)
                fp = h5py.File(filename, 'r')
                print("Opening file: ",filename)
                self.readFile(fp,ch)
                fp.close()
            if self.blocksPerFile == None:
                self.getBlocksPerFile()
                print("blocks per file: ", self.blocksPerFile)
            if not self.getDataOut():
                print("Error getting DataOut invalid number of blocks")
                return
            name = name[-16:]
            # print("Final name out: ", name)
            outFile = os.path.join(self.pathOut, name)
            # print("Outfile: ", outFile)
            self.writeData(outFile)