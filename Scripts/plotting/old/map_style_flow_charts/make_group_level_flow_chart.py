
import sys, os
import pandas as pd 
import geopandas as gpd
import numpy as np 
import matplotlib as mpl
import matplotlib.pyplot as plt
plt.rcParams['font.family'] = 'monospace'

#########################
# user input
#########################


# run name and water year
run_id = 'G141_13to18_182'
wy_list = [2013,2014,2015,2016,2017,2018]
#run_id = 'FR13_025'
#wy_list = [2013]
#run_id = 'FR17_018'
#wy_list = [2017]
#run_id = 'FR18_006'
#wy_list = [2018]
#run_id = 'FR13_003'
#wy_list = [2013]
#run_id = 'FR17_003'
#wy_list = [2017]


# include parameter name in reaction label? no for Algae, yes for DIN
include_param_in_rx_label = False

# number of significant figures to include in the LARGEST reaction and transpor terms ... this
# will set the format for writing the numbers on the map
nsigfig = 4


# check if full resolution or not
if 'FR' in run_id:
    FR = True
else:
    FR = False

# lists to iterate over in for loops
averaging_period_list = ['annual', 'seasonal', 'monthly'] # can also add 'weekly'
param_list = ['DIN', 'TN', 'Algae', 'TN_include_sediment']
domain_name_list = ['Whole_Bay_ABC','WB_South_Bay_ABC','WB_Subembayments','WB_Channel_Shoal','RMP_Subembayments','RMP_Channel_Shoal','WB_and_RMP_Subembayments','WB_and_RMP_Channel_Shoal']


# parameter name (Algae, DIN, TN, TN_include_sediment)
for param in param_list:

    # name the domain we are plotting here
    for domain_name in domain_name_list:


        if domain_name == 'Whole_Bay_ABC':
        
        
            # figure size
            figsize = (90,90)
        
            group_list = ['L','K','J','I','H','G','F','E','D','C','B','A','V','U1','T1','S1','U2','T2','S2','X','W','Z','Y',
                          'RB','Alcatraz_Whirlpool','CB_East_Exchange','Y2','Berkeley_Marina','Larkspur_Ferry',
                          'SE_San_Pablo_Shoal','San_Pablo_Channel','San_Pablo_Shoal','San_Pablo_Exchange',
                          'Stockton_Channel_Suisun_Bay','Sacramento_Channel','Roe_Island','Chipps_Island','Grizzly_Bay',
                          'Suisun_Slough','Suisun-Fairfield','Squiggly_Creek','LSB']
        
            # dictionary of flux arrows to plot (key is the group name, value is a list of directions/faces)
            connection_dict = {'L' : ['S','E','N'],
                               'K' : ['S','E','N'],
                               'J' : ['E','N'],
                               'I' : ['N'],
                               'H' : ['E','N'],
                               'G' : ['E','N'],
                               'F' : ['E','N'],
                               'E' : ['N'],
                               'D' : ['E','N'],
                               'C' : ['E','N'],
                               'B' : ['E','N'],
                               'A' : ['N'],
                               'V' : ['E'],
                               'U1' : ['E','N'],
                               'T1' : ['E','N'],
                               'S1' : ['N'],
                               'S2' : ['E','N'],
                               'U2' : ['E','N'],
                               'T2' : ['E','N'],
                               #'S2' : ['N'],
                               'X' : ['E','N'],
                               'W' : ['E'],
                               'Z' : ['N'], # note Z to E is defined backwards b/c multiply connected, too lazy to fix, so use Y to W instead
                               'Y' : ['W','E','N','S'],
                               'Berkeley_Marina' : ['S'],
                               'Alcatraz_Whirlpool' : ['W','E'],
                               'RB' : ['S'],
                               'Y2' : ['W','N','E'],
                               'CB_East_Exchange' : ['W','N','E'],
                               'Larkspur_Ferry' : ['S','E','N'],
                               'SE_San_Pablo_Shoal' : ['N','W'],
                               'San_Pablo_Channel' : ['E'], 
                               'San_Pablo_Exchange' : ['N','S'],
                               'Petaluma' : ['S'],
                               'Sonoma' : ['S'],
                               'Napa' : ['S'],
                               'Stockton_Channel_Suisun_Bay' : ['E'],
                               'Sacramento_Channel' : ['W','E'],
                               'Roe_Island' : ['N','S','E','W'],
                               'Chipps_Island' : ['S','E','W'],
                               'Grizzly_Bay' : ['S'],
                               'Suisun_Slough' : ['S'],
                               'Suisun-Fairfield' : ['N','S'],
                               'Squiggly_Creek' : ['E']
                               }
            # make some adjustments for agg grid
            if not FR:

                # in the AGG grid, Suisun_Slough and Sqiggly Creek are lumped in with Suisun-Farfield
                group_list.remove('Suisun_Slough')
                group_list.remove('Squiggly_Creek')                          
                del connection_dict['Suisun_Slough']
                del connection_dict['Squiggly_Creek']
                connection_dict['Suisun-Fairfield'] = ['W','E']

                # Petaluma and Sonoma are lumped in w/ San Pably Bay in AGG grid so we are missing these flows from N into SPB
                del connection_dict['Petaluma'] 
                del connection_dict['Sonoma'] 

                # these small connections don't exist in the AGG grid
                connection_dict['Larkspur_Ferry'].remove('S') 
                connection_dict['S2'].remove('N') 
                connection_dict['SE_San_Pablo_Shoal'].remove('W') 
        
        if domain_name == 'Whole_Bay_New_CVs':
        
        
            # figure size
            figsize = (90,90)
        
            group_list = ['SB_WB_west_shoal_north_half','SB_WB_west_shoal_south_half',
                          'SB_WB_east_shoal_north_half','SB_WB_east_shoal_south_half',
                          'SB_WB_channel_north_half','SB_WB_channel_south_half',
                          'Z','Y',
                          'RB','Alcatraz_Whirlpool','CB_East_Exchange','Y2','Berkeley_Marina','Larkspur_Ferry',
                          'SE_San_Pablo_Shoal','San_Pablo_Channel','San_Pablo_Shoal','San_Pablo_Exchange',
                          'Stockton_Channel_Suisun_Bay','Sacramento_Channel','Roe_Island','Chipps_Island','Grizzly_Bay',
                          'Suisun_Slough','Suisun-Fairfield','Squiggly_Creek','LSB']
        
            # dictionary of flux arrows to plot (key is the group name, value is a list of directions/faces)
            connection_dict = {'SB_WB_west_shoal_north_half' : ['S','E'],
                               'SB_WB_channel_north_half': ['N','S','E'],
                               'SB_WB_east_shoal_north_half' : ['S'],
                               'SB_WB_west_shoal_south_half' : ['S','E'],
                               'SB_WB_channel_south_half' : ['S','E'],
                               'Z' : ['N'], # note Z to E is defined backwards b/c multiply connected, too lazy to fix, so use Y to W instead
                               'Y' : ['W', 'E','N','S'],
                               'Berkeley_Marina' : ['S'],
                               'Alcatraz_Whirlpool' : ['W','E'],
                               'RB' : ['S'],
                               'Y2' : ['W','N','E'],
                               'CB_East_Exchange' : ['W','N','E'],
                               'Larkspur_Ferry' : ['S','E','N'],
                               'SE_San_Pablo_Shoal' : ['N','W'],
                               'San_Pablo_Channel' : ['E'], 
                               'San_Pablo_Exchange' : ['N','S'],
                               'Petaluma' : ['S'],
                               'Sonoma' : ['S'],
                               'Napa' : ['S'],
                               'Stockton_Channel_Suisun_Bay' : ['E'],
                               'Sacramento_Channel' : ['W','E'],
                               'Roe_Island' : ['N','S','E','W'],
                               'Chipps_Island' : ['S','E','W'],
                               'Grizzly_Bay' : ['S'],
                               'Suisun_Slough' : ['S'],
                               'Suisun-Fairfield' : ['N','S'],
                               'Squiggly_Creek' : ['E']
                               }

            # make some adjustments for agg grid
            if not FR:

                # in the AGG grid, Suisun_Slough and Sqiggly Creek are lumped in with Suisun-Farfield
                group_list.remove('Suisun_Slough')
                group_list.remove('Squiggly_Creek')                          
                del connection_dict['Suisun_Slough']
                del connection_dict['Squiggly_Creek']
                connection_dict['Suisun-Fairfield'] = ['W','E']

                # Petaluma and Sonoma are lumped in w/ San Pably Bay in AGG grid so we are missing these flows from N into SPB
                del connection_dict['Petaluma'] 
                del connection_dict['Sonoma'] 

                # these small connections don't exist in the AGG grid
                connection_dict['Larkspur_Ferry'].remove('S') 
                connection_dict['S2'].remove('N') 
                connection_dict['SE_San_Pablo_Shoal'].remove('W') 
        
        if domain_name == 'WB_South_Bay_ABC':
        
            # figure size
            figsize = (36,50)
        
            # list of the groups to plot
            group_list = ['L','K','J','I','H','G','F','E','D','C','B','A','V','U1','T1','S1','U2','T2','S2','X','W','Z','Y']
            
            # dictionary of flux arrows to plot (key is the group name, value is a list of directions/faces)
            connection_dict = {'L' : ['S','E','N'],
                               'K' : ['S','E','N'],
                               'J' : ['E','N'],
                               'I' : ['N'],
                               'H' : ['E','N'],
                               'G' : ['E','N'],
                               'F' : ['E','N'],
                               'E' : ['N'],
                               'D' : ['E','N'],
                               'C' : ['E','N'],
                               'B' : ['E','N'],
                               'A' : ['N'],
                               'V' : ['E'],
                               'U1' : ['E','N'],
                               'T1' : ['E','N'],
                               'S1' : ['N'],
                               'S2' : ['E','N'],
                               'U2' : ['E','N'],
                               'T2' : ['E','N'],
                               #'S2' : ['N'],
                               'X' : ['E','N'],
                               'W' : ['E','N'],
                               'Z' : ['N'], # note Z to E is defined backwards b/c multiply connected, too lazy to fix, so use Y to W instead
                               'Y' : ['W','E','N']}

            # make some adjustments for agg grid
            if not FR:

                # these small connections don't exist in the AGG grid
                connection_dict['S2'].remove('N') 

        elif domain_name == 'WB_Subembayments':
        
            # figure size
            figsize = (16,16)
        
            # dictionary with coordinates of center arrows along with the name of the corresponding group
            group_list = ['Suisun_Bay', 'San_Pablo_Bay', 'Central_Bay_WB', 'SB_WB', 'LSB']
        
            # dictionary of flux arrows to plot (key is the group name, value is a list of directions/faces) 
            connection_dict = {
                               'Suisun_Bay' : ['W','N','E'],
                               'San_Pablo_Bay' : ['S'],
                               'Napa' : ['S'],
                               'Petaluma' : ['S'],
                               'Sonoma' : ['S'], 
                               'Central_Bay_WB' : ['W', 'S'], 
                               'SB_WB' : ['S']
                               }

            # make some adjustments for agg grid
            if not FR:

                # Petaluma and Sonoma are lumped in w/ San Pably Bay in AGG grid so we are missing these flows from N into SPB
                del connection_dict['Petaluma'] 
                del connection_dict['Sonoma'] 

        elif domain_name == 'WB_Channel_Shoal':
        
            # figure size
            figsize = (30,30)
        
            # dictionary with coordinates of center arrows along with the name of the corresponding group
            group_list = ['SB_WB_west_shoal', 
                          'SB_WB_east_shoal','SB_WB_channel', 'LSB']
        
            # dictionary of flux arrows to plot (key is the group name, value is a list of directions/faces) 
            connection_dict = {
                               'SB_WB_channel' : ['S','N','E','W'], 
                               'SB_WB_east_shoal' : ['N'], 
                               'SB_WB_west_shoal' : ['S']
                               }


        elif domain_name == 'RMP_Subembayments':
        
            # figure size
            figsize = (16,16)
        
            # dictionary with coordinates of center arrows along with the name of the corresponding group
            group_list = ['Suisun_Bay', 'San_Pablo_Bay', 'Central_Bay_RMP', 'SB_RMP', 'LSB']
        
            # dictionary of flux arrows to plot (key is the group name, value is a list of directions/faces) 
            connection_dict = {'Suisun_Bay' : ['W','N','E'],
                               'San_Pablo_Bay' : ['S'],
                               'Napa' : ['S'],
                               'Petaluma' : ['S'],
                               'Sonoma' : ['S'], 
                               'Central_Bay_RMP' : ['W', 'S'], 
                               'SB_RMP' : ['S']}

            # make some adjustments for agg grid
            if not FR:

                # Petaluma and Sonoma are lumped in w/ San Pably Bay in AGG grid so we are missing these flows from N into SPB
                del connection_dict['Petaluma'] 
                del connection_dict['Sonoma'] 

        
        elif domain_name == 'RMP_Channel_Shoal':
        
            # figure size
            figsize = (30,30)
        
            # dictionary with coordinates of center arrows along with the name of the corresponding group
            group_list = ['SB_RMP_west_shoal', 'SB_RMP_east_shoal','SB_RMP_channel', 'LSB']
        
            # dictionary of flux arrows to plot (key is the group name, value is a list of directions/faces) 
            connection_dict = {
                               'SB_RMP_channel' : ['S','N','E','W'], 
                               'SB_RMP_east_shoal' : ['N'], 
                               'SB_RMP_west_shoal' : ['S','N']
                               }

        elif domain_name == 'WB_and_RMP_Subembayments':
        
            # figure size
            figsize = (16,16)
        
            # dictionary with coordinates of center arrows along with the name of the corresponding group
            group_list = ['Suisun_Bay', 'San_Pablo_Bay', 'Central_Bay_WB', 'SB_WB_north_half', 'SB_WB_south_half', 'LSB']
        
            # dictionary of flux arrows to plot (key is the group name, value is a list of directions/faces) 
            connection_dict = {
                               'Suisun_Bay' : ['W','N','E'],
                               'San_Pablo_Bay' : ['S'],
                               'Napa' : ['S'],
                               'Petaluma' : ['S'],
                               'Sonoma' : ['S'], 
                               'Central_Bay_WB' : ['W', 'S'], 
                               'SB_WB_north_half' : ['S'], 
                               'SB_WB_south_half' : ['S'],
                               }

            # make some adjustments for agg grid
            if not FR:

                # Petaluma and Sonoma are lumped in w/ San Pably Bay in AGG grid so we are missing these flows from N into SPB
                del connection_dict['Petaluma'] 
                del connection_dict['Sonoma'] 
        
        elif domain_name == 'WB_and_RMP_Channel_Shoal':
        
            # figure size
            figsize = (30,30)
        
            # dictionary with coordinates of center arrows along with the name of the corresponding group
            group_list = ['SB_WB_west_shoal_north_half','SB_WB_west_shoal_south_half',
                          'SB_WB_east_shoal_north_half','SB_WB_east_shoal_south_half',
                          'SB_WB_channel_north_half','SB_WB_channel_south_half']
        
            # dictionary of flux arrows to plot (key is the group name, value is a list of directions/faces) 
            connection_dict = {'SB_WB_west_shoal_north_half' : ['S','E'],
                               'SB_WB_channel_north_half': ['N','S','E'],
                               'SB_WB_east_shoal_north_half' : ['N','S'],
                               'SB_WB_west_shoal_south_half' : ['S','E'],
                               'SB_WB_channel_south_half' : ['S','E']
                               }
        
        # path to shapefile that defines groups and their connectivity
        if FR:
            group_con_shp_fn = '/richmondvol1/hpcshared/NMS_Projects/Control_Volume_Analysis/Definitions/shapefiles/group_connectivity_shapefile_FR.shp'
            group_def_shp_fn = '/richmondvol1/hpcshared/NMS_Projects/Control_Volume_Analysis/Definitions/shapefiles/group_definition_shapefile_FR.shp'
        else:
            group_con_shp_fn = '/richmondvol1/hpcshared/NMS_Projects/Control_Volume_Analysis/Definitions/shapefiles/group_connectivity_shapefile_AGG.shp'
            group_def_shp_fn = '/richmondvol1/hpcshared/NMS_Projects/Control_Volume_Analysis/Definitions/shapefiles/group_definition_shapefile_AGG.shp'
        
        # balance table path
        balance_table_fn = os.path.join('../../Balance_Tables/%s/%s_Table_By_Group.csv' % (run_id, param.lower()))
        
        # units and whether or not to include loading
        if param=='Algae':
            unit = 'Mg/d C'
            include_load = False
        elif param=='DIN':
            unit = 'Mg/d N'
            include_load = True
        elif param=='TN':
            unit = 'Mg/d N'
            include_load = True
        elif param=='TN_include_sediment':
            unit = 'Mg/d N'
            include_load = True
        
        #########################
        # main
        #########################
        
        # make output file folder
        output_dir = '../../Plots/%s/group_level_mass_balance_maps/' % run_id
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # load balance table, convert time to datetime64
        df = pd.read_csv(balance_table_fn)
        df['time'] = df['time'].astype('datetime64[ns]')
        # tri to included groups
        #ind = []
        #for group in df['group']:
        #    if group in group_list:
        #        ind.append(True)
        #    else:
        #        ind.append(False)
        #df = df.loc[ind]
        
        # find the list of reactions and make a list of their trimmed names (no units)
        reaction_list = []
        for col in df.columns:
            if ',d' in col and not 'dMass/dt' in col and not 'ZERO' in col:
                reaction_list.append(col)
        reaction_list_trimmed = []
        for reaction in reaction_list:
            reaction1 = reaction.replace(' (Mg/d)','')
            if not include_param_in_rx_label:
                reaction1 = reaction1.replace(param,'').replace(',','').replace('_','')
                #reaction1 = reaction1[reaction1.find(',')+1:]
            reaction_list_trimmed.append(reaction1)
        nreact = len(reaction_list)
        
        # sum the reactions to get the net reaction, and add net reaction to list
        df['Net Rx (Mg/d)'] = df[reaction_list].sum(axis=1)
        reaction_list.append('Net Rx (Mg/d)')
        reaction_list_trimmed.append('Net Rx')
        
        # add storage to reaction list -- it's not really a reaction, but we want to print it with the reactions
        reaction_list.append('%s,dMass/dt (Mg/d)' % param)
        reaction_list_trimmed.append('dM/dt')
        
        # add net loading to reaction list
        if include_load:
            reaction_list.append('%s,Net Load (Mg/d)' % param)
            reaction_list_trimmed.append('Load')
        
        # make a list of the flux terms
        flux_list = ['%s,Flux In from N (Mg/d)' % param, 
                     '%s,Flux In from S (Mg/d)' % param,
                     '%s,Flux In from E (Mg/d)' % param, 
                     '%s,Flux In from W (Mg/d)' % param]
        
        # load shapefiles
        gdf_con = gpd.read_file(group_con_shp_fn)
        gdf_def = gpd.read_file(group_def_shp_fn)
        
        # add centroid column
        gdf_con['centroid'] = gdf_con.centroid
        gdf_def['centroid'] = gdf_def.centroid
        
        # trim group shapefile to just the included groups
        ind = []
        for group in group_list:
            i = np.argmax(gdf_def['feature'].values==group)
            ind.append(i)
        gdf_def = gdf_def.iloc[ind]
        
        # loop through water years in water year list 
        for wy in wy_list:

            # loop through the averaging periods
            for averaging_period in averaging_period_list:
            
                # depending on averaging period, define a list of start times and end times for those averaging periods
                if averaging_period == 'annual':
                    start_times = np.array(['%d-10-01' % (wy-1)]).astype('datetime64[ns]')
                    end_times   = np.array(['%d-10-01' % wy]).astype('datetime64[ns]')
                elif averaging_period == 'seasonal':
                    start_times = np.array(['%d-10-01' % (wy-1), '%d-01-01' % wy, '%d-04-01' % wy, '%d-07-01' % wy]).astype('datetime64[ns]')
                    end_times   = np.array(['%d-01-01' % wy, '%d-04-01' % wy, '%d-07-01' % wy, '%d-10-01' % wy]).astype('datetime64[ns]') 
                elif averaging_period == 'monthly':
                    start_times = np.array(['%d-10-01' % (wy-1),'%d-11-01' % (wy-1),'%d-12-01' % (wy-1),
                                            '%d-01-01' % wy, '%d-02-01' % wy, '%d-03-01' % wy,
                                            '%d-04-01' % wy, '%d-05-01' % wy, '%d-06-01' % wy,
                                            '%d-07-01' % wy, '%d-08-01' % wy, '%d-09-01' % wy]).astype('datetime64[ns]')
                    end_times   = np.array(['%d-11-01' % (wy-1),'%d-12-01' % (wy-1),
                                            '%d-01-01' % wy, '%d-02-01' % wy, '%d-03-01' % wy,
                                            '%d-04-01' % wy, '%d-05-01' % wy, '%d-06-01' % wy,
                                            '%d-07-01' % wy, '%d-08-01' % wy, '%d-09-01' % wy, '%d-10-01' % wy]).astype('datetime64[ns]')
                elif averaging_period == 'weekly':
                    times = np.array([np.datetime64('%d-10-01' % (wy-1),'ns') + np.timedelta64(7,'D')*n for n in range(55)])
                    times = times[times<=np.datetime64('%d-10-01' % wy)]
                    start_times = times[0:-1]
                    end_times = times[1:]
                
                
                # loop through the averaging periods just for the purpose of finding the number of significant figures 
                # we need in the reaction terms and the flux terms
                ntime = len(start_times)
                maxrx = 0
                maxflux = 0
                for it in range(ntime):
                
                    # take the average over this averaging period
                    ind = np.logical_and(df['time'] >= start_times[it], df['time'] <= end_times[it])
                    df1 = df.loc[ind].groupby('group').mean()
                
                    # find the max reaction and add to running max
                    maxrx1 = np.abs(df1[reaction_list].values).max()  
                    if maxrx1>maxrx:
                        maxrx = maxrx1.copy()
                
                    # find the max flux and add to running max
                    maxflux1 = np.abs(df1[flux_list].values).max()  
                    if maxflux1>maxflux:
                        maxflux = maxflux1.copy()
                
                # find the lenght of the longest reaction name
                rx_name_length = 0
                for reaction in reaction_list_trimmed:
                    n = len(reaction)
                    if n > rx_name_length:
                        rx_name_length = n
                rx_name_fmt = '%%%ds' % rx_name_length
                
                # use nsigfig significant figures for largest reaction term... here we calculate the 
                # decimal place of the first and nth, and use it to format the reaction
                digit1 = round(np.ceil(np.log10(maxrx)))
                digitN = digit1-nsigfig
                if digit1>0: 
                    if digitN>=0:
                        rx_fmt = '%%%d.0f' % digit1 
                    else:
                        rx_fmt = '%%%d.%df' % (digit1, -digitN)
                else:
                    rx_fmt = '%%0.%df' % (-digitN)
                
                # do the same thing but for the flux term
                digit1 = round(np.ceil(np.log10(maxflux)))
                digitN = digit1-(nsigfig-1) ### subtract one from number of significant figures for fluxes
                if digit1>0: 
                    if digitN>=0:
                        flux_fmt = '%%%d.0f' % digit1 
                    else:
                        flux_fmt = '%%%d.%df' % (digit1, -digitN)
                else:
                    flux_fmt = '%%.%df' % (-digitN)
                
                # now loop through the averaging periods for the purpose of plotting the mass budget
                for it in range(ntime):
                
                    # take the average over this averaging period
                    ind = np.logical_and(df['time'] >= start_times[it], df['time'] <= end_times[it])
                    df1 = df.loc[ind].groupby('group').mean()
                 
                    # make a plot of the groups
                    fig, ax = plt.subplots(figsize=figsize)
                    gdf_def.plot(ax=ax, color='w', edgecolor='b')
                    ax.axis('off')
                
                    # loop through the groups and add the reactions at the centroid
                    for group in group_list:
                
                        # get the centroid for this group
                        xc, yc =  gdf_def.loc[gdf_def['feature']==group]['centroid'].values[0].xy
                        xc = xc[0]
                        yc = yc[0]
                
                        # build reaction string
                        rx_str = ''
                        for irx in range(len(reaction_list)):
                            rx_val = df1.loc[group][reaction_list[irx]]
                            if rx_val >= 0:
                                extra_space = ' '
                            else:
                                extra_space = ''
                            rx_str = rx_str + rx_name_fmt % reaction_list_trimmed[irx] + ' = ' + extra_space + rx_fmt % rx_val + '\n'
                        rx_str = rx_str[0:-1]
                
                        # plot at centroid
                        ax.text(xc,yc,rx_str,ha='center',va='center')
                
                    # loop through the connections and add arrows at the centroid, pointing perpendicular to the boundary
                    for connection in connection_dict.keys():
                
                        for side in connection_dict[connection]:
                
                            # features are like "L to N" or "A to E"
                            feature = '%s to %s' % (connection, side)
                
                            # name of column corresponding to the flux
                            flux_column = '%s,Flux In from %s (Mg/d)' % (param, side)
                
                            # get the centroid for this group
                            xc, yc =  gdf_con.loc[gdf_con['feature']==feature]['centroid'].values[0].xy
                            xc = xc[0]
                            yc = yc[0]
                
                            # get the first and last coordinates of the line
                            line = gdf_con.loc[gdf_con['feature']==feature]['geometry'].values[0]
                            if line.type == 'LineString':
                                line1 = line
                                line2 = line
                            elif line.type == 'MultiLineString':
                                line1 = line[0]
                                while line1.type == 'MultiLineString':
                                    line1 = line1[0]
                                line2 = line[-1]
                                while line2.type == 'MultiLineString':
                                    line2 = line2[-1]
                            x1, y1 = line1.coords[0]
                            x2, y2 = line2.coords[-1]
                
                            # calculate the left arrow angle so it is perpendicular to the line
                            angle = np.arctan2(x2-x1, y1-y2)*180/np.pi
                
                            # get the flux value
                            flux_val = df1.loc[connection][flux_column] 
                
                            # flip the arrow angle if the flux is negative and make the flux positive
                            if flux_val<0:
                                angle = angle + 180
                                flux_val = -flux_val
                
                            # make the string
                            flux_str = flux_fmt % flux_val
                
                            # add the text arrow
                            bbox_props = dict(boxstyle='larrow',fc='w',ec='k')
                            t = ax.text(xc,yc,flux_str,ha='center',va='center',rotation=angle,bbox=bbox_props)
                
                    # save
                    fig.tight_layout(rect=[0, 0.03, 1, 0.95])
                    ax.set_title('%s: average over %s to %s\n%s mass balance (units are %s) ' % (run_id, 
                                                        np.datetime_as_string(start_times[it],unit='D'), 
                                                        np.datetime_as_string(end_times[it],unit='D'), 
                                                        param, unit))
                    plt.savefig(os.path.join(output_dir, 'Mass_Budget_Map_%s_WY%d_%s_%s_%s_%03d.png' % (run_id,wy,param,domain_name,averaging_period,it)))
                    plt.close()
                    
                            