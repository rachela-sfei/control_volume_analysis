'''

alliek august 2022

this creates reaction stack plots for a single run across a set of "groups"
defined by the user, such as the RMP subembayments, or the sections of south bay

the results are saved in a subfolder called "reaction_stack_plots_multigroup"

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
runid = 'FR21_007'
server = 'chicago'
vol = 'vol2'
#runid = 'FR13_003'
#if 1:
#    runid = 'FR22_HAB_058'
#    server = 'chicago'
#if 1:
#    runid = 'FR13_026'
#    server = 'chicago'
#if 1:
#    runid = 'FR17_019'
#    server = 'chicago'
#if 1:
#    runid = 'FR18_007'
#    server = 'chicago'

# autoscale x axis (if you set to False, script will set min/max based on water year range)
# note: this option was added for the 2022 HAB simulations, you probably want to set it to False for everything else
autoscale_x = True

# optional start and end time (useful for comparing single water year to multiple water year runs, can set to None, otherwise
# set to date string with format like '2022-08-19')
time_start = None
time_end = None

# base directory for the output figures (in theory should be able to run on windows laptop with mounted drives or on server)
figure_base_dir = '/richmondvol1/hpcshared/open_bay/bgc/figures'

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
panel_list = ['South_Bay_ABC','All_Subs_RMP', 'All_Subs_WB', 'South_Bay_6Part']

# list of normalizations (divide by area, volume, or nothing)
norm_list = ['Area','Volume','None']

# list of time integration types
tavg_list = ['Filtered','Cumulative']   # can also add 'Daily' if desired
#tavg_list = ['Daily']

# this is a function, but it's really more like user input b/c this is where you specify the properties of the different plots
# of groups of groups that we are going to make
def panel_properties(panel):

    '''
    usage:  figure_size, nrows, ncols, group_list, group_labels, panel_label = panel_properties(panel)
    '''

    if panel == 'All_Subs_RMP':
    
        if len(wy_list)>=6:
            figure_size = (20, 10)
        else:
            figure_size = (15, 10)
        ncols = 3
        nrows = 2
    
        group_list = ['Whole_Bay','Suisun_Bay','San_Pablo_Bay','Central_Bay_RMP','SB_RMP','LSB']
        group_labels = ['Whole Bay','Suisun Bay','San Pablo Bay','Central Bay (RMP)','South Bay (RMP)','Lower South Bay']
        panel_label = 'by Subembayment (RMP)'

    elif panel == 'All_Subs_WB':
    
        if len(wy_list)>=6:
            figure_size = (20, 10)
        else:
            figure_size = (15, 10)
        ncols = 3
        nrows = 2
    
        group_list = ['Whole_Bay','Suisun_Bay','San_Pablo_Bay','Central_Bay_WB','SB_WB','LSB']
        group_labels = ['Whole Bay','Suisun Bay','San Pablo Bay','Central Bay (WB)','South Bay (WB)','Lower South Bay']
        panel_label = 'by Subembayment (Water Board)'
    
    elif panel == 'South_Bay_6Part':
    
        if len(wy_list)>=6:
            figure_size = (20, 10)
        else:
            figure_size = (15, 10)
        ncols = 3
        nrows = 2
    
        # list of south bay chunks (note this could be any list of groups, doesn't have to be subembayments)
        group_list = ['SB_WB_west_shoal_north_half','SB_WB_channel_north_half','SB_WB_east_shoal_north_half',
                         'SB_WB_west_shoal_south_half','SB_WB_channel_south_half','SB_WB_east_shoal_south_half']
        group_labels = ['NW Shoal','N Channel','NE Shoal','SW Shoal','S Channel','SE Shoal']
        panel_label = 'Across South Bay'

    elif panel == 'South_Bay_ABC':
    
        if len(wy_list)>=6:
            figure_size = (20, 10)
        else:
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

#########################################################################################
## main
#########################################################################################

# get strings with concise lists of runs and water years
run_list_str = CVPL.make_concise_runid_list_string([runid])

# path to figures, create if it does not exist
figure_path = os.path.join(figure_base_dir, run_list_str, 'multigroup_reaction_stacks')
if not os.path.exists(figure_path):
    os.makedirs(figure_path)
print('\nfigures will be saved here: %s\n' % figure_path)
            
## balance table folder
run_base_dir = '/%s%s/hpcshared' % (server,vol)
run_dir = CVPL.get_run_dir(run_base_dir, runid)
table_dir = os.path.join(run_dir,'Balance_Tables')

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
        if tavg=='Cumulative':
            units = 'Mg'
        else:
            units = 'Mg/d'

        # load up the balance table data for the parameter of interest with the time averaging type of interest
        input_fn = os.path.join(table_dir,'%s_Table_By_Group%s.csv' % (param.lower(), tavg_suff))
        try:
            data = pd.read_csv(input_fn)
        except:
            print('could not open %s\nit probably doesn''t exist, skipping this one' % input_fn)
            continue

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

        # get list of sources and sinks, with and without units (leave units off in legend, put units on y axis)
        source_list = []
        sink_list = []
        for col in data.columns:
            if not 'ZERO' in col:
                if not ',dMass/' in col:
                    if ',d' in col:
                        if data[col].mean()>0:
                            source_list.append(col)
                        elif data[col].mean()<0:
                            sink_list.append(col)
        reaction_list = []
        for rx in sink_list:
            reaction_list.append(rx)
        for rx in source_list:
            reaction_list.append(rx)
        source_list_trimmed = []
        for rx in source_list:
            source_list_trimmed.append(rx.replace(' (%s)' % units,''))
        sink_list_trimmed = []
        for rx in sink_list:
            sink_list_trimmed.append(rx.replace(' (%s)' % units,''))
        reaction_list_trimmed = []
        for rx in reaction_list:
            reaction_list_trimmed.append(rx.replace(' (%s)' % units,''))
        
        # loop through norms
        for norm in norm_list:
                    
            # normalize data by volume or area if specifiec
            if norm == 'Volume':
                norm_units = 'g %s/m$^3$/d' % grams_of_what[param]
                normval = data['Volume (Mean, m^3)'].values / 1e6
                norm_name = '_Per_Volume'
            elif norm == 'Area':
                norm_units = 'g %s/m$^2$/d' % grams_of_what[param]
                normval = data['Area (m^2)'].values /1e6
                norm_name = '_Per_Area'
            elif norm == 'None':
                norm_units = 'Mg %s/d' % grams_of_what[param]
                normval = 1
                norm_name = ''
            if tavg == 'Cumulative':
                norm_units = norm_units.replace('/d','')

            # apply the normalization to all columns except group and time
            data1 = data.copy(deep=True)
            for col in data.columns:
                if col in ['group', 'time', 'Volume (m^3)', 'Volume (Mean, m^3)', 'Area (m^2)']:
                    data1[col] = data[col].values
                else:
                    data1[col] = data[col].values / normval
            data = data1.copy(deep=True)
        
            # loop through the sets of panels we want to plot
            for panel in panel_list:
        
                # get some information about this grouping of panels
                figure_size, nrows, ncols, group_list, group_labels, panel_label = panel_properties(panel)
        
                # make sure number of groups matches length of group labels, and that they fit on the plot
                ngroups = len(group_list)
                assert ngroups==len(group_labels)
                assert nrows*ncols>=ngroups
        
                # create figure
                fig, ax = plt.subplots(nrows, ncols, figsize=figure_size)
                ax = ax.flatten()
        
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

                    # fill up dataframe with reactions
                    df = pd.DataFrame(index=time)
                    for rx in reaction_list:
                        df[rx] = data_group[rx].values
                    df.columns = reaction_list_trimmed
                
                    # get net reaction and storage
                    Net_Rx_Group = data_group['%s,Net Reaction (%s)' % (param, units)].values
                    Net_Rx_Group_Check_Sum = df.values.sum(axis=1)
                    Storage_Group = -data_group['%s,dMass/dt, Balance Check (%s)' % (param, units)].values
            
                    # add storage to the dataframe
                    df['Storage (-dM/dt)'] = Storage_Group
            
                    # divide into positive and negative values
                    df_pos = df.copy(deep=True)
                    df_neg = df.copy(deep=True)
                    df_pos[df<0] = 0
                    df_neg[df>0] = 0
                
                    # add to figure
                    ax[igroup].stackplot(time, df_pos.values.transpose(), colors = colors[0:len(df.columns)], labels=df.columns)
                    ax[igroup].stackplot(time, df_neg.values.transpose(), colors = colors[0:len(df.columns)])
                    ax[igroup].plot(time, Net_Rx_Group, 'k', label='Net Reaction')
                    #ax[igroup].plot(time, Net_Rx_Group_Check_Sum, 'm--', label='Net Reaction, Check Sum')
                    ax[igroup].plot(time, Net_Rx_Group + Storage_Group, 'b', label='Net Reaction - dM/dt')
                    ax[igroup].set_title('%s\nArea = %0.0f km$^2$\nVolume = %0.0f km$^2$ x m' % (group_labels[igroup], area_km2, volume_km2xm))
                    if np.mod(igroup, ncols)==0:
                        ax[igroup].set_ylabel('Reactions and Storage (%s)' % norm_units)

                    # add legend
                    if igroup==(ncols-1):
                        ax[igroup].legend(loc='center left',bbox_to_anchor=(1, 0.5))
        

                # format axes 
                ymax = 0
                for iax in range(len(ax)):
                    ax1 = ax[iax]
                    if iax>=ngroups:
                        ax1.axis('off')
                    else:
                        if autoscale_x:
                            ax1.autoscale(enable=True, axis='x', tight=True)
                        else:
                            ax1.set_xlim((tmin,tmax))
                            ax1.xaxis.set_major_locator(major_locator)
                            ax1.xaxis.set_minor_locator(minor_locator)
                            ax1.xaxis.set_major_formatter(major_formatter)
                        ax1.grid(which='both')
                        ymax = np.max(np.array([ymax,np.abs(ax1.get_ylim()).max()]))
                for ax1 in ax:
                    ax1.set_ylim((-ymax,ymax))
                if autoscale_x:
                    fig.autofmt_xdate()
        
                # add title and save the figure of subembayment reactions
                fig.suptitle('%s %s Reactions %s\n%s' % (tavg_str, param, panel_label,runid))
                fig.tight_layout(rect=[0, 0, 1, 0.98])
                fig.savefig(os.path.join(figure_path, '%s_%s_Rx_Stacks_%s%s_%s_%s.png' % (run_list_str, wy_list_str, tavg, norm_name, panel, param)),dpi=300)
        
                # close figures
                plt.close('all')
            
        