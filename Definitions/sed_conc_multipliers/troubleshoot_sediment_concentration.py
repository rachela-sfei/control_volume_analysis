
'''
This script converts *.his and *-bal.his data to *.csv formatted balance tables containing
daily fluxes and reaction terms in the "monitoring regions" defined by polygons and transects.
Updated by Allie in 2022 to run in new python environment on chicago:
    source activate geo_env
    cd /richmondvol1/hpcshared/NMS_Projects/Control_Volume/Scripts/create_balance_tables
and run from there
'''

#################################################
# IMPORT MODULES (save stompy for later)
#################################################

import os, sys, shutil
import xarray as xr
import numpy as np
import pandas as pd
import datetime 
import geopandas as gpd
import matplotlib.pylab as plt

##################
# MAIN
##################


FR_or_Agg = 'FR'

outdir = 'troubleshoot_sediment_conc'
if not os.path.exists(outdir):
    os.makedirs(outdir)

if FR_or_Agg=='FR':

    # load polygon shapefile
    poly_df_new = gpd.read_file('../../Definitions/model_input_shapefiles/Agg_mod_contiguous_v24.shp')
    Area_new = poly_df_new.area.values
    poly_df_old = gpd.read_file('../../Definitions/model_input_shapefiles/Agg_mod_contiguous.shp')
    Area_old = poly_df_old.area.values


    # path to his and his bal files
    table_path_list = [
    '/chicagovol2/hpcshared/open_bay/bgc/full_res/WY2021/FR21_002/Balance_Tables/', # new binaries, new grid
    '/chicagovol1/hpcshared/open_bay/bgc/full_res/WY2022/FR22_012_dfm_t141798opt/Balance_Tables/', # new binaries, old grid
    '/chicagovol1/hpcshared/open_bay/bgc/full_res/WY2013/FR13_026/Balance_Tables/'] # old binaries, old grid

    # run labels
    run_label_list = ['FR21_002 (new binaries, new grid)','FR22_012 (new binaries, old grid)','FR13_026 (old binaries, old grid)']

    #'/chicagovol2/hpcshared/open_bay/bgc/agg/WY13to22/G141_13to22_016/Balance_Tables/', # new binaries, new grid
    Area_list = [Area_new, Area_old, Area_old]

    # colors and linestyles for plot
    colors = ['k','c','r']
    linestyles = ['-','--',':']

elif FR_or_Agg=='Agg':

    # load polygon shapefile
    poly_df_new = gpd.read_file('../../Definitions/model_input_shapefiles/Agg_mod_contiguous_v24-agg141.shp')
    Area_new = poly_df_new.area.values
    poly_df_old = gpd.read_file('../../Definitions/model_input_shapefiles/Agg_mod_contiguous_141.shp')
    Area_old = poly_df_old.area.values

    # path to his and his bal files
    table_path_list = [
    '/chicagovol2/hpcshared/open_bay/bgc/agg/WY13to22/G141_13to22_016/Balance_Tables/', # new binaries, new grid
    '/richmondvol1/hpcshared/Grid141/WY13to18/G141_13to18_246/Balance_Tables/', # old binaries, old grid
    ] 

    # run labels
    run_label_list = ['G141_13to22_016 (new binaries, new grid)','G141_13to18_246 (old binaries, old grid)']

    #'/chicagovol2/hpcshared/open_bay/bgc/agg/WY13to22/G141_13to22_016/Balance_Tables/', # new binaries, new grid
    Area_list = [Area_new, Area_old]

    # colors and linestyles for plot
    colors = ['k','c','r']
    linestyles = ['-','--',':']


# variables to test
varnames = ['detns1','detns2','diats1','oons1','oons2']

for ipoly in range(len(Area_new)):

    fig, ax = plt.subplots(2,3, figsize=(20,11), constrained_layout=True)
    ax = ax.flatten()

    # loop through all the parameters (nh4, no3, diat, etc.)
    for it, table_path in enumerate(table_path_list):

        ratios = []

        Area = Area_list[it]

        for ivar,varname in enumerate(varnames):

            try:
                df = pd.read_csv(os.path.join(table_path,'%s_Table.csv' % varname))
            except:
                continue

            # sum everything in the mass balance to get mass closure estimate of dVar/dt
            cols = []
            for col in df.columns:
                if (varname+',') in col.lower():
                    cols.append(col)

            # find the polygon
            ind = (df['Control Volume'] == 'polygon%d' % ipoly).values

            # sum the reactions, transport, and loading to get an estimate of dM/dt
            dVdt_bal = df[cols].sum(axis=1).values[ind]

            # take the independent estimate of dM/dt, calculated from concentraiton,
            # from the balance table
            dVdt_con = df['dVar/dt'].values[ind]

            # now find non nan values
            ind = np.logical_and(~np.isnan(dVdt_bal), ~np.isnan(dVdt_con))
            dVdt_bal = dVdt_bal[ind]
            dVdt_con = dVdt_con[ind]

            # find limits
            minx = np.min(dVdt_bal)
            maxx = np.max(dVdt_bal)

            # find ratio, filter out small values of dVdt_con
            ind = np.abs(dVdt_con)>=1e-4
            ratio = np.mean(dVdt_bal[ind] / dVdt_con[ind])

            # now plot
            ax[ivar].plot(dVdt_bal, dVdt_con, '.', color=colors[it], markersize=1, alpha=0.5)
            ax[ivar].plot([minx, maxx], [minx/ratio, maxx/ratio], 
                          color=colors[it], linestyle=linestyles[it], label='%s\n: dM/dt (balance)/ dM/dt (conc) = %0.2f' % (run_label_list[it], ratio))

            # add axis labels
            if it==0:
                ax[ivar].set_xlabel('dM/dt from mass bal')
                ax[ivar].set_ylabel('dM/dt from concent.')
                ax[ivar].set_title('%s' % varname)

            # collect ratios across variables and runs
            ratios.append(ratio)

    ratio = np.nanmedian(np.array(ratios))

    poly_df_new.loc[ipoly,'ratio'] = ratio

    for ax1 in ax:
        ax1.legend()

    fig.savefig(os.path.join(outdir,'dMdt_compare_%s_polygon%d.png' % (FR_or_Agg,ipoly)))

    plt.close('all')

fig, ax = plt.subplots(figsize=(20,14), constrained_layout=True)
poly_df_new.plot(ax=ax, column='ratio', cmap='jet', vmin=0, vmax=15, legend=True, edgecolor='gray')
ax.axis('off')
for ipoly in range(len(poly_df_new)):
    xc, yc = poly_df_new.iloc[ipoly].geometry.centroid.xy
    ratio = poly_df_new.iloc[ipoly]['ratio']
    ax.text(xc[0],yc[0],'%0.1f' % ratio, fontsize=8, ha='center', va='center')
title_str = 'dM/dt (balance) / dM/dt (concentration)\nmedian across runs '
for run_label in run_label_list:
    title_str = title_str + run_label.split()[0] + ', '
title_str = title_str[0:-2] + '\nand variables '
for varname in varnames:
    title_str = title_str + varname + ', '
title_str = title_str[0:-2] 
ax.set_title(title_str)
fig.savefig(os.path.join(outdir,'dMdt_compare_MAP_%s.png' % FR_or_Agg))

df = pd.DataFrame(poly_df_new['ratio'].values, columns=['dMdt(bal)/dMdt(con)'])
df.index.name='polygon'

df.to_csv('Multiply_Polygon_Sediment_Conc_By_%s.csv' % FR_or_Agg)