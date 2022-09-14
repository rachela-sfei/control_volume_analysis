
#################################################################
# USER INPUT
#################################################################
# Basic options 
Groups = 'All'
# Groups = ['SB_RMP', 'SB_RMP_east_shoal', 'SB_RMP_west_shoal', 'SB_WB', 
          # 'SB_WB_east_shoal', 'SB_WB_west_shoal','LSB'] # set to 'All' for all groups 
# Groups = ['San_Pablo_Shoal', 'San_Pablo_Channel', 'San_Pablo_Exchange'] 
Integrate = ['Filtered_'] #, 'Cumulative_',  'Daily_'] # daily = raw; filtered = spring-neap filtered; cumulative = sum over time
    
Norm = ['Mass_'] #,'Concentration_'] # options are 'Mass_' and 'Concentration_'
    
# list of composite parameters, must correspond to names in the balance files
param_list = ['DIN'] # , 'TN', 'PON','N-Diat','N-Zoopl','DetN','DO']
    
# list of paths to the balance tables of the runs we are going to compare (ref = reference run, com = comparison run) 
# this script can handle three scenarios:
#   (1) number of reference runs equals number of comparison runs, in which case runs will be compared one-to-one
#   (2) there is only one reference run and there are many comparison runs, in which case the reference run will be compared to 
#           each comparison run
#   (3) there are no comparison runs, in which case set com_folders = [] and each reference run will be plotted alone

import os
# ref_runs =  [f.name for f in os.scandir(output_dir) if f.is_dir() ]

    
ref_runs = ['/richmondvol1/hpcshared/NMS_Projects/Control_Volume_Analysis/Balance_Tables/FR18_004//']
plot_folder = '/richmondvol1/hpcshared/NMS_Projects/Control_Volume_Analysis/Plots/FR18_004_stack_plots//'


# time string indicating end of the model warm-up period (when to
# start plotting the data) in format 'YYYY-MM-DD'
start_str = '2017-10-01'


#com_runs = ['/home/alliek/mnt/hpc/hpcvol1/hpcshared/Grid141/WY2013/Source_Attribution/G141_13_018/compare_to_fullres/_postprocessing/Balance_Tables/san_jose',
            # '/home/alliek/mnt/hpc/hpcvol1/hpcshared/Grid141/WY2013/Source_Attribution/G141_13_018/compare_to_fullres/_postprocessing/Balance_Tables/ebda']
com_runs =  [] # compare_to_fullres\\_postprocessing\\Balance_Tables\\san_jose']
                
# 0.38*0.    
# labels/titles corresponding to the runs specified above
# SW took these from run log 1
ref_labels = {} 
ref_labels['G141_17_018']  = 'G141_17_018'
ref_labels['G141_17_019']  = 'Presented as the base case calibration in 2020 annual report'
ref_labels['G141_17_020']  = '$k_d$ sensitivity: use Derek model as is. Rest as in G141_17_019'
ref_labels['G141_17_021']  = '$k_d$ sensitivity: use 0.1x Derek model as is. Rest as in G141_17_019'
ref_labels['G141_17_022']  = 'Z_minfood sensitivity: Z_minfood = 0.05. Rest as in G141_17_019'
ref_labels['G141_17_023']  = 'Z_minfood sensitivity: Z_minfood = 0. Rest as in G141_17_019'
ref_labels['G141_17_024']  = 'ZP Ing: Z_JXm =125. Rest as in G141_17_019'
ref_labels['G141_17_025']  = 'ZP Ing: Z_JXm =375. Rest as in G141_17_019'
ref_labels['G141_17_026']  = 'Sediment sensitivity: set initial sediment concentrations to 0. Rest as in G141_17_019'
ref_labels['G141_17_027']  = 'Untrim $k_d$s from Jan 1 to Apr 30: Set kd multiplier=0.5. Rest as in G141_17_019. '
ref_labels['G141_17_028']  = 'Untrim $k_d$s from Jan 1 to Apr 30: Set kd multiplier=1. Rest as in G141_17_019. ' 
ref_labels['G141_17_029']  = 'Untrim $k_d$s from Jan 1 to Apr 30: Set kd multiplier=0.1. Rest as in G141_17_019. '
ref_labels['G141_17_030']  = ''
ref_labels['G141_17_031']  = 'Set ZP Ing Rate to 0. Rest as in G141_17_028.'
ref_labels['FR17_003']     = 'Current best-calibrated WY17 Model'
ref_labels['/hpcvol1/hpcshared/Full_res/Control_Volume_Analysis/WY2013/FR13_003//'] = 'WY2013 (FR13_003)'
ref_labels['/richmondvol1/hpcshared/NMS_Projects/Control_Volume_Analysis/Balance_Tables/FR18_004//'] = 'WY2018 (FR18_004)'
          #'Full Res. w/o EBDA']
#com_labels = ['Agg. Grid Base'] #,
#              #'Agg. 141 w/o EBDA']

com_labels =  [] #['25% Reduction','25% Increase','EBDA','San Central','San Jose','EMBUD']
              
#com_labels = ['25% Reduction', '25% Increase', 'Sacramento','SASM','San Joaquin',
#              'Sausalito','FS','SF Southeast','American','LG','SFO',
#              'Marin5','Shell','benicia','Millbrae','Sonoma Valley','Burlingame',
#              'Mt. View','South Bayside', 'Calistoga','Napa','South SF',
#              'San Central','Novato','St Helena','Central Marin','Palo Alto','Sunnyvale',
#              'Ch','Petaluma','Tesoro','Chevron','Phillips66','Treasure Island',
#              'DDSD','Pinole','Valero','Rodeo','Vallejo','EBDA',
#              'San Jose','West County Richmond','EBMUD','San Mateo','Yountville']              
              
# names for subfolders containing the plots for each pair of runs we are compring, or each
# single run we are plotting (if there is just one run you can set plot_subfolders = [''] to 
# put results directly in the main plot folder)
#plot_subfolders = ['minus25', 'plus25', 'false_sac','sasm','false_sj','sausalito','fs','sf_southeast','american','lg','sfo',
#              'marin5','shell','benicia','millbrae','sonoma_valley','burlingame','mt_view','south_bayside',
#              'calistoga','napa','south_sf','cccsd','novato','st_helena','central_marin','palo_alto','sunnyvale',
#              'ch','petaluma','tesoro','chevron','phillips66','treasure_island','ddsd','pinole','valero','rodeo',
#              'vallejo','ebda','san_jose','west_county_richmond','ebmud','san_mateo','yountville'] #'san_jose'] #,'ebda']

plot_subfolders = [''] #['minus25','plus25','ebda','cccsd','san_jose','ebmud']

if len(com_runs) > 0 :
    com_runs = com_runs*len(plot_subfolders) 
    for i, val in enumerate(plot_subfolders):
        com_runs[i] = com_runs[i]+val+'/'

# flag to indicate if we should plot the difference between the reference and comparison runs (only relevant for scenarios 1 and 2 above)
plot_difference = False
    
# name (and path) of folder for saving plots 



    
# flag to drop reaction terms that are always zero, and set a cutoff in Mg/d that qualifies as "zero"
drop_zero_reactions = True
zero_cutoff = 1.0e-4

#################################################################
# IMPORT PACKAGES
#################################################################

import sys, copy, os
import pandas as pd
import numpy as np
import matplotlib.pylab as plt
import matplotlib.dates as mdates
import matplotlib.gridspec as gridspec
#from matplotlib.dates import DateFormatter
import datetime as dt
from scipy.signal import butter, lfilter
#from pandas.plotting import register_matplotlib_converters
#register_matplotlib_converters()
# make month locator for plotting
months = mdates.MonthLocator(range(1,13),bymonthday=1,interval=3)  # every month
months1 = mdates.MonthLocator()
Date_fmt = mdates.DateFormatter("%b '%y")
plt.switch_backend('Agg')
####################################
# FUNCTIONS
####################################

def spring_neap_filter(y, dt_days = 1.0, low_bound=1/36.0, high_bound=1/48.0):

    """ 
    Based on Noah Knowles' tidal filter, for which low_bound = 1/(30 hr) and
    high_bound = 1/(40 hr). By analogy, since tidal period is 12.5 hours and 
    spring-neap period is 15 days, 1/30 hr translates to 1/36 days and 1/40 hr
    translates to 1/48 days. It is a bit of a misnomer to call these "bounds" 
    as in fact this filter is basically a top-hat with a slightly sloping 
    side instead of a vertical line. The low_bound and high_bound describe the
    start and end points of the sloping bit.
    
    The original default parameters 1/30 and 1/40 are derived from the article:
    1981, 'Removing Tidal-Period Variations from Time-Series Data
    Using Low Pass Filters' by Roy Walters and Cythia Heston, in
    Physical Oceanography, Volume 12, pg 112.

    Noah derived this code from the TAPPY project: 
        https://github.com/pwcazenave/tappy
    Allie King then adapted code from Noah 
    
    Usage:
        
        yf = tidal_filter(y, deltat)
        
    Input:
    
        y = time series to be filtered
        dt_days = time step between data points in days
    
    Output:
        
        yf = filtered time series
    
    """
    
    # convert low and high bounds to match series time step
    low_bound = dt_days*low_bound
    high_bound = dt_days*high_bound
    
    if len(y) % 2:
        result = np.fft.rfft(y, len(y))
    else:
        result = np.fft.rfft(y)
    freq = np.fft.fftfreq(len(y))[:len(result)]
    factor = np.ones_like(result)
    factor[freq > low_bound] = 0.0

    sl = np.logical_and(high_bound < freq, freq < low_bound)

    a = factor[sl]
    # Create float array of required length and reverse
    a = np.arange(len(a) + 2).astype(float)[::-1]

    # Ramp from 1 to 0 exclusive
    a = (a/a[0])[1:-1]

    # Insert ramp into factor
    factor[sl] = a

    result = result * factor
    yf = np.fft.irfft(result, len(y))
    
    return yf 
    
#################################################################
# MAIN
#################################################################
   
# note number of reference and comparison runs
Nref = len(ref_runs)
Ncom = len(com_runs)
   
# make sure that one of the following is true:
# (1) the number of reference and comparison runs is the same (they will be compared one-to-one), or
# (2) there is only one reference run (we will compare it to each of the comparison runs), or 
# (3) there are no comparison runs (in which case we will just plot one run without comparing)
assert (Nref==Ncom or Nref==1 or Ncom==0)

# make sure the number of labels matches the number of runs
# assert Nref==len(ref_labels)
# assert Ncom==len(com_labels)

# if there is only one reference run, copy its path and labels to match the number of comparison runs
if Nref==1 and Ncom > 0:
    Nref = Ncom    
    ref_runs = ref_runs * Ncom
    ref_labels = ref_labels * Ncom

    # check for correct number of plot subfolders
    assert Nref==len(plot_subfolders)
    
# make director(ies) for figures

for i, plot_subfolder in enumerate(plot_subfolders):
    #this_plot_folder = os.path.join(ref_runs[i],plot_folder)
    this_plot_folder = plot_folder
    print(this_plot_folder)
    if not os.path.exists(this_plot_folder):
        os.makedirs(this_plot_folder)    
    
    this_plot_subfolder = os.path.join(this_plot_folder,plot_subfolder)   
    if not os.path.exists(this_plot_subfolder):
        os.makedirs(this_plot_subfolder)
    
# set some plotting parameters
params = {'axes.labelsize': 10,
          'axes.titlesize': 10,
          'xtick.labelsize': 10,
          'ytick.labelsize': 10,
          'legend.fontsize': 8}
plt.rcParams.update(params)

# set figure size and number of columns of subplots based on whether we are comparing 
# runs with/without showing differences or just plotting a single run at a time
if Ncom==0:                         # single run at a time
    figsize_default = (6, 8)
    figsize_detritus = (6, 5.5)
    ncolumns = 1
elif not plot_difference:           # comparing runs without showing difference
    figsize_default = (9, 8)
    figsize_detritus = (9, 5.5)
    ncolumns = 2
else:                               # comparing runs and showing differences
    figsize_default = (12, 8)
    figsize_detritus = (12, 5.5)
    ncolumns = 3

BBOX = (1.02,0.1, 1.2, 0.8)

# loop through all the reference runs
for iref in range(Nref):
    #Groups = 'All'
    # retrieve correct reference and comparison run along with corresponding labels and plot subfolders
    ref_run = ref_runs[iref]
    print(ref_run)
    ref_label = ref_labels[ref_run]
    if Ncom>0:
        com_run = com_runs[iref]
        com_label = com_labels[iref]
    plot_subfolder = plot_subfolders[iref]
    print(plot_subfolder)
    # create plots for raw, spring-neap filtered, and cumulative data
    for i_integrate in Integrate:
        print(i_integrate)
        # create plots for both un-normalized (Mg/d) and normalized (g/d/m3) values
        for i_norm in Norm:
            print(i_norm)
            # loop through the parameters
            for param in param_list:
        
                # load data frame with all budget data compiled into groups for reference and comparision data
                df_ref = pd.read_csv(os.path.join(ref_run,'Balance_Table_By_Group_Composite_Parameter_' + param + '.csv'))
                
                if Groups == 'All':
                    Groups = df_ref.group.unique()
                    
                    
                if Ncom>0:
                    df_com = pd.read_csv(os.path.join(com_run,'Balance_Table_By_Group_Composite_Parameter_' + param + '.csv'))
                # print(df_ref)   
                    
                # convert time stamps to datetime objects and find time delta in units of days
                #df_ref['time'] = [dt.datetime.strptime(time,'%Y-%m-%d') for time in df_ref['time']]
                df_ref['time'] = pd.to_datetime(df_ref['time'])
                dt_days_ref = (df_ref['time'][1] - df_ref['time'][0]).total_seconds()/3600./24.
                if Ncom>0:    
                    #df_com['time'] = [dt.datetime.strptime(time,'%Y-%m-%d') for time in df_com['time']]
                    df_com['time'] = pd.to_datetime(df_com['time'])
                    dt_days_com = (df_com['time'][1] - df_com['time'][0]).total_seconds()/3600./24.
                    
                # find the list of reaction terms 
                reaction_name_list_ref = []
                for colname in df_ref.columns:
                    if (',d') in colname:
                        if not ((param + ',dMass/dt') in colname):
                            if (param == 'TN'): # Rename PP residual for TN to fit within panel
                                if ('N-Diat,dPPDiat') in colname:
                                    df_ref['PP Residual (Mg/d)'] = df_ref[colname]
                                    colname = 'PP Residual (Mg/d)'
                            reaction_name_list_ref.append(colname)
                            
                if Ncom>0:
                    reaction_name_list_com = []
                    for colname in df_com.columns:
                        if (',d') in colname:
                            if not ((param + ',dMass/dt') in colname):
                                if (param == 'TN'): # Rename PP residual for TN to fit within panel
                                    if ('N-Diat,dPPDiat') in colname:
                                        df_com['PP Residual (Mg/d)']=df_com[colname]
                                        colname = 'PP Residual (Mg/d)'                                
                                reaction_name_list_com.append(colname)
                        
                # if reactions are different for reference and comparison runs, throw an assertion error
                if Ncom>0:
                    for reaction in reaction_name_list_ref:
                        assert reaction in reaction_name_list_com
                    for reaction in reaction_name_list_com:
                        assert reaction in reaction_name_list_ref
                reaction_name_list = reaction_name_list_ref
                
                # drop reaction terms that are always zero (both from the data frame and from the list of reactions in the reaction name list)
                if drop_zero_reactions:
                    reaction_name_list_copy = copy.deepcopy(reaction_name_list)
                    for reaction_name in reaction_name_list:
                        # if there are comparison runs, require both reaction and comparison run reaciton terms to be zero
                        if Ncom>0:
                            if (not any(df_ref[reaction_name].abs() > zero_cutoff)) and (not any(df_com[reaction_name].abs() > zero_cutoff)):
                                reaction_name_list_copy.remove(reaction_name)
                                df_ref.drop(columns=[reaction_name], inplace=True)
                                df_com.drop(columns=[reaction_name], inplace=True)
                        # otherwise only have to worry about reference runs
                        else:
                            if not any(df_ref[reaction_name].abs() > zero_cutoff):
                                reaction_name_list_copy.remove(reaction_name)
                                df_ref.drop(columns=[reaction_name], inplace=True)
                    reaction_name_list = copy.deepcopy(reaction_name_list_copy)
                    del reaction_name_list_copy
                    
                # if normalized, divide by volume and change units 
                if i_norm == 'Concentration_':
                    colnames = df_ref.columns[4:]
                    for colname in colnames:
                        df_ref[colname] = df_ref[colname]/df_ref['Volume (m^3)']*1.0e6
                        df_ref.rename(columns={colname : colname.replace('Mg','g/m3')}, inplace=True)
                    units = 'g/m3/d'
                    if Ncom>0:
                        colnames = df_com.columns[4:]
                        for colname in colnames:
                            df_com[colname] = df_com[colname]/df_com['Volume (m^3)']*1.0e6
                            df_com.rename(columns={colname : colname.replace('Mg','g/m3')}, inplace=True)
                    for i in range(len(reaction_name_list)):
                        reaction_name_list[i] = reaction_name_list[i].replace('(Mg/d)','(g/m3/d)')
                else:
                    units = 'Mg/d'
                
                # if cumulative, integrate allgroups data and remove "/d" from units, starting at date defined by start_str
                if i_integrate == 'Cumulative_':  
                    colnames = df_ref.columns[4:]  
                    for colname in colnames:
                        if not ',Mass' in colname:
                            for group in np.unique(df_ref['group'].values):
                                ind = np.logical_and(df_ref['group'] == group, df_ref['time']>=pd.Timestamp(start_str))
                                df_ref.loc[ind,colname] = df_ref.loc[ind,colname].cumsum()
                            df_ref.rename(columns={colname : colname.replace('/d)',')')}, inplace=True)
                    units = units.replace('/d','')
                    if Ncom>0:   
                        colnames = df_com.columns[4:]  
                        for colname in colnames:
                            if not ',Mass' in colname:
                                for group in np.unique(df_com['group'].values):
                                    ind = np.logical_and(df_com['group'] == group, df_com['time']>=pd.Timestamp(start_str))
                                    df_com.loc[ind,colname] = df_com.loc[ind,colname].cumsum()
                                df_com.rename(columns={colname : colname.replace('/d)',')')}, inplace=True)
                    for i in range(len(reaction_name_list)):
                        reaction_name_list[i] = reaction_name_list[i].replace('/d)',')')
                        
                # otherwise if filtered apply spring-neap filter to obtained filtered time series for each field in balance table
                elif i_integrate == 'Filtered_':
                    for group in df_ref.group.unique():
                        for col in range(2,len(df_ref.columns)):
                            ind = df_ref['group']==group   # logical index selecting group
                            colname = df_ref.columns[col]  # column name 
                            df_ref.loc[ind,colname] = spring_neap_filter(df_ref.loc[ind,colname].values, dt_days_ref) # spring-neap filter
                    if Ncom>0:
                        for group in df_com.group.unique():
                            for col in range(2,len(df_com.columns)):
                                ind = df_com['group']==group   # logical index selecting group
                                colname = df_com.columns[col]  # column name 
                                df_com.loc[ind,colname] = spring_neap_filter(df_com.loc[ind,colname].values, dt_days_com) # spring-neap filter
                        
                # drop all the data during the model warmup period, before the water year starts
                start_time = np.datetime64(start_str)
                ind = df_ref['time'].values >=start_time
                df_ref = df_ref.loc[ind,:]
                if Ncom>0:
                    ind = df_com['time']>=start_time
                    df_com = df_com.loc[ind,:]
                                        
                # make sure sources stay positive and sinks stay negative
                # (this is necessary for making stack plots, which are mostly messed up 
                # when 0.0 is represented as -0.0 and vice versa)
                for reaction_name in reaction_name_list:
                    if df_ref[reaction_name].mean() >= 0.0:
                        ind = df_ref[reaction_name] < 0.0
                        if any(ind):
                            df_ref.loc[ind,reaction_name] = 0.0
                    else:
                        ind = df_ref[reaction_name] > 0.0
                        if any(ind):
                            df_ref.loc[ind,reaction_name] = -0.0
                if Ncom>0:
                    for reaction_name in reaction_name_list:
                        if df_com[reaction_name].mean() >= 0.0:
                            ind = df_com[reaction_name] < 0.0
                            if any(ind):
                                df_com.loc[ind,reaction_name] = 0.0
                        else:
                            ind = df_com[reaction_name] > 0.0
                            if any(ind):
                                df_com.loc[ind,reaction_name] = -0.0
                                
                # Groups == 'All'             
                # # loop through the groups and plot budgets for each group
              
                    
                for group in Groups: 
                    print(group)
                    # throw an assertion error if group doesn't exit in comparison run balance table
                    if Ncom>0:
                        assert (group in df_com.group.values)
                
                    # logical index to select data in this group, and reset starting index at zero
                    ind = df_ref['group'] == group
                    dataframe_ref = df_ref.loc[ind,:].copy(deep=True).reset_index()
                    if len(dataframe_ref) == 0:
                        print('Skipping group %s' % group)
                        continue 
                    xmin = dataframe_ref['time'].iloc[0]
                    xmax = dataframe_ref['time'].iloc[-1]
                        
                    if Ncom>0:
                        ind = df_com['group'] == group
                        dataframe_com = df_com[ind].copy(deep=True).reset_index()
                    # select subset of dataframe corresponding to reactions for this parameter, and set index
                    # to the time stamp, so stack plot will work properly. Note for some reason have to add 
                    # 1969 to date to get the right year in the plot
                    dataframe_ref_rx = dataframe_ref[reaction_name_list].copy(deep=True)
                    dataframe_ref_rx = dataframe_ref_rx.set_index(dataframe_ref['time']) #.apply(lambda x: x + pd.DateOffset(years=69))) 
                    if Ncom>0:
                        dataframe_com_rx = dataframe_com[reaction_name_list].copy(deep=True)
                        dataframe_com_rx = dataframe_com_rx.set_index(dataframe_com['time']) #.apply(lambda x: x + pd.DateOffset(years=69))) 
                        
                    # if there are comparison plots and we are plotting differences, make sure the time axes have the same starting time
                    # and time step, and chose the longer time series for plotting (one may be longer than the other if one or both 
                    # simulations did not run to completion). also set the x limits for plotting, chosing the widest time window
                    if Ncom>0 and plot_difference:
                        assert dataframe_ref['time'].iloc[0] == dataframe_com['time'].iloc[0]
                        assert (dataframe_ref['time'].iloc[1] - dataframe_ref['time'].iloc[0]) == (dataframe_com['time'].iloc[1] - dataframe_com['time'].iloc[0])
                        if len(dataframe_ref['time']) >= len(dataframe_com['time']):
                            difftimes = dataframe_ref['time']
                        else:
                            difftimes = dataframe_com['time'] 
                    # if Ncom>0:
                    #     if dataframe_ref['time'].iloc[0] <= dataframe_com['time'].iloc[0]:
                    #         xmin = dataframe_ref['time'].iloc[0]
                    #     else:
                    #         xmin = dataframe_com['time'].iloc[0] 
                    #     if dataframe_ref['time'].iloc[-1] >= dataframe_com['time'].iloc[-1]:
                    #         xmax = dataframe_ref['time'].iloc[-1]
                    #     else:
                    #         xmax = dataframe_com['time'].iloc[-1]
                    # else:
                    #     xmin = dataframe_ref['time'].iloc[0]
                    #     xmax = dataframe_ref['time'].iloc[-1]
                    xmin_rx = xmin + pd.DateOffset(years=69)
                    xmax_rx = xmax + pd.DateOffset(years=69)
                    
                    # intialize plot -- if parameter is detritus, only make two rows of subplots because 
                    # there are no transport fluxes, otherwise make three rows. number of columns is set earlier
                    # based on whether we are just looking at one run, or comparing, and if comparing if we are 
                    # also plotting the difference
                    if 'Det' in param:
                        fig = plt.figure(figsize=figsize_detritus)
                        spec = gridspec.GridSpec(ncols=ncolumns, nrows=2, figure=fig)
                    else:
                        fig = plt.figure(figsize=figsize_default)
                        spec = gridspec.GridSpec(ncols=ncolumns, nrows=3, figure=fig)
                    
                    # ... Mass Budget
                    if 'Det' in param:
                        
                        # ... reference run
                        ax1 = fig.add_subplot(spec[0,0])
                        ax1.plot(dataframe_ref['time'], 
                                 dataframe_ref[param + ',Net Load (' + units + ')'],
                                 '-',
                                 label=(param + ',Net Load (' + units + ')'))
                        ax1.plot(dataframe_ref['time'], 
                                 dataframe_ref[param + ',Net Reaction (' + units + ')'], 
                                 '-',
                                 label=(param + ',Net Reaction (' + units + ')'))
                        ax1.plot(dataframe_ref['time'], 
                                 dataframe_ref[param + ',dMass/dt, Balance Check (' + units + ')'], 
                                 '--', 
                                 label=(param + ',dMass/dt (' + units + ')'))
                        ax1.set_title(ref_label)
                        ymax = np.max(np.abs(ax1.get_ylim())) 
                        
                        # ... comparison run
                        if Ncom>0:    
                            ax2 = fig.add_subplot(spec[0,1])
                            ax2.plot(dataframe_com['time'], 
                                     dataframe_com[param + ',Net Load (' + units + ')'], 
                                     '-', 
                                     label=(param + ',Net Load (' + units + ')'))
                            ax2.plot(dataframe_com['time'], 
                                     dataframe_com[param + ',Net Reaction (' + units + ')'], 
                                     '-', 
                                     label=(param + ',Net Reaction (' + units + ')'))
                            ax2.plot(dataframe_com['time'], 
                                     dataframe_com[param + ',dMass/dt, Balance Check (' + units + ')'], 
                                     '--', 
                                     label=(param + ',dMass/dt (' + units + ')'))
                            ax2.set_title(com_label)                            
                            ymax = np.max([ymax, np.max(np.abs(ax2.get_ylim()))])
                            
                        # ... difference between reference and comparison runs
                        if Ncom>0 and plot_difference:
                            ax3 = fig.add_subplot(spec[0,2])
                            ax3.plot(difftimes, 
                                     dataframe_ref[param + ',Net Load (' + units + ')'] - dataframe_com[param + ',Net Load (' + units + ')'], 
                                     '-', 
                                     label=(param + ',Net Load (' + units + ')'))
                            ax3.plot(difftimes, 
                                     dataframe_ref[param + ',Net Reaction (' + units + ')'] - dataframe_com[param + ',Net Reaction (' + units + ')'], 
                                     '-', 
                                     label=(param + ',Net Reaction (' + units + ')'))
                            ax3.plot(difftimes, 
                                     dataframe_ref[param + ',dMass/dt, Balance Check (' + units + ')'] - dataframe_com[param + ',dMass/dt, Balance Check (' + units + ')'],
                                      '--', 
                                      label=(param + ',dMass/dt (' + units + ')'))
                            ax3.set_title('(' + ref_label + ') - (' + com_label + ')')                          
                            ymax = np.max([ymax, np.max(np.abs(ax3.get_ylim()))])
                    
                    else:
                        
                        # ... reference run
                        ax1 = fig.add_subplot(spec[0,0])
                        ax1.plot(dataframe_ref['time'], 
                                 dataframe_ref[param + ',Net Load (' + units + ')'],
                                 '-',
                                 label=(param + ',Net Load (' + units + ')'))
                        ax1.plot(dataframe_ref['time'], 
                                 dataframe_ref[param + ',Net Reaction (' + units + ')'], 
                                 '-',
                                 label=(param + ',Net Reaction (' + units + ')'))
                        ax1.plot(dataframe_ref['time'], 
                                 dataframe_ref[param + ',Net Transport In (' + units + ')'], 
                                 '-', 
                                 label=(param + ',Net Transport In (' + units + ')'))
                        ax1.plot(dataframe_ref['time'], 
                                 dataframe_ref[param + ',dMass/dt (' + units + ')'], 
                                 '-', 
                                 label=(param + ',dMass/dt (' + units + ')'))
                        ax1.plot(dataframe_ref['time'], 
                                 dataframe_ref[param + ',dMass/dt, Balance Check (' + units + ')'], 
                                 '--', 
                                 label=(param + ',dMass/dt, Balance Check (' + units + ')'))   
                        ax1.set_title(ref_label)                       
                        ymax = np.max(np.abs(ax1.get_ylim())) 
                                
                        # ... comparison run
                        if Ncom>0:    
                            ax2 = fig.add_subplot(spec[0,1])
                            ax2.plot(dataframe_com['time'], 
                                     dataframe_com[param + ',Net Load (' + units + ')'], 
                                     '-', 
                                     label=(param + ',Net Load (' + units + ')'))
                            ax2.plot(dataframe_com['time'], 
                                     dataframe_com[param + ',Net Reaction (' + units + ')'], 
                                     '-', 
                                     label=(param + ',Net Reaction (' + units + ')'))
                            ax2.plot(dataframe_com['time'], 
                                     dataframe_com[param + ',Net Transport In (' + units + ')'], 
                                     '-', 
                                     label=(param + ',Net Transport In (' + units + ')'))
                            ax2.plot(dataframe_com['time'], 
                                     dataframe_com[param + ',dMass/dt (' + units + ')'], 
                                     '-', 
                                     label=(param + ',dMass/dt (' + units + ')'))
                            ax2.plot(dataframe_com['time'], 
                                     dataframe_com[param + ',dMass/dt, Balance Check (' + units + ')'], 
                                     '--', 
                                     label=(param + ',dMass/dt, Balance Check (' + units + ')'))
                            ax2.set_title(com_label)                            
                            ymax = np.max([ymax, np.max(np.abs(ax2.get_ylim()))])
                            
                        # ... difference between reference and comparison runs
                        if Ncom>0 and plot_difference:
                            ax3 = fig.add_subplot(spec[0,2])
                            ax3.plot(difftimes, 
                                     dataframe_ref[param + ',Net Load (' + units + ')'] - dataframe_com[param + ',Net Load (' + units + ')'], 
                                     '-', 
                                     label=(param + ',Net Load (' + units + ')'))
                            ax3.plot(difftimes, 
                                     dataframe_ref[param + ',Net Reaction (' + units + ')'] - dataframe_com[param + ',Net Reaction (' + units + ')'], 
                                     '-', 
                                     label=(param + ',Net Reaction (' + units + ')'))
                            ax3.plot(difftimes, 
                                     dataframe_ref[param + ',Net Transport In (' + units + ')'] - dataframe_com[param + ',Net Transport In (' + units + ')'], 
                                     '-', 
                                     label=(param + ',Net Transport In (' + units + ')'))
                            ax3.plot(difftimes, 
                                     dataframe_ref[param + ',dMass/dt (' + units + ')'] - dataframe_com[param + ',dMass/dt (' + units + ')'], 
                                     '-', 
                                     label=(param + ',dMass/dt (' + units + ')'))
                            ax3.plot(difftimes, 
                                     dataframe_ref[param + ',dMass/dt, Balance Check (' + units + ')'] - dataframe_com[param + ',dMass/dt, Balance Check (' + units + ')'], 
                                     '--', 
                                     label=(param + ',dMass/dt, Balance Check (' + units + ')'))
                            ax3.set_title('(' + ref_label + ') - (' + com_label + ')')                           
                            ymax = np.max([ymax, np.max(np.abs(ax3.get_ylim()))])
                    
                    # now do some formatting of the mass balance axis that's the same for detritus and non-detritus parameters  
                    fig.suptitle('Group %s' % group)  
                    
                    # ... reference run
                    ax1.xaxis.set_major_locator(months)
                    ax1.set_xticklabels([])   
                    #ax1.xaxis.set_major_formatter(Date_fmt)
#                    for tick in ax1.get_xticklabels():
#                        tick.set_rotation(45)
                    ax1.set_ylim(-ymax, ymax)
                    #ax1.autoscale(enable=True, axis='x', tight=True)
                    ax1.set_xlim((xmin, xmax))                                      
                    ax1.grid()
                    if i_integrate == 'Cumulative_':
                        ax1.set_ylabel(param + ', Cumulative')
                    else:
                        ax1.set_ylabel(param + ', Rate') 
                         
                    # ... comparison run
                    if Ncom>0:
                        ax2.xaxis.set_major_locator(months)
                        #ax2.xaxis.set_major_formatter(Date_fmt)
                        ax2.set_xticklabels([]) 
                        ax2.set_yticklabels([])
#                        for tick in ax2.get_xticklabels():
#                            tick.set_rotation(45)
                        ax2.set_ylim(-ymax, ymax)
#                        ax2.autoscale(enable=True, axis='x', tight=True)
                        ax2.set_xlim((xmin, xmax))
                        ax2.grid()
#                        if i_integrate == 'Cumulative_':
#                            ax2.set_ylabel(param + ', Cumulative')
#                        else:
#                            ax2.set_ylabel(param + ', Rate')
                            
                    # ... difference between reference and comparison runs
                    if Ncom>0 and plot_difference:
                        ax3.xaxis.set_major_locator(months)
                        ax3.set_xticklabels([])       
                        ax3.set_yticklabels([])
#                        ax3.xaxis.set_major_formatter(Date_fmt)
#                        for tick in ax3.get_xticklabels():
#                            tick.set_rotation(45)
                        ax3.set_ylim(-ymax, ymax)
#                        ax3.autoscale(enable=True, axis='x', tight=True)
                        ax3.set_xlim((xmin, xmax))
                        ax3.grid()
#                        if i_integrate == 'Cumulative_':
#                            ax3.set_ylabel(param + ', Cumulative')
#                        else:
#                            ax3.set_ylabel(param + ', Rate')
                            
                    # ... add legend to appropriate axis
                    if Ncom==0:
                        ax1.legend(loc='center left', bbox_to_anchor=BBOX)
                    elif not plot_difference:
                        ax2.legend(loc='center left', bbox_to_anchor=BBOX) 
                    else:
                        ax3.legend(loc='center left', bbox_to_anchor=BBOX)
                    
                    # ... Fluxes
                    if 'Det' in param:
                        pass
                    else:
                    
                        # ... reference run
                        ax1 = fig.add_subplot(spec[1,0])
                        ax1.plot(dataframe_ref['time'], 
                                 dataframe_ref[param + ',Flux In from N (' + units + ')'], 
                                 '-', 
                                 label=(param + ',Flux In from N (' + units + ')'))
                        ax1.plot(dataframe_ref['time'], 
                                 dataframe_ref[param + ',Flux In from S (' + units + ')'], 
                                 '-', 
                                 label=(param + ',Flux In from S (' + units + ')'))
                        ax1.plot(dataframe_ref['time'], 
                                 dataframe_ref[param + ',Flux In from E (' + units + ')'], 
                                 '-', 
                                 label=(param + ',Flux In from E (' + units + ')'))
                        ax1.plot(dataframe_ref['time'], 
                                 dataframe_ref[param + ',Flux In from W (' + units + ')'], 
                                 '-', 
                                 label=(param + ',Flux In from W (' + units + ')'))
                        ax1.xaxis.set_major_locator(months)
                        ax1.set_xticklabels([])                           
#                        ax1.xaxis.set_major_formatter(Date_fmt)
#                        for tick in ax1.get_xticklabels():
#                            tick.set_rotation(45)
#                        ax1.autoscale(enable=True, axis='x', tight=True)
                        ax1.set_xlim((xmin, xmax))
                        ax1.grid()
                        if i_integrate == 'Cumulative_':
                            ax1.set_ylabel(param + ', Cumulative')
                        else:
                            ax1.set_ylabel(param + ', Rate') 
                        ymax = np.max(np.abs(ax1.get_ylim()))
                            
                        # ... comparison run
                        if Ncom>0:    
                            ax2 = fig.add_subplot(spec[1,1])
                            ax2.plot(dataframe_com['time'], 
                                     dataframe_com[param + ',Flux In from N (' + units + ')'], 
                                     '-', 
                                     label=(param + ',Flux In from N (' + units + ')'))
                            ax2.plot(dataframe_com['time'], 
                                     dataframe_com[param + ',Flux In from S (' + units + ')'], 
                                     '-', 
                                     label=(param + ',Flux In from S (' + units + ')'))
                            ax2.plot(dataframe_com['time'], 
                                     dataframe_com[param + ',Flux In from E (' + units + ')'], 
                                     '-', 
                                     label=(param + ',Flux In from E (' + units + ')'))
                            ax2.plot(dataframe_com['time'], 
                                     dataframe_com[param + ',Flux In from W (' + units + ')'], 
                                     '-', 
                                     label=(param + ',Flux In from W (' + units + ')'))
                            ax2.xaxis.set_major_locator(months)
                            ax2.set_xticklabels([])        
                            ax2.set_yticklabels([])
#                            ax2.xaxis.set_major_formatter(Date_fmt)
#                            for tick in ax2.get_xticklabels():
#                                tick.set_rotation(45)
#                            ax2.autoscale(enable=True, axis='x', tight=True)
                            ax2.set_xlim((xmin, xmax))
                            ax2.grid()
#                            if i_integrate == 'Cumulative_':
#                                ax2.set_ylabel(param + ', Cumulative')
#                            else:
#                                ax2.set_ylabel(param + ', Rate')
                            ymax = np.max([ymax, np.max(np.abs(ax2.get_ylim()))])
                            
                        # ... difference between reference and comparison runs
                        if Ncom>0 and plot_difference:
                            ax3 = fig.add_subplot(spec[1,2])
                            ax3.plot(difftimes, 
                                     dataframe_ref[param + ',Flux In from N (' + units + ')'] - dataframe_com[param + ',Flux In from N (' + units + ')'], 
                                     '-', 
                                     label=(param + ',Flux In from N (' + units + ')'))
                            ax3.plot(difftimes, 
                                     dataframe_ref[param + ',Flux In from S (' + units + ')'] - dataframe_com[param + ',Flux In from S (' + units + ')'], 
                                     '-', 
                                     label=(param + ',Flux In from S (' + units + ')'))
                            ax3.plot(difftimes, 
                                     dataframe_ref[param + ',Flux In from E (' + units + ')'] - dataframe_com[param + ',Flux In from E (' + units + ')'], 
                                     '-', 
                                     label=(param + ',Flux In from E (' + units + ')'))
                            ax3.plot(difftimes, 
                                     dataframe_ref[param + ',Flux In from W (' + units + ')'] - dataframe_com[param + ',Flux In from W (' + units + ')'], 
                                     '-', 
                                     label=(param + ',Flux In from W (' + units + ')'))                            
                            ax3.xaxis.set_major_locator(months)
                            ax3.set_xticklabels([])     
                            ax3.set_yticklabels([])                            
#                            ax3.xaxis.set_major_formatter(Date_fmt)
#                            for tick in ax3.get_xticklabels():
#                                tick.set_rotation(45)
#                            ax3.autoscale(enable=True, axis='x', tight=True)
                            ax3.set_xlim((xmin, xmax))
                            ax3.grid()
#                            if i_integrate == 'Cumulative_':
#                                ax3.set_ylabel(param + ', Cumulative')
#                            else:
#                                ax3.set_ylabel(param + ', Rate')
                            ymax_diff = np.max(np.abs(ax3.get_ylim()))
                            ax3.set_ylim(-ymax, ymax)
                        
                        # now do some formatting of the flux axis and add legend to appropriate axis
                        ax1.set_ylim(-ymax, ymax)
                        if Ncom>0:
                            ax2.set_ylim(-ymax, ymax)
                        if Ncom==0:
                            ax1.legend(loc='center left', bbox_to_anchor=BBOX)
                        elif not plot_difference:
                            ax2.legend(loc='center left', bbox_to_anchor=BBOX) 
                        else:
                            ax3.legend(loc='center left', bbox_to_anchor=BBOX)
                    
                    # ... Reactions
                    if any(reaction_name_list):
                        
                        # ... reference run
                        if 'Det' in param:
                            ax1 = fig.add_subplot(spec[1,0])
                        else:
                            ax1 = fig.add_subplot(spec[2,0])
                        #
                        Y = dataframe_ref_rx.values
                        Y = np.transpose(Y)
                        
                        # the following shows the x-axis correctly, but does not stack the 
                        # reactions on either side of 0 like Pandas area plot does
                        #ax1.stackplot(dataframe_ref_rx.index, Y, baseline='sym')
                        
                        # very clunky fix to overcome the issue with the x-axis not 
                        # showing correctly when using Pandas area plot 
                        ax2d = ax1.twiny()
                        
                        if plot_difference:
                            ax2d = dataframe_ref_rx.plot.area(ax=ax2d,legend=False)
                        else:
                            ax2d = dataframe_ref_rx.plot.area(ax=ax2d)
                        #ax2d.set_yticklabels([])
                        ax2d.set_xticklabels([])
                        ax2d.set_xticks([])
                        ax2d.minorticks_off() 
                        # ax2d.set_ylabel(None)
                        ax2d.set_xlabel('')     # need this SW                    
#                        ax1.plot()
                        ymax = np.max(np.abs(ax2d.get_ylim()))
                        xlim = (xmin, xmax)
                        ax1.scatter(xlim, (-ymax,ymax), marker='.', 
                                    s = 0.0001, c = 'k')                        
                        
                        ax1.xaxis.set_major_locator(months)  
                        ax1.xaxis.set_minor_locator(months1)
                        ax1.xaxis.set_major_formatter(Date_fmt)
#                        for tick in ax1.get_xticklabels():
#                            tick.set_rotation(45)
                        ax1.autoscale(enable=True, axis='x', tight=True)  
                        ax1.set_xlim((xmin, xmax))
                        # rotate_labels...
#                        for label in ax1.get_xticklabels():
#                            label.set_rotation(60)
#                            label.set_horizontalalignment('right')                         
                        ax1.grid()
                        # ax1.set_xlabel(None)
                        if i_integrate == 'Cumulative_':
                            ax1.set_ylabel(param + ', Cumulative')
                        else:
                            ax1.set_ylabel(param + ', Rate')
                        #ax1.minorticks_off() 
                        ymax = np.max(np.abs(ax1.get_ylim()))
                        # ... comparison case
                        if Ncom>0:
                            if 'Det' in param:
                                ax2 = fig.add_subplot(spec[1,1])
                            else:
                                ax2 = fig.add_subplot(spec[2,1])
                            
                            # very clunky fix to overcome the issue with the x-axis not showing correctly when using Pandas area plot 
                            ax2d = ax2.twiny()
                            ax2d = dataframe_com_rx.plot.area(ax=ax2d,legend=False)  
                            ax2d.minorticks_off() 
                            ax2d.set_yticklabels([])
                            ax2d.set_xticklabels([])
                            ax2d.set_xticks([])
                            # ax2d.set_ylabel(None)
                            ax2d.set_xlabel('')
                            
                            ymax = np.max([ymax, np.max(np.abs(ax2d.get_ylim()))])
                            xlim = (xmin, xmax)
                            ax2.scatter(xlim, (-ymax,ymax), marker='.', 
                                        s = 0.0001, c = 'k')
                            
                            #Y = dataframe_com_rx.to_numpy()
                            #ax2.stackplot(dataframe_com_rx.index.values,np.transpose(Y),baseline='sym')
                            ax2.xaxis.set_major_locator(months)
                            ax2.xaxis.set_minor_locator(months1)
                            ax2.xaxis.set_major_formatter(Date_fmt)
#                            for tick in ax2.get_xticklabels():
#                                tick.set_rotation(45)
                            #ax2.autoscale(enable=True, axis='x', tight=True)  
                            
                            ax2.set_yticklabels([])  
#                            for label in ax2.get_xticklabels():
#                                label.set_rotation(60)
#                                label.set_horizontalalignment('right')                             
                            ax2.grid()
                            # ax2.set_xlabel(None)
#                            if i_integrate == 'Cumulative_':
#                                ax2.set_ylabel(param + ', Cumulative')
#                            else:
#                                ax2.set_ylabel(param + ', Rate')
                            #ax2.minorticks_off() 
                            
                            
                            
                            
                            
                        
                        # ... difference between reference and comparison runs
                        if Ncom>0 and plot_difference:
                            if 'Det' in param:
                                ax3 = fig.add_subplot(spec[1,2])
                            else:
                                ax3 = fig.add_subplot(spec[2,2])
                            # loop through reactions
                            for icol in range(len(dataframe_ref_rx.columns)):
                                # make sure reactions appear in same order for ref vs. com runs -- if not throw assertion error
                                assert dataframe_ref_rx.columns[icol] == dataframe_com_rx.columns[icol] 
                                # now select a column and plot it
                                col = dataframe_ref_rx.columns[icol]
                                ax3.plot(difftimes, 
                                     dataframe_ref_rx[col] - dataframe_com_rx[col], 
                                     '-', 
                                     label=col)                           
                            ax3.xaxis.set_major_locator(months)
                            ax3.xaxis.set_minor_locator(months1)
                            ax3.xaxis.set_major_formatter(Date_fmt)
#                            for tick in ax3.get_xticklabels():
#                                tick.set_rotation(45)
#                            ax3.autoscale(enable=True, axis='x', tight=True)
                            ax3.set_xlim((xmin, xmax))
#                            for label in ax3.get_xticklabels():
#                                label.set_rotation(60)
#                                label.set_horizontalalignment('right')                             
                            ax3.grid()
#                            if i_integrate == 'Cumulative_':
#                                ax3.set_ylabel(param + ', Cumulative')
#                            else:
#                                ax3.set_ylabel(param + ', Rate')
                            ymax_diff = np.max(np.abs(ax3.get_ylim()))
                            ax3.set_ylim(-ymax, ymax)
                            ax3.set_yticklabels([])  
                        
                        # now do some formatting of the flux axis and add legend to appropriate axis
                        ax1.set_ylim(-ymax, ymax)
                        if Ncom>0:
                            ax2.set_ylim(-ymax, ymax)
                        if Ncom==0:
                            #ax1.legend(loc='center left', bbox_to_anchor=BBOX)
                            ax2d.legend(loc='center left', bbox_to_anchor=BBOX)
                        elif not plot_difference:
                            ax2.legend(loc='center left', bbox_to_anchor=BBOX) 
                        else:
                            ax3.legend(loc='center left', bbox_to_anchor=BBOX)
                        
                    
                    # ... Save ref_runs[iref]+
                    fig.tight_layout(rect=[0, 0.03, 1, 0.95])
                    fig.autofmt_xdate()     
                    picname = plot_folder+'/'+plot_subfolder+'/'+i_integrate + i_norm + param + '_Group_{:s}.png'.format(group)
                    print('Saved %s' % picname)
                    fig.savefig(picname, dpi = 200)
                    plt.close()
                    
            
    
            



