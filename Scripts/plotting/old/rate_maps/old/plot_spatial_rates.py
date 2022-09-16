# -*- coding: utf-8 -*-
"""
Created on Mon Feb  1 11:48:47 2021

This script is made to help generate rate plots of the aggregated polygons 
and potentially show (a) our new agg polygons ... or other shape files on top?
up to the user. 

@author: siennaw
"""
# h:\hpcshared\NMS_Projects\Control_Volume_Analysis\Balance_Tables\FR17_003\
water_year  = 'WY2017'
run_name    = 'FR17_003'
pdf_label   = 'Sett_DNit_Map'
interval = 7    # Interval (#days between each plot)



from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
plt.switch_backend('Agg')
from matplotlib.backends.backend_pdf import PdfPages
try:
    import geopandas as gpd
except:
    raise Exception('\n' + 
          'ERROR: this Python environment does not include geopandas.\n' + 
          'To load environment with geopandas, exit Python, execute the\n' + 
          'following at the command line:\n' + 
          '    source activate /home/zhenlin/.conda/envs/my_root\n' + 
          'and then re-launch Python.\n')

# Make PDF file name     
pdffile = '/richmondvol1/hpcshared/NMS_Projects/Control_Volume_Analysis/Plots/%s/%s_%s.pdf' % (run_name, pdf_label, run_name)

# Read in the shapefile 
polys   = gpd.read_file(r'/richmondvol1/hpcshared/inputs/shapefiles/Agg_mod_contiguous_plus_subembayments_shoal_channel.shp')
agg     = gpd.read_file(r'/richmondvol1/hpcshared/NMS_Projects/Control_Volume_Analysis/Definitions/shapefiles/AggregatedControlVolumes.shp')  


#################################
# /// Read in different rates /// 
################################# 
# Primary production / production rate
primary_table = pd.read_csv(r'/richmondvol1/hpcshared/NMS_Projects/Control_Volume_Analysis/Balance_Tables/%s/diat_Table.csv' % (run_name))
primary_table['SUB'] = primary_table['Diat,dPPDiat']
pri_label = 'Primary Production (dPPDiat), g/m$^3$/day'

# Dentrification 
denit_table = pd.read_csv(r'/richmondvol1/hpcshared/NMS_Projects/Control_Volume_Analysis/Balance_Tables/%s/no3_Table.csv' % (run_name))
denit_table['SUB'] =  denit_table['NO3,dDenitWat'] + denit_table['NO3,dDenitSed']
denit_label = 'Nitrogen loss through denitrification, g/m$^3$/day'


# Settling of organic matter --> composite, so a little trickier 
pon1_table      = pd.read_csv(r'/richmondvol1/hpcshared/NMS_Projects/Control_Volume_Analysis/Balance_Tables/%s/pon1_Table.csv' % (run_name))
settling_table  = pon1_table.merge(primary_table, on = ['time', 'Control Volume', 'Volume']) 
settling_table['SUB'] = settling_table['Diat,dSedDiat']*0.15 + settling_table['PON1,dSedPON1']
sett_label = 'Settling organic matter (N-diat + PON1), g/m$^3$/day'

# # Nitrification
# table   = pd.read_csv(r'/richmondvol1/hpcshared/Full_res/Control_Volume_Analysis/WY2017/FR17_003/nh4_Table.csv')
# SUB     = 'NH4,dNitrif'
# label   = 'Nitrification, mg/m$^3$/day'
# pdffile = '/richmondvol1/hpcshared/Full_res/Control_Volume_Analysis/WY2017/FR17_003/nitrification_map_17.pdf'

# # Calculate residence time 
# cont  = pd.read_csv(r'/richmondvol1/hpcshared/Full_res/Control_Volume_Analysis/%s/%s/continuity_Table.csv' % (water_year, run_name))
# cont['Net'] = cont['Continuity,Transp out'] + cont['Continuity,Transp in']
# cont['ResTime'] =  np.abs(cont['Net'] / cont['Volume']) * 24 # Residence time in hours


# We just want the first 146 polygons (the other are weird aggregated, larger polygons)
NPolys  = 146

# Gather dates in the table and sort the dates chronologically 
dates = list(set(primary_table.time))
Dates = pd.to_datetime(dates)
index = np.argsort(dates)
dates = [dates[i] for i in index ]
dates = dates[50:-1]


#################################
# /// Functions for plotting  /// 
################################# 
# (1) clean axis & plot the aggregated groups on top... 
def clean_axis(axis, date):
    axis.xaxis.set_visible(0)
    axis.yaxis.set_visible(0)
    axis.axis('equal')
    axis.set_title(date, fontsize = 25)
    axis.set_frame_on(False)
    agg.boundary.plot(ax = axis, color = 'slategray')

# (2) make a color bar w/ defined vmax and label ... 
def make_colorbar(MAX, cmap_str, axis, label):
    norm = matplotlib.colors.Normalize(0, MAX)
    cmapp = matplotlib.cm.ScalarMappable(norm= norm, cmap= cmap_str)
    cmapp.set_array([])   # we need this line with our old HPC Python... 
    cb = plt.colorbar(cmapp, ax = axis, shrink = 0.6)
    cb.ax.tick_params(labelsize = 14)
    cb.set_label(label, fontsize = 14)

# (4) index into a dataframe to normalize some mass value by volume & define the max value @ timestamp
def load_substance(table, date, SUB):
    values = table.loc[table.time == date,['Control Volume', SUB, 'Volume']]
    values[SUB] = values[SUB].values / values['Volume'].values  # normalize by volume 
    MAX = np.max(values[SUB].values)
    return values, MAX 

# (5) index into a dataframe to extract a value of (1) polygon
def val_at_poly(values, poly_num, SUB):
    return values.loc[values['Control Volume'] == 'polygon%d' % poly_num, SUB].values
      


#%%

'''
The weird set-up here is designed to speed up our loops. Originally we plotted w/ geopandas
but that took a lifetime. Now we take advantage of the relative speedier matplotlib polygon
library. In order to do this, we intialize our polygons on a figure, and then assign values
for the colors in a loop. This way we don't have to draw everything over and over again. 
'''

# Make a list of all the polygons we want to plot 
skip    = [i for i in range(118, 136)] # these are in the ocean so we are skipping them
polys2plot = [i for i in range(NPolys) if i not in skip] 
patches =  [polys.geometry[i]  for i in polys2plot]  # collection of polygon geometries 

# Another weird loop. Here we go through and convert all our polygons to objects matplotlib likes
Patches = [Polygon(np.asarray(poly.exterior)) for poly in patches] 
        
# Create patch collection   
patches0 = PatchCollection(Patches, facecolor='white', edgecolor='face')
patches1 = PatchCollection(Patches, facecolor='white', edgecolor='face')
patches2 = PatchCollection(Patches, facecolor='white', edgecolor='face')

#################################
# ////// MAKE PLOT !  //////////
################################# 
fig, ax = plt.subplots(nrows = 1, ncols = 3, sharex = False, sharey = False, figsize=(24,10))

# Add patches to plot
p0 = ax[0].add_collection(patches0)
p1 = ax[1].add_collection(patches1)
p2 = ax[2].add_collection(patches2)

# If you don't do this your plot will be tiny and weird
ax[0].autoscale_view()
ax[1].autoscale_view()
ax[2].autoscale_view()

# Set colormaps for each axis
p0.set_cmap('Spectral_r')
p1.set_cmap('Spectral_r')
p2.set_cmap('Spectral_r')
 
# Fixed max values for each substance #<<<<<<<<< customize ! 
MAXtime = 8 
dppMax  = 0.06
dMax    = 0.015
settMax = 0.005

# Set the clim for each axis       #%%%%%%%%%%%% UPDATE $$$$$$$$$$$
p0.set_clim(0, dppMax)
p1.set_clim(0, dMax)
p2.set_clim(0, MAXtime)

# Make colorbars for each axis       #%%%%%%%%%%%% UPDATE $$$$$$$$$$$
make_colorbar(dMax,     'Spectral_r',   ax[1],  denit_label)
make_colorbar(MAXtime,  'summer_r'  ,   ax[2],  'HOURS')
make_colorbar(dppMax,  'Spectral_r',   ax[0],  pri_label)
   
# Now the part of the plot that will change w/ each loop...          
print('PDF == %s' % pdffile)
with PdfPages(pdffile) as pdf: 
    # Loop through dates 
    for i,date in enumerate(dates):
        if i % interval == 0 :      # daily plots would be a bit much
            
            arr0 = []
            arr1 = []
            arr2 = [] 
    
            # Select all the data @ that date #%%%%%%%%%%%% UPDATE $$$$$$$$$$$
            denit, _ = load_substance(denit_table,   date, 'SUB') 
            dpp  , _ = load_substance(primary_table, date, 'SUB')
            sett , _ = load_substance(settling_table,date, 'SUB')
            
            # Extract residence time 
            # cont_values = cont.loc[cont.time == date,['Control Volume','ResTime']]
            # MAXtime = np.max(cont_values['ResTime']) 
    
            
            # Generate values for all the polygons 
            for i in polys2plot: 
                arr0.append(val_at_poly(dpp, i, 'SUB')) 
                arr1.append(val_at_poly(sett, i, 'SUB')) #%%%%%%%%%%%% UPDATE $$$$$$$$$$$
                arr2.append(val_at_poly(denit, i, 'SUB'))

            # Convert values to a 1-D array that we can feed to a colormap
            arr0 = np.ravel(np.array(arr0))
            arr1 = np.ravel(np.array(arr1))
            arr2 = np.ravel(np.array(arr2)) 
            
            # Set colors for the plot 
            arr0 = arr0.clip(0, dppMax)
            p0.set_array(arr0)
            p1.set_array(arr1)
            p2.set_array(arr2)
  
            # Make axes invisible for cleaner plot #%%%%%%%%%%%% UPDATE $$$$$$$$$$$
            clean_axis(ax[1], '%s (%s)' % (date, sett_label))
            clean_axis(ax[2], '%s (%s)' % (date, 'Denitrification'))
            clean_axis(ax[0], '%s (%s)' % (date, 'DPP (Primary Production)'))
            # clean_axis(ax[2], 'Residence Time')
            
            fig.canvas.draw()
            pdf.savefig(dpi = 100, bbox_inches='tight')
            print('Done %s' % date)
            
print('DONE')
plt.close()



   

