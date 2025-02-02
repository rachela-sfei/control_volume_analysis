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
import geopandas as gpd
from importlib import reload
import control_volume_plotting_library as CVPL # plotting library must be in same folder as this script
reload(CVPL)

###################
## USER INPUT
###################

#runid = 'G141_13to22_016' 
runid = 'FR21_002'
server = 'chicago'
vol = 'vol2'
is_v24 = True

# base directory for the output figures (in theory should be able to run on windows laptop with mounted drives or on server)
figure_base_dir = '/richmondvol1/hpcshared/open_bay/bgc/figures'

# list of substances to try to plot
substance_list = ['continuity', 'nh4', 'no3', 'pon1', 'pon2', 'don', 'diat', 'diats1', 'green', 'oxy', 
                  'zoopl_e', 'zoopl_r', 'zoopl_v', 
                  'mussel_v','mussel_e','mussel_r','grazer4_v','grazer4_e','grazer4_r',
                  'detns1', 'detns2', 'oons1', 'oons2',
                  'poc1', 'poc2','detcs1', 'detcs2', 'oocs1', 'oocs2']

# start with the default color cycle and add even more colors because the number of reactions is OUT OF CONTROL!
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
          'fuchsia','gold','lawngreen','aqua','lavender','navy','lightgray']

# base directory for model input (used to find shapefiles)
input_base_dir = '/richmondvol1/hpcshared'

# path to the shapefile for full res / aggregated runs
if 'FR' in runid:
    if is_v24:
        shp_fn = os.path.join(input_base_dir,'inputs','shapefiles','Agg_mod_contiguous_v24.shp')
    else:
        shp_fn = os.path.join(input_base_dir,'inputs','shapefiles','Agg_mod_contiguous.shp')
else:
    if is_v24:
        shp_fn = os.path.join(input_base_dir,'inputs','shapefiles','Agg_mod_contiguous_v24-agg141.shp')
    else:
        shp_fn = os.path.join(input_base_dir,'inputs','shapefiles','Agg_mod_contiguous_141.shp')

#####################
# MAIN
#####################

# get strings with concise lists of runs and water years
run_list_str = CVPL.make_concise_runid_list_string([runid])

# path to figures, create if it does not exist
figure_path = os.path.join(figure_base_dir, run_list_str, 'polygon_level_masscons')
if not os.path.exists(figure_path):
    os.makedirs(figure_path)
print('\nfigures will be saved here: %s\n' % figure_path)

# get balance table directory
run_base_dir = '/%s%s/hpcshared' % (server,vol)
run_dir = CVPL.get_run_dir(run_base_dir, runid)
balance_table_dir = os.path.join(run_dir,'Balance_Tables')

# read shapefile, add columns for error
gdf = gpd.read_file(shp_fn)
gdf['err_dmdt'] = np.nan
gdf['err_flux'] = np.nan

# loop through substances
for isub, substance in enumerate(substance_list):

    # read balance table
    try:
        data = pd.read_csv(os.path.join(balance_table_dir, '%s_Table.csv' % substance))
    except:
        print('unable to load table for %s, probably does not exist' % substance)
        continue

    # get the list of positive and negative reactions, also transport and load terms
    rx_pos_cols = []
    rx_neg_cols = []
    load_cols = []
    tran_cols = []
    for col in data.columns:
        if 'Loads' in col:
            load_cols.append(col)
        elif 'Transp' in col:
            tran_cols.append(col)
        elif not col in ['time', 'Control Volume', 'Concentration (mg/l)', 'Volume',
                       'Volume (Mean)', 'Area','dVar/dt']:
            if not 'To_' in col:
                if not 'Flux' in col:
                    if np.nanmean(data[col])>=0:
                        rx_pos_cols.append(col)
                    else:
                        rx_neg_cols.append(col)

    # compile all reactions
    rx_cols = rx_pos_cols.copy()
    for rx in rx_neg_cols:
        rx_cols.append(rx)

    # get list of polygons
    poly_list = np.sort(np.unique(data['Control Volume'].values))


    # compute number of fluxes
    numflux = 0
    for col in data.columns:
        if 'Flux' in col:
            numflux += 1

    # loop through the polygons
    for poly in poly_list:

        # get polygon number
        ipoly = int(poly[7:])

        # select data for this polygon
        ind = data['Control Volume'] == poly
        data1 = data.loc[ind]

        # get time and time step in days
        time = data1['time'].values.astype('datetime64[ns]')
        dt_days = (time[1]-time[0])/np.timedelta64(1,'D')

        # get storage term
        dMdt = data1['dVar/dt'].values / 1e6

        # sum up loads, transport, net reaction
        load = data1[load_cols].sum(axis=1).values / 1e6
        net_tr = data1[tran_cols].sum(axis=1).values / 1e6
        net_rx = data1[rx_cols].sum(axis=1).values / 1e6

        # compute storage from other terms
        dMdt_balcheck = load + net_tr + net_rx

        # make a dataframe with the reactions
        if len(rx_cols)>0:
            df_rx = data1[rx_cols]  / 1e6
            df_rx_pos = df_rx.copy(deep=True)
            df_rx_neg = df_rx.copy(deep=True)
            df_rx_pos[df_rx<0] = 0
            df_rx_neg[df_rx>0] = 0

        # make a dataframe with the fluxes
        df_flux = pd.DataFrame()
        to_poly_list = []
        for fluxnum in range(numflux):
            to_poly = data1['To_poly%d' % fluxnum].values[0]
            if not np.isnan(to_poly):
                to_poly_str = 'flux to polygon%d' % to_poly
                df_flux[to_poly_str] = data1['Flux%d' % fluxnum] / 1e6
        net_flux = df_flux.sum(axis=1)

        # make a figure
        fig, ax = plt.subplots(3,1,figsize=(8.5,11), constrained_layout=True)

        # plot the mass balance
        ax[0].plot(time,load, label='Point Source Load')
        ax[0].plot(time,net_tr, label='Net Transport In')
        ax[0].plot(time,net_rx, label='Net Reaction')
        ax[0].plot(time,dMdt, color='aqua', label='dMass/dt')
        ax[0].plot(time,dMdt_balcheck, '--', color='yellow', label='dMass/dt (Balance Check)')
        ax[0].set_xlim((time[0],time[-1]))
        ax[0].legend()
        ax[0].set_ylabel('Rate (Mg/d)')

        # plot the reactions
        if len(rx_cols)>0:
            ax[1].stackplot(time, df_rx_pos.values.transpose(), colors = colors[0:len(df_rx.columns)], labels=df_rx.columns)
            ax[1].stackplot(time, df_rx_neg.values.transpose(), colors = colors[0:len(df_rx.columns)])
            ax[1].plot(time, net_rx, color='aqua',label='Net Reaction')
            ax[1].set_xlim((time[0],time[-1]))
            ax[1].legend()
            ax[1].set_ylabel('Rate (Mg/d)')

        # plot the transport
        for col in df_flux.columns:
            ax[2].plot(time, df_flux[col], label=col)
        ax[2].plot(time, net_flux, color='aqua', label='sum of fluxes across transects')
        ax[2].plot(time, net_tr, '--', color='yellow', label='net transport from mass balance')
        ax[2].set_xlim((time[0],time[-1]))
        ax[2].legend()
        ax[2].set_ylabel('Rate (Mg/d)')    

        ax[0].set_title('%s: Mass budget for %s' % (runid,poly))
        fig.savefig(os.path.join(figure_path, '%s_mass_budget_%s_%s.png' % (runid,substance, poly)), dpi=200)    

        plt.close('all')

        #########################################
        # compute error and plot for each substance
        #########################################

        err_mass = np.sqrt(np.mean((dMdt_balcheck - dMdt)**2) / np.mean(dMdt**2)) * 100
        err_flux = np.sqrt(np.mean((net_flux - net_tr)**2) / np.mean(net_tr**2)) * 100

        if ipoly in gdf.index:

            print('ipoly=%d' % ipoly)
            gdf.loc[ipoly, 'err_dmdt'] = err_mass
            gdf.loc[ipoly, 'err_flux'] = err_flux


        if poly == poly_list[-1]:

            fig, ax = plt.subplots(1,2, figsize=(16,8), constrained_layout=True)

            gdf.plot(column='err_dmdt', ax=ax[0], vmin=0, vmax=100, cmap='jet', legend=True)
            gdf.plot(column='err_flux', ax=ax[1], vmin=0, vmax=100, cmap='jet', legend=True)

            ax[0].axis('off')
            ax[1].axis('off')
            ax[0].set_title('100% x square root of\n<(dM/dt - dM/dt (balance check))^2>\n/<(dM/dt)^2>')
            ax[1].set_title('100% x square root of\n<(net flux - net transport in)^2>\n/<(net transport in)^2>')
            fig.suptitle('%s: %s' % (runid,substance))
            fig.savefig(os.path.join(figure_path, '%s_mass_and_flux_error_%s.png' % (runid,substance)), dpi=200)    


            plt.close('all')


        #########################################
        # now do the same thing but cumulative
        #########################################

        # get storage term
        dMdt = np.cumsum(dMdt)*dt_days

        # sum up loads, transport, net reaction
        load = np.cumsum(load)*dt_days
        net_tr = np.cumsum(net_tr)*dt_days
        net_rx = np.cumsum(net_rx)*dt_days

        # compute storage from other terms
        dMdt_balcheck = load + net_tr + net_rx

        # make a dataframe with the reactions
        if len(rx_cols)>0:
            df_rx = data1[rx_cols].cumsum()*dt_days  / 1e6
            df_rx_pos = df_rx.copy(deep=True)
            df_rx_neg = df_rx.copy(deep=True)
            df_rx_pos[df_rx<0] = 0
            df_rx_neg[df_rx>0] = 0

        # make a dataframe with the fluxes
        df_flux = df_flux.cumsum()*dt_days
        net_flux = df_flux.sum(axis=1)

        # make a figure
        fig, ax = plt.subplots(3,1,figsize=(8.5,11), constrained_layout=True)

        # plot the mass balance
        ax[0].plot(time,load, label='Point Source Load')
        ax[0].plot(time,net_tr, label='Net Transport In')
        ax[0].plot(time,net_rx, label='Net Reaction')
        ax[0].plot(time,dMdt, color='aqua', label='dMass/dt')
        ax[0].plot(time,dMdt_balcheck, '--', color='yellow', label='dMass/dt (Balance Check)')
        ax[0].set_xlim((time[0],time[-1]))
        ax[0].legend()
        ax[0].set_ylabel('Cumulative Mass (Mg)')

        # plot the reactions
        if len(rx_cols)>0:
            ax[1].stackplot(time, df_rx_pos.values.transpose(), colors = colors[0:len(df_rx.columns)], labels=df_rx.columns)
            ax[1].stackplot(time, df_rx_neg.values.transpose(), colors = colors[0:len(df_rx.columns)])
            ax[1].plot(time, net_rx, color='aqua',label='Net Reaction')
            ax[1].set_xlim((time[0],time[-1]))
            ax[1].legend()
            ax[1].set_ylabel('Cumulative Mass (Mg)')

        # plot the transport
        for col in df_flux.columns:
            ax[2].plot(time, df_flux[col], label=col)
        ax[2].plot(time, net_flux, color='aqua', label='sum of fluxes across transects')
        ax[2].plot(time, net_tr, '--', color='yellow', label='net transport from mass balance')
        ax[2].set_xlim((time[0],time[-1]))
        ax[2].legend()
        ax[2].set_ylabel('Cumulative Mass (Mg)') 

        ax[0].set_title('%s: Mass budget for %s' % (runid,poly))
        fig.savefig(os.path.join(figure_path, '%s_cumulative_mass_budget_%s_%s.png' % (runid,substance, poly)), dpi=200)    

        plt.close('all')

