import os
import sys
import subprocess
import imageio_ffmpeg

def test_ffmpeg():
    print("--- FFMPEG DEBUG START ---")
    try:
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        print(f"FFMPEG Path: {exe}")
        
        if not os.path.exists(exe):
            print("CRITICAL: FFMPEG executable does not exist at path!")
            return
            
        # Test 1: Version check
        print("\nTest 1: Running -version")
        try:
            result = subprocess.run([exe, "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"Return Code: {result.returncode}")
            print(f"Output: {result.stdout.decode('utf-8', errors='ignore')[:100]}...")
        except Exception as e:
            print(f"Test 1 Failed: {e}")
            
    except Exception as e:
        print(f"General Error: {e}")
    print("--- FFMPEG DEBUG END ---")

if __name__ == "__main__":
    test_ffmpeg()
