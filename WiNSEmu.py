#!/usr/bin/python3.8
import netlink.capi as nl 
import netlink.genl.capi as genl 
import sys 
import traceback 
import struct
from Emuh import *
from loss import calc_intference,init_default_matrix,calc_path_loss,get_signal_by_rate,get_fading_signal,calc_signal_fading
from build_topo import build_config,load_mac80211_hwsim,configure_nodes,clear_topo,init_transmit_arr
import random
import traceback
import logging
#global network
global ctx,pc,iteration 

def string_to_mac(mac):
    if(type(mac)!=bytearray):
        mac=str(mac)
        temp=[]
        for i in range(0,len(mac),2):
            temp.append(int(mac[i:i+2],16))
        ba=struct.pack('!6B',temp[0],temp[1],temp[2],temp[3],temp[4],temp[5])
    else:
        ba=mac
    return ba

def process_frames_frm_drv(msg,args):
    #starttime = time.time()
    global iteration
    nlh=nl.nlmsg_hdr(msg)
    ghdr=genl.genlmsg_hdr(nlh)
    if(ghdr.cmd==2):
        iteration=iteration+1
        if iteration==6:
            iteration=0
            ctx.node_transmit=init_transmit_arr(ctx)
        _,attr=genl.py_genlmsg_parse(nlh,0,22,None)
        src=struct.unpack('!6B',nl.nla_data(attr[2]))
        src=''.join(format(x,'02x') for x in src)
        data=nl.nla_data(attr[3])
        flags=nl.nla_get_u32(attr[4])
        tx_rates=struct.unpack('!bBbBbBbB',nl.nla_data(attr[7]))
        cookie=nl.nla_get_u64(attr[8])
        freq=nl.nla_get_u32(attr[19])
        hdr=ieee80211_hdr(data[:2],data[2:4],data[4:10],data[10:16],data[16:22],data[22:24],data[24:30])
        src_addr=''.join(format(x,'02x') for x in struct.unpack('!6B',hdr.addr2))
        if(hdr.addr1 != b'\xff\xff\xff\xff\xff\xff'):
            pc.packet_count+=1
            dst=hdr.addr1
            send_frames(src,dst,data,flags,freq,tx_rates,cookie,brd=False)
        else:
            for addr in ctx.channel_radios[ctx.radio_channels[src]]:
                dst=addr
                if(src_addr==addr):
                    continue
                send_frames(src,addr,data,flags,freq,tx_rates,cookie,brd=True)
        return
           

def string_to_tx_attempts_ba(tx_attempts):
    li=[]
    for i in range(len(tx_attempts)):
        li.append(tx_attempts[i].idx)
        li.append(tx_attempts[i].count)

    a=struct.pack('!bBbBbBbBbB',li[0],li[1],li[2],li[3],li[4],li[5],li[6],li[7],li[8],li[9])

    return a

def set_all_rates_invalid():
    lst=[]
    for _ in range(5):
        tx_rates=hwsim_tx_rate()
        tx_rates.idx=-1
        tx_rates.count=0
        lst.append(tx_rates)
    return lst
def send_frames(src,dst,data,flags,freq,tx_rates,cookie,brd):
    global ctx
    u_tx_rates=[]
    i=0
    while i<8:
        for a,b in [tx_rates[i:i+2]]:
            u_tx_rates.append(hwsim_tx_rate(a,b))
            i=i+2
    round=0
    tx_ok=0
    counter=0
    i=0
    tx_attempts=set_all_rates_invalid()
    if(brd):
        rate_idx=u_tx_rates[0].idx
        signal=int(ctx.snr_matrix[int(ctx.sta_addr[src])-1][int(ctx.sta_addr[dst])-1]+NOISE_LEVEL)
        if ctx.topology_type!='uav':
            signal+= get_fading_signal(ctx,int(ctx.sta_addr[src])-1,int(ctx.sta_addr[dst])-1)
            sig_intf,ctx=calc_intference(ctx,src,dst,brd)
            signal=int(signal-sig_intf)
        if(signal<CCA_THRESHOLD):
            signal=-100
        #   print("Brd Frame droppped! ")
        if(ctx.per_matrix[signal+100][rate_idx]>random.random()):  
            return
        if(signal<CCA_THRESHOLD):
            return

        
        build_send_frames_to_dst(dst,data,freq,rate_idx,signal)
        return
    dst=''.join(format(x,'02x') for x in struct.unpack('!6B',dst))
    if dst in ctx.sta_addr.keys():
        while (round<4 and u_tx_rates[round].idx!=-1 and tx_ok!=1):
            
            counter=1
            tx_attempts[round].idx=u_tx_rates[round].idx
            while(counter<=u_tx_rates[round].count and tx_ok!=1):
                
                rate_idx=tx_attempts[round].idx
                
                signal=int(ctx.snr_matrix[int(ctx.sta_addr[src])-1][int(ctx.sta_addr[dst])-1]+NOISE_LEVEL)
                
                if ctx.topology_type!='uav':
                    signal+= get_fading_signal(ctx,int(ctx.sta_addr[src])-1,int(ctx.sta_addr[dst])-1)
                    sig_intf,ctx=calc_intference(ctx,src,dst,brd)
                    signal=int(signal-sig_intf)

                if(signal<CCA_THRESHOLD):
                    signal=-100
            
                if(ctx.per_matrix[signal+100][rate_idx]>random.random()):
                    pc.packet_dropped+=1
                    pc.packet_Intf_drop+=1
                    print(str(src)+str(dst)+str(signal)+"Dropped")
                    return
                if(signal<CCA_THRESHOLD):
                    print(str(src)+str(dst)+str(signal)+"Dropped")
                    pc.packet_dropped+=1
                    return
                
                if(build_send_frames_to_dst(dst,data,freq,rate_idx,signal) ):
                    pc.packet_sent+=1
                    tx_ok=1

                tx_attempts[round].count=counter
                counter+=1
            round+=1
        tx_attempts_ba=string_to_tx_attempts_ba(tx_attempts) 
    
    else:
        #batman Mgmt Frame
        rate_idx=u_tx_rates[0].idx
        signal=get_signal_by_rate(rate_idx)
        build_send_frames_to_dst(dst,data,freq,rate_idx,signal)
        return

    if tx_ok :
        flags= flags | (1<<2)
        report_tx_status_src(src,flags,signal,tx_attempts_ba,cookie)
    else:
        pc.packet_dropped+=1
        report_tx_status_src(src,flags,signal,tx_attempts_ba,cookie)
        return

def build_send_frames_to_dst(dst,data,freq,rate_idx,signal):
    msg=nl.nlmsg_alloc()
    genl.genlmsg_put(msg,0,0,family,0,1,2,1)
    dst=string_to_mac(dst)
    rc=nl.nla_put(msg,1,dst)
    rc=nl.nla_put(msg,3,data)
    rc=nl.nla_put_u32(msg,19,freq)
    rc=nl.nla_put_u32(msg,5,rate_idx)
    rc=nl.nla_put_u32(msg,6,signal+uint32converter)
    err=nl.nl_send_auto_complete(s,msg)
    nl.nlmsg_free(msg)
    if(err): 
        return 1
    else: return err
    
    

def report_tx_status_src(src,flags,signal,tx_attempts_ba,cookie):
    msg=nl.nlmsg_alloc()
    genl.genlmsg_put(msg,0,0,family,0,1,3,1)
    src=string_to_mac(src)
    rc=nl.nla_put(msg,2,src)
    rc=nl.nla_put_u32(msg,4,flags)
    
    rc=nl.nla_put_u32(msg,6,signal+uint32converter)
    rc=nl.nla_put(msg,7,tx_attempts_ba)
    rc=nl.nla_put_u64(msg,8,cookie)
    if(rc!=0):
        print("Error filling payload")
        nl.nlmsg_free(msg)
        return -1
    nl.nl_send_auto_complete(s,msg)
    nl.nlmsg_free(msg)
    return 0
 

if __name__=="__main__":
    iteration=0
    ctx=emu()
    pc=pcap()
    mesh=build_config(sys.argv[1])
    print(mesh)
    load_mac80211_hwsim(mesh['radio_per_node'])
    if(mesh['topology']==None):
        mesh['topology']='Mesh'
    ctx=configure_nodes(ctx,mesh['noofnodes'],mesh['topology'],mesh['node_type'],mesh['radio_per_node'],mesh['channel']\
        ,mesh['tx_power'],mesh['position'],mesh['tx_power1']\
        ,mesh['links'],mesh['channel1'],mesh['propagation_model'],None,True)
    ctx.snr_matrix,ctx.pl_matrix=init_default_matrix(ctx)
    ctx=calc_signal_fading(ctx)
    print("Simulating Loss between Nodes")
    calc_path_loss(ctx)
    print("SNR_MATRIX:"+str(ctx.snr_matrix))
    print("PATH LOSS:"+str(ctx.pl_matrix))
    print("radio_nodes"+str(ctx.sta_addr))
    tx_cb=nl.nl_cb_alloc(nl.NL_CB_CUSTOM)
    rx_cb=nl.nl_cb_clone(tx_cb)
    s=nl.nl_socket_alloc_cb(tx_cb)
    genl.genl_connect(s)
    family=genl.genl_ctrl_resolve(s,'MAC80211_HWSIM')
    print(family)
    if(family>0):
        print("Netlink Socket Registered")
    else:
        print("Socket Error")
    nl.py_nl_cb_set(rx_cb,nl.NL_CB_MSG_IN,nl.NL_CB_CUSTOM,process_frames_frm_drv,None)
    msg=nl.nlmsg_alloc()
    genl.genlmsg_put(msg,0,0,family,0,1,1,1)
    err=nl.nl_send_auto_complete(s,msg)
    if(err<0):
        print("Error family")
        nl.nlmsg_free(msg) 
    while 1:
        try:    
            nl.nl_recvmsgs(s,rx_cb)
        except Exception as e:
            logging.error(traceback.format_exc())
            print("packet count:"+str(pc.packet_count))
            print("packet Dropped:"+str(pc.packet_dropped))
            print("packet drop due to intference:"+str(pc.packet_Intf_drop))
            print("packet sent:"+str(pc.packet_sent))
            nl.nl_socket_free(s)
            print("socket released")
            clear_topo(mesh)
            break

        