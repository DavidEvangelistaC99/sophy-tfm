#!/usr/bin/python

from schainpy.controller import Project

path ="/home/soporte/Downloads/"

prj = Project()

read_unit = prj.addReadUnit(
    datatype='Spectra',
    path=path,
    startDate='2013/01/01',
    endDate='2013/12/31',
    startTime='00:00:00',
    endTime='23:59:59',
    online=0,
    walk=0
    )

proc_unit = prj.addProcUnit(
    datatype='Spectra',
    inputId=read_unit.getId()
    )


op = proc_unit.addOperation(name='IncohInt')
op.addParameter(name='n', value='2')

op = proc_unit.addOperation(name='selectChannels')
op.addParameter(name='channelList', value='0,1')

op = proc_unit.addOperation(name='selectHeights')
op.addParameter(name='minHei', value='80')
op.addParameter(name='maxHei', value='200')

#op = proc_unit.addOperation(name='removeDC')

op = proc_unit.addOperation(name='SpectraPlot')
op.addParameter(name='wintitle', value='Spectra', format='str')

op = proc_unit.addOperation(name='RTIPlot')
op.addParameter(name='wintitle', value='RTI', format='str')

prj.start()
