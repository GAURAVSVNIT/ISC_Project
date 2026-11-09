"use client";

import { motion, AnimatePresence } from "framer-motion";
import { Shield, Eye, Brain, Globe, Check, Loader2 } from "lucide-react";

interface LoadingOverlayProps {
    isVisible: boolean;
    progress: number;
    stage: string;
    message: string;
}

const stageIcons: Record<string, any> = {
    defense: Shield,
    metadata: Eye,
    visual: Brain,
    semantic: Brain,
    context: Globe,
    complete: Check,
};

export function LoadingOverlay({
    isVisible,
    progress,
    stage,
    message,
}: LoadingOverlayProps) {
    const Icon = stageIcons[stage] || Loader2;

    return (
        <AnimatePresence>
            {isVisible && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="fixed inset-0 bg-black/90 backdrop-blur-sm z-50 flex items-center justify-center"
                >
                    <div className="relative w-full max-w-md px-8">
                        {/* Main card */}
                        <motion.div
                            initial={{ scale: 0.9, y: 20 }}
                            animate={{ scale: 1, y: 0 }}
                            className="bg-gradient-to-br from-neutral-900 to-neutral-950 border border-emerald-500/30 rounded-2xl p-8 shadow-2xl shadow-emerald-500/20"
                        >
                            {/* Icon */}
                            <div className="flex justify-center mb-6">
                                <motion.div
                                    animate={{ rotate: stage === "complete" ? 0 : 360 }}
                                    transition={{
                                        duration: 2,
                                        repeat: stage === "complete" ? 0 : Infinity,
                                        ease: "linear",
                                    }}
                                    className="relative"
                                >
                                    <Icon
                                        className={`w-16 h-16 ${stage === "complete"
                                                ? "text-emerald-500"
                                                : "text-emerald-400"
                                            }`}
                                    />
                                    {stage !== "complete" && (
                                        <motion.div
                                            className="absolute inset-0 bg-emerald-500/20 rounded-full blur-xl"
                                            animate={{
                                                scale: [1, 1.2, 1],
                                                opacity: [0.5, 0.8, 0.5],
                                            }}
                                            transition={{
                                                duration: 2,
                                                repeat: Infinity,
                                            }}
                                        />
                                    )}
                                </motion.div>
                            </div>

                            {/* Progress bar */}
                            <div className="mb-6">
                                <div className="h-2 bg-neutral-800 rounded-full overflow-hidden">
                                    <motion.div
                                        className="h-full bg-gradient-to-r from-emerald-500 to-cyan-500"
                                        initial={{ width: 0 }}
                                        animate={{ width: `${progress}%` }}
                                        transition={{ duration: 0.5, ease: "easeOut" }}
                                    />
                                </div>
                                <div className="flex justify-between mt-2 text-sm text-neutral-400">
                                    <span>{progress}%</span>
                                    <span className="text-emerald-400">{stage}</span>
                                </div>
                            </div>

                            {/* Message */}
                            <motion.p
                                key={message}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="text-center text-neutral-300 text-lg font-medium"
                            >
                                {message}
                            </motion.p>

                            {/* Scanning lines effect */}
                            {stage !== "complete" && (
                                <motion.div
                                    className="absolute inset-0 pointer-events-none"
                                    animate={{ backgroundPosition: ["0% 0%", "0% 100%"] }}
                                    transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                                    style={{
                                        backgroundImage:
                                            "repeating-linear-gradient(0deg, transparent, transparent 2px, rgb(16 185 129 / 0.05) 2px, rgb(16 185 129 / 0.05) 4px)",
                                        backgroundSize: "100% 20px",
                                    }}
                                />
                            )}

                            {/* Glitch effect for complete */}
                            {stage === "complete" && (
                                <motion.div
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: [0, 1, 0] }}
                                    transition={{ duration: 0.5 }}
                                    className="absolute inset-0 bg-emerald-500/10 rounded-2xl"
                                />
                            )}
                        </motion.div>

                        {/* Stage indicators */}
                        <div className="flex justify-center gap-2 mt-6">
                            {["metadata", "visual", "semantic", "context"].map((s, i) => (
                                <motion.div
                                    key={s}
                                    initial={{ scale: 0 }}
                                    animate={{ scale: 1 }}
                                    transition={{ delay: i * 0.1 }}
                                    className={`w-10 h-10 rounded-full flex items-center justify-center border-2 ${progress > (i + 1) * 20
                                            ? "bg-emerald-500/20 border-emerald-500"
                                            : "bg-neutral-900 border-neutral-700"
                                        }`}
                                >
                                    {progress > (i + 1) * 20 && (
                                        <Check className="w-5 h-5 text-emerald-500" />
                                    )}
                                </motion.div>
                            ))}
                        </div>
                    </div>
                </motion.div>
            )}
        </AnimatePresence>
    );
}
