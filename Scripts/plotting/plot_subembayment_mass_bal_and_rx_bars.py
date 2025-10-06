
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
    mpl.use('agg')
    plt.switch_backend('Agg')
from importlib import reload
import control_volume_plotting_library as CVPL # plotting library must be in same folder as this script
reload(CVPL)

#############################
# user input
#############################

# group the reactions for ease of reading the bar chart? see group_reactions function defined below 
# to see or edit how they are grouped
group_reactions_flag = True

# same y axis for transport? (if false, will still make them the same for matching water years, for comparison of agg and fr runs)
same_trans_axis = True

# same y axis limits for reactions? (if false, will still make them the same for matching water years, for comparison of agg and fr runs)
same_rx_axis = True

# same y axis for BOTH reactions and transport? (if false, will still apply axis flags above and water year matching)
same_trans_AND_rx_axis = True

# to address problem that in wy2016 and wy2017 the transport in suisun bay and other embayments is out of control
# create a second set of plots that are zoomed in so those are off the chart, here set the number of plots to cut 
# off
# ncut_plots = 8
ncut_plots = 0

# list of run id's and corresponding water years -- these lists should be the same length
# and each item in the list will correspond to a column in the figure
#runid_list = ['G141_13to18_246','FR13_003','G141_13to18_246','FR17_003']
#wy_list = [2013, 2013, 2017, 2017]

# runid_list = ['FR13_028', 'FR14_001', 'FR15_001', 'FR16_001','FR17_021','FR18_009']
# wy_list = [2013,2014,2015,2016,2017,2018]
# server_list = ['chicago','boise','boise','boise','chicago','chicago']

runid_list = ['FR13_028', 'FR14_001', 'FR15_001', 'FR16_001','FR17_021','FR18_009']
wy_list = [2013,2014,2015,2016,2017,2018]
server_list = ['chicago','boise','boise','boise','chicago','chicago']
vol_list = ['vol1','vol1','vol1','vol1','vol1','vol1']
all_time_together = False


# list of time averaging periods (choices are 'Annual','Seasonal','Monthly')
# each time step within a given water year will be a row in the figures
#time_period_list = ['Annual','Seasonal','Monthly']
time_period_list = ['Seasonal']


# list of "groups" corresponding to subembayments (these are their names in the balance tables), 
# each "group" corresponds to one set of sourc/sink bars in each subplot of the figure
group_list_1 = ['LSB', 'SB_RMP', 'SB_WB_north_half', 'Central_Bay_WB', 'San_Pablo_Bay', 'Suisun_Bay', 'Whole_Bay']   

# list of bar plot labels corresponding to these groups (must be same length)
group_labels_1 = ['Lower\nSouth\nBay', 
                'South\nBay\n(RMP)', 
                'South\nBay\n(WB,N.\nhalf)', 
                'Central\nBay\n(WB)', 
                'San\nPablo\nBay', 
                'Suisun\nBay', 
                'Whole\nBay']

# list of parameters to plot (this is for batch processing, they appear in separate figures)
param_list = ['DIN','TN','TN_plus_DetNS12','TN_include_sediment','DetNS12','OONS12']

# list of norms to use (this is for batch processing, they appear in separate figures)
norm_list = ['Area','None']

# base directory for the output figures (in theory should be able to run on windows laptop with mounted drives or on server)
#base_dir = r'X:\hpcshared'
figure_base_dir = '/richmondvol1/hpcshared/open_bay/bgc/figures'

# figure size scales with number of subplots
subplot_width = 4
subplot_height = 4.5

# bar zorder
bzorder = 20

# start with the default color cycle and add even more colors because the number of reactions is OUT OF CONTROL!
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
          'fuchsia','gold','lawngreen','aqua','lavender','navy','lightgray','salmon','skyblue','darkturquoise','darkkhaki','rosybrown']


# list of directions the subembayment influx comes from, by group name key
# each connection in the list is itself a tuple with the following 3 entries:
# (group name, direction flux comes INTO the group from, multiplier to turn flux in into an influx to the group key CV)
# note if the group name is the same as the group key, the multiplier should be 1, and if it is an adjacent group, it should be -1
# NOTE SAN PABLO BAY INFLUX IS DIFFERENT FOR AGG GRID, SO SET THIS INSIDE THE FOR LOOP LATER ON, MAKING IT POSSIBLE TO COMPARE FULL RES AND AGG RUNS
influx_dir_dict = {}
influx_dir_dict['LSB'] = []
influx_dir_dict['SB_RMP'] = [('SB_RMP','S',1)]
influx_dir_dict['SB_WB'] = [('SB_WB','S',1)]
influx_dir_dict['SB_WB_north_half'] = [('SB_WB_north_half','S',1)]
influx_dir_dict['Central_Bay_RMP'] = [('Central_Bay_RMP','S',1),('Central_Bay_RMP','N',1)]
influx_dir_dict['Central_Bay_WB'] = [('Central_Bay_WB','S',1),('Central_Bay_WB','N',1)]
influx_dir_dict['Suisun_Bay'] = [('Suisun_Bay','E',1),('Suisun_Bay','N',1)]
influx_dir_dict['Whole_Bay'] = [('Whole_Bay','E',1),('Whole_Bay','N',1)]
influx_dir_dict['San_Pablo_Bay_FR'] = [('San_Pablo_Bay','E',1),('Sonoma','S',-1),('Petaluma','S',-1),('Napa','S',-1)]
influx_dir_dict['San_Pablo_Bay_AGG'] = [('San_Pablo_Bay','E',1),('Napa','S',-1)]

# list of directions the outflux goes to, by group name key
# each connection in the list is itself a tuple with the following 3 entries:
# (group name, direction flux comes INTO the group from, multiplier to turn flux in into an outflux)
# note if the group name is the same as the group key, the multiplier should be -1, and if it is an adjacent group, it should be 1
outflux_dir_dict = {}
outflux_dir_dict['LSB'] = [('LSB','N',-1)]
outflux_dir_dict['SB_RMP'] = [('SB_RMP','N',-1)]
outflux_dir_dict['SB_WB'] = [('SB_WB','N',-1)]
outflux_dir_dict['SB_WB_north_half'] = [('SB_WB_north_half','N',-1)]
outflux_dir_dict['Central_Bay_RMP'] = [('Central_Bay_RMP','W',-1)]
outflux_dir_dict['Central_Bay_WB'] = [('Central_Bay_WB','W',-1)]
outflux_dir_dict['San_Pablo_Bay'] = [('San_Pablo_Bay','S',-1)]
outflux_dir_dict['Suisun_Bay'] = [('Suisun_Bay','W',-1)]
outflux_dir_dict['Whole_Bay'] = [('Whole_Bay','W',-1)]


##########################
# functions
##########################

# returns a dictionary with reactions to group
def group_reactions(param):

    if param=='DIN':

        group_rx = {'DIN,dDINUpt (Mg/d)' : 'DIN,dDINUpt + DIN,dDINUptS1 (Mg/d)',  
                    'DIN,dDINUptS1 (Mg/d)' : 'DIN,dDINUpt + DIN,dDINUptS1 (Mg/d)',
                    'NH4,dMinPON1 (Mg/d)' : 'NH4,dMinPON1 + NH4,dMinPON2\n+ NH4,dMinDON + NH4,dZ_NRes\n+ NH4,dNH4Aut + NH4,dNH4AUTS1 (Mg/d)',
                    'NH4,dMinPON2 (Mg/d)' : 'NH4,dMinPON1 + NH4,dMinPON2\n+ NH4,dMinDON + NH4,dZ_NRes\n+ NH4,dNH4Aut + NH4,dNH4AUTS1 (Mg/d)', 
                    'NH4,dMinDON (Mg/d)' : 'NH4,dMinPON1 + NH4,dMinPON2\n+ NH4,dMinDON + NH4,dZ_NRes\n+ NH4,dNH4Aut + NH4,dNH4AUTS1 (Mg/d)', 
                    'NH4,dZ_NRes (Mg/d)' : 'NH4,dMinPON1 + NH4,dMinPON2\n+ NH4,dMinDON + NH4,dZ_NRes\n+ NH4,dNH4Aut + NH4,dNH4AUTS1 (Mg/d)',
                    'NH4,dNH4Aut (Mg/d)' : 'NH4,dMinPON1 + NH4,dMinPON2\n+ NH4,dMinDON + NH4,dZ_NRes\n+ NH4,dNH4Aut + NH4,dNH4AUTS1 (Mg/d)', 
                    'NH4,dNH4AUTS1 (Mg/d)' : 'NH4,dMinPON1 + NH4,dMinPON2\n+ NH4,dMinDON + NH4,dZ_NRes\n+ NH4,dNH4Aut + NH4,dNH4AUTS1 (Mg/d)'}

    else:

        group_rx = {}

    return group_rx


# tells you if the parameter is benthic (if it's benthic, don't include the transport plot, because it
# doesn't get transported, so everything is zero)
def is_there_loading(param):

    if param in ['Algae','Green','Diat','DiatS1',
                 'OXY', 
                 'DetNS1','DetNS2','DetNS','OONS1','OONS2','OONS',
                 'TotalDetNS1','TotalDetNS1','TotalDetNS']:
        has_loading = False
    else:
        has_loading = True

    return has_loading

    
# divide array into positive and negative entries
def pos_neg(data):
    pos = np.zeros(np.shape(data))
    neg = np.zeros(np.shape(data))
    ind = data>0
    pos[ind] = data.copy()[ind]
    ind = data<0
    neg[ind] = data.copy()[ind]
    return pos, neg

##########################
# main
##########################

# do some checks to make sure user input makes sense
nruns = len(runid_list)
assert nruns == len(wy_list)
ngroups = len(group_list_1)
assert ngroups == len(group_labels_1)

# get strings with concise lists of runs and water years
run_list_str = CVPL.make_concise_runid_list_string(runid_list)
wy_list_str = CVPL.make_concise_water_year_list_string(wy_list)

# path to figures, create if it does not exist
figure_path = os.path.join(figure_base_dir, run_list_str, 'subembayment_mass_bal_and_rx_bars')
if not os.path.exists(figure_path):
    os.makedirs(figure_path)
print('\nfigures will be saved here: %s\n' % figure_path)

# parameter to plot
for param in param_list:
    print(param)

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
            run_base_dir = '/%s%s/hpcshared' % (server_list[irun],vol_list[irun])
            run_dir = CVPL.get_run_dir(run_base_dir, runid)
            balance_table_dir = os.path.join(run_dir,'Balance_Tables')
            
            # load up the balance table data for the parameter of interest
            input_fn = os.path.join(balance_table_dir,balance_table_fn)
            try:
                data = pd.read_csv(input_fn)
            except:
                print('could not open %s\nit probably doesn''t exist, skipping this one' % input_fn)
                continue

            # group reactions as specified
            if group_reactions_flag:
                group_rx = group_reactions(param)
                for rx in group_rx.keys():
                    if not group_rx[rx] in data.columns:
                        data[group_rx[rx]] = data[rx]
                    else:
                        data[group_rx[rx]] += data[rx]
                    data.drop(columns=[rx],inplace=True)

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
            # also, if no norm, eliminate the whole bay group from group list
            if norm == 'None':
                norm_name = ''
                norm_label = ''
                ind = ~(np.array(group_list_1)=='Whole_Bay')
                group_list = np.array(group_list_1)[ind]
                group_labels = np.array(group_labels_1)[ind]
            elif norm == 'Area':
                norm_name = '_Per_Area'
                norm_label = ' per Area'
                group_list = group_list_1
                group_labels = group_labels_1
            elif norm == 'Volume':
                norm_name = '_Per_Volume'
                norm_label = ' per Volume'
                group_list = group_list_1
                group_labels = group_labels_1
            ngroups = len(group_list)

            # now loop through the runs for real 
            for irun in range(nruns):
    
                # get the run id and water year
                runid = runid_list[irun]
                wy = wy_list[irun]

                # get path to the balance table folder in the run folder
                run_base_dir = '/%s%s/hpcshared' % (server_list[irun], vol_list[irun])
                run_dir = CVPL.get_run_dir(run_base_dir, runid)
                balance_table_dir = os.path.join(run_dir,'Balance_Tables')
    
                # read balance table
                df = pd.read_csv(os.path.join(balance_table_dir, balance_table_fn))
                df['time'] = pd.to_datetime(df['time'])

                # group reactions as specified
                if group_reactions_flag:
                    group_rx = group_reactions(param)
                    for rx in group_rx.keys():
                        if not group_rx[rx] in df.columns:
                            df[group_rx[rx]] = df[rx]
                        else:
                            df[group_rx[rx]] += df[rx]
                        df.drop(columns=[rx],inplace=True)
    
                # isolate the water year
                ind = np.logical_and(df['time'].values >= np.datetime64('%d-10-01' % (wy-1)), 
                                     df['time'].values <  np.datetime64('%d-10-01' % wy))
                df = df.loc[ind]

                # get the unique times
                time = np.unique(df.time.values)
                ntime = len(time)

                ### SAN PABLO BAY INFLUX COMPONENTS ARE DIFFERENT FOR AGG AND FULL RES RUNS SO SET THEM HERE
                if 'FR' in runid:
                    influx_dir_dict['San_Pablo_Bay'] = influx_dir_dict['San_Pablo_Bay_FR']
                else:
                    influx_dir_dict['San_Pablo_Bay'] = influx_dir_dict['San_Pablo_Bay_AGG']

                # if this is the first run, initialize the figure and name it, also decide which row to put the legend
                if irun==0:
                    fig, ax = plt.subplots(nrows=ntime, ncols=nruns, figsize=((nruns+1.5)*subplot_width, ntime*subplot_height))
                    figure_fn = '%s_%s_mass_bal_and_rx_bars_%s%s_%s.png' % (run_list_str, wy_list_str, time_period, norm_name, param)
                    figure_zoom_fn = '%s_%s_mass_bal_and_rx_bars_ZOOM_%s%s_%s.png' % (run_list_str, wy_list_str, time_period, norm_name, param)

                    # make a second axis for the reactions
                    if not same_trans_AND_rx_axis:
                        ax_twin = ax.copy()
                        if ntime==1 or nruns==1:
                            for i in range(len(ax_twin)):
                                ax_twin[i] = ax[i].twinx()
                        else:
                            for itime1 in range(ntime):
                                for irun1 in range(nruns):
                                    ax_twin[itime1, irun1] = ax[itime1, irun1].twinx()
                    else:
                        ax_twin = ax

                # now loop through the time steps and fill up this column of the figure
                for itime in range(len(time)):

                    # initialize data matrices for sources and sinks
                    data_sources  = np.zeros((nsource, ngroups))
                    data_sinks = np.zeros((nsink, ngroups))
                    
                    # initialize data matrices for mass balance terms
                    data_influx  = np.zeros(ngroups)
                    data_outflux = np.zeros(ngroups)
                    data_rx      = np.zeros(ngroups)
                    data_load    = np.zeros(ngroups)
                    data_storage = np.zeros(ngroups)
                    data_minortribs = np.zeros(ngroups)

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


                        # put the loads and rxes and storage in the data arrays
                        data_load[igroup] = df_group['%s,Net Load (Mg/d)' % param] / normval
                        data_rx[igroup] = df_group['%s,Net Reaction (Mg/d)' % param] / normval
                        data_storage[igroup] = df_group['%s,dMass/dt, Balance Check (Mg/d)' % param] / normval

                        # add up the influxes using dictionary that gives list of connections that are influxes for this group
                        for influx in influx_dir_dict[group_list[igroup]]:
                            
                            # each influx is a tuple giving the group, the side, and the mutliplier 
                            influx_group, influx_dir, influx_mult = influx
                
                            # get the data for the influx group
                            df_influx = df_now.loc[df_now['group'] == influx_group]
                
                            # add the influx, mutliplying by the multiplier to get the direction right
                            data_influx[igroup] = data_influx[igroup] + influx_mult * df_influx['%s,Flux In from %s (Mg/d)' % (param, influx_dir)] / normval
                
                        # add up the outfluxed using dictionary that gives list of connections that are outfluxes for this group
                        for outflux in outflux_dir_dict[group_list[igroup]]:
                
                            # each influx is a tuple giving the group, the side, and the mutliplier 
                            outflux_group, outflux_dir, outflux_mult = outflux
                
                            # get the data for the influx group
                            df_outflux = df_now.loc[df_now['group'] == outflux_group]
                
                            # add the influx, mutliplying by the multiplier to get the direction right
                            data_outflux[igroup] = data_outflux[igroup] + outflux_mult * df_outflux['%s,Flux In from %s (Mg/d)' % (param, outflux_dir)] / normval

                        # compute minor tributary inputs 
                        data_minortribs[igroup] = df_group['%s,Net Transport In (Mg/d)' % param] / normval - data_influx[igroup] + data_outflux[igroup]

                    # calculate closure error by finding what storage would need to be to close the equation
                    data_storage_1 = data_load + data_influx + data_minortribs + data_rx - data_outflux
                    data_closure = data_storage_1 - data_storage
    
                    # flip the sign of outflux and storage because they are on the RHS of the equation
                    data_storage = - data_storage.copy()
                    data_outflux = - data_outflux.copy()
                    data_closure = - data_closure.copy()

                    # divide mass balance terms into positive and negative
                    pos_influx , neg_influx  = pos_neg(data_influx )
                    pos_outflux, neg_outflux = pos_neg(data_outflux)
                    pos_minortribs, neg_minortribs = pos_neg(data_minortribs)
                    pos_rx     , neg_rx      = pos_neg(data_rx     )
                    pos_load   , neg_load    = pos_neg(data_load   )
                    pos_storage, neg_storage = pos_neg(data_storage)
                    pos_closure, neg_closure = pos_neg(data_closure)

                    # get the axis handle for plotting (axis may be 1d or 2d depending on ntime, nruns)
                    if nruns==1 and ntime==1:
                        ax1 = ax
                        ax2 = ax_twin
                    elif nruns==1:
                        ax1 = ax[itime]
                        ax2 = ax_twin[itime]
                    elif ntime==1:
                        ax1 = ax[irun]
                        ax2 = ax_twin[irun]
                    else:
                        ax1 = ax[itime, irun]
                        ax2 = ax_twin[itime, irun]

                    # initialize color counter
                    icolor = -1

                    # intialize trackers for bottom position of stacked bars
                    pos_bottom = np.zeros(ngroups)
                    neg_bottom = np.zeros(ngroups)

                    # add net rx to plot
                    icolor = icolor + 1
                    ax1.bar(X + 0*W + O, pos_rx, W, bottom=pos_bottom, color=colors[icolor], label='Net Reaction', zorder=bzorder)
                    pos_bottom = pos_bottom + pos_rx
                    ax1.bar(X + 0*W + O, neg_rx, W, bottom=neg_bottom, color=colors[icolor], zorder=bzorder)
                    neg_bottom = neg_bottom + neg_rx

                    # add storage to plot
                    icolor = icolor + 1
                    ax1.bar(X + 0*W + O, pos_storage, W, bottom=pos_bottom, color=colors[icolor], label='Storage (dM/dt) x -1', zorder=bzorder)
                    pos_bottom = pos_bottom + pos_storage
                    ax1.bar(X + 0*W + O, neg_storage, W, bottom=neg_bottom, color=colors[icolor], zorder=bzorder)
                    neg_bottom = neg_bottom + neg_storage

                    # add loading
                    if is_there_loading(param):
                        icolor = icolor + 1
                        ax1.bar(X + 0*W + O, pos_load, W, bottom=pos_bottom, color=colors[icolor], label='Loading (Point Sources)', zorder=bzorder)
                        pos_bottom = pos_bottom + pos_load
                        ax1.bar(X + 0*W + O, neg_load, W, bottom=neg_bottom, color=colors[icolor], zorder=bzorder)
                        neg_bottom = neg_bottom + neg_load

                    # add influx
                    icolor = icolor + 1
                    ax1.bar(X + 0*W + O, pos_influx, W, bottom=pos_bottom, color=colors[icolor], label='Influx', zorder=bzorder)
                    pos_bottom = pos_bottom + pos_influx
                    ax1.bar(X + 0*W + O, neg_influx, W, bottom=neg_bottom, color=colors[icolor], zorder=bzorder)
                    neg_bottom = neg_bottom + neg_influx

                    # add minor trib influx
                    icolor = icolor + 1
                    ax1.bar(X + 0*W + O, pos_minortribs, W, bottom=pos_bottom, color=colors[icolor], label='Minor Trib', zorder=bzorder)
                    pos_bottom = pos_bottom + pos_minortribs
                    ax1.bar(X + 0*W + O, neg_minortribs, W, bottom=neg_bottom, color=colors[icolor], zorder=bzorder)
                    neg_bottom = neg_bottom + neg_minortribs

                    # add outflux
                    icolor = icolor + 1
                    ax1.bar(X + 0*W + O, pos_outflux, W, bottom=pos_bottom, color=colors[icolor], label='Outflux', zorder=bzorder)
                    pos_bottom = pos_bottom + pos_outflux
                    ax1.bar(X + 0*W + O, neg_outflux, W, bottom=neg_bottom, color=colors[icolor], zorder=bzorder)
                    neg_bottom = neg_bottom + neg_outflux

                    # add closure error
                    icolor = icolor + 1
                    ax1.bar(X + 0*W + O, pos_closure, W, bottom=pos_bottom, color=colors[icolor], label='Closure Error', zorder=bzorder)
                    pos_bottom = pos_bottom + pos_closure
                    ax1.bar(X + 0*W + O, neg_closure, W, bottom=neg_bottom, color=colors[icolor], zorder=bzorder)
                    neg_bottom = neg_bottom + neg_closure

                    # add sources to plot (plus -1 x net reaction)
                    if nsource>0:
                        i = 0
                        icolor += 1
                        ax2.bar(X + 1*W + O, data_sources[i,:], W, label=source_list_trimmed[i], color=colors[icolor], zorder=bzorder)
                        bottom = data_sources[i,:]
                        for i in range(1,nsource):
                            icolor += 1
                            ax2.bar(X + 1*W + O, data_sources[i,:], W, bottom=bottom, label=source_list_trimmed[i], color=colors[icolor], zorder=bzorder)
                            bottom = bottom + data_sources[i,:]
                        ax2.bar(X + 1*W + O, -neg_rx, W, bottom=bottom, color=colors[0], zorder=bzorder)

                    # add sinks to plot
                    if nsink>0:
                        i = 0
                        icolor += 1
                        ax2.bar(X + 1*W + O, data_sinks[i,:], W, label=sink_list_trimmed[i], color=colors[icolor], zorder=bzorder)
                        bottom = data_sinks[i,:]
                        for i in range(1,nsink):
                            icolor += 1
                            ax2.bar(X + 1*W + O, data_sinks[i,:], W, bottom=bottom, label=sink_list_trimmed[i], color=colors[icolor], zorder=bzorder)
                            bottom = bottom + data_sinks[i,:]
                        ax2.bar(X + 1*W + O, -pos_rx, W, bottom=bottom, label='-1 x Net Reaction', color=colors[0], zorder=bzorder)
                    
                    # reset the x tick labels
                    ax1.set_xticks(X)
                    ax2.set_xticks(X)
                    if itime==(ntime-1):
                        ax1.set_xticklabels(group_labels)
                    else:
                        ax1.set_xticklabels([''] * ngroups)
                    
                    # label the y axes
                    if irun==0:
                        ax1.set_ylabel('Mass Balance Rates (%s)' % units)
                    if not same_trans_AND_rx_axis:
                        if irun==(nruns-1):
                            ax2.set_ylabel('Reaction Rates (%s)' % units)

                    # set the title, always include time period, add run name in first row
                    if itime==0:
                        title_str = runid + '\n'
                    else:
                        title_str = ''
                    title_str += df_group['Time Period']
                    ax1.set_title(title_str)

                    # add the legend
                    if itime==0:
                        if irun==0:
                            ax1.legend(bbox_to_anchor=(-0.25, 1), loc='upper right')
                        if irun==(nruns-1):
                            if nsource + nsink > 10:
                                ncol = 2
                            else:
                                ncol = 1
                            ax2.legend(bbox_to_anchor=(1.25, 1), loc='upper left', ncol=ncol)

                    # add a horizontal line at zero
                    ax1.axhline(0, linestyle='-', color='k',linewidth=0.5, zorder=0.5) # horizontal line at zero only

            # add suptitle, tight layout
            fig.suptitle('%s Reactions (left axis) and Mass Balance (right axis) %s' % (param, norm_label))
            fig.tight_layout(rect=[0, 0., 1, 0.98])
            
            # if these flags are set, make all axes the same regardless of water year
            if same_trans_AND_rx_axis: 
                ymax_all = []
                for ax1, ax2 in zip(ax.flatten(),ax_twin.flatten()):
                     ymax_all.append(np.max([np.abs(ax1.get_ylim()[0]),np.abs(ax1.get_ylim()[1]),np.abs(ax2.get_ylim()[0]),np.abs(ax2.get_ylim()[1])]))
                ymax_all.sort()

                # first make plots that show full scale
                ymax1 = ymax_all[-1]
                for ax1 in ax.flatten():
                    ax1.set_ylim((-1.05*ymax1, 1.05*ymax1))
                    ax1.grid(axis='y')
                for ax1 in ax_twin.flatten():
                    ax1.set_ylim((-1.05*ymax1, 1.05*ymax1))
                fig.savefig(os.path.join(figure_path,figure_fn),dpi=500)

                # then make plots that trim full scale to exclued the full extend of ncut_plots
                ymax1 = ymax_all[-1 - ncut_plots]
                for ax1 in ax.flatten():
                    ax1.set_ylim((-1.05*ymax1, 1.05*ymax1))
                for ax1 in ax_twin.flatten():
                    ax1.set_ylim((-1.05*ymax1, 1.05*ymax1))
                fig.savefig(os.path.join(figure_path,figure_zoom_fn))
            else:
                if nruns==1:
                    pass
                else:
                    for itime in range(ntime):
                        if ntime==1:
                            ax1 = ax
                            ax2 = ax_twin
                        else:
                            ax1 = ax[itime]
                            ax2 = ax_twin[itime]
                        wy_unique = np.unique(wy_list)
                        for wy in wy_unique:
                            ymax1 = 0
                            ymax2 = 0
                            for irun in range(nruns):
                                if wy_list[irun] == wy:
                                    ymax1 = np.max([ymax1, np.abs(ax1[irun].get_ylim()[0]),np.abs(ax1[irun].get_ylim()[1])])
                                    ymax2 = np.max([ymax2, np.abs(ax2[irun].get_ylim()[0]),np.abs(ax2[irun].get_ylim()[1])])
                            for irun in range(nruns):
                                if wy_list[irun] == wy:
                                    ax1[irun].set_ylim((-1.05*ymax1, 1.05*ymax1))
                                    ax2[irun].set_ylim((-1.05*ymax2, 1.05*ymax2))
                if same_trans_axis:
                    ymax1 = 0
                    for ax1 in ax.flatten():
                         ymax1 = np.max([ymax1, np.abs(ax1.get_ylim()[0]),np.abs(ax1.get_ylim()[1])])
                    for ax1 in ax.flatten():
                        ax1.set_ylim((-1.05*ymax1, 1.05*ymax1))
                if same_rx_axis:
                    ymax1 = 0
                    for ax1 in ax_twin.flatten():
                         ymax1 = np.max([ymax1, np.abs(ax1.get_ylim()[0]),np.abs(ax1.get_ylim()[1])])
                    for ax1 in ax_twin.flatten():
                        ax1.set_ylim((-1.05*ymax1, 1.05*ymax1))
                        # if runs are for the same water year, make their y axes match

                fig.savefig(os.path.join(figure_path,figure_fn))
            
            plt.close('all')                        