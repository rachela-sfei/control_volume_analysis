'''

Don't worry about this script, it is just an old script I used to test different
interpolation methods for inferring the flux vectors in the residual circulation plots...
keeping it here just in case it becomes useful again

A brief look at this, seems the some of the file paths are not correct, so if you need to 
run it, you'll need to update those

Allie King Sept 2022

'''

### PACKAGES

import xarray as xr
import matplotlib.pyplot as plt
import numpy as np
import geopandas as gpd
import matplotlib.animation as manimation
import os,sys
import pandas as pd
import matplotlib as mpl
from scipy.interpolate import griddata
from shapely.geometry import Point
import matplotlib.pyplot as plt 

### FUNCTIONS
    
def Poly2Transect(left,right,pi='all'):
    # find the transects for each polygon and the signs based on the following
    # rule: transects with their 'from' segment left of the path are positive
    # otherwise negated; so left polygons are given a negative sign
    def p2t_i(i):
        indl = np.where(left==i)[0]
        indr = np.where(right==i)[0]
        signl = np.ones_like(indl)*-1
        signr = np.ones_like(indr)
        return {'transect':np.concatenate([indl,indr]),
                 'sign':np.concatenate([signl,signr])}
    if pi=='all':
        p2t = []
        for i in np.arange(pmax):
            p2t.append(p2t_i(i))
    elif isinstance(pi,int):
        p2t = p2t_i(pi)
    else:
        raise ValueError("The type of pi is not implemented")      
    return p2t

#################    
### USER INPUT
#################

# path to DWAQ run, hist file, and hist_bal file
path =  '../dwaq2019061300/'
histfn = os.path.join(path,'dwaq_hist.nc')
histbal_fn = os.path.join(path,'dwaq_hist_bal.nc') 

# path to shape functions defining control volumes and transects for DWAQ output
shpfn = '../../Definitions/model_input_shapefiles/Agg_exchange_lines.shp'
shpfn_poly = '../Definitions/model_input_shapefiles/Agg_mod_contiguous.shp'

# names of variables to sum (in this case to get DIN)
varname1 = 'no3'
varname2 = 'nh4'

# set a maximum radius defining the neighborhood for interpolating
# fluxes across transects to find flux vectors and also define power
# for inverse distance weithging
dmax = 6000.

# set max number of points to use in least squares approximation
Nmax = 4

# set maximum flux for coloring streamlines
qmax = 50

# define extent of South Bay 
x_SB = [551000.,595000.]
y_SB = [4138000.,4182000.]

# regular grid spanning South Bay
x = np.arange(553000.,593000.,1000.)
y = np.arange(4138000.,4183000.,1000.)
xg, yg = np.meshgrid(x,y)

# set scale of quiver lengths as multiple of half the x-unit scale
quiver_scale_SB = 125./10000.

###################
### MAIN PROGRAM
###################

# load data from hist and hist_bal files
hdata = xr.open_dataset(histfn)
hbdata = xr.open_dataset(histbal_fn) # history balance file
TransectBL = ['transect' in name for name in hdata.location_names.values[0]]
indT = np.where(TransectBL)[0] # find all transects from the output hist file
PolygonBL = ['polygon' in name for name in hdata.location_names.values[0]]
indP = np.where(PolygonBL)[0] # find all polygons from the output hist file
Vp = hdata.isel(nSegment=indP)['volume']
PolygonBL_bal = ['polygon' in name for name in hbdata.region.values]
indP_bal = np.where(PolygonBL_bal)[0] # find all polygons from the output hist blanace file
varT = hdata.isel(nSegment=indT)[varname1] + hdata.isel(nSegment=indT)[varname2]
varP = hdata.isel(nSegment=indP)[varname1] + hdata.isel(nSegment=indP)[varname2]

# times and unique dates
time = np.array([pd.to_datetime(t) for t in hdata.time.data])
dates = np.unique(np.array([t.date() for t in time]))

# take averages over the water year, which begins on october 1
ind = time>=pd.Timestamp('2012-10-01 00:00:00')
varT = varT.values[ind,:].mean(axis=0)
varP = varP.values[ind,:].mean(axis=0) 

# continue computing stuff
varPV = varP*Vp
fieldBL = [varname1.lower()+',' in name.lower() for name in hbdata.field.values]
indF = np.where(fieldBL)[0]
varP_bal = hbdata.isel(region=indP_bal).isel(field=indF)

# read control volume exchange lines and find control volume polygons to left and right
gdf = gpd.read_file(shpfn)
left = gdf.left
right = gdf.right
pmax = max(left.max(),right.max()) +1 # total number of polygons and they are zero-based

# map from polygons to transect -- not sure what this does           
p2t = Poly2Transect(left,right)    

# read control volume polygons from shapefile
poly_df = gpd.read_file(shpfn_poly)

# merge polygons into a single polygon representing the whole bay and
# extract the polygon from the geopandas dataframe as a shapely polygon
poly_allbay_gdf = poly_df.copy(deep=True)
poly_allbay_gdf['dummy']=1
poly_allbay_gdf = poly_allbay_gdf.dissolve(by='dummy')
poly_allbay = poly_allbay_gdf.iloc[0].geometry

# find centroids of the transects dividing the polygons
xe = gdf.geometry.centroid.x.values
ye = gdf.geometry.centroid.y.values

# find centroids of the polygons
poly_x = poly_df.geometry.centroid.x.values
poly_y = poly_df.geometry.centroid.y.values

# find centroid of the polygon to the right of each edge
xright = poly_x[gdf.right.values]   
yright = poly_y[gdf.right.values]

# length of the line between the centroid of the edge and the centroid of the polygon to the right
line_length = np.sqrt( (xe-xright)**2 + (ye-yright)**2 )

# this gives the lengths of the edges/transects/exchange lines
edge_length = gdf.geometry.length.values 

# rename variables for consistency with code that loops over times
Tmap = varP
TmapV = varPV
varTmean = varT   

# compute vector components of flux normal to each transect, 
# normalizing the flux by edge length to get flux per unit length
# (actually direction is not normal to the transect but points from one
# polygon centroid to the other polygon centroid)
qx =  (xright-xe)/line_length*varTmean/edge_length
qy =  (yright-ye)/line_length*varTmean/edge_length

# find the unit normal in the direction of the fluxes across the transects
nx = qx/np.sqrt(qx**2 + qy**2)
ny = qy/np.sqrt(qx**2 + qy**2)

# filter out the fluxes across transects that are less than 800m long
ind = edge_length > 800.
nx1 = nx[ind]
ny1 = ny[ind]
xe1 = xe[ind]
ye1 = ye[ind]
qx1 = qx[ind]
qy1 = qy[ind]

# initialize flux vectors as nan at polygon centroids
# ... unweighted least square solution using 4 closest points
qxc = np.nan*np.ones(np.shape(poly_x))
qyc = np.nan*np.ones(np.shape(poly_x))
# ... inverse distance weighted
qxc_d = np.nan*np.ones(np.shape(poly_x))
qyc_d = np.nan*np.ones(np.shape(poly_x))
# ... inverse distance square weighted
qxc_d2 = np.nan*np.ones(np.shape(poly_x))
qyc_d2 = np.nan*np.ones(np.shape(poly_x))
# ... inverse distance cubed weighted
qxc_d3 = np.nan*np.ones(np.shape(poly_x))
qyc_d3 = np.nan*np.ones(np.shape(poly_x))
# ...  on regular grid
qxg = np.nan*np.ones(np.shape(xg))
qyg = np.nan*np.ones(np.shape(yg))

                   
# loop through the polygon centroids, evaluating flux vectors, using just the 5 closest 
# points -- using different weighting methods
for i in range(len(poly_x)):
        
        ## pick out coordinates on grid
        xc1 = poly_x[i]
        yc1 = poly_y[i]
        
        # check if point is inside the bay, and if it is, proceed with 
        # interpolation step
        if Point(xc1,yc1).within(poly_allbay):
        
            # find the distances between this grid point and points where fluxes
            # are defined
            d = np.sqrt((xe1-xc1)**2 + (ye1-yc1)**2)
            
            #############################################################
            # solve unweighted least square problem using only 4 closet
            # points in the neighborhood
            #############################################################
            
            # select points where d is less that 6000m 
            indn = d <= dmax
            d2 = d[indn]
            nx2 = nx1[indn]
            ny2 = ny1[indn]
            xe2 = xe1[indn]
            ye2 = ye1[indn]
            qx2 = qx1[indn]
            qy2 = qy1[indn]
            N = len(nx2)
            
            # use only the Nmax closest points
            if N > Nmax:
                indn = np.argsort(d2)
                indn = indn[0:Nmax]
                N = Nmax
                d2 = d2[indn]
                nx2 = nx2[indn]
                ny2 = ny2[indn]
                xe2 = xe2[indn]
                ye2 = ye2[indn]
                qx2 = qx2[indn]
                qy2 = qy2[indn]
            
            # only possible to solve matrix equation if have at least 3 points
            if N>=3:
                A = np.zeros((N,2))
                A[:,0] = nx2
                A[:,1] = ny2
                b = np.zeros(N)
                b[:] = np.sqrt(qx2**2 + qy2**2)
                W = np.zeros((N,N))
                for n in range(N):
                    W[n,n] = 1
                xhat = np.matmul(np.linalg.inv(np.matmul(np.transpose(A),np.matmul(W,A) )),
                              np.matmul(np.transpose(A),np.matmul(W,b))) 
                qxc[i] = xhat[0]
                qyc[i] = xhat[1]
           
            #############################################################
            # solve least square problem using all points in 6000m radius
            # and using inverse distance weighting
            #############################################################
            
            # select points where d is less that 6000m 
            indn = d <= dmax
            d2 = d[indn]
            nx2 = nx1[indn]
            ny2 = ny1[indn]
            xe2 = xe1[indn]
            ye2 = ye1[indn]
            qx2 = qx1[indn]
            qy2 = qy1[indn]
            N = len(nx2)
            
            # use only the Nmax closest points
            if N > Nmax:
                indn = np.argsort(d2)
                indn = indn[0:Nmax]
                N = Nmax
                d2 = d2[indn]
                nx2 = nx2[indn]
                ny2 = ny2[indn]
                xe2 = xe2[indn]
                ye2 = ye2[indn]
                qx2 = qx2[indn]
                qy2 = qy2[indn]
            
            # only solve matrix equation if have at least 4 points
            if N>=3:
                A = np.zeros((N,2))
                A[:,0] = nx2
                A[:,1] = ny2
                b = np.zeros(N)
                b[:] = np.sqrt(qx2**2 + qy2**2)
                W = np.zeros((N,N))
                for n in range(N):
                    W[n,n] = 1/d2[n]
                xhat = np.matmul(np.linalg.inv(np.matmul(np.transpose(A),np.matmul(W,A) )),
                              np.matmul(np.transpose(A),np.matmul(W,b))) 
                qxc_d[i] = xhat[0]
                qyc_d[i] = xhat[1]
                
            #############################################################
            # solve least square problem using all points in 6000m radius
            # and using inverse distance squared weighting
            #############################################################
            
            # select points where d is less that 6000m 
            indn = d <= dmax
            d2 = d[indn]
            nx2 = nx1[indn]
            ny2 = ny1[indn]
            xe2 = xe1[indn]
            ye2 = ye1[indn]
            qx2 = qx1[indn]
            qy2 = qy1[indn]
            N = len(nx2)
            
            # use only the Nmax closest points
            if N > Nmax:
                indn = np.argsort(d2)
                indn = indn[0:Nmax]
                N = Nmax
                d2 = d2[indn]
                nx2 = nx2[indn]
                ny2 = ny2[indn]
                xe2 = xe2[indn]
                ye2 = ye2[indn]
                qx2 = qx2[indn]
                qy2 = qy2[indn]
            
            # only solve matrix equation if have at least 4 points
            if N>=3:
                A = np.zeros((N,2))
                A[:,0] = nx2
                A[:,1] = ny2
                b = np.zeros(N)
                b[:] = np.sqrt(qx2**2 + qy2**2)
                W = np.zeros((N,N))
                for n in range(N):
                    W[n,n] = 1/d2[n]**2
                xhat = np.matmul(np.linalg.inv(np.matmul(np.transpose(A),np.matmul(W,A) )),
                              np.matmul(np.transpose(A),np.matmul(W,b))) 
                qxc_d2[i] = xhat[0]
                qyc_d2[i] = xhat[1]
                
            #############################################################
            # solve least square problem using all points in 6000m radius
            # and using inverse distance cubed weighting
            #############################################################
            
            # select points where d is less that 6000m 
            indn = d <= dmax
            d2 = d[indn]
            nx2 = nx1[indn]
            ny2 = ny1[indn]
            xe2 = xe1[indn]
            ye2 = ye1[indn]
            qx2 = qx1[indn]
            qy2 = qy1[indn]
            N = len(nx2)
            
            # use only the Nmax closest points
            if N > Nmax:
                indn = np.argsort(d2)
                indn = indn[0:Nmax]
                N = Nmax
                d2 = d2[indn]
                nx2 = nx2[indn]
                ny2 = ny2[indn]
                xe2 = xe2[indn]
                ye2 = ye2[indn]
                qx2 = qx2[indn]
                qy2 = qy2[indn]
            
            # only solve matrix equation if have at least 4 points
            if N>=3:
                A = np.zeros((N,2))
                A[:,0] = nx2
                A[:,1] = ny2
                b = np.zeros(N)
                b[:] = np.sqrt(qx2**2 + qy2**2)
                W = np.zeros((N,N))
                for n in range(N):
                    W[n,n] = 1/d2[n]**3
                xhat = np.matmul(np.linalg.inv(np.matmul(np.transpose(A),np.matmul(W,A) )),
                              np.matmul(np.transpose(A),np.matmul(W,b))) 
                qxc_d3[i] = xhat[0]
                qyc_d3[i] = xhat[1]
                
# loop through the regular grid, evaluating flux vectors, using just the 5 closest 
# points and the inverse distance cubed weighting matrix
for i in range(len(x)):
    for j in range(len(y)):
        
        ## pick out coordinates on grid
        xc1 = x[i]
        yc1 = y[j]
        
        # check if point is inside the bay, and if it is, proceed with 
        # interpolation step
        if Point(xc1,yc1).within(poly_allbay):
        
            # find the distances between this grid point and points where fluxes
            # are defined
            d = np.sqrt((xe1-xc1)**2 + (ye1-yc1)**2)
            
            #############################################################
            # solve unweighted least square problem using only 4 closet
            # points in the neighborhood
            #############################################################
            
            # select points where d is less that 6000m 
            indn = d <= dmax
            d2 = d[indn]
            nx2 = nx1[indn]
            ny2 = ny1[indn]
            xe2 = xe1[indn]
            ye2 = ye1[indn]
            qx2 = qx1[indn]
            qy2 = qy1[indn]
            N = len(nx2)
            
            # use only the Nmax closest points
            if N > Nmax:
                indn = np.argsort(d2)
                indn = indn[0:Nmax]
                N = Nmax
                d2 = d2[indn]
                nx2 = nx2[indn]
                ny2 = ny2[indn]
                xe2 = xe2[indn]
                ye2 = ye2[indn]
                qx2 = qx2[indn]
                qy2 = qy2[indn]
            
            # only possible to solve matrix equation if have at least 3 points
            if N>=3:
                A = np.zeros((N,2))
                A[:,0] = nx2
                A[:,1] = ny2
                b = np.zeros(N)
                b[:] = np.sqrt(qx2**2 + qy2**2)
                W = np.zeros((N,N))
                for n in range(N):
                    W[n,n] = 1/d2[n]**3
                xhat = np.matmul(np.linalg.inv(np.matmul(np.transpose(A),np.matmul(W,A) )),
                              np.matmul(np.transpose(A),np.matmul(W,b))) 
                qxg[j,i] = xhat[0]
                qyg[j,i] = xhat[1]
 
           
# plot the vector field at the polygon centroids along with the fluxes 
# across the polygon faces to make sure they look like they agree
fig = plt.figure(figsize=(10,10))
ax = fig.subplots()
plt.axis((np.min(x_SB), np.max(x_SB), np.min(y_SB), np.max(y_SB)))
poly_df.plot(ax=ax,color='w',edgecolor='k')
ind = np.logical_and(np.logical_and(xe1>=np.min(x_SB), xe1<=np.max(x_SB)), np.logical_and(ye1>=np.min(y_SB), ye1<=np.max(y_SB)))
plt.quiver(xe1[ind],ye1[ind],qx1[ind],qy1[ind],scale=quiver_scale_SB,scale_units='x',units='x',width=100,color='r',label='fluxes normal to faces')
ind = np.logical_and(np.logical_and(poly_x>=np.min(x_SB), poly_x<=np.max(x_SB)), np.logical_and(poly_y>=np.min(y_SB), poly_y<=np.max(y_SB)))
plt.quiver(poly_x[ind],poly_y[ind],qxc[ind],qyc[ind],scale=quiver_scale_SB,scale_units='x',units='x',width=100,color='k',label='flux vectors, no weighting, 5 closest points')
plt.quiver(poly_x[ind],poly_y[ind],qxc_d[ind],qyc_d[ind],scale=quiver_scale_SB,scale_units='x',units='x',width=100,color='b',label='flux vectors, 1/d weighting, 5 closest points')
plt.quiver(poly_x[ind],poly_y[ind],qxc_d2[ind],qyc_d2[ind],scale=quiver_scale_SB,scale_units='x',units='x',width=100,color='m',label='flux vectors, 1/d$^2$ weighting, 5 closest points')
plt.quiver(poly_x[ind],poly_y[ind],qxc_d3[ind],qyc_d3[ind],scale=quiver_scale_SB,scale_units='x',units='x',width=100,color='g',label='flux vectors, 1/d$^3$ weighting, 5 closest points')
plt.plot([580000.,582000.],[4165000.,4165000.],'k',linewidth=4)
plt.text(581000.,4167000.,'%0.1f g/m/d' % (quiver_scale_SB*2000.),horizontalalignment='center')
plt.xlabel('x (m, UTM Zone 10)')
plt.ylabel('y (m)')
plt.suptitle('Annual Average DIN Flux')
plt.legend()
fig.savefig('plots/DIN_Flux_Annual_Average_Compare_Weighting_Methods/din_flux_polygon_centroids.png')

# plot the vector field on the regular grid along with the fluxes 
# across the polygon faces to make sure they look like they agree
fig = plt.figure(figsize=(10,10))
ax = fig.subplots()
plt.axis((np.min(x_SB), np.max(x_SB), np.min(y_SB), np.max(y_SB)))
poly_df.plot(ax=ax,color='w',edgecolor='k')
ind = np.logical_and(np.logical_and(xe1>=np.min(x_SB), xe1<=np.max(x_SB)), np.logical_and(ye1>=np.min(y_SB), ye1<=np.max(y_SB)))
plt.quiver(xe1[ind],ye1[ind],qx1[ind],qy1[ind],scale=quiver_scale_SB,scale_units='x',units='x',width=200,color='r',label='fluxes normal to faces')
plt.quiver(xg,yg,qxg,qyg,scale=quiver_scale_SB,scale_units='x',units='x',width=100,color='k',label='flux vectors, 1/d$^3$ weighting, 5 closest points')
plt.plot([580000.,582000.],[4165000.,4165000.],'k',linewidth=4)
plt.text(581000.,4167000.,'%0.1f g/m/d' % (quiver_scale_SB*2000.),horizontalalignment='center')
plt.xlabel('x (m, UTM Zone 10)')
plt.ylabel('y (m)')
plt.suptitle('Annual Average DIN Flux')
plt.legend()
fig.savefig('plots/DIN_Flux_Annual_Average_Compare_Weighting_Methods/din_flux_regular_grid.png')

# plot streamlines using the fine regular grid along with the fluxes 
# across the polygon faces to make sure they look like they agree
fig = plt.figure(figsize=(10,10))
ax = fig.subplots()
plt.axis((np.min(x_SB), np.max(x_SB), np.min(y_SB), np.max(y_SB)))
norm = mpl.colors.Normalize(vmin = 0, vmax = qmax)
plt.streamplot(xg,yg,qxg,qyg,color=np.sqrt(qxg**2+qyg**2),cmap='jet',norm=norm,density=2)
cbar = plt.colorbar(fraction=0.046, pad=0.04)
cbar.set_label('Flux Magnitude (g/m/d)')
poly_df.plot(ax=ax,color='w',edgecolor='k')
ind = np.logical_and(np.logical_and(xe1>=np.min(x_SB), xe1<=np.max(x_SB)), np.logical_and(ye1>=np.min(y_SB), ye1<=np.max(y_SB)))
plt.quiver(xe1[ind],ye1[ind],qx1[ind],qy1[ind],scale=quiver_scale_SB,scale_units='x',units='x',width=200,color='r',label='fluxes normal to faces')
plt.plot([580000.,582000.],[4165000.,4165000.],'k',linewidth=4)
plt.text(581000.,4167000.,'%0.1f g/m/d' % (quiver_scale_SB*2000.),horizontalalignment='center')
plt.xlabel('x (m, UTM Zone 10)')
plt.ylabel('y (m)')
plt.suptitle('Annual Average DIN Flux')
plt.legend()
fig.savefig('plots/DIN_Flux_Annual_Average_Compare_Weighting_Methods/din_flux_streamlines.png')


