
'''
This script converts *.his and *-bal.his data to *.csv formatted balance tables containing
daily fluxes and reaction terms in the "monitoring regions" defined by polygons and transects.
Updated by Allie in 2022 to run in new python environment on chicago:
    source activate geo_env
    cd /richmondvol1/hpcshared/NMS_Projects/Control_Volume/Scripts/create_balance_tables
and run from there
'''

#################################################
# IMPORT MODULES (save stompy for later)
#################################################

import os, sys, shutil
import xarray as xr
import numpy as np
import pandas as pd
import datetime 
import geopandas as gpd

##################
# MAIN
##################

# load polygon shapefile
poly_df = gpd.read_file('../../Definitions/model_input_shapefiles/Agg_mod_contiguous_v24-agg141.shp')
pmax = len(poly_df)
Area = poly_df.area.values

# path to his and his bal files
#histfn      = os.path.join('/chicagovol2/hpcshared/open_bay/bgc/agg/WY13to22/G141_13to22_016','dwaq_hist.nc')
#histbal_fn  = os.path.join('/chicagovol2/hpcshared/open_bay/bgc/agg/WY13to22/G141_13to22_016','dwaq_hist_bal.nc')
histfn      = os.path.join('/chicagovol2/hpcshared/open_bay/bgc/full_res/WY2021/FR21_002','dwaq_hist.nc')
histbal_fn  = os.path.join('/chicagovol2/hpcshared/open_bay/bgc/full_res/WY2021/FR21_002','dwaq_hist_bal.nc')


# suffix for output files
#suff = 'G141_13to22_016'
suff = 'FR21_002'

# variables to test
varnames = ['detns1','detns2','diats1','oons1','oons2','detps1','detps2','detcs1','detcs2']#[var.lower() for var in hbdata.sub.values]

# time window
t_win = ('2013-10-01', '2022-10-01')

# open hist file, create it from the *.his file if needed
try:
    hdata = xr.open_dataset(histfn)
except:
    fn = None
    for fn1 in os.listdir(step0_config.run_dir):
        if ('.his' in fn1) and (not ('-bal.his' in fn1)):
            fn = fn1
    if fn is None:
        raise Exception('Cannot find *.his file in %s' % step0_config.run_dir)
    else:
        print('could not find dwaq_hist.nc, creating it now...')
        hdata = step0_config.dio.his_file_xarray(os.path.join(step0_config.run_dir,fn))
        hdata.to_netcdf(histfn)
        hdata = xr.open_dataset(histfn)

# take time slice to speed things up
hdata = hdata.sel(time=slice(t_win[0],t_win[1]))

# added this in august 2023 to make non-nefis style dwaq_hist.nc work too
if 'bal' in hdata.variables:
    print('WARNING: dwaq_hist.nc is not in the nefis based format, doing a kludgey reformat to make these scripts work...')
    nSegment = np.arange(0,len(hdata.region))
    hdata1 = xr.Dataset({'location_names': xr.DataArray(data = np.tile(hdata.region.values,(1,1)))})
    for field1 in hdata.field.values:
        hdata1[field1.lower()] = xr.DataArray(data   = hdata.sel(field=field1).bal.values,
                                          dims   = ['time','nSegment'],
                                          coords = {'time': hdata.time.values,
                                                    'nSegment' : nSegment})
    hdata = hdata1
    del hdata1

# open hist-bal file, create it from the *-bal.his file if needed
try:
    hbdata = xr.open_dataset(histbal_fn)
except:
    fn = None
    for fn1 in os.listdir(step0_config.run_dir):
        if '-bal.his' in fn1:
            fn = fn1
    if fn is None:
        raise Exception('Cannot find *-bal.his file in %s' % step0_config.run_dir)
    else:
        print('could not find dwaq_hist_bal.nc, creating it now...')
        hbdata = step0_config.dio.bal_his_file_xarray(os.path.join(step0_config.run_dir,fn))
        hbdata.to_netcdf(histbal_fn)
        hbdata = xr.open_dataset(histbal_fn)

# take time slice to speed things up
hbdata = hbdata.sel(time=slice(t_win[0],t_win[1]))

# get the start time and make sure his and his-bal start times match
start_time = pd.to_datetime(hdata.time.values[0])
if not start_time == pd.to_datetime(hbdata.time.values[0]):
    raise Exception('start time of his-bal data doesn\'t match start time of his data')
start_date = np.datetime64('%d-%02d-%02d' % (start_time.year, start_time.month, start_time.day))

# if the simulation does not start at midnight, subtract the time of day, and add it back later
offset_time = start_time.to_datetime64() - start_date
hdata['time'] = hdata['time'] - offset_time
hbdata['time'] = hbdata['time'] - offset_time

# renumber the polygons and transects so they match the shape file -- 
# newer version of stompy scrambles the numbers but does not scramble the order
polyc = 0
tranc = 0
for i in range(len(hdata.location_names.values[0])):
    if 'transect' in hdata.location_names.values[0][i]:
        hdata.location_names.values[0][i]='transect%04d' % tranc
        tranc = tranc + 1
    elif 'polygon' in hdata.location_names.values[0][i]:
        hdata.location_names.values[0][i]='polygon%d' % polyc
        polyc = polyc + 1 
polyc = 0
for i in range(len(hbdata.region.values)):
    if 'polygon' in hbdata.region.values[i]:
        hbdata.region.values[i] = 'polygon%d' % polyc
        polyc = polyc + 1

# loop through all the parameters (nh4, no3, diat, etc.)
for varname in varnames:
    
    # create name for balance table output file
    outfile = varname +'_Table_%s.csv' % suff
    
    ##%% Get all the data
    TransectBL = ['transect' in name for name in hdata.location_names.values[0]]
    indT = np.where(TransectBL)[0]
    PolygonBL = ['polygon' in name for name in hdata.location_names.values[0]]
    indP = np.where(PolygonBL)[0]
    PolygonBL_bal = ['polygon' in name for name in hbdata.region.values]
    indP_bal = np.where(PolygonBL_bal)[0]
    varT = hdata.isel(nSegment=indT)[varname]
    varP = hdata.isel(nSegment=indP)[varname]
    fieldBL = [varname.lower()+',' in name.lower() for name in hbdata.field.values]
    indF = np.where(fieldBL)[0]
    varP_bal = hbdata.isel(region=indP_bal).isel(field=indF)
    Vp = hdata.isel(nSegment=indP)['volume']  

    # check the frequency of the data, and if frequency is higher than daily, resample onto a daily axis
    deltat_P = (varP.time[1]-varP.time[0]).values
    deltat_T = (varT.time[1]-varT.time[0]).values
    deltat_B = (varP_bal.time[1]-varP_bal.time[0]).values

    # ... if polygon output is less than daily, resample onto daily axis (take instantaneous snapshots)
    # ... for volume additionally provide a mean value for normalizing rates
    if deltat_P < np.timedelta64(1,'D'):
        varP = varP.resample(time='1D').nearest()
        Vp = Vp.resample(time='1D').nearest()
        Vp_mean = Vp.resample(time='1D',closed='right',label='right').mean(dim='time')
    elif deltat_P==np.timedelta64(1,'D'):
        pass
    else:
        raise Exception('ERROR: his file has time step greater than one day')
    # ... transect output should be integrated in time, bizarrely the integral is open on the 
    # ... left and closed on the right, i.e., integral is from 0<t<=T. note the time ends up shifted
    # ... so add a day to it
    if deltat_T<np.timedelta64(1,'D'):
        varT = varT.resample(time='1D',closed='right',label='right').sum(dim='time')
    elif deltat_T==np.timedelta64(1,'D'):
        pass
    else:
        raise Exception('ERROR: his file has time step greater than one day')
    # ... balance output should be integrated in time, bizarrely the integral is open on the 
    # ... left and closed on the right, i.e., integral is from 0<t<=T. note the time ends up shifted
    # ... so add a day to it
    if deltat_B<np.timedelta64(1,'D'):
        varP_bal = varP_bal.resample(time='1D',closed='right',label='right').sum(dim='time')
    elif deltat_B==np.timedelta64(1,'D'):
        pass
    else:
        raise Exception('ERROR: his-bal file has time step greater than one day')

    # subtract one day from all output, becasue currently the values represent the backwards average 
    # over the PREVIOUS day
    varP['time'] = varP['time'] - np.timedelta64(1,'D')
    Vp['time'] = Vp['time'] - np.timedelta64(1,'D')
    Vp_mean['time'] = Vp_mean['time'] - np.timedelta64(1,'D')
    varT['time'] = varT['time'] - np.timedelta64(1,'D')
    varP_bal['time'] = varP_bal['time'] - np.timedelta64(1,'D')

    # now make sure polygon, transect, and balance data have same number of time steps (this 
    # condition may be violated in case of incomplete simulation)
    tmin = np.min([varP.time.values[-1],varT.time.values[-1],varP_bal.time.values[-1]])
    varP = varP.where(varP.time<=tmin,drop=True)
    Vp = Vp.where(Vp.time<=tmin,drop=True)
    Vp_mean = Vp_mean.where(Vp_mean.time<=tmin,drop=True)
    varT = varT.where(varT.time<=tmin,drop=True)
    varP_bal = varP_bal.where(varP_bal.time<=tmin,drop=True)
    
    # get the units and determine if per area or per volume, then compute dMass/dt accordingly 
    diffVar = (varP*Area).diff(dim='time')
    Conc = (varP*Area)/Vp
    
    #%% Outputting variables for each polygon.                         
    df_output = pd.DataFrame()  
    for i,p in enumerate(varP_bal.region.values):

        pi_df = varP_bal.bal.sel(region=p).to_pandas() 

        # sum everything in the mass balance to get mass closure estimate of dVar/dt
        cols = []
        for col in pi_df.columns:
            if (varname+',') in col.lower():
                cols.append(col)

        pi_df['dVar/dt (bal)'] = pi_df[cols].sum(axis=1)
        pi_df['dVar/dt (con)'] = np.append(diffVar[0,i],diffVar[:,i])  
        pi_df['dVar/dt (bal) / dVar/dt (con)'] = pi_df['dVar/dt (bal)'] / pi_df['dVar/dt (con)']
        
        if i==0:
            column_list = ['Control Volume','Concentration (mg/l)','Volume','Volume (Mean)',
                           'Area'] + list(pi_df.columns)   
        
        pi_df['Concentration (mg/l)'] = Conc.isel(nSegment=i).values
        pi_df['Control Volume'] = p
        pi_df['Volume'] = Vp.values[:,i]
        pi_df['Volume (Mean)'] = Vp_mean.values[:,i] 
        pi_df['Area'] = Area[i] 


        # remove the first time step because it is garbage
        pi_df = pi_df.iloc[1:]

        df_output = pd.concat([df_output,pi_df])

    df_output = df_output[column_list] 

    # adjust for offset time
    time = pd.to_datetime(df_output.index + offset_time)
    df_output.set_index(time, inplace=True)

    # save
    df_output.to_csv(outfile,columns=column_list)   

