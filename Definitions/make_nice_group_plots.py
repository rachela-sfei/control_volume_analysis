'''
this script makes plots of the "groups" for presentations and manuscripts
'''

import sys, os
import pandas as pd
import numpy as np
import matplotlib.pylab as plt
import geopandas as gpd

figure_width = 8.5

FR_or_AGG = 'FR'
#FR_or_AGG = 'AGG'


gdf = gpd.read_file('group_shapefiles/group_definition_shapefile_%s.shp' % FR_or_AGG)
if FR_or_AGG=='FR':
    gdf_outline = gpd.read_file('model_input_shapefiles/Grid_Outline.shp')
else:
    gdf_outline = gpd.read_file('model_input_shapefiles/Grid_Outline_141.shp')


for domain_name in ['Whole_Bay_ABC','WB_South_Bay_ABC','WB_Subembayments',
                    'WB_Channel_Shoal','RMP_Subembayments','RMP_Channel_Shoal',
                    'WB_and_RMP_Subembayments','WB_and_RMP_Channel_Shoal']:

    # set default font size (gets overridden for some domain names)
    fs =16

    if domain_name == 'WB_Subembayments_Exact':

        group_list = ['Lower_South_Bay_WB_FR', 'South_Bay_WB_FR','Central_Bay_WB_FR', 'San_Pablo_Bay_WB_FR', 'Carquinez_WB_FR','Suisun_WB_FR'] 

    if domain_name == 'RMP_Subembayments_Exact':
       
       group_list = ['Lower_South_Bay_RMP_FR', 'South_Bay_RMP_FR','Central_Bay_RMP_FR', 'San_Pablo_Bay_RMP_FR', 'Suisun_RMP_FR']

    if domain_name == 'Whole_Bay_ABC':
        
        group_list = ['L','K','J','I','H','G','F','E','D','C','B','A','V','U1','T1','S1','U2','T2','S2','X','W','Z','Y',
                      'RB','Alcatraz_Whirlpool','CB_East_Exchange','Y2','Berkeley_Marina','Larkspur_Ferry',
                      'SE_San_Pablo_Shoal','San_Pablo_Channel','San_Pablo_Shoal','San_Pablo_Exchange',
                      'Stockton_Channel_Suisun_Bay','Sacramento_Channel','Roe_Island','Chipps_Island','Grizzly_Bay',
                      'Suisun_Slough','Suisun-Fairfield','Squiggly_Creek','LSB']
        fs=12

    if domain_name == 'WB_South_Bay_ABC':
    
    
        # list of the groups to plot
        group_list = ['L','K','J','I','H','G','F','E','D','C','B','A','V','U1','T1','S1','U2','T2','S2','X','W','Z','Y']
        
   
    elif domain_name == 'WB_Subembayments':
    
        # dictionary with coordinates of center arrows along with the name of the corresponding group
        group_list = ['Suisun_Bay', 'San_Pablo_Bay', 'Central_Bay_WB', 'SB_WB', 'LSB']
    
    
    elif domain_name == 'WB_Channel_Shoal':
    
    
        # dictionary with coordinates of center arrows along with the name of the corresponding group
        group_list = ['Suisun_Bay', 'San_Pablo_Channel', 'San_Pablo_Exchange', 'San_Pablo_Shoal',
                      'SE_San_Pablo_Shoal', 'Central_Bay_WB', 'SB_WB_west_shoal', 
                      'SB_WB_east_shoal','SB_WB_channel', 'LSB']
    
    elif domain_name == 'RMP_Subembayments':

        # dictionary with coordinates of center arrows along with the name of the corresponding group
        group_list = ['Suisun_Bay', 'San_Pablo_Bay', 'Central_Bay_RMP', 'SB_RMP', 'LSB']
    
    elif domain_name == 'RMP_Channel_Shoal':
    
        # dictionary with coordinates of center arrows along with the name of the corresponding group
        group_list = ['Suisun_Bay', 'San_Pablo_Channel', 'San_Pablo_Exchange', 'San_Pablo_Shoal',
                      'SE_San_Pablo_Shoal', 'Central_Bay_RMP', 'SB_RMP_west_shoal', 
                      'SB_RMP_east_shoal','SB_RMP_channel', 'LSB']
    
    elif domain_name == 'WB_and_RMP_Subembayments':

        # dictionary with coordinates of center arrows along with the name of the corresponding group
        group_list = ['Suisun_Bay', 'San_Pablo_Bay', 'Central_Bay_WB', 'SB_WB_north_half', 'SB_WB_south_half', 'LSB']
    
    
    elif domain_name == 'WB_and_RMP_Channel_Shoal':
    
    
        # dictionary with coordinates of center arrows along with the name of the corresponding group
        group_list = ['SB_WB_west_shoal_north_half','SB_WB_west_shoal_south_half',
                      'SB_WB_east_shoal_north_half','SB_WB_east_shoal_south_half',
                          'SB_WB_channel_north_half','SB_WB_channel_south_half']

    # select subset of geodataframe corresponidng to the list of groups in this set
    nf = len(gdf)
    ind = np.zeros(nf, dtype=bool)
    for i in range(nf):
        ind[i] = gdf.iloc[i]['feature'] in group_list
    gdf1 = gdf.loc[ind]

    # calculate centroids
    centroids = gdf1.centroid.values
    xc = []
    yc = []
    for point in centroids:
        xy = point.xy
        xc.append(xy[0][0])
        yc.append(xy[1][0])
    features = gdf1['feature'].values

    # make a figure
    fig, ax = plt.subplots()
    gdf1.plot(ax=ax,color='lightblue',edgecolor='blue')


    # set figure size proporitonal to axis dimensions
    ax.axis('tight')
    axlim = ax.axis()
    figure_height = 0.8*figure_width * (axlim[3]-axlim[2])/(axlim[1]-axlim[0])
    fig.set_size_inches(figure_width, figure_height)
    ax.axis('off')
    ax.axis('equal')
    axlim = ax.axis()
    gdf_outline.boundary.plot(ax=ax,edgecolor='blue')
    ax.axis(axlim)
    fig.tight_layout(rect=[0, 0.03, 1, 0.98])
    
    # add title
    ax.set_title(domain_name,fontsize=fs)

    # save
    plt.savefig('nice_group_plots/%s_Group_Map_%s_No_Labels.png' % (FR_or_AGG,domain_name))

    # add group names, nudging some of them a bit for readability
    for i in range(len(xc)):

        # calculate nudge
        xn = 0
        yn = 0
        if features[i]=='Alcatraz_Whirlpool':
            yn = 2000
        if features[i]=='Sacramento_Channel':
            yn = 2000
        if features[i]=='SB_RMP_channel':
            yn = 500
        if features[i]=='SB_WB_east_shoal_north_half':
            yn = 500
        if features[i]=='SB_WB_east_shoal':
            yn = 500
        if features[i]=='Squiggly_Creek':
            xn = 4000
        if features[i]=='Suisun_Slough':
            yn = 2000

        # add text to figure
        plt.text(xc[i]+xn,yc[i]+yn,features[i],fontsize=fs,ha='center')

    # save again
    plt.savefig('nice_group_plots/%s_Group_Map_%s_With_Labels.png' % (FR_or_AGG,domain_name))




    plt.close()