"use client";

import {
  Shield,
  Activity,
  Cpu,
  Globe,
  FileSearch,
  Brain,
  Lock,
  ArrowRight,
} from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { VThemeToggle } from "@/components/ui/VToggle";
import { cn } from "@/lib/utils";
import Navbar from "@/components/navbar";

export default function HomePage() {
  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      <Navbar />
      {/* ================= HERO ================= */}
      <section className="border-b border-border/40 py-20">
        <div className="container mx-auto px-4 grid gap-12 lg:grid-cols-2 items-center">

          {/* Left */}
          <div className="space-y-6">
            <span className="inline-flex items-center rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-xs font-semibold text-primary">
              Enterprise AI · Trust Infrastructure
            </span>

            <h1 className="text-4xl sm:text-5xl font-bold tracking-tight">
              Multi-Modal Misinformation Detection,
              <span className="block text-primary">Built for Reality.</span>
            </h1>

            <p className="text-lg text-muted-foreground max-w-xl">
              Veritas detects manipulated text, images, and videos by uncovering
              cross-modal inconsistencies, deepfakes, and out-of-context media —
              with clear, human-readable explanations.
            </p>

            <div className="flex gap-4">
              <Link href="/product">
                <Button size="lg" className="rounded-full px-8">
                  Use our product
                </Button>
              </Link>

              <Link href="/docs/client">
                <Button size="lg" variant="outline" className="rounded-full">
                  View API Docs
                </Button>
              </Link>
            </div>

          </div>

          {/* Right Card */}
          <Card className="border-primary/20 bg-card/60 backdrop-blur-sm shadow-xl">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-sm">
                <Activity className="h-4 w-4 text-primary" />
                Live Analysis Engine
              </CardTitle>
              <CardDescription>Inference pipeline status</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 font-mono text-sm">
              <div className="flex justify-between">
                <span>Status</span>
                <span className="text-green-500">Active</span>
              </div>
              <div className="flex justify-between">
                <span>Verdict</span>
                <span className="text-red-500">Fake</span>
              </div>
              <div className="flex justify-between">
                <span>Confidence</span>
                <span>0.93</span>
              </div>
              <div className="pt-2 text-muted-foreground text-xs">
                Explanation: Facial artifacts and semantic mismatch detected
                between audio transcript and lip movement.
              </div>
            </CardContent>
          </Card>

        </div>
      </section>

      {/* ================= CAPABILITIES ================= */}
      <section className="py-20">
        <div className="container mx-auto px-4 space-y-12">
          <div className="text-center max-w-2xl mx-auto">
            <h2 className="text-3xl font-bold tracking-tight">
              Engineered for Media Authenticity at Scale.
            </h2>

            <p className="mt-4 text-muted-foreground">
              Every component of Veritas maps directly to the mandatory
              requirements of multi-modal misinformation detection.
            </p>
          </div>

          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            <Feature icon={Brain} title="Cross-Modal Consistency">
              Detects caption-media mismatches using semantic alignment models.
            </Feature>
            <Feature icon={FileSearch} title="Out-of-Context Media">
              Identifies reused images and videos via perceptual hashing and web evidence.
            </Feature>
            <Feature icon={Cpu} title="Synthetic Media Detection">
              Flags AI-generated text, images, and deepfake videos.
            </Feature>
            <Feature icon={Shield} title="Explainable AI">
              Generates natural-language explanations citing concrete evidence.
            </Feature>
            <Feature icon={Lock} title="Adversarial Robustness">
              Resilient to perturbations, prompt attacks, and unseen manipulations.
            </Feature>
            <Feature icon={Globe} title="Quantitative Evaluation">
              Accuracy, robustness, and explanation-quality metrics built-in.
            </Feature>
          </div>
        </div>
      </section>

      {/* ================= HOW IT WORKS ================= */}
      <section className="border-t border-border/40 py-20 bg-muted/20">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12">
            How Veritas Works
          </h2>

          <div className="grid gap-8 md:grid-cols-3 text-center">
            <Step number="01" title="Ingest Media">
              Text, images, or videos with optional claims.
            </Step>
            <Step number="02" title="Multi-Modal Analysis">
              Visual, semantic, and contextual pipelines.
            </Step>
            <Step number="03" title="Explain Verdict">
              Fake or authentic — with evidence and confidence.
            </Step>
          </div>
        </div>
      </section>

      {/* ================= CTA ================= */}
      <section className="py-20">
        <div className="container mx-auto px-4 text-center space-y-6">
          <h2 className="text-4xl font-bold">
            Stop Guessing. Start Verifying.
          </h2>
          <p className="text-muted-foreground max-w-xl mx-auto">
            Bring trust, transparency, and explainability to your media pipelines.
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Link href="/product">
              <Button size="lg" className="rounded-full px-10">
                Launch Detection Engine
              </Button>
            </Link>
            <Link href="/docs/client">
              <Button size="lg" variant="outline" className="rounded-full">
                API & Integration Docs <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* ================= FOOTER ================= */}
      <footer className="border-t border-border/40 py-8 bg-muted/10">
        <div className="container mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-muted-foreground">
          <div className="flex items-center gap-2">
            <Shield className="h-4 w-4 text-primary" />
            <span>© 2026 Veritas · Multi-Modal Verification Platform</span>
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
    </div>
  );
}

/* ================= SMALL COMPONENTS ================= */

function Feature({ icon: Icon, title, children }: any) {
  return (
    <Card>
      <CardHeader>
        <Icon className="h-6 w-6 text-primary mb-2" />
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent className="text-sm text-muted-foreground">
        {children}
      </CardContent>
    </Card>
  );
}

function Step({ number, title, children }: any) {
  return (
    <div className="space-y-2">
      <div className="text-primary font-mono text-sm">{number}</div>
      <h3 className="text-lg font-semibold">{title}</h3>
      <p className="text-muted-foreground text-sm">{children}</p>
    </div>
  );
}
