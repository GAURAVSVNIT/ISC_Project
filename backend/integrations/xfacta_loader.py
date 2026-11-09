import json
import os
from PIL import Image

class XFactaLoader:
    def __init__(self, base_path="XFacta"):
        self.base_path = base_path
        
    def load_batch(self, batch_num=1, split="fake_sample"):
        """
        Loads a specific batch of XFacta data.
        Returns: List of (image_path, claim, label)
        """
        # Adjust path based on actual folder structure if needed
        json_path = os.path.join(self.base_path, split, f"batch{batch_num}.json")
        media_dir = os.path.join(self.base_path, split, "media", f"batch{batch_num}")
        
        if not os.path.exists(json_path):
             # Try determining path relative to data dir if absolute path fails
             print(f"Warning: JSON file not found at {json_path}")
             return []

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        dataset = []
        for item in data:
            # XFacta JSON structure: tweet_id, ooc_tweet, flagging_tweet
            tweet_data = item.get('ooc_tweet', {})
            img_list = tweet_data.get('images', [])
            
            if not img_list:
                continue
                
            img_rel_path = img_list[0] # e.g., "./media/batch1/1/images/img0.jpeg"
            claim = tweet_data.get('text', "")
            
            # Construct full path
            # base_path/split/img_rel_path
            # normpath handles the './' in img_rel_path
            full_img_path = os.path.normpath(os.path.join(self.base_path, split, img_rel_path))
            
            if os.path.exists(full_img_path):
                dataset.append({
                    "image": full_img_path,
                    "claim": claim,
                    "label": "FAKE" if split == "fake_sample" else "REAL"
                })
            else:
                 # Debug check: only print for first few failures to avoid spam
                 if len(dataset) == 0:
                     print(f"DEBUG: Image not found at {full_img_path}")
                
        return dataset
