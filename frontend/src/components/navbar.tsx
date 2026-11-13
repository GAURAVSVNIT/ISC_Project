import Link from "next/link";
import { Shield } from "lucide-react";
import { Button } from "@/components/ui/button";
import { VThemeToggle } from "@/components/ui/VToggle";

export default function Navbar() {
  return (
    <header className="sticky top-0 z-50 border-b border-border/40 bg-background/80 backdrop-blur-md">
      <div className="container mx-auto h-16 px-4 flex items-center justify-between">
        
        {/* Brand → Home */}
        <Link href="/" className="flex items-center gap-2.5 font-bold text-lg hover:opacity-90 transition-opacity">
          <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary border border-primary/20">
            <Shield className="h-4 w-4" />
          </div>
          <span className="tracking-tight">Veritas</span>
        </Link>

        <div className="flex items-center gap-2 sm:gap-4">
          <Link href="/product">
            <Button variant="ghost" size="sm">Product</Button>
          </Link>

          <Link href="/docs/client">
            <Button variant="ghost" size="sm">Docs & API</Button>
          </Link>

          <VThemeToggle />
        </div>
      </div>
    </header>
  );
}
