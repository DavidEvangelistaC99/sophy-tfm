#!/usr/bin/python

from schainpy.controller import Project

path ="/home/soporte/Downloads/"

prj = Project()

read_unit = prj.addReadUnit(
    datatype='Voltage',
    path=path,
    startDate='2015/01/01',
    endDate='2015/12/31',
    startTime='00:00:00',
    endTime='23:59:59',
    online=0,
    walk=0
    )

proc_unit1 = prj.addProcUnit(
    datatype='Voltage',
    inputId=read_unit.getId()
    )

#op = proc_unit1.addOperation(name='ProfileSelector')
#op.addParameter( name='rangeList', value="(0,19),(100,119)")

op = proc_unit1.addOperation(name='MyAverage')
op.addParameter(name='n', value='10')

#op = proc_unit1.addOperation(name='CohInt')
#op.addParameter(name='n', value='10')

#op = proc_unit1.addOperation(name='Decoder')
#op.addParameter(name='times', value='10')


op = proc_unit1.addOperation(name='ScopePlot')
op.addParameter(name='wintitle', value='Scope', format='str')

'''
proc_unit2 = prj.addProcUnit(
    datatype='Spectra',
    inputId=proc_unit1.getId()
    )
proc_unit2.addParameter(name='nFFTPoints', value='64')


op = proc_unit2.addOperation(name='SpectraPlot')
op.addParameter(name='wintitle', value='Spectra', format='str')

op = proc_unit2.addOperation(name='RTIPlot')
op.addParameter(name='wintitle', value='RTI', format='str')
'''
prj.start()
