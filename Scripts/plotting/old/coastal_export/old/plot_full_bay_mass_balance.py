'''

Use new "Whole_Bay" group to work up budget

This creates a stack plot where positive is:
- bay-wide DIN Loading
- Delta influx (this is the net flux in from the W)
and negative is:
- net DIN assimilation (this is the net Rx term)
- outflux throguh Golden Gate (this is the negative of net flux in from the E)

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

wy = 2013
run2plot = 'FR13_003'

## pick the time window for cumulative plot
t_window = np.array(['%d-10-01' % (wy-1),'%d-10-01' % wy]).astype('datetime64')

## composite parameter (must match suffix of balance table)
param = 'DIN'

## balance table folder
table_dir = r'X:\hpcshared\NMS_Projects\Control_Volume_Analysis\Balance_Tables\%s' % run2plot

## output plot directory
out_dir = r'X:\hpcshared\NMS_Projects\Control_Volume_Analysis\Plots\%s' % run2plot

## here's a colorblind friendly color cycle
cfc = ['#377eb8', '#ff7f00', '#4daf4a',
                  '#f781bf', '#a65628', '#984ea3',
                  '#999999', '#e41a1c', '#dede00']

# set y limits for plots
ylim_day = 700
ylim_tif = 500
ylim_cum = 55000/1000

# figure size for individual year plots 
fs = (5,5)

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
fig, ax = plt.subplots(figsize=fs
ax.plot([],[],color=cfc[0], label='POTW Loading', linewidth=3)
ax.plot([],[],color=cfc[1], label='Delta Influx', linewidth=3)
ax.plot([],[],color=cfc[2], label='Assimilation', linewidth=3)
ax.plot([],[],color=cfc[3], label='Golden Gate Outflux', linewidth=3)
ax.stackplot(data_cum['time'],data_cum['%s,Net Load (Mg/d)' % param]/1000,data_cum['%s,Flux In from E (Mg/d)' % param]/1000, colors=[cfc[0],cfc[1]])
ax.stackplot(data_cum['time'],data_cum['%s,Net Reaction (Mg/d)' % param]/1000,data_cum['%s,Flux In from W (Mg/d)' % param]/1000, colors=[cfc[2],cfc[3]])
ax.grid(b=True, alpha = 0.3)
ax.set_xlim((t_window[0],t_window[-1]))
ax.set_ylim((-ylim_cum, ylim_cum))
ax.legend(loc='upper left')
ax.set_title('Whole Bay %s Budget' % param)
ax.set_ylabel('Cumulative %s (10$^9$g)' % param)
plt.tight_layout()
plt.savefig(os.path.join(out_dir, 'Whole_Bay_Budget_Cumulative_%s_%s.png' % (param, run2plot)))

# plot tidally filtered
fig1, ax1 = plt.subplots(figsize=fs
ax1.plot(data_tfi['time'],data_tfi['%s,Net Load (Mg/d)' % param],label='POTW Loading')
ax1.plot(data_tfi['time'],data_tfi['%s,Flux In from E (Mg/d)' % param],label='Delta Influx')
ax1.plot(data_tfi['time'],data_tfi['%s,Net Reaction (Mg/d)' % param],label='Assimilation')
ax1.plot(data_tfi['time'],data_tfi['%s,Flux In from W (Mg/d)' % param],label='Golden Gate Outflux')
ax1.grid(b=True, alpha = 0.3)
ax1.set_xlim((t_window[0],t_window[-1]))
ax1.set_ylim((-ylim_tif, ylim_tif))
ax1.legend()
ax1.set_title('Whole Bay %s Budget' % param)
ax1.set_ylabel('Rate (Mg/d)')
plt.tight_layout()
plt.savefig(os.path.join(out_dir, 'Whole_Bay_Budget_Filtered_%s_%s.png' % (param, run2plot)))

# plot daily
fig2, ax2 = plt.subplots(figsize=fs)
ax2.plot(data['time'],data['%s,Net Load (Mg/d)' % param],label='POTW Loading')
ax2.plot(data['time'],data['%s,Flux In from E (Mg/d)' % param],label='Delta Influx')
ax2.plot(data['time'],data['%s,Net Reaction (Mg/d)' % param],label='Assimilation')
ax2.plot(data['time'],data['%s,Flux In from W (Mg/d)' % param],label='Golden Gate Outflux')
ax2.grid(b=True, alpha = 0.3)
ax2.set_xlim((t_window[0],t_window[-1]))
ax2.set_ylim((-ylim_day, ylim_day))
ax2.legend()
ax2.set_title('Whole Bay %s Budget' % param)
ax2.set_ylabel('Rate (Mg/d)')
plt.tight_layout()
plt.savefig(os.path.join(out_dir, 'Whole_Bay_Budget_Daily_%s_%s.png' % (param, run2plot)))


plt.close('all')