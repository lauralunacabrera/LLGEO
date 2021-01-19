c     ******************************************************************
c     TEST OF FORTRAN FORMATTING
c     ******************************************************************
      program fortran_formats
    
c     Variable type
      real*4 my_num

c     Specify number
      my_num = 1.234567

  1   format(F8.2)
  2   format(F8.0)

      write(6, 1) my_num
      write(6, 2) my_num

      end