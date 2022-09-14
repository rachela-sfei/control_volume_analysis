# -*- coding: utf-8 -*-
"""
Created on Mon Dec 27 14:08:53 2021

@author: siennaw


['group', 'time', 'Volume (m^3)', 'Area (m^2)', 'DIN,Mass (Mg)',
       'DIN,dMass/dt (Mg/d)', 'DIN,Net Flux In (Mg/d)', 'DIN,Net Load (Mg/d)',
       'DIN,Net Transport In (Mg/d)', 'DIN,Net Reaction (Mg/d)',
       'DIN,dMass/dt, Balance Check (Mg/d)', 'DIN,Flux In from N (Mg/d)',
       'DIN,Flux In from S (Mg/d)', 'DIN,Flux In from E (Mg/d)',
       'DIN,Flux In from W (Mg/d)', 'NO3,dDenitWat (Mg/d)',
       'NO3,dDenitSed (Mg/d)', 'NO3,dNiDen (Mg/d)', 'NH4,dMinPON1 (Mg/d)',
       'NH4,dMinDON (Mg/d)', 'NH4,dM_NRes (Mg/d)', 'NH4,dZ_NRes (Mg/d)',
       'NH4,dNH4Aut (Mg/d)', 'DIN,dNitrif (Mg/d)', 'DIN,dDINUpt (Mg/d)',
       'NH4,dMinDetN (Mg/d)']


Here I am recreating the flow chart Dave did in Microsoft PPT or something
using code so we can automate the production.

Python is not necessarily the friendlist environment to mess w/ text boxes 
and labels and arrows, but I've done my best to make it look... reasonable. 

Not the most elegant coding but this is not particurly conducive to much
beyond hard-wiring calculations.


--------------------------------------

edited by alliek March 2022 for NTW meeting

"""


import pandas as pd 
import numpy as np 
import matplotlib as mpl
import matplotlib.pyplot as plt
from pathlib import Path
import sys
import os 
from matplotlib import rcParams # alliek add this to make fonts fixed width, so they align better

rcParams['font.family'] = 'monospace'



    
def local2hpc(pathname):
    # Little hack. See if I'm running this script on a local computer or HPC,
    # and adjust path accordingly.
    OS = sys.platform 
    if OS == 'linux':
        print('Running script on HPC...')
        pathname = pathname.replace('\\', '/')
        pathname = pathname.replace('h:', '/richmondvol1/')
        print('HPC path is %s\n' % pathname)
        plt.switch_backend('Agg')
        plt.rcParams['axes.titlepad'] = 8
    if 'win' in OS:
        print('Running script on local computer...')
        plt.rcParams['axes.titley'] = 1.05
        plt.switch_backend('Qt5Agg')
    return pathname 
    
# (1) if using windows, where is richmondvol1 mounted?
windir = 'X'

# (2) Define the CSV you want to read in 
run_name = 'FR18_003'

# (3) What's the water year?
water_year = 2018

# (4) Define the time window you want to average over
# (5) Time window labels for plot title and figure names
if 0:
    time_window = ['%d-10-01' % (water_year - 1), '%d-01-01' % water_year] 
    figure_title = 'WY%s: Oct, Nov, Dec' % water_year
    figure_label = 'Seasonal_01'
elif 0:
    time_window = ['%d-01-01' % water_year, '%d-04-01' % water_year] 
    figure_title = 'WY%s: Jan, Feb, Mar' % water_year
    figure_label = 'Seasonal_02'
elif 0:    
    time_window = ['%d-04-01' % water_year, '%d-07-01' % water_year] 
    figure_title = 'WY%s: Apr, May, Jun' % water_year
    figure_label = 'Seasonal_03'
elif 1:
    time_window = ['%d-07-01' % water_year, '%d-10-01' % water_year] 
    figure_title = 'WY%s: Jul, Aug,Sep' % water_year
    figure_label = 'Seasonal_04'



#%% 
# -------------------------------------------------------------------
# Now the script is taking over
# -------------------------------------------------------------------
#  (0) Figure out the name of the csv we want to read, and convert file path depending on computer this script is run on.
csv = r'%s:\hpcshared\NMS_Projects\Control_Volume_Analysis\Balance_Tables\%s\Balance_Table_By_Group_Composite_Parameter_DIN.csv' % (windir, run_name)
csv = local2hpc(csv)

# (1) Come up with the output file name 
plot_dir = r'%s:\hpcshared\NMS_Projects\Control_Volume_Analysis\Plots\%s' % (windir,run_name) # alliek -- change plot folder from water year to run id
plot_dir = local2hpc(plot_dir)
if not os.path.exists(plot_dir):
    os.makedirs(plot_dir)   # getting a permission error, need to make directory by hand for now
out_fn = os.path.join(plot_dir,'FlowChart_DIN_%s_%s.png' % (run_name, figure_label))
out_fn = local2hpc(out_fn)
print('Output will be saved as %s\n' % out_fn)

# (2) Read the data
data =pd.read_csv(csv)
print('Read in file: %s' % csv)

# These are the CV groups we are plotting. It is YOUR JOB, READER (!!) to make 
# sure these all border eachother in the grid created by this plot. This script
# is not going to check for you. You can run this script and look at a map to make
# sure the configuration is correct (moving both east-west and north-south)
cv_groups = ['D', 'C', 'B', 'A', 
         'H', 'G', 'F', 'E', 
         'L', 'K', 'J', 'I']

# Geometry of plots / groups listed above 
nrow = 3
ncol = 4 

#%% 

# (3) Average by TIME ! 
#   * average data over a window of time (specified as 'time window')
#   * group data by control volume

data['Date'] = pd.to_datetime(data.time)
time_start,time_end = pd.to_datetime(time_window[0]), pd.to_datetime(time_window[1])
indt = np.logical_and(data['Date']>=time_start, data['Date']<time_end)

## note from alliek: to calculate time scales, we need to take the time average first, also we should only count outflows for transport time ... save for later
## Time scales (should always be positive) 
#data['rx_timescale']        = abs(data['DIN,Mass (Mg)'] / data['DIN,Net Reaction (Mg/d)'] ) 
#data['transport_timescale'] = abs(data['DIN,Mass (Mg)'] / data['DIN,Net Flux In (Mg/d)']  )

# Grab selection of data during data range, group by CV & average
data_sel = data.loc[indt]
data_sel = data_sel.groupby(['group']).mean()

# now that we have taken time average, can compute reaction time scale
data_sel['rx_timescale'] = np.abs(data_sel['DIN,Mass (Mg)'] / data_sel['DIN,Net Reaction (Mg/d)'] ) 

# To compute transport time scale upper bound, need to look at N/S/E/W sides and add up the fluxes that are out only 
# ... first convert inflow to outflow for each side of the  control volume
Q_N = -data_sel['DIN,Flux In from N (Mg/d)'].values
Q_S = -data_sel['DIN,Flux In from S (Mg/d)'].values
Q_E = -data_sel['DIN,Flux In from E (Mg/d)'].values
Q_W = -data_sel['DIN,Flux In from W (Mg/d)'].values
# ... for each side of the control volume, compute a factor "F" that equals 1 when Q is positive (out) and 0 when Q is negative (ind)
F_N = 0.5*np.divide(np.abs(Q_N) + Q_N, np.abs(Q_N))
F_S = 0.5*np.divide(np.abs(Q_S) + Q_S, np.abs(Q_S))
F_E = 0.5*np.divide(np.abs(Q_E) + Q_E, np.abs(Q_E))
F_W = 0.5*np.divide(np.abs(Q_W) + Q_W, np.abs(Q_W))
# ... note this formula for F returns NaN when Q is zero... replace NaNs with zeros
F_N[np.isnan(F_N)] = 0
F_S[np.isnan(F_S)] = 0
F_E[np.isnan(F_E)] = 0
F_W[np.isnan(F_W)] = 0
# ... now coupute the total outflow by adding up outflow through all the sides ... F will zero out inflows and multply outflows by 1
Q_out = F_N*Q_N + F_S*Q_S + F_E*Q_E + F_W*Q_W
# ... finally use total outflow to compute upper bound on transport time scale / flushing time
data_sel['transport_timescale'] = np.abs(data_sel['DIN,Mass (Mg)'] / Q_out  )


# Now compute reaction timescale and upper bound on transport time scale

## Integrate the fluxes over the time period (units now Mg, not Mg/day) 
# data_cum    = data.loc[indt]
# flux_columns = list([i for i in data_cum.columns if 'Flux' in i])
# cumflux     = data_cum.groupby(['group']).sum()
# deltat = (time_end - time_start).days
# cumflux = cumflux[flux_columns]*deltat
# cumflux.columns = [c.replace('(Mg/d)', '(Mg)') for c in cumflux.columns]

# print('Cumulative flux over %d days' % deltat)
# del flux_columns, deltat, data_cum, indt 
    #%% 
    # ## compute cumulative flux
    # ind = np.logical_and(time>=cum_times[0],time<=cum_times[-1])
    # cumflux = np.cumsum(flux[ind]) * deltat

'''
        'DIN,Net Load (Mg/d)',
        'DIN,Net Transport In (Mg/d)', 
        'DIN,Net Reaction (Mg/d)',
        'DIN,dMass/dt, Balance Check (Mg/d)', 
        'DIN,Flux In from N (Mg/d)',
        'DIN,Flux In from S (Mg/d)', 
        'DIN,Flux In from E (Mg/d)',
        'DIN,Flux In from W (Mg/d)', 
       
        'NO3,dDenitWat (Mg/d)',
        'NO3,dDenitSed (Mg/d)', 

        'NO3,dNiDen (Mg/d)', 
        'NH4,dMinPON1 (Mg/d)',
        'NH4,dMinDON (Mg/d)', 
        'NH4,dM_NRes (Mg/d)', 
        'NH4,dZ_NRes (Mg/d)',
        'NH4,dNH4Aut (Mg/d)', 
        'DIN,dNitrif (Mg/d)',
        'DIN,dDINUpt (Mg/d)',
        'NH4,dMinDetN (Mg/d)']

'''

#%% 

# Function DEF: get_sign : if pos, return (+) , if negative, return (-)
# def get_sign(num):
#     if num>0:
#         sign = '+'
#     else:
#         sign = '-'
#     return sign         
  

# (5) Now we start building the data for the plot. This is the text that 
# goes in the text boxes. We are going to loop through all the CVs and 
# add text data on each volume. The data is stored in a list.
cv_groups_data = []
LJ = 14
for group in cv_groups: 
    #     text = r'$\bf{Group~%s}$' % group + '\n'

    text = 'Group %s' % group + '\n'
    data_group = data_sel.loc[group]
    
    # MASS OF DIN
    mass = data_group['DIN,Mass (Mg)']
    text += 'DIN Mass'.ljust(LJ) + ' = %5.0f Mg\n' % (mass)
    
    # LOADING (IF APPLICABLE)
    load    = data_group['DIN,Net Load (Mg/d)']
    text += 'Loading'.ljust(LJ) + ' = %5.2f Mg/d\n' % (load)

    # MINERALIZATION
    mineralization = data_group['NH4,dMinDetN (Mg/d)'] + data_group['NH4,dMinPON1 (Mg/d)'] 
    text += 'Mineralization'.ljust(LJ) + ' = %5.2f Mg/d\n' % (mineralization)
    
    # ZOOPLANKTON RESPIRATION 
    zoop_res = data_group['NH4,dZ_NRes (Mg/d)']
    text += 'Zoop resp.'.ljust(LJ) + ' = %5.2f Mg/d\n' % (zoop_res)

    # LOSS / DENITRIFICATION
    denit   = data_group['NO3,dDenitWat (Mg/d)'] + data_group['NO3,dDenitSed (Mg/d)'] 
    text += 'Denitrif.'.ljust(LJ) + ' = %5.2f Mg/d\n' % (denit)
        
    # UPTAKE BY PHYTO
    uptake  = data_group['DIN,dDINUpt (Mg/d)']
    text += 'Uptake'.ljust(LJ) + ' = %5.2f Mg/d\n' % (uptake)

    # NET REACTION
    netrx   = data_group['DIN,Net Reaction (Mg/d)']
    text += 'Net Reaction'.ljust(LJ) + ' = %5.2f Mg/d\n' % (netrx) # get_sign(netrx),

    # TIME SCALES 
    rx_timescale = data_group['rx_timescale']
    transport_timescale   = data_group['transport_timescale']
    text += '$t_{rx}$ = %0.1f d, $t_{transp}$ < %0.1f d' % (rx_timescale, transport_timescale)

    cv_groups_data.append(text)
        
#%% Calculating fluxes 

# (6) This is the ugliest part of the script. Here we need to figure out 
# all of our flux arrows. Again, this script will NOT CHECK this is correct...
# you can do some cute debugging tricks if you want to check the arrows are
# showing the correct data. Note that we need to think about both the magnitude
# of the arrow, but also its sign!! 
print('Now collecting flux data....\n')

# (7) First off: our E-W arrows
flux_west, west_flux_dir= [], [] 
for group in cv_groups: 
    if group in cv_groups[::4]:    # These three groups are on the West border, so zero flux ... 
        continue  
    else:
        data_group = data_sel.loc[group]
        west = data_group['DIN,Flux In from W (Mg/d)']
        # text = '%3.0f' % (abs(west)) 
        text = '%.1f' % (abs(west)) 
        flux_west.append(text)
        if west<0: # If the flux in from the west is NEGATIVE, the CV is exporting DIN to the EAST
            west_flux_dir.append('larrow')
        else:
            west_flux_dir.append('rarrow')
    
flux_north, north_flux_rotation = [] , []

# (8) N-S arrows, except for bottom row ... 
for group in cv_groups: 
    data_group = data_sel.loc[group]
    north = data_group['DIN,Flux In from N (Mg/d)']
    # text = '%3.0f' % (abs(north))
    text = '%.1f' % (abs(north)) 

    flux_north.append(text)
    if north<0:  # If the flux in from the north is NEGATIVE, the CV is exporting DIN NORTHWARD
        north_flux_rotation.append(90)
    else:
        north_flux_rotation.append(-90)
        
# (9) Bottom row gets special treatment b/c we have to use southward data    
flux_north_bottom_row,  flux_north_bottom_row_rotation= [] , []
for group in cv_groups[8:]: 
    data_group = data_sel.loc[group]
    south = data_group['DIN,Flux In from S (Mg/d)']
    # text = '%3.0f' % (abs(south))
    text = '%.1f' % (abs(south)) 

    flux_north_bottom_row.append(text)
    if south>0:  # If the flux in from the south is POSITIVE, the flux arrow needs to be NORTHWARD (into the CV)
        flux_north_bottom_row_rotation.append(90)
    else:
        flux_north_bottom_row_rotation.append(-90)
        
        
#%%

    
    

#fig = plt.figure(figsize = (13,7.5))
fig = plt.figure(figsize = (15.6,9))
ax = plt.gca() 
ax.xaxis.set_visible(0)
ax.yaxis.set_visible(0)
ax.set_frame_on(False)
# print(plt.rcParams)

ax.set_title('DIN in South Bay, %s' % figure_title, fontsize = 15)
ttl = ax.title 
ttl.set_position([.5, 1.1])

space_between = 0.055


props = dict(boxstyle='round', facecolor='skyblue', alpha=0.5)
plot_size = 0.2
# normalize_size : calculate the size of the arrow based on max value
MAX_SIZE = 1.5
MAX_VAL = max([float(x) for x in (flux_west + flux_north)])
def normalize_size(value):
    value = float(value)
    val = value/MAX_VAL
    val = val*MAX_SIZE + 0.05
    print('%s normalized == %f' % (value, val))
    return val

'''
first row == 1-space_between 
(1 - space_between) + nplot*plot_width + space_bewteen*(nplot-1)

'''



# 
names = ['D', 'C', 'B', 'A', 
         'H', 'G', 'F', 'E', 
         'L', 'K', 'J', 'I']
k = 0
# Set up text boxes
for r in range(nrow):
    y = (1-(space_between*(r+1) + (plot_size*1.25*r)))
    for c in range(ncol):
        x = (0 + space_between*(c+1) + (plot_size*c))
        ax.text(x, y, cv_groups_data[k], transform=ax.transAxes, fontsize=9,
                verticalalignment='top', bbox=props)
        k+= 1 

k = 0


    
flux_fontsize = 8    

# Set up E-W Arrows
for r in range(nrow):
    y = (1-(space_between*(r+1) + (plot_size*1.25*r)))-space_between*2
    for c in range(1,ncol):
        x = (0 + space_between*(c) + (plot_size*c))
        t = ax.text(x, y, 
                    flux_west[k] + '\nMg/d', 
                    ha="center", 
                    va="center", 
                    rotation=0,
                    zorder = 0,
                    size= flux_fontsize, #normalize_size(flux_west[k]),
                    bbox=dict(boxstyle="%s,pad=%f" % (west_flux_dir[k], normalize_size(flux_west[k])), 
                      fc="thistle", ec="plum", 
                      lw=2, alpha = 0.6))
        k+= 1 
        
       
# Set up  N-S Arrows
k=0
for r in range(nrow):
    y = (1-(space_between*(r+1) + (plot_size*1.25*r)))+space_between
    for c in range(0,ncol):
        x = (0 + space_between*(c+2.2) + (plot_size*c))
        t = ax.text(x, y, 
                    flux_north[k] + '\nMg/d', 
                    ha="center", 
                    va="center", 
                    rotation=north_flux_rotation[k],
                    size=flux_fontsize,
                    zorder = 0,
                    bbox=dict(boxstyle="rarrow,pad=%f" % normalize_size(flux_north[k]) ,
                      fc="thistle", ec="plum", 
                      lw=2, 
                      alpha = 0.6))
        k+= 1 

# Last row of arrows (N-S)
k = 0
r = 3
y = (1-(space_between*(r+1) + (plot_size*1.2*r)))+space_between
for c in range(0,ncol):
    if float(flux_north_bottom_row[k]) == 0:
        k+= 1
        continue 
    x = (0 + space_between*(c+2.2) + (plot_size*c))
    t = ax.text(x, y, 
                flux_north_bottom_row[k] + '\nMg/d', 
                ha="center", 
                va="center", 
                rotation=flux_north_bottom_row_rotation[k],
                size=flux_fontsize,
                zorder = 0,
                bbox=dict(boxstyle="rarrow,pad=%f" % normalize_size(flux_north_bottom_row[k]) ,
                  fc="thistle", ec="plum", 
                  lw= 2, 
                  alpha = 0.6))
    k+= 1 


fig.savefig(out_fn)

print('Saved %s' % out_fn)
plt.show()