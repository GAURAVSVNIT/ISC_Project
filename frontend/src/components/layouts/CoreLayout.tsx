"use client";

import { ReactNode } from "react";
import Navbar from "../navbar";

export default function CoreLayout({ children }: { children: ReactNode }) {
  return (
    <main className="min-h-screen bg-background text-foreground flex flex-col">
      <Navbar/>
      <div className="flex-1 container mx-auto px-4 py-8 md:py-12">
        {children}
      </div>

      <footer className="border-t border-border/40 py-6">
        <div className="container mx-auto px-4 text-center text-xs text-muted-foreground">
          © 2026 Veritas · Enterprise Media Verification Platform
        </div>
      </footer>
    </main>
  );
}
