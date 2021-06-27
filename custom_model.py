import numpy as np
import matplotlib.pyplot as plt
import pickle
import tensorflow as tf
tfk = tf.keras
tfkm = tf.keras.models
tfkl = tf.keras.layers
import tensorflow.keras.backend as K
from mmwave_chanmod.models import ChanMod, combine_los_nlos, get_link_state
from tqdm import trange
from mmwave_chanmod.models import ChanMod, DataFormat
from mmwave_chanmod.antenna import Elem3GPP, Elem3GPPMultiSector
import math
from loss_models import logDistance,friis
model_dir = './mmwave_chanmod/model_data'
pl_max=200
'''
# Link states
    no_link = 0
    los_link = 1
    nlos_link = 2
    nlink_states = 3
    
# Cell types
terr_cell = 0
aerial_cell = 1
ncell_type = 2
'''
bw = 400e6   # Bandwidth in Hz
nf = 6  # Noise figure in dB
bf_gain = 10*np.log10(64*16)-3  # Array gain 
kT = -174   # Thermal noise in dB/Hz
tx_pow = 23  # TX power in dBm
npts = 100   # number of points for each (x,z) bin
aer_height=30  # Height of the aerial cell
downtilt = 10  # downtilt on terrestrial cells
nx = 40
nz = 20
chan_model = ChanMod(pl_max=pl_max,model_dir=model_dir)
chan_model.load_link_model()
chan_model.load_path_model(weights_fn='path_weights.h5')
def vectorize(src,dst):
    return np.asarray([[dst[0]-src[0],dst[1]-src[1],dst[2]-src[2]]])
    
def get_path_loss_from_model(ctx,src,dst):
    #print(src.sta_type,dst.sta_type)
    if(src.sta_type=='uav' and dst.sta_type=='uav'):
        return logDistance(ctx,dst,src)
    elif(src.sta_type=='aer' and dst.sta_type=='aer'):
        #print('yes logdistance')
        return logDistance(ctx,dst,src)
    elif(src.sta_type=='ter' and dst.sta_type=='ter'):
        return logDistance(ctx,dst,src)
    elif(src.sta_type=='aer' and dst.sta_type=='ter'):
        return logDistance(ctx,dst,src)
    elif(src.sta_type=='ter' and dst.sta_type=='aer'):
        return logDistance(ctx,dst,src)
    
    else:
        dvec=vectorize(src.position,dst.position)
        if(src.sta_type=='aer' or dst.sta_type=='aer'):
            cell_type=np.asarray([1])
        elif(src.sta_type=='terr' or dst.sta_type=='terr'):
            cell_type=np.asarray([0])
    link_state=np.asarray([1])
    return get_snr(ctx,src,dst,dvec,cell_type,link_state)
def path_loss_from_model(dvec,cell_type,link_state):
    npaths_max = chan_model.npaths_max
    # Find the indices where there are some link
    # and where there is a LOS link
    Ilink = np.where(link_state != ChanMod.no_link)[0]
    Ilos  = np.where(link_state == ChanMod.los_link)[0]
    los   = link_state == ChanMod.los_link        

    # Get the condition variables and random noise
    U = chan_model.transform_cond(dvec[Ilink], cell_type[Ilink], los[Ilink])
    nlink1 = U.shape[0]
    Z = np.random.normal(0,1,(nlink1,chan_model.nlatent))

    # Run through the sampling network
    X = chan_model.path_mod.sampler.predict([Z,U]) 

    # Compute the inverse transform to get back the path loss
    # and angle data
    nlos_pl, nlos_ang , nlos_dly = chan_model.inv_transform_data(dvec[Ilink], X)
    return nlos_pl,nlos_ang,nlos_dly

def comp_pl_gain(pl, gain, pl_max):
    """
    Computes the path loss with directional gain
    Parameters
    ----------
    pl : (nlink,npaths_max) array
        Array of path losses for each path
    gain : (nlink, npaths_max) array
        Array of gains on each path
    pl_max : scalar
        Max path loss.  Values below this are not considerd
    Returns
    -------
    pl_dir : (nlink,) array
        Effective path loss with directional gain
    """
    n = pl.shape[0]
    pl_dir = np.zeros(n)
    for i in range(n):
        I = np.where(pl[i,:] < pl_max - 0.1)[0]
        if len(I) == 0:
            pl_dir[i] = pl_max
        else:
            pl_gain = pl[i,I] - gain[i,I]
            pl_dir[i] = -10*np.log10( np.sum(10**(-0.1*pl_gain) ) )
    return pl_dir
 
def get_snr(ctx,src,dst,dvec,cell_type,link_state):
    snr_med = np.zeros((1,1))
    pl_med=np.zeros((1,1))
    # Create the BS elements
    if cell_type == ChanMod.aerial_cell:
        elem_gnb = Elem3GPP(theta0=0, thetabw=90, phibw=0)
    else:
        elem_gnb = Elem3GPPMultiSector(nsect=3,theta0=90+downtilt,\
                                       thetabw=65,\
                                       phi0=0, phibw=90)
    elem_ue = Elem3GPP(theta0=180, thetabw=90, phibw=0)
    snr = np.zeros((1,1,npts))
    pl_arr = np.zeros(npts)
    for i in range(npts):
        # Generate random channels
        pl, ang, _ = path_loss_from_model(dvec,cell_type,link_state) 

        # Compute the UE gain
        if(dst.sta_type=='uav'):
            ue_theta = ang[:,:,DataFormat.aoa_theta_ind]
            ue_phi = ang[:,:,DataFormat.aoa_phi_ind]
            gain_ue = elem_ue.response(ue_phi, ue_theta)

            # Compute the gNB gain
            gnb_theta = ang[:,:,DataFormat.aod_theta_ind]
            gnb_phi = ang[:,:,DataFormat.aod_phi_ind]
            gain_gnb = elem_gnb.response(gnb_phi, gnb_theta)
            gain_tot = gain_ue + gain_gnb
        
        else:
            ue_theta = ang[:,:,DataFormat.aod_theta_ind]
            ue_phi = ang[:,:,DataFormat.aod_phi_ind]
            gain_ue = elem_ue.response(ue_phi, ue_theta)

            # Compute the gNB gain
            gnb_theta = ang[:,:,DataFormat.aoa_theta_ind]
            gnb_phi = ang[:,:,DataFormat.aoa_phi_ind]
            gain_gnb = elem_gnb.response(gnb_phi, gnb_theta)
            gain_tot = gain_ue + gain_gnb

        # Compute the directional gain and RX power
        pl_gain_i = comp_pl_gain(pl, gain_tot, pl_max)
        #tx_pow=
        
        snri = ctx.radio_txpower1[int(src.idx)-1][int(dst.idx)-1] - pl_gain_i + bf_gain - kT - nf - 10*np.log10(bw)
        snri = np.flipud(snri)  
        pl_gain_i=np.flipud(pl_gain_i)
        snr[:,:,i] = snri
        pl_arr[i] = pl_gain_i
    
    # Get the median rx power
    snr_med[:,:] = np.median(snr,axis=2) 
    pl_med =np.median(pl_arr)
    return snr_med[0][0],pl_med 