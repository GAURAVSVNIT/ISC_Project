import { BadgeCheck, AlertTriangle, HelpCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface VerdictBadgeProps {
    verdict: 'REAL' | 'FAKE' | 'UNCERTAIN';
    className?: string;
}

export function VerdictBadge({ verdict, className }: VerdictBadgeProps) {
    const config = {
        REAL: {
            icon: BadgeCheck,
            text: "AUTHENTIC MEDIA",
            color: "bg-emerald-500/15 text-emerald-500 border-emerald-500/50",
            iconColor: "text-emerald-500"
        },
        FAKE: {
            icon: AlertTriangle,
            text: "LIKELY MANIPULATED",
            color: "bg-destructive/15 text-destructive border-destructive/50",
            iconColor: "text-destructive"
        },
        UNCERTAIN: {
            icon: HelpCircle,
            text: "INCONCLUSIVE",
            color: "bg-yellow-500/15 text-yellow-500 border-yellow-500/50",
            iconColor: "text-yellow-500"
        }
    };

    const { icon: Icon, text, color } = config[verdict] || config.UNCERTAIN;

    return (
        <div className={cn(
            "inline-flex items-center gap-2 px-4 py-2 rounded-full border font-bold tracking-wider",
            color,
            className
        )}>
            <Icon className="w-5 h-5" />
            <span>{text}</span>
        </div>
    );
}
