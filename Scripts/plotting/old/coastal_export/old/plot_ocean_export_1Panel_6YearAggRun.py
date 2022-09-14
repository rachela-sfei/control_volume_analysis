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



# PARAM_SENS = 'Diagenesis rate in Layers 1,2'
# Dict : run label followed by RunID 
runs2plot   = {'Base (#125)'         : 'G141_13to18_125'}
run_name    = 'Base (#125)'

print('Making plots for %s \n' % run_name)

## pick a composite parameter to plot
param = 'DIN'

#%%
## pick the time window for cumulative plot
water_years = np.arange(2013,2019)
time_windows  = [('%d-03-01' % (i), '%d-10-01' % i) for i in water_years]



    
#%%
# cum_times = np.array(['2013-03-01','2013-06-01']).astype('datetime64')

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



## directory containting balance tables, including path
base_dir = './balance_tables'



# Make output directory 
output_dir = r'/richmondvol1/hpcshared/Grid141/WY13to18//%s/CONTROL_VOLUME_PLOTS//' % runs2plot[run_name]
# output_dir = '/%s/%s//' % (output_dir, PARAM_SENS)
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
    print('Made %s' % output_dir)

## file name for output figure, including path
outfig_fn = '%s/FLUX_OUT_GG_AllWY_GrowingSeason.png'  % (output_dir)
      
    
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
fig, ax = plt.subplots(1,2,figsize=(16,5))

colors = ['skyblue', 'orchid', 'brown', 'gold', 'springgreen', 'indigo', 'crimson']
 
 ## loop through the run folders

# for irun, run_label in enumerate(run_labels):

run_folder = runs2plot[run_name]


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
# deltat = (time[1] - time[0]).astype('timedelta64[h]').astype(int) / 24

    


for i, water_year in enumerate(water_years): 

    print('Plotting WY%d' % water_year)
    ## compute time step in days (allowing that it might be minutes)
    nt = [time_windows[i][0], time_windows[i][1]]
 

    deltat  = (np.array(nt)).astype('datetime64') #.astype(int) / 24
    ind = np.logical_and(time>=deltat[0], time<=deltat[1])

    # xt      = np.arange(0, (deltat[1] - deltat[0]).astype(int))
    
    ## add total flux to the plot
    flux0 = flux[ind]
    xt = np.arange(0,len(flux0))


    ax[0].plot(xt, flux0/1e6, label = 'WY%d' % water_year, linewidth = 2.5, alpha = 0.6) # , color = colors[i] )

    # compute cumulative flux
    cumflux = np.cumsum(flux0) * xt[-1]
    ax[1].plot(xt, cumflux/1e9, label = water_year, linewidth = 3, alpha = 0.6) # , color = colors[i] )

# Make xlabel-s for x-axis 
times = pd.date_range(deltat[0], deltat[1], freq='31D')
x_loc = np.arange(0, 365, 31)                                              
x_labels = [x.strftime('%b') for x in times]

# Set up instantaneous flux 
ax[0].set_xticks(x_loc)
ax[0].set_xticklabels(x_labels)
ax[0].grid(b=True, alpha = 0.2)
ax[0].legend()
ax[0].set_xlim(0, 210)
ax[0].set_ylabel('%s Flux (10$^6$ g/d)' % param)

# Set up cumulative flux 
ax[1].set_xticks(x_loc)
ax[1].set_xticklabels(x_labels)
ax[1].grid(b=True, alpha = 0.2)
ax[1].set_xlim(0, 210)
ax[1].set_ylabel('Cumulative Flux (10$^9$ g)')             

ax[0].set_title('Instantaneous Flux')
ax[1].set_title('Cumulative Flux')
ax[1].set_ylabel('Cumulative %s Flux (10$^9$ g)' % param)
                                                                                                                                                                                                                                                                                

fig.suptitle('%s Flux Out of Golden Gate' % (param))
fig.savefig(outfig_fn)
plt.close('all')
print(outfig_fn)
            
      