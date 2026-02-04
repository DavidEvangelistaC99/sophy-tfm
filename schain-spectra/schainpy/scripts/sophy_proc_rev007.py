import os,sys,json
import datetime
import time
import argparse

from schainpy.controller import Project
'''
NOTA:
Este script de prueba.
- Unidad del lectura 'HDFReader'.
- Unidad de procesamiento ParametersProc
'''
PATH  = "/home/soporte/Documents/EVENTO/HYO_PM@2022-06-09T15-05-12/paramC0N36.0/2022-06-09T18-00-00/"
#PATH  = "/home/soporte/Documents/EVENTO/HYO_PM@2022-06-09T15-05-12/param/2022-06-09T18-00-00/"

#PATH = "/home/soporte/Documents/EVENTO/HYO_PM@2022-06-09T15-05-12/paramC0N36.0/2022-06-09T19-00-00/"
#PATH = "/home/soporte/Documents/EVENTO/HYO_PM@2022-05-31T12-00-17/paramC0N36.0/2022-05-31T16-00-00/"
path  = PATH
PARAM = {
    'S': {'zmin': -45, 'zmax': -25, 'colormap': 'jet', 'label': 'Power', 'wrname': 'power','cb_label': 'dBm', 'ch':0},
    'SNR': {'zmin': -40, 'zmax': -20, 'colormap': 'jet', 'label': 'SNR', 'wrname': 'snr','cb_label': 'dB', 'ch':0},
    'V': {'zmin': -12, 'zmax': 12, 'colormap': 'sophy_v', 'label': 'Velocity', 'wrname': 'velocity', 'cb_label': 'm/s', 'ch':0},
    'R': {'zmin': 0,   'zmax': 1,  'colormap': 'jet',    'label': 'RhoHV', 'wrname':'rhoHV', 'cb_label': '*',  'ch':0},
    'P': {'zmin': -180,'zmax': 180,'colormap': 'RdBu_r', 'label': 'PhiDP', 'wrname':'phiDP' , 'cb_label': 'º',  'ch':0},
    'D': {'zmin': -30, 'zmax': 80, 'colormap': 'sophy_r','label': 'ZDR','wrname':'differential_reflectivity' , 'cb_label': 'dBz','ch':0},
    'Z':  {'zmin': -30, 'zmax': 80, 'colormap': 'sophy_r','label': 'Reflectivity ',  'wrname':'reflectivity', 'cb_label': 'dBz','ch':0},
    'W':  {'zmin': 0, 'zmax': 15, 'colormap': 'sophy_w','label': 'Spectral Width', 'wrname':'spectral_width', 'cb_label': 'm/s', 'ch':0}
    }

def main(args):
    #filefmt="******%Y%m%d*%H%M%S*******"
    #filefmt="SOPHY_20220609_184620_E8.0_Z"
    parameters = args.parameters
    grado      = args.grado
    MASK = None

    for param in parameters:
        filefmt   ="******%Y%m%d*%H%M%S*******"
        filter= "_E"+str(grado)+".0_"+param
        variable = 'Data/'+PARAM[param]['wrname']+'/H'
        desc = {
                'Data': {
                    'data_param': [variable],
                    'utctime'   : 'Data/time'
                },
                 'Metadata': {
                    'heightList': 'Metadata/range',
                    'data_azi'  : 'Metadata/azimuth',
                    'data_ele'  : 'Metadata/elevation',
                    'mode_op'   : 'Metadata/scan_type',
                    'h0'        : 'Metadata/range_correction',
                }
            }

        project   = Project()

        project.setup(id='10',name='Test Simulator',description=desc)

        readUnitConfObj = project.addReadUnit(datatype='HDFReader',
                                                    path=path,
                                                    startDate="2022/01/01",   #"2020/01/01",#today,
                                                    endDate= "2022/12/01",  #"2020/12/30",#today,
                                                    startTime='00:00:00',
                                                    endTime='23:59:59',
                                                    delay=0,
                                                    #set=0,
                                                    online=0,
                                                    walk=0,
                                                    filefmt=filefmt,
                                                    filter=filter,
                                                    dparam= 1,
                                                    description= json.dumps(desc))#1

        proc1 = project.addProcUnit(datatype='ParametersProc',inputId=readUnitConfObj.getId())

        if args.plot:
            print("plotea")
            op= proc1.addOperation(name='WeatherParamsPlot')
            if args.save:
                op.addParameter(name='save', value=path_plots, format='str')
            op.addParameter(name='save_period', value=-1)
            op.addParameter(name='show', value=args.show)
            op.addParameter(name='channels', value='0,')
            op.addParameter(name='zmin', value=PARAM[param]['zmin'], format='int')
            op.addParameter(name='zmax', value=PARAM[param]['zmax'], format='int')
            op.addParameter(name='attr_data', value=param, format='str')
            op.addParameter(name='labels', value=[PARAM[param]['label']])
            op.addParameter(name='save_code', value=param)
            op.addParameter(name='cb_label', value=PARAM[param]['cb_label'])
            op.addParameter(name='colormap', value=PARAM[param]['colormap'])
            op.addParameter(name='bgcolor', value='black')
            if MASK: op.addParameter(name='mask', value=MASK, format='float')
            if args.server:
                op.addParameter(name='server', value='0.0.0.0:4444')
                op.addParameter(name='exp_code', value='400')
        project.start()

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Script to process SOPHy data.')
    parser.add_argument('--parameters', nargs='*', default=['S'],
                        help='Variables to process: P, Z, V ,W')
    parser.add_argument('--grado', default=2,
                        help='Angle in Elev to plot')
    parser.add_argument('--save', default=0,
                        help='Save plot')
    parser.add_argument('--range', default=0, type=float,
                        help='Max range to plot')
    parser.add_argument('--plot', action='store_true',
                        help='Create plot files')
    parser.add_argument('--show', action='store_true',
                        help='Show matplotlib plot.')
    parser.add_argument('--server', action='store_true',
                        help='Send to realtime')
    args = parser.parse_args()

    main(args)
