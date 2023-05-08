# -*- coding: utf-8 -*-
"""
Created on Tue May  7 12:01:06 2019
Generating subembayments grid from a shapefile of polygons. 
@author: zhenlinz
"""

import numpy as np
import geopandas as gpd
import matplotlib.pylab as plt

CV_fn = 'Agg_mod_contiguous.shp'
EL_fn = 'Agg_exchange_lines.shp'
CV_fig_fn = 'Agg_mod_contiguous.png'
EL_fig_fn = 'Agg_exchange_lines.png'

# read shapefiles  
CV_gpd = gpd.read_file(CV_fn)
EL_gpd = gpd.read_file(EL_fn)
           
# plot control volumes, including their numbers
fig, ax = plt.subplots(figsize=(24,18))
CV_gpd.plot(ax=ax,color='w',edgecolor='b')
EL_gpd.plot(ax=ax,edgecolor='r')
for i in range(len(CV_gpd)):
    g = CV_gpd.iloc[i].geometry
    plt.text(g.centroid.x,g.centroid.y,'%d' % i,verticalalignment='center',horizontalalignment='center')
plt.savefig(CV_fig_fn)
       
# plot exchange lines, including their numbers
fig, ax = plt.subplots(figsize=(24,18))
CV_gpd.plot(ax=ax,color='w',edgecolor='b')
EL_gpd.plot(ax=ax,edgecolor='r')
for i in range(len(EL_gpd)):
    g = EL_gpd.iloc[i].geometry
    plt.text(g.centroid.x,g.centroid.y,'%d' % i,verticalalignment='center',horizontalalignment='center')
plt.savefig(EL_fig_fn)
           
        
    
    

    
 
 
 
    
