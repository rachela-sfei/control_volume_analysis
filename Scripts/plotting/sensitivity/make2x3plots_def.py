# -*- coding: utf-8 -*-
"""
Created on Mon Jan  3 10:21:35 2022

@author: siennaw
"""


try:
    import geopandas as gpd
except:
    raise Exception('\n' + 
          'ERROR: this Python environment does not include geopandas.\n' + 
          'To load environment with geopandas on richmond, exit Python, execute the\n' + 
          'following at the command line:\n' + 
          '    source activate /home/zhenlin/.conda/envs/my_root\n' + 
          'and then re-launch Python. If on the other servers:\n' + 
          '    conda activate geo_env')
print('LOADING!?')


# path to shapefiles defining polygons and transects for the monitoring regions
# (make sure these are the same ones used to initialize the DWAQ run)
shpfn_poly =  '/richmondvol1/hpcshared/inputs/shapefiles/Agg_mod_contiguous_141.shp'
shpfn_tran = '/richmondvol1/hpcshared/inputs/shapefiles/Agg_exchange_lines_141.shp'

# Read in the shapefile 
polys   = gpd.read_file(shpfn_poly) 
transects     = gpd.read_file(shpfn_tran) 


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
               


# Sub-areas for bar graph 
AREAS = {   'LSB'           :  [7, 5, 4, 112, 111, 1, 3, 115, 113, 2, 114, 0, 138], 
            'South_Bay'     :  [23, 30, 15, 22, 27, 28, 106, 105, 104, 103, 102,
                                101, 24, 14, 21, 25, 26, 20, 13, 18, 19, 100, 139, 
                                11, 12, 10, 29, 8, 6, 107, 9, 110, 109, 108] ,
            'Central_Bay'   : [53, 56, 99, 89, 92, 52, 93, 87, 88, 91, 51, 50, 
                               90, 85, 95, 94, 96, 97, 98, 86, 49, 47, 48, 46, 
                               45, 140, 44, 43, 42, 41, 16, 36, 37, 38, 39, 40, 
                               17, 31, 32, 33, 34, 35],
            'San_Pablo_Bay' : [63, 65, 54, 55, 66, 64, 59, 60, 58, 134, 68, 67,
                               55, 54, 57],
            'Suisun_Bay'    : [69, 70, 71, 78, 72, 84, 79, 82, 83, 80, 81, 73, 76,
                               74, 75]     } 

AREAS_names = ['LSB', 'South_Bay', 'Central_Bay', 'San_Pablo_Bay', 'Suisun_Bay'] #  list(AREAS.keys()) 


print(AREAS_names)

AREAS_POLYGONS = {} 
for AREA in AREAS:
    AREAS_POLYGONS[AREA] = ['polygon%d' % i for i in AREAS[AREA]]
    
    
def find_inds(df, area_name):
    polygon_names =  AREAS_POLYGONS[area_name]
    df_poly = list(df['Control Volume'].values) 
    df_inds = [(name in polygon_names)  for name in df_poly]   
    return df_inds
    



# # Dict : run label followed by RunID 
# runs2plot = {'Base (#125)'         : 'G141_13to18_125',
#              'Higher (25%)'         : 'G141_13to18_126',
#              'Lower (25%)'         : 'G141_13to18_127'} 

# PARAM_SENS = 'Diat Growth Rate'
# base_run = 'Base (#125)'

# param2max = {'DPP' :  0.6,
#              'Denit' : 'Denitrification',
#              'dZ_Diat' : 0.05} 




  #################################
    # ////// MAKE PLOT !  //////////
    ################################# 
    # fig, axs = plt.subplots(nrows = 2, ncols = 3, sharex = False, sharey = False, figsize=(20,10))
    
    # # Add patches to plot
    # patches_ = [] 
    
    # axs = axs.ravel() 
    
    # for i, ax in enumerate(axs):
    #     # patches00 = copy.copy(patches0) #copy()
    #     patch_ = ax.add_collection(PATCHES[i])
    #     patch_.set_cmap(cmap)
    #     patch_.set_clim(0, MAX)
    #     patches_.append(patch_)
    #     if i==2 or i==5:
    #         make_colorbar(MAX,  cmap,   ax,  pri_label)
    #     ax.autoscale_view()
        
        
    # output_dir = r'/richmondvol1/hpcshared/Grid141/WY13to18//G141_13to18_117/CONTROL_VOLUME_PLOTS//'
    
    # # Triple loop! OUTER LOOP : Water Year (1 per page / figure)
    # for water_year in water_years:
    #     k = 0             
        
    #     # Second loop : Winter vs Growing Season
    #     for i, time_window_label in enumerate(['Winter (%s)' % water_year, 'Growing Season (%s)' % water_year]): 
            
            
    #         print('\n ... Plotting : %s \n' % time_window_label)
            
    #         # Third loop: Run[s]! 
    #         for n, run_name in enumerate(run_names):    
                
    #             # pull out dataframe from dictionary (it's already averaged!)
    #             df = DATA[time_window_label + run_name + param]
    #             # extract value for each polygon 
                
    #             array = [(val_at_poly(df, i, param)) for i in polys2plot] 
                
    #             # convert it to 1D array and assign to polycollection 
    #             array = np.ravel(np.array(array))
    #             array = array.clip(0, MAX)
    #             patches_[k].set_array(array)
                
    #             # clean the axes and add a title 
    #             clean_axis(axs[k], '%s (%s)' % (time_window_label.replace('(%s)' % water_year, '') , run_labels[n]))
                
    #             k += 1  # a counter // we use this for the axis count 
                
    #     fig.canvas.draw()
    #     fig.suptitle('%s %s' % ('Seasonal DPP', water_year), fontsize = 20)
    
    #     savename = '%s/%s.png' % (output_dir, water_year) 
    #     fig.savefig(savename)
    #     print(savename)
    
    # print('DONE!!!!!!!!!!!!!!!!!!!')
    # plt.close()
    
    
    
    