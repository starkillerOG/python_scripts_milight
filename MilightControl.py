#=====================================================================================================================================
# Import required modules
#=====================================================================================================================================
Python_module_path = "/srv/homeassistant/lib/python3.5/site-packages"    # Path to the Python Paho.mqtt.client module, because OpenElec does not support normal installation of python modules the path to the files of the module must be appended.

import socket
import sys
sys.path.append(Python_module_path)     # add the path to the MQTT module
import paho.mqtt.client as mqtt         # import the Paho MQTT module
import colorsys
import json
import ast
import yaml

#=====================================================================================================================================
# Read the required login credentials.
#=====================================================================================================================================

# Read YAML Passwords:
password_file_path = "????"  # path to the YAML file containing the required login information, you can also enter login credentials directly on the places where "secrets[]" is used in the settings section.
filedata = open(password_file_path, "r")
secrets = yaml.safe_load(filedata)

#=====================================================================================================================================
# Settings section, the values in this section can be altered to personal preference and system configuration.
# at least the values under settings need to be set to your specific system.
#=====================================================================================================================================

# General settings
feedback = 0                                            # If executed in a terminal get messages about the color and ports on each message, syntax: 0=feedback off, 1=feedback on.
# MQTT listener Settings
broker_address =  secrets["MQTT_address"]               # IP address of the device running the MQTT broker (often an Raspberry Pi, an ESP8266 or an PC), syntax: "192.168.1.000"
broker_port =     secrets["MQTT_port"]                  # Port of the MQTT broker, syntax: 1111
broker_username = secrets["MQTT_username"]              # User name of the MQTT broker, syntax: "abcdefg"
broker_password = secrets["MQTT_password"]              # Password of the MQTT broker, syntax: "abcdefg"
broker_topic = "milight/#"                              # MQTT broker topic to subscribe to in order to receive the miligth updates, syntax: "abcdefg"
Milight_control_base_topic = "milight_control/"         # The base topic that is used to control milight bulbs using the ESP milight hub, syntax: "abcdefg"
# Hyperion Settings
Hyperion_IP = secrets["Lightberry_IP"]                  # IP address of the device running Hyperion (often an Raspberry Pi), syntax: '192.168.1.000'
Hyperion_port_list = ['00000','11111','22222']          # Full port list of all Hyperion instances, each instance is a different light group. Syntax for two lights: ['00000','11111']
Hyperion_mode_list = ['HDMI','Color']                   # Define mode list for the mode button
# 433 MHz RF wall plugs Settings
RF_puls_lengt = "485"
RF_protocol = "2"
RF_bits = "28"
RF_control_msg = {'group_A_ON':00000000,'group_A_OFF':11111111,'group_B_ON':22222222,'group_B_OFF':33333333,'group_C_ON':44444444,'group_C_OFF':55555555,'group_D_ON':66666666,'group_D_OFF':77777777,'group_ALL_ON':88888888,'group_ALL_OFF':99999999}
# Milight remote Settings
Hue_corr = 9                                            # Color wheel offset correction, to account for a remote appearing to have the color wheel rotated a bit with respect to the hue value.
Milight_remote_ignore_listen = ['0x0000','0x1111','0x2222','0x3333','0x4444']    # The Milight Device ID's that will be ignored, if you listen en control the same milight device a feedback loop arises winch fluds everything with commands, this is to prevent that.
# initialize the port groups
ports_group = {}
# Add the default ports (if device ID can not be matched)
ports_group['def_0'] = {'Hyperion': ['00000','11111'], 'Milight': ['-'], 'RF-switch': ['-'], 'MQTT': ['-']}            # The lights in group 0 (top ON/OFF button), a list of Hyperion ports for the instances of Hyperion that you want to control in this group, syntax for 1 light: ['00000'], syntax for 2 lights: ['00000','11111'], syntax to disable the group behaviour of this button: []
ports_group['def_1'] = {'Hyperion': ['00000'], 'Milight': ['-'], 'RF-switch': ['-'], 'MQTT': ['-']}                    # The lights in group 1 (bottom ON/OFF button 1), a list of Hyperion ports for the instances of Hyperion that you want to control in this group, syntax for 1 light: ['00000'], syntax for 2 lights: ['00000','11111'], syntax to disable the group behaviour of this button: []
ports_group['def_2'] = {'Hyperion': ['11111'], 'Milight': ['-'], 'RF-switch': ['-'], 'MQTT': ['-']}                    # The lights in group 2 (bottom ON/OFF button 2), a list of Hyperion ports for the instances of Hyperion that you want to control in this group, syntax for 1 light: ['00000'], syntax for 2 lights: ['00000','11111'], syntax to disable the group behaviour of this button: []
ports_group['def_3'] = {'Hyperion': [], 'Milight': [], 'RF-switch': ['-'], 'MQTT': ['-']}                              # The lights in group 3 (bottom ON/OFF button 3), a list of Hyperion ports for the instances of Hyperion that you want to control in this group, syntax for 1 light: ['00000'], syntax for 2 lights: ['00000','11111'], syntax to disable the group behaviour of this button: []
ports_group['def_4'] = {'Hyperion': ['-'], 'Milight': ['-'], 'RF-switch': ['-'], 'MQTT': ['-']}                        # The lights in group 4 (bottom ON/OFF button 4), a list of Hyperion ports for the instances of Hyperion that you want to control in this group, syntax for 1 light: ['00000'], syntax for 2 lights: ['00000','11111'], syntax to disable the group behaviour of this button: []
ports_group['def_5'] = {'Hyperion': ['-'], 'Milight': ['-'], 'RF-switch': ['-'], 'MQTT': ['-']} 
ports_group['def_6'] = {'Hyperion': ['-'], 'Milight': ['-'], 'RF-switch': ['-'], 'MQTT': ['-']} 
ports_group['def_7'] = {'Hyperion': ['-'], 'Milight': ['-'], 'RF-switch': ['-'], 'MQTT': ['-']} 
ports_group['def_8'] = {'Hyperion': ['-'], 'Milight': ['-'], 'RF-switch': ['-'], 'MQTT': ['-']}                        # The lights in group 4 (bottom ON/OFF button 4), a list of Hyperion ports for the instances of Hyperion that you want to control in this group, syntax for 1 light: ['00000'], syntax for 2 lights: ['00000','11111'], syntax to disable the group behaviour of this button: []
# Add the ports for remote ID: '0xAAAA' (bed room)
ports_group['0xAAAA_0'] = {'Hyperion': ['22222'], 'Milight': ['-'], 'RF-switch': ['group_C'], 'MQTT': ['-']}           # The lights in group 0 (top ON/OFF button), a list of Hyperion ports for the instances of Hyperion that you want to control in this group, syntax for 1 light: ['00000'], syntax for 2 lights: ['00000','11111'], syntax to disable the group behaviour of this button: []
ports_group['0xAAAA_1'] = {'Hyperion': ['-'], 'Milight': ['-'], 'RF-switch': ['-'], 'MQTT': ['-']}                     # The lights in group 1 (bottom ON/OFF button 1), a list of Hyperion ports for the instances of Hyperion that you want to control in this group, syntax for 1 light: ['00000'], syntax for 2 lights: ['00000','11111'], syntax to disable the group behaviour of this button: []
ports_group['0xAAAA_2'] = {'Hyperion': ['22222'], 'Milight': ['-'], 'RF-switch': ['-'], 'MQTT': ['-']}                 # The lights in group 2 (bottom ON/OFF button 2), a list of Hyperion ports for the instances of Hyperion that you want to control in this group, syntax for 1 light: ['00000'], syntax for 2 lights: ['00000','11111'], syntax to disable the group behaviour of this button: []
ports_group['0xAAAA_3'] = {'Hyperion': ['-'], 'Milight': ['-'], 'RF-switch': ['group_C'], 'MQTT': ['-']}                           # The lights in group 3 (bottom ON/OFF button 3), a list of Hyperion ports for the instances of Hyperion that you want to control in this group, syntax for 1 light: ['00000'], syntax for 2 lights: ['00000','11111'], syntax to disable the group behaviour of this button: []
ports_group['0xAAAA_4'] = {'Hyperion': ['00000','11111','22222'], 'Milight': ['-'], 'RF-switch': ['group_ALL'], 'MQTT': ['-']}     # The lights in group 4 (bottom ON/OFF button 4), a list of Hyperion ports for the instances of Hyperion that you want to control in this group, syntax for 1 light: ['00000'], syntax for 2 lights: ['00000','11111'], syntax to disable the group behaviour of this button: []
# Add the ports for remote ID: '0xBBBB' (living room)
ports_group['0xBBBB_0'] = {'Hyperion': ['00000','11111'], 'Milight': ['-'], 'RF-switch': ['-'], 'MQTT': ['-']}         # The lights in group 0 (top ON/OFF button), a list of Hyperion ports for the instances of Hyperion that you want to control in this group, syntax for 1 light: ['00000'], syntax for 2 lights: ['00000','11111'], syntax to disable the group behaviour of this button: []
ports_group['0xBBBB_1'] = {'Hyperion': ['-'], 'Milight': ['-'], 'RF-switch': ['-'], 'MQTT': ['-']}                     # The lights in group 1 (bottom ON/OFF button 1), a list of Hyperion ports for the instances of Hyperion that you want to control in this group, syntax for 1 light: ['00000'], syntax for 2 lights: ['00000','11111'], syntax to disable the group behaviour of this button: []
ports_group['0xBBBB_2'] = {'Hyperion': ['00000'], 'Milight': ['-'], 'RF-switch': ['-'], 'MQTT': ['-']}                 # The lights in group 2 (bottom ON/OFF button 2), a list of Hyperion ports for the instances of Hyperion that you want to control in this group, syntax for 1 light: ['00000'], syntax for 2 lights: ['00000','11111'], syntax to disable the group behaviour of this button: []
ports_group['0xBBBB_3'] = {'Hyperion': ['11111'], 'Milight': ['-'], 'RF-switch': ['-'], 'MQTT': ['-']}                 # The lights in group 3 (bottom ON/OFF button 3), a list of Hyperion ports for the instances of Hyperion that you want to control in this group, syntax for 1 light: ['00000'], syntax for 2 lights: ['00000','11111'], syntax to disable the group behaviour of this button: []
ports_group['0xBBBB_4'] = {'Hyperion': ['-'], 'Milight': ['-'], 'RF-switch': ['-'], 'MQTT': ['-']}                     # The lights in group 4 (bottom ON/OFF button 4), a list of Hyperion ports for the instances of Hyperion that you want to control in this group, syntax for 1 light: ['00000'], syntax for 2 lights: ['00000','11111'], syntax to disable the group behaviour of this button: []
# Add the ports for remote ID: '0xCCCC' (wall panel)
ports_group['0xCCCC_0'] = {'Hyperion': ['00000','11111','22222'], 'Milight': [['0x0000','rgbw','1','rgbw'],['0x1111','rgb_cct','3','cct']], 'RF-switch': ['group_ALL'], 'MQTT': {'Milight_button': 'state', 'Milight_value': 'OFF' , 'topic': 'HomeAssistant/control', 'payload': 'Shutdown_ALL'}}              # The lights in group 0 (top ON/OFF button), a list of Hyperion ports for the instances of Hyperion that you want to control in this group, syntax for 1 light: ['00000'], syntax for 2 lights: ['00000','11111'], syntax to disable the group behaviour of this button: []
ports_group['0xCCCC_1'] = {'Hyperion': ['-'], 'Milight': ['-'], 'RF-switch': ['-'], 'MQTT': ['-']}                     # The lights in group 1 (bottom ON/OFF button 1), a list of Hyperion ports for the instances of Hyperion that you want to control in this group, syntax for 1 light: ['00000'], syntax for 2 lights: ['00000','11111'], syntax to disable the group behaviour of this button: []
ports_group['0xCCCC_2'] = {'Hyperion': ['00000'], 'Milight': ['-'], 'RF-switch': ['-'], 'MQTT': ['-']}                 # The lights in group 2 (bottom ON/OFF button 2), a list of Hyperion ports for the instances of Hyperion that you want to control in this group, syntax for 1 light: ['00000'], syntax for 2 lights: ['00000','11111'], syntax to disable the group behaviour of this button: []
ports_group['0xCCCC_3'] = {'Hyperion': ['11111'], 'Milight':['-'], 'RF-switch': ['-'], 'MQTT': ['-']}                  # The lights in group 3 (bottom ON/OFF button 3), a list of Hyperion ports for the instances of Hyperion that you want to control in this group, syntax for 1 light: ['00000'], syntax for 2 lights: ['00000','11111'], syntax to disable the group behaviour of this button: []
ports_group['0xCCCC_4'] = {'Hyperion': ['-'], 'Milight': ['-'], 'RF-switch': ['-'], 'MQTT': ['-']}                     # The lights in group 4 (bottom ON/OFF button 4), a list of Hyperion ports for the instances of Hyperion that you want to control in this group, syntax for 1 light: ['00000'], syntax for 2 lights: ['00000','11111'], syntax to disable the group behaviour of this button: []
ports_group['0xCCCC_5'] = {'Hyperion': ['-'], 'Milight': [['0x0000','rgbw','1','rgbw']], 'RF-switch': ['-'], 'MQTT': ['-']}
ports_group['0xCCCC_6'] = {'Hyperion': ['22222'], 'Milight': ['-'], 'RF-switch': ['-'], 'MQTT': ['-']}
ports_group['0xCCCC_7'] = {'Hyperion': ['-'], 'Milight': ['-'], 'RF-switch': ['group_C'], 'MQTT': ['-']}
ports_group['0xCCCC_8'] = {'Hyperion': ['-'], 'Milight': [['0x1111','rgb_cct','3','cct']], 'RF-switch': ['-'], 'MQTT': ['-']}

# Initialize all the global variables that we need, these are the global variables that are received from the Milight Remote.
global Milight_Hue, Milight_Sat, Milight_Lum, Milight_temp, Milight_Power, Milight_Mode, Hyperion_ports
# set the defaults
Milight_Hue = 240                                        # Hue, default color: blue
Milight_Sat = 100                                        # Saturation / Grey value, always 100 best.
Milight_Lum = 50*2                                       # Luminosity, 0 to 50 is intensity, 50 to 100 goes to white.
Milight_temp = 370                                       # White temperature, Value is in mireds, between 153-370 mireds (2700K-6500K).
Milight_Power = 'ON'                                     # Hyperion power status ON/OFF.
Milight_Mode = 'Color'                                   # Hyperion mode, HDMI grabbing mode or solid color mode
Hyperion_ports = ['00000']                               # Hyperion instance that is controlled for this specific button press/command
# extra global variables that are needed
global Milight_mem
Milight_mem = {}


#=====================================================================================================================================
# Define the code to execute on receiving an MQTT message
#=====================================================================================================================================

def on_message(client, userdata, msg):
    # print empty line to indicate new message handled.
    if feedback == 1:
        print("")
    # Method of stopping this python script: sent an MQTT message with the payload: "stop"
    if (msg.payload == "stop" or msg.payload == "STOP" or msg.payload == "Stop"):
        print("STOP payload received, exiting the MQTT listener")
        client.disconnect()
        sys.exit(1)
    # Method for checking the status of this script
    if (msg.payload == "query_status"):
        client.publish("MQTT_connection_status", str("Milight MQTT Control: connected"), qos=0, retain=False)
        print("MQTT connected")
        return
    # Get the received command as the payload of the MQTT message
    try:
        mess = ast.literal_eval(msg.payload)    # ast.literal_eval is safe:)
    except:
        mess = {}
        print("Invalid payload/command")
        # Display the received MQTT messages if executed in a terminal
        print("topic: " + msg.topic)
        print("payload: " + str(msg.payload))
        return
    
    #=====================================================================================================================================
    # Overwrite the variables that are received from the Milight remote, keep the rest of the variables the same as the previous stored values.
    #=====================================================================================================================================
    
    
    # Get the global variables
    global Milight_Hue, Milight_Sat, Milight_Lum, Milight_temp, Milight_Power, Milight_Mode, Hyperion_ports
    
    # Get the device ID, bulb type and group_id from the topic.
    try:
        Topic_rec = msg.topic.split("/")
        DeviceID = Topic_rec[1]
        bulb_type = Topic_rec[2]
        group_id = Topic_rec[3]
    except:
        print("Topic did not include device_ID, bulb_type and group_id")
        return
    
    # Device ID
    if (DeviceID in Milight_remote_ignore_listen):    # Check if command is sent from a remote where we listen to
        if feedback == 1:
            print("Device ID: " + str(DeviceID) + " in ignore list, not listening")
        return
    
    # Button ID
    ButtonID = mess.get("button_id", "")
    if ButtonID == 0: # invalid button
        if feedback == 1:
            print("Invalid button")
        return
    
    # ON/OFF state
    Power_org = Milight_Power # original power
    Milight_Power = mess.get("state", Milight_Power)
    if Milight_Power != Power_org:                     # If the power state changes.
        Milight_Mode = 'Color'                         # switch to color mode, otherwise if the HDMI signal is not provided it looks like it is not working.
        if (Milight_Sat < 30 or Milight_Lum < 10*2):   # check if the saturation & luminosity are set to very dim, if so, set back to default, to prevent a situation were the lights are so dim that the on/off button appears to do nothing.
            Milight_Sat = 100
            Milight_Lum = 50*2
    
    # Light group ON/OFF buttons
    group = '_' + str(group_id)
    try:
        Hyperion_ports = ports_group.get(DeviceID+group,ports_group['def'+group])['Hyperion']
        Milight_ports = ports_group.get(DeviceID+group,ports_group['def'+group])['Milight']
        RF_ports = ports_group.get(DeviceID+group,ports_group['def'+group])['RF-switch']
        MQTT_ports = ports_group.get(DeviceID+group,ports_group['def'+group])['MQTT']
    except:
        print("Failed to find ports for device ID: " + str(DeviceID) + ", group: " + group.replace('_','') + ", failed to use default ports.")
        return
    
    # Hue color wheel
    Hue_org = Milight_Hue
    Milight_Hue = (mess.get("hue", Milight_Hue-Hue_corr)+Hue_corr)%360
    if Milight_Hue != Hue_org: # if the Hue color wheel is pressed
        Milight_Mode = 'Color' # switch to color mode
    
    # Luminosity slider
    Lum_org = Milight_Lum
    Milight_Lum = int(round(float(mess.get("brightness", (float(Milight_Lum)*255/100)))/255*100))
    
    # Saturation buttons
    Milight_Sat = mess.get("saturation", Milight_Sat)
    Mi_command = mess.get("command", "")
    if Mi_command == "mode_speed_down": # S- button
        Milight_Sat = max(0, min(Milight_Sat - 5, 100)) # fixed to range 0 to 100
    elif Mi_command == "mode_speed_up": # S+ button
        Milight_Sat = max(0, min(Milight_Sat + 5, 100)) # fixed to range 0 to 100
    
    # Color temperature slider
    temp_org = Milight_temp
    Milight_temp = mess.get("color_temp", Milight_temp)
    
    # Mode button
    try:
        mode = mess["mode"]
        index = (Hyperion_mode_list.index(Milight_Mode) + 1) % len(Hyperion_mode_list) # select next index in the list
        Milight_Mode = Hyperion_mode_list[index] # update to new mode
        if index == 1: # If Hyperion is switched back to Color mode, reset the Saturation & Luminosity to the best values to get nice pure colors.
            Milight_Sat = 100
            Milight_Lum = 50*2
    except:
        mode = "not pressed"
    
    if feedback == 1:
        if not ((DeviceID+group) in ports_group):
            print("Ports for device ID: " + str(DeviceID) + " and group: " + group.replace('_','') + ", not specified, using defaults")
        if (Hyperion_ports == ['-'] and Milight_ports == ['-'] and RF_ports == ['-']):
            print("No device associated with device ID: " + str(DeviceID) + ", group: " + group.replace('_',''))
            return
        if (Hyperion_ports != ['-'] or Milight_ports != ['-']):
            HSV = [Milight_Hue,Milight_Sat,Milight_Lum]
            print("HSV: " + str(HSV))
    
    #=====================================================================================================================================
    # Check if sent to Hyperion is necessary
    #=====================================================================================================================================
    
    if Hyperion_ports != ['-']:
        
        #=====================================================================================================================================
        # Build command to sent to Hyperion
        #=====================================================================================================================================
        
        
        # Convert HSL color to RGB
        rgb_raw = colorsys.hsv_to_rgb(float(Milight_Hue)/360, float(Milight_Sat)/100, float(Milight_Lum)/100)
        rgb = [int(round(i*255)) for i in rgb_raw]
        
        # check for white command
        if (Mi_command == "white_mode"):
            rgb = [255,255,255]
        
        # Convert RGB color to Hex
        Hex = '#%02X%02X%02X' % tuple(rgb)
        
        # Check power status, Hyperion doesn't have a true OFF state, setting the color to solid black will turn it 'OFF'. Note that this does not override the current color stored in the global variable, therefore if you turn the lights back on the same color will be remembered.
        if Milight_Power == 'OFF':
            Hex = '#000000'
            rgb = [0,0,0]
        
        # Build command that will be sent to Hyperion
        if Milight_Mode == 'Color':
            payload = {"command":"color", "priority":50, "color":rgb} #"""/storage/hyperion/bin/hyperion-remote.sh --color '""" + Hex + """'"""
        elif Milight_Mode == 'HDMI':
            if Milight_Power == 'ON':
                payload = {"command":"clearall"}    # The HDMI grabber needs a priority with a higher value such that the color will be displayed if no other commands are present but if a color is supplied it will display that color.
            elif Milight_Power == 'OFF':
                payload = {"command":"color", "priority":50, "color":[0,0,0]}
        command = json.dumps(payload) + '\n'
        
        # Check for power state change
        if (Milight_Power != Power_org or (("state" in mess) and len(mess)==1)): # If the power state changes, first clear all priorities to get ensure the command is not block by for instance the phone app with higher priority.
            command = json.dumps({"command":"clearall"}) + '\n' + command
        
        
        #=====================================================================================================================================
        # Sent command to Hyperion
        #=====================================================================================================================================
        
        
        # get the global Hyperion connections that are active
        global Hyperion_s
        
        # Sent command in a loop to each Hyperion instance that needs to be controlled through it's JSON interface.
        for i in range(0, len(Hyperion_ports)):
            try:
                index = Hyperion_port_list.index(Hyperion_ports[i])      # look up the index that we need from the connection list for the correct port.
                Hyperion_s[index].sendall(command)                       # sent the command.
            except:
                print('connection failed, trying to connect')
                # disconnect
                try:
                    for iii in range(0, len(Hyperion_s)):
                        Hyperion_s[iii].shutdown(socket.SHUT_WR)
                        Hyperion_s[iii].close()
                except:
                    print('disconnect (partially) failed')
                # initilize connection list
                Hyperion_s = []
                # connect
                for ii in range(0, len(Hyperion_port_list)):
                    Hyperion_s.append(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
                    Hyperion_s[ii].connect((Hyperion_IP, int(float(Hyperion_port_list[ii]))))
                    print('Connected to ' + str(Hyperion_IP) + ":" + str(int(float(Hyperion_port_list[ii]))))
                # retry sent
                index = Hyperion_port_list.index(Hyperion_ports[i])      # look up the index that we need from the connection list for the correct port.
                Hyperion_s[index].sendall(command)                       # sent the command.
            if feedback == 1:
                print('Hyperion port sent: ' + Hyperion_ports[i])
                #res = s.recv(1024)     # the response from Hyperion
                #print(res)
        
        
        #=====================================================================================================================================
        # Diagnostics
        #=====================================================================================================================================
        
        if feedback == 1:
            #print(msg.topic+" "+str(msg.payload))
            #print(rgb_raw)
            print("RGB: " + str(rgb))
            #print(Hex)
            #print(command)
            #print("ButtonID: " + str(ButtonID))
            #print("DeviceID: " + str(DeviceID))
            #print("mode button" + str(mode))
            print("Mode: " + Milight_Mode)
    
    
    #=====================================================================================================================================
    # Check if sent to Milight is necessary
    #=====================================================================================================================================
    
    if Milight_ports != ['-']:
        # map the hue slider as temp slider
        #BL = 360
        #BR = 75
        #TL = 260
        #TR = 190
        #if Milight_Hue>=0 and Milight_Hue<=BR: #warm white
        #    temp = 100
        #elif Milight_Hue>=TR and Milight_Hue<=TL: #cold white
        #    temp = 0
        #elif Milight_Hue>BR and Milight_Hue<TR: #right side
        #    temp = int(round(100-((Milight_Hue-BR)*100/(TR-BR))))
        #else: #left side
        #    temp = (Milight_Hue-260)*100/(360-TL)
        
        
        # sent command in loop
        for i in range(0, len(Milight_ports)):
            topic_pub = Milight_control_base_topic + Milight_ports[i][0] + '/' + Milight_ports[i][1] + '/' + Milight_ports[i][2]
            
            # construct command
            global Milight_mem
            ID = Milight_ports[i][0]+Milight_ports[i][2]
            command = {}
            if (("state" in mess) and len(mess)==1): # power status explicitly in the sent message.
                command["status"] = Milight_Power
            elif ("Pow"+ID) in Milight_mem: # otherwise check if the power status has changed with regards of the previous command.
                if Milight_Power != Milight_mem["Pow"+ID]:
                    command["status"] = Milight_Power
            if (Milight_Lum != Lum_org or (("brightness" in mess) and len(mess)==1)):
                command["level"] = Milight_Lum
            if (Mi_command == "white_mode" and Milight_ports[i][3] != 'cct'):
                command["command"] = "set_white"
            if Milight_Hue != Hue_org:
                command["hue"] = Milight_Hue
            if (Milight_temp != temp_org or (("color_temp" in mess) and len(mess)==1)):
                command["color_temp"] = Milight_temp
            if Milight_ports[i][3] == 'cct':
                if (("saturation" in mess) and len(mess)==1):
                    command["temperature"] = Milight_Sat
            command = str(command)
            Milight_mem["Pow"+ID] = Milight_Power
            
            # diagnostics
            if feedback == 1:
                print("Pub topic: " + topic_pub)
                print("Command: " + command)
            
            # sent command
            client.publish(topic_pub, command)
            
    #=====================================================================================================================================
    # Check if sent to 433 MHz RF is necessary
    #=====================================================================================================================================
    
    if RF_ports != ['-']:
        if ("state" in mess):
            # MQTT topic to control RF switches
            rf_topic = "home/commands/PLSL_" + RF_puls_lengt + "/433_" + RF_protocol + "/RFBITS_" + RF_bits
            # loop over all devices to control
            for i in range(0, len(RF_ports)):
                # look up the rf command to switch the corresponding group ON/OFF
                message = RF_control_msg[RF_ports[i] + '_' + Milight_Power]
                
                # diagnostics
                if feedback == 1:
                    print("Switch RF: " + RF_ports[i] + " " + Milight_Power)
                    print("Pub topic: " + rf_topic)
                    print("Command: " + str(message))
                
                # Sent the MQTT command
                client.publish(rf_topic, message)
        elif feedback == 1:
            print("No ON/OFF command for rf-switch, ignoring")
    
    #=====================================================================================================================================
    # Check if custom MQTT message is necessary
    #=====================================================================================================================================
    
    if MQTT_ports != ['-']:
        #{'Milight_button': 'state', 'Milight_value': 'OFF' , 'topic': 'HomeAssistant/control', 'payload': 'Shutdown_ALL'}
        if (MQTT_ports['Milight_button'] in mess):
            if (mess[MQTT_ports['Milight_button']] == MQTT_ports['Milight_value']):
                client.publish(MQTT_ports['topic'], MQTT_ports['payload'])
                
                # diagnostics
                if feedback == 1:
                    print("MQTT control, Pub topic: " + MQTT_ports['topic'] + " , Command: " + str(MQTT_ports['payload']))

#=====================================================================================================================================
# Define the MQTT broker behaviour
#=====================================================================================================================================
def on_disconnect(client, userdata, rc):
    if rc != 0: # if disconnect not caused by calling disconnect() (rc = root cause).
        if feedback == 1: 
            print("Unexpected MQTT disconnection, trying to reconnect")

def on_connect(client, userdata, flags, rc):
    print("connecting to broker")
    if rc == 0:
        print("successfully connected to MQTT broker")
        client.subscribe(broker_topic)                    # subscribe to the broker topic
    elif rc == 3:
        print("connection failed, broker with IP: " + broker_address + " unavailable")
    else:
        print("connection failed")

def on_subscribe(client, userdata, mid, granted_qos):
    print("Subscribing to topic: " + broker_topic)

#=====================================================================================================================================
# Start the MQTT listener with its infinite loop.
#=====================================================================================================================================


print("creating MQTT client")
client = mqtt.Client("MilightRemote",clean_session=True)    #client = mqtt.Client("Milight",clean_session=False)         # create new instance
client.on_message = on_message                                # define that the above code is executed when a message is received
client.on_connect = on_connect                                # define that the above code is executed when the client connects
client.on_subscribe = on_subscribe                            # define that the above code is executed when the client subscribes to a topic
client.on_disconnect = on_disconnect                        # define that the above code is executed when the client disconnects
#client.reconnect_delay_set(min_delay=2, max_delay=10)        # set the delay between reconnection attempts
client.username_pw_set(broker_username, broker_password)    # set the username and password for the MQTT broker
client.connect(broker_address, port=broker_port)             # connect to the broker
# subscribing to the broker topic is done in the on_connect code.

# Start the infinite loop to listen for messages, when an MQTT message with payload "stop" is sent the loop will exit and the script stops.
client.loop_forever(retry_first_connection=True)    #client.loop_forever(retry_first_connection=True)
