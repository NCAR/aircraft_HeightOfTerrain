## ----initialization,echo=FALSE,include=FALSE-----------------------------

print ('running HeightOfTerrain')
thisFileName <- "HeightOfTerrain"
require(Ranadu, quietly = TRUE, warn.conflicts=FALSE)
require(ggplot2)
require(grid)
library(knitr)
library(maps)
require(ggthemes)
# require(vioplot)
require(plyr)
opts_chunk$set(echo=FALSE, include=FALSE, fig.lp="fig:")
opts_chunk$set(fig.width=6, fig.height=5, fig.align="center", digits=4)
Directory <- DataDirectory ()
Flight <- "rf12" 		
Project = "DEEPWAVE"	
fname = sprintf("%s%s/%s%s.nc", Directory,Project,Project,Flight)
SaveRData <- sprintf("%s.Rdata.gz", thisFileName)
setwd ('~/RStudio/HeightOfTerrain')

##----------------------------------------------------------
## These are the run options to set via command-line or UI:
GeneratePlots <- TRUE
ShowPlots <- FALSE
ALL <- FALSE
NEXT <- FALSE
Project <- "DEEPWAVE"
Flight <- 12
getNext <- function(ProjectDir, Project) {
  Fl <- sort (list.files (sprintf ("%s%s/", DataDirectory (), ProjectDir),
    sprintf ("%srf..Z.nc", Project)), decreasing = TRUE)[1]
  if (is.na (Fl)) {
    Flight <- 1
  } else {
    Flight <- sub (".*rf", '',  sub ("Z.nc", '', Fl))
    Flight <- as.numeric(Flight)+1
  }
  return (Flight)
}
if (!interactive()) {
  run.args <- commandArgs (TRUE)
  if (length (run.args) > 0) {
    Project <- run.args[1]
    ProjectDir <- Project
    if (grepl ('HIPPO', Project)) {
      ProjectDir <- 'HIPPO'
    }
  } else {
    print ("Usage: Rscript HeightOfTerrain.R Project Flight")
    print ("Example: Rswcript HeightOfTerrain.R DEEPWAVE 12")
    stop ("exiting...")
  }
  if (length (run.args) > 1) {
    if (run.args[2] != 'NEXT') {
      Flight <- as.numeric (run.args[2])
    } else {
      ## Find max rf in data directory,
      ## Use as default if none supplied via command line:
      
      Flight <- getNext(ProjectDir, Project)
    }
  }
} else {  ## this is the interactive section
  x <- readline (sprintf ("Project is %s; CR to accept or enter new project name: ", Project))
  if (nchar(x) > 1) {
    Project <- x
    if (grepl ('HIPPO', Project)) {
      ProjectDir <- 'HIPPO'
    } else {
      ProjectDir <- Project
    }
  }
  x <- readline (sprintf ("Flight is %d; CR to accept, number or 'NEXT' for new flight name: ", Flight))
  if (x == 'NEXT') {
    Flight <- getNext(ProjectDir, Project)
  } else if (nchar(x) > 0 && !is.na(as.numeric(x))) {
    Flight <- as.numeric(x)
  }
}

## Now have run arguments.
## Find lat-long range covered by this flight:
fname <- sprintf ('%s%s/%srf%02d.nc', DataDirectory(), ProjectDir, Project, Flight)
FI <- DataFileInfo (fname)
lt_s <- floor (FI$LatMin) - 1
lt_n <- ceiling (FI$LatMax) + 1
lg_w <- floor (FI$LonMin) - 1
lg_e <- ceiling (FI$LonMax) + 1



## ----download-zip-files, echo=FALSE, eval=TRUE---------------------------

# there should be a subdirectory named 'TerrainData' 
# under the main project directory 
## next line commented and code changed to use TerrainData.
## Reason: otherwise, knitr problems arise from changing wd
# setwd ("./TerrainData")    # Save the data in a subdirectory 
newSRTM <- FALSE  ## the below lines are saved to record how the saved file was made:
subdirs <- c('Islands', 'North_America', 'South_America', 'Eurasia', 'Africa', 'Australia')
if (newSRTM) {
  SRTMdata <- list()
  for (subd in subdirs) {
    url <- sprintf('https://dds.cr.usgs.gov/srtm/version2_1/SRTM3/%s/', subd)
    FLS <- RCurl::getURL(url, dirlistonly=TRUE)
    fls <- strsplit (FLS, '<.*?zip\\">')
    fls <- as.vector(fls[[1]])
    SRTMdata[[sprintf('%s', subd)]]=fls
  }
  save(SRTMdata, file='SRTM.Rdata')
} else {
  load('SRTM.Rdata')  ## this loads SRTMdata
}

###### loop through the needed files
## (This loops twice, first to get an estimate of how much must be downloaded, for the progress meter.)
SRTMfilesNeeded <- 0
for (lt in lt_s:lt_n) {    # latitude limits (note 'S' or 'N' in sprintf statement) 
  for (lg in lg_w:lg_e) {   # longitude limits (note 'E' or 'W') 
    if (lt <= 0) {
      if (lg >= 0) {
        sname <- sprintf ('ZS%dE%03d.gz', -lt, lg)
      } else {
        sname <- sprintf ('ZS%dW%03d.gz', -lt, -lg)
      }
    } else {
      if (lg >= 0) {
        sname <- sprintf ('ZN%dE%03d.gz', lt, lg)
      } else {
        sname <- sprintf ('ZN%dW%03d.gz', lt, -lg)
      }
    }
    if (!file.exists(sprintf ('TerrainData/%s', sname))) {
      dname <- paste0 (sub('^Z', '', sub('.gz$', '', sname)), '.hgt')
      for (subd in subdirs) { 
        ## check if needed file is in this subdirectory; skip if not
        if (sprintf (' %s.zip', dname) %in% SRTMdata[[subd]]) {
          SRTMfilesNeeded <- SRTMfilesNeeded + 1
        }
      }
    }
  }
}
if (SRTMfilesNeeded == 0) {
  print ('SRTM data 100% downloaded')
} else {
  print ('SRTM data 0% downloaded')  
  print (sprintf ('new SRTM files to download: %d', SRTMfilesNeeded))
  SRTMfilesDownloaded <- 0
  print ('Downloading from SRTM database')
  for (lt in lt_s:lt_n) {    # latitude limits (note 'S' or 'N' in sprintf statement) 
    for (lg in lg_w:lg_e) {   # longitude limits (note 'E' or 'W') 
      if (lt <= 0) {
        if (lg >= 0) {
          sname <- sprintf ('ZS%dE%03d.gz', -lt, lg)
          dname <- sprintf ("S%dE%03d.hgt", -lt, lg) # a sq. degree of data 
        } else {
          sname <- sprintf ('ZS%dW%03d.gz', -lt, -lg)
          dname <- sprintf ("S%dW%03d.hgt", -lt, -lg)
        }
      } else {
        if (lg >= 0) {
          sname <- sprintf ('ZN%dE%03d.gz', lt, lg)
          dname <- sprintf ("N%dE%03d.hgt", lt, lg)
        } else {
          sname <- sprintf ('ZN%dW%03d.gz', lt, -lg)
          dname <- sprintf ("N%dW%03d.hgt", lt, -lg)
        }
      }
      print (sprintf('SRTM data %.0f%% downloaded', 100 * SRTMfilesDownloaded / SRTMfilesNeeded))
      if (!file.exists(sprintf ('TerrainData/%s', sname))) {   # Skip if file is already present 
        print (sprintf ('looking for %s (%s)', dname, sname))
        ## search everything! (inefficient, but files are saved once found)
        for (subd in subdirs) { 
          ## check if needed file is in this subdirectory; skip if not
          if (sprintf (' %s.zip', dname) %in% SRTMdata[[subd]]) {   
            url <- sprintf ("https://dds.cr.usgs.gov/srtm/version2_1/SRTM3/%s/%s.zip", subd, dname) 
            if (RCurl::url.exists (url)) { 
              system (sprintf ("wget %s -P TerrainData", url), wait=TRUE) # wget call to do the download 
              SRTMfilesDownloaded <- SRTMfilesDownloaded + 1
              utils::unzip(sprintf("TerrainData/%s.zip", dname), exdir='TerrainData') # and unzip 
	      ## sometimes the file unzips to lower case:
	      if (!file.exists (sprintf ('TerrainData/%s', dname))) {
		      tname <- tolower (dname)
		      if (file.exists (sprintf ('TerrainData/%s', tname))) {
			      system (sprintf ('mv TerrainData/%s TerrainData/%s',
					       tname, dname), wait=TRUE)
		      }
	      }
                
              # then read the whole deg x deg array
              # 'swap' changes from big-endian to little-endian 
              height <- readBin (sprintf ('TerrainData/%s', dname), 'int', size=2, n=1201*1201, endian='swap')
              height [height == -32768] <- NA     # set NA for missing values 
              dim (height) <- c(1201,1201)        # Make into a matrix 
              save (height, file=sprintf ('TerrainData/%s', sname), compress='gzip') 
              unlink (sprintf("TerrainData/%s.zip", dname)) # delete the zip file 
              unlink (sprintf ('TerrainData/%s', dname)) # and the unzipped file 
            }
          }
        } 
      } 
    } 
  }
}
print ('SRTM download done')
print ('Process to find SFC 0% done')

## ----height-function, echo=TRUE, include=TRUE----------------------------

HeightOfTerrain <- function (.lat, .long) { 
  lt <- floor (.lat) 
  lg <- floor (.long) 
  if (is.na(lt)) {return (NA)} 
  if (is.na(lg)) {return (NA)} 
  if (lt < 0) { 
    NS <- "S" 
    lt <- -lt 
  } else {
    NS <- "N" 
  } 
  if (lg < 0) {
    EW <- "W" 
    lg <- -lg
  } else { 
    EW <- "E" 
  } 
  vname <- sprintf("TerrainData/Z%s%02d%s%03d", NS, lt, EW, lg) 
  if (!exists(vname, .GlobalEnv)) { 
    zfile <- sprintf("%s.gz", vname) 
    if (file.exists(zfile)) { 
      load(file=zfile) 
      assign (vname, height, envir=.GlobalEnv) 
    } else { 
      return (NA) 
    } 
  } 
  ix <- as.integer ((.long - floor (.long) + 1/2400) * 1200) + 1 
  iy <- as.integer ((ceiling(.lat) - .lat + 1/2400) * 1200) + 1 
  if (ceiling (.lat) == .lat) { # exact match fails; correct it
    iy <- 1201
  }
  hgt <- get(vname, envir=.GlobalEnv)[ix, iy] 
  return (hgt) 
}

## ----test vs USGS:
# require(RCurl)
# n <- 5
# HOT <- vector ("numeric", n)
# USGS <- vector ("numeric", n)
# ltt <- runif (n, lt_s, lt_n)
# lgg <- runif (n, lg_w, lg_e)
# for (i in 1:n) {
#   HOT[i] <- HeightOfTerrain (ltt[i], lgg[i])
#   url <- sprintf ("https://nationalmap.gov/epqs/pqs.php?x=%f&y=%f&units=Meters&output=json", lgg[i], ltt[i])
#   USGS[i] <- as.numeric (strsplit (strsplit (RCurl::getURL(url), 'Elevation\":')[[1]][2], ',.*'))
# }
# meanDiff <- mean (HOT-USGS, na.rm=TRUE)
# sdDiff <- sd (HOT-USGS, na.rm=TRUE)
# print (sprintf ("mean difference: %f", meanDiff))
# print (sprintf ("std dev: %f", sdDiff))
# hist (HOT-USGS, breaks=50, xlim=c(-10,10))

## elevations were also verified in the Southern hemisphere by reference to 
## http://www.mapcoordinates.net/en .


## ----add-variables-to-netCDF-file, echo=TRUE, include=TRUE---------------

fname <- sprintf("%s%s/%srf%02d.nc", DataDirectory (), Project, Project, Flight)
fnew <- sprintf("%s%s/%srf%02dZ.nc", DataDirectory (), Project, Project, Flight) 
# copy file to avoid changing original: 
Z <- file.copy (fname, fnew, overwrite=TRUE) ## Z just avoids printing
# load data needed to calculate the new variables:
## Data <- getNetCDF (fnew, c("LATC", "LONC", "GGALT", "GGEOIDHT")) 
Data <- getNetCDF (fnew, c("LATC", "LONC", "GGALT"))  ## don't need GGEOIDHT: error in original ALTG 
SFC <- vector ("numeric", length(Data$Time)) 
netCDFfile <- nc_open (fnew, write=TRUE) 
for (i in 1:length (Data$Time)) {
  if (i %% 2000 == 0) {
    print (sprintf('Process to find SFC %.0f%% done', 100 * i / length (Data$Time)))
  }
  if (is.na(Data$LATC[i])) {next} 
  if (is.na(Data$LONC[i])) {next} 
  SFC[i] <- HeightOfTerrain (Data$LATC[i], Data$LONC[i]) 
  # if (i %in% 2000:2100) {sprintf("%f %f %f", SFC[i], Data$LATC[i], Data$LONC[i])} 
}
SFC[is.na(SFC)] <- 0  ## assumed over ocean if missing
# print (summary(SFC)) 
# print (TellAbout(SFC)) 
## ALTG <- Data$GGALT - Data$GGEOIDHT - SFC    ## error in original (DEEPWAVE)
Data$ALTG <- Data$GGALT - SFC 
Data$SFC <- SFC 
print ('modify netCDF file to add SFC and ALTG')


## ----modify-netCDF-file--------------------------------------------------

varSFC <- ncvar_def ("SFC", "m", netCDFfile$dim["Time"], -32767., "Elevation of the Earth's surface below the aircraft position") 
varALTG <- ncvar_def ("ALTG", "m", netCDFfile$dim["Time"], -32767., "Altitude of the aircraft above the Earth's surface")
newfile <- ncvar_add (netCDFfile, varSFC) 
newfile <- ncvar_add (newfile, varALTG) 
ncvar_put (newfile, "SFC", Data$SFC) 
ncvar_put (newfile, "ALTG", Data$ALTG) 
nc_close (newfile)


## ----plot-flight-track, include=TRUE, fig.cap="The flight track for the GV on flight 12 of the DEEPWAVE project."----
print ("generating plots")
png (file='HOTplots/track.png', width=900, height=600, res=150)
plotTrack (Data, .Spacing=60, .WindFlags=2)
title (sprintf ('%srf%02d', Project, Flight))
invisible(dev.off())

# print (summary(SFC))


## ----plot-terrain-height, include=TRUE, fig.cap="The elevation of the terrain below the position of the aircraft during Flight 12 of the DEEPWAVE project."----

Data$ALTG[Data$ALTG < -32000] <- NA
png (file='HOTplots/HOT.png', width=900, height=600, res=150)
with(Data, plotWAC (data.frame (Time, GGALT, ALTG, SFC),
  legend.position=NA))
title (sprintf ('%srf%02d', Project, Flight))
invisible (dev.off())

print ('-- DONE --')

