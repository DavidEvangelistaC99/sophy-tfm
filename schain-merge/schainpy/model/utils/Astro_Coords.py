""" 
The module  ASTRO_COORDS.py  gathers classes and functions for coordinates transformation. Additiona-
lly a class EquatorialCorrections and celestial bodies are defined. The first of these is to correct 
any error  in the location  of the body and the second to know the location of certain celestial bo-
dies in the sky.

MODULES CALLED:
OS, NUMPY, NUMERIC, SCIPY, TIME_CONVERSIONS
        
MODIFICATION HISTORY:
Created by Ing. Freddy Galindo (frederickgalindo@gmail.com). ROJ Sep 20, 2009.
"""

import numpy
#import Numeric
import scipy.interpolate
import os
import sys
from schainpy.model.utils import TimeTools
from schainpy.model.utils import Misc_Routines

class EquatorialCorrections():
    def __init__(self):
        """
        EquatorialCorrections class creates an  object to call methods to correct the  loca-
        tion of the celestial bodies.
        
        Modification History
        --------------------
        Converted to Object-oriented Programming by Freddy Galindo, ROJ, 27 September 2009.
        """
        
        pass
    
    def co_nutate(self,jd,ra,dec):
        """
        co_nutate calculates changes in RA and Dec due to  nutation of the Earth's rotation
        Additionally it returns the obliquity of the ecliptic (eps), nutation in the longi-
        tude of the ecliptic (d_psi) and nutation in the pbliquity of the ecliptic (d_eps).

        Parameters
        ----------
        jd = Julian Date (Scalar or array).
        RA = A scalar o array giving the Right Ascention of interest.
        Dec = A scalar o array giving the Right Ascention of interest.

        Return
        ------
        d_ra =  Correction to ra due to nutation.
        d_dec = Correction to dec due to nutation.

        Examples
        --------
        >> Julian = 2462088.7 
        >> Ra = 41.547213
        >> Dec = 49.348483
        >> [d_ra,d_dec,eps,d_psi,d_eps] = co_nutate(julian,Ra,Dec)
        >> print d_ra, d_dec, eps, d_psi, d_eps
        [ 15.84276651] [ 6.21641029] [ 0.4090404] [ 14.85990198] [ 2.70408658]

        Modification history
        --------------------
        Written by Chris O'Dell, 2002.
        Converted to Python by Freddy R. Galindo, ROJ, 26 September 2009.
        """
        
        jd = numpy.atleast_1d(jd)
        ra = numpy.atleast_1d(ra)
        dec = numpy.atleast_1d(dec)
        
        # Useful transformation constants
        d2as = numpy.pi/(180.*3600.)
        
        # Julian centuries from J2000 of jd
        T = (jd - 2451545.0)/36525.0

        # Must calculate obliquity of ecliptic
        [d_psi, d_eps] = self.nutate(jd)
        d_psi = numpy.atleast_1d(d_psi)
        d_eps = numpy.atleast_1d(d_eps)
        
        eps0 = (23.4392911*3600.) - (46.8150*T) - (0.00059*T**2) + (0.001813*T**3)
        # True obliquity of the ecliptic in radians
        eps = (eps0 + d_eps)/3600.*Misc_Routines.CoFactors.d2r
        
        # Useful numbers
        ce = numpy.cos(eps)
        se = numpy.sin(eps)

        # Convert Ra-Dec to equatorial rectangular coordinates
        x = numpy.cos(ra*Misc_Routines.CoFactors.d2r)*numpy.cos(dec*Misc_Routines.CoFactors.d2r)
        y = numpy.sin(ra*Misc_Routines.CoFactors.d2r)*numpy.cos(dec*Misc_Routines.CoFactors.d2r)
        z = numpy.sin(dec*Misc_Routines.CoFactors.d2r)
        
        # Apply corrections to each rectangular coordinate
        x2 = x - (y*ce + z*se)*d_psi*Misc_Routines.CoFactors.s2r
        y2 = y + (x*ce*d_psi - z*d_eps)*Misc_Routines.CoFactors.s2r
        z2 = z + (x*se*d_psi + y*d_eps)*Misc_Routines.CoFactors.s2r
        
        # Convert bask to equatorial spherical coordinates
        r = numpy.sqrt(x2**2. + y2**2. + z2**2.)
        xyproj =numpy.sqrt(x2**2. + y2**2.)
        
        ra2 = x2*0.0
        dec2 = x2*0.0
        
        xyproj = numpy.atleast_1d(xyproj)
        z = numpy.atleast_1d(z)
        r = numpy.atleast_1d(r)
        x2 = numpy.atleast_1d(x2)
        y2 = numpy.atleast_1d(y2)
        z2 = numpy.atleast_1d(z2)
        ra2 = numpy.atleast_1d(ra2)
        dec2 = numpy.atleast_1d(dec2)
        
        w1 = numpy.where((xyproj==0) & (z!=0))
        w2 = numpy.where(xyproj!=0)
        
        # Calculate Ra and Dec in radians (later convert to degrees)
        if w1[0].size>0:
            # Places where xyproj=0 (point at NCP or SCP)
            dec2[w1] = numpy.arcsin(z2[w1]/r[w1])
            ra2[w1] = 0
        
        if w2[0].size>0:
            # Places other than NCP or SCP
            ra2[w2] = numpy.arctan2(y2[w2],x2[w2])
            dec2[w2] = numpy.arcsin(z2[w2]/r[w2])

        # Converting to degree
        ra2 = ra2/Misc_Routines.CoFactors.d2r
        dec2 = dec2/Misc_Routines.CoFactors.d2r
        
        w = numpy.where(ra2<0.)
        if w[0].size>0:
            ra2[w] = ra2[w] + 360.
        
        # Return changes in Ra and Dec in arcseconds
        d_ra = (ra2 -ra)*3600.
        d_dec = (dec2 - dec)*3600.
        
        return d_ra, d_dec, eps, d_psi, d_eps
        
    def nutate(self,jd):
        """
        nutate returns the nutation in longitude and obliquity for a given Julian date.
        
        Parameters
        ----------
        jd = Julian ephemeris date, scalar or vector.
        
        Return
        ------ 
        nut_long = The nutation in longitude.
        nut_obliq = The nutation in latitude.
        
        Example
        -------
        >> julian = 2446895.5
        >> [nut_long,nut_obliq] = nutate(julian)
        >> print nut_long, nut_obliq
        -3.78793107711 9.44252069864
        
        >> julians = 2415020.5 + numpy.arange(50)
        >> [nut_long,nut_obliq] = nutate(julians)
        
        Modification History
        --------------------
        Written by W.Landsman (Goddard/HSTX), June 1996.
        Converted to Python by Freddy R. Galindo, ROJ, 26 September 2009.
        """

        jd = numpy.atleast_1d(jd)
        
        # Form time in Julian centuries from 1900
        t = (jd - 2451545.0)/36525.0
        
        # Mean elongation of the moon
        coeff1 = numpy.array([1/189474.0,-0.0019142,445267.111480,297.85036])
        d = numpy.poly1d(coeff1)
        d = d(t)*Misc_Routines.CoFactors.d2r
        d = self.cirrange(d,rad=1)
        
        # Sun's mean elongation
        coeff2 = numpy.array([-1./3e5,-0.0001603,35999.050340,357.52772])
        m = numpy.poly1d(coeff2)
        m = m(t)*Misc_Routines.CoFactors.d2r
        m = self.cirrange(m,rad=1)
        
        # Moon's mean elongation
        coeff3 = numpy.array([1.0/5.625e4,0.0086972,477198.867398,134.96298])
        mprime = numpy.poly1d(coeff3)
        mprime = mprime(t)*Misc_Routines.CoFactors.d2r
        mprime = self.cirrange(mprime,rad=1)
        
        # Moon's argument of latitude
        coeff4 = numpy.array([-1.0/3.27270e5,-0.0036825,483202.017538,93.27191])
        f = numpy.poly1d(coeff4)
        f = f(t)*Misc_Routines.CoFactors.d2r
        f = self.cirrange(f,rad=1)
        
        # Longitude fo the ascending node of the Moon's  mean orbit on the ecliptic, measu-
        # red from the mean equinox of the date.
        coeff5 = numpy.array([1.0/4.5e5,0.0020708,-1934.136261,125.04452])
        omega = numpy.poly1d(coeff5)
        omega = omega(t)*Misc_Routines.CoFactors.d2r
        omega = self.cirrange(omega,rad=1)

        d_lng = numpy.array([0,-2,0,0,0,0,-2,0,0,-2,-2,-2,0,2,0,2,0,0,-2,0,2,0,0,-2,0,-2,0,0,\
            2,-2,0,-2,0,0,2,2,0,-2,0,2,2,-2,-2,2,2,0,-2,-2,0,-2,-2,0,-1,-2,1,0,0,-1,0,\
            0,2,0,2])

        m_lng = numpy.array([0,0,0,0,1,0,1,0,0,-1])
        m_lng = numpy.append(m_lng,numpy.zeros(17))
        m_lng = numpy.append(m_lng,numpy.array([2,0,2,1,0,-1,0,0,0,1,1,-1,0,0,0,0,0,0,-1,-1,0,0,\
            0,1,0,0,1,0,0,0,-1,1,-1,-1,0,-1]))

        mp_lng = numpy.array([0,0,0,0,0,1,0,0,1,0,1,0,-1,0,1,-1,-1,1,2,-2,0,2,2,1,0,0, -1, 0,\
            -1,0,0,1,0,2,-1,1,0,1,0,0,1,2,1,-2,0,1,0,0,2,2,0,1,1,0,0,1,-2,1,1,1,-1,3,0])

        f_lng = numpy.array([0,2,2,0,0,0,2,2,2,2,0,2,2,0,0,2,0,2,0,2,2,2,0,2,2,2,2,0,0,2,0,0,\
            0,-2,2,2,2,0,2,2,0,2,2,0,0,0,2,0,2,0,2,-2,0,0,0,2,2,0,0,2,2,2,2])

        om_lng = numpy.array([1,2,2,2,0,0,2,1,2,2,0,1,2,0,1,2,1,1,0,1,2,2,0,2,0,0,1,0,1,2,1, \
            1,1,0,1,2,2,0,2,1,0,2,1,1,1,0,1,1,1,1,1,0,0,0,0,0,2,0,0,2,2,2,2])

        sin_lng = numpy.array([-171996,-13187,-2274,2062,1426,712,-517,-386,-301, 217, -158, \
               129,123,63,63,-59,-58,-51,48,46,-38,-31,29,29,26,-22,21,17,16,-16,-15,-13,\
                 -12,11,-10,-8,7,-7,-7,-7,6,6,6,-6,-6,5,-5,-5,-5,4,4,4,-4,-4,-4,3,-3,-3,-3,\
            -3,-3,-3,-3])

        sdelt = numpy.array([-174.2,-1.6,-0.2,0.2,-3.4,0.1,1.2,-0.4,0,-0.5,0, 0.1, 0, 0, 0.1,\
             0,-0.1])
        sdelt = numpy.append(sdelt,numpy.zeros(10))
        sdelt = numpy.append(sdelt,numpy.array([-0.1, 0, 0.1]))
        sdelt = numpy.append(sdelt,numpy.zeros(33))
        
        cos_lng = numpy.array([92025,5736,977,-895,54,-7,224,200,129,-95,0,-70,-53,0,-33,26, \
            32,27,0,-24,16,13,0,-12,0,0,-10,0,-8,7,9,7,6,0,5,3,-3,0,3,3,0,-3,-3,3,3,0,\
            3,3,3])
        cos_lng = numpy.append(cos_lng,numpy.zeros(14))
        
        cdelt = numpy.array([8.9,-3.1,-0.5,0.5,-0.1,0.0,-0.6,0.0,-0.1,0.3])
        cdelt = numpy.append(cdelt,numpy.zeros(53))

        # Sum the periodic terms.
        n = numpy.size(jd)
        nut_long = numpy.zeros(n)
        nut_obliq = numpy.zeros(n)
        
        d_lng = d_lng.reshape(numpy.size(d_lng),1)
        d = d.reshape(numpy.size(d),1)
        matrix_d_lng = numpy.dot(d_lng,d.transpose())
        
        m_lng = m_lng.reshape(numpy.size(m_lng),1)
        m = m.reshape(numpy.size(m),1)
        matrix_m_lng = numpy.dot(m_lng,m.transpose())
        
        mp_lng = mp_lng.reshape(numpy.size(mp_lng),1)
        mprime = mprime.reshape(numpy.size(mprime),1)
        matrix_mp_lng = numpy.dot(mp_lng,mprime.transpose())
        
        f_lng = f_lng.reshape(numpy.size(f_lng),1)
        f = f.reshape(numpy.size(f),1)
        matrix_f_lng = numpy.dot(f_lng,f.transpose())
        
        om_lng = om_lng.reshape(numpy.size(om_lng),1)
        omega = omega.reshape(numpy.size(omega),1)
        matrix_om_lng = numpy.dot(om_lng,omega.transpose())
        
        arg = matrix_d_lng + matrix_m_lng + matrix_mp_lng + matrix_f_lng + matrix_om_lng
        
        sarg = numpy.sin(arg)
        carg = numpy.cos(arg)

        for ii in numpy.arange(n):
            nut_long[ii] = 0.0001*numpy.sum((sdelt*t[ii] + sin_lng)*sarg[:,ii])
            nut_obliq[ii] = 0.0001*numpy.sum((cdelt*t[ii] + cos_lng)*carg[:,ii])

        if numpy.size(jd)==1:
            nut_long = nut_long[0]
            nut_obliq = nut_obliq[0]
    
        return nut_long, nut_obliq

    def co_aberration(self,jd,ra,dec):
        """
        co_aberration calculates changes to Ra and Dec due to "the effect of aberration".
        
        Parameters
        ----------
        jd = Julian Date (Scalar or vector).
        ra = A scalar o vector giving the Right Ascention of interest.
        dec = A scalar o vector giving the Declination of interest.
        
        Return
        ------
        d_ra = The correction to right ascension due to aberration (must be added  to ra to
          get the correct value).
        d_dec = The correction to  declination due to aberration (must be  added to the dec
          to get the correct value).
        eps = True obliquity of the ecliptic (in radians).
        
        Examples
        --------
        >> Julian = 2462088.7 
        >> Ra = 41.547213
        >> Dec = 49.348483
        >> [d_ra,d_dec,eps] = co_aberration(julian,Ra,Dec)
        >> print d_ra, d_dec, eps
        [ 30.04441796] [ 6.69837858] [ 0.40904059]
        
        Modification history
        --------------------
        Written by Chris O'Dell , Univ. of Wisconsin, June 2002.
        Converted to Python by Freddy R. Galindo, ROJ, 27 September 2009.
        """

        # Julian centuries from J2000 of jd.
        T = (jd - 2451545.0)/36525.0
        
        # Getting obliquity of ecliptic
        njd = numpy.size(jd)
        jd = numpy.atleast_1d(jd)
        ra = numpy.atleast_1d(ra)
        dec = numpy.atleast_1d(dec)
        
        d_psi = numpy.zeros(njd)
        d_epsilon = d_psi
        for ii in numpy.arange(njd):
            [dp,de] = self.nutate(jd[ii])
            d_psi[ii] = dp
            d_epsilon[ii] = de

        coeff = 23 + 26/60. + 21.488/3600.
        eps0 = coeff*3600. - 46.8150*T - 0.00059*T**2. + 0.001813*T**3.
        # True obliquity of the ecliptic in radians
        eps = (eps0 + d_epsilon)/3600*Misc_Routines.CoFactors.d2r
        
        celestialbodies = CelestialBodies()
        [sunra,sundec,sunlon,sunobliq] = celestialbodies.sunpos(jd)
        
        # Earth's orbital eccentricity
        e = 0.016708634 - 0.000042037*T - 0.0000001267*T**2.
        
        # longitude of perihelion, in degrees
        pi = 102.93735 + 1.71946*T + 0.00046*T**2
        
        # Constant of aberration, in arcseconds
        k = 20.49552 
        
        cd = numpy.cos(dec*Misc_Routines.CoFactors.d2r)    ; sd = numpy.sin(dec*Misc_Routines.CoFactors.d2r)
        ce = numpy.cos(eps)                  ; te = numpy.tan(eps)
        cp = numpy.cos(pi*Misc_Routines.CoFactors.d2r)     ; sp = numpy.sin(pi*Misc_Routines.CoFactors.d2r)
        cs = numpy.cos(sunlon*Misc_Routines.CoFactors.d2r) ; ss = numpy.sin(sunlon*Misc_Routines.CoFactors.d2r)
        ca = numpy.cos(ra*Misc_Routines.CoFactors.d2r)     ; sa = numpy.sin(ra*Misc_Routines.CoFactors.d2r)
        
        term1 = (ca*cs*ce + sa*ss)/cd
        term2 = (ca*cp*ce + sa*sp)/cd
        term3 = (cs*ce*(te*cd - sa*sd) + ca*sd*ss)
        term4 = (cp*ce*(te*cd - sa*sd) + ca*sd*sp)
        
        d_ra = -k*term1 + e*k*term2
        d_dec = -k*term3 + e*k*term4
        
        return d_ra, d_dec, eps

    def precess(self,ra,dec,equinox1=None,equinox2=None,FK4=0,rad=0):
        """
        precess coordinates from EQUINOX1 to EQUINOX2
        
        Parameters
        -----------
        ra = A scalar o vector giving the Right Ascention of interest.
        dec = A scalar o vector giving the Declination of interest.
        equinox1 = Original equinox of coordinates, numeric scalar.  If omitted, the __Pre-
          cess will query for equinox1 and equinox2.
        equinox2 = Original equinox of coordinates.
        FK4 = If this keyword is  set  and non-zero, the FK4  (B1950)  system will  be used
          otherwise FK5 (J2000) will be used instead.
        rad = If this keyword is set and non-zero,  then the input and  output  RAD and DEC
          vectors are in radian rather than degree.
        
        Return
        ------
        ra = Right ascension after precession (scalar or vector) in degrees, unless the rad
          keyword is set.
        dec = Declination after precession (scalar or vector)  in degrees,  unless  the rad
          keyword is set.
        
        Examples
        --------
        >> Ra = 329.88772
        >> Dec = -56.992515
        >> [p_ra,p_dec] = precess(Ra,Dec,1950,1975,FK4=1)
        >> print p_ra, p_dec
        [ 330.31442971] [-56.87186154] 
        
        Modification history
        --------------------
        Written by Wayne Landsman, STI Corporation, August 1986.
        Converted to Python by Freddy R. Galindo, ROJ, 27 September 2009.
        """

        npts = numpy.size(ra)
        ra = numpy.atleast_1d(ra)
        dec = numpy.atleast_1d(dec)

        if rad==0:
            ra_rad = ra*Misc_Routines.CoFactors.d2r
            dec_rad = dec*Misc_Routines.CoFactors.d2r
        else:
            ra_rad = ra
            dec_rad = dec

        x = numpy.zeros((npts,3))
        x[:,0] = numpy.cos(dec_rad)*numpy.cos(ra_rad)
        x[:,1] = numpy.cos(dec_rad)*numpy.sin(ra_rad)
        x[:,2] = numpy.sin(dec_rad)
        
        # Use premat function to get precession matrix from equinox1 to equinox2
        r = self.premat(equinox1,equinox2,FK4)
        
        x2 = numpy.dot(r,x.transpose())
        
        ra_rad = numpy.arctan2(x2[1,:],x2[0,:])
        dec_rad = numpy.arcsin(x2[2,:])
        
        if rad==0:
            ra = ra_rad/Misc_Routines.CoFactors.d2r
            ra = ra + (ra<0)*360.
            dec = dec_rad/Misc_Routines.CoFactors.d2r
        else:
            ra = ra_rad
            ra = ra + (ra<0)*numpy.pi*2.
            dec = dec_rad

        return ra, dec  

    def premat(self,equinox1,equinox2,FK4=0):
        """
        premat returns the precession matrix needed to go from EQUINOX1 to EQUINOX2.
        
        Parameters
        ----------
        equinox1 = Original equinox of coordinates, numeric scalar.
        equinox2 = Equinox of precessed coordinates.
        FK4 = If this keyword is set and non-zero, the FK4 (B1950) system precession angles
          are used to compute the precession matrix. The default is to use FK5 (J2000) pre-
                  cession angles.
        
        Return
        ------
        r = Precession matrix, used to precess equatorial rectangular coordinates.
        
        Examples
        --------
        >> matrix = premat(1950.0,1975.0,FK4=1)
        >> print matrix
        [[  9.99981438e-01  -5.58774959e-03  -2.42908517e-03]
         [  5.58774959e-03   9.99984388e-01  -6.78691471e-06]
         [  2.42908517e-03  -6.78633095e-06   9.99997050e-01]]
        
        Modification history
        --------------------
        Written by Wayne Landsman, HSTX Corporation, June 1994.
        Converted to Python by Freddy R. Galindo, ROJ, 27 September 2009.
        """

        t = 0.001*(equinox2 - equinox1)

        if FK4==0:
            st=0.001*(equinox1 - 2000.)            
            # Computing 3 rotation angles.
            A=Misc_Routines.CoFactors.s2r*t*(23062.181+st*(139.656+0.0139*st)+t*(30.188-0.344*st+17.998*t))
            B=Misc_Routines.CoFactors.s2r*t*t*(79.280+0.410*st+0.205*t)+A
            C=Misc_Routines.CoFactors.s2r*t*(20043.109-st*(85.33+0.217*st)+ t*(-42.665-0.217*st-41.833*t))
        else:
            st=0.001*(equinox1 - 1900)
            # Computing 3 rotation angles
            A=Misc_Routines.CoFactors.s2r*t*(23042.53+st*(139.75+0.06*st)+t*(30.23-0.27*st+18.0*t))
            B=Misc_Routines.CoFactors.s2r*t*t*(79.27+0.66*st+0.32*t)+A
            C=Misc_Routines.CoFactors.s2r*t*(20046.85-st*(85.33+0.37*st)+t*(-42.67-0.37*st-41.8*t))

        sina = numpy.sin(A); sinb = numpy.sin(B); sinc = numpy.sin(C)
        cosa = numpy.cos(A); cosb = numpy.cos(B); cosc = numpy.cos(C)
        
        r = numpy.zeros((3,3))        
        r[:,0] = numpy.array([cosa*cosb*cosc-sina*sinb,sina*cosb+cosa*sinb*cosc,cosa*sinc])
        r[:,1] = numpy.array([-cosa*sinb-sina*cosb*cosc,cosa*cosb-sina*sinb*cosc,-sina*sinc])
        r[:,2] = numpy.array([-cosb*sinc,-sinb*sinc,cosc])
        
        return r

    def cirrange(self,angle,rad=0):
        """
        cirrange forces an angle into the range 0<= angle < 360.
        
        Parameters
        ----------
        angle = The angle to modify, in degrees. Can be scalar or vector.
        rad = Set to 1 if the angle is specified in radians rather than degrees. It is for-
          ced into the range 0 <= angle < 2 PI
        
        Return
        ------
        angle = The angle after the modification.
        
        Example
        -------
        >> angle = cirrange(numpy.array([420,400,361]))
        >> print angle
        >> [60, 40, 1]
        
        Modification History
        --------------------
        Written by Michael R. Greason, Hughes STX, 10 February 1994.
        Converted to Python by Freddy R. Galindo, ROJ, 26 September 2009.
        """        

        angle = numpy.atleast_1d(angle)
        
        if rad==1:
            cnst = numpy.pi*2.
        elif rad==0:
            cnst = 360.

        # Deal with the lower limit.
        angle = angle % cnst
        
        # Deal with negative values, if way
        neg = numpy.where(angle<0.0)
        if neg[0].size>0: angle[neg] = angle[neg] + cnst
        
        return angle


class CelestialBodies(EquatorialCorrections):
    def __init__(self):
        """
        CelestialBodies class creates a object to call methods of celestial bodies location.
        
        Modification History
        --------------------
        Converted to Object-oriented Programming by Freddy Galindo, ROJ, 27 September 2009.
        """

        EquatorialCorrections.__init__(self)

    def sunpos(self,jd,rad=0):
        """
        sunpos method computes the RA and Dec of the Sun at a given date.
        
        Parameters
        ----------
        jd = The julian date of the day (and time), scalar or vector.
        rad = If this keyword is set and non-zero,  then the input and  output  RAD and DEC
          vectors are in radian rather than degree.
        
        Return
        ------
        ra = The right ascension of the sun at that date in degrees.
        dec = The declination of the sun at that date in degrees.
        elong = Ecliptic longitude of the sun at that date in degrees.
        obliquity = The declination of the sun at that date in degrees.
        
        Examples
        --------
        >> jd = 2466880
        >> [ra,dec,elong,obliquity] = sunpos(jd)
        >> print ra, dec, elong, obliquity
        [ 275.53499556] [-23.33840558] [ 275.08917968] [ 23.43596165]
        
        >> [ra,dec,elong,obliquity] = sunpos(jd,rad=1)
        >> print ra, dec, elong, obliquity
        [ 4.80899288] [-0.40733202] [ 4.80121192] [ 0.40903469]
        
        >> jd = 2450449.5 + numpy.arange(365)
        >> [ra,dec,elong,obliquity] = sunpos(jd)
        
        Modification history
        --------------------
        Written by Micheal R. Greason, STX Corporation, 28 October 1988.
        Converted to Python by Freddy R. Galindo, ROJ, 27 September 2009.
        """

        jd = numpy.atleast_1d(jd)
        
        # Form time in Julian centuries from 1900.
        t = (jd -2415020.0)/36525.0
        
        # Form sun's mean longitude
        l = (279.696678+((36000.768925*t) % 360.0))*3600.0
        
        # Allow for  ellipticity of the orbit  (equation of centre)  using the Earth's mean
        # anomoly ME
        me = 358.475844 + ((35999.049750*t) % 360.0)
        ellcor = (6910.1 - 17.2*t)*numpy.sin(me*Misc_Routines.CoFactors.d2r) + 72.3*numpy.sin(2.0*me*Misc_Routines.CoFactors.d2r)
        l = l + ellcor
        
        # Allow for the Venus perturbations using the mean anomaly of Venus MV
        mv = 212.603219 + ((58517.803875*t) % 360.0)
        vencorr = 4.8*numpy.cos((299.1017 + mv - me)*Misc_Routines.CoFactors.d2r) + \
            5.5*numpy.cos((148.3133 +  2.0*mv  -  2.0*me )*Misc_Routines.CoFactors.d2r) + \
            2.5*numpy.cos((315.9433 +  2.0*mv  -  3.0*me )*Misc_Routines.CoFactors.d2r) + \
            1.6*numpy.cos((345.2533 +  3.0*mv  -  4.0*me )*Misc_Routines.CoFactors.d2r) + \
            1.0*numpy.cos((318.15   +  3.0*mv  -  5.0*me )*Misc_Routines.CoFactors.d2r)
        l = l + vencorr

        # Allow for the Mars perturbations using the mean anomaly of Mars MM
        mm = 319.529425 + ((19139.858500*t) % 360.0)
        marscorr = 2.0*numpy.cos((343.8883 - 2.0*mm + 2.0*me)*Misc_Routines.CoFactors.d2r ) + \
            1.8*numpy.cos((200.4017 -  2.0*mm  + me)*Misc_Routines.CoFactors.d2r)
        l = l + marscorr

        # Allow for the Jupiter perturbations using the mean anomaly of Jupiter MJ
        mj = 225.328328 + ((3034.6920239*t) % 360.0)
        jupcorr = 7.2*numpy.cos((179.5317 - mj + me )*Misc_Routines.CoFactors.d2r) + \
            2.6*numpy.cos((263.2167 - mj)*Misc_Routines.CoFactors.d2r) + \
            2.7*numpy.cos((87.1450 - 2.0*mj + 2.0*me)*Misc_Routines.CoFactors.d2r) + \
            1.6*numpy.cos((109.4933 - 2.0*mj + me)*Misc_Routines.CoFactors.d2r)
        l = l + jupcorr

        # Allow for Moons perturbations using mean elongation of the Moon from the Sun D
        d = 350.7376814 + ((445267.11422*t) % 360.0)
        mooncorr  = 6.5*numpy.sin(d*Misc_Routines.CoFactors.d2r)
        l = l + mooncorr
        
        # Allow for long period terms
        longterm  = + 6.4*numpy.sin((231.19 + 20.20*t)*Misc_Routines.CoFactors.d2r)
        l = l + longterm
        l = (l + 2592000.0) % 1296000.0
        longmed = l/3600.0
        
        # Allow for Aberration
        l = l - 20.5
        
        # Allow for Nutation using the longitude of the Moons mean node OMEGA
        omega = 259.183275 - ((1934.142008*t) % 360.0)
        l = l - 17.2*numpy.sin(omega*Misc_Routines.CoFactors.d2r)

        # Form the True Obliquity
        oblt = 23.452294 - 0.0130125*t + (9.2*numpy.cos(omega*Misc_Routines.CoFactors.d2r))/3600.0
        
        # Form Right Ascension and Declination
        l = l/3600.0
        ra  = numpy.arctan2((numpy.sin(l*Misc_Routines.CoFactors.d2r)*numpy.cos(oblt*Misc_Routines.CoFactors.d2r)),numpy.cos(l*Misc_Routines.CoFactors.d2r))
        
        neg = numpy.where(ra < 0.0)
        if neg[0].size > 0: ra[neg] = ra[neg] + 2.0*numpy.pi
        
        dec = numpy.arcsin(numpy.sin(l*Misc_Routines.CoFactors.d2r)*numpy.sin(oblt*Misc_Routines.CoFactors.d2r))
        
        if rad==1:            
            oblt = oblt*Misc_Routines.CoFactors.d2r
            longmed = longmed*Misc_Routines.CoFactors.d2r
        else:
            ra = ra/Misc_Routines.CoFactors.d2r
            dec = dec/Misc_Routines.CoFactors.d2r

        return ra, dec, longmed, oblt

    def moonpos(self,jd,rad=0):
        """
        moonpos method computes the RA and Dec of the Moon at specified Julian date(s).
        
        Parameters
        ----------
        jd = The julian date of the day (and time), scalar or vector.
        rad = If this keyword is set and non-zero,  then the input and  output  RAD and DEC
          vectors are in radian rather than degree.
        
        Return
        ------
        ra = The right ascension of the sun at that date in degrees.
        dec = The declination of the sun at that date in degrees.
        dist = The Earth-moon distance  in kilometers  (between the center of the Earth and
          the center of the moon).
        geolon = Apparent longitude of the moon in degrees, referred to the ecliptic of the
          specified date(s).
        geolat = Apparent latitude  the  moon in  degrees,  referred to the ecliptic of the
          specified date(s).
        
        Examples
        --------
        >> jd = 2448724.5
        >> [ra,dec,dist,geolon,geolat] = sunpos(jd)
        >> print ra, dec, dist, geolon, geolat
        [ 134.68846855] [ 13.76836663] [ 368409.68481613] [ 133.16726428] [-3.22912642]
        
        >> [ra,dec,dist,geolon, geolat] = sunpos(jd,rad=1)
        >> print ra, dec, dist, geolon, geolat
        [ 2.35075724] [ 0.24030333] [ 368409.68481613] [ 2.32420722] [-0.05635889]
        
        >> jd = 2450449.5 + numpy.arange(365)
        >> [ra,dec,dist,geolon, geolat] = sunpos(jd)
        
        Modification history
        --------------------
        Written by Micheal R. Greason, STX Corporation, 31 October 1988.
        Converted to Python by Freddy R. Galindo, ROJ, 06 October 2009.
        """

        jd = numpy.atleast_1d(jd)
        
        # Form time in Julian centuries from 1900.
        t = (jd - 2451545.0)/36525.0

        d_lng = numpy.array([0,2,2,0,0,0,2,2,2,2,0,1,0,2,0,0,4,0,4,2,2,1,1,2,2,4,2,0,2,2,1,2,\
          0,0,2,2,2,4,0,3,2,4,0,2,2,2,4,0,4,1,2,0,1,3,4,2,0,1,2,2])
        
        m_lng = numpy.array([0,0,0,0,1,0,0,-1,0,-1,1,0,1,0,0,0,0,0,0,1,1,0,1,-1,0,0,0,1,0,-1,\
          0,-2,1,2,-2,0,0,-1,0,0,1,-1,2,2,1,-1,0,0,-1,0,1,0,1,0,0,-1,2,1,0,0])

        mp_lng = numpy.array([1,-1,0,2,0,0,-2,-1,1,0,-1,0,1,0,1,1,-1,3,-2,-1,0,-1,0,1,2,0,-3,\
          -2,-1,-2,1,0,2,0,-1,1,0,-1,2,-1,1,-2,-1,-1,-2,0,1,4,0,-2,0,2,1,-2,-3,2,1,-1,3,-1])
        
        f_lng = numpy.array([0,0,0,0,0,2,0,0,0,0,0,0,0,-2,2,-2,0,0,0,0,0,0,0,0,0,0,0,0,2,0,0,\
          0,0,0,0,-2,2,0,2,0,0,0,0,0,0,-2,0,0,0,0,-2,-2,0,0,0,0,0,0,0,-2])
        
        sin_lng = numpy.array([6288774,1274027,658314,213618,-185116,-114332,58793,57066,\
          53322,45758,-40923,-34720,-30383,15327,-12528,10980,10675,10034,8548,-7888,\
             -6766,-5163,4987,4036,3994,3861,3665,-2689,-2602,2390,-2348,2236,-2120,-2069,\
          2048,-1773,-1595,1215,-1110,-892,-810,759,-713,-700,691,596,549,537,520,-487,\
          -399,-381,351,-340,330,327,-323,299,294,0.0])
        
        cos_lng = numpy.array([-20905355,-3699111,-2955968,-569925,48888,-3149,246158,-152138,\
          -170733,-204586,-129620,108743,104755,10321,0,79661,-34782,-23210,-21636,24208,\
          30824,-8379,-16675,-12831,-10445,-11650,14403,-7003,0,10056,6322, -9884,5751,0,\
          -4950,4130,0,-3958,0,3258,2616,-1897,-2117,2354,0,0,-1423,-1117,-1571,-1739,0, \
          -4421,0,0,0,0,1165,0,0,8752.0])

        d_lat = numpy.array([0,0,0,2,2,2,2,0,2,0,2,2,2,2,2,2,2,0,4,0,0,0,1,0,0,0,1,0,4,4,0,4,\
          2,2,2,2,0,2,2,2,2,4,2,2,0,2,1,1,0,2,1,2,0,4,4,1,4,1,4,2])
        
        m_lat = numpy.array([0,0,0,0,0,0,0,0,0,0,-1,0,0,1,-1,-1,-1,1,0,1,0,1,0,1,1,1,0,0,0,0,\
          0,0,0,0,-1,0,0,0,0,1,1,0,-1,-2,0,1,1,1,1,1,0,-1,1,0,-1,0,0,0,-1,-2])
        
        mp_lat = numpy.array([0,1,1,0,-1,-1,0,2,1,2,0,-2,1,0,-1,0,-1,-1,-1,0,0,-1,0,1,1,0,0,\
          3,0,-1,1,-2,0,2,1,-2,3,2,-3,-1,0,0,1,0,1,1,0,0,-2,-1,1,-2,2,-2,-1,1,1,-1,0,0])

        f_lat = numpy.array([1,1,-1,-1,1,-1,1,1,-1,-1,-1,-1,1,-1,1,1,-1,-1,-1,1,3,1,1,1,-1,\
          -1,-1,1,-1,1,-3,1,-3,-1,-1,1,-1,1,-1,1,1,1,1,-1,3,-1,-1,1,-1,-1,1,-1,1,-1,-1, \
          -1,-1,-1,-1,1])
        
        sin_lat = numpy.array([5128122,280602,277693,173237,55413,46271, 32573, 17198, 9266, \
          8822,8216,4324,4200,-3359,2463,2211,2065,-1870,1828,-1794, -1749, -1565, -1491, \
          -1475,-1410,-1344,-1335,1107,1021,833,777,671,607,596,491,-451,439,422,421,-366,\
          -351,331,315,302,-283,-229,223,223,-220,-220,-185,181,-177,176, 166, -164, 132, \
          -119,115,107.0])

        # Mean longitude of the moon refered to mean equinox of the date.
        coeff0 = numpy.array([-1./6.5194e7,1./538841.,-0.0015786,481267.88123421,218.3164477])
        lprimed = numpy.poly1d(coeff0)
        lprimed = lprimed(t)
        lprimed = self.cirrange(lprimed,rad=0)
        lprime = lprimed*Misc_Routines.CoFactors.d2r
    
        # Mean elongation of the moon
        coeff1 = numpy.array([-1./1.13065e8,1./545868.,-0.0018819,445267.1114034,297.8501921])
        d = numpy.poly1d(coeff1)
        d = d(t)*Misc_Routines.CoFactors.d2r
        d = self.cirrange(d,rad=1)
        
        # Sun's mean anomaly
        coeff2 = numpy.array([1.0/2.449e7,-0.0001536,35999.0502909,357.5291092])
        M = numpy.poly1d(coeff2)
        M = M(t)*Misc_Routines.CoFactors.d2r
        M = self.cirrange(M,rad=1)
        
        # Moon's mean anomaly
        coeff3 = numpy.array([-1.0/1.4712e7,1.0/6.9699e4,0.0087414,477198.8675055,134.9633964])
        Mprime = numpy.poly1d(coeff3)
        Mprime = Mprime(t)*Misc_Routines.CoFactors.d2r
        Mprime = self.cirrange(Mprime,rad=1)
        
        # Moon's argument of latitude
        coeff4 = numpy.array([1.0/8.6331e8,-1.0/3.526e7,-0.0036539,483202.0175233,93.2720950])
        F = numpy.poly1d(coeff4)
        F = F(t)*Misc_Routines.CoFactors.d2r
        F = self.cirrange(F,rad=1)

        # Eccentricity of Earth's orbit around the sun
        e = 1 - 0.002516*t - 7.4e-6*(t**2.)
        e2 = e**2.
        
        ecorr1 = numpy.where((numpy.abs(m_lng))==1)
        ecorr2 = numpy.where((numpy.abs(m_lat))==1)        
        ecorr3 = numpy.where((numpy.abs(m_lng))==2)        
        ecorr4 = numpy.where((numpy.abs(m_lat))==2)                
        
        # Additional arguments.
        A1 = (119.75 + 131.849*t)*Misc_Routines.CoFactors.d2r
        A2 = (53.09 + 479264.290*t)*Misc_Routines.CoFactors.d2r
        A3 = (313.45 + 481266.484*t)*Misc_Routines.CoFactors.d2r
        suml_add = 3958.*numpy.sin(A1) + 1962.*numpy.sin(lprime - F) + 318*numpy.sin(A2)
        sumb_add = -2235.*numpy.sin(lprime) + 382.*numpy.sin(A3) + 175.*numpy.sin(A1-F) + \
            175.*numpy.sin(A1 + F) + 127.*numpy.sin(lprime - Mprime) - 115.*numpy.sin(lprime + Mprime)
        
        # Sum the periodic terms
        geolon = numpy.zeros(jd.size)
        geolat = numpy.zeros(jd.size)
        dist = numpy.zeros(jd.size)
    
        for i in numpy.arange(jd.size):
            sinlng = sin_lng
            coslng = cos_lng
            sinlat = sin_lat
            
            sinlng[ecorr1] = e[i]*sinlng[ecorr1]
            coslng[ecorr1] = e[i]*coslng[ecorr1]
            sinlat[ecorr2] = e[i]*sinlat[ecorr2]
            sinlng[ecorr3] = e2[i]*sinlng[ecorr3]
            coslng[ecorr3] = e2[i]*coslng[ecorr3]
            sinlat[ecorr4] = e2[i]*sinlat[ecorr4]
            
            arg = d_lng*d[i] + m_lng*M[i] + mp_lng*Mprime[i] + f_lng*F[i]
            geolon[i] = lprimed[i] + (numpy.sum(sinlng*numpy.sin(arg)) + suml_add[i] )/1.e6
            dist[i] = 385000.56 + numpy.sum(coslng*numpy.cos(arg))/1.e3
            arg = d_lat*d[i] + m_lat*M[i] + mp_lat*Mprime[i] + f_lat*F[i]
            geolat[i] = (numpy.sum(sinlat*numpy.sin(arg)) + sumb_add[i])/1.e6

        [nlon, elon] = self.nutate(jd)
        geolon =  geolon + nlon/3.6e3
        geolon = self.cirrange(geolon,rad=0)
        lamb = geolon*Misc_Routines.CoFactors.d2r
        beta = geolat*Misc_Routines.CoFactors.d2r    
        
        # Find mean obliquity and convert lamb, beta to RA, Dec
        c = numpy.array([2.45,5.79,27.87,7.12,-39.05,-249.67,-51.38,1999.25,-1.55,-4680.93, \
           21.448])
        junk = numpy.poly1d(c); 
        epsilon = 23. + (26./60.) + (junk(t/1.e2)/3600.)
        # True obliquity in radians
        eps = (epsilon + elon/3600. )*Misc_Routines.CoFactors.d2r
        
        ra = numpy.arctan2(numpy.sin(lamb)*numpy.cos(eps)-numpy.tan(beta)*numpy.sin(eps),numpy.cos(lamb))
        ra = self.cirrange(ra,rad=1)
        
        dec = numpy.arcsin(numpy.sin(beta)*numpy.cos(eps) + numpy.cos(beta)*numpy.sin(eps)*numpy.sin(lamb))

        if rad==1:
            geolon = lamb
            geolat = beta
        else:
            ra = ra/Misc_Routines.CoFactors.d2r
            dec = dec/Misc_Routines.CoFactors.d2r
        
        return ra, dec, dist, geolon, geolat

    def hydrapos(self):
        """
        hydrapos method returns RA and Dec provided by Bill Coles (Oct 2003).
        
        Parameters
        ----------
        None
        
        Return
        ------
        ra = The right ascension of the sun at that date in degrees.
        dec = The declination of the sun at that date in degrees.
        Examples
        --------
        >> [ra,dec] = hydrapos()
        >> print ra, dec
        139.45 -12.0833333333
        
        Modification history
        --------------------             
        Converted to Python by Freddy R. Galindo, ROJ, 06 October 2009.
        """

        ra = (9. + 17.8/60.)*15.
        dec = -(12. + 5./60.)
        
        return ra, dec


    def skynoise_jro(self,dec_cut=-11.95,filename='skynoise_jro.dat',filepath=None):
        """
        hydrapos returns RA and Dec provided by Bill Coles (Oct 2003).
        
        Parameters
        ----------
        dec_cut = A scalar giving  the declination  to get a cut of the skynoise over Jica-
          marca. The default value is -11.95.
        filename = A string to specify name the skynoise file. The default value is skynoi-
          se_jro.dat
        
        Return
        ------
        maxra = The maximum right ascension to the declination used to get a cut.
        ra = The right ascension.
        Examples
        --------
        >> [maxra,ra] = skynoise_jro()
        >> print maxra, ra
        139.45 -12.0833333333
        
        Modification history
        --------------------             
        Converted to Python by Freddy R. Galindo, ROJ, 06 October 2009.
        """

        if filepath==None:
          filepath = '/app/utils/'  
        
        f = open(os.path.join(filepath,filename),'rb')
        
        # Reading SkyNoise Power (lineal scale)
        ha_sky = numpy.fromfile(f,numpy.dtype([('var','<f4')]),480*20)
        ha_sky = ha_sky['var'].reshape(20,480).transpose()
        
        dec_sky = numpy.fromfile(f,numpy.dtype([('var','<f4')]),480*20)
        dec_sky = dec_sky['var'].reshape((20,480)).transpose()
        
        tmp_sky = numpy.fromfile(f,numpy.dtype([('var','<f4')]),480*20)
        tmp_sky = tmp_sky['var'].reshape((20,480)).transpose()
        
        f.close()
        
        nha = 480
        tmp_cut = numpy.zeros(nha)
        for iha in numpy.arange(nha):
            tck = scipy.interpolate.splrep(dec_sky[iha,:],tmp_sky[iha,:],s=0)
            tmp_cut[iha] = scipy.interpolate.splev(dec_cut,tck,der=0)

        ptr = numpy.nanargmax(tmp_cut)
        
        maxra = ha_sky[ptr,0]
        ra = ha_sky[:,0]
        
        return maxra, ra

    def skyNoise(self,jd,ut=-5.0,longitude=-76.87,filename='galaxy.txt',filepath=None):
        """
        hydrapos returns RA and Dec provided by Bill Coles (Oct 2003).
        
        Parameters
        ----------
        jd = The julian date of the day (and time), scalar or vector.
        
        dec_cut = A scalar giving  the declination  to get a cut of the skynoise over Jica-
          marca. The default value is -11.95.
        filename = A string to specify name the skynoise file. The default value is skynoi-
          se_jro.dat
        
        Return
        ------
        maxra = The maximum right ascension to the declination used to get a cut.
        ra = The right ascension.
        
        Examples
         --------
        >> [maxra,ra] = skynoise_jro()
        >> print maxra, ra
        139.45 -12.0833333333
        
        Modification history
        --------------------             
        Converted to Python by Freddy R. Galindo, ROJ, 06 October 2009.
        """

        # Defining date to compute SkyNoise.
        [year, month, dom, hour, mis, secs] = TimeTools.Julian(jd).change2time()
        is_dom = (month==9) & (dom==21)
        if is_dom:
            tmp = jd
            jd = TimeTools.Time(year,9,22).change2julian()
            dom = 22

        # Reading SkyNoise
        if filepath==None:filepath='./resource'        
        f = open(os.path.join(filepath,filename))
        
        lines = f.read()
        f.close()
        
        nlines = 99
        lines = lines.split('\n')
        data = numpy.zeros((2,nlines))*numpy.float32(0.)
        for ii in numpy.arange(nlines):
            line = numpy.array([lines[ii][0:6],lines[ii][6:]])
            data[:,ii] = numpy.float32(line)

        # Getting SkyNoise to the date desired.
        otime = data[0,:]*60.0
        opowr = data[1,:]
        
        hour = numpy.array([0,23]);
        mins = numpy.array([0,59]);
        secs = numpy.array([0,59]);
        LTrange = TimeTools.Time(year,month,dom,hour,mins,secs).change2julday()
        LTtime  = LTrange[0] + numpy.arange(1440)*((LTrange[1] - LTrange[0])/(1440.-1))
        lst = TimeTools.Julian(LTtime + (-3600.*ut/86400.)).change2lst()

        ipowr = lst*0.0
        # Interpolating using scipy (inside max and min "x")
        otime = otime/3600.
        val = numpy.where((lst>numpy.min(otime)) & (lst<numpy.max(otime))); val = val[0]
        tck = scipy.interpolate.interp1d(otime,opowr)
        ipowr[val] = tck(lst[val])

        # Extrapolating above maximum time data (23.75).
        uval = numpy.where(lst>numpy.max(otime))
        if uval[0].size>0:
            ii = numpy.min(uval[0])
            m = (ipowr[ii-1] - ipowr[ii-2])/(lst[ii-1] - lst[ii-2])
            b = ipowr[ii-1] - m*lst[ii-1]            
            ipowr[uval] = m*lst[uval] + b

        if is_dom:
            lst = numpy.roll(lst,4)        
            ipowr = numpy.roll(ipowr,4)

        new_lst = numpy.int32(lst*3600.)
        new_pow = ipowr

        return ipowr, LTtime, lst


class AltAz(EquatorialCorrections):
    def __init__(self,alt,az,jd,lat=-11.95,lon=-76.8667,WS=0,altitude=500,nutate_=0,precess_=0,\
        aberration_=0,B1950=0):
        """
        The AltAz class creates an object which represents the target position in horizontal
        coordinates (alt-az) and allows to convert (using the methods) from  this coordinate
        system to others (e.g. Equatorial).

        Parameters
        ----------
        alt = Altitude in degrees. Scalar or vector.
        az = Azimuth angle in degrees (measured EAST from NORTH, but see keyword WS).  Sca-
          lar or vector.
        jd = Julian date. Scalar or vector.
         lat = North geodetic latitude of location in degrees. The default value is -11.95.
        lon = East longitude of location in degrees. The default value is -76.8667.
        WS = Set this to 1 to get the azimuth measured westward from south.
        altitude = The altitude of the observing location, in meters. The default 500.
        nutate_ = Set this to 1 to force nutation, 0  for no nutation.
        precess_ = Set this to 1 to force precession, 0  for no precession.
        aberration_ = Set this to 1 to force aberration correction, 0  for no correction.
        B1950 = Set this if your RA and DEC are specified in B1950,  FK4 coordinates  (ins-
          tead of J2000, FK5)

        Modification History
        --------------------
        Converted to Object-oriented Programming by Freddy Galindo, ROJ, 26 September 2009.
        """
            
        EquatorialCorrections.__init__(self)
        
        self.alt = numpy.atleast_1d(alt)
        self.az = numpy.atleast_1d(az)
        self.jd = numpy.atleast_1d(jd)
        self.lat = lat
        self.lon = lon
        self.WS = WS
        self.altitude = altitude
        
        self.nutate_ = nutate_
        self.aberration_ = aberration_
        self.precess_ = precess_
        self.B1950 = B1950

    def change2equatorial(self):
        """
        change2equatorial method converts horizon (Alt-Az) coordinates to equatorial coordi-
        nates (ra-dec).
        
        Return
        ------
        ra = Right ascension of object (J2000) in degrees (FK5). Scalar or vector.
        dec = Declination of object (J2000), in degrees (FK5). Scalar or vector.
        ha = Hour angle in degrees.
        
        Example    
        -------
        >> alt = 88.5401  
        >> az = -128.990       
        >> jd = 2452640.5
        >> ObjAltAz = AltAz(alt,az,jd)
        >> [ra, dec, ha] = ObjAltAz.change2equatorial()
        >> print ra, dec, ha
        [ 22.20280632] [-12.86610025] [ 1.1638927]
        
        Modification History
        --------------------
        Written Chris O'Dell Univ. of Wisconsin-Madison, May 2002.
        Converted to Python by Freddy R. Galindo, ROJ, 26 September 2009.
        """

        az = self.az
        alt = self.alt
        if self.WS>0:az = az -180.    
        ra_tmp  = numpy.zeros(numpy.size(self.jd)) + 45.
        dec_tmp = numpy.zeros(numpy.size(self.jd)) + 45.
        [dra1,ddec1,eps,d_psi,d_eps] = self.co_nutate(self.jd,ra_tmp, dec_tmp)
        
        # Getting local mean sidereal time (lmst)
        lmst = TimeTools.Julian(self.jd[0]).change2lst()
        lmst = lmst*Misc_Routines.CoFactors.h2d
        # Getting local apparent sidereal time (last)
        last = lmst + d_psi*numpy.cos(eps)/3600.
        
        # Now do the spherical trig to get APPARENT hour angle and declination (Degrees).
        [ha, dec] = self.change2HaDec()
        
        # Finding Right Ascension (in degrees, from 0 to 360.)
        ra = (last - ha + 360.) % 360.
        
        # Calculate NUTATION and ABERRATION Correction to Ra-Dec
        [dra1, ddec1,eps,d_psi,d_eps] = self.co_nutate(self.jd,ra,dec)
        [dra2,ddec2,eps] = self.co_aberration(self.jd,ra,dec)
        
        # Make Nutation and Aberration correction (if wanted)
        ra = ra - (dra1*self.nutate_ + dra2*self.aberration_)/3600.
        dec = dec - (ddec1*self.nutate_ + ddec2*self.aberration_)/3600.
        
        # Computing current equinox
        j_now = (self.jd - 2451545.)/365.25 + 2000 
        
        # Precess coordinates to current date
        if self.precess_==1:
            njd = numpy.size(self.jd)
            for ii in numpy.arange(njd):
                ra_i = ra[ii]
                dec_i = dec[ii]
                now = j_now[ii]
                
                if self.B1950==1:
                    [ra_i,dec_i] = self.precess(ra_i,dec_i,now,1950.,FK4=1)
                elif self.B1950==0:
                    [ra_i,dec_i] = self.precess(ra_i,dec_i,now,2000.,FK4=0)
            
                ra[ii] = ra_i
                dec[ii] = dec_i
    
        return ra, dec, ha

    def change2HaDec(self):
        """
        change2HaDec method converts from horizon (Alt-Az) coordinates to hour angle and de-
        clination.
        
        Return
        ------
        ha = The local apparent hour angle, in degrees. The hour angle is the time that ri-
          ght ascension of 0 hours crosses the local meridian. It is unambiguisoly defined.
        dec = The local apparent declination, in degrees.
        
        Example    
        -------
        >> alt = 88.5401  
        >> az = -128.990       
        >> jd = 2452640.5
        >> ObjAltAz = AltAz(alt,az,jd)
        >> [ha, dec] = ObjAltAz.change2HaDec()
        >> print ha, dec
        [ 1.1638927] [-12.86610025]
        
        Modification History
        --------------------
        Written Chris O'Dell Univ. of Wisconsin-Madison, May 2002.
        Converted to Python by Freddy R. Galindo, ROJ, 26 September 2009.
        """    

        alt_r = numpy.atleast_1d(self.alt*Misc_Routines.CoFactors.d2r)
        az_r = numpy.atleast_1d(self.az*Misc_Routines.CoFactors.d2r)
        lat_r = numpy.atleast_1d(self.lat*Misc_Routines.CoFactors.d2r)
        
        # Find local hour angle (in degrees, from 0 to 360.)
        y_ha = -1*numpy.sin(az_r)*numpy.cos(alt_r)
        x_ha = -1*numpy.cos(az_r)*numpy.sin(lat_r)*numpy.cos(alt_r) +  numpy.sin(alt_r)*numpy.cos(lat_r)
        
        ha = numpy.arctan2(y_ha,x_ha)
        ha = ha/Misc_Routines.CoFactors.d2r
        
        w = numpy.where(ha<0.)
        if w[0].size>0:ha[w] = ha[w] + 360.
        ha = ha % 360.
        
        # Find declination (positive if north of celestial equatorial, negative if south)
        sindec = numpy.sin(lat_r)*numpy.sin(alt_r) + numpy.cos(lat_r)*numpy.cos(alt_r)*numpy.cos(az_r)
        dec = numpy.arcsin(sindec)/Misc_Routines.CoFactors.d2r
        
        return ha, dec    


class Equatorial(EquatorialCorrections):
    def __init__(self,ra,dec,jd,lat=-11.95,lon=-76.8667,WS=0,altitude=500,nutate_=0,precess_=0,\
                aberration_=0,B1950=0):
        """
        The Equatorial class creates an object which represents the target position in equa-
        torial coordinates (ha-dec)  and allows  to convert  (using the class  methods) from
        this coordinate system to others (e.g. AltAz).
        
        Parameters
        ----------
        ra = Right ascension of object (J2000) in degrees (FK5). Scalar or vector.
        dec = Declination of object (J2000), in degrees (FK5). Scalar or vector.
        jd = Julian date. Scalar or vector.
        lat = North geodetic latitude of location in degrees. The default value is -11.95.
        lon = East longitude of location in degrees. The default value is -76.8667.
        WS = Set this to 1 to get the azimuth measured westward from south.
        altitude = The altitude of the observing location, in meters. The default 500.
        nutate = Set this to 1 to force nutation, 0  for no nutation.
        precess = Set this to 1 to force precession, 0  for no precession.
        aberration = Set this to 1 to force aberration correction, 0  for no correction.
        B1950 = Set this if your RA and DEC are specified in B1950,  FK4 coordinates  (ins-
          tead of J2000, FK5)
        
        Modification History
        --------------------
        Converted to Object-oriented Programming by Freddy Galindo, ROJ, 29 September 2009.
        """

        EquatorialCorrections.__init__(self)
        
        self.ra = numpy.atleast_1d(ra)
        self.dec = numpy.atleast_1d(dec)
        self.jd = numpy.atleast_1d(jd)
        self.lat = lat
        self.lon = lon
        self.WS = WS
        self.altitude = altitude
        
        self.nutate_ = nutate_
        self.aberration_ = aberration_
        self.precess_ = precess_
        self.B1950 = B1950

    def change2AltAz(self):
        """
        change2AltAz method converts from equatorial coordinates (ha-dec) to horizon coordi-
        nates (alt-az).
        
        Return
        ------
        alt = Altitude in degrees. Scalar or vector.
        az = Azimuth angle in degrees (measured EAST from NORTH, but see keyword WS).  Sca-
          lar or vector.
        ha = Hour angle in degrees.
        
        Example    
        -------
        >> ra = 43.370609 
        >> dec = -28.0000 
        >> jd = 2452640.5
        >> ObjEq = Equatorial(ra,dec,jd)
        >> [alt, az, ha] = ObjEq.change2AltAz()
        >> print alt, az, ha
        [ 65.3546497] [ 133.58753124] [ 339.99609002]
        
        Modification History
        --------------------
        Written Chris O'Dell Univ. of Wisconsin-Madison. May 2002
        Converted to Python by Freddy R. Galindo, ROJ, 29 September 2009.
        """

        ra = self.ra
        dec = self.dec
        
        # Computing current equinox
        j_now = (self.jd - 2451545.)/365.25 + 2000
        
        # Precess coordinates to current date
        if self.precess_==1:
            njd = numpy.size(self.jd)
            for ii in numpy.arange(njd):
                ra_i = ra[ii]
                dec_i = dec[ii]
                now = j_now[ii]
                
                if self.B1950==1:
                    [ra_i,dec_i] = self.precess(ra_i,dec_i,now,1950.,FK4=1)
                elif self.B1950==0:
                    [ra_i,dec_i] = self.precess(ra_i,dec_i,now,2000.,FK4=0)
                
                ra[ii] = ra_i
                dec[ii] = dec_i

        # Calculate NUTATION and ABERRATION Correction to Ra-Dec
        [dra1, ddec1,eps,d_psi,d_eps] = self.co_nutate(self.jd,ra,dec)
        [dra2,ddec2,eps] = self.co_aberration(self.jd,ra,dec)
        
        # Make Nutation and Aberration correction (if wanted)
        ra = ra + (dra1*self.nutate_ + dra2*self.aberration_)/3600.
        dec = dec + (ddec1*self.nutate_ + ddec2*self.aberration_)/3600.
        
        # Getting local mean sidereal time (lmst)
        lmst = TimeTools.Julian(self.jd).change2lst()
        
        lmst = lmst*Misc_Routines.CoFactors.h2d
        # Getting local apparent sidereal time (last)
        last = lmst + d_psi*numpy.cos(eps)/3600.
        
        # Finding Hour Angle (in degrees, from 0 to 360.)
        ha = last - ra        
        w = numpy.where(ha<0.)
        if w[0].size>0:ha[w] = ha[w] + 360.
        ha = ha % 360.        

        # Now do the spherical trig to get APPARENT hour angle and declination (Degrees).
        [alt, az] = self.HaDec2AltAz(ha,dec)
        
        return alt, az, ha

    def HaDec2AltAz(self,ha,dec):
        """
        HaDec2AltAz convert hour angle and declination (ha-dec) to horizon coords (alt-az).
        
        Parameters
        ----------
        ha = The local apparent hour angle, in DEGREES, scalar or vector.
        dec = The local apparent declination, in DEGREES, scalar or vector.
        
        Return
        ------
        alt = Altitude in degrees. Scalar or vector.
        az = Azimuth angle in degrees (measured EAST from NORTH, but see keyword WS).  Sca-
          lar or vector.
        
        Modification History
        --------------------
        Written Chris O'Dell Univ. of Wisconsin-Madison, May 2002.
        Converted to Python by Freddy R. Galindo, ROJ, 26 September 2009.
        """

        sh = numpy.sin(ha*Misc_Routines.CoFactors.d2r) ; ch = numpy.cos(ha*Misc_Routines.CoFactors.d2r)
        sd = numpy.sin(dec*Misc_Routines.CoFactors.d2r) ; cd = numpy.cos(dec*Misc_Routines.CoFactors.d2r)
        sl = numpy.sin(self.lat*Misc_Routines.CoFactors.d2r) ; cl = numpy.cos(self.lat*Misc_Routines.CoFactors.d2r)
        
        x = -1*ch*cd*sl + sd*cl
        y = -1*sh*cd
        z = ch*cd*cl + sd*sl
        r = numpy.sqrt(x**2. + y**2.)
        
        az = numpy.arctan2(y,x)/Misc_Routines.CoFactors.d2r
        alt = numpy.arctan2(z,r)/Misc_Routines.CoFactors.d2r
        
        # correct for negative az.
        w = numpy.where(az<0.)
        if w[0].size>0:az[w] = az[w] + 360.
        
        # Convert az to West from South, if desired
        if self.WS==1: az = (az + 180.) % 360.
        
        return alt, az


class Geodetic():
    def __init__(self,lat=-11.95,alt=0):    
        """
        The Geodetic class creates an object which represents the real position on earth of
        a target (Geodetic Coordinates: lat-alt) and allows to convert (using the class me-
        thods) from this coordinate system to others (e.g. geocentric).
        
        Parameters
        ----------
        lat = Geodetic latitude of location in degrees. The default value is -11.95.
        
        alt = Geodetic altitude (km). The default value is 0.
        
        Modification History
        --------------------
        Converted to Object-oriented Programming by Freddy R. Galindo, ROJ, 02 October 2009.
        """

        self.lat = numpy.atleast_1d(lat)
        self.alt = numpy.atleast_1d(alt)
        
        self.a = 6378.16
        self.ab2 = 1.0067397
        self.ep2 = 0.0067397

    def change2geocentric(self):    
        """
        change2geocentric method converts from Geodetic to Geocentric  coordinates. The re-
        ference    geoid is that adopted by the IAU in 1964.
        
        Return
        ------
        gclat = Geocentric latitude (in degrees), scalar or vector.
        gcalt = Geocentric radial distance (km), scalar or vector.
        
        Example    
        -------
        >> ObjGeoid = Geodetic(lat=-11.95,alt=0)
        >> [gclat, gcalt] = ObjGeoid.change2geocentric()
        >> print gclat, gcalt
        [-11.87227742] [ 6377.25048195]
        
        Modification History
        --------------------
        Converted to Python by Freddy R. Galindo, ROJ, 02 October 2009.        
        """

        gdl = self.lat*Misc_Routines.CoFactors.d2r
        slat = numpy.sin(gdl)
        clat = numpy.cos(gdl)
        slat2 = slat**2.
        clat2 = (self.ab2*clat)**2.
        
        sbet = slat/numpy.sqrt(slat2 + clat2)
        sbet2 = (sbet**2.) # < 1
        noval = numpy.where(sbet2>1)
        if noval[0].size>0:sbet2[noval] = 1
        cbet = numpy.sqrt(1. - sbet2)
        
        rgeoid = self.a/numpy.sqrt(1. + self.ep2*sbet2)
        
        x =  rgeoid*cbet + self.alt*clat
        y =  rgeoid*sbet + self.alt*slat

        gcalt = numpy.sqrt(x**2. + y**2.)
        gclat = numpy.arctan2(y,x)/Misc_Routines.CoFactors.d2r
        
        return gclat, gcalt
