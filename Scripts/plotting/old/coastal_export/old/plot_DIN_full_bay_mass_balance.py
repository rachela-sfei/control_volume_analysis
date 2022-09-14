'''

Allie wrote this script and I just modified it a tiny bit. Will try to comment it.

Goal is to plot export out the Golden Gate.

'''

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

water_year = 'WY2017'
run2plot = 'FR17_003'

## pick the time window for cumulative plot
t_window = np.array(['2016-10-01','2017-10-01']).astype('datetime64')

#########################################################################################

output_dir = '/richmondvol1/hpcshared/NMS_Projects/Control_Volume_Analysis/Balance_Tables/'


## note from and to polygons defining the location of the boundary between bay and ocean at Golden Gate bridge (based on this map:
## 1_Nutrient_Share\1_Projects_NUTRIENTS\Modeling\NOTES_AK\DWAQ\Control_Volume_Shapefiles\Open_Bay\Agg_mod_contiguous.png)

# Full resolution run numbers. Will need to be slightly different for agg grid. 
if 1:   ## includes GG polygon as part of bay (94 flows into 118, 121, and 119
    from_polys = [94]
    to_polys = [[118,121,119]] # <<FR [[116]]
    from_delta = [77]
    to_delta = [[75]]

else:   ## includes GG polygon as part of ocean (95 flows into 94, and 96 flows into 94 as well)
    from_polys = [95,96]
    to_polys = [[94],[94]]



## directory containting balance tables, including path
base_dir = '/richmondvol1/hpcshared/NMS_Projects/Control_Volume_Analysis/Balance_Tables/'

# Make output directory 
output_dir = '/richmondvol1/hpcshared/NMS_Projects/Control_Volume_Analysis/Plots/%s/' % water_year  

if not os.path.exists(output_dir):
    os.makedirs(output_dir)
    print('Made %s' % output_dir)

## file name for output figure, including path
outfig_fn = '%s/DIN_export_GGDelta_%s.png'  % (output_dir, run2plot)
      

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
    

''' Moving this functionality into a function (haha get it!) so it doesn't clog up our script ''' 
def calculate_flux(From_polys, To_polys, param):
    ## loop through components of composite parameter
    ncp = len(composite_parameters[param])
    for icp in range(ncp):
    
        ## get multiplier and name of parameter for first component parameter
        mult_i, param_i = composite_parameters[param][icp]

        ## name of balance table for component parameter
        balance_table_i = '%s_Table.csv' % param_i.lower()
        
        # ## load the balance table
        # if 'Agg' in run_label:
        #     filename = os.path.join( run_folder, balance_table_i)
        #     from_polys = [94]
        #     to_polys = [[116]]
        # else:
        #     from_polys = [94]
        #     to_polys = [[118,121,119]]

        filename = os.path.join(run_folder,  balance_table_i)
            
        print('Reading %s ... \n' % filename)
        df_1 = pd.read_csv(filename)
    
    
   ## loop through the from polygons
        nfp = len(From_polys)
        for ifp in range(nfp):
        
            ## from polygon number
            from_poly = From_polys[ifp]
        
            ## select from polygon data
            df = df_1.loc[df_1['Control Volume'] == 'polygon%d' % from_poly]
        
            ## loop through the to polys and identify their numbering in the balance table
            to_polys_1 = []
            for to_poly in To_polys[ifp]:
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
            # print('ntp = %d' % ntp)
            for itp in range(ntp):
                if ((itp == 0) and (ifp == 0)):
                    flux_i = - df['Flux%d' % to_polys_1[itp]].values
                else:
                    flux_i = flux_i - df['Flux%d' % to_polys_1[itp]].values
    
            ## now add the contribution of this component parameter to the total flux (e.g. add NO3 and NH4 to get DIN)
            print(icp)
            if icp == 0:
                flux = mult_i * flux_i.copy()
            else:
                flux = flux.copy() + mult_i * flux_i.copy()
    return df, flux
                
###########################################################################################
## MAIN
###########################################################################################

# SW NOTE -- you can see a version of this script used to work as a loop to plot multiple runs.
# I took out the loop functionality but it should be easy to add back in. 

irun = 0 
run_folder = '%s/%s' % (base_dir , run2plot) 

## initialize a figure, to put up plots for all the different runs
fig, ax = plt.subplots(1,2,figsize=(15,4))

colors = ['skyblue', 'orchid', 'brown']
 
## pick a composite parameter to plot
param = 'DIN'

# Get fluxes out the Golden Gate + Loading from the Delta.
df, gg_flux = calculate_flux(from_polys, to_polys, param)
df, delta_flux = calculate_flux(from_delta, to_delta, param)

## get times from the final dataframe
time = df['time'].values.astype('datetime64[ns]')

## compute time step in days (allowing that it might be minutes)
deltat = (time[1] - time[0]).astype('timedelta64[h]').astype(int) / 24

## compute cumulative flux
ind = np.logical_and(time>=t_window[0],time<=t_window[-1])
gg_cumflux = np.cumsum(gg_flux[ind]) * deltat
delta_cumflux = np.cumsum(delta_flux[ind]) * deltat

## add total flux to the plot
ax[0].plot(time, gg_flux/1e6, label = 'Flux out the Golden Gate', color = colors[irun])
ax[0].plot(time, delta_flux/1e6, label = 'Flux in from Delta', color = colors[irun+1])

# cumulative flux to plot 
ax[1].plot(time[ind], gg_cumflux/1e9,    label = 'Flux out the Golden Gate', color = colors[irun], linewidth = 3, alpha = 0.8)
ax[1].plot(time[ind], delta_cumflux/1e9, label = 'Flux in from Delta', color = colors[irun+1], linewidth = 3, alpha = 0.8)
                 
## finish up the plot 
for axis in [ax[0], ax[1]]:
    axis.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    axis.xaxis.set_major_formatter(mdates.DateFormatter('%b/%Y'))
    axis.grid(b=True, alpha = 0.3)
    axis.set_xlim((t_window[0],t_window[-1]))

ax[0].legend(loc='upper right')
ax[1].legend(loc='upper left')
ax[0].set_title('Instantaneous')
ax[0].set_ylabel('%s Flux (10$^6$ g/d)' % param)
ax[1].set_title('Cumulative')
ax[1].set_ylabel('Cumulative %s Flux (10$^9$ g)' % param)
fig.suptitle('%s Flux' % (param))
fig.savefig(outfig_fn)
print('Saved: %s' % outfig_fn)
plt.close('all')
            

#%% STACK PLOT --> EXPORT OUT THE GOLDEN GATE PARTITIONED INTO NO3, NH4

outfig_fn = '%s/DIN_export_GG+Delta_nh4+no3_%s.png'  % (output_dir, run2plot)

## initialize a figure, to put up plots for all the different runs
fig, ax = plt.subplots(1,2,figsize=(15,4))

colors = ['skyblue', 'orchid', 'brown']
  
# Get fluxes out the Golden Gate + Loading from the Delta.
param = 'NH4'
df, gg_flux_nh4 = calculate_flux(from_polys, to_polys, param)
# df, delta_flux_nh4 = calculate_flux(from_delta, to_delta, param)

param = 'NO3'
df, gg_flux_no3 = calculate_flux(from_polys, to_polys, param)
# df, delta_flux_no3 = calculate_flux(from_delta, to_delta, param)  

## get times from the final dataframe
time = df['time'].values.astype('datetime64[ns]')

## compute time step in days (allowing that it might be minutes)
deltat = (time[1] - time[0]).astype('timedelta64[h]').astype(int) / 24

## compute cumulative flux
ind = np.logical_and(time>=t_window[0],time<=t_window[-1])
gg_cumflux_no3 = np.cumsum(gg_flux_no3[ind]) * deltat
gg_cumflux_nh4 = np.cumsum(gg_flux_nh4[ind]) * deltat

# First axis : instantaneous flux 
ax[0].plot([],[],color='forestgreen', label='NO$_3$', linewidth=3)
ax[0].plot([],[],color='skyblue', label='NH$_4$', linewidth=3)
ax[0].stackplot(time, gg_flux_no3/1e6, gg_flux_nh4/1e6, colors=['forestgreen','skyblue'])

ax[1].plot([],[],color='forestgreen', label='NO$_3$', linewidth=3)
ax[1].plot([],[],color='skyblue', label='NH$_4$', linewidth=3)
ax[1].stackplot(time[ind], gg_cumflux_no3/1e9, gg_cumflux_nh4/1e9, colors=['forestgreen','skyblue'])

## finish up the plot 
for axis in [ax[0], ax[1]]:
    axis.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    axis.xaxis.set_major_formatter(mdates.DateFormatter('%b/%Y'))
    axis.grid(b=True, alpha = 0.3)
    axis.set_xlim((t_window[0],t_window[-1]))

ax[0].legend(loc='upper right')
ax[1].legend(loc='upper left')

ax[0].set_title('Instantaneous')
ax[0].set_ylabel('%s Flux (10$^6$ g/d)' % param)
ax[1].set_title('Cumulative')
ax[1].set_ylabel('Cumulative %s Flux (10$^9$ g)' % param)
fig.autofmt_xdate()
fig.suptitle('%s Flux' % (param))
fig.savefig(outfig_fn)
print('Saved: %s' % outfig_fn)
plt.close('all')