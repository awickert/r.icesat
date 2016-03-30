# ICESAT
# All generic unless I mark it as something for Ecuador

# DATA SOURCE
# https://nsidc.org/data/icesat/data.html -- all data
# GLA06 (everything) and GLA14 (land surface), HDF5.
# GLA14 -- used by Chinese researchers for Tibetan lakes
# And so this is what I have written this code around.

# Download HDF5 files (I use wget -r) and then use the recursive glob
# to find all of these

import h5py
import numpy as np
import glob
from datetime import datetime as dt
import os
import fnmatch
import shutil

#########
# INPUT #
#########

# Bounding box -- Chimborazo
w = -78.95
e = -78.65
s = -1.6
n = -1.3

"""
w = -77
e = -76
s = -2
n = -1

w = -98
e = -89
s = 43
n = 50
"""

# Outname -- name of path and output .txt concatenated file
outname = 'Chimborazo_xyzt'
#outname = 'MinnesotaLakes'

# Utility function
def recursive_glob(wildcard, rootdir=os.getcwd()):
  matches = []
  for root, dirnames, filenames in os.walk(rootdir):
      for filename in fnmatch.filter(filenames, wildcard):
          matches.append(os.path.join(root, filename))
  return matches

#################################
# STEP 1: EXTRACT DATA FROM HDF #
#################################

t2000 = dt(2000,1,1) # Reference point for timestamps
tUNIX = dt(1970,1,1)
tOffset = (t2000 - tUNIX).total_seconds()

filenames = sorted(recursive_glob('*.H5'))

try:
  print 'Creating directory', outname
  os.mkdir(outname)
except:
  print 'Directory', outname, 'exists.'

for filename in filenames:

  print os.path.split(filename)[-1],
  
  #try:

  f = h5py.File(filename, 'r')

  d40h = f['Data_40HZ']
  lat = d40h['Geolocation']['d_lat'].value
  lon = d40h['Geolocation']['d_lon'].value
  elev = d40h['Elevation_Surfaces']['d_elev'].value
  # no-data value in elev:
  elev[elev == 1.7976931348623157E308] = np.nan
  # Keep length the same for now
  #lat = lat[np.isnan(elev) == False]
  #lon = lon[np.isnan(elev) == False]
  #elev = elev[np.isnan(elev) == False]
 
  timeUNIX = d40h['Time']['d_UTCTime_40'].value + tOffset

  # Local region
  # e-lon and n-lat
  region = (lon < ((360+e)%360)) * (lon > ((360+w)%360)) * (lat < n) * (lat > s)
  elevS = elev[region]
  latS = lat[region]
  lonS = lon[region]
  timeUNIXS = timeUNIX[region]
  if len(elevS) == 0:
    print "No data in region from this set of passes."
    continue
  
  deltaTime = np.ceil(np.max(timeUNIXS) - np.min(timeUNIXS))
  
  startTimeDateTime = dt.utcfromtimestamp(np.min(timeUNIXS))
  
  # Keep to date -- passes are just a matter of 2-3 minutes
  
  outfile = 'ICESat_' + '%04d' %startTimeDateTime.year \
                      + '%02d' %startTimeDateTime.month \
                      + '%02d' %startTimeDateTime.day
  print " -->", outfile

  xyztS = np.hstack(( np.expand_dims(lonS, 2), np.expand_dims(latS, 2), \
                      np.expand_dims(elevS, 2), np.expand_dims(timeUNIXS, 2) ))
                      
  np.savetxt(outname + '/' + outfile, xyztS, delimiter='|')

  #except:
  #  print "  >> ***File must not be complete***"
  #  #os.remove(filename)
  #  #print "  >>", filename, "deleted. Try to download again."

#############################################################
# STEP 2: CONCATENATE ALL OUTPUT FILES INTO A SINGLE MASTER #
#############################################################

outfilename = outname + '.txt'
with open(outfilename, 'wb') as outfile:
    for filename in glob.glob(outname+'/ICESat_*'):
        if filename == outfilename:
            # don't want to copy the output into the output
            continue
        with open(filename, 'rb') as readfile:
            shutil.copyfileobj(readfile, outfile)

#################################
# STEP 3: IMPORT INTO GRASS GIS #
#################################

from grass import script as grass

# OPTION 1: ALL PATHS
infilepaths = sorted(glob(outname+'/*'))
print ""
print "GRASS import"
print ""
for infilepath in infilepaths:
  infilename = os.path.split(infilepath)[-1]
  print infilename
  #try:
  grass.run_command('v.in.ascii', input=infilepath, output=infilename, x=1, y=2, z=3, columns="x double precision, y double precision, z double precision, tUNIX double precision", overwrite=True, quiet=True)
#  #except:
#  #  print "  >> File already imported"
# If too many points to register w/ topology
#  , flags='b')

# OPTION 2: ALL AT ONCE
print ""
print "GRASS import"
print ""
  infilename = outfilename
  print infilename
  #try:
  grass.run_command('v.in.ascii', input=infilename, output=os.path.splitext(infilename)[0], x=1, y=2, z=3, columns="x double precision, y double precision, z double precision, tUNIX double precision", overwrite=True, quiet=True)
#  #except:
#  #  print "  >> File already imported"
# If too many points to register w/ topology
#  , flags='b')

# region
grass.run_command('g.region', flags='p', w = w, e = e, s = s, n = n)

