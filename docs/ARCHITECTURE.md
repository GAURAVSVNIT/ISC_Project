# Echelon / Veritas - System Architecture

## 1. High-Level Multi-Stream Architecture

```mermaid
graph TD
    UserInput[User Input<br/>Image / Video / Audio] --> PreProcessor[Media Pre-Processor]
    
    subgraph PreProcessing
        PreProcessor -->|Image| ImgExtract[Image Extractor]
        PreProcessor -->|Video| FrameExtract[Frame Extraction]
        PreProcessor -->|Video| AudioExtract[Audio Extraction]
        PreProcessor -->|Audio| AudioNorm[Audio Normalization]
    end

    FrameExtract --> StreamA
    ImgExtract --> StreamA
    FrameExtract --> StreamB
    ImgExtract --> StreamB
    AudioExtract --> StreamD
    AudioNorm --> StreamD

    subgraph Streams
        StreamA[Stream A: Visual Forensics<br/>Pixel-level AI<br/>UniversalFakeDetect / ConvNeXt]
        StreamB[Stream B: Semantic Consistency<br/>Cross-Modal<br/>CLIP ViT-L/14]
        StreamD[Stream D: Audio Forensics<br/>Frequency-based<br/>Spectrogram CNN / Wav2Vec2]
        
        StreamC[Stream C: Context Grounding<br/>Reverse Search / Fact Check<br/>SerpAPI / XFacta]
    end

    StreamA --> Fusion[Fusion Controller<br/>Evidence Aggregator]
    StreamB --> Fusion
    StreamD --> Fusion
    StreamC --> Fusion

    Fusion --> Explanation[Reasoning & Explanation<br/>Final Verdict]
```

## 2. Execution Pipeline

### Routing Logic

1. **IF Image**:
    * Stream A (Visual)
    * Stream B (Semantic)
    * Stream C (Context)
2. **IF Audio**:
    * Stream D (Audio)
    * Stream C (Context - Optional)
3. **IF Video**:
    * **Frame Extraction**: Middle frame / Keyframes -> Analyzed as Image (Streams A & B)
    * **Audio Extraction**: Track isolated -> Analyzed as Audio (Stream D)
    * **Results Fusion**: Combined confidence score.

## 3. Stream Specifications

### Stream D: Audio Forensics

* **Preprocessing**: Resample (16kHz), Normalize, Windowing.
* **Features**: Phase Coherence, Band Energy, Temporal Artifacts.
* **Model**: `Hemgg/Deepfake-audio-detection` (Wav2Vec2).

### Stream A: Visual Forensics

* **Model**: `CNN_Finetune` (ResNet50/ConvNeXt) + `UniversalFakeDetect`.
* **Technique**: Frequency Domain Analysis (DCT), Error Level Analysis (ELA).
