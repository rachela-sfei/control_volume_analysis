

'''
this script is a mess, but it does lots of things -- 
it reads the hist and his-bal files, which at this time have hourly fluxes across edges of control volume polygons
over different averaging periods, which the user can select, it computes the mean and RMS (with mean removed) fluxes over those edges
these fluxes are the components of the vector fluxes normal to the edges
the script infers the full vector by solving a least square problem:
1) at the centroids of the control volumes, using fluxes across the edges of that control volume
2) onto a regular grid, using the fluxes acrosss the 4 nearest edges, provided they are no farther than 6000m away
then it plots all this info in several ways
to visualize the RMS fluxes, we multiply by 0.12, which is a mixing efficiency Rusty computed from some tracer studies, he found basically that
the tidal dispersion coefficient across a given cell edge was proportional to 0.12 x the RMS fluctition of the volume flux
not totally sure how this translates to mass flux... 
'''

#################
### PACKAGES
#################

import xarray as xr
import matplotlib.pyplot as plt
import numpy as np
import geopandas as gpd
import os,sys
import pandas as pd
import matplotlib as mpl
from scipy.interpolate import griddata
from shapely.geometry import Point
import matplotlib.pyplot as plt 
import scipy.signal as signal
from importlib import reload
import control_volume_plotting_library as CVPL # plotting library must be in same folder as this script
reload(CVPL)

#################    
### USER INPUT
#################

# run folder and water year'

isel=4
if isel==0:
    runid = 'FR13_028'
    wystr = 'WY2013'
    server = 'chicago'
    water_year = 2013 # this script doesn't work with agg runs yet
if isel==1:
    runid = 'FR14_001'
    wystr = 'WY2014'
    server = 'boise'
    water_year = 2014 # this script doesn't work with agg runs yet
if isel==2:
    runid = 'FR15_001'
    wystr = 'WY2015'
    server = 'boise'
    water_year = 2015 # this script doesn't work with agg runs yet
if isel==3:
    runid = 'FR16_001'
    wystr = 'WY2016'
    server = 'boise'
    water_year = 2016 # this script doesn't work with agg runs yet
if isel==4:
    runid = 'FR17_021'
    wystr = 'WY2017'
    server = 'chicago'
    water_year = 2017 # this script doesn't work with agg runs yet
if isel==5:
    runid = 'FR18_009'
    wystr = 'WY2018'
    server = 'chicago'
    water_year = 2018 # this script doesn't work with agg runs yet

# set an efficiency for mixing due to tidal dispersion (Rusty's alpha from dispersion coefficients for aggregated model)
alpha = 0.12

# name of composite variable to plot and units
units = 'm3/s'
conversion_factor = 1/(24*3600) # convert m3/d to m3/s
plotname_prefix = 'Volume'
plot_label = 'Q1 = <Q>\nQ2 = %0.2f<(Q-<Q>)^2>^0.5 (%s)\nNOTE: numbers on plot are Q1, Q2 while colors are log10 Q1, log10 Q2' % (alpha, units)

# names of variables to sum over and stoichiometric multipliers to arrive at composite variable
variables = ['continuity']
multipliers = [1.00]
           
# filter option (chose from 'tidal' (semidiurnal), 'spring-neap','seasonal','monthly', 'daily')
filter_option = 'monthly'

# base directory for the output figures (in theory should be able to run on windows laptop with mounted drives or on server)
figure_base_dir = '/richmondvol1/hpcshared/open_bay/bgc/figures'

# base directory for model input, namely the shapefiles (this definitely runs on linux, in theory can also run this in windows and use mounted drive)
# (this is ignored if poly_path and tran_path are specified as something other than None above)
model_input_dir = '/richmondvol1/hpcshared'

# path to shapefiles (note use original 141 shapefiles because won't use other cv's and transects for these plots)
shpfn =  os.path.join(model_input_dir,'inputs','shapefiles','Agg_exchange_lines.shp') 
shpfn_poly = os.path.join(model_input_dir,'inputs','shapefiles','Agg_mod_contiguous.shp') 


# some parameters controlling the algorithm for inferring flux vectors at cell centers from dot products of flux vectors at cell edges
dmax = 10000. # maximum radius defining the neighborhood for interpolating
Nmax = 6 #  max number of points to use in least squares approximation on regular grid

# set minimum edge length to include in plots, and some calculations (meters)
min_edge_length = 800



# regular grid spanning whole bay
dx = 250.
x = np.arange(538000.,611500.,dx)
y = np.arange(4136500.,4225000.,dx)
xg, yg = np.meshgrid(x,y)

# some parameters for the flux vector map
axlim =(520000, 611000.0, 4137214.3349336325, 4236092.86876108)
legloc = (572500,4185000)
arrow_scale=4
key_arrow_frac = 0.5

# start time string, for trimming data
start_time = np.datetime64('%s-10-01' % (water_year-1)) 

# polygon numbers to include in whole bay polygon (excluding ocean)
ibay = [0, 117, 139, 2, 113, 114, 115, 111, 1, 3, 116, 7, 4, 112, 5, 108, 109, 110, 9, 107, 
    6, 8, 29, 10, 12, 11, 138, 137, 100, 19, 18, 13, 20, 26, 25, 21, 14, 24, 101, 102, 103, 104, 
    105, 106, 28, 27, 22, 15, 30, 23, 35, 34, 33, 32, 31, 17, 41, 40, 39, 38, 37, 36, 16, 140, 
    44, 43, 42, 46, 45, 49, 47, 97, 98, 86, 96, 95, 85, 93, 52, 87, 94, 48, 51, 50, 90, 88, 91, 
    89, 92, 53, 56, 99, 54, 55, 57, 67, 65, 66, 136, 58, 59, 63, 64, 60, 62, 61, 143, 144, 141, 
    68, 69, 70, 71, 78, 72, 84, 79, 146, 80, 82, 83, 142, 145, 73, 81, 74, 76, 77, 75]


# polygon numbers to include in vector flux maps (crop off the ocean, exclude polygons where have vector info in one direciton only)
ipoly = np.sort(np.array([ 2, 113, 114, 115, 111, 1, 3, 116, 7, 4, 112, 5, 108, 109, 110, 9, 107, # LSB sloughs 0, 139, 117
    6, 8, 29, 10, 12, 11, 100, 19, 18, 13, 20, 26, 25, 21, 14, 24, 101, 102, 103, 104, # Redwood Creek: 138, 137 
    105, 106, 28, 27, 22, 15, 30, 23, 35, 34, 33, 32, 31, 41, 40, 39, 38, 37, 36, 140, 
    44, 43, 42, 46, 45, 49, 47, 97, 98, 86, 96, 95, 85, 93, 52,   48, 51, 50, 90, 88, 91, 
    89, 92, 53, 56, 99, 54, 55, 57, 67, 65, 66, 136, 58, 59, 63, 64, 60, 62, 61, # san pablo tribs: 143, 144, 141, 
    68,   71, 78, 72, 84, 79, 146, 80, 82, 83, 142, 145, 73, 81, 74, 76])) # delta confluence 75, 77]
# carquinez only has flux info from E/W 69,70, 
# golden gate only has E/W flux info 94
# near golden gate, only has E/W flux info 87,
# along west shoal of south bay, too much anisotropy in side length 16, 17

# transect numbers to include (crop off the ocean)
itran = np.sort(np.array([  0,   1,   2,   3,   4,   5,   6,   7,   8,   9,  10,  11,  12,
        13,  14,  15,  16,  17,  18,  19,  20,  21,  22,  23,  24,  25,
        26,  27,  28,  29,  30,  31,  32,  33,  34,  35,  36,  37,  38,
        39,  40,  41,  42,  43,  44,  45,  46,  47,  48,  49,  50,  51,
        52,  53,  54,  55,  56,  57,  58,  59,  60,  61,  62,  63,  64,
        65,  66,  67,  68,  69,  70,  71,  72,  73,  74,  75,  76,  77,
        78,  79,  80,  81,  82,  83,  84,  85,  86,  87,  88,  89,  90,
        91,  92,  93,  94,  95,  96,  97,  98,  99, 100, 101, 102, 103,
       104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116,
       117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129,
       130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142,
       143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155,
       156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168,
       169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181,
       182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194,
       195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207,
       208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220,
       221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233,
       234, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244, 245, 246,
       247, 248, 249, 250, 251, 252, 253, 254, 255, 256, 257, 258, 259,
       260, 261, 262, 263, 264, 265, 266, 267, 268, 269, 270, 271, 272,
       273, 274, 275, 276, 277, 278, 279, 280, 281, 282,319]))

#################
### FUNCTIONS
#################

def semidi_filter(y, dt_hrs = 1., fcut = 1/35., N = 4):

    """
    Performs a tidal filter on the y series using a 4th order low pass
    butterworth filter and constant padding
   
    Usage:
       
        yf = semidi_filter(y, dt_hrs=1.0, fcut = 1/35, N=4.)
       
    Input:
       
        y    = time series
        dt_hrs   = time step (unit is hours)
        fcut = cutoff frequency in 1/hours
               
    Output:
   
        yf   = tidally filtered signal
   
    """
   
    # compute sampling frequency from time step
    fs = 1/dt_hrs
   
    # compute dimensionless cutoff frequency w.r.t. Nyquist frequency
    Wn = fcut/(0.5*fs)
   
    # compute filter coefficients
    b, a = signal.butter(N, Wn, 'low')
   
    # filter the signal
    yf = signal.filtfilt(b,a,y,padtype='constant')
   
    # return fitlered signal
    return yf


def spring_neap_filter(y, dt_days = 1./24., fcut = 1/36., N = 4):

    """
    Performs a spring-neap filter on the y series using a 4th order low pass
    butterworth filter and constant padding
   
    Usage:
       
        yf = spring_neap_filter(y, dt_days=1.0, fcut = 1/36., N=4)
       
    Input:
       
        y    = time series
        dt_days   = time step (unit is days)
        fcut = cutoff frequency in 1/days
               
    Output:
   
        yf   = tidally filtered signal
   
    """
   
    # compute sampling frequency from time step
    fs = 1/dt_days
   
    # compute dimensionless cutoff frequency w.r.t. Nyquist frequency
    Wn = fcut/(0.5*fs)
   
    # compute filter coefficients
    b, a = signal.butter(N, Wn, 'low')
   
    # filter the signal
    yf = signal.filtfilt(b,a,y,padtype='constant')
   
    # return fitlered signal
    return yf


###################
### MAIN PROGRAM
###################

# get string with concise list of runs 
run_list_str = CVPL.make_concise_runid_list_string([runid])

# path to figures, create if it does not exist
figure_path = os.path.join(figure_base_dir, run_list_str, 'fluxes_for_restime')
if not os.path.exists(figure_path):
    os.makedirs(figure_path)
print('\nfigures will be saved here: %s\n' % figure_path)

# get path to run folder
run_base_dir = '/%svol1/hpcshared' % server
run_dir = CVPL.get_run_dir(run_base_dir, runid)

# path to hist file
histfn = os.path.join(run_dir,'dwaq_hist.nc')

# load data from hist 
hdata = xr.open_dataset(histfn) 

# find all transects from the output hist file
TransectBL = ['transect' in name for name in hdata.location_names.values[0]]
indT = np.where(TransectBL)[0]

# check which of the variables exist in this run, and trim variable and multiplier lists accordingly
variables1 = []
multipliers1 = []
for i in range(len(variables)):
    if variables[i] in list(hdata.variables):
        variables1.append(variables[i])
        multipliers1.append(multipliers[i])
variables = variables1
multipliers = multipliers1

# sum variables (e.g. nh4 + no3), multiplying by their stoichiometric multipliers, for 
# both transects and polygons
varT = multipliers[0]*hdata.isel(nSegment=indT)[variables[0]].values
if len(variables)>1:    
    for i in range(1,len(variables)):
        varT = varT + multipliers[i]*hdata.isel(nSegment=indT)[variables[i]].values

# multiply by conversion factor
varT = varT * conversion_factor

# times
time = np.array([pd.to_datetime(t) for t in hdata.time.data])

# calculate the time step in days by starting with number of hours and dividing by 24
dt_days = (time[1] - time[0])/np.timedelta64(1,'h') / 24
dt_hrs = dt_days*24

# to compute the RMS flux that results in 2-way dispersion, we need to remove the tidally filtered 
# flux, where "tidal" always means semidirunal tides ... this matches what Rusty did in the aggregated
# grid tidally filtered model ... so here we compute the "tidal residual" flux which is the flux minus
# the tidally filtered flux, and we compute its rms over the semidiurnal tidal cycle
#
# later on, if we run a spring-neap filter or a monthly average or other time aggregation, we will feed
# the tidal mean and rms into that aggregation so it is treated linearly, i.e., to aggregate to monthly
# average we take the monthly average rms, not the root mean square over the month
#
varT_AVG_1 = np.zeros(varT.shape)
for i in range(len(varT[0,:])):
    varT_AVG_1[:,i] = semidi_filter(varT[:,i], dt_hrs = dt_hrs)
varT_tidal_residual = varT - varT_AVG_1
varT_RMS_1 = np.zeros(varT.shape)
for i in range(len(varT[0,:])):
    varT_RMS_1[:,i] = np.sqrt(semidi_filter((varT_tidal_residual[:,i])**2, dt_hrs = dt_hrs))

# aaverage or filter, take the RMS as well as average, and select data before the start time
ind = time>=pd.Timestamp(start_time)
if filter_option == 'unfiltered':
    
    varT_AVG = varT[ind,:]
    varT_RMS = np.zeros(np.shape(varT))
    time = time[ind]
    
    # plot title
    plot_title = '%s: %s, Unfiltered' % (runid, plot_label)

elif filter_option == 'spring-neap':

    varT_AVG = np.zeros(varT.shape)
    varT_RMS = np.zeros(varT.shape)
    for i in range(len(varT[0,:])):
        varT_AVG[:,i] = spring_neap_filter(varT_AVG_1[:,i], dt_days = dt_days)
        varT_RMS[:,i] = spring_neap_filter(varT_RMS_1[:,i], dt_days = dt_days)
    varT_AVG = varT_AVG[ind,:]
    varT_RMS = varT_RMS[ind,:]
    time = time[ind]

    # downsample to every 7 days
    nskip = int(np.timedelta64(7,'D')/np.timedelta64(int(dt_hrs),'h'))
    varT_AVG = varT_AVG[::nskip,:]
    varT_RMS = varT_RMS[::nskip,:]
    time = time[::nskip]

    # plot title
    plot_title = '%s\n%s\nFiltered Over Spring-Neap Cycle' % (runid, plot_label)

elif filter_option == 'tidal':
    varT_AVG = varT_AVG_1
    varT_RMS = varT_RMS_1

    # downsample to every 3 hours
    nskip = int(np.timedelta64(3,'h')/np.timedelta64(int(dt_hrs),'h'))
    time = time[::nskip]
    varT_AVG = varT_AVG[::nskip,:]
    varT_RMS = varT_RMS[::nskip,:]


    # plot title
    plot_title = '%s\n%s\nTidally Filtered' % (runid, plot_label)

elif filter_option == 'monthly':
    ind01 = np.logical_and(time>=pd.Timestamp('%d-10-01' % (water_year-1)), time<pd.Timestamp('%d-11-01' % (water_year-1)))
    ind02 = np.logical_and(time>=pd.Timestamp('%d-11-01' % (water_year-1)), time<pd.Timestamp('%d-12-01' % (water_year-1)))
    ind03 = np.logical_and(time>=pd.Timestamp('%d-12-01' % (water_year-1)), time<pd.Timestamp('%d-01-01' % water_year))
    ind04 = np.logical_and(time>=pd.Timestamp('%d-01-01' % water_year), time<pd.Timestamp('%d-02-01' % water_year))
    ind05 = np.logical_and(time>=pd.Timestamp('%d-02-01' % water_year), time<pd.Timestamp('%d-03-01' % water_year))
    ind06 = np.logical_and(time>=pd.Timestamp('%d-03-01' % water_year), time<pd.Timestamp('%d-04-01' % water_year))
    ind07 = np.logical_and(time>=pd.Timestamp('%d-04-01' % water_year), time<pd.Timestamp('%d-05-01' % water_year))
    ind08 = np.logical_and(time>=pd.Timestamp('%d-05-01' % water_year), time<pd.Timestamp('%d-06-01' % water_year))
    ind09 = np.logical_and(time>=pd.Timestamp('%d-06-01' % water_year), time<pd.Timestamp('%d-07-01' % water_year))
    ind10 = np.logical_and(time>=pd.Timestamp('%d-07-01' % water_year), time<pd.Timestamp('%d-08-01' % water_year))
    ind11 = np.logical_and(time>=pd.Timestamp('%d-08-01' % water_year), time<pd.Timestamp('%d-09-01' % water_year))
    ind12 = np.logical_and(time>=pd.Timestamp('%d-09-01' % water_year), time<pd.Timestamp('%d-10-01' % water_year))
    ntime, ntran = varT.shape
    varT_AVG = np.zeros((12,ntran))
    varT_RMS = np.zeros((12,ntran))
    varT_AVG[0,:] = np.mean(varT_AVG_1[ind01,:],axis=0)
    varT_AVG[1,:] = np.mean(varT_AVG_1[ind02,:],axis=0)
    varT_AVG[2,:] = np.mean(varT_AVG_1[ind03,:],axis=0)
    varT_AVG[3,:] = np.mean(varT_AVG_1[ind04,:],axis=0)
    varT_AVG[4,:] = np.mean(varT_AVG_1[ind05,:],axis=0)
    varT_AVG[5,:] = np.mean(varT_AVG_1[ind06,:],axis=0)
    varT_AVG[6,:] = np.mean(varT_AVG_1[ind07,:],axis=0)
    varT_AVG[7,:] = np.mean(varT_AVG_1[ind08,:],axis=0)
    varT_AVG[8,:] = np.mean(varT_AVG_1[ind09,:],axis=0)
    varT_AVG[9,:] = np.mean(varT_AVG_1[ind10,:],axis=0)
    varT_AVG[10,:] = np.mean(varT_AVG_1[ind11,:],axis=0)
    varT_AVG[11,:] = np.mean(varT_AVG_1[ind12,:],axis=0)
    varT_RMS[0,:] = np.sqrt(np.mean((varT_RMS_1[ind01,:])**2,axis=0))
    varT_RMS[1,:] = np.sqrt(np.mean((varT_RMS_1[ind02,:])**2,axis=0))
    varT_RMS[2,:] = np.sqrt(np.mean((varT_RMS_1[ind03,:])**2,axis=0))
    varT_RMS[3,:] = np.sqrt(np.mean((varT_RMS_1[ind04,:])**2,axis=0))
    varT_RMS[4,:] = np.sqrt(np.mean((varT_RMS_1[ind05,:])**2,axis=0))
    varT_RMS[5,:] = np.sqrt(np.mean((varT_RMS_1[ind06,:])**2,axis=0))
    varT_RMS[6,:] = np.sqrt(np.mean((varT_RMS_1[ind07,:])**2,axis=0))
    varT_RMS[7,:] = np.sqrt(np.mean((varT_RMS_1[ind08,:])**2,axis=0))
    varT_RMS[8,:] = np.sqrt(np.mean((varT_RMS_1[ind09,:])**2,axis=0))
    varT_RMS[9,:] = np.sqrt(np.mean((varT_RMS_1[ind10,:])**2,axis=0))
    varT_RMS[10,:] = np.sqrt(np.mean((varT_RMS_1[ind11,:])**2,axis=0))
    varT_RMS[11,:] = np.sqrt(np.mean((varT_RMS_1[ind12,:])**2,axis=0))

    time = ['Oct %d' % (water_year-1), 
            'Nov %d' % (water_year-1),
            'Dec %d' % (water_year-1),
            'Jan %d' % water_year,
            'Feb %d' % water_year,
            'Mar %d' % water_year,
            'Apr %d' % water_year,
            'May %d' % water_year,
            'Jun %d' % water_year,
            'Jul %d' % water_year,
            'Aug %d' % water_year,
            'Sep %d' % water_year]

    # plot title
    plot_title = '%s\n%s\nMonthly Average' % (runid, plot_label)

elif filter_option == 'seasonal':
    ind1 = np.logical_and(time>=pd.Timestamp('%d-10-01' % (water_year-1)), time<pd.Timestamp('%d-01-01' % water_year))
    ind2 = np.logical_and(time<pd.Timestamp('%d-01-01' % water_year), time<pd.Timestamp('%d-04-01' % water_year))
    ind3 = np.logical_and(time<pd.Timestamp('%d-04-01' % water_year), time<pd.Timestamp('%d-07-01' % water_year))
    ind4 = np.logical_and(time<pd.Timestamp('%d-07-01' % water_year), time<pd.Timestamp('%d-10-01' % water_year))
    ntime, ntran = varT.shape
    varT_AVG = np.zeros((4,ntran))
    varT_RMS = np.zeros((4,ntran))
    varT_AVG[0,:] = np.mean(varT_AVG_1[ind1,:],axis=0)
    varT_AVG[1,:] = np.mean(varT_AVG_1[ind2,:],axis=0)
    varT_AVG[2,:] = np.mean(varT_AVG_1[ind3,:],axis=0)
    varT_AVG[3,:] = np.mean(varT_AVG_1[ind4,:],axis=0)
    varT_RMS[0,:] = np.sqrt(np.mean((varT_RMS_1[ind1,:])**2,axis=0))
    varT_RMS[1,:] = np.sqrt(np.mean((varT_RMS_1[ind2,:])**2,axis=0))
    varT_RMS[2,:] = np.sqrt(np.mean((varT_RMS_1[ind3,:])**2,axis=0))
    varT_RMS[3,:] = np.sqrt(np.mean((varT_RMS_1[ind4,:])**2,axis=0))

    time = ['Oct, Nov, Dec', 'Jan, Feb, Mar', 'Apr, May, Jun', 'Jul, Aug, Sep']

    # plot title
    plot_title = '%s\n%s\nSeasonal Average' % (runid, plot_label)

elif filter_option == 'annual':
    varT_AVG = varT_AVG_1[ind,:].mean(axis=0)
    varT_RMS = varT_RMS_1[ind,:].mean(axis=0)
    time = time[ind][0]

    plot_title = '%s\n%s\nAnnual Average' % (runid, plot_label)
    time = time[ind][0]

# trim fluxes to included transects only
varT_AVG = varT_AVG[:,itran]
varT_RMS = varT_RMS[:,itran]

# read control volume exchange and polygons
gdf = gpd.read_file(shpfn).loc[itran]
poly_df = gpd.read_file(shpfn_poly)

# do a bunch of geometry calculations for edges before trimming edges and polygons to the ones we want to plot ...

# merge polygons into a single polygon representing the whole bay and
# extract the polygon from the geopandas dataframe as a shapely polygon
poly_allbay_gdf = poly_df.iloc[ibay].copy(deep=True)
poly_allbay_gdf['dummy']=1
poly_allbay_gdf = poly_allbay_gdf.dissolve(by='dummy')
poly_allbay = poly_allbay_gdf.iloc[0].geometry

# find centroids of the edges
xe = gdf.geometry.centroid.x.values
ye = gdf.geometry.centroid.y.values
gdf['xe'] = xe
gdf['ye'] = ye

# centroids of the polygons
poly_x = poly_df.geometry.centroid.x.values
poly_y = poly_df.geometry.centroid.y.values

# centroid of the polygon to the right of each edge
xright = poly_x[gdf.right.values]   
yright = poly_y[gdf.right.values]

# length of the line between the centroid of the edge 
# and the centroid of the polygon to the right
line_length = np.sqrt( (xe-xright)**2 + (ye-yright)**2 )

# this gives the lengths of the edges/transects/exchange lines
edge_length = gdf.geometry.length.values 

# now trim the polygons down to the ones we want to plot only
poly_df = poly_df.loc[ipoly]

# find centroids of cell centers and add the coordinates to the geodataframe
xc = []
yc = []
for point in poly_df.centroid.values:
    xc1, yc1 = point.coords.xy
    xc.append(xc1[0])
    yc.append(yc1[0])
poly_df['xc'] = xc
poly_df['yc'] = yc

# for each polygon, find the list of edges, and add to the geodataframe
poly_df['edgelist'] = None
for index in poly_df.index.values:
    edge_list = []
    for edge_index in gdf.index.values:
        if (gdf.loc[edge_index].left == index) or (gdf.loc[edge_index].right == index):
            edge_list.append(edge_index)
    poly_df['edgelist'].loc[index] = edge_list

# add edge length to edge dataframe
gdf['edgelength'] = edge_length


############## do not do this becasue we want total flow rate ##############
## normalize fluxes by edge length to get per unit meter
#ntime = len(time)
#varT_AVG = varT_AVG /np.tile(edge_length,(ntime,1))
#varT_RMS = varT_RMS /np.tile(edge_length,(ntime,1))

# adjust RMS by mixing efficiency
varT_RMS = alpha * varT_RMS

# set max colorbar values for average fluxes using 95th percentile
qmax = np.nanpercentile(np.abs(varT_AVG),95)

# set max for plotting both average fluxes and 2-way dispersive fluxes using 95th percentile, with trump
# using only the edges greater than 
ind = edge_length > min_edge_length
qmax0 = np.nanpercentile(np.abs(varT_AVG[:,ind]),95)
qmax1 = np.nanpercentile(varT_RMS[:,ind],95)
if qmax0>qmax1:
    qmax1 = qmax0
qmin0 = np.nanpercentile(np.abs(varT_AVG[:,ind]),5)
qmin1 = np.nanpercentile(varT_RMS[:,ind],5)
if qmin0<qmin1:
    qmin1 = qmin0


# loop through times, interpolate to centroids and to regular grid (using least squares approach), and plot
ntime = len(time)
for itime in range(ntime):

    print('time step %d of %d' % (itime,ntime))

    # find the time matching this time stamp, and divide by edge length to get flux per meter
    if filter_option=='annual':
        varTmean = varT_AVG
        varTrms = varT_RMS
    else:
        varTmean = varT_AVG[itime,:]
        varTrms = varT_RMS[itime,:]

    # compute vector components of flux normal to each transect, 
    # normalizing the flux by edge length to get flux per unit length
    # (actually direction is not normal to the transect but points from one
    # polygon centroid to the other polygon centroid)
    qx =  (xright-xe)/line_length*varTmean
    qy =  (yright-ye)/line_length*varTmean
    
    # find the unit normal in the direction of the fluxes across the transects
    nx = qx/np.sqrt(qx**2 + qy**2)
    ny = qy/np.sqrt(qx**2 + qy**2)

    # add to the edge geodataframe
    gdf['qx'] = qx
    gdf['qy'] = qy
    gdf['nx'] = nx
    gdf['ny'] = ny
    
    # add mean and rms values of flux as columns in geodataframe for edges
    gdf['mean'] = np.abs(varTmean)
    gdf['rms'] = varTrms
    gdf['logmean'] = np.log10(np.abs(varTmean))
    gdf['logrms'] = np.log10(varTrms)

    # plot fluxes across edges, with direcitons for mean fluxes
    fig1, ax1 = plt.subplots(1,2,figsize=(16*3,11*3), constrained_layout=True)
    poly_allbay_gdf.plot(ax=ax1[0],color='w',edgecolor='k')
    poly_allbay_gdf.plot(ax=ax1[1],color='w',edgecolor='k')
    gdf.plot(column='logmean',ax=ax1[0],vmin=np.log10(qmin1),vmax=np.log10(qmax1),cmap='jet',legend=True,
        legend_kwds={'label' : 'log10 Q1 (%s)' % units,'fraction' : 0.02, 'pad' : 0.0, 'orientation' : 'horizontal'})
    gdf.plot(column='logrms',ax=ax1[1],vmin=np.log10(qmin1),vmax=np.log10(qmax1),cmap='jet',legend=True,
        legend_kwds={'label' : 'log10 Q2 (%s)' % units,'fraction' : 0.02, 'pad' : 0.0, 'orientation' : 'horizontal'})
    ind = edge_length > min_edge_length
    ax1[0].quiver(xe[ind],ye[ind],nx[ind],ny[ind],scale=100,scale_units='width',width=0.001,color='m')
    for iax in [0,1]:
        ax1[iax].axis('off')
        ax1[iax].axis('tight')
        ax1[iax].axis('equal')
        #ax1[iax].axis((np.min(x),np.max(x),np.min(y),np.max(y)))
    if filter_option=='annual':
        fig1.suptitle(plot_title)
    else:
        fig1.suptitle(plot_title + '\n' + str(time[itime]))

    # add numbers to the figure
    for ie in range(len(gdf)):
        ax1[0].text(gdf.iloc[ie]['xe'], gdf.iloc[ie]['ye'], '%0.1f' % gdf.iloc[ie]['mean'])
        ax1[1].text(gdf.iloc[ie]['xe'], gdf.iloc[ie]['ye'], '%0.1f' % gdf.iloc[ie]['rms'])

    fig1.savefig(os.path.join(figure_path,'%s_volume_flux_map_mean_and_rms_edges_%s_%06d.png' % (runid,filter_option,itime)),dpi=300)

    plt.close('all')

            
# to make into a movie, in terminal on chicago, navigate into folder with the plots and type
# ffmpeg -framerate 10 -start_number 0 -i FR17_017_Algae_flux_map_streamlines_plus_rms_spring-neap_%06d.png -f mp4 -vcodec h264 -pix_fmt yuv420p din_flux_streamlines_spring_neap_filtered.mp4
hdata.close()