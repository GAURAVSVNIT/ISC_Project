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
                // Convert image to base64
                const base64Image = await new Promise<string>((resolve, reject) => {
                    const reader = new FileReader();
                    reader.onload = () => {
                        const base64 = (reader.result as string).split(",")[1];
                        resolve(base64);
                    };
                    reader.onerror = reject;
                    reader.readAsDataURL(image);
                });

                // Create WebSocket connection
                const ws = new WebSocket("ws://localhost:8000/ws/analyze");
                wsRef.current = ws;

                ws.onopen = () => {
                    console.log("WebSocket connected");
                    ws.send(
                        JSON.stringify({
                            image: base64Image,
                            claim,
                            enable_defense: true, // Enforced by default
                        })
                    );
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
