sudo kill -s 2 $(pgrep -f RFID_Reader.py | head -1)
# Auto restarts and clears cache and swap memory (Linux allocates poorly)
#sudo chmod +x killscript.sh
echo 1 > /proc/sys/vm/drop_caches && swapoff -a  && dphys-swapfile swapon
sleep 3
sudo /usr/bin/python3 /home/pi/MouseTrackingSystem/RFID_Reader.py
