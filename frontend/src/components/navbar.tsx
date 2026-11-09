import Link from "next/link";
import { Button } from "@/components/ui/button";
import { VThemeToggle } from "@/components/ui/VToggle";

export default function Navbar() {
  return (
    <header className="sticky top-0 z-50 border-b border-border/40 bg-background/80 backdrop-blur-md">
      <div className="container mx-auto h-16 px-4 flex items-center justify-between">
        
        {/* Brand → Home */}
        <Link href="/" className="flex items-center gap-2 font-bold text-lg hover:opacity-90">
          <span>Veritas</span>
        </Link>

        <div className="flex items-center gap-4">
          <Link href="/product">
            <Button variant="ghost" size="sm">Product</Button>
          </Link>

          <Link href="/doc/client">
            <Button variant="ghost" size="sm">API</Button>
          </Link>

          <Link href="/docs/client">
            <Button variant="ghost" size="sm">Docs</Button>
          </Link>

          <VThemeToggle />
        </div>
      </div>
    </header>
  );
}
