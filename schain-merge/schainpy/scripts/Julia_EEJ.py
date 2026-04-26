#!/usr/bin/env python
'''
Created on Jul 7, 2014

@author: roj-idl71
'''
import os, sys, json

#path = os.path.dirname(os.getcwd())
#path = os.path.join(path, 'source')
#sys.path.insert(0, path)

from schainpy.controller import Project

if __name__ == '__main__':

    desc = "JULIA raw experiment "
    filename = "schain.xml"

    dpath = '/home/roberto/puma/JULIA_NEW/JULIA_EW/D2022/'
    dpath = '/home/roberto/puma/JULIA_NEW/JULIA_EW/D2021/'
    dpath = '/home/roberto/puma/JULIA_NEW/JULIA_EW/D2017/'
    dpath = '/home/roberto/puma/JULIA_NEW/JULIA_EW/D2021/'
    dpath = '/home/roberto/puma/JULIA_NEW/JULIA_EW/D2018/'
    #dpath = '/home/roberto/puma/JULIA_NEW/JULIA_EW/D2017/'
    #dpath = '/home/roberto/Folder_aux/D2019/'

    ##dpath = '/home/roberto/puma/JULIA_EW_IMAGING/JULIA_EW/D2017/'
    dpath = '/home/soporte/PUMA/JULIA_EW_IMAGING/JULIA_EW/D2017/'

    figpath = '/home/soporte/DATA/Pictures/JULIA/EEJ/Skew_but_dop_is_shift'+'/'+dpath[-5:-1]
    ppath = "/home/soporte/DATA/MLT/Oblique/2022_03/data_reshape"
    spcdata = '/home/soporte/DATA/JULIA/EEJ/SPC'
    path_parameters = '/home/soporte/DATA/JULIA/EEJ/Params'
    db_range=['25','35']
    db_range=['10','20']
    #db_range=['14','20']
    db_range=['10','23']
    db_range=['13','20']
    db_range=['21','30']
    db_range=['15','30']
    db_range=['13','28']
    tiempo=['7','18']
    altura1=[2,20]
    altura1=[90,220]
    velocity=['-80','80']
    period=60
# PROJECT 1

    show_spc = 0
    save_spc = 0
    fitting = 1
    save_params = 1
    plot_params = 0

    controllerObj = Project()
    controllerObj.setup(id = '191', name='altura1', description=desc)

    readUnitConfObj1 = controllerObj.addReadUnit(datatype='SpectraReader',
                                                path=dpath,
                                                startDate='2017/09/01', #Check 21-29 Jun 2021, 18 May 2022
                                                endDate='2017/09/30', #05,06,07-01-18
                                                #startTime='06:00:00',
                                                #endTime='18:00:00',
                                                startTime='07:00:00',
                                                #startTime='10:00:00',
                                                #startTime='08:38:01',
                                                #startTime='11:16:00',
                                                #startTime='08:13:00',
                                                endTime='17:59:59',
                                                #startTime='16:30:00',
                                                #endTime='17:30:59',
                                                online=0,
                                                walk=1,
                                                expLabel='150EEJ',
                                                getByBlock=1,
						                        delay=20)

#    opObj00 = readUnitConfObj.addOperation(name='printInfo')
#    opObj00 = readUnitConfObj.addOperation(name='printNumberOfBlock')

    procUnitConfObj1 = controllerObj.addProcUnit(datatype='SpectraProc', inputId=readUnitConfObj1.getId())

    opObj11 = procUnitConfObj1.addOperation(name='selectChannels')
    opObj11.addParameter(name='channelList', value='2,', format='intlist')

    '''
    opObj11 = procUnitConfObj1SPC.addOperation(name='removeDC')
    opObj11.addParameter(name='mode', value='2', format='int')
    '''

    #opObj11 = procUnitConfObj1.addOperation(name='dopplerFlip') #It fixes the Doppler
    #opObj11.addParameter(name='chann', value='0', format='int')

    opObj11 = procUnitConfObj1.addOperation(name='removeInterference')

    opObj11 = procUnitConfObj1.addOperation(name='IncohInt', optype='other')
    #opObj11.addParameter(name='n', value='20', format='int')
    opObj11.addParameter(name='n', value='1', format='int')

    opObj11 = procUnitConfObj1.addOperation(name='GetSNR', optype='other')

    if save_spc:
        dataList=['data_spc',
                'utctime']
        metadataList=['nFFTPoints','VelRange','normFactor',
                    'heightList','timeZone']

        op221 = procUnitConfObj1.addOperation(name='HDFWriter', optype='external')
        op221.addParameter(name='path', value=spcdata)
        #op221.addParameter(name='mode', value=1, format='int')
        op221.addParameter(name='dataList', value=dataList)
        op221.addParameter(name='metadataList', value=metadataList)
        #op221.addParameter(name='blocksPerFile', value=500)
        op221.addParameter(name='blocksPerFile', value=2000)

    if show_spc:
        #'''
    #    opObj11 = procUnitConfObj1SPC.addOperation(name='removeInterference')

        opObj11 = procUnitConfObj1.addOperation(name='SpectraPlot', optype='other')
        opObj11.addParameter(name='id', value='1', format='int')
        opObj11.addParameter(name='wintitle', value='Oblique', format='str')
        opObj11.addParameter(name='zmin', value=db_range[0], format='int')
        opObj11.addParameter(name='zmax', value=db_range[1], format='int')
        opObj11.addParameter(name='xaxis', value='velocity', format='str')
        opObj11.addParameter(name='ymin', value=altura1[0], format='int')
        opObj11.addParameter(name='ymax', value=altura1[1], format='int')
    #    opObj11.addParameter(name='xmin', value=velocity[0], format='int')
    #    opObj11.addParameter(name='xmax', value=velocity[1], format='int')
        opObj11.addParameter(name='showprofile', value='1', format='int')
        opObj11.addParameter(name='save', value=figpath, format='str')
        #'''
        #'''
        opObj11 = procUnitConfObj1.addOperation(name='RTIPlot', optype='other')
        opObj11.addParameter(name='id', value='10', format='int')
        opObj11.addParameter(name='wintitle', value='JULIA EEJ RTI', format='str')
        opObj11.addParameter(name='xmin', value=tiempo[0], format='float')
        opObj11.addParameter(name='xmax', value=tiempo[1], format='float')
        opObj11.addParameter(name='ymin', value=altura1[0], format='int')
        opObj11.addParameter(name='ymax', value=altura1[1], format='int')
        opObj11.addParameter(name='zmin', value=db_range[0], format='int')
        opObj11.addParameter(name='zmax', value=db_range[1], format='int')
        opObj11.addParameter(name='showprofile', value='1', format='int')
        #opObj11.addParameter(name='save_period', value=40, format='str')
        opObj11.addParameter(name='save', value=figpath, format='str')
        #opObj11.addParameter(name='throttle', value=1, format='str')
        #'''
        '''
        opObj11 = procUnitConfObj1.addOperation(name='SnrPlot', optype='other')
        opObj11.addParameter(name='id', value='10', format='int')
        opObj11.addParameter(name='wintitle', value='JULIA EEJ SNR', format='str')
        opObj11.addParameter(name='xmin', value=tiempo[0], format='float')
        opObj11.addParameter(name='xmax', value=tiempo[1], format='float')
        opObj11.addParameter(name='ymin', value=altura1[0], format='int')
        opObj11.addParameter(name='ymax', value=altura1[1], format='int')
        opObj11.addParameter(name='zmin', value=0.1, format='int')
        opObj11.addParameter(name='zmax', value=50, format='int')
        #opObj11.addParameter(name='showprofile', value='1', format='int')
        opObj11.addParameter(name='save', value=figpath, format='str')
        '''
    if fitting:
        Dop = 'Max' #Plot and Save the Pos[Max_val] as the Doppler Shift
        Dop = 'Shift' #Plot and Save the Skew Gaussian Shift as the Doppler Shift
        opObj11 = procUnitConfObj1.addOperation(name='Oblique_Gauss_Fit', optype='other')
        opObj11.addParameter(name='mode', value=9, format='int') #Skew
        opObj11.addParameter(name='Dop', value=Dop)
        #opObj11.addParameter(name='mode', value=11, format='int')

        if save_params:
            '''
            dataList=['powerdB', 'Oblique_params', 'Oblique_param_errors', 'dplr_2_u', 'data_snr',
                    'utctime']
            metadataList=['VelRange',
                        'heightList','timeZone']

            op221 = procUnitConfObj1.addOperation(name='HDFWriter', optype='external')
            op221.addParameter(name='path', value=path_parameters)
            #op221.addParameter(name='mode', value=1, format='int')
            op221.addParameter(name='dataList', value=dataList)
            op221.addParameter(name='metadataList', value=metadataList)
            #op221.addParameter(name='blocksPerFile', value=500)
            op221.addParameter(name='blocksPerFile', value=2000)
            '''

            one = {'gdlatr': 'lat', 'gdlonr': 'lon', 'inttms': 'paramInterval'} #reader gdlatr-->lat only 1D

            two = {
                'snl': 'snl', #Debería salir como el original pero más limpio
                'RANGE': 'heightList',   #<----- nmonics
                'DOPP_T1_EEJ': ('Dop_EEJ_T1', (0)),
                'DDOPP_T1_EEJ': ('Err_Dop_EEJ_T1', (0)),
                'SPEC_W_T1_EEJ': ('Spec_W_T1', (0)),
                'DSPEC_W_T1_EEJ': ('Err_Spec_W_T1', (0)),
                'DOPP_T2_EEJ': ('Dop_EEJ_T2', (0)),
                'DDOPP_T2_EEJ': ('Err_Dop_EEJ_T2', (0)),
                'SPEC_W_T2_EEJ': ('Spec_W_T2', (0)),
                'DSPEC_W_T2_EEJ': ('Err_Spec_W_T2', (0)),
                } #writer


            ind = ['range']

            meta = {
                'kinst': 840, #instrumnet code, 840 for JULIA, 14 for JULIA MP CSR
                'kindat': 1962, #type of data #Este es el nuevo e igual para JULIA y JULIA CSR
                'catalog': {
                    'principleInvestigator': 'Danny Scipión',
                    'expPurpose': 'Equatorial Electrojet Parameters',
                    },
                'header': {
                    'analyst': 'D. Hysell'
                }
            }


            op_writer = procUnitConfObj1.addOperation(name='MADWriter', optype='external')
            #op_writer.addParameter(name='path', value='/home/roberto/DATA/hdf5_outputs/Madrigal/EEJ')
            #op_writer.addParameter(name='path', value='/home/roberto/DATA/hdf5_outputs/Madrigal/EEJ/Dop_Max_Val')
            #op_writer.addParameter(name='path', value='/home/roberto/DATA/hdf5_outputs/Madrigal/EEJ/'+Dop+'/'+dpath[-5:-1])
            #op_writer.addParameter(name='path', value='/home/roberto/DATA/hdf5_outputs/Madrigal/EEJ/CorrectFiles/no_snl_Test/01/'+Dop+'/'+dpath[-5:-1])
            op_writer.addParameter(name='path', value='/home/soporte/DATA/hdf5_outputs/Madrigal/EEJ/FinalFiles/'+Dop+'/'+dpath[-5:-1])
            op_writer.addParameter(name='format', value='hdf5', format='str')
            op_writer.addParameter(name='oneDDict', value=json.dumps(one), format='str')
            op_writer.addParameter(name='twoDDict', value=json.dumps(two), format='str')
            op_writer.addParameter(name='ind2DList', value=json.dumps(ind), format='str')
            op_writer.addParameter(name='metadata', value=json.dumps(meta), format='str')


        if plot_params:
            '''
            opObj11 = procUnitConfObj1.addOperation(name='DopplerEEJPlot', optype='other')
            opObj11.addParameter(name='id', value='10', format='int')
            opObj11.addParameter(name='wintitle', value='Doppler EEJ', format='str')
            opObj11.addParameter(name='xmin', value=tiempo[0], format='float')
            opObj11.addParameter(name='xmax', value=tiempo[1], format='float')
            opObj11.addParameter(name='ymin', value=altura1[0], format='int')
            opObj11.addParameter(name='ymax', value=altura1[1], format='int')
            #opObj11.addParameter(name='zmin', value=-250, format='int')
            #opObj11.addParameter(name='zmax', value=250, format='int')
            opObj11.addParameter(name='zlimits', value='(-400,400),(-250,250)')
            #opObj11.addParameter(name='showprofile', value='1', format='int')
            opObj11.addParameter(name='save', value=figpath, format='str')
            #opObj11.addParameter(name='EEJtype', value=1, format='int')

            opObj11 = procUnitConfObj1.addOperation(name='SpcWidthEEJPlot', optype='other')
            opObj11.addParameter(name='id', value='10', format='int')
            opObj11.addParameter(name='wintitle', value='Spectral Width EEJ', format='str')
            opObj11.addParameter(name='xmin', value=tiempo[0], format='float')
            opObj11.addParameter(name='xmax', value=tiempo[1], format='float')
            opObj11.addParameter(name='ymin', value=altura1[0], format='int')
            opObj11.addParameter(name='ymax', value=altura1[1], format='int')
            #opObj11.addParameter(name='zmin', value=0., format='int')
            #opObj11.addParameter(name='zmax', value=250, format='int')
            opObj11.addParameter(name='zlimits', value='(0.1,100),(0.1,250)')
            #opObj11.addParameter(name='showprofile', value='1', format='int')
            opObj11.addParameter(name='save', value=figpath, format='str')
            #opObj11.addParameter(name='EEJtype', value=1, format='int')
            '''
            opObj11 = procUnitConfObj1.addOperation(name='SpectraObliquePlot', optype='other')
            opObj11.addParameter(name='id', value='1', format='int')
            opObj11.addParameter(name='wintitle', value='Oblique', format='str')
            opObj11.addParameter(name='zmin', value=db_range[0], format='int')
            opObj11.addParameter(name='zmax', value=db_range[1], format='int')
            opObj11.addParameter(name='xaxis', value='velocity', format='str')
            opObj11.addParameter(name='ymin', value=altura1[0], format='int')
            opObj11.addParameter(name='ymax', value=altura1[1], format='int')
        #    opObj11.addParameter(name='xmin', value=velocity[0], format='int')
        #    opObj11.addParameter(name='xmax', value=velocity[1], format='int')
            opObj11.addParameter(name='showprofile', value='1', format='int')
            opObj11.addParameter(name='save', value=figpath+'/400', format='str')

            '''
            opObj11 = procUnitConfObj1.addOperation(name='DopplerEEJPlot', optype='other')
            opObj11.addParameter(name='id', value='10', format='int')
            opObj11.addParameter(name='wintitle', value='Doppler EEJ Type II', format='str')
            opObj11.addParameter(name='xmin', value=tiempo[0], format='float')
            opObj11.addParameter(name='xmax', value=tiempo[1], format='float')
        #    opObj11.addParameter(name='ymin', value=altura1[0], format='int')
        #    opObj11.addParameter(name='ymax', value=altura1[1], format='int')
            opObj11.addParameter(name='zmin', value=-250, format='int')
            opObj11.addParameter(name='zmax', value=250, format='int')
            #opObj11.addParameter(name='showprofile', value='1', format='int')
            opObj11.addParameter(name='save', value=figpath, format='str')
            opObj11.addParameter(name='EEJtype', value=2, format='int')
            '''




    controllerObj.start()