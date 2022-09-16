

'''
last updated by allie king in June 2022
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

#################
### FUNCTIONS
#################

def scan_lsp_for_NC_PC(lsp_path):

    # scan the lsp file for mentions of N:C ratios and P:C ratios
    NC_ratios = {}
    PC_ratios = {}
    with open(lsp_path,'r') as f:
        lines = f.readlines()
        for i in range(len(lines)-1):
            line1 = lines[i]
            line2 = lines[i+1]
            if 'N:C ratio Diatoms' in line1:
                NC_ratios['Diat'] = float(line2.split(':')[1])
            elif 'N:C ratio Greens' in line1:
                NC_ratios['Green'] = float(line2.split(':')[1])
            elif 'N:C ratio of DEB Zooplankton' in line1:
                NC_ratios['Zoopl_V'] = float(line2.split(':')[1])
                NC_ratios['Zoopl_E'] = float(line2.split(':')[1])
                NC_ratios['Zoopl_R'] = float(line2.split(':')[1])
            elif 'N:C ratio of DEB Grazer4' in line1:
                NC_ratios['Grazer4_V'] = float(line2.split(':')[1])
                NC_ratios['Grazer4_E'] = float(line2.split(':')[1])
                NC_ratios['Grazer4_R'] = float(line2.split(':')[1])
            elif 'N:C ratio of DEB Mussel' in line1:
                NC_ratios['Mussel_V'] = float(line2.split(':')[1])
                NC_ratios['Mussel_E'] = float(line2.split(':')[1])
                NC_ratios['Mussel_R'] = float(line2.split(':')[1])
            if 'P:C ratio Diatoms' in line1:
                PC_ratios['Diatom'] = float(line2.split(':')[1])
            elif 'P:C ratio Greens' in line1:
                PC_ratios['Green'] = float(line2.split(':')[1])
            elif 'P:C ratio of DEB Zooplankton' in line1:
                PC_ratios['Zoopl_V'] = float(line2.split(':')[1])
                PC_ratios['Zoopl_E'] = float(line2.split(':')[1])
                PC_ratios['Zoopl_R'] = float(line2.split(':')[1])
            elif 'P:C ratio of DEB Grazer4' in line1:
                PC_ratios['Grazer4_V'] = float(line2.split(':')[1])
                PC_ratios['Grazer4_E'] = float(line2.split(':')[1])
                PC_ratios['Grazer4_R'] = float(line2.split(':')[1])
            elif 'P:C ratio of DEB Mussel' in line1:
                PC_ratios['Mussel_V'] = float(line2.split(':')[1])
                PC_ratios['Mussel_E'] = float(line2.split(':')[1])
                PC_ratios['Mussel_R'] = float(line2.split(':')[1])
    return (NC_ratios, PC_ratios)

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
    

#################    
### USER INPUT
#################

# run folder and water year'
#run_folder = 'FR13_025'
#water_year = 2013
#run_folder = 'FR17_018'
#water_year = 2017
run_folder = 'FR18_006'
water_year = 2018

# root directory (for runs, shapefiles, and output csv files)
root_dir = '/richmondvol1/hpcshared/'   ## running on chicago
#root_dir = r'X:\hpcshared'              ## running on windows laptop with mounted drive

# output folder path
plotfolder = os.path.join(root_dir,'NMS_Projects','Control_Volume_Analysis','Plots',run_folder,'flux_maps')

# path to run folder and shapefiles (note use original 141 shapefiles because won't use other cv's and transects for these plots)
shpfn =  os.path.join(root_dir,'inputs','shapefiles','Agg_exchange_lines.shp') 
shpfn_poly = os.path.join(root_dir,'inputs','shapefiles','Agg_mod_contiguous.shp') 
path = os.path.join(root_dir,'Full_res','WY%d' % water_year,run_folder)
lsp_path = os.path.join(root_dir,'Full_res','WY%d' % water_year,run_folder,'sfbay_dynamo000.lsp')

# some parameters controlling the algorithm for inferring flux vectors at cell centers from dot products of flux vectors at cell edges
dmax = 10000. # maximum radius defining the neighborhood for interpolating
Nmax = 6 #  max number of points to use in least squares approximation on regular grid

# set minimum edge length to include in plots, and some calculations (meters)
min_edge_length = 800

# set an efficiency for mixing due to tidal dispersion (Rusty's alpha from dispersion coefficients for aggregated model)
alpha = 0.12

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

# retrieve the stoichiometric multipliers from the *.lsp file
NC_ratios, PC_ratios = scan_lsp_for_NC_PC(lsp_path)

# path to DWAQ run, hist file, and hist_bal file
histfn = os.path.join(path,'dwaq_hist.nc')
histbal_fn = os.path.join(path,'dwaq_hist_bal.nc') 

###################
### MAIN PROGRAM
###################

# create plot directory
if not os.path.exists(plotfolder):
    os.makedirs(plotfolder)

# loop through filter options and parameeters
for param in ['din','tn','continuity','algae']:

    if param=='algae':

        filter_option_list = ['spring-neap','seasonal','daily']

    else:

        filter_option_list = ['seasonal']

    for filter_option in filter_option_list:


        # set the values that depend on the parameter
        if param == 'continuity':
        
            plotname_prefix = 'Volume'
        
            # names of variables to sum (in this case to get DIN) and stoichiometric multipliers
            variables = ['continuity']
            multipliers = [1.00]
        
            units = 'm2/d'
        
        elif param == 'din':
        
            plotname_prefix = 'DIN'
        
            # names of variables to sum (in this case to get DIN) and stoichiometric multipliers
            variables = ['no3', 'nh4']
            multipliers = [1.00, 1.00]
        
            units = 'gN/m/d'
        
        elif param == 'tn':
        
            plotname_prefix = 'TN'
        
            variables = ['no3', 'nh4', 'pon1', 'diat', 'green', 'zoopl_v', 'zoopl_e', 'zoopl_r']
            multipliers = [1.00, 1.00, 1.00, NC_ratios['Diat'], NC_ratios['Green'], NC_ratios['Zoopl_V'], NC_ratios['Zoopl_E'], NC_ratios['Zoopl_R']]
        
            units = 'gN/m/d'
        
        elif param == 'algae':
        
            plotname_prefix = 'Algae'
        
            variables = ['diat','green']
            multipliers = [1.00,1.00]
        
            units = 'gC/m/d'
        
        if param == 'n-algae':
        
            plotname_prefix = 'N-Algae'
        
            variables = ['diat','green']
            multipliers = [NC_ratios['Diat'],NC_ratios['Green']]
        
            units = 'gN/m/d'
        
        # load data from hist and hist_bal files
        hdata = xr.open_dataset(histfn) # history file
        
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
        
        # times
        time = np.array([pd.to_datetime(t) for t in hdata.time.data])
        
        # calculate the time step in days by starting with number of hours and dividing by 24
        dt_days = (time[1] - time[0])/np.timedelta64(1,'h') / 24
        dt_hrs = dt_days*24
        
        # to compute the RMS flux that results in 2-way dispersion, we need to remove the tidally filtered 
        # flux, where "tidal" always means semidirunal tides ... this matches what Rusty did in the aggregated
        # grid tidally filtered model ... so here we compute the "tidal residual" flux which is the flux minus
        # the tidally filtered flux
        varT_tidally_averaged = np.zeros(varT.shape)
        for i in range(len(varT[0,:])):
            varT_tidally_averaged[:,i] = semidi_filter(varT[:,i], dt_hrs = dt_hrs)
        varT_tidal_residual = varT - varT_tidally_averaged
        
        # aaverage or filter, take the RMS as well as average, and select data before the start time
        ind = time>=pd.Timestamp(start_time)
        if filter_option == 'unfiltered':
            
            varT_AVG = varT[ind,:]
            varT_RMS = np.zeros(np.shape(varT))
            time = time[ind]
            
            # plot title
            plot_title = '%s: %s Flux, Unfiltered' % (run_folder, plotname_prefix)
        
        elif filter_option == 'spring-neap':
            varT_AVG = np.zeros(varT.shape)
            for i in range(len(varT[0,:])):
                varT_AVG[:,i] = spring_neap_filter(varT[:,i], dt_days = dt_days)
            varT_RMS = np.zeros(varT.shape)
            for i in range(len(varT[0,:])):
                varT_RMS[:,i] = np.sqrt(spring_neap_filter((varT_tidal_residual[:,i])**2, dt_days = dt_days))
            varT_AVG = varT_AVG[ind,:]
            varT_RMS = varT_RMS[ind,:]
            time = time[ind]
        
            # downsample to every 7 days
            nskip = int(np.timedelta64(7,'D')/np.timedelta64(int(dt_hrs),'h'))
            varT_AVG = varT_AVG[::nskip,:]
            varT_RMS = varT_RMS[::nskip,:]
            time = time[::nskip]
        
            # plot title
            plot_title = '%s: %s Flux, Filtered Over Spring-Neap Cycle' % (run_folder, plotname_prefix)
        
        elif filter_option == 'tidal':
            varT_AVG = np.zeros(varT.shape)
            for i in range(len(varT[0,:])):
                varT_AVG[:,i] = semidi_filter(varT[:,i], dt_hrs = dt_hrs)
            varT_RMS = np.zeros(varT.shape)
            for i in range(len(varT[0,:])):
                varT_RMS[:,i] = np.sqrt(semidi_filter((varT_tidal_residual[:,i])**2, dt_hrs = dt_hrs))
            varT_AVG = varT_AVG[ind,:]
            varT_RMS = varT_RMS[ind,:]
            time = time[ind]
        
            # downsample to every 3 hours
            nskip = int(np.timedelta64(3,'h')/np.timedelta64(int(dt_hrs),'h'))
            time = time[::nskip]
            varT_AVG = varT_AVG[::nskip,:]
            varT_RMS = varT_RMS[::nskip,:]
        
        
            # plot title
            plot_title = '%s: %s Flux, Tidally Filtered' % (run_folder, plotname_prefix)
        
        elif filter_option == 'seasonal':
            ind1 = np.logical_and(time>=pd.Timestamp('%d-10-01' % (water_year-1)), time<pd.Timestamp('%d-01-01' % water_year))
            ind2 = np.logical_and(time<pd.Timestamp('%d-01-01' % water_year), time<pd.Timestamp('%d-04-01' % water_year))
            ind3 = np.logical_and(time<pd.Timestamp('%d-04-01' % water_year), time<pd.Timestamp('%d-07-01' % water_year))
            ind4 = np.logical_and(time<pd.Timestamp('%d-07-01' % water_year), time<pd.Timestamp('%d-10-01' % water_year))
            ntime, ntran = varT.shape
            varT_AVG = np.zeros((4,ntran))
            varT_RMS = np.zeros((4,ntran))
            varT_AVG[0,:] = np.mean(varT[ind1,:],axis=0)
            varT_AVG[1,:] = np.mean(varT[ind2,:],axis=0)
            varT_AVG[2,:] = np.mean(varT[ind3,:],axis=0)
            varT_AVG[3,:] = np.mean(varT[ind4,:],axis=0)
            varT_RMS[0,:] = np.sqrt(np.mean((varT_tidal_residual[ind1,:])**2,axis=0))
            varT_RMS[1,:] = np.sqrt(np.mean((varT_tidal_residual[ind2,:])**2,axis=0))
            varT_RMS[2,:] = np.sqrt(np.mean((varT_tidal_residual[ind3,:])**2,axis=0))
            varT_RMS[3,:] = np.sqrt(np.mean((varT_tidal_residual[ind4,:])**2,axis=0))
        
            time = ['Oct, Nov, Dec', 'Jan, Feb, Mar', 'Apr, May, Jun', 'Jul, Aug, Sep']
        
            # plot title
            plot_title = '%s: %s Flux, Seasonal Average' % (run_folder, plotname_prefix)
        
        elif filter_option == 'annual':
            varT_AVG = varT[ind,:].mean(axis=0)
            varT_RMS = np.sqrt(np.mean((varT_tidal_residual[ind,:])**2,axis=0))
            time = time[ind][0]
        
            plot_title = '%s: %s Flux, Annual Average' % (run_folder, plotname_prefix)
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
        
        # make a mask to select grid points that are in the bay
        print('making grid mask, this takes awhile...')
        grid_mask = np.zeros(np.shape(xg), dtype='bool')
        for i in range(len(x)):
            for j in range(len(y)):
                
                ## pick out coordinates on grid
                xc1 = x[i]
                yc1 = y[j]
                
                # check if point is inside the bay, and if it is, mark true
                if Point(xc1,yc1).within(poly_allbay):
                    grid_mask[j,i] = True
        print('...done with grid mask')
        
        
        # normalize fluxes by edge length to get per unit meter
        ntime = len(time)
        varT_AVG = varT_AVG/np.tile(edge_length,(ntime,1))
        varT_RMS = varT_RMS/np.tile(edge_length,(ntime,1))
        
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
        
        # find 
        
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
            
            # interpolate onto cell centroids using a least square inverse distance 
            # weighting method to find the flux vectors from the fluxes projected onto
            # the polygon transects
        
            # initialize flux vectors as nan at centroids
            qxc = np.nan*np.ones(np.shape(xc))
            qyc = np.nan*np.ones(np.shape(xc))
        
            # ... loop through the regular grid, evaluating flux vectors
            for i in range(len(poly_df)):
                    
                # get the list of edges touching this polygon
                xc1 = poly_df.iloc[i]['xc']
                yc1 = poly_df.iloc[i]['yc']
                edge_list = poly_df.iloc[i]['edgelist']
        
                # loop over the edges in the edge list and get all the edge flux values and unit normals for edges with length > 6000m
                nx2 = []
                ny2 = []
                qx2 = []
                qy2 = []
                for edge in edge_list:
                    if gdf.loc[edge]['edgelength'] > min_edge_length:
                        nx2.append(gdf.loc[edge]['nx'])
                        ny2.append(gdf.loc[edge]['ny'])
                        qx2.append(gdf.loc[edge]['qx'])
                        qy2.append(gdf.loc[edge]['qy'])
                nx2 = np.array(nx2)
                ny2 = np.array(ny2)
                qx2 = np.array(qx2)
                qy2 = np.array(qy2)
                N = len(nx2)
        
                #############################################################
                # solve unweighted least square problem 
                #############################################################
                
                # only possible to solve matrix equation if have at least 2 points
                if N>=2:
                    A = np.zeros((N,2))
                    A[:,0] = nx2
                    A[:,1] = ny2
                    b = np.zeros(N)
                    b[:] = np.sqrt(qx2**2 + qy2**2)
                    W = np.zeros((N,N))
                    for n in range(N):
                        W[n,n] = 1
                    xhat = np.matmul(np.linalg.inv(np.matmul(np.transpose(A),np.matmul(W,A) )),
                                  np.matmul(np.transpose(A),np.matmul(W,b))) 
                    qxc[i] = xhat[0]
                    qyc[i] = xhat[1]
        
            # get magnitude of centroid fluxes
            qcM = np.sqrt(qxc**2 + qyc**2)
        
            # interpolate onto the regular grid using a least square inverse distance 
            # weighting method to find the flux vectors from the fluxes projected onto
            # the polygon transects
            
            # initialize flux vectors as nan on regular grid
            qxg = np.nan*np.ones(np.shape(xg))
            qyg = np.nan*np.ones(np.shape(xg))
        
            # filter out the fluxes across transects that are less than 800m long
            ind = edge_length > min_edge_length
            nx1 = nx[ind]
            ny1 = ny[ind]
            qx1 = qx[ind]
            qy1 = qy[ind]
            xe1 = xe[ind]
            ye1 = ye[ind]
        
            # loop through the regular grid, evaluating flux vectors, using just the 5 closest 
            # points and the inverse distance cubed weighting matrix
            for i in range(len(x)):
                for j in range(len(y)):
                    
                    ## pick out coordinates on grid
                    xc1 = x[i]
                    yc1 = y[j]
                    
                    # check if point is inside the bay, and if it is, proceed with 
                    # interpolation step
                    #if Point(xc1,yc1).within(poly_allbay):
                    
                    # find the distances between this grid point and points where fluxes
                    # are defined
                    d = np.sqrt((xe1-xc1)**2 + (ye1-yc1)**2)
                    
                    #############################################################
                    # solve unweighted least square problem using only 4 closet
                    # points in the neighborhood
                    #############################################################
                    
                    # select points where d is less that 6000m 
                    indn = d <= dmax
                    d2 = d[indn]
                    nx2 = nx1[indn]
                    ny2 = ny1[indn]
                    qx2 = qx1[indn]
                    qy2 = qy1[indn]
                    N = len(nx2)
                    
                    # use only the Nmax closest points
                    if N > Nmax:
                        indn = np.argsort(d2)
                        indn = indn[0:Nmax]
                        N = Nmax
                        d2 = d2[indn]
                        nx2 = nx2[indn]
                        ny2 = ny2[indn]
                        qx2 = qx2[indn]
                        qy2 = qy2[indn]
                    
                    # only possible to solve matrix equation if have at least 3 points
                    if N>=3:
                        A = np.zeros((N,2))
                        A[:,0] = nx2
                        A[:,1] = ny2
                        b = np.zeros(N)
                        b[:] = np.sqrt(qx2**2 + qy2**2)
                        W = np.zeros((N,N))
                        for n in range(N):
                            W[n,n] = 1/d2[n]**3
                        xhat = np.matmul(np.linalg.inv(np.matmul(np.transpose(A),np.matmul(W,A) )),
                                      np.matmul(np.transpose(A),np.matmul(W,b))) 
                        qxg[j,i] = xhat[0]
                        qyg[j,i] = xhat[1]
                       
            # make values outside bay nan
            qxg[~grid_mask] = np.nan
            qyg[~grid_mask] = np.nan
        
            # compute magnitude of mean flux on regular grid
            qgM = np.sqrt(qxg**2 + qyg**2)
        
            # add mean and rms values of flux as columns in geodataframe for edges
            gdf['mean'] = np.abs(varTmean)
            gdf['rms'] = varTrms
            gdf['logmean'] = np.log10(np.abs(varTmean))
            gdf['logrms'] = np.log10(varTrms)
        
            # plot streamlines using the fine regular grid 
            fig = plt.figure(figsize=(8.5,11))
            ax = fig.subplots()
            fig.tight_layout(rect=[0, 0.03, 1, 0.95])
            norm = mpl.colors.Normalize(vmin = 0, vmax = qmax)
            plt.streamplot(xg,yg,qxg,qyg,color=np.sqrt(qxg**2+qyg**2),cmap='jet',norm=norm,density=5)
            cbar = plt.colorbar(fraction=0.02, pad=0.01, orientation='horizontal')
            cbar.set_label('Mean Flux Magnitude (%s)' % units)
            poly_allbay_gdf.plot(ax=ax,color='w',edgecolor='k')
            plt.axis('off')
            #plt.axis((np.min(x),np.max(x),np.min(y),np.max(y)))
            plt.axis('tight')
            plt.axis('equal')
            plt.xlabel('x (m, UTM Zone 10)')
            plt.ylabel('y (m)')
            if filter_option=='annual':
                fig.suptitle(plot_title)
            else:
                fig.suptitle(plot_title + '\n' + str(time[itime]))
            fig.savefig(os.path.join(plotfolder,'%s_%s_flux_map_streamlines_%s_%06d.png' % (run_folder,plotname_prefix,filter_option,itime)),dpi=300)
        
            # plot fluxes across edges, with direcitons for mean fluxes
            fig1, ax1 = plt.subplots(1,2,figsize=(16,11))
            poly_allbay_gdf.plot(ax=ax1[0],color='w',edgecolor='k')
            poly_allbay_gdf.plot(ax=ax1[1],color='w',edgecolor='k')
            gdf.plot(column='logmean',ax=ax1[0],vmin=np.log10(qmin1),vmax=np.log10(qmax1),cmap='jet',legend=True,
                legend_kwds={'label' : 'log10 (mean flux) (%s)' % units,'fraction' : 0.02, 'pad' : 0.0, 'orientation' : 'horizontal'})
            gdf.plot(column='logrms',ax=ax1[1],vmin=np.log10(qmin1),vmax=np.log10(qmax1),cmap='jet',legend=True,
                legend_kwds={'label' : 'log10 (%0.2f x RMS flux) (%s)' % (alpha,units),'fraction' : 0.02, 'pad' : 0.0, 'orientation' : 'horizontal'})
            ind = edge_length > min_edge_length
            ax1[0].quiver(xe[ind],ye[ind],nx[ind],ny[ind],scale=100,scale_units='width',width=0.001)
            for iax in [0,1]:
                ax1[iax].axis('off')
                ax1[iax].axis('tight')
                ax1[iax].axis('equal')
                #ax1[iax].axis((np.min(x),np.max(x),np.min(y),np.max(y)))
            fig1.tight_layout(rect=[0, 0.03, 1, 0.95])
            if filter_option=='annual':
                fig1.suptitle(plot_title)
            else:
                fig1.suptitle(plot_title + '\n' + str(time[itime]))
            fig1.savefig(os.path.join(plotfolder,'%s_%s_flux_map_mean_and_rms_edges_%s_%06d.png' % (run_folder,plotname_prefix,filter_option,itime)),dpi=300)
        
            # plot mean fluxes at centroids and RMS fluxes across edges
            fig2, ax2 = plt.subplots(figsize=(8.5,11))
            norm = mpl.colors.Normalize(vmin=np.log10(qmin1),vmax=np.log10(qmax1))
            poly_allbay_gdf.plot(ax=ax2,color='w',edgecolor='k')
            gdf.plot(column='logrms',ax=ax2,norm=norm,cmap='jet',legend=True,
                legend_kwds={'label' : 'log10 Flux (%s)' % units,'fraction' : 0.01, 'pad' : -0.1})
            ax2.axis('off')
            ax2.quiver(xc,yc,qxc/qmax1,qyc/qmax1,np.log10(qcM),cmap='jet',norm=norm,width=0.002,scale_units='width',scale=arrow_scale)
            ax2.quiver(legloc[0],legloc[1],key_arrow_frac,0,np.log10(key_arrow_frac*qmax1),cmap='jet',norm=norm,width=0.005,scale_units='width',scale=arrow_scale)
            ax2.text(legloc[0],legloc[1]+1000,'%0.0f %s' % (key_arrow_frac*qmax1, units))
            fig2.tight_layout(rect=[0, 0.03, 1, 0.95])
            ax2.axis(axlim)
            if filter_option=='annual':
                fig2.suptitle(plot_title + '\nvectors = mean flux, edges = 0.12 x RMS deviation from tidally filtered flux')
            else:
                fig2.suptitle(plot_title + '\nvectors = mean flux, edges = 0.12 x RMS deviation from tidally filtered flux\n' + str(time[itime]))
            fig2.savefig(os.path.join(plotfolder,'%s_%s_flux_map_mean_and_rms_vectors_%s_%06d.png' % (run_folder,plotname_prefix,filter_option,itime)),dpi=300)
            
            # plot mean fluxe streamlines with RMS fluxes across edges
            fig3, ax3 = plt.subplots(figsize=(8.5,11))
            norm = mpl.colors.Normalize(vmin=np.log10(qmin1),vmax=np.log10(qmax1))
            poly_allbay_gdf.plot(ax=ax3,color='w',edgecolor='k')
            gdf.plot(column='logrms',ax=ax3,norm=norm,cmap='jet',linewidth=1,legend=True,
                legend_kwds={'label' : 'log10 Flux (%s)' % units,'fraction' : 0.01, 'pad' : -0.1})
            ax3.streamplot(xg,yg,qxg,qyg,color=np.log10(qgM),cmap='jet',norm=norm,density=5,linewidth=1)
            ax3.axis('off')
            fig3.tight_layout(rect=[0, 0.03, 1, 0.95])
            ax3.axis(axlim)
            if filter_option=='annual':
                fig3.suptitle(plot_title + '\nstreamlines = mean flux, edges = 0.12 x RMS deviation from tidally filtered flux')
            else:
                fig3.suptitle(plot_title + '\nstreamlines = mean flux, edges = 0.12 x RMS deviation from tidally filtered flux\n' + str(time[itime]))
            fig3.savefig(os.path.join(plotfolder,'%s_%s_flux_map_streamlines_plus_rms_%s_%06d.png' % (run_folder,plotname_prefix,filter_option,itime)),dpi=300)
        
            # plot mean flux magnitude in color with RMS fluxes across edges and black streamlines on top
            fig4, ax4 = plt.subplots(figsize=(8.5,11))
            norm = mpl.colors.Normalize(vmin=np.log10(qmin1),vmax=np.log10(qmax1))
            poly_allbay_gdf.plot(ax=ax4,color='w',edgecolor='k')
            ax4.pcolor(xg-dx/2,yg-dx/2,np.log10(qgM),norm=norm,cmap='jet')
            gdf.plot(column='logrms',ax=ax4,norm=norm,cmap='jet',linewidth=2,legend=True,
                legend_kwds={'label' : 'log10 Flux (%s)' % units,'fraction' : 0.01, 'pad' : -0.1})
            ax4.streamplot(xg,yg,qxg,qyg,color='k',cmap='jet',norm=norm,density=5,linewidth=0.5)
            ax4.axis('off')
            fig4.tight_layout(rect=[0, 0.03, 1, 0.95])
            ax4.axis(axlim)
            if filter_option=='annual':
                fig4.suptitle(plot_title + '\nbackground color = mean flux magnitude, edges = 0.12 x RMS deviation from tidally filtered flux\nstreamlines = mean flux direction')
            else:
                fig4.suptitle(plot_title + '\nbackground color = mean flux magnitude, edges = 0.12 x RMS deviation from tidally filtered flux\nstreamlines = mean flux direction\n' + str(time[itime]))
            fig4.savefig(os.path.join(plotfolder,'%s_%s_flux_map_streamlines_plus_mean_and_rms_%s_%06d.png' % (run_folder,plotname_prefix,filter_option,itime)),dpi=300)
        
            plt.close('all')
                    
        # to make into a movie, in terminal on chicago, navigate into folder with the plots and type
        # ffmpeg -framerate 10 -start_number 0 -i FR17_017_Algae_flux_map_streamlines_plus_rms_spring-neap_%06d.png -f mp4 -vcodec h264 -pix_fmt yuv420p din_flux_streamlines_spring_neap_filtered.mp4
        hdata.close()