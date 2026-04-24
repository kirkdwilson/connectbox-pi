#! /usr/bin/python3
# -*- coding: utf-8 -*-
import subprocess
import sys
import shutil
import os
from . import page_display_image
import time
import neo_batterylevelshutdown.usb as usb
import neo_batterylevelshutdown.hats as hat
import json
import logging

import neo_batterylevelshutdown.globals as globals

# globals was initiated by cli, so no need to re initialize here
# We do the imports here... but function calls inside of the code
if globals.device_type == "RM3":
    import radxa.CM3    # not required
    import OPi.GPIO as GPIO  # pylint: disable=import-error
elif globals.device_type == "NEO":
    import RPi.GPIO as GPIO  # pylint: disable=import-error
elif globals.device_type == "OZ2":
    import RPi.GPIO as GPIO  # pylint: disable=import-error
    import orangepi.zero2
else:
    import RPi.GPIO as GPIO  # pylint: disable=import-error


comsFileName = "/tmp/creating_menus.txt"
DEBUG = True

class BUTTONS:
    # This class is for dealing with button presses on the connectbox

    BUTTON_PRESS_BUSY = False  # Prevent dual usage of the handleButtonPress function
    BUTTON_PRESS_TIMEOUT_SEC = 0.25  # Prevent bouncing of the handleButtonPress function
    BUTTON_PRESS_CLEARED_TIME = time.time()  # When was the handleButtonPress was last cleared
    CHECK_PRESS_THRESHOLD_SEC = 4  # Threshold for what qualifies as a long press and limit to the length of time in the interrupt routine
    DISPLAY_TIMEOUT_SECS = 120     #screen on time before auto off

    def __init__(self, hat_class, display_class):

        self.display = display_class
        self.hat = hat_class
        self.display_type = display_class.display_type
        self.USABLE_BUTTONS = self.hat.USABLE_BUTTONS
        self.command_to_reference = ''
        self.l = []
        NoMountOrig = 0

    def checkReturn(self, val):
        fp = open('/usr/local/connectbox/brand.j2', "r", encoding='utf-8')
        brand = json.load(fp)
        fp.close()
        NoMountOrig = (brand['usb0NoMount'])
        brand['usb0NoMount'] = val
        fp = open('/usr/local/connectbox/brand.j2', "w", encoding='utf-8')
        json.dump(brand, fp, indent = 4, sort_keys = False)
        try:
            fp.close()

        except:
            print("Couldn't write brand.j2 out")
            print("Error couldn't write brand.j2 out")
        time.sleep(4)		#sleep to allow PxUSBm to catch up
        return(NoMountOrig)


    # pylint: disable=too-many-branches, too-many-branches, too-many-return-statements, too-many-statements
    def executeCommands(self, command):
        '''
         :This is where we will actually be executing the commands
         :param command: the command we want to execute
         :return: Nothing
        '''

        ext = "/content/"

        if not (self.hat.batteryLevelAboveVoltage(self.hat.BATTERY_WARNING_VOLTAGE)):
            return  # If low battery, we can't do admin functions as we may run out of power.

        print("Execute Command: %s", command)


#####################################################################################################
# REMOVE USB
#####################################################################################################

        if command == 'remove_usb':
            logging.debug("In remove usb page")
            os.sync()
            globals.a = "Remove USB"
            x = 1
            while x > 0:
                try:
                    fp = open(comsFileName, "w", encoding="utf-8")
                    fp.write(globals.a)
                    fp.close()
                    x = 0
                except: 
                    x = 1
            fp.close()
            while (usb.isUsbPresent() != ""):     #check  to see if usb is inserted
                logging.debug("USB still present")
                self.display.showRemoveUsbPage()  # tell them to remove it if so
                self.display.pageStack = 'remove_usb'  # let handleButtonPress know to repeat
                time.sleep(2)
            logging.debug("USB removed")
            self.display.pageStack = 'success'  # let out handleButtonPress know
            self.display.showSuccessPage()  # display our success page
            time.sleep(3) # allow PxUSBm to catch up
            globals.a = ""
            while os.path.isfile(comsFileName):
                os.remove(comsFileName)
                time.sleep(2)



###################################################################################################$#
# COPY From USB
#####################################################################################################

        elif command == 'copy_from_usb':
            print("copy from USB")
            NoMountOrig = self.checkReturn("1")		#Set usb0NoMount to 1
            os.sync()
            time.sleep(3)				# allow PxUSBm to catch up


            c = usb.getUSB(1)			#Get the first USB entry
            if (c == ""):  # check to see if usb is inserted
                self.display.pageStack = 'insertUSB'
                self.display.showInsertUsbPage()
                while (usb.isUsbPresent() == ""):
                    time.sleep(2)
                time.sleep(3)			#make sure we catch up on screen
                x = 1
                globals.a = "Checking Mounts"
                while x > 0:
                    try:
                        fp = open(comsFileName, "w", encoding="utf-8")
                        fp.write(globals.a)
                        fp.close()
                        x = 0
                    except: 
                        x = 1
                fp.close()
            c = usb.getUSB(1)
            dev = usb.isUsbPresent('/dev/'+ c)
            print("Using location " +str(dev) + " as media copy location")
            x = 1
            while x > 0:
                try:
                    fp = open(comsFileName, "w", encoding="utf-8")
                    fp.write(globals.a)
                    fp.close()
                    x = 0
                except: 
                    x = 1
            fp.close()
            mnt = usb.getMount(dev)
            print("mounting location is: " + mnt)
            if mnt == '/media/usb0':
                print("Moving /media/usb0 to /media/usb11 to be able to copy")
                if not os.path.exists('/media/usb11'):  # check that usb11 exists to be able to move the mount
                    os.mkdir('/media/usb11')  # make the directory
                if not usb.moveMount(mnt, '/media/usb11') == 0:  # see if our remount was successful
                    self.display.pageStack = 'error'
                    self.display.showErrorPage("Moving Mount")  # if not generate error page and exit
                    print("move of " + mnt + " to usb11 failed")
                    self.checkReturn( NoMountOrig)
                    time.sleep(3) # make sure we let the dsipaly catch up.
                    while os.path.isfile(comsFileName):
                        os.remove(comsFileName)
                    return False
                else:
                    mounts = str(subprocess.check_output(['df']))
                    if not ("/media/usb11" in mounts):
                        print("post mount shows that the mount didn't finish correctly")
                        os.system("rm "+comsFileName)
                    while os.path.isfile(comsFileName):
                        os.remove(comsFileName)
                        time.sleep(3)  # Let the display catch up
                        return False
                    print("move mount completed correctly and we're good to go")
                    mnt = "/media/usb11"
            else:
                print("We are not mounted on /media/usb0")
                print("Starting to find the mount point for: " + dev)
                mnt = usb.getMount(dev)
                print("mount is not USB0 but is: " + mnt)
                if mnt == "":
                    x = 11
                    print("we were not mounted as /media/usb0 and we were supposed to be mounted but are not")
                    while (not(os.path.exists("/media/usb" + str(x))) and (x >= 1)):
                        x -= 1
                    mnt = "/media/usb" + str(x)
                    if not os.path.exists(mnt):
                        os.mkdir(mnt)
                    if usb.mount(dev, mnt):
                        print("mounted USB device as " + mnt + " since it wasn't mounted")

            print("Preparing to check space of source " + mnt)

            self.pageStack = 'checkSpace'  # Don't allow the display to turn off
            globals.sequence = 0
            self.display.pageStack = 'wait'
            globals.a = "Checking Space"
            f = open(comsFileName, "w", encoding="utf-8")
            f.write(globals.a)
            f.close()
            self.display.showWaitPage(globals.a)
            time.sleep(3)   #let mmLoader andd PxUSBm catch up.
            if os.path.exists("/media/usb0" + ext):
                print("Destination path already exists, erasing before copy")
                try:
                    x = shutil.rmtree("/media/usb0" + ext)
                except:
                    pass

            (d, s) = usb.checkSpace(mnt,'/media/usb0')  # verify that source is smaller than destination
            print("Space of Destination is: " + str(d) + ", Source: " + str(s) + " at: " + mnt)
            if d < s or s == 0:  # if destination free is less than source we don't have enough space
                if d < s:
                    print("source exceeds destination at" + dev + ext)
                else:
                    print("source is 0 bytes in length so nothing to copy")
                if usb.isUsbPresent(dev) != "":
                    self.display.showRemoveUsbPage()  # show the remove usb page
                    self.display.pageStack = 'remove_usb'  # show we removed the usb key
                    self.command_to_reference = 'remove_usb'
                    while usb.isUsbPresent(dev) != "":
                        time.sleep(3)  # Wait for the key to be removed
                    self.display.pageStack = "success"
                    self.display.showSuccessPage()
                    print("success on removing USB key!")
                    self.checkReturn( NoMountOrig)
                    while os.path.isfile(comsFileName):
                        os.remove(comsFileName)
                    return(False)
            else:
                print("Space of Destination is ok for source to copy to " + dev + ext)
                # we think we have keys to work with if we go forward from here. where the size is ok for the copy
                print("There is enough space so we will go forward with the copy")
                print("starting to do the copy with device " + mnt + ext)
                globals.sequence = 0
                globals.a = ("Copying Files\nSize:" + str(int(s / 1000000)) + "MB")
                f = open(comsFileName, "w", encoding="utf-8")
                f.write(globals.a)
                f.close()
                self.display.showWaitPage(globals.a)
                if usb.copyFiles(mnt, "/media/usb0", ext) > 0:  # see if we copied successfully
                    print("failed the copy. display an error page")
                    hat.displayPowerOffTime = time.time() + self.DISPLAY_TIMEOUT_SECS
                    self.display.showErrorPage("Failed Copy")  # if not generate error page and exit
                    self.display.pageStack = 'error'
                    self.checkReturn( NoMountOrig)
                    os.system("rm "+comsFileName)
                    while os.path.isfile(comsFileName):
                        os.remove(comsFileName)
                    return(False)
                else:
                    pass  # we have finished the copy so we want to unmount the media/usb11 and run on the internal
                print("Ok were going to clean up now")
                os.sync()
                usb.unmount(mnt)  # unmount the key
                while os.path.isfile(comsFileName):
                    os.system("rm "+comsFileName)
                time.sleep(2)

                z = ord('a')
                curDev = '/dev/sda1'

                hat.displayPowerOffTime = sys.maxsize
                self.display.pageStack = 'remove_usb'  # show we removed the usb key
                self.display.showRemoveUsbPage()  # show the remove usb page

                while z < ord("k"):
                    if usb.isUsbPresent(curDev) != "":
                        z -= 1    # lets make sure we keep looking at this one
                        if usb.getMount(curDev) != "":
                            try:
                                usb.umount(usb.getMount(curDev))
                                usb.umount(curDev)
                            except:
                                pass
                    z += 1  # lets look at the next one
                    curDev = '/dev/sd/'+chr(z)+"1"

            time.sleep(2)

            # We finished the umounts
            self.display.pageStack = 'success'
            self.display.showSuccessPage()
            hat.displayPowerOffTime = time.time() + self.DISPLAY_TIMEOUT_SECS
            logging.debug("succes page now restoring the Usb0NoMount flag")
            self.checkReturn( NoMountOrig)
            os.system("rm "+comsFileName)
            while os.path.isfile(comsFileName):
                os.remove(comsFileName)
            time.sleep(3)
            os.system("/usr/bin/python3 /usr/local/connectbox/bin/mmiLoader.py >/tmp/loadContent.log 2>&1 &")
            return (0)

#######################################################################################################
# erase folder
#######################################################################################################

        elif command == 'erase_folder':

            ext = "/content/"

            file_exists = False  # in regards to README.txt file
            if (usb.isUsbPresent() != ""):
                hat.displayPowerOffTime = sys.maxsize
                self.display.showRemoveUsbPage()                    #show the remove usb page
                self.display.pageStack = 'remove_usb'                #show we removed the usb key
                self.command_to_reference = 'remove_usb'
                dev = usb.getUSB(1)
                if (dev != ""): subprocess.Popen('umount '+dev, shell=False)
                while (usb.isUsbPresent() != ""):
                    time.sleep(3)                                       #Wait for the key to be removed
                self.display.pageStack= "success"
                self.display.showSuccessPage()
                print("succes on removing USB key before erase!")
                hat.displayPowerOffTime = time.time() + self.DISPLAY_TIMEOUT_SECS

            for file_object in os.listdir('/media/usb0'+ext):
                file_object_path = os.path.join('/media/usb0'+ext, file_object)
                if os.path.isfile(file_object_path):
                    os.unlink(file_object_path)
                else:
                    shutil.rmtree(file_object_path)
            logging.debug("FILES NUKED!!!")

            self.display.pageStack = 'success'
            self.display.showSuccessPage()
            time.sleep(3)
            os.system("/usr/bin/python3 /usr/local/connectbox/bin/mmiLoader.py >/tmp/loadContent.log 2>&1 &")

########################################################################################################
# COPY TO USB
########################################################################################################

        elif command == 'copy_to_usb':
            logging.debug("got to copy to usb code")
            #get the value of usb0NoMount and save it and set it
            try:
               if os.path.exists('/usr/local/connectbox/brand.j2'):
                   with open('/usr/local/connectbox/brand.j2', "r+") as fp:
                      try:
                          m = json.load(fp)
                          fp.close()
                          NoMountOrig = m.get("usb0NoMount", 0) # get the original value, default to 0 if not present
                      except json.JSONDecodeError:
                          print(f"Error: Invalid JSON in {filepath}")
                          m = {}
                   if m.get("usb0NoMount") != 0:
                       m["usb0NoMount"] = 0
                       with open("/usr/local/connectbox.brand.j2","w") as fp:
                            fp.seek(0)
                            json.dump(m, fp)
                            fp.truncate()
                            fp.close()
               else:
                   print("Error: File not found at {filepath}")
                   self.checkReturn( NoMountOrig)
                   return(1)
            except Exception as e:
                 print("An unexpected error occurred: {e}")
                 # Consider logging the error or taking other appropriate action
                 self.checkReturn( NoMountOrig)
                 return(1)

            z = ord("a")
            dev = '/dev/sd'+chr(z)+'1'
            while (usb.isUsbPresent(dev)== "") and (z <= (ord('a')+10)):
                z +=1
                dev = '/dev/sd'+chr(z)+"1"
            if not(z < (ord('a')+10)):						#going to find if we have any keys loaded
                hat.displayPowerOffTime = sys.maxsize
                self.display.pageStack = 'insertUSB'
                self.display.showInsertUsbPage()
                z = ord("a")
                dev = '/dev/sd'+chr(z)+"1"
                while (usb.isUsbPresent(dev) == ""):                         # only checks for one USB key
                    z += 1
                    if z > (ord('a')+10):
                        z = ord('a')
                    dev = '/dev/sd'+chr(z)+"1"
		#ok we found a key inserted
                z = ord("a")
                dev = '/dev/sd'+chr(z)+'1'
                while (usb.isUsbPresent(dev)== "") and (z <= (ord('a')+10)):
                    z +=1
                    dev = '/dev/sd'+chr(z)+"1"
            if z > (ord('a')+10):
                self.checkReturn( NoMountOrig)
                return(1)

            hat.displayPowerOffTime = time.time() + self.DISPLAY_TIMEOUT_SECS
            print("Found USB key at "+dev)
            hat.displayPowerOffTime = sys.maxsize
            self.display.pageStack = 'wait'
            globals.sequence = 0
            globals.a = "Checking Sizes"
            f = open(comsFileName, "w", encoding="utf-8")
            f.write(globals.a)
            f.close()
            self.display.showWaitPage(globals.a)
            logging.debug("we have found at least one usb to copy to: "+dev)

            mnt = usb.getMount(dev)
            print("found mount of "+str(mnt))
            if (mnt == '/media/usb0') or (mnt == ""):                                # if the key is mounted on '/media/usb0' then we have to move it.
                if (mnt == ""):			#We dont have a mount point
                    print("mount is null so we need to mount")
                    if not os.path.exists("/media/usb11"):
                        os.mkdir("/media/usb11")
                        print(" made directory usb11")
                    try:
                        if usb.mount(dev,'/media/usb11'):
                            print("we did the mount on /media/usb11")
                            mnt = "/media/usb11"
                        else:
                            print("Mount of "+dev+" Failed")
                            while os.path.isfile(comsFileName):
                                os.remove(comsFileName)
                            return(1)
                    except:
                        self.display.showErrorPage("USB not mounted")
                        self.display.pageStack = 'error'
                        hat.displayPowerOffTime = time.time() + self.DISPLAY_TIMEOUT_SECS
                        os.system("rm "+comsFileName)
                        self.checkReturn( NoMountOrig)
                        while os.path.isfile(comsFileName):
                            os.remove(comsFileName)
                        return(1)
                else:
                    print("Moving "+ dev+ " to /media/usb11 be able to copy")
                    if not os.path.exists('/media/usb11'):                              # check that usb11 exists to be able to move the mount
                        os.mkdir('/media/usb11')                                        # make the directory
                    x = usb.moveMount(mnt, '/media/usb11')                              # see if our remount was successful
                    if x != 0:
                            self.display.showErrorPage("Moving Mount")                  # if not generate error page and exit
                            self.display.pageStack = 'error'
                            os.rmdir("/media/usb11")
                            self.checkReturn( NoMountOrig)
                            hat.displayPowerOffTime = time.time() + self.DISPLAY_TIMEOUT_SECS
                            os.system("rm "+comsFileName)
                            self.checkReturn( NoMountOrig)
                            while os.path.isfile(comsFileName):
                                os.remove(comsFileName)
                            return(1)
                    else:
 
                        if getDev("/media/usb11") == "":
                            self.display.showErrorPage("USB not mounted")               # if not generate error page and exit
                            self.display.pageStack = 'error'
                            self.checkReturn( NoMountOrig)
                            hat.displayPowerOffTime = time.time() + self.DISPLAY_TIMEOUT_SECS
                            os.system("rm "+comsFileName)
                            self.checkReturn( NoMountOrig)
                            return(1)
            else:
                mnt = usb.getMount(dev)
                if (mnt == "") or (mnt=="/media/usb0"):
                    os.remove(comsFileName)
                    self.checkReturn( NoMountOrig)
                    while os.path.isfile(comsFileName):
                        os.remove(comsFileName)
                    return(1)

            print("We are getting the size for source: /media/usb0 and destination: " + str(mnt))
            if os.path.isdir(mnt):
                try:
                    shutil.rmtree((mnt+ext), ignore_errors=True)                        #remove old data from /source/ directory
                except OSError:
                    print("had a problem deleting the destination file: ",+ext)
                    self.display.showErrorPage("failed deletion")
                    self.display.pageStack = 'error'
                    self.checkReturn( NoMountOrig)
                    hat.displayPowerOffTime = time.time() + self.DISPLAY_TIMEOUT_SECS
                    os.system("rm "+comsFileName)
                    self.checkReturn( NoMountOrig)
                    while os.path.isfile(comsFileName):
                        os.remove(comsFileName)
                    return(1)
            print("going to check space on the usb and sd card")
            (d, s) = usb.checkSpace('/media/usb0', mnt)  # verify that source is smaller than destination
            print("Space of Destination is: " + str(d) + ", Source: " + str(s) + " from: " + mnt)
            if ((d < s) or (s==0)):  # if destination free is less than source we don't hav
                if d < s:
                    print("source exceeds destination at" + dev + ext)
                elif (s == 0):
                    print("source is 0 bytes in length so nothing to copy")
                    os.system("rm "+comsFileName)
                    if usb.isUsbPresent(dev) != "":
                        hat.displayPowerOffTime = sys.maxsize
                        self.display.showRemoveUsbPage()  # show the remove usb page
                        self.display.pageStack = 'remove_usb'  # show we removed the usb key
                        self.command_to_reference = 'remove_usb'
                        while usb.isUsbPresent(dev) != "":
                            time.sleep(3)  # Wait for the key to be removed
                        self.display.pageStack = "success"
                        self.display.showSuccessPage()
                        print("success on removing USB key!")
                        self.checkReturn( NoMountOrig)
                        hat.displayPowerOffTime = time.time() + self.DISPLAY_TIMEOUT_SECS
                        self.checkReturn( NoMountOrig)
                    while os.path.isfile(comsFileName):
                        os.remove(comsFileName)
                    return(1)
            else:
                print("Space of Destination is ok for source to copy to " + dev + ext)
                # we think we have keys to work with if we go forward from here. where the size is ok for the copy
                print("There is enough space so we will go forward with the copy")
                print("starting to do the copy with device " + mnt + ext)
                hat.displayPowerOffTime = sys.maxsize
                globals.sequence = 0
                globals.a = ("Copying Files\nSize:" + str(int(s / 1000000)) + "MB")
                f = open(comsFileName, "w", encoding="utf-8")
                f.write(globals.a)
                f.close()
                self.display.showWaitPage(globals.a)
                if usb.copyFiles("/media/usb0", mnt, ext) > 0:  # see if we copied successfully
                    print("failed the copy. display an error page")
                    hat.displayPowerOffTime = sys.maxsize
                    self.display.showErrorPage("Failed Copy")  # if not generate error page and exit
                    self.display.pageStack = 'error'
                    time.sleep(self.DISPLAY_TIMEOUT_SECS)
                    self.display.showRemoveUsbPage()
                    self.display.pageStack = 'remove_usb'
                    while usb.getMount(dev) != False:
                        time.sleep(2)
                    print("we don't know the state of the mount so we just leave it")
                    self.checkReturn( NoMountOrig)
                    hat.displayPowerOffTime = time.time() + self.DISPLAY_TIMEOUT_SECS
                    os.system("rm "+comsFileName)
                    self.checkReturn( NoMountOrig)
                    while os.path.isfile(comsFileName):
                        os.remove(comsFileName)
                    return(1)
                else:
                    pass  # we have finished the copy so we want to unmount the media/usb11 and run on the internal
                print("Ok were going to clean up now")
                os.sync()
                usb.unmount(mnt)  # unmount the key
                while os.path.isfile(comsFileName):
                    os.system("rm "+comsFileName)
                time.sleep(2)
                hat.displayPowerOffTime = sys.maxsize
                self.display.pageStack = 'remove_usb'  # show we removed the usb key
                self.display.showRemoveUsbPage()  # show the remove usb page
                z = ord('a')
                curDev = '/dev/sda1'
                while z < ord("k"):
                    if usb.isUsbPresent(curDev) != "":
                        z -= 1       # make sure we stay on this key
                        if usb.getMount(curDev) != "":
                            try:
                                usb.umount(usb.getMount(curDev))
                                usb.umount(curDev)
                            except:
                                pass
                    z += 1  # lets look at the next one
                    curDev = '/dev/sd' + chr(z) + '1'  # create the next curdev

            # We finished the umounts
            time.sleep(2)
            self.display.pageStack = 'success'
            self.display.showSuccessPage()
            logging.debug("successss page now restoring the Usb0NoMount flag")
            hat.displayPowerOffTime = time.time() + self.DISPLAY_TIMEOUT_SECS
            self.checkReturn( NoMountOrig)
            os.system("rm "+comsFileName)
            while os.path.isfile(comsFileName):
                os.remove(comsFileName)
            return 0

###########################################################################################################
# Button Presses go here from the interrupt handler
##########################################################################################################


    def handleButtonPress(self, channel):
        '''
        The method was created to handle the button press event.  It will get the time buttons
        pressed and then, based upon other criteria, decide how to control further events.

        :param channel: The pin number that has been pressed and thus is registering a 0
        :return: nothing

        '''

        # For OPi.GPIO, it turns out that the state of the button can be read without
        #  killing the event detect!

        print("we have a button press on channel "+ str(channel))

        print("we had a button press")
        if self.display_type == 'DummyDisplay':                                           # this device has no buttons or display, skip
            return

        # this section is to prevent both buttons calling this method and getting two replies
        if self.BUTTON_PRESS_BUSY:  # if flag is set that means this method is currently being used
            print("skipping button press - BUSY flag")
            return  # skip

        # check the amount of time that has passed since this function has been cleared and
        #  see if it exceeds the timeout set.  This avoids buttons bouncing triggering
        #  this function
        if time.time() - self.BUTTON_PRESS_CLEARED_TIME > self.BUTTON_PRESS_TIMEOUT_SEC:
            self.BUTTON_PRESS_BUSY = True                                                 # if enough time, proceed and set the BUSY flag

        else:  # if not enough time, pass
            logging.debug("return from time.time - self.button_press_cleared_time")
            return

        logging.debug("Handling button press")
        # get time single button was pressed along with the amount of time both buttons were pressed

        print("just before check press time")


        channelTime, dualTime = self.checkPressTime(channel)

        logging.debug("time stamp for channel Time line 524: %s", channelTime)
        logging.debug("time stamp for dualTime line 525: %s", dualTime)

        # clear the CHECK_PRESS_BUSY flag
        self.BUTTON_PRESS_BUSY = False

        # reset the CHECK_PRESS_CLEARED_TIME to now
        self.BUTTON_PRESS_CLEARED_TIME = time.time()

        pageStack = self.display.pageStack  # shortcut
        print ("PAGESTACK: %s", pageStack)
        print ("COMMAND: %s", self.command_to_reference)

        # this is where we decide what to do with the button press.  ChanelTime is the first
        # button pushed, dualTime is the amount of time both buttons were pushed.
        if channelTime < .1:  # Ignore noise
            pass

        # if either button is below the press threshold, treat as normal
        elif channelTime < (self.CHECK_PRESS_THRESHOLD_SEC ) or \
                dualTime < (self.CHECK_PRESS_THRESHOLD_SEC ):
            print("hit self.check_press_threshold_sec line 655")
            if channel == self.USABLE_BUTTONS[0]:                                           # this is the left button
                print("Left button: pageStack ="+str(pageStack))
                if pageStack in ['success']:                # return to 1st page of admin stack
                    self.moveToStartPage(channel)
                elif pageStack in ['confirm', 'error', 'error_no_space', 'error_no_space2']:     # return to first page admin stack
                    self.display.pageStack = 'admin'
                    self.chooseCancel(pageStack)
                elif pageStack in ['remove_usb']:            # never reach here... loops elsewhere until they remove the USB stick
                    self.chooseEnter(pageStack)
                else:                                       # anything else, we treat as a moveForward (default) function
                    self.moveForward(channel)
            else:                                                                           # right button
                print("Right button: pageStack ="+str(pageStack))
                if pageStack in ['success']:                # return to 1st page of admin stack
                    self.moveToStartPage(channel)
                elif pageStack == 'status':                 # standard behavior - status stack
                    self.moveBackward(channel)
                elif pageStack in ['error']:                # both conditions return to admin stack
                    self.chooseCancel(pageStack)
                else:                                       # this is an enter key in the admin stack
                    self.chooseEnter(pageStack)

        # if we have a long press (both are equal or greater than threshold) call switch pages
        elif channelTime >= self.CHECK_PRESS_THRESHOLD_SEC or \
                dualTime >= self.CHECK_PRESS_THRESHOLD_SEC :
            print("hats 576 hit dual button press time, move forward admin")
            print("hats 576 hit dual button press time, move forward admin",channelTime,dualTime)
            self.switchPages()


    def checkPressTime(self, channel):
        print("top of checkPressTime")

        '''
        This method checks for a long double press of the buttons.  Previously, we only
        had to deal with a single press of a single button.

        This method requires two pins which are contained in the USABLE_BUTTONS list constant.
        This was necessary because different HATs use different pins.  This list will be used
        for two things.  One, to determine which is the non-button pressed, this is done by
        comparing the channel passed in to the first item in the list.  If it is not the first
        item, it must be the second.  Two, if there is no double long press, then the
          information is used to decide which method applies to which pin.  The first item in the
          list is the left button, the second item is the second button.

         If there is a double long press, we call a swapPages method.

        :param channel: The pin number that has been pressed and thus is registering a 0
        :return: time original button pressed, time both buttons were pressed

       '''

        # otherChannel is the button that has not been passed in by the channel parameter.
        otherChannel = self.USABLE_BUTTONS[0] if channel == self.USABLE_BUTTONS[1] else \
            self.USABLE_BUTTONS[1]

        print("channel = "+str(channel) +"    and otherChannel = " +str(otherChannel))

        # NEO ONLY
        # Temporarily turn off the push button interrupt handler
        #   and turn on the push button pins as regular inputs
        # Note that this is a specific case of buttons being on PG6 and PG7... 
        #  If another implementation is made for NEO, this will need updating.
        if (globals.device_type == "NEO"):
            cmd = "devmem2 0x01c208d8 w 0x00777777 >/dev/null"
            os.popen(cmd).read()
#            print("done with removing NEO event detects")

        # there are two timers here.  One is for total time the original button was pushed.
        # The second is for when the second button was pushed.  The timer gets restarted if
        # the button is not pressed or is released.  The reason for the recorder is that if
        # it is not kept, then when you let off the second button it will bounce and give a
        # false reading.  Here we keep the highest consecutive time it was pushed.
        startTime = time.time()                                                                 # time original button is pushed
        dualStartTime = time.time()                                                             # time both buttons were pushed.
        dualTimeRecorded = 0                                                                    # to prevent time being reset when letting off of buttons

        while GPIO.input(channel) == 0:                                                         # While original button is being pressed
            if GPIO.input(otherChannel) == 0:                                                   # capture hold time if 2nd button down
                dualButtonTime = time.time() - dualStartTime                                    # How long were both buttons down?
                if dualButtonTime > dualTimeRecorded:
                    dualTimeRecorded = dualButtonTime
            if GPIO.input(otherChannel) == 1:                                                   # move start time up if not pressing other button
                dualStartTime = time.time()                                                     # reset start time to now
            if (time.time() - startTime) > (self.CHECK_PRESS_THRESHOLD_SEC + 1):                # don't stick in this interrupt service forever
                break                                                                           # (note: CHECK_PRESS_THRESHOLD_SEC == 3)

        buttonTime = time.time() - startTime                                                    # How long was the original button down?

#        print(" finished timing buttons")
        print("    buttonTime = "+str(buttonTime)+ "dualTimeRecorded = "+str(dualTimeRecorded))

        # We are through with reading of the button states so turn interrupt handling back on
        if (globals.device_type == "NEO"):
            cmd = "devmem2 0x01c208d8 w 0x66777777 >/dev/null"
            os.popen(cmd).read()
            print("after NEO re-establish interrupts")

        if (dualTimeRecorded  >= self.CHECK_PRESS_THRESHOLD_SEC):
            return buttonTime, dualTimeRecorded

        elif (buttonTime <  self.CHECK_PRESS_THRESHOLD_SEC):
            return buttonTime, dualTimeRecorded

	# if we fall through then we have a single long button press so we shutdown
        print("we fell through the return from the button interrupt",buttonTime, dualTimeRecorded)
        self.hat.displayPowerOffTime = time.time() + self.DISPLAY_TIMEOUT_SECS
        self.hat.shutdownDevice()


    def chooseCancel(self, pageStack):
        """ method for use when cancelling a choice"""
        logging.debug("Choice cancelled")
#        self.command_to_reference = self.display.getAdminPageName()                             # really don't want to leave this one loaded
        if pageStack == 'confirm': pageStack= 'admin'
        self.display.moveForward()                                                              # drops back to the admin pages
        # reset the display power off time
        self.hat.displayPowerOffTime = time.time() + self.DISPLAY_TIMEOUT_SECS

    def chooseEnter(self, pageStack):
        """ method for use when enter selected"""
        logging.debug("Enter pressed.")
        if pageStack == 'admin':
            if self.display.checkIfLastPage():                                                  # if true, go back to admin pageStack
                self.display.switchPages()                                                      # swap to status pages
            else:
                                                                                                # find page name before we change it
                self.command_to_reference = self.display.getAdminPageName()
                logging.debug("Leaving admin page: %s",
                              self.command_to_reference)
                logging.debug("Confirmed Page shown")
                self.display.showConfirmPage()                  # pageStack now = 'confirm'
        else:
            logging.debug("Choice confirmed")
            print("choice confirmed command to reference: ",self.command_to_reference)
            globals.sequence = 0
#            self.display.showWaitPage()
#            self.display.pageStack = 'wait'
#            logging.debug("Waiting Page shown")
            self.executeCommands(self.command_to_reference)

        # reset the display power off time
        self.hat.displayPowerOffTime = time.time() + self.DISPLAY_TIMEOUT_SECS

    def switchPages(self):
        """method for use on button press to change display options"""
        logging.debug("You have now entered, the SwitchPages")
        self.display.switchPages()
        # reset the display power off time
        self.hat.displayPowerOffTime = time.time() + self.DISPLAY_TIMEOUT_SECS

    def moveToStartPage(self,channel):
        self.display.moveToStartPage()
        # reset the display power off time
        self.hat.displayPowerOffTime = time.time() + self.DISPLAY_TIMEOUT_SECS


    def moveForward(self, channel):
        """method for use on button press to cycle display"""
        logging.debug("Processing press on GPIO %s (move forward)", channel)
        self.display.moveForward()
        # reset the display power off time
        self.hat.displayPowerOffTime = time.time() + self.DISPLAY_TIMEOUT_SECS

    def moveBackward(self, channel):
        """method for use on button press to cycle display"""
        logging.debug("Processing press on GPIO %s (move backward)", channel)
        self.display.moveBackward()
        # reset the display power off time
        self.hat.displayPowerOffTime = time.time() + self.DISPLAY_TIMEOUT_SECS
