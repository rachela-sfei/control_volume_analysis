
# automatically finds all balance tables in folder, including balance tables for base level
# substances (e.g. no3_Table.csv), balance tables for composite substances, after the reactions
# have been grouped (e.g. din_Table.csv), and balance tables for both base level and composite
# substances that have been aggregated into spatial groups (e.g. din_Table_By_Group.csv, 
# din_Table_By_Group.csv) THEN applies a spring-neap filter and a cumulative sum by water year, 
# and also does monthly and seasonal averages and weekly averages, which time averages to do is 
# specified in config.py

########################################################################################
# import python packages
########################################################################################

import sys, os
import pandas as pd
import numpy as np
import matplotlib.pylab as plt
import datetime as dt
import logging
import socket
from scipy.signal import butter, filtfilt
hostname = socket.gethostname()
import step0_config

# if running the script alone, load the configuration module (in this folder)
if __name__ == "__main__":

    import importlib
    importlib.reload(step0_config)

######################
# functions
######################

def logger_cleanup():

    ''' check for open log files, close them, release handlers'''

    # clean up logging
    logger = logging.getLogger()
    handlers = list(logger.handlers)
    if len(handlers)>0:
        for handler in handlers:
            handler.close()
            logger.removeHandler(handler) 

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
    b, a = butter(N, Wn, 'low')
   
    # subtract the mean
    ym = np.mean(y)

    # filter the signal
    yf = filtfilt(b,a,y-ym,padtype='constant') + ym
   
    # return fitlered signal
    return yf


def semidi_filter(y, dt_hrs = 1., fcut = 1/35., N = 4):

    """
    Performs a tidal filter on the y series using a 4th order low pass
    butterworth filter and constant padding
   
    Usage:
       
        yf = semidi_filter(y, dt_hrs=1.0, fcut = 1/35, N=4.)
       
    Input:
       
        y    = time series
        dt_hrs   = time step (unit is hours)
        fcut = cutoff frequency in 1/hours
               
    Output:
   
        yf   = tidally filtered signal
   
    """
   
    # compute sampling frequency from time step
    fs = 1/dt_hrs
   
    # compute dimensionless cutoff frequency w.r.t. Nyquist frequency
    Wn = fcut/(0.5*fs)
   
    # compute filter coefficients
    b, a = butter(N, Wn, 'low')

    # subtract the mean
    ym = np.mean(y)
   
    # filter the signal
    yf = filtfilt(b,a,y-ym,padtype='constant') + ym
   
    # return fitlered signal
    return yf

###########################################################################################
# load dictionaries that define the groups (A, B, C, etc.) by the list of control volumes
# that make up each group (group_dict) and the list of pairs of control volumes making up
# fluxes out of the N, S, E, and W faces of each group (flux_pairs_dict)
###########################################################################################

# setup logging to file and to screen 
logger_cleanup()
logging.basicConfig(
level=logging.INFO,
format="%(asctime)s [%(levelname)s] %(message)s",
handlers=[
    logging.FileHandler(os.path.join(step0_config.balance_table_dir,"log_step6.log"),'w'),
    logging.StreamHandler(sys.stdout)
])

# add some basic info to log file
user = os.getlogin()
scriptname= __file__
conda_env=os.environ['CONDA_DEFAULT_ENV']
today= dt.datetime.now().strftime('%b %d, %Y')
logging.info('Time aggregated balance tables were produced on %s by %s on %s in %s using %s' % (today, user, hostname, conda_env, scriptname))

# if continuity is in list of substances to plot, include the flow_m3s tables
if 'continuity' in step0_config.plot_substance_list:
    step0_config.plot_substance_list.append('flow_m3s')

# get a list of all the files in the balance table directory, and pick out the ones with the format
# (param)_Table.csv or (param)_Table_By_Group.csv
table_list = []
file_list = os.listdir(step0_config.balance_table_dir)
for file in file_list:
    if 'Table.csv' in file:
        param = file[0:-10]
        if param in step0_config.plot_substance_list:
            table_list.append(file)
    elif 'Table_By_Group.csv' in file:
        table_list.append(file)

# output number of parameters and types of parameters found 
logging.info('Scanned directory %s for files with format PARAM_Table.csv and PARAM_Table_By_Group.csv where PARAM is in ' % step0_config.balance_table_dir + 
             'step0_config.plot_substance_list and retrieved following list of balance tables:')
for table in table_list:
    logging.info('   %s' % table)

# loop through the tables
for balance_table_fn in table_list:

    # print
    logging.info('Reading %s ...' % balance_table_fn)

    # determine if balance table is by group or not
    if 'By_Group' in balance_table_fn:
        by_group = True
    else:
        by_group = False

    # determine if balance table is the special high frequency flow rate one we are going to use to compute residence time
    if 'flow_m3s' in balance_table_fn:
        is_flow = True
    else:
        is_flow = False

    # read in the balance table corresponding to this parameter
    df = pd.read_csv(os.path.join(step0_config.balance_table_dir,balance_table_fn))

    # convert time to datetime64
    df['time'] = df['time'].astype('datetime64')

    # need to find the name of the parameter in the table, use the "PARAM,Loads in"
    # column and take everything before the comma
    if is_flow:
        param = 'Continuity'
    else:
        for col in df.columns:
            if by_group:
                if ',Net Load (Mg/d)' in col:
                    param = col.split(',')[0]
            else:
                if ',Loads in' in col:
                    param = col.split(',')[0]

    # print
    logging.info('    Identified substance as %s' % param)

    # in some of our runs, the initial loading value is zero, which messes with the tidal filter, 
    # so check if this is the case, and if so, replace with the second loading value ... 
    if not is_flow:
        t0 = df['time'].iloc[0]
        t1 = df['time'].iloc[1]
        ind0 = df['time'].values==t0 
        ind1 = df['time'].values==t1
        if by_group:
            df.loc[ind0,'%s,Net Load (Mg/d)' % param] = df.loc[ind1,'%s,Net Load (Mg/d)' % param].values[0]
        else:
            df.loc[ind0,'%s,Loads in' % param] = df.loc[ind1,'%s,Loads in' % param].values[0]

    # find the set of water years available in this run
    time = np.unique(df.time)
    yr = pd.Timestamp(time.min()).year - 1
    yrmax = pd.Timestamp(time.max()).year
    wy_list = []
    wy_list = [yr+1]
    while yr<=yrmax:
        if (np.datetime64('%d-10-01' % yr) >= time[0]) and (sum(time>=np.datetime64('%d-10-01' % yr))>0):
            wy_list.append(yr+1)
        yr += 1

    # time step in days
    deltat_days = (time[1]-time[0])/np.timedelta64(1,'D')

    # print water years
    logging.info('    Identified following water years in balance table: %s' % wy_list ) 

    # name of the group column and list of the unique groups
    if by_group:
        group_col = 'group'
        volume_col = 'Volume (m^3)'
    else:
        group_col = 'Control Volume'
        volume_col = 'Volume'
    group_list = np.unique(df[group_col])

    # if we are operating on flow rates here, we need to take a moment to compute the tidally filtered mean
    # and root mean square deviation from that mean, along each side, to get advection and dispersion
    if is_flow:

        # output 
        logging.info('    Computing semidiurnal filtered flow rate and root mean square...') 
        
        # time step in hours
        deltat_hrs = (time[1]-time[0])/np.timedelta64(1,'h')

        # start a new dataframe that will contain <Q> and 0.12 <(Q-<Q>)^2>^0.5
        cols = []
        for col in df.columns:
            if not 'Flux' in col:
                cols.append(col)
        df_F = df[cols].copy(deep=True)

        # take the tidal filter of volume
        V = np.zeros(len(df))
        for group in group_list:
            ind = df[group_col].values == group
            V[ind] = semidi_filter(df.loc[ind][volume_col].values, dt_hrs = deltat_hrs, fcut = 1/35., N = 4)
        df_F[volume_col] = V.copy()

        # if this is at the polygon level
        if not by_group:

            # count the number of fields labeled "To_polyN" where N is an integer
            n2poly = 0
            for col in df.columns:
                if 'To_poly' in col:
                    n2poly = n2poly + 1

            # loop through them
            for ipoly in range(n2poly):

                Q = np.nan * np.ones(len(df))
                Qavg = Q.copy()
                Qrms = Q.copy() 
                for group in group_list:

                    ind = df['Control Volume'].values == group
                    Q[ind] = df.loc[ind]['Flux%d' % ipoly].values
                    if np.sum(np.isnan(Q[ind]))==0:
                        Qavg[ind] = semidi_filter(Q[ind], dt_hrs = deltat_hrs, fcut = 1/35., N = 4)
                        Qms = semidi_filter((Q[ind] - Qavg[ind])**2, dt_hrs = deltat_hrs, fcut = 1/35., N = 4)
                        Qms[Qms<0] = 0
                        Qrms[ind] = np.sqrt(Qms)

                df_F['<Q>%d' % ipoly] = Qavg.copy()
                df_F['%0.2fsqrt(<(Q-<Q>)^2>)%d' % (step0_config.alpha,ipoly)] = step0_config.alpha * Qrms.copy()

        else:

            # count the number of fluxes to track in each direction (n2poly is weird notation here)
            n2poly = 0
            for col in df.columns:
                if 'Flux' in col:
                    n2poly = n2poly + 1
            n2poly = int(n2poly/4)

            for NSEW in ['N','S','E','W']:
                for i2poly in range(n2poly):
                    Q = np.zeros(len(df))
                    Qavg = Q.copy()
                    Qrms = Q.copy() 
                    for group in group_list:
                        ind = df['group'].values == group
                        Q[ind] = df.loc[ind]['Continuity,Flux In from %s%02d (Mg/d)' % (NSEW, i2poly+1)].values
                        if np.any(np.abs(Q[ind])>0):
                            Qavg[ind] = semidi_filter(Q[ind], dt_hrs = deltat_hrs, fcut = 1/35., N = 4)
                            Qms = semidi_filter((Q[ind] - Qavg[ind])**2, dt_hrs = deltat_hrs, fcut = 1/35., N = 4)
                            Qms[Qms<0] = 0
                            Qrms[ind] = np.sqrt(Qms)
                    df_F['<Q>%s%02d' % (NSEW,i2poly+1)] = Qavg.copy()
                    df_F['%0.2fsqrt(<(Q-<Q>)^2>)%s%02d' % (step0_config.alpha,NSEW,i2poly+1)] = step0_config.alpha * Qrms.copy()

        # use the filtered dataframe
        df = df_F.copy(deep=True)
        del df_F

        # take a daily average and save it 
        logging.info('    Take the daily average and save it before moving on to other types of time aggregation') 
        logging.info('    (Note hourly data will be used going forward, just saving daily along the way)...') 
        df_tavg = pd.DataFrame(columns=df.columns)
        for group in group_list:
            df1 = df.loc[df[group_col].values==group].resample('D',on='time').mean(numeric_only=True).reset_index()
            df1[group_col] = group
            df_tavg = pd.concat([df_tavg,df1])
        balance_table_fn_out = balance_table_fn.replace('flow_m3s','Qavg_Qrms') 
        logging.info('    Saving %s' % balance_table_fn_out) 
        df_tavg.to_csv(os.path.join(step0_config.balance_table_dir,balance_table_fn_out),index=False, float_format=step0_config.float_format) 

    # get a list of columns we want to aggregate in time
    column_list = list(df.columns)
    for col in df.columns:
        if col in ['time', 'Control Volume', 'group']:
            column_list.remove(col)
        elif 'To_poly' in col:
            column_list.remove(col)

    # for cumulative sum, also skip aggregating concentration and volume
    column_list_cum = column_list.copy()
    for col in df.columns:
        if col in ['Concentration (mg/l)','Area', 'Area (m^2)','Volume','Volume (Mean)','Volume (m^3)','Volume (Mean, m^3)']:
            column_list_cum.remove(col)

    # loop through the time average aggregation schemes
    for tavg in step0_config.tavg_list: 

        # take cumulative sum by water year, starting on Oct 1 of first water year
        if tavg=='Cumulative':

            # print
            if not is_flow:
                logging.info('    Taking cumulative sum by water year ...') 
            else:
                logging.info('    Skipping cumulative sum for %s ...' % balance_table_fn) 
                continue

            # copy the dataframe
            df_tavg = df.copy(deep=True)

            # loop through the groups or control volumes
            for group in group_list:

                # loop though the water years and take cumulative sum by water year
                for wy in wy_list:

                    # find indices of data in this group and this water year
                    ind = np.logical_and(df[group_col] == group, 
                          np.logical_and(df.time>=np.datetime64('%d-10-01' % (wy-1)), 
                                         df.time<np.datetime64('%d-10-01' % wy)))

                    # take cumulative sum
                    df_tavg.loc[ind,column_list_cum] = df.loc[ind,column_list_cum].cumsum() * deltat_days

            # since we integrated in time, units are now Mg instead of Mg/d
            df_tavg.columns = df_tavg.columns.str.replace('Mg/d','Mg')

        # take spring-neap filter and then crop data before Oct 1 of first water year
        elif tavg=='Filtered':

            # print
            logging.info('    Taking spring-neap filter ...') 

            # copy the dataframe
            df_tavg = df.copy(deep=True)
                    
            # tidally filter each group
            for group in group_list:

                # find index of this group
                ind = df[group_col] == group

                # loop through the columns we want to filter and filter each
                for col in column_list:
                    df_tavg.loc[ind,col] = spring_neap_filter(df.loc[ind,col], dt_days=deltat_days)

            # crop times before october 1 of first water year
            ind = df_tavg.time >= np.datetime64('%d-10-01' % (wy_list[0]-1))
            df_tavg = df_tavg.loc[ind]

            # resample onto a daily time axis
            days = df_tavg['time'].values.astype('datetime64[D]')
            ind = np.equal(df_tavg['time'].values, days)
            df_tavg = df_tavg.loc[ind]

        # seasonal, monthly, and weekly averages
        elif tavg in ['Annual','Seasonal','Seasonal2','Seasonal3','Monthly','Weekly']:

            # print
            logging.info('    Taking %s average ...' % tavg) 

            # create a list of time averaging windows
            time_windows = []
            time_titles = []
            if tavg == 'Annual':

                for wy in wy_list:

                    time_windows.append(['%d-10-01' % (wy-1),'%d-10-01' % wy])
                    time_titles.append('WY%d' % wy)

            elif tavg == 'Seasonal':

                for wy in wy_list:

                    time_windows.append(['%d-10-01' % (wy-1),'%d-01-01' % wy])
                    time_titles.append('Oct, Nov, Dec of %d' % (wy-1))
                    time_windows.append(['%d-01-01' % wy,'%d-04-01' % wy])
                    time_titles.append('Jan, Feb, Mar of %d' % wy)
                    time_windows.append(['%d-04-01' % wy,'%d-07-01' % wy])
                    time_titles.append('Apr, May, Jun of %d' % wy)
                    time_windows.append(['%d-07-01' % wy,'%d-10-01' % wy])
                    time_titles.append('Jul, Aug, Sep of %d' % wy)


            elif tavg == 'Seasonal2':

                for wy in wy_list:

                    time_windows.append(['%d-10-01' % (wy-1),'%d-02-01' % wy])
                    time_titles.append('Oct, Nov, Dec, Jan of %d/%d' % (wy-1, wy))
                    time_windows.append(['%d-02-01' % wy,'%d-06-01' % wy])
                    time_titles.append('Feb, Mar, Apr, May of %d' % wy)
                    time_windows.append(['%d-06-01' % wy,'%d-10-01' % wy])
                    time_titles.append('Jun, Jul, Aug, Sep of %d' % wy)

            elif tavg == 'Seasonal3':

                for wy in wy_list:

                    time_windows.append(['%d-10-01' % (wy-1),'%d-02-01' % wy])
                    time_titles.append('Oct-Jan of %d/%d' % (wy-1, wy))
                    time_windows.append(['%d-02-01' % wy,'%d-10-01' % wy])
                    time_titles.append('Feb-Sep of %d' % wy)
                    
            elif tavg == 'Monthly':

                for wy in wy_list:

                    time_windows.append(['%d-10-01' % (wy-1),'%d-11-01' % (wy-1)])
                    time_titles.append('Oct %d' % (wy-1))
                    time_windows.append(['%d-11-01' % (wy-1),'%d-12-01' % (wy-1)])
                    time_titles.append('Nov %d' % (wy-1))
                    time_windows.append(['%d-12-01' % (wy-1),'%d-01-01' % wy])
                    time_titles.append('Dec %d' % (wy-1))
                    time_windows.append(['%d-01-01' % wy,'%d-02-01' % wy])
                    time_titles.append('Jan %d' % wy)
                    time_windows.append(['%d-02-01' % wy,'%d-03-01' % wy])
                    time_titles.append('Feb %d' % wy)
                    time_windows.append(['%d-03-01' % wy,'%d-04-01' % wy])
                    time_titles.append('Mar %d' % wy)
                    time_windows.append(['%d-04-01' % wy,'%d-05-01' % wy])
                    time_titles.append('Apr %d' % wy)
                    time_windows.append(['%d-05-01' % wy,'%d-06-01' % wy])
                    time_titles.append('May %d' % wy)
                    time_windows.append(['%d-06-01' % wy,'%d-07-01' % wy])
                    time_titles.append('Jun %d' % wy)
                    time_windows.append(['%d-07-01' % wy,'%d-08-01' % wy])
                    time_titles.append('Jul %d' % wy)
                    time_windows.append(['%d-08-01' % wy,'%d-09-01' % wy])
                    time_titles.append('Aug %d' % wy)
                    time_windows.append(['%d-09-01' % wy,'%d-10-01' % wy])
                    time_titles.append('Sep %d' % wy)

            elif tavg == 'Weekly':

                time_windows = []
                time_titles = []
                wy_1 = wy_list[0]
                start_time_1 = np.datetime64('%d-10-01' % (wy_1-1))
                while wy_1 <= wy_list[-1]:
                    while start_time_1<np.datetime64('%d-10-01' % wy_1):
                        time_windows.append([start_time_1, start_time_1 + np.timedelta64(1,'W')])
                        time_titles.append('Week starting %s' % start_time_1.astype('datetime64[D]'))
                        start_time_1 += np.timedelta64(1,'W')
                    wy_1 += 1
                    start_time_1 = np.datetime64('%d-10-01' % (wy_1-1))

            # initialize dataframe
            df_tavg = pd.DataFrame()

            # loop through the groups
            for group in group_list:

                # get just the data for this group
                df1 = df.loc[df[group_col] == group].copy(deep=True)

                # loop through the time windows, take the time averages, and append to dataframe
                for time_window, time_title in zip(time_windows, time_titles):

                    # find indices of the data in this time window
                    ind = np.logical_and(df1['time']>=np.datetime64(time_window[0]), df1['time']<=np.datetime64(time_window[1]))
                    df2 = df1.loc[ind].copy(deep=True)

                    # to get the initial time and the polygon right, take the first entry of the data
                    df3 = df2.iloc[0:1].copy(deep=True)

                    # add time title
                    df3['Time Period'] = time_title 

                    # now take the average of the columns we mean to average in time
                    df3[column_list] = df2[column_list].mean()

                    # append to time average dataframe
                    df_tavg = pd.concat([df_tavg, df3])

        # save the results to a balance table, appending the time averaging scheme to the FRONT
        balance_table_fn_out = '%s_%s.csv' % (balance_table_fn.replace('.csv','').replace('flow_m3s','Qavg_Qrms'), tavg)            
        logging.info('    Saving %s' % balance_table_fn_out) 
        df_tavg.to_csv(os.path.join(step0_config.balance_table_dir,balance_table_fn_out),index=False, float_format=step0_config.float_format)

# clean up logging
logger_cleanup()
