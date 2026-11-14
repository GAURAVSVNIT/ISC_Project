# Video Detection Pipeline

How an uploaded video becomes a verdict, what was measured, and what it cannot do yet.

## Flow

```
upload (REST multipart, or WebSocket chunked)
  │
  ├─ 1. Probe            ffprobe/OpenCV: duration, fps, resolution, audio track, tags
  │                      not a video → error; audio-only container (.m4a) → audio pipeline
  ├─ 2. Provenance       C2PA Content Credentials + AI-tool tags in the container
  │                      file declares itself AI-made → verdict Fake, models skipped
  ├─ 3. Decode           8–24 frames spread evenly over the whole video; audio → 16 kHz WAV
  ├─ 4. Stream V         every frame scored by the AI-generation detector
  │                      → per-frame timeline, flagged time segments, most suspicious frame
  ├─ 5. Stream D         synthetic-voice detector on the audio track (skipped if silent)
  │      + claim check (CLIP) and web context — shown, but they do not vote
  ├─ 6. Fusion           visual + audio → Fake / Uncertain / Authentic
  └─ 7. Report           LLM explanation + ledger block containing the file's SHA-256
```

| Step | Code |
|---|---|
| Decode, probe, audio extraction | `backend/utils/video_processor.py` |
| Provenance (C2PA, tags) | `backend/utils/video_metadata.py` |
| Frame detector, timeline, segments | `backend/streams/video.py` |
| Fusion rules | `backend/core/fusion.py` |
| Orchestration | `Orchestrator.process_video_request` in `backend/core/orchestrator.py` |
| API (REST + WebSocket) | `backend/main.py` |
| UI | `frontend/src/components/video-timeline.tsx` |
| Settings | `VIDEO_*` in `backend/config.py` (overridable in `.env`) |

## Verdict rules

- **Fake**: the average frame score is ≥ 0.5, or the file's own metadata declares it AI-generated.
- **Uncertain**: the frame score is 0.35–0.5; or a run of frames is flagged while the rest is clean
  (possible spliced segment); or only the voice is flagged.
- **Authentic**: none of the above.

A flagged voice alone gives *Uncertain*, not *Fake*. In a spot check the voice detector called
1 of 4 genuine human recordings synthetic, so it warns but does not convict. Set
`VIDEO_AUDIO_CAN_CONVICT=true` to change that.

A detector that fails to load or run produces an error, never a verdict.

## Which detector, and why

The image detector used for still images (Genesis ConvNeXt) was tested on video frames first and
was close to chance. Candidates were then compared on 63 clips: 29 real (Pexels stock footage and
camera samples) and 34 AI-generated (AnimateDiff, CogVideoX, Runway, Stable Video Diffusion, Veo,
VideoPoet from the DeepAction dataset, plus two Sora clips). ROC-AUC, mean score over 8 frames:

| Detector | AUC |
|---|---|
| Genesis ConvNeXt (image pipeline) | 0.62 |
| UniversalFakeDetect (CLIP + `fc_weights.pth`) | 0.61 |
| Organika/sdxl-detector | 0.57 |
| Ateeqq/ai-vs-human-image-detector | 0.60 |
| haywoodsloan/ai-image-detector-deploy | 0.76 |
| **Community Forensics ViT-S/384** | **0.90** |

Community Forensics is used (`buildborderless/CommunityForensics-DeepfakeDet-ViT`, MIT licence,
84 MB, revision pinned in config). Each frame is scored on one resized view and five
native-resolution crops, which preserves the fine pixel detail the detector relies on.

### Result of the full pipeline on the same 63 clips

Metadata ignored, so this measures the pixel detector alone:

| | Authentic | Uncertain | Fake |
|---|---|---|---|
| 29 real clips | 27 | 2 | **0** |
| 34 AI clips | **9** | 0 | 25 |

ROC-AUC 0.94. All nine misses are Google Veo (6), Sora (2) and one CogVideoX clip.
With metadata enabled the verdict counts are the same; 5 Runway clips are caught by their C2PA
manifest before any model runs.

Reproduce or test your own data (`dataset/real/*.mp4`, `dataset/fake/*.mp4`):

```
python -m backend.benchmarks.eval_video /path/to/dataset --no-metadata --csv results.csv
```

## Limits — read before trusting a verdict

- **63 clips is a small sample**, and the detector choice was made on it. Expect lower accuracy on
  other data. Build a larger test set before quoting numbers.
- **Newer generators are missed.** Veo and Sora clips mostly scored as authentic. "Authentic"
  means "no known fingerprint found", not "proven real".
- **Face-swap and lip-sync deepfakes are not covered.** The detector looks for fully generated
  imagery. A real video with a swapped face was not tested and will likely pass.
- **No temporal model.** Frames are judged one by one; motion inconsistencies are not analysed.
- **Voice detector is weak** (see above) and is meant for speech, not music or ambient sound.
- **C2PA signatures are not validated.** The manifest is read, not cryptographically verified, and
  metadata disappears when a video is re-encoded or passed through social media.
- Heavy compression and screen recordings were not tested.

## Operation

- First use downloads the detector from Hugging Face (84 MB) into the HF cache.
- `ffmpeg` is required for audio; `ffprobe` is used when present (falls back to OpenCV).
- Uploads over WebSocket use a chunked protocol: `{"type":"start","claim","filename","size"}`,
  binary frames, `{"type":"end"}`. The old single-message base64 form still works for small files.
- `VIDEO_AV_CONSISTENCY=true` adds the ImageBind audio-visual similarity card (4.8 GB model).
  It is informational and never changes the verdict.
- Tests: `python -m pytest backend/tests/test_video_pipeline.py` (no weights or network needed).
