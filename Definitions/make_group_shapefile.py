'''
For plotting, it is useful to have a shapefile defining all the group polygons and their
N,S,E,W connections to each other. Here we generate this shapefile. We also make plots illustrating
the groups an their N,S,E,W connections. It is useful to check these plots if you define any new
groups, to check for errors
'''

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
        group_definition_file   = 'group_definitions/control_volume_definitions_v24_FR.txt'
        group_connectivity_file = 'group_definitions/connectivity_definitions_v24_FR.txt'
        polygon_shape_file = 'model_input_shapefiles/Agg_mod_contiguous_v24.shp'
        output_plot_path = 'plots_of_groups/FR_v24_group_%s.png'
        output_definition_path = 'group_shapefiles/group_definition_shapefile_v24_FR.shp'
        output_connectivity_path = 'group_shapefiles/group_connectivity_shapefile_v24_FR.shp'

    else:
        group_definition_file   = 'group_definitions/control_volume_definitions_FR.txt'
        group_connectivity_file = 'group_definitions/connectivity_definitions_FR.txt'
        polygon_shape_file = 'model_input_shapefiles/Agg_mod_contiguous.shp'
        output_plot_path = 'plots_of_groups/FR_group_%s.png'
        output_definition_path = 'group_shapefiles/group_definition_shapefile_FR.shp'
        output_connectivity_path = 'group_shapefiles/group_connectivity_shapefile_FR.shp'

# for AGG runs (includs now whole bay group added by allie)
else:
    if v24:
        group_definition_file   = 'group_definitions/control_volume_definitions_v24_141.txt'
        group_connectivity_file = 'group_definitions/connectivity_definitions_v24_141.txt'
        polygon_shape_file = 'model_input_shapefiles/Agg_mod_contiguous_v24-agg141.shp'
        output_plot_path = 'plots_of_groups/AGG_v24_group_%s.png'
        output_definition_path = 'group_shapefiles/group_definition_shapefile_v24_AGG.shp'
        output_connectivity_path = 'group_shapefiles/group_connectivity_shapefile_v24_AGG.shp'
    else:
        group_definition_file   = 'group_definitions/control_volume_definitions_141.txt'
        group_connectivity_file = 'group_definitions/connectivity_definitions_141.txt'
        polygon_shape_file = 'model_input_shapefiles/Agg_mod_contiguous_141.shp'
        output_plot_path = 'plots_of_groups/AGG_group_%s.png'
        output_definition_path = 'group_shapefiles/group_definition_shapefile_AGG.shp'
        output_connectivity_path = 'group_shapefiles/group_connectivity_shapefile_AGG.shp'




########################################################################################
# import python packages
########################################################################################

import sys, os
import pandas as pd
import numpy as np
import matplotlib.pylab as plt
import geopandas as gpd
from shapely.geometry import LineString

###########################################################################################
# load dictionaries that define the groups (A, B, C, etc.) by the list of control volumes
# that make up each group (group_dict) and the list of pairs of control volumes making up
# fluxes out of the N, S, E, and W faces of each group (flux_pairs_dict)
###########################################################################################

# read from text file a dictionary grouping control volumes into lettered groups 
# format:
#   GROUP_NAME : CV1, CV2, CV3, ...
# where:
#   GROUP_NAME = name of group
#   CV1, CV2, CV3, ... = numbers of control volumes comprising the group
group_dict = {}
with open(group_definition_file,'r') as f: 
    for line in f.readlines():
        # split line at ':' into key and control volume list, dropping newline character first
        (key, val) = line.rstrip('\n').split(':')  
        # remove whitespace surrounding key 
        key = key.strip()
        # add list to dictionary
        print(key)
        group_dict[key] = eval(val) 
      
        
# read from text file a dictionary specifying all the fluxes between 
# control volumes making up fluxes from each lettered group to the north, 
# south, east, and west
# format:
#   LETTER2DIRECTION : [[CVf,CVt]_1, [CVf,CVt]_2, [CVf,CVt]_3, ...]
# where:
#   LETTER = name of group
#   DIRECTION = N, S, E, or W stand for "to the north", south, east, or west, respectively
#   [CVf, CVt]_i = defines a flux from control volume CVf to control volume CVt
#   where i = 1, 2, 3, ... make up all the fluxes for a particular group/direction pair
flux_pairs_dict = {}
with open(group_connectivity_file,'r') as f: 
    for line in f.readlines():
        # split line at ':' into key and connectivity volume list, dropping newline character first
        (key, val) = line.rstrip('\n').split(':') 
        # trim whitespace around key
        key = key.strip()
        # add list to dictionary
        flux_pairs_dict[key] = eval(val)

# load polygon shapefile as geopandas dataframe
gdf_poly = gpd.read_file(polygon_shape_file)

# add the centroid of the polygon
xc = []
yc = []
for point in gdf_poly.centroid:
    xy = point.coords.xy
    xc.append(xy[0][0])
    yc.append(xy[1][0])
gdf_poly['xc'] = xc
gdf_poly['yc'] = yc

# initialize a dataframe to contain the groups and their connectivities
df_group = pd.DataFrame(columns=['geometry','feature'])
df_connect = pd.DataFrame(columns=['geometry','feature'])

# loop through the groups
for group in group_dict.keys():

    # get list of polygons that comprise the group and merge into one
    poly_list = group_dict[group]
    group_poly = gdf_poly.iloc[poly_list].dissolve()

    # add the group polygon to the list of features
    df_group = df_group.append({'feature' : group, 
                                'geometry' : group_poly.iloc[0].geometry}, 
                                ignore_index=True)

# convert to geodataframe
gdf_group = gpd.GeoDataFrame(df_group)

# print
print('Finished creating geodataframe with aggregated groups...')

# loop through the groups again
for group in group_dict.keys():

    # print
    print('Compiling connections for group %s...' % group)

    # boundary of the polygon corresponding to this group
    group_bound = gdf_group.loc[gdf_group['feature']==group].geometry.values[0].boundary

    # if the boundary is a multilinestring, that means there are islands inside, so take 
    # just the longest line string, representing the outer polygon
    if group_bound.type == 'MultiLineString':
        maxlen = 0
        maxline = None
        for line in list(group_bound.geoms):
            if line.length > maxlen:
                maxlen = line.length
                maxline = line
        group_bound = maxline

    # get the unique coordinates of the outer polygon, in clockwise order (note the starting
    # point is arbitrary)
    group_coords = list(group_bound.coords)[0:-1]

    # now get the list of connectivities for this group (these have names like 'A to N' 
    # or 'A to W' for group 'A')
    connectivity_list = []
    for key in flux_pairs_dict.keys():
        if group == key[0:len(group)]:
            if (group + ' to ') in key:
                connectivity_list.append(key)

    # loop through the connectivity keys 
    for connectivity in connectivity_list:

        # print
        print('Working on connectivity %s ...' % connectivity)

        # get the list of polygon pairs defining the connectivity
        flux_pairs = flux_pairs_dict[connectivity]

        # if list is empty, pass
        if len(flux_pairs) > 0:

            # get the list of point coordinates that make up the connection lines
            coord_list = []
            for flux_pair in flux_pairs:

                # get the to and from polygons designated by this flux pair
                poly1 = gdf_poly.iloc[flux_pair[0]].geometry
                poly2 = gdf_poly.iloc[flux_pair[1]].geometry

                # find the intersection of the flux pair polygons
                inter = poly1.intersection(poly2)

                # add all the lines comprising the intersection to the list of lines
                if inter.type=='LineString':
                    for coord in inter.coords:
                        coord_list.append(coord)
                elif inter.type=='MultiLineString':
                    for line in list(inter.geoms):
                        for coord in line.coords:
                            coord_list.append(coord)
                else:
                    raise Exception('intersection between polygons %d and %d is not a line' % (flux_pair[0],flux_pair[1]))

            # eliminate repeats
            coord_list = list(set(coord_list))

            # number of coordinates in list
            ngc = len(group_coords)
            ncc = len(coord_list)

            # check the list of coordinates comprising the group, and if the first, last, 2nd, or 2nd to last
            # point is in our list of boundary coordinates, put the last point in the front of the list to rotate
            # them around the polygon
            if ngc-ncc>=4:
                while ((group_coords[0] in coord_list) or (group_coords[1] in coord_list) 
                                                  or (group_coords[-1] in coord_list) 
                                                  or (group_coords[-2] in coord_list)):
                    group_coords.insert(0,group_coords.pop())
            elif ngc-ncc>=2:
                while ((group_coords[0] in coord_list) or (group_coords[-1] in coord_list)):
                    group_coords.insert(0,group_coords.pop())
                print('Group has >=2 but <4 points outside this connection...')
            else:
                print('Group has <2 points outside this connection...')
                break

            # now sort the coordinate list in order of the group coordinates
            coord_list_sorted = [gc for gc in group_coords if gc in coord_list]

            # merge coordinates into a line
            merged_line = LineString(coord_list_sorted)

            # add the line defining the connectivity to the dataframe
            df_connect = df_connect.append({'feature' : connectivity, 
                                        'geometry' : merged_line}, 
                                        ignore_index=True)


# convert to geodataframe
gdf_connect = gpd.GeoDataFrame(df_connect)

# plot and save to make sure it looks ok
for group in gdf_group.feature:

    # find indices of group and its connections
    igroup = np.argmax(gdf_group.feature==group)
    iconnect = []
    for i in range(len(gdf_connect.feature)):
        if gdf_connect.feature.values[i][0:(len(group)+4)] == ('%s to ' % group):
            iconnect.append(i)

    # plot the group 
    fig, ax = plt.subplots(figsize=(20,20))
    fig.tight_layout()

    # first plot the polygons w/ numbers in the background
    gdf_poly.boundary.plot(ax=ax,edgecolor='lightgray')
    for i in range(len(gdf_poly)):
        ax.text(gdf_poly.iloc[i].xc, gdf_poly.iloc[i].yc, '%d' % i, color='lightgray')

    # add the group polygon
    gdf_group.iloc[igroup:igroup+1].plot(ax=ax)

    # plot outlines of all groups in the shapefile 
    gdf_group.boundary.plot(ax=ax, edgecolor='k')
    ax.axis('off')

    # plot the connection boundaries and label centroids
    if len(iconnect) > 0:
        color_list = ['b','g','gold','c','m']
        count=0
        for i in iconnect:

            # centroid
            xc,yc = gdf_connect.iloc[i].geometry.centroid.xy
            xc=xc[0]
            yc=yc[0]

            # get the first and last coordinates of the line
            line = gdf_connect.iloc[i].geometry
            if line.type == 'LineString':
                line1 = line
                line2 = line
            elif line.type == 'MultiLineString':
                line1 = list(line.geoms)[0]
                while line1.type == 'MultiLineString':
                    line1 = list(line1.geoms)[0]
                line2 = list(line.geoms)[-1]
                while line2.type == 'MultiLineString':
                    line2 = list(line2.geoms)[-1]
            x1, y1 = line1.coords[0]
            x2, y2 = line2.coords[-1]
            angle = np.arctan2(x2-x1, y1-y2)*180/np.pi

            # plot the connection and add a text arrow pointing out
            label = gdf_connect.iloc[i].feature.split(' to ')[1]
            gdf_connect.iloc[i:i+1].plot(ax=ax, color=color_list[count])
            bbox_props = dict(boxstyle='rarrow',fc='w',ec=color_list[count])
            t = ax.text(xc,yc,label,ha='center',va='center',rotation=angle,bbox=bbox_props)
            count = count+1

    # add title and save
    ax.set_title('group ' + group)
    ax.axis('off')
    plt.savefig(output_plot_path % group)

    # zoopm in and save again
    xpoly, ypoly = gdf_group.iloc[igroup]['geometry'].exterior.xy
    minx = np.min(xpoly)
    maxx = np.max(xpoly)
    dx = maxx - minx
    miny = np.min(ypoly)
    maxy = np.max(ypoly)
    dy = maxy - miny
    zoom_box = (minx - dx, maxx + dx, miny - dy, maxy + dy)
    ax.axis(zoom_box)
    plt.savefig(output_plot_path % ('%s_%s' % (group,'ZOOM')))



# now concatenate groups and connectivities and save in a shapefile
gdf_group.to_file(output_definition_path)
gdf_connect.to_file(output_connectivity_path)