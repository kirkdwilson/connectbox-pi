#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pexpect
import time
import logging
import logging.handlers
import re
import os
import sys

progress_file = '/usr/local/connectbox/expand_progress.txt'
connectbox_scroll = False
max_partition = 0
DEBUG = True

def Revision():
    revision = ""
    try:
        f = open('/proc/cpuinfo','r')
        for line in f:
            if 'Radxa CM3 IO' in line: revision = "RM3"
            elif "Revision" in line:
                x = line.find(":")
                y = len(line)-1
                revision = line[(x+2):y].strip()
        f.close()
        if len(revision) != 0:
            return revision
        else:
            process = os.popen("lshw -short")
            net_stats = process.read()
            process.close()
            version = "Unknown"
            x = net_stats.find("system")
            if x > 0:
                l = net_stats[x+6 :]
                y = l.find("\n")
                l = l[0:y].strip()
                if l in ["Orange Pi Zero2", "Orange Pi Zero 2", "OrangePi Zero2"]:
                    version = "OrangePiZero2"
                else:
                    version = l
            return version
    except:
        return "Error"

def do_resize2fs(rpi_platform, rm3_platform):
    global connectbox_scroll
    global max_partition
    if (rm3_platform == True):
      FS = "/dev/mmcblk1p"+str(max_partition)
    elif (rpi_platform == True):
      if connectbox_scroll == True:
         FS = "/dev/mmcblk0p"+str(max_partition)
      else:
        FS = "/dev/mmcblk0p2"
    else:
        FS = "/dev/mmcblk0p1"
    cmd = 'resize2fs ' + FS
    out = pexpect.run(cmd, timeout=600)
    out = out.decode('utf-8')
    if "blocks long" in out:
        print("resize2fs complete... now reboot")
        f = open(progress_file, "w")
        f.write("resize2fs_done")
        f.close()
        os.sync()
        os.system('shutdown -r now')

def do_fdisk(rpi_platform, rm3_platform):
    global connectbox_scroll
    global max_partition
    if not (rm3_platform):
      child = pexpect.spawn('fdisk /dev/mmcblk0', timeout = 10)
    else:
      child = pexpect.spawn('fdisk /dev/mmcblk1', timeout = 10)
    try:
      i = child.expect(['Command (m for help)*', 'No such file or directory'])
    except:
      pass
    if i==1:
        child.kill(0)
        if not (rm3_platform):
          child = pexpect.spawn("fdisk /dev/mmcblk1", timeout = 10)
          try:
            i = child.expect(['Command(m for help)*', 'No such file or directory'])
          except:
            pass
          if i==1:
            child.kill(0)
    if i==0:
        child.sendline('p')
        i = child.expect('Command (m for help)*')
        response = child.before
        respString = response.decode('utf-8')
        if respString.find("/dev/mmcblk0p5") >=0:
          connectbox_scroll = True
        else: 
          connectbox_scroll = False
        
        if rm3_platform == True:
            x = 2
            while  respString.find("/dev/mmcblk1p"+str(x))>=0:
              x += 1
            x = x -1
            max_partition = x
            p = re.compile('mmcblk[0-9]p'+str(x)+'\s*[0-9]+')
        else:
            x = 2
            while  respString.find("/dev/mmcblk0p"+str(x))>=0:
              x += 1
            x = x -1
            max_partition = x
            p = re.compile('mmcblk[0-9]p'+str(x)+'\s*[0-9]+')
            
        m = p.search(respString)
        match = m.group()
        p = re.compile('\s[0-9]+')
        m = p.search(match)
        startSector = m.group()
        
        child.sendline('d')
        if rpi_platform or rm3_platform:
            i = child.expect('Partition number')
            child.sendline(str(x))
        i = child.expect('Command (m for help)*')
        child.sendline('n')
        
        if rm3_platform:
          i = child.expect('default 2')
          child.sendline(str(x))
          i = child.expect('First sector')
        else:
          i = child.expect('(default p):*')
          child.sendline('p')
          if rpi_platform:
            i = child.expect('default 2*')
            child.sendline(str(x))
            i = child.expect('default 2048*')
          else:
              i = child.expect('default 1*')
              child.sendline('1')
              i = child.expect('default 2048*')
        child.sendline(startSector)
        child.sendline('\n')
        i = child.expect('signature*')
        child.sendline('N')
        i = child.expect('Command (m for help)*')
        child.sendline('w')
        i = child.expect('Syncing disks*')
        
        f = open(progress_file, "w")
        f.write("fdisk_done   maxp="+str(max_partition))
        f.close()
        os.sync()
        os.system('shutdown -r now')

if __name__ == "__main__":
    file_exists = os.path.exists(progress_file)
    if file_exists:
        f = open(progress_file, "r")
        progress = f.read()
        f.close()
        if "fdisk_done" not in progress:
            print("First boot expansion completely done. Exiting.")
            sys.exit(0)

    version = Revision()
    rpi_platform = False
    rm3_platform = False

    if version != "Unknown" and version != "Error":
        if "CM" in version or "PI" in version:
            rpi_platform = True
        if "RM3" in version or "Rock CM3" in version:
            rm3_platform = True

    if not file_exists:
        print("starting the fdisk operation for expansion")
        os.sync()
        do_fdisk(rpi_platform, rm3_platform)
    else:
        if "fdisk_done" in progress:
            maxp = progress.split("maxp=")
            if len(maxp) > 1:
                max_partition = maxp[1][0]
            print("starting the resize2fs to format full disk")
            os.sync()
            do_resize2fs(rpi_platform, rm3_platform)
