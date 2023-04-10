
"""
alliek prep for 2020 NTW meeting March 11
"""


import copy
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib as mpl
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import numpy as np
import os, sys
import pandas as pd
import cmocean 
import geopandas as gpd
if not 'DISPLAY' in os.environ:
    import matplotlib
    mpl.use('agg')
    plt.switch_backend('Agg')
from importlib import reload
import control_volume_plotting_library as CVPL # plotting library must be in same folder as this script
reload(CVPL)

#############################
# user input
#############################

# list of run id's and corresponding water years -- these lists should be the same length
# and each item in the list will correspond to a column in the figure
runid_list = ['G141_13to18_246','FR13_003','G141_13to18_246','FR17_003']
wy_list = [2013, 2013, 2017, 2017]

# list of time averaging periods (choices are 'Annual','Seasonal','Monthly')
# each time step within a given water year will be a row in the figures
#time_period_list = ['Annual','Seasonal','Monthly']
time_period_list = ['Seasonal']

# list of "groups" corresponding to subembayments (these are their names in the balance tables), 
# each "group" corresponds to one set of sourc/sink bars in each subplot of the figure
group_list = ['LSB', 'SB_RMP', 'Central_Bay_RMP', 'San_Pablo_Bay', 'Suisun_Bay', 'Whole_Bay']  # can add 'Whole_Bay' 

# list of bar plot labels corresponding to these groups (must be same length)
group_labels = ['Lower\nSouth\nBay', 'South\nBay\n(RMP)', 'Central\nBay\n(RMP)', 'San\nPablo\nBay', 'Suisun\nBay', 'Whole\nBay']

# list of parameters to plot (this is for batch processing, they appear in separate figures)
param_list = ['DIN','TN','TN_include_sediment','TotalDetNS','OXY','Algae']

# list of norms to use (this is for batch processing, they appear in separate figures)
norm_list = ['Area','Volume','None']

# base directory for the output figures (in theory should be able to run on windows laptop with mounted drives or on server)
#base_dir = r'X:\hpcshared'
figure_base_dir = '/richmondvol1/hpcshared/open_bay/bgc/figures'

# figure size scales with number of subplots
subplot_width = 5
subplot_height = 3

# start with the default color cycle and add even more colors because the number of reactions is OUT OF CONTROL!
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
          'fuchsia','gold','lawngreen','aqua','lavender','navy','lightgray','salmon','b','darkturquoise','darkkhaki','rosybrown','k']

##########################
# main
##########################

# do some checks to make sure user input makes sense
nruns = len(runid_list)
assert nruns == len(wy_list)
ngroups = len(group_list)
assert ngroups == len(group_labels)

# get strings with concise lists of runs and water years
run_list_str = CVPL.make_concise_runid_list_string(runid_list)
wy_list_str = CVPL.make_concise_water_year_list_string(wy_list)

# path to figures, create if it does not exist
figure_path = os.path.join(figure_base_dir, run_list_str, 'subembayment_reaction_bars')
if not os.path.exists(figure_path):
    os.makedirs(figure_path)
print('\nfigures will be saved here: %s\n' % figure_path)

# parameter to plot
for param in param_list:

    # loop through averaging time periods (Annual, Seasonal, Monthly)
    for time_period in time_period_list:

        # balance table name is the same across all the runs, just located in different directories
        balance_table_fn = '%s_Table_By_Group_%s.csv' % (param.lower(), time_period)

        # before we plot the different runs, take a sneak peek to find a list of all the reactions, across all the runs
        source_list = []
        sink_list = []
        for irun in range(nruns):

            # get the run id
            runid = runid_list[irun]
    
            # get path to the balance table folder in the run folder
            run_base_dir = '/%svol1/hpcshared' % server_list[irun]
            run_dir = CVPL.get_run_dir(run_base_dir, runid)
            balance_table_dir = os.path.join(run_dir,'Balance_Tables')
            
            # load up the balance table data for the parameter of interest
            input_fn = os.path.join(balance_table_dir,balance_table_fn)
            try:
                data = pd.read_csv(input_fn)
            except:
                print('could not open %s\nit probably doesn''t exist, skipping this one' % input_fn)
                continue

            # get the reaction lists
            source_list_1 = []
            sink_list_1 = []
            for col in data.columns:
                if not 'ZERO' in col:
                    if not ',dMass/' in col:
                        if ',d' in col:
                            if data[col].mean()>0:
                                source_list_1.append(col)
                            elif data[col].mean()<0:
                                sink_list_1.append(col)

            # add to master list
            for rx in source_list_1:
                if not rx in source_list:
                    source_list.append(rx)
            for rx in sink_list_1:
                if not rx in sink_list:
                    sink_list.append(rx)


        # sometimes a term may be a source or a sink, such as oxygen reaeration...
        # in this case our algorithim might have flagged it as a source in one run and 
        # a sink in the other (depending if the average was positive or negative) ... go through
        # the source terms and make sure none of them appear as sinks as well
        # search for any such terms and delete them from the sink list
        for source in source_list:
            if source in sink_list:
                sink_list.remove(source)

        # count sources and sinks
        nsource = len(source_list)
        nsink = len(sink_list)

        # trim the units for concise legend
        source_list_trimmed = []
        for rx in source_list:
            source_list_trimmed.append(rx.replace(' (Mg/d)',''))
        # trim the units for concise legend
        sink_list_trimmed = []
        for rx in sink_list:
            sink_list_trimmed.append(rx.replace(' (Mg/d)',''))

        # loop through the norms
        for norm in norm_list:

            # string for indicating norm in figure names
            if norm == 'None':
                norm_name = ''
                norm_label = ''
            elif norm == 'Area':
                norm_name = '_Per_Area'
                norm_label = ' per Area'
            elif norm == 'Volume':
                norm_name = '_Per_Volume'
                norm_label = ' per Volume'

            # initialize tracker for tallest y axis
            ymax = 0

            # now loop through the runs for real 
            for irun in range(nruns):
    
                # get the run id and water year
                runid = runid_list[irun]
                wy = wy_list[irun]
        
                # get path to the balance table folder in the run folder
                run_base_dir = '/%svol1/hpcshared' % server_list[irun]
                run_dir = CVPL.get_run_dir(run_base_dir, runid)
                balance_table_dir = os.path.join(run_dir,'Balance_Tables')
    
                # read balance table
                df = pd.read_csv(os.path.join(balance_table_dir, balance_table_fn))
                df['time'] = pd.to_datetime(df['time'])
    
                # isolate the water year
                ind = np.logical_and(df['time'].values >= np.datetime64('%d-10-01' % (wy-1)), 
                                     df['time'].values <  np.datetime64('%d-10-01' % wy))
                df = df.loc[ind]

                # get the unique times
                time = np.unique(df.time.values)
                ntime = len(time)

                # if this is the first run, initialize the figure and name it, also decide which row to put the legend
                if irun==0:
                    fig, ax = plt.subplots(nrows=ntime, ncols=nruns, figsize=((nruns+0.5)*subplot_width, ntime*subplot_height))
                    figure_fn = '%s_%s_reaction_bars_%s%s_%s.png' % (run_list_str, wy_list_str, time_period, norm_name, param)
                    row_leg = int(np.floor((ntime-1)/2))

                # now loop through the time steps and fill up this column of the figure
                for itime in range(len(time)):

                    # initialize data matrices for sources and sinks
                    data_sources  = np.zeros((nsource, ngroups))
                    data_sinks = np.zeros((nsink, ngroups))
                    
                    # set up an x axis for plotting the different color bars and compute the widths of the bars based on how many there are, also offset
                    nbars=2
                    X = np.arange(ngroups)
                    W = 1/(nbars + 1)
                    O = (1-nbars)*W/2 
                        
                    # get the data for this time step 
                    indt = df['time'].values == time[itime]
                    df_now = df.loc[indt]
                    
                    # loop through the group
                    for igroup in range(ngroups):
                    
                        # get the data for this group
                        df_group = df_now.loc[df_now['group'] == group_list[igroup]].iloc[0]
                    
                        # get the value we need to normalize by
                        if norm=='None':
                            normval = 1
                            units = 'Mg/d'
                        elif norm=='Area':
                            normval = df_group['Area (m^2)'] / 1e6
                            units = 'g/m$^2$/d'
                        elif norm=='Volume':
                            normval = df_group['Volume (m^3)'] / 1e6
                            units = 'mg/L/d'
                    
                        # load up the source and sink matrices
                        for i in range(nsource):
                            if source_list[i] in df_group.keys():
                                data_sources[i, igroup] = df_group[source_list[i]] / normval
                        for i in range(nsink):
                            if sink_list[i] in df_group.keys():
                                data_sinks[i, igroup] = df_group[sink_list[i]] / normval

                    # get the axis handle for plotting (axis may be 1d or 2d depending on ntime, nruns)
                    if nruns==1 and ntime==1:
                        ax1 = ax
                    elif nruns==1:
                        ax1 = ax[itime]
                    elif ntime==1:
                        ax1 = ax[irun]
                    else:
                        ax1 = ax[itime, irun]

                    # initialize color counter
                    color_counter = -1

                    # add sources to plot
                    if nsource>0:
                        i = 0
                        color_counter += 1
                        ax1.bar(X + 0*W + O, data_sources[i,:], W, label=source_list_trimmed[i], color=colors[color_counter])
                        bottom = data_sources[i,:]
                        for i in range(1,nsource):
                            color_counter += 1
                            ax1.bar(X + 0*W + O, data_sources[i,:], W, bottom=bottom, label=source_list_trimmed[i], color=colors[color_counter])
                            bottom = bottom + data_sources[i,:]
                    
                    # add sinks to plot
                    if nsink>0:
                        i = 0
                        color_counter += 1
                        ax1.bar(X + 1*W + O, -data_sinks[i,:], W, label=sink_list_trimmed[i], color=colors[color_counter])
                        bottom = -data_sinks[i,:]
                        for i in range(1,nsink):
                            color_counter += 1
                            ax1.bar(X + 1*W + O, -data_sinks[i,:], W, bottom=bottom, label=sink_list_trimmed[i], color=colors[color_counter])
                            bottom = bottom - data_sinks[i,:]

                    # keep track of the tallest y axis
                    ymax = np.max([ymax, ax1.get_ylim()[1]])
                    
                    # add horizontal grid lines 
                    ax1.yaxis.grid()
                    
                    # reset the x tick labels
                    ax1.set_xticks(X)
                    if itime==(ntime-1):
                        ax1.set_xticklabels(group_labels)
                    else:
                        ax1.set_xticklabels([''] * ngroups)
                    
                    # label the y axes
                    if irun==0:
                        ax1.set_ylabel('Reaction Rate (%s)' % units)

                    # set the title, always include time period, add run name in first row
                    if itime==0:
                        title_str = runid + '\n'
                    else:
                        title_str = ''
                    title_str += df_group['Time Period']
                    ax1.set_title(title_str)

                    # add the legend
                    if itime==row_leg and irun==(nruns-1):
                        ax1.legend(bbox_to_anchor=(1, 0.5), loc='center left')

            # set all the y axis limits to same range
            for ax1 in ax.flatten():
                ax1.set_ylim((0,1.05*ymax))
                    
            # add suptitle, tight layout, save
            fig.suptitle('%s Reaction Sources and Sinks%s' % (param, norm_label))
            fig.tight_layout(rect=[0, 0., 1, 0.98])
            fig.savefig(os.path.join(figure_path,figure_fn))
            
            plt.close('all')                        