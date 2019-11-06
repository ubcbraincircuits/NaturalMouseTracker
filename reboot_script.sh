echo performance | sudo tee /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
echo performance | sudo tee /sys/devices/system/cpu/cpu1/cpufreq/scaling_governor
echo performance | sudo tee /sys/devices/system/cpu/cpu2/cpufreq/scaling_governor
echo performance | sudo tee /sys/devices/system/cpu/cpu3/cpufreq/scaling_governor
sleep 10
sudo /usr/bin/python3 /home/pi/MouseTrackingSystem/RFID_Reader.py


