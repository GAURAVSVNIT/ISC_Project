"""
Metadata Pre-Filter for AI-Generated Image Detection

Cost Optimization: Check EXIF data BEFORE running expensive GPU/API operations.
If metadata contains AI generation tags → instant verdict (no compute needed).
If metadata is absent/suspicious → proceed to full pipeline.
"""

from PIL import Image
from PIL.ExifTags import TAGS
import io
from typing import Dict, Any

class MetadataFilter:
    """
    Fast metadata checker for AI-generated image detection.
    Extracts EXIF data and flags obvious AI signatures.
    """
    
    # Known AI software signatures (expanded)
    AI_SOFTWARE_SIGNATURES = [
        "midjourney",
        "stable diffusion",
        "dall-e",
        "dalle",
        "firefly",
        "leonardo.ai",
        "dreamshaper",
        "automatic1111",
        "comfyui",
        "novelai",
        "craiyon",
        "imagen",
        "ai-generated",
        "invokeai",
        "fooocus",
        "tensor.art",
        "playground",
        "artbreeder",
        "nightcafe",
        "starryai",
    ]
    
    # AI generation prompt keywords
    AI_PROMPT_KEYWORDS = [
        "negative prompt",
        "sampling steps",
        "cfg scale",
        "denoising strength",
        "sampler:",
        "seed:",
        "model:",
    ]
    
    # Camera metadata fields (real photos typically have these)
    CAMERA_FIELDS = ["Make", "Model", "LensModel", "FocalLength", "ExposureTime", "FNumber", "ISO"]
    
    def check(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Analyze image metadata for AI generation indicators.
        
        Returns:
            {
                "verdict": "FAKE" | "UNKNOWN",
                "confidence": "HIGH" | "LOW",
                "ai_tags": [...],
                "has_camera_metadata": bool,
                "should_short_circuit": bool  # True if we can skip full pipeline
            }
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
            exif_data = image.getexif()
            
            # Check PNG chunks first (highest AI detection rate)
            if image.format == "PNG":
                png_ai_tags = self._check_png_chunks(image)
                if png_ai_tags:
                    return {
                        "verdict": "FAKE",
                        "confidence": "HIGH",
                        "ai_tags": png_ai_tags,
                        "has_camera_metadata": False,
                        "should_short_circuit": True,
                        "reason": f"AI workflow detected in PNG: {', '.join(png_ai_tags[:2])}"
                    }
            
            if not exif_data:
                # No EXIF at all - could be stripped by platform OR AI-generated
                return {
                    "verdict": "UNKNOWN",
                    "confidence": "LOW",
                    "ai_tags": [],
                    "has_camera_metadata": False,
                    "should_short_circuit": False,
                    "reason": "No EXIF data present"
                }
            
            # Extract readable tags
            metadata = {}
            for tag_id, value in exif_data.items():
                tag_name = TAGS.get(tag_id, tag_id)
                metadata[tag_name] = str(value)
            
            # Check for AI software signatures in EXIF
            ai_tags = self._check_ai_signatures(metadata)
            if ai_tags:
                return {
                    "verdict": "FAKE",
                    "confidence": "HIGH",
                    "ai_tags": ai_tags,
                    "has_camera_metadata": False,
                    "should_short_circuit": True,  # ✅ STOP - Don't waste GPU
                    "reason": f"AI software detected: {', '.join(ai_tags)}"
                }
            
            # Check for temporal anomalies (suspicious timestamp patterns)
            temporal_suspicious = self._check_temporal_anomalies(metadata)
            if temporal_suspicious:
                # Don't short-circuit, but flag as suspicious
                pass
            
            # Check for camera metadata
            has_camera_data = self._has_camera_metadata(metadata)
            
            if has_camera_data:
                # Has camera metadata - could be real OR faked
                # Don't short-circuit (metadata can be spoofed)
                return {
                    "verdict": "UNKNOWN",
                    "confidence": "LOW",
                    "ai_tags": [],
                    "has_camera_metadata": True,
                    "should_short_circuit": False,
                    "reason": "Camera metadata present (could be faked)"
                }
            else:
                # No camera data, no AI tags - suspicious but inconclusive
                return {
                    "verdict": "UNKNOWN",
                    "confidence": "LOW",
                    "ai_tags": [],
                    "has_camera_metadata": False,
                    "should_short_circuit": False,
                    "reason": "No camera metadata (suspicious but not definitive)"
                }
                
        except Exception as e:
            # If PIL fails (likely Video or Audio), fall back to Binary Signature Scan
            # This allows us to catch "Sora" or "Suno" tags in MP4/MP3 headers
            binary_tags = self._check_binary_signatures(image_bytes)
            if binary_tags:
                return {
                    "verdict": "FAKE",
                    "confidence": "HIGH",
                    "ai_tags": binary_tags,
                    "has_camera_metadata": False,
                    "should_short_circuit": True, # ✅ STOP - Video/Audio AI Detected
                    "reason": f"AI signature found in file header: {', '.join(binary_tags[:2])}"
                }
                
            # Valid failure (not AI, just unreadable/other format)
            return {
                "verdict": "UNKNOWN",
                "confidence": "LOW",
                "ai_tags": [],
                "has_camera_metadata": False,
                "should_short_circuit": False,
                "reason": f"Metadata extraction skipped: {str(e)[:50]}"
            }
            
    def _check_binary_signatures(self, file_bytes: bytes) -> list:
        """
        Scans values in the first 2MB of file for known AI Video/Audio signatures.
        Useful for MP4/MP3 containers where PIL fails.
        """
        found_tags = []
        try:
            # Limit scan to header/metadata area (first 2MB is usually enough)
            header_chunk = file_bytes[:2 * 1024 * 1024]
            # Convert to lower string (careful with decoding, using ignore)
            try:
                # Naive decode for string searching
                decoded = header_chunk.decode('utf-8', errors='ignore').lower()
                
                # Extended signatures for Video/Audio
                video_audio_sigs = [
                    "sora", "runwayml", "pika labs", "lavie", "stable video", 
                    "suno", "udio", "elevenlabs", "bark", "audiocraft"
                ]
                
                for sig in video_audio_sigs:
                    if sig in decoded:
                        found_tags.append(f"Header:{sig}")
                        
            except:
                pass
        except:
            pass
            
        return found_tags
    
    def _check_ai_signatures(self, metadata: Dict[str, str]) -> list:
        """
        Search for AI generation signatures in metadata fields.
        """
        found_tags = []
        
        # Check common fields
        check_fields = ["Software", "Artist", "ImageDescription", "UserComment", "Copyright"]
        
        for field in check_fields:
            if field in metadata:
                field_value = metadata[field].lower()
                for signature in self.AI_SOFTWARE_SIGNATURES:
                    if signature in field_value:
                        found_tags.append(f"{field}: {metadata[field]}")
        
        return found_tags
    
    def _check_png_chunks(self, image: Image.Image) -> list:
        """
        Check PNG tEXt/iTXt chunks for AI generation parameters.
        Stable Diffusion/ComfyUI embed full workflow here.
        """
        found_tags = []
        
        try:
            # PNG info is stored in image.info dict
            if hasattr(image, 'info') and image.info:
                for key, value in image.info.items():
                    if isinstance(value, (str, bytes)):
                        text_value = value.decode('utf-8', errors='ignore') if isinstance(value, bytes) else value
                        text_lower = text_value.lower()
                        
                        # Check for AI software
                        for signature in self.AI_SOFTWARE_SIGNATURES:
                            if signature in text_lower:
                                found_tags.append(f"PNG:{key}={text_value[:50]}")
                                break
                        
                        # Check for prompt keywords
                        for keyword in self.AI_PROMPT_KEYWORDS:
                            if keyword in text_lower:
                                found_tags.append(f"PNG:AI-Params={text_value[:50]}")
                                break
        except Exception:
            pass  # PNG parsing error - not critical
        
        return found_tags
    
    def _check_temporal_anomalies(self, metadata: Dict[str, str]) -> bool:
        """
        Check for suspicious timestamp patterns.
        Real cameras have slight differences between timestamps.
        AI-generated images often have identical timestamps (or none).
        """
        timestamp_fields = ["DateTimeOriginal", "DateTimeDigitized", "DateTime"]
        timestamps = [metadata.get(field) for field in timestamp_fields if field in metadata]
        
        # If all timestamps are identical, it's suspicious
        if len(timestamps) >= 2 and len(set(timestamps)) == 1:
            return True  # All identical - suspicious
        
        return False
    
    def _has_camera_metadata(self, metadata: Dict[str, str]) -> bool:
        """
        Check if image has typical camera EXIF fields.
        """
        camera_fields_found = sum(1 for field in self.CAMERA_FIELDS if field in metadata)
        # Require at least 3 camera fields to consider it "real camera data"
        return camera_fields_found >= 3

# Singleton instance
metadata_filter = MetadataFilter()
