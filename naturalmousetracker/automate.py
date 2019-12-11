#!/usr/bin/python3
import re
import os
import sys
import argparse
import getpass
#import multiprocessing as mp
import billiard as mp
import naturalmousetracker.tracking_pipeline.detect_mice as detect_mice
import naturalmousetracker.tracking_pipeline.crop_videos as crop_videos
import naturalmousetracker.tracking_pipeline.head_tail_label as dlc
import naturalmousetracker.tracking_pipeline.classify_behaviours as classify

'''
This program automates the mousetrackingsystem pipeline
Usage: $ python3 automate.py /home/pi/folder_to_crawl

'''



def isTimeStamp(folder_name):
    '''
    Checks if a folder is a valid timestamp

    '''
    regex='[0-9]{4}-[0-9]{2}-[0-9]{2}_[0-9]{2}'
    if(re.search(regex, folder_name)):
            return True
    return False


#Check every folder in dir search for processed.json and videos folder. Different actions depending which is found
def main(fullPath, configPath):

    '''
    Check every foldername and see if its a valid timestamp.
    if its a valid timestamp, crawl the directory looking for:
        A) processed.JSON
        b) videos folder
        c) processed_ht.JSON

    if A is not found, run detect_mice
    if B is not found, run crop_videos
    if C is not found, run DLC
    if all are found run classify
    '''
    host = "localhost"
    user = "admin"
    db = "tracking_behaviour"
    password = getpass.getpass(prompt= "Please enter the password for the database")
    print("fullPath=", fullPath)
    detect_folders = []
    crop_folders = []
    for folder in os.listdir(fullPath):
        print(folder)
        if isTimeStamp(folder): #This folder is a timestamp so check if it contains videos folder or processed.JSON
            print(folder, "is time stamp, recursing")
            if 'processed.json' not in os.listdir(fullPath+"/"+folder):
                print("no json found in folder run darknet",folder)
                detect_folders.append((fullPath, folder))
                # detect_mice.run(dataDrive, dir)
        else:
            print(folder, "Not a timestamp, nothing to do")
    detect_pool = mp.Pool(8)
    crop_pool = mp.Pool(4)
    print("detect folders:", detect_folders)
    detect_pool.starmap(detect_mice.run, detect_folders)
    detect_pool.close() #without this raises value error: pool is still running
    detect_pool.join()
    for folder in os.listdir(fullPath):
        print(folder)
        if isTimeStamp(folder): #This folder is a timestamp so check if it contains videos folder or processed.JSON
            print(folder, "is time stamp, recursing")
            if 'processed.json' in os.listdir(fullPath+"/"+folder):
                if ('videos' not in os.listdir(fullPath+"/"+folder)):
                    print("no videos found but json present, run crop_videos here")
                    crop_folders.append((fullPath, folder))
                    #crop_videos.run(dataDrive, dir)
    crop_pool.starmap(crop_videos.run, crop_folders)
    crop_pool.close() #Same as above
    crop_pool.join()
    for folder in os.listdir(fullPath):
        print(folder)
        if isTimeStamp(folder): #This folder is a timestamp so check if it contains videos folder or processed.JSON
            print(folder, "is time stamp, recursing")
            if 'processed_ht.json' not in os.listdir(fullPath+"/"+folder):
                if ('videos' in os.listdir(fullPath+"/"+folder)):
                    print("videos found and no ht json present, run DLC")
                    dlc.run(fullPath, folder, configPath)
                    #crop_videos.run(dataDrive, dir)

    classify_pool = mp.Pool(8)
    classify_folders = []
    for folder in os.listdir(fullPath):
        print(folder)
        if isTimeStamp(folder): #This folder is a timestamp so check if it contains videos folder or processed.JSON
            print(folder, "is time stamp, recursing")
            if 'processed_ht.json' in os.listdir(fullPath+"/"+folder):
                classify_folders.append((fullPath, folder, user, host, db, password))
    classify_pool.starmap(classify.run, classify_folders)




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

    main(fullPath)
