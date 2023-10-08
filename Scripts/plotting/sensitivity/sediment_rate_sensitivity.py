
''' alliek oct 2023
pradeep wants to investigate how det and oons mineralization vary with sedimentation
rate to consider adjusting denitrification in s1/s2 model based on sedimentation

'''

##################
# IMPORT MODULES
##################

import sys,os
import copy
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib as mpl
if not 'DISPLAY' in os.environ:
    mpl.use('agg')
    plt.switch_backend('Agg')
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import numpy as np
import os, sys
import pandas as pd
import cmocean 
import geopandas as gpd
from importlib import reload
sys.path.append('..')
import control_volume_plotting_library as CVPL # plotting library must be in same folder as this script
reload(CVPL)

###################
## USER INPUT
###################


#runid_list = ['G141_22_078','G141_22_087','G141_22_083','G141_22_084','G141_22_085','G141_22_086']
#wy_list=[2022,2022,2022,2022,2022,2022]
#server_list = ['fortcollins','fortcollins','fortcollins','fortcollins','fortcollins','fortcollins']

#please do this for Run078 vs Run012 [BACWA], Run103[40%], Run104[60%], Run105[82%]) –
runid_list = ['G141_22_078','G141_22_102','G141_22_103','G141_22_104','G141_22_105']
wy_list=[2022,2022,2022,2022,2022]
server_list = ['fortcollins','fortcollins','fortcollins','fortcollins','fortcollins']


################################################################################################################
# THE FOLLOWING LISTS ARE JUST FOR BATCH PROCESSING PURPOSES, SO THE USER DOESN'T HAVE TO CHANGE THE SCRIPT
# EACH TIME THEY WANT TO PLOT A NEW RATE, TIME AVERAGING PERIOD, NORMALIZATION, ETC. CAN JUST RUN IT ALL AT ONCE
################################################################################################################

# list of rates
rate_list = ['settling','det_min','oo_min','denit']  
multiple_rates_on_same_figure = True
multiple_rates_figure_label = 'Settling_vs_Mineralization'
multiple_rates_figure_title = 'Settling and Mineralization'
caxis_limit_override = None#{'Area' : None, 'Volume': None, 'None' : None}
all_time_together=False

# list of time averaging periods (choices are 'Annual','Seasonal','Monthly')
time_period_list = ['Annual']

# list of normalizations (divide by 'None','Area','Volume')
norm_list = ['Area','None']

# get length of run list and wy list, make sure they're the same length, also check if all runs are the same
nruns = len(runid_list)
assert nruns == len(wy_list)

# base directory for the output figures (in theory should be able to run on windows laptop with mounted drives or on server)
figure_base_dir = '/richmondvol1/hpcshared/open_bay/bgc/figures'

# base directory for model input (used to find shapefiles)
input_base_dir = '/richmondvol1/hpcshared'

# nanpercentile for color map cutoff
cper = 90

# set the approximate size of the figure subplots in inches (if there are N subplots the figure will be N x subplot_width wide)
subplot_width = 4
subplot_height = 5

# set font size (may want to adjust)
plt.rcParams['font.size'] = '16'

# path to the shapefile for full res / aggregated runs
shp_fn_FR = os.path.join(input_base_dir,'inputs','shapefiles','Agg_mod_contiguous_plus_subembayments_shoal_channel.shp')
shp_fn_AGG = os.path.join(input_base_dir,'inputs','shapefiles','Agg_mod_contiguous_141.shp')


# this gigantic function is really user input because this is where the user can define different rates to plot.
# the user should keep a close eye on this function becuase the reaction_list variables may need to change if more
# substances are added to the model or if the user has changed the way reactions are grouped in 
# step3_group_reactions_for_composite_parameters.py, as specified in composite_reaction_dict of step0_config.py)
def get_rate_properties(rate_name):

    ''' 
    usage: 
    
    rate_title, grams_of_what, balance_table_list, multiplier_list, reaction_list, cmap, cmap_diverging = get_rate_properties(rate_name)
    '''

    if rate_name=='settling':
    
        rate_title = 'Settling'
        grams_of_what = 'C'
        balance_table_list = ['algae_Table.csv','poc1_Table.csv','poc2_Table.csv']
        multiplier_list = [-1,-1,-1]
        reaction_list = [['Diat,dSedDiat','Green,dSedGreen'],
                         ['POC1,dSedPOC1'],
                         ['POC2,dSedPOC2']]
        cmap = 'jet'#cmocean.cm.amp
        cmap_diverging = False
    
    elif rate_name=='det_min':
    
        rate_title = 'DetCS1+DetCS2 Mineralization'
        grams_of_what = 'C'
        balance_table_list = ['detcs1_Table.csv','detcs2_Table.csv']
        multiplier_list = [-1,-1]
        reaction_list = [['DetCS1,dMinDetCS1'],['DetCS2,dMinDetCS2']]
        cmap = 'jet'#cmocean.cm.amp
        cmap_diverging = False


    elif rate_name=='oo_min':
    
        rate_title = 'OOCS1+OOCS2 Mineralization'
        grams_of_what = 'C'
        balance_table_list = ['oocs1_Table.csv','oocs2_Table.csv']
        multiplier_list = [-1,-1]
        reaction_list = [['OOCS1,dMinOOCS1'],['OOCS2,dMinOOCS2']]
        cmap = 'jet'#cmocean.cm.amp
        cmap_diverging = False

    elif rate_name=='denit':
        
        rate_title = 'Denitrification'                      
        grams_of_what = 'N'                                 
        balance_table_list = ['din_Table.csv']              
        multiplier_list = [-1]                              
        reaction_list = [["NO3,dDenit"]]# already lumped this in, in latest version of CV scripts:"NO3,dNiDen"]]      
        cmap = 'jet'#cmocean.cm.amp # cmocean.cm.dense # make it positive to plot with assimilation                             
        cmap_diverging = False  
    
    return rate_title, grams_of_what, balance_table_list, multiplier_list, reaction_list, cmap, cmap_diverging

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

# flag to plot the percent change from the base case (run with and without this for sensitivty plot)
for plot_percent_change in [True,False]:

    # path to figures, create if it does not exist
    figure_path = os.path.join(figure_base_dir, run_list_str, 'sedimentation_sensitivity')
    if not os.path.exists(figure_path):
        os.makedirs(figure_path)
    print('\nfigures will be saved here: %s\n' % figure_path)
    
    # check if all the runs are the same
    if len(np.unique(runid_list))==1:
        all_runs_same = True
    else:
        all_runs_same = False
    
    # loop through averaging time periods (Annual, Seasonal, Monthly)
    for time_period in time_period_list:
    
        # loop through norms (Area, Volume, None)
        for norm in norm_list:
    
            # loop through rates to plot
            nrates = len(rate_list)
            for irate, rate_name in enumerate(rate_list):
    
                # load up a bunch of variables specific to this rate_name (this function is defined in the user input section above)
                rate_title, grams_of_what, balance_table_list, multiplier_list, reaction_list, cmap, cmap_diverging = get_rate_properties(rate_name)
    
                # override diverging colormap
                if plot_percent_change:
                    cmap='jet'
                    #cmap_diverging=True
    
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
    
                # override units
                if plot_percent_change:
                    norm_units = 'percent difference from base case'
    
                #######################################################################################################################################
                # here's phase 1 of the meat of this script
                # loop through the runs, building up a the dictionary of lists of geodataframes for plotting, and tracking the color bar limits 
                #######################################################################################################################################
                
                # check number of balance tables 
                ntables = len(balance_table_list)
                
                # initiliaze color bar limits, which will be calculated by looking across all the runs and all the time windows
                pmin_all = 0
                pmax_all = 0
                
                # initialize dictionary containing geodataframes for plotting all the runs and time windows (this is confusing, sorry about that, but it works and is fast enough)
                gdf_all_dict = {}
                time_labels_dict = {}
                
                # loop through the runs, 
                for irun in range(nruns):
                
                    # get run ID and water year
                    runid = runid_list[irun]
                    wy = wy_list[irun]
    
                    # get path to the balance table folder in the run folder
                    run_base_dir = '/%svol1/hpcshared' % server_list[irun]
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
    
                    # initialize output dataframe
                    if irun==0:
                        if irate==0:
                            poly_list = []
                            for irow in range(len(gdf)):
                                poly_list.append('polygon%d' % irow)
                            df_out = pd.DataFrame(poly_list,columns=['polygon'])
                            df_out['Area (m2)'] = gdf.area
                
                    # read the first balance table and sum up the reacitons, mutiplying by the appropriate stoichiometric multiplier
                    balance_table_name = balance_table_list[0].replace('.csv','_%s.csv' % time_period)
                    df = pd.read_csv(os.path.join(balance_table_dir, balance_table_name))
    
                    # need to check that all the reactions are in this run, 
                    reaction_list_0 = []
                    for rx in reaction_list[0]:
                        if rx in df.columns:
                            reaction_list_0.append(rx)
                    rate = multiplier_list[0]*df[reaction_list_0].sum(axis=1)
    
                    # if there is more than one balance table, add those up too, summing the reactions by the multipliers
                    if ntables>1:
                        for i in range(1,ntables):
                            balance_table_name = balance_table_list[i].replace('.csv','_%s.csv' % time_period)
                            df = pd.read_csv(os.path.join(balance_table_dir, balance_table_name))
    
                            # need to check that all reactions are in this run
                            reaction_list_i = []
                            for rx in reaction_list[i]:
                                if rx in df.columns:
                                    reaction_list_i.append(rx)
                            rate = rate + multiplier_list[i]*df[reaction_list_i].sum(axis=1)
                    
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
                                
                    
                        # if this is the base case, save it
                        if plot_percent_change:
                            if irun == 0:
                                Rate0 = gdf['Rate'].values
                            gdf['Rate'] = (gdf['Rate'] - Rate0)/Rate0 * 100
    
                        # add results to output dataframe
                        df_out['%s %s (%s)' % (runid, rate_title, norm_units)] = gdf['Rate'].values
    
                        # get the max and min parameter value
                        pmax = np.nanpercentile(gdf['Rate'].iloc[iplot],cper)
                        pmin = np.nanpercentile(gdf['Rate'].iloc[iplot],100-cper)
                        
                        # keep track of the biggest limits across time windows AND across all runs
                        pmin_all = np.min([pmin,pmin_all])
                        pmax_all = np.max([pmax,pmax_all])
                        
                        # append geodataframes
                        gdf_all.append(copy.deepcopy(gdf))
                
                    # now append list of geodataframes to the dictionary
                    time_labels_dict[irun] = time_labels.copy()
                    gdf_all_dict[irun] = gdf_all.copy()
    
                # if it's a diverging colormap, make the max and min the same amplitude
                if cmap_diverging:
                    pmax_all = np.max([pmax_all,-pmin_all])
                    pmin_all = -pmax_all
    
                # if a min/max is hard-coded, apply it here
                if not caxis_limit_override is None:
                    if cmap_diverging:
                        pmax_all = caxis_limit_override[norm]
                        pmin_all = - caxis_limit_override[norm]
                    else:
                        pmax_all = caxis_limit_override[norm]
                        pmin_all = 0
    
                # ######################################################################################################################
                # here is phase 2 of the meat of this script
                # now loop through time winodws and plot all the runs we are comparing in the same figure with the same color bar limits
                ########################################################################################################################
    
                # make figure title
                cbar_title = '%s\n(%s)' % (rate_title, norm_units)
    
                # make a function to add a subplot to figure
                def add_subplot(iaxis, itime, irun):
    
                    # get geodataframe
                    gdf = gdf_all_dict[irun][itime]
        
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
                    
                    # turn off axis 
                    ax[iaxis].axis('off')
    
                    # set title (only put titles in first row)
                    title_str = ''
                    if (not multiple_rates_on_same_figure) or irate==0:
                        if not all_runs_same:
                            title_str += '%s\n' % runid_list[irun]
                        title_str += time_labels_dict[irun][itime]
                    ax[iaxis].set_title(title_str)
    
                def add_colorbar():
    
                    # add the colorbar
                    cax = inset_axes(ax[-1],
                        width="5%",  
                        height="90%",
                        loc='center right',
                        borderpad=-2
                       )
    
                    # make colorbar behave well in case that all values are zero
                    if pmin_all==0 and pmax_all==0:
                        if cmap_diverging:
                            pmin_all_1 = 1
                            pmax_all_1 = 1
                        else:
                            pmin_all_1 = 0
                            pmax_all_1 = 1
                    else:
                        pmin_all_1 = pmin_all
                        pmax_all_1 = pmax_all
    
                    # make norm and add colorbar
                    norm1 = mpl.colors.Normalize(vmin=pmin_all_1, vmax=pmax_all_1)
                    mpl.colorbar.ColorbarBase(cax, cmap=cmap,norm=norm1, label=cbar_title, orientation='vertical')
                    
                def finish_up_figure():
    
                    # save and close
                    fig.tight_layout(rect=rect)   
                    fig.savefig(os.path.join(figure_path, figure_fn))
                     
    
                # figure out number of rows and columns 
                if nruns==1 and all_time_together:
                    ncols = ntime
                else: 
                    ncols = nruns
                if multiple_rates_on_same_figure:
                    nrows = nrates
                else:
                    nrows = 1
    
                # figure size depends on number of rows and columns, add some extra width for the legend which can be quite wide
                figsize = (subplot_width*ncols + 0.4*subplot_width, subplot_height*nrows)
    
                # the tight layout rectangle needs room for the legend, and also needs room for a suptitle if there is a 
                # suptitle, but we only have a suptitle in some cases 
                if multiple_rates_on_same_figure or (nruns==1 and all_time_together) or all_runs_same:
                    rect = [0, 0.01, 1-0.4/ncols, 1-0.025/nrows]
                else:
                    rect = [0, 0.01, 1-0.4/ncols, 0.99]
    
                # position of suptitle apparently needs to be adjusted for number of plots
                suptitle_y = np.min([0.98 + nrows*0.0014,0.99])
    
                #################################################################################################################
                # if there is only one run, there's an option to plot all the time windows on the same figure -- this does that
                #################################################################################################################
    
                if nruns==1 and all_time_together:
    
                    # if we are plotting one rate at a time, make the figure name and the figure for each rate
                    if not multiple_rates_on_same_figure:
                    
                        # make figure name
                        figure_fn = '%s_%s_Rate_Map%s_%s_%s_ALLTIME.png' % (run_list_str, wy_list_str, norm_name, time_period, rate_name)
                        
                        if plot_percent_change:
                            figure_fn=figure_fn.replace('.png','_PERCENT_CHANGE.png') 
    
                        # set up figure subwindows with room for a colorbar 
                        fig, ax = plt.subplots(nrows, ncols, figsize=figsize)
    
                        # put runid in suptitle since there's only one run
                        fig.suptitle(runid,y=suptitle_y)
    
                    # otherwise, if multiple rates are on the same figure, make the figure name and the figure only when we are
                    # working on the very first rate, the other times, grab the axis from the following row
                    else:
    
                        if irate==0:
    
                            # make figure name
                            figure_fn = '%s_%s_Rate_Map%s_%s_%s_ALLTIME.png' % (run_list_str, wy_list_str, norm_name, time_period, multiple_rates_figure_label)
                   
                            if plot_percent_change:
                                figure_fn=figure_fn.replace('.png','_PERCENT_CHANGE.png') 
    
                            # set up figure subwindows with room for a colorbar 
                            fig, ax1 = plt.subplots(nrows, ncols, figsize=figsize)
    
                            # add title -- if there is only one run or all runs are the same, put runid in the suptitle
                            if all_runs_same:
                                fig.suptitle(multiple_rates_figure_title + ': ' + runid,y=suptitle_y)
                            else:
                                fig.suptitle(multiple_rates_figure_title, y=suptitle_y)
            
                        # take the irate row of the axis
                        ax = ax1[irate,:]
    
                    # loop through the times and add a subplot for each time
                    for itime in range(ntime):
                    
                        add_subplot(itime, itime, irun)
    
                    # add a colorbar at the end of every ros
                    add_colorbar()        
    
                    # if plotting multiple rates on the same figure, save only on last rate, otherwise save for each rate
                    if (irate==(nrates-1)) or (not multiple_rates_on_same_figure):    
                        finish_up_figure()
                        plt.close('all')
    
                #####################################################################################################
                # otherwise make a separate plot for each time window, where the subplots are the different runs
                #####################################################################################################
    
                else:
    
                    if not multiple_rates_on_same_figure: 
    
                        for itime in range(ntime):
        
                            # make figure name
                            figure_fn = '%s_%s_Rate_Map_%s%s_%s_Time%04d.png' % (run_list_str, wy_list_str, time_period, norm_name, rate_name, itime)
    
                            if plot_percent_change:
                                figure_fn=figure_fn.replace('.png','_PERCENT_CHANGE.png') 
    
                            # set up figure subwindows with room for a colorbar 
                            fig, ax = plt.subplots(nrows, ncols, figsize=figsize)
    
                            # if all the runs are the same, add run as suptitle
                            if all_runs_same:
                                fig.suptitle(runid,y=suptitle_y)
            
                            # loop through the runs and plot
                            for irun in range(nruns):
                        
                                add_subplot(irun, itime, irun)
        
                            add_colorbar()            
                            finish_up_figure()
                            plt.close('all')
    
                    # if there are multiple rates on the same figure, we have generate a figure for each time step and keep them open 
                    # as we add all the rates to each... this may crash if we try to do weekly plots, but that would be silly to compare
                    # multiple runs on a week by week basis so probably we won't ever try that
                    else: 
    
                        # on first rate, open up the figures
                        if irate==0:
    
                            figure_fn_all = []
                            fig_all = []
                            ax_all = []
                            for itime in range(ntime):
    
                                # make figure name
                                figure_fn = '%s_%s_Rate_Map%s_%s_%s_Time%04d.png' % (run_list_str, wy_list_str, norm_name, time_period, multiple_rates_figure_label, itime)
                           
                                if plot_percent_change:
                                    figure_fn=figure_fn.replace('.png','_PERCENT_CHANGE.png') 
    
                                # set up figure subwindows with room for a colorbar 
                                fig, ax = plt.subplots(nrows, ncols, figsize=figsize)
    
                                # add title -- if there is only one run or all runs are the same, put runid in the suptitle
                                if all_runs_same:
                                    fig.suptitle(multiple_rates_figure_title + ': ' + runid,y=suptitle_y)
                                else:
                                    fig.suptitle(multiple_rates_figure_title, y=suptitle_y)
                                
                                # save the handles and figure names in lists
                                figure_fn_all.append(figure_fn)
                                fig_all.append(fig)
                                ax_all.append(ax)
    
                        # for each rate, leaf through the figures adding subplots
                        for itime in range(ntime):
    
                            # make figure name
                            fig = fig_all[itime]
                            ax = ax_all[itime][irate]
    
                            # loop through the runs and plot
                            for irun in range(nruns):
                        
                                add_subplot(irun, itime, irun)
    
                            add_colorbar()            
        
                        # on the last rate, finish up the figures
                        if irate == (nrates-1):
    
                            for itime in range(ntime):
                                figure_fn = figure_fn_all[itime]
                                fig = fig_all[itime]
    
                                finish_up_figure()
    
                            plt.close('all')
    
            if plot_percent_change:
                dataframe_fn = figure_fn.replace('.png','_PERCENT_CHANGE.csv')
            else:
                dataframe_fn = figure_fn.replace('.png','.csv')
            df_out.to_csv(os.path.join(figure_path, dataframe_fn))
        
            