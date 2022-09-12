
''' alliek August 2022
plot bay-wide maps of rates such as primary productivity, oxygen consumption, denitrification, etc. 
at seasonal, monthly, or even weekly time steps. this script can plot one time step at a time (e.g. Oct, Nov, Dec, etc.), 
comparing a list of run / water year combos at each time step, with one run/wy in each column, or it can plot multiple 
time steps for just one run all on the same plot, with each time step being a column. you may plot rates 
normalized by area, volume, or nothing. note that to create plots for a given time averaging period, you must
have already conducted a time average of the balance tables for that period in step6_aggregate_in_time.py (in the 
Scripts/create_balance_tables directory of this Control_Volume_Analysis repository). it is common to skip some
time averaging periods to save space, so you may need to go back and run step6_aggregate_in_time.py again, if you
want time resolution like weekly.

feel free to define new rates -- search for "if rate_name==" to see where the rates are defined

the results are saved in a subfolder called "rate_maps"

'''

##################
# IMPORT MODULES
##################

import copy
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib as mpl
from mpl_toolkits.axes_grid1 import ImageGrid
import numpy as np
import os, sys
import pandas as pd
import cmocean 
import geopandas as gpd
from importlib import reload
import control_volume_plotting_library as CVPL # plotting library must be in same folder as this script
reload(CVPL)

###################
## USER INPUT
###################

############################################################################################################################
# RUN ID AND WATER YEAR LISTS ARE SPECIAL BECAUSE THESE DETERMINE THE NUMBER OF SUBPLOTS AND THEIR CONTENT
#
#       make a list of run ID's and a list of water years. these lists should be the same length N. the script will make 
#       subplots with N columns where each column n corresponds to run runid_list[n] and water year wy_list[n]. one figure 
#       with N subplots will be created per time step in the time averaging period (e.g. 4 figures for Seasonal averages)
#
#       special case: if there is only ONE entry in runid_list and wy_list, there is an option to try and stuff all of 
#       the time steps onto a single plot, instead of having one plot per time step -- if you want to do this, set 
#       all_time_together = True below
#
########################################################################################################################

# this example will make figures with 3 subplots, each corresponding to a different run
#runid_list = ['FR13_025','FR17_018','FR18_006']
#wy_list = [2013, 2017, 2018]

# this example will make figures with 6 subplots, each corresponding to a different water year for the same run
runid_list = ['G141_13to18_215','G141_13to18_215','G141_13to18_215','G141_13to18_215','G141_13to18_215','G141_13to18_215']
wy_list = [2013, 2014, 2015, 2016, 2017, 2018]

# this is like the previous example but also compares apples-to-apples full resolution and aggregated runs
#runid_list = ['G141_13to18_197','FR13_025','G141_13to18_197','G141_13to18_197','G141_13to18_197','G141_13to18_197','FR17_018','G141_13to18_197','FR18_006']
#wy_list = [2013, 2013, 2014, 2015, 2016, 2017, 2017, 2018, 2018]

# in this example, provided that all_time_together = True (see below) a single 1xN figure is generated where N is the 
# number of time averaging periods in 2013 (e.g. 4 for Seasonal, 12 for monthly). if all_time_together = False, this
# example will generate N figures with one subplot each
#runid_list = ['G141_13to18_215']
#wy_list = [2013]


################################################################################################################
# THE FOLLOWING LISTS ARE JUST FOR BATCH PROCESSING PURPOSES, SO THE USER DOESN'T HAVE TO CHANGE THE SCRIPT
# EACH TIME THEY WANT TO PLOT A NEW RATE, TIME AVERAGING PERIOD, NORMALIZATION, ETC. CAN JUST RUN IT ALL AT ONCE
################################################################################################################

# specify the rates you want to plot right now (see function get_rate_properties(rate_name) defined below to 
# get their definitions)
rate_list = ['oxycon-water','oxycon-sed','dpp','dpp-benthic','dpp-pelagic','denit','n-dpp','n-dpp-pelagic',
             'n-dpp-benthic','din_recycling','dmin_water','dmin_sed','din_loss','tn_loss','n-algae-sed','pon-sed',
             'diats1-loss','diats1-aut','tn_include_sediment_loss']
#rate_list = ['dpp']

# list of time averaging periods (choices are 'Annual','Seasonal','Monthly')
#time_period_list = ['Annual','Seasonal','Monthly']
time_period_list = ['Seasonal']

# list of normalizations (divide by 'None','Area','Volume')
#norm_list = ['None','Area','Volume']
norm_list = ['Area']

# get length of run list and wy list, make sure they're the same length
nruns = len(runid_list)
assert nruns == len(wy_list)

# if there is only ONE entry in runid_list and wy_list, there is an option to try and stuff all of the time steps onto a single
# plot, instead of having one plot per time step -- the script will try to automatically tile the subplots so this fits, but it
# may get ridiculous for something like monthly averages
all_time_together = False

# base directory for the model runs and the output figures (in theory should be able to run on windows laptop with mounted drives or on server)
#base_dir = r'X:\hpcshared'
run_base_dir = '/richmondvol1/hpcshared'
figure_base_dir = '/chicagovol1/hpcshared/open_bay/bgc/figures'

# nanpercentile for color map cutoff
cper = 97.5

# set the approximate size of the figure subplots in inches (if there are N subplots the figure will be N x subplot_width wide)
subplot_width = 4
subplot_height = 5.5

# set font size (may want to adjust)
plt.rcParams['font.size'] = '16'

# path to the shapefile for full res / aggregated runs
shp_fn_FR = os.path.join(run_base_dir,'inputs','shapefiles','Agg_mod_contiguous_plus_subembayments_shoal_channel.shp')
shp_fn_AGG = os.path.join(run_base_dir,'inputs','shapefiles','Agg_mod_contiguous_141.shp')

# this gigantic function is really user input because this is where the user can define different rates to plot.
# the user should keep a close eye on this function becuase the reaction_list variables may need to change if more
# substances are added to the model or if the user has changed the way reactions are grouped in 
# step3_group_reactions_for_composite_parameters.py, as specified in composite_reaction_dict of step0_config.py)
def get_rate_properties(rate_name):

    ''' 
    usage: 
    
    rate_title, grams_of_what, balance_table_list, multiplier_list, reaction_list, cmap, cmap_diverging, log_scale = get_rate_properties(rate_name)
    
    '''
    if rate_name=='oxycon-water':
    
        rate_title = 'Oxygen Consumption (Water Column)'        # title for figure
        grams_of_what = 'O'                                     # grams of what in the units?   
        balance_table_list = ['oxy_Table.csv']                  # list of balance tables
        multiplier_list = [-1]                                  # multiplier for each balance table
        reaction_list = [['OXY,dOxCon']]                        # for each balance table, list of reactions to sum
        cmap = cmocean.cm.dense                                 # color map
        cmap_diverging = False                                  # center at zero (True if rate goes positive and negative)?
        log_scale = False                                       # include a log scale plot?

    elif rate_name=='oxycon-sed':
    
        rate_title = 'Oxygen Consumption (Sediment)'
        grams_of_what = 'O'
        balance_table_list = ['oxy_Table.csv']
        multiplier_list = [-1]
        reaction_list = [['OXY,dMinDetCS1', 'OXY,dMinDetCS2', 'OXY,dMinOOCS1', 'OXY,dMinOOCS2']]
        cmap = cmocean.cm.dense  
        cmap_diverging = False
        log_scale = False  

    elif rate_name=='dpp':
    
        rate_title = 'Net Primary Productivity' 
        grams_of_what = 'C'
        balance_table_list = ['algae_Table.csv']
        multiplier_list = [1]
        reaction_list = [['Diat,dPPDiat','Green,dPPGreen','DiatS1,dPPDiatS1']]
        cmap = cmocean.cm.algae
        cmap_diverging = False
        log_scale = False

    elif rate_name=='dpp-benthic':
    
        rate_title = 'Net Primary Productivity (Benthic)'
        grams_of_what = 'C'
        balance_table_list = ['algae_Table.csv']
        multiplier_list = [1]
        reaction_list = [['DiatS1,dPPDiatS1']]
        cmap = cmocean.cm.algae
        cmap_diverging = False
        log_scale = False

    elif rate_name=='dpp-pelagic':
    
        rate_title = 'Net Primary Productivity (Pelagic)'
        grams_of_what = 'C'
        balance_table_list = ['algae_Table.csv']
        multiplier_list = [1]
        reaction_list = [['Diat,dPPDiat','Green,dPPGreen']]
        cmap = cmocean.cm.algae
        cmap_diverging = False
        log_scale = False
    
    elif rate_name=='denit':
        
        rate_title = 'Denitrification'                      
        grams_of_what = 'N'                                 
        balance_table_list = ['din_Table.csv']              
        multiplier_list = [-1]                              
        reaction_list = [["NO3,dDenit", "NO3,dNiDen"]]      
        cmap = cmocean.cm.dense                             
        cmap_diverging = False                              
        log_scale = False                                   

    elif rate_name=='n-dpp':
    
        rate_title = 'Net Primary Productivity'
        grams_of_what = 'N'
        balance_table_list = ['din_Table.csv']
        multiplier_list = [-1]
        reaction_list = [['DIN,dDINUpt','DIN,dDINUptS1']]
        cmap = cmocean.cm.algae
        cmap_diverging = False
        log_scale = False

    elif rate_name=='n-dpp-pelagic':
    
        rate_title = 'Net Primary Productivity'
        grams_of_what = 'N'
        balance_table_list = ['din_Table.csv']
        multiplier_list = [-1]
        reaction_list = [['DIN,dDINUpt']]
        cmap = cmocean.cm.algae
        cmap_diverging = False
        log_scale = False

    elif rate_name=='n-dpp-benthic':
    
        rate_title = 'Net Primary Productivity'
        grams_of_what = 'N'
        balance_table_list = ['din_Table.csv']
        multiplier_list = [-1]
        reaction_list = [['DIN,dDINUptS1']]
        cmap = cmocean.cm.algae
        cmap_diverging = False
        log_scale = False 

    elif rate_name=='din_recycling':
    
        rate_title = 'DIN Recycling (Respiration + Mortality)'
        grams_of_what = 'N'
        balance_table_list = ['din_Table.csv']
        multiplier_list = [1]
        reaction_list = [["NH4,dZ_NRes",
                          "NH4,dNH4Aut"]]
        cmap = cmocean.cm.balance
        cmap = cmocean.cm.amp
        cmap_diverging = False
        log_scale = False

    elif rate_name=='dmin_water':
    
        rate_title = 'DON + PON Mineralization'
        grams_of_what = 'N'
        balance_table_list = ['din_Table.csv']
        multiplier_list = [1]
        reaction_list = [["NH4,dMinDON","NH4,dMinPON"]]
        cmap = cmocean.cm.matter
        cmap_diverging = False
        log_scale = False

    elif rate_name=='dmin_sed':
    
        rate_title = 'Detritus Mineralization'
        grams_of_what = 'N'
        balance_table_list = ['din_Table.csv']
        multiplier_list = [1]
        reaction_list = [['NH4,dMinTotalDetNS']]
        cmap = cmocean.cm.turbid
        cmap_diverging = False
        log_scale = False

    
    elif rate_name=='din_loss':
    
        rate_title = 'DIN Assimilation'
        grams_of_what = 'N'
        balance_table_list = ['din_Table.csv']
        multiplier_list = [-1]
        reaction_list = [['NH4,dMinTotalDetNS',
                          'DIN,dDINUpt',
                          'DIN,dDINUptS1',
                          'NO3,dDenit',
                          'NO3,dNiDen',
                          'NH4,dMinPON',
                          'NH4,dMinDON',
                          'NH4,dZ_NRes',
                          'NH4,dNH4Aut']]
        cmap = cmocean.cm.balance
        cmap_diverging = True
        log_scale = False

    elif rate_name=='tn_loss':

        rate_title = 'TN Reactive Loss'  
        grams_of_what = 'N'
        balance_table_list = ['tn_Table.csv']
        multiplier_list = [-1]
        reaction_list = [['NO3,dDenit',
                          'NO3,dNiDen',
                          'Algae,dSedAlgae',
                          'PON,dSedPON',
                          'DiatS1,dMrtDiatS1',
                          'DiatS1,dBurS1Diat',
                          'NH4,dMinTotalDetNS',
                          'NH4,dNH4AUTS1',
                          'NH4,dClam_NRes',
                          'PON1,dClam_NDef',
                          'Algae,dClam_Algae',
                          'PON1,dClam_PON1']]
        cmap = cmocean.cm.balance
        cmap_diverging = True
        log_scale = False

    elif rate_name=='n-algae-sed':
    
        rate_title = 'Settling of Algae'
        grams_of_what = 'N'
        balance_table_list = ['tn_Table.csv']
        multiplier_list = [-1]
        reaction_list = [["Algae,dSedAlgae"]]
        cmap = cmocean.cm.algae
        cmap_diverging = False
        log_scale = False

    elif rate_name=='pon-sed':

        rate_title = 'Settling of PON'
        grams_of_what = 'N'
        balance_table_list = ['tn_Table.csv']
        multiplier_list = [-1]
        reaction_list = [["PON,dSedPON"]]
        cmap = mpl.cm.Greys
        cmap_diverging = False
        log_scale = False

    elif rate_name=='diats1-loss':
    
        rate_title = 'Benthic Algae Mortality/Burial'
        grams_of_what = 'N'
        balance_table_list = ['tn_Table.csv']
        multiplier_list = [-1]
        reaction_list = [['DiatS1,dMrtDiatS1',
                          'DiatS1,dBurS1Diat']]
        cmap = mpl.cm.Purples
        cmap_diverging = False
        log_scale = False

    elif rate_name=='diats1-aut':

        rate_title = 'Benthic Algae Autolysis'
        grams_of_what = 'N'
        balance_table_list = ['tn_Table.csv']
        multiplier_list = [1]
        reaction_list = [['NH4,dNH4AUTS1']]
        cmap = mpl.cm.Oranges
        cmap_diverging = False
        log_scale = False

    elif rate_name=='tn_include_sediment_loss':
    
        rate_title = 'TN (including sediment N) Reactive Loss'
        grams_of_what = 'N'
        balance_table_list = ['tn_include_sediment_Table.csv']
        multiplier_list = [-1]
        reaction_list = [['NO3,dDenit',
                          'NO3,dNiDen',
                          'DetNS2,dBurS2DetN',
                          'OONS2,dBurS2OON',
                          'DiatS1,dBurS1Diat']]
        cmap = mpl.cm.Spectral_r
        cmap_diverging = False
        log_scale = False
    
    return rate_title, grams_of_what, balance_table_list, multiplier_list, reaction_list, cmap, cmap_diverging, log_scale

# subset of polygons to include in plot (don't mess with this unless the shapefiles are drastically altered)
iplot_FR = [0, 117, 139, 2, 113, 114, 115, 111, 1, 3, 116, 7, 4, 112, 5, 108, 109, 110, 9, 107, 
6, 8, 29, 10, 12, 11, 138, 137, 100, 19, 18, 13, 20, 26, 25, 21, 14, 24, 101, 102, 103, 104, 
105, 106, 28, 27, 22, 15, 30, 23, 35, 34, 33, 32, 31, 17, 41, 40, 39, 38, 37, 36, 16, 140, 
44, 43, 42, 46, 45, 49, 47, 97, 98, 86, 96, 95, 85, 93, 52, 87, 94, 48, 51, 50, 90, 88, 91, 
89, 92, 53, 56, 99, 54, 55, 57, 67, 65, 66, 136, 58, 59, 63, 64, 60, 62, 61, 143, 144, 141, 
68, 69, 70, 71, 78, 72, 84, 79, 146, 80, 82, 83, 142, 145, 73, 81, 74, 76, 77, 75]
iplot_AGG = [  0,   1,   2,   3,   4,   5,   6,   7,   8,   9,  10,  11,  12,
    13,  14,  15,  16,  17,  18,  19,  20,  21,  22,  23,  24,  25,
    26,  27,  28,  29,  30,  31,  32,  33,  34,  35,  36,  37,  38,
    39,  40,  41,  42,  43,  44,  45,  46,  47,  48,  49,  50,  51,
    52,  53,  54,  55,  56,  57,  58,  59,  60,  61,  62,  63,  64,
    65,  66,  67,  68,  69,  70,  71,  72,  73,  74,  75,  76,  77,
    78,  79,  80,  81,  82,  83,  84,  85,  86,  87,  88,  89,  90,
    91,  92,  93,  94,  95,  96,  97,  98,  99, 100, 101, 102, 103,
   104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115,
   134, 136, 137, 138, 139, 140]

# axis limits
axlim = (531280.627955355, 610527.2330959855, 4138850.8659710716, 4233404.6647333605)

##################
### MAIN
##################

# get strings with concise lists of runs and water years
run_list_str = CVPL.make_concise_runid_list_string(runid_list)
wy_list_str = CVPL.make_concise_water_year_list_string(wy_list)

# path to figures, create if it does not exist
figure_path = os.path.join(figure_base_dir, run_list_str, 'rate_maps')
if not os.path.exists(figure_path):
    os.makedirs(figure_path)

# loop through rates to plot
for rate_name in rate_list:

    # load up a bunch of variables specific to this rate_name (this function is defined in the user input section above)
    rate_title, grams_of_what, balance_table_list, multiplier_list, reaction_list, cmap, cmap_diverging, log_scale = get_rate_properties(rate_name)

    # loop through averaging time periods (Annual, Seasonal, Monthly)
    for time_period in time_period_list:

        # loop through norms (Area, Volume, None)
        for norm in norm_list:

            # units for normalized data and string for including in figure name
            if norm == 'Volume':
                norm_units = 'g %s/m$^3$/d' % grams_of_what
                norm_name = '_Per_Volume'
            elif norm == 'Area':
                norm_units = 'g %s/m$^2$/d' % grams_of_what
                norm_name = '_Per_Area'
            elif norm == 'None':
                norm_units = 'g %s/d' % grams_of_what
                norm_name = ''
            else:
                raise Exception("must specifiy normalization correctly")
            norm_units_log = 'Log10 ' + norm_units

            #####################
            # here's the meat
            #####################
            
            # check number of balance tables 
            ntables = len(balance_table_list)
            
            # initiliaze color bar limits, which will be calculated by looking across all the runs and all the time windows
            pmin_all = 0
            pmax_all = 0
            if log_scale:
                pmin_log_all = 1e30
                pmax_log_all = -1e30
            
            # initialize dictionary containing geodataframes for plotting all the runs and time windows (this is confusing, sorry about that, but it works and is fast enough)
            gdf_all_dict = {}
            gdf_log_all_dict = {}
            time_labels_dict = {}
            
            # loop through the runs, building up a the dictionary of lists of geodataframes for plotting, and tracking the color bar limits 
            for irun in range(nruns):
            
                # get run ID and water year
                runid = runid_list[irun]
                wy = wy_list[irun]

                # get path to the balance table folder in the run folder
                run_dir = CVPL.get_run_dir(run_base_dir, runid)
                balance_table_dir = os.path.join(run_dir,'Balance_Tables')

                # path to the shapefile w/ the base level control volumes
                if 'FR' in runid:
                    shp_fn = shp_fn_FR
                    iplot = iplot_FR
                else:
                    shp_fn = shp_fn_AGG
                    iplot = iplot_AGG

                # load the shapefile and initialize Rate column
                gdf = gpd.read_file(shp_fn)
                gdf['Rate'] = np.nan
            
                # copy for plotting log
                if log_scale:
                    gdf_log = gdf.copy(deep=True)
            
                # read the first balance table and sum up the reacitons, mutiplying by the appropriate stoichiometric multiplier
                balance_table_name = balance_table_list[0].replace('.csv','_%s.csv' % time_period)
                df = pd.read_csv(os.path.join(balance_table_dir, balance_table_name))
                rate = multiplier_list[0]*df[reaction_list[0]].sum(axis=1)
                
                # if there is more than one balance table, add those up too, summing the reactions by the multipliers
                if ntables>1:
                    for i in range(1,ntables):
                        balance_table_name = balance_table_list[i].replace('.csv','_%s.csv' % time_period)
                        df = pd.read_csv(os.path.join(balance_table_dir, balance_table_name))
                        rate = rate + multiplier_list[i]*df[reaction_list[i]].sum(axis=1)
                
                # from the last balance table, grab all the control voulme ID and geometry info, as well as the time axis, then
                # add the rate 
                df = df[['time', 'Time Period', 'Control Volume', 'Volume (Mean)', 'Area']]
                df['Rate'] = rate
                df['time'] = df['time'].astype('datetime64[ns]')

                # select just the data in the water year specified for this plotting window
                ind = np.logical_and(df['time']>=np.datetime64('%d-10-01' % (wy-1)), df['time']<np.datetime64('%d-10-01' % wy))
                df = df.loc[ind]
                
                # get a list of the time period names
                ind = df['Control Volume'] == 'polygon0'
                time_labels = df['Time Period'].loc[ind].values
                ntime = len(time_labels)
                
                # initialize list of geodataframes and a list of corresponding time window labels
                gdf_all = []
                if log_scale:
                    gdf_log_all = []

                # loop through time windows, building up list of geodataframes, and finding the max and min values
                for itime in range(ntime):
                
                    # loop through teh polygons
                    for poly in range(len(gdf)):
                    
                        # polygon name
                        polyname = 'polygon%d' % poly

                        # indices corresponding to polygon
                        ind = (df['Control Volume'] == polyname).values

                        # get divisor based on normaliization
                        if norm=='Volume':
                            V = df.loc[ind]['Volume (Mean)'].iloc[itime]
                        elif norm=='Area':
                            V = df.loc[ind]['Area'].iloc[itime]
                        elif norm=='None':
                            V = 1
                            
                        # find intersection of polygon and time window
                        
                        # take the average over this time window, normalize, and load into a geodataframe
                        gdf['Rate'].iloc[poly] = df.loc[ind]['Rate'].iloc[itime]/V
                        if log_scale:
                            gdf_log['Rate'].iloc[poly] = np.log10(df.loc[ind]['Rate'].iloc[itime]/V)
                            
                
                    # get the max and min parameter value
                    pmax = np.nanpercentile(gdf['Rate'].iloc[iplot],cper)
                    pmin = np.nanpercentile(gdf['Rate'].iloc[iplot],100-cper)
                    if log_scale:
                        pmax_log = np.nanpercentile(gdf_log['Rate'].iloc[iplot],cper)
                        pmin_log = np.nanpercentile(gdf_log['Rate'].iloc[iplot],100-cper)
                    
                    # keep track of the biggest limits across time windows AND across all runs
                    pmin_all = np.min([pmin,pmin_all])
                    pmax_all = np.max([pmax,pmax_all])
                    if log_scale:
                        pmin_log_all = np.min([pmin_log,pmin_log_all])
                        pmax_log_all = np.max([pmax_log,pmax_log_all])
                    
                    # append geodataframes
                    gdf_all.append(copy.deepcopy(gdf))
                    if log_scale:
                        gdf_log_all.append(copy.deepcopy(gdf_log))
            
                # now append list of geodataframes to the dictionary
                time_labels_dict[irun] = time_labels.copy()
                gdf_all_dict[irun] = gdf_all.copy()
                if log_scale:
                    gdf_log_all_dict[irun] = gdf_log_all.copy()
                
            # if it's a diverging colormap, make the max and min the same amplitude
            if cmap_diverging:
                pmax_all = np.max([pmax_all,-pmin_all])
                pmin_all = -pmax_all

            # now loop through time winodws and plot all the runs we are comparing in the same figure with the same color bar limits

            # make figure title
            cbar_title = '%s\n(%s)' % (rate_title, norm_units)
            if log_scale:
                cbar_title_log = '%s\n(%s)' % (rate_title, norm_units_log)

            # define a little function to make a figure and axis
            def make_figure(figsize, nrows, ncols):

                # set up figure subwindows with room for a colorbar 
                fig = plt.figure(figsize=figsize)
                ax = ImageGrid(fig, 111,          # as in plt.subplot(111)
                             nrows_ncols=(nrows,ncols),
                             axes_pad=0.15,
                             share_all=True,
                             cbar_location="right",
                             cbar_mode="single",
                             cbar_size="7%",
                             cbar_pad=0.15,
                             )

                return fig, ax

            def add_subplot(iaxis, itime, irun):

                # get geodataframe
                gdf = gdf_all_dict[irun][itime]
                if log_scale:
                    gdf_log = gdf_log_all_dict[irun][itime]
    
                # path to the shapefile w/ the base level control volumes
                if 'FR' in runid_list[irun]:
                    iplot = iplot_FR
                else:
                    iplot = iplot_AGG
    
                # get outline for plotting
                gdf['dummy'] = 1
                outline = gdf.iloc[iplot].dissolve(by='dummy')
                
                # add to plot
                gdf.iloc[iplot].plot(ax=ax[iaxis], column='Rate', cmap=cmap, vmin = pmin_all, vmax = pmax_all)
                outline.boundary.plot(ax=ax[iaxis],edgecolor='k')
                ax[iaxis].axis(axlim)
                
                # turn off axis, set title 
                ax[iaxis].axis('off')
                ax[iaxis].set_title('%s' % time_labels_dict[irun][itime])
                
                # same for log plot
                if log_scale:
                    gdf_log.iloc[iplot].plot(ax=ax1[iaxis], column='Rate', cmap=cmap, vmin = pmin_log_all, vmax = pmax_log_all)
                    outline.boundary.plot(ax=ax1[iaxis],edgecolor='k')
                    ax1[iaxis].axis(axlim)
                
                    ax1[iaxis].axis('off')
                    ax1[iaxis].set_title('%s' % time_labels_dict[irun][itime])

            def finish_up_figure():

                # add the colorbar
                norm1 = mpl.colors.Normalize(vmin=pmin_all, vmax=pmax_all)
                mpl.colorbar.ColorbarBase(ax[-1].cax, cmap=cmap,norm=norm1, label=cbar_title)
                if log_scale:
                    norm1 = mpl.colors.Normalize(vmin=pmin_log_all, vmax=pmax_log_all)
                    mpl.colorbar.ColorbarBase(ax1[-1].cax, cmap=cmap,norm=norm1, label=cbar_title_log)
                
                # save and close
                fig.suptitle(runid_list[irun])
                fig.tight_layout(rect=[0, 0.03, 1, 0.98])
                fig.savefig(os.path.join(figure_path, figure_fn))
                if log_scale:
                    fig1.suptitle(runid_list[irun])
                    fig1.tight_layout(rect=[0, 0.03, 1, 0.98])
                    fig1.savefig(os.path.join(figure_path, figure_log_fn))
                
                plt.close('all') 

            # if there is only one run, there's an option to plot all the time windows on the same figure -- this does that
            if nruns==1 and all_time_together:
                
                # subplot dimensions and figure size
                nrows = 1
                ncols = ntime
                figsize = (subplot_width*ncols, subplot_height*nrows)

                # make figure name
                figure_fn = '%s_%s_%s_Map%s_%s_ALLTIME.png' % (run_list_str, wy_list_str, rate_name, norm_name, time_period)
                if log_scale:
                    figure_log_fn = '%s_%s_log10_%s_Map%s_%s_ALLTIME.png' % (run_list_str, wy_list_str, rate_name, norm_name, time_period)

                # set up figure subwindows with room for a colorbar 
                fig, ax = make_figure(figsize, nrows, ncols)
                if log_scale: 
                    fig1, ax1 = make_figure(figsize, nrows, ncols)

                # loop through the times and add a subplot for each time
                irun = 0
                for itime in range(ntime):
                
                    add_subplot(itime, itime, irun)
                
                finish_up_figure()            

            # otherwise make a separate plot for each time window, where the subplots are the different runs
            else:

                # set number of subplots and figure size
                nrows = 1
                ncols = nruns
                figsize = (subplot_width*ncols, subplot_height*nrows)

                for itime in range(ntime):
                    
                    # make figure name
                    figure_fn = '%s_%s_%s_Map%s_%s_%04d.png' % (run_list_str, wy_list_str, rate_name, norm_name, time_period, itime)
                    if log_scale:
                        figure_log_fn = '%s_%s_log10_%s_Map%s_%s_%04d.png' % (run_list_str, wy_list_str, rate_name, norm_name, time_period, itime)
                
                    # set up figure subwindows with room for a colorbar 
                    fig, ax = make_figure(figsize, nrows, ncols)
                    if log_scale: 
                        fig1, ax1 = make_figure(figsize, nrows, ncols)
    
                    # loop through the runs and plot
                    for irun in range(nruns):
                
                        add_subplot(irun, itime, irun)

                    finish_up_figure()                 