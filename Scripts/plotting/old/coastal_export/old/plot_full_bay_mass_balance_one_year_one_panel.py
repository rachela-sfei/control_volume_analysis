'''

Use new "Whole_Bay" group to work up budget

This creates a four panel plot with the following panels
- bay-wide DIN Loading
- Delta influx (net flux in from the W)
- assimilation (net Rx term)
- outflux throguh Golden Gate (net flux in from the E)

Multiple water years are plotted together, based on full resoluation runs

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

wy = 2018
run2plot = 'FR18_004'
fig_suff = run2plot
title = 'WY%d' % wy

## composite parameter (must match suffix of balance table)
param = 'TN'

## output plot directory
out_dir = r'X:\hpcshared\NMS_Projects\Control_Volume_Analysis\Plots\%s' % run2plot

## here's a colorblind friendly color cycle
cfc = ['#377eb8', '#ff7f00', '#4daf4a',
                  '#f781bf', '#a65628', '#984ea3',
                  '#999999', '#e41a1c', '#dede00']

# figure size 
fs = (6,3)

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

# dummy start time
ts = np.datetime64('2012-10-01')

## balance table folder
table_dir = r'X:\hpcshared\NMS_Projects\Control_Volume_Analysis\Balance_Tables\%s' % run2plot

## pick the time window for cumulative plot
t_window = np.array(['%d-10-01' % (wy-1),'%d-10-01' % wy]).astype('datetime64')

# water year string
water_year = 'WY%d' % wy

# input is the composite parameter balance table, in the corresponding run folder
input_fn = os.path.join(table_dir,'Balance_Table_By_Group_Composite_Parameter_%s.csv' % param)

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
fig0, ax0 = plt.subplots(1,1,figsize=fs)
ax0.plot([], [], color =cfc[0], label ='Reactive Loss', linewidth=6, alpha=0.5)
ax0.plot([], [], color =cfc[1], label ='Loads (POTW + Delta)', linewidth=6, alpha=0.5)
ax0.plot([], [], color =cfc[2], label ='Export (Golden Gate)', linewidth=6)
ax0.stackplot(data_cum['time'],-data_cum['%s,Net Reaction (Mg/d)' % param]/1000,-data_cum['%s,Flux In from W (Mg/d)' % param]/1000, colors=[cfc[0],cfc[1]])
ax0.plot(data_cum['time'],data_cum['%s,Net Load (Mg/d)' % param]/1000 + data_cum['%s,Flux In from E (Mg/d)' % param]/1000, color=cfc[2], linewidth=4)

# plot tidally filtered
fig1, ax1 = plt.subplots(1,1,figsize=fs)
ax1.plot([], [], color =cfc[0], label ='Reactive Loss', linewidth=6, alpha=0.5)
ax1.plot([], [], color =cfc[1], label ='Loads (POTW + Delta)', linewidth=6, alpha=0.5)
ax1.plot([], [], color =cfc[2], label ='Export (Golden Gate)', linewidth=6)
ax1.stackplot(data_tfi['time'],-data_tfi['%s,Net Reaction (Mg/d)' % param]/1000,-data_tfi['%s,Flux In from W (Mg/d)' % param]/1000, colors=[cfc[0],cfc[1]])
ax1.plot(data_tfi['time'],data_tfi['%s,Net Load (Mg/d)' % param]/1000 + data_tfi['%s,Flux In from E (Mg/d)' % param]/1000, color=cfc[2], linewidth=4)

# plot daily
fig2, ax2 = plt.subplots(1,1,figsize=fs)
ax2.plot([], [], color =cfc[0], label ='Reactive Loss', linewidth=6, alpha=0.5)
ax2.plot([], [], color =cfc[1], label ='Loads (POTW + Delta)', linewidth=6, alpha=0.5)
ax2.plot([], [], color =cfc[2], label ='Export (Golden Gate)', linewidth=6)
ax2.stackplot(data['time'],-data['%s,Net Reaction (Mg/d)' % param]/1000,-data['%s,Flux In from W (Mg/d)' % param]/1000, colors=[cfc[0],cfc[1]])
ax2.plot(data['time'],data['%s,Net Load (Mg/d)' % param]/1000 + data['%s,Flux In from E (Mg/d)' % param]/1000, color=cfc[2], linewidth=4)

# clean up the axes, add labels, legend, titles, grid, etc.
for (ax, units) in zip([ax0,ax1,ax2], [' (10$^9$g/d)', ' (Mg/d)', ' (Mg/d)']):
    ax.set_ylabel(param + units)
    ax.grid(b=True, alpha = 0.3)
    ax.set_xlim((data['time'].iloc[0],data['time'].iloc[-1]))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('1-%b'))
    ax.legend()
    ymin, ymax = ax.get_ylim()
    if ymin>0:
        ax.set_ylim((0,ymax))
    children = ax.get_children()
    for i in range(4):
        children[i].set_alpha(0.5)

ax0.set_title(title)
ax1.set_title(title)
ax2.set_title(title)

# format and save figures
for fig in [fig0,fig1,fig2]:
    fig.autofmt_xdate()
    fig.tight_layout()
fig0.savefig(os.path.join(out_dir, 'Whole_Bay_Budget_Cumulative_%s_%s.png' % (param, fig_suff)))
fig1.savefig(os.path.join(out_dir, 'Whole_Bay_Budget_Filtered_%s_%s.png' % (param, fig_suff)))
fig2.savefig(os.path.join(out_dir, 'Whole_Bay_Budget_Daily_%s_%s.png' % (param, fig_suff)))
