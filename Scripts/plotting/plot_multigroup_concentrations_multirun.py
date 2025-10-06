'''

alliek dec 2023

this creates concentration plots for multiple runs across a set of "groups"
defined by the user, such as the RMP subembayments, or the sections of south bay

the results are saved in a subfolder called "concentration_multigroup"

'''

########################################################################################
## import python packages
########################################################################################

import sys, os
import pandas as pd
import numpy as np
import matplotlib.pylab as plt
import datetime as dt
import matplotlib.dates as mdates
from matplotlib.backends.backend_pdf import PdfPages
if not 'DISPLAY' in os.environ:
    import matplotlib
    matplotlib.use('agg')
    plt.switch_backend('Agg')
from importlib import reload
import control_volume_plotting_library as CVPL # plotting library must be in same folder as this script
reload(CVPL)


#########################################################################################
## user input
#########################################################################################

# run name and server where it is located

#runid_list = ['G141_13to18_284', 'G141_13to18_285', 'G141_13to18_286', 'G141_13to18_287']
#wystr_list = ['WY13to18','WY13to18','WY13to18','WY13to18']
#server_list = ['fortcollins','fortcollins','fortcollins','fortcollins']
#vol_list = ['vol1','vol1','vol1','vol1']

runid_list = ['FR21_007', 'FR21_009','FR21_008']
wystr_list = ['WY2021','WY2021','WY2021']
server_list = ['chicago','chicago','chicago']
vol_list = ['vol2','vol2','vol2']


# autoscale x axis (if you set to False, script will set min/max based on water year range)
# note: this option was added for the 2022 HAB simulations, you probably want to set it to False for everything else
autoscale_x = True

# optional start and end time (useful for comparing single water year to multiple water year runs, can set to None, otherwise
# set to date string with format like '2022-08-19')
time_start = None
time_end = None

## list of parameters to plot
param_list = ['Algae','DIN','TN','TN_plus_DetNS12','DetNS12','OONS12','OXY','DetCS1']

# dictionary to map parameter to element corresponding to mass
grams_of_what = {'DIN' : 'N', 
                 'TN' : 'N', 
                 'TN_plus_DetNS12' : 'N', 
                 'DetNS12' : 'N',
                 'OONS12' : 'N', 
                 'N-Algae' : 'N', 
                 'N-Diat' : 'N', 
                 'N-Green' : 'N', 
                 'N-DiatS1' : 'N',
                 'Algae' : 'C', 
                 'Diat' : 'C', 
                 'Green' : 'C', 
                 'DiatS1' : 'C',
                 'DetCS1' : 'C', 
                 'OXY' : 'O'}

# list of panels to plot (a "panel" is a bad name for a plot of a collection of groups, each group in one subplot)
panel_list = ['South_Bay_ABC','South_Bay_6Part','All_Subs_RMP']#, 'All_Subs_WB', 'South_Bay_6Part']

# list of time integration types (don't do cumulative, doesn't make sense for concentration)
tavg_list = ['Filtered','Cumulative']   # can also add 'Daily' if desired
#tavg_list = ['Daily']

# base directory for the and the output figures (in theory should be able to run on windows laptop with mounted drives or on server)
figure_base_dir = '/richmondvol1/hpcshared/open_bay/bgc/figures'

# this is a function, but it's really more like user input b/c this is where you specify the properties of the different plots
# of groups of groups that we are going to make
def panel_properties(panel):

    '''
    usage:  figure_size, nrows, ncols, group_list, group_labels, panel_label = panel_properties(panel)
    '''

    if panel == 'All_Subs_RMP':
    
        figure_size = (15, 10)
        ncols = 3
        nrows = 2
    
        group_list = ['Whole_Bay','Suisun_Bay','San_Pablo_Bay','Central_Bay_RMP','SB_RMP','LSB']
        group_labels = ['Whole Bay','Suisun Bay','San Pablo Bay','Central Bay (RMP)','South Bay (RMP)','Lower South Bay']
        panel_label = 'by Subembayment (RMP)'

    elif panel == 'All_Subs_WB':
    
        figure_size = (15, 10)
        ncols = 3
        nrows = 2
    
        group_list = ['Whole_Bay','Suisun_Bay','San_Pablo_Bay','Central_Bay_WB','SB_WB','LSB']
        group_labels = ['Whole Bay','Suisun Bay','San Pablo Bay','Central Bay (WB)','South Bay (WB)','Lower South Bay']
        panel_label = 'by Subembayment (Water Board)'
    
    elif panel == 'South_Bay_6Part':
    
        figure_size = (15, 10)
        ncols = 3
        nrows = 2
    
        # list of south bay chunks (note this could be any list of groups, doesn't have to be subembayments)
        group_list = ['SB_WB_west_shoal_north_half','SB_WB_channel_north_half','SB_WB_east_shoal_north_half',
                         'SB_WB_west_shoal_south_half','SB_WB_channel_south_half','SB_WB_east_shoal_south_half']
        group_labels = ['NW Shoal','N Channel','NE Shoal','SW Shoal','S Channel','SE Shoal']
        panel_label = 'Across South Bay'

    elif panel == 'South_Bay_ABC':
    
        figure_size = (18, 15)
        ncols = 4
        nrows = 3
    
        # list of south bay chunks (note this could be any list of groups, doesn't have to be subembayments)
        group_list = ['D','C','B','A','H','G','F','E','L','K','J','I']
        group_labels = ['D','C','B','A','H','G','F','E','L','K','J','I']
        panel_label = 'Across South Bay'

    return (figure_size, nrows, ncols, group_list, group_labels, panel_label)

# time axis formatting
major_locator = mdates.YearLocator()
minor_locator = mdates.MonthLocator(bymonth=(1,4,7,10))
major_formatter = mdates.DateFormatter('%Y')

# default color cycle
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
          'fuchsia','gold','lawngreen','aqua','lavender','navy','lightgray']


# tells you if the parameter is benthic (if it's benthic, don't include the transport plot, because it
# doesn't get transported, so everything is zero)
def is_it_benthic(param):

    if param in ['DetNS1','DetNS2','DetNS','OONS1','OONS2','OONS',
                 'DetNS12', 'OONS12','DiatS1','N-DiatS1',
                 'TotalDetNS1','TotalDetNS1','TotalDetNS','DiatS1','DetCS1']:
        is_benthic = True
    else:
        is_benthic = False

    return is_benthic

#########################################################################################
## main
#########################################################################################

# get strings with concise lists of runs and water years
run_list_str = CVPL.make_concise_runid_list_string(runid_list)

# path to figures, create if it does not exist
figure_path = os.path.join(figure_base_dir, run_list_str, 'multigroup_concentrations')
if not os.path.exists(figure_path):
    os.makedirs(figure_path)
print('\nfigures will be saved here: %s\n' % figure_path)

# loop through the sets of panels we want to plot
for panel in panel_list:

    # figure names, plot concentration only for first norm, since it doesn't follow the norm anyway
    pdffile = '%s_%s_Control_Volume_Concentrations.pdf' % (run_list_str,panel)
    
    # open pdfs
    with PdfPages(os.path.join(figure_path,pdffile)) as pdf2:

        # get some information about this grouping of panels
        figure_size, nrows, ncols, group_list, group_labels, panel_label = panel_properties(panel)
    
        # make sure number of groups matches length of group labels, and that they fit on the plot
        ngroups = len(group_list)
        assert ngroups==len(group_labels)
        assert nrows*ncols>=ngroups
    
        # loop through parameters
        for param in param_list:
        
            # loop through different time averages: daily, spring-neap filter, cumulative
            for tavg in tavg_list:
        
                # define some time-averaging period based strings for figure labeling and balance table filename
                if tavg=='Filtered':
                    tavg_str = 'Spring-Neap Filtered'
                else:
                    tavg_str = tavg
                if tavg=='Daily':
                    tavg_suff = ''
                else:
                    tavg_suff = '_' + tavg
                units = 'Mg/d'

                # get mass column
                mass_col = '%s,Mass (Mg)' % param

                # initialize figures
                fig2, ax2 = plt.subplots(nrows, ncols, figsize=figure_size)
                ax2 = ax2.flatten()
        
                # loop through the runs
                for irun, runid in enumerate(runid_list):

                    # get server and wystr
                    server = server_list[irun]
                    wystr = wystr_list[irun]
                    vol = vol_list[irun]

                    ## balance table folder
                    run_base_dir = '/%s%s/hpcshared' % (server,vol)
                    run_dir = CVPL.get_run_dir(run_base_dir, runid)
                    table_dir = os.path.join(run_dir,'Balance_Tables')

                    # load up the balance table data for the parameter of interest with the time averaging type of interest
                    input_fn = os.path.join(table_dir,'%s_Table_By_Group%s.csv' % (param.lower(), tavg_suff))
                    try:
                        data = pd.read_csv(input_fn)
                    except:
                        print('could not open %s\nit probably doesn''t exist, skipping this one' % input_fn)
                        continue
    
                    # add a column for concentration
                    if not is_it_benthic(param):
                        data['Concentration'] = data[mass_col].values / data['Volume (Mean, m^3)'].values * 1e6
                        conc_units = 'mg %s/L' % grams_of_what[param] 
                    else:
                        data['Concentration'] = data[mass_col].values / data['Area (m^2)'].values * 1e6
                        conc_units = 'g %s/m$^2$' % grams_of_what[param]
            
                    # convert times from string to datetime64
                    data['time'] = data['time'].astype('datetime64[ns]')
                    
                    # if there is a start and end time specified by the user, trim
                    # and if start time is not specified, trim early times anyway, starting on october 1 of the first year
                    if not time_start is None:
                        ind = data['time'] >= np.datetime64(time_start)
                        data = data.loc[ind]
                    else:
                        yr1 = pd.Timestamp(data['time'].iloc[0]).year
                        ind = data['time'] >= np.datetime64('%d-10-01' % yr1)
                    if not time_end is None:
                        ind = data['time'] < np.datetime64(time_end)
                        data = data.loc[ind]
            
                    # get the times
                    time = data['time'].unique()
            
                    # get the list of water years available, requiruing at least two data points in a water year
                    jan1 = pd.DatetimeIndex(np.unique(time.astype('datetime64[Y]')))
                    yr_list = [j.year for j in jan1]
                    yr_list.append(np.min(yr_list)-1)
                    yr_list.append(np.max(yr_list)+1)
                    wy_list = []
                    for yr in yr_list:
                        if np.sum(np.logical_and(time>=np.datetime64('%d-10-01' % yr), time<np.datetime64('%d-10-01' % (yr+1))))>1:
                            wy_list.append(yr+1)
            
                    # getting list of water years was all for the purpose of generating this nice string to include in the plot name
                    wy_list_str = CVPL.make_concise_water_year_list_string(wy_list)
            
                    # get first and last date for the time axis
                    wymin = np.array(wy_list).min()
                    wymax = np.array(wy_list).max()
                    tmin = np.datetime64('%d-10-01' % (wymin-1))
                    tmax = np.datetime64('%d-10-01' % wymax)
            
                    # get time
                    time = np.unique(data['time'].values)
                    ntime = len(time)
    
                    # loop through the groups
                    for igroup in range(ngroups):
                
                        # get data for group
                        group = group_list[igroup]
                        ind = data['group'] == group
                        data_group = data.loc[ind].copy(deep=True)
    
                        # find the area and volume of the group
                        area_km2 = np.mean(data_group['Area (m^2)'].values)/1000/1000
                        volume_km2xm = np.mean(data_group['Volume (Mean, m^3)'].values)/1000/1000
    
                        ###########################################
                        # work on concentration figure
                        ###########################################
                    
                        ax2[igroup].plot(time, data_group['Concentration'], label=runid)
                        # title and ylabel
                        if irun==0:
                            ax2[igroup].set_title('%s\nArea = %0.0f km$^2$\nVolume = %0.0f km$^2$ x m' % (group_labels[igroup], area_km2, volume_km2xm))
                            if np.mod(igroup, ncols)==0:
                                ax2[igroup].set_ylabel('Concentration (%s)' % conc_units)       
    
                ax2[igroup].legend() # add legend to final plot

                fig2.suptitle('%s %s Concentration %s' % (tavg_str, param, panel_label))
                
                # format axes -- everything but concentration is symmetric about y=0
                # concentration minimum is zero
                for ax in [ax2]:
                    ymax = 0
                    for iax in range(len(ax)):
                        ax0 = ax[iax]
                        if iax>=ngroups:
                            ax0.axis('off')
                        else:
                            if autoscale_x:
                                ax0.autoscale(enable=True, axis='x', tight=True)
                            else:
                                ax0.set_xlim((tmin,tmax))
                                ax0.xaxis.set_major_locator(major_locator)
                                ax0.xaxis.set_minor_locator(minor_locator)
                                ax0.xaxis.set_major_formatter(major_formatter)
                            ax0.grid(which='both')
                            ymax = np.max(np.array([ymax,np.abs(ax0.get_ylim()).max()]))
                    for ax0 in ax:
                        ax0.set_ylim((0,ymax))
                if autoscale_x:
                    for fig in [fig2]:
                        fig.autofmt_xdate()
        
                # add title and save the figure of subembayment reactions
                fig2.tight_layout(rect=[0, 0, 1, 0.98])
                pdf2.savefig(fig2)
                # close
                plt.close('all')
                    
                    

        