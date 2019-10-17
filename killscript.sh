sudo kill -s 2 $(pgrep -f RFID_Reader.py)
# Auto restarts 
#sudo chmod +x killscript.sh
sudo /usr/bin/python3 /home/pi/MouseTrackingSystem/RFID_Reader.py
