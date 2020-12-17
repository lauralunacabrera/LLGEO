c     ******************************************************************
c     *                                                                *
c     *                       subroutine sim2d                         *
c     *                                                                *
c     ******************************************************************
c     Latest Update: November 28, 2020
c
c     PURPOSE: 
c     This subroutine is similar to Dr. Fenton's sim2d, except it is 
c     designed to be compiled with F2PY and used from Python. It calls
c     LAS2G with a pre-selected covariance function.
c
c     Can only do non-conditioned 2D random fields!
c
c     To be compiled using F2PY: https://numpy.org/doc/stable/f2py/
c
c     ARGUMENTS (from LAS2G):
c
c     Z (output)
c          real array of size >= N1 x (5*N2/4) which on output will
c          contain the realization of the 2-D process in the first N1xN2
c          locations. When dimensioned as Z(N1,5*N2/4) in the calling
c          routine and indexed as Z(i,j), Z(1,1) is the lower left cell, 
c          Z(2,1) is the next cell in X direction (to the right), etc.,
c          while Z(1,2) is the next cell in the Y direction (upwards).
c          The extra space is required for workspace (to store
c          the previous stage in the subdivision). (output)
c
c     N1 and N2 (input)
c          no. of cells to discretize the field in the x and y direction
c          respectively (corresponding to the 1st and 2nd indices of Z
c          respectively). Both N1 and N2 must have the form: N1=k1*2**m
c          and N2=k2*2**m where m is common to both and k1 and k2 are
c          positive integers satisfying k1*k2 <= MXK. Generally k1 & k2
c          are chosen to be as large as possible and still satisfy the 
c          above requirements so the the first stage involves directly 
c          simulating a k1xk2 field by inversion of a covariance matrix.
c          A potential example is (N1,N2)=(160,256) which gives k1=5,
c          k2=8, and m=5. Note that in general N1 & N2 cannot be chosen
c          arbitrarily - it is usually best to choose m first then
c          k1 & k2 so as to satisfy or exceed the problem requirements. 
c          Note that because of the requirements on k1*k2, N1 cannot be
c          more than MXK times as big (or smaller) than N2.
c
c     XL and YL (input)
c          physical dimensions of the process.
c  
c     dvarfn (input)
c          external real*8 function which returns the variance of the
c          random process averaged over a given area. dvarfn is
c          referenced as follows:   var = dvarfn( V1, V2 )
c          where (V1,V2) are the side dimensions of the rectangular 
c          averaging domain. Any other parameters to the function 
c          must be passed by common block from the calling routine.
c          Note that the variance of the random process averaged over 
c          the area (V1 x V2) is the product of the point variance and 
c          the traditionally defined "variance" function, as discussed 
c          by Vanmarcke (pg 186).
c
c     KSEED (input)
c          integer seed to be used to initialize the pseudo-random number
c          generator. The generator is only initialized on the first call
c          to this routine or when abs(INIT) = 1.
c          If KSEED = 0, then a random seed will be used (based on the
c          process ID of the current program invocation - see iseed.f)
c          On output, KSEED is set to the value of the actual seed used.
c
c     OUTNAM (input) 
c          Name of file onto which debugging info will be printed (12 char max).
c
c     II (input)
c          must be equal to 1 the first time LAS2G is being called.
c
c     PARAMETERS:
c     MXN = maximum field size (MXN x MXN)
c     
c     NOTES:
c     A few important notes on F2PY:
c     1) F2PY does not like arrays with allocatable size, ex. Z(*), 
c        because C++ does not allow for those.
c     2) Variable intents must be declared using cf2py statements which 
c        are ignored by Fortran but used to generate the F2PY signature
c        file.
c     ******************************************************************

      subroutine sim2d(Z, N1, N2, XL, YL, zm, zv, thx, thy, fncnam,
     >                 pa, pb, kseed, outnam, ii)

c     -------------- variable intents and types of F2PY ----------------
cf2py intent(out) Z
cf2py intent(in)  N1
cf2py intent(in)  N2
cf2py intent(in)  XL
cf2py intent(in)  YL
cf2py intent(in)  thx
cf2py intent(in)  thy
cf2py intent(in)  zm
cf2py intent(in)  zv
cf2py intent(in)  fncnam
cf2py intent(in)  pa
cf2py intent(in)  pb
cf2py intent(in)  kseed
cf2py intent(in)  outnam
cf2py intent(in)  ii

c     ----------------------- Variable Definitions ---------------------
c     Basic parameters
      parameter(MXN = 256)
      integer N1, N2, kseed, iout, ii
      real    Z(2*N1*N2)
      real*8  zm, zv, pa, pb, thx, thy, XL, YL
      character*6 fncnam
      character*24 rdate, outnam
      logical lcomp 

c     Variance functions in GAF77, and appropriate parameters
      real*8   dlavx2, dlspx2
      external dlavx2, dlspx2
      real*8   dpa, dpb, dthx, dthy, dthz
      common/dparam/ dpa, dpb, dthx, dthy, dthz
      
c     Format specifiers
   1  format(a,a,a)
   2  format(5F10.2)
   3  format(a, i3, i9, F5.2)
   4  format(i4, i4, 4F5.2)

c ---------------------- set-up basic parameters -----------------------
c     Export common block parameters
      dpa  = dble(pa)
      dpb  = dble(pb)
      dthx = dble(thx)
      dthy = dble(thy)
      
c     ---------------------- set-up stats file -------------------------
      iout = 8
      i = lnblnk(outnam)
      call fdate(rdate)
      open(iout, file = outnam(1:i), status = 'UNKNOWN')
      write(iout, *) rdate
      write(iout, *) 'pa. pb. thx. thy, thz'
      write(iout, *) dpa, dpb, dthx, dthy, dthz
      write(iout, *) 'N1, N2, XL, YL, zm, zv'
      write(iout, *)  N1, N2, XL, YL, zm, zv

c     ---------------------------- checks-------------------------------
c     Check field size
      N12 = N1 * N2
      if (N12 .gt. MXN * MXN) then
            write(iout, 1) 'Error: Problem too big! Reduce resolution'
            stop
      endif

c     Check covariance function
      if(.not.(lcomp('dlavx2',fncnam) .or. lcomp('dlspx2',fncnam))) then
            write(iout, 1) 'Error: Unkown covariance function'
            stop
      endif

c     ---------- call LAS2G, depending on specified fncnam -------------
      write(iout, 1) 'Starting field generation'

c     Change variance to 1, will adjust later
      dpa = 1.d0

c     Generate uniform standard random field
      if (lcomp('dlavx2', fncnam)) then
            write(iout, 1) 'Using dlavx2 covariance function'
            write(iout, *) 'my_sim2d.f  :  ', N1, N2, XL, YL
            call las2g( Z, N1, N2, XL, YL, dlavx2, kseed, ii, iout)

      elseif (lcomp('dlspx2', fncnam)) then
            write(iout, 1) 'Using dlspx2 covariance function'
            call las2g( Z, N1, N2, XL, YL, dlspx2, kseed, ii, iout)
      endif

c     Write info to stats file      
      write(iout, 1) 'Done with the standard random field'
      if (ii .eq. 1) then
            write(iout, *) 'Generator seed used = ', kseed
      endif

c     Scale to desired normal distribution (TO DO CHANGE HERE!)
      do 50 i = 1, N1*N2
            Z(i) = zm + sqrt(zv) * Z(i)
   50 continue

c     Report progress, close, and end routine   
      write(iout, *) 'Sim number and seed:', ii, kseed
      close(iout)
      return
      end