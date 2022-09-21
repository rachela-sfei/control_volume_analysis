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
from importlib import reload
import control_volume_plotting_library as CVPL # plotting library must be in same folder as this script
reload(CVPL)

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

# list or runs to plot and water years to pick out of corresponding run (each is a column in the plot)
# use 'WY13to18' to plot all years of a 6-year aggregated grid run, otherwise format should be 'WY2013', 'WY2018', etc.
#runid_list = ['G141_13to18_246','FR13_003','G141_13to18_246','FR17_003']
#wystr_list = ['WY2013','WY2013','WY2017','WY2017']
#runid_list = ['G141_13to18_246']
#wystr_list = ['WY13to18']
#runid_list = ['FR13_003']
#wystr_list = ['WY2013']
runid_list = ['FR17_003']
wystr_list = ['WY2017']


# list of parameters to plot (must match balance table, one plot per parameter is created)
param_list = ['DIN','TN','TN_include_sediment','OXY','TotalDetNS', 'Algae', 'Diat', 'Green','DiatS1']

# list of types of time aggregation (e.g. ['Filtered','Cumulative','Daily']) one plot per is created
tavg_list = ['Filtered','Cumulative']

# list of normalizations (divide by 'None','Area','Volume')
norm_list = ['Area']

# do you want to include mass in the figure? if so it will go in first row, but we skip this one for cumulative time aggregation
include_mass = True

# base directory for the model runs and the output figures (in theory should be able to run on windows laptop with mounted drives or on server)
#run_base_dir = r'X:\hpcshared'
run_base_dir = '/richmondvol1/hpcshared'
figure_base_dir = '/chicagovol1/hpcshared/open_bay/bgc/figures'

# number of runs (corresponds to number of columns)
nruns = len(runid_list)
assert nruns==len(wystr_list)

# width of figure and height of figure per row (number of rows is variable)
if 'WY13to18' in wystr_list: 
    fig_width = 7.5*(nruns+0.75)
else:
    fig_width = 4*(nruns+0.75)
row_height = 3

# start with the default color cycle and add even more colors because the number of reactions is OUT OF CONTROL!
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
          'fuchsia','gold','lawngreen','aqua','lavender','navy','lightgray']

# map variable to element (grams of what?)
element_dict = {}
element_dict['TN'] = 'N'
element_dict['TN_include_sediment'] = 'N'
element_dict['DIN'] = 'N'
element_dict['OXY'] = 'O'
element_dict['NO3'] = 'N'
element_dict['NH4'] = 'N'
element_dict['Algae'] = 'C'
element_dict['Diat'] = 'C'
element_dict['Green'] = 'C'
element_dict['DiatS1'] = 'C'
element_dict['Zoopl'] = 'C'

# tells you if the parameter is benthic (if it's benthic, don't include the transport plot, because it
# doesn't get transported, so everything is zero)
def is_it_benthic(param):

    if param in ['DetNS1','DetNS2','DetNS','OONS1','OONS2','OONS',
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
figure_path = os.path.join(figure_base_dir, run_list_str, 'aug2020_3panel')
if not os.path.exists(figure_path):
    os.makedirs(figure_path)
print('\nfigures will be saved here: %s\n' % figure_path)

# if group_list is set to 'all' or is otherwise not a list, take a sneak peek at one of the balance 
# tables and retrieve a list of all the spatial groups (hopefully this one exists)
if group_list == 'all':
    run_dir = CVPL.get_run_dir(run_base_dir, runid_list[0])
    balance_table_dir = os.path.join(run_dir,'Balance_Tables')
    data = pd.read_csv(os.path.join(balance_table_dir,'%s_Table_By_Group.csv' % param_list[0].lower()))
    group_list = list(np.unique(data.group))

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

        # column names for grabbing and plotting the terms we want to plot
        mass_closure_cols = ['%s,Net Load (%s)' % (param,units),
                         '%s,Net Reaction (%s)' % (param,units),
                         '%s,Net Transport In (%s)' % (param,units),
                         '%s,dMass/dt (%s)' % (param,units)]
        flux_cols = ['%s,Flux In from N (%s)' % (param,units),
                     '%s,Flux In from S (%s)' % (param,units),
                     '%s,Flux In from E (%s)' % (param,units),
                     '%s,Flux In from W (%s)' % (param,units)]

        # get storage column specifically so we can switch the sign
        storage_col = '%s,dMass/dt (%s)' % (param,units)

        # also get mass column
        mass_col = '%s,Mass (Mg)' % param

        # corresponding names for legend
        mass_closure_cols_trimmed = ['Net Load',
                                     'Net Reaction',
                                     'Net Transport In',
                                     '- dMass/dt']
        flux_cols_trimmed = ['Flux in from North',
                             'Flux in from South', 
                             'Flux in from East',
                             'Flux in from West']
    
        # before we plot the different runs, take a sneak peek to find a list of all the reactions, across 
        # all the runs
        master_source_cols = []
        master_sink_cols = []
        master_reaction_cols = []
        for irun in range(nruns):

            # get the run id
            runid = runid_list[irun]
    
            # get path to the balance table folder in the run folder
            run_dir = CVPL.get_run_dir(run_base_dir, runid)
            balance_table_dir = os.path.join(run_dir,'Balance_Tables')
            
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
                            if data[col].mean()>0:
                                source_cols.append(col)
                            elif data[col].mean()<0:
                                sink_cols.append(col)

            # add to master list
            for rx in source_cols:
                if not rx in master_source_cols:
                    master_source_cols.append(rx)
            for rx in sink_cols:
                if not rx in master_sink_cols:
                    master_sink_cols.append(rx)
    
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

            # loop through the gropus
            for group in group_list:

                # boolean to say if you should save the figure (if can't find this group for some of the runs, skip it)
                plot_this_one = True

                # compute number of rows for the figure, then initialize figure
                nrows = 2
                if not is_it_benthic(param):
                    nrows += 1
                if include_mass and (not tavg=='Cumulative'):
                    nrows += 1
                fig, ax = plt.subplots(nrows,nruns,figsize=(fig_width, nrows*row_height))
                  
                # loop through the runs, each one is a column in the figure
                was_there_data = np.zeros(nruns,dtype=bool)
                for irun in range(nruns):
        
                    # get the figure axis for this run
                    if nruns>1:
                        ax_run = ax[:,irun]
                    else:
                        ax_run = ax
        
                    # get the run id
                    runid = runid_list[irun]
            
                    # get path to the balance table folder in the run folder
                    run_dir = CVPL.get_run_dir(run_base_dir, runid)
                    balance_table_dir = os.path.join(run_dir,'Balance_Tables')
                    
                    # load up the balance table data for the parameter of interest
                    input_fn = os.path.join(balance_table_dir,'%s_Table_By_Group%s.csv' % (param.lower(), tavg_BT_str))
                    try:
                        data = pd.read_csv(input_fn)
                    except:
                        print('could not open %s\nit probably doesn''t exist, skipping this one' % input_fn)
                    else:
                        was_there_data[irun] = True

                    # get the list of columns we want to normalize (anythign with Mg in the name)
                    if was_there_data[irun]:
                        norm_cols = []
                        for col in data.columns:
                            if 'Mg' in col:
                                norm_cols.append(col)

                    # if normalized, divide and change units
                    if norm == 'None':
                        units_label = '%s %s' % (units, element_dict[param])
                        units_mass_label = 'Mg %s' % element_dict[param]
                        label_mass = 'Mass'
                        norm_name = ''
                    elif norm == 'Area':
                        if was_there_data[irun]:
                            for col in norm_cols:
                                data[col] = data[col] / data['Area (m^2)'] * 1e6
                        units_label = '%s/m$^2$ %s' % (units.replace('M',''),element_dict[param])
                        units_mass_label = 'g %s/m$^2$' % element_dict[param]
                        label_mass = 'Mass per Area'
                        norm_name = '_Per_Area'
                    elif norm == 'Volume':
                        if was_there_data[irun]:
                            for col in norm_cols:
                                data[col] = data[col] / data['Volume (Mean, m^3)'] * 1e6
                        units_label = '%s/m$^3$ %s' % (units.replace('M',''),element_dict[param])
                        units_mass_label = 'g %s/m$^3$' % element_dict[param]
                        label_mass = 'Concentration'
                        norm_name = '_Per_Volume'

                    
                    if was_there_data[irun]:

                        # find indices of data in this group
                        ind = data['group'] == group

                        # if you can't find any data in this group, throw the skip plot flag and continue
                        if not np.any(ind):
                            plot_this_one = False
                            continue

                        # select data in this group
                        data_group = data.loc[ind].copy()
            
                        # convert times from string to datetime64
                        data_group['time'] = pd.to_datetime(data_group['time'])
                
                        # compute time step in days
                        deltat = (data_group['time'].iloc[1] - data_group['time'].iloc[0])/np.timedelta64(1,'h')/24

                        # find the area and volume of the group
                        area_km2 = np.mean(data_group['Area (m^2)'].values)/1000/1000
                        volume_km2xm = np.mean(data_group['Volume (Mean, m^3)'].values)/1000/1000
            
                    # generate a list of water years to plot from this run, based on the water year string
                    # (this is confusing because for each item in the wystr_list we are generating another list
                    wystr = wystr_list[irun]
                    wy_list = CVPL.list_of_wy_str_2_list_of_int_wys([wystr]) 
            
                    # get first and last date for time axis
                    wymin = np.array(wy_list).min()
                    wymax = np.array(wy_list).max()
                    tmin = np.datetime64('%d-10-01' % (wymin-1))
                    tmax = np.datetime64('%d-10-01' % wymax)
                
                    # loop through the water years we are to plot for this run
                    nwy = len(wy_list)
                    for iwy in range(nwy):
                        
                        # get water year
                        wy = wy_list[iwy]
            
                        ## pick the time window based on water year
                        t_window = np.array(['%d-10-01' % (wy-1),'%d-10-01' % wy]).astype('datetime64')
                
                        # water year string
                        water_year = 'WY%d' % wy
        
                        if was_there_data[irun]:

                            # select the data in this time window (the "f" notation is a relic of when used to do the 
                            # spring-neap filtering in the plotting script)
                            ind = np.logical_and( data_group.time>=t_window[0], data_group.time<t_window[1])
                            dataf = data_group.loc[ind]
                
                            # get time
                            time = np.unique(dataf['time'].values)
                            ntime = len(time)

                        ########################################
                        # initialize the row counter
                        ########################################

                        irow = 0

                        ########################################
                        # plot the mass (skip if cumulative)
                        ########################################
            
                        row_mass = None
                        if include_mass and (not tavg=='Cumulative'):

                            if was_there_data[irun]:
                                ax_run[irow].plot(time, dataf[mass_col], color=colors[0])
                            if irun==0:
                                ax_run[irow].set_ylabel('%s\n(%s)' % (label_mass,units_mass_label))

                            row_mass = irow
                            irow += 1

                        ########################################
                        # plot the mass budget
                        ########################################
            
                        if was_there_data[irun]:

                            # make a dataframe to contain mass closure stuff
                            df = dataf[mass_closure_cols].copy()
        
                            # flip the sign of the storage term
                            df[storage_col] = -df[storage_col].values
                
                            # rename the columns so units don't appear in legend
                            df.columns = mass_closure_cols_trimmed
        
                            # divide into positive and negative
                            df_pos = df.copy(deep=True)
                            df_neg = df.copy(deep=True)
                            df_pos[df<0] = 0
                            df_neg[df>0] = 0
                
                            # add to figure
                            ax_run[irow].stackplot(time, df_pos.values.transpose(), colors = colors[0:len(df.columns)], labels=df.columns)
                            ax_run[irow].stackplot(time, df_neg.values.transpose(), colors = colors[0:len(df.columns)])

                        if iwy==0:

                            if irun==0:
                                ax_run[irow].set_ylabel('Rates in Mass Balance\n(%s)' % (units_label))
                            if irun==(nruns-1):

                                # it is very tricky to get the legend info if the last column doesn't have data, this finds the 
                                # axis handle for the last column that had data and uses its contents to put the legend in the last 
                                # column
                                irun1 = np.argmax(was_there_data)
                                if nruns>1:
                                    ax_run1 = ax[:,irun1]
                                else:
                                    ax_run1 = ax
                                handles, labels = ax_run1[irow].get_legend_handles_labels()

                                # put the legend in the last column, but with contents based on first column that had data
                                ax_run[irow].legend(handles, labels, loc='center left',bbox_to_anchor=(1, 0.5))

                        row_budget = irow
                        irow += 1
        
                        ############################################
                        # plot the transport terms (if not benthic)
                        ############################################

                        row_transport = None
                        if not is_it_benthic(param):

                            if was_there_data[irun]:

                                # make a dataframe to contain transport stuff
                                df = dataf[flux_cols].copy()
                    
                                # rename the columns so units don't appear in legend
                                df.columns = flux_cols_trimmed
    
                                # compute then add the net transport and the minor tributary loading
                                net_flux_NSEW = df.values.sum(axis=1)
                                net_transport_in = dataf['%s,Net Transport In (%s)' % (param,units)].values
                                df['Tributary Inputs'] = net_transport_in - net_flux_NSEW
                    
                                # add to figure
                                ax_run[irow].plot(time, net_transport_in, color='k', label='Net Transport In')
                                for col, color in zip(df.columns,colors):
                                    ax_run[irow].plot(time, df[col], color=color, label=col)

                            if iwy==0:
                                if irun==0:
                                    ax_run[irow].set_ylabel('Transport Fluxes\n(%s)' % (units_label))
                                if irun==(nruns-1):
                                    
                                    # it is very tricky to get the legend info if the last column doesn't have data, this finds the 
                                    # axis handle for the last column that had data and uses its contents to put the legend in the last 
                                    # column
                                    irun1 = np.argmax(was_there_data)
                                    if nruns>1:
                                        ax_run1 = ax[:,irun1]
                                    else:
                                        ax_run1 = ax
                                    handles, labels = ax_run1[irow].get_legend_handles_labels()
    
                                    # put the legend in the last column, but with contents based on first column that had data
                                    ax_run[irow].legend(handles, labels, loc='center left',bbox_to_anchor=(1, 0.5))
    
                            row_transport = irow
                            irow += 1

                        ############################################
                        # plot the reaction terms 
                        ############################################

                        if was_there_data[irun]:

                            # make dataframe with reactions for whole bay
                            df = pd.DataFrame(columns=master_reaction_cols)
                            for rx in master_reaction_cols:
                                if rx in dataf.columns:
                                    df[rx] = dataf[rx].copy()
                            df = df.fillna(0)
                            df.columns = master_reaction_cols_trimmed
    
                            # compute net reaction
                            net_rx = df.values.sum(axis=1)
            
                            # divide into positive and negative
                            df_pos = df.copy(deep=True)
                            df_neg = df.copy(deep=True)
                            df_pos[df<0] = 0
                            df_neg[df>0] = 0
                
                            # add to figure 
                            ax_run[irow].stackplot(time, df_pos.values.transpose(), colors = colors[0:len(df.columns)], labels=df.columns)
                            ax_run[irow].stackplot(time, df_neg.values.transpose(), colors = colors[0:len(df.columns)])
                            ax_run[irow].plot(time, net_rx, color='k', label = 'Net Reaction')

                        if iwy==0:
                            if irun==0:
                                ax_run[irow].set_ylabel('Reactions\n(%s)' % (units_label))
                            if irun==(nruns-1):

                                # it is very tricky to get the legend info if the last column doesn't have data, this finds the 
                                # axis handle for the last column that had data and uses its contents to put the legend in the last 
                                # column
                                irun1 = np.argmax(was_there_data)
                                if nruns>1:
                                    ax_run1 = ax[:,irun1]
                                else:
                                    ax_run1 = ax
                                handles, labels = ax_run1[irow].get_legend_handles_labels()

                                # put the legend in the last column, but with contents based on first column that had data
                                ax_run[irow].legend(handles, labels, loc='center left',bbox_to_anchor=(1, 0.5))

                        # row corresponding to reactions
                        row_rx = irow

            
                    # add label for run
                    ax_run[0].set_title('Run %s\nGroup Area = %0.0f km$^2$\nGroup Volume = %0.0f km$^2$ x m' % (runid, area_km2, volume_km2xm))
        
                    # format time axis for all rows
                    for ax1 in ax_run:
                        ax1.set_xlim((tmin,tmax))
                        ax1.xaxis.set_major_locator(mdates.YearLocator())
                        ax1.xaxis.set_minor_locator(mdates.MonthLocator(bymonth=(1,4,7,10)))
                        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
                        ax1.grid(visible=True,which='both')

                # if group was found in all runs, go ahead and finish up the plot and save it
                if plot_this_one:

                    # set y axis limits the same across runs
                    # ... for mass row set min at zero
                    for irow in [row_mass]:
                        if not irow is None:
                            if nruns==1:
                                ymax = np.abs(ax[irow].get_ylim()).max()
                                ax[irow].set_ylim((0,ymax))
                            else:
                                ymax = 0
                                for irun in range(nruns):
                                    if was_there_data[irun]:
                                        ymax1 = np.abs(ax[irow,irun].get_ylim()).max()
                                        ymax = np.max([ymax,ymax1])
                                for irun in range(nruns):
                                    ax[irow,irun].set_ylim((0,ymax))
    
                    # ... for first and 2nd rows, make y axis symmetric around zero
                    for irow in [row_budget, row_transport, row_rx]:
                        if not irow is None:
                            if nruns==1:
                                ymax = np.abs(ax[irow].get_ylim()).max()
                                ax[irow].set_ylim((-ymax,ymax))
                            else:
                                ymax = 0
                                for irun in range(nruns):
                                    if was_there_data[irun]:
                                        ymax1 = np.abs(ax[irow,irun].get_ylim()).max()
                                        ymax = np.max([ymax,ymax1])
                                for irun in range(nruns):
                                    ax[irow,irun].set_ylim((-ymax,ymax))
    
                    # get the string to describe the group
                    if nice_names is None:
                        group_str = group
                    else:
                        group_str = nice_names[group]
            
                    # add title and save the figure
                    fig.suptitle('%s %s Budget\nGroup = %s' % (tavg_str, param, group_str))
                    fig.tight_layout(rect=[0, 0, 1, 0.975])
                    figure_fn = '%s_%s_Aug2020_3panel_%s%s_Group=%s_%s.png' % (run_list_str, wy_list_str, tavg, norm_name, group, param)
                    fig.savefig(os.path.join(figure_path, figure_fn))
                
                    # close figures
                    plt.close('all')
    
