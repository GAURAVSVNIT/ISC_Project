import json
import os
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
from tqdm import tqdm

# --- Configuration ---
DATA_DIR = "backend/data"
JSON_PATH = os.path.join(DATA_DIR, "dev.json")
OUTPUT_DIR = "backend/weights/clip_finetuned"
BATCH_SIZE = 4 # Small batch for consumer GPU
EPOCHS = 5 # Increased for better convergence
LEARNING_RATE = 5e-6
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ... (Dataset class remains same) ...

class EchelonDataset(Dataset):
    def __init__(self, json_path, root_dir, processor):
        self.root_dir = root_dir
        self.processor = processor
        with open(json_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
            
        # Filter out missing images
        self.valid_data = []
        for item in self.data:
            # Fix paths: /projects/vig/hzy/XFacta/ -> backend/data/
            # Check likely subfolders
            for img_path in item['images']:
                # Extract relative path from expected structure
                # e.g. .../fake_sample/media/batchX/Y/images/img0.jpeg
                if "fake_sample" in img_path:
                    rel_path = img_path.split("fake_sample")[-1].lstrip("/\\")
                    full_path = os.path.join(root_dir, "fake_sample", rel_path)
                elif "real_sample" in img_path:
                    rel_path = img_path.split("real_sample")[-1].lstrip("/\\")
                    full_path = os.path.join(root_dir, "real_sample", rel_path)
                else:
                    full_path = img_path # fallback

                # Check if exists (some might be missing in sample data)
                if os.path.exists(full_path):
                    self.valid_data.append({
                        "text": item['text'],
                        "image_path": full_path,
                        "label": 1.0 if item['label'] else 0.0 # 1=Consistent, 0=Inconsistent
                    })
                    break # Take first available image per item
        
        print(f"Loaded {len(self.valid_data)} valid pairs out of {len(self.data)} entries.")

    def __len__(self):
        return len(self.valid_data)

    def __getitem__(self, idx):
        item = self.valid_data[idx]
        image = Image.open(item['image_path']).convert("RGB")
        text = item['text']
        label = torch.tensor(item['label'], dtype=torch.float32)

        # Truncate text to 77 tokens max
        inputs = self.processor(
            text=[text], 
            images=image, 
            return_tensors="pt", 
            padding="max_length", 
            truncation=True
        )
        
        # Squeeze batch dim from tokenizer
        return {
            "input_ids": inputs['input_ids'].squeeze(0),
            "attention_mask": inputs['attention_mask'].squeeze(0),
            "pixel_values": inputs['pixel_values'].squeeze(0),
            "label": label
        }

def train():
    # Check for existing checkpoint
    checkpoint_path = os.path.join(OUTPUT_DIR, "checkpoint")
    if os.path.exists(checkpoint_path) and os.path.exists(os.path.join(checkpoint_path, "config.json")):
        print(f"Resuming training from {checkpoint_path}...")
        model_name = checkpoint_path
    else:
        print(f"Initializing generic CLIP (ViT-L/14) on {DEVICE}...")
        model_name = "openai/clip-vit-large-patch14"

    model = CLIPModel.from_pretrained(model_name).to(DEVICE)
    processor = CLIPProcessor.from_pretrained(model_name)
    
    dataset = EchelonDataset(JSON_PATH, DATA_DIR, processor)
    if len(dataset) == 0:
        print("CRITICAL: No images found. Check path mapping.")
        return

    dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)
    
    optimizer = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE)
    criterion = nn.MSELoss() # Simple regression to target similarity (0 or 1)

    model.train()
    
    print(f"Starting Fine-tuning for {EPOCHS} epochs...")
    for epoch in range(EPOCHS):
        total_loss = 0
        progress = tqdm(dataloader, desc=f"Epoch {epoch+1}/{EPOCHS}")
        
        for batch in progress:
            input_ids = batch['input_ids'].to(DEVICE)
            attention_mask = batch['attention_mask'].to(DEVICE)
            pixel_values = batch['pixel_values'].to(DEVICE)
            labels = batch['label'].to(DEVICE)

            optimizer.zero_grad()
            
            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                pixel_values=pixel_values
            )
            
            # Helper to compute similarity manually since we want to regress it to a label
            # Get Embeddings
            img_embeds = outputs.image_embeds
            text_embeds = outputs.text_embeds
            
            # Normalize
            img_embeds = img_embeds / img_embeds.norm(p=2, dim=-1, keepdim=True)
            text_embeds = text_embeds / text_embeds.norm(p=2, dim=-1, keepdim=True)
            
            # Compute Cosine Similarity (Dot product of normalized vectors)
            # Both are (Batch, 768)
            logits = torch.sum(text_embeds * img_embeds, dim=1) # Shape: (Batch,)
            
            # Loss: MSE(Predicted_Similarity, Label)
            # Label is 1.0 (Consistent) or 0.0 (Inconsistent)
            # CLIP logits are raw dot products, usually -1 to 1.
            loss = criterion(logits, labels)
            
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            progress.set_postfix({"loss": loss.item()})

        print(f"Epoch {epoch+1} Complete. Avg Loss: {total_loss/len(dataloader):.4f}")

    # Save Checkpoint (HF format)
    save_path = os.path.join(OUTPUT_DIR, "checkpoint")
    print(f"Saving HF model to {save_path}...")
    model.save_pretrained(save_path)
    processor.save_pretrained(save_path)

    # Save PTH (State Dict)
    pth_path = os.path.join(OUTPUT_DIR, "finetuned_clip.pth")
    print(f"Saving .pth model to {pth_path}...")
    torch.save(model.state_dict(), pth_path)
    
    print("Retraining and Export Complete! ✅")

if __name__ == "__main__":
    train()
