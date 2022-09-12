#!/usr/bin/env python
# coding: utf-8

# Residual Circulation Plot
# Try to extract residual circulation from DFM or DWAQ output
# DWAQ output has intergrated transport,  which for material
# transport is more appropriate.




import sys, os
sys.path.append('/opt/software/rusty/stompy/newest_commit/stompy')
import numpy as np
import stompy.model.delft.waq_scenario as dwaq
import matplotlib.pyplot as plt
from stompy import utils
# This gets us an edge-Q to cell-velocity:
from stompy.model.stream_tracer import U_perot
from stompy.grid import unstructured_grid
import datetime 
import xarray as xr 
from stompy.model.pypart import basic
import stompy.plot.cmap as scmap
from matplotlib import collections
import pandas as pd
from scipy.interpolate import griddata
from matplotlib import colors as mcolors
from matplotlib import cm

#############
# user input
#############

# path to hyd file
hyd_file = '/chicagovol1/hpcshared/open_bay/hydro/full_res/wy2022_bloom/runs/wy2022_bloom_with_temp/DFM_DELWAQ_wy2022_bloom_with_temp/wy2022_bloom_with_temp.hyd'

# where to put the output plots
plot_dir = '/chicagovol1/hpcshared/open_bay/hydro/full_res/wy2022_bloom/runs/wy2022_bloom_with_temp/postprocessing/residual_circulation'

# axis limits and padding to compute velocities on grid
axlim_zoom = (543640.4193889998, 580870.6570183466, 4149206.0610822025, 4198657.989622132)
axlim_padding = 5000

# averaging time period of 2 weeks and output time step of 1 day
tavg_period = np.timedelta64(14,'D')
deltat_out = np.timedelta64(3,'D')

# number of months of spinup time (start making plots after spinup time)
nmonths_spinup = 2

# toggle to include streamlines maps
plot_streamlines_maps = True


############
# main
############

# make directory for storing plots
if not os.path.exists(plot_dir):
    os.makedirs(plot_dir)


# Path to hydro 
hydro = dwaq.HydroFiles(hyd_file)
hydro.infer_2d_elements()
# just to be sure that the reshaping below is kosher,  here
# check the ordering. for dense hydro this should be fine.
assert np.all( 0 == np.std( hydro.seg_to_2d_element.reshape((10, -1)),  axis = 0) )
hydro.infer_2d_links()
# get that to vectors and plot to see if this is correct
g = hydro.grid()
unstructured_grid.cleanup_dfm_multidomains(g)
e2c = g.edge_to_cells(recalc = True)




def flowlink_to_edge(self, g):
    """
    Create a sparse matrix that maps a per-flowlink,  signed quantity (i.e. flow)
    to the edges of g. BC flows entering at the boundary are handled,  but
    internal outfalls are ignored.
    """
    from scipy import sparse
    self.infer_2d_links()
    M = sparse.dok_matrix( (g.Nedges(), self.n_2d_links),  np.float64)
    e2c = g.edge_to_cells()
    geom = self.get_geom()

    cc = g.cells_center()
    elem_xy = np.c_[ geom.FlowElem_xcc.values, 
                   geom.FlowElem_ycc.values ]

    def elt_to_cell(elt):
        # in general elts are preserved as the same cell index, 
        # and this is actually more robust then the geometry
        # check because of some non-orthogonal cells that have
        # a circumcenter outside the corresponding cell.
        if utils.dist(elem_xy[elt] - cc[elt])<2.0:
            return elt
        # in a few cases the circumcenter is not inside the cell, 
        # so better to select the nearest circumcenter than the
        # cell containing it.
        c = g.select_cells_nearest(elem_xy[elt], inside = False)
        assert c is not None
        return c

    for link, (eltA, eltB) in utils.progress(enumerate(self.links)):
        assert eltB>= 0
        cB = elt_to_cell(eltB)

        if eltA<0: # eltA<0 means it's a boundary.
            # so find a boundary edge for that cell
            for j in g.cell_to_edges(cB):
                if e2c[j, 0]<0:
                    sgn = 1
                    break
                elif e2c[j, 1]<0:
                    sgn = -1
                    break
            else:
                print("Link %d -- %d does not map to a grid boundary,  likely a discharge,  and will be ignored."%(eltA, eltB))
                # This is probably a discharge. Ignore it.
                continue
        else:
            cA = elt_to_cell(eltA)
            j = g.cells_to_edge(cA, cB)
            if j is None:
                raise Exception("%d to %d was not an edge in the grid"%(eltA, eltB))
            if (e2c[j, 0] == cA) and (e2c[j, 1] == cB):
                # positive DWAQ flow is A->B
                # positive edge normal for grid is the same
                sgn = 1
            elif (e2c[j, 1] == cA) and (e2c[j, 0] == cB):
                sgn = -1
            else:
                raise Exception("Bad match on link->edge")
        M[j, link] = sgn
    return M

M = flowlink_to_edge(hydro, g)


# get info about start time, stop time, time step in seconds, number of time steps
t_start = np.datetime64(hydro.time0)
t_stop = t_start + np.timedelta64(hydro.t_secs[-1],'s')
times = t_start + hydro.t_secs.astype('timedelta64[s]')

# find the time corresponding to 2 months of model spin-up
months = times.astype('datetime64[M]').astype(int)
t_spunup = times[np.argmax(months==months[0]+nmonths_spinup)]

# to feed the plotting script, we need a set of indices corresponding to the start times and 
# end times of a series of time averaging windows 
t0s = [] # indices for start of averaging periods
tNs = [] # indices for end of averaging periods
tCs = [] # indices for centers of averaging periods
time_1 = t_spunup
while time_1<t_stop:
    time_0 = time_1-tavg_period/2
    time_N = time_1+tavg_period/2
    if time_0>t_start and time_N<t_stop:
        tC = np.argmax(times==time_1)
        t0 = np.argmax(times==time_0)
        tN = np.argmax(times==time_N)
        tCs.append(tC)
        t0s.append(t0)
        tNs.append(tN)
    time_1 = time_1 + deltat_out

# loop through averaging periods and make plots
first_time = True
first_time_1 = True

counter = 0
for t0,tC,tN in zip(t0s, tCs, tNs): 
    
    counter += 1
    time_slice = slice(t0, tN)
    time0 = hydro.time0 # datetime object
    start_slice = time0 + datetime.timedelta(seconds = float(hydro.t_secs[t0])) 
    end_slice   = time0 + datetime.timedelta(seconds = float(hydro.t_secs[tN])) 
    center_slice = time0  + datetime.timedelta(seconds = float(hydro.t_secs[tC])) 
    print('We are looking at a slice from %s - %s, centered at %s' % (start_slice.strftime('%d %b %Y %H:%M'),  end_slice.strftime('%d %b %Y %H:%M'),center_slice.strftime('%d %b %Y %H:%M')))
    
    
    sum_flow_link = np.zeros(hydro.n_2d_links)
    sum_volumes = np.zeros(hydro.n_2d_elements)
    sum_count = 0
    
    
    # Time_slice is an index slice into the time array 
    for t_sec in utils.progress(hydro.t_secs[time_slice]):
        flow    = hydro.flows(t_sec)
        volumes = hydro.volumes(t_sec) # temporarily don't care about time staggering
        flow_link = np.bincount(hydro.exch_to_2d_link['link'], 
                              weights = flow[:hydro.n_exch_x]*hydro.exch_to_2d_link['sgn'])
    
        vol_element = np.bincount(hydro.seg_to_2d_element,  weights = volumes)
        sum_flow_link +=  flow_link
        sum_volumes +=  vol_element
        sum_count +=  1
        
    
    flow_edge = M.dot(sum_flow_link/sum_count)
    vel_cell  = U_perot(g, flow_edge, sum_volumes/sum_count)
    
    # get a gridded representation 
    if first_time : 

        first_time = False
        
        bounds = g.bounds()
        x = np.arange(bounds[0], bounds[1], 750)
        y = np.arange(bounds[2], bounds[3], 750)
        X, Y = np.meshgrid(x, y)
        XY = np.c_[X.ravel(),  Y.ravel()]
        cells = [g.select_cells_nearest(xy, inside = True) for xy in XY]
        xyc = [(xy, c) for xy, c in zip(XY, cells) if c is not None]
        xy, c = zip(*xyc)  # c is index of cell 
        xy = np.array(xy)  # array of x,y coordinates
        c = np.array(c)    # array of coordinating cell indicies 
 
        # make a smaller grid with bounds just outside the zoom window
        xzoom = x[np.logical_and(x>=axlim_zoom[0]-axlim_padding, x<=axlim_zoom[1]+axlim_padding)]
        yzoom = y[np.logical_and(y>=axlim_zoom[2]-axlim_padding, y<=axlim_zoom[3]+axlim_padding)]    
        Xzoom, Yzoom = np.meshgrid(xzoom,yzoom)

        # list of indices that map xy to Xzoom, Yzoom (by default use zero, later set values to nan there using nanmasi)
        ny, nx = np.shape(Xzoom)
        I = np.zeros((ny,nx),dtype=int)
        nanmask = np.zeros((ny,nx),dtype=bool) 
        for i in range(nx):
            for j in range(ny):
                dum = np.argwhere(np.logical_and(Xzoom[j,i]==xy[:,0], Yzoom[j,i]==xy[:,1]))
                if len(dum)==0:
                    nanmask[j,i] = True
                else:
                    I[j,i] = dum[0]
        
    

    ptm = basic.UgridParticles(ncs = [], grid = g)
    # monkey patch static velocity field
    ptm.t_unix = 0
    ptm.U = vel_cell
    ptm.velocity_valid_time=[-1e6, 1e6]
    
    ptm.add_particles(x = xy)
    ptm.P['u'] = ptm.U[ptm.P['c']]
    
    ptm.integrate(np.arange(0, 3*3600, 360))
    
    states = np.array([out[0] for out in ptm.output])
    states.shape
    segs = states.transpose(1, 0, 2)

    
    
    fig, ax = plt.subplots(figsize = (8.5, 10))

    # velocity magnitudde
    mags = utils.dist( vel_cell )
    
    # cell centroids corresponding to velocity magnitudes
    xyg = g.cells_centroid_py()

    # interpolate velocity magnitudes onto regular grid
    mags_xy = griddata(xyg, mags, xy, method='linear')
    
    ccoll = g.plot_cells(values = mags, ax = ax, cmap = scmap.load_gradient('turbo.cpt'))
    ccoll.set_lw(0.6)
    ccoll.set_edgecolor('face')
    ccoll.set_clim([0 ,  0.2])
    plt.colorbar(ccoll, ax = ax, fraction = 0.07, shrink = 0.6)
    

    line_color  = 'w'
    seg_coll    = collections.LineCollection(segs,  zorder = 3,  lw = 0.5,  color = line_color)
    ax.add_collection(seg_coll)
    
    # this gives vector at end of particle track
    uv = utils.to_unit( (segs[:, -1, :]-segs[:, -2, :]) )

    # this gives vector at beginning of particle track
    uv0 = utils.to_unit( (segs[:, 2, :]-segs[:, 1, :]) )

    # now multiply unit vectors at beginning of particle tracks to get velocity vectors
    uv_withmag = uv0* np.tile(mags_xy,(2,1)).transpose()
    
    arrow_width = 0.001 # with 9x9 plot, default was 0.0024 and was too wide
    width_mult = 1 # make arrow heads bigger than default w.r.t. arrow width

    quiv = ax.quiver(segs[:, -1, 0], segs[:, -1, 1], 
                    uv[:, 0], uv[:, 1], scale = 200, zorder = 2.5, color = line_color, width=arrow_width, headwidth=3*width_mult, headlength=5*width_mult) #, width=0.001, headwidth=3*width_mult, headlength=5*width_mult)
    quiv.headaxislength = quiv.headlength

    ax.axis('equal')
    ax.axis(axlim_zoom)
    #ax.set_facecolor('silver')
    ax.xaxis.set_visible(0)
    ax.yaxis.set_visible(0)
    fig.suptitle('velocity (m/s)\naveraged over %s\ncentered at %s' % (tavg_period, center_slice.strftime('%Y-%m-%d')))
    fig.savefig(os.path.join(plot_dir,'residual_velocity_%d-day-avg_%06d.png' % (tavg_period.astype(int),counter)),  dpi = 500)

    plt.close('all')

    ################
    # now make a streamline plot ..............
    ###############

    if plot_streamlines_maps:

        # nicer notation for grid poitns and velocity vector components, magnitude
        xx = xy[:,0]
        yy = xy[:,1]
        velx = uv_withmag[:,0]
        vely = uv_withmag[:,1]
        velm = np.sqrt(velx**2 + vely**2)
    
        # for scaling colorbar, use the 95th pecentile of the velocity magnitude inside the zoom window on the first time step only
        # note there isn't much variation in time so fine to use the first timestep
        if first_time_1:
            first_time_1 = False
            izoom = np.logical_and( np.logical_and ( xx >= axlim_zoom[0], xx<= axlim_zoom[1]),
                                np.logical_and ( yy >= axlim_zoom[2], yy<= axlim_zoom[3]) )
            vmax = np.nanpercentile(velm[izoom], 95)

            ## also get start points
            #start_points = []
            #for j in range(ny):
            #    for i in range(nx):
            #        start_points.append([Xzoom[j,i],Yzoom[j,i]])
    
        # need to put this on the grid X, Y ... recall indices I map xx, yy to X,Y and nanmask return locations that don't have corresponding xx, yy
        VELX = np.zeros((ny,nx))
        VELY = np.zeros((ny,nx))
        VELX = velx[I]
        VELY = vely[I]
        VELX[nanmask] = np.nan
        VELY[nanmask] = np.nan
        VELM = np.sqrt(VELX**2 + VELY**2)
    
    

    
        fig, ax = plt.subplots(figsize = (8.5, 10))
        
        ax.set_facecolor('gray')
        background = g.plot_cells(values = np.ones(np.shape(mags)), ax = ax, cmap='gray')
        background.set_lw(0.6)
        background.set_edgecolor('face')
        background.set_clim([0 ,  1])
        
        cmap = scmap.load_gradient('turbo.cpt')
        norm = mcolors.Normalize(vmin = 0, vmax = vmax)

        # streamline density = 1 means a 30x30 grid, scale up to our ny x nx grid
        density = 3
        densityxy = (density* ny/30, density*nx/30)
    
        #ax.streamplot(X,Y,VELX,VELY,color=VELM,cmap=cmap,norm=norm,density=densityxy)
        ax.streamplot(Xzoom,Yzoom,VELX,VELY,color=VELM,cmap=cmap,norm=norm,density=densityxy)
        
        cbar = fig.colorbar(cm.ScalarMappable(norm=norm, cmap=cmap), ax=ax,fraction=0.02, pad=0.01, orientation='horizontal')
        cbar.set_label('velocity (m/s)')
    
        ax.axis('equal')
        ax.axis(axlim_zoom)
        #ax.set_facecolor('silver')
        ax.xaxis.set_visible(0)
        ax.yaxis.set_visible(0)
        fig.suptitle('velocity (m/s)\naveraged over %s\ncentered at %s' % (tavg_period, center_slice.strftime('%Y-%m-%d')))
    
        fig.savefig(os.path.join(plot_dir,'residual_velocity_streamlines_%d-day-avg_%06d.png' % (tavg_period.astype(int),counter)),  dpi = 500)
    
        plt.close('all')
    
    