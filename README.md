##### WiNS_Emulator V1.0 #########

How to Run WiNSEmulator:
- Run the Emulator using "sudo python3 WiNSEmu.py <topology_file>".

How to Build topology file:
- Example Topology files:WiNSEmu/examples
- Toplogy files need below:
    - noofnodes (1-100) = Total number of nodes in Network
    - topology  (mesh,uav) = Defines the type of wireless network it can be "mesh" or "uav"
    - node_type (mesh,uav,aer) = Defines the Node/station type in the network it can be "mesh" or "uav" or "aer"
    - radio_per_node (1-100) = Defines radios per each station or node 
    - channel (2.4 or 5G Channels)- Define channel per radio
    - tx_power = Transmit power per node
    - position = location of node/station in (x,y,z)coordinates
    - tx_power1 = txpower from radio to radio in 2d matrix
    - channel1 = channel from radio to radio in 2d matrix
    - propagation_model(logDistance,logNormalShadowing,custom_model)= loss model to use 
- Naming Convention of Nodes :
- Dependencies:
- Need Linux kernel 5.4.X 
- Support for Linux MAC80211_HWSIM , Batman_ADV Driver Modules  
- Install libnl3.5.0 ( https://github.com/thom311/libnl/releases/download/libnl3_5_0/libnl-3.5.0.tar.gz) {install internal dependencies for libnl if you get any while installing libnl}
- After download
- $ cd libnl3.5.0
- $ ./configure --prefix=/usr     \
            --sysconfdir=/etc \
            --disable-static  && make
- $ make install( as root)
- $ cd libnl3.5.0/python
- $ python3 ./setup.py build
- $ sudo python3 ./setup.py install
- Use python3.5 or higher (to avoid buffer overflow issues)
- $ pip3 install ordered-set
- $ pip3 install numpy
- $ pip3 install tqdm
