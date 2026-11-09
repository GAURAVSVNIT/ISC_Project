import asyncio
import torch
from typing import Dict, Any
from PIL import Image
import io
import os

class SemanticStream:
    """
    Stream B: Semantic Consistency
    Uses CLIP for Image Captioning + Sentence Transformer for Similarity
    """
    
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.is_ready = False
        self.model = None
        self.processor = None

    def _ensure_models_loaded(self):
        if self.is_ready:
            return True
            
        try:
            print(f"Loading Semantic Models on {self.device}...")
            
            # Load CLIP (ViT-L/14) from Hugging Face
            from transformers import CLIPProcessor, CLIPModel
            
            # Check for fine-tuned weights
            ft_path = "backend/weights/clip_finetuned/checkpoint"
            if os.path.exists(ft_path) and os.path.exists(os.path.join(ft_path, "config.json")):
                 print(f"Found fine-tuned CLIP model at {ft_path}")
                 model_name_or_path = ft_path
            else:
                 print("Using base OpenAI/CLIP model (No fine-tuning found)")
                 model_name_or_path = "openai/clip-vit-large-patch14"
            
            self.processor = CLIPProcessor.from_pretrained(model_name_or_path)
            self.model = CLIPModel.from_pretrained(model_name_or_path).to(self.device)
            
            self.is_ready = True
            print(f"Semantic Stream ({model_name_or_path}) Loaded Successfully.")
            return True
        except Exception as e:
            print(f"Error loading Semantic Stream: {e}")
            self.is_ready = False
            return False

    async def analyze(self, image_bytes: bytes, claim: str) -> Dict[str, Any]:
        # Lazy Loading
        if not self.is_ready:
            success = self._ensure_models_loaded()
            if not success:
                return {
                    "score": 0.0, 
                    "status": "Error: Models failed to load", 
                    "model": "CLIP ViT-L/14",
                    "evidence": []
                }

        try:
            print(f"[Semantic] Analyzing image bytes: {len(image_bytes)}")
            stream = io.BytesIO(image_bytes)
            stream.seek(0)
            image = Image.open(stream).convert('RGB')
            
            # Truncate claim to fits CLIP's context length (77 tokens usually)
            # CLIP handles truncation, but let's be safe passing it.
            inputs = self.processor(text=[claim], images=image, return_tensors="pt", padding=True, truncation=True).to(self.device)
            
            # Compute embeddings
            with torch.no_grad():
                outputs = self.model(**inputs)
                
            # CLIP returns logits_per_image which correlates to similarity
            # But we want the raw Cosine Similarity of the embeddings for a normalized score
            image_embeds = outputs.image_embeds
            text_embeds = outputs.text_embeds
            
            # Normalize
            image_embeds = image_embeds / image_embeds.norm(p=2, dim=-1, keepdim=True)
            text_embeds = text_embeds / text_embeds.norm(p=2, dim=-1, keepdim=True)
            
            # Cosine similarity
            cosine_score = torch.matmul(text_embeds, image_embeds.t()).item()
            
            # Heuristics for CLIP ViT-L/14
            # Raw cosine similarity in CLIP is often low (0.2 - 0.3 range even for matches)
            # We scale it roughly or just report logic based on a calibrated threshold.
            # "A photo of a [object]" usually matches > 0.25
            # Totally unrelated < 0.20
            # Exact match > 0.30
            # Note: This requires calibration. For now we use 0.23 as a soft threshold.
            
            status = "Consistent" if cosine_score > 0.23 else "Inconsistent"
            
            # Generate pseudo-evidence
            evidence = [
                {"type": "embedding", "content": f"CLIP Analysis: Encoded image and text into shared latent space."},
                {"type": "similarity", "content": f"CLIP Similarity Score: {cosine_score:.4f} (Threshold 0.23)"}
            ]

            return {
                "score": cosine_score,
                "status": status,
                "model": "CLIP ViT-L/14",
                "evidence": evidence
            }
            
        except Exception as e:
            print(f"Semantic Analysis Error: {e}")
            return {
                "score": 0.0,
                "status": "Error",
                "model": "Failed",
                "evidence": [{"type": "error", "content":str(e)}]
            }

semantic_stream = SemanticStream()
