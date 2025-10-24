import geopandas as gpd
import os, sys

# path to group def and grid shapefiles, base directory
# '/richmondvol1/alliek/local_repos/control_volume_analysis/Scripts/troubleshooting'
sub_fn = os.path.join('..','..','Definitions','group_shapefiles','group_definition_shapefile_v24_FR.shp')
grid_fn = os.path.join('..','..','Definitions','grid_shapefiles','open_bay_model_grid_FR_v24.shp')

# load shapefiles
subs = gpd.read_file(sub_fn)
grid = gpd.read_file(grid_fn)

# isolate one subembayment (enter subs['feature'].values in command line to see all 
# subemebayments and more!)
sub_poly = subs.loc[subs['feature']=='SB_RMP']

# this gives you a logical index that's true for grid cells within the subembayment, note
inside_index = grid.within(sub_poly['geometry'].values[0])

# if working with the netcdf grid you can just use FlowElem_xcc, FlowElem_ycc, but you need
# turn them into shapely points 
# from shapely.geometry import Point
# grid_points = [Point(x,y) for x, y in zip(grid_xr['FlowElem_xcc'], grid_xr['FlowElem_ycc'])]