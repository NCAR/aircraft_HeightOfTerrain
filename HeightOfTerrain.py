import os
import sys
import gzip
import zipfile
import urllib.request
import numpy as np
import pandas as pd
import netCDF4
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
import datetime
import argparse

# Configuration
TdbData = "./TerrainData"
thisFileName = "HeightOfTerrain"

def datetoday():
    """Returns the current date in 'Day Month Year' format."""
    now = datetime.datetime.now()
    month_names = ["January", "February", "March", "April", "May", "June",
                   "July", "August", "September", "October", "November", "December"]
    return f"{now.day} {month_names[now.month - 1]} {now.year}"

def parse_args():
    parser = argparse.ArgumentParser(description='Process terrain height data.')
    parser.add_argument('Project', type=str, nargs='?', default='CAESAR', help='Project name')
    parser.add_argument('Flight', type=str, nargs='?', default='rf05', help='Flight number')
    parser.add_argument('Directory', type=str, nargs='?', default='/Users/srunkel/dev/Data/dat', help='Directory path')
    parser.add_argument('lt_s', type=int, nargs='?', default=37, help='Southern latitude')
    parser.add_argument('lt_n', type=int, nargs='?', default=41, help='Northern latitude')
    parser.add_argument('lg_w', type=int, nargs='?', default=-111, help='Western longitude')
    parser.add_argument('lg_e', type=int, nargs='?', default=-99, help='Eastern longitude')
    parser.add_argument('Tdb', type=str, nargs='?', default='yes', help='Terrain database flag')
    return parser.parse_args()

def HeightOfTerrain(lat, lon):
    lt = int(np.floor(lat))
    lg = int(np.floor(lon))
    if np.isnan(lt) or np.isnan(lg):
        return np.nan
    NS = 'S' if lt < 0 else 'N'
    lt = abs(lt)
    EW = 'W' if lg < 0 else 'E'
    lg = abs(lg)
    vname = f"{NS}{lt:02d}{EW}{lg:03d}"
    hgt_file = f"{vname}.hgt"
    
    # Search for the .hgt file in the subfolders
    for root, dirs, files in os.walk(TdbData):
        if hgt_file in files:
            hgt_file_path = os.path.join(root, hgt_file)
            try:
                with open(hgt_file_path, 'rb') as f:
                    height = np.fromfile(f, dtype='>i2').astype(np.float32) # ensure float32
                height[height == -32768] = np.nan
                height = height.reshape(1201, 1201)
                ix = int((lon - np.floor(lon) + 1/2400) * 1200)
                iy = int((np.ceil(lat) - lat + 1/2400) * 1200)
                if np.ceil(lat) == lat:
                    iy = 1200
                hgt = height[ix, iy]
                return hgt
            except FileNotFoundError as e:
                print(e)
                return np.nan
    print(f"File not found: {hgt_file}")
    return np.nan

def main():
    args = parse_args()

    Project = args.Project
    Flight = args.Flight
    Directory = args.Directory
    lt_s = args.lt_s
    lt_n = args.lt_n
    lg_w = args.lg_w
    lg_e = args.lg_e
    Tdb = args.Tdb

    fname = f"{Directory}/{Project}{Flight}.nc"
    print(f"Processing {fname} {Tdb}")
    lettr = '';
    numbr = '';
    if Tdb == "yes":
        if not os.path.exists(TdbData):
            os.makedirs(TdbData)
        os.chdir(TdbData)
        for lt in range(lt_s, lt_n + 1):
            lettr = lt // 4 + 1
            NS = 'N' if lt >= 0 else 'S'
            if lg_w > lg_e:
                lrange = list(range(lg_w, 181)) + list(range(-180, lg_e + 1))
            else:
                lrange = range(lg_w, lg_e + 1)
            for lg in lrange:
                EW = 'E' if lg >= 0 else 'W'
                sname = f"Z{NS}{abs(lt)}{EW}{abs(lg):03d}.gz"
                dname = f"{NS}{abs(lt):02d}{EW}{abs(lg):03d}.hgt"
                
                numbr = 30 + lg // 6 + 1
                if lt < 0:
                    FileName = f"S{chr(ord('A') - lettr)}{numbr:02d}"
                else:
                    FileName = f"{chr(ord('A') + lettr - 1)}{numbr:02d}"
                if os.path.exists("TerrainData/"+FileName):
                    continue
                else:
                    zipFileName = f"{FileName}.zip"
                    if not os.path.exists(zipFileName):
                        print("Downloading ", zipFileName)
                        url = f"http://www.viewfinderpanoramas.org/dem3/{zipFileName}"
                        try:
                            urllib.request.urlretrieve(url, zipFileName)
                        except urllib.error.URLError:
                            print(f"Could not download {zipFileName} from {url}")
                            continue
                    try:
                        if not os.path.exists(os.path.join(TdbData, dname)):
                            with zipfile.ZipFile(zipFileName, 'r') as zip_ref:
                                zip_ref.extractall(TdbData)
                            print(f"Extracted {zipFileName}")
                        else:
                            print(f"{dname} already exists, skipping extraction.")
                    except zipfile.BadZipFile:
                        print(f"Bad zip file: {zipFileName}")
                        continue
                    if os.path.exists(dname):
                        with open(dname, 'rb') as f:
                            height = np.fromfile(f, dtype='>i2').astype(np.float32)
                        height[height == -32768] = np.nan
                        height = height.reshape(1201, 1201)
                        with gzip.open(sname, 'wb') as f:
                            np.save(f, height)
                        print(f"Saved {sname}")

        os.chdir("..")
        print("Done loading Terrain Database")

    fnew = f"{Directory}/{Project}{Flight}Z.nc"
    print(f"Copy file {fname} to {fnew}")
    os.system(f"cp {fname} {fnew}")

    nc_data = netCDF4.Dataset(fnew, 'r+')
    LATC = nc_data.variables['LATC'][:]
    LONC = nc_data.variables['LONC'][:]
    GGALT = nc_data.variables['GGALT'][:]
    GGLAT = nc_data.variables['GGLAT'][:]
    GGLON = nc_data.variables['GGLON'][:]
    Time = nc_data.variables['Time'][:]

    SFC = np.zeros(len(Time))
    for i in range(len(Time)):
        if np.isnan(LONC[i]) or np.isnan(LATC[i]):
            SFC[i] = HeightOfTerrain(GGLAT[i], GGLON[i])
        else:
            SFC[i] = HeightOfTerrain(LATC[i], LONC[i])

    if not np.all(np.isnan(SFC)):
        SFC_interp = interp1d(np.arange(len(SFC)), SFC, kind='linear', fill_value='extrapolate')
        valid_indices = ~np.isnan(SFC)
        SFC_valid = SFC[valid_indices]
        valid_times = np.arange(len(SFC))[valid_indices]
        SFC = SFC_interp(np.arange(len(SFC)))
        for i in range(len(SFC)):
            if np.isnan(SFC[i]):
                SFC[i] = 0
    SFC[np.isnan(SFC)] = 0
    ALTG = GGALT - SFC

    nc_data.createVariable('SFC_SRTM', 'f4', ('Time',), fill_value=-9999)
    nc_data.createVariable('ALTG_SRTM', 'f4', ('Time',), fill_value=-9999)

    nc_data.variables['SFC_SRTM'][:] = SFC
    nc_data.variables['ALTG_SRTM'][:] = ALTG
    nc_data.variables['SFC_SRTM'].setncattr('long_name', "Elevation of the Earth's surface below the aircraft position, WGS-84")
    nc_data.variables['SFC_SRTM'].setncattr('DataSource', 'viewfinderpanorama Jonathan de Ferranti')
    nc_data.variables['SFC_SRTM'].setncattr('Category', 'NavPosition')
    nc_data.variables['SFC_SRTM'].setncattr('Dependencies', '2 LATC LONC')
    minmax = f"{np.nanmin(SFC):.0f}f,{np.nanmax(SFC):.0f}f"
    nc_data.variables['SFC_SRTM'].setncattr('actual_range', minmax)
    nc_data.variables['SFC_SRTM'].setncattr('units', 'm')
    nc_data.variables['ALTG_SRTM'].setncattr('long_name', "Altitude of the aircraft above the Earth's surface, WGS-84")
    nc_data.variables['ALTG_SRTM'].setncattr('DataSource', 'viewfinderpanorama Jonathan de Ferranti')
    nc_data.variables['ALTG_SRTM'].setncattr('Category', 'NavPosition')
    nc_data.variables['ALTG_SRTM'].setncattr('units', 'm')
    nc_data.variables['ALTG_SRTM'].setncattr('Dependencies', '2 SFC_SRTM GGALT')
    minmax2 = f"{np.nanmin(ALTG):.0f}f,{np.nanmax(ALTG):.0f}f"
    nc_data.variables['ALTG_SRTM'].setncattr('actual_range', minmax2)

    ##Uncomment to plot results for debugging
"""     nc_data.close()
    plt.figure(figsize=(12, 6))
    plt.plot(Time, GGALT, label='GGALT (Geometric Altitude)')
    plt.plot(Time, SFC, label='SFC (Surface Height)')
    plt.plot(Time, ALTG, label='ALTG (Geometric Altitude - Surface Height)')
    plt.xlabel('Time')
    plt.ylabel('Height (m)')
    plt.title(f'Height Variables Over Time for {Project} {Flight}')
    plt.legend()
    plt.grid(True)
    plt.show() """

if __name__ == "__main__":
    main()