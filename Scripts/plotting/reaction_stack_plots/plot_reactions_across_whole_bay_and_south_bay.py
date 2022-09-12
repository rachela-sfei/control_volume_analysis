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


# list or runs to plot and list of water years to pick out of corresponding run
run2plot = 'G141_13to18_207'
wy_list = [2013,2014,2015,2016,2017,2018]

## composite parameter (must match suffix of balance table)
#param = 'DIN'
#param = 'TN'
param = 'TN_include_sediment'
#param = 'Algae'

# base directory (depends if running from laptop or on an hpc)
#base_dir = r'X:\hpcshared'
#base_dir = '/richmondvol1/hpcshared'
base_dir = '/chicagovol1/hpcshared'

## output plot directory
out_dir = os.path.join(base_dir,'NMS_Projects','Control_Volume_Analysis','Plots',run2plot,'stack_plots_multigroup')

## list of parameters to plot
param_list = ['DIN','TN','TN_include_sediment','OXY','DetNS', 'Algae']

# dictionary to map parameter to element corresponding to mass
grams_of_what = {'DIN' : 'N', 'TN' : 'N', 'TN_include_sediment' : 'N', 'DetNS' : 'N', 'Algae' : 'C', 'OXY' : 'O'}

# list of panels to plot
panel_list = ['Whole_Bay_RMP', 'Whole_Bay_WB', 'South_Bay_6Part']

# list of normalizations (divide by area, volume, or nothing)
norm_list = ['Area','Volume','None']

# list of time integration types
tavg_list = ['Filtered', 'Cumulative']   # can also add 'Daily' if desired

# this is a function, but it's really more like user input b/c this is where you specify the properties of the different plots
# we are going to make
def panel_properties(panel):

    '''
    usage:  figure_size, nrows, ncols, group_list, group_labels, panel_label = panel_properties(panel)
    '''

    if panel == 'Whole_Bay_RMP':
    
        if len(wy_list)>=6:
            figure_size = (20, 10)
        else:
            figure_size = (15, 10)
        ncols = 3
        nrows = 2
    
        group_list = ['Whole_Bay','Suisun_Bay','San_Pablo_Bay','Central_Bay_RMP','SB_RMP','LSB']
        group_labels = ['Whole Bay','Suisun Bay','San Pablo Bay','Central Bay (RMP)','South Bay (RMP)','Lower South Bay']
        panel_label = 'by Subembayment (RMP)'

    elif panel == 'Whole_Bay_WB':
    
        if len(wy_list)>=6:
            figure_size = (20, 10)
        else:
            figure_size = (15, 10)
        ncols = 3
        nrows = 2
    
        group_list = ['Whole_Bay','Suisun_Bay','San_Pablo_Bay','Central_Bay_WB','SB_WB','LSB']
        group_labels = ['Whole Bay','Suisun Bay','San Pablo Bay','Central Bay (WB)','South Bay (WB)','Lower South Bay']
        panel_label = 'by Subembayment (Water Board)'
    
    elif panel == 'South_Bay_6Part':
    
        if len(wy_list)>=6:
            figure_size = (20, 10)
        else:
            figure_size = (15, 10)
        ncols = 3
        nrows = 2
    
        # list of south bay chunks (note this could be any list of groups, doesn't have to be subembayments)
        group_list = ['SB_WB_west_shoal_north_half','SB_WB_channel_north_half','SB_WB_east_shoal_north_half',
                         'SB_WB_west_shoal_south_half','SB_WB_channel_south_half','SB_WB_east_shoal_south_half']
        group_labels = ['NW Shoal','N Channel','NE Shoal','SW Shoal','S Channel','SE Shoal']
        panel_label = 'Across South Bay'

    return (figure_size, nrows, ncols, group_list, group_labels, panel_label)

# time axis formatting
major_locator = mdates.YearLocator()
minor_locator = mdates.MonthLocator(bymonth=(1,4,7,10))
major_formatter = mdates.DateFormatter('%Y')

# default color cycle
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']

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

#########################################################################################
## main
#########################################################################################

# check if plot directory exists and create it if not
if not os.path.exists(out_dir):
    os.makedirs(out_dir)

# make a kind of confusing figure prefix with list of runs and water years
fig_pref = run2plot + '_'
if wy_list==[2013,2014,2015,2016,2017,2018]:
    fig_pref += 'WY13to18_'
elif all(wy_list[0]==np.array(wy_list)):
    fig_pref += 'WY%d_' % wy_list[0]
else:        
    for wy in wy_list:
        fig_pref += 'WY%d_' % wy
fig_pref = fig_pref[0:-1]

# get first and last date for time axis
wymin = np.array(wy_list).min()
wymax = np.array(wy_list).max()
tmin = np.datetime64('%d-10-01' % (wymin-1))
tmax = np.datetime64('%d-10-01' % wymax)

# loop through parameters
for param in param_list:

    # loop through different time averages: daily, spring-neap filter, cumulative
    for tavg in tavg_list:

        # loop through norms
        for norm in norm_list:
    
            # for figure labeling
            if tavg=='Filtered':
                tavg_str = 'Spring-Neap Filtered'
            else:
                tavg_str = tavg
        
            ## balance table folder
            table_dir = os.path.join(base_dir,'NMS_Projects','Control_Volume_Analysis','Balance_Tables',run2plot)
        
            # load up the balance table data for the parameter of interest
            input_fn = os.path.join(table_dir,'%s_Table_By_Group.csv' % param.lower())
            data = pd.read_csv(input_fn)
        
            # convert times from string to datetime64
            data['time'] = pd.to_datetime(data['time'])
        
            # get list of all groups
            allgroups = np.unique(data['group'].values)
        
            # compute time step in days
            deltat = (data['time'].iloc[1] - data['time'].iloc[0])/np.timedelta64(1,'h')/24
        
            # get list of sources and sinks, and the list of columns we want to apply the tidal filter to
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
        
            # replace the first loading value (which is zero) with the second loading value ...
            # this is because sometimes the loading starts out at zero and that messes with the tidal filter 
            t0 = data['time'].iloc[0]
            t1 = data['time'].iloc[1]
            for group in allgroups:
                ind0 = np.logical_and(data['group'].values==group,data['time'].values==t0) 
                ind1 = np.logical_and(data['group'].values==group,data['time'].values==t1) 
                data.loc[ind0,'%s,Net Load (Mg/d)' % param] = data.loc[ind1,'%s,Net Load (Mg/d)' % param].values[0]

            # normalize data by volume or area if specifiec
            if norm == 'Volume':
                norm_units = 'g %s/m$^3$/d' % grams_of_what[param]
                normval = data['Volume (Mean, m^3)'].values / 1e6
            elif norm == 'Area':
                norm_units = 'g %s/m$^2$/d' % grams_of_what[param]
                normval = data['Area (m^2)'].values /1e6
            elif norm == 'None':
                norm_units = 'Mg %s/d' % grams_of_what[param]
                normval = 1

            # apply the normalization to all columns except group and time
            data1 = data.copy(deep=True)
            for col in data.columns:
                if col in ['group', 'time']:
                    data1[col] = data[col].values
                else:
                    data1[col] = data[col].values / normval
            data = data1.copy(deep=True)
        
            # loop through the sets of panels we want to plot
            for panel in panel_list:
        
                # get some information about this grouping of panels
                figure_size, nrows, ncols, group_list, group_labels, panel_label = panel_properties(panel)
        
                # make sure number of groups matches length of group labels, and that they fit on the plot
                ngroups = len(group_list)
                assert ngroups==len(group_labels)
                assert nrows*ncols>=ngroups
        
                # create figure
                fig, ax = plt.subplots(nrows, ncols, figsize=figure_size)
                ax = ax.flatten()
        
                # loop through the water years
                for iwy in range(len(wy_list)):
                    wy = wy_list[iwy]
                
                    ## pick the time window based on water year
                    t_window = np.array(['%d-10-01' % (wy-1),'%d-10-01' % wy]).astype('datetime64')
                
                    # water year string
                    water_year = 'WY%d' % wy
            
                    # apply tidal filter or cumulative sum when called for
                    if tavg == 'Filtered':
                    
                        # make a copy of the data
                        dataf = data.copy(deep=True)
                    
                        # tidally filter each group
                        for group in allgroups:
                            ind = data['group'].values == group
                            for col in filt_cols:
                                dataf.loc[ind,col] = spring_neap_filter(data.loc[ind,col])
                    
                        # trim in time after applying filter to 
                        indt = np.logical_and(dataf['time']>=t_window[0], dataf['time']<t_window[1])
                        dataf = dataf.loc[indt]
                    
                    elif tavg =='Cumulative':
                    
                        # trim in time before doing cumulative sum
                        indt = np.logical_and(data['time']>=t_window[0], data['time']<t_window[1])
                        dataf = data.loc[indt].copy(deep=True)
                    
                        # then do cumulative sum
                        for group in allgroups:
                            ind = dataf['group'].values == group
                            for col in filt_cols:
                                dataf.loc[ind,col] = np.cumsum(dataf.loc[ind,col]) * deltat  
            
                    else:   
                    
                        indt = np.logical_and(data['time']>=t_window[0], data['time']<t_window[1])
                        dataf = data.loc[indt].copy(deep=True)
            
                    # get time
                    time = np.unique(dataf['time'].values)
                    ntime = len(time)
            
                    # loop through the groups
                    for igroup in range(ngroups):
            
                        # get data for group
                        group = group_list[igroup]
                        ind = dataf['group'] == group
                        data_group = dataf.loc[ind].copy(deep=True)

                        # fill up dataframe with reactions
                        df = pd.DataFrame(index=time)
                        for rx in reaction_list:
                            df[rx] = data_group[rx].values
                        df.columns = reaction_list_trimmed
                
                        # get net reaction and storage
                        Net_Rx_Group = data_group['%s,Net Reaction (Mg/d)' % param].values
                        Net_Rx_Group_Check_Sum = df.values.sum(axis=1)
                        Storage_Group = -data_group['%s,dMass/dt, Balance Check (Mg/d)' % param].values
            
                        # add storage to the dataframe
                        df['Storage (-dM/dt)'] = Storage_Group
            
                        # divide into positive and negative values
                        df_pos = df.copy(deep=True)
                        df_neg = df.copy(deep=True)
                        df_pos[df<0] = 0
                        df_neg[df>0] = 0
                
                        # add to figure
                        ax[igroup].stackplot(time, df_pos.values.transpose(), colors = colors[0:len(df.columns)], labels=df.columns)
                        ax[igroup].stackplot(time, df_neg.values.transpose(), colors = colors[0:len(df.columns)])
                        ax[igroup].plot(time, Net_Rx_Group, 'k', label='Net Reaction')
                        ax[igroup].plot(time, Net_Rx_Group_Check_Sum, 'm--', label='Net Reaction, Check Sum')
                        ax[igroup].plot(time, Net_Rx_Group + Storage_Group, 'b', label='Net Reaction - dM/dt')
                        ax[igroup].set_title(group_labels[igroup])
                        if np.mod(igroup, ncols)==0:
                            ax[igroup].set_ylabel('Reactions and Storage (%s)' % norm_units)
        
                        # add legend
                        if iwy==0:
                            if igroup==(ncols-1):
                                ax[igroup].legend(loc='center left',bbox_to_anchor=(1, 0.5))
            
                # format axes 
                ymax = 0
                for iax in range(len(ax)):
                    ax1 = ax[iax]
                    if iax>=ngroups:
                        ax1.axis('off')
                    else:
                        ax1.set_xlim((tmin,tmax))
                        ax1.xaxis.set_major_locator(major_locator)
                        ax1.xaxis.set_minor_locator(minor_locator)
                        ax1.xaxis.set_major_formatter(major_formatter)
                        ax1.grid(which='both')
                        ymax = np.max(np.array([ymax,np.abs(ax1.get_ylim()).max()]))
                for ax1 in ax:
                    ax1.set_ylim((-ymax,ymax))
        
                # add title and save the figure of subembayment reactions
                fig.suptitle('%s %s Reactions %s\n%s' % (tavg_str, param, panel_label,run2plot))
                fig.tight_layout(rect=[0, 0.03, 1, 0.95])
                fig.savefig(os.path.join(out_dir, '%s_%s_Reactions_%s_%s_%s.png' % (fig_pref, param, panel, tavg, norm)),dpi=300)
        
                # close figures
                plt.close('all')
            
        