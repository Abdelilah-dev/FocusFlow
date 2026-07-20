#libraries
import time
from datetime import datetime
from plyer import notification
import platform
import os

if platform.system() == "Windows":
    hosts_path = os.path.join(os.environ['SystemRoot'], 'System32', 'drivers', 'etc', 'hosts')
else:
    hosts_path = "/etc/hosts"

#variables
now = datetime.now()
current_total_minutes     = (now.hour * 60) + now.minute

study_time                = input("Enter the study time (ex: 12:35 (HH:MM)) : ")
study_hours               = input("Enter the study hours (ex: 1:45 (HH:MM)) : ")

parts                     = study_time.split(":")
parts1                    = study_hours.split(":")

study_hour                = int(parts[0])
study_minute              = int(parts[1])

study_hour_hours          = int(parts1[0])
study_minute_hours        = int(parts1[1])

study_total_minutes       = (study_hour * 60) + study_minute
study_hours_total_minutes = ((study_hour_hours * 60) + study_minute_hours)
end_study_total_minutes   = study_total_minutes + study_hours_total_minutes
last_alert_minute         = -1

SITES_TO_BLOCK = [
    "www.youtube.com", "youtube.com",
    "www.facebook.com", "facebook.com",
    "www.instagram.com", "instagram.com",
    "www.tiktok.com", "tiktok.com",
    "www.twitter.com", "twitter.com",
    "www.snapchat.com", "snapchat.com"
]

#foctions
def is_study_time_active(current, start, end):
    return current >= start and current < end

def send_alert(message):
    try:
        notification.notify(title="FocusFlow", message=message, timeout=5)
    except Exception as e:
        print(f"Error: {e}")

def block_sites():
    with open(hosts_path, 'a', encoding='utf-8') as file:
        for site in SITES_TO_BLOCK:
            file.write(f"127.0.0.1 {site}\n")

def unblock_sites():
    with open(hosts_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        
    with open(hosts_path, 'w', encoding='utf-8') as file:
        for line in lines:
            if not any(site in line for site in SITES_TO_BLOCK):
                file.write(line)

is_blocking = False

print(f"FocusFlow running on: {platform.system()}")

#loops
while True:
    now = datetime.now()
    start_total_minutes = study_total_minutes
    current_minutes     = (now.hour * 60) + now.minute
    time_until_start    = start_total_minutes - current_minutes

    is_study_time    = is_study_time_active((now.hour * 60) + now.minute, study_total_minutes, end_study_total_minutes)

        #conditions
    if 0 < time_until_start <= 10:    
        if time_until_start % 3 == 0:
            if last_alert_minute != current_minutes:
                send_alert(f"Study starts in {time_until_start} minutes!")
            last_alert_minute = current_minutes

    if is_study_time:
        if not is_blocking:
            print("\n[!] Time to study! Blocking sites...")
            unblock_sites()
            block_sites() 
            is_blocking = True
        print(f"It's study time: {now.strftime('%H:%M')} - Focus mode ON!", end="\r")
    else:
        if is_blocking:
            print("\n[!] Study finished! Unblocking sites...")
            unblock_sites()
            is_blocking = False
        print(f"Not study time. Current time: {now.strftime('%H:%M')} enjoy.", end="\r")
        
    time.sleep(1)