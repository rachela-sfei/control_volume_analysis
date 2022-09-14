# -*- coding: utf-8 -*-
"""

"""


import pandas as pd 
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
plt.switch_backend('Agg')
import scipy.signal as signal    
import numpy as np 


# where all the balance tables are 
base_dir = '/richmondvol1/hpcshared/NMS_Projects/Control_Volume_Analysis/Balance_Tables/'

# where we will store the plots 
plot_dir = '/richmondvol1/hpcshared/NMS_Projects/Control_Volume_Analysis/Plots/Compare_Water_Years/'


# set up the runs we want to plot as a dictionary. The key is the name of the run / 
# label for the plot. The data is the path to the balance table. 
tables2plot = {'WY2013' : '%s/FR13_003/Balance_Table_All_Parameters_By_Group.csv' % base_dir,
               'WY2017' : '%s/FR17_003/Balance_Table_All_Parameters_By_Group.csv' % base_dir,
               }

tables2plot = {'FR13_003' : 'WY2013' , #: '%s/FR13_003/Balance_Table_All_Parameters_By_Group.csv' % base_dir,
               'FR17_003' : 'WY2017' , # : '%s/FR17_003/Balance_Table_All_Parameters_By_Group.csv' % base_dir,
               }


# ///////////////////////////////////////////////
# List of all the terms we're interested in (one for DPP, a bunch for total nitrogen assimilation)
diat_dpp = 'Diat,dPPDiat (Mg/d)'
nit_assim_terms = ["NO3,dDenitWat","NO3,dNitrif","NO3,dDenitSed",
                   "NO3,dNiDen", "NO3,dNO3Upt", "NH4,dMinPON1",
                   "NH4,dMinDON","NH4,dNitrif","NH4,dMinDetNS1",
                   "NH4,dMinDetNS2","NH4,dZ_NRes","NH4,dNH4Aut","NH4,dNH4Upt"]
nit_assim_terms = ['%s (Mg/d)' % i for i in nit_assim_terms]
# ///////////////////////////////////////////////
    


# ///////////////////////////////////////////////
# Read in all the tables listed in the dictionary. 
tables2plot_ = {} 
for table in tables2plot:
    tables2plot_[table] = pd.read_csv('%s/%s/Balance_Table_All_Parameters_By_Group.csv' %  (base_dir, table)) 
run_names = '_'.join(list(tables2plot.keys())) 
# ///////////////////////////////////////////////





# //////////////// DEFINE FUNCTIONS /////////////////////

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



'''
LOTS of functions here ... each of these pertain to different ways of selecting
and normalizing the data. 
'''
def get_rate(group, label, key):
    ''' Get a rate (mass/time) from the table, apply filter, cut off funky ends '''
    table = tables2plot_[key]
    ind = table.group == group
    subset = table[label].loc[ind]
    time   =  pd.to_datetime(table['time'].loc[table.group == group])
    filt_values = spring_neap_filter(subset.values)
    filt_cutoff = slice(20, len(time) - 20)
    return time[filt_cutoff], filt_values[filt_cutoff] 


def get_AN_rate(group, label, key):
    ''' Get a rate from the table, normalize by area (mass/area/time) apply filter, cut off funky ends '''
    table = tables2plot_[key]
    area   = table['Area (m^2)'].loc[table.group == group] 
    
    if not isinstance(label, str):
        subset = table[label].loc[table.group == group].sum(axis=1)
    else:
        subset = table[label].loc[table.group == group]
        
    time   =  pd.to_datetime(table['time'].loc[table.group == group])
    an_values = subset / area 
    filt_values = spring_neap_filter(an_values.values)
    filt_cutoff = slice(20, len(time) - 20)
    y = filt_values[filt_cutoff] 
    return time[filt_cutoff], y #np.cumsum(y)
    # return time[filt_cutoff], filt_values[filt_cutoff] 


def get_AN_rate_NOFILT(group, label, key):
    ''' Get a rate from the table, normalize by area (mass/area/time), cut off funky ends '''

    table = tables2plot_[key]
    area   = table['Area (m^2)'].loc[table.group == group] 
    if not isinstance(label, str):
        subset = table[label].loc[table.group == group].sum(axis=1)
    else:
        subset = table[label].loc[table.group == group]

    time   =  pd.to_datetime(table['time'].loc[table.group == group])
    an_values = subset / area 
    # filt_values = spring_neap_filter(an_values.values)
    filt_cutoff = slice(20, len(time) - 20)
    y = an_values.values[filt_cutoff] 
    return time[filt_cutoff], y #np.cumsum(y)

def get_AN_rate_summed(groups, label, key):
    ''' Get rates from the table over multiple CVs, sum them, normalize by area (mass/area/time), cut off funky ends '''
    table = tables2plot_[key]
    for i, group in enumerate(groups): 
        if i == 0:
            if not isinstance(label, str):
                subset = table[label].loc[table.group == group].sum(axis=1)
            else:
                subset = table[label].loc[table.group == group]         
            area   = table['Area (m^2)'].loc[table.group == group].values 
            time   =  pd.to_datetime(table['time'].loc[table.group == group])
        else:
            if not isinstance(label, str):
                subset += table[label].loc[table.group == group].sum(axis=1).values
            else:
                subset += table[label].loc[table.group == group].values
            area   += table['Area (m^2)'].loc[table.group == group].values 
    subset = subset / area 
    filt_values = spring_neap_filter(subset) 
    filt_cutoff = slice(20, len(time) - 20)
    return time[filt_cutoff], filt_values[filt_cutoff] 

def get_rate_summed(groups, label, key):
    ''' Get rates from the table over multiple CVs, sum them, cut off funky ends '''
    table = tables2plot_[key]
    for i, group in enumerate(groups): 
        if i == 0:
            if not isinstance(label, str):
                subset = table[label].loc[table.group == group].sum(axis=1)
            else:
                subset = table[label].loc[table.group == group]
            
            time   =  pd.to_datetime(table['time'].loc[table.group == group])
        else:
            if not isinstance(label, str):
                subset += table[label].loc[table.group == group].sum(axis=1).values
            else:
                subset += table[label].loc[table.group == group].values
            
            # subset += table[label].loc[table.group == group].values 
    filt_values = spring_neap_filter(subset)
    filt_cutoff = slice(20, len(time) - 20)
    return time[filt_cutoff], filt_values[filt_cutoff] 

def clean_axis(ax):
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b/%y'))
    ax.grid(True, alpha = 0.2)
    ax.legend(loc = 'upper left', ncol= 2)
    ax.set_xlim(x.values[40], x.values[-1])
    # ax.set_ylabel('Mg/day')
    # plt.legend() 



#%% ############################# 
#  FIRST : PRIMARY PRODUCTION   #
# ###############################


full_bay_groups = ['Central_Bay', 'Suisun_Bay', 'SB_RMP', 'San_Pablo_Bay', 'LSB']

# AREA-NORMALIZED DPP RATE 
if 1 : 
    fig, axs = plt.subplots(nrows = 2, ncols = 1, sharex = False, sharey = True, 
                                figsize=(10,5))
    for i,runID in enumerate(tables2plot_):       
        x , y = get_AN_rate_summed(full_bay_groups, diat_dpp, runID) 
        axs[i].plot(x,y*1e6,color= 'indigo', linewidth= 4, label = tables2plot[runID])

        clean_axis(axs[i])
        axs[i].set_ylabel('gC/m$^2$/day')
    
    title = 'Full Bay area-normalized DPP rate' 
    fig.suptitle(title) 
    fout = '%s/%s_%s.png' % (plot_dir, title, run_names) 
    fig.savefig(fout)
    print('Saved %s \n' % fout)


# TOTAL DPP RATE 
if 1 : 
    fig, axs = plt.subplots(nrows = 2, ncols = 1, sharex = False, sharey = True, 
                                figsize=(10,5))
    for i,runID in enumerate(tables2plot_):       
        x , y = get_rate_summed(full_bay_groups, diat_dpp, runID) 
        axs[i].plot(x,y*1e6,color= 'forestgreen', linewidth= 4, label = tables2plot[runID])

        clean_axis(axs[i])
        axs[i].set_ylabel('gC/day') 
        
    title = 'Full Bay total DPP rate' 
    fig.suptitle(title) 
    fout = '%s/%s_%s.png' % (plot_dir, title, run_names) 
    fig.savefig(fout)
    print('Saved %s \n' % fout)


#%% #######################################
#  SECOND : TOTAL NITROGEN ASSIMILATION   #
# #########################################


# AREA-NORMALIZED DIN ASSIMILATION RATE 
if 1 : 
    fig, axs = plt.subplots(nrows = 2, ncols = 1, sharex = False, sharey = True, 
                                figsize=(10,5))
    for i,runID in enumerate(tables2plot_):       
        x , y = get_AN_rate_summed(full_bay_groups, nit_assim_terms, runID) 
        axs[i].plot(x,y*1e6,color= 'skyblue', linewidth= 4, label = tables2plot[runID])

        clean_axis(axs[i])
        axs[i].set_ylabel('gN/m$^2$/day')
    title = 'Full Bay area-normalized DIN assimilation rate' 
    fig.suptitle(title) 
    fout = '%s/%s_%s.png' % (plot_dir, title, run_names) 
    fig.savefig(fout)
    print('Saved %s \n' % fout)

# TOTAL DIN ASSIMILATION RATE 
if 1 : 
    fig, axs = plt.subplots(nrows = 2, ncols = 1, sharex = False, sharey = True, 
                                figsize=(10,5))
    for i,runID in enumerate(tables2plot_):       
        x , y = get_rate_summed(full_bay_groups, nit_assim_terms, runID) 
        axs[i].plot(x,y*1e6,color= 'forestgreen', linewidth= 4, label = tables2plot[runID])

        clean_axis(axs[i])
        axs[i].set_ylabel('gN/day') 
        
    title = 'Full Bay total DIN assimilation rate' 
    fig.suptitle(title) 
    fout = '%s/%s_%s.png' % (plot_dir, title, run_names) 
    fig.savefig(fout)
    print('Saved %s \n' % fout)
    
    




   
