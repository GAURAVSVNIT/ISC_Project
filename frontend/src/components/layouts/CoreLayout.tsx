"use client";

import { ReactNode } from "react";
import Link from "next/link";
import { Shield } from "lucide-react";
import Navbar from "../navbar";

export default function CoreLayout({ children }: { children: ReactNode }) {
  return (
    <main className="min-h-screen bg-background text-foreground flex flex-col">
      <Navbar/>
      <div className="flex-1 container mx-auto px-4 py-8 md:py-12">
        {children}
      </div>

      <footer className="border-t border-border/40 py-8 bg-muted/10">
        <div className="container mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-muted-foreground">
          <div className="flex items-center gap-2">
            <Shield className="h-4 w-4 text-primary" />
            <span>© 2026 Veritas · Enterprise Media Verification Platform</span>
          </div>
          <div className="flex items-center gap-6 text-xs">
            <Link href="/" className="hover:text-foreground transition-colors">Home</Link>
            <Link href="/product" className="hover:text-foreground transition-colors">Product</Link>
            <Link href="/docs/client" className="hover:text-foreground transition-colors">Documentation</Link>
            <a
              href="https://github.com/GAURAVSVNIT/ISC_Project"
              target="_blank"
              rel="noreferrer"
              className="hover:text-foreground transition-colors"
            >
              GitHub
            </a>
          </div>
        </div>
      </footer>
    </main>
  );
}
