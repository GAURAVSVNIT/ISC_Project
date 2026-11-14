"""
Verdict fusion for the video pipeline.

Only signals that actually detect synthetic media vote:
  - visual: frame-level AI-generation score (Stream V)
  - audio:  synthetic-voice score of the audio track (Stream D)

How they combine:
  - Visual at or above the threshold            -> Fake.
  - Visual clean but the voice is flagged       -> Uncertain (not Fake).
    The voice detector is the weaker of the two: in a spot check it flagged 1 of 4
    genuine human recordings as synthetic, so on its own it raises a warning but
    does not convict. Set VIDEO_AUDIO_CAN_CONVICT=true to make it decisive.
  - Scores are never averaged: a real clip with a cloned voice must not be
    averaged down to "authentic".

Claim-consistency (CLIP), web context and audio-visual similarity are shown to
the user but do not vote: they measure whether the claim matches the content,
not whether the content is synthetic.
"""

from typing import Any, Dict, List, Optional


def audio_is_usable(audio: Optional[Dict[str, Any]]) -> bool:
    """An audio result may vote only if the detector really ran on audible sound."""
    if not audio:
        return False
    if audio.get("usable") is False:
        return False
    status = str(audio.get("status", ""))
    if status.startswith("Error") or status.startswith("No Audio") or status.startswith("Silent"):
        return False
    return isinstance(audio.get("score"), (int, float))


def fuse_video(
    visual: Dict[str, Any],
    audio: Optional[Dict[str, Any]],
    threshold: float = 0.5,
    margin: float = 0.15,
    audio_can_convict: bool = False,
) -> Dict[str, Any]:
    """
    Returns {verdict, confidence_score, risk_score, drivers, notes}.
    verdict is "Fake", "Authentic" or "Uncertain".
    risk_score is the strongest detector score (0 = authentic, 1 = fake).
    """
    visual_score = float(visual["score"])
    drivers: List[str] = []
    notes: List[str] = []

    audio_score: Optional[float] = None
    if audio_is_usable(audio):
        audio_score = float(audio["score"])
    else:
        notes.append("Audio track did not contribute (missing, silent or failed).")

    visual_flag = visual_score >= threshold
    audio_flag = audio_score is not None and audio_score >= threshold
    if visual_flag:
        drivers.append("visual")
    if audio_flag:
        drivers.append("audio")

    risk = max(visual_score, audio_score) if audio_score is not None else visual_score

    if visual_flag or (audio_flag and audio_can_convict):
        verdict = "Fake"
        confidence = risk
    elif audio_flag:
        verdict = "Uncertain"
        confidence = 0.5
        notes.append(
            "The voice track is flagged as synthetic but the pictures are not. "
            "The voice detector alone is not reliable enough to call the video fake."
        )
    elif visual_score >= threshold - margin or visual.get("partial_suspicion"):
        verdict = "Uncertain"
        confidence = 0.5
        if visual.get("partial_suspicion"):
            notes.append("Part of the video is flagged while the rest looks clean.")
        else:
            notes.append("The visual score is close to the decision threshold.")
    else:
        verdict = "Authentic"
        confidence = 1.0 - risk

    return {
        "verdict": verdict,
        "confidence_score": float(confidence),
        "risk_score": float(risk),
        "drivers": drivers,
        "notes": notes,
    }
