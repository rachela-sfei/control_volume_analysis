import os, sys
import pandas as pd
import numpy as np
import matplotlib.pylab as plt

fn_list = [
'/fortcollinsvol1/hpcshared/open_bay/bgc/full_res/WY2022/FR22_046/Balance_Tables/din_Table_By_Group.csv',
'/fortcollinsvol1/hpcshared/open_bay/bgc/full_res/WY2022/FR22_033/Balance_Tables/din_Table_By_Group.csv',
'/fortcollinsvol1/hpcshared/open_bay/bgc/full_res/WY2022/FR22_034/Balance_Tables/din_Table_By_Group.csv',
'/fortcollinsvol1/hpcshared/open_bay/bgc/full_res/WY2022/FR22_035/Balance_Tables/din_Table_By_Group.csv',
'/fortcollinsvol1/hpcshared/open_bay/bgc/full_res/WY2022/FR22_036/Balance_Tables/din_Table_By_Group.csv',
'/fortcollinsvol1/hpcshared/open_bay/bgc/full_res/WY2022/FR22_037/Balance_Tables/din_Table_By_Group.csv']

runid_list = ['FR22_046','FR22_033','FR22_034','FR22_035','FR22_036','FR22_037']
label_list = ['Base Case','BACWA annual','45% annual','50% annual','55% annual','60% annual']


df_out = pd.DataFrame(index=range(len(fn_list)))
df_out['runid'] = runid_list
df_out['scenario'] = label_list


for group in ['LSB', 'SB_WB', 'Central_Bay_WB','San_Pablo_Bay','Suisun_Bay', 'Whole_Bay']:

	for i, fn in enumerate(fn_list):

		df = pd.read_csv(fn)
		ind = df['group'] == group
		df = df.loc[ind]
		df['time'] = df['time'].astype('datetime64[ns]')
		ind = np.logical_and(df['time']>=np.datetime64('2022-07-01'),
 			                 df['time']< np.datetime64('2022-08-01'))
		df = df.loc[ind]
	
		df_out.loc[i,'%s DIN,Net Load (Mg/d)' % group] = df['DIN,Net Load (Mg/d)'].mean()
		df_out.loc[i,'%s NH4,dMinOONS12 (Mg/d)' % group] = df['NH4,dMinOONS12 (Mg/d)'].mean()

	df_out['%s dMinOONS12 / Net Load' % group] = df_out['%s NH4,dMinOONS12 (Mg/d)' % group]/df_out['%s DIN,Net Load (Mg/d)' % group]

df_out.to_csv('subembayment_POTW_OONS_4permit.csv')
