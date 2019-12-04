#!/usr/bin/python3
import re
import os
import sys
import argparse
import darknet_video
import visualize

'''
This program automates the mousetrackingsystem pipeline
Usage: $ python3 automate.py /home/pi/folder_to_crawl

'''


#checks if arguement passed is valid pseudo datetime regex
def isTimeStamp(folder_name):
    regex='[0-9]{4}-[0-9]{2}-[0-9]{2}_[0-9]{2}'
    if(re.search(regex, folder_name)):
            return True
    return False

#Check every folder in dir search for processed.json and videos folder. Different actions depending which is found
def main():
    print("Dir=", dir)
    print("DataDrive=", dataDrive)
    print("fullPAth=", fullPath)

    for folder in os.listdir(fullPath):
        print(folder)
        if isTimeStamp(folder): #This folder is a timestamp so check if it contains videos folder or processed.JSON
            print(folder, "is time stamp, recursing")
            if 'processed.json' in os.listdir(fullPath+"/"+folder):
                    if ('videos' in os.listdir(fullPath+"/"+folder)):
                        print("both json and videos folder found, nothing to do here") #If both are present do nothing
                    else:
                        print("no videos found but json present, run visualize here")
                        visualize.run(dataDrive, dir)

            else:
                print("no json found in folder run darknet",folder)
                darknet_video.run(dataDrive, dir)
        else:
            print(folder, "Not a timestamp, nothing to do")




if __name__ == '__main__':
    if not len(sys.argv) > 1:
        print("Please provide both the data drive and path to folder as seperate command line argument")
        sys.exit(1)

    if os.name == 'nt':
        #for windows
        dataDrive = sys.argv[1]
        dir = sys.argv[2]
        fullPath= dataDrive + ":" + dir


    else:
        dir=sys.argv[2]
        dataDrive = sys.argv[1]
        fullPath = dataDrive + "/" + dir

    main()
