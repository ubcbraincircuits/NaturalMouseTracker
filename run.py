import naturalmousetracker.automate as auto
import naturalmousetracker.tracking_pipeline.detect_mice as detect_mice
import naturalmousetracker.tracking_pipeline.crop_videos as crop_videos
import naturalmousetracker.tracking_pipeline.head_tail_label as dlc
import naturalmousetracker.tracking_pipeline.classify_behaviours as classify

if __name__ == "__main__":
    action = None
    while action is None:
        action = input("What do you want to do?\n\
                1) Run the full pipeline\n\
                2) Run the tracker\n\
                3) Run the cropping\n\
                4) Run DeepLabCut\n\
                5) Run classification: ")
        try:
            action = int(action)
        except Exception as e:
            print("Please enter a valid number.")
            action = None
        if action > 5 or action < 1:
            print("Please enter a valid number.")
            action = None

    drive = input("Type in the full path to the folder containing your data.\n\
            For example, if your data is in Desktop/<date_time>, type in C:/Users/<user>/Desktop/: ")
    configPath = input("Type in the full path to the DeepLabCut configuration file: ")
    if action == 1:
        auto.main(drive, configPath)
    else:
        folder = input("Please enter the name of the folder containing your video data.\n\
         An example would be 1970-01-01_00-00.: ")
        if action == 2:
            detect_mice.run(drive, folder, showVid=True)
        elif action == 3:
            crop_videos.run(drive, folder)
        elif action == 4:
            dlc.run(drive, folder, configPath)
        else:
            host = "localhost"
            user = "admin"
            db = "tracking_behaviour"
            password = getpass.getpass(prompt= "Please enter the password for the database")
            classify.run(drive, folder, user, host, db, password)
