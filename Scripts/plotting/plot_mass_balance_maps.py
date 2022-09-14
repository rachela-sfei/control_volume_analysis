
#########################
# import packages
#########################
import sys, os
import pandas as pd 
import geopandas as gpd
import numpy as np 
import matplotlib as mpl
import matplotlib.pyplot as plt
from importlib import reload
import control_volume_plotting_library as CVPL # plotting library must be in same folder as this script
reload(CVPL)

#########################
# user input
#########################

# run name 
#runid = 'G141_13to18_197'
#runid = 'FR13_025'
#runid = 'FR17_018'
#runid = 'FR18_006'
runid = 'FR13_003'
#runid = 'FR17_003'

# list of parameters to make plots for
param_list = ['TN', 'DIN', 'Algae', 'TN_include_sediment']

# list of "domains" which are groups of groups to plot
#domain_name_list = ['Whole_Bay_ABC','WB_South_Bay_ABC','WB_Subembayments','WB_Channel_Shoal','RMP_Subembayments',
#                    'RMP_Channel_Shoal','WB_and_RMP_Subembayments','WB_and_RMP_Channel_Shoal']
domain_name_list = ['WB_and_RMP_Subembayments','WB_and_RMP_Channel_Shoal']

# list of averaging periods to use for generating maps
averaging_period_list = ['Seasonal'] # can also add 'Annual', Monthly', and/or 'Weekly' assuming those time averages were created in step6 of create_balance_tables scripts

# base directory for the model runs and the output figures (in theory should be able to run on windows laptop with mounted drives or on server)
#base_dir = r'X:\hpcshared'
run_base_dir = '/richmondvol1/hpcshared'
figure_base_dir = '/chicagovol1/hpcshared/open_bay/bgc/figures'

# number of significant figures to include in the LARGEST reaction and transpor terms ... this
# will set the format for writing the numbers on the map, note this will set sig figs for reaction
# terms and fluxes will include one fewer sig figs, since they are generally bigger
nsigfig = 4

# drop zero reactions?
drop_zero_rx = True
zero_tol = 0.001

# use this function to define units, whether or not to include loading in the plot (set to false for 
# algae, zoopl, or anything else that doesn't come in through point sources), whether or not to 
# include name of parameter in the reaction name
def some_plotting_details(param):

    ''' 
    define some details based on parameter, user can add details if add parameters

    usage: 

        unit, include_load, include_param_in_rx_label = some_plotting_details(param)
    '''

    if param=='Algae':
        unit = 'Mg/d C'
        include_load = False
        include_param_in_rx_label = True
    elif param=='DIN':
        unit = 'Mg/d N'
        include_load = True
        include_param_in_rx_label = True
    elif param=='TN':
        unit = 'Mg/d N'
        include_load = True
        include_param_in_rx_label = True
    elif param=='TN_include_sediment':
        unit = 'Mg/d N'
        include_load = True
        include_param_in_rx_label = True

    return unit, include_load, include_param_in_rx_label

# here is where the user can define various sets of groups to plot
def get_domain_properties(domain_name):

    '''
    function defining properties of domains, which are groups of group that we plan to put on the same plot

    usage:

        figsize, group_list, connection_dict = get_domain_properties(domain_name)
    
    '''

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
        if FR_or_AGG=='AGG':

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
        if FR_or_AGG=='AGG':

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
        if FR_or_AGG=='AGG':

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
        if FR_or_AGG=='AGG':

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
        if FR_or_AGG=='AGG':

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
        if FR_or_AGG=='AGG':

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

    return figsize, group_list, connection_dict

# check if full resolution or not
if 'FR' in runid:
    FR_or_AGG = 'FR'
else:
    FR_or_AGG = 'AGG'

# path to shapefile that defines groups and their connectivity (assumes you are running this 
# script from the directory it is located in the Control_Volume_Analysis repository, need to change 
# shapefile_path if this isn't true)
shapefile_path = os.path.join('..','..','Definitions','group_shapefiles')
group_con_shp_fn = os.path.join(shapefile_path,'group_connectivity_shapefile_%s.shp' % FR_or_AGG)
group_def_shp_fn = os.path.join(shapefile_path,'group_definition_shapefile_%s.shp' % FR_or_AGG)

# set the font so everything lines up nicely
plt.rcParams['font.family'] = 'monospace' 

#############
# main
#############

# get string with concise list of runs (this tells us where to save the figures)
# note it is just one run so put it in brackets to make a list, so the function works right
run_list_str = CVPL.make_concise_runid_list_string([runid])

# path to figures, create if it does not exist
figure_path = os.path.join(figure_base_dir, run_list_str, 'mass_balance_maps')
if not os.path.exists(figure_path):
    os.makedirs(figure_path)

# get path to the balance table folder in the run folder
run_dir = CVPL.get_run_dir(run_base_dir, runid)
balance_table_dir = os.path.join(run_dir,'Balance_Tables')

# parameter name (Algae, DIN, TN, TN_include_sediment)
for param in param_list:

    # get some plotting details
    unit, include_load, include_param_in_rx_label = some_plotting_details(param)

    # make a list of the flux terms
    flux_list = ['%s,Flux In from N (Mg/d)' % param, 
                 '%s,Flux In from S (Mg/d)' % param,
                 '%s,Flux In from E (Mg/d)' % param, 
                 '%s,Flux In from W (Mg/d)' % param]

    # loop through the averaging periods
    for averaging_period in averaging_period_list:

        # read in the balance table
        balance_table_fn = os.path.join(balance_table_dir, '%s_Table_By_Group_%s.csv' % (param.lower(), averaging_period))
        try:
            df = pd.read_csv(balance_table_fn)
        except:
            raise Exception('could not load %s, check to make sure you generated %s averages '  % (balance_table_fn, averaging_period) +  
                            'when you ran step6_aggregate_in_time.py in the create_balance_tables scripts')
                            
        # convert time to datetime64
        df['time'] = df['time'].astype('datetime64[ns]')

        # find the list of reactions and make a list of their trimmed names (no units)
        reaction_list = []
        for col in df.columns:
            if ',d' in col and not 'dMass/dt' in col and not 'ZERO' in col:
                reaction_list.append(col)

        # drop zero reaction terms 
        if drop_zero_rx:
            for rx in reaction_list.copy():
                if (df[rx] == 0).all():
                    reaction_list.remove(rx)

        # trim units from reaction list for putting in legend (units are already in y axis label)
        reaction_list_trimmed = []
        for reaction in reaction_list:
            reaction1 = reaction.replace(' (Mg/d)','')
            if not include_param_in_rx_label:
                reaction1 = reaction1.replace(param,'').replace(',','').replace('_','')
                #reaction1 = reaction1[reaction1.find(',')+1:]
            reaction_list_trimmed.append(reaction1)
        nreact = len(reaction_list)

        # find the lenght of the longest reaction name (use this to format the reaction names in the plots)
        rx_name_length = 0
        for reaction in reaction_list_trimmed:
            n = len(reaction)
            if n > rx_name_length:
                rx_name_length = n
        rx_name_fmt = '%%%ds' % rx_name_length
        
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
        
        # loop through the domains you want to plot
        for domain_name in domain_name_list:
    
            # get properties for plotting this domain
            figsize, group_list, connection_dict = get_domain_properties(domain_name)
            
            # units and whether or not to include loading and whether to print parameter name in reaction terms
            unit, include_load, include_param_in_rx_label = some_plotting_details(param)
            
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

            # also trim the balance table to only include gropus in the group list
            ind = np.zeros(len(df),dtype=bool)
            for i in range(len(df)):
                if df['group'].iloc[i] in group_list:
                    ind[i] = True
            df1 = df.loc[ind]

            # for the purposes of determining significant figures, need to find the maximum reaction rate over all time
            # and the maximum flux over all time
            maxrx = df1[reaction_list].abs().max().max()
            maxflux = df1[flux_list].abs().max().max()

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
            
            # do the same thing but for the flux term, and subtract one from number of significant figures for fluxes
            digit1 = round(np.ceil(np.log10(maxflux)))
            digitN = digit1-(nsigfig-1) 
            if digit1>0: 
                if digitN>=0:
                    flux_fmt = '%%%d.0f' % digit1 
                else:
                    flux_fmt = '%%%d.%df' % (digit1, -digitN)
            else:
                flux_fmt = '%%.%df' % (-digitN)
        
            # get the unique times, sorted
            time = np.unique(df['time'].values)
            ntime = len(time)

            # now loop through the averaging periods for the purpose of plotting the mass budget
            for it in range(ntime):
            
                # select this time step
                ind = df['time'].values == time[it]
                df1 = df.loc[ind]

                # get the label for this time step
                time_label = df1.iloc[0]['Time Period']
            
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
                    ind = df1['group'] == group
                    rx_str = ''
                    for irx in range(len(reaction_list)):
                        rx_val = df1.loc[ind][reaction_list[irx]].values[0]
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
                        ind = df1['group'] == connection
                        flux_val = df1.loc[ind][flux_column].values[0]
            
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
                ax.set_title('%s: averaged over %s\n%s mass balance (units are %s) ' % (runid, 
                                                    time_label, 
                                                    param, unit))
                plt.savefig(os.path.join(figure_path, '%s_%s_%s_mass_balance_map_%s_%04d.png' % (run_list_str, domain_name, param, averaging_period, it)))
                plt.close()
                        
                                