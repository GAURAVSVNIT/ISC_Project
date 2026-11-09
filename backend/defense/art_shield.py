from PIL import Image, ImageFilter
import io

class VeritasShield:
    """
    Implements adversarial defense preprocessing using spatial smoothing 
    and compression to neutralize perturbations.
    """
    
    @staticmethod
    def sanitize(image_bytes: bytes) -> bytes:
        """
        Apply defense layers: Gaussian Blur + JPEG Compression + Resizing.
        Returns sanitized image bytes.
        """
        # Load image
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        
        # 1. Gaussian Blur (Lightest touch to break adversarial noise without destroying texture)
        # Radius 0.5 is very subtle.
        image = image.filter(ImageFilter.GaussianBlur(radius=0.5))
        
        # 2. Resizing (disrupts pixel-grid attack patterns)
        w, h = image.size
        # Downsample slightly then upsample
        image = image.resize((int(w * 0.9), int(h * 0.9)), Image.Resampling.LANCZOS)
        image = image.resize((w, h), Image.Resampling.BICUBIC)
        
        # 3. JPEG Compression (High quality to preserve forensic artifacts)
        # Quality 95 removes high-freq adversarial noise but keeps visual integrity.
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=95)
        buffer.seek(0)
        
        return buffer.getvalue()

    @staticmethod
    def detect_trailing_bytes(file_bytes: bytes) -> bool:
        """
        Detects if there are suspicious trailing bytes after the image EOF.
        Common steganography tactic: Appending ZIP/RAR to JPG.
        """
        if len(file_bytes) < 4:
            return False
            
        # Check for JPEG EOI marker (FF D9)
        # Note: This is a basic check. Sophisticated parsers are needed for robust detection.
        if file_bytes.startswith(b'\xff\xd8'):
            eoi_index = file_bytes.rfind(b'\xff\xd9')
            if eoi_index != -1:
                # If EOI is found, check if there is significant data after it
                trailing_size = len(file_bytes) - (eoi_index + 2)
                if trailing_size > 100: # Allow 100 bytes for potential metadata/padding
                    return True
        
        return False

shield = VeritasShield()
