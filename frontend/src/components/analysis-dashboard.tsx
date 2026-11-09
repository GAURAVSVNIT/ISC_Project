"use client";

import { useState } from "react";
import { marked } from "marked";
import { UploadZone } from "./upload-zone";
import { StreamCard } from "./stream-card";
import { VerdictBadge } from "./verdict-badge";
import {
    Eye,
    Brain,
    Globe,
    ShieldCheck,
    ShieldAlert,
    Sparkles,
    Music,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { useRealtimeAnalysis, AnalysisProgress } from "@/hooks/use-realtime-analysis";
import { LoadingOverlay } from "@/components/loading-overlay";

// Helper to map backend verdict to badge type
function mapVerdict(verdict: string): 'REAL' | 'FAKE' | 'UNCERTAIN' {
    if (!verdict) return 'UNCERTAIN';
    const v = verdict.toUpperCase();
    if (v === 'FAKE' || v === 'SYNTHETIC') return 'FAKE';
    if (v === 'AUTHENTIC' || v === 'REAL') return 'REAL';
    return 'UNCERTAIN';
}

interface StreamEvidence {
    content: string;
}

interface AnalysisResult {
    verdict: string;
    confidence_score: number;
    explanation: string;
    visual: {
        score: number;
        status: string;
        model: string;
        label?: string;
        heatmap?: string;
    };
    semantic: {
        score: number;
        status: string;
        model: string;
        evidence: StreamEvidence[];
    };
    context: {
        evidence_found: boolean;
        summary: string;
        sources: string[];
    };
    audio?: {
        score: number;
        status: string;
        model: string;
        details?: {
            phase_coherence_avg: number;
            temporal_artifact_avg: number;
            windows_processed: number;
        };
    };
    metadata?: {
        should_short_circuit: boolean;
        reason: string;
        ai_tags: string[];
    };
    cost_optimized: boolean;
    verification?: {
        block_index: number;
        block_hash: string;
        timestamp: number;
    };
}

export function AnalysisDashboard() {
    const {
        analyze,
        reset,
        progress,
        stage,
        message,
        results,
        isAnalyzing,
        error: wsError
    } = useRealtimeAnalysis();

    const [claim, setClaim] = useState("");
    const [localError, setLocalError] = useState<string | null>(null);

    // Sync WS results/error to local state for compatibility
    const error = wsError || localError;
    const result = results as AnalysisResult | null;

    const handleFileSelect = async (file: File) => {
        if (!claim.trim()) {
            setLocalError("Please enter a claim to verify.");
            return;
        }
        setLocalError(null);
        analyze(file, claim);
    };

    const resetAnalysis = () => {
        setClaim("");
        setLocalError(null);
        reset();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    return (
        <div className="w-full max-w-6xl mx-auto space-y-8 animate-in fade-in duration-500">
            {/* Upload Section */}
            {!result && (
                <div className="flex flex-col items-center justify-center min-h-[60vh]">
                    <div className="text-center mb-12 space-y-4">
                        <div className="inline-flex items-center justify-center p-3 rounded-2xl bg-primary/10 mb-4 ring-1 ring-primary/20">
                            <Sparkles className="w-6 h-6 text-primary" />
                        </div>
                        <h1
                            className="text-4xl md:text-6xl font-extrabold tracking-tight bg-gradient-to-b from-foreground to-foreground/60 bg-clip-text text-transparent">
                            Deepfake Detection
                        </h1>

                        <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
                            Advanced multi-stream analysis combining visual forensics,
                            semantic consistency, and internet context.
                        </p>
                    </div>

                    <div className="flex flex-col items-center gap-4 mb-8 w-full max-w-md mx-auto">
                        <div className="w-full">
                            <Input
                                placeholder="Enter claim to verify (e.g., 'Is this image real?')"
                                value={claim}
                                onChange={(e) => setClaim(e.target.value)}
                                className="h-12 text-lg text-center bg-card/50 backdrop-blur border-primary/20 focus:border-primary transition-all"
                                disabled={isAnalyzing}
                            />
                        </div>

                    </div>

                    {/* Debug: Log result structure to inspect missing context */}
                    {result && console.log("Analysis Result:", result)}

                    <UploadZone
                        onFileSelect={handleFileSelect}
                        isAnalyzing={isAnalyzing}
                    />
                    {error && (
                        <p className="text-destructive mt-4 font-medium text-center">{error}</p>
                    )}

                    <LoadingOverlay
                        isVisible={isAnalyzing}
                        progress={progress}
                        stage={stage}
                        message={message}
                    />
                </div>
            )}

            {/* Results Section */}
            {result && (
                <div className="space-y-8">
                    {/* Header with Verdict */}
                    <div className="flex flex-col md:flex-row items-center justify-between gap-6 p-8 rounded-2xl bg-card border border-border/50 shadow-2xl relative overflow-hidden group">
                        <div className="absolute inset-0 bg-gradient-to-r from-primary/5 via-transparent to-primary/5 opacity-0 group-hover:opacity-100 transition-opacity" />

                        <div className="space-y-2 relative z-10">
                            <h2 className="text-3xl font-bold tracking-tight">
                                Analysis Complete
                            </h2>
                            <div
                                className="text-muted-foreground max-w-xl [&>p]:mb-3 [&>ul]:list-disc [&>ul]:pl-5 [&>strong]:text-foreground [&>strong]:font-semibold"
                                dangerouslySetInnerHTML={{ __html: marked.parse(result.explanation || "No explanation available.") as string }}
                            />
                        </div>

                        <div className="flex flex-col items-end gap-3 relative z-10">
                            {result.cost_optimized && (
                                <div className="flex items-center gap-1.5 px-3 py-1 bg-emerald-500/10 text-emerald-500 rounded-full border border-emerald-500/20 text-xs font-medium tracking-wide">
                                    <Sparkles className="w-3.5 h-3.5" />
                                    <span>COST OPTIMIZED</span>
                                </div>
                            )}
                            {result.verification && (
                                <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-500/10 text-blue-400 rounded-full border border-blue-500/20 text-xs font-mono" title={`Full Hash: ${result.verification.block_hash}`}>
                                    <div className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
                                    <span>BLOCK #{result.verification.block_index}</span>
                                    <span className="text-muted-foreground">
                                        | {result.verification.block_hash.substring(0, 8)}...
                                    </span>
                                </div>
                            )}
                            <VerdictBadge
                                verdict={mapVerdict(result.verdict)}
                                className="text-lg px-6 py-3"
                            />
                            <Button variant="outline" onClick={resetAnalysis} size="sm">
                                Analyze Another
                            </Button>
                        </div>
                    </div>

                    {/* Streams Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

                        {/* Stream A: Visual */}
                        {!result.visual.status.includes("N/A") && (
                            <StreamCard
                                title="Visual Forensics"
                                icon={Eye}
                                type="visual"
                                status={result.visual.status}
                                score={result.visual.score}
                                description={
                                    result.visual.model || "ConvNeXt"
                                }
                            >
                                {result.visual.heatmap && (
                                    <div className="mt-4 pt-4 border-t border-border/50">
                                        <p className="text-xs font-semibold mb-2 uppercase text-muted-foreground flex items-center gap-2">
                                            <Sparkles className="w-3 h-3 text-red-500" />
                                            AI Artifact Map (Grad-CAM)
                                        </p>
                                        <div className="relative rounded-lg overflow-hidden border border-border/50 group/map">
                                            <img
                                                src={`data:image/png;base64,${result.visual.heatmap}`}
                                                alt="AI Heatmap"
                                                className="w-full h-auto object-cover"
                                            />
                                            <div className="absolute inset-0 bg-black/50 opacity-0 group-hover/map:opacity-100 transition-opacity flex items-center justify-center">
                                                <p className="text-white text-xs font-medium px-2 text-center">
                                                    Red areas indicate AI generation patterns
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </StreamCard>
                        )}

                        {/* Stream B: Semantic */}
                        {!result.semantic.status.includes("N/A") && (
                            <StreamCard
                                title="Semantic Consistency"
                                icon={Brain}
                                type="semantic"
                                status={result.semantic.status}
                                score={result.semantic.score}
                                description={result.semantic.model}
                            >
                                <div className="mt-4 pt-4 border-t border-border/50">
                                    <p className="text-xs font-semibold mb-2 uppercase text-muted-foreground">
                                        Evidence
                                    </p>
                                    <ul className="space-y-2">
                                        {result.semantic.evidence?.slice(0, 2).map((ev, i) => (
                                            <li key={i} className="text-xs p-2 rounded bg-muted/50">
                                                {ev.content}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            </StreamCard>
                        )}

                        {/* Stream D: Audio */}
                        {result.audio && (
                            <StreamCard
                                title="Audio Forensics"
                                icon={Music}
                                type="visual" // Reusing visual color style for now
                                status={result.audio.status}
                                score={result.audio.score}
                                description={result.audio.model}
                            >
                                {result.audio.details && (
                                    <div className="mt-4 pt-4 border-t border-border/50 space-y-3">
                                        <div className="flex justify-between text-xs">
                                            <span className="text-muted-foreground">Phase Coherence</span>
                                            <span className="font-mono">{result.audio.details.phase_coherence_avg?.toFixed(3)}</span>
                                        </div>
                                        <div className="flex justify-between text-xs">
                                            <span className="text-muted-foreground">Temporal Artifacts</span>
                                            <span className="font-mono">{result.audio.details.temporal_artifact_avg?.toFixed(4)}</span>
                                        </div>
                                        <div className="flex justify-between text-xs">
                                            <span className="text-muted-foreground">Windows Processed</span>
                                            <span className="font-mono">{result.audio.details.windows_processed}</span>
                                        </div>
                                    </div>
                                )}
                            </StreamCard>
                        )}


                        {/* Stream C: Context */}
                        {result.context && (
                            <StreamCard
                                title="Context Verification"
                                icon={Globe}
                                type="context"
                                status={result.context.evidence_found ? "Verified" : "Unverified"}
                                description={
                                    result.context.summary ? (
                                        <ul className="list-disc pl-4 space-y-1">
                                            {result.context.summary.split("\n-").map((line, i) => {
                                                const cleanedLine = line.replace(/^- /, "").trim();
                                                if (!cleanedLine) return null;
                                                return <li key={i}>{cleanedLine}</li>;
                                            })}
                                        </ul>
                                    ) : (
                                        "No external context found."
                                    )
                                }
                            >
                                {result.context.sources?.length > 0 && (
                                    <div className="mt-4 pt-4 border-t border-border/50">
                                        <p className="text-xs font-semibold mb-2 uppercase text-muted-foreground">
                                            Sources
                                        </p>
                                        <ul className="space-y-1">
                                            {result.context.sources.map((src, i) => (
                                                <li key={i}>
                                                    <a
                                                        href={src}
                                                        target="_blank"
                                                        rel="noreferrer"
                                                        className="text-xs text-primary hover:underline truncate block"
                                                    >
                                                        {src}
                                                    </a>
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                            </StreamCard>
                        )}

                        {/* Metadata Card (conditional) */}
                        {result.metadata && result.metadata.should_short_circuit && (
                            <StreamCard
                                title="Metadata Analysis"
                                icon={ShieldCheck}
                                type="visual"
                                status="AI Signature Found"
                                score={1.0}
                                description={`Reason: ${result.metadata.reason}`}
                            >
                                <div className="mt-4 pt-4 border-t border-border/50">
                                    <p className="text-xs text-muted-foreground flex items-center gap-2">
                                        <Sparkles className="w-3 h-3 text-primary" />
                                        EXIF data contains definitive AI generation tags.
                                    </p>
                                    {result.metadata.ai_tags.length > 0 && (
                                        <div className="mt-2 flex flex-wrap gap-1">
                                            {result.metadata.ai_tags.map((tag, i) => (
                                                <span
                                                    key={i}
                                                    className="px-1.5 py-0.5 rounded-md bg-destructive/10 text-destructive text-[10px] font-mono border border-destructive/20"
                                                >
                                                    {tag}
                                                </span>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            </StreamCard>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
