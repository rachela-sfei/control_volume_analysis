
# make some plots to check for mass conservation, using the results of step3
# note this checks the reactions only, for composite parameters
# Allie April 2022
#

#################################################################
# IMPORT PACKAGES
#################################################################

import sys, os, re
import pandas as pd
import numpy as np
import matplotlib.pylab as plt
from matplotlib.backends.backend_pdf import PdfPages
import logging
import datetime
import geopandas as gpd
import socket
hostname = socket.gethostname()
import step0_config

# if running the script alone, load the configuration module (in this folder)
if __name__ == "__main__":

    import importlib
    importlib.reload(step0_config)

#################################################################
# USER INPUT
#################################################################



# is full resolution?
if 'FR' in step0_config.runid:
    FR = True
else:
    FR = False

# path to shapefiles corresponding to the polygons in the balance tables, also select a subset of polygons to plot
if step0_config.is_delta:
    rx_pos = (508800,4286000) 

elif FR:
    iplot = [0, 117, 139, 2, 113, 114, 115, 111, 1, 3, 116, 7, 4, 112, 5, 108, 109, 110, 9, 107, 
    6, 8, 29, 10, 12, 11, 138, 137, 100, 19, 18, 13, 20, 26, 25, 21, 14, 24, 101, 102, 103, 104, 
    105, 106, 28, 27, 22, 15, 30, 23, 35, 34, 33, 32, 31, 17, 41, 40, 39, 38, 37, 36, 16, 140, 
    44, 43, 42, 46, 45, 49, 47, 97, 98, 86, 96, 95, 85, 93, 52, 87, 94, 48, 51, 50, 90, 88, 91, 
    89, 92, 53, 56, 99, 54, 55, 57, 67, 65, 66, 136, 58, 59, 63, 64, 60, 62, 61, 143, 144, 141, 
    68, 69, 70, 71, 78, 72, 84, 79, 146, 80, 82, 83, 142, 145, 73, 81, 74, 76, 77, 75]
    rx_pos = (573900,4204500)
else:
    iplot = [  0,   1,   2,   3,   4,   5,   6,   7,   8,   9,  10,  11,  12,
        13,  14,  15,  16,  17,  18,  19,  20,  21,  22,  23,  24,  25,
        26,  27,  28,  29,  30,  31,  32,  33,  34,  35,  36,  37,  38,
        39,  40,  41,  42,  43,  44,  45,  46,  47,  48,  49,  50,  51,
        52,  53,  54,  55,  56,  57,  58,  59,  60,  61,  62,  63,  64,
        65,  66,  67,  68,  69,  70,  71,  72,  73,  74,  75,  76,  77,
        78,  79,  80,  81,  82,  83,  84,  85,  86,  87,  88,  89,  90,
        91,  92,  93,  94,  95,  96,  97,  98,  99, 100, 101, 102, 103,
       104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115,
       134, 136, 137, 138, 139, 140]
    rx_pos = (573900,4204500)

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


#################################################################
# MAIN
#################################################################

# setup logging to file and to screen 
logger_cleanup()
logging.basicConfig(
level=logging.INFO,
format="%(asctime)s [%(levelname)s] %(message)s",
handlers=[
    logging.FileHandler(os.path.join(step0_config.balance_table_dir,"log_step4.log"),'w'),
    logging.StreamHandler(sys.stdout)
])

# add some basic info to log file
user = os.getlogin()
scriptname= __file__
conda_env=os.environ['CONDA_DEFAULT_ENV']
today= datetime.datetime.now().strftime('%b %d, %Y')
logging.info('Checking for mass conservation on %s by %s on %s in %s using %s' % (today, user, hostname, conda_env, scriptname))

# put mass conservation check plots in the same directory as the balance tables themselves
output_path = os.path.join(step0_config.balance_table_dir,'mass_conservation_check')
if not os.path.exists(output_path):
    os.makedirs(output_path)

# loop through the parameeters
for param in step0_config.mass_cons_check_param_list:

    # name of the pdf file that will contain maps showing contribution of the grouped reaction terms
    rx_map_path = os.path.join(output_path, '%s_%s_reaction_percentage_map.pdf' % (step0_config.runid,param))

    # which reaction to normalize by
    normalize_by = step0_config.mass_cons_check_normalize_by_dict[param]

    # log 
    logging.info('Checking %s for mass conservation, normalizing by %s, using error tolerance of %f' % (param, normalize_by, step0_config.error_tol_percent))
    
    # read table
    table_name = '%s_Table.csv' % param.lower()
    try:
        df = pd.read_csv(os.path.join(step0_config.balance_table_dir,table_name))
    except:
        print('Cannot open %s, skipping mass conservation check for this parameter')
        continue

    # read the polygon shapefile, and if delta, find the water board polygons and select those to plot
    gdf = gpd.read_file(step0_config.poly_path)
    if step0_config.is_delta:
        ind = gdf['polytype'] == 'WB'
        iplot = list(gdf.loc[ind].index)
    
    # select subset of polygons to plot, and come up with list of corresponding polygon names
    iplot = np.sort(iplot)
    gdf = gdf.iloc[iplot]
    polys = np.array(['polygon%d' % i for i in iplot])
    
    # get list of reactions
    rx_list = get_rx_list(df, param)
    
    # plot style list
    plot_colors = ['#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231', '#911eb4', '#46f0f0', '#f032e6', '#bcf60c', '#fabebe', '#008080', '#e6beff', '#9a6324', '#fffac8', '#800000', '#aaffc3', '#808000', '#ffd8b1', '#000075', '#808080', '#ffffff', '#000000',
                   '#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231', '#911eb4', '#46f0f0', '#f032e6', '#bcf60c', '#fabebe', '#008080', '#e6beff', '#9a6324', '#fffac8', '#800000', '#aaffc3', '#808000', '#ffd8b1', '#000075', '#808080', '#ffffff', '#000000',
                   '#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231', '#911eb4', '#46f0f0', '#f032e6', '#bcf60c', '#fabebe', '#008080', '#e6beff', '#9a6324', '#fffac8', '#800000', '#aaffc3', '#808000', '#ffd8b1', '#000075', '#808080', '#ffffff', '#000000']
    line_styles = ['-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-',
                   '--', '--', '--', '--', '--', '--', '--', '--', '--', '--', '--', '--', '--', '--', '--', '--', '--', '--', '--', '--', '--', '--',
                   ':', ':', ':', ':', ':', ':', ':', ':', ':', ':', ':', ':', ':', ':', ':', ':', ':', ':', ':', ':', ':', ':']
    
    # initialize a dataframee with reactions as columns and polygons as rows
    df_percent = pd.DataFrame(columns=polys, index=pd.Index(rx_list))
    
    # loop through polygons, plot reaction terms, and tabulate errors for terms that should be zero
    for poly in polys:
    
        # get data just for this polygon
        ind = df['Control Volume']==poly
        df1 = df.loc[ind]
        time = df1['time'].astype('datetime64[ns]')
    
        # create figure with all reactions
        fig, ax = plt.subplots(figsize=(16,16))
        counter2 = 0
        for rx in rx_list:

            ## skip some terms when troubleshooting to see smaller terms a bit better
            #if rx=='NO3,dDenit':
            #    continue
            #if rx=='OONS2,dBurS2OON':
            #    continue
            #if rx=='DetNS2,dBurS2DetN':
            #    continue
            #if rx=='DiatS1,dBurS1Diat':
            #    continue

            ax.plot(time, df1[rx], label=rx, color = plot_colors[counter2], linestyle = line_styles[counter2])
            counter2 = counter2 + 1

        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05))
        ax.set_ylabel('reaction rate g/d')
        ax.set_title('%s: %s' % (step0_config.runid, poly))
        fig.tight_layout()
        plt.savefig(os.path.join(output_path,'%s_%s_%s_check_rx_mass_cons.png' % (step0_config.runid, param, poly)))
        plt.close('all')
    
        # compute time average of all reaction terms
        df1_tavg = df1[rx_list].mean(axis=0)
    
        # compute the percent of each reaction compared to the absolute value of the "normalize by" reaction
        df1_percent = df1_tavg/np.abs(df1_tavg[normalize_by])*100
        
        # tabulate percent
        df_percent[poly] = df1_percent
    
    # take area weighted average of the normalized reactions
    total_area = np.sum(gdf.area.values)
    area = np.tile(gdf.area.values, (len(df_percent),1))

    df_percent_avg = pd.DataFrame(columns=df_percent.index)
    for irx, rx in enumerate(df_percent.index):
        df_percent_avg.loc[0,rx] = np.nanmean(df_percent.iloc[irx] * area[irx,:] / total_area)
    
    # now loop through the reaction terms and create a pdf that shows percent contribution of each, w.r.t. max souce/sink
    with PdfPages(rx_map_path) as pdf:
    
        for rx in rx_list:
    
            # load up the geodataframe with the percent values correcponding to this reaction
            gdf['percent'] = df_percent.loc[rx].values
    
            # format the reaction name for printing on the plot
            rx1 = rx.replace(' + ',' +\n              ')
    
            # plot percent 
            fig, ax = plt.subplots(figsize=(11, 11))
            gdf.plot(ax=ax, column='percent', vmin=-100, vmax=100, cmap='seismic', legend=True)
            gdf.boundary.plot(ax=ax, color='k')
            ax.axis('off')
            ax.set_title('%s: reaction rate as percent of |%s|\ntime averaged over entire simulation' % (step0_config.runid, normalize_by))
            ax.text(rx_pos[0],rx_pos[1],rx1,ha='left',va='top',fontsize=14)
            fig.tight_layout()
            pdf.savefig()
            plt.close('all')
    
    # print a warning if there are mass conservation errors detected, and abort if asked
    for rx in rx_list:
    
        if 'ZERO' in rx:

            if np.abs(df_percent_avg[rx].values[0]) > step0_config.error_tol_percent:

                logging.info('WARNING: Reaction %s is NOT zero. Averaged over whole domain and simulation period it is %f ' % (rx,df_percent_avg[rx]) + 
                              'percent of %s, which exceeds the error tolerance %f percent' % (normalize_by, step0_config.error_tol_percent))

                if step0_config.abort_for_mass_cons_error:
                    raise Exception('ABORTING for mass conservation error, see command line and log_step4.log for details ' + 
                                    'consider setting step0_config.abort_for_mass_cons_error to False for troubleshooting')

            else:

                logging.info('SUCCESS: Reaction %s, averaged over whole domain and simulation period, is %f ' % (rx,df_percent_avg[rx].values[0]) +  
                             'percent of %s, which is below error tolerance %f percent' % (normalize_by, step0_config.error_tol_percent))
    
logger_cleanup()    