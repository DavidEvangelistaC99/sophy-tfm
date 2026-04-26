'''
Created on Jul 9, 2014

@author: roj-idl71
'''
import os
import datetime
import numpy

from schainpy.model.graphics.jroplot_base import Plot, plt


class ScopePlot(Plot):

    '''
       Plot for Scope
    '''

    CODE = 'scope'
    plot_type = 'scatter'

    def setup(self):

        self.xaxis = 'Range (Km)'
        self.nplots = len(self.data.channels)
        self.nrows = int(numpy.ceil(self.nplots/2))
        self.ncols = int(numpy.ceil(self.nplots/self.nrows))
        self.ylabel = 'Intensity [dB]'
        self.titles = ['Channel '+str(self.data.channels[i])+" " for i in self.data.channels]
        self.colorbar = False
        self.width = 6
        self.height = 4

    def update(self, dataOut):

        data = {}
        meta = {
            'nProfiles': dataOut.nProfiles,
            'flagDataAsBlock': dataOut.flagDataAsBlock,
            'profileIndex': dataOut.profileIndex,
        }
        if self.CODE == 'scope':
            data[self.CODE] = dataOut.data
        elif self.CODE == 'pp_power':
            data[self.CODE] = dataOut.dataPP_POWER
        elif self.CODE == 'pp_signal':
            data[self.CODE] = dataOut.dataPP_POW
        elif self.CODE == 'pp_velocity':
            data[self.CODE] = dataOut.dataPP_DOP
        elif self.CODE == 'pp_specwidth':
            data[self.CODE] = dataOut.dataPP_WIDTH

        return data, meta

    def plot_iq(self, x, y, channelIndexList, thisDatetime, wintitle):

        yreal = y[channelIndexList,:].real
        yimag = y[channelIndexList,:].imag
        Maintitle = wintitle + " Scope: %s" %(thisDatetime.strftime("%d-%b-%Y"))
        self.xlabel = "Range (Km)"
        self.ylabel = "Intensity - IQ"

        self.y = yreal
        self.x = x

        self.titles[0] = title

        for i,ax in enumerate(self.axes):
            title = "Channel %d" %(i)
            if ax.firsttime:
                self.xmin = min(x)
                self.xmax = max(x)
                ax.plt_r = ax.plot(x, yreal[i,:], color='b')[0]
                ax.plt_i = ax.plot(x, yimag[i,:], color='r')[0]
            else:
                ax.plt_r.set_data(x, yreal[i,:])
                ax.plt_i.set_data(x, yimag[i,:])
        plt.suptitle(Maintitle)

    def plot_power(self, x, y, channelIndexList, thisDatetime, wintitle):
        y = y[channelIndexList,:] * numpy.conjugate(y[channelIndexList,:])
        yreal = y.real
        yreal = 10*numpy.log10(yreal)
        self.y = yreal
        title = wintitle + " Power: %s" %(thisDatetime.strftime("%d-%b-%Y"))
        self.xlabel = "Range (Km)"
        self.ylabel = "Intensity [dB]"


        self.titles[0] = title

        for i,ax in enumerate(self.axes):
            title = "Channel %d" %(i)
            ychannel = yreal[i,:]

            if ax.firsttime:
                self.xmin = min(x)
                self.xmax = max(x)
                ax.plt_r = ax.plot(x, ychannel)[0]
            else:
                ax.plt_r.set_data(x, ychannel)

    def plot_weatherpower(self, x, y, channelIndexList, thisDatetime, wintitle):


        y      = y[channelIndexList,:]
        yreal  = y.real
        yreal  = 10*numpy.log10(yreal)
        self.y = yreal
        title  = wintitle + " Scope: %s" %(thisDatetime.strftime("%d-%b-%Y %H:%M:%S"))
        self.xlabel = "Range (Km)"
        self.ylabel = "Intensity"
        self.xmin   = min(x)
        self.xmax   = max(x)

        self.titles[0] =title
        for i,ax in enumerate(self.axes):
            title    = "Channel %d" %(i)

            ychannel = yreal[i,:]

            if ax.firsttime:
                ax.plt_r = ax.plot(x, ychannel)[0]
            else:
                #pass
                ax.plt_r.set_data(x, ychannel)

    def plot_weathervelocity(self, x, y, channelIndexList, thisDatetime, wintitle):

        x = x[channelIndexList,:]
        yreal  = y
        self.y = yreal
        title = wintitle + " Scope: %s" %(thisDatetime.strftime("%d-%b-%Y %H:%M:%S"))
        self.xlabel = "Velocity (m/s)"
        self.ylabel = "Range (Km)"
        self.xmin   = numpy.min(x)
        self.xmax   = numpy.max(x)
        self.titles[0] =title
        for i,ax in enumerate(self.axes):
            title    = "Channel %d" %(i)
            xchannel    = x[i,:]
            if ax.firsttime:
                ax.plt_r = ax.plot(xchannel, yreal)[0]
            else:
                #pass
                ax.plt_r.set_data(xchannel, yreal)

    def plot_weatherspecwidth(self, x, y, channelIndexList, thisDatetime, wintitle):

        x = x[channelIndexList,:]
        yreal  = y
        self.y = yreal
        title = wintitle + " Scope: %s" %(thisDatetime.strftime("%d-%b-%Y %H:%M:%S"))
        self.xlabel = "width "
        self.ylabel = "Range (Km)"
        self.xmin   = numpy.min(x)
        self.xmax   = numpy.max(x)
        self.titles[0] =title
        for i,ax in enumerate(self.axes):
            title    = "Channel %d" %(i)
            xchannel    = x[i,:]
            if ax.firsttime:
                ax.plt_r = ax.plot(xchannel, yreal)[0]
            else:
                #pass
                ax.plt_r.set_data(xchannel, yreal)

    def plot(self):
        if self.channels:
            channels = self.channels
        else:
            channels = self.data.channels

        thisDatetime = datetime.datetime.utcfromtimestamp(self.data.times[-1])

        scope = self.data[-1][self.CODE]

        if self.data.flagDataAsBlock:

            for i in range(self.data.nProfiles):

                wintitle1 = " [Profile = %d] " %i
                if self.CODE =="scope":
                    if self.type == "power":
                        self.plot_power(self.data.yrange,
                                        scope[:,i,:],
                                        channels,
                                        thisDatetime,
                                        wintitle1
                                        )

                    if self.type == "iq":
                        self.plot_iq(self.data.yrange,
                                     scope[:,i,:],
                                     channels,
                                     thisDatetime,
                                     wintitle1
                                    )
                if self.CODE=="pp_power":
                    self.plot_weatherpower(self.data.yrange,
                               scope[:,i,:],
                               channels,
                               thisDatetime,
                               wintitle
                               )
                if self.CODE=="pp_signal":
                    self.plot_weatherpower(self.data.yrange,
                               scope[:,i,:],
                               channels,
                               thisDatetime,
                               wintitle
                               )
                if self.CODE=="pp_velocity":
                    self.plot_weathervelocity(scope[:,i,:],
                               self.data.yrange,
                               channels,
                               thisDatetime,
                               wintitle
                               )
                if self.CODE=="pp_spcwidth":
                    self.plot_weatherspecwidth(scope[:,i,:],
                               self.data.yrange,
                               channels,
                               thisDatetime,
                               wintitle
                               )
        else:
            wintitle = " [Profile = %d] " %self.data.profileIndex
            if self.CODE== "scope":
                if self.type == "power":
                     self.plot_power(self.data.yrange,
                                scope,
                                channels,
                                thisDatetime,
                                wintitle
                                )

                if self.type == "iq":
                    self.plot_iq(self.data.yrange,
                                scope,
                                channels,
                                thisDatetime,
                                wintitle
                                )
            if self.CODE=="pp_power":
                self.plot_weatherpower(self.data.yrange,
                                    scope,
                                    channels,
                                    thisDatetime,
                                    wintitle
                                       )
            if self.CODE=="pp_signal":
                self.plot_weatherpower(self.data.yrange,
                                    scope,
                                    channels,
                                    thisDatetime,
                                    wintitle
                                       )
            if self.CODE=="pp_velocity":
                self.plot_weathervelocity(scope,
                                       self.data.yrange,
                                       channels,
                                       thisDatetime,
                                       wintitle
                                       )
            if self.CODE=="pp_specwidth":
                self.plot_weatherspecwidth(scope,
                                       self.data.yrange,
                                       channels,
                                       thisDatetime,
                                       wintitle
                                       )


class PulsepairPowerPlot(ScopePlot):
    '''
    Plot for  P= S+N
    '''

    CODE = 'pp_power'
    plot_type = 'scatter'

class PulsepairVelocityPlot(ScopePlot):
    '''
    Plot for VELOCITY
    '''
    CODE = 'pp_velocity'
    plot_type = 'scatter'

class PulsepairSpecwidthPlot(ScopePlot):
    '''
    Plot for WIDTH
    '''
    CODE = 'pp_specwidth'
    plot_type = 'scatter'

class PulsepairSignalPlot(ScopePlot):
    '''
    Plot for S
    '''

    CODE = 'pp_signal'
    plot_type = 'scatter'

class Spectra2DPlot(Plot):
    '''
    Plot for 2D Spectra data
    Necessary data as Block
    you could use profiles2Block Operation

    Example:
    # opObj11 = volts_proc.addOperation(name='profiles2Block', optype='other')
    # # opObj11.addParameter(name='n', value=10, format='int') 
    # opObj11.addParameter(name='timeInterval', value='2', format='int')

    # opObj12 = volts_proc.addOperation(name='Spectra2DPlot', optype='external')
    '''

    CODE = 'spc'
    colormap = 'jet'
    plot_type = 'pcolor'
    buffering = False
    channelList = []
    elevationList = []
    azimuthList = []

    def setup(self):

        self.nplots = len(self.data.channels)
        self.ncols = int(numpy.sqrt(self.nplots) + 0.9)
        self.nrows = int((1.0 * self.nplots / self.ncols) + 0.9)
        self.height = 3.4 * self.nrows

        self.cb_label = 'dB'
        if self.showprofile:
            self.width = 5.2 * self.ncols
        else:
            self.width = 4.2* self.ncols
        self.plots_adjust.update({'wspace': 0.4, 'hspace':0.4, 'left': 0.1, 'right': 0.9, 'bottom': 0.12})
        self.ylabel = 'Range [km]'


    def update_list(self,dataOut):
        if len(self.channelList) == 0:
            self.channelList = dataOut.channelList
        if len(self.elevationList) == 0:
            self.elevationList = dataOut.elevationList
        if len(self.azimuthList) == 0:
            self.azimuthList = dataOut.azimuthList

    def update(self, dataOut):
        
        self.update_list(dataOut)
        data = {}
        meta = {}


        spectrum = numpy.fft.fftshift(numpy.fft.fft2(dataOut.data, axes=(1,2)))
        z = numpy.abs(spectrum)
        phase = numpy.angle(spectrum)

        z = numpy.where(numpy.isfinite(z), z, numpy.NAN)
        spc = 10*numpy.log10(z)
        dt1 = dataOut.ippSeconds
        dt2 = dataOut.radarControllerHeaderObj.heightResolution/150000
        data['spc'] = spc
        data['phase'] = phase
        f1 = numpy.fft.fftshift(numpy.fft.fftfreq(spectrum.shape[1],d=dt1)/1000)
        f2 =  numpy.fft.fftshift(numpy.fft.fftfreq(spectrum.shape[2],d=dt2)/1000)
        meta['range'] = (f1, f2)

        return data, meta

    def plot(self):
        x = self.data.range[0]
        y = self.data.range[1]
        self.xlabel = "Frequency (kHz)"
        self.ylabel = "Frequency (kHz)"
        

        self.titles = []
        self.y = y

        data = self.data[-1]
        z = data['spc']
        for n, ax in enumerate(self.axes):
            if ax.firsttime:
                self.xmax = self.xmax if self.xmax else numpy.nanmax(x)
                self.xmin = self.xmin if self.xmin else -self.xmax
                self.zmin = self.zmin if self.zmin else numpy.nanmin(z)
                self.zmax = self.zmax if self.zmax else numpy.nanmax(z)
                ax.plt = ax.pcolormesh(x, y, z[n].T,
                                       vmin=self.zmin,
                                       vmax=self.zmax,
                                       cmap=plt.get_cmap(self.colormap)
                                       )

            else:
                ax.plt.set_array(z[n].T.ravel())

            if len(self.azimuthList) > 0 and len(self.elevationList) > 0:
                self.titles.append('CH {}: {:2.1f}elv {:2.1f} az '.format(self.channelList[n], self.elevationList[n], self.azimuthList[n]))
            else:
                self.titles.append('CH {}:  '.format(self.channelList[n]))