# -*- coding: utf-8 -*-
"""
Created on Mon Feb  1 11:48:47 2021

This script is designed to make 2x3 grid plots for the RMP report
I am trying to set this up to be relatively flexible depdning on the normalization scheme
you want to use + the parameter you want to plot.



@author: siennaw
"""



from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import cmocean
import numpy as np
plt.switch_backend('Agg')
import os 
from matplotlib.backends.backend_pdf import PdfPages


# I moved a lot of extra pieces of this script (defs/functions) to an auxiliary file
try:
    import geopandas as gpd
except:
    raise Exception('\n' + 
          'ERROR: this Python environment does not include geopandas.\n' + 
          'To load environment with geopandas, exit Python, execute the\n' + 
          'following at the command line:\n' + 
          '    source activate /home/zhenlin/.conda/envs/my_root\n' + 
          'and then re-launch Python.\n')
print('LOADING!?')


# path to shapefiles defining polygons and transects for the monitoring regions
# (make sure these are the same ones used to initialize the DWAQ run)




###################
## USER INPUT
###################

# path to folder that contains run folders, which in turn contain model output including dwaq_hist.nc 
# and *-bal.his files. if there are no run subfolders, this is the direct path to dwaq_hist.nc and *-bal.his
# path = '../'


# Agg141_wy14to18_125 and _147; FR13_003,_021;
#  FR17_003 x, 014 X,  !015; FR18_003, 004.


agg = False
run_name = 'FR13_021'
water_year = 'WY2013'

if agg:  
    base_path = r'/richmondvol1/hpcshared/Grid141/WY13to18//'
    shpfn_poly =  '/richmondvol1/hpcshared/inputs/shapefiles/Agg_mod_contiguous_141.shp'
    shpfn_tran = '/richmondvol1/hpcshared/inputs/shapefiles/Agg_exchange_lines_141.shp'

else:
    base_path = r'/richmondvol1/hpcshared/NMS_Projects/Control_Volume_Analysis/Balance_Tables/'
    shpfn_poly = r'/richmondvol1/hpcshared/inputs/shapefiles/Agg_mod_contiguous_plus_subembayments_shoal_channel.shp'


# Read in the shapefile 
polys   = gpd.read_file(shpfn_poly) 
# transects     = gpd.read_file(shpfn_tran) 




# ///////////////////////////////////// 
base_run = 'Base (#125)'

# zoop_grazing, Denit, DPP , oxygen_consumption 'DPP', 'zoop_grazing', 
params2plot = ['nitrogen_assimilation', 'oxygen_consumption', 'Denit', 'zoop_grazing', 'DPP']

# What normalization scheme you want to use for the data ('Area', 'Volume')
NORM = 'Area'

denit_label = 'Nitrogen loss through denitrification, g/m$^3$/day'

# Cmocean colormap! 
cmap = cmocean.cm.deep
cmap_diff = cmocean.cm.balance


# Make output directory 
output_dir = r'/richmondvol1/hpcshared/NMS_Projects/Control_Volume_Analysis/Plots/' 
output_dir = '/%s/%s//' % (output_dir, run_name)
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
    print('Made %s' % output_dir)


# --------------------------------------------------------------------------
print('Making plots for %s \n' % run_name)

# --------------------------------------------------------------------------
# Define all the parameters + units / etc with dictionaries 
param = 'DPP'

incl_green = True # set to True for 6 year agg grid runs based off Run 125 and related

param2name = {'DPP' : 'DPP',
              'Denit' : 'Denitrification',
              'zoop_grazing' : 'Algae consumption by zoop',
              'oxygen_consumption' : 'Oxygen Consumption',
              'nitrogen_assimilation' : 'Nitrogen Assimilation'}

param2max = { 'DPP' :  0.6,
              'Denit' : 0.05,
              'zoop_grazing' : 0.1,
              'oxygen_consumption' : 1,
              'nitrogen_assimilation' : 0.05} 

param2percentagerange = {'DPP' :  2,
              'Denit' : 0.2,
              'zoop_grazing' : 1.5,
              'oxygen_consumption' : 1.1,
              'nitrogen_assimilation' : 0.5} 

units = {} 
units.update(dict.fromkeys(['zoop_grazing', 'DPP'], 'gC'))
units.update(dict.fromkeys(['Denit', 'nitrogen_assimilation']  , 'gN'))
units['oxygen_consumption'] = 'gO'

def param2unit(param, NORM):
    if NORM == 'Area' :
        per = 'm$^2$'
    elif NORM == 'Volume':
        per = 'm$^3$'
    else:
        assert(False)
    unit = '%s/%s/day' % (units[param], per)
    return unit 

def normalize_data(df, NORM):
    ''' Extract normalization factor from the dataset''' 
    print('NORMALIZING BY: %s \n\n' % NORM)
    if NORM == 'Volume':
        V = df['Volume'].values
    elif NORM =='Area':
        V = df['Area'].values 
    elif NORM =='None':
        V = df['Area'].values*0 + 1
    return V 
               


# --------------------------------------------------------------------------                       
########################################
# /// Read in different rates + runs /// 
######################################## 
DATA = {}            
   

    
# Primary production / production rate
filename = os.path.join(base_path, run_name, 'diat_Table.csv')
primary_table = pd.read_csv(filename)

# Get normalization factor 
norm = normalize_data(primary_table, NORM)

# PM addition -- need to add "Greens" for Agg Grid 125 and later
try:
    filename = os.path.join(base_path, run_name, 'green_Table.csv')
    primary_table_g = pd.read_csv(filename)
except:
    incl_green = False 
# Denitrification 
filename = os.path.join(base_path, run_name,  'no3_Table.csv')
no3_table = pd.read_csv(filename)

 # Ammonium 
filename = os.path.join(base_path, run_name,  'nh4_Table.csv')
nh4_table = pd.read_csv(filename)

# Oxygen Consumption 
filename = os.path.join(base_path, run_name,  'oxy_Table.csv')
oxy_table = pd.read_csv(filename)

# Nitrogen Assimilation 
no3_table['na_1'] = no3_table[["NO3,dDenitWat","NO3,dNitrif","NO3,dDenitSed","NO3,dNiDen", "NO3,dNO3Upt"]].sum(axis=1)
nh4_table['na_2'] = nh4_table[["NH4,dMinPON1","NH4,dMinDON","NH4,dNitrif","NH4,dMinDetNS1",
                                   "NH4,dMinDetNS2","NH4,dZ_NRes","NH4,dNH4Aut","NH4,dNH4Upt"]].sum(axis=1)

# Normalize data 
no3_table['Denit']                  = abs(no3_table['NO3,dDenitWat'] + no3_table['NO3,dDenitSed']) / norm
primary_table['DPP']                = primary_table['Diat,dPPDiat'] / norm
primary_table['zoop_grazing']       = abs(primary_table['Diat,dZ_Diat']) / norm  # Grazing of diatoms by zoop

if incl_green:
    primary_table['DPP']                = primary_table['DPP'] + (primary_table_g['Green,dPPGreen'] / norm )
    primary_table['zoop_grazing']       = primary_table['zoop_grazing'] + abs(primary_table_g['Green,dZ_Grn']) / norm  # Grazing of greens by zoop

oxy_table['oxygen_consumption']     = abs(oxy_table['OXY,dOxCon'] + oxy_table['OXY,dMinDetCS1']) / norm 
no3_table['nitrogen_assimilation']  = abs(no3_table['na_1'] + nh4_table['na_2']) / norm

# Save norm for weighting data 
no3_table['norm']     = norm
primary_table['norm']   = norm
oxy_table['norm']       = norm

# Save data for each run in dictionary
DATA[run_name + 'Denit']    = no3_table
DATA[run_name + 'DPP']      = primary_table
DATA[run_name + 'time']     = pd.to_datetime(no3_table.time.values) 
DATA[run_name + 'zoop_grazing'] = primary_table
DATA[run_name + 'oxygen_consumption'] = oxy_table
DATA[run_name + 'nitrogen_assimilation'] = no3_table

# --------------------------------------------------------------------------                       

###########################################
# /// Seasons / times we want to average /// 
###########################################             


def get_time_windows(water_year):
    time_windows = {} 
    year = int(water_year.replace('WY',''))  # Strip year from string 
    time_windows['Winter (%s)' % water_year] = ['%d-10-01' % (year-1),'%d-02-01' % year]
    time_windows[water_year] = ['%d-10-01' % (year-1),'%d-10-01' % year]
    time_windows['Growing Season (%s)' % water_year] = ['%d-02-01' % (year),'%d-10-01' % year]
    return time_windows 


           
# water_years = ['WY2018', 'WY2017' , 'WY2015', 'WY2016', 'WY2013' , 'WY2014'] 

# time_windows = {'Winter (WY2015)'         : ['2014-10-01','2015-02-01'],
#                 'Growing Season (WY2015)' : ['2015-02-01','2015-10-01'],
#                 'Winter (WY2013)'         : ['2012-10-01','2013-02-01'],
#                 'Growing Season (WY2013)' : ['2013-02-01','2013-10-01'],
#                 'Winter (WY2014)'         : ['2013-10-01','2014-02-01'],
#                 'Growing Season (WY2014)' : ['2014-02-01','2014-10-01'],
#                 'Winter (WY2016)'         : ['2015-10-01','2016-02-01'],
#                 'Growing Season (WY2016)' : ['2016-02-01','2016-10-01'],
#                 'Winter (WY2017)'         : ['2016-10-01','2017-02-01'],
#                 'Growing Season (WY2017)' : ['2017-02-01','2017-10-01'],
#                 'Winter (WY2018)'         : ['2017-10-01','2018-02-01'],
#                 'Growing Season (WY2018)' : ['2018-02-01','2018-10-01']}


time_windows = get_time_windows(water_year) 
time_window_labels = list(time_windows.keys())
time_windows_dates = [time_windows[key] for key in time_window_labels]
nwindows = len(time_windows)

# --------------------------------------------------------------------------                       
###########################################
# /// Average over the time windows /// 
########################################### 

for param in params2plot:

    print('\n\nPLOTTING PARAMETER: %s' % param.capitalize())
    unit = param2unit(param, NORM)
    
    for label in time_window_labels:
        print('Averaging over %s ... \n' % label)
        
       
        # print('Run == %s' % run_name)
        
        data = DATA[run_name + param]
        time = DATA[run_name + 'time']
        
        time_window = time_windows[label]
        time_start = np.datetime64(time_window[0])
        time_end = np.datetime64(time_window[1])
        indt = np.logical_and(time>=time_start,time<time_end)
        
        Time = list(set(time[indt])) 
                
        data_sel = data.loc[indt]
        data_sel = data_sel.groupby(['Control Volume']).mean()
        DATA[label + run_name + param] = data_sel
            
            # print(areas_df.mean(axis=0))
            # assert(False)
        print('Saved %s time frame for %s -- %s' % (label, run_name, param))
    
    
# --------------------------------------------------------------------------                       
    #################################
    # /// Functions for plotting  /// 
    ################################# 
    # (1) clean axis & plot the aggregated groups on top... 
    def clean_axis(axis):
        axis.xaxis.set_visible(0)
        axis.yaxis.set_visible(0)
        axis.axis('equal')
        # axis.set_title(date, fontsize = 15)
        axis.set_frame_on(False)
        # agg.boundary.plot(ax = axis, color = 'slategray')
    
    # (2) make a color bar w/ defined vmax and label ... 
    def make_colorbar(MAX, cmap_str, axis, label):
        norm = matplotlib.colors.Normalize(0, MAX)
        cmapp = matplotlib.cm.ScalarMappable(norm= norm, cmap= cmap_str)
        cmapp.set_array([])   # we need this line with our old HPC Python... 
        cb = plt.colorbar(cmapp, ax = axis, shrink = 0.7, orientation = 'vertical', pad = 0.02)
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
        return values.loc[values.index == 'polygon%d' % poly_num, SUB].values
          
    percentage_range = param2percentagerange[param]*100
    def make_percentage_colorbar(cmap_str, axis, label):
        norm = matplotlib.colors.Normalize(-percentage_range, percentage_range)
        cmapp = matplotlib.cm.ScalarMappable(norm= norm, cmap= cmap_str)
        cmapp.set_array([])   # we need this line with our old HPC Python... 
        cb = plt.colorbar(cmapp, ax = axis, shrink = 0.7, orientation = 'vertical', pad = 0.02)
        cb.ax.tick_params(labelsize = 14)
        cb.set_label(label, fontsize = 14)
    
    #%%
    
    '''
    The weird set-up here is designed to speed up our loops. Originally we plotted w/ geopandas
    but that took a lifetime. Now we take advantage of the relative speedier matplotlib polygon
    library. In order to do this, we intialize our polygons on a figure, and then assign values
    for the colors in a loop. This way we don't have to draw everything over and over again. 
    '''
    NPolys  = 141
    
    # Make a list of all the polygons we want to plot 136
    skip    = [i for i in range(118, 136)] # these are in the ocean so we are skipping them 118, 136
    polys2plot = [i for i in range(NPolys) if i not in  skip] 
    if agg:
        polys2plot.append(134)
    
    

    
    # Create polygon geometries 
    patches =  [polys.geometry[i]  for i in polys2plot]  
    
    # Another weird loop. Here we go through and convert all our polygons to objects matplotlib types
    Patches = [Polygon(np.asarray(poly.exterior)) for poly in patches] 
            
    # Create patch collection   
    PATCHES = [PatchCollection(Patches, facecolor='white', edgecolor='face')] # for i in range(10)]
    
    fig = plt.figure(figsize=(5,5))
    ax = plt.gca() 
    
    # Add patches to plot
    # patches_ = [] 
           
    patch_ = ax.add_collection(PATCHES[0]) #[0])
    patch_.set_clim(0, param2max[param])
    patch_.set_cmap(cmap)
    make_colorbar(param2max[param],  cmap,   ax,  unit)
    ax.autoscale_view()

                   
        
    # Second loop : Winter vs Growing Season
    for i, time_window_label in enumerate(['Winter (%s)' % water_year, 'Growing Season (%s)' % water_year, water_year]): 
        
        
        print('\n ... Plotting : %s \n' % time_window_label)
        k = 0  
   
            
        # pull out dataframe from dictionary (it's already averaged!)
        df = DATA[time_window_label + run_name + param]
        # extract value for each polygon 
        
        array = [(val_at_poly(df, i, param)) for i in polys2plot] 
        
        # convert it to 1D array and assign to polycollection 
        array = np.ravel(np.array(array))
        array = array.clip(0, param2max[param])
        # patches_[k].set_array(array)
        patch_.set_array(array)

        # clean the axes and add a title 
        clean_axis(ax) 
        
        fig.canvas.draw()
        ax.set_title('%s during %s' % (param2name[param],  time_window_label), fontsize = 11)
    
        savename = '%s/%s_%s_%s_%s.png' % (output_dir, water_year, time_window_label.replace('(%s)' % water_year, ''), param.capitalize(), run_name) 
        fig.savefig(savename)
        
        print(savename)
    
    
    print('DONE!!!!!!!!!!!!!!!!!!!')
    plt.close()


   

