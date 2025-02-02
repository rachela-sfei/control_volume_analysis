'''
Check that the group boundaries don't overlap
'''

########################################################################################
# import python packages
########################################################################################

import sys, os
import pandas as pd
import numpy as np
import matplotlib.pylab as plt
import geopandas as gpd
from shapely.geometry import LineString

#########################################################################################
# user input
#########################################################################################

## subset of groups to make shapefile
#group_subset = ['L','K','J','I','H','G','F','E','D','C','B','A','V','U1','T1','S1','U2','T2','S2','X','W','Z','Y']

# is full resolution?
FR=True

# is v24?
v24 = True

# for FR Runs (includes new segments defined by sienna and whole bay added by allie...)
if FR:
    if v24:
        output_definition_path = 'group_shapefiles/group_definition_shapefile_v24_FR.shp'
        output_connectivity_path = 'group_shapefiles/group_connectivity_shapefile_v24_FR.shp'

    else:
        output_definition_path = 'group_shapefiles/group_definition_shapefile_FR.shp'
        output_connectivity_path = 'group_shapefiles/group_connectivity_shapefile_FR.shp'

# for AGG runs (includs now whole bay group added by allie)
else:
    if v24:
        output_definition_path = 'group_shapefiles/group_definition_shapefile_v24_AGG.shp'
        output_connectivity_path = 'group_shapefiles/group_connectivity_shapefile_v24_AGG.shp'
    else:
        output_definition_path = 'group_shapefiles/group_definition_shapefile_AGG.shp'
        output_connectivity_path = 'group_shapefiles/group_connectivity_shapefile_AGG.shp'


# now concatenate groups and connectivities and save in a shapefile
gdf_group = gpd.read_file(output_definition_path)
gdf_connect = gpd.read_file(output_connectivity_path)

for group in gdf_group.feature:

    ind = gdf_connect['feature'] == '%s to N' % group
    if np.any(ind):
        lineN = gdf_connect.loc[ind]['geometry'].values[0]
    else:
        lineN = None
    ind = gdf_connect['feature'] == '%s to S' % group
    if np.any(ind):
        lineS = gdf_connect.loc[ind]['geometry'].values[0]
    else:
        lineS = None
    ind = gdf_connect['feature'] == '%s to E' % group
    if np.any(ind):
        lineE = gdf_connect.loc[ind]['geometry'].values[0]
    else:
        lineE = None
    ind = gdf_connect['feature'] == '%s to W' % group
    if np.any(ind):
        lineW = gdf_connect.loc[ind]['geometry'].values[0]
    else:
        lineW = None

    if not lineN is None:

        if not lineE is None:

            inter = lineN.intersection(lineE)

            if not (inter.is_empty or inter.geom_type=='Point'):

                raise Exception('Group %s: N and E intersedtion is %s' % (group, inter.geom_type))

        if not lineW is None:

            inter = lineN.intersection(lineW)

            if not (inter.is_empty or inter.geom_type=='Point'):

                raise Exception('Group %s: N and W intersedtion is %s' % (group, inter.geom_type))

    if not lineS is None:

        if not lineE is None:

            inter = lineS.intersection(lineE)

            if not (inter.is_empty or inter.geom_type=='Point'):

                raise Exception('Group %s: S and E intersedtion is %s' % (group, inter.geom_type))

        if not lineW is None:

            inter = lineS.intersection(lineW)

            if not (inter.is_empty or inter.geom_type=='Point'):

                raise Exception('Group %s: S and W intersedtion is %s' % (group, inter.geom_type))




