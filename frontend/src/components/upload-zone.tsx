'use client';

import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, X, AlertCircle, Music, FileAudio, FileVideo } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface UploadZoneProps {
    onFileSelect: (file: File) => void;
    isAnalyzing: boolean;
}

export function UploadZone({ onFileSelect, isAnalyzing }: UploadZoneProps) {
    const [preview, setPreview] = useState<string | null>(null);
    const [fileType, setFileType] = useState<'image' | 'audio' | 'video' | null>(null);
    const [fileName, setFileName] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    const validateDuration = (file: File): Promise<boolean> => {
        return new Promise((resolve) => {
            const video = document.createElement('video');
            video.preload = 'metadata';
            video.onloadedmetadata = () => {
                window.URL.revokeObjectURL(video.src);
                resolve(video.duration <= 15);
            };
            video.onerror = () => {
                resolve(false); // Fail validation on error
            };
            video.src = URL.createObjectURL(file);
        });
    };

    const onDrop = useCallback(async (acceptedFiles: File[]) => {
        setError(null);
        const file = acceptedFiles[0];

        if (!file) return;

        const isImage = file.type.startsWith('image/');
        const isAudio = file.type.startsWith('audio/');
        const isVideo = file.type.startsWith('video/');

        if (!isImage && !isAudio && !isVideo) {
            setError('Please upload a supported file (Image, Audio, or Video).');
            return;
        }

        const MAX_SIZE = 100 * 1024 * 1024; // 100MB
        if (file.size > MAX_SIZE) {
            setError('File size must be less than 100MB.');
            return;
        }

        if (isVideo || isAudio) {
            const isValidDuration = await validateDuration(file);
            if (!isValidDuration) {
                setError('Media duration must be 15 seconds or less.');
                return;
            }
        }

        const objectUrl = URL.createObjectURL(file);
        setPreview(objectUrl);
        setFileType(isImage ? 'image' : isVideo ? 'video' : 'audio');
        setFileName(file.name);
        onFileSelect(file);
    }, [onFileSelect]);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'image/*': ['.jpeg', '.jpg', '.png', '.webp'],
            'audio/*': ['.mp3', '.wav', '.m4a'],
            'video/*': ['.mp4', '.webm', '.mov']
        },
        maxFiles: 1,
        disabled: isAnalyzing
    });

    const clearFile = (e: React.MouseEvent) => {
        e.stopPropagation();
        if (preview) URL.revokeObjectURL(preview); // Clean up memory
        setPreview(null);
        setFileType(null);
        setFileName(null);
        setError(null);
    };

    return (
        <div className="w-full max-w-2xl mx-auto mb-8">
            <div
                {...getRootProps()}
                className={cn(
                    "relative group cursor-pointer transition-all duration-300 ease-in-out",
                    "border-2 border-dashed rounded-xl p-8 text-center",
                    isDragActive ? "border-primary bg-primary/5" : "border-muted-foreground/25 hover:border-primary/50 hover:bg-muted/50",
                    preview ? "border-transparent p-0 overflow-hidden" : ""
                )}
            >
                <input {...getInputProps()} />

                {preview ? (
                    <div className="relative w-full rounded-xl flex items-center justify-center overflow-hidden bg-black/5 min-h-[160px] md:min-h-[320px]">

                        {fileType === 'image' ? (
                            // eslint-disable-next-line @next/next/no-img-element
                            <img
                                src={preview}
                                alt="Preview"
                                className="object-contain w-full h-full max-h-[320px]"
                            />
                        ) : fileType === 'video' ? (
                            <div className="flex flex-col items-center justify-center space-y-4 p-8 w-full">
                                <div className="w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center animate-pulse">
                                    <FileVideo className="w-10 h-10 text-primary" />
                                </div>
                                <div className="text-center">
                                    <p className="font-semibold text-foreground text-lg">{fileName}</p>
                                    <p className="text-sm text-muted-foreground">Video file loaded</p>
                                </div>
                                <video
                                    controls
                                    src={preview}
                                    onClick={(e) => e.stopPropagation()}
                                    className="w-full max-w-md mt-4 rounded-lg"
                                />
                            </div>
                        ) : (
                            <div className="flex flex-col items-center justify-center space-y-4 p-8 w-full">
                                <div className="w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center animate-pulse">
                                    <Music className="w-10 h-10 text-primary" />
                                </div>
                                <div className="text-center">
                                    <p className="font-semibold text-foreground text-lg">{fileName}</p>
                                    <p className="text-sm text-muted-foreground">Audio file loaded</p>
                                </div>
                                <audio
                                    controls
                                    src={preview}
                                    onClick={(e) => e.stopPropagation()}
                                    className="w-full max-w-md mt-4"
                                />
                            </div>
                        )}

                        <div className={cn(
                            "absolute inset-0 bg-black/40 transition-opacity flex items-center justify-center",
                            isAnalyzing ? "opacity-100" : "opacity-0 group-hover:opacity-100"
                        )}>
                            {!isAnalyzing && (
                                <Button
                                    variant="destructive"
                                    size="sm"
                                    onClick={clearFile}
                                    className="gap-2"
                                >
                                    <X className="w-4 h-4" /> Change File
                                </Button>
                            )}

                            {isAnalyzing && (
                                <div className="absolute inset-0 bg-background/80 backdrop-blur-sm flex flex-col items-center justify-center space-y-4 z-10">
                                    <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
                                    <p className="text-sm font-medium animate-pulse">Analyzing media...</p>
                                </div>
                            )}
                        </div>
                    </div>
                ) : (
                    <div className="flex flex-col items-center justify-center space-y-4 py-8">
                        <div className={`p-4 rounded-full bg-muted/50 transition-colors ${isDragActive ? 'bg-primary/20 text-primary' : ''}`}>
                            <Upload className="w-8 h-8 md:w-10 md:h-10 text-muted-foreground" />
                        </div>
                        <div className="space-y-1">
                            <p className="text-lg font-medium">
                                {isDragActive ? "Drop file here" : "Upload suspected media"}
                            </p>
                            <p className="text-sm text-muted-foreground">
                                Drag & drop or click to browse
                            </p>
                        </div>
                        <div className="flex flex-wrap items-center justify-center gap-2 text-xs text-muted-foreground/60">
                            <span className="flex items-center gap-1"><File className="w-3 h-3" /> Image, Audio & Video (≤ 15s)</span>
                            <span>•</span>
                            <span>Max 100MB</span>
                        </div>
                    </div>
                )}
            </div>

            {error && (
                <div className="mt-4 p-3 rounded-lg bg-destructive/10 text-destructive text-sm flex items-center gap-2 animate-in slide-in-from-top-2">
                    <AlertCircle className="w-4 h-4" />
                    {error}
                </div>
            )}
        </div>
    );
}
