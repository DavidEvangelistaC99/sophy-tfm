
# SOPHY PROC script
import os, sys, json, argparse
import datetime
import time

PATH = '/DATA_RM/DATA'
# PATH = '/Users/jespinoza/workspace/data/'
#PATH = '/home/soporte/Documents/HUANCAYO'
PARAM = {
    'P': {'name': 'dataPP_POWER', 'zmin': -45, 'zmax': -25, 'colormap': 'jet', 'label': 'Power', 'wrname': 'Pow','cb_label': 'dB', 'ch':0},
    'V': {'name': 'dataPP_DOP', 'zmin': -20, 'zmax': 20, 'colormap': 'seismic', 'label': 'Velocity', 'wrname': 'Vel', 'cb_label': 'm/s', 'ch':0},
    'RH': {'name': 'RhoHV_R', 'zmin': 0,   'zmax': 1,  'colormap': 'jet',    'label': 'Coef.Correlacion', 'wrname':'R', 'cb_label': '*',  'ch':0},
    'FD': {'name': 'PhiD_P', 'zmin': -180,'zmax': 180,'colormap': 'RdBu_r', 'label': 'Fase Diferencial', 'wrname':'P' , 'cb_label': 'º',  'ch':0},
    'ZD': {'name': 'Zdb_D', 'zmin': -20, 'zmax': 60, 'colormap': 'viridis','label': 'Reflect.Diferencial','wrname':'D' , 'cb_label': 'dBz','ch':0},
    'Z':  {'name': 'Zdb', 'zmin': -20, 'zmax': 70, 'colormap': 'gist_ncar','label': 'Reflectividad',  'wrname':'Z', 'cb_label': 'dBz','ch':1},
    'W':  {'name': 'Sigmav_W', 'zmin': 0, 'zmax':5, 'colormap': 'viridis','label': 'AnchoEspectral', 'wrname':'S', 'cb_label': 'hz', 'ch':1}
    }

#
def max_index(r, sample_rate, ipp):

    return int(sample_rate*ipp*1e6 * r / 60) + int(sample_rate*ipp*1e6 * 1.2 / 60)

def main(args):

    experiment = args.experiment
    fp = open(os.path.join(PATH, experiment, 'experiment.conf'))
    conf = json.loads(fp.read())

    ipp_km = conf['usrp_tx']['ipp']
    ipp = ipp_km * 2 /300000
    sample_rate  = conf['usrp_rx']['sample_rate']
    axis = ['0' if x=='elevation' else '1' for x in conf['pedestal']['axis']]      # AZIMUTH 1 ELEVACION 0
    speed_axis = conf['pedestal']['speed']
    steeps = conf['pedestal']['table']
    time_offset = args.time_offset
    parameters = args.parameters
    start_date = experiment.split('@')[1].split('T')[0].replace('-', '/')
    end_date = start_date
    start_time = experiment.split('@')[1].split('T')[1].replace('-', ':')
    end_time = '23:59:59'
    N = int(1/(speed_axis[0]*ipp))                                               # 1 GRADO DE RESOLUCION
    path = os.path.join(PATH, experiment, 'rawdata')
    path_ped = os.path.join(PATH, experiment, 'position')
    path_plots = os.path.join(PATH, experiment, 'plots_ch0')
    path_save = os.path.join(PATH, experiment, 'param')
    RMIX = 20

    from schainpy.controller import Project

    project = Project()
    project.setup(id='1', name='Sophy', description='sophy proc')

    reader = project.addReadUnit(datatype='DigitalRFReader',
        path=path,
        startDate=start_date,
        endDate=end_date,
        startTime=start_time,
        endTime=end_time,
        delay=30,
        channelList='0',
        online=args.online,
        walk=1,
        ippKm = ipp_km,
        getByBlock = 1,
        nProfileBlocks = N,
    )

    if not conf['usrp_tx']['enable_2']: # One Pulse
        voltage = project.addProcUnit(datatype='VoltageProc', inputId=reader.getId())

        if conf['usrp_tx']['code_type_1']:
            code = [c.split() for c in conf['usrp']['code_1']]
            op = voltage.addOperation(name='Decoder', optype='other')
            op.addParameter(name='code', value=code)
            op.addParameter(name='nCode', value=len(code), format='int')
            op.addParameter(name='nBaud', value=len(code[0]), format='int')

        op = voltage.addOperation(name='setH0')
        op.addParameter(name='h0', value='-1.2')

        if args.range >= 0:
            op = voltage.addOperation(name='selectHeights')
            op.addParameter(name='minIndex', value='0', format='int')
            op.addParameter(name='maxIndex', value=max_index(RMIX, sample_rate, ipp), format='int')

        code=[[1]]
        opObj11 = voltage.addOperation(name='Decoder', optype='other')
        opObj11.addParameter(name='code', value=code)
        opObj11.addParameter(name='nCode', value='1', format='int')
        opObj11.addParameter(name='nBaud', value='1', format='int')

        op = voltage2.addOperation(name='CohInt', optype='other') #Minimo integrar 2 perfiles por ser codigo complementario
        op.addParameter(name='n', value=2*len(code), format='int')

        #op = voltage.addOperation(name='PulsePair_vRF', optype='other')
        #op.addParameter(name='n', value=int(N), format='int')

        if args.range >= 0:
            op = voltage.addOperation(name='selectHeights')
            op.addParameter(name='minIndex', value='0', format='int')
            op.addParameter(name='maxIndex', value=max_index(RMIX, sample_rate, ipp), format='int')


        op = voltage.addOperation(name='PulsePair_vRF', optype='other')
        op.addParameter(name='n', value=125, format='int')


        proc = project.addProcUnit(datatype='ParametersProc', inputId=voltage.getId())
        #procUnitConfObjB.addParameter(name='runNextUnit', value=True)

        opObj10 = proc.addOperation(name="WeatherRadar")
        opObj10.addParameter(name='variableList',value='Reflectividad,VelocidadRadial,AnchoEspectral')

        # {"latitude": -12.0404828587, "longitude": -75.2147483647, "altitude": 3379.2147483647}

        op = proc.addOperation(name='PedestalInformation')
        op.addParameter(name='path', value=path_ped, format='str')
        op.addParameter(name='interval', value='0.04')
        op.addParameter(name='time_offset', value=time_offset)
        op.addParameter(name='az_offset', value=-26.2)

        for param in parameters:
            op = proc.addOperation(name='Block360_vRF4')
            #op.addParameter(name='axis', value=','.join(axis))
            op.addParameter(name='attr_data', value=PARAM[param]['name'])
            op.addParameter(name='runNextOp', value=True)

            op= proc.addOperation(name='WeatherParamsPlot')
            if args.save: op.addParameter(name='save', value=path_plots, format='str')
            op.addParameter(name='save_period', value=-1)
            op.addParameter(name='show', value=args.show)
            op.addParameter(name='channels', value='0,')
            op.addParameter(name='zmin', value=PARAM[param]['zmin'])
            op.addParameter(name='zmax', value=PARAM[param]['zmax'])
            op.addParameter(name='attr_data', value=PARAM[param]['name'], format='str')
            op.addParameter(name='labels', value=[PARAM[param]['label']])
            op.addParameter(name='save_code', value=param)
            op.addParameter(name='cb_label', value=PARAM[param]['cb_label'])
            op.addParameter(name='colormap', value=PARAM[param]['colormap'])

            desc = {
                    'Data': {
                        PARAM[param]['name']: PARAM[param]['label'],
                        'utctime': 'time'
                    },
                     'Metadata': {
                        'heightList': 'range',
                        'data_azi': 'azimuth',
                        'data_ele': 'elevation',
                    }
                }

            if args.save:
                opObj10 = proc.addOperation(name='HDFWriter')
                opObj10.addParameter(name='path',value=path_save+'-{}'.format(param), format='str')
                opObj10.addParameter(name='Reset',value=True)
                opObj10.addParameter(name='setType',value='weather')
                opObj10.addParameter(name='description',value='desc')
                opObj10.addParameter(name='blocksPerFile',value='1',format='int')
                opObj10.addParameter(name='metadataList',value='heightList,data_azi,data_ele')
                opObj10.addParameter(name='dataList',value='{},utctime'.format(PARAM[param]['name']))

    else: #Two pulses

        voltage1 = project.addProcUnit(datatype='VoltageProc', inputId=reader.getId())

        print("repetions",conf['usrp_tx']['repetitions_1'])

        op = voltage1.addOperation(name='ProfileSelector')
        op.addParameter(name='profileRangeList', value='0,{}'.format(conf['usrp_tx']['repetitions_1']-1))


        #op3 = voltage1.addOperation(name='ProfileSelector', optype='other')
        #op3.addParameter(name='profileRangeList', value='1,123')

        '''
        if conf['usrp_tx']['code_type_1'] != 'None':
            code = [c.split() for c in conf['usrp_tx']['code_1']]
            op = voltage1.addOperation(name='Decoder', optype='other')
            op.addParameter(name='code', value=code)
            op.addParameter(name='nCode', value=len(code), format='int')
            op.addParameter(name='nBaud', value=len(code[0]), format='int')
        '''

        code=[[1]]

        opObj11 = voltage1.addOperation(name='Decoder', optype='other')
        opObj11.addParameter(name='code', value=code)
        opObj11.addParameter(name='nCode', value='1', format='int')
        opObj11.addParameter(name='nBaud', value='1', format='int')

        op = voltage1.addOperation(name='setH0')
        op.addParameter(name='h0', value='-1.2')

        if args.range >= 0:
            op = voltage1.addOperation(name='selectHeights')
            op.addParameter(name='minIndex', value='0', format='int')
            op.addParameter(name='maxIndex', value=max_index(RMIX, sample_rate, ipp), format='int')

        op = voltage1.addOperation(name='CohInt', optype='other') #Minimo integrar 2 perfiles por ser codigo complementario
        op.addParameter(name='n', value=2, format='int')

        op = voltage1.addOperation(name='PulsePair_vRF', optype='other')
        #op.addParameter(name='n', value=int(N), format='int')
        op.addParameter(name='n', value=61, format='int')
        #op.addParameter(name='removeDC',value=True)

        '''
        if args.range >= 0:
            print("corto",max_index(RMIX, sample_rate, ipp))
            op = voltage1.addOperation(name='selectHeights')
            op.addParameter(name='minIndex', value='0', format='int')
            op.addParameter(name='maxIndex', value=max_index(RMIX, sample_rate, ipp), format='int')
        '''
        proc1 = project.addProcUnit(datatype='ParametersProc', inputId=voltage1.getId())
        proc1.addParameter(name='runNextUnit', value=True)

        opObj10 = proc1.addOperation(name="WeatherRadar")
        opObj10.addParameter(name='variableList',value='Reflectividad,VelocidadRadial,AnchoEspectral')
        opObj10.addParameter(name='tauW',value=0.4*1e-6)
        opObj10.addParameter(name='Pt',value=0.2)

        # {"latitude": -12.0404828587, "longitude": -75.2147483647, "altitude": 3379.2147483647}

        op = proc1.addOperation(name='PedestalInformation')
        op.addParameter(name='path', value=path_ped, format='str')
        op.addParameter(name='interval', value='0.04')
        op.addParameter(name='time_offset', value=time_offset)
        op.addParameter(name='az_offset', value=-26.2)

        for param in parameters:
            op = proc1.addOperation(name='Block360_vRF4')
            op.addParameter(name='attr_data', value=PARAM[param]['name'])
            op.addParameter(name='runNextOp', value=True)

        voltage2 = project.addProcUnit(datatype='VoltageProc', inputId=reader.getId())

        op = voltage2.addOperation(name='ProfileSelector')
        op.addParameter(name='profileRangeList', value='{},{}'.format(conf['usrp_tx']['repetitions_1'], conf['usrp_tx']['repetitions_1']+conf['usrp_tx']['repetitions_2']-1))


        if conf['usrp_tx']['code_type_2']:
            print(conf['usrp_tx']['code_2'])
            codes = [ c.strip() for c in conf['usrp_tx']['code_2'].split(',')]
            code = []
            for c in codes:
                code.append([int(x) for x in c])
            print(code)
            print(code[0])
            op = voltage2.addOperation(name='Decoder', optype='other')
            op.addParameter(name='code', value=code)
            op.addParameter(name='nCode', value=len(code), format='int')
            op.addParameter(name='nBaud', value=len(code[0]), format='int')
            import numpy
            pwcode = numpy.sum(numpy.array(code[0])**2)
            print("pwcode",pwcode)

            op = voltage2.addOperation(name='CohInt', optype='other') #Minimo integrar 2 perfiles por ser codigo complementario
            op.addParameter(name='n', value=len(code), format='int')
            ncode = len(code)
        else:
            ncode = 1

        op = voltage2.addOperation(name='setH0')
        op.addParameter(name='h0', value='-1.2')

        if args.range >= 0:
            if args.range==0:
                args.range= ipp_km
            op = voltage2.addOperation(name='selectHeights')
            op.addParameter(name='minIndex', value=max_index(RMIX, sample_rate, ipp), format='int')
            op.addParameter(name='maxIndex', value=max_index(args.range, sample_rate, ipp), format='int')

        #op = voltage2.addOperation(name='PulsePair_vRF', optype='other')
        #op.addParameter(name='n', value=int(N)/ncode, format='int')
        op = voltage2.addOperation(name='PulsePair_vRF', optype='other')
        op.addParameter(name='n', value=64, format='int')
        #op.addParameter(name='removeDC',value=True)

        '''

        if args.range >= 0:
            if args.range==0:
                args.range= ipp_km
            op = voltage2.addOperation(name='selectHeights')
            print("largo",max_index(RMIX, sample_rate, ipp))
            print("largo2",max_index(args.range, sample_rate, ipp))

            op.addParameter(name='minIndex', value=max_index(RMIX, sample_rate, ipp), format='int')
            op.addParameter(name='maxIndex', value=max_index(args.range, sample_rate, ipp), format='int')
        '''

        proc2 = project.addProcUnit(datatype='ParametersProc', inputId=voltage2.getId())

        opObj10 = proc2.addOperation(name="WeatherRadar")
        opObj10.addParameter(name='variableList',value='Reflectividad,AnchoEspectral')
        opObj10.addParameter(name='tauW',value=6.3*1e-6)
        opObj10.addParameter(name='Pt',value=3.2)


        # {"latitude": -12.0404828587, "longitude": -75.2147483647, "altitude": 3379.2147483647}

        op = proc2.addOperation(name='PedestalInformation')
        op.addParameter(name='path', value=path_ped, format='str')
        op.addParameter(name='interval', value='0.04')
        op.addParameter(name='time_offset', value=time_offset)
        op.addParameter(name='az_offset', value=-26.2)

        for param in parameters:
            op = proc2.addOperation(name='Block360_vRF4')
            #op.addParameter(name='axis', value=','.join(axis))
            op.addParameter(name='attr_data', value=PARAM[param]['name'])
            op.addParameter(name='runNextOp', value=True)

            merge = project.addProcUnit(datatype='MergeProc', inputId=[proc1.getId(), proc2.getId()])
            merge.addParameter(name='attr_data', value=PARAM[param]['name'])
            merge.addParameter(name='mode', value='7') #RM

            op= merge.addOperation(name='WeatherParamsPlot')
            if args.save: op.addParameter(name='save', value=path_plots, format='str')
            op.addParameter(name='save_period', value=-1)
            op.addParameter(name='show', value=args.show)
            op.addParameter(name='channels', value='0,')
            op.addParameter(name='zmin', value=PARAM[param]['zmin'])
            op.addParameter(name='zmax', value=PARAM[param]['zmax'])
            op.addParameter(name='attr_data', value=PARAM[param]['name'], format='str')
            op.addParameter(name='labels', value=[PARAM[param]['label']])
            op.addParameter(name='save_code', value=param)
            op.addParameter(name='cb_label', value=PARAM[param]['cb_label'])
            op.addParameter(name='colormap', value=PARAM[param]['colormap'])

            desc = {
                    'Data': {
                        PARAM[param]['name']: PARAM[param]['label'],
                        'utctime': 'time'
                    },
                     'Metadata': {
                        'heightList': 'range',
                        'data_azi': 'azimuth',
                        'data_ele': 'elevation',
                    }
                }

            if args.save:
                opObj10 = merge.addOperation(name='HDFWriter')
                opObj10.addParameter(name='path',value=path_save, format='str')
                opObj10.addParameter(name='Reset',value=True)
                opObj10.addParameter(name='setType',value='weather')
                opObj10.addParameter(name='description',value='desc')
                opObj10.addParameter(name='blocksPerFile',value='1',format='int')
                opObj10.addParameter(name='metadataList',value='heightList,data_azi,data_ele')
                opObj10.addParameter(name='dataList',value='{},utctime'.format(PARAM[param]['name']))

    project.start()

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Script to process SOPHy data.')
    parser.add_argument('experiment',
                        help='Experiment name')
    parser.add_argument('--parameters', nargs='*', default=['P'],
                        help='Variables to process: P, Z, V')
    parser.add_argument('--time_offset', default=0,
                        help='Fix time offset')
    parser.add_argument('--range', default=0, type=float,
                        help='Max range to plot')
    parser.add_argument('--save', action='store_true',
                        help='Create output files')
    parser.add_argument('--show', action='store_true',
                        help='Show matplotlib plot.')
    parser.add_argument('--online', action='store_true',
                        help='Set online mode.')

    args = parser.parse_args()

    main(args)
