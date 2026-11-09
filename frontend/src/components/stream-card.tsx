import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { CheckCircle2, XCircle, AlertCircle } from "lucide-react";

interface StreamCardProps {
    title: string;
    icon: React.ElementType;
    score?: number;
    status: string; // "Consistent", "Tampered", etc.
    description?: string | React.ReactNode;
    isLoading?: boolean;
    type: 'visual' | 'semantic' | 'context';
    children?: React.ReactNode;
}

export function StreamCard({
    title,
    icon: Icon,
    score,
    status,
    description,
    isLoading,
    type,
    children
}: StreamCardProps) {

    // Determine color based on status/score logic (simplified for now)
    const getStatusColor = () => {
        if (isLoading) return "text-muted-foreground";
        const s = status.toLowerCase();
        // Check negative first to avoid partial matches (e.g. "inconsistent" contains "consistent")
        if (s.includes("fake") || s.includes("inconsistent") || s.includes("manipulated")) return "text-destructive";
        if (s.includes("consistent") || s.includes("real") || s.includes("authentic") || s.includes("verified")) return "text-emerald-500";
        return "text-yellow-500";
    };

    const statusColor = getStatusColor();

    return (
        <Card className="overflow-hidden border-muted transition-all hover:border-primary/50 hover:shadow-lg">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium uppercase tracking-wider text-muted-foreground">
                    {title}
                </CardTitle>
                <Icon className={cn("h-4 w-4", statusColor)} />
            </CardHeader>
            <CardContent>
                {isLoading ? (
                    <div className="h-24 flex items-center justify-center">
                        <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                    </div>
                ) : (
                    <div className="space-y-4">
                        <div className="flex items-end justify-between">
                            <div>
                                <div className={cn("text-2xl font-bold", statusColor)}>
                                    {status}
                                </div>
                                {score !== undefined && (
                                    <p className="text-xs text-muted-foreground mt-1">
                                        Confidence: {status.toLowerCase().includes("authentic") || status.toLowerCase().includes("real") || status.toLowerCase().includes("inconsistent")
                                            ? ((1 - score) * 100).toFixed(1)
                                            : (score * 100).toFixed(1)}%
                                    </p>
                                )}
                            </div>
                            {score !== undefined && (
                                <div className="w-16 h-16 rounded-full border-4 border-muted flex items-center justify-center relative">
                                    <svg className="absolute inset-0 w-full h-full -rotate-90" viewBox="0 0 32 32">
                                        <circle cx="16" cy="16" r="14" fill="none" stroke="currentColor" strokeWidth="4" className="text-muted/20" />
                                        <circle
                                            cx="16"
                                            cy="16"
                                            r="14"
                                            fill="none"
                                            stroke="currentColor"
                                            strokeWidth="4"
                                            strokeDasharray={`${(status.toLowerCase().includes("authentic") || status.toLowerCase().includes("real") || status.toLowerCase().includes("inconsistent") ? (1 - score) : score) * 88} 100`}
                                            className={statusColor}
                                        />
                                    </svg>
                                    <span className="text-[10px] font-bold">
                                        {(status.toLowerCase().includes("authentic") || status.toLowerCase().includes("real") || status.toLowerCase().includes("inconsistent")
                                            ? (1 - score) * 10
                                            : score * 10).toFixed(1)}
                                    </span>
                                </div>
                            )}
                        </div>
                        {description && (
                            <div className="text-xs text-muted-foreground">
                                {description}
                            </div>
                        )}
                        {children}
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
