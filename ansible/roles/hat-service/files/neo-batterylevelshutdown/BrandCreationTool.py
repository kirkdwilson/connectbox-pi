# Branding file creation tool
import io  
import json


# not that Enable_MassStorage of 1 will override g_device.  Additionally, both MassStorage and g_device are subject to otg : high, low, none

# Create the dictionary
details  = {'Brand':"Connectbox", \
        'enhancedInterfaceLogo" : 'connectbox_logo.png', \
        'Image':"", \
        'Font': '27', \
        'pos_x': '6', \
        'pos_y': '0', \
        'Device_type': "NEO", \
        "usb0NoMount": '0', \
        "lcd_pages_main": '1',\
        "lcd_pages_info": '1',\
        "lcd_pages_battery": '1',\
        "lcd_pages_multi_bat": '1',\
        "lcd_pages_stats_hour_one": '1',\
        "lcd_pages_stats_hour_two": '1',\
        "lcd_pages_stats_day_one": "1",\
        "lcd_pages_stats_day_two": "1",\
        "lcd_pages_stats_week_one": "1",\
        "lcd_pages_stats_week_two": "1",\
        "lcd_pages_stats_month_one": "1",\
        "lcd_pages_stats_month_two": "1",\
        "lcd_pages_admin": '0',\
        "Enable_MassStorage": "",\
        "g_device": "g_serial",\
        "otg": "none",\
        "server_url": "", \
        "server_authorization": "", \
        "server_sitename": "", \
        "server_siteadmin_name": "", \
        "server_siteadmin_email": "", \
        "server_siteadmin_phone": "", \
        "server_siteadmin_country": "" \
        }

# Write the dictionary
a = input("Device_type (NEO) ?: ")
details['Device_type'] = a
x = 3
while (x != 0 or X != 1):
    b = input("Enable lcd_pages_admin (0) ?:")
    x = int(b)
details["lcd_pages_admin"]= x


with io.open('/usr/local/connectbox/brand.j2', mode='w') as f:
    f.write(json.dumps(details))
    f.close()

with open('hostname', 'w') as f:
    f.write((details["Brand"]).lower()) 
    f.close()

