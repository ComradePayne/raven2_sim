'''/* Runs Raven 2 simulator by calling packet generator, Raven control software, and visualization code
 * Copyright (C) 2015 University of Illinois Board of Trustees, DEPEND Research Group, Creators: Homa Alemzadeh and Daniel Chen
 *
 * This file is part of Raven 2 Surgical Simulator.
 *
 * Raven 2 Surgical Simulator is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Lesser General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * Raven 2 Surgical Simulator is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with Raven 2 Control.  If not, see <http://www.gnu.org/licenses/>.
 */'''

import os
import subprocess
import random
import sys
from math import cos, sin, sqrt, acos, asin, pow as pow_f
import socket
import sys
from collections import OrderedDict
import numpy as np
import struct
import time
import signal
from sys import argv

env = os.environ.copy()
#print env['ROS_PACKAGE_PATH']
splits = env['ROS_PACKAGE_PATH'].split(':')
raven_home = splits[0]
print '\nRaven Home Found to be: '+raven_home
rsp = str(raw_input("Is the Raven Home found correctly (Yes/No)? "))
if rsp.lower() == 'yes' or rsp.lower() == 'y':
    print 'Found Raven Home Directory.. Starting..\n'
elif rsp.lower() == 'no' or rsp.lower() == 'n':
    print 'Please change the ROS_PACKAGE_PATH environment variable.\n'
    sys.exit(2)
else:
    rsp = input("Is this correct? (Yes/No)")

cur_inj = -1
saved_param = []
surgeon_simulator = 1;
UDP_IP = "127.0.0.1"
UDP_PORT = 34000

# Parse the arguments
script, mode, packet_gen = argv
if mode == "sim":
    print "Run the Simulation"
elif mode == "dyn_sim":
    print "Run the Dynamic Simulation"
elif mode == "rob": 
    print "Run the Real Robot"
else:
    print "Usage: python run.py <sim|dyn_sim|rob> <1:packet_gen|0:gui>"
    sys.exit(2)


# Change define macros
src_file = raven_home + "/include/raven/defines.h"
bkup_file = raven_home + "/include/raven/defines_back.h"
chk_file = raven_home + "/include/raven/defines_last_run"
cmd = 'cp ' + src_file + ' ' + bkup_file
os.system(cmd)
#open files
src_fp = open(src_file,'w')
bkup_fp = open(bkup_file,'r')
start_line = 0;
for i, line in enumerate(bkup_fp):
    if (line.find('Homa') > 0):
	start_line = i   
    if (i == start_line + 1): 
    	if mode == "rob":
    	    line = '//'+line
    if (i == start_line + 2):
    	if mode == "rob" or mode == "sim":
    	    line = '//'+line
    if (i == start_line + 3) or (i == start_line + 4):
	if packet_gen == "0":   
	    line = '//'+line
    src_fp.write(line)
src_fp.close()
bkup_fp.close()
# Make the file
cmd = 'cd ' + raven_home + ';make -j > compile.output'
make_ret = os.system(cmd)
os.system(cmd)
#save a check file
cmd = 'cp ' + src_file + ' ' + chk_file
os.system(cmd)
#restore file
cmd = 'chmod 777 '+bkup_file;
os.system(cmd);
cmd = 'cp ' + bkup_file + ' ' + src_file
# delete backup
if (os.system(cmd) == 0): 
    cmd = 'rm ' + bkup_file;
    os.system(cmd);   
if (make_ret != 0):
   print "Make Error: Compilation Failed..\n"
   quit()
   sys.exit(0)


# Open Sockets
os.system("killall xterm")
sock = socket.socket(socket.AF_INET, # Internet
                      socket.SOCK_DGRAM) # UDP
sock.bind((UDP_IP,UDP_PORT))

# Find my own IP
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("gmail.com", 80))
my_ip = s.getsockname()[0]
#print my_ip
s.close()

goldenRavenTask= 'xterm -e roslaunch raven_2 raven_2.launch'
ravenTask = 'xterm -hold -e roslaunch raven_2 raven_2.launch'
visTask = 'xterm -hold -e roslaunch raven_visualization raven_visualization.launch'
rostopicTask = 'rostopic echo -p ravenstate >'+raven_home+'/latest_run.csv'
if (surgeon_simulator == 1):
    packetTask = 'xterm -hold -e python '+raven_home+'/Real_Packet_Generator_Surgeon.py '+ mode
    #print(packetTask)
else:
    packetTask = 'xterm -e python '+raven_home+'/Packet_Generator.py'


def quit(): 
    try:
        r2_control_pid = subprocess.check_output("pgrep r2_control", 
                shell=True)
        os.killpg(int(r2_control_pid), signal.SIGINT)
        time.sleep(1)
    except:
        pass
    try:
        roslaunch_pid = subprocess.check_output("pgrep roslaunch", 
                shell=True)
        os.killpg(int(roslaunch_pid), signal.SIGINT)
        time.sleep(1)
    except:
        pass
    try:
        os.killpg(raven_proc.pid, signal.SIGINT)
        time.sleep(1)
    except:
        pass
    try:
        os.killpg(packet_proc.pid, signal.SIGINT)
        time.sleep(1)
    except:
        pass
    try:
        os.killpg(rostopic_proc.pid, signal.SIGINT)
        time.sleep(1)
    except:
        pass

    os.system("killall roslaunch")
    os.system("killall rostopic")    
    os.system("killall r2_control")
    os.system("killall rviz")
    os.system("killall rviz")
    os.system("killall xterm")
    os.system("killall python")

def signal_handler(signal, frame):
    print "Ctrl+C Pressed!"
    quit()
    sys.exit(0)

# Main code starts here
signal.signal(signal.SIGINT, signal_handler)

# Call visualization, packet generator, and Raven II software
vis_proc = subprocess.Popen(visTask, env=env, shell=True, preexec_fn=os.setsid)
time.sleep(4)  
if packet_gen == "1":
	packet_proc = subprocess.Popen(packetTask, shell=True, preexec_fn=os.setsid)
        print "Using the packet generator.."
elif packet_gen == "0":
	print "Waiting for the GUI packets.."
else:
    print "Usage: python run.py <sim|dyn_sim|rob> <1:packet_gen|0:gui>"
    sys.exit(2)
raven_proc = subprocess.Popen(ravenTask, env=env, shell=True, preexec_fn=os.setsid)
rostopic_proc = subprocess.Popen(rostopicTask, env=env, shell=True, preexec_fn=os.setsid)
print("Press Ctrl+C to exit.")

#Wait for a response from the robot
data = ''
while not data:
    print("Waiting for Raven to be done...")
    data = sock.recvfrom(100)
    if data[0].find('Done!') > -1:
        print("Raven is done, shutdown everything...")  
    elif data[0].find('Stopped') > -1:
        print("Raven is stopped, shutdown everything...")  
    else:
        data = ''

quit()

