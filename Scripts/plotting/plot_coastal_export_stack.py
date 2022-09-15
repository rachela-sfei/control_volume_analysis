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
from importlib import reload
import control_volume_plotting_library as CVPL # plotting library must be in same folder as this script
reload(CVPL)


#########################################################################################
## user input
#########################################################################################

# list or runs to plot and water year to pick out of corresponding run (each is a column in the plot)
#runid_list = ['G141_13to18_247']
runid_list = ['FR17_003']

# this is the list of water years to zoom in on within each plot, should be the same length as runid_list
# use 'WY13to18' to plot all years of a 6-year aggregated grid run, otherwise format should be 'WY2013', 'WY2018', etc.
#wystr_list = ['WY13to18','WY13to18']
#wystr_list = ['WY13to18']
wystr_list = ['WY2017']

## composite parameter (must match suffix of balance table)
param_list = ['DIN','TN','TN_include_sediment']

# list of types of time aggregation (e.g. ['Filtered','Cumulative','Daily'])
tavg_list = ['Daily','Filtered','Cumulative']

# base directory for the model runs and the output figures (in theory should be able to run on windows laptop with mounted drives or on server)
#run_base_dir = r'X:\hpcshared'
run_base_dir = '/richmondvol1/hpcshared'
figure_base_dir = '/chicagovol1/hpcshared/open_bay/bgc/figures'

# number of runs (corresponds to number of columns)
nruns = len(runid_list)
assert nruns==len(wystr_list)

# figure size for (3 rows) x (nruns columns) mass budget plot 
# (make figure wider to accomodate multi-year run -- same plot 
# window width will be used for each run in current version of code)
# add one to number of runs to accomodate the legend, which is quite large
if 'WY13to18' in wystr_list: 
    fs = (7.5*(nruns+1),10)
else:
    fs = (5*(nruns+1),10)

# start with the default color cycle and add even more colors because the number of reactions is OUT OF CONTROL!
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
          'fuchsia','gold','lawngreen','aqua','lavender','navy','lightgray']

# finction to list of components OF THE COASTAL EXPORT (need not include benthic components, 
# because they can't flow out of the bay as they are stuck to the bed) given the parameter
def return_components_list(param):

    if param == 'DIN':
        components_list = ['NH4','NO3']
    elif param == 'TN':
        components_list = ['NH4','NO3','PON1','PON2','DON','N-Zoopl','N-Algae'] 
    elif param == 'TN_include_sediment':
        components_list = ['NH4','NO3','PON1','PON2','DON','N-Zoopl','N-Algae'] 
    else:
        components_list = [param]
    ncom = len(components_list)

    return components_list, ncom

# time axis formatting (label start of year put grid line every 4 months)
major_locator = mdates.YearLocator()
minor_locator = mdates.MonthLocator(bymonth=(1,4,7,10))
major_formatter = mdates.DateFormatter('%Y')

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
figure_path = os.path.join(figure_base_dir, run_list_str, 'coastal_export')
if not os.path.exists(figure_path):
    os.makedirs(figure_path)

# loop through parameters
for param in param_list:

    # get list of components for this parameter
    components_list, ncom = return_components_list(param)
    
    # loop through different time averages: daily, spring-neap filter, cumulative
    for tavg in tavg_list:
    
        # initialize 3 panel figure with complete mass balance, reactions, and export composition
        fig, ax = plt.subplots(3,nruns,figsize=fs)
    
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
        else:
            units = 'Mg/d'
    
        # before we plot the different runs, take a sneak peek to find a list of all the reactions
        master_source_list = []
        master_sink_list = []
        master_reaction_list = []
        for irun in range(nruns):

            # get the run id
            runid = runid_list[irun]
    
            # get path to the balance table folder in the run folder
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

        # loop through the runs, each one is a column in the figure
        for irun in range(nruns):
    
            # print run
            print('run %d of %d' % (irun+1,nruns))
    
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
            data = pd.read_csv(input_fn)
    
            # also load up balance tables for the component parameters 
            data_components = []
            for ic in range(ncom):
                input_fn = os.path.join(balance_table_dir,'%s_Table_By_Group%s.csv' % (components_list[ic].lower(), tavg_BT_str))
                try:
                    data_component = pd.read_csv(input_fn)
                except:
                    data_components.append(None)
                else:
                    data_components.append(data_component)
    
            # select 'Whole_Bay' group
            ind = data['group'] == 'Whole_Bay'
            data = data.loc[ind]
            for ic in range(ncom):
                if not data_components[ic] is None:
                    data_components[ic] = data_components[ic].loc[ind]
    
            # convert times from string to datetime64
            data['time'] = pd.to_datetime(data['time'])
            for ic in range(ncom):
                if not data_components[ic] is None:
                    data_components[ic]['time'] = pd.to_datetime(data_components[ic]['time'])
        
            # compute time step in days
            deltat = (data['time'].iloc[1] - data['time'].iloc[0])/np.timedelta64(1,'h')/24
    
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

                # select the data in this time window (the "f" notation is a relic of when used to do the 
                # spring-neap filtering in the plotting script)
                ind = np.logical_and( data.time>=t_window[0], data.time<t_window[1])
                dataf = data.loc[ind]
                dataf_components = []
                for ic in range(ncom):
                    if not data_components[ic] is None:
                        dataf_components.append(data_components[ic].loc[ind])
                    else:
                        dataf_components.append(None)
    
                # get time
                time = np.unique(dataf['time'].values)
                ntime = len(time)
    
                ########################################
                # plot the mass budget for the whole bay
                ########################################
    
                # get stats for whole bay
                Delta_Influx = dataf['%s,Flux In from E (%s)' % (param,units)].values
                GG_Outflux = dataf['%s,Flux In from W (%s)' % (param,units)].values
                Minor_Trib_Influx = dataf['%s,Net Transport In (%s)' % (param,units)].values - GG_Outflux - Delta_Influx
                Storage = -dataf['%s,dMass/dt, Balance Check (%s)' % (param,units)].values
                Net_Rx = dataf['%s,Net Reaction (%s)' % (param,units)].values
                Net_Loading = dataf['%s,Net Load (%s)' % (param,units)].values
                Tribs_Plus_Loads = Delta_Influx + Minor_Trib_Influx + Net_Loading
    
                # golden gate outflux by components
                GG_Outflux_Com = np.zeros((ntime, ncom))
                for icom in range(ncom):
                    if not dataf_components[icom] is None:
                        ind = dataf_components[icom]['group'].values == 'Whole_Bay'
                        GG_Outflux_Com[:,icom] = dataf_components[icom].loc[ind]['%s,Flux In from W (%s)' % (components_list[icom],units)].values
    
                # make a dataframe to contain statistics for the whole bay
                df = pd.DataFrame(index=time)
                df['Point Sources'] = Net_Loading.copy()
                df['Delta Influx'] = Delta_Influx.copy()
                df['Minor Tribs'] = Minor_Trib_Influx.copy()
                df['Storage (-dM/dt)'] = Storage.copy()
                df['Net Reaction'] = Net_Rx.copy()
                df['Golden Gate Outflux'] = GG_Outflux.copy()
    
                # divide into positive and negative
                df_pos = df.copy(deep=True)
                df_neg = df.copy(deep=True)
                df_pos[df<0] = 0
                df_neg[df>0] = 0
    
                # add to figure
                ax_run[0].stackplot(time, df_pos.values.transpose(), colors = colors[0:len(df.columns)], labels=df.columns)
                ax_run[0].stackplot(time, df_neg.values.transpose(), colors = colors[0:len(df.columns)])
                if iwy==0:
                    if irun==0:
                        ax_run[0].set_ylabel('Whole Bay Mass Balance (%s)' % units)
                    if irun==(nruns-1):
                        ax_run[0].legend(loc='center left',bbox_to_anchor=(1, 0.5))

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
                df['Storage (-dM/dt)'] = Storage.copy()

                # divide into positive and negative
                df_pos = df.copy(deep=True)
                df_neg = df.copy(deep=True)
                df_pos[df<0] = 0
                df_neg[df>0] = 0
    
                # add to figure 1
                ax_run[1].stackplot(time, df_pos.values.transpose(), colors = colors[0:len(df.columns)], labels=df.columns)
                ax_run[1].stackplot(time, df_neg.values.transpose(), colors = colors[0:len(df.columns)])
                ax_run[1].plot(time, Net_Rx, 'k', label='Net Reaction')
                ax_run[1].plot(time, Net_Rx_Check_Sum, 'm--', label='Net Reaction, Check Sum')
                ax_run[1].plot(time, Net_Rx + Storage, 'b', label='Net Reaction - dM/dt')
                if iwy==0:
                    if irun==0:
                        ax_run[1].set_ylabel('Whole Bay Reactions (%s)' % units)
                    if irun==(nruns-1):
                        ax_run[1].legend(loc='center left',bbox_to_anchor=(1, 0.5))
            
                # make a dataframe with GG outflux components
                df = pd.DataFrame(index=time)
                for icom in range(ncom):
                    df[components_list[icom] + ' Outflux Through GG'] = -GG_Outflux_Com[:,icom]
    
                # divide into positive and negative values
                df_pos = df.copy(deep=True)
                df_neg = df.copy(deep=True)
                df_pos[df<0] = 0
                df_neg[df>0] = 0
    
                # add to figure 3
                ax_run[2].stackplot(time, df_pos.values.transpose(), colors = colors[0:len(df.columns)], labels=df.columns)
                ax_run[2].stackplot(time, df_neg.values.transpose(), colors = colors[0:len(df.columns)])
                ax_run[2].plot(time,Tribs_Plus_Loads, 'k--', label='%s Loading from Tribs and Point Sources' % param)
                ax_run[2].plot(time, -GG_Outflux, 'k', label='%s Outflux Through GG' % param)
                if iwy==0:
                    if irun==0:
                        ax_run[2].set_ylabel('Whole Bay Influx vs. Outflux (%s)' % units)
                    if irun==(nruns-1):
                        ax_run[2].legend(loc='center left',bbox_to_anchor=(1, 0.5))
    
            # add label for run
            ax_run[0].set_title('Run %s' % runid)
    
            # format time axis for all 3 rows
            for ax1 in ax_run:
                ax1.set_xlim((tmin,tmax))
                ax1.xaxis.set_major_locator(major_locator)
                ax1.xaxis.set_minor_locator(minor_locator)
                ax1.xaxis.set_major_formatter(major_formatter)
                ax1.grid(which='both')

        # set y axis limits the same across runs
        # ... for first and 2nd rows, make y axis symmetric around zero
        for irow in [0,1]:
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
        # ... for 3rd row set min at zero
        for irow in [2]:
            if nruns==1:
                ymax = np.abs(ax[irow].get_ylim()).max()
                ax[irow].set_ylim((0,ymax))
            else:
                ymax = 0
                for irun in range(nruns):
                    ymax1 = np.abs(ax[irow,irun].get_ylim()).max()
                    ymax = np.max([ymax,ymax1])
                for irun in range(nruns):
                    ax[irow,irun].set_ylim((0,ymax))

        # add title and save the figure
        fig.suptitle('Whole Bay %s %s Budget' % (tavg_str, param))
        fig.tight_layout(rect=[0, 0.03, 1, 0.95])
        fig.savefig(os.path.join(figure_path, '%s_%s_%s_Coastal_Export_Stackplot_%s.png' % (run_list_str, wy_list_str, param, tavg)),dpi=300)
    
        # close figures
        plt.close('all')
    
