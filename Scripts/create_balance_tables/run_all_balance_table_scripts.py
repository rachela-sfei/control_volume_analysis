

# To create the balance tables, you can either run the scripts one at a time, or you can use this script to run them all at once.
# To specify the run you want to process, the directory where you want the balance table output, and other user input variables, 
# make changes to the step0_config.py script. The configuration variables specified in step0_config.py are imported by each of the 
# following modules
#
# created by Allie August 2022

import sys, importlib

def import_or_reload_module_by_string_name(module_name):

	''' This function looks complicated, but it does something very simple: it accepts a module name as a string,
	and if that module name is already imported, it will reload the module. If it is not already imported, it will 
	import it for the first time'''

	if module_name in sys.modules:
		importlib.reload(importlib.import_module(module_name))
	else:
		importlib.import_module(module_name)

import_or_reload_module_by_string_name('step0_config')
import_or_reload_module_by_string_name('step1_create_balance_tables')
import_or_reload_module_by_string_name('step2_create_balance_tables_for_composite_parameters')
import_or_reload_module_by_string_name('step3_group_reactions_for_composite_parameters')
import_or_reload_module_by_string_name('step4_check_mass_conservation')
import_or_reload_module_by_string_name('step5_compile_balance_tables_into_groups')
import_or_reload_module_by_string_name('step6_aggregate_in_time')