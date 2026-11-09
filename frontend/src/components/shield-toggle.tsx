"use client"

import { ShieldCheck, ShieldAlert } from "lucide-react";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label"; // We need Label too
import { cn } from "@/lib/utils";

interface ShieldToggleProps {
    enabled: boolean;
    onToggle: (enabled: boolean) => void;
    disabled?: boolean;
}

export function ShieldToggle({ enabled, onToggle, disabled }: ShieldToggleProps) {
    return (
        <div className={cn(
            "flex items-center gap-3 px-4 py-2 rounded-lg border transition-colors",
            enabled ? "bg-primary/5 border-primary/20" : "bg-muted/5 border-transparent"
        )}>
            <div className={cn("p-1.5 rounded-full", enabled ? "text-primary" : "text-muted-foreground")}>
                {enabled ? <ShieldCheck className="w-5 h-5" /> : <ShieldAlert className="w-5 h-5" />}
            </div>
            <div className="flex flex-col">
                <span className="text-sm font-medium">Adversarial Defense</span>
                <span className="text-[10px] text-muted-foreground">Pre-process noise filtering</span>
            </div>
            <Switch
                checked={enabled}
                onCheckedChange={onToggle}
                disabled={disabled}
                className="ml-2"
            />
        </div>
    );
}
