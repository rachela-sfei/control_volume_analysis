
''' 
Configuration module for ALL of the create_balance_table scripts 
This is where we set global variables that are used by all the scripts. 

alliek august 2022
'''

##############################
# user input
##############################

# abort if error tolerance is exceeded? set to False for troubleshooting only. (this is used in step4_check_mass_conservation.py)
# NOTE THAT FOR FR13_003 AND FR13_007 RUNS, THERE IS A MASS CONSERVATION ERROR BUT IT IS NOT A DEAL BREAKER, SO WE SET THIS TO FALSE
# WHEN GENERATING BALANCE TABLES FOR THOSE RUNS (the error is that algae that settles to the bed does not go into detritus, it just 
# leaves the model forever, so that SUMS TO ZERO: Diat,dSedDiat + DetNS1,dSedAlgN is not zero)
abort_for_mass_cons_error = False

# important flags for various model configurations
sedmod = True # the output from our sedmod is different than what is going on (for DIN and quadratic mortality), need to turn this on if that's the case
is_v24 = True # flag to indicate runs based on new hydro with straightened grid and calibrated temperature model
create_ncfile = True # this creates nc files of the hist and his-bal files


# name of server and runid
vol = 'vol2'

server = 'chicago'
runid = 'FR21_TR_093'
hydro_path = '/boisevol2/hpcshared/open_bay/hydro/full_res/wy2021-v24/runs/wy2021-v24/DFM_DELWAQ_wy2021-v24_bound_temp_salt/wy2021-v24.hyd'

# server = 'chicago'
# runid = 'FR21_021'
# hydro_path = '/boisevol2/hpcshared/open_bay/hydro/full_res/wy2021-v24/runs/wy2021-v24/DFM_DELWAQ_wy2021-v24_bound_temp_salt/wy2021-v24.hyd'

# server = 'boise'
# runid = 'G141_21_430'
# hydro_path = '/chicagovol2/hpcshared/open_bay/hydro/agg/wy2013-wy2022-v24/com-wy2013-wy2022-v24_agg_lp.hyd'

#runid = 'FR21_011_4deltares'
#hydro_path = '/boisevol2/hpcshared/open_bay/hydro/full_res/wy2021-v24-4deltares/runs/wy2021-v24-4deltares/DFM_DELWAQ_wy2021-v24-4deltares_bound_temp_salt/wy2021-v24-4deltares.hyd'



model_run_base_dir = '/%s%s/hpcshared' % (server,vol)

# if the user sets the following variables to None, they are calculated automatically, by making some assumptions about
# how our computers are organized (see below). if your run doesn't fit the usual mold, you can override the automatic stuff
# by setting some or all of these variables directly
poly_path = None
tran_path = None
group_def_path = None          
group_con_path = None
run_dir = None
lsp_path = None
balance_table_dir = None       # will be placed inside run_dir unless otherwise specified

# base directory for model input, namely the shapefiles (this definitely runs on linux, in theory can also run this in windows and use mounted drive)
# (this is ignored if poly_path and tran_path are specified as something other than None above)
model_input_dir = '/richmondvol1/hpcshared'

# stompy directory (stompy is called in step0_create_balance_tables.py to create dwaq_hist_bal.nc from the *-his.bal file if needed)
stompy_dir = '/opt/software/rusty/stompy/newest_commit/stompy'

# base level substances to process. set to string 'all' or a list of substance strings -- warning, processing 
# all of them takes a long time and uses a lot of space (this is used in step1_create_balance_tables.py),
# substance_list = ['continuity', 'nh4', 'no3', 'pon1', 'pon2','pop1', 'pop2', 'don', 'dop', 'oxy', 'si', 'opal', 'po4',
#                  'diat', 'green', 'diats1',
#                  'zoopl_e', 'zoopl_r', 'zoopl_v', 
#                  'mussel_v','mussel_e','mussel_r','grazer4_v','grazer4_e','grazer4_r',
#                  'detns1', 'detns2', 'oons1', 'oons2',
#                  'poc1', 'poc2','detcs1', 'detcs2', 'oocs1', 'oocs2']
substance_list = ['continuity', 'doc', 'don', 'dop', 
                  'detcs1', 'detcs2', 'detns1', 'detns2', 'detps1', 'detps2', 'detsis1', 'detsis2', 
                  'diat', 'diats1', 'green', 
                  'nh4', 'no3', 'oxy', 'opal', 'po4', 'si',
                  'oocs1', 'oocs2', 'oons1', 'oons2', 'oops1', 'oops2', 'oosis1', 'oosis2', 
                  'poc1', 'poc2', 'pon1', 'pon2', 'pop1', 'pop2', 
                  'zoopl_e', 'zoopl_n', 'zoopl_r', 'zoopl_v']# turning all of these on for now because it seems like we need them for the composite parameters

# list of substances we think we are actually going to want to plot -- to save space, the 
# step5_compile_balance_tables_into_groups.py and step6_aggregate_in_time.py scripts will only process these substances
plot_substance_list = ['continuity',
                       'nh4','no3','pon1','pon2','detns1','detns2','detns12','din','tn',#'tn_plus_diats1_plus_detns12' # nitrogen plus composite parameters
                       'po4','pop1','pop2','detps1','detps2','tp',                                                    # phosphorus plus composite parameters
                       'si', 'opal', 'tsi',                                                                           # si plus composite parameters
                       'diat','green','algae',#'n-algae',                                                              # algae
                    #    'zoopl','mussel','grazer4','clams','n-zoopl',                                                  # grazers
                    #    'oons1','oons2','oons12','oops1','oops2', 'oocs1','oocs2',                                     # refractory 
                       'oxy',                                                                                         # oxygen
                    #    'diats1',                                                                                      # microphytobenthos
                       'poc1', 'poc2','detcs1', 'detcs2',]                                                            # carbon 


# list of time averaging schemes to apply (saves space to skip some if we don't need them) 
# (this is used in step6_aggregate_in_time.py)
# in Dec 2023 added Seasonal2 which defines 3 seasons (Oct,Nov,Dec,Jan + Feb,Mar,Apr,May + Jun,Jul,Aug,Sep)
# in contrast to Seasonal which defines 4 seasons (Oct,Nov,Dec + Jan,Feb,Mar + Apr,May,Jun + Jul,Aug,Sep)
tavg_list = ['Filtered','Cumulative','Annual','Seasonal']#,'Seasonal2','Seasonal3','Monthly','Weekly']

# float format for csv files
float_format = '%1.6e'

# set tolerance for mass conservation error as a percentage of whatever variable we chose to normalize by (this is used in step4_check_mass_conservation.py)
error_tol_percent = 1#0.1

# delete all balance tables before re-running step1_create_balance_tables?
delete_balance_tables = True

# is this a delta run? a couple of notes about using these scripts for delta runs
# 1. for now we assume it is a full resolution delta run
# 2. since aggregated groups are not defined for the delta, do not try to run step5_compile_balance_tables_into_groups.py, 
#    but it is ok to run step6_aggregate_in_time.py without running step5_compile_balance_tables_into_groups.py
# 3. originally, i added the capacity to process delta runs to make sure mass of N is conserved, and for the most part it is, 
#    (there's a small leak when N is passed from DIN to algae because we're using an old version of DWAQ)
is_delta = False # is this a delta run (old notes below ~line 110)

# check if this is a tracer run, currently this is configured to only account for the tracers in the "all sources"
# mode of the runs, it can be updated otherwise.
if 'TR' in runid:
    is_tracer = True # is this a tracer run
else:
    is_tracer = False

# for some parameters, the dwaq_hist.nc file does not have the correct units ... use this to override the units
# (this is used only in step1_create_balance_tables.py, where we compute dMass/dt from concentraitons in the *.his
# file, so we need to know if the concentraiton units are g/m3 or g/m3)
units_override = {'zoopl_e' : 'gC/m3',
                  'zoopl_r' : 'gC/m3',
                  'zoopl_v' : 'gC/m3',
                  'zoopl_n' : '#/m3',
                  # added all these too in august 2023 to make things work with non-nefis dwaq_hist.nc
                  'diat' : 'gC/m3','green' : 'gC/m3','nh4' : 'gN/m3','no3' : 'gN/m3',
                  'po4' : 'gP/m3','si' : 'gSi/m3','continuity' : 'g/m3','oxy' : 'g/m3',
                  'poc1' : 'gC/m3','pon1' : 'gN/m3','pop1' : 'gP/m3','doc' : 'gC/m3',
                  'don' : 'gN/m3','dop' : 'gP/m3','opal' : 'gSi/m3','poc2' : 'gC/m3',
                  'pon2' : 'gN/m3','pop2' : 'gP/m3','detcs1' : 'gC/m2','detcs2' : 'gC/m2',
                  'detns1' : 'gN/m2','detns2' : 'gN/m2','detps1' : 'gP/m2','detps2' : 'gP/m2',
                  'detsis1' : 'gSi/m2','detsis2' : 'gSi/m2','diats1' : 'gC/m2','oocs1' : 'gC/m2',
                  'oocs2' : 'gC/m2','oons1' : 'gN/m2','oons2' : 'gN/m2','oops1' : 'gP/m2',
                  'oops2' : 'gP/m2','oosis1' : 'gSi/m2','oosis2' : 'gSi/m2','volume' : 'm3',}

# list of composite parameters -- include all possible component parameters, script will automatically 
# check if they were included in this run and leave it out if needed (this is used in 
# step2_create_balance_tables_for_composite_parameters.py)
composite_parameters = {
    'N-Algae' : ['Diat', 'Green','DiatS1'],
    'N-Zoopl' : ['Zoopl_V', 'Zoopl_E', 'Zoopl_R'],
    'Algae' : ['Diat', 'Green','DiatS1'],
    'Zoopl' : ['Zoopl_V', 'Zoopl_E', 'Zoopl_R'],
    'DIN' : ['NH4', 'NO3'],
#    'TN'  : ['NH4', 'NO3', 'PON1', 'PON2', 'DON', 'Diat', 'DiatS1', 'Green', 'Zoopl_V', 'Zoopl_E', 'Zoopl_R'],
# pradeep seuggested take DiatS1 out of TN Feb 2026
    'TN'  : ['NH4', 'NO3', 'PON1', 'PON2', 'DON', 'Diat', 'Green', 'Zoopl_V', 'Zoopl_E', 'Zoopl_R'], 
#    'TN_include_sediment' : ['NH4', 'NO3', 'PON1', 'PON2', 'DON', 'DetNS1', 'DetNS2', 'OONS1', 'OONS2',
#                             'Diat', 'Green', 'DiatS1', 'Zoopl_V', 'Zoopl_E', 'Zoopl_R',
#                             'Mussel_V','Mussel_E','Mussel_R','Grazer4_V','Grazer4_E','Grazer4_R'], 
#    'TN_plus_DetNS12' : 
# since DiatS1 is no longer part of TN, rename TN_plus_DetNS12 but the components remain the same
    # 'TN_plus_DiatS1_plus_DetNS12' : ['NH4', 'NO3', 'PON1', 'PON2', 'DON', 'DetNS1', 'DetNS2', 
    #                          'Diat', 'Green', 'DiatS1', 'Zoopl_V', 'Zoopl_E', 'Zoopl_R',
    #                          'Mussel_V','Mussel_E','Mussel_R','Grazer4_V','Grazer4_E','Grazer4_R'], 
#    'TotalDetNS' : ['DetNS1','DetNS2','OONS1','OONS2'],   
    'DetNS12' : ['DetNS1','DetNS2'],
    'OONS12' : ['OONS1','OONS2'],               
# pradeep seuggested take DiatS1 out of TP Feb 2026   
    'TP'  : ['PO4', 'POP1', 'POP2', 'DOP', 'Diat', 'Green', 'Zoopl_V', 'Zoopl_E', 'Zoopl_R'],
#    'TP_include_sediment' : ['PO4', 'POP1', 'DOP', 'DetPS1', 'DetPS2', 
#                             'Diat', 'Green', 'DiatS1', 'Zoopl_V', 'Zoopl_E', 'Zoopl_R',
#                             'Mussel_V','Mussel_E','Mussel_R','Grazer4_V','Grazer4_E','Grazer4_R'],
#    'TotalDetPS' : ['DetPS1', 'DetPS2','OOPS1', 'OOPS2'],
#    'TotalDetSi' : ['DetSiS1', 'DetSiS2','OOSiS1', 'OOSiS2'],
    'TSi' : ['Si','Opal', 'Diat', 'Green'], # zooplankton do not contribute to Si budget (only N and P)
    'Grazer4' : ['Grazer4_V', 'Grazer4_E', 'Grazer4_R'],
    'Mussel' : ['Mussel_V', 'Mussel_E', 'Mussel_R'], 
    'Clams' : ['Grazer4_V', 'Grazer4_E', 'Grazer4_R', 'Mussel_V', 'Mussel_E', 'Mussel_R']
}

# is the budget of each composite parameter in grams of C, N, P, etc? (this is used in 
# step2_create_balance_tables_for_composite_parameters.py)
composite_bases = {
    'N-Algae' : 'N',
    'N-Zoopl' : 'N',
    'Algae' : 'C',
    'Zoopl' : 'C',
    'DIN' : 'N',
    'TN'  : 'N', 
    'TN_plus_DetNS12'  : 'N',
    'TN_plus_DiatS1_plus_DetNS12'  : 'N', 
    #'TN_include_sediment'  : 'N', 
    'DetNS12' : 'N',
    'OONS12' : 'N',
    #'TotalDetNS' : 'N',
    'TP'  : 'P', 
    'TP_include_sediment'  : 'P', 
    'TotalDetPS' : 'P',
    'TotalDetSi' : 'Si',
    'TSi' : 'Si',
    'Grazer4' : 'C',
    'Mussel' : 'C',
    'Clams' : 'C'
}

# call out any sets of reactions you want to sum together to appear as one reaction 
# in the composite parameter mass budgets, and give each composite reaction a name ...
# (this is used in step3_group_reactions_for_composite_parameters.py)
composite_reaction_dict = {
     'N-Algae' : {'Diat,dPPDiat' : ['Diat,dPPDiat', 'Diat,dcPPDiat'],
                  'Green,dPPGreen' : ['Green,dPPGreen', 'Green,dcPPGreen'], 
                  ###'DiatS1,dPPDiatS1' : ['DiatS1,dPPDiatS1'], 
                  'Diat,dMrtDiat' : ['Diat,dMrtDiat'],
                  'Green,dMrtGreen' : ['Green,dMrtGreen'],
                  'Diat,dDiatQMrt' : ['Diat,dqmtdiat'],
                  'Diat,dDiatQMrt' : ['Green,dqmtgree'],
                  ###'DiatS1,dMrtDiatS1' : ['DiatS1,dMrtDiatS1'],
                  ###'Diat,dZ_Diat' : ['Diat,dZ_Diat'],
                  ###'Green,dZ_Grn' : ['Green,dZ_Grn'],
                  ###'Diat,dSedDiat' : ['Diat,dSedDiat'],
                  ###'Green,dSedGreen' : ['Green,dSedGreen'],
                  ###'DiatS1,dBurS1Diat' : ['DiatS1,dBurS1Diat'], 
                  'EACH IS ZERO: DiatS1,dResS1Diat + DiatS1,dSWBuS1Dia + DiatS1,dDigS1Diat' : ['DiatS1,dResS1Diat', 'DiatS1,dSWBuS1Dia','DiatS1,dDigS1Diat']},
     'N-Zoopl' : {###'Zoopl_E,dZ_Ea' : ['Zoopl_E,dZ_Ea'], # source,
                  ###'Zoopl_E,dZ_Ec' : ['Zoopl_E,dZ_Ec'], # sink
                  ###'Zoopl_R,dZ_SpwDet' : ['Zoopl_R,dZ_SpwDet'], # sink
                  'Zoopl,dZ_gr' : ['Zoopl_V,dZ_Vgr','Zoopl_R,dZ_Rgr'], # this can be a sink or a source!?
                  'Zoopl,dZ_mor' : ['Zoopl_V,dZ_Vmor','Zoopl_E,dZ_Emor','Zoopl_R,dZ_Rmor']},
     'Algae' : {'Diat,dPPDiat' : ['Diat,dPPDiat', 'Diat,dcPPDiat'],
                  'Green,dPPGreen' : ['Green,dPPGreen', 'Green,dcPPGreen'], 
                  ###'DiatS1,dPPDiatS1' : ['DiatS1,dPPDiatS1'], 
                  'Diat,dMrtDiat' : ['Diat,dMrtDiat'],
                  'Green,dMrtGreen' : ['Green,dMrtGreen'],
                  'Diat,dDiatQMrt' : ['Diat,dqmtdiat'],
                  'Diat,dDiatQMrt' : ['Green,dqmtgree'],
                  ###'DiatS1,dMrtDiatS1' : ['DiatS1,dMrtDiatS1'],
                  ###'Diat,dZ_Diat' : ['Diat,dZ_Diat'],
                  ###'Green,dZ_Grn' : ['Green,dZ_Grn'],
                  ###'Diat,dSedDiat' : ['Diat,dSedDiat'],
                  ###'Green,dSedGreen' : ['Green,dSedGreen'],
                  ###'DiatS1,dBurS1Diat' : ['DiatS1,dBurS1Diat'], 
                  'EACH IS ZERO: DiatS1,dResS1Diat + DiatS1,dSWBuS1Dia + DiatS1,dDigS1Diat' : ['DiatS1,dResS1Diat', 'DiatS1,dSWBuS1Dia','DiatS1,dDigS1Diat']},
     'Zoopl' : {###'Zoopl_E,dZ_Ea' : ['Zoopl_E,dZ_Ea'], # source,
                  ###'Zoopl_E,dZ_Ec' : ['Zoopl_E,dZ_Ec'], # sink
                  ###'Zoopl_R,dZ_SpwDet' : ['Zoopl_R,dZ_SpwDet'], # sink
                  'Zoopl,dZ_gr' : ['Zoopl_V,dZ_Vgr','Zoopl_R,dZ_Rgr'], # this can be a sink or a source!?
                  'Zoopl,dZ_mor' : ['Zoopl_V,dZ_Vmor','Zoopl_E,dZ_Emor','Zoopl_R,dZ_Rmor']},
    # note the all lower case reactions are for the new denitrificaiton model
     'DIN' : {
             'DIN,dDINUpt'  : ['NO3,dNO3Upt', 'NH4,dNH4Upt'], # uptake is a sink, uptake for diatoms and greens is lumped together
             'DIN,dDINUptS1' : ['NH4,dNH4UptS1', 'NH4,dNH4US1D', 'NO3,dNO3UptS1'], # there are three additional uptake terms for benthic algae       
             'NH4,dMinDetNS12': ['NH4,dMinDetNS1', 'NH4,dMinDetNS2','NH4,ddetns1min', 'NH4,ddetns2min'],
             'NH4,dMinOONS12': ['NH4,dMinOONS1', 'NH4,dMinOONS2','NH4,doons1min', 'NH4,doons2min'],
             'NO3,dDenit'   : ['NO3,dDenitWat', 'NO3,dDenitSed','NO3,dNiDen'],
             'NO3,dDetDenit' : ['NO3,ddetcs1nit','NO3,ddetcs2nit'],
             'NO3,dOODenit' : ['NO3,doocs1nit','NO3,doocs2nit'],
             'NH4,dAlgQMrt' : ['NH4,dqmtdNH4','NH4,dqmtgNH4'],
             #'NH4,dMinPON1' : ['NH4,dMinPON1'], # this is a source
             #'NH4,dMinPON2' : ['NH4,dMinPON2'], # this is a source
             'NH4,dMinPON' : ['NH4,dMinPON1','NH4,dMinPON2'],
             ###'NH4,dMinDON' : ['NH4,dMinDON'], # this is a source
             'NH4,dZ_NRes' : ['NH4,dZ_NRes'], # this is a source
             'NH4,dNH4Aut'  : ['NH4,dNH4Aut'], # this is a source 
             ###'NH4,dNH4AUTS1' : ['NH4,dNH4AUTS1'], # this is a source
             'SUMS TO ZERO: NH4,dNitrif + NO3,dNitrif'  : ['NO3,dNitrif', 'NH4,dNitrif'],     # these should cancel out    
             },
    'TN' : { 
             'Algae,dSedAlgae' : ['Diat,dSedDiat', 'Green,dSedGreen'],  # this should be a SINK for TN
             'PON1,dSedPON1' : ['PON1,dSedPON1'], # this should be a SINK for TN
             'PON2,dSedPON2' : ['PON2,dSedPON2'], # this should be a SINK for TN 
            #  'DiatS1,dMrtDiatS1' : ['DiatS1,dMrtDiatS1'], # dead benthic algae turn into detritus through the 'DetNS1,dMrtDetNS1' term, so this is a water column sink
            #  'DiatS1,dBurS1Diat' : ['DiatS1,dBurS1Diat'], # burial of benthic algae appears to be a true sink -- it leaves the model completely!
             'NH4,dMinDetNS12': ['NH4,dMinDetNS1', 'NH4,dMinDetNS2','NH4,ddetns1min', 'NH4,ddetns2min'],
             'NH4,dMinOONS12': ['NH4,dMinOONS1', 'NH4,dMinOONS2','NH4,doons1min', 'NH4,doons2min'],
             'NO3,dDetDenit' : ['NO3,ddetcs1nit','NO3,ddetcs2nit'],
             'NO3,dOODenit' : ['NO3,doocs1nit','NO3,doocs2nit'],
             'NO3,dDenit' : ['NO3,dDenitWat', 'NO3,dDenitSed','NO3,dNiDen'], # this should be a SINK for TN
             'NH4,dNH4AUTS1' : ['NH4,dNH4AUTS1'], # part of the dead algae from DiatS1,dMrtDiatS1 get returned to the water column via autolysis, so this is a water column source
             'NH4,dClam_NRes' : ['NH4,dM_NRes','NH4,dG4_NRes'], # this is a SOURCE for TN (clam pee)
             'PON1,dClam_NDef' : ['PON1,dM_NDef','PON1,dG4_NDef'], # this is a SOURCE for TN (clam poo)
             'Algae,dClam_Algae' : ['Diat,dM_Diat','Diat,dG4_Diat','Green,dM_Green','Green,dG4_Green'], # this is a SINK for TN (clams eat algae)
             'PON1,dClam_PON1' : ['PON1,dM_PON1','PON1,dG4_PON1'], # this is a SINK for TN (clams eat dead algae?)
             'DIN,dDINUptS1' : ['NH4,dNH4UptS1', 'NH4,dNH4US1D', 'NO3,dNO3UptS1'], # there are three additional uptake terms for benthic algae
             # identify groups of terms that sum to zero
             #'SUMS TO ZERO: NH4,dNH4UptS1 + NH4,dNH4US1D + NO3,dNO3UptS1 + DiatS1,dPPDiatS1' : ['NH4,dNH4UptS1', # these terms sum to zero, benthic algae productivity
             #                                                                           'NH4,dNH4US1D', 
             #                                                                           'NO3,dNO3UptS1', 
             #                                                                           'DiatS1,dPPDiatS1'],
             'SUMS TO ZERO: Diat,dqmtdiat + NH4,dqmtdNH4 + PON1,dqmtdLN + PON2,dqmtdRN' : ['Diat,dqmtdiat','NH4,dqmtdNH4','PON1,dqmtdLN','PON2,dqmtdRN'],
             'SUMS TO ZERO: Green,dqmtgree + NH4,dqmtgNH4 + PON1,dqmtgLN + PON2,dqmtgRN' : ['Green,dqmtgree','NH4,dqmtgNH4','PON1,dqmtgLN','PON2,dqmtgRN'],
             # in the PRE August 2020 model this does NOT sum to zero but it should, and it does in later versions of the model
             'SUMS TO ZERO: Diat,dPPDiat + Diat,dcPPDiat + Green,dPPGreen + Green,dcPPGreen + NH4,dNH4Upt + NO3,dNO3Upt' : 
                                                                                     ['Diat,dPPDiat',
                                                                                      'Diat,dcPPDiat',
                                                                                      'Green,dPPGreen',
                                                                                      'Green,dcPPGreen',
                                                                                      'NH4,dNH4Upt',
                                                                                      'NO3,dNO3Upt'], 
             'SUMS TO ZERO: NO3,dNitrif + NH4,dNitrif' : ['NO3,dNitrif','NH4,dNitrif'],      # these two sum to zero
             'SUMS TO ZERO: DON,dCnvDPON1 + PON1,dCnvDPON1' : ['DON,dCnvDPON1','PON1,dCnvDPON1'], # these two sum to zero
             'SUMS TO ZERO: NH4,dMinPON1 + PON1,dMinPON1' : ['NH4,dMinPON1','PON1,dMinPON1'],   # these two sum to zero
             'SUMS TO ZERO: NH4,dMinDON + DON,dMinDON' : ['NH4,dMinDON','DON,dMinDON'],       # these two sum to zero
             'SUMS TO ZERO: Diat,dMrtDiat + Green,dMrtGreen + PON1,dMortDetN + NH4,dNH4Aut' :  [ 
                                        'Diat,dMrtDiat', 
                                        'Green,dMrtGreen',
                                        'PON1,dMortDetN',
                                        'NH4,dNH4Aut'], 
             'SUMS TO ZERO: NH4,dZ_NRes + PON1,dZ_PON1 + PON1,dZ_NDef + PON1,dZ_NSpDet + Diat,dZ_Diat + Green,dZ_Grn + Zoopl_V,dZ_Vgr + Zoopl_R,dZ_SpwDet + Zoopl_R,dZ_Rgr + Zoopl_E,dZ_Ea + Zoopl_E,dZ_Ec' : [
                                         'NH4,dZ_NRes',
                                         'PON1,dZ_PON1',
                                         'PON1,dZ_NDef',
                                         'PON1,dZ_NSpDet',
                                         'Diat,dZ_Diat',
                                         'Green,dZ_Grn',
                                         'Zoopl_V,dZ_Vgr',
                                         'Zoopl_R,dZ_SpwDet',
                                         'Zoopl_R,dZ_Rgr',
                                         'Zoopl_E,dZ_Ea',
                                         'Zoopl_E,dZ_Ec'
                                         ],
             'SUMS TO ZERO: PON1,dZ_NMrt + PON1,dM_NMrt + PON1,dG4_NMrt + PON1,dM_NSpDet + PON1,dG4_NSpDet + Zoopl_V,dZ_Vmor + Zoopl_R,dZ_Rmor + Zoopl_E,dZ_Emor' : [
                                          'PON1,dZ_NMrt',      
                                          'PON1,dM_NMrt',
                                          'PON1,dG4_NMrt',
                                          'PON1,dM_NSpDet',
                                          'PON1,dG4_NSpDet',
                                          'Zoopl_V,dZ_Vmor',  
                                          'Zoopl_R,dZ_Rmor',  
                                          'Zoopl_E,dZ_Emor'],
             'SUMS TO ZERO: PON1,dCnvPPON1 + PON2,dCnvPPON1' : ['PON1,dCnvPPON1','PON2,dCnvPPON1'],   #### NEW #### these are currently nonzero but sum to zero
             'SUMS TO ZERO: NH4,dMinPON2 + PON2,dMinPON2' : ['NH4,dMinPON2','PON2,dMinPON2'],   #### NEW #### these are currently nonzero but sum to zero
             'SUMS TO ZERO: PON2,dCnvPPON2 + DON,dCnvDPON2' : ['PON2,dCnvPPON2','DON,dCnvDPON2'], #### NEW #### each is zero for now (and I suspect they sum to zero anyway)
             'EACH IS ZERO: PON1,dResS1DetN + PON1,dResS2DetN + PON1,dResS1DiDN + PON1,dResS2DiDN' : [ 
                                          'PON1,dResS1DetN', 
                                          'PON1,dResS2DetN', 
                                          'PON1,dResS1DiDN', 
                                          'PON1,dResS2DiDN'],       
             'EACH IS ZERO: DiatS1,dResS1Diat + DiatS1,dSWBuS1Dia + DiatS1,dDigS1Diat' : ['DiatS1,dResS1Diat',      # new benthic algae terms, each one is zero, for now
                                                                                      'DiatS1,dSWBuS1Dia', 
                                                                                      'DiatS1,dDigS1Diat'], 
             'EACH IS ZERO: PON2,dCnvDPON2 + PON2,dMortOON + PON2,dResS1OON + PON2,dResS2OON' : ['PON2,dCnvDPON2','PON2,dMortOON','PON2,dResS1OON','PON2,dResS2OON'] #### NEW #### each is zero for now 
            },
    'OONS12' : {    ###'OONS1,dSedPON2' : ['OONS1,dSedPON2'],  # source
                    'OONS12,dMinOONS12' :  ['OONS1,dMinOONS1', 'OONS2,dMinOONS2','OONS1,doons1min','OONS2,doons2min'], # this is a source
                    #'OONS1,dMinOONS1' : ['OONS1,dMinOONS1'], # sink
                    #'OONS2,dMinOONS2' : ['OONS2,dMinOONS2'], # sink
                    ###'OONS2,dBurS2OON' : ['OONS2,dBurS2OON'], # sink
                    'SUMS TO ZERO: OONS1,dBurS1OON + OONS2,dBurS1OON' : ['OONS1,dBurS1OON', 'OONS2,dBurS1OON'],
                    'SUMS TO ZERO: OONS1,dDigS1OON + OONS2,dDigS1OON' : ['OONS1,dDigS1OON', 'OONS2,dDigS1OON'],
                    'EACH IS ZERO: OONS1,dSWMnOONS1 + OONS1,dResS1OON + OONS1,dSWBuS1OON' : ['OONS1,dSWMnOONS1','OONS1,dResS1OON','OONS1,dSWBuS1OON'],
                    'EACH IS ZERO: OONS2,dSWMnOONS2 + OONS2,dResS2OON + OONS2,dDigS2OON' : ['OONS2,dSWMnOONS2','OONS2,dResS2OON', 'OONS2,dDigS2OON']},
    'DetNS12' : {   ###'DetNS1,dMrtDetNS1' : ['DetNS1,dMrtDetNS1'], # source
                    ###'DetNS1,dSedAlgN' : ['DetNS1,dSedAlgN'], # source
                    ###'DetNS1,dSedPON1' : ['DetNS1,dSedPON1'], # source
                    'DetNS12,dMinDetNS12' : ['DetNS1,dMinDetNS1', 'DetNS2,dMinDetNS2','DetNS1,ddetns1min','DetNS2,ddetns2min'],# this is a source
                    ###'DetNS2,dBurS2DetN' : ['DetNS2,dBurS2DetN'], # sink
                    'SUMS TO ZERO: DetNS1,dBurS1DetN + DetNS2,dBurS1DetN' : ['DetNS1,dBurS1DetN', 'DetNS2,dBurS1DetN'],
                    'SUMS TO ZERO: DetNS2,dDigS1DetN + DetNS1,dDigS1DetN' : ['DetNS2,dDigS1DetN', 'DetNS1,dDigS1DetN'],
                    'EACH IS ZERO: DetNS1,dSWMinDNS1 + DetNS1,dZ_NMrtS1 + DetNS1,dZ_DNS1 + DetNS1,dResS1DetN + DetNS1,dSWBuS1DtN' : ['DetNS1,dSWMinDNS1',
                                                              'DetNS1,dZ_NMrtS1','DetNS1,dZ_DNS1','DetNS1,dResS1DetN','DetNS1,dSWBuS1DtN'],
                    'EACH IS ZERO: DetNS2,dSWMinDNS2 + DetNS2,dResS2DetN + DetNS2,dDigS2DetN' : ['DetNS2,dSWMinDNS2', 'DetNS2,dResS2DetN', 'DetNS2,dDigS2DetN'],},
    'TP' : {
        #  'PO4,dMinPOP12':['PO4,dMinPOP1','PO4,dMinPOP2'], # this may not be a source since it goes to PO4, right?
         'PO4,dMinDetPS12':['PO4,dMinDetPS1','PO4,dMinDetPS2','PO4,ddetps1min','PO4,ddetps2min'], # this is a source in sed NOTE: THIS WAS CREATED WITH SEDMOD ON IF SEDMOD TURNS OFF IT NO LONGER WORKS
         'PO4,dMinOOPS12':['PO4,dMinOOPS1','PO4,dMinOOPS2','PO4,doops1min','PO4,doops2min'], # this is a source in sed
         'Algae,dSedAlgae' : ['Diat,dSedDiat', 'Green,dSedGreen'],  # this should be a SINK for TP
         'PO4,dPO4UptS1' : ['PO4,dPO4UptS1','PO4,dPO4US1D'], # remove from MPB
         'POP1,dSedPOP1' : ['POP1,dSedPOP1'], # sink
         'POP2,dSedPOP2' : ['POP2,dSedPOP2'], # sink
         'PO4,dPO4AutS1' : ['PO4,dPO4AUTS1'], # this is a water column source if MPB is on
         # this is all I can find for now
         'SUMS TO ZERO: Diat,dqmtdiat + PO4,dqmtdPO4 + POP1,dqmtdLP + POP2,dqmtdRP' : ['Diat,dqmtdiat','PO4,dqmtdPO4','POP1,dqmtdLP','POP2,dqmtdRP'], # there is probably some multiplier here too?
         'SUMS TO ZERO: Green,dqmtgree + PO4,dqmtgPO4 + POP1,dqmtgLP + POP2,dqmtgRP' : ['Green,dqmtgree','PO4,dqmtgPO4','POP1,dqmtgLP','POP2,dqmtgRP'],
         'SUMS TO ZERO: Diat,dPPDiat + Diat,dcPPDiat + Green,dPPGreen + Green,dcPPGreen + PO4,dPO4Upt': 
                                                                                     ['Diat,dPPDiat',
                                                                                      'Diat,dcPPDiat',
                                                                                      'Green,dPPGreen',
                                                                                      'Green,dcPPGreen',
                                                                                      'PO4,dPO4Upt',], 
         'SUMS TO ZERO: Diat,dMrtDiat + Green,dMrtGreen + POP1,dMortDetP + PO4,dPO4Aut' :  ['Diat,dMrtDiat', # dead water column algae become PON and NH4 
                                                                                        'Green,dMrtGreen',
                                                                                        'POP1,dMortDetP', 
                                                                                        'PO4,dPO4Aut'], 
         'SUMS TO ZERO: PO4,dMinPOP1 + POP1,dMinPOP1' : ['PO4,dMinPOP1','POP1,dMinPOP1'],   # these two sum to zero
         'SUMS TO ZERO: PO4,dMinPOP2 + POP2,dMinPOP2' : ['PO4,dMinPOP2','POP2,dMinPOP2'],   # these two sum to zero
         'SUMS TO ZERO: PO4,dMinDOP + DOP,dMinDOP' : ['PO4,dMinDOP','DOP,dMinDOP'],       # these two sum to zero    
         'SUMS TO ZERO: PO4,dZ_PRes + POP1,dZ_POP + POP1,dZ_PDef + POP1,dZ_PSpDet + Diat,dZ_Diat + Green,dZ_Grn + Zoopl_V,dZ_Vgr + Zoopl_R,dZ_SpwDet + Zoopl_R,dZ_Rgr + Zoopl_E,dZ_Ea + Zoopl_E,dZ_Ec' : [
                                 'PO4,dZ_PRes',
                                 'POP1,dZ_POP',
                                 'POP1,dZ_PDef',
                                 'POP1,dZ_PSpDet',
                                 'Diat,dZ_Diat',
                                 'Green,dZ_Grn',
                                 'Zoopl_V,dZ_Vgr',
                                 'Zoopl_R,dZ_SpwDet',
                                 'Zoopl_R,dZ_Rgr',
                                 'Zoopl_E,dZ_Ea',
                                 'Zoopl_E,dZ_Ec'],
         'SUMS TO ZERO: POP1,dZ_PMrt + POP1,dM_PMrt + POP1,dG4_PMrt + POP1,dM_PSpDet + POP1,dG4_PSpDet + Zoopl_V,dZ_Vmor + Zoopl_R,dZ_Rmor + Zoopl_E,dZ_Emor' : [
                                          'POP1,dZ_PMrt',      
                                          'POP1,dM_PMrt',
                                          'POP1,dG4_PMrt',
                                          'POP1,dM_PSpDet',
                                          'POP1,dG4_PSpDet',
                                          'Zoopl_V,dZ_Vmor',  
                                          'Zoopl_R,dZ_Rmor',  
                                          'Zoopl_E,dZ_Emor'],
         'SUMS TO ZERO: POP1,dCnvPPOP1 + POP2,dCnvPPOP1' : ['POP1,dCnvPPOP1','POP2,dCnvPPOP1'],
         'EACH IS ZERO: POP1,dResS1DetP + POP1,dResS2DetP + POP1,dResS1DiDP + POP1,dResS2DiDP' : [ 
                                          'POP1,dResS1DetP', 
                                          'POP1,dResS2DetP', 
                                          'POP1,dResS1DiDP', 
                                          'POP1,dResS2DiDP'],
         'EACH IS ZERO: POP2,dCnvPPOP2 + POP2,dMortOOP + POP2,dResS1OOP + PON2,POP2,dResS2OOP' : ['POP2,dCnvPPOP2','POP2,dMortOOP','POP2,dResS1OOP','POP2,dResS2OOP'],
         'SUMS TO ZERO: POP1,dCnvDPOP1 + DOP,dCnvDPOP1' : ['POP1,dCnvDPOP1','DOP,dCnvDPOP1'],
         'SUMS TO ZERO: POP2,dCnvDPOP2 + DOP,dCnvDPOP2' : ['POP2,dCnvDPOP2','DOP,dCnvDPOP2'],
    },
    'TSi' : {
         'Opal,dSedOpal' : ['Opal,dSedOpal'], # flux to sediment sink
         'Opal,dResS12DetS' : ['Opal,dResS1DetS','Opal,dResS2DetS'], # source resuspension of det si from S12
         'Opal,dResS12OOSi' : ['Opal,dResS1OOSi','Opal,dResS2OOSi'], # source resuspension flux of OOSi from S12
         'Opal,dResS12DiDS' : ['Opal,dResS1DiDS','Opal,dResS2DiDS'], # resuspension flux of opal from S12
         'Si,dSiAutS1' : ['Si,dSiAUTS1'], # source of Si from MPB
         'Si,dMinDetSiS12':['Si,dMinDetSiS','Si,dMinDetSS2'],  # sink to the sediments
         'Si,dMinOOSiS12':['Si,dMinOOSiS1','Si,dMinOOSiS2'],  # sink to the sediments
         'Si,dSiUptS1' : ['Si,dSiUptS1','Si,dSiUS1D'], # uptake by MPB to sediments
         'Algae,dSedAlgae' : ['Diat,dSedDiat', 'Green,dSedGreen'],  # this should be a SINK for TSi
        # should sum to zero
         'SUMS TO ZERO: Si,dDissolSi + Opal,dDissolSi' : ['Si,dDissolSi', 'Opal,dDissolSi'],
         'SUMS TO ZERO: Diat,dqmtdiat + Si,dqmtdSi + Opal,dqmtdLSi + Opal,dqmtdRSi' : ['Diat,dqmtdiat','Si,dqmtdSi','Opal,dqmtdLSi','Opal,dqmtdRSi'], # there is probably some multiplier here too?
         'SUMS TO ZERO: Green,dqmtgree + Si,dqmtgSi + Opal,dqmtgLSi + Opal,dqmtgRSi' : ['Green,dqmtgree','Si,dqmtgSi','Opal,dqmtgLSi','Opal,dqmtgRSi'],
         'SUMS TO ZERO: Diat,dMrtDiat + Green,dMrtGreen + Opal,dMortDetSi + Si,dSIaut + Opal,dMortOOSi' :  ['Diat,dMrtDiat','Green,dMrtGreen','Opal,dMortDetSi','Si,dSIaut','Opal,dMortOOSi'], 
         'SUMS TO ZERO: Diat,dPPDiat + Diat,dcPPDiat + Green,dPPGreen + Green,dcPPGreen + Si,dSIUpt': 
                                                                                     ['Diat,dPPDiat',
                                                                                      'Diat,dcPPDiat',
                                                                                      'Green,dPPGreen',
                                                                                      'Green,dcPPGreen',
                                                                                      'Si,dSIUpt',],
         'SUMS TO ZERO: Opal,dZ_SiDef + Opal,dZ_POSi + Diat,dZ_Diat + Green,dZ_Grn' : 
                                                                                    ['Opal,dZ_SiDef','Opal,dZ_POSi',
                                                                                     'Diat,dZ_Diat','Green,dZ_Grn']
    },
        #'TotalDetNS' : {'DetNS1,dMrtDetNS1' : ['DetNS1,dMrtDetNS1'], # source
    #                'DetNS1,dSedAlgN' : ['DetNS1,dSedAlgN'], # source
    #                'DetNS1,dSedPON1' : ['DetNS1,dSedPON1'], # source
    #                'OONS1,dSedPON2' : ['OONS1,dSedPON2'],  # source 
    #                'DetNS1,dMinDetNS1' : ['DetNS1,dMinDetNS1'], # sink 
    #                'DetNS2,dMinDetNS2' : ['DetNS2,dMinDetNS2'], # sink
    #                'OONS1,dMinOONS1' : ['OONS1,dMinOONS1'], # sink
    #                'OONS2,dMinOONS2' : ['OONS2,dMinOONS2'], # sink
    #                'DetNS2,dBurS2DetN' : ['DetNS2,dBurS2DetN'], # sink
    #                'OONS2,dBurS2OON' : ['OONS2,dBurS2OON'], # sink
    #                'SUMS TO ZERO: DetNS1,dBurS1DetN + DetNS2,dBurS1DetN' : ['DetNS1,dBurS1DetN', 'DetNS2,dBurS1DetN'],
    #                'SUMS TO ZERO: DetNS2,dDigS1DetN + DetNS1,dDigS1DetN' : ['DetNS2,dDigS1DetN', 'DetNS1,dDigS1DetN'],
    #                'SUMS TO ZERO: OONS1,dBurS1OON + OONS2,dBurS1OON' : ['OONS1,dBurS1OON', 'OONS2,dBurS1OON'],
    #                'SUMS TO ZERO: OONS1,dDigS1OON + OONS2,dDigS1OON' : ['OONS1,dDigS1OON', 'OONS2,dDigS1OON'],
    #                'EACH IS ZERO: DetNS1,dSWMinDNS1 + DetNS1,dZ_NMrtS1 + DetNS1,dZ_DNS1 + DetNS1,dResS1DetN + DetNS1,dSWBuS1DtN' : ['DetNS1,dSWMinDNS1',
    #                                                          'DetNS1,dZ_NMrtS1','DetNS1,dZ_DNS1','DetNS1,dResS1DetN','DetNS1,dSWBuS1DtN'],
    #                'EACH IS ZERO: DetNS2,dSWMinDNS2 + DetNS2,dResS2DetN + DetNS2,dDigS2DetN' : ['DetNS2,dSWMinDNS2', 'DetNS2,dResS2DetN', 'DetNS2,dDigS2DetN'],
    #                'EACH IS ZERO: OONS1,dSWMnOONS1 + OONS1,dResS1OON + OONS1,dSWBuS1OON' : ['OONS1,dSWMnOONS1','OONS1,dResS1OON','OONS1,dSWBuS1OON'],
    #                'EACH IS ZERO: OONS2,dSWMnOONS2 + OONS2,dResS2OON + OONS2,dDigS2OON' : ['OONS2,dSWMnOONS2','OONS2,dResS2OON', 'OONS2,dDigS2OON'],},
      #  'TN_include_sediment' : {
  #           'NO3,dDenit' : ['NO3,dDenitWat','NO3,dDenitSed','NO3,dNiDen'], # this should be a SINK for TN
  #           'DetNS2,dBurS2DetN' : ['DetNS2,dBurS2DetN'], # this appears to act as a true SINK for TN as well
  #           'OONS2,dBurS2OON' : ['OONS2,dBurS2OON'], # true sink
  #           'DiatS1,dBurS1Diat' : ['DiatS1,dBurS1Diat'], # burial of benthic algae also seems to be a true sink
  #           # in the PRE August 2020 model this does NOT sum to zero but it should
  #           'SUMS TO ZERO: Diat,dPPDiat + Diat,dcPPDiat + Green,dPPGreen + Green,dcPPGreen + NH4,dNH4Upt + NO3,dNO3Upt' : 
  #                                                                                   ['Diat,dPPDiat',
  #                                                                                    'Diat,dcPPDiat',
  #                                                                                    'Green,dPPGreen',
  #                                                                                    'Green,dcPPGreen',
  #                                                                                    'NH4,dNH4Upt',
  #                                                                                    'NO3,dNO3Upt'],
  #           # identify groups of terms that sum to zero
  #           'SUMS TO ZERO: NH4,dNH4UptS1 + NH4,dNH4US1D + NO3,dNO3UptS1 + DiatS1,dPPDiatS1' : ['NH4,dNH4UptS1', # these terms sum to zero, benthic algae productivity
  #                                                                                      'NH4,dNH4US1D', 
  #                                                                                      'NO3,dNO3UptS1', 
  #                                                                                      'DiatS1,dPPDiatS1'], 
  #           'SUMS TO ZERO: NO3,dNitrif + NH4,dNitrif' : ['NO3,dNitrif','NH4,dNitrif'],      # these two sum to zero
  #           'SUMS TO ZERO: DON,dCnvDPON1 + PON1,dCnvDPON1' : ['DON,dCnvDPON1','PON1,dCnvDPON1'], # these two sum to zero
  #           'SUMS TO ZERO: NH4,dMinPON1 + PON1,dMinPON1' : ['NH4,dMinPON1','PON1,dMinPON1'],   # these two sum to zero
  #           'SUMS TO ZERO: NH4,dMinDON + DON,dMinDON' : ['NH4,dMinDON','DON,dMinDON'],       # these two sum to zero
  #           'SUMS TO ZERO: DiatS1,dMrtDiatS1 + DetNS1,dMrtDetNS1 + OONS1,dMrtOONS1 + NH4,dNH4AUTS1' : ['DiatS1,dMrtDiatS1', # when benthic algae die, some goes into detritus, some goes to water column via autolysis 
  #                                                                            'DetNS1,dMrtDetNS1',
  #                                                                            'OONS1,dMrtOONS1', 
  #                                                                            'NH4,dNH4AUTS1'],
  #           'SUMS TO ZERO: Diat,dMrtDiat + Green,dMrtGreen + PON1,dMortDetN + NH4,dNH4Aut' :  ['Diat,dMrtDiat', # dead water column algae become PON and NH4 
  #                                                                                      'Green,dMrtGreen',
  #                                                                                      'PON1,dMortDetN',
  #                                                                                      'NH4,dNH4Aut'], 
  #           'SUMS TO ZERO: NH4,dZ_NRes + PON1,dZ_PON1 + PON1,dZ_NDef + PON1,dZ_NSpDet + Diat,dZ_Diat + Green,dZ_Grn + Zoopl_V,dZ_Vgr + Zoopl_R,dZ_SpwDet + Zoopl_R,dZ_Rgr + Zoopl_E,dZ_Ea + Zoopl_E,dZ_Ec' : [
  #                               'NH4,dZ_NRes',
  #                               'PON1,dZ_PON1',
  #                               'PON1,dZ_NDef',
  #                               'PON1,dZ_NSpDet',
  #                               'Diat,dZ_Diat',
  #                               'Green,dZ_Grn',
  #                               'Zoopl_V,dZ_Vgr',
  #                               'Zoopl_R,dZ_SpwDet',
  #                               'Zoopl_R,dZ_Rgr',
  #                               'Zoopl_E,dZ_Ea',
  #                               'Zoopl_E,dZ_Ec'],
  #           'SUMS TO ZERO: PON1,dSedPON1 + DetNS1,dSedPON1' : ['PON1,dSedPON1', # these still sum to zero with benthic algae
  #                                                      'DetNS1,dSedPON1'],
  #           'SUMS TO ZERO: NH4,dMinDetNS1 + NH4,dMinDetNS2 + DetNS1,dMinDetNS1 + DetNS2,dMinDetNS2' : ['NH4,dMinDetNS1',    # these still sum to zero with benthic algae
  #                                                                                              'NH4,dMinDetNS2', 
  #                                                                                              'DetNS1,dMinDetNS1',
  #                                                                                              'DetNS2,dMinDetNS2'],
  #           'SUMS TO ZERO: Mussel_V,dM_Vmor + Mussel_E,dM_Emor + Mussel_R,dM_Rmor + DetNS1,dM_NMrtS1' : ['Mussel_V,dM_Vmor',
  #                                                                                                   'Mussel_E,dM_Emor',
  #                                                                                                   'Mussel_R,dM_Rmor', 
  #                                                                                                   'DetNS1,dM_NMrtS1'],
  #           'SUMS TO ZERO: Grazer4_V,dG4_Vmor + Grazer4_E,dG4_Emor + Grazer4_R,dG4_Rmor + DetNS1,dG4_NMrtS1' : ['Grazer4_V,dG4_Vmor',
  #                                                                                                          'Grazer4_E,dG4_Emor',
  #                                                                                                          'Grazer4_R,dG4_Rmor',
  #                                                                                                          'DetNS1,dG4_NMrtS1'],
  #           'SUMS TO ZERO: NH4,dM_NRes + PON1,dM_NDef + PON1,dM_PON1 + Diat,dM_Diat + Mussel_V,dM_Vgr + Mussel_E,dM_Ea + Mussel_E,dM_Ec + Mussel_R,dM_Rgr' : ['NH4,dM_NRes',
  #                     'PON1,dM_NDef',
  #                     'PON1,dM_PON1',
  #                     'Diat,dM_Diat',
  #                     'Mussel_V,dM_Vgr',
  #                     'Mussel_E,dM_Ea',
  #                     'Mussel_E,dM_Ec',
  #                     'Mussel_R,dM_Rgr'],
  #           'SUMS TO ZERO: NH4,dG4_NRes + PON1,dG4_NDef + PON1,dG4_PON1 + Diat,dG4_Diat + Grazer4_V,dG4_Vgr + Grazer4_E,dG4_Ea + Grazer4_E,dG4_Ec + Grazer4_R,dG4_Rgr' : ['NH4,dG4_NRes',
  #                       'PON1,dG4_NDef',
  #                       'PON1,dG4_PON1',
  #                       'Diat,dG4_Diat',
  #                       'Grazer4_V,dG4_Vgr',
  #                       'Grazer4_E,dG4_Ea',
  #                       'Grazer4_E,dG4_Ec',
  #                       'Grazer4_R,dG4_Rgr'],
  #           'SUMS TO ZERO: PON1,dZ_NMrt + PON1,dM_NMrt + PON1,dG4_NMrt + PON1,dM_NSpDet + PON1,dG4_NSpDet + Zoopl_V,dZ_Vmor + Zoopl_R,dZ_Rmor + Zoopl_E,dZ_Emor' : [
  #                                        'PON1,dZ_NMrt',      
  #                                        'PON1,dM_NMrt',
  #                                        'PON1,dG4_NMrt',
  #                                        'PON1,dM_NSpDet',
  #                                        'PON1,dG4_NSpDet',
  #                                        'Zoopl_V,dZ_Vmor',  
  #                                        'Zoopl_R,dZ_Rmor',  
  #                                        'Zoopl_E,dZ_Emor'],   
  #           'SUMS TO ZERO: DetNS1,dBurS1DetN + DetNS2,dBurS1DetN' : ['DetNS1,dBurS1DetN', 'DetNS2,dBurS1DetN'],  # these still sum to zero with benthic algae
  #           'SUMS TO ZERO: Diat,dSedDiat + Green,dSedGreen + DetNS1,dSedAlgN' :  ['Diat,dSedDiat','Green,dSedGreen','DetNS1,dSedAlgN'], # these still sum to zero with benthic algae
  #           'SUMS TO ZERO: PON1,dCnvPPON1 + PON2,dCnvPPON1' : ['PON1,dCnvPPON1','PON2,dCnvPPON1'],   #### NEW #### these are currently nonzero but sum to zero
  #           'SUMS TO ZERO: NH4,dMinPON2 + PON2,dMinPON2' : ['NH4,dMinPON2','PON2,dMinPON2'],   #### NEW #### these are currently nonzero but sum to zero
  #           'SUMS TO ZERO: OONS2,dBurS1OON + OONS1,dBurS1OON' : ['OONS2,dBurS1OON','OONS1,dBurS1OON'], #### NEW #### these are currently nonzero but sum to zero
  #           'SUMS TO ZERO: OONS1,dSedPON2 + PON2,dSedPON2' : ['OONS1,dSedPON2','PON2,dSedPON2'], #### NEW #### these are currently nonzero but sum to zero
  #           'SUMS TO ZERO: OONS1,dMinOONS1 + NH4,dMinOONS1' : ['OONS1,dMinOONS1','NH4,dMinOONS1'], #### NEW #### these are currently nonzero but sum to zero
  #           'SUMS TO ZERO: OONS2,dMinOONS2 + NH4,dMinOONS2' : ['OONS2,dMinOONS2','NH4,dMinOONS2'], #### NEW #### these are currently nonzero but sum to zero
  #           'SUMS TO ZERO: PON2,dCnvPPON2 + DON,dCnvDPON2' : ['PON2,dCnvPPON2','DON,dCnvDPON2'], #### NEW #### each is zero for now (and I suspect they sum to zero anyway)
  #           'SUMS TO ZERO: PON2,dResS1OON + OONS1,dResS1OON' : ['PON2,dResS1OON','OONS1,dResS1OON'], #### NEW #### each is zero for now (and I suspect they sum to zero anyway)
  #           'SUMS TO ZERO: PON2,dResS2OON + OONS2,dResS2OON' : ['PON2,dResS2OON','OONS2,dResS2OON'], #### NEW #### each is zero for now (and I suspect they sum to zero anyway)
  #           'SUMS TO ZERO: OONS1,dDigS1OON + OONS2,dDigS1OON' : ['OONS1,dDigS1OON','OONS2,dDigS1OON'], #### NEW #### each is zero for now (and I suspect they sum to zero anyway)
  #           'EACH IS ZERO: PON1,dResS1DetN + PON1,dResS2DetN + PON1,dResS1DiDN + PON1,dResS2DiDN' : [ # each of these is zero
  #                                        'PON1,dResS1DetN', 
  #                                        'PON1,dResS2DetN', 
  #                                        'PON1,dResS1DiDN', 
  #                                        'PON1,dResS2DiDN'],    
  #           'EACH IS ZERO: DetNS1,dZ_NMrtS1 + DetNS1,dZ_DNS1 + DetNS1,dM_DNS1 + DetNS1,dG4_DNS1' :   [
  #                       'DetNS1,dZ_NMrtS1',
  #                       'DetNS1,dZ_DNS1',
  #                       'DetNS1,dM_DNS1',
  #                       'DetNS1,dG4_DNS1'],
  #           'EACH IS ZERO: DetNS1,dSWMinDNS1 + DetNS1,dResS1DetN + DetNS1,dSWBuS1DtN + DetNS1,dDigS1DetN' : [
  #                       'DetNS1,dSWMinDNS1',
  #                       'DetNS1,dResS1DetN',
  #                       'DetNS1,dSWBuS1DtN',
  #                       'DetNS1,dDigS1DetN'],
  #           'EACH IS ZERO: DetNS2,dSWMinDNS2 + DetNS2,dResS2DetN + DetNS2,dDigS1DetN + DetNS2,dDigS2DetN' : [
  #                       'DetNS2,dSWMinDNS2',
  #                       'DetNS2,dResS2DetN',
  #                       'DetNS2,dDigS1DetN',
  #                       'DetNS2,dDigS2DetN'],
  #           'EACH IS ZERO: Mussel_R,dM_SpwDet + Grazer4_R,dG4_SpwDet' : ['Mussel_R,dM_SpwDet','Grazer4_R,dG4_SpwDet'],
  #           'EACH IS ZERO: DiatS1,dResS1Diat + DiatS1,dSWBuS1Dia + DiatS1,dDigS1Diat' : ['DiatS1,dResS1Diat', # new benthic algae terms, each one is zero
  #                                                                                                'DiatS1,dSWBuS1Dia', 
  #                                                                                                'DiatS1,dDigS1Diat'],              
  #           'EACH IS ZERO: PON2,dCnvDPON2 + PON2,dMortOON' : ['PON2,dCnvDPON2', 'PON2,dMortOON'], #### NEW #### each is zero
  #           'EACH IS ZERO: OONS1,dSWMnOONS1 + OONS1,dSWBuS1OON' : ['OONS1,dSWMnOONS1','OONS1,dSWBuS1OON'], #### NEW #### each is zero, and I can't find matches for them
  #           'EACH IS ZERO: OONS2,dSWMnOONS2 + OONS2,dDigS2OON' : ['OONS2,dSWMnOONS2', 'OONS2,dDigS2OON'],             
  #  },
######## NOTE THIS NEEDS TO BE UPDATED SO THAT THE SEDMOD VALUES WORK OUT
    # 'TN_plus_DiatS1_plus_DetNS12' : {
    #          'NO3,dDenit' : ['NO3,dDenitWat','NO3,dDenitSed','NO3,dNiDen'], # this should be a SINK for TN
    #          'NO3,dDetDenit' : ['NO3,ddetcs1nit','NO3,ddetcs2nit'],
    #          'NO3,dOODenit' : ['NO3,doocs1nit','NO3,doocs2nit'],
    #          ###'DetNS2,dBurS2DetN' : ['DetNS2,dBurS2DetN'], # this appears to act as a true SINK for TN as well
    #          ###'DiatS1,dBurS1Diat' : ['DiatS1,dBurS1Diat'], # burial of benthic algae also seems to be a true sink
    #          ###'PON2,dSedPON2' : ['PON2,dSedPON2'], # sink to OONS2
    #          'NH4,dMinOONS12' :  ['NH4,dMinOONS1', 'NH4,dMinOONS2','NH4,doons1min','NH4,doons2min'], # this is a source
    #          'SUMS TO ZERO: Diat,dqmtdiat + NH4,dqmtdNH4 + PON1,dqmtdLN + PON2,dqmtdRN' : ['Diat,dqmtdiat','NH4,dqmtdNH4','PON1,dqmtdLN','PON2,dqmtdRN'],
    #          'SUMS TO ZERO: Green,dqmtgree + NH4,dqmtgNH4 + PON1,dqmtgLN + PON2,dqmtgRN' : ['Green,dqmtgree','NH4,dqmtgNH4','PON1,dqmtgLN','PON2,dqmtgRN'],
    #          'SUMS TO ZERO: Diat,dPPDiat + Diat,dcPPDiat + Green,dPPGreen + Green,dcPPGreen + NH4,dNH4Upt + NO3,dNO3Upt' : 
    #                                                                                  ['Diat,dPPDiat',
    #                                                                                   'Diat,dcPPDiat',
    #                                                                                   'Green,dPPGreen',
    #                                                                                   'Green,dcPPGreen',
    #                                                                                   'NH4,dNH4Upt',
    #                                                                                   'NO3,dNO3Upt'],
    #          # identify groups of terms that sum to zero
    #          'SUMS TO ZERO: NH4,dNH4UptS1 + NH4,dNH4US1D + NO3,dNO3UptS1 + DiatS1,dPPDiatS1' : ['NH4,dNH4UptS1', # these terms sum to zero, benthic algae productivity
    #                                                                                     'NH4,dNH4US1D', 
    #                                                                                     'NO3,dNO3UptS1', 
    #                                                                                     'DiatS1,dPPDiatS1'], 
    #          'SUMS TO ZERO: NO3,dNitrif + NH4,dNitrif' : ['NO3,dNitrif','NH4,dNitrif'],      # these two sum to zero
    #          'SUMS TO ZERO: DON,dCnvDPON1 + PON1,dCnvDPON1' : ['DON,dCnvDPON1','PON1,dCnvDPON1'], # these two sum to zero
    #          'SUMS TO ZERO: NH4,dMinPON1 + PON1,dMinPON1' : ['NH4,dMinPON1','PON1,dMinPON1'],   # these two sum to zero
    #          'SUMS TO ZERO: NH4,dMinDON + DON,dMinDON' : ['NH4,dMinDON','DON,dMinDON'],       # these two sum to zero
    #          'SUMS TO ZERO: DiatS1,dMrtDiatS1 + DetNS1,dMrtDetNS1 + OONS1,dMrtOONS1 + NH4,dNH4AUTS1' : ['DiatS1,dMrtDiatS1', # when benthic algae die, some goes into detritus, some goes to water column via autolysis 
    #                                                                           'DetNS1,dMrtDetNS1', 
    #                                                                           'OONS1,dMrtOONS1',
    #                                                                           'NH4,dNH4AUTS1'],
    #          'SUMS TO ZERO: Diat,dMrtDiat + Green,dMrtGreen + PON1,dMortDetN + NH4,dNH4Aut' :  ['Diat,dMrtDiat', # dead water column algae become PON and NH4 
    #                                                                                     'Green,dMrtGreen',
    #                                                                                     'PON1,dMortDetN',
    #                                                                                     'NH4,dNH4Aut'], 
    #          'SUMS TO ZERO: NH4,dZ_NRes + PON1,dZ_PON1 + PON1,dZ_NDef + PON1,dZ_NSpDet + Diat,dZ_Diat + Green,dZ_Grn + Zoopl_V,dZ_Vgr + Zoopl_R,dZ_SpwDet + Zoopl_R,dZ_Rgr + Zoopl_E,dZ_Ea + Zoopl_E,dZ_Ec' : [
    #                              'NH4,dZ_NRes',
    #                              'PON1,dZ_PON1',
    #                              'PON1,dZ_NDef',
    #                              'PON1,dZ_NSpDet',
    #                              'Diat,dZ_Diat',
    #                              'Green,dZ_Grn',
    #                              'Zoopl_V,dZ_Vgr',
    #                              'Zoopl_R,dZ_SpwDet',
    #                              'Zoopl_R,dZ_Rgr',
    #                              'Zoopl_E,dZ_Ea',
    #                              'Zoopl_E,dZ_Ec'],
    #          'SUMS TO ZERO: PON1,dSedPON1 + DetNS1,dSedPON1' : ['PON1,dSedPON1', # these still sum to zero with benthic algae
    #                                                     'DetNS1,dSedPON1'],
    #          'SUMS TO ZERO: NH4,dMinDetNS1 + NH4,dMinDetNS2 + NH4,ddetns1min + NH4,ddetns2min + DetNS1,dMinDetNS1 + DetNS2,dMinDetNS2 + DetNS1,ddetns1min + DetNS2,ddetns2min' : ['NH4,dMinDetNS1', 'NH4,dMinDetNS2','NH4,ddetns1min','NH4,ddetns2min','DetNS1,dMinDetNS1','DetNS2,dMinDetNS2','DetNS1,ddetns1min','DetNS2,ddetns2min'],
    #          'SUMS TO ZERO: Mussel_V,dM_Vmor + Mussel_E,dM_Emor + Mussel_R,dM_Rmor + DetNS1,dM_NMrtS1' : ['Mussel_V,dM_Vmor',
    #                                                                                                  'Mussel_E,dM_Emor',
    #                                                                                                  'Mussel_R,dM_Rmor', 
    #                                                                                                  'DetNS1,dM_NMrtS1'],
    #          'SUMS TO ZERO: Grazer4_V,dG4_Vmor + Grazer4_E,dG4_Emor + Grazer4_R,dG4_Rmor + DetNS1,dG4_NMrtS1' : ['Grazer4_V,dG4_Vmor',
    #                                                                                                         'Grazer4_E,dG4_Emor',
    #                                                                                                         'Grazer4_R,dG4_Rmor',
    #                                                                                                         'DetNS1,dG4_NMrtS1'],
    #          'SUMS TO ZERO: NH4,dM_NRes + PON1,dM_NDef + PON1,dM_PON1 + Diat,dM_Diat + Mussel_V,dM_Vgr + Mussel_E,dM_Ea + Mussel_E,dM_Ec + Mussel_R,dM_Rgr' : ['NH4,dM_NRes',
    #                    'PON1,dM_NDef',
    #                    'PON1,dM_PON1',
    #                    'Diat,dM_Diat',
    #                    'Mussel_V,dM_Vgr',
    #                    'Mussel_E,dM_Ea',
    #                    'Mussel_E,dM_Ec',
    #                    'Mussel_R,dM_Rgr'],
    #          'SUMS TO ZERO: NH4,dG4_NRes + PON1,dG4_NDef + PON1,dG4_PON1 + Diat,dG4_Diat + Grazer4_V,dG4_Vgr + Grazer4_E,dG4_Ea + Grazer4_E,dG4_Ec + Grazer4_R,dG4_Rgr' : ['NH4,dG4_NRes',
    #                      'PON1,dG4_NDef',
    #                      'PON1,dG4_PON1',
    #                      'Diat,dG4_Diat',
    #                      'Grazer4_V,dG4_Vgr',
    #                      'Grazer4_E,dG4_Ea',
    #                      'Grazer4_E,dG4_Ec',
    #                      'Grazer4_R,dG4_Rgr'],   
    #          'SUMS TO ZERO: PON1,dZ_NMrt + PON1,dM_NMrt + PON1,dG4_NMrt + PON1,dM_NSpDet + PON1,dG4_NSpDet + Zoopl_V,dZ_Vmor + Zoopl_R,dZ_Rmor + Zoopl_E,dZ_Emor' : [
    #                                       'PON1,dZ_NMrt',      
    #                                       'PON1,dM_NMrt',
    #                                       'PON1,dG4_NMrt',
    #                                       'PON1,dM_NSpDet',
    #                                       'PON1,dG4_NSpDet',
    #                                       'Zoopl_V,dZ_Vmor',  
    #                                       'Zoopl_R,dZ_Rmor',  
    #                                       'Zoopl_E,dZ_Emor'], 
    #          'SUMS TO ZERO: DetNS1,dBurS1DetN + DetNS2,dBurS1DetN' : ['DetNS1,dBurS1DetN', 'DetNS2,dBurS1DetN'],  # these still sum to zero with benthic algae
    #          'SUMS TO ZERO: Diat,dSedDiat + Green,dSedGreen + DetNS1,dSedAlgN' :  ['Diat,dSedDiat','Green,dSedGreen','DetNS1,dSedAlgN'], # these still sum to zero with benthic algae
    #          'SUMS TO ZERO: PON1,dCnvPPON1 + PON2,dCnvPPON1' : ['PON1,dCnvPPON1','PON2,dCnvPPON1'],   #### NEW #### these are currently nonzero but sum to zero
    #          'SUMS TO ZERO: NH4,dMinPON2 + PON2,dMinPON2' : ['NH4,dMinPON2','PON2,dMinPON2'],   #### NEW #### these are currently nonzero but sum to zero
    #          'SUMS TO ZERO: PON2,dCnvPPON2 + DON,dCnvDPON2' : ['PON2,dCnvPPON2','DON,dCnvDPON2'], #### NEW #### each is zero for now (and I suspect they sum to zero anyway)
    #          'EACH IS ZERO: PON1,dResS1DetN + PON1,dResS2DetN + PON1,dResS1DiDN + PON1,dResS2DiDN' : [ # each of these is zero
    #                                       'PON1,dResS1DetN', 
    #                                       'PON1,dResS2DetN', 
    #                                       'PON1,dResS1DiDN', 
    #                                       'PON1,dResS2DiDN'],   
    #          'EACH IS ZERO: DetNS1,dZ_NMrtS1 + DetNS1,dZ_DNS1 + DetNS1,dM_DNS1 + DetNS1,dG4_DNS1' :   [
    #                      'DetNS1,dZ_NMrtS1',
    #                      'DetNS1,dZ_DNS1',
    #                      'DetNS1,dM_DNS1',
    #                      'DetNS1,dG4_DNS1'],
    #          'EACH IS ZERO: DetNS1,dSWMinDNS1 + DetNS1,dResS1DetN + DetNS1,dSWBuS1DtN + DetNS1,dDigS1DetN' : [
    #                      'DetNS1,dSWMinDNS1',
    #                      'DetNS1,dResS1DetN',
    #                      'DetNS1,dSWBuS1DtN',
    #                      'DetNS1,dDigS1DetN'],
    #          'EACH IS ZERO: DetNS2,dSWMinDNS2 + DetNS2,dResS2DetN + DetNS2,dDigS1DetN + DetNS2,dDigS2DetN' : [
    #                      'DetNS2,dSWMinDNS2',
    #                      'DetNS2,dResS2DetN',
    #                      'DetNS2,dDigS1DetN',
    #                      'DetNS2,dDigS2DetN'],
    #          'EACH IS ZERO: Mussel_R,dM_SpwDet + Grazer4_R,dG4_SpwDet' : ['Mussel_R,dM_SpwDet','Grazer4_R,dG4_SpwDet'],
    #          'EACH IS ZERO: DiatS1,dResS1Diat + DiatS1,dSWBuS1Dia + DiatS1,dDigS1Diat' : ['DiatS1,dResS1Diat', # new benthic algae terms, each one is zero
    #                                                                                               'DiatS1,dSWBuS1Dia', 
    #                                                                                               'DiatS1,dDigS1Diat'],              
    #          'EACH IS ZERO: PON2,dCnvDPON2' : ['PON2,dCnvDPON2'], #### NEW #### each is zero 
    #          'EACH IS ZERO: PON2,dMortOON' : ['PON2,dMortOON'], #### NEW #### each is zero for now 
    #          'EACH IS ZERO: PON2,dResS1OON' : ['PON2,dResS1OON'], #### NEW #### each is zero for now 
    #          'EACH IS ZERO: PON2,dResS2OON' : ['PON2,dResS2OON'] #### NEW #### each is zero for now 
             
    # },
    # have not gotten to these yet, leaving reactions ungrouped...
    'TP_include_sediment' : {},
    'TotalDetPS' : {},
    'TotalDetSi' : {},
    'Grazer4' : {},
    'Mussel' : {},
    'Clams' : {}
    # add total silica 
}

# which parameters to check for mass conservation? put them in a list
# (this is used for step4_check_mass_conservation.py)
mass_cons_check_param_list = ['N-Algae',
                              'N-Zoopl',
                              'Algae',
                              'Zoopl',
                              'DIN',
                              'TN',
                              'TSi',
                              'TN_plus_DiatS1_plus_DetNS12',
                              'TP',
                              'DetNS12',
                              'OONS12']

# for each parameter in mass_cons_check_param_list, pick a reaction to normalize everything by -- error in the terms
# that should be zero will be measured as a percentage of this term (this is used for step4_check_mass_conservation.py)
mass_cons_check_normalize_by_dict = {'N-Algae' : 'Diat,dPPDiat',
                                     'N-Zoopl' : 'Zoopl_E,dZ_Ea',
                                     'Algae' : 'Diat,dPPDiat',
                                     'Zoopl' : 'Zoopl_E,dZ_Ea',
                                     'DIN' : 'DIN,dDINUpt',
                                     'TN' : 'NH4,dMinDetNS12',
                                     'TN_plus_DiatS1_plus_DetNS12' : 'NH4,dMinOONS12',
                                     'TP' : 'PO4,dMinDetPS12',
                                     'TSi' : 'Si,dMinDetSiS12',
                                     'DetNS12' : 'DetNS1,dSedPON1',
                                     'OONS12' : 'OONS1,dSedPON2'}

##############################
# import stuff
##############################

import sys, os
import logging
import datetime
import xarray as xr
if not stompy_dir in sys.path:
    sys.path.insert(0,stompy_dir)
from stompy.model.delft import waq_scenario
import stompy.model.delft.io as dio
import socket

##############################
# functions
##############################

def get_shapefile_paths(model_input_dir, runid, is_delta):

    '''
    poly_path, tran_path = get_shapefile_paths(model_input_dir, runid, is_delta)

    given the path to the base directory for all our model input, the runid, and boolean saying whether or not this is a delta run,
    automatically find the path to the shapefiles used to set up the run (note we are using an earlier version of the open bay FR shapefiles, 
    which match the later version except that the later verison has some more polygons that we aren't analyzing, so saves space to leave them out
    '''

    if is_delta:

        # path to shapefiles used in final delta runs
        tran_path =  os.path.join(model_input_dir,'Delta','inputs','shapefiles','control_volumes','Delta_Fullres_Transects_Dave_Plus_WB_v4.shp')
        poly_path = os.path.join(model_input_dir,'Delta','inputs','shapefiles','control_volumes','Delta_Fullres_Polygons_Dave_Plus_WB_v4.shp')

    elif 'G673' in runid:

        # path to shapefiles used in aggregated grid runs
        tran_path = os.path.join(model_input_dir,'inputs','shapefiles','Agg_exchange_lines_673.shp')
        poly_path =  os.path.join(model_input_dir,'inputs','shapefiles','Agg_mod_contiguous_673.shp')

    elif 'G141' in runid: # path to shapefiles used in aggregated grid runs

        if is_v24:        
            tran_path = os.path.join(model_input_dir,'inputs','shapefiles','Agg_exchange_lines_v24-agg141.shp')
            poly_path =  os.path.join(model_input_dir,'inputs','shapefiles','Agg_mod_contiguous_v24-agg141.shp')
        else:       
            tran_path = os.path.join(model_input_dir,'inputs','shapefiles','Agg_exchange_lines_141.shp')
            poly_path =  os.path.join(model_input_dir,'inputs','shapefiles','Agg_mod_contiguous_141.shp')


    elif 'FR' in runid:

        if is_v24:
            tran_path = os.path.join(model_input_dir,'inputs','shapefiles','Agg_exchange_lines_v24.shp')
            poly_path = os.path.join(model_input_dir,'inputs','shapefiles','Agg_mod_contiguous_v24.shp')
        else:
            # drop the subembayments b/c haven't worked up a multiplier for sediment concentration 
            # for these polygons -- Allie March 2025
            #tran_path = os.path.join(model_input_dir,'inputs','shapefiles','Agg_exchange_lines_plus_subembayments_shoal_channel.shp')
            #poly_path = os.path.join(model_input_dir,'inputs','shapefiles','Agg_mod_contiguous_plus_subembayments_shoal_channel.shp')
            tran_path = os.path.join(model_input_dir,'inputs','shapefiles','Agg_exchange_lines.shp')
            poly_path = os.path.join(model_input_dir,'inputs','shapefiles','Agg_mod_contiguous.shp')

    return poly_path, tran_path

def get_group_def_path(runid):

    '''
    group_def_path, group_con_path = get_group_def_path(runid)

    get the filenames for the group definition file and the group connectivity file, assuming they are in 
    the same repository as this script... later we will make a copy of these files into the run folder for record
    keeping purposes
    '''

    # directory where the aggregated groups are defined (this is an input directory, probably don't want to change it)
    group_def_dir = os.path.join('..','..','Definitions','group_definitions')

    # filenames
    if 'FR' in runid:
        res = 'FR'
    elif 'G673' in runid:
        res = '673'
    elif 'G141' in runid:
        res = '141'
    else:
        raise Exception('runid %s does not fit expected pattern' % runid)

    # version
    if is_v24:
        ver = '_v24'
    else:
        ver = ''

    group_def_path = os.path.abspath(os.path.join(group_def_dir,'control_volume_definitions%s_%s.txt' % (ver,res)))
    group_con_path = os.path.abspath(os.path.join(group_def_dir,'connectivity_definitions%s_%s.txt' % (ver,res)))

    return group_def_path, group_con_path

def get_sed_conc_mult_path(runid):

    # filenames
    if 'FR' in runid:
        sed_conc_mult_path = os.path.join('..','..','Definitions','sed_conc_multipliers','Multiply_Polygon_Sediment_Conc_By_FR.csv')
    elif 'G141' in runid:
        sed_conc_mult_path = os.path.join('..','..','Definitions','sed_conc_multipliers','Multiply_Polygon_Sediment_Conc_By_Agg.csv')
    else:
        sed_conc_mult_path = None

    return sed_conc_mult_path
    

def get_water_year(runid):

    '''
    water_year = get_water_year(runid)

    given the runid, get the string for the water year folder the run is stored in
    '''

    if 'FR' in runid:
        # this extracts the 2 digit water year, assuming format of runid is like FR13_003 for WY2013 run 003
        yr = int(runid.split('_')[0][2:])
        # turn into water year string
        water_year = 'WY%d' % (2000 + yr)

    elif 'G673' in runid:

        # there are two formats for agg runs, G673_13_003 is water year 2013, G673_13to18_207 is water years 2013-2018
        # get the string that represents the water year
        yr = runid.split('_')[1]
        # if it spans mutlple water years (such as '13to18'), keep the string, just add 'WY' in front of it
        if 'to' in yr:
            water_year = 'WY' + yr
        # otherwise extract the integer and add it to 2000
        else:
            water_year = 'WY%d' % (2000 + int(yr))

    elif 'G141' in runid:

        # there are two formats for agg runs, G141_13_003 is water year 2013, G141_13to18_207 is water years 2013-2018
        # get the string that represents the water year
        yr = runid.split('_')[1]
        # if it spans mutlple water years (such as '13to18'), keep the string, just add 'WY' in front of it
        if 'to' in yr:
            water_year = 'WY' + yr
        # otherwise extract the integer and add it to 2000
        else:
            water_year = 'WY%d' % (2000 + int(yr))
    else:
        raise Exception('runid %s does not fit expected pattern' % runid)

    return water_year

def get_run_dir(model_run_base_dir, runid, is_delta, is_tracer):

    '''
    run_dir = get_run_dir(model_run_base_dir, runid, is_delta)

    given the path to the base directory for all our model input, the runid, and boolean saying whether or not this is a delta run,
    automatically find the path to the directory for the run, where all the input and output files are stored
    '''

    # paths *.his and *-bal.his files, *.lsp file
    if 'richmondvol1' in model_run_base_dir:
        if is_delta:
            run_dir = os.path.join(model_run_base_dir,'Delta','BGC_model','Full_res',runid)
        elif 'FR' in runid:
            water_year = get_water_year(runid)
            run_dir = os.path.join(model_run_base_dir,'Full_res',water_year,runid)
        elif 'G673' in runid:
            water_year = get_water_year(runid)
            run_dir = os.path.join(model_run_base_dir,'Grid673',water_year,runid)
        elif 'G141' in runid:
            water_year = get_water_year(runid)
            run_dir = os.path.join(model_run_base_dir,'Grid141',water_year,runid)
        else:
            raise Exception('runid %s does not fit expected pattern' % runid)
    else:
        if is_delta:
            raise Exception('need to revise step0_config.py to accomodate delta runs on servers besides richmond')
        elif ('FR' in runid) & (not is_tracer):
            print('here')
            water_year = get_water_year(runid)
            run_dir = os.path.join(model_run_base_dir,'open_bay','bgc','full_res',water_year,runid)
        elif 'G673' in runid:
            water_year = get_water_year(runid)
            run_dir = os.path.join(model_run_base_dir,'open_bay','bgc','agg673',water_year,runid)
        elif 'G141' in runid:
            water_year = get_water_year(runid)
            run_dir = os.path.join(model_run_base_dir,'open_bay','bgc','agg',water_year,runid)
        elif ('FR' in runid) & (is_tracer):
            print('here2')
            water_year = get_water_year(runid)
            run_dir = os.path.join(model_run_base_dir,'open_bay','tracer','full_res',water_year,runid,'data_tracer')
        else:
            raise Exception('runid %s does not fit expected pattern' % runid)
            
    return run_dir

def get_lsp_path(run_dir, is_delta, is_tracer):

    '''
    lsp_path = get_lsp_path(run_dir, is_delta)

    given the path to the base directory for all our model input, the runid, and boolean saying whether or not this is a delta run,
    automatically find the path to the *.lsp file
    '''

    if is_delta:
        lsp_path = os.path.join(run_dir,'%s.lsp' % water_year.lower()) 
    elif is_tracer:
        lsp_path = os.path.join(run_dir,'data_tracer','sfbay_dynamo000.lsp')
    elif 'FR' in runid & (not is_tracer):
        lsp_path = os.path.join(run_dir,'sfbay_dynamo000.lsp')
    elif 'G673' in runid:
        lsp_path = os.path.join(run_dir,'sfbay_dynamo000.lsp')
    elif 'G141' in runid:
        lsp_path = os.path.join(run_dir,'sfbay_dynamo000.lsp')
    else:
        raise Exception('runid %s does not fit expected pattern' % runid)
    return lsp_path

def get_balance_table_dir(run_dir):

	''' 
	balance_table_dir = get_balance_table_dir(run_dir)

	unless user says otherwise, put the balance tables in the run directory, in a subfolder called "Balance_Tables"
	'''

	balance_table_dir = os.path.join(run_dir,'Balance_Tables_V2')
	return balance_table_dir

def logger_cleanup():

    ''' check for open log files, close them, release handlers'''

    # clean up logging
    logger = logging.getLogger()
    handlers = list(logger.handlers)
    if len(handlers)>0:
        for handler in handlers:
            handler.close()
            logger.removeHandler(handler) 

######################
# main
######################

# get the paths to the shapefiles used in the model input
if poly_path is None or tran_path is None:
	poly_path, tran_path = get_shapefile_paths(model_input_dir, runid, is_delta)

# get the paths to the group and group connectivity definition files for the aggregated groups (used in step5_)
if group_def_path is None or group_con_path is None:
	group_def_path, group_con_path = get_group_def_path(runid)

# get the paths to the sediment concentration multipliers
sed_conc_mult_path = get_sed_conc_mult_path(runid)

# get the run directory
if run_dir is None:
	run_dir = get_run_dir(model_run_base_dir, runid, is_delta, is_tracer)

# get the path to the lsp file
if lsp_path is None:
	lsp_path = get_lsp_path(run_dir, is_delta, is_tracer)

# get the balance table directory
if balance_table_dir is None:
	balance_table_dir = get_balance_table_dir(run_dir)

# create the balance table directory if it does not exist
if not os.path.exists(balance_table_dir):
	print('Creating folder to store balance tables here:')
	print('    %s' % balance_table_dir)
	os.makedirs(balance_table_dir)
else: 
	print('Balance table folder already exists here:')
	print('    %s' % balance_table_dir)

# setup logging to file and to screen 
logger_cleanup()
logging.basicConfig(
level=logging.INFO,
format="%(asctime)s [%(levelname)s] %(message)s",
handlers=[
    logging.FileHandler(os.path.join(balance_table_dir,"log_step0.log"),'w'),
    logging.StreamHandler(sys.stdout)
])

# add some basic info to log file
user = os.getlogin()
hostname = socket.gethostname()
scriptname= __file__
conda_env=os.environ['CONDA_DEFAULT_ENV']
today= datetime.datetime.now().strftime('%b %d, %Y')
logging.info('Balance table configuration was specified on %s by %s on %s in %s using %s' % (today, user, hostname, conda_env, scriptname))

	
# print the values of all the parameters we are going to use to create the balance tables
logging.info('')
logging.info('Setting things up in step0_config.py ...')
logging.info('')
logging.info('  Processing the following run:')
logging.info('      step0_config.run_dir = %s' % run_dir)
logging.info('  Balance tables will be saved here:')
logging.info('      step0_config.balance_table_dir = %s' % balance_table_dir)
logging.info('  Delete any balance tables found in this directory before proceeding?')
logging.info('      step0_config.delete_balance_tables = %s' % delete_balance_tables)
logging.info('  Processing the following modeled substances:')
logging.info('      step0_config.substance_list = %s' % substance_list)
logging.info('  Assuming polygons and transects in the *.his and *-bal.his files are based on these shapefiles:')
logging.info('      step0_config.poly_path = %s' % poly_path)
logging.info('      step0_config.tran_path = %s' % tran_path)
logging.info('  Using the following group and connectivity definitions for aggregating in space:')
logging.info('      step0_config.group_def_path = %s' % group_def_path)
logging.info('      step0_config.group_con_path = %s' % group_con_path)
logging.info('  Using the following sediment concentration multiplier file:')
logging.info('      step0_config.sed_conc_mult_path = %s' % sed_conc_mult_path)
logging.info('  Using the *.lsp file here:')
logging.info('      step0_config.lsp_path = %s' % lsp_path)
logging.info('  Using the following precision in balance tables:')
logging.info('      step0_config.float_format = %s' % float_format)
logging.info('  Abort for mass conservation error?')
logging.info('      step0_config.abort_for_mass_cons_error = %s' % abort_for_mass_cons_error)
logging.info('  Tolerance for mass conservation error:')
logging.info('      step0_config.error_tol_percent = %f percent' % error_tol_percent)
logging.info('')
logger_cleanup()

