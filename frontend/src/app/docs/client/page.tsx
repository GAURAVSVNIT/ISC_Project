"use client";

import React, { useState } from "react";
import { Copy, Check, Terminal, Play, Shield, Activity, Lock, Moon, Sun, Server, Globe, Cpu } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { VThemeToggle } from "@/components/ui/VToggle";
import { cn } from "@/lib/utils";

// --- Components ---

const CodeBlock = ({
    tabs
}: {
    tabs: { span: string; content: string; lang: string }[]
}) => {
    const [activeTab, setActiveTab] = useState(0);
    const [copied, setCopied] = useState(false);

    const handleCopy = () => {
        navigator.clipboard.writeText(tabs[activeTab].content);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className="rounded-lg border bg-black overflow-hidden shadow-2xl dark:border-white/10">
            <div className="flex items-center justify-between border-b border-white/10 bg-white/5 px-2">
                <div className="flex">
                    {tabs.map((tab, idx) => (
                        <button
                            key={idx}
                            onClick={() => setActiveTab(idx)}
                            className={cn(
                                "px-4 py-2 text-xs font-medium transition-colors hover:text-white focus:outline-none",
                                activeTab === idx
                                    ? "border-b-2 border-primary text-white bg-white/5"
                                    : "text-zinc-400"
                            )}
                        >
                            {tab.span}
                        </button>
                    ))}
                </div>
                <div className="px-2">
                    <button
                        onClick={handleCopy}
                        className="text-zinc-500 hover:text-white transition-colors p-1.5 rounded-md hover:bg-white/10"
                        title="Copy code"
                    >
                        {copied ? <Check className="h-3.5 w-3.5 text-green-500" /> : <Copy className="h-3.5 w-3.5" />}
                    </button>
                </div>
            </div>
            <div className="p-4 overflow-x-auto">
                <pre className="font-mono text-xs text-blue-100/90 leading-relaxed">
                    {tabs[activeTab].content}
                </pre>
            </div>
        </div>
    );
};

const MethodBadge = ({ method }: { method: "GET" | "POST" | "PUT" | "DELETE" }) => {
    const colors = {
        GET: "bg-green-500/10 text-green-600 dark:text-green-400 border-green-500/20",
        POST: "bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20",
        PUT: "bg-orange-500/10 text-orange-600 dark:text-orange-400 border-orange-500/20",
        DELETE: "bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/20",
    };
    return (
        <span className={cn("rounded-md px-2.5 py-0.5 text-xs font-bold border", colors[method])}>
            {method}
        </span>
    );
};

export default function ClientDocsPage() {
    const [keyCopied, setKeyCopied] = useState(false);
    const sampleKey = "Vxxxxxxxxxxxx";

    const handleCopyKey = () => {
        navigator.clipboard.writeText(sampleKey);
        setKeyCopied(true);
        setTimeout(() => setKeyCopied(false), 2000);
    };

    const codeExamples = [
        {
            span: "cURL",
            lang: "bash",
            content: `curl -X POST "https://veritas-engine.com/api/v1/analyze" \\
  -H "Authorization: Bearer ${sampleKey}" \\
  -F "file=@/path/to/media.mp4" \\
  -F "claim=President giving a speech" \\
  -F "enable_defense=true"`
        },
        {
            span: "Python",
            lang: "python",
            content: `import requests

url = "https://veritas-engine.com/api/v1/analyze"
headers = {
    "Authorization": "Bearer ${sampleKey}"
}
files = {
    "file": open("media.mp4", "rb")
}
data = {
    "claim": "President giving a speech",
    "enable_defense": "true"
}

response = requests.post(url, headers=headers, files=files, data=data)
print(response.json())`
        },
        {
            span: "Node.js",
            lang: "javascript",
            content: `const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

const form = new FormData();
form.append('file', fs.createReadStream('media.mp4'));
form.append('claim', 'President giving a speech');
form.append('enable_defense', 'true');

axios.post('https://veritas-engine.com/api/v1/analyze', form, {
  headers: {
    ...form.getHeaders(),
    'Authorization': 'Bearer ${sampleKey}'
  }
})
.then(response => console.log(response.data))
.catch(error => console.error(error));`
        },
        {
            span: "Go",
            lang: "go",
            content: `package main

import (
    "fmt"
    "bytes"
    "mime/multipart"
    "net/http"
    "os"
    "io"
)

func main() {
    url := "https://veritas-engine.com/api/v1/analyze"
    method := "POST"

    payload := &bytes.Buffer{}
    writer := multipart.NewWriter(payload)
    file, _ := os.Open("media.mp4")
    defer file.Close()
    
    part1, _ := writer.CreateFormFile("file", "media.mp4")
    io.Copy(part1, file)
    writer.WriteField("claim", "President giving a speech")
    writer.WriteField("enable_defense", "true")
    writer.Close()

    client := &http.Client {}
    req, _ := http.NewRequest(method, url, payload)
    req.Header.Add("Authorization", "Bearer ${sampleKey}")
    req.Header.Set("Content-Type", writer.FormDataContentType())

    res, _ := client.Do(req)
    defer res.Body.Close()

    body, _ := io.ReadAll(res.Body)
    fmt.Println(string(body))
}`
        }
    ];

    return (
        <div className="min-h-screen bg-background text-foreground selection:bg-primary/20 flex flex-col">
            {/* Sticky Header */}
            <header className="sticky top-0 z-50 w-full border-b border-white/5 bg-background/80 backdrop-blur-md supports-[backdrop-filter]:bg-background/60">
                <div className="container mx-auto flex h-14 items-center justify-between px-4">
                    <div className="flex items-center gap-2 font-bold text-lg tracking-tight">
                        <Shield className="h-5 w-5 text-primary" />
                        <span>Veritas <span className="text-muted-foreground font-normal">Docs</span></span>
                    </div>
                    <div className="flex items-center gap-4">
                        <Button variant="ghost" size="sm" className="hidden sm:flex text-muted-foreground hover:text-foreground">
                            Support
                        </Button>
                        <div className="h-4 w-px bg-border hidden sm:block"></div>
                        <VThemeToggle />
                    </div>
                </div>
            </header>

            {/* Hero Section */}
            <div className="relative border-b border-white/5 bg-black/[0.02] dark:bg-white/[0.02] py-12 md:py-20">
                <div className="container relative mx-auto px-4 max-w-6xl">
                    <div className="grid gap-8 lg:grid-cols-[1.5fr_1fr] items-center">
                        <div className="flex flex-col items-start gap-4">
                            <Badge variant="outline" className="border-primary/20 bg-primary/10 text-primary">
                                API v1.0 Enterprise
                            </Badge>
                            <h1 className="text-4xl font-bold tracking-tight sm:text-5xl bg-clip-text text-transparent bg-gradient-to-r from-foreground to-foreground/70">
                                Integrate Truth directly.
                            </h1>
                            <p className="text-lg text-muted-foreground text-pretty max-w-xl">
                                The world's most advanced deepfake detection and media forensics engine.
                                Seamlessly add verification layers to your social platforms, newsrooms, and security pipelines.
                            </p>
                            <div className="flex flex-wrap gap-4 mt-2">
                                <Button className="rounded-full px-8">Read the Docs</Button>
                                <Button variant="outline" className="rounded-full">Request Enterprise Key</Button>
                            </div>
                        </div>
                        {/* API Key Card Widget */}
                        <div className="w-full">
                            <Card className="border-primary/20 bg-card/60 backdrop-blur-sm shadow-xl relative overflow-hidden group">
                                <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                                <CardHeader className="pb-3 border-b border-border/40">
                                    <div className="flex items-center justify-between">
                                        <CardTitle className="text-sm font-medium flex items-center gap-2">
                                            <Activity className="h-4 w-4 text-primary" />
                                            Your Developer Credentials
                                        </CardTitle>
                                        <span className="text-[10px] uppercase font-bold text-green-500 bg-green-500/10 px-2 py-0.5 rounded-full border border-green-500/20">Active</span>
                                    </div>
                                </CardHeader>
                                <CardContent className="p-5 space-y-4">
                                    <div className="space-y-1.5">
                                        <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Client ID</label>
                                        <div className="font-mono text-xs bg-muted/50 p-2 rounded border border-border/50 text-foreground/80">
                                            client_8f93j2910d
                                        </div>
                                    </div>
                                    <div className="space-y-1.5">
                                        <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center justify-between">
                                            API Secret Key
                                            <span className="text-[10px] normal-case font-normal text-muted-foreground">Keep this safe</span>
                                        </label>
                                        <div className="flex gap-2">
                                            <div className="relative flex-1">
                                                <Input
                                                    type="text"
                                                    value={sampleKey}
                                                    readOnly
                                                    className="font-mono text-sm bg-background/80 pr-10 border-primary/20 focus-visible:ring-primary/20"
                                                />
                                                <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
                                                    <Lock className="h-3 w-3 text-muted-foreground" />
                                                </div>
                                            </div>
                                            <Button size="icon" variant="secondary" onClick={handleCopyKey} className="shrink-0 hover:text-primary">
                                                {keyCopied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                                            </Button>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        </div>
                    </div>
                </div>
            </div>

            <div className="container mx-auto px-4 py-12 max-w-6xl">
                <div className="grid grid-cols-1 gap-12 lg:grid-cols-[250px_1fr]">
                    {/* Sticky Sidebar Navigation */}
                    <aside className="hidden lg:block">
                        <div className="sticky top-24 space-y-8">
                            <div className="space-y-3">
                                <h4 className="text-sm font-semibold tracking-wide text-foreground">Getting Started</h4>
                                <nav className="flex flex-col space-y-1 text-sm text-muted-foreground border-l border-border/50 ml-1">
                                    <a href="#authentication" className="pl-4 py-1 hover:text-primary hover:border-l-primary -ml-px border-l border-transparent transition-all">Authentication</a>
                                    <a href="#errors" className="pl-4 py-1 hover:text-primary hover:border-l-primary -ml-px border-l border-transparent transition-all">Errors</a>
                                </nav>
                            </div>
                            <div className="space-y-3">
                                <h4 className="text-sm font-semibold tracking-wide text-foreground">Core Resources</h4>
                                <nav className="flex flex-col space-y-1 text-sm text-muted-foreground border-l border-border/50 ml-1">
                                    <a href="#health" className="pl-4 py-1 hover:text-primary hover:border-l-primary -ml-px border-l border-transparent transition-all">System Health</a>
                                    <a href="#analysis" className="pl-4 py-1 hover:text-primary hover:border-l-primary -ml-px border-l border-transparent transition-all">Media Analysis</a>
                                </nav>
                            </div>
                        </div>
                    </aside>

                    {/* Main Content */}
                    <main className="space-y-16">

                        {/* Authentication */}
                        <section id="authentication" className="space-y-6 scroll-mt-24">
                            <div className="border-b pb-4">
                                <h2 className="text-3xl font-bold tracking-tight">Authentication</h2>
                                <p className="mt-2 text-lg text-muted-foreground">
                                    Veritas uses standard Bearer Token verification.
                                </p>
                            </div>
                            <div className="prose prose-zinc dark:prose-invert max-w-none">
                                <p>
                                    Authenticate your requests by including your secret API key in the <code>Authorization</code> header of every request.
                                    Unauthorized requests will return a <code>401 Unauthorized</code> response.
                                </p>
                            </div>
                            <div className="rounded-md bg-yellow-500/10 p-4 border border-yellow-500/20">
                                <div className="flex gap-3">
                                    <Lock className="h-5 w-5 text-yellow-600 dark:text-yellow-500 mt-0.5" />
                                    <div className="text-sm text-yellow-900 dark:text-yellow-200">
                                        <p className="font-semibold">Security Notice</p>
                                        <p>Never expose your API key in client-side code (browsers, mobile apps). perform these requests from your backend server.</p>
                                    </div>
                                </div>
                            </div>
                        </section>

                        <hr className="border-border/40" />

                        {/* Health Check */}
                        <section id="health" className="space-y-6 scroll-mt-24">
                            <div>
                                <div className="flex items-center gap-3 mb-2">
                                    <MethodBadge method="GET" />
                                    <h3 className="text-2xl font-bold font-mono">/health</h3>
                                </div>
                                <p className="text-muted-foreground">
                                    Check if the analysis engine is online and ready.
                                </p>
                            </div>

                            <div className="grid gap-6 md:grid-cols-2">
                                <div className="space-y-4">
                                    <div className="space-y-2">
                                        <h4 className="text-sm font-medium uppercase text-muted-foreground flex items-center gap-2">
                                            <Globe className="h-3 w-3" /> Endpoint
                                        </h4>
                                        <code className="block w-full rounded-md border bg-muted/40 px-3 py-2 text-sm text-foreground font-mono">
                                            https://veritas-engine.com/health
                                        </code>
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    <h4 className="text-sm font-medium uppercase text-muted-foreground flex items-center gap-2">
                                        <Server className="h-3 w-3" /> Response
                                    </h4>
                                    <div className="rounded-lg border bg-black p-3 font-mono text-xs text-green-400">
                                        {`{
  "status": "ok",
  "service": "project-veritas-backend"
}`}
                                    </div>
                                </div>
                            </div>
                        </section>

                        <hr className="border-border/40" />

                        {/* Analyze Media */}
                        <section id="analysis" className="space-y-10 scroll-mt-24">
                            <div>
                                <div className="flex items-center gap-3 mb-4">
                                    <MethodBadge method="POST" />
                                    <h3 className="text-2xl font-bold font-mono">/api/v1/analyze</h3>
                                </div>
                                <p className="text-lg text-muted-foreground">
                                    The core inference endpoint. Upload media to run the "Triangle of Truth" analysis (Visual, Semantic, and Contextual Pipelines).
                                </p>
                            </div>

                            {/* Parameters Table */}
                            <Card>
                                <CardHeader className="bg-muted/30 pb-4">
                                    <CardTitle className="text-base">Body Parameters</CardTitle>
                                    <CardDescription>Multipart/form-data required</CardDescription>
                                </CardHeader>
                                <CardContent className="p-0">
                                    <div className="divide-y divide-border/50">
                                        <div className="grid grid-cols-[1fr_2fr] gap-4 p-4 text-sm">
                                            <div className="font-mono text-primary font-semibold">file <span className="text-red-500">*</span></div>
                                            <div className="space-y-1">
                                                <p className="font-medium">File (Binary)</p>
                                                <p className="text-muted-foreground">The image, video, or audio file to analyze. Formats: jpg, png, mp4, wav, mp3. Max 100MB.</p>
                                            </div>
                                        </div>
                                        <div className="grid grid-cols-[1fr_2fr] gap-4 p-4 text-sm">
                                            <div className="font-mono text-primary font-semibold">claim</div>
                                            <div className="space-y-1">
                                                <p className="font-medium">String (Optional)</p>
                                                <p className="text-muted-foreground">Contextual claim or caption associated with the media. Used for semantic consistency checking.</p>
                                            </div>
                                        </div>
                                        <div className="grid grid-cols-[1fr_2fr] gap-4 p-4 text-sm">
                                            <div className="font-mono text-primary font-semibold">enable_defense</div>
                                            <div className="space-y-1">
                                                <p className="font-medium">Boolean (Default: false)</p>
                                                <p className="text-muted-foreground">If true, runs the adversarial defense layer to sanitize inputs before analysis.</p>
                                            </div>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>

                            {/* Code Examples */}
                            <div className="space-y-4">
                                <h4 className="text-sm font-medium uppercase text-muted-foreground flex items-center gap-2">
                                    <Activity className="h-3 w-3" /> Implementation Example
                                </h4>
                                <CodeBlock tabs={codeExamples} />
                            </div>

                            {/* Response Schema */}
                            <div className="space-y-4">
                                <h4 className="text-sm font-medium uppercase text-muted-foreground flex items-center gap-2">
                                    <Cpu className="h-3 w-3" /> Analysis Object
                                </h4>
                                <Card className="bg-muted/20 border-border/60">
                                    <CardContent className="p-4">
                                        <pre className="text-xs font-mono text-foreground leading-relaxed overflow-x-auto">
                                            {`{
  "verdict": "Fake" | "Authentic",
  "confidence_score": float,      // 0.0 to 1.0
  "explanation": string,          // LLM generated reasoning
  "visual": {
    "score": float,
    "heatmap": string (base64)    // If applicable
  },
  "semantic": { ... },            // Consistency metrics
  "context": { ... },             // Web evidence
  "verification": string          // Blockchain hash
}`}
                                        </pre>
                                    </CardContent>
                                </Card>
                            </div>

                        </section>
                    </main>
                </div>
            </div>
        </div>
    );
}

// Simple Badge Component inline to avoid import issues if not present
function Badge({ className, variant = "default", ...props }: React.HTMLAttributes<HTMLDivElement> & { variant?: "default" | "secondary" | "outline" }) {
    const variants = {
        default: "border-transparent bg-primary text-primary-foreground hover:bg-primary/80",
        secondary: "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80",
        outline: "text-foreground",
    };
    return (
        <div className={cn("inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2", variants[variant], className)} {...props} />
    );
}
