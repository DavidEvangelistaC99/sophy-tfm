"""

Converted to Object-oriented Programming by Freddy Galindo, ROJ, 07 October 2009.
Added to signal Chain by Joab Apaza, ROJ, Jun 2023.
"""

import numpy
import time
import os
from scipy.special import lpmn
from schainpy.model.utils import Astro_Coords

class BField():
    def __init__(self,year=None,doy=None,site=1,heights=None,alpha_i=90):
        """
        BField class creates an object to get  the Magnetic  field for a  specific date and
        height(s).

        Parameters
        ----------
        year = A scalar giving the desired year.  If the value is None (default value) then
          the current year will be used.
        doy = A scalar giving the desired day of the year. If the value is None (default va-
          lue) then the current doy will be used.
        site = An integer to choose the geographic coordinates of the place where the magne-
          tic field will be computed. The default value is over Jicamarca (site=1)
        heights = An array giving the heights (km) where the magnetic field will be modeled By default the magnetic field will be computed at 100, 500 and 1000km.
        alpha_i = Angle to interpolate the magnetic field.

        Modification History
        --------------------
        Converted to Object-oriented Programming by Freddy Galindo, ROJ, 07 October 2009.
        Added to signal Chain by Joab Apaza, ROJ, Jun 2023.
        """

        tmp = time.localtime()
        if year==None: year = tmp[0]
        if doy==None:  doy = tmp[7]
        self.year = year
        self.doy = doy
        self.site = site
        if heights is None:
            heights = numpy.array([100,500,1000])
        else:
            heights = numpy.array(heights)
        self.heights = heights
        self.alpha_i = alpha_i

    def getBField(self,maglimits=numpy.array([-37,-37,37,37])):
        """
        getBField models the magnetic field for a different heights in a specific date.

        Parameters
        ----------
        maglimits = An 4-elements array giving ..... The default value is [-7,-7,7,7].

        Return
        ------
        dcos = An 4-dimensional array giving the directional cosines of the magnetic field
          over the desired place.
        alpha = An 3-dimensional array giving the angle of the magnetic field over the desi-
          red place.

        Modification History
        --------------------
        Converted to Python by Freddy R. Galindo, ROJ, 07 October 2009.
        """

        x_ant = numpy.array([1,0,0])
        y_ant = numpy.array([0,1,0])
        z_ant = numpy.array([0,0,1])
        
        if self.site==0:
            title_site = "Magnetic equator"
            coord_site = numpy.array([-76+52./60.,-11+57/60.,0.5])
        elif self.site==1:
            title_site = 'Jicamarca'
            coord_site = [-76-52./60.,-11-57/60.,0.5]
            heta = (45+5.35)*numpy.pi/180.      # (50.35 and 1.46 from Fleish Thesis)
            delta = -1.46*numpy.pi/180


            x_ant1 = numpy.roll(self.rotvector(self.rotvector(x_ant,1,delta),3,theta),1)
            y_ant1 = numpy.roll(self.rotvector(self.rotvector(y_ant,1,delta),3,theta),1)
            z_ant1 = numpy.roll(self.rotvector(self.rotvector(z_ant,1,delta),3,theta),1)

            ang0 = -1*coord_site[0]*numpy.pi/180.
            ang1 = coord_site[1]*numpy.pi/180.
            x_ant = self.rotvector(self.rotvector(x_ant1,2,ang1),3,ang0)
            y_ant = self.rotvector(self.rotvector(y_ant1,2,ang1),3,ang0)
            z_ant = self.rotvector(self.rotvector(z_ant1,2,ang1),3,ang0)

        elif self.site==2: #AMISR
            title_site = 'AMISR 14'

            coord_site = [-76.874913, -11.953371, 0.52984]

            theta = (0.0977)*numpy.pi/180.       #  0.0977
            delta = 0.110*numpy.pi/180        # 0.11

            x_ant1 = numpy.roll(self.rotvector(self.rotvector(x_ant,1,delta),3,theta),1)
            y_ant1 = numpy.roll(self.rotvector(self.rotvector(y_ant,1,delta),3,theta),1)
            z_ant1 = numpy.roll(self.rotvector(self.rotvector(z_ant,1,delta),3,theta),1)

            ang0 = -1*coord_site[0]*numpy.pi/180.
            ang1 = coord_site[1]*numpy.pi/180.
            x_ant = self.rotvector(self.rotvector(x_ant1,2,ang1),3,ang0)
            y_ant = self.rotvector(self.rotvector(y_ant1,2,ang1),3,ang0)
            z_ant = self.rotvector(self.rotvector(z_ant1,2,ang1),3,ang0)
        else:
#            print "No defined Site. Skip..."
            return None

        nhei = self.heights.size
        pt_intercep = numpy.zeros((nhei,2))
        nfields = 1

        grid_res = 2.5
        nlon = int(int(maglimits[2] - maglimits[0])/grid_res + 1)
        nlat = int(int(maglimits[3] - maglimits[1])/grid_res + 1)

        location = numpy.zeros((nlon,nlat,2))
        mlon = numpy.atleast_2d(numpy.arange(nlon)*grid_res + maglimits[0])
        mrep = numpy.atleast_2d(numpy.zeros(nlat) + 1)
        location0 = numpy.dot(mlon.transpose(),mrep)

        mlat = numpy.atleast_2d(numpy.arange(nlat)*grid_res + maglimits[1])
        mrep = numpy.atleast_2d(numpy.zeros(nlon) + 1)
        location1 = numpy.dot(mrep.transpose(),mlat)

        location[:,:,0] = location0
        location[:,:,1] = location1

        alpha = numpy.zeros((nlon,nlat,nhei))
        rr = numpy.zeros((nlon,nlat,nhei,3))
        dcos = numpy.zeros((nlon,nlat,nhei,2))

        global first_time

        first_time = None
        for ilon in numpy.arange(nlon):
            for ilat in numpy.arange(nlat):
                outs = self.__bdotk(self.heights,
                                    self.year + self.doy/366.,
                                    coord_site[1],
                                    coord_site[0],
                                    coord_site[2],
                                    coord_site[1]+location[ilon,ilat,1],
                                    location[ilon,ilat,0]*720./180.)

                alpha[ilon, ilat,:] = outs[1]
                rr[ilon, ilat,:,:] = outs[3]

                mrep = numpy.atleast_2d((numpy.zeros(nhei)+1)).transpose()
                tmp = outs[3]*numpy.dot(mrep,numpy.atleast_2d(x_ant))
                tmp = tmp.sum(axis=1)
                dcos[ilon,ilat,:,0] = tmp/numpy.sqrt((outs[3]**2).sum(axis=1))

                mrep = numpy.atleast_2d((numpy.zeros(nhei)+1)).transpose()
                tmp = outs[3]*numpy.dot(mrep,numpy.atleast_2d(y_ant))
                tmp = tmp.sum(axis=1)
                dcos[ilon,ilat,:,1] = tmp/numpy.sqrt((outs[3]**2).sum(axis=1))

        return dcos, alpha, nlon, nlat


    def __bdotk(self,heights,tm,gdlat=-11.95,gdlon=-76.8667,gdalt=0.0,decd=-12.88, ham=-4.61666667):

        global first_time
        # Mean Earth radius in Km WGS 84
        a_igrf = 6371.2

        bk = numpy.zeros(heights.size)
        alpha = numpy.zeros(heights.size)
        bfm = numpy.zeros(heights.size)
        rr = numpy.zeros((heights.size,3))
        rgc = numpy.zeros((heights.size,3))

        ObjGeodetic = Astro_Coords.Geodetic(gdlat,gdalt)
        [gclat,gcalt] = ObjGeodetic.change2geocentric()

        gclat = gclat*numpy.pi/180.
        gclon = gdlon*numpy.pi/180.

        # Antenna position from center of Earth
        ca_vector = [numpy.cos(gclat)*numpy.cos(gclon),numpy.cos(gclat)*numpy.sin(gclon),numpy.sin(gclat)]
        ca_vector = gcalt*numpy.array(ca_vector)

        dec = decd*numpy.pi/180.

        # K  vector respect to the center of earth.
        klon = gclon + ham*numpy.pi/720.
        k_vector = [numpy.cos(dec)*numpy.cos(klon),numpy.cos(dec)*numpy.sin(klon),numpy.sin(dec)]
        k_vector = numpy.array(k_vector)

        for ih in numpy.arange(heights.size):
            # Vector from Earth's center to volume of interest
            rr[ih,:] = k_vector*heights[ih]
            cv_vector = numpy.squeeze(ca_vector) + rr[ih,:]

            cv_gcalt = numpy.sqrt(numpy.sum(cv_vector**2.))
            cvxy = numpy.sqrt(numpy.sum(cv_vector[0:2]**2.))

            radial = cv_vector/cv_gcalt
            east = numpy.array([-1*cv_vector[1],cv_vector[0],0])/cvxy
            comp1 = east[1]*radial[2] - radial[1]*east[2]
            comp2 = east[2]*radial[0] - radial[2]*east[0]
            comp3 = east[0]*radial[1] - radial[0]*east[1]
            north = -1*numpy.array([comp1, comp2, comp3])

            rr_k = cv_vector - numpy.squeeze(ca_vector)
            u_rr = rr_k/numpy.sqrt(numpy.sum(rr_k**2.))

            cv_gclat = numpy.arctan2(cv_vector[2],cvxy)
            cv_gclon = numpy.arctan2(cv_vector[1],cv_vector[0])

            bhei = cv_gcalt-a_igrf
            blat = cv_gclat*180./numpy.pi
            blon = cv_gclon*180./numpy.pi
            bfield = self.__igrfkudeki(bhei,tm,blat,blon)

            B = (bfield[0]*north + bfield[1]*east - bfield[2]*radial)*1.0e-5

            bfm[ih] = numpy.sqrt(numpy.sum(B**2.)) #module
            bk[ih] = numpy.sum(u_rr*B)
            alpha[ih] = numpy.arccos(bk[ih]/bfm[ih])*180/numpy.pi
            rgc[ih,:] = numpy.array([cv_gclon, cv_gclat, cv_gcalt])

        return bk, alpha, bfm, rr, rgc


    def __igrfkudeki(self,heights,time,latitude,longitude,ae=6371.2):
        """
        __igrfkudeki calculates the International Geomagnetic Reference Field for given in-
        put conditions based on IGRF2005 coefficients.

        Parameters
        ----------
        heights = Scalar or vector giving the height above the Earth  of the point in ques-
          tion in kilometers.
        time = Scalar or vector giving the decimal year of time in question (e.g. 1991.2).
        latitude = Latitude of point in question in decimal degrees. Scalar or vector.
        longitude = Longitude of point in question in decimal degrees. Scalar or vector.
        ae =
        first_time =

        Return
        ------
        bn =
        be =
        bd =
        bmod =
        balpha =
        first_time =

        Modification History
        --------------------
        Converted to Python by Freddy R. Galindo, ROJ, 03 October 2009.
        """

        global first_time
        global gs, hs, nvec, mvec, maxcoef

        heights = numpy.atleast_1d(heights)
        time = numpy.atleast_1d(time)
        latitude = numpy.atleast_1d(latitude)
        longitude = numpy.atleast_1d(longitude)

        if numpy.max(latitude)==90:
#            print "Field calculations are not supported at geographic poles"
            pass

        # output arrays
        bn = numpy.zeros(heights.size)
        be = numpy.zeros(heights.size)
        bd = numpy.zeros(heights.size)

        if first_time==None:first_time=0

        time0 = time[0]
        if time!=first_time:
            #print "Getting coefficients for", time0
            [periods,g,h ] = self.__readIGRFcoeff()
            top_year = numpy.max(periods)
            nperiod = (top_year - 1900)/5 + 1

            maxcoef = 10

            if time0>=2000:maxcoef = 12


            # Normalization array for Schmidt fucntions
            multer = numpy.zeros((2+maxcoef,1+maxcoef)) + 1
            for cn in (numpy.arange(maxcoef)+1):
                for rm in (numpy.arange(cn)+1):
                    tmp = numpy.arange(2*rm) + cn - rm + 1.
                    multer[rm+1,cn] = ((-1.)**rm)*numpy.sqrt(2./tmp.prod())

            schmidt = multer[1:,1:].transpose()

            # n and m arrays
            nvec = numpy.atleast_2d(numpy.arange(maxcoef)+2)
            mvec = numpy.atleast_2d(numpy.arange(maxcoef+1)).transpose()

            # Time adjusted igrf g and h with Schmidt normalization
            # IGRF coefficient arrays: g0(n,m), n=1, maxcoeff,m=0, maxcoeff, ...
            if time0<top_year:
                dtime = (time0 - 1900) % 5
                ntime = int((time0 - 1900 - dtime)/5)
            else:
                # Estimating coefficients for times > top_year
                dtime = (time0 - top_year) + 5
                ntime = int(g[:,0,0].size - 2)

            
            g0 = g[ntime,1:maxcoef+1,:maxcoef+1]
            h0 = h[ntime,1:maxcoef+1,:maxcoef+1]
            gdot = g[ntime+1,1:maxcoef+1,:maxcoef+1]-g[ntime,1:maxcoef+1,:maxcoef+1]
            hdot = h[ntime+1,1:maxcoef+1,:maxcoef+1]-h[ntime,1:maxcoef+1,:maxcoef+1]
            gs = (g0 + dtime*(gdot/5.))*schmidt[:maxcoef,0:maxcoef+1]
            hs = (h0 + dtime*(hdot/5.))*schmidt[:maxcoef,0:maxcoef+1]

            first_time = time0

        for ii in numpy.arange(heights.size):
            # Height dependence array rad = (ae/(ae+height))**(n+3)
            rad = numpy.atleast_2d((ae/(ae + heights[ii]))**(nvec+1))

            # Sin and Cos of m times longitude phi arrays
            mphi = mvec*longitude[ii]*numpy.pi/180.
            cosmphi = numpy.atleast_2d(numpy.cos(mphi))
            sinmphi = numpy.atleast_2d(numpy.sin(mphi))

            # Cos of colatitude theta
            c = numpy.cos((90 - latitude[ii])*numpy.pi/180.)

            # Legendre functions p(n,m|c)
            [p,dp]= lpmn(maxcoef+1,maxcoef+1,c)
            p = p[:,:-1].transpose()
            s = numpy.sqrt((1. - c)*(1 + c))

            # Generate derivative array dpdtheta = -s*dpdc
            dpdtheta = c*p/s
            for m in numpy.arange(maxcoef+2):    dpdtheta[:,m] = m*dpdtheta[:,m]
            dpdtheta = dpdtheta + numpy.roll(p,-1,axis=1)

            # Extracting arrays required for field calculations
            p = p[1:maxcoef+1,:maxcoef+1]
            dpdtheta = dpdtheta[1:maxcoef+1,:maxcoef+1]

            # Weigh p and dpdtheta with gs and hs coefficients.
            gp = gs*p
            hp = hs*p
            gdpdtheta = gs*dpdtheta
            hdpdtheta = hs*dpdtheta
            # Calcultate field components
            matrix0 = numpy.dot(gdpdtheta,cosmphi)
            matrix1 = numpy.dot(hdpdtheta,sinmphi)
            bn[ii] = numpy.dot(rad,(matrix0 + matrix1))
            matrix0 = numpy.dot(hp,(mvec*cosmphi))
            matrix1 = numpy.dot(gp,(mvec*sinmphi))
            be[ii] = numpy.dot((-1*rad),((matrix0 - matrix1)/s))
            matrix0 = numpy.dot(gp,cosmphi)
            matrix1 = numpy.dot(hp,sinmphi)
            bd[ii] = numpy.dot((-1*nvec*rad),(matrix0 + matrix1))

        bmod = numpy.sqrt(bn**2. + be**2. + bd**2.)
        btheta = numpy.arctan(bd/numpy.sqrt(be**2. + bn**2.))*180/numpy.pi
        balpha = numpy.arctan(be/bn)*180./numpy.pi

        #bn : north
        #be : east
        #bn : radial
        #bmod : module


        return bn, be, bd, bmod, btheta, balpha

    def str2num(self, datum):
        try:
            return int(datum)
        except:
            try:
                return float(datum)
            except:
                return datum

    def __readIGRFfile(self, filename):
        list_years=[]
        for i in range(1,26):
            list_years.append(1895.0 + i*5)

        epochs=list_years
        epochs.append(epochs[-1]+5)
        nepochs = numpy.shape(epochs)

        gg = numpy.zeros((13,14,nepochs[0]),dtype=float)
        hh = numpy.zeros((13,14,nepochs[0]),dtype=float)

        coeffs_file=open(filename)
        lines=coeffs_file.readlines()

        coeffs_file.close()

        for line in lines:
            items = line.split()
            g_h = items[0]
            n = self.str2num(items[1])
            m = self.str2num(items[2])

            coeffs = items[3:]

            for i in range(len(coeffs)-1):
                coeffs[i] = self.str2num(coeffs[i])

            #coeffs = numpy.array(coeffs)
            ncoeffs = numpy.shape(coeffs)[0]

            if g_h == 'g':
    #            print n," g ",m
                gg[n-1,m,:]=coeffs
            elif g_h=='h':
    #            print n," h ",m
                hh[n-1,m,:]=coeffs
    #        else :
    #            continue

    #    Ultimo Reordenamiento para  almacenar .
        gg[:,:,nepochs[0]-1] = gg[:,:,nepochs[0]-2] + 5*gg[:,:,nepochs[0]-1]
        hh[:,:,nepochs[0]-1] = hh[:,:,nepochs[0]-2] + 5*hh[:,:,nepochs[0]-1]

#        return numpy.array([gg,hh])
        periods = numpy.array(epochs)
        g = gg
        h = hh
        return periods, g, h


    def __readIGRFcoeff(self,filename="igrf10coeffs.dat"):
        """
        __readIGRFcoeff reads the coefficients from  a binary file which is located  in the
        folder "resource."

        Parameter
        ---------
        filename = A string to specify the name of the file which contains thec coeffs. The
        default value is "igrf10coeffs.dat"

        Return
        ------
        periods = A lineal array giving...
        g1 =
        h1 =

        Modification History
        --------------------
        Converted to Python by Freddy R. Galindo, ROJ, 03 October 2009.
        """

        base_path = os.path.dirname(os.path.abspath(__file__))
        filename = os.path.join(base_path, "igrf13coeffs.txt")

        period_v, g_v, h_v = self.__readIGRFfile(filename)
        g2 = numpy.zeros((14,14,26))
        h2 = numpy.zeros((14,14,26))
        g2[1:14,:,:] = g_v
        h2[1:14,:,:] = h_v

        g = numpy.transpose(g2, (2,0,1))
        h = numpy.transpose(h2, (2,0,1))
        periods = period_v.copy()

        return periods, g, h

    def rotvector(self,vector,axis=1,ang=0):
        """
        rotvector function returns the new vector generated rotating the rectagular coords.

        Parameters
        ----------
        vector = A lineal 3-elements array (x,y,z).
        axis = A integer to specify  the axis used to rotate the coord systems. The default
          value is 1.
            axis = 1 -> Around "x"
            axis = 2 -> Around "y"
            axis = 3 -> Around "z"
        ang = Angle of rotation (in radians). The default value is zero.

        Return
        ------
        rotvector = A lineal array of 3 elements giving the new coordinates.

        Modification History
        --------------------
        Converted to Python by Freddy R. Galindo, ROJ, 01 October 2009.
        """

        if axis==1:
            t = [[1,0,0],[0,numpy.cos(ang),numpy.sin(ang)],[0,-numpy.sin(ang),numpy.cos(ang)]]
        elif axis==2:
            t = [[numpy.cos(ang),0,-numpy.sin(ang)],[0,1,0],[numpy.sin(ang),0,numpy.cos(ang)]]
        elif axis==3:
            t = [[numpy.cos(ang),numpy.sin(ang),0],[-numpy.sin(ang),numpy.cos(ang),0],[0,0,1]]

        rotvector = numpy.array(numpy.dot(numpy.array(t),numpy.array(vector)))

        return rotvector
