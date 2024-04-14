'''

Use new "Whole_Bay" group to work up a mass budget for the whole bay

For the parameter specified (e.g. DIN, TN, Algae)
creates a plot with 3xN subplots where N is the number of runs 
you want to compare to each other (you can just plot one run if you want)

Row 1: stack plot comparing point source loading, delta influx, influx from 
minor tributaries, storage (dM/dt), net reactions, and outflux through the golden gate
for the parameter specified

Row 2: stack plot showing each of the reactions for the parameter specified 
(ignoring groups of terms that sum to zero) along with the net reaction and the
storage term (dM/dt)

Row 3: breaks outflux through golden gate into components of the parameter 
specified (e.g. if parameter is DIN, breaks DIN export down into NH4 and NO3), 
and also compares export to the net loading from the tribuaries (including delta)
and the point sources

Allie King Sept 2022
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


#########################################################################################
## user input
#########################################################################################

# flad to fudge the budgets, lumping OONS12 mineralization with loading instead of reactions
fudge_oons = True

# autoscale x axis (if you set to False, script will set min/max based on water year range)
# note: this option was added for the 2022 HAB simulations, you probably want to set it to False for everything else
autoscale_x = False

# override min/max time
tmin_override = np.datetime64('2022-07-01')
tmax_override = np.datetime64('2022-08-01')

# list of runs to plot, water year to pick out of corresponding run (each is a column in the plot), 
# and a list of servers where each run is located (use 'WY13to18' to plot all years of a 6-year agg grid run, 
# otherwise format should be 'WY2013', 'WY2018', etc.)
#runid_list = ['FR13_028', 'FR14_001', 'FR15_001', 'FR16_001','FR17_021','FR18_009']
#wystr_list = ['WY2013','WY2014','WY2015','WY2016','WY2017','WY2018']
#server_list = ['chicago','boise','boise','boise','chicago','chicago']
runid_list = ['FR22_046', 'FR22_033','FR22_034','FR22_035','FR22_036','FR22_037']
wystr_list = ['WY2022','WY2022','WY2022','WY2022','WY2022','WY2022']
server_list = ['fortcollins','fortcollins','fortcollins','fortcollins','fortcollins','fortcollins']

## composite parameter (must match suffix of balance table)
param_list = ['DIN']#, 'TN_plus_DetNS12', 'TN', 'DetNS12', 'OONS12','OXY']

# list of types of time aggregation (e.g. ['Filtered','Cumulative','Daily'])
#tavg_list = ['Filtered','Cumulative']
tavg_list = ['Daily']#,'Filtered','Cumulative']

# base directory for the and the output figures (in theory should be able to run on windows laptop with mounted drives or on server)
figure_base_dir = '/richmondvol1/hpcshared/open_bay/bgc/figures'

# start with the default color cycle and add even more colors because the number of reactions is OUT OF CONTROL!
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
          'fuchsia','gold','lawngreen','aqua','lavender','navy','lightgray']

# list of "groups" corresponding to subembayments (these are their names in the balance tables), 
# each "group" corresponds to one set of sourc/sink bars in each subplot of the figure
group_list = ['LSB', 'SB_RMP', 'SB_WB', 'SB_WB_north_half', 
              'Central_Bay_RMP', 'Central_Bay_WB',
              'San_Pablo_Bay', 'Suisun_Bay','Whole_Bay']  # can add 'Whole_Bay' 

# list of bar plot labels corresponding to these groups (must be same length)
group_labels = ['Lower South Bay', 'South Bay (RMP)', 'South Bay (WB)', 'South Bay (WB, north half)', 
                'Central Bay (RMP)', 'Central Bay (WB)', 
                'San Pablo Bay', 'Suisun Bay', 'Whole Bay']

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

# number of runs (corresponds to number of columns)
nruns = len(runid_list)
assert nruns==len(wystr_list)
ngroups = len(group_list)
assert ngroups == len(group_labels)


# figure size for (2-4 rows depending) x (nruns columns) mass budget plot 
if 'WY13to18' in wystr_list: 
    figure_width = 7.5*(nruns+2)
elif nruns<=4:
    figure_width = 4*(nruns+2)
else:
    figure_width = 3.5*(nruns+2)
row_height = 2.5
linewidth = 0.5

# function to list of components of a given parameter
def return_components_list(param):

    if param == 'DIN':
        components_list = ['NH4','NO3']
    elif param == 'TN':
        components_list = ['NH4','NO3','PON1','PON2','DON','N-Zoopl','N-Algae','DiatS1'] 
    elif param == 'TN_plus_DetNS12':
        components_list = ['NH4','NO3','PON1','PON2','DON','N-Zoopl','N-Algae','DiatS1','DetNS12'] 
    elif param == 'TN_include_sediment':
        components_list = ['NH4','NO3','PON1','PON2','DON','N-Zoopl','N-Algae','DiatS1','DetNS12','OONS12'] 
    else:
        components_list = [param]
    ncom = len(components_list)

    return components_list, ncom

# tells you if the parameter is benthic (if it's benthic, don't include the export plot row, because it
# doesn't get transported, so everything is zero)
def is_it_benthic(param):

    if param in ['DetNS1','DetNS2','DetNS12','OONS1','OONS2','OONS12',
                 'TotalDetNS1','TotalDetNS1','TotalDetNS','DiatS1']:
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
figure_path = os.path.join(figure_base_dir, run_list_str, 'subembayment_stack')
if not os.path.exists(figure_path):
    os.makedirs(figure_path)
print('\nfigures will be saved here: %s\n' % figure_path)

# loop through parameters
for param in param_list:

    # get list of components for this parameter
    components_list, ncom = return_components_list(param)

    # compute the number of rows in the plots, depends on whether parameter is benthic and whether
    # breakdown of net reaction by subembayment is included
    nrows = 2
    if not is_it_benthic(param):
        nrows += 4

    # loop through the groups
    for igroup in range(ngroups):
    
        # loop through different time averages: daily, spring-neap filter, cumulative
        for tavg in tavg_list:
        
            # initialize 3 panel figure with complete mass balance, reactions, and export composition
            fig, ax = plt.subplots(nrows,nruns,figsize=(figure_width, row_height*nrows + 0.5))
        
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

            # units
            if tavg=='Cumulative':
                units = 'Mg'
                units_plot = 'Gg'
                divide_by = 1000 # convert Mg to Gg in plots
            else:
                units = 'Mg/d'
                units_plot = 'Mg/d'
                divide_by = 1 # leave as Mg/d in plots
        
            # before we plot the different runs, take a sneak peek to find a list of all the reactions
            master_source_list = []
            master_sink_list = []
            master_reaction_list = []
            for irun in range(nruns):

                # get the run id
                runid = runid_list[irun]
        
                # get path to the balance table folder in the run folder
                run_base_dir = '/%svol1/hpcshared' % server_list[irun]
                run_dir = CVPL.get_run_dir(run_base_dir, runid)
                balance_table_dir = os.path.join(run_dir,'Balance_Tables')

                # load up the balance table data for the parameter of interest
                input_fn = os.path.join(balance_table_dir,'%s_Table_By_Group%s.csv' % (param.lower(), tavg_BT_str))
                data = pd.read_csv(input_fn)

                # get the reaction lists
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

                # add to master list
                for rx in source_list:
                    if not rx in master_source_list:
                        master_source_list.append(rx)
                for rx in sink_list:
                    if not rx in master_sink_list:
                        master_sink_list.append(rx)

            # sometimes a term may be a source or a sink, such as oxygen reaeration...
            # in this case our algorithim might have flagged it as a source in one run and 
            # a sink in the other (depending if the average was positive or negative) ... go through
            # the source terms and make sure none of them appear as sinks as well
            # search for any such terms and delete them from the sink list
            for source in master_source_list:
                if source in master_sink_list:
                    master_sink_list.remove(source)
        
            # combine master sources and sinks to get reactions
            master_reaction_list = []
            for rx in master_sink_list:
                master_reaction_list.append(rx)
            for rx in master_source_list:
                master_reaction_list.append(rx)

            # trim the units for concise legend
            master_reaction_list_trimmed = []
            for rx in master_reaction_list:
                master_reaction_list_trimmed.append(rx.replace(' (%s)' % units,''))

            # if we are fudging the oons budget, remove OONS mineralization from the master reaction list
            if fudge_oons and (param in ['DIN','TN','TN_plus_DetNS12']):
                master_reaction_list.remove('NH4,dMinOONS12 (%s)' % units)
                master_reaction_list_trimmed.remove('NH4,dMinOONS12')
                minus_oons_rx_str = '\n- NH4,dMinOONS12'
                plus_oons_rx_str = '\n+ NH4,dMinOONS12'
            else:
                minus_oons_rx_str = ''
                plus_oons_rx_str = ''

            # loop through the runs, each one is a column in the figure
            for irun in range(nruns):

                # get the run id
                runid = runid_list[irun]

                ### SAN PABLO BAY INFLUX COMPONENTS ARE DIFFERENT FOR AGG AND FULL RES RUNS SO SET THEM HERE
                if 'FR' in runid:
                    influx_dir_dict['San_Pablo_Bay'] = influx_dir_dict['San_Pablo_Bay_FR']
                else:
                    influx_dir_dict['San_Pablo_Bay'] = influx_dir_dict['San_Pablo_Bay_AGG']
        
                # get the figure axis for this run
                if nruns>1:
                    ax_run = ax[:,irun]
                else:
                    ax_run = ax
        
                # get path to the balance table folder in the run folder
                run_base_dir = '/%svol1/hpcshared' % server_list[irun]
                run_dir = CVPL.get_run_dir(run_base_dir, runid)
                balance_table_dir = os.path.join(run_dir,'Balance_Tables')
                
                # load up the balance table data for the parameter of interest
                input_fn = os.path.join(balance_table_dir,'%s_Table_By_Group%s.csv' % (param.lower(), tavg_BT_str))
                data1 = pd.read_csv(input_fn)

                # also load up balance tables for the component parameters, and keep track of which components don't exist in this model 
                data1_components = []
                com_exists = []
                for ic in range(ncom):
                    input_fn = os.path.join(balance_table_dir,'%s_Table_By_Group%s.csv' % (components_list[ic].lower(), tavg_BT_str))
                    try:
                        data1_component = pd.read_csv(input_fn)
                    except:
                        data1_components.append(None)
                        com_exists.append(False)
                    else:
                        data1_components.append(data1_component)
                        com_exists.append(True)

                # get data from the group
                ind = data1['group'] == group_list[igroup]
                data = data1.loc[ind]
                data_components = []
                for ic in range(ncom):
                    if com_exists[ic]:
                        data_components.append(data1_components[ic].loc[ind])
                    else:
                        data_components.append(None)
                npts = len(data)
        
                # initialize influx and outflux data
                data_influx = np.zeros(npts)
                data_outflux = np.zeros(npts)
                data_influx_components = []
                data_outflux_components = []
                for ic in range(ncom):
                    if com_exists[ic]:
                        data_influx_components.append(np.zeros(npts))
                        data_outflux_components.append(np.zeros(npts))
                    else:
                        data_influx_components.append(None)
                        data_outflux_components.append(None)

                # add up the influxes using dictionary that gives list of connections that are influxes for this group
                for influx in influx_dir_dict[group_list[igroup]]:
                    
                    # each influx is a tuple giving the group, the side, and the mutliplier 
                    influx_group, influx_dir, influx_mult = influx
            
                    # add the influx, mutliplying by the multiplier to get the direction right
                    data_influx += influx_mult * data1.loc[data1['group'] == influx_group]['%s,Flux In from %s (%s)' % (param, influx_dir, units)].values
                    for ic in range(ncom):
                        if com_exists[ic]:
                            data_influx_components[ic] += influx_mult * data1_components[ic].loc[data1_components[ic]['group'] == influx_group]['%s,Flux In from %s (%s)' % (components_list[ic], influx_dir, units)].values

                # add up the outfluxed using dictionary that gives list of connections that are outfluxes for this group
                for outflux in outflux_dir_dict[group_list[igroup]]:
                
                    # each influx is a tuple giving the group, the side, and the mutliplier 
                    outflux_group, outflux_dir, outflux_mult = outflux
                
                    # add the influx, mutliplying by the multiplier to get the direction right
                    data_outflux += outflux_mult * data1.loc[data1['group'] == outflux_group]['%s,Flux In from %s (%s)' % (param, outflux_dir, units)].values
                    for ic in range(ncom):
                        if com_exists[ic]:
                            data_outflux_components[ic] += outflux_mult * data1_components[ic].loc[data1_components[ic]['group'] == outflux_group]['%s,Flux In from %s (%s)' % (components_list[ic], outflux_dir, units)].values
        
                # convert times from string to datetime64
                data['time'] = pd.to_datetime(data['time'])
                for ic in range(ncom):
                    if com_exists[ic]:
                        data_components[ic]['time'] = pd.to_datetime(data_components[ic]['time']).values
            
                # compute time step in days
                deltat = (data['time'].iloc[1] - data['time'].iloc[0])/np.timedelta64(1,'h')/24
        
                # generate a list of water years to plot from this run, based on the water year string
                # (this is confusing because for each item in the wystr_list we are generating another list
                wystr = wystr_list[irun]
                wy_list = CVPL.list_of_wy_str_2_list_of_int_wys([wystr]) 
        
                # get first and last date for time axis
                wymin = np.array(wy_list).min()
                wymax = np.array(wy_list).max()
                if tmin_override is None:
                    tmin = np.datetime64('%d-10-01' % (wymin-1))
                else:
                    tmin = tmin_override
                if tmax_override is None:
                    tmax = np.datetime64('%d-10-01' % wymax)
                else:
                    tmax = tmax_override
            
                # loop through the water years we are to plot for this run
                nwy = len(wy_list)
                for iwy in range(nwy):
                    
                    # get water year
                    wy = wy_list[iwy]
        
                    ## pick the time window based on water year
                    t_window = np.array(['%d-10-01' % (wy-1),'%d-10-01' % wy]).astype('datetime64')
            
                    # water year string
                    water_year = 'WY%d' % wy

                    # select the data in this time window (the "f" notation is a relic of when used to do the 
                    # spring-neap filtering in the plotting script)
                    ind = np.logical_and( data.time.values>=t_window[0], data.time.values<t_window[1])
                    dataf = data.loc[ind]
                    dataf_influx = data_influx[ind]
                    dataf_outflux = data_outflux[ind]
                    dataf_components = []
                    dataf_influx_components = []
                    dataf_outflux_components = []
                    for ic in range(ncom):
                        if com_exists[ic]:
                            dataf_components.append(data_components[ic].loc[ind])
                            dataf_influx_components.append(data_influx_components[ic][ind])
                            dataf_outflux_components.append(data_outflux_components[ic][ind])
                        else:
                            dataf_components.append(None)
                            dataf_influx_components.append(None)
                            dataf_outflux_components.append(None)

                    # get time
                    time = np.unique(dataf['time'].values)
                    ntime = len(time)

                    # if we are fudging the oons budget, isolate the oons mineralization term
                    if fudge_oons:
                        if param in ['DIN','TN','TN_plus_DetNS12']:
                            oons_rx = dataf['NH4,dMinOONS12 (%s)' % units].values

                    ########################################
                    # plot the mass budget for the group
                    ########################################
        
                    # first row of plot
                    irow = 0
                    irow_all = [irow]

                    # get stats for whole bay
                    Upstream_Influx = dataf_influx #dataf['%s,Flux In from E (%s)' % (param,units)].values
                    Downstream_Outflux = -dataf_outflux #dataf['%s,Flux In from W (%s)' % (param,units)].values
                    Minor_Trib_Influx = dataf['%s,Net Transport In (%s)' % (param,units)].values - Downstream_Outflux - Upstream_Influx
                    Storage = -dataf['%s,dMass/dt, Balance Check (%s)' % (param,units)].values
                    Net_Rx = dataf['%s,Net Reaction (%s)' % (param,units)].values
                    if fudge_oons: 
                        if param in ['DIN','TN','TN_plus_DetNS12']:
                            Net_Rx = Net_Rx - oons_rx
                    Net_Loading = dataf['%s,Net Load (%s)' % (param,units)].values
                    Influx_Plus_Tribs = Upstream_Influx + Minor_Trib_Influx
                    # do NOT add OONS min to net loading because track it separately
                    #if fudge_oons: 
                    #    if param in ['DIN','TN','TN_plus_DetNS12']:
                    #        Net_Loading = Net_Loading + oons_rx 
                    Net_Assimilation = -(Storage + Net_Rx)

                    # compute all the same things by components
                    Upstream_Influx_Com = np.zeros((ntime, ncom))
                    Downstream_Outflux_Com = np.zeros((ntime, ncom))
                    Minor_Trib_Influx_Com = np.zeros((ntime, ncom))
                    Storage_Com = np.zeros((ntime, ncom))
                    Net_Rx_Com = np.zeros((ntime, ncom))
                    Net_Loading_Com = np.zeros((ntime, ncom))
                    Influx_Plus_Tribs_Com = np.zeros((ntime, ncom))
                    Net_Assimilation_Com = np.zeros((ntime, ncom))
                    for icom in range(ncom):
                        if com_exists[icom]:
                            Upstream_Influx_Com[:,icom] = dataf_influx_components[icom]
                            Downstream_Outflux_Com[:,icom] = -dataf_outflux_components[icom]#dataf_components[icom].loc[ind]['%s,Flux In from W (%s)' % (components_list[icom],units)].values
                            Minor_Trib_Influx_Com[:,icom] = (dataf_components[icom]['%s,Net Transport In (%s)' % (components_list[icom],units)].values
                                                             - Downstream_Outflux_Com[:,icom] 
                                                             - Upstream_Influx_Com[:,icom] )
                            Storage_Com[:,icom] = -dataf_components[icom]['%s,dMass/dt, Balance Check (%s)' % (components_list[icom],units)].values
                            Net_Rx_Com[:,icom] = dataf_components[icom]['%s,Net Reaction (%s)' % (components_list[icom],units)].values
                            if fudge_oons:
                                if param in ['DIN','TN','TN_plus_DetNS12']:
                                    if components_list[icom]=='NH4':
                                        Net_Rx_Com[:,icom] = Net_Rx_Com[:,icom] - oons_rx
                            Net_Loading_Com[:,icom] = dataf_components[icom]['%s,Net Load (%s)' % (components_list[icom],units)].values
                            Influx_Plus_Tribs_Com[:,icom] = Upstream_Influx_Com[:,icom] + Minor_Trib_Influx_Com[:,icom] 
                            Net_Assimilation_Com[:,icom] = -(Storage_Com[:,icom] + Net_Rx_Com[:,icom])

                    # make a dataframe to contain statistics for the whole bay
                    df = pd.DataFrame(index=time)
                    if not is_it_benthic(param):
                        df['Point Sources'] = Net_Loading.copy()
                        df['Upstream Influx'] = Upstream_Influx.copy()
                        df['Minor Tribs'] = Minor_Trib_Influx.copy()
                        if fudge_oons:
                            if param in ['DIN','TN','TN_plus_DetNS12']:
                                df['NH4,dMinOONS12'] = oons_rx.copy()
                    df['-1 x Storage (-dM/dt)'] = Storage.copy()
                    df['Net Reaction%s' % minus_oons_rx_str] = Net_Rx.copy()
                    if not is_it_benthic(param):
                        df['Downstream Outflux'] = Downstream_Outflux.copy()

                    # make the colors match between benthic and not benthic plots
                    if is_it_benthic(param):
                        color_list = colors[3:5]
                    else:
                        color_list = colors
        
                    # divide into positive and negative
                    df_pos = df.copy(deep=True)
                    df_neg = df.copy(deep=True)
                    df_pos[df<0] = 0
                    df_neg[df>0] = 0
        
                    # add to figure
                    ax_run[irow].stackplot(time, df_pos.values.transpose()/divide_by, colors = color_list, labels=df.columns)
                    ax_run[irow].stackplot(time, df_neg.values.transpose()/divide_by, colors = color_list)
                    if iwy==0:
                        if irun==0:
                            ax_run[irow].set_ylabel('Mass Balance (%s)' % units_plot)
                        if irun==(nruns-1):
                            ax_run[irow].legend(loc='center left',bbox_to_anchor=(1, 0.5),ncol=2)

                    ################################
                    # reactions in next row of plot
                    ################################

                    irow += 1  
                    irow_all.append(irow)              

                    # make dataframe with reactions for whole bay
                    df = pd.DataFrame(columns=master_reaction_list)
                    for rx in master_reaction_list:
                        if rx in dataf.columns:
                            df[rx] = dataf[rx]
                    df = df.fillna(0)
                    df.columns = master_reaction_list_trimmed

                    # before adding storage, check reactions sum correctly
                    Net_Rx_Check_Sum = df.values.sum(axis=1)

                    # add storage
                    df['-1 x Storage (-dM/dt)'] = Storage.copy()

                    # divide into positive and negative
                    df_pos = df.copy(deep=True)
                    df_neg = df.copy(deep=True)
                    df_pos[df<0] = 0
                    df_neg[df>0] = 0
        
                    # add to figure 1
                    ax_run[irow].stackplot(time, df_pos.values.transpose()/divide_by, colors = colors[0:len(df.columns)], labels=df.columns)
                    ax_run[irow].stackplot(time, df_neg.values.transpose()/divide_by, colors = colors[0:len(df.columns)])
                    ax_run[irow].plot(time, Net_Rx/divide_by, 'b', label='Net Reaction%s' % minus_oons_rx_str, linewidth=linewidth)
                    #ax_run[irow].plot(time, Net_Rx_Check_Sum/divide_by, 'm--', label='Net Reaction, Check Sum', linewidth=linewidth)
                    if not is_it_benthic(param):
                        ax_run[irow].plot(time, (Net_Rx + Storage)/divide_by, 'k', label='-1 x Assimilation:\nNet Rx. - dM/dt%s' % minus_oons_rx_str, linewidth=linewidth)
                    if iwy==0:
                        if irun==0:
                            ax_run[irow].set_ylabel('Reactions (%s)' % units_plot)
                        if irun==(nruns-1):
                            ax_run[irow].legend(loc='center left',bbox_to_anchor=(1, 0.5),ncol=2)

                    # if not benthic, add influx, outflux, and assimilation by components
                    if not is_it_benthic(param):

                        ########################
                        # loading by components
                        ########################

                        irow += 1  
                        irow_inout = [irow]

                        # make a dataframe with influx plus loads components
                        df = pd.DataFrame(index=time)
                        for icom in range(ncom):
                            df[components_list[icom] + ' Load'] = Net_Loading_Com[:,icom]

                        if fudge_oons and (param in ['DIN','TN','TN_plus_DetNS12']):
                            df['NH4,dMinOONS12'] = oons_rx

                        # divide into positive and negative values
                        df_pos = df.copy(deep=True)
                        df_neg = df.copy(deep=True)
                        df_pos[df<0] = 0
                        df_neg[df>0] = 0
            
                        # add to figure 
                        ax_run[irow].stackplot(time, df_pos.values.transpose()/divide_by, colors = colors[0:len(df.columns)], labels=df.columns)
                        ax_run[irow].stackplot(time, df_neg.values.transpose()/divide_by, colors = colors[0:len(df.columns)])
                        ax_run[irow].plot(time,Net_Loading/divide_by, 'k', label='%s Load' % param, linewidth=linewidth)
                        #ax_run[irow].plot(time, -Downstream_Outflux/divide_by, 'k', label='%s Outflux\nThrough GG' % param, linewidth=linewidth)
                        if iwy==0:
                            if irun==0:
                                ax_run[irow].set_ylabel('Loads (%s)' % units_plot)
                            if irun==(nruns-1):
                                ax_run[irow].legend(loc='center left',bbox_to_anchor=(1, 0.5),ncol=2)

                        ########################
                        # influx by components
                        ########################

                        irow += 1  
                        irow_inout.append(irow)

                        # make a dataframe with influx plus loads components
                        df = pd.DataFrame(index=time)
                        for icom in range(ncom):
                            df[components_list[icom] + ' Influx'] = Upstream_Influx_Com[:,icom] + Minor_Trib_Influx_Com[:,icom]
            
                        # divide into positive and negative values
                        df_pos = df.copy(deep=True)
                        df_neg = df.copy(deep=True)
                        df_pos[df<0] = 0
                        df_neg[df>0] = 0
            
                        # add to figure 
                        ax_run[irow].stackplot(time, df_pos.values.transpose()/divide_by, colors = colors[0:len(df.columns)], labels=df.columns)
                        ax_run[irow].stackplot(time, df_neg.values.transpose()/divide_by, colors = colors[0:len(df.columns)])
                        ax_run[irow].plot(time,(Upstream_Influx+Minor_Trib_Influx)/divide_by, 'k', label='%s Influx' % param, linewidth=linewidth)
                        #ax_run[irow].plot(time, -Downstream_Outflux/divide_by, 'k', label='%s Outflux\nThrough GG' % param, linewidth=linewidth)
                        if iwy==0:
                            if irun==0:
                                ax_run[irow].set_ylabel('Upstream Influx\n+ Minor Tribs (%s)' % units_plot)
                            if irun==(nruns-1):
                                ax_run[irow].legend(loc='center left',bbox_to_anchor=(1, 0.5),ncol=2)


                        ########################
                        # outflux by components
                        ########################
                        
                        irow += 1  
                        irow_inout.append(irow)

                        # make a dataframe with outflux plus loads components
                        df = pd.DataFrame(index=time)
                        for icom in range(ncom):
                            #df[components_list[icom] + ' Outflux Through GG'] = -Downstream_Outflux_Com[:,icom]
                            df[components_list[icom] + ' Outflux'] = -Downstream_Outflux_Com[:,icom]
            
                        # divide into positive and negative values
                        df_pos = df.copy(deep=True)
                        df_neg = df.copy(deep=True)
                        df_pos[df<0] = 0
                        df_neg[df>0] = 0
            
                        # add to figure 
                        ax_run[irow].stackplot(time, df_pos.values.transpose()/divide_by, colors = colors[0:len(df.columns)], labels=df.columns)
                        ax_run[irow].stackplot(time, df_neg.values.transpose()/divide_by, colors = colors[0:len(df.columns)])
                        ax_run[irow].plot(time,-Downstream_Outflux/divide_by, 'k', label='%s Outflux' % param, linewidth=linewidth)
                        #ax_run[irow].plot(time, -Downstream_Outflux/divide_by, 'k', label='%s Outflux\nThrough GG' % param, linewidth=linewidth)
                        if iwy==0:
                            if irun==0:
                                ax_run[irow].set_ylabel('Downstream\nOutflux (%s)' % units_plot)
                            if irun==(nruns-1):
                                ax_run[irow].legend(loc='center left',bbox_to_anchor=(1, 0.5),ncol=2)


                        #############################
                        # assimilation by components
                        #############################
                        
                        irow += 1  
                        irow_all.append(irow)

                        # make a dataframe with outflux plus loads components
                        df = pd.DataFrame(index=time)
                        for icom in range(ncom):
                            #df[components_list[icom] + ' Outflux Through GG'] = -Downstream_Outflux_Com[:,icom]
                            if fudge_oons and (param in ['DIN','TN','TN_plus_DetNS12']) and components_list[icom] == 'NH4':
                                df[components_list[icom] + ' Assimilation%s' % plus_oons_rx_str] = Net_Assimilation_Com[:,icom]
                            else:
                                df[components_list[icom] + ' Assimilation'] = Net_Assimilation_Com[:,icom]
            
                        # divide into positive and negative values
                        df_pos = df.copy(deep=True)
                        df_neg = df.copy(deep=True)
                        df_pos[df<0] = 0
                        df_neg[df>0] = 0
            
                        # add to figure 
                        ax_run[irow].stackplot(time, df_pos.values.transpose()/divide_by, colors = colors[0:len(df.columns)], labels=df.columns)
                        ax_run[irow].stackplot(time, df_neg.values.transpose()/divide_by, colors = colors[0:len(df.columns)])
                        ax_run[irow].plot(time,Net_Assimilation/divide_by, 'k', label='%s Assimilation%s' % (param,plus_oons_rx_str), linewidth=linewidth)
                        #ax_run[irow].plot(time, -Downstream_Outflux/divide_by, 'k', label='%s Outflux\nThrough GG' % param, linewidth=linewidth)
                        if iwy==0:
                            if irun==0:
                                ax_run[irow].set_ylabel('Assimilation\ndM/dt - Net Rx. (%s)' % units_plot)
                            if irun==(nruns-1):
                                ax_run[irow].legend(loc='center left',bbox_to_anchor=(1, 0.5),ncol=2)

                # add label for run
                ax_run[0].set_title('Run %s' % runid)

                # format time axis for all rows
                if autoscale_x:
                    for ax1 in ax_run:
                        ax1.autoscale(enable=True, axis='x', tight=True)
                        ax1.grid(visible=True,which='both')
                    fig.autofmt_xdate()
                else:
                    for ax1 in ax_run:
                        ax1.set_xlim((tmin,tmax))
                        ax1.xaxis.set_major_locator(mdates.YearLocator())
                        ax1.xaxis.set_minor_locator(mdates.MonthLocator(bymonth=(1,4,7,10)))
                        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
                        ax1.grid(visible=True,which='both')

            # set y axis limits the same across runs
            # ... for first and 2nd rows (and last row if not benthic), make y axis symmetric around zero
            for irow in irow_all:
                if nruns==1:
                    ymax = np.abs(ax[irow].get_ylim()).max()
                    ax[irow].set_ylim((-ymax,ymax))
                else:
                    ymax = 0
                    for irun in range(nruns):
                        ymax1 = np.abs(ax[irow,irun].get_ylim()).max()
                        ymax = np.max([ymax,ymax1])
                    for irun in range(nruns):
                        ax[irow,irun].set_ylim((-ymax,ymax))
            # ... for loading, influx, and outflux, make y axes all the same, based on max/min
            if not is_it_benthic(param):
                ymax = 0
                ymin = 0
                for irow in irow_inout:
                    for irun in range(nruns):
                        ax[irow,irun].autoscale(enable=True, axis='y', tight=True) # first make the y axes tight
                for irow in irow_inout:
                    for irun in range(nruns):
                        ymax1 = np.max(ax[irow,irun].get_ylim())
                        ymax = np.max([ymax,ymax1])
                        ymin1 = np.min(ax[irow,irun].get_ylim())
                        ymin = np.min([ymin,ymin1])
                for irow in irow_inout:
                    for irun in range(nruns):
                        ax[irow,irun].set_ylim((ymin,ymax))

            # add title and save the figure
            fig.suptitle('%s %s %s Budget' % (group_labels[igroup], tavg_str, param))
            fig.tight_layout(rect=[0, 0.03, 1, 0.95])
            fig.savefig(os.path.join(figure_path, '%s_%s_In_Out_Stack_%s_%s_%s.png' % (run_list_str, wy_list_str, group_list[igroup], tavg, param)),dpi=300)
        
            # close figures
            plt.close('all')
        
