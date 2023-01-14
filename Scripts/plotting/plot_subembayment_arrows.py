
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
if not 'DISPLAY' in os.environ:
    import matplotlib
    matplotlib.use('agg')
    plt.switch_backend('Agg')
from importlib import reload
import control_volume_plotting_library as CVPL # plotting library must be in same folder as this script
reload(CVPL)

#############################
# user input
#############################

# list of run id's and corresponding water years -- these lists should be the same length
# and each item in the list will correspond to a column in the figure
if 1:
    runid_list = ['FR22_HAB_054', 'FR22_HAB_055', 'FR22_HAB_056', 'FR22_HAB_057', 'FR22_HAB_058']
    wy_list = [2022,2022,2022,2022,2022]
    server_list = ['chicago','chicago','chicago','chicago','chicago']

#if 1:    
#    runid_list = ['FR13_026', 'G141_13to18_246','FR17_019', 'G141_13to18_246','FR18_007', 'G141_13to18_246']
#    wy_list = [2013,2013,2017,2017,2018,2018]
#    server_list = ['chicago','richmond','chicago','richmond','chicago','richmond']
#if 1:    
#    runid_list = ['FR13_003', 'FR13_026', 'FR17_003','FR17_019']
#    wy_list = [2013,2013,2017,2017]
#    server_list = ['richmond','chicago','richmond','chicago']

# list of time averages to plot (must have pre-generated these w/ step6 of the create_balance_tables scripts)
tavg_list = ['Weekly']

# list of parameters to plot -- these will be processed one after the other, not compared
param_list = ['DIN','TN','TN_include_sediment','TotalDetNS','OXY','Algae']

# flag to put all runs and/or times on same plot
# runs will be different columns and times will be different rows
runs_on_same_plot = True
times_on_same_plot = True

# figure size
subplot_height = 10
subplot_width = 6

# arrow scale (m2 per Mg/d)
# later in code will compute arrow_scale = arrow_scale_area / arrow_scale_Mgd
arrow_scale_area = 5000**2
arrow_scale_Mgd = {'DIN' : 50,
                   'TN' : 50,
                   'TN_include_sediment' : 50,
                   'TotalDetNS' : 25,
                   'OXY' : 400,
                   'Algae' : 75,
                   'DiatS1' : 50}


# what fraction of the arrow length to make the width
arrow_width_factor = 0.25

# boolean to test arrow direction
test_arrow_direction = False

# base directory for the output figures (in theory should be able to run on windows laptop with mounted drives or on server)
figure_base_dir = '/chicagovol1/hpcshared/open_bay/bgc/figures'
group_shapefile_dir = '../../Definitions/group_shapefiles'

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
flux_arrow_dict[8] = [(566000,4215100), (-0.4472135954999579, 0.8944271909999159), 'Napa', 'S']
# note that arrows 8 and 9 should be included for FR runs ONLY -- create a variable called fluxrange to cap agg run
flux_arrow_dict[9] = [(552800, 4222200), (-0.4472135954999579, 0.8944271909999159), 'Sonoma', 'S']
flux_arrow_dict[10] = [(545200, 4218100), (-0.7071067811865476, 0.7071067811865476), 'Petaluma', 'S']
fluxrange_AGG = 9
fluxrange_FR = 11

# dictionary with coordinates of center arrows along with the name of the corresponding group
center_arrow_dict = {}
center_arrow_dict[0] = [(584500, 4146000), 'LSB']
center_arrow_dict[1] = [(567600, 4164300), 'SB_WB_south_half']
center_arrow_dict[2] = [(559900, 4175200), 'SB_WB_north_half']
center_arrow_dict[3] = [(556900, 4193400), 'Central_Bay_WB']
center_arrow_dict[4] = [(550500, 4216800), 'San_Pablo_Bay']
center_arrow_dict[5] = [(584700, 4216900), 'Suisun_Bay']

# spacing between the three center arrows (loading, reaction, storage)
center_arrow_offset = 2000

# axis window 
axis_window = (527515.336093358, 601052.0291024673, 4134193.7827598574, 4237441.867634327)
#(509062.33981440606, 614035.4169852139, 4134370.722411021, 4236807.203694713)

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

# fontsize for legend, title, etc
fontsize = 16

##########################
# functions
##########################

# tells you if the parameter is benthic (if it's benthic, don't include the transport plot, because it
# doesn't get transported, so everything is zero)
def is_there_loading(param):

    if param in ['Algae','Green','Diat','DiatS1',
                 'OXY', 
                 'DetNS1','DetNS2','DetNS','OONS1','OONS2','OONS',
                 'TotalDetNS1','TotalDetNS1','TotalDetNS']:
        has_loading = False
    else:
        has_loading = True

    return has_loading


##########################
# main
##########################

# do some checks to make sure user input makes sense
nruns = len(runid_list)
assert nruns == len(wy_list)

# get strings with concise lists of runs and water years
run_list_str = CVPL.make_concise_runid_list_string(runid_list)
wy_list_str = CVPL.make_concise_water_year_list_string(wy_list)

# path to figures, create if it does not exist
figure_path = os.path.join(figure_base_dir, run_list_str, 'subembayment_arrows')
if not os.path.exists(figure_path):
    os.makedirs(figure_path)
print('\nfigures will be saved here: %s\n' % figure_path)

# parameter to plot
for param in param_list:

    # compute figure arrow scale based on parameter
    arrow_scale = arrow_scale_area / arrow_scale_Mgd[param]

    # loop through averaging time periods (Annual, Seasonal, Monthly)
    for tavg in tavg_list:

        # balance table name is the same across all the runs, just located in different directories
        balance_table_fn = '%s_Table_By_Group_%s.csv' % (param.lower(), tavg)

        # before we plot the different runs, take a sneak peek to find a list of all the reactions, across all the runs
        source_list = []
        sink_list = []
        for irun in range(nruns):

            # get the run id
            runid = runid_list[irun]
    
            # get path to the balance table folder in the run folder
            run_base_dir = '/%svol1/hpcshared' % server_list[irun]
            run_dir = CVPL.get_run_dir(run_base_dir, runid)
            balance_table_dir = os.path.join(run_dir,'Balance_Tables')
            
            # load up the balance table data for the parameter of interest
            input_fn = os.path.join(balance_table_dir,balance_table_fn)
            try:
                data = pd.read_csv(input_fn)
            except:
                print('could not open %s\nit probably doesn''t exist, skipping this one' % input_fn)
                continue

            # get the reaction lists
            source_list_1 = []
            sink_list_1 = []
            for col in data.columns:
                if not 'ZERO' in col:
                    if not ',dMass/' in col:
                        if ',d' in col:
                            if data[col].mean()>0:
                                source_list_1.append(col)
                            elif data[col].mean()<0:
                                sink_list_1.append(col)

            # add to master list
            for rx in source_list_1:
                if not rx in source_list:
                    source_list.append(rx)
            for rx in sink_list_1:
                if not rx in sink_list:
                    sink_list.append(rx)

            # count sources and sinks
            nsource = len(source_list)
            nsink = len(sink_list)

        # initialize a list of figure handles for the different time steps
        fig_list = []
        ax_list = []

        # loop through the runs
        for irun in range(nruns):

            # get the run id and water year
            runid = runid_list[irun]
            wy = wy_list[irun]
    
            # path to the shapefile w/ the base level control volumes and also range of flux dictionary keys
            # (this is a weird thing that has the effect of excluding Sonoma and Petaluma from the agg grid 
            # runs b/c these fluxes don't exist for agg runs)
            if 'FR' in runid:
                shp_fn = os.path.join(group_shapefile_dir,'group_definition_shapefile_FR.shp')
                fluxrange = fluxrange_FR
            else:
                shp_fn = os.path.join(group_shapefile_dir,'group_definition_shapefile_AGG.shp')
                fluxrange = fluxrange_AGG

            # get path to the balance table folder in the run folder
            run_base_dir = '/%svol1/hpcshared' % server_list[irun]
            run_dir = CVPL.get_run_dir(run_base_dir, runid)
            balance_table_dir = os.path.join(run_dir,'Balance_Tables')

            # read balance table
            df_1 = pd.read_csv(os.path.join(balance_table_dir, balance_table_fn))
            df_1['time'] = pd.to_datetime(df_1['time'])
    
            # isolate the water year
            ind = np.logical_and(df_1['time'].values >= np.datetime64('%d-10-01' % (wy-1)), 
                                 df_1['time'].values <  np.datetime64('%d-10-01' % wy))
            df_1 = df_1.loc[ind]

            # get the unique times
            time = np.unique(df_1.time.values)
            ntime = len(time)
            
            # load the shapefile
            shp = gpd.read_file(shp_fn)
            
            # find list of indices of polygons to plot
            iplot = []
            for i in range(len(shp)):
                if shp.iloc[i]['feature'] in poly_list:
                    iplot.append(i) 

            # loop through the time steps
            for itime in range(ntime):
        
                # on first run, initialize a figure and add it to the list
                if irun==0:
                    fig, ax = plt.subplots(1,nruns+1,figsize=((nruns+1)*subplot_width, subplot_height))
                    fig_list.append(fig)
                    ax_list.append(ax)

                # select the correct figure for this time step and the correct axis for this run
                fig = fig_list[itime]
                ax = ax_list[itime][irun]

                # get data at this time step
                indt = df_1['time'].values == time[itime]
                df = df_1.loc[indt]
                df.index = df['group']

                # get the time label
                time_label = df['Time Period'].iloc[0]
        
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
        
                    # isolate group
                    df_group = df.loc[group]
                    if len(group) > 1:
                        print('warning: %d duplicate time steps at time %s, using final time step' % (len(df_group), time[itime]))
                        df_group = df_group.iloc[-1]
        
                    # get the loading and the reactions from the balance tables
                    loading_1 = df_group['%s,Net Load (Mg/d)' % param] 
                    storage_1 = df_group['%s,dMass/dt, Balance Check (Mg/d)' % param] 
                    source_1 = 0
                    for source1 in source_list:
                        if source1 in df.columns:
                            source_1 += df_group[source1].copy()
                    sink_1 = 0
                    for sink1 in sink_list:
                        if sink1 in df.columns:
                            sink_1 += df_group[sink1].copy()
                    reaction_1 = df_group['%s,Net Reaction (Mg/d)' % param] 
                    if (reaction_1 - (source_1+sink_1))/reaction_1 > 0.01:
                        print('warning (param=%s, tavg=%s, irun=%d, itime=%d) not exactly equal reaction = %f vs. sources-sinks = %f' % (param, tavg, irun, itime, reaction_1,source_1+sink_1))
        
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
                for key in range(fluxrange):
                
                    # get the coordinates, direction, group name, and side
                    x, y = flux_arrow_dict[key][0]
                    dx, dy = flux_arrow_dict[key][1]
                    group = flux_arrow_dict[key][2]
                    side = flux_arrow_dict[key][3]

                    # isolate group
                    df_group = df.loc[group]
                    if len(group) > 1:
                        print('warning: %d duplicate time steps at time %s, using final time step' % (len(df_group), time[itime]))
                        df_group = df_group.iloc[-1]
                
                    # get the flux in on the group side combo specified
                    transport_1 = df_group['%s,Flux In from %s (Mg/d)' % (param, side)]
                
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
                shp.iloc[iplot].plot(ax=ax, color = map_color, edgecolor=edge_color, zorder=0.5)
                
                # add transport, loading, storage, and reaction arrows
                for i in range(len(transport)):
                    area = transport[i]*arrow_scale
                    length = np.sqrt(area / arrow_width_factor)
                    width = arrow_width_factor * length
                    head_width = 2*width
                    head_length = 1.5*width
                    ax.arrow(xT[i], yT[i], dxT[i]*length, dyT[i]*length, zorder = 3,
                             width = width, head_width=head_width, head_length=head_length, 
                             length_includes_head=True, color=transport_color, linewidth=0, edgecolor=None, alpha=1)
                for i in range(len(loading)):
                    area = loading[i]*arrow_scale
                    length = np.sqrt(area / arrow_width_factor)
                    width = arrow_width_factor * length
                    head_width = 2*width
                    head_length = 1.5*width
                    ax.arrow(xC[i]-center_arrow_offset, yC[i], dxL[i]*length, dyL[i]*length, zorder = 2,
                             width = width, head_width=head_width, head_length=head_width, 
                             length_includes_head=True, color=loading_color, linewidth=0, edgecolor=None, alpha=1)
                for i in range(len(source)):
                    area = source[i]*arrow_scale
                    length = np.sqrt(area / arrow_width_factor)
                    width = arrow_width_factor * length
                    head_width = 2*width
                    head_length = 1.5*width
                    ax.arrow(xC[i], yC[i], dxP[i]*length, dyP[i]*length,  zorder = 1,
                             width = width, head_width=head_width, head_length=head_width, 
                             length_includes_head=True, color=source_color, linewidth=0, edgecolor=None, alpha=1)
                for i in range(len(sink)):
                    area = sink[i]*arrow_scale
                    length = np.sqrt(area / arrow_width_factor)
                    width = arrow_width_factor * length
                    head_width = 2*width
                    head_length = 1.5*width
                    ax.arrow(xC[i], yC[i], dxM[i]*length, dyM[i]*length,  zorder = 1,
                             width = width, head_width=head_width, head_length=head_width, 
                             length_includes_head=True, color=sink_color, linewidth=0, edgecolor=None, alpha=1)
                for i in range(len(reaction)):
                    area = reaction[i]*arrow_scale
                    length = np.sqrt(area / arrow_width_factor)
                    width = arrow_width_factor * length
                    head_width = 2*width
                    head_length = 1.5*width
                    ax.arrow(xC[i], yC[i], dxR[i]*length, dyR[i]*length, zorder = 4, 
                             width = width, head_width=head_width, head_length=head_width, 
                             length_includes_head=True, color=reaction_color, linewidth=0, edgecolor=None, alpha=1)
                for i in range(len(storage)):
                    area = storage[i]*arrow_scale
                    length = np.sqrt(area / arrow_width_factor)
                    width = arrow_width_factor * length
                    head_width = 2*width
                    head_length = 1.5*width
                    ax.arrow(xC[i]+center_arrow_offset, yC[i], dxS[i]*length, dyS[i]*length,  zorder = 5,
                             width = width, head_width=head_width, head_length=head_width, 
                             length_includes_head=True, color=storage_color, linewidth=0, edgecolor=None, alpha=1)

                # fix the axis, add a title, etc
                ax.axis(axis_window)
                ax.axis('off')
                ax.set_title('%s: %s' % (runid, time_label), fontsize=fontsize)
                
                # add a legend to final run
                if irun==(nruns-1):

                    # dummy axis
                    ax = ax_list[itime][irun+1]

                    # add the map but make it white so it's effectively invisible
                    shp.iloc[iplot].plot(ax=ax, color = 'w', edgecolor='w', zorder=0.5)

                    # legend specs - coordinates and space between entries, we draw the legend manually instead of calling plt.legend()
                    #legend_loc = (582700, 4190300)
                    legend_loc = (axis_window[0] + 6000, axis_window[3] - 25000)
                    legend_yspace = 6000

                    # arrow size stuff
                    length = np.sqrt(arrow_scale_area / arrow_width_factor)
                    width = arrow_width_factor * length
                    head_width = 2*width
                    head_length = 1.5*width

                    # ... legend title
                    leg_offset = legend_yspace
                    ax.text(legend_loc[0],legend_loc[1]+2*leg_offset,'Magnitudes are Proportional\nto Arrow Base Area', fontsize=fontsize, va='center')
                    leg_offset = leg_offset - legend_yspace
                    # ... transport arrow
                    ax.arrow(legend_loc[0], legend_loc[1]+leg_offset, length, 0, width = width, head_width=head_width, head_length=head_length, length_includes_head=True, color=transport_color, edgecolor=None, alpha=1)
                    ax.text(legend_loc[0]+1.5*length,legend_loc[1]+leg_offset,'%0.0f Mg/d Transport' % arrow_scale_Mgd[param], fontsize=fontsize, va='center')
                    leg_offset = leg_offset - legend_yspace
                    # ... loading arrow
                    if is_there_loading(param):
                        ax.arrow(legend_loc[0], legend_loc[1]+leg_offset, length, 0, width = width, head_width=head_width, head_length=head_length, length_includes_head=True, color=loading_color, edgecolor=None, alpha=1)
                        ax.text(legend_loc[0]+1.5*length,legend_loc[1]+leg_offset,'%0.0f Mg/d Loading' % arrow_scale_Mgd[param],fontsize=fontsize, va='center')
                        leg_offset = leg_offset - legend_yspace
                    # ... source arrow
                    ax.arrow(legend_loc[0], legend_loc[1]+leg_offset, length, 0, width = width, head_width=head_width, head_length=head_length, length_includes_head=True, color=source_color, edgecolor=None, alpha=1)
                    ax.text(legend_loc[0]+1.5*length,legend_loc[1]+leg_offset,'%0.0f Mg/d Sources' % arrow_scale_Mgd[param],fontsize=fontsize, va='center')
                    leg_offset = leg_offset - legend_yspace
                    # ... sink arrow
                    ax.arrow(legend_loc[0], legend_loc[1]+leg_offset, length, 0, width = width, head_width=head_width, head_length=head_length, length_includes_head=True, color=sink_color, edgecolor=None, alpha=1)
                    ax.text(legend_loc[0]+1.5*length,legend_loc[1]+leg_offset,'%0.0f Mg/d Sinks' % arrow_scale_Mgd[param],fontsize=fontsize, va='center')
                    leg_offset = leg_offset - legend_yspace
                    # ... reaction arrow
                    ax.arrow(legend_loc[0], legend_loc[1]+leg_offset, length, 0, width = width, head_width=head_width, head_length=head_length, length_includes_head=True, color=reaction_color, edgecolor=None, alpha=1)
                    ax.text(legend_loc[0]+1.5*length,legend_loc[1]+leg_offset,'%0.0f Mg/d Net Reaction' % arrow_scale_Mgd[param],fontsize=fontsize, va='center')
                    leg_offset = leg_offset - legend_yspace
                    # ... storage arrow
                    ax.arrow(legend_loc[0], legend_loc[1]+leg_offset, length, 0, width = width, head_width=head_width, head_length=head_length, length_includes_head=True, color=storage_color, edgecolor=None, alpha=1)
                    ax.text(legend_loc[0]+1.5*length,legend_loc[1]+leg_offset,'%0.0f Mg/d Storage (dM/dt)' % arrow_scale_Mgd[param],fontsize=fontsize, va='center')

                    ax.axis(axis_window)
                    ax.axis('off')
                    ax.set_title('')

        # now that all the runs are plotted, loop through the times one last time and finish up the figures
        for itime in range(ntime):

            fig = fig_list[itime]
            ax = ax_list[itime]

            fig.suptitle('%s Budget' % param, fontsize=fontsize)
            fig.canvas.draw()
            fig.tight_layout(rect=[0, 0, 1, 0.98])
            fig.savefig(os.path.join(figure_path, '%s_Subembayment_Arrow_Map_%s_%s_Time%04d.png' % (run_list_str, tavg, param, itime)))
             
        plt.close('all')                    