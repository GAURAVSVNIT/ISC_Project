import torch
import torch.nn as nn
import timm
from torchvision import transforms
from PIL import Image
import io
import os
import cv2
import numpy as np
import base64
from backend.config import settings

class GenesisStream:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.is_ready = False
        self._load_model()

    def _load_model(self):
        """
        Load ConvNeXt Large with custom head.
        """
        # Resolve path relative to this file's location
        current_dir = os.path.dirname(os.path.abspath(__file__))
        weights_path = os.path.join(current_dir, "../weights/best_convnext_large.pth")
        weights_path = os.path.normpath(weights_path)  # Normalize path
        
        if not os.path.exists(weights_path):
            print(f"Genesis Stream: Weights not found at {weights_path}. Running in degraded mode.")
            return

        try:
            print(f"Loading Genesis (ConvNeXt Large) on {self.device}...")
            # 1. Create Model Structure
            self.model = timm.create_model("convnext_large", pretrained=False) # No need for pretrained if loading full state
            
            # 2. Modify Head (As per app.py)
            n_features = self.model.head.fc.in_features
            self.model.head.fc = nn.Sequential(
                nn.Dropout(0.2),
                nn.Linear(n_features, 2)
            )
            
            # 3. Load Weights
            checkpoint = torch.load(weights_path, map_location=self.device)
            # Handle potential state dict nesting
            state_dict = checkpoint["model_state_dict"] if "model_state_dict" in checkpoint else checkpoint
            self.model.load_state_dict(state_dict)
            
            self.model.to(self.device)
            self.model.eval()
            self.is_ready = True
            print("Genesis Stream Loaded Successfully.")

        except Exception as e:
            print(f"Error loading Genesis Stream: {e}")
            self.is_ready = False
    
    def generate_gradcam(self, image_tensor, original_image: Image.Image, target_class=0):
        """
        Generate Grad-CAM heatmap visualization.
        Shows WHERE the model detected AI artifacts.
        """
        if not self.is_ready:
            return None
        
        try:
            # Storage for activations and gradients
            activations = []
            gradients = []
            
            # Hook functions
            def forward_hook(module, input, output):
                activations.append(output.detach())
            
            def backward_hook(module, grad_input, grad_output):
                gradients.append(grad_output[0].detach())
            
            # Register hooks on the final convolutional stage
            target_layer = self.model.stages[-1]  # Last ConvNeXt stage
            h_forward = target_layer.register_forward_hook(forward_hook)
            h_backward = target_layer.register_full_backward_hook(backward_hook)
            
            # Forward pass
            self.model.zero_grad()
            output = self.model(image_tensor)
            
            # Backward pass on target class (0 = Fake)
            output[0, target_class].backward()
            
            # Remove hooks
            h_forward.remove()
            h_backward.remove()
            
            # Get activations and gradients
            acts = activations[0][0]  # Shape: [C, H, W]
            grads = gradients[0][0]   # Shape: [C, H, W]
            
            # Global average pooling on gradients to get weights
            weights = grads.mean(dim=(1, 2))  # Shape: [C]
            
            # Weighted combination of activation maps
            cam = torch.zeros(acts.shape[1:], device=self.device)
            for i, w in enumerate(weights):
                cam += w * acts[i]
            
            # Apply ReLU and normalize
            cam = torch.relu(cam)
            if cam.max() > 0:
                cam = cam / cam.max()
            
            # Convert to numpy
            cam_numpy = cam.cpu().numpy()
            
            # Resize to original image size
            cam_resized = cv2.resize(cam_numpy, (original_image.width, original_image.height))
            
            # Apply colormap (Jet: blue=low, red=high activation)
            heatmap_colored = cv2.applyColorMap(np.uint8(255 * cam_resized), cv2.COLORMAP_JET)
            
            # Convert BGR to RGB
            heatmap_rgb = cv2.cvtColor(heatmap_colored, cv2.COLOR_BGR2RGB)
            
            # Blend with original image (50% opacity)
            original_array = np.array(original_image.convert('RGB'))
            blended = cv2.addWeighted(original_array, 0.6, heatmap_rgb, 0.4, 0)
            
            # Encode to base64
            _, buffer = cv2.imencode('.png', cv2.cvtColor(blended, cv2.COLOR_RGB2BGR))
            heatmap_base64 = base64.b64encode(buffer).decode('utf-8')
            
            return heatmap_base64
            
        except Exception as e:
            print(f"Grad-CAM generation error: {e}")
            return None

    async def analyze(self, image_bytes: bytes, generate_heatmap: bool = True) -> dict:
        """
        Analyze image using ConvNeXt.
        """
        if not self.is_ready:
            return {"score": 0.0, "status": "Error: Model not loaded", "model": "Genesis (Failed)"}

        try:
            print(f"[Genesis] Analyzing image bytes: {len(image_bytes)}")
            stream = io.BytesIO(image_bytes)
            stream.seek(0)
            
            original_image = Image.open(stream)
            image = original_image.convert("RGB")
            
            # Preprocessing (From app.py)
            transform = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.Lambda(lambda x: x.convert("RGB")),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225]
                )
            ])
            
            img_tensor = transform(image).unsqueeze(0).to(self.device)

            with torch.no_grad():
                output = self.model(img_tensor)
                # Output shape: [1, 2] (Logits for Real/Fake?)
                # app.py says: pred_class = output.argmax(dim=1).item()
                # label = "AI-Generated" if pred == 0 else "Real"
                # Wait, if 0 is AI-Generated, then Index 0 = Fake, Index 1 = Real?
                # Let's verify prediction logic in app.py
                
                probs = torch.softmax(output, dim=1)
                fake_prob = probs[0][0].item() # Assuming Index 0 is Fake based on app.py logic
                real_prob = probs[0][1].item()
                
                # app.py: label = "AI-Generated" if pred == 0 else "Real"
                # This confirms Index 0 is the "Positive" class for detection (AI-Generated).
                
                score = fake_prob 
                status = "Synthetic/Fake" if score > 0.5 else "Authentic Media"

                label = "Deepfake" if score > 0.5 else "Real"

            # Generate Grad-CAM heatmap (Must be outside torch.no_grad)
            heatmap = None
            if generate_heatmap and score > 0.3:  # Only generate for suspicious images
                 heatmap = self.generate_gradcam(img_tensor, original_image, target_class=0)
            result = {
                "score": score,
                "status": status,
                "label": label,
                "model": "Genesis (ConvNeXt)",
                "details": {
                    "fake_prob": fake_prob,
                    "real_prob": real_prob
                }
            }
            
            if heatmap:
                result["heatmap"] = heatmap
                
            return result

        except Exception as e:
            print(f"Genesis Inference Error: {e}")
            return {"score": 0.0, "status": f"Error: {e}"}

# Singleton instance
genesis_stream = GenesisStream()
