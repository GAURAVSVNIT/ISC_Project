import librosa
import numpy as np
import torch
import soundfile as sf
import io
import os
from transformers import AutoFeatureExtractor, AutoModelForAudioClassification
from typing import List, Dict, Any, Tuple


class AudioStream:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.feature_extractor = None
        self.is_ready = False
        self.model_name = "Hemgg/Deepfake-audio-detection"  # Or "bisher/wav2vec2-asv-deepfake"

    def _ensure_models_loaded(self):
        """
        Lazy load the Wav2Vec2-based deepfake detection model.
        """
        if self.is_ready:
            return True
        
        try:
            print(f"Loading Audio Stream Model ({self.model_name}) on {self.device}...")
            self.feature_extractor = AutoFeatureExtractor.from_pretrained(self.model_name)
            self.model = AutoModelForAudioClassification.from_pretrained(self.model_name).to(self.device)
            self.model.eval()
            self.is_ready = True
            print("Audio Stream Loaded Successfully.")
            return True
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error loading Audio Stream: {e}")
            self.is_ready = False
            return False

    def preprocess_audio(self, file_bytes: bytes, sr=16000, duration=3.0) -> Tuple[List[np.ndarray], int]:
        """
        Load, normalize, and segment the audio.
        """
        try:
            # Load audio from bytes
            y, _ = librosa.load(io.BytesIO(file_bytes), sr=sr)
            
            # Normalize
            y = librosa.util.normalize(y, norm=np.inf)
            max_val = np.max(np.abs(y))
            if max_val > 0:
                y /= max_val
            
            # Segment into windows
            # If audio is shorter than duration, pad it
            total_samples = len(y)
            window_samples = int(sr * duration)
            
            if total_samples < window_samples:
                y = librosa.util.fix_length(y, size=window_samples)
                windows = [y]
            else:
                frames = librosa.util.frame(y, frame_length=window_samples, hop_length=int(sr * 0.5))
                windows = [librosa.util.fix_length(frame, size=window_samples) for frame in frames.T]

            return windows, sr
        except Exception as e:
            print(f"Error in audio preprocessing: {e}")
            return [], sr

    def extract_features(self, audio_window: np.ndarray, sr=16000) -> Dict[str, Any]:
        """
        Extract acoustic features for analysis (Mel-spec, phase coherence, etc.).
        Note: The Transformer model typically takes raw waveform, but these features
        are useful for the 'explanation' or potential fusion.
        """
        try:
            n_fft = 2048
            hop_length = 512
            n_mels = 128
            
            # Mel-spectrogram
            mel = librosa.feature.melspectrogram(y=audio_window, sr=sr, n_mels=n_mels, n_fft=n_fft, hop_length=hop_length)
            mel_db = librosa.amplitude_to_db(mel, ref=np.max)
            
            # STFT for phase
            stft = librosa.stft(audio_window, n_fft=n_fft, hop_length=hop_length)
            mag, phase = librosa.magphase(stft)
            
            # Phase coherence
            phase_unwrap = np.angle(np.unwrap(np.angle(phase), axis=0))
            if phase_unwrap.shape[1] > 1:
                phase_coherence = np.std(np.diff(phase_unwrap, axis=0), axis=0).mean()
            else:
                phase_coherence = 0.0
            
            # Frequency band energy
            bands = librosa.feature.rms(S=mag, frame_length=hop_length)
            cutoff = sr // 2 // 4 # Approx 4kHz
            low_band = librosa.feature.rms(S=mag[:cutoff])
            high_band = librosa.feature.rms(S=mag[cutoff:2*cutoff])
            
            band_energy_mean = np.mean([low_band.mean(), high_band.mean()])
            
            # Energy Variance (Temporal artifacts)
            energy_var = np.var(librosa.feature.rms(y=audio_window))
            
            return {
                # 'mel': mel_db, # Too large to return in JSON usually, handle separately if needed
                'phase_coherence': float(phase_coherence),
                'band_energy_mean': float(band_energy_mean),
                'energy_var': float(energy_var)
            }
        except Exception as e:
            print(f"Feature extraction error: {e}")
            return {}

    async def analyze(self, file_bytes: bytes) -> Dict[str, Any]:
        """
        Main analysis pipeline for Stream D.
        """
        if not self.is_ready:
            success = self._ensure_models_loaded()
            if not success:
                return {
                    "score": 0.0,
                    "status": "Error: Model failed to load",
                    "model": self.model_name
                }
                
        try:
            # 1. Preprocess
            windows, sr = self.preprocess_audio(file_bytes)
            if not windows:
                return {"score": 0.0, "status": "Error: Processing failed", "model": self.model_name}

            probs = []
            features_list = []

            # 2. Inference & Feature Extraction per window
            for window in windows:
                # Model Inference
                inputs = self.feature_extractor(window, sampling_rate=sr, return_tensors="pt")
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                
                with torch.no_grad():
                    outputs = self.model(**inputs)
                    # Class 0: Real, Class 1: Fake (usually, depends on specific model)
                    # For 'Hemgg/Deepfake-audio-detection', check model card labels.
                    # Assuming [Real, Fake] for now.
                    prob = torch.softmax(outputs.logits, dim=-1)[0][1].item()
                    probs.append(prob)
                
                # Feature Extraction (for explanation)
                feats = self.extract_features(window, sr)
                features_list.append(feats)

            # 3. Aggregation
            ai_prob = float(np.mean(probs))
            
            # Aggregate features for reporting
            avg_phase = float(np.mean([f.get('phase_coherence', 0) for f in features_list]))
            avg_energy_var = float(np.mean([f.get('energy_var', 0) for f in features_list]))

            status = "Synthetic/Fake" if ai_prob > 0.5 else "Authentic Audio"
            
            return {
                "score": ai_prob,
                "status": status,
                "model": self.model_name,
                "details": {
                    "phase_coherence_avg": avg_phase,
                    "temporal_artifact_avg": avg_energy_var,
                    "windows_processed": len(windows)
                }
            }
            
        except Exception as e:
            print(f"Audio Stream Analysis Error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "score": 0.0, 
                "status": f"Error: {str(e)}", 
                "model": self.model_name
            }

# Global instance
audio_stream = AudioStream()
