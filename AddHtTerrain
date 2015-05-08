#!/bin/sh

Rscript -e "library(knitr); knitr::purl('HeightOfTerrain.Rnw')"

if [ "$1" == "" ]; then
   echo "Must include project name on command-line, e.g. AddHtTerrain FRAPPE"
   exit
fi

project=$1
if [ "$project" == "DEEPWAVE" ]; then
   lt_s="-60"
   lt_n="-20"
   lg_w="130"
   lg_e="-150"
else
   lt_s=$2
   lt_n=$3
   lg_w=$4
   lg_e=$5
fi
echo "Adding Terrain Ht vars to production netCDF files for project $project"
echo "Using lat/long range $lt_s - $lt_n, $lg_w - $lg_e"

for file in `ls /scr/raf/Prod_Data/$project/${project}rf??.nc`
do
    flight=${file:(-7):4}
    Rscript HeightOfTerrain.R $project $flight $lt_s $lt_n $lg_w $lg_e
done
