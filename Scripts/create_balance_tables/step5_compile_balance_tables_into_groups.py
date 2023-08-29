
# in this step, we take all the balance tables for base substances and for composite parameters
# and we aggregate in space, grouping polygons into "groups". the groups are defined in the 
# control_volume_definitions_FR.txt file, and the way they are connected to each other is defined in the 
# connectivity_definitions_FR.txt file. this script automatically finds all the tables for the 
# base level substances and the composite substances with grouped reactions, and creates a table with the same name
# but with "_By_Group" appended at the end

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
    logging.FileHandler(os.path.join(step0_config.balance_table_dir,"log_step5.log"),'w'),
    logging.StreamHandler(sys.stdout)
])

# add some basic info to log file
user = os.getlogin()
scriptname= __file__
conda_env=os.environ['CONDA_DEFAULT_ENV']
today= dt.datetime.now().strftime('%b %d, %Y')
logging.info('Group level balance tables were produced on %s by %s on %s in %s using %s' % (today, user, hostname, conda_env, scriptname))

# read from text file a dictionary grouping control volumes into lettered groups 
# format:
#   GROUP_NAME : CV1, CV2, CV3, ...
# where:
#   GROUP_NAME = name of group
#   CV1, CV2, CV3, ... = numbers of control volumes comprising the group
group_dict = {}
with open(step0_config.group_def_path,'r') as f: 
    for line in f.readlines():
        # split line at ':' into key and control volume list, dropping newline character first
        (key, val) = line.rstrip('\n').split(':')  
        # remove whitespace surrounding key 
        key = key.strip()
        # add list to dictionary
        group_dict[key] = eval(val) 
      
        
# read from text file a dictionary specifying all the fluxes between 
# control volumes making up fluxes from each lettered group to the north, 
# south, east, and west
# format:
#   LETTER2DIRECTION : [[CVf,CVt]_1, [CVf,CVt]_2, [CVf,CVt]_3, ...]
# where:
#   LETTER = name of group
#   DIRECTION = N, S, E, or W stand for "to the north", south, east, or west, respectively
#   [CVf, CVt]_i = defines a flux from control volume CVf to control volume CVt
#   where i = 1, 2, 3, ... make up all the fluxes for a particular group/direction pair
flux_pairs_dict = {}
with open(step0_config.group_con_path,'r') as f: 
    for line in f.readlines():
        # split line at ':' into key and connectivity volume list, dropping newline character first
        (key, val) = line.rstrip('\n').split(':') 
        # trim whitespace around key
        key = key.strip()
        # add list to dictionary
        flux_pairs_dict[key] = eval(val) 

# find the maximum number of flux pairs for a single group
maxpairs = 0
for key in flux_pairs_dict.keys():
    npairs = len(np.array(flux_pairs_dict[key]))
    if npairs>maxpairs:
        maxpairs=npairs

# note how many groups there are, and make sure groups are defined only once, also make
# sure there are no repeat connections 
Ng = len(group_dict)
assert Ng == len(np.unique(list(group_dict.keys())))
assert len(list(flux_pairs_dict.keys())) == len(np.unique(list(flux_pairs_dict.keys())))

# find the number of unique types of connections (N/S/E/W also possibly NE/SW/etc)
direction_list = []
for key in flux_pairs_dict.keys():
    direction = key[key.find(' to ')+4:]
    if not direction in direction_list:
        direction_list.append(direction)
logging.info('flux directions include: ')
for direction in direction_list:
    logging.info('    ' + direction)

# get a list of all the files in the balance table directory, identify the ones with the format (param)_Table.csv, and get the list of parameters
param_list = []
file_list = os.listdir(step0_config.balance_table_dir)
for file in file_list:
    if 'Table.csv' in file:
        param = file[0:-10]
        if param in step0_config.plot_substance_list:
            param_list.append(param)
        else:
            logging.info('skipping %s_Table.csv because %s is not in step0_config.plot_substance_list' % (param, param))
Nparams = len(param_list)

# output number of parameters and types of parameters found 
logging.info('Scanned directory %s for files with format PARAM_Table.csv where PARAM is in ' % step0_config.balance_table_dir + 
             'step0_config.plot_substance_list and retrieved following list of %d parameters:' % Nparams)
for param in param_list:
    logging.info('   %s' % param)

# loop through the parameters
for ip in range(Nparams):

    #######################################################################################
    # Read control volume budgets from the balance table and extract time info
    ########################################################################################

    # read in the balance table corresponding to this parameter
    balance_table_fn = param_list[ip].lower() + '_Table.csv'
    try:
        df = pd.read_csv(os.path.join(step0_config.balance_table_dir,balance_table_fn))
    except:
        logging.info('error reading %s, skipping this one ...' % balance_table_fn)
        continue

    # do something special if continuity is include, to help calculate residence time
    if param_list[ip]=='continuity':
        try:
            df_HF = pd.read_csv(os.path.join(step0_config.balance_table_dir,'flow_m3s_Table.csv'))
        except:
            logging.info('error reading flow_m3s_Table.csv, skipping this one ...' % balance_table_fn)
            continue

    # need to find the appropriate capitalization of the lowercase parameter name, use the "PARAM,Loads in"
    # column and take everything before the comma
    for col in df.columns:
        if ',Loads in' in col:
            param_name = col.split(',')[0]
    
    # print
    logging.info('Building grouped balance table for %s ...' % param_name)

    # convert time stamp strings to datetime objects, noting that for some reason the format of the 
    # time stamp strings is different in different balance tables -- sometimes Y-M-D and sometimes M/D/Y,
    # so accomodate for this
    try:
        df['time'] = [dt.datetime.strptime(timestamp, '%Y-%m-%d').date() for timestamp in df['time']]
    except:
        df['time'] = [dt.datetime.strptime(timestamp, '%m/%d/%Y').date() for timestamp in df['time']]

    # extract unique dates and note number of time steps, and also create a date string
    # corresponding to these dates
    dates = np.sort(np.unique(df['time'].values))
    Nt = len(dates)
    datestrings = [dt.datetime.strftime(date,'%Y-%m-%d') for date in dates]

    # time handling for high frequency flow data
    if param_list[ip]=='continuity':
        df_HF['time'] = df_HF['time'].astype('datetime64[ns]')
        times_HF = np.unique(df_HF['time'].values)
        Nt_HF = len(times_HF)
        timestrings_HF = list(pd.DatetimeIndex(times_HF).astype(str))

    ##########################################################################################
    # Intialize a master data frame to store all of the data by group (A, B, C, ...)
    ##########################################################################################

    # initialize a list that will contain all the column names for the master data frame, 
    # starting with the variables that are the same across all the parameters
    column_names = ['group','time','Volume (m^3)','Volume (Mean, m^3)','Area (m^2)',
                             param_name + ',' + 'Mass (Mg)', 
                             param_name + ',' + 'dMass/dt (Mg/d)',
                             param_name + ',' + 'Net Flux In (Mg/d)',
                             param_name + ',' + 'Net Load (Mg/d)',
                             param_name + ',' + 'Net Transport In (Mg/d)',
                             param_name + ',' + 'Net Reaction (Mg/d)',
                             param_name + ',' + 'dMass/dt, Balance Check (Mg/d)']

    # append fluxes from N, S, E, W, etc.
    for direction in direction_list:
        column_names.append(param_name + ',' + 'Flux In from %s (Mg/d)' % direction)
                
    # append the reaction terms, which are unique to each parameter, also save the 
    # list of reaction names . this code assumes that the reaction terms are all the 
    # column names with a comma in them followed by a 'd'
    reaction_name_list = []
    for rt in df.columns:
        if ',d' in rt:
            column_names.append(rt + ' (Mg/d)')
            reaction_name_list.append(rt + ' (Mg/d)')
    
    # now that we have all the column names compiled, initialize the master data frame
    df_master = pd.DataFrame(columns=column_names)
    
    # fill in the groups and timestamps in the master data frame such that the order
    # of the groups are A, A, A, ...., B, B, B, ...., C, C, C, ...., etc. with the number 
    # of repeats of each gropup letter equal to the number of time stamps
    group_list = []
    datestrings_list = []
    for group in group_dict.keys():
        group_list += [group] * Nt            
        datestrings_list += datestrings.copy() 
    df_master['group'] = group_list.copy()
    df_master['time'] = datestrings_list.copy()
    
    # initalize all of the other columns in the data frame, i.e., everything besides
    # group and time stamp, as arrays of zeros of type float
    for col in df_master.columns[2:]:
        df_master[col] = 0.0

    ##### if parameter is continuity, work on the high frequency flow rate groupings 
    ##### to use to compute residence time later
    if param_list[ip]=='continuity':

        # keep contributions to each side separate, resulting in a ridiculous number of flux columns    
        column_names_HF = ['group','time','Volume (m^3)']
        for direction in direction_list:
            for ipairs in range(maxpairs):
                column_names_HF.append(param_name + ',' + 'Flux In from %s%02d (Mg/d)' % (direction,ipairs+1))

        # now that we have all the column names compiled, initialize the master data frame
        df_master_HF = pd.DataFrame(columns=column_names_HF)
        
        # fill in the groups and timestamps in the master data frame such that the order
        # of the groups are A, A, A, ...., B, B, B, ...., C, C, C, ...., etc. with the number 
        # of repeats of each gropup letter equal to the number of time stamps
        group_list_HF = []
        timestrings_list_HF = []
        for group in group_dict.keys():
            group_list_HF += [group] * Nt_HF            
            timestrings_list_HF += timestrings_HF.copy() 
        df_master_HF['group'] = group_list_HF.copy()
        df_master_HF['time'] = timestrings_list_HF.copy()
        
        # initalize all of the other columns in the data frame, i.e., everything besides
        # group and time stamp, as arrays of zeros of type float
        for col in df_master_HF.columns[2:]:
            df_master_HF[col] = 0.0
       
    ########################################################################################
    # for each group/face pair, i.e., A2N, A2S, ... , L2E, L2W, add up all of the
    # fluxes between pairs of control volumes that make up the total flux through 
    # that face
    ########################################################################################
    
    # loop through all of the group/face pairs (A2N, A2S, ... , L2E, L2W)
    for flux_key in flux_pairs_dict.keys():    
    
        # extract group letter (A, B, C, ... ) and face (N, S, E, W) from flux_key
        group = str(flux_key).split()[0]
        NSEW = str(flux_key).split()[-1]
        
        # initialize total flux through this group/face pair at zero 
        flux_param = np.zeros(Nt, dtype=float)
        
        # loop through pairs of control volumes comprising total flux through this group/face, 
        # and add up the fluxes
        for ipair, flux_pair in enumerate(flux_pairs_dict[flux_key]):  
            
            # each flux_pair is a 2-item list where the first item is the "from" 
            # control volume/polygon and the second item is the "to" control volume/polygon
            from_poly = flux_pair[0]
            to_poly = flux_pair[1]        

            # using logical indexing, extract the rows of the balance table data frames corresponding to 
            # the "from" polygon in this particular flux pair for each parameter, storing the values in a list
            rows_from_param = df.loc[df['Control Volume'] == ('polygon%d' % from_poly)]
            
            # only need one row to identify which control volume is the "to" polygon, so pick out the first row
            row_to_param = rows_from_param.iloc[0]
                
            # count the number of fields labeled "To_polyN" where N is an integer
            n2poly = 0
            for key in row_to_param.keys():
                if 'To_poly' in key:
                    n2poly = n2poly + 1
            
            # note that the way Zhenlin handled the "to" control volumes is by creating eight fields called 
            # "To_polyX" where X = 0, 1, ..., 7, that map to the numbers of all the "to" control volumes for each
            # "from" polygon. using our one example row, find the number X of the "to" polygon in the corresponding 
            # to the "to" control volume in our flux pair -- should be the same for all substances but doing them 
            # separately to narrow down origin of any potential errors
            polynum_param = None
            for p in range(0,n2poly):
                if row_to_param['To_poly%d' % p] == to_poly:
                    polynum_param = p
            
            # if we can't find the "to" polygon, polynum will remain None, and the 
            # following will throw an assertion error. if you get this error, it means
            # there is either an error in the definition of the flux dictionary or an error
            # in Zhenlin's data tables, probably the dictionary
            assert(polynum_param+1)
            
            # add the flux for this control volume pair flux to the total flux for the group/side pair
            flux_param += rows_from_param["Flux%d" % polynum_param].values.copy()

            # if we are on the continuity parameter, populate the table for high frequency flow rate through the 
            # sides ... in this case, we are NOT adding up the fluxes across the different sides, instead we 
            # are keeping the sides separate
            if param_list[ip]=='continuity':

                # using logical indexing, extract the rows of the balance table data frames corresponding to 
                # the "from" polygon in this particular flux pair for each parameter, storing the values in a list
                rows_from_param_HF = df_HF.loc[df_HF['Control Volume'] == ('polygon%d' % from_poly)]
                
                # only need one row to identify which control volume is the "to" polygon, so pick out the first row
                row_to_param_HF = rows_from_param_HF.iloc[0]
                    
                # count the number of fields labeled "To_polyN" where N is an integer
                n2poly = 0
                for key in row_to_param.keys():
                    if 'To_poly' in key:
                        n2poly = n2poly + 1
                
                # note that the way Zhenlin handled the "to" control volumes is by creating eight fields called 
                # "To_polyX" where X = 0, 1, ..., 7, that map to the numbers of all the "to" control volumes for each
                # "from" polygon. using our one example row, find the number X of the "to" polygon in the corresponding 
                # to the "to" control volume in our flux pair -- should be the same for all substances but doing them 
                # separately to narrow down origin of any potential errors
                polynum_param = None
                for p in range(0,n2poly):
                    if row_to_param['To_poly%d' % p] == to_poly:
                        polynum_param = p
                
                # if we can't find the "to" polygon, polynum will remain None, and the 
                # following will throw an assertion error. if you get this error, it means
                # there is either an error in the definition of the flux dictionary or an error
                # in Zhenlin's data tables, probably the dictionary
                assert(polynum_param+1)
                
                # add the flux for this control volume pair flux to the total flux for the group/side pair
                ind_m = df_master_HF['group'] == group
                df_master_HF.loc[ind_m,param_name + ',Flux In from %s%02d (Mg/d)' % (NSEW,ipair+1)] = rows_from_param_HF["Flux%d" % polynum_param].values

        # add the total flux for this group/side pair to the master data frame in the appropriate place
        # switching direction because while Zhenlin's "To_poly" implies these fluxes are out, they are
        # actually in. divide by 1e6 to converg g/d to Mg/d
        ind_m = df_master['group'] == group
        df_master.loc[ind_m,param_name + ',Flux In from %s (Mg/d)' % NSEW] = flux_param.copy()/1.0e6
           
    ########################################################################################
    # For each group (A, B, C, ...) add up all the contributions from the multiple
    # control volumes that comprise the group to get the total area, volume, rate of 
    # change of mass, loads, and reaction rates
    ########################################################################################
    
    # loop through the groups
    for group in group_dict.keys():

        # initialize the area and volume of the group, 
        # which are the same for all the parameters, at zero
        Volume = np.zeros(Nt, dtype=float)
        Volume_mean = np.zeros(Nt, dtype=float)
        Area = np.zeros(Nt, dtype=float)
        
        # initialize the variables that are the same for all parameters at zero
        Mass = np.zeros(Nt, dtype=float)
        dMdt = np.zeros(Nt, dtype=float)
        Load_In = np.zeros(Nt, dtype=float)
        Transport_In = np.zeros(Nt, dtype=float)
        
        # initialize all the reaction terms at zero
        Nr = len(reaction_name_list)
        reaction_term_values = []
        for ir in range(Nr):    
            reaction_term_values.append(np.zeros(Nt, dtype=float))

        # for the high frequency flow rate dataframe, we only need to aggregate volume
        if param_list[ip]=='continuity':
            Volume_HF = np.zeros(Nt_HF, dtype=float)
        
        # loop through all the control volumes that comprise this group, and add 
        # up the reaction terms, masses, volumes, loads, etc.
        for cvnum in group_dict[group]:
        
            # logical index for selecting rows of substance-specific data frames 
            # corresponding to this control volume (a.k.a. polygon) 
            ind_s = df['Control Volume'] == 'polygon%d' % cvnum
           
            # add volumes and areas
            Volume    += df.loc[ind_s,'Volume'].values.copy()
            Volume_mean    += df.loc[ind_s,'Volume (Mean)'].values.copy()
            Area      += df.loc[ind_s,'Area'].values.copy()
            
            # add the mass, multiplying concentration by volume to get mass
            Mass  += df.loc[ind_s,'Volume'].values.copy() * df.loc[ind_s,'Concentration (mg/l)'].values.copy()
        
            # add the mass rate of change, loads, and transport in
            dMdt         +=   df.loc[ind_s,'dVar/dt'].values.copy()
            Load_In      += ( df.loc[ind_s,param_name + ',Loads in'].values.copy() + df.loc[ind_s,param_name + ',Loads out'].values.copy() )
            Transport_In += ( df.loc[ind_s,param_name + ',Transp in'].values.copy() + df.loc[ind_s,param_name + ',Transp out'].values.copy() )
            
            # add the reaction rates, noting that in dataframe df, the reaction name doesn't
            # include the units so need to trim the reaction name string
            for ir in range(Nr):
                reaction_term_values[ir] += df.loc[ind_s,reaction_name_list[ir][0:-7]].values.copy()

            # for the high frequency flow rate dataframe, we only need to aggregate volume
            if param_list[ip]=='continuity':
                ind_s = df_HF['Control Volume'] == 'polygon%d' % cvnum
                Volume_HF    += df_HF.loc[ind_s,'Volume'].values.copy()
            
        # assign totals to appropriate group in master data frame
        ind_m = df_master['group'] == group
        
        # add volumes and areas
        df_master.loc[ind_m,'Volume (m^3)']  = Volume.copy()
        df_master.loc[ind_m,'Volume (Mean, m^3)']  = Volume_mean.copy()
        df_master.loc[ind_m,'Area (m^2)']    = Area.copy()
        
        # set mass, mass rate of change, net load, net transport in, dividing by 1.0e6 to 
        # convert g to Mg and g/d to Mg/d
        df_master.loc[ind_m,param_name + ',Mass (Mg)']               = Mass.copy()/1.0e6
        df_master.loc[ind_m,param_name + ',dMass/dt (Mg/d)']         = dMdt.copy()/1.0e6
        df_master.loc[ind_m,param_name + ',Net Load (Mg/d)']         = Load_In.copy()/1.0e6
        df_master.loc[ind_m,param_name + ',Net Transport In (Mg/d)'] = Transport_In.copy()/1.0e6
        
        # set reaction terms, dividing by 1.0e6 to convert g to Mg and g/d to Mg/d
        for ir in range(Nr):
            df_master.loc[ind_m,reaction_name_list[ir]] = reaction_term_values[ir].copy()/1.0e6

        # for the high frequency flow rate dataframe, we only need to aggregate volume
        if param_list[ip]=='continuity':
            ind_m = df_master_HF['group'] == group
            df_master_HF.loc[ind_m,'Volume (m^3)']  = Volume_HF.copy()

    ########################################################################################
    # Add up the fluxes and reactions for this parameter to get the net and add to dataframe
    ########################################################################################
                
    # add N,S,E,W,NE,etc components to get the net flux out and set value in the master data
    # frame
    df_master[param_name + ',Net Flux In (Mg/d)'] = 0
    for direction in direction_list:
        df_master[param_name + ',Net Flux In (Mg/d)'] += df_master[param_name + ',Flux In from %s (Mg/d)' % direction].values.copy()
    
    # add up all the reaction rates to get the net reaction rate and set value in 
    # the master data frame
    Nr = len(reaction_name_list)
    if Nr>0:
        net_reaction = df_master[reaction_name_list[0]].values.copy()
        for ir in range(1,Nr):
            net_reaction += df_master[reaction_name_list[ir]].values.copy()
        df_master[param_name + ',Net Reaction (Mg/d)'] = net_reaction.copy()
    else:
        df_master[param_name + ',Net Reaction (Mg/d)'] = 0
    
    # do a balance check on the rate of change of mass
    df_master[param_name + ',dMass/dt, Balance Check (Mg/d)'] = ( 
                              df_master[param_name + ',Net Load (Mg/d)'].values.copy()
                            + df_master[param_name + ',Net Reaction (Mg/d)'].values.copy()  
                            + df_master[param_name + ',Net Transport In (Mg/d)'].values.copy() )
    
        
    ########################################################################################
    # Print master dataframe to *.csv
    ########################################################################################
    
    df_master.to_csv(os.path.join(step0_config.balance_table_dir,'%s_Table_By_Group.csv' % param_name.lower()),index=False, float_format=step0_config.float_format)
    
    # if this is the continuity parameter, additionally output table for high frequency flow rates
    if param_list[ip]=='continuity':
        df_master_HF.to_csv(os.path.join(step0_config.balance_table_dir,'flow_m3s_Table_By_Group.csv'),index=False, float_format=step0_config.float_format)
    


# clean up logging
logger_cleanup()