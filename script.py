import sys
import os
import time

file_path = r"C:\Users\kirkw\Documents\Hobby - ConnectBox\Lattest Code Connectbox\usr_local_connectbox_bin\PxUSBm.py"
with open(file_path, "rb") as f:
    content = f.read()

target = b"""              if not(check_iwconfig(AP)):
                  os.system("/bin/systemctl restart hostapd")
                  if not(check_iwconfig(AP)):
                     logging.info("Still not up so having to resort to getNetworkClass")
                     getNetworkClass(1)       # try to fix the problem (shouldn't get here normally)"""
target = target.replace(b"\n", b"\r")

replacement = b"""              if not(check_iwconfig(AP)):
                  os.system("/bin/systemctl restart hostapd")
                  if not(check_iwconfig(AP)):
                     logging.info("Still not up, attempting to reload driver")
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
                         logger.info("Reloading specific driver: " + driver)
                         os.system("rmmod " + driver)
                         time.sleep(2)
                         os.system("modprobe " + driver)
                     else:
                         logger.info("Driver not found in lshw, trying common drivers")
                         os.system("rmmod 8812au 2>/dev/null; rmmod 8189fs 2>/dev/null; rmmod brcmfmac 2>/dev/null")
                         time.sleep(2)
                         os.system("modprobe 8812au 2>/dev/null; modprobe 8189fs 2>/dev/null; modprobe brcmfmac 2>/dev/null")
                     time.sleep(5)
                     os.system("ifup wlan"+str(AP))
                     os.system("/bin/systemctl restart hostapd")
                     if not(check_iwconfig(AP)):
                         logging.info("Still not up so having to resort to getNetworkClass")
                         getNetworkClass(1)       # try to fix the problem (shouldn't get here normally)"""
replacement = replacement.replace(b"\n", b"\r")

if target in content:
    new_content = content.replace(target, replacement)
    with open(file_path, "wb") as f:
        f.write(new_content)
    print("Success")
else:
    print("Target not found")
