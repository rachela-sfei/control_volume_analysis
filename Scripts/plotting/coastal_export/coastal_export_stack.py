'''

Use new "Whole_Bay" group to work up budget

This creates a four panel plot with the following panels
- bay-wide DIN Loading
- Delta influx (net flux in from the W)
- assimilation (net Rx term)
- outflux throguh Golden Gate (net flux in from the E)

Multiple water years are plotted together, based on full resoluation runs

July 2020 update w/ new "Whole Bay" CV that includes fluxes in from SPB

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
#plt.switch_backend("Agg")


#########################################################################################
## user input
#########################################################################################


# list or runs to plot and water year to pick out of corresponding run (each is a column in the plot)
run2plot_list = ['G141_13to18_197','G141_13to18_207']

# this is the list of water years to zoom in on within each plot, should be the same length as run2plot_list
# use 'WY13to18' to plot all years of a 6-year aggregated grid run, otherwise format should be 'WY2013', 'WY2018', etc.
wystr_list = ['WY13to18', 'WY13to18']

## composite parameter (must match suffix of balance table)
param_list = ['DIN','TN','TN_include_sediment']

# base directory (depends if running from laptop or on an hpc)
#base_dir = r'X:\hpcshared'
#base_dir = '/richmondvol1/hpcshared'
base_dir = '/chicagovol1/hpcshared'

# output folder path
if all(np.array(run2plot_list)==run2plot_list[0]):
    out_dir = os.path.join(base_dir,'NMS_Projects','Control_Volume_Analysis','Plots',run2plot_list[0],'coastal_export')
else:
    out_dir = os.path.join(base_dir,'NMS_Projects','Control_Volume_Analysis','Plots','Compare_Water_Years','coastal_export')

# number of runs (corresponds to number of columns)
nruns = len(run2plot_list)
assert nruns==len(wystr_list)

# figure size for (3 rows) x (nruns columns) mass budget plot 
# (make figure wider to accomodate multi-year run -- same plot 
# window width will be used for each run in current version of code)
if 'WY13to18' in wystr_list: 
    fs = (7.5*nruns,10)
else:
    fs = (5*nruns,10)

# default color cycle
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']

# finction to list of components OF THE COASTAL EXPORT (need not include benthic components) given the parameter
def return_components_list(param):

    if param == 'DIN':
        components_list = ['NH4','NO3']
    elif param == 'TN':
        components_list = ['NH4','NO3','PON1','DON','N-Zoopl','N-Algae'] 
    elif param == 'TN_include_sediment':
        components_list = ['NH4','NO3','PON1','DON','N-Zoopl','N-Algae'] 
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

def spring_neap_filter(y, dt_days = 1.0, fcut = 1/36., N = 6):

    """
    Performs a spring-neap filter on the y series using a 6th order low pass
    butterworth filter and constant padding
   
    Usage:
       
        yf = spring_neap_filter(y, dt_days=1.0, fcut = 1/36.)
       
    Input:
       
        y    = time series
        dt_days   = time step (unit is days)
        fcut = cutoff frequency in 1/days
               
    Output:
   
        yf   = tidally filtered signal
   
    """
   
    # compute sampling frequency from time step
    fs = 1/dt_days
   
    # compute dimensionless cutoff frequency w.r.t. Nyquist frequency
    Wn = fcut/(0.5*fs)
    # compute filter coefficients
    b, a = signal.butter(N, Wn, 'low')
   
    # filter the signal
    yf = signal.filtfilt(b,a,y,padtype='constant')
   
    # return fitlered signal
    return yf

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

# make a kind of confusing figure prefix with list of runs and water years
sameruns = all(run2plot_list[0]==np.array(run2plot_list))
samewys = all(wystr_list[0]==np.array(wystr_list))
if sameruns:
    fig_pref = run2plot_list[0] + '_'
    if not samewys:
        for wystr in wystr_list:
            fig_pref += wystr + '_'
else:
    fig_pref = ''
    for (run_ID,wystr) in zip(run2plot_list,wystr_list):
        fig_pref += run_ID + '_'
        if not samewys:
            fig_pref += wystr + '_'
if samewys:
    fig_pref += wystr_list[0] + '_'
fig_pref = fig_pref[0:-1]

# check if plot directory exists and create it if not
if not os.path.exists(out_dir):
    os.makedirs(out_dir)

# loop through parameters
for param in param_list:

    # get list of components for this parameter
    components_list, ncom = return_components_list(param)
    
    # loop through different time averages: daily, spring-neap filter, cumulative
    for tavg in ['Filtered','Cumulative','Daily']:
    
        # initialize 3 panel figure with complete mass balance, reactions, and export composition
        fig, ax = plt.subplots(3,nruns,figsize=fs)
    
        # for figure labeling
        if tavg=='Filtered':
            tavg_str = 'Spring-Neap Filtered'
        else:
            tavg_str = tavg
    
        # loop through the runs, each one is a column in the figure
        for irun in range(nruns):
    
            # print run
            print('run %d of %d' % (irun,nruns))
        
            # get the run id
            run2plot = run2plot_list[irun]
    
            ## balance table folder
            table_dir = os.path.join(base_dir,'NMS_Projects','Control_Volume_Analysis','Balance_Tables',run2plot)
            
            # load up the balance table data for the parameter of interest
            input_fn = os.path.join(table_dir,'%s_Table_By_Group.csv' % param.lower())
            data = pd.read_csv(input_fn)
    
            # also load up balance tables for the component parameters 
            data_components = []
            for ic in range(ncom):
                input_fn = os.path.join(table_dir,'%s_Table_By_Group.csv' % components_list[ic].lower())
                data_components.append(pd.read_csv(input_fn))
    
            # select 'Whole_Bay' group
            ind = data['group'] == 'Whole_Bay'
            data = data.loc[ind]
            for ic in range(ncom):
                data_components[ic] = data_components[ic].loc[ind]
    
            # convert times from string to datetime64
            data['time'] = pd.to_datetime(data['time'])
            for ic in range(ncom):
                data_components[ic]['time'] = pd.to_datetime(data_components[ic]['time'])
        
            # compute time step in days
            deltat = (data['time'].iloc[1] - data['time'].iloc[0])/np.timedelta64(1,'h')/24
    
            # generate a list of water years to plot from this run, based on the water year string
            # (this is confusing because for each item in the wystr_list we are generating another list, 
            # also this won't work for any multi year run except WY13to18)
            wystr = wystr_list[irun]
            if wystr=='WY13to18':
                wy_list = [2013,2014,2015,2016,2017,2018]
            else:
                wy_list = [int(wystr[2:])]
    
            # get first and last date for time axis
            wymin = np.array(wy_list).min()
            wymax = np.array(wy_list).max()
            tmin = np.datetime64('%d-10-01' % (wymin-1))
            tmax = np.datetime64('%d-10-01' % wymax)
        
            # for the first run, get list of sources and sinks, and the list of columns we want to apply the tidal filter to
            if irun == 0:
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
                reaction_list = []
                for rx in sink_list:
                    reaction_list.append(rx)
                for rx in source_list:
                    reaction_list.append(rx)
    
                source_list_trimmed = []
                for rx in source_list:
                    source_list_trimmed.append(rx.replace(' (Mg/d)',''))
                sink_list_trimmed = []
                for rx in sink_list:
                    sink_list_trimmed.append(rx.replace(' (Mg/d)',''))
                reaction_list_trimmed = []
                for rx in reaction_list:
                    reaction_list_trimmed.append(rx.replace(' (Mg/d)',''))
    
                # get subset of column names we want to apply tidal filter and cumulative sum on
                filt_cols = np.array(data.columns)
                filt_cols = filt_cols[~('Area (m^2)' == filt_cols)]
                filt_cols = filt_cols[~('time'==filt_cols)]
                filt_cols = filt_cols[~('group'==filt_cols)]
                filt_cols_components = []
                for ic in range(ncom):
                    filt_cols_components.append(data_components[ic].columns)
                    filt_cols_components[ic] = filt_cols_components[ic][~('Area (m^2)' == filt_cols_components[ic])]
                    filt_cols_components[ic] = filt_cols_components[ic][~('time'==filt_cols_components[ic])]
                    filt_cols_components[ic] = filt_cols_components[ic][~('group'==filt_cols_components[ic])]
        
            # replace the first loading value (which is zero) with the second loading value ...
            # this is because sometimes the loading starts out at zero and that messes with the tidal filter 
            t0 = data['time'].iloc[0]
            t1 = data['time'].iloc[1]
            ind0 = data['time'].values==t0 
            ind1 = data['time'].values==t1
            data.loc[ind0,'%s,Net Load (Mg/d)' % param] = data.loc[ind1,'%s,Net Load (Mg/d)' % param].values[0]
            for ic in range(ncom):
                data_components[ic].loc[ind0,'%s,Net Load (Mg/d)' % components_list[ic]] = data_components[ic].loc[ind1,'%s,Net Load (Mg/d)' % components_list[ic]].values[0]
    
            # loop through the water years we are to plot for this run
            nwy = len(wy_list)
            for iwy in range(nwy):
                
                # get water year
                wy = wy_list[iwy]
    
                ## pick the time window based on water year
                t_window = np.array(['%d-10-01' % (wy-1),'%d-10-01' % wy]).astype('datetime64')
        
                # water year string
                water_year = 'WY%d' % wy
    
                # apply tidal filter or cumulative sum when called for
                if tavg == 'Filtered':
        
                    # make a copy of the data
                    dataf = data.copy(deep=True)
                    dataf_components = []
                    for ic in range(ncom):
                        dataf_components.append(data_components[ic].copy(deep=True))
        
                    # tidally filter 
                    for col in filt_cols:
                        dataf[col] = spring_neap_filter(data[col].values)
                    for ic in range(ncom):
                        for col in filt_cols_components[ic]:
                            dataf_components[ic][col] = spring_neap_filter(data_components[ic][col].values)
        
                    # trim in time after applying filter to 
                    indt = np.logical_and(dataf['time']>=t_window[0], dataf['time']<t_window[1])
                    dataf = dataf.loc[indt]
                    for ic in range(ncom):
                        dataf_components[ic] = dataf_components[ic].loc[indt]
                
                elif tavg =='Cumulative':
        
                    # trim in time before doing cumulative sum
                    indt = np.logical_and(data['time']>=t_window[0], data['time']<t_window[1])
                    dataf = data.loc[indt].copy(deep=True)
                    dataf_components = []
                    for ic in range(ncom):
                        dataf_components.append(data_components[ic].loc[indt].copy(deep=True))
        
                    # then do cumulative sum
                    for col in filt_cols:
                        dataf[col] = np.cumsum(dataf[col]) * deltat    
                    for ic in range(ncom):
                        for col in filt_cols_components[ic]:
                            dataf_components[ic][col] = np.cumsum(dataf_components[ic][col]) * deltat
                else:   
        
                    indt = np.logical_and(data['time']>=t_window[0], data['time']<t_window[1])
                    dataf = data.loc[indt].copy(deep=True)
                    dataf_components = []
                    for ic in range(ncom):
                        dataf_components.append(data_components[ic].loc[indt].copy(deep=True))
    
                # get time
                time = np.unique(dataf['time'].values)
                ntime = len(time)
    
                ########################################
                # plot the mass budget for the whole bay
                ########################################
    
                # get stats for whole bay
                Delta_Influx = dataf['%s,Flux In from E (Mg/d)' % param].values
                GG_Outflux = dataf['%s,Flux In from W (Mg/d)' % param].values
                Minor_Trib_Influx = dataf['%s,Net Transport In (Mg/d)' % param].values - GG_Outflux - Delta_Influx
                Storage = -dataf['%s,dMass/dt, Balance Check (Mg/d)' % param].values
                Net_Rx = dataf['%s,Net Reaction (Mg/d)' % param].values
                Net_Loading = dataf['%s,Net Load (Mg/d)' % param].values
                Net_Rx_Check_Sum = dataf[reaction_list].values.sum(axis=1)
                Tribs_Plus_Loads = Delta_Influx + Minor_Trib_Influx + Net_Loading
    
                # golden gate outflux by components
                GG_Outflux_Com = np.zeros((ntime, ncom))
                for icom in range(ncom):
                    ind = dataf_components[icom]['group'].values == 'Whole_Bay'
                    GG_Outflux_Com[:,icom] = dataf_components[icom].loc[ind]['%s,Flux In from W (Mg/d)' % components_list[icom]].values
    
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
                ax[0,irun].stackplot(time, df_pos.values.transpose(), colors = colors[0:len(df.columns)], labels=df.columns)
                ax[0,irun].stackplot(time, df_neg.values.transpose(), colors = colors[0:len(df.columns)])
                if iwy==0:
                    if irun==0:
                        ax[0,irun].set_ylabel('Whole Bay Mass Balance (Mg/d)')
                    elif irun==(nruns-1):
                        ax[0,irun].legend(loc='center left',bbox_to_anchor=(1, 0.5))
    
                # make dataframe with reactions for whole bay
                df = dataf[reaction_list]
                df.columns = reaction_list_trimmed
                df['Storage (-dM/dt)'] = Storage.copy()
    
                # divide into positive and negative
                df_pos = df.copy(deep=True)
                df_neg = df.copy(deep=True)
                df_pos[df<0] = 0
                df_neg[df>0] = 0
    
                # add to figure 1
                ax[1,irun].stackplot(time, df_pos.values.transpose(), colors = colors[0:len(df.columns)], labels=df.columns)
                ax[1,irun].stackplot(time, df_neg.values.transpose(), colors = colors[0:len(df.columns)])
                ax[1,irun].plot(time, Net_Rx, 'k', label='Net Reaction')
                ax[1,irun].plot(time, Net_Rx_Check_Sum, 'm--', label='Net Reaction, Check Sum')
                ax[1,irun].plot(time, Net_Rx + Storage, 'b', label='Net Reaction - dM/dt')
                if iwy==0:
                    if irun==0:
                        ax[1,irun].set_ylabel('Whole Bay Reactions (Mg/d)')
                    elif irun==(nruns-1):
                        ax[1,irun].legend(loc='center left',bbox_to_anchor=(1, 0.5))
            
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
                ax[2,irun].stackplot(time, df_pos.values.transpose(), colors = colors[0:len(df.columns)], labels=df.columns)
                ax[2,irun].stackplot(time, df_neg.values.transpose(), colors = colors[0:len(df.columns)])
                ax[2,irun].plot(time,Tribs_Plus_Loads, 'k--', label='%s Loading from Tribs and Point Sources' % param)
                ax[2,irun].plot(time, -GG_Outflux, 'k', label='%s Outflux Through GG' % param)
                if iwy==0:
                    if irun==0:
                        ax[2,irun].set_ylabel('Whole Bay Influx vs. Outflux (Mg/d)')
                    elif irun==(nruns-1):
                        ax[2,irun].legend(loc='center left',bbox_to_anchor=(1, 0.5))
    
            # add label for run
            ax[0,irun].set_title('Run %s' % run2plot)
    
            # format time axis for all 3 rows
            for ax1 in ax[:,irun]:
                ax1.set_xlim((tmin,tmax))
                ax1.xaxis.set_major_locator(major_locator)
                ax1.xaxis.set_minor_locator(minor_locator)
                ax1.xaxis.set_major_formatter(major_formatter)
                ax1.grid(which='both')
    
    
        # set y axis limits the same across runs
        # ... for first and 2nd rows, make y axis symmetric around zero
        for irow in [0,1]:
            ymax = 0
            for irun in range(nruns):
                ymax1 = np.abs(ax[irow,irun].get_ylim()).max()
                ymax = np.max([ymax,ymax1])
            for irun in range(nruns):
                ax[irow,irun].set_ylim((-ymax,ymax))
        # ... for 3rd row set min at zero
        for irow in [2]:
            ymax = 0
            for irun in range(nruns):
                ymax1 = np.abs(ax[irow,irun].get_ylim()).max()
                ymax = np.max([ymax,ymax1])
            for irun in range(nruns):
                ax[irow,irun].set_ylim((0,ymax))
    
        # add title and save the figure
        fig.suptitle('Whole Bay %s %s Budget' % (tavg_str, param))
        fig.tight_layout(rect=[0, 0.03, 1, 0.95])
        fig.savefig(os.path.join(out_dir, '%s_Whole_Bay_Budget_Stacked_%s_%s.png' % (fig_pref, tavg, param)),dpi=300)
    
        # close figures
        plt.close('all')
    
