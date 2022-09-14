#################################################################
# IMPORT PACKAGES
#################################################################

import sys, copy, os
import pandas as pd
import numpy as np
import matplotlib.pylab as plt
import matplotlib.dates as mdates
import matplotlib.gridspec as gridspec
from matplotlib.dates import DateFormatter
import datetime as dt
from scipy.signal import butter, lfilter
from scipy import signal
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()


#################################################################
# USER INPUT
#################################################################
    


# run id and water year
#run_id = 'FR13_025'
#wy = 2013
#run_id = 'FR17_018'
#wy = 2017
run_id = 'FR18_006'
wy = 2018

# variables
param_list = ['TN','TN_include_sediment','DIN','NO3','NH4','Algae','Zoopl']

# map variable to element (grams of what?)
element_dict = {}
element_dict['TN'] = 'N'
element_dict['TN_include_sediment'] = 'N'
element_dict['DIN'] = 'N'
element_dict['NO3'] = 'N'
element_dict['NH4'] = 'N'
element_dict['Algae'] = 'C'
element_dict['Zoopl'] = 'C'

# list of variables for which mass is incorrect
mass_is_wrong_list = ['TN_include_sediment']

# time string indicating end of the model warm-up period (when to
# start plotting the data) in format 'YYYY-MM-DD'
start_str = '%d-10-01' % (wy-1)

# labels/titles corresponding to the runs specified above
run_label = 'WY%d (%s)' % (wy, run_id)

# flag to drop reaction terms that are always zero, and set a cutoff in Mg/d that qualifies as "zero"
drop_zero_reactions = True
zero_cutoff = 1.0e-4
    
# name (and path) of folder for saving plots 
plot_folder = 'Plots_Eachgroup_Raw_Params'

# base directory (windows laptop or hpc)
#base_dir = r'X:\hpcshared'
base_dir = '/richmondvol1/hpcshared'

# balance table directory
balance_table_dir = os.path.join(base_dir,'NMS_Projects','Control_Volume_Analysis','Balance_Tables',run_id)

# balance table directory
plot_folder = os.path.join(base_dir,'NMS_Projects','Control_Volume_Analysis','Plots',run_id,'stack_plots')
           

####################################
# FUNCTIONS
####################################

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

#def spring_neap_filter(y, dt_days = 1.0, low_bound=1/36.0, high_bound=1/48.0):
#
#    """ 
#    Based on Noah Knowles' tidal filter, for which low_bound = 1/(30 hr) and
#    high_bound = 1/(40 hr). By analogy, since tidal period is 12.5 hours and 
#    spring-neap period is 15 days, 1/30 hr translates to 1/36 days and 1/40 hr
#    translates to 1/48 days. It is a bit of a misnomer to call these "bounds" 
#    as in fact this filter is basically a top-hat with a slightly sloping 
#    side instead of a vertical line. The low_bound and high_bound describe the
#    start and end points of the sloping bit.
#    
#    The original default parameters 1/30 and 1/40 are derived from the article:
#    1981, 'Removing Tidal-Period Variations from Time-Series Data
#    Using Low Pass Filters' by Roy Walters and Cythia Heston, in
#    Physical Oceanography, Volume 12, pg 112.
#
#    Noah derived this code from the TAPPY project: 
#        https://github.com/pwcazenave/tappy
#    Allie King then adapted code from Noah 
#    
#    Usage:
#        
#        yf = tidal_filter(y, deltat)
#        
#    Input:
#    
#        y = time series to be filtered
#        dt_days = time step between data points in days
#    
#    Output:
#        
#        yf = filtered time series
#    
#    """
#    
#    # convert low and high bounds to match series time step
#    low_bound = dt_days*low_bound
#    high_bound = dt_days*high_bound
#    
#    if len(y) % 2:
#        result = np.fft.rfft(y, len(y))
#    else:
#        result = np.fft.rfft(y)
#    freq = np.fft.fftfreq(len(y))[:len(result)]
#    factor = np.ones_like(result)
#    factor[freq > low_bound] = 0.0
#
#    sl = np.logical_and(high_bound < freq, freq < low_bound)
#
#    a = factor[sl]
#    # Create float array of required length and reverse
#    a = np.arange(len(a) + 2).astype(float)[::-1]
#
#    # Ramp from 1 to 0 exclusive
#    a = (a/a[0])[1:-1]
#
#    # Insert ramp into factor
#    factor[sl] = a
#
#    result = result * factor
#    yf = np.fft.irfft(result, len(y))
#    
#    return yf 
    
#################################################################
# MAIN
#################################################################

# make month locator for plotting
months = mdates.MonthLocator()  # every month

# make director(ies) for figures
if not os.path.exists(plot_folder):
    os.makedirs(plot_folder)
    
# set some plotting parameters
params = {'axes.labelsize': 10,
          'axes.titlesize': 10,
          'xtick.labelsize': 10,
          'ytick.labelsize': 10,
          'legend.fontsize': 8}
plt.rcParams.update(params)



# create plots for raw, spring-neap filtered, and cumulative data
for i_integrate in ['Cumulative_', 'Filtered_', 'Daily_']:

    # create plots for both un-normalized (Mg/d) and normalized (g/d/m2) (g/d/m3) values
    for i_norm in ['Mass_','Concentration_','PerArea_']:

        # loop through parameters
        for param in param_list:


            # include mass on plot for algae or zooplankton only
            if param in ['Algae','Zoopl']:
                include_mass = True      
            else:
                include_mass = False

            # set figure size and number of columns of subplots
            if include_mass:
                figsize_default = (6, 10)
                figsize_detritus = (6, 8)
            else:
                figsize_default = (6, 7.5)
                figsize_detritus = (6, 5.5)
            ncolumns = 1

            # load data frame with all budget data compiled into groups for reference and comparision data
            df_ref = pd.read_csv(os.path.join(balance_table_dir,'%s_Table_By_Group.csv' % param.lower()))

            # take units (Mg/d) out of column names
            colnames = df_ref.columns
            for colname in colnames:
                df_ref.rename(columns={colname : colname.replace(' (Mg/d)','')}, inplace=True)
                df_ref.rename(columns={colname : colname.replace(' (Mg)','')}, inplace=True)

            # convert time stamps to datetime objects and find time delta in units of days
            df_ref['time'] = [dt.datetime.strptime(time,'%Y-%m-%d') for time in df_ref['time']]
            dt_days_ref = (df_ref['time'][1] - df_ref['time'][0]).total_seconds()/3600./24.
                
            # loop through the parameters and find the names of each parameter's reaction terms,
            # compiling into a dictionary where key is parameter name and value is list of reaction
            # term names for that parameter
            reaction_name_list = []
            for colname in df_ref.columns:
                if ',d' in colname:
                    if not ((param + ',dMass/dt') in colname):
                        reaction_name_list.append(colname)
              
            # drop reaction terms that are always zero (both from the data frame and from the list of reactions in the reaction name dictionary)
            if drop_zero_reactions:
                reaction_name_list_trimmed = reaction_name_list.copy()
                for reaction_name in reaction_name_list:
                    if ('ZERO' in reaction_name) or (not any(df_ref[reaction_name].abs() > zero_cutoff)):
                        reaction_name_list_trimmed.remove(reaction_name)
                        df_ref.drop(columns=[reaction_name], inplace=True)
                reaction_name_list = reaction_name_list_trimmed.copy()

            # if normalized, divide and change units 
            if i_norm == 'Concentration_':
                df_ref[param + ',Mass'] = df_ref[param + ',Mass']/df_ref['Volume (Mean, m^3)']*1.0e6
                colnames = df_ref.columns[4:]
                for colname in colnames:
                    df_ref[colname] = df_ref[colname]/df_ref['Volume (Mean, m^3)']*1.0e6
                units = 'g %s/m$^3$/d' % element_dict[param]
                units_mass = 'mg/L %s' % element_dict[param]
                label_mass = 'Concentration'
            elif i_norm == 'PerArea_':
                df_ref[param + ',Mass'] = df_ref[param + ',Mass']/df_ref['Area (m^2)']*1.0e6
                colnames = df_ref.columns[4:]
                for colname in colnames:
                    df_ref[colname] = df_ref[colname]/df_ref['Area (m^2)']*1.0e6
                units = 'g %s/m$^2$/d' % element_dict[param]
                units_mass = 'g %s/m$^2$' % element_dict[param]
                label_mass = 'Mass Per Unit Area'
            elif i_norm == 'Mass_':
                units = 'Mg %s/d' % element_dict[param]
                units_mass = 'Mg %s' % element_dict[param]
                label_mass = 'Mass'
            else:
                raise Exception('i_norm not recognized')

            # if cumulative, integrate allgroups data and remove "/d" from units, starting at date defined by start_str
            if i_integrate == 'Cumulative_':  
                colnames = df_ref.columns[4:]  
                for colname in colnames:
                    if not ',Mass' in colname:
                        for group in np.unique(df_ref['group'].values):
                            ind = np.logical_and(df_ref['group'] == group, df_ref['time']>=pd.Timestamp(start_str))
                            df_ref.loc[ind,colname] = df_ref.loc[ind,colname].cumsum()
                # for the mass column, apply a spring-neap filter
                colname = '%s,Mass' % param
                for group in df_ref.group.unique():
                    ind = df_ref['group']==group   # logical index selecting group
                    df_ref.loc[ind,colname] = spring_neap_filter(df_ref.loc[ind,colname].values, dt_days_ref) # spring-neap filter
                units = units.replace('/d','')
                    
            # otherwise if filtered apply spring-neap filter to obtained filtered time series for each field in balance table
            elif i_integrate == 'Filtered_':
                for group in df_ref.group.unique():
                    ind = df_ref['group']==group   # logical index selecting group
                    for col in range(2,len(df_ref.columns)):
                        colname = df_ref.columns[col]  # column name 
                        df_ref.loc[ind,colname] = spring_neap_filter(df_ref.loc[ind,colname].values, dt_days_ref) # spring-neap filter
                
            # drop all the data during the model warmup period, before the water year starts
            start_time = np.datetime64(start_str)
            ind = df_ref['time']>=start_time
            df_ref = df_ref.loc[ind,:]
                
            # identify sources and sinks                    
            # make sure sources stay positive and sinks stay negative
            # (this is necessary for making stack plots, which are mostly messed up 
            # when 0.0 is represented as -0.0 and vice versa)
            source_name_list = []
            sink_name_list = []
            for reaction_name in reaction_name_list:
                if df_ref[reaction_name].mean() >= 0.0:
                    source_name_list.append(reaction_name)
                    ind = df_ref[reaction_name] < 0.0
                    if any(ind):
                        df_ref.loc[ind,reaction_name] = 0.0
                else:
                    sink_name_list.append(reaction_name)
                    ind = df_ref[reaction_name] > 0.0
                    if any(ind):
                        df_ref.loc[ind,reaction_name] = -0.0
        
            # order reactions with sources first, then sinks
            reaction_name_list_ordered = source_name_list.copy()
            for sink_name in sink_name_list:
                reaction_name_list_ordered.append(sink_name)

            # loop through the groups and plot budgets for each group
            for group in df_ref.group.unique():
            
            
                # logical index to select data in this group, and reset starting index at zero
                ind = df_ref['group'] == group
                dataframe_ref = df_ref[ind].copy(deep=True).reset_index()
                
                # select subset of dataframe corresponding to reactions for this parameter, and set index
                # to the time stamp, so stack plot will work properly. Note for some reason have to add 
                # 1969 to date to get the right year in the plot
                dataframe_ref_rx = dataframe_ref[reaction_name_list_ordered].copy(deep=True)
                dataframe_ref_rx = dataframe_ref_rx.set_index(dataframe_ref['time'].apply(lambda x: x + pd.DateOffset(years=69))) 
                    
                # if there are comparison plots and we are plotting differences, make sure the time axes have the same starting time
                # and time step, and chose the longer time series for plotting (one may be longer than the other if one or both 
                # simulations did not run to completion). also set the x limits for plotting, chosing the widest time window
                xmin = dataframe_ref['time'].iloc[0]
                xmax = dataframe_ref['time'].iloc[-1]
                xmin_rx = xmin + pd.DateOffset(years=69)
                xmax_rx = xmax + pd.DateOffset(years=69)
                
                # intialize plot -- if parameter is detritus, only make two rows of subplots because 
                # there are no transport fluxes, otherwise make three rows. number of columns is set earlier
                # based on whether we are just looking at one run, or comparing, and if comparing if we are 
                # also plotting the difference
                if include_mass:
                    addone = 1
                else:
                    addone = 0
                if 'Det' in param:
                    fig = plt.figure(figsize=figsize_detritus)
                    spec = gridspec.GridSpec(ncols=ncolumns, nrows=2+addone, figure=fig)
                else:
                    fig = plt.figure(figsize=figsize_default)
                    spec = gridspec.GridSpec(ncols=ncolumns, nrows=3+addone, figure=fig)
                fig.suptitle('Group %s' % group) 
                irow = 0

                # ... Mass time series

                if include_mass:
                # add mass
                    ax1 = fig.add_subplot(spec[irow,0])
                    ax1.plot(dataframe_ref['time'], dataframe_ref[param + ',Mass'])
                     
                    ax1.xaxis.set_major_locator(months)
                    ax1.xaxis.set_major_formatter(DateFormatter('%b'))
                    for tick in ax1.get_xticklabels():
                        tick.set_rotation(90)
                    ax1.autoscale(enable=True, axis='x', tight=True)
                    ax1.set_xlim((xmin, xmax))
                    ax1.set_ylim((0,ax1.get_ylim()[1]))
                    ax1.grid()
                    ax1.set_ylabel('%s %s (%s)' % (param, label_mass,units_mass))
                    irow = irow + 1
              
                    ax1.set_title(run_label)


                # ... Mass Budget
                if 'Det' in param:
                    
                    # ... reference run
                    ax1 = fig.add_subplot(spec[irow,0])
                    ax1.plot(dataframe_ref['time'], 
                             dataframe_ref[param + ',Net Load'],
                             '-',
                             label=(param + ',Net Load'))
                    ax1.plot(dataframe_ref['time'], 
                             dataframe_ref[param + ',Net Reaction'], 
                             '-',
                             label=(param + ',Net Reaction'))
                    ax1.plot(dataframe_ref['time'], 
                             dataframe_ref[param + ',dMass/dt, Balance Check'], 
                             '--', 
                             label=(param + ',dMass/dt'))
                    
                else:
                    
                    # ... reference run
                    ax1 = fig.add_subplot(spec[irow,0])
                    ax1.plot(dataframe_ref['time'], 
                             dataframe_ref[param + ',Net Load'],
                             '-',
                             label=(param + ',Net Load'))
                    ax1.plot(dataframe_ref['time'], 
                             dataframe_ref[param + ',Net Reaction'], 
                             '-',
                             label=(param + ',Net Reaction'))
                    ax1.plot(dataframe_ref['time'], 
                             dataframe_ref[param + ',Net Transport In'], 
                             '-', 
                             label=(param + ',Net Transport In'))

                    # in new version of balance table scripts, I seem to be getting the volume wrong, so dMass/dt does not 
                    # seem to be correct -- use the residual dMass/dt that closes mass conservation instead
                    #ax1.plot(dataframe_ref['time'], 
                    #         dataframe_ref[param + ',dMass/dt'], 
                    #         '-', 
                    #         label=(param + ',dMass/dt'))
                    #ax1.plot(dataframe_ref['time'], 
                    #         dataframe_ref[param + ',dMass/dt, Balance Check'], 
                    #         '--', 
                    #         label=(param + ',dMass/dt, Balance Check'))   
                    ax1.plot(dataframe_ref['time'], 
                             dataframe_ref[param + ',dMass/dt, Balance Check'], 
                             '-', 
                             label=(param + ',dMass/dt'))   


                
                # now do some formatting of the mass balance axis that's the same for detritus and non-detritus parameters  
                ax1.xaxis.set_major_locator(months)
                ax1.xaxis.set_major_formatter(DateFormatter('%b'))
                for tick in ax1.get_xticklabels():
                    tick.set_rotation(90)
                ax1.autoscale(enable=True, axis='x', tight=True)
                ax1.set_xlim((xmin, xmax))
                ymax = np.max(np.abs(ax1.get_ylim()))
                ax1.set_ylim(-ymax, ymax)
                ax1.grid()
                if i_integrate == 'Cumulative_':
                    ax1.set_ylabel('Cumulative Mass (' + units + ')')
                elif i_integrate == 'Filtered_':
                    ax1.set_ylabel('Filtered Rate (' + units + ')') 
                else:
                    ax1.set_ylabel('Daily Avg. Rate (' + units + ')') 
              
                # ... add legend to appropriate axis
                ax1.legend(loc='center left', bbox_to_anchor=(1,0.5))    


                if not include_mass:
                    ax1.set_title(run_label)
                irow = irow + 1

                # ... Fluxes
                if 'Det' in param:
                    pass
                else:
                
                    ax1 = fig.add_subplot(spec[irow,0])
                    ax1.plot(dataframe_ref['time'], 
                             dataframe_ref[param + ',Flux In from N'], 
                             '-', 
                             label=(param + ',Flux In from N'))
                    ax1.plot(dataframe_ref['time'], 
                             dataframe_ref[param + ',Flux In from S'], 
                             '-', 
                             label=(param + ',Flux In from S'))
                    ax1.plot(dataframe_ref['time'], 
                             dataframe_ref[param + ',Flux In from E'], 
                             '-', 
                             label=(param + ',Flux In from E'))
                    ax1.plot(dataframe_ref['time'], 
                             dataframe_ref[param + ',Flux In from W'], 
                             '-', 
                             label=(param + ',Flux In from W'))
                        
                    
                    # now do some formatting of the flux axis and add legend to appropriate axis
                    ax1.xaxis.set_major_locator(months)
                    ax1.xaxis.set_major_formatter(DateFormatter('%b'))
                    for tick in ax1.get_xticklabels():
                        tick.set_rotation(90)
                    ax1.autoscale(enable=True, axis='x', tight=True)
                    ax1.set_xlim((xmin, xmax))
                    ax1.grid()
                    ymax = np.max(np.abs(ax1.get_ylim()))
                    ax1.set_ylim(-ymax, ymax)
                    if i_integrate == 'Cumulative_':
                        ax1.set_ylabel('Cumulative Mass (' + units + ')')
                    elif i_integrate == 'Filtered_':
                        ax1.set_ylabel('Filtered Rate (' + units + ')') 
                    else:
                        ax1.set_ylabel('Daily Avg. Rate (' + units + ')') 
                    ax1.legend(loc='center left', bbox_to_anchor=(1,0.5))

                    irow = irow + 1
                    
                # ... Reactions
                if any(reaction_name_list):
                    
                    # ... reference run
                    ax1 = fig.add_subplot(spec[irow,0])
                    dataframe_ref_rx.plot.area(ax=ax1,legend=False) 
                    ax1.xaxis.set_major_formatter(DateFormatter('%b'))
                    for tick in ax1.get_xticklabels():
                        tick.set_rotation(90)
                    ax1.autoscale(enable=True, axis='x', tight=True)  
                    ax1.set_xlim((xmin_rx, xmax_rx))
                    ax1.grid()
                    ax1.set_xlabel(None)
                    if i_integrate == 'Cumulative_':
                        ax1.set_ylabel('Cumulative Mass (' + units + ')')
                    elif i_integrate == 'Filtered_':
                        ax1.set_ylabel('Filtered Rate (' + units + ')') 
                    else:
                        ax1.set_ylabel('Daily Avg. Rate (' + units + ')') 
                    ymax = np.max(np.abs(ax1.get_ylim()))
                    ax1.minorticks_off() 
                    ax1.set_xticks(ax1.get_xticks()[0:-1]) # for whavever reason, Sep label is included twice, eliminate the last one
                    
                    # now do some formatting of the flux axis and add legend to appropriate axis
                    ax1.set_ylim(-ymax, ymax)
                    ax1.legend(loc='center left', bbox_to_anchor=(1,0.5))
                    
                
                # ... Save
                fig.tight_layout(rect=[0, 0, 1, 0.98])
                fig.savefig(os.path.join(plot_folder,i_integrate + i_norm + param + '_Group_%s.png' % group))
                plt.close()
            
        

    