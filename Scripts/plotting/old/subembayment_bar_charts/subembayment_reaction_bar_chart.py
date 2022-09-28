
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

# run id and water year
#runid = 'FR13_025'  
#water_year_list = [2013]
#runid = 'FR17_018'  
#water_year_list = [2017]  
#runid = 'FR18_006'
#water_year_list = [2018]
#runid = 'FR13_003'  
#water_year_list = [2013]
#runid = 'FR17_003'  
#water_year_list = [2017] 
runid = 'G141_13to18_197'
water_year_list = [2013,2014,2015,2016,2017,2018]

# base directory (windows or linux)
#base_dir = r'X:\hpcshared'
base_dir = '/richmondvol1/hpcshared'

# path to balance tables (they should be organized by run ID within this folderr)
balance_table_path = os.path.join(base_dir,'NMS_Projects','Control_Volume_Analysis','Balance_Tables')

# list of "groups" corresponding to subembayments (these are their names in the balance tables)
group_list = ['LSB', 'SB_RMP', 'Central_Bay_RMP', 'San_Pablo_Bay', 'Suisun_Bay', 'Whole_Bay']  # can add 'Whole_Bay' 

# list of bar plot labels corresponding to these groups
group_labels = ['Lower\nSouth Bay', 'South Bay\n(RMP)', 'Central Bay\n(RMP)', 'San Pablo\nBay', 'Suisun Bay', 'Whole Bay']

# figure size
figsize = (8,4)

##########################
# main
##########################

# number of groups
ngroups = len(group_list)
if not len(group_labels)==ngroups:
    raise Exception('group_labels must have same length as group_list')

# parameter to plot
for param in ['DIN','TN','TN_include_sediment','Algae']:

    # balance table name
    balance_table_fn = '%s_Table_By_Group.csv' % param.lower()
    
    # read balance table
    df = pd.read_csv(os.path.join(balance_table_path, runid, balance_table_fn))
    df['time'] = pd.to_datetime(df['time'])
    
    # get list of reactions, excluding the ones with ZERO in their name 
    reaction_list = []
    for colname in df.columns:
        if ',d' in colname:
            if not ((param + ',dMass/dt') in colname):
                if not 'ZERO' in colname:
                    reaction_list.append(colname)
    
    # get list of sources and sinks based on mean value of reactions
    source_list = []
    sink_list = []
    for reaction in reaction_list:
        if np.mean(df[reaction]) > 0:
            source_list.append(reaction)
        else:
            sink_list.append(reaction)
    nsource = len(source_list)
    nsink = len(sink_list)
    
    # trim (Mg/d) from reaciton names for purpose of legend entries
    source_list_trimmed = []
    for source in source_list:
        source_list_trimmed.append(source.replace(' (Mg/d)',''))
    sink_list_trimmed = []
    for sink in sink_list:
        sink_list_trimmed.append(sink.replace(' (Mg/d)',''))
    
    # initialize data matrices for sources and sinks
    data_sources  = np.zeros((nsource, ngroups))
    data_sinks = np.zeros((nsink, ngroups))
    
    # figure path
    figure_path = os.path.join(base_dir,'NMS_Projects','Control_Volume_Analysis','Plots',runid,'bar_plots')
    if not os.path.exists(figure_path):
        os.makedirs(figure_path)
    
    # set up an x axis for plotting the different color bars and compute the widths of the bars based on how many there are, also offset
    nbars=2
    X = np.arange(ngroups)
    W = 1/(nbars + 1)
    O = (1-nbars)*W/2 
    
    for water_year in water_year_list:

        # loop through these time averaging windows
        tavg_labels = ['Annual Average', 'Oct, Nov, Dec','Jan, Feb, Mar','Apr, May, Jun','Jul, Aug, Sep']
        tavg_figname = ['Annual','Oct-Nov-Dec','Jan-Feb-Mar','Apr-May-Jun','Jul-Aug-Sep']
        tavg_start_time = ['%d-10-01' % (water_year-1),'%d-10-01' % (water_year-1), '%d-01-01' % water_year, '%d-04-01' % water_year, '%d-07-01' % water_year]
        tavg_end_time   = ['%d-10-01' % water_year,    '%d-01-01' % water_year,     '%d-04-01' % water_year, '%d-07-01' % water_year, '%d-10-01' % water_year]

        # number of time averaging windows
        ntime = len(tavg_labels)

        # loop through time averaging windows
        for itime in range(ntime):
        
            # take the time average
            indt = np.logical_and(df['time']>=np.datetime64(tavg_start_time[itime]), df['time']<np.datetime64(tavg_end_time[itime]))
            df_avg = df.loc[indt].groupby(['group']).mean()
        
            # figure title
            figure_title = 'WY%d (%s)\n%s' % (water_year, runid, tavg_labels[itime])
            
            # loop through the norms
            for norm in ['Area','Total','Volume']:
            
        
                # figure name 
                figure_name = '%s_WY%d_%s_Reaction_Bar_Plot_%s_%s.png' % (runid, water_year, param, tavg_figname[itime], norm)
        
                
                # loop through the group
                for igroup in range(ngroups):
            
                    # get the data for this group
                    df_group = df_avg.loc[df_avg.index == group_list[igroup]]
        
                    # get the value we need to normalize by
                    if norm=='Total':
                        normval = 1
                        units = 'Mg/d'
                    elif norm=='Area':
                        normval = df_group['Area (m^2)'].values[0] / 1e6
                        units = 'g/m$^2$/d'
                    elif norm=='Volume':
                        normval = df_group['Volume (m^3)'].values[0] / 1e6
                        units = 'mg/L/d'
        
                    # load up the source and sink matrices
                    for i in range(nsource):
                        data_sources[i, igroup] = df_group[source_list[i]] / normval
                    for i in range(nsink):
                        data_sinks[i, igroup] = df_group[sink_list[i]] / normval
        
                # now that we have all the data, put it in the bar chart
                fig, ax = plt.subplots(figsize=figsize)
        
                # sources 
                if nsource>0:
                    i = 0
                    ax.bar(X + 0*W + O, data_sources[i,:], W, label=source_list_trimmed[i])
                    bottom = data_sources[i,:]
                    for i in range(1,nsource):
                        ax.bar(X + 0*W + O, data_sources[i,:], W, bottom=bottom, label=source_list_trimmed[i])
                        bottom = bottom + data_sources[i,:]
        
                # sinks
                if nsink>0:
                    i = 0
                    ax.bar(X + 1*W + O, -data_sinks[i,:], W, label=sink_list_trimmed[i])
                    bottom = -data_sinks[i,:]
                    for i in range(1,nsink):
                        ax.bar(X + 1*W + O, -data_sinks[i,:], W, bottom=bottom, label=sink_list_trimmed[i])
                        bottom = bottom - data_sinks[i,:]
           
                # add horizontal grid lines 
                ax.yaxis.grid()
            
                # reset the x tick labels
                for i in range(4):
                    ax.set_xticks(X)
                    ax.set_xticklabels(group_labels)
            
                # label the y axes and title
                ax.set_ylabel('%s Reaction Rate (%s)' % (param,units))
                ax.set_title(figure_title)
        
                # add legend, tight layout, save
                ax.legend(bbox_to_anchor=(1, 0.5), loc='center left')
                fig.tight_layout()
                fig.savefig(os.path.join(figure_path,figure_name))
                
                plt.close('all')    