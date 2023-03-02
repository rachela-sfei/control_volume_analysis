# -*- coding: utf-8 -*-
"""
Created on Mon Feb  1 11:48:47 2021

This script is designed to make 2x3 grid plots for the RMP report
I am trying to set this up to be relatively flexible depdning on the normalization scheme
you want to use + the parameter you want to plot.



@author: siennaw
"""


import os, sys
import matplotlib
import matplotlib.pyplot as plt
if not 'DISPLAY' in os.environ:
    matplotlib.use('agg')
    plt.switch_backend('Agg')
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon
import pandas as pd
import cmocean
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from importlib import reload
sys.path.append('../')# plotting library must be one directory up
import control_volume_plotting_library as CVPL 
reload(CVPL)

# I moved a lot of extra pieces of this script (defs/functions) to an auxiliary file
from make2x3plots_def import * 

# here is where we store the list of all the runs (paramter + runIDs)
from sensitivity_run_definitions import param2run, server_dict 


###################
## USER INPUT
###################

# option to autoscale the map color limits to a certain percetile of the range ...
# same scale will be used for all time periods for a given senisitivty run and parameter
# if autoscale_casis = False, color axis will be read from the make2x3plots_def.py file
autoscale_caxis = True
percentile_cutoff = 95   # this will automatically set the range for the colorbar cutoff
max_percentage_change = 75   # this sets a SINGLE SCALE for the percentage change plots

# base directory for the output figures (in theory should be able to run on windows laptop with mounted drives or on server)
figure_base_dir = '/chicagovol1/hpcshared/open_bay/bgc/figures'


# PARAM_SENS gives keys to dictionary defined in sensitivity_run_definitions.py
for PARAM_SENS in ['Zero growth rates', 'Light Extinction Coefficient','Include Clams','Phytoplankton Growth Rate','Sediment Initial Conc C/N/P/Si',  
                   'Zoop Ingestion Rate', 'Diagenesis Rates for Fresh Sediment', 
                   'Diagenesis Rates for Legacy Sediment']: 
                   
        
        
    
    runs2plot = param2run[PARAM_SENS]
    
    
    
    
    # ///////////////////////////////////// 
    base_run = 'Base (#246)'
    
    # zoop_grazing, Denit, Net PP , oxygen_consumption 'Net PP', 'zoop_grazing', 
    params2plot = ['nitrogen_assimilation', 'oxygen_consumption', 'Denit', 'zoop_grazing', 'Net PP']
    
    # What normalization scheme you want to use for the data ('Area', 'Volume')
    NORM = 'Area'
    
    denit_label = 'Nitrogen loss through denitrification, g/m$^3$/day'
    
    # Cmocean colormap! 
    cmap = cmocean.cm.deep
    cmap_diff = cmocean.cm.balance
        
    
    # --------------------------------------------------------------------------
    # Split apart the run labels + runIDs 
    run_labels  = list(runs2plot.keys())
    runid_list   = [runs2plot[key] for key in run_labels]
    nruns       = len(runid_list)
    low_run = [run_name for run_name in runs2plot.keys() if '-' in run_name or 'Channel growth' in run_name or 'Include Clams' in run_name]
    high_run = [run_name for run_name in runs2plot.keys() if '+' in run_name or 'Shoal growth' in run_name]

    # now that we have runid_list, build server_list
    server_list = []
    for runid in runid_list:
        server_list.append(server_dict[runid])
    
    print('Making plots for %s \n' % runid_list)

    # get string with concise list of runs 
    run_list_str = CVPL.make_concise_runid_list_string(runid_list)

    # path to figures, create if it does not exist
    figure_path = os.path.join(figure_base_dir, run_list_str, 'sensitivity')
    if not os.path.exists(figure_path):
        os.makedirs(figure_path)
    print('\nfigures will be saved here: %s\n' % figure_path)
    

    # --------------------------------------------------------------------------
    # Define all the parameters + units / etc with dictionaries 
    param = 'Net PP'
    
    # green is automatically included, or not, as appropriate by updated balance table scripts
    #incl_green = True # set to True for 6 year agg grid runs based off Run 125 and related
    


    param2name = {'Net PP' : 'Net PP',
                  'Denit' : 'Denitrification',
                  'zoop_grazing' : 'Algae consumption by zoop',
                  'oxygen_consumption' : 'Oxygen Consumption',
                  'nitrogen_assimilation' : 'Nitrogen Assimilation'}

    # hard code colorbar limits here, if autoscale_caxis is false
    if not autoscale_caxis:
        param2max = { 'Net PP' :  0.6,
                      'Denit' : 0.05,
                      'zoop_grazing' : 0.1,
                      'oxygen_consumption' : 1,
                      'nitrogen_assimilation' : 0.05} 
        
        param2percentagerange = {'Net PP' :  2,
                      'Denit' : 0.2,
                      'zoop_grazing' : 1.5,
                      'oxygen_consumption' : 1.1,
                      'nitrogen_assimilation' : 0.5} 
    
    units = {} 
    units.update(dict.fromkeys(['zoop_grazing', 'Net PP'], 'gC'))
    units.update(dict.fromkeys(['Denit', 'nitrogen_assimilation']  , 'gN'))
    units['oxygen_consumption'] = 'gO$_2$'
    
    def param2unit(param, NORM):
        if NORM == 'Area' :
            per = 'm$^2$'
        elif NORM == 'Volume':
            per = 'm$^3$'
        else:
            assert(False)
        unit = '%s/%s/day' % (units[param], per)
        return unit 
    


    # --------------------------------------------------------------------------                       
    ########################################
    # /// Read in different rates + runs /// 
    ######################################## 
    DATA = {}            
    for n, runid in enumerate(runid_list): 

       
        print('Reading in %s ... \n [%d/%d]' % (runid, n, len(runid_list)))
        
        # get path to the balance table folder in the run folder
        run_base_dir = '/%svol1/hpcshared' % server_list[n]
        run_dir = CVPL.get_run_dir(run_base_dir, runid)
        balance_table_dir = os.path.join(run_dir,'Balance_Tables')
            
        
        # Primary production / production rate
        filename = os.path.join(balance_table_dir, 'algae_Table.csv')
        primary_table = pd.read_csv(filename)
        
        # Get normalization factor 
        norm = normalize_data(primary_table, NORM)
    
        ## PM addition -- need to add "Greens" for Agg Grid 125 and later
        #if incl_green:
        #    filename = os.path.join(balance_table_dir, 'green_Table.csv')
        #    primary_table_g = pd.read_csv(filename)
            
        # Denitrification 
        filename = os.path.join(balance_table_dir,   'no3_Table.csv')
        no3_table = pd.read_csv(filename)
    
         # Ammonium 
        filename = os.path.join(balance_table_dir,   'nh4_Table.csv')
        nh4_table = pd.read_csv(filename)
        
        # Oxygen Consumption 
        filename = os.path.join(balance_table_dir,   'oxy_Table.csv')
        oxy_table = pd.read_csv(filename)

        
        # Nitrogen Assimilation 
        #no3_table['na_1'] = no3_table[["NO3,dDenitWat","NO3,dNitrif","NO3,dDenitSed","NO3,dNiDen", "NO3,dNO3Upt"]].sum(axis=1)
        #nh4_table['na_2'] = nh4_table[["NH4,dMinPON1","NH4,dMinDON","NH4,dNitrif","NH4,dMinDetNS1",
        #                                   "NH4,dMinDetNS2","NH4,dZ_NRes","NH4,dNH4Aut","NH4,dNH4Upt"]].sum(axis=1)
        no3_table['na_1'] = no3_table[['NO3,dDenitWat', 'NO3,dNitrif','NO3,dDenitSed', 'NO3,dNiDen', 'NO3,dNO3UptS1', 'NO3,dNO3Upt']].sum(axis=1)
        nh4_table['na_2'] = nh4_table[['NH4,dMinPON1', 'NH4,dMinPON2','NH4,dMinDON', 'NH4,dNitrif', 'NH4,dMinDetNS1', 
                                       'NH4,dMinDetNS2', 'NH4,dMinOONS1', 'NH4,dMinOONS2', 'NH4,dZ_NRes', 'NH4,dNH4UptS1',
                                       'NH4,dNH4US1D', 'NH4,dNH4Aut', 'NH4,dNH4AUTS1', 'NH4,dNH4Upt']].sum(axis=1)
        
        # Normalize data 
        no3_table['Denit']                  = abs(no3_table['NO3,dDenitWat'] + no3_table['NO3,dDenitSed']) / norm
        #primary_table['Net PP']                = primary_table['Diat,dPPDiat'] / norm
        #primary_table['Net PP'] = primary_table[['Diat,dPPDiat','Green,dPPGreen','DiatS1,dPPDiatS1']].sum(axis=1)/norm
        primary_table['Net PP'] = primary_table[['Diat,dPPDiat','Green,dPPGreen']].sum(axis=1)/norm
        #primary_table['zoop_grazing']       = abs(primary_table['Diat,dZ_Diat']) / norm  # Grazing of diatoms by zoop
        primary_table['zoop_grazing']       = abs(primary_table[['Diat,dZ_Diat', 'Green,dZ_Grn']].sum(axis=1)) / norm

        #if incl_green:
        #    primary_table['Net PP']                = primary_table['Net PP'] + (primary_table_g['Green,dPPGreen'] / norm )
        #    primary_table['zoop_grazing']       = primary_table['zoop_grazing'] + abs(primary_table_g['Green,dZ_Grn']) / norm  # Grazing of greens by zoop
        
        #oxy_table['oxygen_consumption']     = abs(oxy_table['OXY,dOxCon'] + oxy_table['OXY,dMinDetCS1']) / norm 
        oxy_table['oxygen_consumption']     = abs(oxy_table[['OXY,dOxCon','OXY,dMinDetCS1', 'OXY,dMinDetCS2', 'OXY,dMinOOCS1', 'OXY,dMinOOCS2']].sum(axis=1)) / norm 
        no3_table['nitrogen_assimilation']  = abs(no3_table['na_1'] + nh4_table['na_2']) / norm
        
        # Save norm for weighting data 
        no3_table['norm']     = norm
        primary_table['norm']   = norm
        oxy_table['norm']       = norm
        
        # Save data for each run in dictionary
        DATA[runid + 'Denit']    = no3_table
        DATA[runid + 'Net PP']      = primary_table
        DATA[runid + 'time']     = pd.to_datetime(no3_table.time.values) 
        DATA[runid + 'zoop_grazing'] = primary_table
        DATA[runid + 'oxygen_consumption'] = oxy_table
        DATA[runid + 'nitrogen_assimilation'] = no3_table


    # --------------------------------------------------------------------------                       
    
    ###########################################
    # /// Seasons / times we want to average /// 
    ###########################################                              
    water_years = ['WY2018', 'WY2017' , 'WY2015', 'WY2016', 'WY2013' , 'WY2014'] 
    
    time_windows = {'Winter (WY2015)'         : ['2014-10-01','2015-02-01'],
                    'Growing Season (WY2015)' : ['2015-02-01','2015-10-01'],
                    'Winter (WY2013)'         : ['2012-10-01','2013-02-01'],
                    'Growing Season (WY2013)' : ['2013-02-01','2013-10-01'],
                    'Winter (WY2014)'         : ['2013-10-01','2014-02-01'],
                    'Growing Season (WY2014)' : ['2014-02-01','2014-10-01'],
                    'Winter (WY2016)'         : ['2015-10-01','2016-02-01'],
                    'Growing Season (WY2016)' : ['2016-02-01','2016-10-01'],
                    'Winter (WY2017)'         : ['2016-10-01','2017-02-01'],
                    'Growing Season (WY2017)' : ['2017-02-01','2017-10-01'],
                    'Winter (WY2018)'         : ['2017-10-01','2018-02-01'],
                    'Growing Season (WY2018)' : ['2018-02-01','2018-10-01']}
    
    time_window_labels = list(time_windows.keys())
    time_windows_dates = [time_windows[key] for key in time_window_labels]
    nwindows = len(time_windows)
    
    # --------------------------------------------------------------------------                       
    ###########################################
    # /// Average over the time windows /// 
    ########################################### 
    
    for param in params2plot:
    
        print('\n\nPLOTTING PARAMETER: %s' % param.capitalize())
        unit = param2unit(param, NORM)
        
        for label in time_window_labels:
            print('Averaging over %s ... \n' % label)
            
            for n, runid in enumerate(runid_list):
                # print('Run == %s' % runid)
                
                data = DATA[runid + param]
                time = DATA[runid + 'time']
                
                time_window = time_windows[label]
                time_start = np.datetime64(time_window[0])
                time_end = np.datetime64(time_window[1])
                indt = np.logical_and(time>=time_start,time<time_end)
                
                
                Time = list(set(time[indt])) 
                areas_df = pd.DataFrame(index = Time, columns=(AREAS_names))
                for i,t in enumerate(Time):
                    data0 = data.loc[time == t]
                    for area in AREAS_names:
                        polygon_inds = find_inds(data0, area)
                        data1 = data0.loc[polygon_inds]
                        weighted_av = sum(data1[param] * data1['norm']) / sum(data1['norm'])
                        areas_df.loc[t, area] = weighted_av
                        
                data_sel = data.loc[indt]
                data_sel = data_sel.groupby(['Control Volume']).mean()
                DATA[label + runid + param] = data_sel
                DATA[label + runid + param + 'area_weighted_average'] = areas_df.mean(axis=0)
                
                # print(areas_df.mean(axis=0))
                # assert(False)
                print('Saved %s time frame for %s -- %s' % (label, runid, param))
        
        
    # --------------------------------------------------------------------------                       
        #################################
        # /// Functions for plotting  /// 
        ################################# 
        # (1) clean axis & plot the aggregated groups on top... 
        def clean_axis(axis, date):
            axis.xaxis.set_visible(0)
            axis.yaxis.set_visible(0)
            axis.axis('equal')
            axis.set_title(date, fontsize = 15)
            axis.set_frame_on(False)
            # agg.boundary.plot(ax = axis, color = 'slategray')
        
        # (2) make a color bar w/ defined vmax and label ... 
        def make_colorbar(MAX, cmap_str, axis, label):
            norm = matplotlib.colors.Normalize(0, MAX)
            cmapp = matplotlib.cm.ScalarMappable(norm= norm, cmap= cmap_str)
            cmapp.set_array([])   # we need this line with our old HPC Python... 
            cb = plt.colorbar(cmapp, ax = axis, shrink = 0.7, orientation = 'vertical', pad = 0.02)
            cb.ax.tick_params(labelsize = 14)
            cb.set_label(label, fontsize = 14)
        
        # (4) index into a dataframe to normalize some mass value by volume & define the max value @ timestamp
        def load_substance(table, date, SUB):
            values = table.loc[table.time == date,['Control Volume', SUB, 'Volume']]
            values[SUB] = values[SUB].values / values['Volume'].values  # normalize by volume 
            MAX = np.max(values[SUB].values)
            return values, MAX 
        
        # (5) index into a dataframe to extract a value of (1) polygon
        def val_at_poly(values, poly_num, SUB):
            return values.loc[values.index == 'polygon%d' % poly_num, SUB].values
              
        
        def make_percentage_colorbar(cmap_str, axis, label, percentage_range):
            norm = matplotlib.colors.Normalize(-percentage_range, percentage_range)
            cmapp = matplotlib.cm.ScalarMappable(norm= norm, cmap= cmap_str)
            cmapp.set_array([])   # we need this line with our old HPC Python... 
            cb = plt.colorbar(cmapp, ax = axis, shrink = 0.7, orientation = 'vertical', pad = 0.02)
            cb.ax.tick_params(labelsize = 14)
            cb.set_label(label, fontsize = 14)
        
        #%%
        
        '''
        The weird set-up here is designed to speed up our loops. Originally we plotted w/ geopandas
        but that took a lifetime. Now we take advantage of the relative speedier matplotlib polygon
        library. In order to do this, we intialize our polygons on a figure, and then assign values
        for the colors in a loop. This way we don't have to draw everything over and over again. 
        '''
        NPolys  = 141
        
        # Make a list of all the polygons we want to plot 136
        skip    = [i for i in range(118, 136)] # these are in the ocean so we are skipping them 118, 136
        polys2plot = [i for i in range(NPolys) if i not in  skip] 
        polys2plot.append(134)
            
        # Triple loop! OUTER LOOP : Water Year (1 per page / figure)
        for water_year in water_years:
                       
            
            # Second loop : Winter vs Growing Season
            for i, time_window_label in enumerate(['Winter (%s)' % water_year, 'Growing Season (%s)' % water_year]): 
                
                # find auto scale for color axis
                max_val = 0
                for n, runid in enumerate(runid_list):    
                    df = DATA[time_window_label + runid + param]
                    array = [(val_at_poly(df, i, param)) for i in polys2plot] 
                    max_val = np.max([max_val, np.nanpercentile(array, percentile_cutoff)])

                # Bottom right == Diff w/ base
                base = DATA[time_window_label + runs2plot[base_run] + param]
                base_array = [(val_at_poly(base, i, param)) for i in polys2plot]
                base_array = np.ravel(np.array(base_array))
                
                # LOW END DIFFERENCE 
                diff1 = DATA[time_window_label + runs2plot[low_run[0]] + param]
                diff1_array = [(val_at_poly(diff1, i, param)) for i in polys2plot]
                diff1_array = np.ravel(np.array(diff1_array))
                diff1_array = 100 * (diff1_array-base_array) / base_array 

                # HIGH END DIFFERENCE PLOT ! 
                if len(high_run) > 0:
                    diff2 = DATA[time_window_label + runs2plot[high_run[0]] + param]
                    diff2_array = [(val_at_poly(diff2, i, param)) for i in polys2plot]
                    diff2_array = np.ravel(np.array(diff2_array))
                    diff2_array = 100 * (diff2_array - base_array) / base_array 

                # find color map range based on percentile cutoff
                max_diff = 0
                max_diff = np.max([max_diff, np.percentile(diff1_array, percentile_cutoff)])
                max_diff = np.max([max_diff, -np.percentile(diff1_array, 100-percentile_cutoff)])
                if len(high_run) > 0:
                    max_diff = np.max([max_diff, np.percentile(diff2_array, percentile_cutoff)])   
                    max_diff = np.max([max_diff, -np.percentile(diff2_array, 100-percentile_cutoff)])  


                # set up the figure
                if len(high_run)>0: 
                    fig, axs = plt.subplots(nrows = 2, ncols = 3, sharex = False, sharey = False, figsize=(20,10))
                else:
                    fig, axs = plt.subplots(nrows = 2, ncols = 2, sharex = False, sharey = False, figsize=(14,10))
                

                # Create polygon geometries 
                patches =  [polys.geometry[i]  for i in polys2plot]  
                
                # Another weird loop. Here we go through and convert all our polygons to objects matplotlib types
                Patches = [Polygon(np.asarray(poly.exterior)) for poly in patches] 
                        
                # Create patch collection   
                PATCHES = [PatchCollection(Patches, facecolor='white', edgecolor='face') for i in range(10)]


                # Add patches to plot
                patches_ = [] 
                
                # Format the axes, add + format the patches 
                axs = axs.ravel() 
                for i, ax in enumerate(axs):
                    
                    # Don't set up last axis .. this is the bar chart
                    if i==len(axs)-1:
                        break

                    
                    patch_ = ax.add_collection(PATCHES[i])
                    if (i<3 and len(high_run)>0) or (i<2 and len(high_run)==0):
                            if autoscale_caxis:
                                patch_.set_clim(0, max_val)
                            else:
                                patch_.set_clim(0, param2max[param])
                            patch_.set_cmap(cmap)
                    else:

                        #### hard code the range for the percent change plots, so we can compare across sensitivity tests
                        percentage_range = max_percentage_change

                        # alternatively could use autoscaling and/or paramter specific hard coding
                        # with or without a cap
                        #if autoscale_caxis:
                        #    percentage_range = max_diff
                        #else:
                        #    percentage_range = param2percentagerange[param]*100
                        #percentage_range = np.min([percentage_range, max_percentage_change])

                        patch_.set_clim(-percentage_range, percentage_range)
                        patch_.set_cmap(cmap_diff)
                    patches_.append(patch_)
                    if (i==2 and len(high_run)>0) or (i==1 and len(high_run)==0):
                        if autoscale_caxis:
                            make_colorbar(max_val,  cmap,   ax,  unit)
                        else:
                            make_colorbar(param2max[param],  cmap,   ax,  unit)
                    if (i==4 and len(high_run)>0) or (i==2 and len(high_run)==0): 
                        make_percentage_colorbar(cmap_diff,   ax,  '', percentage_range)
                    ax.autoscale_view()    
                
                print('\n ... Plotting : %s \n' % time_window_label)
                k = 0  
                # Top Row == Run Maps 
                for n, runid in enumerate(runid_list):    
                    
                    # pull out dataframe from dictionary (it's already averaged!)
                    df = DATA[time_window_label + runid + param]
                    # extract value for each polygon 
                    
                    array = [(val_at_poly(df, i, param)) for i in polys2plot] 
                    
                    # convert it to 1D array and assign to polycollection 
                    array = np.ravel(np.array(array))
                    if autoscale_caxis:
                        array = array.clip(0, max_val)
                    else:
                        array = array.clip(0, param2max[param])
                    patches_[k].set_array(array)
                    
                    # clean the axes and add a title 
                    clean_axis(axs[k], '%s' % run_labels[n])
                    
                    k += 1  # a counter // we use this for the axis count 
                
                
                patches_[k].set_array(diff1_array)
                   
                # clean the axes and add a title 
                clean_axis(axs[k], '%s \n%% diff relative to base' % low_run[0])
                k +=1
                
                if len(high_run) > 0:
                    patches_[k].set_array(diff2_array)
                    # clean the axes and add a title 
                    clean_axis(axs[k], '%s \n%% diff relative to base' % high_run[0] )
                    k +=1
        
     

                
                '''
                    LAST AXIS: BAR CHART !! 
                '''
                index = np.arange(0, len(AREAS_names))
                bar_width = 0.2
                opacity = 0.8
                bar_colors = ['skyblue', 'orchid', 'brown']
                index_shift = [-bar_width, 0, bar_width]
                axs[k].clear() 
                
                # Loop through each run 
                for i, runid in enumerate(runid_list):
                    bar_data = DATA[time_window_label + runid + param + 'area_weighted_average']
                    
                    print(time_window_label + runid + param + 'area_weighted_average')
                    print(bar_data.values)
                    rects1 = axs[k].bar(index + index_shift[i], bar_data.values, bar_width,
                        alpha=opacity,
                        color=bar_colors[i],
                        label= run_labels[i])
                    
                
        
                axs[k].set_xlabel('Subembayment')
                axs[k].set_ylabel(unit)
                plt.title('Average by Subembayment')
                plt.xticks(index, [N.replace('_', ' ') for N in AREAS_names]) 
                axs[k].legend()
                axs[k].grid(b=True, alpha = 0.15)
        
        
                fig.canvas.draw()
                fig.suptitle('Sensitivity to %s \n %s during %s' % (PARAM_SENS, param2name[param],  time_window_label), fontsize = 20)
            
                savename = '%s/%s_%s_%s_Sensitivity_to_%s.png' % (figure_path, water_year, time_window_label.replace('(%s)' % water_year, ''), param.capitalize(), PARAM_SENS.replace('/',' ')) 
                fig.savefig(savename)
                plt.close('all')
                
                print(savename)
        
        
        print('DONE!!!!!!!!!!!!!!!!!!!')
   
    
    
