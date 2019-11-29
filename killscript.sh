sudo kill -s 2 $(pgrep -f record.py | head -1)
# Auto restarts and clears cache and swap memory (Linux allocates poorly)
#sudo chmod +x killscript.sh
sleep 2
if [ $(pgrep -f record.py | wc -l) -gt 0 ];
then sudo reboot
fi
echo "ended succesfully"
echo 1 > /proc/sys/vm/drop_caches
sudo umount /mnt/frameData
#sudo mv /mnt/frameData/* /home/pi/Desktop/frameData
sudo mount /dev/sda2
COUNTER=0
while [  $COUNTER -lt  3 ]; do
	sudo /usr/bin/python3 /home/pi/MouseTrackingSystem/record.py || { COUNTER=$((COUNTER+1));}
	if [  $COUNTER -lt 1 ];
		then break
	fi
	echo 'starting again'
	sudo umount /mnt/frameData
        sudo mv /mnt/frameData/* /home/pi/Desktop/frameData
        sudo mount /dev/sda2
done

#if program doesnt run proper , exit code of this shell is 1
#if the program get sig int and exits smoothly, exit code of this shell is 130
#if program runs till completion exit code of this shell is 0. (will not happen)
