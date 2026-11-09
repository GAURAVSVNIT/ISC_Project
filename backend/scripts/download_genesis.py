import requests
import os
import sys

URL = "https://huggingface.co/spaces/jenil1236/convnext-gradcam-api/resolve/main/best_convnext_large.pth"
DEST = "backend/weights/best_convnext_large.pth"

def download_file():
    # Check if already exists
    if os.path.exists(DEST):
        file_size = os.path.getsize(DEST)
        print(f"File already exists: {DEST} ({file_size:,} bytes)")
        if file_size > 780000000:  # ~780MB+
            print("File appears complete. Skipping download.")
            return
        else:
            print("File appears incomplete. Removing and re-downloading...")
            os.remove(DEST)

    # Ensure directory exists
    os.makedirs(os.path.dirname(DEST), exist_ok=True)
    
    print(f"Downloading ConvNeXt Large weights (~750MB)...")
    print(f"URL: {URL}")
    print(f"Destination: {os.path.abspath(DEST)}")
    print()
    
    try:
        with requests.get(URL, stream=True, timeout=30) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            downloaded = 0
            chunk_size = 1024 * 1024  # 1MB chunks
            
            with open(DEST, 'wb') as f:
                for chunk in r.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size:
                            percent = (downloaded / total_size) * 100
                            mb_downloaded = downloaded / (1024 * 1024)
                            mb_total = total_size / (1024 * 1024)
                            sys.stdout.write(f"\rProgress: {percent:.1f}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)")
                            sys.stdout.flush()
        
        print("\n✓ Download Complete!")
        print(f"File saved: {os.path.abspath(DEST)} ({os.path.getsize(DEST):,} bytes)")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        if os.path.exists(DEST):
            print("Cleaning up partial download...")
            os.remove(DEST)
        sys.exit(1)

if __name__ == "__main__":
    download_file()
