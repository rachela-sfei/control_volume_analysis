
''' alliek August 2022
plot bay-wide maps of rates such as primary productivity, oxygen consumption, denitrification, etc. 
at seasonal, monthly, or even weekly time steps. this script can plot one time step at a time (e.g. Oct, Nov, Dec, etc.), 
comparing a list of run / water year combos at each time step, with one run/wy in each column, or it can plot multiple 
time steps for just one run all on the same plot, with each time step being a column. you may plot rates 
normalized by area, volume, or nothing. note that to create plots for a given time averaging period, you must
have already conducted a time average of the balance tables for that period in step6_aggregate_in_time.py (in the 
Scripts/create_balance_tables directory of this Control_Volume_Analysis repository). it is common to skip some
time averaging periods to save space, so you may need to go back and run step6_aggregate_in_time.py again, if you
want time resolution like weekly.

feel free to define new rates -- search for "if rate_name==" to see where the rates are defined

the results are saved in a subfolder called "rate_maps"

'''

##################
# IMPORT MODULES
##################

import sys,os
import copy
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib as mpl
if not 'DISPLAY' in os.environ:
    mpl.use('agg')
    plt.switch_backend('Agg')
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import numpy as np
import os, sys
import pandas as pd
import cmocean 
import nmmn.plots
turbo=nmmn.plots.turbocmap()
import geopandas as gpd
from importlib import reload
import control_volume_plotting_library as CVPL # plotting library must be in same folder as this script
reload(CVPL)

###################
## USER INPUT
###################

############################################################################################################################
# RUN ID, WATER YEAR, AND RATE LISTS ARE SPECIAL BECAUSE THESE DETERMINE THE NUMBER OF SUBPLOTS AND THEIR CONTENT
#
#       make a list of run ID's and a list of water years. these lists should be the same length N. the script will make 
#       subplots with N columns where each column n corresponds to run runid_list[n] and water year wy_list[n]. one figure 
#       with N subplots will be created per time step in the time averaging period (e.g. 4 figures for Seasonal averages)
#
#       special case: if there is only ONE entry in runid_list and wy_list, there is an option to try and stuff all of 
#       the time steps onto a single plot, instead of having one plot per time step -- if you want to do this, set 
#       all_time_together = True below
#
#       finally specify the list of rates you want to plot. these can be compiled into a single figure, with one rate
#       per row (in which case you need to give a name to the collection of rates for the title and the figure name)
#       or you can make one figure per rate
#
########################################################################################################################


# this example will make figures with 3 subplots, each corresponding to a different run
#runid_list = ['FR13_025','FR17_018','FR18_006']
#wy_list = [2013, 2017, 2018]
#all_time_together = False

# this example will make figures with 6 subplots, each corresponding to a different water year for the same run
#runid_list = ['G141_13to18_246','G141_13to18_246','G141_13to18_246','G141_13to18_246','G141_13to18_246','G141_13to18_246']
#wy_list = [2013, 2014, 2015, 2016, 2017, 2018]
#all_time_together = False

## this is like the previous example but also compares apples-to-apples full resolution and aggregated runs
#runid_list = ['G141_13to18_246','FR13_003','G141_13to18_246','FR17_003']
#wy_list = [2013, 2013, 2017, 2017]
#all_time_together = False

# in this example, provided that all_time_together = True (see below) a single 1xN figure is generated where N is the 
# number of time averaging periods in 2013 (e.g. 4 for Seasonal, 12 for monthly). if all_time_together = False, this
# example will generate N figures with one subplot each. Note if you want to plot multiple water years in an agg run 
# you should do them one at a time (sorry it's not automated)
#runid_list = ['FR18_007']
#wy_list = [2018]
#server_list = ['chicago']
#all_time_together = True

# runid_list = ['FR13_028', 'FR14_001', 'FR15_001', 'FR16_001','FR17_021','FR18_009']
# wy_list = [2013,2014,2015,2016,2017,2018]
# server_list = ['chicago','boise','boise','boise','chicago','chicago']
# all_time_together = False

runid_list = ['FR21_007', 'FR21_009','FR21_008']
wy_list = [2021,2021,2021]
server_list = ['chicago','chicago','chicago']
vol_list = ['vol2','vol2','vol2']
all_time_together = False

#runid_list = ['G141_22_010','G141_22_011','G141_22_006','G141_22_018','G141_22_021']
#wy_list=[2022,2022,2022,2022,2022]
#server_list = ['fortcollins','fortcollins','fortcollins','fortcollins','fortcollins']
#all_time_together=False

#runid_list = ['FR22_012','FR22_013']
#wy_list=[2022,2022]
#server_list = ['fortcollins','fortcollins']
#all_time_together=False

for select_a_rate_set in [-3,-2,-1,1,2,4]:

    if select_a_rate_set==-3:

        # subset DIN budget for CV manuscript
        rate_list = ['dpp-pelagic','settling',
                     'grazing','mortality-pelagic',
                     'dpp-benthic','mortality-benthic',
                     'burial','total-algae-rx']  
        multiple_rates_on_same_figure = True
        multiple_rates_figure_label = 'Algae_Rx_Summary'
        multiple_rates_figure_title = 'Mass Budget for Diat + Green + DiatS1'
        caxis_limit_override = {'Area' : 1.4, 'Volume': 0.7, 'None' : None}


    if select_a_rate_set==-2:

        # subset DIN budget for CV manuscript
        rate_list = ['n-dpp',    
                     'din_recycling',
                     'dmin_sed']  
        multiple_rates_on_same_figure = True
        multiple_rates_figure_label = 'DIN_Uptake_Recycling'
        multiple_rates_figure_title = 'DIN Uptake and Recycling'
        caxis_limit_override = {'Area' : 0.2, 'Volume': 0.1, 'None' : 3e6}


    if select_a_rate_set==-1:

        # subset DIN budget for CV manuscript
        rate_list = ['denit']  
        multiple_rates_on_same_figure = False
        multiple_rates_figure_label = 'Denit'
        multiple_rates_figure_title = 'Denitrification'
        caxis_limit_override = {'Area' : None, 'Volume': None, 'None' : None}
        all_time_together=True

    if select_a_rate_set==0:

        # THIS DOESN'T WORK, NOT SURE IT EVER WORKED

        # in this example we plot ALL the available rates (unless the user has defined some more I didn't include here)
        # but we plot them separately
        rate_list = ['oxycon-water','oxycon-sed','dpp','dpp-benthic','dpp-pelagic','denit','n-dpp','n-dpp-pelagic',
                     'n-dpp-benthic','din_recycling','dmin_water','dmin_sed','din_rx','tn_rx','n-algae-sed','pon-sed',
                     'diats1-loss','diats1-aut','tn_include_sediment_loss']
        multiple_rates_on_same_figure = False
        multiple_rates_figure_label = None
        multiple_rates_figure_title = None
        caxis_limit_override = {'Area' : None, 'Volume': None, 'None' : None}

    elif select_a_rate_set==1:

        # in this example we plot all the rates that make up the net DIN reaction
        rate_list = ['n-dpp',
                     'denit',             
                     'din_recycling',     
                     'dmin_sed',   
                     'din_rx']  
        multiple_rates_on_same_figure = True
        multiple_rates_figure_label = 'DIN_Rx_Summary'
        multiple_rates_figure_title = 'DIN Reaction Summary'
        caxis_limit_override = {'Area' : None, 'Volume': None, 'None' : None}
        #caxis_limit_override = {'Area' : 0.25, 'Volume': 0.12, 'None' : None}
        
    elif select_a_rate_set==2:    

        ### in this example we plot all the rates that make up the net TN reaction
        rate_list = ['denit',     
                     'n-sed',        
                     'n-diats1-mort',  
                     #'n-diats1-buri', # seems to be zero for the time being     
                     #'diats1-aut',  # seems to be zero for the time being
                     'dmin_sed',   
                     'tn_rx']
        multiple_rates_on_same_figure = True
        multiple_rates_figure_label = 'TN_Rx_Summary'
        multiple_rates_figure_title = 'TN Reaction Summary'
        caxis_limit_override = {'Area' : None, 'Volume': None, 'None' : None}
        #caxis_limit_override = {'Area' : 0.075, 'Volume': 0.05, 'None' : None}

    elif select_a_rate_set==3:   

        # THIS DOESN'T WORK ANYMORE SINCE WE REMOVED TOTALDETNS COMPOUND SUBSTANCE

        # in this example we plot all the rates that make up the net TotalDetNS reaction
        rate_list = ['n-sed',
                     'n-diats1-mort',
                     'dmin_sed1',             
                     'dmin_sed2',     
                     'det_bur',
                     'totaldetns_rx']  
        multiple_rates_on_same_figure = True
        multiple_rates_figure_label = 'TotalDetNS_Rx_Summary'
        multiple_rates_figure_title = 'Detritus Reaction Summary'
        caxis_limit_override = {'Area' : None, 'Volume': None, 'None' : None}

    elif select_a_rate_set==4:

        # in this example we plot all the rates that make up the net OXY reaction
        rate_list = ['oxycon-water',
                     'oxycon-sed',
                     'oxy1',             
                     'oxy2',     
                     'oxy3',
                     'oxy4',     
                     'oxy5',     
                     'oxy6',     
                     'oxy7',     
                     'oxy8',     
                     'oxy_rx']  
        multiple_rates_on_same_figure = True
        multiple_rates_figure_label = 'OXY_Rx_Summary'
        multiple_rates_figure_title = 'OXY Reaction Summary'
        caxis_limit_override = {'Area' : None, 'Volume': None, 'None' : None}

    ################################################################################################################
    # THE FOLLOWING LISTS ARE JUST FOR BATCH PROCESSING PURPOSES, SO THE USER DOESN'T HAVE TO CHANGE THE SCRIPT
    # EACH TIME THEY WANT TO PLOT A NEW RATE, TIME AVERAGING PERIOD, NORMALIZATION, ETC. CAN JUST RUN IT ALL AT ONCE
    ################################################################################################################

    # list of time averaging periods (choices are 'Annual','Seasonal','Monthly')
    time_period_list = ['Seasonal']
    #time_period_list = ['Annual','Seasonal']

    # list of normalizations (divide by 'None','Area','Volume')
    #norm_list = ['Area','Volume']
    norm_list = ['Area']

    # get length of run list and wy list, make sure they're the same length, also check if all runs are the same
    nruns = len(runid_list)
    assert nruns == len(wy_list)

    # base directory for the output figures (in theory should be able to run on windows laptop with mounted drives or on server)
    figure_base_dir = '/richmondvol1/hpcshared/open_bay/bgc/figures'

    # base directory for model input (used to find shapefiles)
    input_base_dir = '/richmondvol1/hpcshared'

    # nanpercentile for color map cutoff
    cper = 95

    # set the approximate size of the figure subplots in inches (if there are N subplots the figure will be N x subplot_width wide)
    subplot_width = 4
    subplot_height = 5

    # set font size (may want to adjust)
    plt.rcParams['font.size'] = '16'

    # path to the shapefile for full res / aggregated runs
    shp_fn_FR = os.path.join(input_base_dir,'inputs','shapefiles','Agg_mod_contiguous.shp')
    shp_fn_AGG = os.path.join(input_base_dir,'inputs','shapefiles','Agg_mod_contiguous_141.shp')

    # this gigantic function is really user input because this is where the user can define different rates to plot.
    # the user should keep a close eye on this function becuase the reaction_list variables may need to change if more
    # substances are added to the model or if the user has changed the way reactions are grouped in 
    # step3_group_reactions_for_composite_parameters.py, as specified in composite_reaction_dict of step0_config.py)
    def get_rate_properties(rate_name):

        ''' 
        usage: 
        
        rate_title, grams_of_what, balance_table_list, multiplier_list, reaction_list, cmap, cmap_diverging = get_rate_properties(rate_name)
        
        '''
        if rate_name=='oxycon-water':
        
            #rate_title = 'Oxygen Consumption (Water Column)'        # title for figure
            rate_title = '-1 x OXY,dOxCon'        
            grams_of_what = 'O'                                     # grams of what in the units?   
            balance_table_list = ['oxy_Table.csv']                  # list of balance tables
            multiplier_list = [-1]                                  # multiplier for each balance table
            reaction_list = [['OXY,dOxCon']]                        # for each balance table, list of reactions to sum
            cmap = turbo#cmocean.cm.amp                                   # color map
            cmap_diverging = False                                  # center at zero (True if rate goes positive and negative)?

        elif rate_name=='oxycon-sed':
        
            #rate_title = 'Oxygen Consumption (Sediment)'
            rate_title = '-1 x OXY,dMinTotalDetCS1'
            grams_of_what = 'O'
            balance_table_list = ['oxy_Table.csv']
            multiplier_list = [-1]
            reaction_list = [['OXY,dMinDetCS1', 'OXY,dMinDetCS2', 'OXY,dMinOOCS1', 'OXY,dMinOOCS2']]
            cmap = turbo#cmocean.cm.amp  
            cmap_diverging = False

        elif rate_name=='oxy1':
        
            rate_title = '-1 x OXY,dNitrif'
            grams_of_what = 'O'
            balance_table_list = ['oxy_Table.csv']
            multiplier_list = [-1]
            reaction_list = [['OXY,dNitrif']]
            cmap = turbo#cmocean.cm.amp  
            cmap_diverging = False

        elif rate_name=='oxy2':
        
            rate_title = '-1 x OXY,dZ_Resp'
            grams_of_what = 'O'
            balance_table_list = ['oxy_Table.csv']
            multiplier_list = [-1]
            reaction_list = [['OXY,dZ_Resp']]
            cmap = turbo#cmocean.cm.amp  
            cmap_diverging = False

        elif rate_name=='oxy3':
        
            rate_title = 'OXY,dDenitWat'
            grams_of_what = 'O'
            balance_table_list = ['oxy_Table.csv']
            multiplier_list = [1]
            reaction_list = [['OXY,dDenitWat']]
            cmap = turbo#cmocean.cm.dense  
            cmap_diverging = False

        elif rate_name=='oxy4':
        
            rate_title = 'OXY,dPPDiat + OXY,dPPGreen\n(includes correction)'
            grams_of_what = 'O'
            balance_table_list = ['oxy_Table.csv']
            multiplier_list = [1]
            reaction_list = [['OXY,dPPDiat', 'OXY,dcPPDiat', 'OXY,dPPGreen', 'OXY,dcPPGreen']]
            cmap = turbo#cmocean.cm.dense  
            cmap_diverging = False

        elif rate_name=='oxy5':
        
            rate_title = 'OXY,dPPDiatS1'
            grams_of_what = 'O'
            balance_table_list = ['oxy_Table.csv']
            multiplier_list = [1]
            reaction_list = [['OXY,dPPDiatS1']]
            cmap = turbo#cmocean.cm.dense  
            cmap_diverging = False

        elif rate_name=='oxy6':
        
            rate_title = 'OXY,dNO3Upt'
            grams_of_what = 'O'
            balance_table_list = ['oxy_Table.csv']
            multiplier_list = [1]
            reaction_list = [['OXY,dNO3Upt']]
            cmap = turbo#cmocean.cm.dense  
            cmap_diverging = False


        elif rate_name=='oxy7':
        
            rate_title = 'OXY,dNO3UptS1'
            grams_of_what = 'O'
            balance_table_list = ['oxy_Table.csv']
            multiplier_list = [1]
            reaction_list = [['OXY,dNO3UptS1']]
            cmap = turbo#cmocean.cm.dense  
            cmap_diverging = False


        elif rate_name=='oxy8':
        
            rate_title = 'OXY,dREAROXY'
            grams_of_what = 'O'
            balance_table_list = ['oxy_Table.csv']
            multiplier_list = [1]
            reaction_list = [['OXY,dREAROXY']]
            cmap = turbo#cmocean.cm.balance_r  
            cmap_diverging = True

        elif rate_name=='oxy_rx':
        
            rate_title = 'Net OXY Rx.'
            grams_of_what = 'O'
            balance_table_list = ['oxy_Table.csv']
            multiplier_list = [1]
            reaction_list = [['OXY,dDenitWat', 'OXY,dNitrif',
                              'OXY,dMinDetCS1', 'OXY,dMinDetCS2', 'OXY,dMinOOCS1', 'OXY,dMinOOCS2',
                              'OXY,dOxCon', 'OXY,dZ_Resp', 'OXY,dREAROXY', 'OXY,dPPGreen',
                              'OXY,dPPDiat', 'OXY,dPPDiatS1', 'OXY,dNO3UptS1', 'OXY,dcPPGreen',
                              'OXY,dcPPDiat', 'OXY,dNO3Upt']]
            cmap = turbo#cmocean.cm.balance_r
            cmap_diverging = True

        elif rate_name=='dpp':
        
            rate_title = 'Net Primary Productivity' 
            grams_of_what = 'C'
            balance_table_list = ['algae_Table.csv']
            multiplier_list = [1]
            reaction_list = [['Diat,dPPDiat','Green,dPPGreen','DiatS1,dPPDiatS1']]
            cmap = turbo#cmocean.cm.amp
            cmap_diverging = False

        elif rate_name=='dpp-benthic':
        
            rate_title = 'Net Primary Productivity (Benthic)'
            grams_of_what = 'C'
            balance_table_list = ['algae_Table.csv']
            multiplier_list = [1]
            reaction_list = [['DiatS1,dPPDiatS1']]
            cmap = turbo#cmocean.cm.amp
            cmap_diverging = False

        elif rate_name=='dpp-pelagic':
        
            rate_title = 'Net Primary Productivity (Pelagic)'
            grams_of_what = 'C'
            balance_table_list = ['algae_Table.csv']
            multiplier_list = [1]
            reaction_list = [['Diat,dPPDiat','Green,dPPGreen']]
            cmap = turbo#cmocean.cm.amp
            cmap_diverging = False

        elif rate_name=='mortality-pelagic':
        
            rate_title = 'Mortailty (Pelagic)'
            grams_of_what = 'C'
            balance_table_list = ['algae_Table.csv']
            multiplier_list = [-1]
            reaction_list = [['Diat,dMrtDiat', 'Green,dMrtGreen']]
            cmap = turbo#cmocean.cm.amp
            cmap_diverging = False

        elif rate_name=='mortality-benthic':
        
            rate_title = 'Mortailty (Benthic)'
            grams_of_what = 'C'
            balance_table_list = ['algae_Table.csv']
            multiplier_list = [-1]
            reaction_list = [['DiatS1,dMrtDiatS1']]
            cmap = turbo#cmocean.cm.amp
            cmap_diverging = False
        elif rate_name=='grazing':
        
            rate_title = 'Grazing'
            grams_of_what = 'C'
            balance_table_list = ['algae_Table.csv']
            multiplier_list = [-1]
            reaction_list = [['Diat,dZ_Diat', 'Green,dZ_Grn']]
            cmap = turbo#cmocean.cm.amp
            cmap_diverging = False

        elif rate_name=='settling':
        
            rate_title = 'Settling'
            grams_of_what = 'C'
            balance_table_list = ['algae_Table.csv']
            multiplier_list = [-1]
            reaction_list = [['Diat,dSedDiat','Green,dSedGreen']]
            cmap = turbo#cmocean.cm.amp
            cmap_diverging = False

        elif rate_name=='burial':
        
            rate_title = 'Burial'
            grams_of_what = 'C'
            balance_table_list = ['algae_Table.csv']
            multiplier_list = [-1]
            reaction_list = [['DiatS1,dBurS1Diat']]
            cmap = turbo#cmocean.cm.amp
            cmap_diverging = False

        elif rate_name=='total-algae-rx':
        
            rate_title = 'Net Rx.'
            grams_of_what = 'C'
            balance_table_list = ['algae_Table.csv']
            multiplier_list = [1]
            reaction_list = [['Diat,dPPDiat', 'Green,dPPGreen',
                              'DiatS1,dPPDiatS1', 
                              'Diat,dMrtDiat', 'Green,dMrtGreen','DiatS1,dMrtDiatS1', 
                              'Diat,dZ_Diat', 'Green,dZ_Grn', 
                              'Diat,dSedDiat','Green,dSedGreen', 
                              'DiatS1,dBurS1Diat']]
            cmap = turbo#cmocean.cm.balance
            cmap_diverging = True


        
        elif rate_name=='denit':
            
            rate_title = 'Denitrification'                      
            grams_of_what = 'N'                                 
            balance_table_list = ['din_Table.csv']              
            multiplier_list = [-1]                              
            reaction_list = [["NO3,dDenit"]]# already lumped this in, in latest version of CV scripts:"NO3,dNiDen"]]      
            cmap = turbo#cmocean.cm.amp # cmocean.cm.dense # make it positive to plot with assimilation                             
            cmap_diverging = False                             

        elif rate_name=='n-dpp':
        
            rate_title = 'Net Primary Productivity'
            grams_of_what = 'N'
            balance_table_list = ['din_Table.csv']
            multiplier_list = [-1]
            reaction_list = [['DIN,dDINUpt','DIN,dDINUptS1']]
            cmap = turbo#cmocean.cm.amp
            cmap_diverging = False

        elif rate_name=='n-dpp-pelagic':
        
            rate_title = 'Net Pelagic Pr. Prod.'
            grams_of_what = 'N'
            balance_table_list = ['din_Table.csv']
            multiplier_list = [-1]
            reaction_list = [['DIN,dDINUpt']]
            cmap = turbo#cmocean.cm.dense
            cmap_diverging = False

        elif rate_name=='n-dpp-benthic':
        
            rate_title = 'Net Benthic Pr. Prod.'
            grams_of_what = 'N'
            balance_table_list = ['din_Table.csv']
            multiplier_list = [-1]
            reaction_list = [['DIN,dDINUptS1']]
            cmap = turbo#cmocean.cm.dense
            cmap_diverging = False

        elif rate_name=='din_recycling':
        
            rate_title = 'DIN Recycling (Respiration + Mortality +\nMineralization of DON and PON)'
            grams_of_what = 'N'
            balance_table_list = ['din_Table.csv']
            multiplier_list = [1]
            reaction_list = [["NH4,dZ_NRes",
                              "NH4,dNH4Aut",
                              'NH4,dNH4AUTS1',
                              "NH4,dMinDON",
                              "NH4,dMinPON1",
                              "NH4,dMinPON2"]]
            cmap = turbo#cmocean.cm.amp
            cmap_diverging = False

        elif rate_name=='dmin_sed':
        
            rate_title = 'Detritus Mineralization'
            grams_of_what = 'N'
            balance_table_list = ['din_Table.csv']
            multiplier_list = [1]
            reaction_list = [['NH4,dMinDetNS12']] #,'NH4,dMinOONS12']] # exclude OONS1 and OONS2, Pradeep says to pretend it's loading
            cmap = turbo#cmocean.cm.amp
            cmap_diverging = False

        elif rate_name=='dmin_sed1':
        
            rate_title = 'DetNS1 + OONS1 Mineral.'
            grams_of_what = 'N'
            balance_table_list = ['totaldetns_Table.csv']
            multiplier_list = [-1]
            reaction_list = [['DetNS1,dMinDetNS1',
                              'OONS1,dMinOONS1']]
            cmap = turbo#cmocean.cm.dense
            cmap_diverging = False

        elif rate_name=='dmin_sed2':
        
            rate_title = 'DetNS2 + OONS2 Mineral.'
            grams_of_what = 'N'
            balance_table_list = ['totaldetns_Table.csv']
            multiplier_list = [-1]
            reaction_list = [['DetNS2,dMinDetNS2',
                              'OONS2,dMinOONS2']]
            cmap = turbo#cmocean.cm.dense
            cmap_diverging = False

        elif rate_name=='det_bur':
        
            rate_title = 'DetNS2 + OONS2 Burial'
            grams_of_what = 'N'
            balance_table_list = ['totaldetns_Table.csv']
            multiplier_list = [-1]
            reaction_list = [['DetNS2,dBurS2DetN','OONS2,dBurS2OON']]
            cmap = turbo#cmocean.cm.dense
            cmap_diverging = False
        
        elif rate_name=='din_assim':
        
            rate_title = 'DIN Assimilation\n(dM/dt - Rx)'
            grams_of_what = 'N'
            balance_table_list = ['din_Table.csv','din_Table.csv']
            multiplier_list = [1,-1]
            reaction_list = [['dVar/dt'], ['NH4,dMinDetNS12', 
                                           #'NH4,dMinOONS12', # pretend this is loading
                                           'DIN,dDINUpt', 
                                           'DIN,dDINUptS1',
                                           'NO3,dDenit', 
                                           'NH4,dMinPON1', 
                                           'NH4,dMinPON2', 
                                           'NH4,dMinDON',
                                           'NH4,dZ_NRes', 
                                           'NH4,dNH4Aut', 
                                           'NH4,dNH4AUTS1']]
            cmap = turbo#cmocean.cm.balance
            cmap_diverging = True

        elif rate_name=='tn_plus_detns12_assim':

            rate_title = 'TN Assimilation\n(dM/dt - Rx)'
            grams_of_what = 'N'
            balance_table_list = ['tn_plus_detns12_Table.csv','tn_plus_detns12_Table.csv']
            multiplier_list = [1,-1]
            reaction_list = [['dVar/dt'],['NO3,dDenit',
                                          'DetNS2,dBurS2DetN', 
                                          'DiatS1,dBurS1Diat'
                                          #'NH4,dMinOONS12', # pretend this is loading 
                                          'PON2,dSedPON2']]
            cmap = turbo#cmocean.cm.balance
            cmap_diverging = True

        elif rate_name=='din_rx':

            rate_title = 'Net DIN Rx'  
            grams_of_what = 'N'
            balance_table_list = ['din_Table.csv']
            multiplier_list = [1]
            reaction_list = [['DIN,dDINUpt','DIN,dDINUptS1',
                              "NO3,dDenit","NH4,dZ_NRes",
                              "NH4,dNH4Aut",'NH4,dNH4AUTS1',"NH4,dMinDON","NH4,dMinPON1",
                              "NH4,dMinPON2",'NH4,dMinDetNS12']]
            cmap = turbo#cmocean.cm.balance
            cmap_diverging = True

        elif rate_name=='tn_rx':

            rate_title = 'Net TN Rx.'  
            grams_of_what = 'N'
            balance_table_list = ['tn_Table.csv']
            multiplier_list = [1]
            reaction_list = [['NO3,dDenit',
                              'NO3,dNiDen',
                              'Algae,dSedAlgae',
                              'PON,dSedPON',
                              'DiatS1,dMrtDiatS1',
                              'DiatS1,dBurS1Diat',
                              'NH4,dMinTotalDetNS',
                              'NH4,dNH4AUTS1',
                              'NH4,dClam_NRes',
                              'PON1,dClam_NDef',
                              'Algae,dClam_Algae',
                              'PON1,dClam_PON1']]
            cmap = turbo#cmocean.cm.balance
            cmap_diverging = True

        elif rate_name=='n-sed':
        
            rate_title = 'Settling of Algae + PON'
            grams_of_what = 'N'
            balance_table_list = ['tn_Table.csv']
            multiplier_list = [-1]
            reaction_list = [["Algae,dSedAlgae","PON,dSedPON"]]
            cmap = turbo#cmocean.cm.dense
            cmap_diverging = False

        elif rate_name=='n-diats1-mort':
        
            rate_title = 'Benthic Algae Mortality'
            grams_of_what = 'N'
            balance_table_list = ['tn_Table.csv']
            multiplier_list = [-1]
            reaction_list = [['DiatS1,dMrtDiatS1']]
            cmap = turbo#cmocean.cm.dense
            cmap_diverging = False

        elif rate_name=='n-diats1-buri':
        
            rate_title = 'Benthic Algae Burial'
            grams_of_what = 'N'
            balance_table_list = ['tn_Table.csv']
            multiplier_list = [-1]
            reaction_list = [['DiatS1,dBurS1Diat']]
            cmap = turbo#cmocean.cm.dense
            cmap_diverging = False

        elif rate_name=='diats1-aut':

            rate_title = 'Benthic Algae Autolysis'
            grams_of_what = 'N'
            balance_table_list = ['tn_Table.csv']
            multiplier_list = [1]
            reaction_list = [['NH4,dNH4AUTS1']]
            cmap = turbo#cmocean.cm.amp
            cmap_diverging = False

        elif rate_name=='tn_include_sediment_loss':
        
            rate_title = 'TN (including sediment N) Reactive Loss'
            grams_of_what = 'N'
            balance_table_list = ['tn_include_sediment_Table.csv']
            multiplier_list = [-1]
            reaction_list = [['NO3,dDenit',
                              'NO3,dNiDen',
                              'DetNS2,dBurS2DetN',
                              'OONS2,dBurS2OON',
                              'DiatS1,dBurS1Diat']]
            cmap = turbo#cmocean.cm.dense
            cmap_diverging = False

        elif rate_name=='totaldetns_rx':
        
            rate_title = 'Detritus Net Rx.'
            grams_of_what = 'N'
            balance_table_list = ['totaldetns_Table.csv']
            multiplier_list = [1]
            reaction_list = [['DetNS1,dMrtDetNS1',
                              'DetNS1,dSedAlgN', 
                              'DetNS1,dSedPON1', 
                              'DetNS1,dMinDetNS1',
                              'OONS1,dMinOONS1',
                              'DetNS2,dMinDetNS2',
                              'OONS2,dMinOONS2',
                              'DetNS2,dBurS2DetN',
                              'OONS2,dBurS2OON']]
            cmap = turbo#cmocean.cm.amp
            cmap_diverging = False
        
        return rate_title, grams_of_what, balance_table_list, multiplier_list, reaction_list, cmap, cmap_diverging

    # subset of polygons to include in plot (don't mess with this unless the shapefiles are drastically altered)
    iplot_FR = [0, 117, 139, 2, 113, 114, 115, 111, 1, 3, 116, 7, 4, 112, 5, 108, 109, 110, 9, 107, 
    6, 8, 29, 10, 12, 11, 138, 137, 100, 19, 18, 13, 20, 26, 25, 21, 14, 24, 101, 102, 103, 104, 
    105, 106, 28, 27, 22, 15, 30, 23, 35, 34, 33, 32, 31, 17, 41, 40, 39, 38, 37, 36, 16, 140, 
    44, 43, 42, 46, 45, 49, 47, 97, 98, 86, 96, 95, 85, 93, 52, 87, 94, 48, 51, 50, 90, 88, 91, 
    89, 92, 53, 56, 99, 54, 55, 57, 67, 65, 66, 136, 58, 59, 63, 64, 60, 62, 61, 143, 144, 141, 
    68, 69, 70, 71, 78, 72, 84, 79, 146, 80, 82, 83, 142, 145, 73, 81, 74, 76, 77, 75]
    iplot_AGG = [  0,   1,   2,   3,   4,   5,   6,   7,   8,   9,  10,  11,  12,
        13,  14,  15,  16,  17,  18,  19,  20,  21,  22,  23,  24,  25,
        26,  27,  28,  29,  30,  31,  32,  33,  34,  35,  36,  37,  38,
        39,  40,  41,  42,  43,  44,  45,  46,  47,  48,  49,  50,  51,
        52,  53,  54,  55,  56,  57,  58,  59,  60,  61,  62,  63,  64,
        65,  66,  67,  68,  69,  70,  71,  72,  73,  74,  75,  76,  77,
        78,  79,  80,  81,  82,  83,  84,  85,  86,  87,  88,  89,  90,
        91,  92,  93,  94,  95,  96,  97,  98,  99, 100, 101, 102, 103,
       104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115,
       134, 136, 137, 138, 139, 140]

    # axis limits
    axlim = (531280.627955355, 610527.2330959855, 4138850.8659710716, 4233404.6647333605)

    ##################
    ### MAIN
    ##################

    # get strings with concise lists of runs and water years
    run_list_str = CVPL.make_concise_runid_list_string(runid_list)
    wy_list_str = CVPL.make_concise_water_year_list_string(wy_list)

    # path to figures, create if it does not exist
    figure_path = os.path.join(figure_base_dir, run_list_str, 'rate_maps')
    if not os.path.exists(figure_path):
        os.makedirs(figure_path)
    print('\nfigures will be saved here: %s\n' % figure_path)

    # check if all the runs are the same
    if len(np.unique(runid_list))==1:
        all_runs_same = True
    else:
        all_runs_same = False

    # loop through averaging time periods (Annual, Seasonal, Monthly)
    for time_period in time_period_list:

        # loop through norms (Area, Volume, None)
        for norm in norm_list:

            # loop through rates to plot
            nrates = len(rate_list)
            for irate, rate_name in enumerate(rate_list):

                #if rate_name=='tn_plus_detns12_assim':
                #    sys.exit()

                # load up a bunch of variables specific to this rate_name (this function is defined in the user input section above)
                rate_title, grams_of_what, balance_table_list, multiplier_list, reaction_list, cmap, cmap_diverging = get_rate_properties(rate_name)

                # units for normalized data and string for including in figure name
                if norm == 'Volume':
                    norm_units = 'g %s/m$^3$/d' % grams_of_what
                    norm_name = '_Per_Volume'
                elif norm == 'Area':
                    norm_units = 'g %s/m$^2$/d' % grams_of_what
                    norm_name = '_Per_Area'
                elif norm == 'None':
                    norm_units = 'g %s/d' % grams_of_what
                    norm_name = ''
                else:
                    raise Exception("must specifiy normalization correctly")

                #######################################################################################################################################
                # here's phase 1 of the meat of this script
                # loop through the runs, building up a the dictionary of lists of geodataframes for plotting, and tracking the color bar limits 
                #######################################################################################################################################
                
                # check number of balance tables 
                ntables = len(balance_table_list)
                
                # initiliaze color bar limits, which will be calculated by looking across all the runs and all the time windows
                pmin_all = 0
                pmax_all = 0
                
                # initialize dictionary containing geodataframes for plotting all the runs and time windows (this is confusing, sorry about that, but it works and is fast enough)
                gdf_all_dict = {}
                time_labels_dict = {}
                
                # loop through the runs, 
                for irun in range(nruns):
                
                    # get run ID and water year
                    runid = runid_list[irun]
                    wy = wy_list[irun]

                    # get path to the balance table folder in the run folder
                    run_base_dir = '/%svol2/hpcshared' % server_list[irun]
                    run_dir = CVPL.get_run_dir(run_base_dir, runid)
                    balance_table_dir = os.path.join(run_dir,'Balance_Tables')

                    # path to the shapefile w/ the base level control volumes
                    if 'FR' in runid:
                        shp_fn = shp_fn_FR
                        iplot = iplot_FR
                    else:
                        shp_fn = shp_fn_AGG
                        iplot = iplot_AGG

                    # load the shapefile and initialize Rate column
                    gdf = gpd.read_file(shp_fn)
                    gdf['Rate'] = np.nan
                
                    # read the first balance table and sum up the reacitons, mutiplying by the appropriate stoichiometric multiplier
                    balance_table_name = balance_table_list[0].replace('.csv','_%s.csv' % time_period)
                    df = pd.read_csv(os.path.join(balance_table_dir, balance_table_name))

                    # need to check that all the reactions are in this run, 
                    reaction_list_0 = []
                    for rx in reaction_list[0]:
                        if rx in df.columns:
                            reaction_list_0.append(rx)
                    rate = multiplier_list[0]*df[reaction_list_0].sum(axis=1)

                    # if there is more than one balance table, add those up too, summing the reactions by the multipliers
                    if ntables>1:
                        for i in range(1,ntables):
                            balance_table_name = balance_table_list[i].replace('.csv','_%s.csv' % time_period)
                            df = pd.read_csv(os.path.join(balance_table_dir, balance_table_name))

                            # need to check that all reactions are in this run
                            reaction_list_i = []
                            for rx in reaction_list[i]:
                                if rx in df.columns:
                                    reaction_list_i.append(rx)
                            rate = rate + multiplier_list[i]*df[reaction_list_i].sum(axis=1)
                    
                    # from the last balance table, grab all the control voulme ID and geometry info, as well as the time axis, then
                    # add the rate 
                    df = df[['time', 'Time Period', 'Control Volume', 'Volume (Mean)', 'Area']]
                    df['Rate'] = rate
                    df['time'] = df['time'].astype('datetime64[ns]')

                    # select just the data in the water year specified for this plotting window
                    ind = np.logical_and(df['time']>=np.datetime64('%d-10-01' % (wy-1)), df['time']<np.datetime64('%d-10-01' % wy))
                    df = df.loc[ind]
                    
                    # get a list of the time period names
                    ind = df['Control Volume'] == 'polygon0'
                    time_labels = df['Time Period'].loc[ind].values
                    ntime = len(time_labels)
                    
                    # initialize list of geodataframes and a list of corresponding time window labels
                    gdf_all = []

                    # loop through time windows, building up list of geodataframes, and finding the max and min values
                    for itime in range(ntime):
                    
                        # loop through teh polygons
                        for poly in range(len(gdf)):
                        
                            # polygon name
                            polyname = 'polygon%d' % poly

                            # indices corresponding to polygon
                            ind = (df['Control Volume'] == polyname).values

                            # get divisor based on normaliization
                            if norm=='Volume':
                                V = df.loc[ind]['Volume (Mean)'].iloc[itime]
                            elif norm=='Area':
                                V = df.loc[ind]['Area'].iloc[itime]
                            elif norm=='None':
                                V = 1
                                
                            # find intersection of polygon and time window
                            
                            # take the average over this time window, normalize, and load into a geodataframe
                            gdf['Rate'].iloc[poly] = df.loc[ind]['Rate'].iloc[itime]/V
                                
                    
                        # get the max and min parameter value
                        pmax = np.nanpercentile(gdf['Rate'].iloc[iplot],cper)
                        pmin = np.nanpercentile(gdf['Rate'].iloc[iplot],100-cper)
                        
                        # keep track of the biggest limits across time windows AND across all runs
                        pmin_all = np.min([pmin,pmin_all])
                        pmax_all = np.max([pmax,pmax_all])
                        
                        # append geodataframes
                        gdf_all.append(copy.deepcopy(gdf))
                
                    # now append list of geodataframes to the dictionary
                    time_labels_dict[irun] = time_labels.copy()
                    gdf_all_dict[irun] = gdf_all.copy()
                    
                # if it's a diverging colormap, make the max and min the same amplitude
                if cmap_diverging:
                    pmax_all = np.max([pmax_all,-pmin_all])
                    pmin_all = -pmax_all

                # if a min/max is hard-coded, apply it here
                if not caxis_limit_override[norm] is None:
                    if cmap_diverging:
                        pmax_all = caxis_limit_override[norm]
                        pmin_all = - caxis_limit_override[norm]
                    else:
                        pmax_all = caxis_limit_override[norm]
                        pmin_all = 0

                # ######################################################################################################################
                # here is phase 2 of the meat of this script
                # now loop through time winodws and plot all the runs we are comparing in the same figure with the same color bar limits
                ########################################################################################################################

                # make figure title
                cbar_title = '%s\n(%s)' % (rate_title, norm_units)

                # make a function to add a subplot to figure
                def add_subplot(iaxis, itime, irun):

                    # get geodataframe
                    gdf = gdf_all_dict[irun][itime]
        
                    # path to the shapefile w/ the base level control volumes
                    if 'FR' in runid_list[irun]:
                        iplot = iplot_FR
                    else:
                        iplot = iplot_AGG
        
                    # get outline for plotting
                    gdf['dummy'] = 1
                    outline = gdf.iloc[iplot].dissolve(by='dummy')
                    
                    # add to plot
                    gdf.iloc[iplot].plot(ax=ax[iaxis], column='Rate', cmap=cmap, vmin = pmin_all, vmax = pmax_all)
                    outline.boundary.plot(ax=ax[iaxis],edgecolor='k')
                    ax[iaxis].axis(axlim)
                    
                    # turn off axis 
                    ax[iaxis].axis('off')

                    # set title (only put titles in first row)
                    title_str = ''
                    if (not multiple_rates_on_same_figure) or irate==0:
                        if not all_runs_same:
                            title_str += '%s\n' % runid_list[irun]
                        title_str += time_labels_dict[irun][itime]
                    ax[iaxis].set_title(title_str)

                def add_colorbar():

                    # add the colorbar
                    cax = inset_axes(ax[-1],
                        width="5%",  
                        height="90%",
                        loc='center right',
                        borderpad=-2
                       )

                    # make colorbar behave well in case that all values are zero
                    if pmin_all==0 and pmax_all==0:
                        if cmap_diverging:
                            pmin_all_1 = 1
                            pmax_all_1 = 1
                        else:
                            pmin_all_1 = 0
                            pmax_all_1 = 1
                    else:
                        pmin_all_1 = pmin_all
                        pmax_all_1 = pmax_all

                    # make norm and add colorbar
                    norm1 = mpl.colors.Normalize(vmin=pmin_all_1, vmax=pmax_all_1)
                    mpl.colorbar.ColorbarBase(cax, cmap=cmap,norm=norm1, label=cbar_title, orientation='vertical')
                    
                def finish_up_figure():

                    # save and close
                    fig.tight_layout(rect=rect)
                    fig.savefig(os.path.join(figure_path, figure_fn))
                     

                # figure out number of rows and columns 
                if nruns==1 and all_time_together:
                    ncols = ntime
                else: 
                    ncols = nruns
                if multiple_rates_on_same_figure:
                    nrows = nrates
                else:
                    nrows = 1

                # figure size depends on number of rows and columns, add some extra width for the legend which can be quite wide
                figsize = (subplot_width*ncols + 0.4*subplot_width, subplot_height*nrows)

                # the tight layout rectangle needs room for the legend, and also needs room for a suptitle if there is a 
                # suptitle, but we only have a suptitle in some cases 
                if multiple_rates_on_same_figure or (nruns==1 and all_time_together) or all_runs_same:
                    rect = [0, 0.01, 1-0.4/ncols, 1-0.025/nrows]
                else:
                    rect = [0, 0.01, 1-0.4/ncols, 0.99]

                # position of suptitle apparently needs to be adjusted for number of plots
                suptitle_y = np.min([0.98 + nrows*0.0014,0.99])

                #################################################################################################################
                # if there is only one run, there's an option to plot all the time windows on the same figure -- this does that
                #################################################################################################################

                if nruns==1 and all_time_together:

                    # if we are plotting one rate at a time, make the figure name and the figure for each rate
                    if not multiple_rates_on_same_figure:
                    
                        # make figure name
                        figure_fn = '%s_%s_Rate_Map%s_%s_%s_ALLTIME.png' % (run_list_str, wy_list_str, norm_name, time_period, rate_name)
                   
                        # set up figure subwindows with room for a colorbar 
                        fig, ax = plt.subplots(nrows, ncols, figsize=figsize)

                        # put runid in suptitle since there's only one run
                        fig.suptitle(runid,y=suptitle_y)

                    # otherwise, if multiple rates are on the same figure, make the figure name and the figure only when we are
                    # working on the very first rate, the other times, grab the axis from the following row
                    else:

                        if irate==0:

                            # make figure name
                            figure_fn = '%s_%s_Rate_Map%s_%s_%s_ALLTIME.png' % (run_list_str, wy_list_str, norm_name, time_period, multiple_rates_figure_label)
                   
                            # set up figure subwindows with room for a colorbar 
                            fig, ax1 = plt.subplots(nrows, ncols, figsize=figsize)

                            # add title -- if there is only one run or all runs are the same, put runid in the suptitle
                            if all_runs_same:
                                fig.suptitle(multiple_rates_figure_title + ': ' + runid,y=suptitle_y)
                            else:
                                fig.suptitle(multiple_rates_figure_title, y=suptitle_y)
            
                        # take the irate row of the axis
                        ax = ax1[irate,:]

                    # loop through the times and add a subplot for each time
                    for itime in range(ntime):
                    
                        add_subplot(itime, itime, irun)

                    # add a colorbar at the end of every ros
                    add_colorbar()        

                    # if plotting multiple rates on the same figure, save only on last rate, otherwise save for each rate
                    if (irate==(nrates-1)) or (not multiple_rates_on_same_figure):    
                        finish_up_figure()
                        plt.close('all')

                #####################################################################################################
                # otherwise make a separate plot for each time window, where the subplots are the different runs
                #####################################################################################################

                else:

                    if not multiple_rates_on_same_figure: 

                        for itime in range(ntime):
        
                            # make figure name
                            figure_fn = '%s_%s_Rate_Map_%s%s_%s_Time%04d.png' % (run_list_str, wy_list_str, time_period, norm_name, rate_name, itime)
                           
                            # set up figure subwindows with room for a colorbar 
                            fig, ax = plt.subplots(nrows, ncols, figsize=figsize)

                            # if all the runs are the same, add run as suptitle
                            if all_runs_same:
                                fig.suptitle(runid,y=suptitle_y)
            
                            # loop through the runs and plot
                            for irun in range(nruns):
                        
                                add_subplot(irun, itime, irun)
        
                            add_colorbar()            
                            finish_up_figure()
                            plt.close('all')

                    # if there are multiple rates on the same figure, we have generate a figure for each time step and keep them open 
                    # as we add all the rates to each... this may crash if we try to do weekly plots, but that would be silly to compare
                    # multiple runs on a week by week basis so probably we won't ever try that
                    else: 

                        # on first rate, open up the figures
                        if irate==0:

                            figure_fn_all = []
                            fig_all = []
                            ax_all = []
                            for itime in range(ntime):

                                # make figure name
                                figure_fn = '%s_%s_Rate_Map%s_%s_%s_Time%04d.png' % (run_list_str, wy_list_str, norm_name, time_period, multiple_rates_figure_label, itime)
                           
                                # set up figure subwindows with room for a colorbar 
                                fig, ax = plt.subplots(nrows, ncols, figsize=figsize)

                                # add title -- if there is only one run or all runs are the same, put runid in the suptitle
                                if all_runs_same:
                                    fig.suptitle(multiple_rates_figure_title + ': ' + runid,y=suptitle_y)
                                else:
                                    fig.suptitle(multiple_rates_figure_title, y=suptitle_y)
                                
                                # save the handles and figure names in lists
                                figure_fn_all.append(figure_fn)
                                fig_all.append(fig)
                                ax_all.append(ax)

                        # for each rate, leaf through the figures adding subplots
                        for itime in range(ntime):

                            # make figure name
                            fig = fig_all[itime]
                            ax = ax_all[itime][irate]

                            # loop through the runs and plot
                            for irun in range(nruns):
                        
                                add_subplot(irun, itime, irun)

                            add_colorbar()            
        
                        # on the last rate, finish up the figures
                        if irate == (nrates-1):

                            for itime in range(ntime):
                                figure_fn = figure_fn_all[itime]
                                fig = fig_all[itime]

                                finish_up_figure()

                            plt.close('all')

        
        
        