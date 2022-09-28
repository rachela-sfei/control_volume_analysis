
"""
alliek prep for 2020 NTW meeting March 11
"""


import pandas as pd 
import numpy as np 
import matplotlib.pyplot as plt
import sys
import os 
import geopandas as gpd
import matplotlib.collections as mcollections

#############################
# user input
#############################

# figure size
figsize = (12,12)

# run ID and water year
#run_ID = 'FR13_025'
run_ID = 'FR13_021'
water_year_list = [2013]
#run_ID = 'FR17_018'
#water_year_list = [2017]
#run_ID = 'FR18_006'
#water_year_list = [2018]
#run_ID = 'G141_13to18_197'
#water_year_list = [2013,2014,2015,2016,2017,2018]

# arrow scale (m2 per Mg/d)
arrow_scale_area = 5000**2
arrow_scale_Mgd = 50
arrow_scale = arrow_scale_area / arrow_scale_Mgd

# what fraction of the arrow length to make the width
arrow_width_factor = 0.25

# boolean to test arrow direction
test_arrow_direction = False

# base directory (windows laptop vs. hpc)
#base_dir = r'X:\hpcshared'
base_dir = '/richmondvol1/hpcshared'

# path to balance tables (they should be organized by run ID within this folderr)
balance_table_path = os.path.join(base_dir,'NMS_Projects','Control_Volume_Analysis','Balance_Tables',run_ID)

# path to the shapefile w/ the base level control volumes
if 'FR' in run_ID:
    shp_fn = os.path.join(base_dir,'NMS_Projects','Control_Volume_Analysis','Definitions','shapefiles','group_definition_shapefile_FR.shp')
else:
    shp_fn = os.path.join(base_dir,'NMS_Projects','Control_Volume_Analysis','Definitions','shapefiles','group_definition_shapefile_AGG.shp')

# figure output path and name
figure_path =  os.path.join(base_dir,'NMS_Projects','Control_Volume_Analysis','Plots',run_ID,'subembayment_arrow_maps_source_sink')

# list of control volumes in the group shapefile that we want to plot (find these by hand -- can look in the control volume definition file to cheat)
poly_list = ['LSB','SB_WB_south_half','SB_WB_north_half','Central_Bay_WB','San_Pablo_Bay','Suisun_Bay']

# dictionary containing a list of flux arrows, their coordinates, their directions, 
# and the group name and flux direction that will give us their magnitude
# for example arrow 0 is located at the N end of LSB at (577740, 4151650), points into LSB with unit normal 
# (0.5846897297003711, -0.8112569999592649), and we get its magnitude from the LSB flux into the N (note in 
# balance tables fluxes are given w.r.t. the directions pointing into the control volume)
flux_arrow_dict = {}
#flux_arrow_dict[0] = [(577740, 4151650), (0.5846897297003711, -0.8112569999592649), 'LSB', 'N']
flux_arrow_dict[0] = [(578270, 4150400), (0.5846897297003711, -0.8112569999592649), 'LSB', 'N']
flux_arrow_dict[1] = [(564000, 4168400), (0.6011444224120746, -0.7991404028097022), 'SB_WB_south_half', 'N']
flux_arrow_dict[2] = [(556010, 4185000), (0.6011444224120746, -0.7991404028097022), 'SB_WB_north_half', 'N']
flux_arrow_dict[3] = [(582000, 4220600), ( 0.7071067811865476, -0.7071067811865476), 'Suisun_Bay', 'N']   # flux into Suisun_WB_FR doesn't look right so use whole bay group
flux_arrow_dict[4] = [(597600, 4211600), (-1, 0), 'Suisun_Bay', 'E']
#flux_arrow_dict[5] = [(567540, 4213030), (-0.9999913556128004, 0.004157968214606239), 'San_Pablo_Bay', 'E']
flux_arrow_dict[5] = [(572680, 4211230), (-0.9999913556128004, 0.004157968214606239), 'San_Pablo_Bay', 'E']
flux_arrow_dict[6] = [(548900, 4203060), (0.39497836590984664, 0.9186904214495693), 'San_Pablo_Bay', 'S']
flux_arrow_dict[7] = [(545850, 4185660), (0.8944271909999159, 0.4472135954999579), 'Central_Bay_WB', 'W']
flux_arrow_dict[10] = [(566000,4215100), (-0.4472135954999579, 0.8944271909999159), 'Napa', 'S']
if 'FR' in run_ID:
    flux_arrow_dict[8] = [(552800, 4222200), (-0.4472135954999579, 0.8944271909999159), 'Sonoma', 'S']
    flux_arrow_dict[9] = [(545200, 4218100), (-0.7071067811865476, 0.7071067811865476), 'Petaluma', 'S']

# dictionary with coordinates of center arrows along with the name of the corresponding group
center_arrow_dict = {}
center_arrow_dict[0] = [(584500, 4146000), 'LSB']
center_arrow_dict[1] = [(567600, 4164300), 'SB_WB_south_half']
center_arrow_dict[2] = [(559900, 4175200), 'SB_WB_north_half']
center_arrow_dict[3] = [(556900, 4193400), 'Central_Bay_WB']
center_arrow_dict[4] = [(550500, 4216800), 'San_Pablo_Bay']
#center_arrow_dict[5] = [(584700, 4219900), 'Suisun_Bay']
center_arrow_dict[5] = [(584700, 4216900), 'Suisun_Bay']

# spacing between the three center arrows (loading, reaction, storage)
center_arrow_offset = 2000

# legend specs - coordinates and space between entries, we draw the legend manually instead of calling plt.legend()
legend_loc = (582700, 4190300)
legend_yspace = 6000

# axis window 
axis_window = (509062.33981440606, 614035.4169852139, 4134370.722411021, 4236807.203694713)

# arrow colors and map color
map_color = 'lightgray'
edge_color = 'darkgray'
boundary_color = 'k'
transport_color = 'green'
loading_color = 'red'
source_color = 'magenta'
sink_color = 'cyan'
reaction_color = 'black'
storage_color = 'yellow'

##########################
# main
##########################

# check if plot directory exists and create it if not
if not os.path.exists(figure_path):
    os.makedirs(figure_path)

# parameter to plot
for param in ['DIN','TN','TN_include_sediment','Algae']:

    # balance table name depends on parameter
    balance_table_name = '%s_Table_By_Group.csv' % param.lower()
    
    # load the balance table 
    df_1 = pd.read_csv(os.path.join(balance_table_path,balance_table_name))
    df_1['time'] = df_1['time'].astype('datetime64[ns]')

    # get list of sources and sinks
    source_list = []
    sink_list = []
    for col in df_1.columns:
        if not 'ZERO' in col:
            if not ',dMass/' in col:
                if ',d' in col:
                    if df_1[col].mean()>0:
                        source_list.append(col)
                    elif df_1[col].mean()<0:
                        sink_list.append(col)
    
    # load the shapefile
    shp = gpd.read_file(shp_fn)
    
    # find list of indices of polygons to plot
    iplot = []
    for i in range(len(shp)):
        if shp.iloc[i]['feature'] in poly_list:
            iplot.append(i)
    
    for water_year in water_year_list:

        for time_avg in ['Seasonal','Monthly']:
        
        
            # time period for averaging, figure names, figure titles
            if time_avg=='Monthly':
                start_time_list = [np.datetime64('%d-10-01' % (water_year-1)),
                               np.datetime64('%d-11-01' % (water_year-1)),
                               np.datetime64('%d-12-01' % (water_year-1)),
                               np.datetime64('%d-01-01' % water_year),
                               np.datetime64('%d-02-01' % water_year),
                               np.datetime64('%d-03-01' % water_year),
                               np.datetime64('%d-04-01' % water_year),
                               np.datetime64('%d-05-01' % water_year),
                               np.datetime64('%d-06-01' % water_year),
                               np.datetime64('%d-07-01' % water_year),
                               np.datetime64('%d-08-01' % water_year),
                               np.datetime64('%d-09-01' % water_year)]
                end_time_list =   [np.datetime64('%d-11-01' % (water_year-1)),
                               np.datetime64('%d-12-01' % (water_year-1)),
                               np.datetime64('%d-01-01' % water_year),
                               np.datetime64('%d-02-01' % water_year),
                               np.datetime64('%d-03-01' % water_year),
                               np.datetime64('%d-04-01' % water_year),
                               np.datetime64('%d-05-01' % water_year),
                               np.datetime64('%d-06-01' % water_year),
                               np.datetime64('%d-07-01' % water_year),
                               np.datetime64('%d-08-01' % water_year),
                               np.datetime64('%d-09-01' % water_year),
                               np.datetime64('%d-10-01' % water_year)]
                figure_fn_list = [('%s_%s_subembayment_arrow_map_monthly_WY%d_%s.png' % (run_ID, param, water_year, '%02d')) % i for i in range(12)] 
                figure_title_list = ['WY%d Oct\n%s Budget' % (water_year, param),
                                 'WY%d Nov\n%s Budget' % (water_year, param),
                                 'WY%d Dec\n%s Budget' % (water_year, param),
                                 'WY%d Jan\n%s Budget' % (water_year, param),
                                 'WY%d Feb\n%s Budget' % (water_year, param),
                                 'WY%d Mar\n%s Budget' % (water_year, param),
                                 'WY%d Apr\n%s Budget' % (water_year, param),
                                 'WY%d May\n%s Budget' % (water_year, param),
                                 'WY%d Jun\n%s Budget' % (water_year, param),
                                 'WY%d Jul\n%s Budget' % (water_year, param),
                                 'WY%d Aug\n%s Budget' % (water_year, param),
                                 'WY%d Sep\n%s Budget' % (water_year, param)]
            
            elif time_avg=='Seasonal': 
                start_time_list = [np.datetime64('%d-10-01' % (water_year-1)),
                               np.datetime64('%d-01-01' % water_year),
                               np.datetime64('%d-04-01' % water_year),
                               np.datetime64('%d-07-01' % water_year)]
                end_time_list =   [np.datetime64('%d-01-01' % water_year),
                               np.datetime64('%d-04-01' % water_year),
                               np.datetime64('%d-07-01' % water_year),
                               np.datetime64('%d-10-01' % water_year)]
                figure_fn_list = [('%s_%s_subembayment_arrow_map_seasonal_WY%d_%s.png' % (run_ID, param, water_year, '%02d')) % i for i in range(4)] 
                figure_title_list = ['WY%d Oct, Nov, Dec\n%s Budget' % (water_year, param),
                                 'WY%d Jan, Feb, Mar\n%s Budget' % (water_year, param),
                                 'WY%d Apr, May, Jun\n%s Budget' % (water_year, param),
                                 'WY%d Jul, Aug, Sep\n%s Budget' % (water_year, param)]
        
            # loop through time windows
            for iwindow in range(len(start_time_list)):
            
                # extract start and end times, figure name, and figure title from input list
                start_time = start_time_list[iwindow]
                end_time = end_time_list[iwindow]
                figure_fn = figure_fn_list[iwindow]
                figure_title = figure_title_list[iwindow]
            
                # average over the time window
                indt = np.logical_and(df_1['time']>=start_time, df_1['time']<end_time)
                df = df_1.loc[indt].groupby(['group']).mean()

                # get the loading and reactive loss arrow info from the dictionaries and the balance tables
                xC = [] # C is for center arrows (loading, storage, sources, and sinks)
                yC = []
                dxL = [] # L is for loading
                dyL = []
                dxS = [] # S is for storage
                dyS = []
                dxP = [] # P is for +, sources
                dyP = []
                dxM = [] # M is for -, sinks
                dyM = []
                dxR = [] # R is for net reaction
                dyR = []
                loading = []
                storage = []
                source = []
                sink = []
                reaction = []
                for key in center_arrow_dict.keys():
                
                    # get the coordinates and the group name
                    x, y = center_arrow_dict[key][0]
                    group = center_arrow_dict[key][1]


                    # get the loading and the reactions from the balance tables
                    loading_1 = df.loc[group]['%s,Net Load (Mg/d)' % param] 
                    storage_1 = df.loc[group]['%s,dMass/dt, Balance Check (Mg/d)' % param] 
                    source_1 = df.loc[group][source_list].sum()
                    sink_1 = df.loc[group][sink_list].sum()
                    reaction_1 = df.loc[group]['%s,Net Reaction (Mg/d)' % param] 
                    if (reaction_1 - (source_1+sink_1))/reaction_1 > 0.01:
                        print('warning: not exactly equal reaction = %f vs. sources-sinks = %f' % (reaction_1,source_1+sink_1))

                    # append to the list
                    xC.append(x)
                    yC.append(y)
                    dxL.append(0)
                    dyL.append(1)
                    dxS.append(0)
                    dyS.append(1)
                    dxP.append(0)
                    dyP.append(1)
                    dxM.append(0)
                    dyM.append(1)
                    dxR.append(0)
                    dyR.append(1)
                    if test_arrow_direction:
                        loading.append(1)
                        storage.append(1)
                        source.append(1)
                        sink.append(-1)
                        reaction.append(-1)
                    else:
                        loading.append(loading_1)
                        storage.append(storage_1)
                        source.append(source_1)
                        sink.append(sink_1)
                        reaction.append(reaction_1)
                
                # get the transect arrow info from the dictionaries and the balance tables
                xT = []
                yT = []
                dxT = []
                dyT = []
                transport = []
                for key in flux_arrow_dict.keys():
                
                    # get the coordinates, direction, group name, and side
                    x, y = flux_arrow_dict[key][0]
                    dx, dy = flux_arrow_dict[key][1]
                    group = flux_arrow_dict[key][2]
                    side = flux_arrow_dict[key][3]
                
                    # get the flux in on the group side combo specified
                    transport_1 = df.loc[group]['%s,Flux In from %s (Mg/d)' % (param, side)]
                
                    # append to the list
                    xT.append(x)
                    yT.append(y)
                    dxT.append(dx)
                    dyT.append(dy)
                    if test_arrow_direction:
                        transport.append(1)
                    else:
                        transport.append(transport_1)
                
                # convert loading, reaction, storage, and transport info to arrays
                xC = np.array(xC)
                yC = np.array(yC)
                xT = np.array(xT)
                yT = np.array(yT)
                dxL = np.array(dxL)
                dyL = np.array(dyL)
                dxS = np.array(dxS)
                dyS = np.array(dyS)
                dxP = np.array(dxP)
                dyP = np.array(dyP)
                dxM = np.array(dxM)
                dyM = np.array(dyM)
                dxR = np.array(dxR)
                dyR = np.array(dyR)
                dxT = np.array(dxT)
                dyT = np.array(dyT)
                loading = np.array(loading)
                storage = np.array(storage)
                source = np.array(source)
                sink = np.array(sink)
                reaction = np.array(reaction)
                transport = np.array(transport)
                

                # normalize dx and dy to make sure length is one (don't worry about loadign, storage, sources, sinks, they are 1)
                dsT = np.sqrt(dxT**2 + dyT**2)
                dxT = dxT/dsT
                dyT = dyT/dsT

                # loop through all the terms, check if positive or negative, and if negative, make it positive
                # but also flip the arrow direction around
                for i in range(len(loading)):
                    if loading[i] < 0:
                        loading[i] = -loading[i]
                        dyL[i] = -dyL[i]
                        dxL[i] = -dxL[i]
                for i in range(len(storage)):
                    if storage[i] < 0:
                        storage[i] = -storage[i]
                        dyS[i] = -dyS[i]
                        dxS[i] = -dxS[i]
                for i in range(len(source)):
                    if source[i] < 0:
                        source[i] = -source[i]
                        dyP[i] = -dyP[i]
                        dxP[i] = -dxP[i]
                for i in range(len(sink)):
                    if sink[i] < 0:
                        sink[i] = -sink[i]
                        dyM[i] = -dyM[i]
                        dxM[i] = -dxM[i]
                for i in range(len(reaction)):
                    if reaction[i] < 0:
                        reaction[i] = -reaction[i]
                        dyR[i] = -dyR[i]
                        dxR[i] = -dxR[i]
                for i in range(len(transport)):
                    if transport[i] < 0:
                        transport[i] = -transport[i]
                        dyT[i] = -dyT[i]
                        dxT[i] = -dxT[i]
            
                # create the map
                fig, ax = plt.subplots(figsize=figsize)
                shp.iloc[iplot].plot(ax=ax, color = map_color, edgecolor=edge_color)
                
                # add transport, loading, storage, and reaction arrows
                for i in range(len(transport)):
                    area = transport[i]*arrow_scale
                    length = np.sqrt(area / arrow_width_factor)
                    width = arrow_width_factor * length
                    head_width = 2*width
                    head_length = 1.5*width
                    ax.arrow(xT[i], yT[i], dxT[i]*length, dyT[i]*length, width = width, head_width=head_width, head_length=head_length, length_includes_head=True, color=transport_color, linewidth=0, edgecolor=None, alpha=1)
                for i in range(len(loading)):
                    area = loading[i]*arrow_scale
                    length = np.sqrt(area / arrow_width_factor)
                    width = arrow_width_factor * length
                    head_width = 2*width
                    head_length = 1.5*width
                    ax.arrow(xC[i]-center_arrow_offset, yC[i], dxL[i]*length, dyL[i]*length, width = width, head_width=head_width, head_length=head_width, length_includes_head=True, color=loading_color, linewidth=0, edgecolor=None, alpha=1)
                for i in range(len(source)):
                    area = source[i]*arrow_scale
                    length = np.sqrt(area / arrow_width_factor)
                    width = arrow_width_factor * length
                    head_width = 2*width
                    head_length = 1.5*width
                    ax.arrow(xC[i], yC[i], dxP[i]*length, dyP[i]*length, width = width, head_width=head_width, head_length=head_width, length_includes_head=True, color=source_color, linewidth=0, edgecolor=None, alpha=1)
                for i in range(len(sink)):
                    area = sink[i]*arrow_scale
                    length = np.sqrt(area / arrow_width_factor)
                    width = arrow_width_factor * length
                    head_width = 2*width
                    head_length = 1.5*width
                    ax.arrow(xC[i], yC[i], dxM[i]*length, dyM[i]*length, width = width, head_width=head_width, head_length=head_width, length_includes_head=True, color=sink_color, linewidth=0, edgecolor=None, alpha=1)
                for i in range(len(reaction)):
                    area = reaction[i]*arrow_scale
                    length = np.sqrt(area / arrow_width_factor)
                    width = arrow_width_factor * length
                    head_width = 2*width
                    head_length = 1.5*width
                    ax.arrow(xC[i], yC[i], dxR[i]*length, dyR[i]*length, width = width, head_width=head_width, head_length=head_width, length_includes_head=True, color=reaction_color, linewidth=0, edgecolor=None, alpha=1)
                for i in range(len(storage)):
                    area = storage[i]*arrow_scale
                    length = np.sqrt(area / arrow_width_factor)
                    width = arrow_width_factor * length
                    head_width = 2*width
                    head_length = 1.5*width
                    ax.arrow(xC[i]+center_arrow_offset, yC[i], dxS[i]*length, dyS[i]*length, width = width, head_width=head_width, head_length=head_width, length_includes_head=True, color=storage_color, linewidth=0, edgecolor=None, alpha=1)
                
                # fontsize
                fontsize=16
                
                # add a legend
                length = np.sqrt(arrow_scale_area / arrow_width_factor)
                width = arrow_width_factor * length
                head_width = 2*width
                head_length = 1.5*width
                # ... legend title
                leg_offset = legend_yspace
                plt.text(legend_loc[0],legend_loc[1]+leg_offset,'Magnitudes are Proportional to Arrow Base Area', fontsize=fontsize, va='center')
                leg_offset = leg_offset - legend_yspace
                # ... transport arrow
                ax.arrow(legend_loc[0], legend_loc[1]+leg_offset, length, 0, width = width, head_width=head_width, head_length=head_length, length_includes_head=True, color=transport_color, edgecolor=None, alpha=1)
                plt.text(legend_loc[0]+1.5*length,legend_loc[1]+leg_offset,'%0.0f Mg/d Transport' % arrow_scale_Mgd, fontsize=fontsize, va='center')
                leg_offset = leg_offset - legend_yspace
                # ... loading arrow
                if not param=='Algae':
                    ax.arrow(legend_loc[0], legend_loc[1]+leg_offset, length, 0, width = width, head_width=head_width, head_length=head_length, length_includes_head=True, color=loading_color, edgecolor=None, alpha=1)
                    plt.text(legend_loc[0]+1.5*length,legend_loc[1]+leg_offset,'%0.0f Mg/d Loading' % arrow_scale_Mgd,fontsize=fontsize, va='center')
                    leg_offset = leg_offset - legend_yspace
                # ... source arrow
                ax.arrow(legend_loc[0], legend_loc[1]+leg_offset, length, 0, width = width, head_width=head_width, head_length=head_length, length_includes_head=True, color=source_color, edgecolor=None, alpha=1)
                plt.text(legend_loc[0]+1.5*length,legend_loc[1]+leg_offset,'%0.0f Mg/d Sources' % arrow_scale_Mgd,fontsize=fontsize, va='center')
                leg_offset = leg_offset - legend_yspace
                # ... sink arrow
                ax.arrow(legend_loc[0], legend_loc[1]+leg_offset, length, 0, width = width, head_width=head_width, head_length=head_length, length_includes_head=True, color=sink_color, edgecolor=None, alpha=1)
                plt.text(legend_loc[0]+1.5*length,legend_loc[1]+leg_offset,'%0.0f Mg/d Sinks' % arrow_scale_Mgd,fontsize=fontsize, va='center')
                leg_offset = leg_offset - legend_yspace
                # ... reaction arrow
                ax.arrow(legend_loc[0], legend_loc[1]+leg_offset, length, 0, width = width, head_width=head_width, head_length=head_length, length_includes_head=True, color=reaction_color, edgecolor=None, alpha=1)
                plt.text(legend_loc[0]+1.5*length,legend_loc[1]+leg_offset,'%0.0f Mg/d Net Reaction' % arrow_scale_Mgd,fontsize=fontsize, va='center')
                leg_offset = leg_offset - legend_yspace
                # ... storage arrow
                ax.arrow(legend_loc[0], legend_loc[1]+leg_offset, length, 0, width = width, head_width=head_width, head_length=head_length, length_includes_head=True, color=storage_color, edgecolor=None, alpha=1)
                plt.text(legend_loc[0]+1.5*length,legend_loc[1]+leg_offset,'%0.0f Mg/d Storage' % arrow_scale_Mgd,fontsize=fontsize, va='center')
                
                # fix the axis, add a title, etc
                ax.axis(axis_window)
                ax.axis('off')
                ax.set_title(figure_title, fontsize=fontsize)
                fig.tight_layout()
                fig.savefig(os.path.join(figure_path,figure_fn),dpi=300)
            
                plt.close('all')            