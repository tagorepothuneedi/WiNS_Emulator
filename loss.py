from Emuh import *
from math import sqrt,log10,pi
import random
from loss_models import logNormalShadowing,twoRayGround,logDistance,ITU,friis
from custom_model import get_path_loss_from_model
from tqdm import tqdm
def get_fading_signal(ctx,src,dst):
    return ctx.sta_fading[src][dst]
def calc_signal_fading(ctx):
    ctx.sta_fading=[[0 for i in range(ctx.noofnodes)] for j in range(ctx.noofnodes)]
    for i in range(ctx.noofnodes):
        for j in range(ctx.noofnodes):
            normal=-6.0
            for _ in range(12):
                normal+=random.random()
            ctx.sta_fading[i][j]=ctx.fading_coeffient*normal
    return ctx

def get_signal_by_rate(rate_idx):
    rate2signal=[-50,-77,-74,-71,-69,-66,-64,-62,-59,-56,-53,-50,-47,-44,-41]
    if(rate_idx>=0 or rate_idx<15):
        return rate2signal[rate_idx]
    return 0

def calc_path_loss(ctx):
    '''
    if ctx.propagation_model=='custom_model':
        #from custom_model import get_path_loss_from_model
        ctx.propagation_model=ctx.custom_pl
    ''' 
    
    for src in tqdm(ctx.stations.keys()):
        for dst in ctx.stations.keys():
            if(src is dst):
                continue
            snr,pl=ctx.propagation_model(ctx,ctx.stations[dst],ctx.stations[src])
            ctx.snr_matrix[int(src)-1][int(dst)-1]=int(snr) 
            ctx.pl_matrix[int(src)-1][int(dst)-1]=int(pl) 
            
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

def static_interference(ctx,src,dst):
    intf_power=0.0
    channel=ctx.radio_channels[dst]
    for i,mac in enumerate(ctx.channel_radios[channel]):
        if(mac==src or mac==dst):
            continue
        signal=int(ctx.snr_matrix[i][int(ctx.sta_addr[dst])-1]+NOISE_LEVEL+ get_fading_signal(ctx,i,int(ctx.sta_addr[dst])-1))
        intf_power+=dBm_to_milliwatt(signal)
    if(intf_power<=1.0):
        return 0
    return int(milliwatt_to_dBm(intf_power)+0.5)

def dynamic_interference(ctx,src,dst):
    intf_power=0
    channel=ctx.radio_channels[src]
    src=ctx.sta_addr[src]
    dst=ctx.sta_addr[dst]
    ctx.node_transmit[channel].append(src)
    ctx.node_transmit[channel].append(dst)
    intf_nodes=ctx.node_transmit[channel]
    if len(intf_nodes)>2:
        ctx.node_transmit[channel].remove(src)
        ctx.node_transmit[channel].remove(dst)
        for node in ctx.node_transmit[channel]:
            if node!=dst:
                signal=int(ctx.snr_matrix[int(node)-1][int(dst)-1]+NOISE_LEVEL+ get_fading_signal(ctx,int(node)-1,int(dst)-1))
                intf_power+=dBm_to_milliwatt(signal)
        ctx.node_transmit[channel].append(src)
        ctx.node_transmit[channel].append(dst)
        if(intf_power<=1.0):
            return 0,ctx
        return int(milliwatt_to_dBm(intf_power)+0.5),ctx
    else:
        return intf_power,ctx
    
def calc_intference(ctx,src,dst,brd):
    if brd:
        return 0,ctx
    else:
        return dynamic_interference(ctx,src,dst)


def init_default_matrix(ctx):
    snr_matrix=[[None for i in range(ctx.noofnodes)] for j in range(ctx.noofnodes)]
    pl_matrix=[[None for i in range(ctx.noofnodes)] for j in range(ctx.noofnodes)]
    #print(ctx.noofnodes)
    return snr_matrix,pl_matrix

def dBm_to_milliwatt(db_intf):
    INTF_LIMIT=31
    intf_diff=NOISE_LEVEL - db_intf
    if(intf_diff>=INTF_LIMIT):
        return 0.001
    if(intf_diff<=-INTF_LIMIT):
        return 1000.0
    return 10.0**(-intf_diff/10.0)
def milliwatt_to_dBm(val):
    return 10.0*log10(val)