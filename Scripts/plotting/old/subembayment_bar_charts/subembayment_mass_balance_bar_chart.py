
"""
alliek prep for 2022 NTW meeting March 11, adapted for manuscript in June/July 2022
"""


import pandas as pd 
import numpy as np 
import matplotlib.pyplot as plt
import sys
import os 

#############################
# user input
#############################

# figure size
figsize = (8.5,13.5)
figsize_algae = (8.5,11)

# base directory (windows or linux)
#base_dir = r'X:\hpcshared'
base_dir = '/richmondvol1/hpcshared'

# path to balance tables (they should be organized by run ID within this folderr)
balance_table_path = os.path.join(base_dir,'NMS_Projects','Control_Volume_Analysis','Balance_Tables')

# list of "groups" corresponding to subembayments (these are their names in the balance tables)
group_list = ['LSB', 'SB_RMP', 'Central_Bay_RMP', 'San_Pablo_Bay', 'Suisun_Bay', 'Whole_Bay']  

# list of bar plot labels corresponding to these groups
group_labels = ['Lower\nSouth Bay', 'South Bay\n(RMP)', 'Central Bay\n(RMP)', 'San Pablo\nBay', 'Suisun Bay', 'Whole Bay']


# this compares latest full res runs
#bar_labels = ['WY2013 (FR13_025)','WY2017 (FR17_018)','WY2018 (FR18_006)']
#bar_run_ID = ['FR13_025','FR17_018','FR18_006']
#bar_wy = [2013,2017,2018]

# compare old and new full res runs
#bar_labels = ['WY2013 (FR13_025)','WY2013 (FR13_003)','WY2017 (FR17_018)','WY2017 (FR17_003)','WY2018 (FR18_006)']
#bar_run_ID = ['FR13_025','FR13_003','FR17_018','FR17_003','FR18_006']
#bar_wy = [2013,2013,2017,2017,2018]
bar_labels = ['WY2013 (G141_13to18_197)','WY2014 (G141_13to18_197)','WY2015 (G141_13to18_197)','WY2016 (G141_13to18_197)','WY2017 (G141_13to18_197)','WY2018 (G141_13to18_197)']
bar_run_ID = ['G141_13to18_197','G141_13to18_197','G141_13to18_197','G141_13to18_197','G141_13to18_197','G141_13to18_197']
bar_wy = [2013,2014,2015,2016,2017,2018]

# some plot style choicesa
colors = ['red','gold','purple','orange','blue','magenta']

# fill the bar (True) or leave center transparent (False)?
fills = [True,True,True,True,True,True]

# list of directions the influx comes from, by group name key
# each connection in the list is itself a tuple with the following 3 entries:
# (group name, direction flux comes INTO the group from, multiplier to turn flux in into an influx to the group key CV)
# note if the group name is the same as the group key, the multiplier should be 1, and if it is an adjacent group, it should be -1
influx_dir_dict = {}
influx_dir_dict['LSB'] = []
influx_dir_dict['SB_RMP'] = [('SB_RMP','S',1)]
influx_dir_dict['Central_Bay_RMP'] = [('Central_Bay_RMP','S',1),('Central_Bay_RMP','N',1)]
# SAN PABLO BAY INFLUX IS DIFFERENT FOR AGG GRID, SO SET THIS INSIDE THE FOR LOOP LATER ON, MAKING IT POSSIBLE TO COMPARE FULL RES AND AGG RUNS
#influx_dir_dict['San_Pablo_Bay'] = [('San_Pablo_Bay','E',1),('Sonoma','S',-1),('Petaluma','S',-1),('Napa','S',-1)]
influx_dir_dict['Suisun_Bay'] = [('Suisun_Bay','E',1),('Suisun_Bay','N',1)]
influx_dir_dict['Whole_Bay'] = [('Whole_Bay','E',1),('Whole_Bay','N',1)]

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

# run id prefix (this should reflect the runs)
run_ID_prefix = ''
for run_ID in np.unique(np.array(bar_run_ID)):
    run_ID_prefix += run_ID + '_'


# figure path
if all(np.array(bar_run_ID)==bar_run_ID[0]):
    figure_path = os.path.join(base_dir,'NMS_Projects','Control_Volume_Analysis','Plots',bar_run_ID[0],'bar_plots')
else:
    figure_path = os.path.join(base_dir,'NMS_Projects','Control_Volume_Analysis','Plots','Compare_Water_Years','bar_plots')

##########################
# main
##########################

# check if plot directory exists and create it if not
if not os.path.exists(figure_path):
    os.makedirs(figure_path)

# loop through some time averaging periods

# parameter to plot
for param in ['Algae', 'DIN', 'TN', 'TN_include_sediment']:

    # balance table name
    balance_table_fn = '%s_Table_By_Group.csv' % param.lower()
    
    # norm ('Total', 'Area', or 'Volume')
    for norm in ['Total','Area','Volume']:

        for tperiod in ['annual','fall','winter','spring','summer']:

            bar_start_time = []
            bar_end_time = []

            if tperiod=='annual':

                for wy in bar_wy:
                    bar_start_time.append('%d-10-01' % (wy-1))
                    bar_end_time.append('%d-10-01' % wy)
                tsuf = 'Annual' # suffix for figure neme that indicates time averaging period
                figure_title = 'Annual Average %s Budget' % param
                
            elif tperiod=='fall':

                for wy in bar_wy:
                    bar_start_time.append('%d-10-01' % (wy-1)) 
                    bar_end_time.append('%d-01-01' % wy) 
                tsuf = 'Oct-Nov-Dec' # suffix for figure neme that indicates time averaging period
                figure_title = '%s Budget: Oct, Nov, Dec' % param

            elif tperiod=='winter':

                for wy in bar_wy:
                    bar_start_time.append('%d-01-01' % wy) 
                    bar_end_time.append('%d-04-01' % wy) 
                tsuf = 'Jan-Feb-Mar' # suffix for figure neme that indicates time averaging period
                figure_title = '%s Budget: Jan, Feb, Mar' % param
            
            elif tperiod=='spring':

                for wy in bar_wy:
                    bar_start_time.append('%d-04-01' % wy) 
                    bar_end_time.append('%d-07-01' % wy) 
                tsuf = 'Apr-May-Jun' # suffix for figure neme that indicates time averaging period
                figure_title = '%s Budget: Apr, May, Jun' % param
            
            elif tperiod=='summer':

                for wy in bar_wy:
                    bar_start_time.append('%d-07-01' % wy) 
                    bar_end_time.append('%d-10-01' % wy) 
                tsuf = 'Jul-Aug-Sep' # suffix for figure neme that indicates time averaging period
                figure_title = '%s Budget: Jul, Aug, Sep' % param

            # figure name includes norm
            figure_name = '%s%s_Subembayment_Mass_Budget_Bar_Plot_%s_%s.png' % (run_ID_prefix, param, tsuf, norm)
            
            # check that the bar labels, run ids, and start times have the same dimension
            nbars = len(bar_labels)
            if not len(bar_run_ID)==nbars:
                raise Exception('bar_run_ID must have same length as bar_labels')
            if not len(bar_start_time)==nbars:
                raise Exception('bar_start_time must have same length as bar_labels')
            if not len(bar_end_time)==nbars:
                raise Exception('bar_end_time must have same length as bar_labels')
            
            # number of groups
            ngroups = len(group_list)
            if not len(group_labels)==ngroups:
                raise Exception('group_labels must have same length as group_list')
            
            # norm label
            if norm=='Total':
                units = 'Mg/d'
            elif norm=='Area':
                units = 'kg/d/m$^2$'
            elif norm=='Volume':
                units = 'kg/d/m$^3$'
            else:
                raise Exception('do not recognize norm type %s, must be Total, Area, or Volume' % norm)
            
            # build up arrays whose rows correspond to the different bar colors, and columns are the different groups (subembayments), 
            # we are going to plot the influx, outflux, loading, and rx
            data_influx  = np.zeros((nbars, ngroups))
            data_outflux = np.zeros((nbars, ngroups))
            data_rx    = np.zeros((nbars, ngroups))
            data_load    = np.zeros((nbars, ngroups))
            data_storage    = np.zeros((nbars, ngroups))
            
            # loop through the bar colors
            for ibar in range(nbars):

                ### SAN PABLO BAY INFLUX COMPONENTS ARE DIFFERENT FOR AGG AND FULL RES RUNS SO SET THEM HERE
                if 'FR' in bar_run_ID[ibar]:
                    influx_dir_dict['San_Pablo_Bay'] = [('San_Pablo_Bay','E',1),('Sonoma','S',-1),('Petaluma','S',-1),('Napa','S',-1)]
                else:
                    influx_dir_dict['San_Pablo_Bay'] = [('San_Pablo_Bay','E',1),('Napa','S',-1)]
            
                # load the run for this bar color and average over the time period specified for this bar color
                df = pd.read_csv(os.path.join(balance_table_path, bar_run_ID[ibar], balance_table_fn))
                df['time'] = pd.to_datetime(df['time'])
                indt = np.logical_and(df['time']>=np.datetime64(bar_start_time[ibar]), df['time']<np.datetime64(bar_end_time[ibar]))
                df = df.loc[indt].groupby(['group']).mean()
            
                # loop through the group
                for igroup in range(ngroups):
            
                    # get the data for this group
                    df_group = df.loc[df.index == group_list[igroup]]
            
                    # get the value we need to normalize by
                    if norm=='Total':
                        normval = 1
                    elif norm=='Area':
                        normval = df_group['Area (m^2)'].values[0] / 1e9
                    elif norm=='Volume':
                        normval = df_group['Volume (m^3)'].values[0] / 1e9
                    else:
                        raise Exception('do not recognize norm type %s, must be Total, Area, or Volume' % norm)
            
                    # put the loads and rxes and storage in the data array (note for TN_include_sediment we didn't handle concentration correctly for
                    # sediment partition, so dM/dt is not correct -- use the dM/dt from the mass balance check instead for this parameter)
                    data_load[ibar, igroup] = df_group['%s,Net Load (Mg/d)' % param] / normval
                    data_rx[ibar, igroup] = df_group['%s,Net Reaction (Mg/d)' % param] / normval
                    if param == 'TN_include_sediment':
                        data_storage[ibar, igroup] = df_group['%s,dMass/dt, Balance Check (Mg/d)' % param] / normval
                    else:
                        data_storage[ibar, igroup] = df_group['%s,dMass/dt (Mg/d)' % param] / normval
                    
                    # add up the influxes using dictionary that gives list of connections that are influxes for this group
                    for influx in influx_dir_dict[group_list[igroup]]:
                        
                        # each influx is a tuple giving the group, the side, and the mutliplier 
                        influx_group, influx_dir, influx_mult = influx
                    
                        # get the data for the influx group
                        df_influx = df.loc[df.index == influx_group]
                    
                        # add the influx, mutliplying by the multiplier to get the direction right
                        data_influx[ibar, igroup] = data_influx[ibar, igroup] + influx_mult * df_influx['%s,Flux In from %s (Mg/d)' % (param, influx_dir)] / normval
            
                    # add up the outfluxed using dictionary that gives list of connections that are outfluxes for this group
                    for outflux in outflux_dir_dict[group_list[igroup]]:
            
                        # each influx is a tuple giving the group, the side, and the mutliplier 
                        outflux_group, outflux_dir, outflux_mult = outflux
            
                        # get the data for the influx group
                        df_outflux = df.loc[df.index == outflux_group]
            
                        # add the influx, mutliplying by the multiplier to get the direction right
                        data_outflux[ibar, igroup] = data_outflux[ibar, igroup] + outflux_mult * df_outflux['%s,Flux In from %s (Mg/d)' % (param, outflux_dir)] / normval

                    # compute flux in from net transport in and outflux
                    #data_influx[ibar, igroup] = df_group['%s,Net Transport In (Mg/d)' % param] / normval + data_outflux[ibar, igroup]
            
            # calculate closure error by finding what storage would need to be to close the equation
            data_storage_1 = data_load + data_influx + data_rx - data_outflux
            data_closure = data_storage_1 - data_storage

            # set up an x axis for plotting the different color bars and compute the widths of the bars based on how many there are, also offset
            X = np.arange(ngroups)
            W = 1/(nbars + 1)
            O = (1-nbars)*W/2 
            
            # now that we have all the data, put it in the bar chart
            if param=='Algae':
                n0=5
                fig, ax = plt.subplots(n0,1, figsize=figsize_algae)
            else:
                n0=6
                fig, ax = plt.subplots(n0,1, figsize=figsize)
            for ibar in range(nbars):
                if param=='Algae':
                    i0=0
                else:
                    i0=1
                    ax[0].bar(X + ibar*W + O, data_load[ibar], W, label=bar_labels[ibar], color=colors[ibar], edgecolor=colors[ibar], fill=fills[ibar])
                    ax[0].set_ylabel('Loading (%s)' % units)
                ax[i0].bar(X + ibar*W + O, data_influx[ibar], W, label=bar_labels[ibar], color=colors[ibar], edgecolor=colors[ibar], fill=fills[ibar])
                ax[i0+1].bar(X + ibar*W + O, data_rx[ibar], W, label=bar_labels[ibar], color=colors[ibar], edgecolor=colors[ibar], fill=fills[ibar])
                ax[i0+2].bar(X + ibar*W + O, data_storage[ibar], W, label=bar_labels[ibar], color=colors[ibar], edgecolor=colors[ibar], fill=fills[ibar])
                ax[i0+3].bar(X + ibar*W + O, data_outflux[ibar], W, label=bar_labels[ibar], color=colors[ibar], edgecolor=colors[ibar], fill=fills[ibar])
                ax[i0+4].bar(X + ibar*W + O, data_closure[ibar], W, label=bar_labels[ibar], color=colors[ibar], edgecolor=colors[ibar], fill=fills[ibar])
            
            # add horizonplt.tal grid lines
            for i in range(n0):
                ax[i].yaxis.grid()
            
            # reset the x tick labels
            for i in range(n0):
                ax[i].set_xticks(X)
                ax[i].set_xticklabels(group_labels)
            
            # label the y axes and title
            ax[i0].set_ylabel('Influx (%s)' % units)
            ax[i0+1].set_ylabel('Net Reaction (%s)' % units)
            ax[i0+2].set_ylabel('Storage (%s)' % units)
            ax[i0+3].set_ylabel('Outflux (%s)' % units)
            ax[i0+4].set_ylabel('Closure Err (%s)' % units)
            ax[0].set_title(figure_title)
            
            
            # add legend, tight layout, save
            ax[n0-1].legend(bbox_to_anchor=(0.5, -0.35), loc='upper center', ncol=nbars)
            fig.tight_layout()
            fig.savefig(os.path.join(figure_path,figure_name))
            
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