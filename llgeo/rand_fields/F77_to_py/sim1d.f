c     ******************************************************************
c     *                                                                *
c     *                       subroutine sim1d                         *
c     *                                                                *
c     ******************************************************************
c     Latest Update: November 28, 2020
c
c     PURPOSE:
c     This subroutine is similar to Dr. Fenton's sim1d, except it is
c     designed to be compiled with F2PY and used from Python. It calls
c     LAS1G with a pre-selected covariance function.
c
c     Can only do non-conditioned 1D random fields!
c
c     To be compileds using F2PY: https://numpy.org/doc/stable/f2py/
c
c
c     ARGUMENTS:
c        Z (output)
c           real array, which will contain the realization of the 2-D 
c           process in the first n locations. Extra size is used as 
c           workspace to store previous stages in the subdivision.
c     
c        n (input)
c           number of cells to discretize the field. Note that the field
c           resolution given by n must be such that N = k1 * 2**m where
c           k1 is a positive integer in the range [1, 16] and m is an 
c           integer in the range [0, 16]. Thus, the largest value of n
c           is 1,048,576, although here it must also be less than MXN. 
c           An error message will be issued if n does not satisfy the 
c           above equation.
c
c        xl (input)
c           physical dimensions of the process
c
c        zm (input)
c           mean of the random process
c
c        zv (input)
c           point variance of the random process
c
c        thx (input)
c           scale of fluctuation of the random process
c
c        fncnam (input)
c           character string of length 6, which contains the name of
c           the supplied variance function. This names must be one of:
c
c              'dlace1' -> 1D Damped oscillatory noise process
c              'dlafr1' -> 1D Fractional Gaussian noise model.
c                          Requires (H, delta) where H is thx and
c                          delta is the cell dimension.
c              'dlavx1' -> 1D Exponentially decaying (Markov) model.
c                          Requires scale of fluctuaction.
c              'dlsmp1' -> 1D Simple polynomial decaying covariance.
c              'dlspx1' -> 1D Gaussian decaying correlation model.
c                          requires scale of fluctuation.
c
c        pa (input)
c           Typically the point variance of the random process. It's the 
c           first additional parameter for the covariance function.
c           Not that this will be set as part of common block parameters
c           but wanted to avoid having to do that from Python (although
c           it is perfectly doable). 
c
c        pb (input)
c           Typically not used, unless covariance function requires two
c           parameters (it's the second additional parameter).
c           Not that this will be set as part of common block parameters
c           but wanted to avoid having to do that from Python (although
c           it is perfectly doable). 
c
c        kseed (input)
c           Integer seed to be used to initialize the pseudo-random 
c           number generator. The generator is only initialized on the 
c           first call to this routine or when abs(ii) = 1
c           If kseed = 0, then a random seed will be used. 
c
c        iout (input)
c           Unit number onto which error and warning messages are logged
c
c        ii (input)
c           Must be equal to 1 the first time LAS1G is being called.
c    
c     PARAMETERS:
c           MXN = maximum number of points in the field
c
c     EXTERNAL MODULES:
c           This program uses modules from the library:
c           1) libGAF.so (must be dynamically compiled library)
c 
c     ******************************************************************
     
      subroutine sim1d(z, n, xl, zm, zv, thx, fncnam, pa, pb, kseed,
     >                 iout, ii)

c     -------------- variable intents and types of F2PY ----------------
cf2py intent(out)  z
cf2py intent(in)   n
cf2py intent(in)   xl
cf2py intent(in)   zm
cf2py intent(in)   zv
cf2py intent(in)   thx
cf2py intent(in)   fncnam
cf2py intent(in)   pa
cf2py intent(in)   pb
cf2py intent(in)   kseed
cf2py intent(in)   iout
cf2py intent(in)   ii

c     ------------------------ variable definitions --------------------
c     Basic parameters
      parameter(MXN = 16384)
      integer n, kseed, nbh, iout, ii
      real z(2*n), xl
      real*8 zm, zv, thx, pa, pb
      character*6 fncnam
      character*24 rdate
      logical lcomp
      
c     Variance functions in GAF77      
      real*8   dlace1, dlafr1, dlavx1, dlsmp1, dlspx1
      external dlace1, dlafr1, dlavx1, dlsmp1, dlspx1
      real*8         dpa, dpb, dthx, dthy, dthz
      common/dparam/ dpa, dpb, dthx, dthy, dthz

c     Format specigiers
   1  format(a,a,a) 
   2  format(3F5.2)

c ---------------------- set-up basic parameters -----------------------
      nbh = 3

c     Export common block parameters
      dthx = dble(thx)
      dpa  = dble(pa)
      dpb  = dble(pb)

c ------------------------- set-up a debugging file --------------------
      call fdate(rdate)
      open(iout, file = 'sim1d.stats', status = 'UNKNOWN')
      write(iout,1) rdate
      write(iout,1) 'The common block parameters are:'
      write(iout,2) dpa, dpb, dthx

      if( n .gt. MXN ) then
         write(iout, *) 'Process too long. Max = ', MXN, 'points\n'
         stop
      endif

c --------------------- get random field realization  ------------------
      if     (lcomp('dlace1', fncnam)) then
         write(iout, 1) 'Using dlace1 covariance function'
         call las1g(z, n, xl, dlace1, nbh, kseed, ii, iout)

      elseif (lcomp('dlafr1', fncnam)) then
         write(iout, 1) 'Using dlafr1 covariance function'
         call las1g(z, n, xl, dlafr1, nbh, kseed, ii, iout)
         
      elseif (lcomp('dlavx1', fncnam)) then
         write(iout, 1) 'Using dlavx1 covariance function'
         call las1g(z, n, xl, dlavx1, nbh, kseed, ii, iout)

      elseif (lcomp('dlsmp1', fncnam)) then
         write(iout, 1) 'Using dlsmp1 covariance function'
         call las1g(z, n, xl, dlsmp1, nbh, kseed, ii, iout)

      elseif (lcomp('dlspx1', fncnam)) then
         write(iout, 1) 'Using dlspx1 covariance function'
         call las1g(z, n, xl, dlspx1, nbh, kseed, ii, iout)

      else
         write(iout, 1) 'Unknown covariance function'
         stop

      endif

c     Scale to proper distribution
      do 50 i = 1, n
            Z(i) = zm + Z(i)
   50 continue

c     Report progress, close, and end routine   
      write(iout, *) 'Sim number and seed:', ii, kseed
      close(iout)
      return
      end