"use client";

import { useState, useCallback, useRef } from "react";

export interface AnalysisProgress {
    stage: string;
    progress: number;
    message: string;
    status: "processing" | "success" | "error";
    results?: any;
}

export interface AnalysisHookReturn {
    analyze: (image: File, claim: string) => void;
    reset: () => void;
    progress: number;
    stage: string;
    message: string;
    results: any | null;
    isAnalyzing: boolean;
    error: string | null;
}

const UPLOAD_CHUNK_BYTES = 512 * 1024;

export function useRealtimeAnalysis(): AnalysisHookReturn {
    const [progress, setProgress] = useState(0);
    const [stage, setStage] = useState("");
    const [message, setMessage] = useState("");
    const [results, setResults] = useState<any | null>(null);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const wsRef = useRef<WebSocket | null>(null);

    const analyze = useCallback(
        async (image: File, claim: string) => {
            // Reset state
            setProgress(0);
            setStage("");
            setMessage("");
            setResults(null);
            setError(null);
            setIsAnalyzing(true);

            try {
                // Create WebSocket connection
                const ws = new WebSocket("ws://localhost:8000/ws/analyze");
                ws.binaryType = "arraybuffer";
                wsRef.current = ws;

                ws.onopen = async () => {
                    console.log("WebSocket connected");
                    try {
                        // Chunked upload: a JSON header, the file as binary frames, then an end marker.
                        // A single base64 JSON message is capped by the WebSocket message size
                        // (16 MB on the server), which most videos exceed.
                        ws.send(
                            JSON.stringify({
                                type: "start",
                                claim,
                                filename: image.name,
                                size: image.size,
                                enable_defense: true, // Enforced by default
                            })
                        );

                        setStage("upload");
                        const totalMb = (image.size / (1024 * 1024)).toFixed(1);
                        for (let offset = 0; offset < image.size; offset += UPLOAD_CHUNK_BYTES) {
                            if (ws.readyState !== WebSocket.OPEN) return;
                            const chunk = await image.slice(offset, offset + UPLOAD_CHUNK_BYTES).arrayBuffer();
                            ws.send(chunk);
                            // Let the socket drain so large files do not pile up in memory.
                            while (ws.bufferedAmount > 4 * UPLOAD_CHUNK_BYTES && ws.readyState === WebSocket.OPEN) {
                                await new Promise((resolve) => setTimeout(resolve, 20));
                            }
                            const sent = Math.min(offset + UPLOAD_CHUNK_BYTES, image.size);
                            setProgress(Math.round((sent / image.size) * 5));
                            setMessage(`Uploading ${(sent / (1024 * 1024)).toFixed(1)} / ${totalMb} MB...`);
                        }
                        if (ws.readyState === WebSocket.OPEN) {
                            ws.send(JSON.stringify({ type: "end" }));
                        }
                    } catch (err) {
                        setError(err instanceof Error ? err.message : "Upload failed");
                        setIsAnalyzing(false);
                        ws.close();
                    }
                };

                ws.onmessage = (event) => {
                    const data: AnalysisProgress = JSON.parse(event.data);

                    setProgress(data.progress);
                    setStage(data.stage);
                    setMessage(data.message);

                    if (data.stage === "complete" && data.results) {
                        setResults(data.results);
                        setIsAnalyzing(false);
                        ws.close();
                    } else if (data.stage === "error") {
                        setError(data.message);
                        setIsAnalyzing(false);
                        ws.close();
                    }
                };

                ws.onerror = (error) => {
                    console.error("WebSocket error:", error);
                    setError("Connection error occurred");
                    setIsAnalyzing(false);
                };

                ws.onclose = () => {
                    console.log("WebSocket closed");
                };
            } catch (err) {
                setError(err instanceof Error ? err.message : "Unknown error");
                setIsAnalyzing(false);
            }
        },
        []
    );

    const reset = useCallback(() => {
        setResults(null);
        setError(null);
        setStage("");
        setMessage("");
        setProgress(0);
        setIsAnalyzing(false);
    }, []);

    return {
        analyze,
        reset,
        progress,
        stage,
        message,
        results,
        isAnalyzing,
        error,
    };
}
