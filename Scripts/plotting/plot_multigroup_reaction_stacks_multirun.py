''' 

this script makes 3-panel plots like the ones from our August 2020 model update report,
our first take at the control volume analysis. 

it is very slow, sorry about that

there are three rows 
    (1) the top row shows the terms in the mass balance (dM/dt, net reaction, net loading, net transport in)
    (2) the second row breaks the transport terms into N/S/E/W components
    (3) the third row is a stack plot with the components of the net reaction

the user can compare multiple runs and multiple water years

the script is capable of making plots even when only some runs contain a given substance (e.g. DiatS1 is 
not in the older runs, but you can compare old and new runs and it will just leave the old run subplots
empty)

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
from scipy import signal
if not 'DISPLAY' in os.environ:
    import matplotlib
    matplotlib.use('agg')
    plt.switch_backend('Agg')
from importlib import reload
import control_volume_plotting_library as CVPL # plotting library must be in same folder as this script
reload(CVPL)
from collections import OrderedDict

# load the nice names for the spatially aggregated "groups" ... if you can't find it, return none
sys.path.append(os.path.join('..','..','Definitions','group_definitions'))
try:
    from control_volume_nice_names import nice_names
except:
    nice_names = None

#########################################################################################
## user input
#########################################################################################

# list of the groups to plot (set to 'all' to plot all groups)
#group_list = ['Whole_Bay','A','D']
group_list = 'all'

# autoscale x axis (if you set to False, script will set min/max based on water year range)
# note: this option was added for the 2022 HAB simulations, you probably want to set it to False for everything else
autoscale_x = True

# here's another option for the x axis ... again only applies to the HAB model
xlim_override = None
#xlim_override = ['%d-07-20', '%d-09-10']

# list or runs to plot and water years to pick out of corresponding run (each is a column in the plot)
# use 'WY13to18' to plot all years of a 6-year aggregated grid run, otherwise format should be 'WY2013', 'WY2018', etc.
# also list servers where runs are stored
#runid_list = ['FR13_028', 'FR14_001', 'FR15_001', 'FR16_001','FR17_021','FR18_009']
#wystr_list = ['WY2013','WY2014','WY2015','WY2016','WY2017','WY2018']
#server_list = ['chicago','boise','boise','boise','chicago','chicago']
runid_list = ['FR21_007', 'FR21_009','FR21_008']
wystr_list = ['WY2021','WY2021','WY2021']
server_list = ['chicago','chicago','chicago']
vol_list = ['vol2','vol2','vol2']

# list of groups
panel = 'Middle_Subs_RMP_and_WB'

if panel == 'Middle_Subs_RMP_and_WB':
    group_list = ['San_Pablo_Bay','Central_Bay_WB','SB_WB_north_half','SB_RMP']
    group_labels = ['San Pablo Bay','Central Bay (WB)','South Bay (WB, N. half)','South Bay (RMP)']
    panel_label = 'by Subembayment (RMP / WB)'

elif panel == 'All_Subs_RMP':
    group_list = ['Whole_Bay','Suisun_Bay','San_Pablo_Bay','Central_Bay_RMP','SB_RMP','LSB']
    group_labels = ['Whole Bay','Suisun Bay','San Pablo Bay','Central Bay (RMP)','South Bay (RMP)','Lower South Bay']
    panel_label = 'by Subembayment (RMP)'

elif panel == 'All_Subs_WB':
    group_list = ['Whole_Bay','Suisun_Bay','San_Pablo_Bay','Central_Bay_WB','SB_WB','LSB']
    group_labels = ['Whole Bay','Suisun Bay','San Pablo Bay','Central Bay (WB)','South Bay (WB)','Lower South Bay']
    panel_label = 'by Subembayment (Water Board)'

elif panel == 'South_Bay_6Part':
    group_list = ['SB_WB_west_shoal_north_half','SB_WB_channel_north_half','SB_WB_east_shoal_north_half',
                     'SB_WB_west_shoal_south_half','SB_WB_channel_south_half','SB_WB_east_shoal_south_half']
    group_labels = ['NW Shoal','N Channel','NE Shoal','SW Shoal','S Channel','SE Shoal']
    panel_label = 'Across South Bay'

# list of parameters to plot (must match balance table, one plot per parameter is created)
param_list = ['DIN','TN','TN_plus_DetNS12','OXY','DetNS12','OONS12', 'Algae','DetCS1']

# reaction groupings (optional, if parameter is not found as a key, all 
# reactions will be plotted)
rx_grouping = {}
if 1:
    # grouping for DIN
    din_dict = OrderedDict()
    din_dict['Denitrification (Mg/d)'] = ['NO3,dDenit (Mg/d)']
    din_dict['Uptake, Pelagic (Mg/d)'] = ['DIN,dDINUpt (Mg/d)'] 
    din_dict['Uptake, Benthic (Mg/d)'] = ['DIN,dDINUptS1 (Mg/d)']
    din_dict['Water Col. Recycling (Mg/d)'] = ['NH4,dMinPON1 (Mg/d)',
                                        'NH4,dMinPON2 (Mg/d)',
                                        'NH4,dMinDON (Mg/d)',
                                        'NH4,dZ_NRes (Mg/d)',
                                        'NH4,dNH4Aut (Mg/d)']
    din_dict['Mineral. of Detritus (Mg/d)'] = ['NH4,dMinDetNS12 (Mg/d)']
    rx_grouping['DIN'] = din_dict

    # grouping for TN
    tn_dict = OrderedDict()
    tn_dict['Denitrification (Mg/d)'] = ['NO3,dDenit (Mg/d)']
    tn_dict['Settling of Algae/PON (Mg/d)'] = ['Algae,dSedAlgae (Mg/d)',
                                        'PON1,dSedPON1 (Mg/d)',
                                        'PON2,dSedPON2 (Mg/d)'] 
    tn_dict['Benthic Algae Mortality (Mg/d)'] = ['DiatS1,dMrtDiatS1 (Mg/d)']
    tn_dict['Mineral. of Detritus (Mg/d)'] = ['NH4,dMinDetNS12 (Mg/d)']
    rx_grouping['TN']  = tn_dict

# list of types of time aggregation (e.g. ['Filtered','Cumulative','Daily']) one plot per is created
#tavg_list = ['Filtered','Cumulative']
#tavg_list = ['Daily']
tavg_list = ['Filtered','Cumulative']

# list of normalizations (divide by 'None','Area','Volume')
norm_list = ['None','Area','Volume']

# base directory for the output figures (in theory should be able to run on windows laptop with mounted drives or on server)
figure_base_dir = '/richmondvol1/hpcshared/open_bay/bgc/figures'

# number of runs (corresponds to number of columns)
nruns = len(runid_list)
assert nruns==len(wystr_list)
ngroups = len(group_list)
assert ngroups==len(group_list)
assert ngroups==len(group_labels)

# width of figure and height of figure per row (number of rows is variable)
if 'WY13to18' in wystr_list: 
    fig_width = 7.5*(nruns+0.75)
else:
    fig_width = 4*(nruns+0.75)
row_height = 3
fig_height = row_height*ngroups

# maximum number of rows in the legend (needed b/c tight_layout shrinks subplot windows to try 
# to accomodate legend, unsuccessfully, if it gets too long --OXY reaction in particular has so many reactions)
max_legend_rows = 10

# start with the default color cycle and add even more colors because the number of reactions is OUT OF CONTROL!
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
          'fuchsia','gold','lawngreen','aqua','lavender','navy','lightgray']

# map variable to element (grams of what?)
element_dict = {}
element_dict['TN'] = 'N'
element_dict['TN_include_sediment'] = 'N'
element_dict['TN_plus_DetNS12'] = 'N'
element_dict['DetNS12'] = 'N'
element_dict['OONS12'] = 'N'
element_dict['TotalDetNS'] = 'N'
element_dict['DIN'] = 'N'
element_dict['NO3'] = 'N'
element_dict['NH4'] = 'N'
element_dict['N-Algae'] = 'N'
element_dict['N-Diat'] = 'N'
element_dict['N-Green'] = 'N'
element_dict['N-DiatS1'] = 'N'
element_dict['N-Zoopl'] = 'N'
element_dict['Algae'] = 'C'
element_dict['Diat'] = 'C'
element_dict['Green'] = 'C'
element_dict['DiatS1'] = 'C'
element_dict['DetCS1'] = 'C'
element_dict['Zoopl'] = 'C'
element_dict['OXY'] = 'O'

# tells you if the parameter is benthic (if it's benthic, don't include the transport plot, because it
# doesn't get transported, so everything is zero)
def is_it_benthic(param):

    if param in ['DetNS1','DetNS2','DetNS','OONS1','OONS2','OONS','OONS12','DetNS12',
                 'TotalDetNS1','TotalDetNS1','TotalDetNS','DiatS1','DetCS1']:
        is_benthic = True
    else:
        is_benthic = False

    return is_benthic

#########################################################################################
## functions
#########################################################################################

def pos_neg(array):

    '''returns two arrays with shape array, one with positive entries, other with negative,
    all other entries are zero'''

    shape = np.shape(array)
    pos = np.zeros(shape)
    neg = np.zeros(shape)

    ind = array>0
    pos[ind] = array[ind]

    ind = array<0
    neg[ind] = array[ind]

    return pos, neg

#########################################################################################
## main
#########################################################################################


# get string with concise list of runs 
run_list_str = CVPL.make_concise_runid_list_string(runid_list)

# from the list of water year strings, get a list of integer water years, then convert back
# to a concise list of water year strings for naming the figure
wy_list = CVPL.list_of_wy_str_2_list_of_int_wys(wystr_list)   # note this variable gets overridden later
wy_list_str = CVPL.make_concise_water_year_list_string(wy_list)

# path to figures, create if it does not exist
figure_path = os.path.join(figure_base_dir, run_list_str, 'reaction_stacks_multigroup_multirun')
if not os.path.exists(figure_path):
    os.makedirs(figure_path)
print('\nfigures will be saved here: %s\n' % figure_path)

# loop through parameters
for param in param_list:
    
    # loop through different time averages: daily, spring-neap filter, cumulative
    for tavg in tavg_list:

        # for figure labeling
        if tavg=='Filtered':
            tavg_str = 'Spring-Neap Filtered'
        else:
            tavg_str = tavg

        # for loading balance tables
        if tavg=='Daily':
            tavg_BT_str = ''
        else:
            tavg_BT_str = '_' + tavg

        # units in the balance table column names
        if tavg=='Cumulative':
            units = 'Mg'
        else:
            units = 'Mg/d'
    
        # before we plot the different runs, take a sneak peek to find a list of all the reactions, across 
        # all the runs
        master_source_cols = []
        master_sink_cols = []
        master_reaction_cols = []
        for irun in range(nruns):

            # get the run id
            runid = runid_list[irun]

            # get path to the balance table folder in the run folder
            run_base_dir = '/%s%s/hpcshared' % (server_list[irun],vol_list[irun])
            run_dir = CVPL.get_run_dir(run_base_dir, runid)
            balance_table_dir = os.path.join(run_dir,'Balance_Tables_V2')
            
            # load up the balance table data for the parameter of interest
            input_fn = os.path.join(balance_table_dir,'%s_Table_By_Group%s.csv' % (param.lower(), tavg_BT_str))
            try:
                data = pd.read_csv(input_fn)
            except:
                print('could not open %s\nit probably doesn''t exist, skipping this one' % input_fn)
                continue

            # get the reaction lists
            source_cols = []
            sink_cols = []
            for col in data.columns:
                if not 'ZERO' in col:
                    if not ',dMass/' in col:
                        if ',d' in col:
                            if data[col].mean()>=0:
                                source_cols.append(col)
                            elif data[col].mean()<0:
                                sink_cols.append(col)

            # group the reactions if indicated and recalculate sources and sinks
            if param in rx_grouping.keys():
                source_cols = []
                sink_cols = []
                data1 = data[['group', 'time', 'Volume (m^3)', 'Volume (Mean, m^3)', 
                              'Area (m^2)','%s,Mass (Mg)' % param, 
                              '%s,dMass/dt (%s)' % (param,units), 
                              '%s,Net Flux In (%s)' % (param,units),
                              '%s,Net Load (%s)' % (param,units), 
                              '%s,Net Transport In (%s)' % (param,units),
                              '%s,dMass/dt, Balance Check (%s)' % (param,units)]]
                for key in rx_grouping[param].keys():
                    key1 = key.replace('Mg/d',units)
                    rx_list = [rx.replace('Mg/d',units) for rx in rx_grouping[param][key]]
                    data1[key1] = data[rx_list].sum(axis=1)
                    if data1[key1].mean()>=0:
                        source_cols.append(key1)
                    elif data1[key1].mean()<0:
                        sink_cols.append(key1)
                data = data1.copy()

            # add to master list
            for rx in source_cols:
                if not rx in master_source_cols:
                    master_source_cols.append(rx)
            for rx in sink_cols:
                if not rx in master_sink_cols:
                    master_sink_cols.append(rx)

        # sometimes a term may be a source or a sink, such as oxygen reaeration...
        # in this case our algorithim might have flagged it as a source in one run and 
        # a sink in the other (depending if the average was positive or negative) ... go through
        # the source terms and make sure none of them appear as sinks as well
        # search for any such terms and delete them from the sink list
        for source in master_source_cols:
            if source in master_sink_cols:
                master_sink_cols.remove(source)

        # combine master sources and sinks to get reactions
        master_reaction_cols = []
        for rx in master_sink_cols:
            master_reaction_cols.append(rx)
        for rx in master_source_cols:
            master_reaction_cols.append(rx)
            
        # trim the units for concise legend
        master_reaction_cols_trimmed = []
        for rx in master_reaction_cols:
            master_reaction_cols_trimmed.append(rx.replace(' (%s)' % units,''))

        # loop through the norms
        for norm in norm_list:

            # initialize the figure
            fig, ax = plt.subplots(ngroups,nruns,figsize=(fig_width, fig_height))
              
            # loop through the runs, each one is a column in the figure
            for irun in range(nruns):
        
                # get the run id
                runid = runid_list[irun]
            
                # get path to the balance table folder in the run folder
                run_base_dir = '/%s%s/hpcshared' % (server_list[irun],vol_list[irun])
                run_dir = CVPL.get_run_dir(run_base_dir, runid)
                balance_table_dir = os.path.join(run_dir,'Balance_Tables_V2')
                
                # load up the balance table data for the parameter of interest
                input_fn = os.path.join(balance_table_dir,'%s_Table_By_Group%s.csv' % (param.lower(), tavg_BT_str))
                try:
                    data = pd.read_csv(input_fn)
                except:
                    raise Exception('could not open %s' % input_fn)

                # group the reactions if indicated 
                if param in rx_grouping.keys():
                    source_cols = []
                    sink_cols = []
                    data1 = data[['group', 'time', 'Volume (m^3)', 'Volume (Mean, m^3)', 
                                  'Area (m^2)','%s,Mass (Mg)' % param, 
                                  '%s,dMass/dt (%s)' % (param,units), 
                                  '%s,Net Flux In (%s)' % (param,units),
                                  '%s,Net Load (%s)' % (param,units), 
                                  '%s,Net Transport In (%s)' % (param,units),
                                  '%s,dMass/dt, Balance Check (%s)' % (param,units)]]
                    for key in rx_grouping[param].keys():
                        key1 = key.replace('Mg/d',units)
                        rx_list = [rx.replace('Mg/d',units) for rx in rx_grouping[param][key]]
                        data1[key1] = data[rx_list].sum(axis=1)
                    data = data1.copy()


                # get the list of columns we want to normalize (anythign with Mg in the name)
                norm_cols = []
                for col in data.columns:
                    if 'Mg' in col:
                        norm_cols.append(col)

                # if normalized, divide and change units
                if norm == 'None':
                    units_label = '%s %s' % (units, element_dict[param])
                    units_mass_label = 'Mg %s' % element_dict[param]
                    norm_name = ''
                    norm_title = ''
                elif norm == 'Area':
                    for col in norm_cols:
                        data[col] = data[col] / data['Area (m^2)'] * 1e6
                    units_label = '%s/m$^2$ %s' % (units.replace('M',''),element_dict[param])
                    units_mass_label = 'g %s/m$^2$' % element_dict[param]
                    norm_name = '_Per_Area'
                    norm_title = ' (per unit area)'
                elif norm == 'Volume':
                    for col in norm_cols:
                        data[col] = data[col] / data['Volume (Mean, m^3)'] * 1e6
                    units_label = '%s/m$^3$ %s' % (units.replace('M',''),element_dict[param])
                    units_mass_label = 'g %s/m$^3$' % element_dict[param]
                    norm_name = '_Per_Volume'
                    norm_title = ' (per unit volume)'

                # generate a list of water years to plot from this run, based on the water year string
                # (this is confusing because for each item in the wystr_list we are generating another list
                wystr = wystr_list[irun]
                wy_list = CVPL.list_of_wy_str_2_list_of_int_wys([wystr]) 
            
                # get first and last date for time axis
                wymin = np.array(wy_list).min()
                wymax = np.array(wy_list).max()
                t_window = np.array(['%d-10-01' % (wymin-1),'%d-10-01' % wymax]).astype('datetime64')

                # convert time to numpy and select time window
                data['time'] = data['time'].astype('datetime64[ns]')
                ind = np.logical_and( data.time>=t_window[0], data.time<t_window[1])
                data = data.loc[ind]
            
                # get time
                time = np.unique(data['time'].values)
                ntime = len(time)

                # loop through the groups
                for igroup, group in enumerate(group_list):

                    # get the figure axis
                    ax1 = ax[igroup,irun]

                    # find indices of data in this group
                    ind = data['group'] == group

                    # select data in this group
                    data_group = data.loc[ind].copy()
            
                    # convert times from string to datetime64
                    data_group['time'] = pd.to_datetime(data_group['time'])
            
                    # compute time step in days
                    deltat = (data_group['time'].iloc[1] - data_group['time'].iloc[0])/np.timedelta64(1,'h')/24

                    # find the area and volume of the group
                    area_km2 = np.mean(data_group['Area (m^2)'].values)/1000/1000
                    volume_km2xm = np.mean(data_group['Volume (Mean, m^3)'].values)/1000/1000

                    # make dataframe with reactions 
                    df = pd.DataFrame(columns=master_reaction_cols)
                    for rx in master_reaction_cols:
                        if rx in data_group.columns:
                            df[rx] = data_group[rx].copy()
                    df = df.fillna(0)
                    df.columns = master_reaction_cols_trimmed

                    # add terms to close the mass budget 
                    df.insert(loc=0,
                              column='Loads',
                              value=data_group['%s,Net Load (%s)' % (param,units)])
                    #df.insert(loc=2,
                    #          column='Net Transport In',
                    #          value=data_group['%s,Net Transport In (%s)' % (param,units)])
                    df['-dM/dt']=-data_group['%s,dMass/dt, Balance Check (%s)' % (param,units)]
                    

                    # compute net reaction
                    #net_rx = df.values.sum(axis=1)
            
                    # divide into positive and negative
                    df_pos = df.copy(deep=True)
                    df_neg = df.copy(deep=True)
                    df_pos[df<0] = 0
                    df_neg[df>0] = 0
            
                    # add to figure 
                    ax1.stackplot(time, df_pos.values.transpose(), colors = colors[0:len(df.columns)], labels=df.columns)
                    ax1.stackplot(time, df_neg.values.transpose(), colors = colors[0:len(df.columns)])

                    # add decorations to plot
                    if igroup==0:
                        ax1.set_title(runid)
                    if irun==0:
                        ax1.set_ylabel('%s\nArea: %0.0f km$^2$\nVol: %0.0f km$^2$m\nReactions (%s)' % (group_labels[igroup],area_km2,volume_km2xm,units_label))
                    if not irun==0:
                        ax1.yaxis.set_tick_params(labelleft=False)
                    if irun==(nruns-1) and igroup==0:

                        # put the legend in the last column, but with contents based on first column that had data
                        nrx = len(master_reaction_cols)
                        ncol = int(np.ceil(nrx/max_legend_rows))
                        ax1.legend(loc='center left',bbox_to_anchor=(1, 0.5), ncol=ncol)
            
                # format time axis for all rows
                for ax1 in ax[:,irun]:
                    ax1.set_xlim((t_window[0],t_window[1]))
                    ax1.xaxis.set_major_locator(mdates.YearLocator())
                    ax1.xaxis.set_minor_locator(mdates.MonthLocator(bymonth=(1,4,7,10)))
                    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
                    ax1.grid(visible=True,which='both')


            # for each group, make the y axes the same across runs
            for igroup in range(ngroups):
                ymax = 0
                for irun in range(nruns):
                    ymax1 = np.abs(np.array(ax[igroup,irun].get_ylim())).max()
                    if ymax1 > ymax:
                        ymax = ymax1
                for irun in range(nruns):
                    ax[igroup,irun].set_ylim(-ymax,ymax)

            # add title and save the figure
            fig.suptitle('%s %s Budget%s' % (tavg_str, param, norm_title))
            fig.tight_layout(rect=[0, 0, 1, 0.975])
            figure_fn = '%s_%s_%s_stackplot_%s%s_%s.png' % (run_list_str, wy_list_str, panel, tavg, norm_name, param)
            fig.savefig(os.path.join(figure_path, figure_fn))
            
            # close figures
            plt.close('all')
    
