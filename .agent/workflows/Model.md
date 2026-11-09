---
description: Model Specification
---

# 🤖 Project Veritas: Model Specification

## Overview
This document specifies the AI models used in our multi-modal misinformation detection system. Each stream uses specialized models for its analysis task.

---

## Stream A: Visual Forensics (Fake Image Detection)

### Primary Model: UniversalFakeDetect

**Repository:** [WisconsinAIVision/UniversalFakeDetect](https://github.com/WisconsinAIVision/UniversalFakeDetect)

**Paper:** "Towards Universal Fake Image Detectors that Generalize Across Generative Models" (CVPR 2023)

**Authors:** Utkarsh Ojha*, Yuheng Li*, Yong Jae Lee (*Equal contribution)

#### Architecture
- **Backbone:** CLIP ViT-L/14 (frozen)
- **Classifier:** Linear layer trained on top of CLIP features
- **Key Innovation:** Uses CLIP's pre-trained feature space which generalizes across different generative models (GANs, Diffusion models, etc.)

#### Capabilities
- Detects fake images from:
  - **GANs:** ProGAN, CycleGAN, BigGAN, StyleGAN, etc.
  - **Diffusion Models:** LDM, GLIDE, Stable Diffusion, DALL-E
  - **Other Generators:** Deepfakes, Midjourney, etc.

#### Setup
```bash
# Clone repository
git clone https://github.com/Yuheng-Li/UniversalFakeDetect
cd UniversalFakeDetect

# Install dependencies
pip install torch torchvision
```

#### Pretrained Weights
Download from: `pretrained_weights/fc_weights.pth` (provided in repo)

#### Inference
```python
python validate.py \
    --arch=CLIP:ViT-L/14 \
    --ckpt=pretrained_weights/fc_weights.pth \
    --real_path <path_to_real> \
    --fake_path <path_to_fake>
```

#### Integration Notes
- Model outputs a confidence score (0-1) indicating probability of image being AI-generated
- Threshold of 0.5 is default for binary classification
- For our system, we'll return the raw score for nuanced verdicts

---

## Stream B: Semantic Consistency (Cross-Modal Misinformation Detection)

### Primary Framework: XFacta (Fine-tuned)

**Repository:** [neu-vi/XFacta](https://github.com/neu-vi/XFacta)

**Paper:** "XFacta: Contemporary, Real-World Dataset and Evaluation for Multimodal Misinformation Detection with Multimodal LLMs" (arXiv 2025)

**Authors:** Yuzhuo Xiao, Zeyu Han, Yuhan Wang, Huaizu Jiang

#### About
XFacta is a contemporary, real-world dataset designed for evaluating MLLM-based misinformation detectors. It provides a pipeline to automatically construct datasets based on current trending topics and systematically evaluates various MLLM-based detection strategies.

#### Architecture Options
- **OpenAI Models:** `openai/gpt-4o`
- **Gemini Models:** `gemini/flash-2.0`
- **Local Models:** Qwen2-VL-2B, Qwen2-VL-7B, Qwen2-VL-72B

#### Reasoning Approaches
| Approach | Description |
|----------|-------------|
| `cot_prompt_evidence` | Chain-of-Thought with evidence prompting |
| `prompt_ensembles_evidence` | Ensemble prompting with evidence |
| `self_consistency` | Self-consistency voting |
| `multi_step` | Multi-step reasoning pipeline |

#### Evidence Types
1. Extract text from images (OCR)
2. Generate images based on captions
3. Generate text based on captions
4. Retrieve news from DuckDuckGo
5. Retrieve text from DuckDuckGo
6. Retrieve images from DuckDuckGo
7. Question-based text evidence search
8. Question-based image evidence search

#### Dataset Structure
```
XFacta/
├── fake_sample/
│   ├── media/                     # Folder containing image batches
│   │   ├── batch1/                # Each contains 100 images
│   │   ├── ...
│   │   └── batch12/
│   ├── batch1.json                # Metadata for batch1
│   ├── ...
│   └── batch12.json
├── true_sample/
│   ├── media/
│   │   ├── batch1/
│   │   ├── ...
│   │   └── batch12/
│   ├── batch1.json
│   ├── ...
│   └── batch12.json
├── dev.json                       # Development split metadata
└── test.json                      # Test split metadata
```

**Dataset Download:** [Google Drive Link](https://drive.google.com/drive/folders/1Sj5Rr6TpbPNzWhUjQt60fRc6xSQD2DWK)

#### Setup
```bash
# Clone repository
git clone https://github.com/neu-vi/XFacta
conda create -n xfacta python=3.10
conda activate xfacta
cd XFacta
pip install -r requirements.txt

# Install modified dspy (for multi-image support)
cd dspy
pip install .[dev]
```

#### API Configuration
Create `.env` file:
```
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_VISION_API_KEY=your_google_vision_api_key_here
cse_id=your_custom_search_engine_id_here
```

#### Inference
```bash
python Predict.py \
    --llm_name openai/gpt-4o \
    --data_path /path/to/XFacta \
    --reasoning_approach cot_prompt_evidence \
    --dataset_split test \
    --include_evidences 1 4 5 \
    --top_k_evidence 5 \
    --filter_untrusted \
    --evidence_cache
```

#### Integration Notes
- We will **fine-tune** this framework on our use case
- Evidence retrieval provides grounding for cross-modal consistency checks
- Multi-step reasoning enables explainable detection
- Supports both API-based and local model deployment

---

## Stream C: Contextual Grounding (Reverse Image Search)

### API: SerpApi (Google Reverse Image Search)

**Documentation:** [SerpApi Reverse Image](https://serpapi.com/google-reverse-image)

#### Usage
```python
from serpapi import GoogleSearch

params = {
    "engine": "google_reverse_image",
    "image_url": "<image_url>",
    "api_key": "<SERPAPI_KEY>"
}

search = GoogleSearch(params)
results = search.get_dict()

# Extract key information
earliest_date = results.get("inline_images", [{}])[0].get("date")
origin_label = results.get("best_guess_label")
```

#### Integration Notes
- Compare `earliest_date` with user's claimed date
- Use `origin_label` to verify context (e.g., "Yellow Vest Protests 2018")
- Flag if image predates the claimed event

---

## Reasoning Core: Explanation Generation

### Model: GPT-4o (OpenAI)

**API:** OpenAI Chat Completions

#### System Prompt Design
```
You are an expert fact-checker analyzing multi-modal content for misinformation.
Given the following evidence from three analysis streams, provide:
1. A verdict: "Authentic", "Misleading", or "Fake"
2. A confidence score (0-1)
3. A natural language explanation citing specific evidence

Evidence:
- Visual Stream: {visual_result}
- Semantic Stream: {semantic_result}
- Context Stream: {context_result}
```

#### Integration Notes
- Use structured JSON output mode for consistent parsing
- Temperature: 0.3 (for consistent, factual responses)
- Max tokens: 500 (concise explanations)

---

## Adversarial Defense: Veritas Shield

### Method: Input Preprocessing (ART-inspired)

**Library:** Pillow + Custom filters

#### Techniques
1. **Gaussian Blur:** Remove high-frequency adversarial noise
2. **JPEG Compression:** Destroy subtle perturbations
3. **Resizing:** Disrupt pixel-level patterns

```python
from PIL import Image, ImageFilter

def shield_preprocess(image: Image.Image) -> Image.Image:
    # Gaussian blur
    image = image.filter(ImageFilter.GaussianBlur(radius=1))
    
    # JPEG compression (quality 85)
    buffer = io.BytesIO()
    image.save(buffer, format='JPEG', quality=85)
    buffer.seek(0)
    image = Image.open(buffer)
    
    # Slight resize down then up
    w, h = image.size
    image = image.resize((int(w*0.9), int(h*0.9)))
    image = image.resize((w, h))
    
    return image
```

---

## Model Performance Summary

| Stream | Model | Task | Expected Accuracy |
|--------|-------|------|-------------------|
| A | UniversalFakeDetect | Fake Image Detection | ~95% on known, ~85% on unseen |
| B | XFacta (Fine-tuned) | Cross-Modal Misinformation | MLLM-based with evidence retrieval |
| C | SerpApi | Context Search | Dependent on image indexing |
| Core | GPT-4o | Explanation Gen | High-quality NLG |

---

## Citations

```bibtex
@inproceedings{ojha2023fakedetect,
  title={Towards Universal Fake Image Detectors that Generalize Across Generative Models},
  author={Ojha, Utkarsh and Li, Yuheng and Lee, Yong Jae},
  booktitle={CVPR},
  year={2023}
}

@article{xiao2025xfacta,
  title={XFacta: Contemporary, Real-World Dataset and Evaluation for Multimodal Misinformation Detection with Multimodal LLMs},
  author={Xiao, Yuzhuo and Han, Zeyu and Wang, Yuhan and Jiang, Huaizu},
  journal={arXiv preprint arXiv:2508.09999},
  year={2025}
}
```
