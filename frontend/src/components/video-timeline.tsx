"use client";

import { useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { Film, AlertTriangle, Fingerprint } from "lucide-react";

export interface VideoTimelineFrame {
    index: number;
    time: number;
    score: number;
    thumb?: string;
}

export interface VideoSegment {
    start: number;
    end: number;
    peak: number;
    frames: number;
}

export interface VideoAnalysis {
    duration: number;
    width: number;
    height: number;
    fps: number;
    has_audio?: boolean;
    video_codec?: string | null;
    frames_analyzed: number;
    timeline: VideoTimelineFrame[];
    segments: VideoSegment[];
    peak_frame?: { index: number; time: number; score: number; image: string };
    drivers?: string[];
    notes?: string[];
}

export interface VideoProvenance {
    reason?: string;
    c2pa?: {
        present: boolean;
        ai_generated: boolean;
        digital_source_type?: string | null;
        generators?: string[];
    } | null;
    container?: { format?: string | null; encoder?: string | null; creation_time?: string | null };
}

interface VideoTimelineProps {
    video: VideoAnalysis;
    provenance?: VideoProvenance | null;
    fakeThreshold?: number;
    uncertainThreshold?: number;
}

function formatTime(seconds: number): string {
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const m = Math.floor(seconds / 60);
    const s = Math.round(seconds - m * 60);
    return `${m}:${s.toString().padStart(2, "0")}`;
}

export function VideoTimeline({
    video,
    provenance,
    fakeThreshold = 0.5,
    uncertainThreshold = 0.35,
}: VideoTimelineProps) {
    const frames = video.timeline ?? [];
    const peakIndex = frames.reduce((best, f, i) => (f.score > frames[best].score ? i : best), 0);
    const [selected, setSelected] = useState<number>(peakIndex);
    const current = frames[selected];

    const tone = (score: number) =>
        score >= fakeThreshold ? "fake" : score >= uncertainThreshold ? "unsure" : "real";
    const barColor = { fake: "bg-destructive", unsure: "bg-yellow-500", real: "bg-emerald-500" };
    const ringColor = { fake: "ring-destructive", unsure: "ring-yellow-500", real: "ring-emerald-500" };
    const textColor = { fake: "text-destructive", unsure: "text-yellow-500", real: "text-emerald-500" };

    const flagged = frames.filter((f) => f.score >= fakeThreshold).length;
    const c2pa = provenance?.c2pa;

    return (
        <Card className="overflow-hidden border-muted">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium uppercase tracking-wider text-muted-foreground">
                    Frame-by-frame scan
                </CardTitle>
                <Film className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent className="space-y-5">
                {/* Facts */}
                <div className="flex flex-wrap gap-2 text-xs">
                    {[
                        `${formatTime(video.duration)} long`,
                        `${video.width}×${video.height}`,
                        `${Math.round(video.fps)} fps`,
                        video.has_audio ? "has audio" : "no audio",
                        frames.length > 0 ? `${flagged} of ${frames.length} frames flagged` : "no frames scanned",
                    ].map((chip) => (
                        <span key={chip} className="px-2 py-1 rounded-md bg-muted/60 border border-border/40 font-mono">
                            {chip}
                        </span>
                    ))}
                </div>

                {frames.length > 0 && current && (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                        {/* Selected frame */}
                        <div className="md:col-span-1 space-y-2">
                            <div className={cn("relative rounded-lg overflow-hidden ring-2", ringColor[tone(current.score)])}>
                                {/* eslint-disable-next-line @next/next/no-img-element */}
                                <img
                                    src={`data:image/jpeg;base64,${
                                        selected === peakIndex && video.peak_frame?.image
                                            ? video.peak_frame.image
                                            : current.thumb
                                    }`}
                                    alt={`Frame at ${formatTime(current.time)}`}
                                    className="w-full h-auto object-cover"
                                />
                            </div>
                            <p className="text-xs text-muted-foreground">
                                Frame at <span className="font-mono">{formatTime(current.time)}</span>
                                {selected === peakIndex && " (most suspicious)"} —{" "}
                                <span className={cn("font-semibold", textColor[tone(current.score)])}>
                                    {(current.score * 100).toFixed(0)}% AI score
                                </span>
                            </p>
                        </div>

                        {/* Timeline */}
                        <div className="md:col-span-2 space-y-3">
                            {/* Score bars */}
                            <div className="relative h-24 flex items-end gap-[2px] border-b border-border/60">
                                <div
                                    className="absolute left-0 right-0 border-t border-dashed border-destructive/50 pointer-events-none"
                                    style={{ bottom: `${fakeThreshold * 100}%` }}
                                />
                                {frames.map((f, i) => (
                                    <button
                                        key={f.index}
                                        type="button"
                                        onClick={() => setSelected(i)}
                                        onMouseEnter={() => setSelected(i)}
                                        title={`${formatTime(f.time)} — ${(f.score * 100).toFixed(0)}%`}
                                        className="relative flex-1 h-full cursor-pointer"
                                        aria-label={`Frame at ${formatTime(f.time)}, AI score ${(f.score * 100).toFixed(0)} percent`}
                                    >
                                        <span
                                            className={cn(
                                                "absolute bottom-0 inset-x-0 rounded-t-sm transition-opacity",
                                                barColor[tone(f.score)],
                                                i === selected ? "opacity-100" : "opacity-60"
                                            )}
                                            style={{ height: `${Math.max(3, f.score * 100)}%` }}
                                        />
                                    </button>
                                ))}
                            </div>
                            <div className="flex justify-between text-[10px] text-muted-foreground font-mono">
                                <span>0s</span>
                                <span>dashed line = fake threshold</span>
                                <span>{formatTime(video.duration)}</span>
                            </div>

                            {/* Thumbnails */}
                            <div className="flex gap-1 overflow-x-auto pb-1">
                                {frames.map((f, i) => (
                                    <button
                                        key={f.index}
                                        type="button"
                                        onClick={() => setSelected(i)}
                                        className={cn(
                                            "shrink-0 w-16 rounded overflow-hidden border-b-4 cursor-pointer transition-opacity",
                                            f.score >= fakeThreshold
                                                ? "border-destructive"
                                                : f.score >= uncertainThreshold
                                                ? "border-yellow-500"
                                                : "border-emerald-500",
                                            i === selected ? "opacity-100 ring-1 ring-primary" : "opacity-70 hover:opacity-100"
                                        )}
                                    >
                                        {/* eslint-disable-next-line @next/next/no-img-element */}
                                        <img
                                            src={`data:image/jpeg;base64,${f.thumb}`}
                                            alt={`Frame at ${formatTime(f.time)}`}
                                            className="w-full h-10 object-cover"
                                        />
                                    </button>
                                ))}
                            </div>

                            {/* Flagged segments */}
                            {video.segments?.length > 0 && (
                                <div className="flex flex-wrap items-center gap-2 text-xs">
                                    <AlertTriangle className="w-3.5 h-3.5 text-destructive" />
                                    <span className="text-muted-foreground">Flagged:</span>
                                    {video.segments.map((seg, i) => (
                                        <span
                                            key={i}
                                            className="px-2 py-0.5 rounded-md bg-destructive/10 text-destructive border border-destructive/20 font-mono"
                                        >
                                            {seg.start === seg.end
                                                ? formatTime(seg.start)
                                                : `${formatTime(seg.start)} – ${formatTime(seg.end)}`}{" "}
                                            (peak {(seg.peak * 100).toFixed(0)}%)
                                        </span>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* Provenance + notes */}
                <div className="pt-4 border-t border-border/50 space-y-2 text-xs text-muted-foreground">
                    <p className="flex items-start gap-2">
                        <Fingerprint className="w-3.5 h-3.5 mt-0.5 shrink-0" />
                        <span>
                            <span className="font-semibold text-foreground">Provenance: </span>
                            {c2pa?.present
                                ? c2pa.ai_generated
                                    ? `Content Credentials (C2PA) declare this file AI-generated${
                                          c2pa.generators?.length ? ` — ${c2pa.generators.slice(0, 3).join(", ")}` : ""
                                      }.`
                                    : "Content Credentials (C2PA) found, with no AI-generation declaration."
                                : provenance?.reason ?? "No provenance metadata."}
                            {provenance?.container?.encoder && (
                                <span className="font-mono"> Encoder: {provenance.container.encoder}.</span>
                            )}
                        </span>
                    </p>
                    {video.notes?.map((note, i) => (
                        <p key={i} className="pl-5">
                            {note}
                        </p>
                    ))}
                </div>
            </CardContent>
        </Card>
    );
}
