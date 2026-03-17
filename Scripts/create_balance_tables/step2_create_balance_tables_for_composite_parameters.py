
'''
Starting with balance tables for modeled parameters, create balance tables for composite parameters
such as DIN and TN. Automatically finds correct stoichiometric mutipliers from *.lsp file. All the 
reactions in each of the component parameters are included separately. They may be consolidated into 
composite reaction terms in "step3". Allie April 2022
'''

#################################################################
# IMPORT PACKAGES
#################################################################

import sys, os, re
import pandas as pd
import numpy as np
import matplotlib.pylab as plt
import logging
import datetime
import socket
hostname = socket.gethostname()
import step0_config

# if running the script alone, load the configuration module (in this folder)
if __name__ == "__main__":

    import importlib
    importlib.reload(step0_config)

#################################################################
# FUNCTIONS
#################################################################

# define a function that returns a list of the reactions included in a balance table
def get_rx_list(df, substance):    
    rx_list = []
    columns = df.columns  
    for column in columns:
        if not column in ['time', 'Control Volume', 'Concentration (mg/l)', 'Volume',
                          'Volume (Mean)', 'Area', 'dVar/dt', '%s,Loads in' % substance, '%s,Loads out' % substance,
                          '%s,Transp in' % substance, '%s,Transp out' % substance]:
            if not 'Flux' in column:
                if not 'To_poly' in column:
                    rx_list.append(column)
    return rx_list

def logger_cleanup():

    ''' check for open log files, close them, release handlers'''

    # clean up logging
    logger = logging.getLogger()
    handlers = list(logger.handlers)
    if len(handlers)>0:
        for handler in handlers:
            handler.close()
            logger.removeHandler(handler) 

###################################################################
# MAIN
###################################################################

# setup logging to file and to screen 
logger_cleanup()
logging.basicConfig(
level=logging.INFO,
format="%(asctime)s [%(levelname)s] %(message)s",
handlers=[
    logging.FileHandler(os.path.join(step0_config.balance_table_dir,"log_step2.log"),'w'),
    logging.StreamHandler(sys.stdout)
])

# add some basic info to log file
user = os.getlogin()
scriptname= __file__
conda_env=os.environ['CONDA_DEFAULT_ENV']
today= datetime.datetime.now().strftime('%b %d, %Y')
logging.info('Composite balance tables with "Ungrouped Rx" were produced on %s by %s on %s in %s using %s' % (today, user, hostname, conda_env, scriptname))

# scan the lsp file for mentions of N:C ratios P:C ratios
NC_ratios = {}
PC_ratios = {}
SC_ratios = {}
with open(step0_config.lsp_path,'r') as f:
    lines = f.readlines()
    for i in range(len(lines)-1):
        line1 = lines[i]
        line2 = lines[i+1]
        if 'NCRatDiat ' in line1:
            NC_ratios['Diat'] = float(line2.split(':')[1])
        elif 'N:C ratio Greens' in line1:
            NC_ratios['Green'] = float(line2.split(':')[1])
        elif 'NCRatDiatS ' in line1:
            NC_ratios['DiatS1'] = float(line2.split(':')[1])
        elif 'N:C ratio of DEB Zooplankton' in line1:
            NC_ratios['Zoopl_V'] = float(line2.split(':')[1])
            NC_ratios['Zoopl_E'] = float(line2.split(':')[1])
            NC_ratios['Zoopl_R'] = float(line2.split(':')[1])
        elif 'N:C ratio of DEB Grazer4' in line1:
            NC_ratios['Grazer4_V'] = float(line2.split(':')[1])
            NC_ratios['Grazer4_E'] = float(line2.split(':')[1])
            NC_ratios['Grazer4_R'] = float(line2.split(':')[1])
        elif 'N:C ratio of DEB Mussel' in line1:
            NC_ratios['Mussel_V'] = float(line2.split(':')[1])
            NC_ratios['Mussel_E'] = float(line2.split(':')[1])
            NC_ratios['Mussel_R'] = float(line2.split(':')[1])
        if 'PCRatDiat ' in line1:
            PC_ratios['Diat'] = float(line2.split(':')[1])
        elif 'P:C ratio Greens' in line1:
            PC_ratios['Green'] = float(line2.split(':')[1])
        elif 'PCRatDiatS ' in line1:
            PC_ratios['DiatS1'] = float(line2.split(':')[1])
        elif 'P:C ratio of DEB Zooplankton' in line1:
            PC_ratios['Zoopl_V'] = float(line2.split(':')[1])
            PC_ratios['Zoopl_E'] = float(line2.split(':')[1])
            PC_ratios['Zoopl_R'] = float(line2.split(':')[1])
        elif 'P:C ratio of DEB Grazer4' in line1:
            PC_ratios['Grazer4_V'] = float(line2.split(':')[1])
            PC_ratios['Grazer4_E'] = float(line2.split(':')[1])
            PC_ratios['Grazer4_R'] = float(line2.split(':')[1])
        elif 'P:C ratio of DEB Mussel' in line1:
            PC_ratios['Mussel_V'] = float(line2.split(':')[1])
            PC_ratios['Mussel_E'] = float(line2.split(':')[1])
            PC_ratios['Mussel_R'] = float(line2.split(':')[1])
        if 'SCRatDiat ' in line1:
            SC_ratios['Diat'] = float(line2.split(':')[1])
        elif 'Si:C ratio Greens' in line1:
            SC_ratios['Green'] = float(line2.split(':')[1])
        elif 'PCRatDiatS ' in line1:
            SC_ratios['DiatS1'] = float(line2.split(':')[1])
        elif 'Si:C ratio of DEB Zooplankton' in line1:
            SC_ratios['Zoopl_V'] = float(line2.split(':')[1])
            SC_ratios['Zoopl_E'] = float(line2.split(':')[1])
            SC_ratios['Zoopl_R'] = float(line2.split(':')[1])
        elif 'Si:C ratio of DEB Grazer4' in line1:
            SC_ratios['Grazer4_V'] = float(line2.split(':')[1])
            SC_ratios['Grazer4_E'] = float(line2.split(':')[1])
            SC_ratios['Grazer4_R'] = float(line2.split(':')[1])
        elif 'Si:C ratio of DEB Mussel' in line1:
            SC_ratios['Mussel_V'] = float(line2.split(':')[1])
            SC_ratios['Mussel_E'] = float(line2.split(':')[1])
            SC_ratios['Mussel_R'] = float(line2.split(':')[1])
logging.info('The following N:C ratios were found in %s:' % step0_config.lsp_path)
keys = list(NC_ratios.keys())
keys.sort()
for key in keys:
    logging.info('    %s : %f' % (key, NC_ratios[key]))
logging.info('The following P:C ratios were found in %s:' % step0_config.lsp_path)
keys = list(PC_ratios.keys())
keys.sort()
for key in keys:
    logging.info('    %s : %f' % (key, PC_ratios[key]))
logging.info('The following Si:C ratios were found in %s:' % step0_config.lsp_path)
keys = list(SC_ratios.keys())
keys.sort()
for key in keys:
    logging.info('    %s : %f' % (key, SC_ratios[key]))

# read the lsp file and return a list of the substances
substances = []
with open(step0_config.lsp_path,'r') as f:
    for line in f.readlines():
        if '-fluxes for [' in line:
            # the following ugly expression returns the string between the brackets, stripped of whitespace:
            substances.append(line[line.find("[")+1:line.find("]")].strip()) 
logging.info('The following substances were found in %s:' % step0_config.lsp_path)
for substance in substances:
    logging.info('    %s' % substance)

# load all the balance tables into a dictionary
logging.info('Reading balance tables from %s:' % step0_config.balance_table_dir)
df_dict = {}
for substance in substances.copy():
    table_name = '%s_Table.csv' % substance.lower()
    try:
        df = pd.read_csv(os.path.join(step0_config.balance_table_dir,table_name))
    except:
        logging.info('    Did not find %s' % table_name)
        substances.remove(substance)
    else:
        logging.info('    Succesfully read %s' % table_name)
        df_dict[substance] = df.copy(deep=True)    

# find the number of adjacent polygons included in the fluxes, using the NH4 balance table
logging.info('Using the NH4 balance table to check number of adjacent polygons included in the fluxes...')
polymax = 0
for column in df_dict['NH4'].columns:
    if 'To_poly' in column:
        n = int(column.strip('To_poly'))
        if n>polymax:
            polymax = n
logging.info('Tracking %d fluxes to adacent polygons' % (polymax+1))

# make a base balance table from the NH4 balance tables, to reuse when initializing composite parameter tables
# ... these columns have the same values in all balance tables
df_base = df_dict['NH4'][['time', 'Control Volume', 'Volume',
       'Volume (Mean)', 'Area']].copy(deep=True)
# ... initialize these columns at zero
df_base['Concentration (mg/l)'] = 0.0
df_base['dVar/dt'] = 0.0
for n in range(polymax+1):
    df_base['To_poly%d' % n] = df_dict['NH4']['To_poly%d' % n].values
    df_base['Flux%d' % n] = 0.0

# make a list of the flux columns to track when adding up the component parameters
flux_list = []
for n in range(polymax+1):
    flux_list.append('Flux%d' % n)

# make a list of the loading and transport terms, with an %s placeholder for the substance
load_transp_list = ['%s,Loads in','%s,Loads out','%s,Transp in','%s,Transp out']

# loop through the composite parameters
for composite_param in step0_config.composite_parameters.keys():
    
    # log
    logging.info('Deriving balance table for %s' % composite_param)

    # check the base element for the composite parameter budget
    composite_base = step0_config.composite_bases[composite_param]
    logging.info('    Base element is %s' % composite_base)

    # initialize the balance table
    df_composite = df_base.copy(deep=True)

    # initialize columns for the loading and transport
    for column in load_transp_list:
        df_composite[column % composite_param] = 0

    # boolean to detect if any of the component parameters were included in the model run, if not, skip this composite parameter
    any_components = False

    # loop through the component parameters making up the composite parameter
    for component_param in step0_config.composite_parameters[composite_param]:

        # log component parameter
        logging.info('    Adding %s budget ...' % component_param)

        # check if this parameter was included in the model run, and if not, skip it
        if not component_param in substances:
            logging.info('       %s not found in list of substances, skipping this component of %s' % (component_param, composite_param))
            continue    
        elif not component_param in df_dict.keys():
            logging.info('       ERROR: substance %s was modeled and is needed to compute %s, but could not find the %s_Table.csv file' % (component_param, composite_param, component_param))
            logging.info('       What to do? Add %s to substance_list in configuration file and re-run step1_create_balance_tables.py, then try again' % component_param)
            raise Exception('substance %s was modeled and is needed to compute %s, but could not find the %s_Table.csv file\n' % (component_param, composite_param, component_param) + 
                            'Add %s to substance_list in configuration file and re-run step1_create_balance_tables.py, then try again' % component_param)
        else:
            any_components = True

        # figure out the correct stoichiometric multiplier
        multiplier = 1
        if composite_base == 'N':
            if component_param in NC_ratios.keys():
                multiplier = NC_ratios[component_param]
        elif composite_base == 'P':
            if component_param in PC_ratios.keys():
                multiplier = PC_ratios[component_param]
        elif composite_base == 'Si':
            if component_param in SC_ratios.keys():
                multiplier = SC_ratios[component_param]
        logging.info('        Using the following stoichiometric multiplier for %s: %f' % (component_param, multiplier))

        # add up the concentrations, the change in mass, and the fluxes
        for column in (['Concentration (mg/l)', 'dVar/dt'] + flux_list):
            logging.info('        Adding contribution to %s' % column)
            df_composite[column] = df_composite[column].values + multiplier * df_dict[component_param][column].values

        # add up the loadings and transport terms
        for column in load_transp_list:
            logging.info('        Adding contribution to %s' % (column % composite_param))
            df_composite[column % composite_param] = df_composite[column % composite_param].values + multiplier * df_dict[component_param][column % component_param].values

        # add the reactions
        rx_list = get_rx_list(df_dict[component_param], component_param)
        for column in rx_list:
            logging.info('        Adding the reaction term %s' % column)
            df_composite[column] = multiplier * df_dict[component_param][column].values

    # now save the composite balance table
    table_name = composite_param.lower() + '_Table_Ungrouped_Rx.csv'
    table_path = os.path.join(step0_config.balance_table_dir, table_name)
    if any_components:
        logging.info('    Saving composite parameter table %s' % table_path)
        df_composite.to_csv(table_path, index=False, float_format=step0_config.float_format)
    else:
        logging.info('    No balance tables for component parameters of %s were found, so no composite table was created' % composite_param)

# clean up logging
logger_cleanup()