import axios from 'axios';

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'multipart/form-data',
  },
});

export interface AnalysisResult {
  visual: {
    score: number;
    status: string;
    label?: string; // Optional as mock might miss it
    model?: string;
  };
  semantic: {
    score: number;
    status: string;
    model: string;
    evidence: Array<{ type: string; content: string }>;
  };
  context: {
    evidence_found: boolean;
    sources: string[];
    summary: string;
  };
  audio?: {
    score: number;
    status: string;
    model: string;
    details?: {
      phase_coherence_avg: number;
      temporal_artifact_avg: number;
      windows_processed: number;
    }
  };
  metadata?: {
    verdict: string;
    confidence: string;
    ai_tags: string[];
    has_camera_metadata: boolean;
    should_short_circuit: boolean;
    reason: string;
  };
  cost_optimized: boolean;
  verdict: 'REAL' | 'FAKE' | 'UNCERTAIN';
  explanation: string;
}

export const analyzeImage = async (file: File, claim: string): Promise<AnalysisResult> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('claim', claim);

  const response = await api.post<AnalysisResult>('/analyze', formData);
  return response.data;
};

export default api;
