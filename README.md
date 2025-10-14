# Aircraft Height of Terrain
This directory contains a Python program and associated files for constructing a variable representing the height of the terrain under the coordinates of a flight track of a research aircraft. Terrain altitude is determined using data from the Shuttle Radar Topography Mission (SRTM).

The Python script adds two variables to a netCDF file in the format provided by the NCAR Research Aviation Facility. The variable names should include SRTM to reference the altitude database used:
 - **SFC_SRTM**: Surface height (terrain altitude from SRTM)
 - **ALTG_SRTM**: Altitude above ground at the flight level of the aircraft

## To run HeightOfTerrain:

### Install required Python packages from the environment.yml and activate your environment

    conda env create -f environment.yml  
    conda activate ncHtTerrain

### Run from the command line: 
`python HeightOfTerrain <PROJECT> <FLIGHT> <DATA_DIRECTORY> <MIN_LAT> <MAX_LAT> <MIN_LON> <MAX_LON>`  
*\<PROJECT\>*: Project name (e.g., CAESAR)   
*\<FLIGHT\>*: Flight number (e.g., rf05)  
*\<DATA_DIRECTORY\>*: Directory containing netCDF files  
*\<MIN_LAT\> \<MAX_LAT\>*: Latitude bounds  
*\<MIN_LON\> \<MAX_LON\>*: Longitude bounds

### Alternatively, install using scons, and then run from the command line anywhere on your system

    scons
    scons install
    HeightOfTerrain <PROJECT> <FLIGHT> <DATA_DIRECTORY> <MIN_LAT> <MAX_LAT> <MIN_LON> <MAX_LON>


## Detailed instructions on the history of this code are on the wiki:

You can read more about the origins of this code in the HeightOfTerrainNOMADSS.pdf included in this repo, or in the accompanying Wiki that will link to the original repository of R code.
https://github.com/NCAR/aircraft_HeightOfTerrain/wiki