#/chicagovol1/hpcshared/open_bay/bgc/figures


#/richmondvol1/hpcshared/Grid141/WY13to18/G141_13to18_140
#/richmondvol1/hpcshared/Grid141/WY2013/G141_13_016
#/richmondvol1/hpcshared/Full_res/WY2013/FR13_025


import numpy as np
import os
import matplotlib
matplotlib.rcParams.update(matplotlib.rcParamsDefault)

def make_concise_runid_list_string(runid_list):

	'''Given a list of run IDs for an NMS open bay biogeochemical model run, 
	returns a concise string listing all the run IDs, intended for naming postprocessing
	figures and the directories where we will store them. Aggregated runs are listed
	before full resolution runs, multiple water year runs come before single water year
	runs, and othewise runs are sorted by year and by run number. We replace the aggregated
	grid run prefix "G141_" with "AGG" to make the string a bit easier to read

	Usage:

		concise_runid_list_string = make_concise_runid_list_string(runid_list)

	An example valid runid_list is 

		['FR18_006', 'G141_17_017','G141_13to18_207','G141_13to18_50','G141_13_016', 'G141_13_017','FR13_025','G141_13to18_50']

	and the value of concise_runid_list_string returned for this runid_list would be

	 	'AGG13to18_197_207_AGG13_016_017_AGG17_017_FR13_025_FR18_006'
	
	'''

	# replace 'G141_' with 'AGG' in runid's
	runid_list_copy = runid_list.copy()
	for i,runid in enumerate(runid_list):
		runid_list_copy[i] = runid.replace('G141_','AGG')
	
	# come up with a corresponding list of just the run prefixes and just the run numbers
	run_pref_list = []
	run_numb_list = []
	for runid in runid_list_copy:
		run_pref_list.append(runid.split('_')[0])
		run_numb_list.append(runid.split('_')[1])
	
	# come up with a sorted list of unique run prefixes (such as AGG13to18, AGG17, FR17) for the AGG and FR runs separately
	run_pref_unique_AGG = []
	run_pref_unique_FR = []
	for runid in runid_list_copy:
		if 'AGG' in runid:
			run_pref_unique_AGG.append(runid.split('_')[0])
		else:
			run_pref_unique_FR.append(runid.split('_')[0])
	run_pref_unique_AGG = np.sort(np.unique(run_pref_unique_AGG))
	run_pref_unique_FR = np.sort(np.unique(run_pref_unique_FR))
	
	# move any runs with 'to' in the runid up to the front (so multi year runs come before single year runs)
	def move_to_up(run_pref_unique):
		i_move = []
		i_stay = []
		for i in range(len(run_pref_unique)):
			if 'to' in run_pref_unique[i]:
				i_move.append(i)
			else:
				i_stay.append(i)
		run_pref_unique = np.concatenate((run_pref_unique[i_move], run_pref_unique[i_stay]))
		return run_pref_unique
	run_pref_unique_AGG = move_to_up(run_pref_unique_AGG)
	run_pref_unique_FR = move_to_up(run_pref_unique_FR)
	
	# concatenate FR and AGG runs to make one list of unique runid prefixes
	run_pref_unique = np.concatenate((run_pref_unique_AGG, run_pref_unique_FR))
	
	# now loop through the sorted unique run prefixes, find all the runs with that prefix, get the corresponding run numbers,
	# sort the run numbers (sort as integers but retain string format), and append to the folder name, thus creating the concise 
	#string listing the run IDs
	concise_runid_list_string = ''
	for run_pref in run_pref_unique:
		concise_runid_list_string = concise_runid_list_string + run_pref + '_'
		i_list = np.where(run_pref==np.array(run_pref_list))[0]
		run_numb_subset = np.unique(np.array(run_numb_list)[i_list])
		run_numb_subset = [x for _, x in sorted(zip(run_numb_subset.astype(int), run_numb_subset))] # this sorts run number strings using corresponding integers
		for run_numb in run_numb_subset:
			concise_runid_list_string = concise_runid_list_string + run_numb + '_'
	concise_runid_list_string = concise_runid_list_string[0:-1]
	
	return concise_runid_list_string

def list_of_wy_str_2_list_of_int_wys(wystr_list):

	''' given a list of strings describing water years (e.g. ['WY2013', 'WY13to18'])
	compute the list of all integer water years included'''

	wy_list = []
	for wystr in wystr_list:
		if 'to' in wystr:
			wy0 = 2000 + int(wystr[2:4])
			wyN = 2000 + int(wystr[6:])
			for wy in range(wy0,wyN+1):
				wy_list.append(wy)
		else:
			wy = int(wystr[2:])
			wy_list.append(wy)
	wy_list = np.sort(np.unique(wy_list))
	wy_list = list(wy_list)

	return wy_list

def make_concise_water_year_list_string(wy_list):

	''' given a list of integer water years (e.g. [2013, 2018]) makes a string
	listing all the years concisely'''

	# get sorted list of unique water years
	wy_list_sorted = np.sort(np.unique(wy_list))
	wy_min = wy_list_sorted[0]
	wy_max = wy_list_sorted[-1]

	# check if water years are consecutive, and if so, output a string with format like 
	# WY13to18 where here 13 means 2013
	if len(wy_list_sorted)>1 and list(np.arange(wy_min,wy_max+1))==list(wy_list_sorted):
		concise_water_year_list_string = 'WY%dto%d' % (wy_min-2000, wy_max-2000)
	
	# otherwise make a string with format like WY13+17+18
	else:
		concise_water_year_list_string = 'WY'
		for wy in wy_list_sorted:
			concise_water_year_list_string = concise_water_year_list_string + '%d+' % (wy-2000)
		concise_water_year_list_string = concise_water_year_list_string[0:-1]

	return concise_water_year_list_string

def get_water_year(runid):

	'''
	water_year = get_water_year(runid)

	given the runid, get the string for the water year folder the run is stored in on richmond
	'''

	if 'FR' in runid:
	    # this extracts the 2 digit water year, assuming format of runid is like FR13_003 for WY2013 run 003
	    yr = int(runid.split('_')[0][2:])
	    # turn into water year string
	    water_year = 'WY%d' % (2000 + yr)
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

def get_run_dir(run_base_dir, runid):

	'''
	run_dir = get_run_dir(run_base_dir, runid)

	given the base directory and runid, return the full path to the model run folder on richmond
	'''

	if 'richmond' in run_base_dir:
		if 'FR' in runid:
			water_year = get_water_year(runid)
			run_dir = os.path.join(run_base_dir,'Full_res',water_year,runid)
		elif 'G141' in runid:
			water_year = get_water_year(runid)
			run_dir = os.path.join(run_base_dir,'Grid141',water_year,runid)
		else:
			raise Exception('runid %s does not fit expected pattern' % runid)
	else:
		if 'FR' in runid:
			water_year = get_water_year(runid)
			run_dir = os.path.join(run_base_dir,'open_bay','bgc','full_res',water_year,runid)
		elif 'G141' in runid:
			water_year = get_water_year(runid)
			run_dir = os.path.join(run_base_dir,'open_bay','bgc','agg',water_year,runid)
		else:
			raise Exception('runid %s does not fit expected pattern' % runid)


	return run_dir