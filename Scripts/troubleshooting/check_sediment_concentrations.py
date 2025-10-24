
import xarray as xr
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Polygon, Point
import matplotlib.pylab as plt
import os, sys

# substance
sub = 'detns1'
SUB = 'DetNS1'

# bed layer (10 sigma layers 0 to 9)
bedlay = 9

# peterson station
sta = 29

# polygon and group with station in it
polynum = 14
groupnum = 'G' 

# station csv
sta_fn = '/richmondvol1/hpcshared/inputs/stations/stations_v4.csv'

# run directory
run_dir = '/chicagovol2/hpcshared/open_bay/bgc/full_res/WY2021/FR21_009'
#run_dir = '/fortcollinsvol1/hpcshared/open_bay/bgc/full_res/WY2022/FR22_046'

# hydro, for grid
grid_fn = '/boisevol2/hpcshared/open_bay/hydro/full_res/wy2021-v24/runs/wy2021-v24/DFM_DELWAQ_wy2021-v24_bound_temp_salt/wy2021-v24_waqgeom.nc'
#grid_fn = '/boisevol1/hpcshared/open_bay/hydro/full_res/wy2022_r52184/runs/wy2022_r52184/DFM_DELWAQ_wy2022_r52184_bound_temp_salt/wy2022_r52184_waqgeom.nc'

# polygon and group shapefiles
poly_fn = '/richmondvol1/alliek/local_repos/control_volume_analysis/Definitions/model_input_shapefiles/Agg_mod_contiguous_v24.shp'
group_fn = '/richmondvol1/alliek/local_repos/control_volume_analysis/Definitions/group_shapefiles/group_definition_shapefile_v24_FR.shp' 

# get station coordinates
df = pd.read_csv(sta_fn)
ind = df['Station']==('%s' % sta)
xsta = df.loc[ind].utm_x.values[0]
ysta = df.loc[ind].utm_y.values[0]

# load balance tables both at polygon level and at group level
df_poly = pd.read_csv(os.path.join(run_dir,'Balance_Tables','%s_Table.csv' % sub))
df_group = pd.read_csv(os.path.join(run_dir,'Balance_Tables','%s_Table_By_Group.csv' % sub))

# load all the data
grid = xr.open_dataset(grid_fn)
data_his = xr.open_dataset(os.path.join(run_dir,'dwaq_hist.nc'))
data_hbal = xr.open_dataset(os.path.join(run_dir,'dwaq_hist_bal.nc'))
data_map = xr.open_dataset(os.path.join(run_dir,'dwaq_map.nc'))
gdf_poly = gpd.read_file(poly_fn)
gdf_group = gpd.read_file(group_fn)

# get centroids of the flow elements
xc = grid['FlowElem_xcc'].values
yc = grid['FlowElem_ycc'].values

# find the area of the flow elements
area = np.zeros(len(xc))
for ig in range(len(xc)):
    xcc = grid['FlowElemContour_x'][ig,:].values
    ycc = grid['FlowElemContour_y'][ig,:].values
    ind = xcc>=0
    xcc = xcc[ind]
    ycc = ycc[ind]
    poly = Polygon([[xcc[i],ycc[i]] for i in range(len(xcc))])
    area[ig] = poly.area

# find index of grid cell closest to history station
d2 = (xc - xsta)**2 + (yc - ysta)**2
imap = np.argmin(d2)

# read the history file data at station 29
time = data_his.time.values
ntime = len(time)
val_his = data_his.sel(region='%d_%d' % (sta,bedlay)).sel(field=SUB).bal.values

# get the history values at the map times
time_map = data_map.time.values
his_time_ind = np.zeros(len(time_map))
for it in range(len(time_map)):
    his_time_ind[it] = np.argmin(np.abs(time - time_map[it]))
his_time_ind = his_time_ind.astype(int)
val_his_at_map = val_his[his_time_ind]

# get the map values
val_map = data_map[SUB].values[:,bedlay,:]

# now get map ouptut at history file station location and at the bed
val_map_at_his = val_map[:,imap]

# plot
fig, ax = plt.subplots(figsize=(8.5,4), constrained_layout=True)
ax.plot(time_map, val_his_at_map, 'k', label = 'history file value at station %d' % sta)
ax.plot(time_map, val_map_at_his, 'm', label = 'map file value at station %d' % sta)
ax.set_ylabel(SUB)
ax.legend()
fig.savefig('compare_his_map_%s_P%d_G%s.png' % (SUB, polynum, groupnum))

# find the map indices within the polygon and the group
poly_shape = gdf_poly.iloc[polynum]['geometry'] 
group_shape = gdf_group.loc[gdf_group['feature']==groupnum]['geometry'].iloc[0]

# find the indices of the coordiniates inside the polygon and the group
ind_poly = np.zeros(len(xc), dtype=bool)
ind_group = np.zeros(len(xc), dtype=bool)
for i in range(len(xc)):
    ind_poly[i] = Point((xc[i],yc[i])).within(poly_shape)
    ind_group[i] = Point((xc[i],yc[i])).within(group_shape)

# plot
fig, ax = plt.subplots(figsize=(8.5,7.5),constrained_layout=True)
ax.plot(xc,yc,'.',label='grid points')
ax.plot(xc[ind_group],yc[ind_group],'.',label='group %s' % groupnum)
ax.plot(xc[ind_poly],yc[ind_poly],'.',label='polygon %d' % polynum)
ax.plot(xsta,ysta,'.',label='station %d' % sta)
ax.axis('off')
ax.legend()
fig.savefig('station_poly_group_%s_P%d_G%s.png' % (SUB, polynum, groupnum))

# take the area weighted average of the map file value across polygon and group
ntime = len(time_map)
area_tile = np.tile(area,(ntime,1))
conc_map_poly = np.sum(val_map[:,ind_poly]*area_tile[:,ind_poly],axis=1)/np.sum(area_tile[:,ind_poly],axis=1)
conc_map_group = np.sum(val_map[:,ind_group]*area_tile[:,ind_group],axis=1)/np.sum(area_tile[:,ind_group],axis=1)

# get the concentrations from the balance tables
df_poly = df_poly[df_poly['Control Volume']==('polygon%d' % polynum)]
time_poly = df_poly['time'].values.astype('datetime64[D]')
conc_poly = (df_poly['Concentration (mg/l)']*df_poly['Volume']/df_poly['Area']).values
df_group = df_group[df_group['group']==groupnum]
time_group = df_group['time'].values.astype('datetime64[D]')
conc_group = (df_group['%s,Mass (Mg)' % SUB]/df_group['Area (m^2)']).values*1e6


# plot
fig, ax = plt.subplots(figsize=(8.5,4), constrained_layout=True)
ax.plot(time_map, val_his_at_map, 'k', label = 'history file value at station %d' % sta)
ax.plot(time_map, conc_map_poly, 'm--', label = 'map file average over polygon %d' % polynum)
ax.plot(time_map, conc_map_group, ':', color='gold', label = 'map file average over group %s' % groupnum)
ax.plot(time_poly, conc_poly, 'blue', label = 'value from polygon level balance table')
ax.plot(time_group, conc_group, 'red', label = 'value from group level balance table')
ax.set_ylabel('%s (g/m^2)' % SUB)
ax.legend()
fig.savefig('compare_his_poly_group_%s_P%d_G%s.png' % (SUB, polynum, groupnum))

# best fit lines
ntbt = len(time_poly)
P_poly = np.polyfit(conc_map_poly[:ntbt], conc_poly[:ntbt], 1)
P_group = np.polyfit(conc_map_group[:ntbt], conc_group[:ntbt],1)

# now get the concentrations from the balance tables
fig, ax = plt.subplots(1,2, figsize=(8.5, 4),constrained_layout=True)
ax[0].plot(conc_map_poly[:ntbt],conc_poly[:ntbt],'.')
xmin, xmax = ax[0].get_xlim()
ax[0].plot(np.array([xmin,xmax]), P_poly[0]*np.array([xmin,xmax])+P_poly[1], label='%f x + %f' % (P_poly[0],P_poly[1]))
ax[0].legend()
ax[0].set_xlabel('mapfile average\nover polygon %d' % polynum)
ax[0].set_ylabel('balance table average\nover polygon %d' % polynum)
ax[0].set_title('%s (g/m^2)' % SUB)
ax[1].plot(conc_map_group[:ntbt],conc_group[:ntbt],'.')
xmin, xmax = ax[1].get_xlim()
ax[1].plot(np.array([xmin,xmax]), P_group[0]*np.array([xmin,xmax])+P_group[1], label='%f x + %f' % (P_poly[0],P_poly[1]))
ax[1].legend()
ax[1].set_xlabel('mapfile average\nover group %s' % groupnum)
ax[1].set_ylabel('balance table average\nover group %s' % groupnum)
ax[1].set_title('%s (g/m^2)' % SUB)
fig.savefig('balance_table_vs_mapfile_avg_scatter_%s_P%d_G%s.png' % (SUB, polynum, groupnum))