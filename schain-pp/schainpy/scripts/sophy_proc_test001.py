# SOPHY PROC script
import os, sys, json, argparse
import datetime
import time

PATH = '/DATA_RM/DATA'
# PATH = '/Users/jespinoza/workspace/data/'
#PATH = '/home/roberto/DATA/data_WR_RHI/RHI'
PATH = '/home/soporte/Downloads/data_WR_RHI'


PARAM = {
    'P':  {'name': 'dataPP_POWER','zmin': 35,  'zmax': 60, 'colormap': 'jet',    'label': 'Power',              'wrname':'Pow', 'cb_label': 'dB', 'ch':1},
    'V':  {'name': 'dataPP_DOP',  'zmin': -20, 'zmax': 20, 'colormap': 'seismic','label': 'Velocity',           'wrname':'Dop', 'cb_label': 'm/s','ch':1},
    'RH': {'name': 'RhoHV_R',     'zmin': 0,   'zmax': 1,  'colormap': 'jet',    'label': 'Coef.Correlacion',   'wrname':'R',   'cb_label': '*',  'ch':0},
    'FD': {'name': 'PhiD_P',      'zmin': -180,'zmax': 180,'colormap': 'RdBu_r', 'label': 'Fase Diferencial',   'wrname':'P' ,  'cb_label': 'º',  'ch':0},
    'ZD': {'name': 'Zdb_D',       'zmin': -20, 'zmax': 80, 'colormap': 'viridis','label': 'Reflect.Diferencial','wrname':'D' ,  'cb_label': 'dBz','ch':0},
    'Z':  {'name': 'Zdb',         'zmin': -20, 'zmax': 60, 'colormap': 'viridis','label': 'Reflectividad',      'wrname':'Z',   'cb_label': 'dBz','ch':1},
    'W':  {'name': 'Sigmav_W',    'zmin': -20, 'zmax': 60, 'colormap': 'viridis','label': 'AnchoEspectral',     'wrname':'S',   'cb_label': 'hz', 'ch':1}
}


#---------------------SIGNAL CHAIN ------------------------------------
# Definido por el usuario puede ser modificado solo se necesita definir. Ejemplo
'''
desc_wr= {
    'Data': {
        'dataPP_POW': 'Power',
        'utctime': 'Time',
        'azimuth': 'az',
        'elevation':'el'
    },
    'Metadata': {
        'heightList': 'range',
        'channelList': 'Channels'
    }
}
'''

def main(args):

    experiment = args.experiment
    fp = open(os.path.join(PATH, experiment, 'experiment.conf'))
    conf = json.loads(fp.read())

    ipp_km = conf['usrp_tx']['ipp']
    ipp = ipp_km * 2 /300000
    samp_rate  = conf['usrp_rx']['sample_rate']
    axis = ['0' if x=='elevation' else '1' for x in conf['pedestal']['speed']]      # AZIMUTH 1 ELEVACION 0
    speed_axis = conf['pedestal']['speed']
    steeps = conf['pedestal']['table']
    time_offset = args.time_offset
    parameters = args.parameters
    #start_date = experiment.split('@')[1].split('T')[0].replace('-', '/')
    start_date = '2022/04/22'
    end_date = start_date
    #start_time = experiment.split('@')[1].split('T')[1]
    start_time ='17:42:55'
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



    op = proc.addOperation(name='PedestalInformation')
    op.addParameter(name='path', value=path_ped, format='str')
    op.addParameter(name='interval', value='0.04', format='float')
    op.addParameter(name='time_offset', value=time_offset)
    #op.addParameter(name='axis', value=','.join(axis)) #Preguntar en pedestal si todos los elementos
                                                       #de aqui son iguales, si lo fueran, que considere
                                                       #el primero dato como el modo (PPI o RHI) y que ya
                                               #no pregunte por el modo porque este no cambia

    for param in parameters:
        op = proc.addOperation(name='Block360_vRF4')
        #op.addParameter(name='axis', value=','.join(axis))
        op.addParameter(name='runNextOp', value=True)
        op.addParameter(name='attr_data', value=PARAM[param]['name'])

        path_fig = '/AUTO{}km'.format(args.range)
        op = proc.addOperation(name='WeatherParamsPlot')
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
            desc_wr= {
                'Data': {
                    PARAM[param]['name']: PARAM[param]['wrname'],#PARAM[param]['name']: {PARAM[param]['wrname']:['P0','P1']},
                    'utctime': 'Time'
                },
                'Metadata': {
                    'heightList': 'range',
                    'channelList': 'Channels',
                    'data_azi': 'azimuth',
                    'data_ele': 'elevation'
                }
            }
            opObj10 = proc.addOperation(name='HDFWriter')
            opObj10.addParameter(name='path',value=path_save, format='str')
            opObj10.addParameter(name='Reset',value=True)
            opObj10.addParameter(name='setType',value='weather')
            opObj10.addParameter(name='blocksPerFile',value='1',format='int')
            #opObj10.addParameter(name='channel',value=PARAM[param]['ch'],format='int')
            opObj10.addParameter(name='metadataList',value='heightList,channelList,Typename,Datatype,Scantype,Latitude,Longitud,Heading,Waveform,PRF,CreatedBy,ContactInformation,data_azi,data_ele')
            opObj10.addParameter(name='Typename', value=PARAM[param]['label'])
            opObj10.addParameter(name='Datatype', value='RadialSet')
            opObj10.addParameter(name='Scantype', value='PPI')
            opObj10.addParameter(name='Latitude', value='-11.96')
            opObj10.addParameter(name='Longitud', value='-76.54')
            opObj10.addParameter(name='Heading', value='293')
            opObj10.addParameter(name='Height', value='293')
            opObj10.addParameter(name='Waveform', value='OFM')
            opObj10.addParameter(name='PRF', value='2500')
            opObj10.addParameter(name='CreatedBy', value='WeatherRadarJROTeam')
            opObj10.addParameter(name='ContactInformation', value='dscipion@igp.gob.pe')
            opObj10.addParameter(name='dataList',value=','.join([PARAM[param]['name'],'utctime']))
            opObj10.addParameter(name='description',value=json.dumps(desc_wr))

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
