
import os
import tempfile
import cv2
import numpy as np
from PIL import Image
from moviepy import VideoFileClip 
import asyncio

def _extract_frame_sync(temp_video_path):
    """Synchronous OpenCV logic to be run in a thread"""
    try:
        cap = cv2.VideoCapture(temp_video_path)
        print("[VideoProcessor] OpenCV VideoCapture initialized.")
        if not cap.isOpened():
            return None
            
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        target_frame_idx = total_frames // 2
        print(f"[VideoProcessor] Total frames: {total_frames}, Target frame index: {target_frame_idx}")
        cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame_idx)
        
        success, frame_bgr = cap.read()
        print(f"[VideoProcessor] Frame read success: {success}")
        cap.release()
        
        if success and frame_bgr is not None:
            return cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        return None
    except Exception as e:
        print(f"[VideoProcessor] data extraction error: {e}")
        return None

async def extract_components(video_bytes: bytes):
    """
    Extracts frames using OpenCV (Robust) and Audio using MoviePy.
    Runs blocking operations in thread pool.
    """
    # Create temp file for the video
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_video:
        temp_video.write(video_bytes)
        temp_video_path = temp_video.name

    try:
        # --- 1. Robust Frame Extraction (OpenCV) ---
        # Run blocking OpenCV IO in thread pool
        print(f"[VideoProcessor] Starting frame extraction for {temp_video_path}")
        frame_rgb = await asyncio.to_thread(_extract_frame_sync, temp_video_path)
        
        image_path = None
        if frame_rgb is not None:
            pil_image = Image.fromarray(frame_rgb)
            print(f"[VideoProcessor] Extracted Frame: {pil_image.size}")
            
            # Save as PNG
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_img:
                pil_image.save(temp_img, format="PNG")
                image_path = temp_img.name
        else:
             print("[VideoProcessor] Error: Failed to read frame from video.")

        # --- 2. Audio Extraction (MoviePy) ---
        import subprocess
        import imageio_ffmpeg

        def _extract_audio_sync():
            try:
                ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
                print(f"[VideoProcessor] Using FFMPEG binary: {ffmpeg_exe}")
                
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
                    audio_output_path = temp_audio.name
                
                # Command: ffmpeg -y -i <video> -vn -acodec pcm_s16le -ar 16000 -ac 1 <audio_out>
                cmd = [
                    ffmpeg_exe,
                    "-y",
                    "-i", temp_video_path,
                    "-vn",
                    "-acodec", "pcm_s16le",
                    "-ar", "16000",
                    "-ac", "1",
                    audio_output_path
                ]
                
                print(f"[VideoProcessor] Running FFMPEG: {' '.join(cmd)}")
                result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                if result.returncode == 0 and os.path.exists(audio_output_path) and os.path.getsize(audio_output_path) > 0:
                    print(f"[VideoProcessor] Audio extracted successfully: {audio_output_path}")
                    return audio_output_path
                else:
                    print(f"[VideoProcessor] FFMPEG failed or no audio. Return code: {result.returncode}")
                    print(f"STDERR: {result.stderr.decode('utf-8', errors='ignore')}")
                    # Cleanup empty file
                    if os.path.exists(audio_output_path):
                        os.remove(audio_output_path)
                    return None
                    
            except Exception as e:
                print(f"[VideoProcessor] Subprocess Audio extraction error: {e}")
                import traceback
                traceback.print_exc()
                return None

        audio_path = await asyncio.to_thread(_extract_audio_sync)
        
        return {
            "image_path": image_path,
            "audio_path": audio_path
        }

    except Exception as e:
        print(f"[VideoProcessor] Critical Error: {e}")
        return None
        
    finally:
        # Cleanup input video
        if os.path.exists(temp_video_path):
            try:
                os.remove(temp_video_path)
            except:
                pass


