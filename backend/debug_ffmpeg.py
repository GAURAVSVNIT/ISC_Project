import sys
try:
    import imageio_ffmpeg
    print(f"DEBUG: FFMPEG Binary: {imageio_ffmpeg.get_ffmpeg_exe()}")
    import moviepy
    print(f"DEBUG: MoviePy Version: {moviepy.__version__}")
except ImportError as e:
    print(f"DEBUG: ImportError: {e}")
except Exception as e:
    print(f"DEBUG: Error: {e}")
