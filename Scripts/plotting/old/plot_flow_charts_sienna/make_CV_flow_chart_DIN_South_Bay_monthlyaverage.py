# -*- coding: utf-8 -*-
"""

Make flow charts for DIN for South Bay
Monthly average
Save the output as PDF


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


"""


import pandas as pd 
import numpy as np 
import matplotlib as mpl
import matplotlib.pyplot as plt
from pathlib import Path
import sys
import os 
from matplotlib.backends.backend_pdf import PdfPages


    
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
    
# plt.switch_backend('auto')

# (1) Define the CSV you want to read in 

csv = 'h:\hpcshared\Full_res\Control_Volume_Analysis\WY2017\FR17_003\Balance_Table_By_Group_Composite_Parameter_DIN.csv'
# csv = 'h:\hpcshared\Full_res\Control_Volume_Analysis\WY2017\FR17_003\Balance_Table_By_Group_Composite_Parameter_DIN.csv'
csv = local2hpc(csv)
# (2) Define the time window you want to average over


# We want to make monthly averaged plots. This is a pretty gimmicky way of doing it ... I didn't feel like writing out manually each month. 
wy = 2017 
year1 = ['10-01', '11-01', '12-01']
year2 = ['1-01', '2-01', '3-01', '4-01', '5-01', '6-01', '7-01', '8-01', '9-01', '10-01']
times = ['%d-%s' % (wy-1, m) for m in year1] + ['%d-%s' % (wy, m) for m in year2]


# time_window = ['2018-02-01', '2018-10-01']  #'2012-10-01',
#  April-August 2013
# (3) Name this window as a string 
# name_of_window = 'February 2018 - October 2018'
time_windows = [(t, times[i+1]) for i,t in enumerate(times[0:-1])]
name_of_windows = [i.strftime('%b-%y') for i in pd.to_datetime(times)] 

#%% 
# -------------------------------------------------------------------
# Now the script is taking over
# -------------------------------------------------------------------

# (1) Come up with the output file name 
out_fn = Path(csv).parent / ('FlowChart_DIN_Monthly_WY%d.pdf' % wy)
out_fn = str(out_fn)
print('Output will be saved as %s\n' % out_fn)

# (2) Read the data
data = pd.read_csv(csv)
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


with PdfPages(out_fn) as pdf: 
        
    for i, time_window in enumerate(time_windows):
        name_of_window = name_of_windows[i]
        print('Plotting %s' % name_of_window)
        
        # ////////////////////////////////
        data['Date'] = pd.to_datetime(data.time)
        time_start,time_end = pd.to_datetime(time_window[0]), pd.to_datetime(time_window[1])
        indt = np.logical_and(data['Date']>=time_start, data['Date']<time_end)
        
        # Time scales (should always be positive)
        data['rx_timescale']        = abs(data['DIN,Mass (Mg)'] / data['DIN,Net Reaction (Mg/d)'] ) 
        data['transport_timescale'] = abs(data['DIN,Mass (Mg)'] / data['DIN,Net Flux In (Mg/d)']  )
        
        # Grab selection of data during data range, group by CV & average
        data_sel = data.loc[indt]
        data_sel = data_sel.groupby(['group']).mean()
        
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
        for group in cv_groups: 
            #     text = r'$\bf{Group~%s}$' % group + '\n'
        
            text = 'Group %s' % group + '\n'
            data_group = data_sel.loc[group]
            
            # MASS OF DIN
            mass = data_group['DIN,Mass (Mg)']
            text += 'DIN Mass = %3.1f Mg\n' % (mass)
            
            # NET REACTION
            netrx   = data_group['DIN,Net Reaction (Mg/d)']
            text += 'Net Rx = %3.1f\n' % (netrx) # get_sign(netrx),
                 
            # TIME SCALES 
            rx_timescale = data_group['rx_timescale']
            transport_timescale   = data_group['transport_timescale']
            text += '$T_{rx}$ = %3.1f, $T_{transport}$ = %3.1f \n' % (rx_timescale, transport_timescale)
            
            # LOADING (IF APPLICABLE)
            load    = data_group['DIN,Net Load (Mg/d)']
            if load>0:
                text += 'Loading = %3.1f\n' % (load)
                
            # UPTAKE BY PHYTO
            uptake  = data_group['DIN,dDINUpt (Mg/d)']
            text += 'Uptake = %3.1f\n' % (uptake)
            
            # ZOOPLANKTON RESPIRATION 
            zoop_res = data_group['NH4,dZ_NRes (Mg/d)']
            text += 'Zoop resp. = %3.1f\n' % (zoop_res)
            
            # MINERALIZATION
            mineralization = data_group['NH4,dMinDetN (Mg/d)'] + data_group['NH4,dMinPON1 (Mg/d)'] 
            text += 'Mineralization = %3.1f\n' % (mineralization)
            
            # LOSS / DENITRIFICATION
            denit   = data_group['NO3,dDenitWat (Mg/d)'] + data_group['NO3,dDenitSed (Mg/d)'] 
            text += 'Denit = %3.1f' % (denit)
        
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
                text = '%.0f' % (abs(west)) 
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
            text = '%.0f' % (abs(north)) 
        
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
            text = '%.2f' % (abs(south)) 
        
            flux_north_bottom_row.append(text)
            if south>0:  # If the flux in from the south is POSITIVE, the flux arrow needs to be NORTHWARD (into the CV)
                flux_north_bottom_row_rotation.append(90)
            else:
                flux_north_bottom_row_rotation.append(-90)
                
                
        #%%
        
            
            
        
        fig = plt.figure(figsize = (13,7.5))
        ax = plt.gca() 
        ax.xaxis.set_visible(0)
        ax.yaxis.set_visible(0)
        ax.set_frame_on(False)
        # print(plt.rcParams)
        
        ax.set_title('DIN in South Bay, %s' % name_of_window, fontsize = 15)
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
            # print('%s normalized == %f' % (value, val))
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
                            flux_west[k], 
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
                            flux_north[k], 
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
                        flux_north_bottom_row[k], 
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
        
        
        # fig.savefig(out_fn)
        pdf.savefig()
        print('Saved %s' % out_fn)
        plt.close() 
        # plt.show()