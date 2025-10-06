Various plotting scripts that use *.csv files created by the create_balance_table scripts as input

In the following I give the paths to folders with examples of figures each script makes:

=====================================================

These scripts are used to generate a set of PDFs with figures intended to use routinely for model validation. Unlike the rest of the scripts, which save in a special folder on richmondvol1 under a list of runid's, these validaiton scripts save in the run folder:

plot_multigroup_reaction_stacks_plus_4validation.py 
/chicagovol2/hpcshared/open_bay/bgc/full_res/WY2021/FR21_007/

plot_coastal_export_4validation.py  
/chicagovol2/hpcshared/open_bay/bgc/full_res/WY2021/FR21_007/               

=====================================================

These scripts work on a single run:

plot_polygon_level_masscons.py           
/richmondvol1/hpcshared/open_bay/bgc/figures/FR21_007/polygon_level_masscons/

plot_multigroup_reaction_stacks.py   
/richmondvol1/hpcshared/open_bay/bgc/figures/FR21_007/multigroup_reaction_stacks/

plot_mass_balance_maps.py   
For this script time stamps are messed up because of the seasonal average issue. Also I'm not sure why there is nonzero transport for detritus...
/richmondvol1/hpcshared/open_bay/bgc/figures/FR21_007/mass_balance_maps/                           

===================================================

These scripts compare different runs:

plot_aug2020_3panel.py  
/richmondvol1/hpcshared/open_bay/bgc/figures/FR21_007_008_009/aug2020_3panel/

plot_coastal_export_stack.py 
/richmondvol1/hpcshared/open_bay/bgc/figures/FR21_007_008_009/coastal_export/ 

plot_subembayment_stack.py  
/richmondvol1/hpcshared/open_bay/bgc/figures/FR21_007_008_009/subembayment_stack/

plot_subembayment_stacks_4paper.py
/richmondvol1/hpcshared/open_bay/bgc/figures/FR21_007_008_009/subembayment_stacks_4paper/

plot_multigroup_concentrations_multirun.py           
/richmondvol1/hpcshared/open_bay/bgc/figures/FR21_007_008_009/multigroup_concentrations/

plot_multigroup_reaction_stacks_multirun.py    
/richmondvol1/hpcshared/open_bay/bgc/figures/FR21_007_008_009/reaction_stacks_multigroup_multirun/          

plot_rate_maps.py                                    
/richmondvol1/hpcshared/open_bay/bgc/figures/FR21_007_008_009/rate_maps/
Do not believe any figures labeled "_Time0000" because the simulation does not include Oct,Nov,Dec, and don't believe the plots for FR21_009 labeled "_Time0003" because this run terminated early. Need to fix the create_balance_tables scripts to better handle runs that start later than Oct 1
                        
==================================================================================

These scripts rely on seasonal averages, which currently do not work for simulations that don't span the whole water year. So I made some examples using earlier simulations:

plot_subembayment_arrows.py
/richmondvol1/hpcshared/open_bay/bgc/figures/FR13_028_FR14_001_FR15_001_FR16_001_FR17_021_FR18_009/subembayment_arrows

plot_subembayment_mass_bal_bars.py
/richmondvol1/hpcshared/open_bay/bgc/figures/FR13_028_FR14_001_FR15_001_FR16_001_FR17_021_FR18_009/subembayment_mass_bal_bars

plot_subembayment_reaction_bars.py
/richmondvol1/hpcshared/open_bay/bgc/figures/FR13_028_FR14_001_FR15_001_FR16_001_FR17_021_FR18_009/subembayment_reaction_bars

plot_subembayment_mass_bal_and_rx_bars.py
/richmondvol1/hpcshared/open_bay/bgc/figures/FR13_028_FR14_001_FR15_001_FR16_001_FR17_021_FR18_009/subembayment_mass_bal_and_rx_bars

==================================================================================

These scripts relied on an estimate of tidal dispersion (mathematically it is diffusion) based on the overly diffusive scheme 16 -- it is proportional to 0.12 times the square root of the variance of volume flux over the tidal cycle. The scripts do not work with the current version of the create_balance_table scripts. We may want to recussivate the mean circulation figures though:

make_flux_maps_all_types.py 
Here's an example of the figures -- note there are several types and only the mean flux is valid:
/richmondvol1/hpcshared/open_bay/bgc/figures/FR13_028/circulation_maps/

plot_exchanges_at_polygon_level_for_residence_time.py  
/richmondvol1/hpcshared/open_bay/bgc/figures/FR13_028/fluxes_for_restime/

plot_residual_circulation.py                         
/richmondvol1/hpcshared/open_bay/bgc/figures/FR13_028/residual_circulation/

===========================================
        
A special script used for 2022 based permit work:
compare_loading_4permit.py   