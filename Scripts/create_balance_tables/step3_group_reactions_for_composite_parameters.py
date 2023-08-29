
'''
Starting with the composite parameter balance tables generated in step2, group together some of the
reactions to create composite reactions. This is an important step where we identify groups of reacitons
that should cancel out to zero because they represent passing of mass from one substance to another (such
as nitrification passing N from NH4 to NO3, in the DIN budget), and thus we may identify mass conservation
errors. Allie April 2022
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

# define a function that returns a list of columns that are not reactions
def get_not_rx_list(df, rx_list):
    not_rx_list = []
    columns = df.columns
    for column in columns:
        if not column in rx_list:
            not_rx_list.append(column)
    return not_rx_list

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
    logging.FileHandler(os.path.join(step0_config.balance_table_dir,"log_step3.log"),'w'),
    logging.StreamHandler(sys.stdout)
])

# add some basic info to log file
user = os.getlogin()
scriptname= __file__
conda_env=os.environ['CONDA_DEFAULT_ENV']
today= datetime.datetime.now().strftime('%b %d, %Y')
logging.info('Composite balance tables with "Grouped Rx" were produced on %s by %s on %s in %s using %s' % (today, user, hostname, conda_env, scriptname))

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

# loop through the composite parameters
for composite_param in step0_config.composite_reaction_dict.keys():

    # log
    logging.info('Grouping reaction terms for %s' % composite_param)

    # input and output table names and paths
    input_table_name = composite_param.lower() + '_Table_Ungrouped_Rx.csv'
    input_table_path = os.path.join(step0_config.balance_table_dir, input_table_name)
    output_table_name = composite_param.lower() + '_Table.csv'
    output_table_path = os.path.join(step0_config.balance_table_dir, output_table_name)
    
    # get dictionary of compositie reactions
    composite_reactions = step0_config.composite_reaction_dict[composite_param]

    #  read input table, which is the balance table for the composite parameters including every single reaction, totally ungrouped
    try:
        df_composite = pd.read_csv(input_table_path)
    except:
        logging.info('error reading %s, skipping this one ...' % input_table_name)
        continue

    # get the list of columns that contain reactions, and the list that don't
    rx_list = get_rx_list(df_composite, composite_param)
    not_rx_list = get_not_rx_list(df_composite, rx_list)

    # do some logging of progress
    logging.info('    The %s budget includes the following reaction terms:' % composite_param)
    for rx in rx_list:
        logging.info('        %s' % rx)
    logging.info('    Now we will group some of these reactions together, taking care not to lose track of any of them ...')

    # initialize the balance table with the grouped parameters
    df_grouped = df_composite[not_rx_list].copy(deep=True)

    # now add all the grouped reactions to the balance table, removing their components from the list of 
    # all the component reactions as we go along
    grouped_rx_list = list(composite_reactions.keys())
    remaining_rx_list = rx_list.copy()
    for grouped_rx in grouped_rx_list:

        # log
        logging.info('        Summing up componenets of %s...' % grouped_rx)
        
        # initialize the grouped reaction at zero
        df_grouped[grouped_rx] = 0

        # sum up its components
        component_reactions = composite_reactions[grouped_rx]
        for rx in component_reactions:

            # log 
            logging.info('        ... %s' % rx)
            
            # if the reaction isn't in the original list of reactions, check if the substance is in the list of modeled subtances --
            # if not, we can skip it, but if it is, the user needs to add this substance to the list of processed substances
            if not (rx in rx_list):

                # get the substance corresponding to the reaction
                sub = rx.split(',')[0]

                if not sub in substances:
                    logging.info('            %s not found, and %s is not included in this model run, skipping ...' % (rx,sub))
                    continue
                elif sub.lower() in step0_config.substance_list:
                    logging.info('            %s not found, but %s was included in step0_config.substance_list, so it is safe to assume this reaction was just not part of the run, skipping... ' % (rx,sub))
                    continue
                else:
                    raise Exception('%s not found in %s, but %s is a substance in this model run. Add ' % (rx, input_table_name, sub.lower()) + 
                                    '%s to substance_list in step0_config.py and start over from ' % sub.lower() + 
                                    'step1_create_balance_tables.py')

            # if the reaction WAS in the original list, but it isn't in the list of remaining reactions,
            # it must have been double counted, so raise an exception
            elif not rx in remaining_rx_list:
                raise Exception('%s is double counted in composite reactions for %s' % (rx, composite_param))
            
            # add the contribution of the component reaction to its grouped reaction
            df_grouped[grouped_rx] = df_grouped[grouped_rx].values + df_composite[rx].values # add contribution to grouped reaction
            
            # remove this reaction from the list of remaining reactions
            remaining_rx_list.remove(rx)

    # now be sure to include all the remaining reactions
    logging.info('        The following reactions were not used in any grouped reactions, adding them to the final budget...')
    for rx in remaining_rx_list:
        logging.info('        ... %s' % rx)
        df_grouped[rx] = df_composite[rx].values

    # double check the final reaction list
    rx_list = get_rx_list(df_grouped, composite_param) 
    logging.info('    The %s budget includes the following reaction terms after grouping:' % composite_param)
    for rx in rx_list:
        logging.info('        %s' % rx)

    # now save the composite balance table
    logging.info('    Saving composite parameter table with grouped reactions %s' % output_table_path)
    df_grouped.to_csv(output_table_path, index=False, float_format=step0_config.float_format)

# clean up logging
logger_cleanup()