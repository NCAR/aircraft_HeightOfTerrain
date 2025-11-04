## Description
This directory, intended to be a project directory for Rstudio, contains an R program and associated files for constructing a variable representing the height of the terrain under the coordinates of a flight track of a research aircraft. That altitude is determined using data from the Shuttle Radar Topography Mission. The R program adds a variable called SFC_SRTM to a netCDF file that is in the format provided by the NCAR Research Aviation Facility. It is set to cover the region of a generic US_based research project, but it can be modified to cover different project regions. The result is a duplicate of the original data file with two variables added, SFC_SRTM to represent the surface height and ALTG_SRTM to represent the altitude above ground at the flight level of the aircraft.

Variable names are SFC_SRTM and ALTG_SRTM to document the reference sfc altitude database used.

Notes from past runs of the code are on the EOL RAF Science wiki:
https://wiki.ucar.edu/spaces/RS/pages/361245600/Aircraft+Altitude+from+Pressure+Alt+and+Terrain+Ht

Additional details about the code can be found in the Wiki portion of the code repository:
https://github.com/NCAR/aircraft_HeightOfTerrain/wiki

# To use this code (brief)
The code will need to be checked out in your home dir in an Rstudio subdir, eg ~/Rstudio/aircraft_HeightOfTerrain

## Running via the script
Edit AddHtTerrain and change the project and rate at the top. If you are
running from run_all, then comment out the DAT line. Run the script and review
the generated command to ensure they are correct. Once you are satisfied, edit
AddHtTerrain again and uncomment the Rscript command at the bottom to run for
real.

## Running manually (good for debugging)

### Point the code at the terrain height database
Determine if all the areas you need are available locally and then edit the
.Rnw file so the variable TdbData points to the location of the TerrainData
 files.

I ran the code blindly and it downloaded a bunch of zero-length files, which
told me what I needed. I compared that file list to the files avaliable in the
TerrainData dir.

### Compile the code into an R script:
> Rscript -e "library(knitr); knitr::purl('HeightOfTerrain.Rnw')"

Run the compiled code, use the bounding box from the project and run:
> Rscript HeightOfTerrain.R <project> <flight> <data_dir> <lat_s> <lat_n> <lon_w> <lon_e>
eg: Rscript HeightOfTerrain.R GOTHAAM rf20 /scr/raf/Prod_Data/GOTHAAM/LRT 35 45 -80 -70 no

### Install missing packages
If you run the code and get messages about missing packages, you can install them in your local home directory.  To install packages:
> R
R> chooseCRANmirror(68)
- it will skip bringing up a window and let you select
then:
R>install.packages("ncdf4") or whatever

### If curl downloads files of zero size, you can download them manually.
I did not do this for GOTHAAM because I had a copy of the needed files. I believe once they are downloaded, the code will still do the endian switch, but I didn't test that, so it might need work.
> for file in `ls *zip`; do curl https://www.viewfinderpanoramas.org/dem3/${file} -o $file ; done
