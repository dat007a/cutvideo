import os
import threading
import subprocess
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import sys
import random
import math

def run_ffmpeg_hidden(command):
    if sys.platform == "win32":
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        subprocess.run(command, startupinfo=si, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def get_video_duration(file_path):
    """Lấy độ dài video bằng FFmpeg"""
    command = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", file_path
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    return float(result.stdout.strip())

def split_video(file_path, output_folder, log_func):
    filename = os.path.splitext(os.path.basename(file_path))[0]
    output_subfolder = os.path.join(output_folder, filename)
    os.makedirs(output_subfolder, exist_ok=True)
    
    # Lấy độ dài video và tính số đoạn
    duration = get_video_duration(file_path)
    segment_time = 5  # Mỗi đoạn 5 giây
    num_segments = math.ceil(duration / segment_time)
    
    # Tạo từng đoạn video với tên ngẫu nhiên
    for i in range(num_segments):
        random_number = random.randint(10000000, 99999999)
        output_file = os.path.join(output_subfolder, f"{random_number}.mp4")
        
        command = [
            "ffmpeg", "-i", file_path, "-c", "copy", "-map", "0",
            "-ss", str(i * segment_time), "-t", str(segment_time),
            "-reset_timestamps", "1", output_file
        ]
        
        run_ffmpeg_hidden(command)
    
    log_func(f"Đã xử lý: {filename}")

def process_videos(input_folder, output_folder, progress_bar, log_label, stop_flag):
    video_files = [
        os.path.join(input_folder, f)
        for f in os.listdir(input_folder)
        if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv'))
    ]

    total = len(video_files)
    for idx, file_path in enumerate(video_files):
        if stop_flag["stop"]:
            log_label.config(text="Đã dừng bởi người dùng.")
            return
        log_label.config(text=f"Đang xử lý: {os.path.basename(file_path)}")
        split_video(file_path, output_folder, lambda msg: log_label.config(text=msg))
        progress_bar['value'] = (idx + 1) / total * 100

    log_label.config(text="Hoàn tất.")

def create_gui():
    root = tk.Tk()
    root.title("Video Splitter Tool (FFmpeg)")
    root.geometry("600x300")

    input_folder = tk.StringVar()
    output_folder = tk.StringVar()
    stop_flag = {"stop": False}

    def browse_input():
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            input_folder.set(folder_selected)

    def browse_output():
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            output_folder.set(folder_selected)

    def start_process():
        if not input_folder.get() or not output_folder.get():
            messagebox.showerror("Lỗi", "Vui lòng chọn thư mục input và output.")
            return
        stop_flag["stop"] = False
        threading.Thread(target=process_videos, args=(
            input_folder.get(), output_folder.get(), progress, log_label, stop_flag
        ), daemon=True).start()

    def stop_process():
        stop_flag["stop"] = True

    tk.Label(root, text="Thư mục chứa video input:").pack(pady=5)
    tk.Entry(root, textvariable=input_folder, width=60).pack()
    tk.Button(root, text="Chọn thư mục", command=browse_input).pack(pady=2)

    tk.Label(root, text="Thư mục lưu video output:").pack(pady=5)
    tk.Entry(root, textvariable=output_folder, width=60).pack()
    tk.Button(root, text="Chọn thư mục", command=browse_output).pack(pady=2)

    tk.Button(root, text="Action", bg="green", fg="black", command=start_process).pack(pady=10)
    tk.Button(root, text="Stop", command=stop_process).pack()

    global progress
    progress = ttk.Progressbar(root, length=500, mode='determinate')
    progress.pack(pady=10)

    global log_label
    log_label = tk.Label(root, text="Trạng thái: Chưa chạy")
    log_label.pack(pady=5)

    root.mainloop()

if __name__ == "__main__":
    create_gui()
