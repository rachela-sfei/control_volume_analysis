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

#wy_list = [2013,2017,2018]
#run2plot_list = ['FR13_021','FR17_014','FR18_004']
#fig_suff = '_FR13_021_FR17_014_FR18_004'
#title_annotation = '\nFull Resolution Model: FR13_021, FR17_014, FR18_004'

wy_list = [2013,2014,2015,2016,2017,2018]
run2plot_list = ['G141_13to18_197','G141_13to18_197','G141_13to18_197','G141_13to18_197','G141_13to18_197','G141_13to18_197']
fig_pref = 'G141_13to18_197'
title_annotation = 'Run G141_13to18_197'


## composite parameter (must match suffix of balance table)
#param = 'DIN'
param = 'TN'
#param = 'TN_include_sediment'
#param = 'Algae'

# base directory (depends if running from laptop or on an hpc)
base_dir = r'X:\hpcshared'
#base_dir = '/richmondvol1/hpcshared'

## output plot directory
out_dir = os.path.join(base_dir,'NMS_Projects','Control_Volume_Analysis','Plots','Compare_Water_Years','coastal_export')

## here's a colorblind friendly color cycle
cfc = ['#377eb8', '#ff7f00', '#4daf4a',
                  '#f781bf', '#a65628', '#984ea3',
                  '#999999', '#e41a1c', '#dede00']

# figure size 
fs = (5.5,8.5)

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

# initialize figure
fig0, ax0 = plt.subplots(3,1,figsize=fs)
fig1, ax1 = plt.subplots(3,1,figsize=fs)
fig2, ax2 = plt.subplots(3,1,figsize=fs)

# dummy start time
ts = np.datetime64('2012-10-01')

for iwy in range(len(wy_list)):

    wy = wy_list[iwy]
    run2plot = run2plot_list[iwy]

    ## balance table folder
    table_dir = os.path.join(base_dir,'NMS_Projects','Control_Volume_Analysis','Balance_Tables',run2plot)

    ## pick the time window for cumulative plot
    t_window = np.array(['%d-10-01' % (wy-1),'%d-10-01' % wy]).astype('datetime64')

    # water year string
    water_year = 'WY%d' % wy

    # input is the composite parameter balance table, in the corresponding run folder
    input_fn = os.path.join(table_dir,'%s_Table_By_Group.csv' % param.lower())

    # load up the balance table data
    data = pd.read_csv(input_fn)

    # convert times from string to datetime64
    data['time'] = pd.to_datetime(data.time)

    # select the whole bay control volume
    data = data.loc[data['group']=='Whole_Bay']

    # if this is WY2018, replace the first loading value (which is zero) with the second loading value
    data['%s,Net Load (Mg/d)' % param].iloc[0] = data['%s,Net Load (Mg/d)' % param].iloc[1]

    # get subset of column names we want to apply tidal filter and cumulative sum on
    cols = data.columns[4:]

    # apply tidal filter before selecting time window to get better end effects
    data_tfi = data.copy(deep=True)
    for col in cols:
        data_tfi[col] = spring_neap_filter(data[col])

    # now pare down to time window of interest
    indt = np.logical_and(data['time']>=t_window[0], data['time']<t_window[1])
    data = data.loc[indt]
    data_tfi = data_tfi.loc[indt]

    # compute cumulutaive sum (compute time step in days)
    deltat = (data['time'].iloc[1] - data['time'].iloc[0])/np.timedelta64(1,'h')/24
    data_cum = data.copy(deep=True)
    for col in cols:
        data_cum[col] = np.cumsum(data[col]) * deltat

    # plot cumulative
    ax0[0].plot(data_cum['time']-t_window[0]+ts,data_cum['%s,Net Load (Mg/d)' % param]/1000 +
                                                data_cum['%s,Flux In from E (Mg/d)' % param]/1000 + 
                                                data_cum['%s,Flux In from N (Mg/d)' % param]/1000,
                                                label=water_year)
    ax0[1].plot(data_cum['time']-t_window[0]+ts,data_cum['%s,Net Reaction (Mg/d)' % param]/1000,label=water_year)
    ax0[2].plot(data_cum['time']-t_window[0]+ts,-data_cum['%s,Flux In from W (Mg/d)' % param]/1000,label=water_year)
    
    # plot tidally filtered
    ax1[0].plot(data_tfi['time']-t_window[0]+ts,data_tfi['%s,Net Load (Mg/d)' % param] + 
                                                data_tfi['%s,Flux In from E (Mg/d)' % param] + 
                                                data_tfi['%s,Flux In from N (Mg/d)' % param],
                                                label=water_year)
    ax1[1].plot(data_tfi['time']-t_window[0]+ts,data_tfi['%s,Net Reaction (Mg/d)' % param],label=water_year)
    ax1[2].plot(data_tfi['time']-t_window[0]+ts,-data_tfi['%s,Flux In from W (Mg/d)' % param],label=water_year)

    # plot daily
    ax2[0].plot(data['time']-t_window[0]+ts,data['%s,Net Load (Mg/d)' % param] + 
                                            data['%s,Flux In from E (Mg/d)' % param] + 
                                            data['%s,Flux In from N (Mg/d)' % param],
                                            label=water_year)
    ax2[1].plot(data['time']-t_window[0]+ts,data['%s,Net Reaction (Mg/d)' % param],label=water_year)
    ax2[2].plot(data['time']-t_window[0]+ts,-data['%s,Flux In from W (Mg/d)' % param],label=water_year)

# clean up the axes, add labels, legend, titles, grid, etc.
for (ax, units) in zip([ax0,ax1,ax2], ['\n(10$^9$g/d)', '\n(Mg/d)', '\n(Mg/d)']):
    ax[0].set_ylabel('Loading (POTW + Delta)' + units)
    ax[1].set_ylabel('Net Reaction' + units)
    ax[2].set_ylabel('Outflux (Golden Gate)' + units)
    for i in range(3):
        ax[i].grid(b=True, alpha = 0.3)
        ax[i].set_xlim((ts,ts+np.timedelta64(365,'D')))
        ax[i].xaxis.set_major_locator(mdates.MonthLocator(interval=1))
        ax[i].xaxis.set_major_formatter(mdates.DateFormatter('1-%b'))
    ax[2].legend()
    ymin, ymax = ax[0].get_ylim()
    if ymin>0:
        ax[0].set_ylim((0,ymax))
    ymin, ymax = ax[1].get_ylim()
    if ymin>0:
        ax[1].set_ylim((0,ymax))
    ymin, ymax = ax[2].get_ylim()
    if ymin>0:
        ax[2].set_ylim((0,ymax))

ax0[0].set_title('Whole Bay Cumulative %s Budget%s' % (param, title_annotation))
ax1[0].set_title('Whole Bay Tidally Fitlered %s Budget%s' % (param, title_annotation))
ax2[0].set_title('Whole Bay Daily %s Budget%s' % (param, title_annotation))

# format and save figures
for fig in [fig0,fig1,fig2]:
    fig.autofmt_xdate()
    fig.tight_layout()
fig0.savefig(os.path.join(out_dir, '%s_Whole_Bay_Budget_Cumulative_%s.png' % (fig_pref, param)))
fig1.savefig(os.path.join(out_dir, '%s_Whole_Bay_Budget_Filtered_%s.png' % (fig_pref, param)))
fig2.savefig(os.path.join(out_dir, '%s_Whole_Bay_Budget_Daily_%s.png' % (fig_pref, param)))

plt.close('')