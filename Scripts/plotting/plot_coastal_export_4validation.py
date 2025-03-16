'''

Use new "Whole_Bay" group to work up a mass budget for the whole bay

For the parameter specified (e.g. DIN, TN, Algae)
creates a plot with 3xN subplots where N is the number of runs 
you want to compare to each other (you can just plot one run if you want)

Row 1: stack plot comparing point source loading, delta influx, influx from 
minor tributaries, storage (dM/dt), net reactions, and outflux through the golden gate
for the parameter specified

Row 2: stack plot showing each of the reactions for the parameter specified 
(ignoring groups of terms that sum to zero) along with the net reaction and the
storage term (dM/dt)

Row 3: breaks outflux through golden gate into components of the parameter 
specified (e.g. if parameter is DIN, breaks DIN export down into NH4 and NO3), 
and also compares export to the net loading from the tribuaries (including delta)
and the point sources

Allie King Sept 2022
'''

########################################################################################
## import python packages
########################################################################################

import sys, os
import pandas as pd
import numpy as np
import matplotlib.pylab as plt
import datetime as dt
import matplotlib.dates as mdates
from scipy import signal
if not 'DISPLAY' in os.environ:
    import matplotlib
    matplotlib.use('agg')
    plt.switch_backend('Agg')
from matplotlib.backends.backend_pdf import PdfPages
from importlib import reload
import control_volume_plotting_library as CVPL # plotting library must be in same folder as this script
reload(CVPL)


#########################################################################################
## user input
#########################################################################################

# autoscale x axis (if you set to False, script will set min/max based on water year range)
# note: this option was added for the 2022 HAB simulations, you probably want to set it to False for everything else
autoscale_x = False

# list of runid, water year, servers, and vol1/vol2
runid = 'G141_13to22_016'
wystr = 'WY13to22'
#runid = 'FR21_002'
#wystr = 'WY2021'
server = 'chicago'
vol = 'vol2'

## composite parameter (must match suffix of balance table)
param_list = ['Algae', 'DIN', 'TN', 'TN_plus_DetNS12']

# list of types of time aggregation (e.g. ['Filtered','Cumulative','Daily'])
#tavg_list = ['Filtered','Cumulative']
tavg_list = ['Cumulative','Filtered']

# start with the default color cycle and add even more colors because the number of reactions is OUT OF CONTROL!
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
          'fuchsia','gold','lawngreen','aqua','lavender','navy','lightgray']

# flag to include a row with the subembayment-by-subembayment net reaction for this parameter
# and the list of subembayments to use (let's use RMP) and a list w/ nice names for legend
include_subembayment_assim = True
subembayment_list = ['LSB', 'SB_RMP', 'Central_Bay_RMP', 'San_Pablo_Bay', 'Suisun_Bay'] 
subembayment_nice = ['Lower South Bay', 'South Bay (RMP)','Central Bay (RMP)', 'San Pablo Bay', 'Suisun Bay']

#########################################################################################
## functions
#########################################################################################

# finction to list of components OF THE COASTAL EXPORT (need not include benthic components, 
# because they can't flow out of the bay as they are stuck to the bed) given the parameter
def return_components_list(param):

    if param == 'DIN':
        components_list = ['NH4','NO3']
    elif param == 'TN':
        components_list = ['NH4','NO3','PON1','PON2','DON','N-Zoopl','N-Algae'] 
    elif param == 'TN_include_sediment':
        components_list = ['NH4','NO3','PON1','PON2','DON','N-Zoopl','N-Algae'] 
    elif param == 'TN_plus_DetNS12':
        components_list = ['NH4','NO3','PON1','PON2','DON','N-Zoopl','N-Algae'] 
    else:
        components_list = [param]
    ncom = len(components_list)

    return components_list, ncom

# tells you if the parameter is benthic (if it's benthic, don't include the export plot row, because it
# doesn't get transported, so everything is zero)
def is_it_benthic(param):

    if param in ['DetNS1','DetNS2','DetNS12','OONS1','OONS2','OONS12',
                 'TotalDetNS1','TotalDetNS1','TotalDetNS','DiatS1']:
        is_benthic = True
    else:
        is_benthic = False

    return is_benthic

def pos_neg(array):

    '''returns two arrays with shape array, one with positive entries, other with negative,
    all other entries are zero'''

    shape = np.shape(array)
    pos = np.zeros(shape)
    neg = np.zeros(shape)

    ind = array>0
    pos[ind] = array[ind]

    ind = array<0
    neg[ind] = array[ind]

    return pos, neg

#########################################################################################
## main
#########################################################################################

## balance table folder
run_base_dir = '/%s%s/hpcshared' % (server,vol)
run_dir = CVPL.get_run_dir(run_base_dir, runid)
balance_table_dir = os.path.join(run_dir,'Balance_Tables')

# get strings with concise lists of runs and water years
run_list_str = CVPL.make_concise_runid_list_string([runid])

# base directory for the output figures 
figure_path = run_dir
print('\nfigures will be saved here: %s\n' % figure_path)

# from the list of water year strings, get a list of integer water years, then convert back
# to a concise list of water year strings for naming the figure
wy_list = CVPL.list_of_wy_str_2_list_of_int_wys([wystr])   # note this variable gets overridden later
wy_list_str = CVPL.make_concise_water_year_list_string(wy_list)

# loop through different time averages: daily, spring-neap filter, cumulative
for tavg in tavg_list:

    # filename
    pdffile = '%s_%s_Coastal_Export_%s.pdf' % (run_list_str, wy_list_str, tavg)

    # for figure labeling
    if tavg=='Filtered':
        tavg_str = 'Spring-Neap Filtered'
    else:
        tavg_str = tavg

    # for loading balance tables
    if tavg=='Daily':
        tavg_BT_str = ''
    else:
        tavg_BT_str = '_' + tavg

    # units
    if tavg=='Cumulative':
        units = 'Mg'
        units_plot = 'Gg'
        divide_by = 1000 # convert Mg to Gg in plots
    else:
        units = 'Mg/d'
        units_plot = 'Mg/d'
        divide_by = 1 # leave as Mg/d in plots

    with PdfPages(os.path.join(figure_path, pdffile)) as pdf:

        # loop through parameters
        for param in param_list:

            # get list of components for this parameter
            components_list, ncom = return_components_list(param)

            # compute the number of rows in the plots, depends on whether parameter is benthic and whether
            # breakdown of net reaction by subembayment is included
            nrows = 2
            if not is_it_benthic(param):
                nrows += 1
            if include_subembayment_assim:
                nrows += 1
            
            # initialize 3 panel figure with complete mass balance, reactions, and export composition
            fig, ax = plt.subplots(nrows,1,figsize=(8.5,11))
        
            # before we plot the different runs, take a sneak peek to find a list of all the reactions
            master_source_list = []
            master_sink_list = []
                
            # load up the balance table data for the parameter of interest
            input_fn = os.path.join(balance_table_dir,'%s_Table_By_Group%s.csv' % (param.lower(), tavg_BT_str))
            data = pd.read_csv(input_fn)

            # get the reaction lists
            master_source_list = []
            master_sink_list = []
            for col in data.columns:
                if not 'ZERO' in col:
                    if not ',dMass/' in col:
                        if ',d' in col:
                            if data[col].mean()>0:
                                master_source_list.append(col)
                            elif data[col].mean()<0:
                                master_sink_list.append(col)

            # sometimes a term may be a source or a sink, such as oxygen reaeration...
            # in this case our algorithim might have flagged it as a source in one run and 
            # a sink in the other (depending if the average was positive or negative) ... go through
            # the source terms and make sure none of them appear as sinks as well
            # search for any such terms and delete them from the sink list
            for source in master_source_list:
                if source in master_sink_list:
                    master_sink_list.remove(source)
        
            # combine master sources and sinks to get reactions
            master_reaction_list = []
            for rx in master_sink_list:
                master_reaction_list.append(rx)
            for rx in master_source_list:
                master_reaction_list.append(rx)

            # trim the units for concise legend
            master_reaction_list_trimmed = []
            for rx in master_reaction_list:
                master_reaction_list_trimmed.append(rx.replace(' (%s)' % units,''))

            # track the min and max reaction by subembayment to see if it is always above or below zero
            if include_subembayment_assim:
                max_rx_by_sub = 0
                min_rx_by_sub = 0
            
            # load up the balance table data for the parameter of interest
            input_fn = os.path.join(balance_table_dir,'%s_Table_By_Group%s.csv' % (param.lower(), tavg_BT_str))
            data = pd.read_csv(input_fn)

            # also load up balance tables for the component parameters 
            data_components = []
            for ic in range(ncom):
                input_fn = os.path.join(balance_table_dir,'%s_Table_By_Group%s.csv' % (components_list[ic].lower(), tavg_BT_str))
                try:
                    data_component = pd.read_csv(input_fn)
                except:
                    data_components.append(None)
                else:
                    data_components.append(data_component)

            # select the subembayment data and load up into a list
            if include_subembayment_assim:
                nsubs = len(subembayment_list)
                data_subs = []
                for sub in subembayment_list:
                    ind = data['group'] == sub
                    data_subs.append(data.loc[ind].copy())

            # select 'Whole_Bay' group
            ind = data['group'] == 'Whole_Bay'
            data = data.loc[ind]
            for ic in range(ncom):
                if not data_components[ic] is None:
                    data_components[ic] = data_components[ic].loc[ind]

            # convert times from string to datetime64
            data['time'] = pd.to_datetime(data['time'])
            for ic in range(ncom):
                if not data_components[ic] is None:
                    data_components[ic]['time'] = pd.to_datetime(data_components[ic]['time']).values
            if include_subembayment_assim:
                for isub in range(nsubs):
                    data_subs[isub]['time'] = pd.to_datetime(data_subs[isub]['time']).values
        
            # compute time step in days
            deltat = (data['time'].iloc[1] - data['time'].iloc[0])/np.timedelta64(1,'h')/24

            # generate a list of water years to plot from this run, based on the water year string
            # (this is confusing because for each item in the wystr_list we are generating another list
            wy_list = CVPL.list_of_wy_str_2_list_of_int_wys([wystr]) 

            # get first and last date for time axis
            wymin = np.array(wy_list).min()
            wymax = np.array(wy_list).max()
            tmin = np.datetime64('%d-10-01' % (wymin-1))
            tmax = np.datetime64('%d-10-01' % wymax)
        
            # loop through the water years we are to plot for this run
            nwy = len(wy_list)
            for iwy in range(nwy):
                
                # get water year
                wy = wy_list[iwy]

                ## pick the time window based on water year
                t_window = np.array(['%d-10-01' % (wy-1),'%d-10-01' % wy]).astype('datetime64')
        
                # water year string
                water_year = 'WY%d' % wy

                # select the data in this time window (the "f" notation is a relic of when used to do the 
                # spring-neap filtering in the plotting script)
                ind = np.logical_and( data.time.values>=t_window[0], data.time.values<t_window[1])
                dataf = data.loc[ind]
                dataf_components = []
                for ic in range(ncom):
                    if not data_components[ic] is None:
                        dataf_components.append(data_components[ic].loc[ind])
                    else:
                        dataf_components.append(None)
                if include_subembayment_assim:
                    dataf_subs = []
                    for isub in range(nsubs):
                        dataf_subs.append(data_subs[isub].loc[ind])

                # get time
                time = np.unique(dataf['time'].values)
                ntime = len(time)

                ########################################
                # plot the mass budget for the whole bay
                ########################################

                # first row of plot
                irow = 0

                # get stats for whole bay
                Delta_Influx = dataf['%s,Flux In from E (%s)' % (param,units)].values
                GG_Outflux = dataf['%s,Flux In from W (%s)' % (param,units)].values
                Minor_Trib_Influx = dataf['%s,Net Transport In (%s)' % (param,units)].values - GG_Outflux - Delta_Influx
                Storage = -dataf['%s,dMass/dt, Balance Check (%s)' % (param,units)].values
                Net_Rx = dataf['%s,Net Reaction (%s)' % (param,units)].values
                Net_Loading = dataf['%s,Net Load (%s)' % (param,units)].values
                Tribs_Plus_Loads = Delta_Influx + Minor_Trib_Influx + Net_Loading

                # golden gate outflux by components
                GG_Outflux_Com = np.zeros((ntime, ncom))
                for icom in range(ncom):
                    if not dataf_components[icom] is None:
                        ind = dataf_components[icom]['group'].values == 'Whole_Bay'
                        GG_Outflux_Com[:,icom] = dataf_components[icom].loc[ind]['%s,Flux In from W (%s)' % (components_list[icom],units)].values

                # make a dataframe to contain statistics for the whole bay
                df = pd.DataFrame(index=time)
                if not is_it_benthic(param):
                    df['Point Sources'] = Net_Loading.copy()
                    df['Delta Influx\n(+Petaluma/Sonoma/Napa)'] = Delta_Influx.copy()
                    df['Minor Tribs'] = Minor_Trib_Influx.copy()
                df['-1 x Storage (-dM/dt)'] = Storage.copy()
                df['Net Reaction'] = Net_Rx.copy()
                if not is_it_benthic(param):
                    df['Golden Gate Outflux'] = GG_Outflux.copy()

                # make the colors match between benthic and not benthic plots
                if is_it_benthic(param):
                    color_list = colors[3:5]
                else:
                    color_list = colors[0:6]

                # divide into positive and negative
                df_pos = df.copy(deep=True)
                df_neg = df.copy(deep=True)
                df_pos[df<0] = 0
                df_neg[df>0] = 0

                # add to figure
                ax[irow].stackplot(time, df_pos.values.transpose()/divide_by, colors = color_list, labels=df.columns)
                ax[irow].stackplot(time, df_neg.values.transpose()/divide_by, colors = color_list)
                if iwy==0:
                    ax[irow].set_ylabel('Whole Bay Mass Balance (%s)' % units_plot)
                    ax[irow].legend(loc='center left',bbox_to_anchor=(1, 0.5))

                # next row of plot
                irow += 1                

                # make dataframe with reactions for whole bay
                df = pd.DataFrame(columns=master_reaction_list)
                for rx in master_reaction_list:
                    if rx in dataf.columns:
                        df[rx] = dataf[rx]
                df = df.fillna(0)
                df.columns = master_reaction_list_trimmed

                # before adding storage, check reactions sum correctly
                Net_Rx_Check_Sum = df.values.sum(axis=1)

                # add storage
                df['-1 x Storage (-dM/dt)'] = Storage.copy()

                # divide into positive and negative
                df_pos = df.copy(deep=True)
                df_neg = df.copy(deep=True)
                df_pos[df<0] = 0
                df_neg[df>0] = 0

                # add to figure 1
                ax[irow].stackplot(time, df_pos.values.transpose()/divide_by, colors = colors[0:len(df.columns)], labels=df.columns)
                ax[irow].stackplot(time, df_neg.values.transpose()/divide_by, colors = colors[0:len(df.columns)])
                ax[irow].plot(time, Net_Rx/divide_by, 'k', label='Net Reaction')
                #ax[irow].plot(time, Net_Rx_Check_Sum/divide_by, 'm--', label='Net Reaction, Check Sum')
                if not is_it_benthic(param):
                    ax[irow].plot(time, (Net_Rx + Storage)/divide_by, 'b', label='-1 x Assimilation:\ndM/dt - Net Rx.')
                if iwy==0:
                    ax[irow].set_ylabel('Whole Bay Reactions (%s)' % units_plot)
                    ax[irow].legend(loc='center left',bbox_to_anchor=(1, 0.5))

                # next row of plot
                if include_subembayment_assim:
                    irow += 1   
                    irow_sub = irow

                    # make a dataframe with assimilation rate for each subembayment
                    df = pd.DataFrame(columns=subembayment_nice, index=time)
                    df.loc[:,:] = 0
                    for isub, sub in enumerate(subembayment_nice):

                        # for benthic parameters, we will plot the net storage instead of the net assimlation 
                        # because the net assimilation is always zero
                        if is_it_benthic(param):
                            df[sub] = dataf_subs[isub]['%s,dMass/dt, Balance Check (%s)' % (param,units)].values
                        else:
                            df[sub] = (dataf_subs[isub]['%s,dMass/dt, Balance Check (%s)' % (param,units)].values - 
                                       dataf_subs[isub]['%s,Net Reaction (%s)' % (param,units)].values )

                    # divide into positive and negative values
                    df_pos = df.copy(deep=True)
                    df_neg = df.copy(deep=True)
                    df_pos[df<0] = 0
                    df_neg[df>0] = 0

                    # add to figure 
                    ax[irow].stackplot(time, df_pos.values.transpose()/divide_by, colors = colors[0:len(df.columns)], labels=df.columns)
                    ax[irow].stackplot(time, df_neg.values.transpose()/divide_by, colors = colors[0:len(df.columns)])
                    #ax[irow].plot(time, Net_Rx/divide_by, 'k', label='Whole Bay: Net Rx.')
                    if is_it_benthic(param):
                        ax[irow].plot(time, -(Storage)/divide_by, 'b', label='Whole Bay Storage')
                    else:
                        ax[irow].plot(time, -(Net_Rx + Storage)/divide_by, 'b', label='Whole Bay Assimilation')
                    if iwy==0:
                        if is_it_benthic(param):
                            ax[irow].set_ylabel('Storage: dM/dt\nby Subembayment (%s)' % units_plot)
                        else:
                            ax[irow].set_ylabel('Assimilation: dM/dt - Net Rx.\nby Subembayment (%s)' % units_plot)
                        ax[irow].legend(loc='center left',bbox_to_anchor=(1, 0.5))

                    # track the max and min
                    max_rx_by_sub = np.max([max_rx_by_sub, df_pos.sum(axis=1).max()])
                    min_rx_by_sub = np.min([min_rx_by_sub, df_neg.sum(axis=1).min()])
            
                # final row of plot
                if not is_it_benthic(param):
                    irow += 1  
                    irow_out = irow

                    # make a dataframe with GG outflux components
                    df = pd.DataFrame(index=time)
                    for icom in range(ncom):
                        df[components_list[icom] + ' Outflux Through GG'] = -GG_Outflux_Com[:,icom]
        
                    # divide into positive and negative values
                    df_pos = df.copy(deep=True)
                    df_neg = df.copy(deep=True)
                    df_pos[df<0] = 0
                    df_neg[df>0] = 0
        
                    # add to figure 3
                    ax[irow].stackplot(time, df_pos.values.transpose()/divide_by, colors = colors[0:len(df.columns)], labels=df.columns)
                    ax[irow].stackplot(time, df_neg.values.transpose()/divide_by, colors = colors[0:len(df.columns)])
                    ax[irow].plot(time,Tribs_Plus_Loads/divide_by, 'k--', label='%s Loading\nfrom Tribs and Point Sources' % param)
                    ax[irow].plot(time, -GG_Outflux/divide_by, 'k', label='%s Outflux\nThrough GG' % param)
                    if iwy==0:
                        ax[irow].set_ylabel('Whole Bay Influx vs. Outflux (%s)' % units_plot)
                        ax[irow].legend(loc='center left',bbox_to_anchor=(1, 0.5))

            # add label for run
            ax[0].set_title('Run %s' % runid)

            # format time axis for all rows
            if autoscale_x:
                for ax1 in ax:
                    ax1.autoscale(enable=True, axis='x', tight=True)
                    ax1.grid(visible=True,which='both')
                fig.autofmt_xdate()
            else:
                for ax1 in ax:
                    ax1.set_xlim((tmin,tmax))
                    ax1.xaxis.set_major_locator(mdates.YearLocator())
                    ax1.xaxis.set_minor_locator(mdates.MonthLocator(bymonth=(1,4,7,10)))
                    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
                    ax1.grid(visible=True,which='both')

            # set y axis limits the same across runs
            # ... for first and 2nd rows, make y axis symmetric around zero
            for irow in [0,1]:
                ymax = np.abs(ax[irow].get_ylim()).max()
                ax[irow].set_ylim((-ymax,ymax))
            # ... for outflux row set min at zero
            if not is_it_benthic(param):
                for irow in [irow_out]:
                    ymax = np.abs(ax[irow].get_ylim()).max()
                    ax[irow].set_ylim((0,ymax))
        
            # ... for reaction by subembayment check if one or the other of max or min is zero
            # ... (don't do this anymore, to accomodate line for input minus output on TN_include_sediment plot)
            if include_subembayment_assim:


                #if np.abs(max_rx_by_sub) < 1e-2:
                #    ymax = 0
                #    ymin = min_rx_by_sub*1.05
                #elif np.abs(min_rx_by_sub) < 1e-2:
                #    ymin = 0
                #    ymax = max_rx_by_sub*1.05
                #else:
                #    max_rx_by_sub = np.max([np.abs(min_rx_by_sub),np.abs(max_rx_by_sub)])
                #    ymin = -max_rx_by_sub*1.05
                #    ymax = max_rx_by_sub*1.05
                max_rx_by_sub = np.max([np.abs(min_rx_by_sub),np.abs(max_rx_by_sub)])
                ymin = -max_rx_by_sub*1.05
                ymax = max_rx_by_sub*1.05
                for irow in [irow_sub]:
                    ax[irow].set_ylim((ymin/divide_by,ymax/divide_by))

            # add title and save the figure
            fig.suptitle('Whole Bay %s %s Budget' % (tavg_str, param))
            fig.tight_layout(rect=[0, 0.03, 1, 0.95])
            pdf.savefig(fig)

            # close figures
            plt.close('all')
        
