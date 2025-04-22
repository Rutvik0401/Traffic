import streamlit as st
import threading
import time
import pandas as pd
import cvlib as cv  # Keeping cvlib for object detection
from cvlib.object_detection import detect_common_objects
from moviepy.editor import VideoFileClip
import random  # Simulating car counts for demonstration

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
    st.sidebar.info("This system detects traffic density and emergency vehicles to optimize signal flow.")

    # Video paths
    video_paths = ["Images/rushS.mp4", "Images/vehicle.mp4", "Images/rush.mp4", "Images/surveillance.m4v"]
    sides = ["North", "West", "East", "South"]

    if len(video_paths) != len(sides):
        st.error("Number of video paths and sides should be the same.")
        return

    cols1, cols2, cols3 = st.columns(3), st.columns(3), st.columns(3)

    # Display video feeds
    st.subheader("Live Camera Feeds")
    for i, video_path in enumerate(video_paths):
        if i == 0:
            cols1[1].video(video_path)
        elif i == 1:
            cols2[0].video(video_path)
        elif i == 2:
            cols2[2].video(video_path)
        else:
            cols3[1].video(video_path)

    # Simulation
    if run_simulation:
        progress = st.progress(0)
        status = st.empty()
        p1, p2, p3, p4 = st.empty(), st.empty(), st.empty(), st.empty()

        for round_num in range(4):
            k = round_num * 10
            car_counts = [0, 0, 0, 0]
            emergency_detected = False
            emergency_side = None

            video_processors = [VideoProcessor(video_path, side) for video_path, side in zip(video_paths, sides)]
            for vp in video_processors:
                vp.start()

            status.info(f"Processing round {round_num + 1}/4...")
            time.sleep(10)
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
                most_traffic_index = car_counts.index(max(car_counts))
                dir = sides[most_traffic_index]

            # Display traffic data table
            data = pd.DataFrame({
                "Side": sides,
                "Number of Vehicles": car_counts,
                "Traffic Light": ["🟢 Green" if side == dir else "🔴 Red" for side in sides]
            })

            st.markdown("### 🚘 Traffic Analysis Table")
            st.dataframe(data, use_container_width=True)

            # Bar chart
            st.markdown("### 📊 Vehicle Count Chart")
            st.bar_chart(pd.DataFrame({'Vehicles': car_counts}, index=sides))

            # Show signal lights
            with st.expander("🚦 View Traffic Lights"):
                Light(dir, cols1, cols2, cols3)

            st.success(f"✅ {dir} has the green light based on current traffic conditions.")

if __name__ == "__main__":
    main()
