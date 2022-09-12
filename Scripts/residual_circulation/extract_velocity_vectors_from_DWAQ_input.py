# -*- coding: utf-8 -*-
"""
Created on Wed Jan 27 07:06:20 2021

@author: siennaw

A script that processes velocities from DELWAQ-input / DFM binary files and computes residual velocity. 

originally sienna's residual_velocity_HPC_TMP.py

"""

# IMPORT PACKAGES
import sys, os
sys.path.append('/opt/software/rusty/stompy/newest_commit/stompy')
import numpy as np 
import stompy.model.delft.waq_scenario as dwaq
import datetime
from stompy.grid import unstructured_grid
import matplotlib.pyplot as plt
import xarray as xr

# Path to the compiled DFM run  [folder w/ hyd, flo, etc...]
run_name    = 'wy2022_bloom_with_temp'
path2files  = '/chicagovol1/hpcshared/open_bay/hydro/full_res/wy2022_bloom/runs/wy2022_bloom_with_temp/DFM_DELWAQ_wy2022_bloom_with_temp'

# simulation start time, end time, time step
start_time = '2022-05-01'
stop_time = '2022-08-23' 
time_step_minutes = 30

# compute number of time steps and create a nice time axis for output
start_time = np.datetime64(start_time)
stop_time = np.datetime64(stop_time)
time_step = np.timedelta64(time_step_minutes,'m')
time = np.arange(start_time, stop_time, time_step)
ntime = len(time)

# Now we can figure out the name of all the hydro files
hyd_file     = '%s/%s.hyd' % (path2files, run_name)
areafile     = '%s/%s.are' % (path2files, run_name)
flofile      = '%s/%s.flo' % (path2files, run_name)
pointer_file = '%s/%s.poi' % (path2files, run_name)
volumefile   = '%s/%s.vol' % (path2files, run_name)

# load the grid
grid_from_nc = xr.open_dataset(os.path.join(path2files,'%s_waqgeom.nc' % run_name))
FlowElem_xcc = grid_from_nc.FlowElem_xcc.values
FlowElem_ycc = grid_from_nc.FlowElem_ycc.values
nFlowElem = grid_from_nc.nFlowElem.values

# Read in hyd file; see what the starting date of the simulation is
hydro = dwaq.HydroFiles(hyd_file)
time0 = hydro.time0 

# Load in grid 
g = hydro.grid()
g = unstructured_grid.cleanup_dfm_multidomains(g)
    

'''
Generator function for reading in the area and flow files. 

    Wrote this as a generator since the original files are too big to read
    in at once w/o consuming a lot of local memory. Here, we read one 
    'chunk' at a time. Please note that Nsegs is the number of floating point
    numbers in each entry of the binary files. For some binary files, this is 
    10*NGrid_Cells (for example, the *.tau file, which consists of 10 layers 
    of shear stress for each grid cell.) For other binary files, this is the
    number of exchange surfaces (aka, *.flo and *.vol files). You can get 
    the # of exchange surfaces out of the *.hyd file if you open it in a text editor. 
'''
def read_binary(file, Nsegs):
    print('Reading in %s ...' % file)
    f = open(file , "rb")
    while True:
        t0 = np.fromfile(f, dtype = np.int32, count = 1 )
        if len(t0)==0 :
            break 
        data = np.fromfile(f, dtype = np.single, count = Nsegs)
        seconds = t0
        yield seconds, data
    f.close() 

'''
Function to read in the pointer file. This file is a bit of a nightmare in my opinion.
    The specification of the grid cell /segment numbers at both sides of an exchange surface is
    done by the specification of four integers for each exchange surface:
    1 the number of the ’from’ segment
    2 the number of the ’to’ segment
    3 the number of the ’from +1’ segment
    4 the number of the ’to+1’segment
NOTE : the 3rd and 4th column are really only used for fancy discretization schemes, so
we won't touch them in this script. 
'''
def read_poi(file):
    print('Reading in %s ...' % file)
    f = open(file , "rb")
    data = np.fromfile(f, dtype = np.int32)
    data = data.reshape((int(len(data)/4)), 4)
    f.close() 
    print('Finshed reading in %s\n' % file)
    return data 


Ncells = g.Ncells() 
Nxch = hydro.n_exch
print('\n Grid has %d horizontal cells \n' % Ncells)     

# Initialize the "flow generator"
flow_gen = read_binary(flofile,  Nxch)

# Initialize the "area generator"
area_gen = read_binary(areafile, Nxch)

# Read in pointer file-- outlines the cell # to--> from of each exchange surface
pointer = read_poi(pointer_file)  

# Initialize the "volume generator" --> only relevant if we calculate residence times
vol_gen = read_binary(volumefile,  Ncells*10)

# Pull out the "from" and "to" colums from the pointer file
from0 = pointer[:,0]  # contents: cell segment #s // 1-based
to0   = pointer[:,1]  

'''
SW NOTE : we need to be super careful about distinguishing between cell segment # and cell index.
this caused a lot of bugs before and I sort it out by trying to convert cell #s to a zero-index
'''


#%% 

### ***** THIS IS WHERE WE TAKE THE BOTTOM LAYER ONLY.... 

# Take just the bottom layer of cells (velocity @ the bed)
steps = np.arange(1, Ncells*10, Ncells)

IND0    = np.logical_and(to0>=steps[4] , from0>=steps[4])
IND1    = np.logical_and(to0<steps[5] , from0<steps[5])
IND     = np.logical_and(IND1, IND0)

# from0 is negative on open boundary exchanges. because we don't want to deal with that let's cut them out....
BOUNDARY = np.logical_and(to0>=steps[-1] , from0< 0)
 
from0   = from0[IND]
to0     = to0[IND]

# //////// CONVERT CELL NUMBERS TO 0-INDEX HERE
# convert to 2D indices 

nfrom = from0 % Ncells - 1
nto   = to0   % Ncells - 1 


# Let's check we did this correctly. If so, the # of exchanges on a horiztonal layer should be equal to our
# number of exchanges (length of nto, nfrom) plus the number of open boundary conditions.

assert(sum(BOUNDARY) ==  (hydro.n_exch_x + hydro.n_exch_y)/10 - len(nto) )
Nexch = len(nto)
print('Successfully selected layer & cropped out open boundary fluxes... \n')

#%% 


'''
A big problem we run into here is how to come up (properly) with unit vectors
that point the correct direction from the cell edge. (<--| vs |-->)

Currently I'm testing a bit of a hack to see if this works. 
We look at the pointer file, and the list of to-from pointers. We 
then make two items:
    (1) a unit vector perpenidcular to the edge between those two cells
    (2) a vector pointing from the centroid of the 'from' cell to the centroid of the 'to' cell
We can then make sure the unit vector is pointing in the right direction by taking the dot product
of (1) and (2). If it's positive, our unit vector is pointing the right way. If it's not, we need 
to flip it. 
'''

# Retrieve the cell centroids + build array of vectors 
Cell_Centers = g.cells_centroid()
Xfrom, Yfrom = Cell_Centers[nfrom, 0] , Cell_Centers[nfrom, 1] #if we hadn't made our cell #s zero-indexed we would run into issues here :)
Xto, Yto     = Cell_Centers[nto,   0] , Cell_Centers[nto,   1] 
Centroid2Centroid  = np.array([Xto - Xfrom, Yto - Yfrom])

assert(Centroid2Centroid.shape[1] == len(nfrom))
print('Gathered grid centroids, made vectors for all centroid exchanges...')

#%% 


'''
Time for some more vector building and mind-bending index challenges.
As it turns out, each EDGE in the unstructured grid has a unique identifier / index
associated w/ it. Of course! 
'''

# /// MAKING UNIT VECTORS!     
#   Each exchange will be assigned a unit vector 

unit_vectors =  {} 
edges = np.empty((Nexch, 2))
for i in range(Nexch):
    cell1, cell2 = nfrom[i]  , nto[i] 
    cell1_edges = g.cell_to_edges(cell1) # Get list of edges lining that cell
    cell2_edges = g.cell_to_edges(cell2)
    
    # Find shared edge between cells == edge along the border.
    for j in cell1_edges:
        if j in cell2_edges:
            edge = j 
            break 
        else:
            edge = None  
            
    # Need to build an exception in case there's no matching edge. Just in case..
    if edge is None:
        print('Error at the pointer between %d --> %d' % (cell1, cell2))
        print(g.is_boundary_cell(cell1))
        print(g.is_boundary_cell(cell2))

    
    # Get the two (x,y) coordinates defining the edge line.
    edgeXY = (g.nodes['x'][g.edges['nodes'][edge]]) 
    xy  = edgeXY[1,:] - edgeXY[0,:]    # Make vector parallel to the edge
    xyN = np.array([xy[1], -xy[0]])    # Make a normal vector 
    
    # Check if the dot product w/ centroid 2 centroid is +
    #  /// if not, flip vector
    if xyN.dot(Centroid2Centroid[:,i]) < 0:
        xyN = np.array([-xy[1], xy[0]])    # Normal vector to (x,y) = (-y, x)

    # Double check this worked. If it's still negative we have a problem.
    assert(np.abs(xy.dot(xyN)) <  1e-3 )
    
    # Normalize by magnitude to produce unit vector 
    nx = xyN[0]/np.sqrt(xyN[0]**2 + xyN[1]**2)
    ny = xyN[1]/np.sqrt(xyN[0]**2 + xyN[1]**2)
    
    ## // OK HERE'S THE COMPLICATED THING .. (see below)
    unit_vectors[edge] = [nx, ny]
    
    '''
    I'm not proud of this bit and there's most certainly a better way. However,
    this was the only way I could get this to run w/o bugs and correctly match
    up all our exchange surfaces to the unit vector.
    
    In short, what we do here is build a dictionary for the unit vectors where
    the key is UNIQUE EDGE #, or the index of the EDGE ITSELF. deeply inelegant..
    
    However, when I tried to build an array where the unit vector is at the same
    index as the exchange itself, I got bugs. Probably another 1 or 0-index
    error.    
    '''
        

#%% 
'''
This loop is slow since we're doing a lot of searching. Tried to speed it up but who knows. 
Long story short, we are creating a dictionary. 

      key --> the cell # (0:NCells-1)
      
      contents --> the list of indices of all the exchanges that involve that cell.
We will use these indices later to slice into our flow array + normal vector array.
Currently I'm experimenting with trying to list indices of exchanges that are:
      (a) Cell of interest --> another cell
      (b) another cell --> cell of interest
      (c) all indices that weren't flagged as 'problems' in our unit vector search.
'''


indices = {}
signs = {}      # we need this for residence time 

for cell in range(Ncells):
    ind = np.logical_or(nfrom == cell, nto == cell)  
    inds = np.argwhere(ind)
    inds = [k[0] for k in inds]
    indices[cell] = inds # all inds where this cell is either the from cell or the to-cell
    
    # Now look at the direction of the pointer: will positive flow be entering or exiting that cell?
    sgn = []
    for i in inds:
        if nfrom[i] == cell:
            sgn.append(-1)  #  flow is leaving cell
        else:
            sgn.append(1)   # flow is entering cell 
        signs[cell] = sgn
print('Finished mapping exchange surfaces to each cell... \n')
#%%  

# This is the worst part of the script, so hang in there. 
# Even looking at this now, it's painful. Essentially we're combining 
# two things we've just done. We go cell by cell and ask the following questions
#   (1) : what is the INDEX of the exchanges associated with this cell?
#         ie, if I were to index into the "flo" file, which flows would be
#         associated with each cell ?
#   (2) : Great, ok. Now that I know the exchange index #, what is the edge number
#        of that exchange surface? 
# With these two ingredients we can map cell number --> exchange index --> unit vector
# Please find a way to get rid of this bit if you can!!!!!! 
ind_map = {}   
for cell in range(Ncells):
    inds = indices[cell]
    for i in inds:
        cell1, cell2 = nfrom[i] , nto[i] 
        if not cell1==cell and not cell2 == cell:
            print('Original cell was %d' % cell)
            print('But according to pointer file, to = %d ; from = %d' % (cell2, cell1))
            print('\n')
        cell1_edges = g.cell_to_edges(cell1)
        cell2_edges = g.cell_to_edges(cell2)
        
        # Find shared edge 
        for j in cell1_edges:
            if j in cell2_edges:
                edge = j 
                break 
            else :
                edge = None
        if edge is None:
            continue 
        ind_map[i] = edge     
print('Finished mapping indices .... \n')
#%% 
'''
PLOTTING THE NORMAL VECTORS + CELLS .... 
This fun bit is great for visualizing what's happening. You can save the figures. It randomly generates them for 2 cells right
now but that can be changed. In short, you can make sure each cell is properly matched up w/ its edges + unit vectors (and that
unit vector is perpendicular to the edge!) 
                                                                                                 
If these plots look good we know our operation will proceed successfully! 
'''
if not os.path.exists("cell_plots"):
    os.makedirs("cell_plots")

for cell in np.random.randint(Ncells, size = (5)):
    cell0 = g.cell_polygon(cell)
    fig = plt.figure()
    plt.plot(*cell0.exterior.xy, color = 'red' , linewidth = 10, label = 'original cell')
    inds = indices[cell]
    for i in inds:
        cell1, cell2 = nfrom[i]  , nto[i] 
        if not cell1==cell and not cell2 == cell:
            print('Original cell was %d' % cell)
            print('But according to pointer file, to = %d ; from = %d' % (cell2, cell1))
            print('\n')
        cell1_edges = g.cell_to_edges(cell1)
        cell2_edges = g.cell_to_edges(cell2)
        
        # Find shared edge 
        for j in cell1_edges:
            if j in cell2_edges:
                edge = j 
                break 
            else :
                edge = None
        if edge is None:
            continue 
        if cell2 == cell:
            p2 = g.cell_polygon(cell1)
        else:
            p2 = g.cell_polygon(cell2)
        edge = ind_map[i]   
        p3 = g.edge_line(edge)
        plt.plot(*p2.exterior.xy, color = 'blue', label = 'TO')
        plt.plot(*p3.xy, color = 'green', linewidth = 5)
        ux, uy = unit_vectors[edge]
        plt.arrow(p3.centroid.coords[0][0], p3.centroid.coords[0][1] , ux*50, 50*uy, head_width = 15)  
        
       
    ax = plt.gca()
    ax.set_title(cell)
    plt.legend() 
    ax.axis('equal')
    fig.savefig('./cell_plots/%d.png' % cell)
    print('Saved plot for cell %d' % cell)
            


#%% 


u, v = np.empty((ntime, Ncells)) , np.empty((ntime, Ncells)) 
u[:] = np.nan
v[:] = np.nan 

for t in range(ntime): 

    # Pull out the values from our generators at the first time step. Each time these are called, it will print the subsequent data chunk.
    seconds, Q      = next(flow_gen) 
    seconds, area   = next(area_gen)
    seconds, volume = next(vol_gen)
     
    
    # Convert flow (m3/s) to m/s by dividing by area. If area==0, U=0 
    U =  np.divide(Q, area, out = np.zeros_like(Q), where=area!=0) # m3/s divided by m2 == m/s velocities 
    
    Q = Q[IND]  # Select the bottom layer (index was defined early in script)
    U = U[IND]
    
    print('%s: Computing velocity vectors for time step %d of %d'% (datetime.datetime.now(),t,ntime))
    
    # Initialize arrays for u, v, and RT (residence time)
    # u, v, RT = np.empty((Ncells)), np.empty((Ncells)), np.empty((Ncells))
    # u[:], v[:] = np.nan , np.nan

    # The fun begins ... 
    for cell in range(Ncells):
        cell_edges = indices[cell]  # Get the index #s of the exchanges w/ that cell
        
        # If there's less than 3 exchanges, we can't solve our matrix equation
        if len(cell_edges) < 3:
            u_cell , v_cell = np.nan, np.nan
            continue 
        else:
            # //// Time to calculate velocity! ///// 
            UNITS = np.empty((len(cell_edges),2))   # Build unit vector matrix
            for i,edge in enumerate(cell_edges):
                UNITS[i,:] =  unit_vectors[ind_map[i]]  # here's that awful indexing...
            
            flows = U[cell_edges]   # All m/s flows at each exchange
 
            
            # Solve the equation--> Ax = B for (x) where :
            #   A = the unit vectors, or direction of flow at each exchange surface 
            #   x = the velocity at the center of the cell
            #   B = the velocity (m/s) at the exchange surface
            try:
                sol = np.linalg.lstsq(UNITS, flows, rcond = 1e-20)
            except:
                print('PROBLEM!!!!!****')
                print(cell)
                print(flows)
                continue 
            
            u_cell , v_cell = sol[0] # Solution ! 
            u[t, cell]     = u_cell
            v[t, cell]     = v_cell

# get a note about how the dataset was generated
if '__file__' in locals():
    file_path = os.path.realpath(__file__)
else:
    file_path = 'extract_velocity_vectors_from_DWAW_input.py'


# make it into an xarray dataset
ds = xr.Dataset({
    'FlowElem_xcc': xr.DataArray(
                data   = FlowElem_xcc,   # enter data here
                dims   = ['nFlowElem'],
                coords = {'nFlowElem' : nFlowElem},
                attrs  = {
                    'units'     : 'm'
                    }
                ),
    'FlowElem_ycc': xr.DataArray(
                data   = FlowElem_ycc,   # enter data here
                dims   = ['nFlowElem'],
                coords = {'nFlowElem' : nFlowElem},
                attrs  = {
                    'units'     : 'm'
                    }
                ),
    'u': xr.DataArray(
                data   = u,   # enter data here
                dims   = ['time','nFlowElem'],
                coords = {'time': time,
                          'nFlowElem' : nFlowElem},
                attrs  = {
                    'units'     : 'm/s'
                    }
                ),
    'v': xr.DataArray(
                data   = u,   # enter data here
                dims   = ['time','nFlowElem'],
                coords = {'time': time,
                          'nFlowElem' : nFlowElem},
                attrs  = {
                    'units'     : 'm/s'
                    }
                )},
        attrs = {'origin' : 'generated at %s by %s' % (datetime.datetime.now(), file_path)}
    )    
             
# save results
ds.to_netcdf(os.path.join(path2files, '%s_velocity_vectors.nc' % run_name))   
       
#res_u = np.nanmean(u, axis=0)
#res_v = np.nanmean(v, axis=0)
#magnitude =  np.sqrt(res_u**2 + res_v**2)
#
#res_uUNIT = res_u/magnitude
#res_vUNIT = res_v/magnitude
#print(magnitude)
#
#
#  
#    
#  
## OLD Plotting stuff 
#import stompy.plot.cmap as scmap
#import matplotlib.pyplot as plt 
#plt.switch_backend('Agg')
#
#  
#fig = plt.figure(figsize = (12, 9))
#ax  = fig.add_subplot(1, 1, 1)
#
#ccoll = g.plot_cells(values = magnitude, ax = ax, cmap = 'PuBu')
#ccoll.set_lw(0.6)
#ccoll.set_edgecolor('face')
#ccoll.set_clim([0 ,  0.2])
#ax.axis('equal')
## ax.axis([545e3, 585e3, 4.140e6, 4.225e6])
#ax.set_facecolor('silver')
#plt.colorbar(ccoll, ax = ax, fraction = 0.07, shrink = 0.6)
#
## QUIVER?
#res_uUNIT = res_u / magnitude 
#res_vUNIT = res_v / magnitude 
## quiv = ax.quiver(Cell_Centers[::50,0],  Cell_Centers[::50,1],
##                     res_uUNIT[::50], res_vUNIT[::50], scale = 85, zorder = 2.5, color = 'white')
#  
#    
#name  = 'DELTA_averaged%s_%s_UU.png' % (run_name, time0 + datetime.timedelta(seconds = float(seconds)))
#name = name.replace(':', "_")
#name = name.replace(' ', "_")
#fig.savefig(name, dpi = 600)
#plt.close()
#print('saved image')
#
##%% 
#fig = plt.figure(figsize = (12, 9))
#ax  = fig.add_subplot(1, 1, 1)
#
#ccoll = g.plot_cells(values = res_u, ax = ax, cmap = 'seismic')
#ccoll.set_lw(0.6)
#ccoll.set_edgecolor('face')
#ccoll.set_clim([-0.2 ,  0.2])
#ax.axis('equal')
## ax.axis([545e3, 585e3, 4.140e6, 4.225e6])
#ax.set_facecolor('silver')
#plt.colorbar(ccoll, ax = ax, fraction = 0.07, shrink = 0.6)
#
## quiv = ax.quiver(Cell_Centers[::50,0],  Cell_Centers[::50,1],
##                     res_uUNIT[::50], res_vUNIT[::50], scale = 85, zorder = 2.5, color = 'white')
#  
#    
#name  = 'DELTA_averaged%s_%s_U.png' % (run_name, time0 + datetime.timedelta(seconds = float(seconds)))
#name = name.replace(':', "_")
#name = name.replace(' ', "_")
#fig.savefig(name, dpi = 600)
#plt.close()
#print('saved image 2')
#
##%% 
#fig = plt.figure(figsize = (12, 9))
#ax  = fig.add_subplot(1, 1, 1)
#
#ccoll = g.plot_cells(values = res_v, ax = ax, cmap = 'seismic')
#ccoll.set_lw(0.6)
#ccoll.set_edgecolor('face')
#ccoll.set_clim([-0.2 ,  0.2])
#ax.axis('equal')
## ax.axis([545e3, 585e3, 4.140e6, 4.225e6])
#ax.set_facecolor('silver')
#plt.colorbar(ccoll, ax = ax, fraction = 0.07, shrink = 0.6)
#
#    
#name  = 'DELTA_averaged%s_%s_V.png' % (run_name, time0 + datetime.timedelta(seconds = float(seconds)))
#name = name.replace(':', "_")
#name = name.replace(' ', "_")
#fig.savefig(name, dpi = 600)
#plt.close()
#print('saved image 3')
#
#
#    # sys.exit() 
#   
#
#
#
#
## def spring_neap_filter(y, dt_days, low_bound=1/36.0, high_bound=1/48.0):
#
##     """ 
##     Based on Noah Knowles' tidal filter, for which low_bound = 1/(30 hr) and
##     high_bound = 1/(40 hr). By analogy, since tidal period is 12.5 hours and 
##     spring-neap period is 15 days, 1/30 hr translates to 1/36 days and 1/40 hr
##     translates to 1/48 days. It is a bit of a misnomer to call these "bounds" 
##     as in fact this filter is basically a top-hat with a slightly sloping 
##     side instead of a vertical line. The low_bound and high_bound describe the
##     start and end points of the sloping bit.
#    
##     The original default parameters 1/30 and 1/40 are derived from the article:
##     1981, 'Removing Tidal-Period Variations from Time-Series Data
##     Using Low Pass Filters' by Roy Walters and Cythia Heston, in
##     Physical Oceanography, Volume 12, pg 112.
#
##     Noah derived this code from the TAPPY project: 
##         https://github.com/pwcazenave/tappy
##     Allie King then adapted code from Noah 
#    
##     Usage:
#        
##         yf = tidal_filter(y, deltat)
#        
##     Input:
#    
##         y = time series to be filtered
##         dt_days = time step between data points in days
#    
##     Output:
#        
##         yf = filtered time series
#    
##     """
#    
##     # convert low and high bounds to match series time step
##     low_bound = dt_days*low_bound
##     high_bound = dt_days*high_bound
#    
##     if len(y) % 2:
##         result = np.fft.rfft(y, len(y))
##     else:
##         result = np.fft.rfft(y)
##     freq = np.fft.fftfreq(len(y))[:len(result)]
##     factor = np.ones_like(result)
##     factor[freq > low_bound] = 0.0
#
##     sl = np.logical_and(high_bound < freq, freq < low_bound)
#
##     a = factor[sl]
##     # Create float array of required length and reverse
##     a = np.arange(len(a) + 2).astype(float)[::-1]
#
##     # Ramp from 1 to 0 exclusive
##     a = (a/a[0])[1:-1]
#
##     # Insert ramp into factor
##     factor[sl] = a
#
##     result = result * factor
##     yf = np.fft.irfft(result, len(y))
#    
##     return yf  
#
#