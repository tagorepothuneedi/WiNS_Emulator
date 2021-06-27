from Emuh import *
from math import sqrt,log10,pi
#from custom_model import *
#from loss import get_freq
import random
def path_loss(ctx, dst, src):
    """Path Loss Model:
    (f) signal frequency transmited(Hz)
    (d) is the distance between the transmitter and the receiver (m)
    (c) speed of light in vacuum (m)
    (L) System loss"""
    f = get_freq(ctx.channel1[int(dst.idx)-1][int(src.idx)-1]) # Convert Ghz to Hz
    c = 299792458.0
    
    d=1
    if d == 0: d = 0.1

    lambda_ = c / f  # lambda: wavelength (m)
    denominator = lambda_ ** 2
    numerator = (4 * pi * d) ** 2 
    pl = 10 * log10(numerator / denominator)

    return int(pl)

def friis(ctx, dst, src):
    """Friis Propagation Loss Model:
    (f) signal frequency transmited(Hz)
    (d) is the distance between the transmitter and the receiver (m)
    (c) speed of light in vacuum (m)
    (L) System loss"""
    gr = 0
    pt = max(ctx.radio_txpower1[int(src.idx)-1][int(dst.idx)-1],ctx.radio_txpower1[int(dst.idx)-1][int(src.idx)-1])
    gt = 0
    gains = pt + gt + gr

    pl = path_loss(ctx, src,dst)
    rssi = gains - pl

    return rssi

def twoRayGround(ctx,  dst, src):
    """Two Ray Ground Propagation Loss Model (does not give a good result for
    a short distance)"""
    gr = 1
    hr = 1
    pt = max(ctx.radio_txpower1[int(src.idx)-1][int(dst.idx)-1],ctx.radio_txpower1[int(dst.idx)-1][int(src.idx)-1])
    gt = 1
    ht = 1
    gains = pt  + gt + gr
    c = 299792458.0  # speed of light in vacuum
    f = get_freq(ctx.channel1[int(dst.idx)-1][int(src.idx)-1]) # frequency in Hz
    d=sqrt((src.position[0]-dst.position[0])**2\
        +(src.position[1]-dst.position[1])**2)
    if d == 0: d = 0.1
    denominator = (c / f) / 1000
    dCross = (4 * pi ) / denominator
    if d < dCross:
        rssi = friis(ctx,src,dst)
    else:
        numerator = (pt * gt * gr * ht ** 2 * hr ** 2)
        denominator = d ** 4
        pldb = int(numerator / denominator)
        rssi = gains - pldb
    return rssi

def logDistance(ctx,dst,src):
    gr = 0
    pt = max(ctx.radio_txpower1[int(src.idx)-1][int(dst.idx)-1],ctx.radio_txpower1[int(dst.idx)-1][int(src.idx)-1])
    gt = 0
    gains = pt + gt + gr
    ref_d = 1
    d=sqrt((src.position[0]-dst.position[0])**2\
        +(src.position[1]-dst.position[1])**2+(src.position[2]-dst.position[2])**2)
    pl = path_loss(ctx, dst,src)
    if d == 0: d = 0.1

    pldb = 10 * ctx.path_loss_param * log10(d / ref_d)
    rssi = gains - (int(pl) + int(pldb)) -NOISE_LEVEL

    return rssi,pl

def logNormalShadowing(ctx, dst,src):
    gr = 1
    pt = max(ctx.radio_txpower1[int(src.idx)-1][int(dst.idx)-1],ctx.radio_txpower1[int(dst.idx)-1][int(src.idx)-1])
    gt = 1
    gRandom = ctx.gRandom
    gains = pt + gt + gr
    ref_d = 1
    pl = path_loss(ctx, dst,src)
    d=sqrt((src.position[0]-dst.position[0])**2\
    +(src.position[1]-dst.position[1])**2+(src.position[2]-dst.position[2])**2)
    if d == 0: d = 0.1
    pldb = 10 * ctx.path_loss_param * log10(d / ref_d) + gRandom
    rssi = gains - (int(pl) + int(pldb)) -NOISE_LEVEL

    return rssi,int(pl) + int(pldb)
    '''
    f=get_freq(ctx.channel1[int(dst.idx)-1][int(src.idx)-1])
    d=sqrt((src.position[0]-dst.position[0])**2\
    +(src.position[1]-dst.position[1])**2)
    PL0=20.0*log10(4.0*pi*1.0*f/SPEED_LIGHT)
    PL=PL0+10.0*(ctx.path_loss_param)*(log10(d)) - gRandom
    return PL
    '''
def ITU(ctx,dst,src):
    f=get_freq(ctx.channel1[int(dst.idx)-1][int(src.idx)-1])
    N=28
    d=sqrt((src.position[0]-dst.position[0])**2\
    +(src.position[1]-dst.position[1])**2)
    if(d>16): N=38
    
    PL=20.0*log10(f)+N*log10(d)+ctx.lF*ctx.nFLOORS-28
    return PL
def get_freq(channel):
    chan_list_2ghz = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    chan_list_5ghz = [36,38, 40,42, 44,46, 48, 52, 56,58, 60, 64, 100,
                    104, 108, 112, 116, 120, 124, 128, 132,
                    136, 140, 149, 153, 157, 161, 165,
                    169, 171, 172, 173, 174, 175, 176,
                    177, 178, 179, 180, 181, 182, 183, 184,
                    185]

    freq_list_2ghz = [2.412e9, 2.417e9, 2.422e9, 2.427e9, 2.432e9, 2.437e9,
                          2.442e9, 2.447e9, 2.452e9, 2.457e9, 2.462e9]
    freq_list_5ghz = [5.18e9,5.19e9, 5.2e9, 5.21e9,5.22e9,5.23e9, 5.24e9, 5.26e9, 5.28e9,5.29e9,5.30e9, 5.32e9,
                        5.50e9, 5.52e9, 5.54e9, 5.56e9, 5.58e9, 5.6e9, 5.62e9,
                        5.64e9, 5.66e9, 5.68e9, 5.7e9, 5.745e9, 5.765e9, 5.785e9,
                        5.805e9, 5.825e9, 5.845e9, 5.855e9, 5.86e9, 5.865e9, 5.87e9,
                        5.875e9, 5.88e9, 5.885e9, 5.89e9, 5.895e9, 5.9e9, 5.905e9,
                        5.91e9, 5.915e9, 5.92e9, 5.925e9]
    
    all_chan = chan_list_2ghz + chan_list_5ghz 
    all_freq = freq_list_2ghz + freq_list_5ghz
    if int(channel) in all_chan:
        idx = all_chan.index(int(channel))
        return all_freq[idx]
    return 2.412e9
