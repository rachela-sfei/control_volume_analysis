########################################################################################
## import python packages
########################################################################################

import sys, os
import pandas as pd
import numpy as np
import matplotlib.pylab as plt
import datetime as dt
import matplotlib.dates as mdates
plt.switch_backend("Agg")


#########################################################################################
## user input
#########################################################################################
# path to folder that contains run folders, which in turn contain model output including dwaq_hist.nc 
# and *-bal.his files. if there are no run subfolders, this is the direct path to dwaq_hist.nc and *-bal.his
# path = '../'

base_path = r'/richmondvol1/hpcshared/Grid141/WY13to18//'


# Dict : run label followed by RunID 
runs2plot = {'Base (#125)'              : 'G141_13to18_125'} 



base_run = 'Base (#125)'


# Split apart the run labels + runIDs 
run_labels = list(runs2plot.keys())
run_names = [runs2plot[key] for key in run_labels]


print('Making plots for %s \n' % run_names)


## pick a composite parameter to plot
param = 'DIN'

## note from and to polygons defining the location of the boundary between bay and ocean at Golden Gate bridge (based on this map:
## 1_Nutrient_Share\1_Projects_NUTRIENTS\Modeling\NOTES_AK\DWAQ\Control_Volume_Shapefiles\Open_Bay\Agg_mod_contiguous.png)
# if 1:   ## includes GG polygon as part of bay (94 flows into 118, 121, and 119
#     from_polys = [94]
#     to_polys = [[118,121,119]]
# else:   ## includes GG polygon as part of ocean (95 flows into 94, and 96 flows into 94 as well)
#     from_polys = [95,96]
#     to_polys = [[94],[94]]

# AGG EQUIVALENT 
if 1:   ## includes GG polygon as part of bay (94 flows into 118, 121, and 119
    from_polys = [94]
    to_polys = [[116]]
else:   ## includes GG polygon as part of ocean (95 flows into 94, and 96 flows into 94 as well)
    from_polys = [95,96]
    to_polys = [[94],[94]]



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

cum_times = np.array(['2013-03-01','2013-09-01']).astype('datetime64')

## directory containting balance tables, including path
base_dir = './balance_tables'



# Make output directory 
output_dir = r'/richmondvol1/hpcshared/Grid141/WY13to18//%s/CONTROL_VOLUME_PLOTS//' % runs2plot[base_run]

if not os.path.exists(output_dir):
    os.makedirs(output_dir)
    print('Made %s' % output_dir)

## file name for output figure, including path
outfig_fn = '%s/FLUX_OUT_GG_6PanelPlot_BASE.png'  % (output_dir)
      
    
## list of line colors, corresponding to test cases
# colors = ['black','red','blue','magenta','darkturquoise','darkorange','limegreen']

## define parameters as sum of their components, multiplied by multipliers
composite_parameters = {
'continuity' : [[1,'continuity']],
'NH4' : [[1.00, 'NH4']],
'NO3' : [[1.00, 'NO3']],
'TN'  : [[1,'NH4'], [1,'NO3'], [1,'DON'], [1,'PON1'], [0.15,'Diat'], [0.1818,'Zoopl_V'], [0.1818,'Zoopl_R'], [0.1818,'Zoopl_E']],
'DIN' : [[1.00, 'NH4'], [1.00, 'NO3']],
'PON' : [[1.00, 'PON1']],
'N-Diat' : [[0.15, 'Diat']],
'N-Zoopl' : [[0.1818,'Zoopl_V'], [0.1818,'Zoopl_R'], [0.1818,'Zoopl_E']],
'DetN' : [[1.00,'DetNS1']],
'Zoopl' : [[1.0,'Zoopl_V'], [1.0,'Zoopl_R'], [1.0,'Zoopl_E']],
'TP' : [[1,'PO4'], [1,'DOP'], [1,'POP1'], [0.01,'Diat'], [0.0263,'Zoopl_V'], [0.0263,'Zoopl_R'], [0.0263,'Zoopl_E']],
'DO' : [[1,'OXY']] 
}
    
    
###########################################################################################
## MAIN
###########################################################################################

## initialize a figure, to put up plots for all the different runs
fig, ax = plt.subplots(6,1,figsize=(7,11), sharey= True)

colors = ['skyblue', 'orchid', 'brown']
 
 
## loop through the run folders
nruns = len(run_names)

for itime, (t0, t1)  in enumerate(growing_seasons):
    print('On %d/%d' % (itime, len(growing_seasons)))
    for irun, run_label in enumerate(run_labels):
    
        run_folder = runs2plot[run_label]
    
        time_window = np.array([t0, t1]).astype('datetime64')
        ## loop through components of composite parameter
        ncp = len(composite_parameters[param])
        for icp in range(ncp):
        
            ## get multiplier and name of parameter for first component parameter
            mult_i, param_i = composite_parameters[param][icp]
    
            ## name of balance table for component parameter
            balance_table_i = '%s_Table.csv' % param_i.lower()
            
            ## load the balance table
            filename = os.path.join(base_path, run_folder , 'balance_tables',   balance_table_i)
            print('Reading %s ... \n' % filename)
            df_1 = pd.read_csv(filename)
        
            ## loop through the from polygons
            nfp = len(from_polys)
            for ifp in range(nfp):
            
                ## from polygon number
                from_poly = from_polys[ifp]
            
                ## select from polygon data
                df = df_1.loc[df_1['Control Volume'] == 'polygon%d' % from_poly]
            
                ## loop through the to polys and identify their numbering in the balance table
                to_polys_1 = []
                for to_poly in to_polys[ifp]:
                    isin = False
                    for p in range(0,5):
                        # print(df)
                        to_poly_test = df['To_poly%d' % p].iloc[0]
                        if not np.isnan(to_poly_test):
                            if int(to_poly_test) == to_poly:
                                isin = True
                                to_polys_1.append(p)
                    if not isin:
                        print('warning: polygon %d is not connected to polygon %d' % (from_poly, to_poly))
                        
                ## now that we know the indices of the to polygons, let's add them up
                ntp = len(to_polys_1)
                for itp in range(ntp):
                    if ((itp == 0) and (ifp == 0)):
                        flux_i = - df['Flux%d' % to_polys_1[itp]].values
                    else:
                        flux_i = flux_i - df['Flux%d' % to_polys_1[itp]].values
    
                ## now add the contribution of this component parameter to the total flux (e.g. add NO3 and NH4 to get DIN)
                if icp == 0:
                    flux = mult_i * flux_i.copy()
                else:
                    flux = flux.copy() + mult_i * flux_i.copy()
        
        ## get times from the final dataframe
        time = df['time'].values.astype('datetime64[ns]')
        ## compute time step in days (allowing that it might be minutes)
        deltat = (time[1] - time[0]).astype('timedelta64[h]').astype(int) / 24

        ## compute cumulative flux
        ind = np.logical_and(time>=time_window[0],time<=time_window[1])
        cumflux = np.cumsum(flux[ind]) * deltat
        
        # Plot 
        ax[itime].plot(time[ind], cumflux/1e9, label = run_label, color = colors[irun], linewidth = 3, alpha = 0.8)
                
    ## finish up the plot
    ax[itime].xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    ax[itime].xaxis.set_major_formatter(mdates.DateFormatter('%b/%Y'))
    ax[itime].grid(b=True, alpha = 0.5)
    ax[itime].set_xlim((time_window[0],time_window[-1]))
    if itime==0:
        ax[itime].legend(loc='upper left')
    ax[itime].set_ylabel('Flux (10$^9$ g)')# % param)
    
    
fig.suptitle('%s Cumulative Flux Out of Golden Gate' % (param))
fig.savefig(outfig_fn)
print(outfig_fn)
plt.close('all')
            
      