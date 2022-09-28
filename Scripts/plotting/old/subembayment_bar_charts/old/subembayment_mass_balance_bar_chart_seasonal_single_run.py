
"""
alliek prep for 2020 NTW meeting March 11
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
figsize = (8,8.5)

# base directory (windows or linux)
#base_dir = r'X:\hpcshared'
base_dir = '/richmondvol1/hpcshared'

# path to balance tables (they should be organized by run ID within this folderr)
balance_table_path = os.path.join(base_dir,'NMS_Projects','Control_Volume_Analysis','Balance_Tables')

# run id and water year
runid = 'FR13_025' # 
water_year = 2013
#runid = 'FR17_018'  
#water_year = 2017  
#runid = 'FR18_006'
#water_year = 2018 

# parameter to plot
param = 'DIN'

# norm ('Total', 'Area', or 'Volume')
for norm in ['Total','Area','Volume']:

    # list of "groups" corresponding to subembayments (these are their names in the balance tables)
    group_list = ['LSB', 'SB_RMP', 'Central_Bay_RMP', 'San_Pablo_Bay', 'Suisun_Bay', 'Whole_Bay']  # can add 'Whole_Bay' 
    
    # list of bar plot labels corresponding to these groups
    group_labels = ['Lower\nSouth Bay', 'South Bay\n(RMP)', 'Central Bay\n(RMP)', 'San Pablo\nBay', 'Suisun Bay', 'Whole Bay']
    
    # list of labels for different color bars (different color bars may represent different time periods 
    # or different model runs), and also make lists with the run ID, start time of the averaging period, 
    # and end time of the averaging period for each bar label 
    bar_labels = ['Oct, Nov, Dec','Jan, Feb, Mar','Apr, May, Jun','Jul, Aug, Sep']
    bar_run_ID = [runid,runid,runid,runid]
    bar_start_time = ['%d-10-01' % (water_year-1), '%d-01-01' % water_year, '%d-04-01' % water_year, '%d-07-01' % water_year]
    bar_end_time   = ['%d-01-01' % water_year, '%d-04-01' % water_year, '%d-07-01' % water_year, '%d-10-01' % water_year]
    
    # some plot style choices
    colors = ['blue','cyan','gold','red']
    fills = [True, True, True, True]
    
    # figure title
    figure_title = 'WY%d (%s) Seasonal Budget for %s' % (water_year, runid, param)
    
    # figure name including path (this should reflect the runs)
    figure_path = os.path.join(base_dir,'NMS_Projects','Control_Volume_Analysis','Plots',runid,'bar_plots')
    figure_name = '%s_%s_Seasonal_Mass_Budget_Bar_Plot_%s.png' % (runid, param, norm)
    
    # use same y range for terms in mass budget
    same_y_range = False
    
    # list of directions the influx comes from, by group name key
    # each connection in the list is itself a tuple with the following 3 entries:
    # (group name, direction flux comes INTO the group from, multiplier to turn flux in into an influx to the group key CV)
    # note if the group name is the same as the group key, the multiplier should be 1, and if it is an adjacent group, it should be -1
    influx_dir_dict = {}
    influx_dir_dict['LSB'] = []
    influx_dir_dict['SB_RMP'] = [('SB_RMP','S',1)]
    influx_dir_dict['Central_Bay_RMP'] = [('Central_Bay_RMP','S',1),('Central_Bay_RMP','N',1)]
    influx_dir_dict['San_Pablo_Bay'] = [('San_Pablo_Bay','E',1),('Sonoma','S',-1),('Petaluma','S',-1),('Napa','S',-1)]
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
    
    # balance table name
    balance_table_fn = '%s_Table_By_Group.csv' % param.lower()
    
    ##########################
    # main
    ##########################
    
    # create figure path if does not exist
    if not os.path.exists(figure_path):
        os.makedirs(figure_path)
    
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
        units = 'mg/d/m$^2$'
    elif norm=='Volume':
        units = 'mg/d/m$^3$'
    else:
        raise Exception('do not recognize norm type %s, must be Total, Area, or Volume' % norm)
    
    # build up arrays whose rows correspond to the different bar colors, and columns are the different groups (subembayments), 
    # we are going to plot the influx, outflux, loading, and loss
    data_influx  = np.zeros((nbars, ngroups))
    data_outflux = np.zeros((nbars, ngroups))
    data_loss    = np.zeros((nbars, ngroups))
    data_load    = np.zeros((nbars, ngroups))
    
    # loop through the bar colors
    for ibar in range(nbars):
    
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
    
            # put the loads and losses in the data array
            data_load[ibar, igroup] = df_group['%s,Net Load (Mg/d)' % param] / normval
            data_loss[ibar, igroup] = -df_group['%s,Net Reaction (Mg/d)' % param] / normval
    
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
    
    # set up an x axis for plotting the different color bars and compute the widths of the bars based on how many there are, also offset
    X = np.arange(ngroups)
    W = 1/(nbars + 1)
    O = (1-nbars)*W/2 
    
    # now that we have all the data, put it in the bar chart
    fig, ax = plt.subplots(4,1, figsize=figsize)
    for ibar in range(nbars):
        ax[0].bar(X + ibar*W + O, data_load[ibar], W, label=bar_labels[ibar], color=colors[ibar], edgecolor=colors[ibar], fill=fills[ibar])
        ax[1].bar(X + ibar*W + O, data_influx[ibar], W, label=bar_labels[ibar], color=colors[ibar], edgecolor=colors[ibar], fill=fills[ibar])
        ax[2].bar(X + ibar*W + O, data_loss[ibar], W, label=bar_labels[ibar], color=colors[ibar], edgecolor=colors[ibar], fill=fills[ibar])
        ax[3].bar(X + ibar*W + O, data_outflux[ibar], W, label=bar_labels[ibar], color=colors[ibar], edgecolor=colors[ibar], fill=fills[ibar])
    
    # add horizontal grid lines
    for i in range(4):
        ax[i].yaxis.grid()
    
    # reset the x tick labels
    for i in range(4):
        ax[i].set_xticks(X)
        ax[i].set_xticklabels(group_labels)
    
    # label the y axes and title
    ax[0].set_ylabel('Loading (%s)' % units)
    ax[1].set_ylabel('Influx (%s)' % units)
    ax[2].set_ylabel('Reactive Loss (%s)' % units)
    ax[3].set_ylabel('Outflux (%s)' % units)
    ax[0].set_title(figure_title)
    
    # set the y axes to have the same range
    if same_y_range:
        yrange = np.max([ax[0].get_ylim()[1]-ax[0].get_ylim()[0],
                   ax[1].get_ylim()[1]-ax[1].get_ylim()[0],
                   ax[2].get_ylim()[1]-ax[2].get_ylim()[0],
                   ax[3].get_ylim()[1]-ax[3].get_ylim()[0] ])
        for i in range(4):
            ymin, ymax = ax[i].get_ylim()
            ymin1 = ymin*yrange/(ymax-ymin)
            ymax1 = ymax*yrange/(ymax-ymin)
            ax[i].set_ylim((ymin1,ymax1))
    
    
    # add legend, tight layout, save
    ax[3].legend(bbox_to_anchor=(0.5, -0.35), loc='upper center', ncol=nbars)
    fig.tight_layout()
    fig.savefig(os.path.join(figure_path,figure_name))
    