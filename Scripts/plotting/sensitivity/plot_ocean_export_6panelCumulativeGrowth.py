########################################################################################
## import python packages
########################################################################################

import sys, os
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
if not 'DISPLAY' in os.environ:
    matplotlib.use('agg')
    plt.switch_backend('Agg')
import datetime as dt
import matplotlib.dates as mdates
from importlib import reload
sys.path.append('../')# plotting library must be one directory up
import control_volume_plotting_library as CVPL 
reload(CVPL)

# here is where we store the list of all the runs (paramter + runIDs)
from sensitivity_run_definitions import param2run, server_dict 

#########################################################################################
## user input
#########################################################################################
# path to folder that contains run folders, which in turn contain model output including dwaq_hist.nc 
# and *-bal.his files. if there are no run subfolders, this is the direct path to dwaq_hist.nc and *-bal.his
# path = '../'

# base directory for the output figures (in theory should be able to run on windows laptop with mounted drives or on server)
figure_base_dir = '/chicagovol1/hpcshared/open_bay/bgc/figures'


# PARAM_SENS gives keys to dictionary defined in sensitivity_run_definitions.py
for PARAM_SENS in ['Phytoplankton Growth Rate','Sediment Initial Conc C/N/P/Si', 'Light Extinction Coefficient', 
                   'Zero growth rates', 'Zoop Ingestion Rate', 'Include Clams', 'Diagenesis Rates for Fresh Sediment', 
                   'Diagenesis Rates for Legacy Sediment']: 

    runs2plot = param2run[PARAM_SENS]
    
    
    
    # PARAM_SENS = 'Clams'
    
    # # Dict : run label followed by RunID 
    # runs2plot = {'Base (#125)'        : 'G141_13to18_125',
    #              'With Clams'         : 'G141_13to18_132'} 
    
    base_run = 'Base (#246)'
    
    
    # Split apart the run labels + runIDs 
    run_labels  = list(runs2plot.keys())
    runid_list   = [runs2plot[key] for key in run_labels]
    nruns = len(runid_list)

    # now that we have runid_list, build server_list
    server_list = []
    for runid in runid_list:
        server_list.append(server_dict[runid])
    
    print('Making plots for %s \n' % runid_list)
    


    run_list_str = CVPL.make_concise_runid_list_string(runid_list)
    
    # path to figures, create if it does not exist
    figure_path = os.path.join(figure_base_dir, run_list_str, 'sensitivity')
    if not os.path.exists(figure_path):
        os.makedirs(figure_path)
    print('\nfigures will be saved here: %s\n' % figure_path)    
    
    ## pick a composite parameter to plot
    for param in ['DIN','TN']:
    
        ## note from and to polygons defining the location of the boundary between bay and ocean at Golden Gate bridge (based on this map:
        ## 1_Nutrient_Share\1_Projects_NUTRIENTS\Modeling\NOTES_AK\DWAQ\Control_Volume_Shapefiles\Open_Bay\Agg_mod_contiguous.png)
        # if 1:   ## includes GG polygon as part of bay (94 flows into 118, 121, and 119
        #     from_polys = [94]
        #     to_polys = [[118,121,119]]
        # else:   ## includes GG polygon as part of ocean (95 flows into 94, and 96 flows into 94 as well)
        #     from_polys = [95,96]
        #     to_polys = [[94],[94]]
        
        ## AGG EQUIVALENT 
        #if 1:   ## includes GG polygon as part of bay (94 flows into 118, 121, and 119
        #    from_polys = [94]
        #    to_polys = [[116]]
        #else:   ## includes GG polygon as part of ocean (95 flows into 94, and 96 flows into 94 as well)
        #    from_polys = [95,96]
        #    to_polys = [[94],[94]]
        #
        
        
        # Make it a 6 panel with each panel showing the cumulative flux out for the 
        # growing season (Mar – Sep) by water year (currently you have the instantaneous
         # for all years and cumulative for 2013 only with the latter showing Mar – May –
         # I have attached the light extinction sensitivity run as a reference for what we currently have).
        #%%
        
        ## pick the time window for cumulative plot
        growing_seasons = [('2013-03-01','2013-09-01'),
                           ('2014-03-01','2014-09-01'),
                           ('2015-03-01','2015-09-01'),
                           ('2016-03-01','2016-09-01'),
                           ('2017-03-01','2017-09-01'),
                           ('2018-03-01','2018-09-01')]
        # growing_seasons = [pd.to_datetime(growing_season) for growing_season in growing_seasons]
        #%% 
    

        
        
        
        ## Make output directory 
        #output_dir = r'/richmondvol1/hpcshared/Grid141/WY13to18//%s/CONTROL_VOLUME_PLOTS//' % runs2plot[base_run]
        #output_dir = '/%s/%s//' % (output_dir, PARAM_SENS)
        #if not os.path.exists(output_dir):
        #    os.makedirs(output_dir)
        #    print('Made %s' % output_dir)
        
        ## file name for output figure, including path
        outfig_fn = os.path.join(figure_path,'%s_CUMFLUX_OUT_GG_6PanelPlot_Sens2%s.png'  % (param, PARAM_SENS.replace('/',' ')))
              
            
        ## list of line colors, corresponding to test cases
        # colors = ['black','red','blue','magenta','darkturquoise','darkorange','limegreen']
        
            
            
        #########################################################################################
        ## MAIN
        ###########################################################################################
        
        ## initialize a figure, to put up plots for all the different runs
        fig, ax = plt.subplots(3,2,figsize=(10,9.5), sharex= False, sharey = True)
        ax=ax.flatten()
        
        colors = ['skyblue', 'orchid', 'brown']
         
         
        ## loop through the run folders
        nruns = len(runid_list)
        
        for itime, (t0, t1)  in enumerate(growing_seasons):
            print('On %d/%d' % (itime, len(growing_seasons)))
            for irun, run_label in enumerate(run_labels):


                # get path to the balance table folder in the run folder
                run_base_dir = '/%svol1/hpcshared' % server_list[irun]
                runid = runid_list[irun]
                run_dir = CVPL.get_run_dir(run_base_dir, runid)
                balance_table_dir = os.path.join(run_dir,'Balance_Tables')
            
                # load the grouped balance table and extract the whole bay
                df = pd.read_csv(os.path.join(balance_table_dir, '%s_Table_By_Group.csv' % param.lower()))
                df = df.loc[df['group'] == 'Whole_Bay']
                flux = -df['%s,Flux In from W (Mg/d)' % param].values
                netrx = df['%s,Net Reaction (Mg/d)' % param].values
                time = df['time'].values.astype('datetime64[ns]')


                ## get times from the final dataframe
                time_window = np.array([t0, t1]).astype('datetime64')
                ## compute time step in days (allowing that it might be minutes)
                deltat = (time[1] - time[0]).astype('timedelta64[h]').astype(int) / 24
        
                ## compute cumulative flux
                ind = np.logical_and(time>=time_window[0],time<=time_window[1])
                cumflux = np.cumsum(flux[ind]) * deltat
                cumrx = np.cumsum(netrx[ind]) * deltat
                
                # Plot 
                ax[itime].plot(time[ind], cumflux /1000, label = run_label, color = colors[irun], linewidth = 3, alpha = 0.8)
                ax[itime].plot(time[ind], cumrx / 1000, '--', color = colors[irun], linewidth = 3, alpha = 0.8)
                #ax[itime].plot(time[ind], flux[ind]/1e6, label = run_label, color = colors[irun], linewidth = 3, alpha = 0.8)
               
        
                
            ## finish up the plot
            ax[itime].xaxis.set_major_locator(mdates.MonthLocator(interval=1))
            ax[itime].xaxis.set_major_formatter(mdates.DateFormatter('%b%y'))
            ax[itime].grid(b=True, alpha = 0.5)
            ax[itime].set_xlim((time_window[0],time_window[-1]))
            if itime==0:
                ax[itime].legend(loc='upper left')
            # ax[itime].set_ylabel('Flux (10$^9$ g)')# % param)
            ax[itime].set_ylabel('Flux (10$^9$ g)' )
            
        fig.suptitle('%s Cumulative Flux Out of Golden Gate\nSensitivity to %s\nSOLID = flux out GG, DASHED = Net Reaction Within Bay' % (param, PARAM_SENS))

        fig.savefig(outfig_fn)
        print(outfig_fn)

        plt.close('all')
                
            