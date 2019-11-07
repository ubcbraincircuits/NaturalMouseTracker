sudo kill -s 2 $(pgrep -f RFID_Reader.py | head -1)
# Auto restarts and clears cache and swap memory (Linux allocates poorly)
#sudo chmod +x killscript.sh
sleep 3
if [ $(pgrep -f RFID_Reader.py | wc -l) -gt 0 ];
then sudo reboot
fi
echo "ended succesfully"
echo 1 > /proc/sys/vm/drop_caches 
sudo /usr/bin/python3 /home/pi/MouseTrackingSystem/RFID_Reader.py
