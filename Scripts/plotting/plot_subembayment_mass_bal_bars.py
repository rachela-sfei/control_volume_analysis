
"""
alliek prep for 2022 NTW meeting March 11, adapted for manuscript in June/July 2022
"""


import pandas as pd 
import numpy as np 
import matplotlib.pyplot as plt
import sys
import os 
import matplotlib.patches as mpatches
from importlib import reload
import control_volume_plotting_library as CVPL # plotting library must be in same folder as this script
reload(CVPL)

#############################
# user input
#############################

# flag to separate sources and sinks
separate_source_sink_flag = True

# base directory for the output figures (in theory should be able to run on windows laptop with mounted drives or on server)
figure_base_dir = '/chicagovol1/hpcshared/open_bay/bgc/figures'

# list of parameters to plot
param_list = ['TotalDetNS', 'DIN','TN_include_sediment', 'TN', 'Algae']

# list of "groups" corresponding to subembayments (these are their names in the balance tables)
group_list = ['LSB', 'SB_RMP', 'Central_Bay_RMP', 'San_Pablo_Bay', 'Suisun_Bay', 'Whole_Bay']  

# list of bar plot labels corresponding to these groups
group_labels = ['Lower\nSouth Bay', 'South Bay\n(RMP)', 'Central Bay\n(RMP)', 'San Pablo\nBay', 'Suisun Bay', 'Whole Bay']

# for each subembayment, there will be a cluster of bars comparing different runs, water years, etc.
# put that info in here
#bar_labels = ['WY2013 (FR13_025)','WY2017 (FR17_018)','WY2018 (FR18_006)']
#bar_run_ID = ['FR13_025','FR17_018','FR18_006']
#bar_wy = [2013,2017,2018]
#bar_labels = ['WY2013 (FR13_025)','WY2013 (FR13_003)','WY2017 (FR17_018)','WY2017 (FR17_003)','WY2018 (FR18_006)']
#bar_run_ID = ['FR13_025','FR13_003','FR17_018','FR17_003','FR18_006']
#bar_wy = [2013,2013,2017,2017,2018]
bar_labels = ['WY2013 (G141_13to18_246)','WY2013 (FR13_003)','WY2017 (G141_13to18_246)','WY2017 (FR17_003)']
bar_run_ID = ['G141_13to18_246','FR13_003','G141_13to18_246','FR17_003']
bar_wy = [2013,2013,2017,2017]
#bar_labels = ['WY2013 (G141_13to18_197)','WY2014 (G141_13to18_197)','WY2015 (G141_13to18_197)','WY2016 (G141_13to18_197)','WY2017 (G141_13to18_197)','WY2018 (G141_13to18_197)']
#bar_run_ID = ['G141_13to18_197','G141_13to18_197','G141_13to18_197','G141_13to18_197','G141_13to18_197','G141_13to18_197']
#bar_wy = [2013,2014,2015,2016,2017,2018]

# list of time averaging periods (choices are 'Annual','Seasonal','Monthly')
#time_period_list = ['Annual','Seasonal','Monthly']
time_period_list = ['Seasonal']

# list of normalizations (divide by 'None','Area','Volume')
#norm_list = ['None','Area','Volume']
norm_list = ['Area','Volume','None']

# ugly hatches to distinguish different runs / water years 
hatches = ['*','o','.','O','xx','--','//','\\\\','||']

# list of directions the subembayment influx comes from, by group name key
# each connection in the list is itself a tuple with the following 3 entries:
# (group name, direction flux comes INTO the group from, multiplier to turn flux in into an influx to the group key CV)
# note if the group name is the same as the group key, the multiplier should be 1, and if it is an adjacent group, it should be -1
# NOTE SAN PABLO BAY INFLUX IS DIFFERENT FOR AGG GRID, SO SET THIS INSIDE THE FOR LOOP LATER ON, MAKING IT POSSIBLE TO COMPARE FULL RES AND AGG RUNS
influx_dir_dict = {}
influx_dir_dict['LSB'] = []
influx_dir_dict['SB_RMP'] = [('SB_RMP','S',1)]
influx_dir_dict['Central_Bay_RMP'] = [('Central_Bay_RMP','S',1),('Central_Bay_RMP','N',1)]
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
outflux_dir_dict['Central_Bay_RMP'] = [('Central_Bay_RMP','W',-1)]
outflux_dir_dict['San_Pablo_Bay'] = [('San_Pablo_Bay','S',-1)]
outflux_dir_dict['Suisun_Bay'] = [('Suisun_Bay','W',-1)]
outflux_dir_dict['Whole_Bay'] = [('Whole_Bay','W',-1)]

# default color cycle
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']

# figure size
figsize = (8.5*len(bar_run_ID)/4 + 2,13.5)

################
# functions
################

# finds the longest common substring between two strings
def lcs(S,T):
    m = len(S)
    n = len(T)
    counter = [[0]*(n+1) for x in range(m+1)]
    longest = 0
    lcs_set = set()
    for i in range(m):
        for j in range(n):
            if S[i] == T[j]:
                c = counter[i][j] + 1
                counter[i+1][j+1] = c
                if c > longest:
                    lcs_set = set()
                    longest = c
                    lcs_set.add(S[i-c+1:i+1])
                elif c == longest:
                    lcs_set.add(S[i-c+1:i+1])

    # convert set to a list and take the first entry
    lcs_out = list(lcs_set)[0]

    return lcs_out

##########################
# main
##########################

# make sure number of bar labels, run id's, and water years matches
nbars = len(bar_labels)
if not len(bar_run_ID)==nbars:
    raise Exception('bar_run_ID must have same length as bar_labels')
if not len(bar_wy)==nbars:
    raise Exception('bar_run_ID must have same length as bar_labels')

# get strings with concise lists of runs and water years
run_list_str = CVPL.make_concise_runid_list_string(bar_run_ID)
wy_list_str = CVPL.make_concise_water_year_list_string(bar_wy)

# path to figures, create if it does not exist
figure_path = os.path.join(figure_base_dir, run_list_str, 'subembayment_mass_bal_bars')
if not os.path.exists(figure_path):
    os.makedirs(figure_path)
print('\nfigures will be saved here: %s\n' % figure_path)

# parameter to plot
for param in param_list:

    # loop thorugh time averaging periods
    for time_period in time_period_list:

        # balance table name
        balance_table_fn = '%s_Table_By_Group_%s.csv' % (param.lower(), time_period)
    
        # read the balance tables and put in a list by runid
        df_allruns = {}
        for ibar in range(nbars):
    
            # runid
            runid = bar_run_ID[ibar]
    
            # get path to the balance table folder in the run folder
            run_base_dir = '/%svol1/hpcshared' % server_list[ibar]
            run_dir = CVPL.get_run_dir(run_base_dir, runid)
            balance_table_dir = os.path.join(run_dir,'Balance_Tables')
    
            # load the run for this bar, convert time to datetime64 
            if not runid in df_allruns.keys():
                df = pd.read_csv(os.path.join(balance_table_dir, balance_table_fn))
                df['time'] = pd.to_datetime(df['time'])
    
                # add to the dictionary
                df_allruns[runid] = df.copy(deep=True)

        # we want to know how many time steps we are going to make plots for -- get the number of time steps by examining the first bar
        # and also looking at the time labels across these time steps, extract the part that is different -- this trims the water year
        # and makes the labels generalizable to all the bars, hopefully!!!
        runid = bar_run_ID[0]
        wy = bar_wy[0]
        df = df_allruns[runid].copy(deep=True)
        ind = np.logical_and(df.time.values>=np.datetime64('%d-10-01' % (wy-1)), df.time.values<np.datetime64('%d-10-01' % wy))
        df = df.loc[ind]
        time = np.unique(df.time.values)
        ntime = len(time)

        # now get the time period labels for the different time steps, trimming off the least common denominator, which hopefully
        # is the water year info, thus making labels apply equally well to all water years
        unique_time_labels = []
        for itime in range(ntime):
            ind = df.time.values == time[itime]
            unique_time_label = df.loc[ind].iloc[0]['Time Period']
            if str(wy-1) in unique_time_label:
                unique_time_label = unique_time_label.replace(str(wy-1),str(wy))
            unique_time_labels.append(unique_time_label)
        least_common_substring = unique_time_labels[0]
        for itime in range(1,ntime):
            least_common_substring = lcs(least_common_substring, unique_time_labels[itime])
        for itime in range(ntime):
            unique_time_labels[itime] = unique_time_labels[itime].replace(least_common_substring,'')
        if time_period=='Annual':
            unique_time_labels = ['Annual Average']

        # norm ('Total', 'Area', or 'Volume')
        for norm in norm_list:
            
            # number of groups
            ngroups = len(group_list)
            if not len(group_labels)==ngroups:
                raise Exception('group_labels must have same length as group_list')
            
            # norm label
            if norm=='None':
                units = 'Mg/d'
                norm_name = ''
            elif norm=='Area':
                units = 'kg/d/m$^2$'
                norm_name = '_Per_Area'
            elif norm=='Volume':
                units = 'kg/d/m$^3$'
                norm_name = '_Per_Volume'

            # loop through the time steps
            for itime in range(ntime):

                # figure name 
                if separate_source_sink_flag:
                    figure_fn = '%s_%s_mass_balance_bars_sources_sinks_%s%s_%s_Time%04d.png' % (run_list_str, wy_list_str, time_period, norm_name, param, itime)
                else:
                    figure_fn = '%s_%s_mass_balance_bars_%s%s_%s_Time%04d.png' % (run_list_str, wy_list_str, time_period, norm_name, param, itime)
            
                # build up arrays whose rows correspond to the different bar colors, and columns are the different groups (subembayments), 
                # we are going to plot the influx, outflux, loading, and rx
                data_influx  = np.zeros((nbars, ngroups))
                data_outflux = np.zeros((nbars, ngroups))
                data_rx      = np.zeros((nbars, ngroups))
                data_source    = np.zeros((nbars, ngroups))
                data_sink    = np.zeros((nbars, ngroups))
                data_load    = np.zeros((nbars, ngroups))
                data_storage    = np.zeros((nbars, ngroups))
                
                # loop through the bar colors
                for ibar in range(nbars):
    
                    # runid and water year
                    runid = bar_run_ID[ibar]
                    wy = bar_wy[ibar]

                    # get the balance table and trim times to the current time step
                    df = df_allruns[runid].copy(deep=True)
                    time = np.unique(df.time.values)
                    time = time[np.logical_and(time>=np.datetime64('%d-10-01' % (wy-1)), time<np.datetime64('%d-10-01' % wy))]
                    time = time[itime]
                    df = df.loc[df.time == time]

                    # get the name of the time averaging period
    
                    ### SAN PABLO BAY INFLUX COMPONENTS ARE DIFFERENT FOR AGG AND FULL RES RUNS SO SET THEM HERE
                    if 'FR' in runid:
                        influx_dir_dict['San_Pablo_Bay'] = influx_dir_dict['San_Pablo_Bay_FR']
                    else:
                        influx_dir_dict['San_Pablo_Bay'] = influx_dir_dict['San_Pablo_Bay_AGG']
    
                    # get list of sources and sinks
                    source_list = []
                    sink_list = []
                    for col in df.columns:
                        if not 'ZERO' in col:
                            if not ',dMass/' in col:
                                if ',d' in col:
                                    if df[col].mean()>0:
                                        source_list.append(col)
                                    elif df[col].mean()<0:
                                        sink_list.append(col)

                    # loop through the group
                    for igroup in range(ngroups):
                
                        # get the data for this group
                        df_group = df.loc[df['group'] == group_list[igroup]]
                
                        # get the value we need to normalize by
                        if norm=='None':
                            normval = 1
                        elif norm=='Area':
                            normval = df_group['Area (m^2)'].values[0] / 1e9
                        elif norm=='Volume':
                            normval = df_group['Volume (Mean, m^3)'].values[0] / 1e9
                
                        # put the loads and rxes and storage in the data array (note for TN_include_sediment we didn't handle concentration correctly for
                        # sediment partition, so dM/dt is not correct -- use the dM/dt from the mass balance check instead for this parameter)
                        data_load[ibar, igroup] = df_group['%s,Net Load (Mg/d)' % param] / normval
                        data_sink[ibar, igroup] = df_group[sink_list].values.sum() / normval
                        data_source[ibar, igroup] = df_group[source_list].values.sum() / normval
                        data_rx[ibar, igroup] = df_group['%s,Net Reaction (Mg/d)' % param] / normval
                        data_storage[ibar, igroup] = df_group['%s,dMass/dt, Balance Check (Mg/d)' % param] / normval
                        
                        # add up the influxes using dictionary that gives list of connections that are influxes for this group
                        for influx in influx_dir_dict[group_list[igroup]]:
                            
                            # each influx is a tuple giving the group, the side, and the mutliplier 
                            influx_group, influx_dir, influx_mult = influx
                
                            # get the data for the influx group
                            df_influx = df.loc[df['group'] == influx_group]
                
                            # add the influx, mutliplying by the multiplier to get the direction right
                            data_influx[ibar, igroup] = data_influx[ibar, igroup] + influx_mult * df_influx['%s,Flux In from %s (Mg/d)' % (param, influx_dir)] / normval
                
                        # add up the outfluxed using dictionary that gives list of connections that are outfluxes for this group
                        for outflux in outflux_dir_dict[group_list[igroup]]:
                
                            # each influx is a tuple giving the group, the side, and the mutliplier 
                            outflux_group, outflux_dir, outflux_mult = outflux
                
                            # get the data for the influx group
                            df_outflux = df.loc[df['group'] == outflux_group]
                
                            # add the influx, mutliplying by the multiplier to get the direction right
                            data_outflux[ibar, igroup] = data_outflux[ibar, igroup] + outflux_mult * df_outflux['%s,Flux In from %s (Mg/d)' % (param, outflux_dir)] / normval
    
                        # compute flux in from net transport in and outflux
                        #data_influx[ibar, igroup] = df_group['%s,Net Transport In (Mg/d)' % param] / normval + data_outflux[ibar, igroup]
    
                # calculate closure error by finding what storage would need to be to close the equation
                data_storage_1 = data_load + data_influx + data_rx - data_outflux
                data_closure = data_storage_1 - data_storage

                # flip the sign of outflux and storage because they are on the RHS of the equation
                data_storage = - data_storage.copy()
                data_outflux = - data_outflux.copy()
                data_closure = - data_closure.copy()
    
                # now divide all the terms into their negative and positive components
                def pos_neg(data):
                    pos = np.zeros((nbars,ngroups))
                    neg = np.zeros((nbars,ngroups))
                    ind = data>0
                    pos[ind] = data.copy()[ind]
                    ind = data<0
                    neg[ind] = data.copy()[ind]
                    return pos, neg
                pos_influx , neg_influx  = pos_neg(data_influx )
                pos_outflux, neg_outflux = pos_neg(data_outflux)
                pos_source , neg_source  = pos_neg(data_source )
                pos_sink   , neg_sink    = pos_neg(data_sink   )
                pos_rx     , neg_rx      = pos_neg(data_rx     )
                pos_load   , neg_load    = pos_neg(data_load   )
                pos_storage, neg_storage = pos_neg(data_storage)
                pos_closure, neg_closure = pos_neg(data_closure)
    
                # find max ylim
                if separate_source_sink_flag:
                    ymax = np.max(pos_influx + pos_outflux + pos_source + pos_sink + pos_load + pos_storage + pos_closure)
                else:
                    ymax = np.max(pos_influx + pos_outflux + pos_rx + pos_load + pos_storage + pos_closure)
                
                # set up an x axis for plotting the different color bars and compute the widths of the bars based on how many there are, also offset
                X = np.arange(ngroups)
                W = 1/(nbars + 1)
                O = (1-nbars)*W/2 
                
                # begin initializing the legend with the hatches corresponding to the different bar labels
                leg_list = []
                for ibar in range(nbars):
                    leg_1 = mpatches.Patch(facecolor='w', hatch = hatches[ibar], label=bar_labels[ibar], edgecolor='k')
                    leg_list.append(leg_1)
    
                # now that we have all the data, put it in the bar chart
                fig, ax = plt.subplots(figsize=figsize)
                for ibar in range(nbars):   
    
                    # positive
                    pos_bottom = np.zeros(np.shape(pos_load[ibar]))
                    neg_bottom = np.zeros(np.shape(neg_load[ibar]))
                    icolor = 0
                    if separate_source_sink_flag:
    
                        # sources
                        ax.bar(X + ibar*W + O, pos_source[ibar], W, bottom=pos_bottom, color=colors[icolor], hatch=hatches[ibar])
                        pos_bottom = pos_bottom + pos_source[ibar]
                        ax.bar(X + ibar*W + O, neg_source[ibar], W, bottom=neg_bottom, color=colors[icolor], hatch=hatches[ibar])
                        neg_bottom = neg_bottom + neg_source[ibar]
                        if ibar==0:
                            leg_1 = mpatches.Patch(facecolor=colors[icolor], label='Source Rxs.')
                            leg_list.append(leg_1)
                        icolor = icolor + 1
                        
                        # sinks
                        ax.bar(X + ibar*W + O, pos_sink[ibar], W, bottom=pos_bottom, color=colors[icolor], hatch=hatches[ibar])
                        pos_bottom = pos_bottom + pos_sink[ibar]
                        ax.bar(X + ibar*W + O, neg_sink[ibar], W, bottom=neg_bottom, color=colors[icolor], hatch=hatches[ibar])
                        neg_bottom = neg_bottom + neg_sink[ibar]
                        if ibar==0:
                            leg_1 = mpatches.Patch(facecolor=colors[icolor], label='Sink Rxs.')
                            leg_list.append(leg_1)
                        icolor = icolor + 1

                        # plot the net reaction as a transparent bar with black outline and base at zero
                        ax.bar(X + ibar*W + O, pos_rx[ibar], W, bottom=0, edgecolor='m', fill=False)
                        ax.bar(X + ibar*W + O, neg_rx[ibar], W, bottom=0, edgecolor='m', fill=False)
                        if ibar==0:
                            leg_1 = mpatches.Patch(edgecolor='m', fill=False, label='Net Reaction')
                            leg_list.append(leg_1)
    
                    else:
    
                        # net rx
                        ax.bar(X + ibar*W + O, pos_rx[ibar], W, bottom=pos_bottom, color=colors[icolor], hatch=hatches[ibar])
                        pos_bottom = pos_bottom + pos_rx[ibar]
                        ax.bar(X + ibar*W + O, neg_rx[ibar], W, bottom=neg_bottom, color=colors[icolor], hatch=hatches[ibar])
                        neg_bottom = neg_bottom + neg_rx[ibar]
                        if ibar==0:
                            leg_1 = mpatches.Patch(facecolor=colors[icolor], label='Net Reaction')
                            leg_list.append(leg_1)
                        icolor = icolor + 1
    
    
                    # storage
                    ax.bar(X + ibar*W + O, pos_storage[ibar], W, bottom=pos_bottom, color=colors[icolor], hatch=hatches[ibar])
                    pos_bottom = pos_bottom + pos_storage[ibar]
                    ax.bar(X + ibar*W + O, neg_storage[ibar], W, bottom=neg_bottom, color=colors[icolor], hatch=hatches[ibar])
                    neg_bottom = neg_bottom + neg_storage[ibar]
                    if ibar==0:
                        leg_1 = mpatches.Patch(facecolor=colors[icolor], label='Storage (dM/dt) x -1')
                        leg_list.append(leg_1)
                    icolor = icolor + 1
    
                    # loading
                    if not param=='Algae':
                        ax.bar(X + ibar*W + O, pos_load[ibar], W, bottom=pos_bottom, color=colors[icolor], hatch=hatches[ibar])
                        pos_bottom = pos_bottom + pos_load[ibar]
                        ax.bar(X + ibar*W + O, neg_load[ibar], W, bottom=neg_bottom, color=colors[icolor], hatch=hatches[ibar])
                        neg_bottom = neg_bottom + neg_load[ibar]
                        if ibar==0:
                            leg_1 = mpatches.Patch(facecolor=colors[icolor], label='Loading (POTW)')
                            leg_list.append(leg_1)
                        icolor = icolor + 1
    
                    # influx
                    ax.bar(X + ibar*W + O, pos_influx[ibar], W, bottom=pos_bottom, color=colors[icolor], hatch=hatches[ibar])
                    pos_bottom = pos_bottom + pos_influx[ibar]
                    ax.bar(X + ibar*W + O, neg_influx[ibar], W, bottom=neg_bottom, color=colors[icolor], hatch=hatches[ibar])
                    neg_bottom = neg_bottom + neg_influx[ibar]
                    if ibar==0:
                        leg_1 = mpatches.Patch(facecolor=colors[icolor], label='Influx')
                        leg_list.append(leg_1)
                    icolor = icolor + 1
    
                    # outflux
                    ax.bar(X + ibar*W + O, pos_outflux[ibar], W, bottom=pos_bottom, color=colors[icolor], hatch=hatches[ibar])
                    pos_bottom = pos_bottom + pos_outflux[ibar]
                    ax.bar(X + ibar*W + O, neg_outflux[ibar], W, bottom=neg_bottom, color=colors[icolor], hatch=hatches[ibar])
                    neg_bottom = neg_bottom + neg_outflux[ibar]
                    if ibar==0:
                        leg_1 = mpatches.Patch(facecolor=colors[icolor], label='Outflux')
                        leg_list.append(leg_1)
                    icolor = icolor + 1
    
                    # closure error
                    ax.bar(X + ibar*W + O, pos_closure[ibar], W, bottom=pos_bottom, color=colors[icolor], hatch=hatches[ibar])
                    ax.bar(X + ibar*W + O, neg_closure[ibar], W, bottom=neg_bottom, color=colors[icolor], hatch=hatches[ibar])
                    if ibar==0:
                        leg_1 = mpatches.Patch(facecolor=colors[icolor], label='Closure Error')
                        leg_list.append(leg_1)
                    
                # add legend to plot
                leg = ax.legend(handles = leg_list, handlelength=4, labelspacing=1.25, loc='center left', bbox_to_anchor=(1, 0.5))
                for patch in leg.get_patches():
                    patch.set_height(15)
                    patch.set_y(-4)
                
                # set y axis
                ax.set_ylim((-1.02*ymax,1.02*ymax))
                
                # add horizonplt.tal grid lines
                ax.yaxis.grid()
                ax.set_axisbelow(True)
                
                # reset the x tick labels
                ax.set_xticks(X)
                ax.set_xticklabels(group_labels)
                
                # label the y axes and title
                ax.set_ylabel('Rate (%s)' % units)
                ax.set_title('%s: %s' % (param, unique_time_labels[itime]))
                       
                # add legend, tight layout, save
                fig.tight_layout()
                fig.savefig(os.path.join(figure_path,figure_fn))
                
                plt.close('all')
                
                #input_fn = os.path.join(input_path, run_ID, 'Balance_Table_By_Group_Composite_Parameter_%s.csv' % param)
                
                #df = pd.read_csv(input_fn)
                
                
                
                
                
                
                
                #data = [[30, 25, 50, 20],
                #[40, 23, 51, 17],
                #[35, 22, 45, 19]]
                #X = np.arange(4)
                #fig = plt.figure()
                #ax = fig.add_axes([0,0,1,1])
                #ax.bar(X + 0.00, data[0], color = 'b', width = 0.25)
                #ax.bar(X + 0.25, data[1], color = 'g', width = 0.25)
                #ax.bar(X + 0.50, data[2], color = 'r', width = 0.25)               