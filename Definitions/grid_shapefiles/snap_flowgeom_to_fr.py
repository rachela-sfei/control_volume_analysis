import geopandas as gpd
import matplotlib.pylab as plt


gdf_fr = gpd.read_file('open_bay_model_grid_FR_v24.shp')
gdf_ag = gpd.read_file('flowgeom_v24.shp')

gdf_fr['aggpoly'] = 0

for iag in range(len(gdf_ag)):

	poly = gdf_ag.iloc[iag]['geometry']

	ind = gdf_fr.centroid.within(poly)

	gdf_fr.loc[ind,'aggpoly'] = iag

gdf_ag_snapped = gdf_fr.dissolve(by='aggpoly')

gdf_ag_snapped.to_file('flowgeom_v24-SNAPPED2FR.shp')

