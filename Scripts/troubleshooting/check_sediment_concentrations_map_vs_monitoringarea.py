
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

# polygon number
polynum = 10

# peterson station
sta = 29


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

# get station coordinates
df = pd.read_csv(sta_fn)
ind = df['Station']==('%s' % sta)
xsta = df.loc[ind].utm_x.values[0]
ysta = df.loc[ind].utm_y.values[0]

# load all the data
grid = xr.open_dataset(grid_fn)
data_his = xr.open_dataset(os.path.join(run_dir,'dwaq_hist.nc'))
data_map = xr.open_dataset(os.path.join(run_dir,'dwaq_map.nc'))
gdf_poly = gpd.read_file(poly_fn)

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

# read the history file data at polygon 14 and also at station 29
time = data_his.time.values
ntime = len(time)
poly_offset = -1
i=0
while poly_offset<0:
    r = data_his.region.values[i]
    if 'polygon' in r:
        poly_offset = int(r.split('polygon')[1])
    i=i+1
val_his = data_his.sel(region='polygon%d' % (polynum+poly_offset)).sel(field=SUB).bal.values
val_his_point = data_his.sel(region='%d_%d' % (sta,bedlay)).sel(field=SUB).bal.values

# get the history values at the map times
time_map = data_map.time.values
his_time_ind = np.zeros(len(time_map))
for it in range(len(time_map)):
    his_time_ind[it] = np.argmin(np.abs(time - time_map[it]))
his_time_ind = his_time_ind.astype(int)
val_his_at_map = val_his[his_time_ind]
val_his_at_map_point = val_his_point[his_time_ind]

# get the map values
val_map = data_map[SUB].values[:,bedlay,:]

# find the map indices within the polygon
poly_shape = gdf_poly.iloc[polynum]['geometry'] 

# find the indices of the coordiniates inside the polygon and the group
ind_poly = np.zeros(len(xc), dtype=bool)
for i in range(len(xc)):
    ind_poly[i] = Point((xc[i],yc[i])).within(poly_shape)

# plot
fig, ax = plt.subplots(figsize=(8.5,6.5),constrained_layout=True)
ax.plot(xc,yc,'.',markersize=3, label='grid points')
ax.plot(xsta, ysta,'.',markersize=20,label='station %d' % sta)
ax.axis('off')
ax.legend(loc='center right')
fig.savefig('station_map_station%d.png' % sta)

# plot
fig, ax = plt.subplots(figsize=(8.5,6.5),constrained_layout=True)
ax.plot(xc,yc,'.',markersize=3, label='grid points')
ax.plot(xc[ind_poly],yc[ind_poly],'.',markersize=3,label='points within monitoring area %d' % polynum)
gpd.GeoDataFrame(geometry=[poly_shape]).boundary.plot(ax=ax, edgecolor='r', label='monitoring area %d' % polynum)
ax.axis('off')
ax.legend(loc='center right')
fig.savefig('poly_map_P%d.png' % polynum)

# take the area weighted average of the map file value across polygon and group
ntime = len(time_map)
area_tile = np.tile(area,(ntime,1))
conc_map_poly = np.sum(val_map[:,ind_poly]*area_tile[:,ind_poly],axis=1)/np.sum(area_tile[:,ind_poly],axis=1)

# now get map ouptut at history file station location and at the bed
val_map_at_his = val_map[:,imap]

# plot the history and map file values at station 29
fig, ax = plt.subplots(figsize=(8,4), constrained_layout=True)
ax.plot(time_map, val_his_at_map_point, 'k', linewidth=2, label='history file output at station %d' % sta)
ax.plot(time_map, val_map_at_his, 'm--', linewidth=2, label='map file output at station %d' % sta)
ax.set_title('compare map file and history\nfiles at a single point: station %d' % sta)
ax.set_ylabel('%s (g/m^2)' % SUB)
ax.legend()
fig.savefig('history_vs_mapfile_at_station%d_%s' % (sta,SUB))

# best fit lines
P_poly = np.polyfit(val_his_at_map, conc_map_poly, 1)

# now make scatter plot
fig, ax = plt.subplots(figsize=(4, 4),constrained_layout=True)
ax.plot(val_his_at_map, conc_map_poly,'.')
xmin, xmax = ax.get_xlim()
ax.plot(np.array([xmin,xmax]), P_poly[0]*np.array([xmin,xmax])+P_poly[1], label='y = %f x + %f' % (P_poly[0],P_poly[1]))
ax.legend()
ax.set_xlabel('history file output\nfor monitoring area %d' % polynum)
ax.set_ylabel('area weighted average of mapfile\noutput across monitoring area %d' % polynum)
ax.set_title('%s (g/m^2): compare map and\nhistory files for monitoring area %d' % (SUB, polynum))
fig.savefig('monitoring_area_history_vs_mapfile_scatter_%s_area%d.png' % (SUB, polynum))