import streamlit as st
import cvlib as cv
import threading
import time
import pandas as pd
import boto3
import tempfile
from cvlib.object_detection import detect_common_objects
from moviepy.editor import VideoFileClip

# AWS S3 Config
s3 = boto3.client('s3')
S3_BUCKET = "smart-traffic-data"
S3_VIDEO_KEYS = [
    "videos/rushS.mp4", "videos/vehicle.mp4",
    "videos/rush.mp4", "videos/surveillance.m4v"
]
sides = ["North", "West", "East", "South"]

def download_video_from_s3(key):
    temp = tempfile.NamedTemporaryFile(delete=False)
    s3.download_fileobj(S3_BUCKET, key, temp)
    temp.close()
    return temp.name

def log_results_to_s3(dataframe, round_num):
    csv_data = dataframe.to_csv(index=False)
    key = f"logs/traffic_analysis_round_{round_num}.csv"
    s3.put_object(Bucket=S3_BUCKET, Key=key, Body=csv_data.encode('utf-8'))

def Light(dir, cols1, cols2, cols3):
    signals = {
        'North': ['Images/greenN.png', 'Images/redW.png', 'Images/redE.png', 'Images/redS.png'],
        'West': ['Images/redN.png', 'Images/greenW.png', 'Images/redE.png', 'Images/redS.png'],
        'East': ['Images/redN.png', 'Images/redW.png', 'Images/greenE.png', 'Images/redS.png'],
        'South': ['Images/redN.png', 'Images/redW.png', 'Images/redE.png', 'Images/greenS.png']
    }
    sig = signals[dir]
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
        self.emergency_present = False
        self.stop_event = threading.Event()

    def run(self):
        global k
        clip = VideoFileClip(self.video_path)
        cap = clip.subclip(k, k + 10)
        frame_count = 0

        for frame in cap.iter_frames():
            if frame_count % 25 == 0:
                bbox, label, conf = cv.detect_common_objects(frame, confidence=0.25, model='yolov3-tiny')
                self.car_count += label.count('car') + label.count('truck') + label.count('motorcycle') + label.count('bus')
                if 'ambulance' in label or 'fire truck' in label or 'police car' in label:
                    self.emergency_present = True

            if self.car_count >= 10:
                break
            frame_count += 1

        clip.close()

    def stop(self):
        self.stop_event.set()

def main():
    global k
    st.set_page_config(page_title="Smart Traffic Management", layout="wide")
    st.markdown("<h1 style='text-align: center; color: teal;'>🚦 Smart Traffic Management System</h1>", unsafe_allow_html=True)

    # Sidebar
    st.sidebar.header("Simulation Controls")
    run_simulation = st.sidebar.button("▶️ Run Traffic Simulation")
    st.sidebar.info("Video files and logs are stored in AWS S3.")

    cols1, cols2, cols3 = st.columns(3), st.columns(3), st.columns(3)

    if run_simulation:
        st.subheader("📹 Live Camera Feeds")

        # Download and show videos
        local_video_paths = [download_video_from_s3(key) for key in S3_VIDEO_KEYS]

        for i, video_path in enumerate(local_video_paths):
            if i == 0:
                cols1[1].video(video_path)
            elif i == 1:
                cols2[0].video(video_path)
            elif i == 2:
                cols2[2].video(video_path)
            else:
                cols3[1].video(video_path)

        progress = st.progress(0)
        status = st.empty()

        for round_num in range(4):
            k = round_num * 10
            car_counts = [0, 0, 0, 0]
            emergency_detected = False
            emergency_side = None

            video_processors = [VideoProcessor(path, side) for path, side in zip(local_video_paths, sides)]
            for vp in video_processors:
                vp.start()

            status.info(f"🔄 Processing round {round_num + 1}/4...")
            time.sleep(15)
            progress.progress((round_num + 1) / 4)

            for vp in video_processors:
                vp.stop()
            for vp in video_processors:
                vp.join()

            for i, vp in enumerate(video_processors):
                car_counts[i] = vp.car_count
                if vp.emergency_present:
                    emergency_detected = True
                    emergency_side = vp.side
                    break

            if emergency_detected:
                st.error(f"🚑 Emergency detected on {emergency_side}! Giving priority.")
                dir = emergency_side
            else:
                dir = sides[car_counts.index(max(car_counts))]

            st.markdown("### 🚘 Traffic Analysis Table")
            data = pd.DataFrame({
                "Side": sides,
                "Number of Vehicles": car_counts,
                "Traffic Light": ["🟢 Green" if side == dir else "🔴 Red" for side in sides]
            })
            st.dataframe(data, use_container_width=True)

            log_results_to_s3(data, round_num + 1)

            st.markdown("### 📊 Vehicle Count Chart")
            st.bar_chart(pd.DataFrame({'Vehicles': car_counts}, index=sides))

            with st.expander("🚦 View Traffic Lights"):
                Light(dir, cols1, cols2, cols3)

            st.success(f"✅ {dir} has the green light based on current traffic conditions.")

if __name__ == "__main__":
    main()
