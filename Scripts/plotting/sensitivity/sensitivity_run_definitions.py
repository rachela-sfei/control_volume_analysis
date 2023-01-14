# -*- coding: utf-8 -*-
"""
Created on Mon Mar 28 11:45:03 2022

@author: siennaw
"""

# Dict : run label followed by RunID 


server_dict = {
    'G141_13to18_246' : 'richmond',
    'G141_13to18_254' : 'fortcollins',
    'G141_13to18_255' : 'fortcollins',
    'G141_13to18_256' : 'fortcollins',
    'G141_13to18_257' : 'fortcollins',
    'G141_13to18_258' : 'fortcollins',
    'G141_13to18_259' : 'fortcollins',
    'G141_13to18_260' : 'boise',
    'G141_13to18_261' : 'boise',
    'G141_13to18_262' : 'boise',
    'G141_13to18_263' : 'boise',
    'G141_13to18_264' : 'boise',
    'G141_13to18_265' : 'boise',
    'G141_13to18_266' : 'boise',
    'G141_13to18_267' : 'boise',
    'G141_13to18_268' : 'boise',
}

param2run = {} 


#%% (1) 'Diat Growth Rate'

runs2plot = { 'Base (#246)'         : 'G141_13to18_246',
              '-25% (#255)'         : 'G141_13to18_255',
              '+25% (#254)'        :  'G141_13to18_254'}  
param2run['Diat Growth Rate'] = runs2plot

#%% (2) Light Extinction Coefficient
runs2plot = {'Base (#246)'         : 'G141_13to18_246',
             '-50% (#256)'         : 'G141_13to18_256',
             '+50% (#257)'         : 'G141_13to18_257'}
param2run['Light Extinction Coefficient'] = runs2plot

#%% (3) ' Zero growth rates'
runs2plot = {
              'Base (#246)'         :           'G141_13to18_246',
              '-Shoal growth=0 (#259)'        : 'G141_13to18_259',
              '+Channel growth=0 (#258)'      : 'G141_13to18_258'}  

param2run['Zero growth rates'] = runs2plot

#%% (4) 'Zoop Ingestion Rate'

runs2plot = {'Base (#246)'         :  'G141_13to18_246',
              '-25% (#261)'         : 'G141_13to18_261',
              '+25% (#260)'         : 'G141_13to18_260'} 
param2run['Zoop Ingestion Rate'] = runs2plot

#%% (5) 'Include Clams' -- add + and - to this one, this is dumb, so it works with the regular script

runs2plot = {'Base (#246)'         :            'G141_13to18_246',
              '-Include Clams (#262)'         : 'G141_13to18_262',
              '+Include Clams (#262)'         : 'G141_13to18_262'} 
param2run['Include Clams'] = runs2plot

#%% (6) 'Sediment Initial Condition'

runs2plot = {
              'Base (#246)'         : 'G141_13to18_246',
              '-50% (#262)'         : 'G141_13to18_262',
              '+50% (#263)'        :  'G141_13to18_263'}  

param2run['Sediment Initial Conc C/N/P/Si'] = runs2plot


#%% (7) 'Diagenesis rate of fresh material'

runs2plot = {'Base (#246)'         : 'G141_13to18_246',
              '-50% (#266)'        : 'G141_13to18_266',
              '+50% (#265)'        : 'G141_13to18_265'}  

param2run['Diagenesis Rates for Fresh Sediment'] = runs2plot


#%% (8) 'Diagenesis rate of legacy material'

runs2plot = {'Base (#246)'         : 'G141_13to18_246',
              '-50% (#268)'        : 'G141_13to18_268',
              '+50% (#267)'        : 'G141_13to18_267'}  

param2run['Diagenesis Rates for Legacy Sediment'] = runs2plot


print('Available sensitivity runs are:')
print(list(param2run.keys()))




# Dict : run label followed by RunID 
# ///////////////////////////////
# runs2plot = {'Lower (50%)'         : 'G141_13to18_129',
#               'Base (#246)'         : 'G141_13to18_246',
#               'Higher (50%)'         : 'G141_13to18_128',
#               } 

# PARAM_SENS = 'Light Extinction Coefficient'
# ///////////////////////////////

# # ///////////////////////////////
# runs2plot = {'Base (#246)'         : 'G141_13to18_246',
#              'Higher (25%)'         : 'G141_13to18_126',
#              'Lower (25%)'         : 'G141_13to18_127'} 

# PARAM_SENS = 'Diat Growth Rate'
# base_run = 'Base (#246)'
# # ///////////////////////////////


# ///////////////////////////////
# Dict : run label followed by RunID 
# runs2plot = {'Lower (25%)'         : 'G141_13to18_131',
#               'Base (#246)'         : 'G141_13to18_246',
#               'Higher (25%)'        : 'G141_13to18_130'} 

# PARAM_SENS = 'Zoop Ingestion Rate'
# base_run = 'Base (#246)'
# ///////////////////////////////


# /////////////////////////////// 
# Dict : run label followed by RunID 
# runs2plot = {'Lower (50%)'         : 'G141_13to18_144',
#               'Base (#246)'         : 'G141_13to18_246',
#               'Higher (50%)'        : 'G141_13to18_143'} 

# PARAM_SENS = 'Diagenesis rate in Layers 1,2'
# base_run = 'Base (#246)'
# ///////////////////////////////


