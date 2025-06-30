
import pandas as pd
import numpy as np 
import matplotlib.pylab as plt
from matplotlib.gridspec import GridSpec
import os, sys


base_dir = '/chicagovol2/hpcshared/open_bay/bgc/agg/WY2021/G141_21_098/Balance_Tables/'
 
table_list=[
 'oxy_Table.csv',
 'diat_Table.csv',
 'green_Table.csv',
 'diats1_Table.csv',
 'no3_Table.csv',
 'nh4_Table.csv',
 'don_Table.csv',
 'pon1_Table.csv',
 'pon2_Table.csv',
 'detns1_Table.csv',
 'detns2_Table.csv',
 'oons1_Table.csv',
 'oons2_Table.csv',
 'zoopl_Table.csv',
 'zoopl_e_Table.csv',
 'zoopl_r_Table.csv',
 'zoopl_v_Table.csv',
 'detcs1_Table.csv',
 'detcs2_Table.csv',
 'oocs1_Table.csv',
 'oocs2_Table.csv',
 'poc1_Table.csv',
 'poc2_Table.csv']

NC_ratios = {
 'Diat' : 0.150000,
 'Green' : 0.160000,
 'DiatS1' : 0.160000,
 'Zoopl_V' : 0.181800,
 'Zoopl_E' : 0.181800,
 'Zoopl_R' : 0.181800
 }

# load all the tables of stuff with N in it
df_diat = pd.read_csv(os.path.join(base_dir,'diat_Table.csv'))
df_green = pd.read_csv(os.path.join(base_dir,'green_Table.csv'))
df_diats1 = pd.read_csv(os.path.join(base_dir,'diats1_Table.csv'))
df_no3 = pd.read_csv(os.path.join(base_dir,'no3_Table.csv'))
df_nh4 = pd.read_csv(os.path.join(base_dir,'nh4_Table.csv'))
df_don = pd.read_csv(os.path.join(base_dir,'don_Table.csv'))
df_pon1 = pd.read_csv(os.path.join(base_dir,'pon1_Table.csv'))
df_pon2 = pd.read_csv(os.path.join(base_dir,'pon2_Table.csv'))
df_detns1 = pd.read_csv(os.path.join(base_dir,'detns1_Table.csv'))
df_detns2 = pd.read_csv(os.path.join(base_dir,'detns2_Table.csv'))
df_oons1 = pd.read_csv(os.path.join(base_dir,'oons1_Table.csv'))
df_oons2 = pd.read_csv(os.path.join(base_dir,'oons2_Table.csv'))

rx_diat = ['Diat,dZ_Diat', 'Diat,dSedDiat', 'Diat,dPPDiat', 'Diat,dMrtDiat', 'Diat,dcPPDiat']
rx_green = ['Green,dZ_Grn', 'Green,dSedGreen', 'Green,dPPGreen', 'Green,dMrtGreen', 'Green,dcPPGreen']
rx_diats1 = ['DiatS1,dPPDiatS1',
       'DiatS1,dMrtDiatS1', 'DiatS1,dResS1Diat', 'DiatS1,dBurS1Diat',
       'DiatS1,dSWBuS1Dia', 'DiatS1,dDigS1Diat']
rx_no3 = ['NO3,dDenitWat', 'NO3,dNitrif', 'NO3,dDenitSed', 'NO3,dNiDen', 'NO3,dNO3UptS1', 'NO3,dNO3Upt']
rx_nh4 = ['NH4,dMinPON1', 'NH4,dMinPON2', 'NH4,dMinDON', 'NH4,dNitrif', 
          'NH4,dMinDetNS1', 'NH4,dMinDetNS2', 'NH4,dMinOONS1', 'NH4,dMinOONS2', 
          'NH4,dZ_NRes', 'NH4,dNH4UptS1', 'NH4,dNH4US1D', 'NH4,dNH4Aut', 'NH4,dNH4AUTS1', 'NH4,dNH4Upt']
rx_don = ['DON,dCnvDPON1', 'DON,dCnvDPON2', 'DON,dMinDON']
rx_pon1 = ['PON1,dCnvPPON1', 'PON1,dCnvDPON1',
       'PON1,dMinPON1', 'PON1,dZ_NMrt', 'PON1,dZ_NDef', 'PON1,dZ_NSpDet',
       'PON1,dZ_PON1', 'PON1,dSedPON1', 'PON1,dMortDetN', 'PON1,dResS1DetN',
       'PON1,dResS2DetN', 'PON1,dResS1DiDN', 'PON1,dResS2DiDN']
rx_pon2 = ['PON2,dCnvPPON1', 'PON2,dCnvPPON2',
       'PON2,dCnvDPON2', 'PON2,dMinPON2', 'PON2,dSedPON2', 'PON2,dMortOON',
       'PON2,dResS1OON', 'PON2,dResS2OON']
rx_detns1 = ['DetNS1,dMinDetNS1',
       'DetNS1,dSWMinDNS1', 'DetNS1,dZ_NMrtS1', 'DetNS1,dZ_DNS1',
       'DetNS1,dSedAlgN', 'DetNS1,dSedPON1', 'DetNS1,dMrtDetNS1',
       'DetNS1,dResS1DetN', 'DetNS1,dBurS1DetN', 'DetNS1,dSWBuS1DtN',
       'DetNS1,dDigS1DetN']
rx_detns2 = ['DetNS2,dMinDetNS2',
       'DetNS2,dSWMinDNS2', 'DetNS2,dResS2DetN', 'DetNS2,dBurS1DetN',
       'DetNS2,dBurS2DetN', 'DetNS2,dDigS1DetN', 'DetNS2,dDigS2DetN']
rx_oons1 = ['OONS1,dMinOONS1',
       'OONS1,dSWMnOONS1', 'OONS1,dSedPON2', 'OONS1,dMrtOONS1',
       'OONS1,dResS1OON', 'OONS1,dBurS1OON', 'OONS1,dSWBuS1OON',
       'OONS1,dDigS1OON']
rx_oons2 = ['OONS2,dMinOONS2',
       'OONS2,dSWMnOONS2', 'OONS2,dResS2OON', 'OONS2,dBurS1OON',
       'OONS2,dBurS2OON', 'OONS2,dDigS1OON', 'OONS2,dDigS2OON']

ind = df_diat['Control Volume'] == 'polygon55'

df_diat=df_diat.loc[ind]
df_green=df_green.loc[ind]
df_diats1=df_diats1.loc[ind]
df_no3=df_no3.loc[ind]
df_nh4=df_nh4.loc[ind]
df_don=df_don.loc[ind]
df_pon1=df_pon1.loc[ind]
df_pon2=df_pon2.loc[ind]
df_detns1=df_detns1.loc[ind]
df_detns2=df_detns2.loc[ind]
df_oons1=df_oons1.loc[ind]
df_oons2=df_oons2.loc[ind]

time = df_diat['time'].astype('datetime64[ns]').values

#params["Z_PrDet"] = PC(1.0)                  # ZP preference for DetC or POC1 - default = 0.0
#params["FrAutDiatS"] = PC(0.15)    # fraction autolysis Diatoms in the sediment  default = 0.0 - this is dissolved nurtients released to WC
#params["FrDetDiatS"] = PC(0.7)     # fraction to detritus Diatoms in the sediment  default = 1.0 - this is dissolved nurtients released to WC; 
# FrDetDiatOO = 1 - FrAutDiatS - FrDetDiatS (not an input parameter but calculated internally)
FrAutDiatS = 0.15
FrDetDiatS = 0.7
FrDetDiatOO = 1 - FrAutDiatS - FrDetDiatS


fig=plt.figure(figsize=(11,3.5))
gs = GridSpec(1, 2, width_ratios=[2, 1])
ax1 = fig.add_subplot(gs[0])
ax2 = fig.add_subplot(gs[1])

ax1.plot(time, df_diats1['DiatS1,dMrtDiatS1'],label='DiatS1,dMrtDiatS1') 
ax1.plot(time, df_nh4['NH4,dNH4AUTS1'],label='NH4,dNH4AUTS1')
ax1.plot(time, df_detns1['DetNS1,dMrtDetNS1'],label='DetNS1,dMrtDetNS1')
ax1.plot(time, df_oons1['OONS1,dMrtOONS1'],'--',label='OONS1,dMrtOONS1')
ax1.legend()
ax1.set_ylabel('reaction rate (Mg/d)')
ax1.set_title('Polygon 55')

x = -df_diats1['DiatS1,dMrtDiatS1']
y = df_detns1['DetNS1,dMrtDetNS1']+df_nh4['NH4,dNH4AUTS1']+df_oons1['OONS1,dMrtOONS1']
p = np.polyfit(x,y,1)
ax2.plot(x, y, '.')
xlim = ax2.get_xlim()
ax2.plot(xlim, p[0]*np.array(xlim)+p[1], label='y = %0.3f x + %0.3f' % (p[0],p[1]))
ax2.set_xlabel('DiatS1,dMrtDiatS1')
ax2.set_ylabel('NH4,dNH4AUTS1 + DetNS1,dMrtDetNS1 + OONS1,dMrtOONS1')
ax2.legend()
fig.savefig('Where_Does_DiatS1_Mort_Go.png')

# DiatS1,dMrtDiatS1 + DetNS1,dMrtDetNS1 + NH4,dNH4AUTS1 + OONS1,dMrtOONS1
# PON2,dMortOON + OONS1,dMrtOONS1

# These are not zero:
# 
# NH4,dZ_NRes + PON1,dZ_NDef + PON1,dZ_NSpDet + Diat,dZ_Diat + Green,dZ_Grn + Zoopl_V,dZ_Vgr + # Zoopl_R,dZ_SpwDet + Zoopl_R,dZ_Rgr + Zoopl_E,dZ_Ea + Zoopl_E,dZ_Ec
# 
# PON1,dZ_PON1 + PON1,dZ_NMrt + PON1,dM_NMrt + PON1,dG4_NMrt + PON1,dM_NSpDet + PON1,dG4_NSpDet + # Zoopl_V,dZ_Vmor + Zoopl_R,dZ_Rmor + Zoopl_E,dZ_Emor
# 
# DiatS1,dMrtDiatS1 + DetNS1,dMrtDetNS1 + NH4,dNH4AUTS1
# 
# NH4,dZ_NRes + PON1,dZ_NDef + PON1,dZ_NSpDet + Diat,dZ_Diat + Green,dZ_Grn + Zoopl_V,dZ_Vgr + # Zoopl_R,dZ_SpwDet + Zoopl_R,dZ_Rgr + Zoopl_E,dZ_Ea + Zoopl_E,dZ_Ec 
# 
# PON2,dMortOON + OONS1,dMrtOONS1
# 
# PON1,dZ_PON1 + PON1,dZ_NMrt + PON1,dM_NMrt + PON1,dG4_NMrt + PON1,dM_NSpDet + PON1,dG4_NSpDet + # Zoopl_V,dZ_Vmor + Zoopl_R,dZ_Rmor + Zoopl_E,dZ_Emor
# 
# Not sure if these are nonzero or if they're just getting normalized by something that's e
# 
# OONS1,dSWMnOONS1 + OONS1,dMrtOONS1 + OONS1,dResS1OON + OONS1,dSWBuS1OON 
# inf percent of OONS1,dSedPON2
# this really is nonzero
# 
# OONS1,dSWMnOONS1 + OONS1,dMrtOONS1 + OONS1,dResS1OON + OONS1,dSWBuS1OON
# inf percent of DetNS1,dSedPON1
# this is really nonzero