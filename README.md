﻿This directory, intended to be a project directory for Rstudio, contains an R program and associated files for constructing a variable representing the height of the terrain under the coordinates of a flight track of a research aircraft. That altitude is determined using data from the Shuttle Radar Topography Mission. The R program adds a variable called SFC to a netCDF file that is in the format provided by the NCAR Research Aviation Facility. It is set to cover the region of the DEEPWAVE research project, but it can be modified to cover different project regions. The result is a duplicate of the original data file with two variables added, SFC to represent the surface height and ALTG to represent the altitude above ground at the flight level of the aircraft.


Variable names should be SFC_SRTM and ALTG_SRTM to document the reference sfc altitude database used.

For instructions on how to use this code:
http://wiki.eol.ucar.edu/rafscience/Aircraft%20Altitude%20from%20Pressure%20Alt%20and%20Terrain%20Ht

To run HeightOfTerrain:
- go to tikal.eol.ucar.edu in a browser and login with tikal pwd
> Rscript -e "library(knitr); knit('HeightOfTerrainNOMADSS.Rnw’)"

— or —

> Rscript -e "library(knitr); knitr::purl('HeightOfTerrainNOMADSS.Rnw')"
> R CMD BATCH HeightOfTerrainNOMADSS.R

To run from the command line you must include the project and flight as
options:
Rscript HeightOfTerrainNOMADSS.R FRAPPE rf04
