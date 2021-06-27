uint32converter=2**32
SNR_DEFAULT=30
NOISE_LEVEL= -91
CCA_THRESHOLD=-90

FREQ_1CH=2.412e9
SPEED_LIGHT=2.99792458e8
HWSIM_ATTR_UNSPEC=0
HWSIM_ATTR_ADDR_RECEIVER=1
HWSIM_ATTR_ADDR_TRANSMITTER=2
HWSIM_ATTR_FRAME=3
HWSIM_ATTR_FLAGS=4
HWSIM_ATTR_RX_RATE=5
HWSIM_ATTR_SIGNAL=6
HWSIM_ATTR_TX_INFO=7
HWSIM_ATTR_COOKIE=8
HWSIM_ATTR_CHANNELS=9
HWSIM_ATTR_RADIO_ID=10
HWSIM_ATTR_REG_HINT_ALPHA2=11
HWSIM_ATTR_REG_CUSTOM_REG=12
HWSIM_ATTR_REG_STRICT_REG=13
HWSIM_ATTR_SUPPORT_P2P_DEVICE=14
HWSIM_ATTR_USE_CHANCTX=15
HWSIM_ATTR_DESTROY_RADIO_ON_CLOSE=16
HWSIM_ATTR_RADIO_NAME=17
HWSIM_ATTR_NO_VIF=18
HWSIM_ATTR_FREQ=19
HWSIM_ATTR_PAD=20

HWSIM_ATTR_MAX=21



class emu():
    def __init__(self,noofnodes=0,topology_type='mesh',fading_coeffient=0.5,per=None,\
        path_loss_param=3.5,Xg=0.0,\
            radio_txpower1=None,link_status=None,channel1=None,\
                sta_addr={},radio_channels={},propagation_model='logDistance',gRandom=0.5):
        self.topology_type=topology_type
        self.noofnodes=noofnodes
        self.stations={}
        self.snr_matrix=None
        self.pl_matrix=None
        self.med_util=None
        self.fading_coeffient=fading_coeffient
        self.path_loss_param=path_loss_param
        self.Xg=Xg
        self.per=per 
        self.path_loss_param=path_loss_param
        self.radio_txpower1=radio_txpower1
        self.link_status=link_status
        self.channel1=channel1
        self.sta_addr=sta_addr
        self.radio_channels=radio_channels
        self.sta_fading=None
        self.channel_radios=None
        self.gRandom=gRandom
        self.propagation_model=propagation_model
        self.per_matrix=None
        self.node_transmit=None

class ieee80211_hdr():
    def __init__(self,frame_control,duration_id,addr1,addr2,addr3,seq_ctrl,addr4):
        self.frame_control=frame_control
        self.duration_id=duration_id
        self.addr1=addr1
        self.addr2=addr2
        self.addr3=addr3
        self.seq_ctrl=seq_ctrl
        self.addr4=addr4
class hwsim_tx_rate():
    def __init__(self,idx=-1,count=0):
        self.idx=idx
        self.count=count

class station():
    def __init__(self,idx=None,name=None,sta_type='mesh',position=None,radios=0,radio_txpower={},radio_mac={},hwaddr=None):
        self.idx=idx 
        self.name=name
        self.sta_type=sta_type
        self.position=position
        self.radios=radios
        self.radio_txpower=radio_txpower
        #self.radio_mac=radio_mac
        #self.hwaddr=hwaddr
        
class frame():
    def __init__(self,cookie,freq,flags,signal,tx_rates,hdr,data):
        self.cookie=cookie
        self.freq=freq
        self.flags=flags
        self.signal=signal
        self.tx_rates=tx_rates
        self.hdr=hdr
        self.hwaddr=hwaddr
        self.data=data
        

class pcap():
    def __init__(self,packet_count=0,packet_dropped=0,packet_Intf_drop=0,packet_sent=0):
        self.packet_count=packet_count
        self.packet_dropped=packet_dropped
        self.packet_Intf_drop=packet_Intf_drop
        self.packet_sent=packet_sent

class custom_model():
    def __init__(self,path_loss,**args):
        self.custom_path_loss=path_loss
        self.args=args