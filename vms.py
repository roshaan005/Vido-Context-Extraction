import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import subprocess
import os
import shutil
import threading
import webbrowser
from datetime import datetime
from pytube import YouTube
import time

class TextToSpeechStream:
    def __init__(self, root, stream_name, row):
        self.root = root
        self.stream_name = stream_name
        self.row = row
        self.is_running = False

        self.create_widgets()

    def create_widgets(self):
        # Create a frame for the stream
        self.stream_frame = ttk.Frame(self.root, padding="20", style="Stream.TFrame")
        self.stream_frame.grid(row=self.row, column=0, columnspan=4, padx=10, pady=10, sticky="ew")

        # Create a label for the stream name
        self.stream_label = ttk.Label(self.stream_frame, text=self.stream_name, font=("Helvetica", 16, "bold"), style="Stream.TLabel")
        self.stream_label.grid(row=0, column=0, columnspan=4, pady=10, sticky="w")

        # Create a label for instructions above Search Word
        ttk.Label(self.stream_frame, text="                                Enter word(s) or list separated by commas", style="Instruction.TLabel").grid(row=1, column=0, columnspan=2, padx=5, pady=(5,0), sticky="w")

        # Create a label and entry for user input (word)
        ttk.Label(self.stream_frame, text="Search Word:", style="Stream.TLabel").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.word_entry = ttk.Entry(self.stream_frame, width=30)
        self.word_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        # Create a label for instructions above URL
        ttk.Label(self.stream_frame, text="                         Input live stream Youtube URL only", style="Instruction.TLabel").grid(row=1, column=2, columnspan=2, padx=5, pady=(5,0), sticky="w")

        # Create a label and entry for user input (URL)
        ttk.Label(self.stream_frame, text="URL:", style="Stream.TLabel").grid(row=2, column=2, padx=5, pady=5, sticky="e")
        self.url_entry = ttk.Entry(self.stream_frame, width=30)
        self.url_entry.grid(row=2, column=3, padx=5, pady=5, sticky="w")

        # Create a label to display creation time
        self.creation_time_label = ttk.Label(self.stream_frame, text="", style="Stream.TLabel")
        self.creation_time_label.grid(row=2, column=4, columnspan=2, padx=5, pady=5, sticky="w")

        # Create a label to display channel name
        self.channel_label = ttk.Label(self.stream_frame, text="", style="Stream.TLabel")
        self.channel_label.grid(row=3, column=4, columnspan=2, padx=5, pady=5, sticky="w")

        # Create a label for status
        self.status_label = ttk.Label(self.stream_frame, text="Status: ", style="Stream.TLabel")
        self.status_label.grid(row=4, column=0, columnspan=4, pady=5, sticky="w")

        # Create a button to trigger text-to-speech and URL processing
        self.action_button = ttk.Button(self.stream_frame, text="Start", command=self.toggle_processing, style="Stream.TButton")
        self.action_button.grid(row=5, column=1, pady=10, sticky="n")

        # Create a "View" button to open the folder
        self.view_button = ttk.Button(self.stream_frame, text="View", command=self.open_folder, style="Stream.TButton")
        self.view_button.grid(row=5, column=2, pady=10, sticky="n")

        # Create a label to display the count of .mp4 videos
        self.mp4_count_label = ttk.Label(self.stream_frame, text="", style="Stream.TLabel")
        self.mp4_count_label.grid(row=5, column=3, columnspan=2, padx=5, pady=5, sticky="e")

    def toggle_processing(self):
        if self.is_running:
            self.stop_processing()
            self.is_running = False
        else:
            self.start_processing()
            self.is_running = True

    def start_processing(self):
        self.action_button.config(text="Stop", style="Running.TButton")
    
        # Set initial status message
        self.status_label.config(text="Status: Generating synthesized words, please wait...")

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.creation_time_label.config(text=f"    Created on: {current_time}")
        
    
        # Get the word and URL from the entries
        words = self.word_entry.get().split(',')  # Split words by comma
        # Check if either word or URL is empty
        if not any(words):
            self.status_label.config(text="Status: Please enter at least one word.")
            return

        for word in words:
            if not word.strip():
                continue
            word_folder = f'/home/jetson/VMS/GUI2CHjetson/{self.stream_name}_detection/{word}/'
            os.makedirs(word_folder, exist_ok=True)
            
            self.status_label.config(text="Status: Generating synthesized words, please wait...")

            try:
                self.status_label.config(text="Status: Generating synthesized words, please wait...")
                # Call the HiFIGAN script using subprocess
                subprocess.run(["python3", f"{self.stream_name}_hifigan.py", word.strip()], check=True)
                self.status_label.config(text=f"Status: Audio generated successfully for the word: {word.strip()}")
                self.create_word_buttons(words)
                time.sleep(3)

            except subprocess.CalledProcessError as e:
                self.status_label.config(text=f"Status: Error: {e}")

        url = self.url_entry.get()

        # Check if URL is provided
        if url:
            try:
                # Call the utube_vid_aud.py script using subprocess
                subprocess.Popen(["python3", f"{self.stream_name}_utube_vid_aud.py", url])
                self.status_label.config(text=f"Status: URL processing started successfully for {self.stream_name}.")

                # Schedule the start of corelation_updated_v2.py after 200 seconds
                self.root.after(150000, self.moniter_process)
            
                # Get and display channel name
                channel_name = get_channel_name(url)
                if channel_name:
                    	self.channel_label.config(text=f"    Channel: {channel_name}")
            
            except Exception as e:
                self.status_label.config(text=f"Status: Error: {e}")

        # Display count of .mp4 videos
        self.update_mp4_count()
        self.current_detected_words = words  # Save words globally
        self.create_word_buttons(words)      # Refresh all buttons with updated counts
 


    def create_word_buttons(self, words):
        # Clear existing word buttons (optional if refreshing)
        if hasattr(self, 'word_buttons'):
            for btn in self.word_buttons:
                btn.destroy()

        self.word_buttons = []
        for idx, word in enumerate(words):
            word = word.strip()
            if not word:
                continue

            folder_path = f'/home/jetson/VMS/GUI2CHjetson/{self.stream_name}_detection/{word}/'
            mp4_count = 0
            if os.path.exists(folder_path):
                mp4_count = len([f for f in os.listdir(folder_path) if f.endswith('.mp4')])

            button = ttk.Button(
                self.stream_frame,
                text=f"▶ {word} ({mp4_count})",
                command=lambda w=word: self.play_all_word_videos(w),
                style="Word.TButton"
            )
            button.grid(row=6 + idx, column=1, columnspan=2, sticky="w", pady=2)
            self.word_buttons.append(button)



    def play_all_word_videos(self, word):
        folder_path = f'/home/jetson/VMS/GUI2CHjetson/{self.stream_name}_detection/{word}/'
        if not os.path.exists(folder_path):
            self.status_label.config(text=f"Status: No folder found for '{word}'")
            return

        mp4_files = sorted(f for f in os.listdir(folder_path) if f.endswith('.mp4'))
        if not mp4_files:
            self.status_label.config(text=f"Status: No videos found for '{word}'")
            return

        self.status_label.config(text=f"Status: Playing all videos for '{word}'")

        for video in mp4_files:
            video_path = os.path.join(folder_path, video)
            try:
                # Use VLC for consistent behavior (plays and waits for finish)
                subprocess.run(["xdg-open", video_path])
            except Exception as e:
                self.status_label.config(text=f"Error playing: {video} | {e}")
                break

    def get_mp4_count(self):
        folder_path = '/home/jetson/VMS/GUI2CHjetson/' + self.stream_name + '_detection/'
        try:
            total_count = 0
            if os.path.exists(folder_path):
            	for word_folder in os.listdir(folder_path):
            		word_path = os.path.join(folder_path, word_folder)
            		if os.path.isdir(word_path):  # Ensure it's a folder                    
            			mp4_files = [f for f in os.listdir(word_path) if f.endswith('.mp4')]
            			total_count += len(mp4_files)
            return total_count
        except Exception as e:
            print("Error:", e)
            return 0
    def update_mp4_count(self):
    	mp4_count = self.get_mp4_count()  
    	self.mp4_count_label.config(text=f"Detections: {mp4_count}")  
    	self.root.after(3000, self.update_mp4_count)  # Update every 3 seconds  

    def start_corelation_updated(self):
        self.status_label.config(text=f"Status: {self.stream_name}_corelation_updated_v2.py started successfully.")
        return subprocess.Popen(["python3", f"{self.stream_name}_corelation_updated_v2.py"])
            

            
#    def moniter_process(self):
#    	process = None
#    	while True:
#    		process = self.start_corelation_updated()
#    		while True:
#    			retcode = process.poll()
#    			if retcode is not None:
#    				time.sleep(200)
#    				break
#    			time.sleep(100)
    def moniter_process(self):
    	self.monitoring_active = True 
    	
    	def check_process():
        	process = self.start_corelation_updated()  # Start the process initially

        	# Monitor the process in the background
        	while self.monitoring_active:
            		retcode = process.poll()  # Check if the process has finished
            		if retcode is not None:  # If process has finished (died)
                		print(f"Process has died with exit code {retcode}. Restarting...")
                		process = self.start_corelation_updated()  # Restart the process
                		if not self.monitoring_active:
                			break
            		time.sleep(30)  # Check the process every 30 seconds

    	# Start the monitoring in a separate thread to avoid blocking the GUI
    	monitoring_thread = threading.Thread(target=check_process, daemon=True)
    	monitoring_thread.start()


#    def moniter_process(self):
#    	def check_process():
#        	process = self.start_corelation_updated()  # Start the process
#        	while True:
#            		retcode = process.poll()  # Check if the process is still running
#            		if retcode is not None:  # If process has finished
#                		# Restart the process
#                		print(f"Process has died. Restarting...")
#                		process = self.start_corelation_updated()  # Restart the process
#            		time.sleep(5)  # Check the process every 5 seconds

#    	self.root.after(1000, check_process)  # Start monitoring the process after 1 second



    

    def stop_processing(self):
        self.action_button.config(text="Start", style="Stream.TButton")
        self.monitoring_active = False
        self.status_label.config(text=f"Status: {self.stream_name} stopped.")

        # Kill the subprocess forcefully
        subprocess.run(["pkill", "-f", f"{self.stream_name}_hifigan.py"])
        subprocess.run(["pkill", "-f", f"{self.stream_name}_utube_vid_aud.py"])
        subprocess.run(["pkill", "-f", f"{self.stream_name}_corelation_updated_v2.py"])

        # Delete files in videos, audios, and searchword1 folders
        try:
            shutil.rmtree(f'/home/jetson/VMS/GUI2CHjetson/{self.stream_name}audios/')
            os.makedirs(f'/home/jetson/VMS/GUI2CHjetson/{self.stream_name}audios/')
            print(f'Directory Created for Audio files ({self.stream_name})')

            shutil.rmtree(f'/home/jetson/VMS/GUI2CHjetson/{self.stream_name}videos/')
            os.makedirs(f'/home/jetson/VMS/GUI2CHjetson/{self.stream_name}videos/')
            print(f'Directory Created for Videos ({self.stream_name})')

            shutil.rmtree(f'/home/jetson/VMS/GUI2CHjetson/{self.stream_name}_searchword1/')
            os.makedirs(f'/home/jetson/VMS/GUI2CHjetson/{self.stream_name}_searchword1/')
            print(f'Directory Created for searchword1 ({self.stream_name})')
        except Exception as e:
            self.status_label.config(text=f"Status: Error while deleting files: {e}")

    def open_folder(self):
        if self.stream_name == "Stream1":
            path = '/home/jetson/VMS/GUI2CHjetson/Stream1_detection/'
        elif self.stream_name == "Stream2":
            path = '/home/jetson/VMS/GUI2CHjetson/Stream2_detection/'
        else:
            return

        try:
            subprocess.run(['xdg-open', path])
            #webbrowser.open(path)
        except Exception as e:
            self.status_label.config(text=f"Status: Error opening folder: {e}")

def toggle_stream2_display(stream2_frame, toggle_button):
    if stream2_frame.winfo_ismapped():
        stream2_frame.grid_remove()
        toggle_button.config(text="+")
    else:
        stream2_frame.grid()
        toggle_button.config(text="-")

def run_stream(stream, root, toggle_button):
    stream_instance = TextToSpeechStream(root, stream["name"], stream["row"])
    if stream["name"] == "Stream2":
        stream_instance.stream_frame.grid_remove()
        toggle_button.config(command=lambda: toggle_stream2_display(stream_instance.stream_frame, toggle_button))

def get_channel_name(url):
    try:
        yt = YouTube(url)
        return yt.author
    except Exception as e:
        print("Error:", e)
        return None

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Live Stream Monitoring Stream")

    # Define stream parameters
    stream1_params = {"name": "Stream1", "row": 0}
    stream2_params = {"name": "Stream2", "row": 1}

    # Create toggle button for Stream 2
    toggle_button = ttk.Button(root, text="+")
    toggle_button.grid(row=2, column=0, columnspan=4, pady=10)

    # Create frames for streams
    stream1_frame = ttk.Frame(root, padding="20", style="Stream.TFrame")
    stream1_frame.grid(row=0, column=0, padx=10, pady=10, sticky="w")

    stream2_frame = ttk.Frame(root, padding="20", style="Stream.TFrame")
    stream2_frame.grid(row=1, column=0, padx=10, pady=10, sticky="w")

    # Create threads for each stream
    thread1 = threading.Thread(target=run_stream, args=(stream1_params, root, toggle_button))
    thread2 = threading.Thread(target=run_stream, args=(stream2_params, root, toggle_button))

    # Start the threads
    thread1.start()
    thread2.start()

    # Style for the buttons and frames
    style = ttk.Style()
    style.configure("Stream.TFrame", background="#ECEFF1")
    style.configure("Stream.TLabel", foreground="#37474F", background="#ECEFF1")
    style.configure("Stream.TButton", font=("Helvetica", 10), background="#03A9F4", foreground="#FFFFFF", padding=5)
    style.configure("Running.TButton", font=("Helvetica", 10), background="#F44336", foreground="#FFFFFF", padding=5)
    style.configure("Instruction.TLabel", foreground="#757575", background="#ECEFF1", font=("Helvetica", 8))  # Style for instructions

    # Main loop for the GUI
    root.mainloop()

