#=====================================================================================================================================
# Import required modules
#=====================================================================================================================================
Python_module_path = "/srv/homeassistant/lib/python3.5/site-packages"    # Path to the Python Paho.mqtt.client module, because OpenElec does not support normal installation of python modules the path to the files of the module must be appended.

import sys
sys.path.append(Python_module_path)        # add the path to the Python modules
import json
import ast
import colorsys
import paho.mqtt.client as mqtt         # import the Paho MQTT module
import yaml


#=====================================================================================================================================
# Read the required login credentials.
#=====================================================================================================================================

# Read YAML Passwords:
password_file_path = "????"
filedata = open(password_file_path, "r")
secrets = yaml.safe_load(filedata)

#=====================================================================================================================================
# Settings section, the values in this section can be altered to personal preference and system configuration.
# at least the values under settings need to be set to your specific system.
# This script only works with python 2 not with python 3 due to the "ast" module.
#=====================================================================================================================================

# feedback
feedback = 0                                            # If executed in a terminal get messages about the color and ports on each message, syntax: 0=feedback off, 1=feedback on.
# MQTT listener Settings
broker_address =  secrets["MQTT_address"]               # IP address of the device running the MQTT broker (often an Raspberry Pi, an ESP8266 or an PC), syntax: "192.168.1.000"
broker_port =     secrets["MQTT_port"]                  # Port of the MQTT broker, syntax: 1111
broker_username = secrets["MQTT_username"]              # User name of the MQTT broker, syntax: "abcdefg"
broker_password = secrets["MQTT_password"]              # Password of the MQTT broker, syntax: "abcdefg"
broker_topic = "milight/#"                              # MQTT broker topic to subscribe to, syntax: "abcdefg"
# Milight remote Settings
Hue_corr = 0                                            # Color wheel offset correction, to account for a remote appearing to have the color wheel rotated a bit with respect to the hue value.
# initialize the state
Milight_state = {}
# Add the configuration for the Milight bulbs
Milight_state['Livingroom_light'] = {'couple': ['0xAAAA_1','0xAAAA_0','0xBBBB_1','0xBBBB_0','0xCCCC_0'],'sublights':['Livingroom_light_1','Livingroom_light_2','Livingroom_light_3']}
Milight_state['Livingroom_light_1'] = {'couple':['0xCCCC_1','0xDDDD_1','0xDDDD_0'],'mainlight':'Livingroom_light'}
Milight_state['Livingroom_light_2'] = {'couple':['0xCCCC_2'],'mainlight':'Livingroom_light'}
Milight_state['Livingroom_light_3'] = {'couple':['0xCCCC_3','0xDDDD_1','0xDDDD_0'],'mainlight':'Livingroom_light'}
Milight_state['Bedroom_light'] = {'couple': ['0xGGGG_1','0xGGGG_0']}
Milight_state['Bathroom_light'] = {'couple': ['0xDDDD_3']}
Milight_state['Hallway_light'] = {'couple': ['0xBBBB_7','0xBBBB_0','0xFFFF_0'],'sublights':['Hallway_light_1','Hallway_light_2']}
Milight_state['Hallway_light_1'] = {'couple':['0xFFFF_1'],'mainlight':'Hallway_light'}
Milight_state['Hallway_light_2'] = {'couple':['0xFFFF_2'],'mainlight':'Hallway_light'}
Milight_state['Desk_light'] = {'couple': ['0xBBBB_4','0xBBBB_0','0xAAAA_4','0xAAAA_0','0xEEEE_0'],'sublights':['Desk_light_1','Desk_light_2']}
Milight_state['Desk_light_1'] = {'couple':['0xEEEE_1'],'mainlight':'Desk_light'}
Milight_state['Desk_light_2'] = {'couple':['0xEEEE_2'],'mainlight':'Desk_light'}

# Set the initial defaults for all lights
for key in Milight_state:
    Milight_state[key]['status'] = {"state":'OFF',"brightness":255}
    Milight_state[key]['mem'] = {"saturation":100,"mode":"-","night_mode":"OFF","brightness_color":255,"brightness_white":255}


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
        client.publish("MQTT_connection_status", str("Milight Forwarder: connected"), qos=0, retain=False)
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

    
    # Get the device ID, bulb type and group_id from the topic.
    try:
        Topic_rec = msg.topic.split("/")
        Topic_rec = msg.topic.split("/")
        DeviceID = Topic_rec[1]
        bulb_type = Topic_rec[2]
        group_id = Topic_rec[3]
    except:
        print("Topic did not include device_ID, bulb_type and group_id")
        return
    
    # Check if device ID in one of the list to couple
    light_name = []
    for key in Milight_state:
        if (str(DeviceID)+'_'+str(group_id)) in Milight_state[key]['couple']:
            light_name.append(key)
    if light_name == []:
        if feedback == 1:
            print("Device ID: " + str(DeviceID) + ", group: " + str(group_id) + " not in couple list, ignoring")
        return
    
    # Button ID
    ButtonID = mess.get("button_id", "")
    if ButtonID == 0: # invalid button
        if feedback == 1:
            print("Invalid button")
        return
    
    # for ID's occurring in multiple lights
    for loop in range(0,len(light_name)):
        # ON/OFF state
        if "state" in mess:
            update_mem(light_name[loop],'status',"state",mess["state"])
            if (mess["state"] == "ON"):
                update_mem(light_name[loop],'mem',"night_mode",'OFF')

        # Check for night command
        Mi_command = mess.get("command", "")
        if (Mi_command == "night_mode"):
            update_mem(light_name[loop],'status','color',{'r':255,'g':255,'b':255})
            update_mem(light_name[loop],'status',"brightness",10)
            update_mem(light_name[loop],'status',"color_temp",262)
            update_mem(light_name[loop],'status',"effect","night")
            update_mem(light_name[loop],'mem','night_mode','ON')
        
        # Ignore all commands if in night mode
        if (Milight_state[light_name[loop]]['mem']['night_mode'] != 'ON'):
            # Check for white command
            if (Mi_command == "white_mode" or Mi_command == "set_white"):
                rgb = [255,255,255]
                update_mem(light_name[loop],'status','color',{'r':255,'g':255,'b':255})
                update_mem(light_name[loop],'mem',"mode",'white')
            
            # Color temperature slider
            if "color_temp" in mess:
                rgb = [255,255,255]
                update_mem(light_name[loop],'status','color',{'r':255,'g':255,'b':255})
                update_mem(light_name[loop],'mem',"color_temp",mess["color_temp"])
                update_mem(light_name[loop],'mem',"mode",'white')
            # Select correct color temp based on night mode
            copy_from_mem(light_name[loop],"color_temp","color_temp")
            
            # Hue color wheel
            if "hue" in mess:
                hue = (mess["hue"]+Hue_corr)%360
                update_mem(light_name[loop],'mem',"hue",hue)
                update_mem(light_name[loop],'mem',"mode",'color')
            
            # Saturation slider
            if "saturation" in mess:
                update_mem(light_name[loop],'mem',"saturation",mess["saturation"])
                update_mem(light_name[loop],'mem',"mode",'color')
            
            # Luminosity slider
            mode = Milight_state[light_name[loop]]['mem']["mode"]
            if "brightness" in mess:
                update_mem(light_name[loop],'mem',"brightness_"+mode,mess["brightness"])
            # Select correct Luminosity based on mode
            select_from_mem_mode(light_name[loop],"brightness_","brightness")
            
            # Convert HSV color to "RGB" if possible
            if ("hue" in Milight_state[light_name[loop]]['mem'] and "saturation" in Milight_state[light_name[loop]]['mem'] and Milight_state[light_name[loop]]['mem']["mode"] == 'color'):
                hue = Milight_state[light_name[loop]]['mem']["hue"]
                sat = Milight_state[light_name[loop]]['mem']["saturation"]
                lum = 255
                rgb_raw = colorsys.hsv_to_rgb(float(hue)/360, float(sat)/100, float(lum)/255)
                rgb = [int(round(i*255)) for i in rgb_raw]
                update_mem_color(light_name[loop],{'r':rgb[0],'g':rgb[1],'b':rgb[2]})
        
            # Select correct effect from mode.
            copy_from_mem(light_name[loop],"mode","effect")

        #=====================================================================================================================================
        # Sent MQTT message to the topic
        #=====================================================================================================================================
        
        topic_pub = "milight_state/" + light_name[loop]
        command = json.dumps(Milight_state[light_name[loop]]['status'])
        
        # diagnostics
        if feedback == 1:
            print("Pub topic: " + topic_pub)
            print(light_name[loop] + ' status: ' + str(command))
        
        # sent command
        client.publish(topic_pub, command, qos=0, retain=True)
        
        # check for sublights
        if 'sublights' in Milight_state[light_name[loop]]:
            for i in range(0,len(Milight_state[light_name[loop]]['sublights'])):
                sub_light_name = Milight_state[light_name[loop]]['sublights'][i]
                topic_pub = "milight_state/" + sub_light_name
                command = json.dumps(Milight_state[sub_light_name]['status'])
                client.publish(topic_pub, command, qos=0, retain=True)
                # diagnostics
                if feedback == 1:
                    print('Also sent to sub-light: ' + sub_light_name)
                    #print('Status: ' + str(command))
        
        # check if it has a mainlight
        if 'mainlight' in Milight_state[light_name[loop]]:
            main_name = Milight_state[light_name[loop]]['mainlight']
            sub_group = Milight_state[main_name]['sublights']
            main_power = 'OFF'
            main_color = {"r":125,"g":125,"b":125}
            for i in range(0,len(sub_group)):
                Power = Milight_state[sub_group[i]]['status'].get("state",'OFF')
                if Power == 'ON':
                    main_power = 'ON'
            topic_pub = "milight_state/" + main_name
            command = json.dumps({'state': main_power,'color':main_color})
            client.publish(topic_pub, command, qos=0, retain=True)
            # diagnostics
            if feedback == 1:
                print('Also sent "' + main_power + '" to main-light: ' + main_name)
        
        #=====================================================================================================================================
        # Diagnostics
        #=====================================================================================================================================
        
        #print(str(Milight_state[light_name[loop]]))

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
# Define the functions used
#=====================================================================================================================================               

def update_mem(update_light_name,update_catagory,update_key,update_value):
    Milight_state[update_light_name][update_catagory][update_key] = update_value
    if 'sublights' in Milight_state[update_light_name]:
        for i in range(0,len(Milight_state[update_light_name]['sublights'])):
            sub_light_name = Milight_state[update_light_name]['sublights'][i]
            if ((Milight_state[sub_light_name]['status']['state'] == 'ON' and Milight_state[sub_light_name]['mem']['night_mode'] != 'ON') or update_key == 'state' or update_key == 'night_mode'):
                Milight_state[sub_light_name][update_catagory][update_key] = update_value

def update_mem_color(update_light_name,update_value):
    Milight_state[update_light_name]['status']['color'] = update_value
    if 'sublights' in Milight_state[update_light_name]:
        for i in range(0,len(Milight_state[update_light_name]['sublights'])):
            sub_light_name = Milight_state[update_light_name]['sublights'][i]
            if (Milight_state[sub_light_name]['status']['state'] == 'ON' and Milight_state[sub_light_name]['mem']["mode"] == 'color' and Milight_state[sub_light_name]['mem']['night_mode'] != 'ON'):
                Milight_state[sub_light_name]['status']['color'] = update_value

def copy_from_mem(update_light_name,mem_key,status_key):
    if mem_key in Milight_state[update_light_name]['mem']: 
        update_value = Milight_state[update_light_name]['mem'][mem_key]
        Milight_state[update_light_name]['status'][status_key] = update_value
    if 'sublights' in Milight_state[update_light_name]:
        for i in range(0,len(Milight_state[update_light_name]['sublights'])):
            sub_light_name = Milight_state[update_light_name]['sublights'][i]
            if (Milight_state[sub_light_name]['status']['state'] == 'ON' and Milight_state[sub_light_name]['mem']['night_mode'] != 'ON'):
                if mem_key in Milight_state[sub_light_name]['mem']:
                    update_value = Milight_state[sub_light_name]['mem'][mem_key]
                    Milight_state[sub_light_name]['status'][status_key] = update_value

def select_from_mem_mode(update_light_name,mem_key_pre,status_key):
    mode = Milight_state[update_light_name]['mem']["mode"]
    mem_key = mem_key_pre + mode
    if mem_key in Milight_state[update_light_name]['mem']: 
        update_value = Milight_state[update_light_name]['mem'][mem_key]
        Milight_state[update_light_name]['status'][status_key] = update_value
    if 'sublights' in Milight_state[update_light_name]:
        for i in range(0,len(Milight_state[update_light_name]['sublights'])):
            sub_light_name = Milight_state[update_light_name]['sublights'][i]
            if (Milight_state[sub_light_name]['status']['state'] == 'ON' and Milight_state[sub_light_name]['mem']['night_mode'] != 'ON'):
                mode = Milight_state[sub_light_name]['mem']["mode"]
                mem_key = mem_key_pre + mode
                if mem_key in Milight_state[sub_light_name]['mem']:
                    update_value = Milight_state[sub_light_name]['mem'][mem_key]
                    Milight_state[sub_light_name]['status'][status_key] = update_value

#=====================================================================================================================================
# Start the MQTT listener with its infinite loop.
#=====================================================================================================================================


print("creating MQTT client")
client = mqtt.Client("MilightForwarder",clean_session=True)    # create new instance
client.on_message = on_message                                # define that the above code is executed when a message is received
client.on_connect = on_connect                                # define that the above code is executed when the client connects
client.on_subscribe = on_subscribe                            # define that the above code is executed when the client subscribes to a topic
client.on_disconnect = on_disconnect                        # define that the above code is executed when the client disconnects
#client.reconnect_delay_set(min_delay=2, max_delay=10)        # set the delay between reconnection attempts
client.username_pw_set(broker_username, broker_password)    # set the username and password for the MQTT broker
client.connect(broker_address, port=broker_port)             # connect to the broker
# subscribing to the broker topic is done in the on_connect code.

# Start the infinite loop to listen for messages, when an MQTT message with payload "stop" is sent the loop will exit and the script stops.
client.loop_forever(retry_first_connection=True)
