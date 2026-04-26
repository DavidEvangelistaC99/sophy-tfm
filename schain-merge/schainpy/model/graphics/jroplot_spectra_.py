# Copyright (c) 2012-2021 Jicamarca Radio Observatory
# All rights reserved.
#
# Distributed under the terms of the BSD 3-clause license.
"""Classes to plot Spectra data

"""

import os
import numpy
import datetime

from schainpy.model.graphics.jroplot_base import Plot, plt, log
from itertools import combinations
from matplotlib.ticker import LinearLocator

from schainpy.model.utils.BField import BField
from scipy.interpolate import splrep
from scipy.interpolate import splev

from matplotlib import __version__ as plt_version

if plt_version >='3.3.4':
    EXTRA_POINTS = 0
else:
    EXTRA_POINTS = 1
class SpectraPlot(Plot):
    '''
    Plot for Spectra data
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
        norm = dataOut.nProfiles * dataOut.max_nIncohInt * dataOut.nCohInt  * dataOut.windowOfFilter
        if dataOut.type == "Parameters":
            noise = 10*numpy.log10(dataOut.getNoise()/dataOut.normFactor)
            spc = 10*numpy.log10(dataOut.data_spc/(dataOut.nProfiles))
        else:
            noise = 10*numpy.log10(dataOut.getNoise()/norm)

            z = numpy.zeros((dataOut.nChannels, dataOut.nFFTPoints, dataOut.nHeights))
            for ch in range(dataOut.nChannels):
                if hasattr(dataOut.normFactor,'ndim'):
                    if dataOut.normFactor.ndim > 1:
                        z[ch] = (numpy.divide(dataOut.data_spc[ch],dataOut.normFactor[ch]))

                    else:
                        z[ch] = (numpy.divide(dataOut.data_spc[ch],dataOut.normFactor))
                else:
                    z[ch] = (numpy.divide(dataOut.data_spc[ch],dataOut.normFactor))

            z = numpy.where(numpy.isfinite(z), z, numpy.NAN)
            spc = 10*numpy.log10(z)

        data['spc'] = spc
        data['rti'] = spc.mean(axis=1)
        data['noise'] = noise
        meta['xrange'] = (dataOut.getFreqRange(EXTRA_POINTS)/1000., dataOut.getAcfRange(EXTRA_POINTS), dataOut.getVelRange(EXTRA_POINTS))
        if self.CODE == 'spc_moments':
            data['moments'] = dataOut.moments

        return data, meta

    def plot(self):

        if self.xaxis == "frequency":
            x = self.data.xrange[0]
            self.xlabel = "Frequency (kHz)"
        elif self.xaxis == "time":
            x = self.data.xrange[1]
            self.xlabel = "Time (ms)"
        else:
            x = self.data.xrange[2]
            self.xlabel = "Velocity (m/s)"

        if (self.CODE == 'spc_moments') | (self.CODE == 'gaussian_fit'):
            x = self.data.xrange[2]
            self.xlabel = "Velocity (m/s)"

        self.titles = []

        y = self.data.yrange
        self.y = y

        data = self.data[-1]
        z = data['spc']

        for n, ax in enumerate(self.axes):
            noise = self.data['noise'][n][0]
            # noise = data['noise'][n]

            if self.CODE == 'spc_moments':
                mean = data['moments'][n, 1]
            if self.CODE == 'gaussian_fit':
                gau0 = data['gaussfit'][n][2,:,0]
                gau1 = data['gaussfit'][n][2,:,1]
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

                if self.showprofile:
                    ax.plt_profile = self.pf_axes[n].plot(
                        data['rti'][n], y)[0]
                    ax.plt_noise = self.pf_axes[n].plot(numpy.repeat(noise, len(y)), y,
                                                        color="k", linestyle="dashed", lw=1)[0]
                if self.CODE == 'spc_moments':
                    ax.plt_mean = ax.plot(mean, y, color='k', lw=1)[0]
                if self.CODE == 'gaussian_fit':
                    ax.plt_gau0 = ax.plot(gau0, y, color='r', lw=1)[0]
                    ax.plt_gau1 = ax.plot(gau1, y, color='y', lw=1)[0]
            else:
                ax.plt.set_array(z[n].T.ravel())
                if self.showprofile:
                    ax.plt_profile.set_data(data['rti'][n], y)
                    ax.plt_noise.set_data(numpy.repeat(noise, len(y)), y)
                if self.CODE == 'spc_moments':
                    ax.plt_mean.set_data(mean, y)
                if self.CODE == 'gaussian_fit':
                    ax.plt_gau0.set_data(gau0, y)
                    ax.plt_gau1.set_data(gau1, y)
            if len(self.azimuthList) > 0 and len(self.elevationList) > 0:
                self.titles.append('CH {}: {:2.1f}elv {:2.1f}az {:3.2f}dB'.format(self.channelList[n], noise, self.elevationList[n], self.azimuthList[n]))
            else:
                self.titles.append('CH {}:  {:3.2f}dB'.format(self.channelList[n], noise))

class SpectraObliquePlot(Plot):
    '''
    Plot for Spectra data
    '''

    CODE = 'spc_oblique'
    colormap = 'jet'
    plot_type = 'pcolor'

    def setup(self):
        self.xaxis = "oblique"
        self.nplots = len(self.data.channels)
        self.ncols = int(numpy.sqrt(self.nplots) + 0.9)
        self.nrows = int((1.0 * self.nplots / self.ncols) + 0.9)
        self.height = 2.6 * self.nrows
        self.cb_label = 'dB'
        if self.showprofile:
            self.width = 4 * self.ncols
        else:
            self.width = 3.5 * self.ncols
        self.plots_adjust.update({'wspace': 0.8, 'hspace':0.2, 'left': 0.2, 'right': 0.9, 'bottom': 0.18})
        self.ylabel = 'Range [km]'

    def update(self, dataOut):

        data = {}
        meta = {}

        spc = 10*numpy.log10(dataOut.data_spc/dataOut.normFactor)
        data['spc'] = spc
        data['rti'] = dataOut.getPower()
        data['noise'] = 10*numpy.log10(dataOut.getNoise()/dataOut.normFactor)
        meta['xrange'] = (dataOut.getFreqRange(1)/1000., dataOut.getAcfRange(1), dataOut.getVelRange(1))

        data['shift1'] = dataOut.Dop_EEJ_T1[0]
        data['shift2'] = dataOut.Dop_EEJ_T2[0]
        data['max_val_2'] = dataOut.Oblique_params[0,-1,:]
        data['shift1_error'] = dataOut.Err_Dop_EEJ_T1[0]
        data['shift2_error'] = dataOut.Err_Dop_EEJ_T2[0]

        return data, meta

    def plot(self):

        if self.xaxis == "frequency":
            x = self.data.xrange[0]
            self.xlabel = "Frequency (kHz)"
        elif self.xaxis == "time":
            x = self.data.xrange[1]
            self.xlabel = "Time (ms)"
        else:
            x = self.data.xrange[2]
            self.xlabel = "Velocity (m/s)"

        self.titles = []

        y = self.data.yrange
        self.y = y

        data = self.data[-1]
        z = data['spc']

        for n, ax in enumerate(self.axes):
            noise = self.data['noise'][n][-1]
            shift1 = data['shift1']
            shift2 = data['shift2']
            max_val_2 = data['max_val_2']
            err1 = data['shift1_error']
            err2 = data['shift2_error']
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

                if self.showprofile:
                    ax.plt_profile = self.pf_axes[n].plot(
                        self.data['rti'][n][-1], y)[0]
                    ax.plt_noise = self.pf_axes[n].plot(numpy.repeat(noise, len(y)), y,
                                                        color="k", linestyle="dashed", lw=1)[0]

                self.ploterr1 = ax.errorbar(shift1, y, xerr=err1, fmt='k^', elinewidth=2.2, marker='o', linestyle='None',markersize=2.5,capsize=0.3,markeredgewidth=0.2)
                self.ploterr2 = ax.errorbar(shift2, y, xerr=err2, fmt='m^',elinewidth=2.2,marker='o',linestyle='None',markersize=2.5,capsize=0.3,markeredgewidth=0.2)
                self.ploterr3 = ax.errorbar(max_val_2, y, xerr=0, fmt='g^',elinewidth=2.2,marker='o',linestyle='None',markersize=2.5,capsize=0.3,markeredgewidth=0.2)

            else:
                self.ploterr1.remove()
                self.ploterr2.remove()
                self.ploterr3.remove()
                ax.plt.set_array(z[n].T.ravel())
                if self.showprofile:
                    ax.plt_profile.set_data(self.data['rti'][n][-1], y)
                    ax.plt_noise.set_data(numpy.repeat(noise, len(y)), y)
                self.ploterr1 = ax.errorbar(shift1, y, xerr=err1, fmt='k^', elinewidth=2.2, marker='o', linestyle='None',markersize=2.5,capsize=0.3,markeredgewidth=0.2)
                self.ploterr2 = ax.errorbar(shift2, y, xerr=err2, fmt='m^',elinewidth=2.2,marker='o',linestyle='None',markersize=2.5,capsize=0.3,markeredgewidth=0.2)
                self.ploterr3 = ax.errorbar(max_val_2, y, xerr=0, fmt='g^',elinewidth=2.2,marker='o',linestyle='None',markersize=2.5,capsize=0.3,markeredgewidth=0.2)

            self.titles.append('CH {}: {:3.2f}dB'.format(n, noise))


class CrossSpectraPlot(Plot):

    CODE = 'cspc'
    colormap = 'jet'
    plot_type = 'pcolor'
    zmin_coh = None
    zmax_coh = None
    zmin_phase = None
    zmax_phase = None
    realChannels = None
    crossPairs = None

    def setup(self):

        self.ncols = 4
        self.nplots = len(self.data.pairs) * 2
        self.nrows = int((1.0 * self.nplots / self.ncols) + 0.9)
        self.width = 3.1 * self.ncols
        self.height = 2.6 * self.nrows
        self.ylabel = 'Range [km]'
        self.showprofile = False
        self.plots_adjust.update({'left': 0.08, 'right': 0.92, 'wspace': 0.5, 'hspace':0.4, 'top':0.95, 'bottom': 0.08})

    def update(self, dataOut):

        data = {}
        meta = {}

        spc = dataOut.data_spc
        cspc = dataOut.data_cspc
        meta['xrange'] = (dataOut.getFreqRange(EXTRA_POINTS)/1000., dataOut.getAcfRange(EXTRA_POINTS), dataOut.getVelRange(EXTRA_POINTS))
        rawPairs = list(combinations(list(range(dataOut.nChannels)), 2))
        meta['pairs'] = rawPairs
        if self.crossPairs == None:
            self.crossPairs = dataOut.pairsList
        tmp = []

        for n, pair in enumerate(meta['pairs']):
            out = cspc[n] / numpy.sqrt(spc[pair[0]] * spc[pair[1]])
            coh = numpy.abs(out)
            phase = numpy.arctan2(out.imag, out.real) * 180 / numpy.pi
            tmp.append(coh)
            tmp.append(phase)

        data['cspc'] = numpy.array(tmp)

        return data, meta

    def plot(self):

        if self.xaxis == "frequency":
            x = self.data.xrange[0]
            self.xlabel = "Frequency (kHz)"
        elif self.xaxis == "time":
            x = self.data.xrange[1]
            self.xlabel = "Time (ms)"
        else:
            x = self.data.xrange[2]
            self.xlabel = "Velocity (m/s)"

        self.titles = []

        y = self.data.yrange
        self.y = y

        data = self.data[-1]
        cspc = data['cspc']

        for n in range(len(self.data.pairs)):
            pair = self.crossPairs[n]
            coh = cspc[n*2]
            phase = cspc[n*2+1]
            ax = self.axes[2 * n]
            if ax.firsttime:
                ax.plt = ax.pcolormesh(x, y, coh.T,
                                       vmin=self.zmin_coh,
                                       vmax=self.zmax_coh,
                                       cmap=plt.get_cmap(self.colormap_coh)
                                       )
            else:
                ax.plt.set_array(coh.T.ravel())
            self.titles.append(
                'Coherence Ch{} * Ch{}'.format(pair[0], pair[1]))

            ax = self.axes[2 * n + 1]
            if ax.firsttime:
                ax.plt = ax.pcolormesh(x, y, phase.T,
                                       vmin=-180,
                                       vmax=180,
                                       cmap=plt.get_cmap(self.colormap_phase)
                                       )
            else:
                ax.plt.set_array(phase.T.ravel())
            self.titles.append('Phase CH{} * CH{}'.format(pair[0], pair[1]))


class CrossSpectra4Plot(Plot):

    CODE = 'cspc'
    colormap = 'jet'
    plot_type = 'pcolor'
    zmin_coh = None
    zmax_coh = None
    zmin_phase = None
    zmax_phase = None

    def setup(self):

        self.ncols = 4
        self.nrows = len(self.data.pairs)
        self.nplots = self.nrows * 4
        self.width = 3.1 * self.ncols
        self.height = 5 * self.nrows
        self.ylabel = 'Range [km]'
        self.showprofile = False
        self.plots_adjust.update({'left': 0.08, 'right': 0.92, 'wspace': 0.5, 'hspace':0.4, 'top':0.95, 'bottom': 0.08})

    def plot(self):

        if self.xaxis == "frequency":
            x = self.data.xrange[0]
            self.xlabel = "Frequency (kHz)"
        elif self.xaxis == "time":
            x = self.data.xrange[1]
            self.xlabel = "Time (ms)"
        else:
            x = self.data.xrange[2]
            self.xlabel = "Velocity (m/s)"

        self.titles = []


        y = self.data.heights
        self.y = y
        nspc = self.data['spc']
        spc = self.data['cspc'][0]
        cspc = self.data['cspc'][1]

        for n in range(self.nrows):
            noise = self.data['noise'][:,-1]
            pair = self.data.pairs[n]

            ax = self.axes[4 * n]
            if ax.firsttime:
                self.xmax = self.xmax if self.xmax else numpy.nanmax(x)
                self.xmin = self.xmin if self.xmin else -self.xmax
                self.zmin = self.zmin if self.zmin else numpy.nanmin(nspc)
                self.zmax = self.zmax if self.zmax else numpy.nanmax(nspc)
                ax.plt = ax.pcolormesh(x , y , nspc[pair[0]].T,
                                       vmin=self.zmin,
                                       vmax=self.zmax,
                                       cmap=plt.get_cmap(self.colormap)
                                       )
            else:

                ax.plt.set_array(nspc[pair[0]].T.ravel())
            self.titles.append('CH {}: {:3.2f}dB'.format(pair[0], noise[pair[0]]))

            ax = self.axes[4 * n + 1]

            if ax.firsttime:
                ax.plt = ax.pcolormesh(x , y, numpy.flip(nspc[pair[1]],axis=0).T,
                                       vmin=self.zmin,
                                       vmax=self.zmax,
                                       cmap=plt.get_cmap(self.colormap)
                                       )
            else:

                ax.plt.set_array(numpy.flip(nspc[pair[1]],axis=0).T.ravel())
            self.titles.append('CH {}: {:3.2f}dB'.format(pair[1], noise[pair[1]]))

            out = cspc[n] / numpy.sqrt(spc[pair[0]] * spc[pair[1]])
            coh = numpy.abs(out)
            phase = numpy.arctan2(out.imag, out.real) * 180 / numpy.pi

            ax = self.axes[4 * n + 2]
            if ax.firsttime:
                ax.plt = ax.pcolormesh(x, y, numpy.flip(coh,axis=0).T,
                                       vmin=0,
                                       vmax=1,
                                       cmap=plt.get_cmap(self.colormap_coh)
                                       )
            else:
                ax.plt.set_array(numpy.flip(coh,axis=0).T.ravel())
            self.titles.append(
                'Coherence Ch{} * Ch{}'.format(pair[0], pair[1]))

            ax = self.axes[4 * n + 3]
            if ax.firsttime:
                ax.plt = ax.pcolormesh(x, y, numpy.flip(phase,axis=0).T,
                                       vmin=-180,
                                       vmax=180,
                                       cmap=plt.get_cmap(self.colormap_phase)
                                       )
            else:
                ax.plt.set_array(numpy.flip(phase,axis=0).T.ravel())
            self.titles.append('Phase CH{} * CH{}'.format(pair[0], pair[1]))


class CrossSpectra2Plot(Plot):

    CODE = 'cspc'
    colormap = 'jet'
    plot_type = 'pcolor'
    zmin_coh = None
    zmax_coh = None
    zmin_phase = None
    zmax_phase = None

    def setup(self):

        self.ncols = 1
        self.nrows = len(self.data.pairs)
        self.nplots = self.nrows * 1
        self.width = 3.1 * self.ncols
        self.height = 5 * self.nrows
        self.ylabel = 'Range [km]'
        self.showprofile = False
        self.plots_adjust.update({'left': 0.22, 'right': .90, 'wspace': 0.5, 'hspace':0.4, 'top':0.95, 'bottom': 0.08})

    def plot(self):

        if self.xaxis == "frequency":
            x = self.data.xrange[0]
            self.xlabel = "Frequency (kHz)"
        elif self.xaxis == "time":
            x = self.data.xrange[1]
            self.xlabel = "Time (ms)"
        else:
            x = self.data.xrange[2]
            self.xlabel = "Velocity (m/s)"

        self.titles = []


        y = self.data.heights
        self.y = y
        cspc = self.data['cspc'][1]

        for n in range(self.nrows):
            noise = self.data['noise'][:,-1]
            pair = self.data.pairs[n]
            out = cspc[n]
            cross = numpy.abs(out)
            z = cross/self.data.nFactor
            cross = 10*numpy.log10(z)

            ax = self.axes[1 * n]
            if ax.firsttime:
                self.xmax = self.xmax if self.xmax else numpy.nanmax(x)
                self.xmin = self.xmin if self.xmin else -self.xmax
                self.zmin = self.zmin if self.zmin else numpy.nanmin(cross)
                self.zmax = self.zmax if self.zmax else numpy.nanmax(cross)
                ax.plt = ax.pcolormesh(x, y, cross.T,
                                       vmin=self.zmin,
                                       vmax=self.zmax,
                                       cmap=plt.get_cmap(self.colormap)
                                       )
            else:
                ax.plt.set_array(cross.T.ravel())
            self.titles.append(
                'Cross Spectra Power Ch{} * Ch{}'.format(pair[0], pair[1]))


class CrossSpectra3Plot(Plot):

    CODE = 'cspc'
    colormap = 'jet'
    plot_type = 'pcolor'
    zmin_coh = None
    zmax_coh = None
    zmin_phase = None
    zmax_phase = None

    def setup(self):

        self.ncols = 3
        self.nrows = len(self.data.pairs)
        self.nplots = self.nrows * 3
        self.width = 3.1 * self.ncols
        self.height = 5 * self.nrows
        self.ylabel = 'Range [km]'
        self.showprofile = False
        self.plots_adjust.update({'left': 0.22, 'right': .90, 'wspace': 0.5, 'hspace':0.4, 'top':0.95, 'bottom': 0.08})

    def plot(self):

        if self.xaxis == "frequency":
            x = self.data.xrange[0]
            self.xlabel = "Frequency (kHz)"
        elif self.xaxis == "time":
            x = self.data.xrange[1]
            self.xlabel = "Time (ms)"
        else:
            x = self.data.xrange[2]
            self.xlabel = "Velocity (m/s)"

        self.titles = []


        y = self.data.heights
        self.y = y

        cspc = self.data['cspc'][1]

        for n in range(self.nrows):
            noise = self.data['noise'][:,-1]
            pair = self.data.pairs[n]
            out = cspc[n]

            cross = numpy.abs(out)
            z = cross/self.data.nFactor
            cross = 10*numpy.log10(z)

            out_r= out.real/self.data.nFactor

            out_i= out.imag/self.data.nFactor

            ax = self.axes[3 * n]
            if ax.firsttime:
                self.xmax = self.xmax if self.xmax else numpy.nanmax(x)
                self.xmin = self.xmin if self.xmin else -self.xmax
                self.zmin = self.zmin if self.zmin else numpy.nanmin(cross)
                self.zmax = self.zmax if self.zmax else numpy.nanmax(cross)
                ax.plt = ax.pcolormesh(x, y, cross.T,
                                       vmin=self.zmin,
                                       vmax=self.zmax,
                                       cmap=plt.get_cmap(self.colormap)
                                       )
            else:
                ax.plt.set_array(cross.T.ravel())
            self.titles.append(
                'Cross Spectra Power Ch{} * Ch{}'.format(pair[0], pair[1]))

            ax = self.axes[3 * n + 1]
            if ax.firsttime:
                self.xmax = self.xmax if self.xmax else numpy.nanmax(x)
                self.xmin = self.xmin if self.xmin else -self.xmax
                self.zmin = self.zmin if self.zmin else numpy.nanmin(cross)
                self.zmax = self.zmax if self.zmax else numpy.nanmax(cross)
                ax.plt = ax.pcolormesh(x, y, out_r.T,
                                       vmin=-1.e6,
                                       vmax=0,
                                       cmap=plt.get_cmap(self.colormap)
                                       )
            else:
                ax.plt.set_array(out_r.T.ravel())
            self.titles.append(
                'Cross Spectra Real Ch{} * Ch{}'.format(pair[0], pair[1]))

            ax = self.axes[3 * n + 2]


            if ax.firsttime:
                self.xmax = self.xmax if self.xmax else numpy.nanmax(x)
                self.xmin = self.xmin if self.xmin else -self.xmax
                self.zmin = self.zmin if self.zmin else numpy.nanmin(cross)
                self.zmax = self.zmax if self.zmax else numpy.nanmax(cross)
                ax.plt = ax.pcolormesh(x, y, out_i.T,
                                       vmin=-1.e6,
                                       vmax=1.e6,
                                       cmap=plt.get_cmap(self.colormap)
                                       )
            else:
                ax.plt.set_array(out_i.T.ravel())
            self.titles.append(
                'Cross Spectra Imag Ch{} * Ch{}'.format(pair[0], pair[1]))

class RTIPlot(Plot):
    '''
    Plot for RTI data
    '''

    CODE = 'rti'
    colormap = 'jet'
    plot_type = 'pcolorbuffer'
    titles = None
    channelList = []
    elevationList = []
    azimuthList = []

    def setup(self):
        self.xaxis = 'time'
        self.ncols = 1
        self.nrows = len(self.data.channels)
        self.nplots = len(self.data.channels)
        self.ylabel = 'Range [km]'
        #self.xlabel = 'Time'
        self.cb_label = 'dB'
        self.plots_adjust.update({'hspace':0.8, 'left': 0.1, 'bottom': 0.1, 'right':0.95})
        self.titles = ['{} Channel {}'.format(
            self.CODE.upper(), x) for x in range(self.nplots)]

    def update_list(self,dataOut):

        if len(self.channelList) == 0:
            self.channelList = dataOut.channelList
        if len(self.elevationList) == 0:
            self.elevationList = dataOut.elevationList
        if len(self.azimuthList) == 0:
            self.azimuthList = dataOut.azimuthList


    def update(self, dataOut):

        if len(self.channelList) == 0:
            self.update_list(dataOut)
        data = {}
        meta = {}
        data['rti'] = dataOut.getPower()
        norm = dataOut.nProfiles * dataOut.max_nIncohInt * dataOut.nCohInt  * dataOut.windowOfFilter
        noise = 10*numpy.log10(dataOut.getNoise()/norm)
        data['noise'] = noise

        return data, meta

    def plot(self):

        self.x = self.data.times
        self.y = self.data.yrange
        self.z = self.data[self.CODE]
        self.z = numpy.array(self.z, dtype=float)
        self.z = numpy.ma.masked_invalid(self.z)
        
        try:
            if self.channelList != None:
                if len(self.elevationList) > 0 and len(self.azimuthList) > 0:
                    self.titles = ['{}  Channel {} ({:2.1f} Elev,  {:2.1f} Azth)'.format(
                        self.CODE.upper(), x, self.elevationList[x], self.azimuthList[x]) for x in self.channelList]
                else:
                    self.titles = ['{}  Channel {}'.format(
                        self.CODE.upper(), x) for x in self.channelList]
        except:
            if self.channelList.any() != None:
                if len(self.elevationList) > 0 and len(self.azimuthList) > 0:
                    self.titles = ['{}  Channel {} ({:2.1f} Elev,  {:2.1f} Azth)'.format(
                        self.CODE.upper(), x, self.elevationList[x], self.azimuthList[x]) for x in self.channelList]
                else:
                    self.titles = ['{} Channel {}'.format(
                        self.CODE.upper(), x) for x in self.channelList]
                    
        if self.decimation is None:
            x, y, z = self.fill_gaps(self.x, self.y, self.z)
        else:
            x, y, z = self.fill_gaps(*self.decimate())

        for n, ax in enumerate(self.axes):

            self.zmin = self.zmin if self.zmin else numpy.min(self.z)
            self.zmax = self.zmax if self.zmax else numpy.max(self.z)
            data = self.data[-1]
            if ax.firsttime:
                ax.plt = ax.pcolormesh(x, y, z[n].T,
                                       vmin=self.zmin,
                                       vmax=self.zmax,
                                       cmap=plt.get_cmap(self.colormap)
                                       )
                if self.showprofile:
                    ax.plot_profile = self.pf_axes[n].plot(data[self.CODE][n], self.y)[0]
                    if "noise" in self.data:

                        ax.plot_noise = self.pf_axes[n].plot(numpy.repeat(data['noise'][n], len(self.y)), self.y,
                                                         color="k", linestyle="dashed", lw=1)[0]
            else:
                ax.collections.remove(ax.collections[0])
                ax.plt = ax.pcolormesh(x, y, z[n].T,
                                       vmin=self.zmin,
                                       vmax=self.zmax,
                                       cmap=plt.get_cmap(self.colormap)
                                       )
                if self.showprofile:
                    ax.plot_profile.set_data(data[self.CODE][n], self.y)
                    if "noise" in self.data:
                        ax.plot_noise.set_data(numpy.repeat(data['noise'][n], len(self.y)), self.y)

class SpectrogramPlot(Plot):
    '''
    Plot for Spectrogram data
    '''

    CODE = 'Spectrogram_Profile'
    colormap = 'binary'
    plot_type = 'pcolorbuffer'

    def setup(self):
        self.xaxis = 'time'
        self.ncols = 1
        self.nrows = len(self.data.channels)
        self.nplots = len(self.data.channels)
        self.xlabel = 'Time'
        self.plots_adjust.update({'hspace':1.2, 'left': 0.1, 'bottom': 0.12, 'right':0.95})
        self.titles = []

        self.titles = ['{} Channel {}'.format(
            self.CODE.upper(), x) for x in range(self.nrows)]


    def update(self, dataOut):
        data = {}
        meta = {}

        maxHei = 1620#+12000
        indb = numpy.where(dataOut.heightList <= maxHei)
        hei = indb[0][-1]

        factor = dataOut.nIncohInt
        z = dataOut.data_spc[:,:,hei] / factor
        z = numpy.where(numpy.isfinite(z), z, numpy.NAN)

        meta['xrange'] = (dataOut.getFreqRange(1)/1000., dataOut.getAcfRange(1), dataOut.getVelRange(1))
        data['Spectrogram_Profile'] = 10 * numpy.log10(z)

        data['hei'] = hei
        data['DH'] = (dataOut.heightList[1] - dataOut.heightList[0])/dataOut.step
        data['nProfiles'] = dataOut.nProfiles

        return data, meta

    def plot(self):

        self.x = self.data.times
        self.z = self.data[self.CODE]
        self.y = self.data.xrange[0]

        hei = self.data['hei'][-1]
        DH = self.data['DH'][-1]
        nProfiles = self.data['nProfiles'][-1]

        self.ylabel = "Frequency (kHz)"

        self.z = numpy.ma.masked_invalid(self.z)

        if self.decimation is None:
            x, y, z = self.fill_gaps(self.x, self.y, self.z)
        else:
            x, y, z = self.fill_gaps(*self.decimate())

        for n, ax in enumerate(self.axes):
            self.zmin = self.zmin if self.zmin else numpy.min(self.z)
            self.zmax = self.zmax if self.zmax else numpy.max(self.z)
            data = self.data[-1]
            if ax.firsttime:
                ax.plt = ax.pcolormesh(x, y, z[n].T,
                                       vmin=self.zmin,
                                       vmax=self.zmax,
                                       cmap=plt.get_cmap(self.colormap)
                                       )
            else:
                ax.collections.remove(ax.collections[0]) #  error while running
                ax.plt = ax.pcolormesh(x, y, z[n].T,
                                       vmin=self.zmin,
                                       vmax=self.zmax,
                                       cmap=plt.get_cmap(self.colormap)
                                       )



class CoherencePlot(RTIPlot):
    '''
    Plot for Coherence data
    '''

    CODE = 'coh'
    titles = None

    def setup(self):
        self.xaxis = 'time'
        self.ncols = 1
        self.nrows = len(self.data.pairs)
        self.nplots = len(self.data.pairs)
        self.ylabel = 'Range [km]'
        self.xlabel = 'Time'
        self.plots_adjust.update({'hspace':0.6, 'left': 0.1, 'bottom': 0.1,'right':0.95})
        if self.CODE == 'coh':
            self.cb_label = ''
            self.titles = [
                'Coherence Map Ch{} * Ch{}'.format(x[0], x[1]) for x in self.data.pairs]
        else:
            self.cb_label = 'Degrees'
            self.titles = [
                'Phase Map Ch{} * Ch{}'.format(x[0], x[1]) for x in self.data.pairs]

    def update(self, dataOut):

        data = {}
        meta = {}
        data['coh'] = dataOut.getCoherence()
        meta['pairs'] = dataOut.pairsList

        return data, meta

class PhasePlot(CoherencePlot):
    '''
    Plot for Phase map data
    '''

    CODE = 'phase'
    colormap = 'seismic'

    def update(self, dataOut):

        data = {}
        meta = {}
        data['phase'] = dataOut.getCoherence(phase=True)
        meta['pairs'] = dataOut.pairsList

        return data, meta

class NoisePlot(Plot):
    '''
    Plot for noise
    '''

    CODE = 'noise'
    plot_type = 'scatterbuffer'

    def setup(self):
        self.xaxis = 'time'
        self.ncols = 1
        self.nrows = 1
        self.nplots = 1
        self.ylabel = 'Intensity [dB]'
        self.xlabel = 'Time'
        self.titles = ['Noise']
        self.colorbar = False
        self.plots_adjust.update({'right': 0.85 })
        self.titles = ['Noise Plot']

    def update(self, dataOut):

        data = {}
        meta = {}
        noise =  10*numpy.log10(dataOut.getNoise())
        noise = noise.reshape(dataOut.nChannels, 1)
        data['noise'] = noise
        meta['yrange'] = numpy.array([])

        return data, meta

    def plot(self):

        x = self.data.times
        xmin = self.data.min_time
        xmax = xmin + self.xrange * 60 * 60
        Y = self.data['noise']

        if self.axes[0].firsttime:
            self.ymin = numpy.nanmin(Y) - 5
            self.ymax = numpy.nanmax(Y) + 5
            for ch in self.data.channels:
                y = Y[ch]
                self.axes[0].plot(x, y, lw=1, label='Ch{}'.format(ch))
            plt.legend(bbox_to_anchor=(1.18, 1.0))
        else:
            for ch in self.data.channels:
                y = Y[ch]
                self.axes[0].lines[ch].set_data(x, y)

class PowerProfilePlot(Plot):

    CODE = 'pow_profile'
    plot_type = 'scatter'

    def setup(self):

        self.ncols = 1
        self.nrows = 1
        self.nplots = 1
        self.height = 4
        self.width = 3
        self.ylabel = 'Range [km]'
        self.xlabel = 'Intensity [dB]'
        self.titles = ['Power Profile']
        self.colorbar = False

    def update(self, dataOut):

        data = {}
        meta = {}
        data[self.CODE] = dataOut.getPower()

        return data, meta

    def plot(self):

        y = self.data.yrange
        self.y = y

        x = self.data[-1][self.CODE]

        if self.xmin is None: self.xmin = numpy.nanmin(x)*0.9
        if self.xmax is None: self.xmax = numpy.nanmax(x)*1.1

        if self.axes[0].firsttime:
            for ch in self.data.channels:
                self.axes[0].plot(x[ch], y, lw=1, label='Ch{}'.format(ch))
            plt.legend()
        else:
            for ch in self.data.channels:
                self.axes[0].lines[ch].set_data(x[ch], y)


class SpectraCutPlot(Plot):

    CODE = 'spc_cut'
    plot_type = 'scatter'
    buffering = False
    heights = []
    channelList = []
    maintitle = "Spectra Cuts"
    flag_setIndex = False

    def setup(self):

        self.nplots = len(self.data.channels)
        self.ncols = int(numpy.sqrt(self.nplots) + 0.9)
        self.nrows = int((1.0 * self.nplots / self.ncols) + 0.9)
        self.width = 4.5 * self.ncols + 2.5
        self.height = 4.8 * self.nrows
        self.ylabel = 'Power [dB]'
        self.colorbar = False
        self.plots_adjust.update({'left':0.1, 'hspace':0.3, 'right': 0.9, 'bottom':0.08})

        if len(self.selectedHeightsList) > 0:
            self.maintitle = "Spectra Cut"# for %d km " %(int(self.selectedHeight))



    def update(self, dataOut):
        if len(self.channelList) == 0:
            self.channelList = dataOut.channelList

        self.heights = dataOut.heightList
        #print("sels: ",self.selectedHeightsList)
        if len(self.selectedHeightsList)>0 and not self.flag_setIndex:

            for sel_height in self.selectedHeightsList:
                index_list = numpy.where(self.heights >= sel_height)
                index_list = index_list[0]
                self.height_index.append(index_list[0])
            #print("sels i:"", self.height_index)
            self.flag_setIndex = True
            #print(self.height_index)
        data = {}
        meta = {}

        norm = dataOut.nProfiles * dataOut.max_nIncohInt * dataOut.nCohInt  * dataOut.windowOfFilter#*dataOut.nFFTPoints
        n0 = 10*numpy.log10(dataOut.getNoise()/norm)
        noise = numpy.repeat(n0,(dataOut.nFFTPoints*dataOut.nHeights)).reshape(dataOut.nChannels,dataOut.nFFTPoints,dataOut.nHeights)


        z = []
        for ch in range(dataOut.nChannels):
            if hasattr(dataOut.normFactor,'shape'):
                z.append(numpy.divide(dataOut.data_spc[ch],dataOut.normFactor[ch]))
            else:
                z.append(numpy.divide(dataOut.data_spc[ch],dataOut.normFactor))

        z = numpy.asarray(z)
        z = numpy.where(numpy.isfinite(z), z, numpy.NAN)
        spc = 10*numpy.log10(z)


        data['spc'] = spc - noise
        meta['xrange'] = (dataOut.getFreqRange(EXTRA_POINTS)/1000., dataOut.getAcfRange(EXTRA_POINTS), dataOut.getVelRange(EXTRA_POINTS))

        return data, meta

    def plot(self):
        if self.xaxis == "frequency":
            x = self.data.xrange[0][0:]
            self.xlabel = "Frequency (kHz)"
        elif self.xaxis == "time":
            x = self.data.xrange[1]
            self.xlabel = "Time (ms)"
        else:
            x = self.data.xrange[2]
            self.xlabel = "Velocity (m/s)"

        self.titles = []

        y = self.data.yrange
        z = self.data[-1]['spc']
        #print(z.shape)
        if len(self.height_index) > 0:
            index = self.height_index
        else:
            index = numpy.arange(0, len(y), int((len(y))/9))
        #print("inde x ", index, self.axes)

        for n, ax in enumerate(self.axes):

            if ax.firsttime:


                self.xmax = self.xmax if self.xmax else numpy.nanmax(x)
                self.xmin = self.xmin if self.xmin else -self.xmax
                self.ymin = self.ymin if self.ymin else numpy.nanmin(z)
                self.ymax = self.ymax if self.ymax else numpy.nanmax(z)


                ax.plt = ax.plot(x, z[n, :, index].T)
                labels = ['Range = {:2.1f}km'.format(y[i]) for i in index]
                self.figures[0].legend(ax.plt, labels, loc='center right', prop={'size': 8})
                ax.minorticks_on()
                ax.grid(which='major', axis='both')
                ax.grid(which='minor', axis='x')
            else:
                for i, line in enumerate(ax.plt):
                    line.set_data(x, z[n, :, index[i]])


            self.titles.append('CH {}'.format(self.channelList[n]))
        plt.suptitle(self.maintitle,  fontsize=10)


class BeaconPhase(Plot):

    __isConfig = None
    __nsubplots = None

    PREFIX = 'beacon_phase'

    def __init__(self):
        Plot.__init__(self)
        self.timerange = 24*60*60
        self.isConfig = False
        self.__nsubplots = 1
        self.counter_imagwr = 0
        self.WIDTH = 800
        self.HEIGHT = 400
        self.WIDTHPROF = 120
        self.HEIGHTPROF = 0
        self.xdata = None
        self.ydata = None

        self.PLOT_CODE = BEACON_CODE

        self.FTP_WEI = None
        self.EXP_CODE = None
        self.SUB_EXP_CODE = None
        self.PLOT_POS = None

        self.filename_phase = None

        self.figfile = None

        self.xmin = None
        self.xmax = None

    def getSubplots(self):

        ncol = 1
        nrow = 1

        return nrow, ncol

    def setup(self, id, nplots, wintitle, showprofile=True, show=True):

        self.__showprofile = showprofile
        self.nplots = nplots

        ncolspan = 7
        colspan = 6
        self.__nsubplots = 2

        self.createFigure(id = id,
                          wintitle = wintitle,
                          widthplot = self.WIDTH+self.WIDTHPROF,
                          heightplot = self.HEIGHT+self.HEIGHTPROF,
                          show=show)

        nrow, ncol = self.getSubplots()

        self.addAxes(nrow, ncol*ncolspan, 0, 0, colspan, 1)

    def save_phase(self, filename_phase):
        f = open(filename_phase,'w+')
        f.write('\n\n')
        f.write('JICAMARCA RADIO OBSERVATORY - Beacon Phase \n')
        f.write('DD MM YYYY  HH MM SS   pair(2,0) pair(2,1) pair(2,3) pair(2,4)\n\n' )
        f.close()

    def save_data(self, filename_phase, data, data_datetime):
        f=open(filename_phase,'a')
        timetuple_data = data_datetime.timetuple()
        day = str(timetuple_data.tm_mday)
        month = str(timetuple_data.tm_mon)
        year = str(timetuple_data.tm_year)
        hour = str(timetuple_data.tm_hour)
        minute = str(timetuple_data.tm_min)
        second = str(timetuple_data.tm_sec)
        f.write(day+' '+month+' '+year+'  '+hour+' '+minute+' '+second+'   '+str(data[0])+'   '+str(data[1])+'   '+str(data[2])+'   '+str(data[3])+'\n')
        f.close()

    def plot(self):
        log.warning('TODO: Not yet implemented...')

    def run(self, dataOut, id, wintitle="", pairsList=None, showprofile='True',
            xmin=None, xmax=None, ymin=None, ymax=None, hmin=None, hmax=None,
            timerange=None,
            save=False, figpath='./', figfile=None, show=True, ftp=False, wr_period=1,
            server=None, folder=None, username=None, password=None,
            ftp_wei=0, exp_code=0, sub_exp_code=0, plot_pos=0):

        if dataOut.flagNoData:
            return dataOut

        if not isTimeInHourRange(dataOut.datatime, xmin, xmax):
            return

        if pairsList == None:
            pairsIndexList = dataOut.pairsIndexList[:10]
        else:
            pairsIndexList = []
            for pair in pairsList:
                if pair not in dataOut.pairsList:
                    raise ValueError("Pair %s is not in dataOut.pairsList" %(pair))
                pairsIndexList.append(dataOut.pairsList.index(pair))

        if pairsIndexList == []:
            return

 #         if len(pairsIndexList) > 4:
 #             pairsIndexList = pairsIndexList[0:4]

        hmin_index = None
        hmax_index = None

        if hmin != None and hmax != None:
            indexes = numpy.arange(dataOut.nHeights)
            hmin_list = indexes[dataOut.heightList >= hmin]
            hmax_list = indexes[dataOut.heightList <= hmax]

            if hmin_list.any():
                hmin_index = hmin_list[0]

            if hmax_list.any():
                hmax_index = hmax_list[-1]+1

        x = dataOut.getTimeRange()

        thisDatetime = dataOut.datatime

        title = wintitle + " Signal Phase" # : %s" %(thisDatetime.strftime("%d-%b-%Y"))
        xlabel = "Local Time"
        ylabel = "Phase (degrees)"

        update_figfile = False

        nplots = len(pairsIndexList)
        phase_beacon = numpy.zeros(len(pairsIndexList))
        for i in range(nplots):
            pair = dataOut.pairsList[pairsIndexList[i]]
            ccf = numpy.average(dataOut.data_cspc[pairsIndexList[i], :, hmin_index:hmax_index], axis=0)
            powa = numpy.average(dataOut.data_spc[pair[0], :, hmin_index:hmax_index], axis=0)
            powb = numpy.average(dataOut.data_spc[pair[1], :, hmin_index:hmax_index], axis=0)
            avgcoherenceComplex = ccf/numpy.sqrt(powa*powb)
            phase = numpy.arctan2(avgcoherenceComplex.imag, avgcoherenceComplex.real)*180/numpy.pi

            if dataOut.beacon_heiIndexList:
                phase_beacon[i] = numpy.average(phase[dataOut.beacon_heiIndexList])
            else:
                phase_beacon[i] = numpy.average(phase)

        if not self.isConfig:

            nplots = len(pairsIndexList)

            self.setup(id=id,
                       nplots=nplots,
                       wintitle=wintitle,
                       showprofile=showprofile,
                       show=show)

            if timerange != None:
                self.timerange = timerange

            self.xmin, self.xmax = self.getTimeLim(x, xmin, xmax, timerange)

            if ymin == None: ymin = 0
            if ymax == None: ymax = 360

            self.FTP_WEI = ftp_wei
            self.EXP_CODE = exp_code
            self.SUB_EXP_CODE = sub_exp_code
            self.PLOT_POS = plot_pos

            self.name = thisDatetime.strftime("%Y%m%d_%H%M%S")
            self.isConfig = True
            self.figfile = figfile
            self.xdata = numpy.array([])
            self.ydata = numpy.array([])

            update_figfile = True

            #open file beacon phase
            path = '%s%03d' %(self.PREFIX, self.id)
            beacon_file = os.path.join(path,'%s.txt'%self.name)
            self.filename_phase = os.path.join(figpath,beacon_file)

        self.setWinTitle(title)


        title = "Phase Plot %s" %(thisDatetime.strftime("%Y/%m/%d %H:%M:%S"))

        legendlabels = ["Pair (%d,%d)"%(pair[0], pair[1]) for pair in dataOut.pairsList]

        axes = self.axesList[0]

        self.xdata = numpy.hstack((self.xdata, x[0:1]))

        if len(self.ydata)==0:
            self.ydata = phase_beacon.reshape(-1,1)
        else:
            self.ydata = numpy.hstack((self.ydata, phase_beacon.reshape(-1,1)))


        axes.pmultilineyaxis(x=self.xdata, y=self.ydata,
                    xmin=self.xmin, xmax=self.xmax, ymin=ymin, ymax=ymax,
                    xlabel=xlabel, ylabel=ylabel, title=title, legendlabels=legendlabels, marker='x', markersize=8, linestyle="solid",
                    XAxisAsTime=True, grid='both'
                    )

        self.draw()

        if dataOut.ltctime >= self.xmax:
            self.counter_imagwr = wr_period
            self.isConfig = False
            update_figfile = True

        self.save(figpath=figpath,
                  figfile=figfile,
                  save=save,
                  ftp=ftp,
                  wr_period=wr_period,
                  thisDatetime=thisDatetime,
                  update_figfile=update_figfile)

        return dataOut
    
##################################### 
class NoiselessSpectraPlot(Plot):
    '''
    Plot for Spectra data, subtracting
    the noise in all channels, using for
    amisr-14 data
    '''

    CODE = 'noiseless_spc'
    colormap = 'jet'
    plot_type = 'pcolor'
    buffering = False
    channelList = []
    last_noise = None

    def setup(self):

        self.nplots = len(self.data.channels)
        self.ncols = int(numpy.sqrt(self.nplots) + 0.9)
        self.nrows = int((1.0 * self.nplots / self.ncols) + 0.9)
        self.height = 3.5 * self.nrows

        self.cb_label = 'dB'
        if self.showprofile:
            self.width = 5.8 * self.ncols
        else:
            self.width = 4.8* self.ncols
        self.plots_adjust.update({'wspace': 0.4, 'hspace':0.4, 'left': 0.1, 'right': 0.92, 'bottom': 0.12})

        self.ylabel = 'Range [km]'


    def update_list(self,dataOut):
        if len(self.channelList) == 0:
            self.channelList = dataOut.channelList

    def update(self, dataOut):

        self.update_list(dataOut)
        data = {}
        meta = {}

        norm = dataOut.nProfiles * dataOut.max_nIncohInt * dataOut.nCohInt  * dataOut.windowOfFilter
        n0 = (dataOut.getNoise()/norm)
        noise = numpy.repeat(n0,(dataOut.nFFTPoints*dataOut.nHeights)).reshape(dataOut.nChannels,dataOut.nFFTPoints,dataOut.nHeights)
        noise = 10*numpy.log10(noise)

        z = numpy.zeros((dataOut.nChannels, dataOut.nFFTPoints, dataOut.nHeights))
        for ch in range(dataOut.nChannels):
            if hasattr(dataOut.normFactor,'ndim'):
                if dataOut.normFactor.ndim > 1:
                    z[ch] = (numpy.divide(dataOut.data_spc[ch],dataOut.normFactor[ch]))
                else:
                    z[ch] = (numpy.divide(dataOut.data_spc[ch],dataOut.normFactor))
            else:
                z[ch] = (numpy.divide(dataOut.data_spc[ch],dataOut.normFactor))

        z = numpy.where(numpy.isfinite(z), z, numpy.NAN)
        spc = 10*numpy.log10(z)


        data['spc'] = spc - noise
        #print(spc.shape)
        data['rti'] = spc.mean(axis=1)
        data['noise'] = noise



        # data['noise'] = noise
        meta['xrange'] = (dataOut.getFreqRange(EXTRA_POINTS)/1000., dataOut.getAcfRange(EXTRA_POINTS), dataOut.getVelRange(EXTRA_POINTS))

        return data, meta

    def plot(self):
        if self.xaxis == "frequency":
            x = self.data.xrange[0]
            self.xlabel = "Frequency (kHz)"
        elif self.xaxis == "time":
            x = self.data.xrange[1]
            self.xlabel = "Time (ms)"
        else:
            x = self.data.xrange[2]
            self.xlabel = "Velocity (m/s)"

        self.titles = []
        y = self.data.yrange
        self.y = y

        data = self.data[-1]
        z = data['spc']

        for n, ax in enumerate(self.axes):
            #noise = data['noise'][n]

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

                if self.showprofile:
                    ax.plt_profile = self.pf_axes[n].plot(
                        data['rti'][n], y)[0]


            else:
                ax.plt.set_array(z[n].T.ravel())
                if self.showprofile:
                    ax.plt_profile.set_data(data['rti'][n], y)


            self.titles.append('CH {}'.format(self.channelList[n]))


class NoiselessRTIPlot(RTIPlot):
    '''
    Plot for RTI data
    '''

    CODE = 'noiseless_rti'
    colormap = 'jet'
    plot_type = 'pcolorbuffer'
    titles = None
    channelList = []
    elevationList = []
    azimuthList = []
    last_noise = None

    def setup(self):
        self.xaxis = 'time'
        self.ncols = 1
        #print("dataChannels ",self.data.channels)
        self.nrows = len(self.data.channels)
        self.nplots = len(self.data.channels)
        self.ylabel = 'Range [km]'
        #self.xlabel = 'Time'
        self.cb_label = 'dB'
        self.plots_adjust.update({'hspace':0.8, 'left': 0.08, 'bottom': 0.2, 'right':0.94})
        self.titles = ['{} Channel {}'.format(
            self.CODE.upper(), x) for x in range(self.nplots)]

    def update_list(self,dataOut):
        if len(self.channelList) == 0:
            self.channelList = dataOut.channelList
        if len(self.elevationList) == 0:
            self.elevationList = dataOut.elevationList
        if len(self.azimuthList) == 0:
            self.azimuthList = dataOut.azimuthList

    def update(self, dataOut):
        if len(self.channelList) == 0:
            self.update_list(dataOut)

        data = {}
        meta = {}
        #print(dataOut.max_nIncohInt, dataOut.nIncohInt)
        #print(dataOut.windowOfFilter,dataOut.nCohInt,dataOut.nProfiles,dataOut.max_nIncohInt,dataOut.nIncohInt
        norm = dataOut.nProfiles * dataOut.max_nIncohInt * dataOut.nCohInt  * dataOut.windowOfFilter
        n0 = 10*numpy.log10(dataOut.getNoise()/norm)
        data['noise'] = n0
        noise = numpy.repeat(n0,dataOut.nHeights).reshape(dataOut.nChannels,dataOut.nHeights)
        noiseless_data = dataOut.getPower() - noise

        #print("power, noise:", dataOut.getPower(), n0)
        #print(noise)
        #print(noiseless_data)
        
        data['noiseless_rti'] = noiseless_data

        return data, meta

    def plot(self):
        from matplotlib import pyplot as plt
        self.x = self.data.times
        self.y = self.data.yrange
        self.z = self.data['noiseless_rti']
        self.z = numpy.array(self.z, dtype=float)
        self.z = numpy.ma.masked_invalid(self.z)


        try:
            if self.channelList != None:
                if len(self.elevationList) > 0 and len(self.azimuthList) > 0:
                    self.titles = ['{}  Channel {} ({:2.1f} Elev,  {:2.1f} Azth)'.format(
                        self.CODE.upper(), x, self.elevationList[x], self.azimuthList[x]) for x in self.channelList]
                else:
                    self.titles = ['{}  Channel {}'.format(
                        self.CODE.upper(), x) for x in self.channelList]
        except:
            if self.channelList.any() != None:
                if len(self.elevationList) > 0 and len(self.azimuthList) > 0:
                    self.titles = ['{}  Channel {} ({:2.1f} Elev,  {:2.1f} Azth)'.format(
                        self.CODE.upper(), x, self.elevationList[x], self.azimuthList[x]) for x in self.channelList]
                else:
                    self.titles = ['{} Channel {}'.format(
                        self.CODE.upper(), x) for x in self.channelList]


        if self.decimation is None:
            x, y, z = self.fill_gaps(self.x, self.y, self.z)
        else:
            x, y, z = self.fill_gaps(*self.decimate())

        dummy_var = self.axes #Extrañamente esto actualiza el valor axes
        #print("plot shapes ", z.shape, x.shape, y.shape)
        #print(self.axes)
        for n, ax in enumerate(self.axes):


            self.zmin = self.zmin if self.zmin else numpy.min(self.z)
            self.zmax = self.zmax if self.zmax else numpy.max(self.z)
            data = self.data[-1]
            if ax.firsttime:
                if (n+1) == len(self.channelList):
                    ax.set_xlabel('Time')
                ax.plt = ax.pcolormesh(x, y, z[n].T,
                                       vmin=self.zmin,
                                       vmax=self.zmax,
                                       cmap=plt.get_cmap(self.colormap)
                                       )
                if self.showprofile:
                    ax.plot_profile = self.pf_axes[n].plot(data['noiseless_rti'][n], self.y)[0]

            else:
                ax.collections.remove(ax.collections[0]) #  error while running
                ax.plt = ax.pcolormesh(x, y, z[n].T,
                                       vmin=self.zmin,
                                       vmax=self.zmax,
                                       cmap=plt.get_cmap(self.colormap)
                                       )
                if self.showprofile:
                    ax.plot_profile.set_data(data['noiseless_rti'][n], self.y)
                    # if "noise" in self.data:
                    #     #ax.plot_noise.set_data(numpy.repeat(data['noise'][n], len(self.y)), self.y)
                    #     ax.plot_noise.set_data(data['noise'][n], self.y)


class OutliersRTIPlot(Plot):
    '''
    Plot for data_xxxx object
    '''

    CODE = 'outlier_rtc' # Range Time Counts
    colormap = 'cool'
    plot_type = 'pcolorbuffer'

    def setup(self):
        self.xaxis = 'time'
        self.ncols = 1
        self.nrows = self.data.shape('outlier_rtc')[0]
        self.nplots = self.nrows
        self.plots_adjust.update({'hspace':0.8, 'left': 0.08, 'bottom': 0.2, 'right':0.94})


        if not self.xlabel:
            self.xlabel = 'Time'

        self.ylabel = 'Height [km]'
        if not self.titles:
            self.titles = ['Outliers Ch:{}'.format(x) for x in range(self.nrows)]

    def update(self, dataOut):

        data = {}
        data['outlier_rtc'] = dataOut.data_outlier

        meta = {}

        return data, meta

    def plot(self):
        # self.data.normalize_heights()
        self.x = self.data.times
        self.y = self.data.yrange
        self.z = self.data['outlier_rtc']

        #self.z = numpy.ma.masked_invalid(self.z)

        if self.decimation is None:
            x, y, z = self.fill_gaps(self.x, self.y, self.z)
        else:
            x, y, z = self.fill_gaps(*self.decimate())

        for n, ax in enumerate(self.axes):

            self.zmax = self.zmax if self.zmax is not None else numpy.max(
                self.z[n])
            self.zmin = self.zmin if self.zmin is not None else numpy.min(
                self.z[n])
            data = self.data[-1]
            if ax.firsttime:
                if self.zlimits is not None:
                    self.zmin, self.zmax = self.zlimits[n]

                ax.plt = ax.pcolormesh(x, y, z[n].T,
                                       vmin=self.zmin,
                                       vmax=self.zmax,
                                       cmap=self.cmaps[n]
                                       )
                if self.showprofile:
                    ax.plot_profile = self.pf_axes[n].plot(data['outlier_rtc'][n], self.y)[0]
                    self.pf_axes[n].set_xlabel('')
            else:
                if self.zlimits is not None:
                    self.zmin, self.zmax = self.zlimits[n]
                ax.collections.remove(ax.collections[0]) #  error while running
                ax.plt = ax.pcolormesh(x, y, z[n].T ,
                                       vmin=self.zmin,
                                       vmax=self.zmax,
                                       cmap=self.cmaps[n]
                                       )
                if self.showprofile:
                    ax.plot_profile.set_data(data['outlier_rtc'][n], self.y)
                    self.pf_axes[n].set_xlabel('')

class NIncohIntRTIPlot(Plot):
    '''
    Plot for data_xxxx object
    '''

    CODE = 'integrations_rtc' # Range Time Counts
    colormap = 'BuGn'
    plot_type = 'pcolorbuffer'

    def setup(self):
        self.xaxis = 'time'
        self.ncols = 1
        self.nrows = self.data.shape('integrations_rtc')[0]
        self.nplots = self.nrows
        self.plots_adjust.update({'hspace':0.8, 'left': 0.08, 'bottom': 0.2, 'right':0.94})


        if not self.xlabel:
            self.xlabel = 'Time'

        self.ylabel = 'Height [km]'
        if not self.titles:
            self.titles = ['Integration Ch:{}'.format(x) for x in range(self.nrows)]

    def update(self, dataOut):

        data = {}
        data['integrations_rtc'] = dataOut.nIncohInt

        meta = {}

        return data, meta

    def plot(self):
        # self.data.normalize_heights()
        self.x = self.data.times
        self.y = self.data.yrange
        self.z = self.data['integrations_rtc']

        #self.z = numpy.ma.masked_invalid(self.z)

        if self.decimation is None:
            x, y, z = self.fill_gaps(self.x, self.y, self.z)
        else:
            x, y, z = self.fill_gaps(*self.decimate())

        for n, ax in enumerate(self.axes):

            self.zmax = self.zmax if self.zmax is not None else numpy.max(
                self.z[n])
            self.zmin = self.zmin if self.zmin is not None else numpy.min(
                self.z[n])
            data = self.data[-1]
            if ax.firsttime:
                if self.zlimits is not None:
                    self.zmin, self.zmax = self.zlimits[n]

                ax.plt = ax.pcolormesh(x, y, z[n].T,
                                       vmin=self.zmin,
                                       vmax=self.zmax,
                                       cmap=self.cmaps[n]
                                       )
                if self.showprofile:
                    ax.plot_profile = self.pf_axes[n].plot(data['integrations_rtc'][n], self.y)[0]
                    self.pf_axes[n].set_xlabel('')
            else:
                if self.zlimits is not None:
                    self.zmin, self.zmax = self.zlimits[n]
                ax.collections.remove(ax.collections[0]) #  error while running
                ax.plt = ax.pcolormesh(x, y, z[n].T ,
                                       vmin=self.zmin,
                                       vmax=self.zmax,
                                       cmap=self.cmaps[n]
                                       )
                if self.showprofile:
                    ax.plot_profile.set_data(data['integrations_rtc'][n], self.y)
                    self.pf_axes[n].set_xlabel('')

    

class RTIMapPlot(Plot):
    '''
    Plot for RTI data

    Example:

    controllerObj = Project()
    controllerObj.setup(id = '11', name='eej_proc', description=desc)
    ##.......................................................................................
    ##.......................................................................................
    readUnitConfObj = controllerObj.addReadUnit(datatype='AMISRReader', path=inPath, startDate='2023/05/24',endDate='2023/05/24', 
                    startTime='12:00:00',endTime='12:45:59',walk=1,timezone='lt',margin_days=1,code = code,nCode = nCode,
                    nBaud = nBaud,nOsamp = nosamp,nChannels=nChannels,nFFT=NFFT, 
                    syncronization=False,shiftChannels=0)

    volts_proc = controllerObj.addProcUnit(datatype='VoltageProc', inputId=readUnitConfObj.getId())

    opObj01 = volts_proc.addOperation(name='Decoder', optype='other')
    opObj01.addParameter(name='code', value=code, format='floatlist')
    opObj01.addParameter(name='nCode', value=1, format='int')
    opObj01.addParameter(name='nBaud', value=nBaud, format='int')
    opObj01.addParameter(name='osamp', value=nosamp, format='int')

    opObj12 = volts_proc.addOperation(name='selectHeights', optype='self')
    opObj12.addParameter(name='minHei', value='90', format='float')
    opObj12.addParameter(name='maxHei', value='150', format='float')

    proc_spc = controllerObj.addProcUnit(datatype='SpectraProc', inputId=volts_proc.getId())
    proc_spc.addParameter(name='nFFTPoints', value='8', format='int')

    opObj11 = proc_spc.addOperation(name='IncohInt', optype='other')
    opObj11.addParameter(name='n', value='1', format='int') 

    beamMapFile = "/home/japaza/Documents/AMISR_sky_mapper/UMET_beamcodes.csv"

    opObj12 = proc_spc.addOperation(name='RTIMapPlot', optype='external')
    opObj12.addParameter(name='selectedHeightsList', value='95, 100, 105, 110 ', format='int')
    opObj12.addParameter(name='bField', value='100', format='int')
    opObj12.addParameter(name='filename', value=beamMapFile, format='str') 
    
    '''

    CODE = 'rti_skymap'
    
    plot_type = 'scatter'
    titles = None
    colormap = 'jet'
    channelList = []
    elevationList = []
    azimuthList = []
    last_noise = None
    flag_setIndex = False
    heights = []
    dcosx = []
    dcosy = []
    fullDcosy = None
    fullDcosy = None
    hindex = []
    mapFile = False
    #####  BField    ####
    flagBField = False 
    dcosxB = []
    dcosyB = []
    Bmarker = ['+','*','D','x','s','>','o','^']
  

    def setup(self):

        self.xaxis = 'Range (Km)'
        if len(self.selectedHeightsList) > 0:
            self.nplots = len(self.selectedHeightsList)
        else: 
            self.nplots = 4
        self.ncols = int(numpy.ceil(self.nplots/2))
        self.nrows = int(numpy.ceil(self.nplots/self.ncols))  
        self.ylabel = 'dcosy'
        self.xlabel = 'dcosx'
        self.colorbar = True
        self.width = 6 + 4.1*self.nrows
        self.height = 3 + 3.5*self.ncols
        

        if self.extFile!=None:
            try:
                pointings =  numpy.genfromtxt(self.extFile, delimiter=',')
                full_azi = pointings[:,1]
                full_elev = pointings[:,2]
                self.fullDcosx = numpy.cos(numpy.radians(full_elev))*numpy.sin(numpy.radians(full_azi))
                self.fullDcosy = numpy.cos(numpy.radians(full_elev))*numpy.cos(numpy.radians(full_azi))
                mapFile = True
            except Exception as e:
                self.extFile = None
                print(e)


    def update_list(self,dataOut):
        if len(self.channelList) == 0:
            self.channelList = dataOut.channelList
        if len(self.elevationList) == 0:
            self.elevationList = dataOut.elevationList
        if len(self.azimuthList) == 0:
            self.azimuthList = dataOut.azimuthList
        a = numpy.radians(numpy.asarray(self.azimuthList))
        e = numpy.radians(numpy.asarray(self.elevationList))
        self.heights = dataOut.heightList
        self.dcosx = numpy.cos(e)*numpy.sin(a)
        self.dcosy = numpy.cos(e)*numpy.cos(a)

        if len(self.bFieldList)>0:
            datetObj = datetime.datetime.fromtimestamp(dataOut.utctime)
            doy = datetObj.timetuple().tm_yday
            year = datetObj.year
            # self.dcosxB, self.dcosyB 
            ObjB = BField(year=year,doy=doy,site=2,heights=self.bFieldList)
            [dcos, alpha, nlon, nlat] = ObjB.getBField()

            alpha_location = numpy.zeros((nlon,2,len(self.bFieldList)))
            for ih in range(len(self.bFieldList)):
                alpha_location[:,0,ih] = dcos[:,0,ih,0]
                for ilon in numpy.arange(nlon):
                    myx = (alpha[ilon,:,ih])[::-1]
                    myy = (dcos[ilon,:,ih,0])[::-1]
                    tck = splrep(myx,myy,s=0)
                    mydcosx = splev(ObjB.alpha_i,tck,der=0)

                    myx = (alpha[ilon,:,ih])[::-1]
                    myy = (dcos[ilon,:,ih,1])[::-1]
                    tck = splrep(myx,myy,s=0)
                    mydcosy = splev(ObjB.alpha_i,tck,der=0)
                    alpha_location[ilon,:,ih] = numpy.array([mydcosx, mydcosy])
                self.dcosxB.append(alpha_location[:,0,ih])
                self.dcosyB.append(alpha_location[:,1,ih])
            self.flagBField = True
            
        if len(self.celestialList)>0:
            #getBField(self.bFieldList, date)
            #pass = kwargs.get('celestial', [])
            pass


    def update(self, dataOut):

        if len(self.channelList) == 0:
            self.update_list(dataOut)

        if not self.flag_setIndex:
            if len(self.selectedHeightsList)>0:
                for sel_height in self.selectedHeightsList:
                    index_list = numpy.where(self.heights >= sel_height)
                    index_list = index_list[0]
                    self.hindex.append(index_list[0])    
            self.flag_setIndex = True

        data = {}
        meta = {}

        data['rti_skymap'] = dataOut.getPower()
        norm = dataOut.nProfiles * dataOut.max_nIncohInt * dataOut.nCohInt  * dataOut.windowOfFilter
        noise = 10*numpy.log10(dataOut.getNoise()/norm)
        data['noise'] = noise

        return data, meta

    def plot(self):

        self.x = self.dcosx
        self.y = self.dcosy
        self.z = self.data[-1]['rti_skymap']
        self.z = numpy.array(self.z, dtype=float)

        if len(self.hindex) > 0:
            index = self.hindex
        else:
            index = numpy.arange(0, len(self.heights), int((len(self.heights))/4.2))

        self.titles = ['Height {:.2f} km '.format(self.heights[i])+" " for i in index]
        for n, ax in enumerate(self.axes):

            if ax.firsttime:
 
                self.xmax = self.xmax if self.xmax else numpy.nanmax(self.x)
                self.xmin = self.xmin if self.xmin else numpy.nanmin(self.x)
                self.ymax = self.ymax if self.ymax else numpy.nanmax(self.y)
                self.ymin = self.ymin if self.ymin else numpy.nanmin(self.y)     
                self.zmax = self.zmax if self.zmax else numpy.nanmax(self.z)
                self.zmin = self.zmin if self.zmin else numpy.nanmin(self.z)

                if self.extFile!=None:
                    ax.scatter(self.fullDcosx, self.fullDcosy, marker="+", s=20)

                ax.plt = ax.scatter(self.x, self.y, c=self.z[:,index[n]], cmap = 'jet',vmin = self.zmin,
                    s=60, marker="s", vmax = self.zmax)
                

                ax.minorticks_on()
                ax.grid(which='major', axis='both')
                ax.grid(which='minor', axis='x')

                if self.flagBField :

                    for ih in range(len(self.bFieldList)):
                        label = str(self.bFieldList[ih]) + ' km'
                        ax.plot(self.dcosxB[ih], self.dcosyB[ih], color='k', marker=self.Bmarker[ih % 8], 
                                         label=label,   linestyle='--',  ms=4.0,lw=0.5)
                    handles, labels = ax.get_legend_handles_labels()
                    a = -0.05
                    b = 1.15 - 1.19*(self.nrows)
                    self.axes[0].legend(handles,labels, bbox_to_anchor=(a,b), prop={'size': (5.8+ 1.1*self.nplots)}, title='B Field ⊥')
            
            else:
                
                ax.plt = ax.scatter(self.x, self.y, c=self.z[:,index[n]], cmap = 'jet',vmin = self.zmin,
                     s=80, marker="s", vmax = self.zmax)

                if self.flagBField :
                    for ih in range(len(self.bFieldList)):
                        ax.plot (self.dcosxB[ih], self.dcosyB[ih], color='k', marker=self.Bmarker[ih % 8],
                                linestyle='--', ms=4.0,lw=0.5)
                        


