import streamlit as st
import cv2
import cvlib as cv
import threading
import time
from cvlib.object_detection import detect_common_objects
from moviepy.editor import VideoFileClip

def Light(dir,cols1, cols2, cols3):
    if dir == 'North':
        sig=['Images/greenN.png','Images/redW.png','Images/redE.png','Images/redS.png']
    if dir == 'West':
        sig=['Images/redN.png','Images/greenW.png','Images/redE.png','Images/redS.png']
    if dir == 'East':
        sig=['Images/redN.png','Images/redW.png','Images/greenE.png','Images/redS.png']
    if dir == 'South':
        sig=['Images/redN.png','Images/redW.png','Images/redE.png','Images/greenS.png']
    for i, img in enumerate(sig):
        if i == 0:
            cols3[2].image(img, width=80)
        elif i == 1:
            cols1[2].image(img, width=100)
        elif i == 2:
            cols3[0].image(img, width=100)
        else:
            cols1[0].image(img, width=80)

class VideoProcessor(threading.Thread):
    def __init__(self, video_path, side):
        super().__init__()
        self.video_path = video_path
        self.side = side
        self.car_count = 0
        self.stop_event = threading.Event()

    def run(self):
        global k
        clip=VideoFileClip(self.video_path)
        cap=clip.subclip(k,k+10)
        frame_count=0

        for frame in cap.iter_frames():
            if(frame_count%25==0):
                bbox, label, conf = cv.detect_common_objects(frame, confidence=0.25, model='yolov3-tiny')            
                self.car_count += label.count('car')+label.count('truck')+label.count('motorcycle')+label.count('bus')
            frame_count+=1

        clip.close()

    def stop(self):
        self.stop_event.set()

def main():
    global k
    st.title("Smart Traffic Management System")

    video_paths = [ "Images/rushS.mp4", "Images/vehicle.mp4", "Images/rush.mp4", "Images/surveillance.m4v"]
    sides = ["North", "West", "East", "South"]

    if len(video_paths) != len(sides):
        st.error("Number of video paths and sides should be the same.")
        return
    # Display videos
    cols1, cols2, cols3 = st.columns(3), st.columns(3), st.columns(3)

    for i, video_path in enumerate(video_paths):
        if i == 0:
            cols1[1].video(video_path)
        elif i == 1:
            cols2[0].video(video_path)
        elif i == 2:
            cols2[2].video(video_path)
        else:
            cols3[1].video(video_path)
    

    if len(video_paths) != len(sides):
        st.error("Number of video paths and sides should be the same.")
        return
    p1,p2,p3,p4=st.empty(),st.empty(),st.empty(),st.empty()        

    for _ in range(4):  # Run for 40 seconds with light adjustment every 10 seconds
        # Create VideoProcessor instances for each video
        k=_*10
        
        car_counts = [0,0,0,0]
        video_processors = [VideoProcessor(video_path, side) for video_path, side in zip(video_paths, sides)]
        for video_processor in video_processors:
            video_processor.start()

        time.sleep(10)  # Wait for 10 seconds
        image_visible = False
        p1.empty()
        p2.empty()
        p3.empty()
        p4.empty()

        # Stop all VideoProcessor instances
        for video_processor in video_processors:
            video_processor.stop()

        # Wait for all threads to finish
        for video_processor in video_processors:
            video_processor.join()

        # Get car counts from all video processors
        car_counts = [video_processor.car_count for video_processor in video_processors]
        print(car_counts)

        # Determine the side with the most traffic
        most_traffic_index = car_counts.index(max(car_counts))

        st.write("{} side has the most traffic.".format(sides[most_traffic_index]))
        st.write("Adjusting traffic lights accordingly...")
        dir=sides[most_traffic_index]
        image_visible=True
        # Function call for Trafic lights
        if dir == 'North':
            sig=['Images/greenN.png','Images/redW.png','Images/redE.png','Images/redS.png']
        if dir == 'West':
            sig=['Images/redN.png','Images/greenW.png','Images/redE.png','Images/redS.png']
        if dir == 'East':
            sig=['Images/redN.png','Images/redW.png','Images/greenE.png','Images/redS.png']
        if dir == 'South':
            sig=['Images/redN.png','Images/redW.png','Images/redE.png','Images/greenS.png']
        for i, img in enumerate(sig):
            if i == 0:
                p1=cols3[2].image(img, width=80)
            elif i == 1:
                p2=cols1[2].image(img, width=100)
            elif i == 2:
                p3=cols3[0].image(img, width=100)
            else:
                p4=cols1[0].image(img, width=80)

if __name__ == "__main__":
    main()

