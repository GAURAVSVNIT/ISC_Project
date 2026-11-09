## Preprocessing

- Resample audio to fixed rate (e.g., 16 kHz)
- Normalize amplitude
- Segment into fixed-length windows


```
INPUT
 │
 ├─► If IMAGE
 │     ├─ Stream A (Visual)
 │     ├─ Stream B (Image + Text)
 │     └─ Stream C (Reverse Search)
 │
 ├─► If AUDIO
 │     ├─ Stream D (Frequency-based Audio AI Detection)
 │     └─ (Optional) Stream E if transcript exists
 │
 └─► If VIDEO
       ├─ Extract frames → Stream A
       ├─ Extract audio  → Stream D
       ├─ Audio-Video sync → Stream E
       ├─ Semantic checks → Stream B
       └─ Context search → Stream C


ALL STREAM RESULTS
 │
 └─► Evidence Fusion
       ├─ Agreement check
       ├─ Out-of-bound mismatch detection
       └─ Confidence calibration
 │
 └─► Explanation Generator
```