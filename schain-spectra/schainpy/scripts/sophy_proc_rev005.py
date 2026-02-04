# SOPHY PROC script
import os, sys, json, argparse
import datetime
import time

PATH = '/DATA_RM/DATA'
# PATH = '/Users/jespinoza/workspace/data/'
#PATH = '/home/roberto/DATA/data_WR_RHI/RHI'
PATH = '/home/soporte/Downloads/data_WR_RHI'
PATH = '/home/soporte/Documents/EVENTO/'


PARAM = {
    'S': {'name': 'dataPP_POWER', 'zmin': -45, 'zmax': -15, 'colormap': 'jet', 'label': 'Power', 'wrname': 'power','cb_label': 'dBm', 'ch':0},
    'S2': {'name': 'data_pow', 'zmin': -45, 'zmax': -15, 'colormap': 'jet', 'label': 'Power', 'wrname': 'power','cb_label': 'dBm', 'ch':0},
    #'V': {'name': 'dataPP_DOP', 'zmin': -10, 'zmax': 10, 'colormap': 'sophy_v', 'label': 'Velocity', 'wrname': 'velocity', 'cb_label': 'm/s', 'ch':0},
    'V': {'name': 'velRadial_V', 'zmin': -10, 'zmax': 10, 'colormap': 'sophy_v', 'label': 'Velocity', 'wrname': 'velocity', 'cb_label': 'm/s', 'ch':0},
    'R': {'name': 'RhoHV_R', 'zmin': 0,   'zmax': 1,  'colormap': 'jet',    'label': 'RhoHV', 'wrname':'rhoHV', 'cb_label': '*',  'ch':0},
    'P': {'name': 'PhiD_P', 'zmin': -180,'zmax': 180,'colormap': 'RdBu_r', 'label': 'PhiDP', 'wrname':'phiDP' , 'cb_label': 'º',  'ch':0},
    'D': {'name': 'Zdb_D', 'zmin': -20, 'zmax': 80, 'colormap': 'gist_ncar','label': 'ZDR','wrname':'differential_reflectivity' , 'cb_label': 'dBz','ch':0},
    'Z':  {'name': 'Zdb', 'zmin': -30, 'zmax': 80, 'colormap': 'sophy_r','label': 'Reflectivity',  'wrname':'reflectivity', 'cb_label': 'dBz','ch':1},
    'W':  {'name': 'Sigmav_W', 'zmin': 0, 'zmax': 12, 'colormap': 'sophy_w','label': 'Spectral Width', 'wrname':'spectral_width', 'cb_label': 'm/s', 'ch':1}
    }

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
    steps = conf['pedestal']['table']
    time_offset = args.time_offset
    parameters = args.parameters
    start_date = experiment.split('@')[1].split('T')[0].replace('-', '/')
    end_date = start_date
    if args.start_time:
        start_time = args.start_time
    else:
        start_time = experiment.split('@')[1].split('T')[1].replace('-', ':')
    #start_time = '16:15:00'
    end_time = '23:59:59'
    N = int(1/(speed_axis[0]*ipp))                                               # 1 GRADO DE RESOLUCION
    path = os.path.join(PATH, experiment, 'rawdata')
    path_ped = os.path.join(PATH, experiment, 'position')
    path_plots = os.path.join(PATH, experiment, 'plotsC0_FD_PL_R'+str(args.range)+'km_removeDC')
    path_save = os.path.join(PATH, experiment, 'paramC0_FD_PL_R'+str(args.range)+'km_removeDC')
    #path_plots = os.path.join(PATH, experiment, 'plotsC0_FD_PL_R'+str(args.range)+'km')
    #path_save = os.path.join(PATH, experiment, 'paramC0_FD_PL_R'+str(args.range)+'km')
    RMIX = 1.62
    MASK =0.3

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
        online=args.online,
        walk=1,
        ippKm = ipp_km,
        getByBlock = 1,
        nProfileBlocks = N,
    )
    voltage = project.addProcUnit(datatype='VoltageProc', inputId=reader.getId())

    op =  voltage.addOperation(name='setAttribute')
    op.addParameter(name='frequency', value='9345.e6', format='float')

    op = voltage.addOperation(name='ProfileSelector')
    op.addParameter(name='profileRangeList', value='{},{}'.format(conf['usrp_tx']['repetitions_1'], conf['usrp_tx']['repetitions_1']+conf['usrp_tx']['repetitions_2']-1))

    if conf['usrp_tx']['code_type_2']:
        codes = [ c.strip() for c in conf['usrp_tx']['code_2'].split(',')]
        code = []
        for c in codes:
            code.append([int(x) for x in c])
        op = voltage.addOperation(name='Decoder', optype='other')
        op.addParameter(name='code', value=code)
        op.addParameter(name='nCode', value=len(code), format='int')
        op.addParameter(name='nBaud', value=len(code[0]), format='int')

        op = voltage.addOperation(name='CohInt', optype='other') #Minimo integrar 2 perfiles por ser codigo complementario
        op.addParameter(name='n', value=len(code), format='int')
        ncode = len(code)
    else:
        ncode = 1

    op = voltage.addOperation(name='setH0')
    op.addParameter(name='h0', value='-1.68')

    if args.range > 0:
        op = voltage.addOperation(name='selectHeights')
        op.addParameter(name='minIndex', value='0', format='int')
        op.addParameter(name='maxIndex', value=max_index(args.range, sample_rate, ipp), format='int')

    #---------------------------------------NEW PROCESSING -----------------------------------------------------
    procB = project.addProcUnit(datatype='SpectraProc', inputId=voltage.getId())
    procB.addParameter(name='nFFTPoints', value=int(conf['usrp_tx']['repetitions_2'])/2, format='int')
    procB.addParameter(name='nProfiles', value=int(conf['usrp_tx']['repetitions_2'])/2, format='int')

    opObj11 = procB.addOperation(name='removeDC')
    opObj11.addParameter(name='mode', value=2)

    proc= project.addProcUnit(datatype='ParametersProc',inputId=procB.getId())

    opObj10 =  proc.addOperation(name='SpectralMoments')
    opObj10.addParameter(name='wradar',value=True)

    #---------------------------------------NEW PROCESSING -----------------------------------------------------

    opObj10 = proc.addOperation(name="WeatherRadar")
    #opObj10.addParameter(name='variableList',value='Reflectividad,VelocidadRadial,AnchoEspectral')
    opObj10.addParameter(name='tauW',value=(1e-6/sample_rate)*len(code[0]))
    opObj10.addParameter(name='Pt',value=((1e-6/sample_rate)*len(code[0])/ipp)*200)

    # {"latitude": -12.0404828587, "longitude": -75.2147483647, "altitude": 3379.2147483647}

    op = proc.addOperation(name='PedestalInformation')
    op.addParameter(name='path', value=path_ped, format='str')
    op.addParameter(name='interval', value='0.04')
    op.addParameter(name='time_offset', value=time_offset)
    #op.addParameter(name='az_offset', value=-26.2)
    op.addParameter(name='mode', value='PPI')

    for param in parameters:
        op = proc.addOperation(name='Block360')
        op.addParameter(name='attr_data', value='data_param')
        op.addParameter(name='runNextOp', value=True)

        op= proc.addOperation(name='WeatherParamsPlot')
        if args.save: op.addParameter(name='save', value=path_plots, format='str')
        op.addParameter(name='save_period', value=-1)
        op.addParameter(name='show', value=args.show)
        op.addParameter(name='channels', value='0,')
        op.addParameter(name='zmin', value=PARAM[param]['zmin'])
        op.addParameter(name='zmax', value=PARAM[param]['zmax'])
        op.addParameter(name='attr_data', value=param, format='str')
        op.addParameter(name='labels', value=[PARAM[param]['label']])
        op.addParameter(name='save_code', value=param)
        op.addParameter(name='cb_label', value=PARAM[param]['cb_label'])
        op.addParameter(name='colormap', value=PARAM[param]['colormap'])
        op.addParameter(name='bgcolor',value='black')
        op.addParameter(name='snr_threshold',value=0.4)

        if MASK: op.addParameter(name='mask', value=MASK, format='float')

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
                }
            }

        if args.save:
            writer = proc.addOperation(name='HDFWriter')
            writer.addParameter(name='path', value=path_save, format='str')
            writer.addParameter(name='Reset', value=True)
            writer.addParameter(name='setType', value='weather')
            writer.addParameter(name='description', value=json.dumps(desc))
            writer.addParameter(name='blocksPerFile', value='1',format='int')
            writer.addParameter(name='metadataList', value='heightList,data_azi,data_ele,mode_op,latitude,longitude,altitude,heading,radar_name,institution,contact,h0,range_unit')
            writer.addParameter(name='dataList', value='data_param,utctime')
            writer.addParameter(name='weather_var', value=param)
            writer.addParameter(name='mask', value=MASK, format='float')
            # meta
            writer.addParameter(name='latitude', value='-12.040436')
            writer.addParameter(name='longitude', value='-75.295893')
            writer.addParameter(name='altitude', value='3379.2147')
            writer.addParameter(name='heading', value='0')
            writer.addParameter(name='radar_name', value='SOPHy')
            writer.addParameter(name='institution', value='IGP')
            writer.addParameter(name='contact', value='dscipion@igp.gob.pe')
            writer.addParameter(name='created_by', value='Signal Chain (https://pypi.org/project/schainpy/)')
            writer.addParameter(name='range_unit', value='km')

    project.start()



if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Script to process SOPHy data.')
    parser.add_argument('experiment',
                        help='Experiment name')
    parser.add_argument('--parameters', nargs='*', default=['S'],
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
    parser.add_argument('--start_time', default='',
                        help='Set start time.')


    args = parser.parse_args()

    main(args) # Operator#ñ8
