# LLGEO
### A Python Library for Geotechnical Engineering Applications

This is a test version!



TODO:
1) utilities -> formatters
    num2str and arr2str functions are an absolute disaster. Really need to fix them.


STRUCTURE

props_nonlinear/
    darandeli_2011.py

quad4m/
    genfiles.py
    geometry.py
    soildat.py

rand_fields/
    LAS.py
    F77_to_py/


VERSION 0.0.3
- llgeo/quad4m/genfiles.py : added genfiles.py, which generates input files for QUAD4M. Note that KSAV and KOUT flags were not coded in so far, and will need to be added in later.
- llgeo/quad4m/geometry.py : fixed orientation of nodes (was clockwise instead of counter-clockwise)


VERSION 0.0.4
- llgeo/quad4m/          : improved documentation of all existing modules
- New modules:
    - llgeo/basic_stats
    - llgeo/cpt_interp
    - llgeo/plotting
    - llgeo/randfields

VERSION 0.0.5
- Decreased python version required to 3.6
