# SOPHY PROC script
import os, sys, json, argparse
import datetime
import time

PATH = '/DATA_RM/DATA'
# PATH = '/Users/jespinoza/workspace/data/'

PARAM = {
    'P': {'name': 'dataPP_POWER', 'zmin': 35, 'zmax': 60, 'colormap': 'jet', 'label': 'Power', 'cb_label': 'dB'},
    'V': {'name': 'dataPP_DOP', 'zmin': -20, 'zmax': 20, 'colormap': 'seismic', 'label': 'Velocity', 'cb_label': 'm/s'},
    'RH': {'name': 'RhoHV_R', 'zmin': 0, 'zmax': 1, 'colormap': 'jet', 'label': 'CoeficienteCorrelacion', 'cb_label': '*'},
    'FD': {'name': 'PhiD_P', 'zmin': -180, 'zmax': 180, 'colormap': 'RdBu_r', 'label': 'Fase Diferencial', 'cb_label': 'º'},
    'ZD': {'name': 'Zdb_D', 'zmin': -20, 'zmax': 80, 'colormap': 'viridis', 'label': 'ReflectividadDiferencial', 'cb_label': 'dB'},
    'Z': {'name': 'Zdb', 'zmin': -20, 'zmax': 60, 'colormap': 'viridis', 'label': 'Reflectividad', 'cb_label': 'dB'},
    'W': {'name': 'Sigmav_W', 'zmin': -20, 'zmax': 60, 'colormap': 'viridis', 'label': 'AnchoEspectral', 'cb_label': 'hz'}
}
#Z,ZD 'mm^6/m^3'

PATH = '/home/soporte/Downloads/data_WR_RHI'



def main(args):

    experiment = args.experiment
    fp = open(os.path.join(PATH, experiment, 'experiment.conf'))
    conf = json.loads(fp.read())

    ipp_km = conf['usrp_tx']['ipp']
    ipp = ipp_km * 2 /300000
    samp_rate  = conf['usrp_rx']['sample_rate']

    #axis = ['0' if x=='elevation' else '1' for x in conf['pedestal']['speed']]      # AZIMUTH 1 ELEVACION 0
    axis = ['0' if x=='elevation' else '1' for x in conf['pedestal']['axis']]      # AZIMUTH 1 ELEVACION 0
    speed_axis = conf['pedestal']['speed']
    steeps = conf['pedestal']['table']
    time_offset = args.time_offset
    parameters = args.parameters
    #start_date = experiment.split('@')[1].split('T')[0].replace('-', '/')
    start_date = '2022/04/22'
    end_date = start_date
    #start_time = experiment.split('@')[1].split('T')[1]
    start_time = '00:00:01'
    end_time = '23:59:59'
    max_index  = int(samp_rate*ipp*1e6 * args.range / 60) + int(samp_rate*ipp*1e6 * 1.2 / 60)
    N = int(1/(speed_axis[0]*ipp))                                               # 1 GRADO DE RESOLUCION
    path = os.path.join(PATH, experiment, 'rawdata')
    path_ped = os.path.join(PATH, experiment, 'position')
    path_plots = os.path.join(PATH, experiment, 'plots')
    path_save = os.path.join(PATH, experiment, 'param')

    dBmin = 35
    dBmax = 60
    Vmin = -20
    Vmax = 20

    from schainpy.controller import Project

    project = Project()
    project.setup(id='1', name='Sophy', description='sophy proc')

    reader = project.addReadUnit(datatype='DigitalRFReader',
        path=path,
        startDate=start_date,
        endDate=end_date,
        startTime=start_time,
        endTime=end_time,
        delay=0,
        online=0,
        walk=1,
        ippKm = ipp_km,
        getByBlock = 1,
        nProfileBlocks = N,
    )

    voltage = project.addProcUnit(datatype='VoltageProc', inputId=reader.getId())
    op = voltage.addOperation(name='setH0')
    op.addParameter(name='h0', value='-1.2')

    if args.range > 0:
        op = voltage.addOperation(name='selectHeights')
        op.addParameter(name='minIndex', value='0', format='int')
        op.addParameter(name='maxIndex', value=max_index, format='int')

    op = voltage.addOperation(name='PulsePair_vRF', optype='other')
    op.addParameter(name='n', value=int(N), format='int')

    proc = project.addProcUnit(datatype='ParametersProc', inputId=voltage.getId())

    #-----------------------new--------- variables polarimetricas---------------
    opObj10 = proc.addOperation(name="WeatherRadar")
    opObj10.addParameter(name='variableList',value='Reflectividad,ReflectividadDiferencial,CoeficienteCorrelacion,FaseDiferencial,VelocidadRadial,AnchoEspectral')

    #---------------------------------------------------------------------------
    op = proc.addOperation(name='PedestalInformation')
    op.addParameter(name='path', value=path_ped, format='str')
    op.addParameter(name='interval', value='0.04', format='float')
    op.addParameter(name='time_offset', value=time_offset)

    for param in parameters:
        op = proc.addOperation(name='Block360_vRF4')
        op.addParameter(name='axis', value=','.join(axis))
        op.addParameter(name='attr_data', value=PARAM[param]['name'])

        if axis[0] == '1':
            path_fig = '/PPI-{}km'.format(args.range)
            op= proc.addOperation(name='Weather_vRF_Plot')
            op.addParameter(name='save', value=path_plots+path_fig, format='str')
            op.addParameter(name='save_period', value=-1)
            op.addParameter(name='show', value=args.show)
            op.addParameter(name='channels', value='1,')
            op.addParameter(name='zmin', value=PARAM[param]['zmin'])
            op.addParameter(name='zmax', value=PARAM[param]['zmax'])
            op.addParameter(name='attr_data', value=PARAM[param]['name'], format='str')
            op.addParameter(name='labels', value=[PARAM[param]['label']])
            op.addParameter(name='save_code', value=param)
            op.addParameter(name='cb_label', value=PARAM[param]['cb_label'])
            op.addParameter(name='colormap', value=PARAM[param]['colormap'])
        if axis[0] == '0':
            path_fig = '/RHI{}km'.format(args.range)
            op= proc.addOperation(name='WeatherRHI_vRF4_Plot')
            op.addParameter(name='save', value=path_plots+path_fig, format='str')
            op.addParameter(name='save_period', value=-1)
            op.addParameter(name='show', value=args.show)
            op.addParameter(name='channels', value='(1,)')
            op.addParameter(name='zmin', value=PARAM[param]['zmin'])
            op.addParameter(name='zmax', value=PARAM[param]['zmax'])
            op.addParameter(name='attr_data', value=PARAM[param]['name'], format='str')
            op.addParameter(name='labels', value=[PARAM[param]['label']])
            op.addParameter(name='save_code', value=param)
            op.addParameter(name='cb_label', value=PARAM[param]['cb_label'])
            op.addParameter(name='colormap', value=PARAM[param]['colormap'])

        if args.save:
            opObj10 = proc.addOperation(name='HDFWriter')
            opObj10.addParameter(name='path',value=path_save, format='str')
            opObj10.addParameter(name='Reset',value=True)
            opObj10.addParameter(name='blocksPerFile',value='1',format='int')
            opObj10.addParameter(name='metadataList',value='heightList,data_azi,data_ele')
            opObj10.addParameter(name='dataList',value='dataPP_POWER,utctime')


    project.start()

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Script to process SOPHy data.')
    parser.add_argument('experiment',
                        help='Experiment name')
    parser.add_argument('--parameters', nargs='*', default=['P'],
                        help='Variables to process: P, Z, V')
    parser.add_argument('--time_offset', default=0,
                        help='Fix time offset')
    parser.add_argument('--range', default=0, type=int,
                        help='Max range to plot')
    parser.add_argument('--save', action='store_true',
                        help='Create output files')
    parser.add_argument('--show', action='store_true',
                        help='Show matplotlib plot.')

    args = parser.parse_args()
    print (args)
    main(args)
