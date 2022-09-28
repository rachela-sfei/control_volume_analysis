
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
figsize = (6.5,8.5)

# path to balance tables (they should be organized by run ID within this folderr)
balance_table_path = r'X:\hpcshared\NMS_Projects\Control_Volume_Analysis\Balance_Tables'

# run id and water year
runid = 'FR18_004' # 'FR13_021' # 'FR17_014' # 
water_year = 2018 # 2013 # 2017 # 

# parameter to plot
param = 'DIN'

# list of "groups" corresponding to subembayments (these are their names in the balance tables)
group_list = ['LSB', 'SB_RMP', 'Central_Bay_RMP', 'San_Pablo_Bay', 'Suisun_Bay']  # can add 'Whole_Bay' 

# list of bar plot labels corresponding to these groups
group_labels = ['Lower\nSouth Bay', 'South Bay', 'Central Bay', 'San Pablo\nBay', 'Suisun\nBay']

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
figure_title = 'WY%d Seasonal DIN Budget' % water_year

# figure name including path (this should reflect the runs)
figure_fn = r'X:\hpcshared\NMS_Projects\Control_Volume_Analysis\Plots\%s\Seasonal_Mass_Budget_Bar_Plot_WY%d.png' % (runid, water_year)

# use same y range for terms in mass budget
same_y_range = False

# list of directions the influx comes from, by group name key
influx_dir_dict = {}
influx_dir_dict['LSB'] = []
influx_dir_dict['SB_RMP'] = ['S']
influx_dir_dict['Central_Bay_RMP'] = ['S','N']
influx_dir_dict['San_Pablo_Bay'] = ['E']
influx_dir_dict['Suisun_Bay'] = ['E']
influx_dir_dict['Whole_Bay'] = ['E']

# list of directions the outflux goes to, by group name key
outflux_dir_dict = {}
outflux_dir_dict['LSB'] = ['N']
outflux_dir_dict['SB_RMP'] = ['N']
outflux_dir_dict['Central_Bay_RMP'] = ['W']
outflux_dir_dict['San_Pablo_Bay'] = ['S']
outflux_dir_dict['Suisun_Bay'] = ['W']
outflux_dir_dict['Whole_Bay'] = ['W']

# balance table name
balance_table_fn = 'Balance_Table_By_Group_Composite_Parameter_%s.csv' % param

##########################
# main
##########################

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

        # put the loads and losses in the data array
        data_load[ibar, igroup] = df_group['%s,Net Load (Mg/d)' % param]
        data_loss[ibar, igroup] = -df_group['%s,Net Reaction (Mg/d)' % param]

        # add up the influxes using dictionary that gives list of sides that are influxes for this group
        for direction in influx_dir_dict[group_list[igroup]]:
            data_influx[ibar, igroup] = data_influx[ibar, igroup] + df_group['%s,Flux In from %s (Mg/d)' % (param, direction)]

        # add up the outfluxed using dictionary that gives list of sides that are outfluxes for this group
        # noting the outflux is in opposite direction as the flux in so need to multiply by -1
        for direction in outflux_dir_dict[group_list[igroup]]:
            data_outflux[ibar, igroup] = data_outflux[ibar, igroup] - df_group['%s,Flux In from %s (Mg/d)' % (param, direction)]

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
ax[0].set_ylabel('Loading (Mg/d)')
ax[1].set_ylabel('Influx (Mg/d)')
ax[2].set_ylabel('Reactive Loss (Mg/d)')
ax[3].set_ylabel('Outflux (Mg/d)')
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
fig.savefig(figure_fn)
