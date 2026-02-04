#!python
'''
'''

import os, sys, json, argparse
import datetime
import time

from schainpy.controller import Project

PATH = "/home/pc-igp-179/Documentos/SOPHy"


PARAM = {
    'S':  {'zmin': -80, 'zmax':-45, 'colormap': 'jet'    , 'label': 'Power', 'wrname': 'power','cb_label': 'dBm', 'ch':0},
    'SNR':{'zmin': -10, 'zmax': 15, 'colormap': 'jet'    , 'label': 'SNR', 'wrname': 'snr','cb_label': 'dB', 'ch':0},
    'V':  {'zmin': -12, 'zmax': 12, 'colormap': 'sophy_v', 'label': 'Velocity', 'wrname': 'velocity', 'cb_label': 'm/s', 'ch':0},
    'R':  {'zmin': 0.5, 'zmax': 1 , 'colormap': 'sophy_r', 'label': 'RhoHV', 'wrname':'rhoHV', 'cb_label': '',  'ch':0},
    'P':  {'zmin': -180,'zmax': 180,'colormap': 'sophy_p', 'label': 'PhiDP', 'wrname':'phiDP' , 'cb_label': 'degrees',  'ch':0},
    'D':  {'zmin': -9 , 'zmax': 12, 'colormap': 'sophy_d', 'label': 'ZDR','wrname':'differential_reflectivity' , 'cb_label': 'dB','ch':0},
    'Z':  {'zmin': -20, 'zmax': 80, 'colormap': 'sophy_z', 'label': 'Reflectivity ',  'wrname':'reflectivity', 'cb_label': 'dBz','ch':0},
    'W':  {'zmin':  0 , 'zmax': 12, 'colormap': 'sophy_w', 'label': 'Spectral Width', 'wrname':'spectral_width', 'cb_label': 'm/s', 'ch':0}
    }

META = ['heightList', 'data_azi', 'data_ele', 'mode_op', 'latitude', 'longitude', 'altitude', 'heading', 'radar_name',
    'institution', 'contact', 'h0', 'range_unit', 'prf', 'prf_unit', 'variable', 'variable_unit', 'n_pulses',
    'pulse1_range', 'pulse1_width', 'pulse2_width', 'pulse1_repetitions', 'pulse2_repetitions', 'pulse_width_unit',
    'snr_threshold', 'data_noise']


def max_index(r, sample_rate, ipp, h0,ipp_km):

    return int(sample_rate*ipp*1e6 * r / ipp_km) + int(sample_rate*ipp*1e6 * -h0 / ipp_km)


def main(args):
    experiment = args.experiment

    fp = open(os.path.join(PATH, experiment, 'experiment.json'))
    conf = json.loads(fp.read())

    ipp_km = conf['usrp_tx']['ipp']
    bottom = conf['pedestal']['bottom']
    ipp = ipp_km * 2 /300000
    sample_rate  = conf['usrp_rx']['sample_rate']
    speed_axis = conf['pedestal']['speed']

    if args.angles:
        angles = args.angles
    else:
        angles = conf['pedestal']['table']



    start_date = conf['name'].split('@')[1].split('T')[0].replace('-', '/')
    end_date = start_date
    if args.start_time:
        start_time = args.start_time
    else:
        start_time = conf['name'].split('@')[1].split('T')[1].replace('-', ':')

    if args.end_time:
        end_time = args.end_time
    else:
        end_time = '23:59:59'
    

    if args.label:
        label = '-{}'.format(args.label)
    else:
        label = ''

    path_plots = os.path.join(PATH, experiment, 'plots{}'.format(label))
    path_save = os.path.join(PATH, experiment, 'param{}'.format(label))


    time_offset = args.time_offset
    parameters = args.parameters

    N = int(1.0/(abs(speed_axis[0])*ipp))
    RMIX = 6.0 
    H0   = -1.33
    MASK = args.mask

    path = os.path.join(PATH, experiment, 'rawdata')
    path_ped = os.path.join(PATH, experiment, 'position')

    proyecto = Project()
    proyecto.setup(id = '2', name='Test_2025', description="PRUEBA")

    lectura = proyecto.addReadUnit(datatype='DigitalRFReader',
                                                path=path,
                                                startDate= "2025/01/06",#today,
                                                endDate= "2025/01/06",#today,
                                                startTime= start_time,
                                                endTime= end_time,
                                                delay=30,
                                                #set=0,
                                                online=0,
                                                walk=1,
                                                ippKm = ipp_km,
                                                getByBlock = 1,
                                                nProfileBlocks = N
                                                )

    n_pulses = 1
    pulse_1_width = conf['usrp_tx']['pulse_1']
    pulse_1_repetitions = conf['usrp_tx']['repetitions_1']
    pulse_2_width = conf['usrp_tx']['pulse_2']
    pulse_2_repetitions = conf['usrp_tx']['repetitions_2']

    if '1' in args.pulses:
        voltage1 = proyecto.addProcUnit(
            datatype='VoltageProc', 
            inputId=lectura.getId()
            )

        op = voltage1.addOperation(
            name='ProfileSelector'
            )
        op.addParameter(
            name='profileRangeList', 
            value='0,{}'.format(conf['usrp_tx']['repetitions_1']-1)
            )

        if conf['usrp_tx']['code_type_1'] != 'None':
            codes = [ c.strip() for c in conf['usrp_tx']['code_1'].split(',')]
            code = []
            for c in codes:
                code.append([int(x) for x in c])
            op = voltage1.addOperation(name='Decoder', optype='other')
            op.addParameter(name='code', value=code)
            op.addParameter(name='nCode', value=len(code), format='int')
            op.addParameter(name='nBaud', value=len(code[0]), format='int')
            ncode = len(code)
        else:
            ncode = 1
            code = ['0']

        op = voltage1.addOperation(name='CohInt', optype='other')
        op.addParameter(name='n', value=ncode, format='int')
            
        op = voltage1.addOperation(name='setH0')
        op.addParameter(name='h0', value=H0, format='float')

        if args.range > 0:
            op = voltage1.addOperation(name='selectHeights')
            op.addParameter(name='minIndex', value=max_index(0, sample_rate, ipp, H0,ipp_km), format='int')
            op.addParameter(name='maxIndex', value=max_index(args.range, sample_rate, ipp, H0,ipp_km), format='int')


        op = voltage1.addOperation(name='PulsePair_vRF', optype='other')
        op.addParameter(name='n', value=int(conf['usrp_tx']['repetitions_1'])/ncode, format='int')

        if args.rmDC:
            op.addParameter(name='removeDC', value=1, format='int')

        proc1 = proyecto.addProcUnit(datatype='ParametersProc', inputId=voltage1.getId())
        proc1.addParameter(name='runNextUnit', value=True)

        opObj10 = proc1.addOperation(name="WeatherRadar")
        opObj10.addParameter(name='CR_Flag',value=True)
        print(1, len(code[0]))
        opObj10.addParameter(name='tauW',value=(1e-6/sample_rate)*len(code[0]))
        opObj10.addParameter(name='Pt',value=200)
        opObj10.addParameter(name='min_index',value=max_index(0, sample_rate, ipp, H0,ipp_km))


        op = proc1.addOperation(name='PedestalInformation')
        op.addParameter(name='path', value=path_ped, format='str')
        op.addParameter(name='interval', value='0.04')
        op.addParameter(name='time_offset', value=time_offset)
        op.addParameter(name='mode', value=args.mode)

        op = proc1.addOperation(name='Block360')
        op.addParameter(name='attr_data', value='data_param')
        op.addParameter(name='runNextOp', value=True)
        op.addParameter(name='angles', value=angles)
        op.addParameter(name='heading', value=conf['heading'])


    if '2' in args.pulses:
        voltage2 = proyecto.addProcUnit(
            datatype='VoltageProc', 
            inputId=lectura.getId()
            )   

        op = voltage2.addOperation(
            name='ProfileSelector'
            )
        op.addParameter(
            name='profileRangeList', 
            value='{},{}'.format(conf['usrp_tx']['repetitions_1'], conf['usrp_tx']['repetitions_1']+conf['usrp_tx']['repetitions_2']-1)
            )

        if conf['usrp_tx']['code_type_2']:
            codes = [ c.strip() for c in conf['usrp_tx']['code_2'].split(',')]
            code = []
            for c in codes:
                code.append([int(x) for x in c])
            op = voltage2.addOperation(name='Decoder', optype='other')
            op.addParameter(name='code', value=code)
            op.addParameter(name='nCode', value=len(code), format='int')
            op.addParameter(name='nBaud', value=len(code[0]), format='int')

            op = voltage2.addOperation(name='CohInt', optype='other')
            op.addParameter(name='n', value=len(code), format='int')

            ncode = len(code)
        else:
            ncode = 1
            
        op = voltage2.addOperation(name='setH0')
        op.addParameter(name='h0', value=H0, format='float')

        if args.range > 0:
            op = voltage2.addOperation(name='selectHeights')
            op.addParameter(name='minIndex', value=max_index(0, sample_rate, ipp, H0,ipp_km), format='int')
            op.addParameter(name='maxIndex', value=max_index(args.range, sample_rate, ipp, H0,ipp_km), format='int')


        op = voltage2.addOperation(name='PulsePair_vRF', optype='other')
        op.addParameter(name='n', value=int(conf['usrp_tx']['repetitions_1'])/ncode, format='int')

        proc2 = proyecto.addProcUnit(datatype='ParametersProc', inputId=voltage2.getId())
        proc2.addParameter(name='runNextUnit', value=True)

        opObj10 = proc2.addOperation(name="WeatherRadar")
        opObj10.addParameter(name='CR_Flag',value=True,format='bool')
        print(2, len(code[0]))
        opObj10.addParameter(name='tauW',value=(1e-6/sample_rate)*len(code[0]))
        opObj10.addParameter(name='Pt',value=200)
        opObj10.addParameter(name='min_index',value=max_index(RMIX, sample_rate, ipp, H0,ipp_km))

        op = proc2.addOperation(name='PedestalInformation')
        op.addParameter(name='path', value=path_ped, format='str')
        op.addParameter(name='interval', value='0.04')
        op.addParameter(name='time_offset', value=time_offset)
        op.addParameter(name='mode', value=args.mode)
        op.addParameter(name='heading', value=conf['heading'])

        op = proc2.addOperation(name='Block360')
        op.addParameter(name='attr_data', value='data_param')
        op.addParameter(name='runNextOp', value=True)
        op.addParameter(name='angles', value=angles)
        op.addParameter(name='heading', value=conf['heading'])
    
    if '1' in args.pulses and '2' in args.pulses:
        merge = proyecto.addProcUnit(datatype='MergeProc', inputId=[proc1.getId(), proc2.getId()])
        merge.addParameter(name='attr_data', value='data_param')
        merge.addParameter(name='mode', value='7')
        merge.addParameter(name='index', value=max_index(RMIX, sample_rate, ipp, H0,ipp_km))

    elif '1' in args.pulses:
        merge = proc1
    elif '2' in args.pulses:
        merge = proc2

    for param in parameters:

        if args.plot:
            op= merge.addOperation(name='WeatherParamsPlot')
            if args.save:
                op.addParameter(name='save', value=path_plots, format='str')
            op.addParameter(name='save_period', value=-1)
            op.addParameter(name='show', value=args.show)
            op.addParameter(name='channels', value='0,')
            op.addParameter(name='zmin', value=PARAM[param]['zmin'], format='int')
            op.addParameter(name='zmax', value=PARAM[param]['zmax'], format='int')
            op.addParameter(name='yrange', value=20, format='int')
            op.addParameter(name='xrange', value=args.range, format='int')
            op.addParameter(name='attr_data', value=param, format='str')
            op.addParameter(name='labels', value=[[PARAM[param]['label']], [PARAM[param]['label']]])
            op.addParameter(name='save_code', value=param)
            op.addParameter(name='cb_label', value=PARAM[param]['cb_label'])
            op.addParameter(name='colormap', value=PARAM[param]['colormap'])
            op.addParameter(name='bgcolor', value='black')
            op.addParameter(name='localtime', value=False)
            op.addParameter(name='shapes', value='./shapes')
            op.addParameter(name='latitude', value=conf['latitude'], format='float')
            op.addParameter(name='longitude', value=conf['longitude'], format='float')
            op.addParameter(name='map', value=True)

            if MASK: op.addParameter(name='mask', value=MASK, format='float')
            if args.server:
                op.addParameter(name='server', value='190.187.237.239:4444')
                op.addParameter(name='exp_code', value='400')

            desc = {
                    'Data': {
                        'data_param': {PARAM[param]['wrname']: ['H', 'V']},
                        'utctime': 'time'
                    },
                     'Metadata': {
                        'heightList': 'range',
                        'data_azi': 'azimuth',
                        'data_ele': 'elevation',
                        'mode_op': 'scan_type',
                        'h0': 'range_correction',
                        'dataPP_NOISE': 'noise',
                    }
                }

        if args.save:
            writer = merge.addOperation(name='HDFWriter')
            writer.addParameter(name='path', value=path_save, format='str')
            writer.addParameter(name='Reset', value=True)
            writer.addParameter(name='setType', value='weather')
            writer.addParameter(name='setChannel', value='0') #new parameter choose ch 0  H  or ch 1 V
            writer.addParameter(name='description', value=json.dumps(desc))
            writer.addParameter(name='blocksPerFile', value='1',format='int')
            writer.addParameter(name='metadataList', value=','.join(META))
            writer.addParameter(name='dataList', value='data_param,utctime')
            writer.addParameter(name='weather_var', value=param)
            writer.addParameter(name='mask', value=MASK, format='float')
            writer.addParameter(name='localtime', value=False)
            # meta
            writer.addParameter(name='latitude', value=conf['latitude'])
            writer.addParameter(name='longitude', value=conf['longitude'])
            writer.addParameter(name='altitude', value=conf['altitude'])
            writer.addParameter(name='heading', value=conf['heading'])
            writer.addParameter(name='radar_name', value='SOPHy')
            writer.addParameter(name='institution', value='IGP')
            writer.addParameter(name='contact', value='dscipion@igp.gob.pe')
            writer.addParameter(name='created_by', value='Signal Chain (https://pypi.org/project/schainpy/)')
            writer.addParameter(name='range_unit', value='km')
            writer.addParameter(name='prf', value=1/ipp)
            writer.addParameter(name='prf_unit', value='hertz')
            writer.addParameter(name='variable', value=PARAM[param]['label'])
            writer.addParameter(name='variable_unit', value=PARAM[param]['cb_label'])
            writer.addParameter(name='n_pulses', value=n_pulses)
            writer.addParameter(name='pulse1_range', value=RMIX)
            writer.addParameter(name='pulse1_width', value=pulse_1_width)
            writer.addParameter(name='pulse2_width', value=pulse_2_width)
            writer.addParameter(name='pulse1_repetitions', value=pulse_1_repetitions)
            writer.addParameter(name='pulse2_repetitions', value=pulse_2_repetitions)
            writer.addParameter(name='pulse_width_unit', value='microseconds')
            writer.addParameter(name='snr_threshold', value=MASK)
            writer.addParameter(name='cr_hv', value=[67.41,67.17]) #new parameter


    return proyecto




if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Script to process SOPHy data.')
    parser.add_argument('experiment',
                        help='Experiment name')
    parser.add_argument('--parameters', nargs='*', default=['S'],
                        help='Variables to process: P, Z, V')
    parser.add_argument('--pulses', nargs='*', default=['1', '2'],
                        help='Variables to process: 1, 2')
    parser.add_argument('--range', default=60, type=float,
                        help='Max range to plot')
    parser.add_argument('--server', action='store_true',
                        help='Send to realtime')
    parser.add_argument('--start_time', default='',
                        help='Set start time.')
    parser.add_argument('--end_time', default='',
                        help='Set end time.')
    parser.add_argument('--rmDC', action='store_true',
                        help='Apply remove DC.')
    parser.add_argument('--time_offset', default=0,
                        help='Fix time offset')
    parser.add_argument('--mode', default=None,
                        help='Type of scan')
    parser.add_argument('--angles', nargs='*', default=[], type=int,
                        help='Angles to process')
    parser.add_argument('--plot', action='store_true',
                        help='Create plot files')
    parser.add_argument('--save', action='store_true',
                        help='Create output files')
    parser.add_argument('--show', action='store_true',
                        help='Show matplotlib plot.')
    parser.add_argument('--mask', default=0.36, type=float,
                        help='Filter mask over SNR')
    parser.add_argument('--label', default='',
                        help='Label for plot & param folder')

    args = parser.parse_args()

    proyecto= main(args)
    proyecto.start() 