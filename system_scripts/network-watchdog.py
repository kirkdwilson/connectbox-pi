#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import time
import subprocess
import json
import logging
import logging.handlers
import re

otime_txt = 0
otime_j2 = 0

def sync_brand():
    file_txt = "/usr/local/connectbox/brand.txt"
    file_j2  = "/usr/local/connectbox/brand.j2"
    global otime_txt
    global otime_j2
    
    try:
        time_txt = os.path.getmtime(file_txt)
    except:
        time_txt = 0
    try:
        time_j2  = os.path.getmtime(file_j2)
    except:
        time_j2 = 0

    if ((otime_txt != time_txt) or (otime_j2 != time_j2)):
        if time_txt > time_j2:
            try:
                f = open(file_txt, 'r', encoding='utf-8')
                brand_Str2 = f.read()
                brand_Str2 = brand_Str2.replace("\n","").replace("\r", "").replace(" ", "")
                brand_dict = json.loads(brand_Str2)
                f.close()
                fo = open(file_j2, "w", encoding='utf-8')
                json.dump(brand_dict, fo, indent=4, sort_keys=False)
                fo.close()
                time_j2  = os.path.getmtime(file_j2)
                otime_j2 = time_j2
            except:
                pass
        else:
            try:
                with open(file_j2, "r", encoding='utf-8') as f:
                    brand_dict = json.load(f)
                fo = open(file_txt, 'w', encoding="utf-8")
                fo.write("{\n")
                x = 0
                regex = r'[a-zA-Z@-_*&^%$#!`~:;?/=+]'
                for k,v in brand_dict.items():
                    vv = str(v)
                    if vv == "": vv = '""'
                    if (re.search(regex, k)): k = '"' + k.replace("\"", "") + '"'
                    elif not str(k).isnumeric():k = '"' + k.replace("\"", "") + '"'
                    
                    if (re.search(regex,vv)): vv = '"' + vv.replace("\"", "") + '"'
                    elif not vv.isnumeric(): vv = '"' +  vv.replace("\"", "") + '"'
                    
                    if x == 0:
                        fo.write("    "+ str(k) + ":" + str(vv))
                        x=1
                    else: fo.write(",\n    " + str(k) + ":" + str(vv))
                fo.write("\n}\n")
                fo.close()
                time_txt = os.path.getmtime(file_txt)
                otime_txt = time_txt
            except:
                pass

def get_AP():
    try:
        f = open("/usr/local/connectbox/wificonf.txt", "r")
        wifi = f.read()
        f.close()
        apwifi = wifi.partition("AccessPointIF=")[2].split("\n")[0]
        AP = int(apwifi.split("wlan")[1])
        return AP
    except:
        return 0

def check_iwconfig(b):
    wlanx = "wlan"+str(b)
    try:
        cmd = "iwconfig"
        rv = subprocess.check_output(cmd, shell=True)
        rvs = rv.decode("utf-8").split(wlanx)
        if (len(rvs) >= 2):
            wlanx_flags = str(rvs[1]).find("Mode:Master")
            if (wlanx_flags) >= 1:
                return True
    except:
        pass
    return False

def check_network():
    AP = get_AP()
    AP_up = check_iwconfig(AP)
    if not AP_up:
        print("AP down, attempting restart")
        try:
            os.system(f"ifdown wlan{AP}")
            os.system(f"ifup wlan{AP}")
        except:
            pass
        
        if not check_iwconfig(AP):
            os.system("/bin/systemctl restart hostapd")
            if not check_iwconfig(AP):
                print("Still not up, attempting to reload driver")
                driver = None
                try:
                    res = os.popen("lshw -c Network").read()
                    r = res.split("wlan")
                    for i in range(1, len(r)):
                        if len(r[i]) > 0 and r[i][0] == str(AP):
                            if "driver=" in r[i]:
                                driver = r[i].split("driver=")[1].split(" ")[0]
                                break
                except:
                    pass
                
                if driver and driver != "none":
                    os.system("rmmod " + driver)
                    time.sleep(2)
                    os.system("modprobe " + driver)
                else:
                    os.system("rmmod 8812au 2>/dev/null; rmmod 8189fs 2>/dev/null; rmmod brcmfmac 2>/dev/null")
                    time.sleep(2)
                    os.system("modprobe 8812au 2>/dev/null; modprobe 8189fs 2>/dev/null; modprobe brcmfmac 2>/dev/null")
                
                time.sleep(5)
                os.system(f"ifup wlan{AP}")
                os.system("/bin/systemctl restart hostapd")

if __name__ == "__main__":
    print("Network watchdog started.")
    # Give the system time to boot
    time.sleep(30)
    while True:
        sync_brand()
        check_network()
        # Drop caches occasionally like PxUSBm.py did
        try:
            os.system("sync; echo 3 > /proc/sys/vm/drop_caches")
        except:
            pass
        time.sleep(30)
