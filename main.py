import datetime

user_name       = input("What's your name ? : ")
time_input = input("Enter study time (e.g., 19:35): ")

# 2. قسم الـ string على النقطة
parts = time_input.split(':')
hour = int(parts[0])   # خذ الساعة
minute = int(parts[1]) # خذ الدقيقة

hours = input("Enter how many hours (e.g., 1:30): ")

# 2. قسم الـ string على النقطة
parts = time_input.split(':')
hour = int(parts[0])   # خذ الساعة
minute = int(parts[1]) # خذ الدقيقة

# 3. حولهم لـ float
now             = datetime.datetime.now()
current_time    = now.hour + (now.minute / 60)
end_time        = study_time + hours
is_study_time   = True

print(f"hi Mr.{user_name}! System checking... Current hour is: {current_time}")

if (study_time - 0.5) <= current_time < study_time and is_study_time:
    print("⚠️ Warning! Study time is starting in less than 30 minutes. Prepare yourself!")

elif study_time <= current_time < end_time and is_study_time:
    print("it's study time! 🚫 Blocking now...")

else:
    print("✅ Safe zone. Enjoy your time.") 
