"use client";

import { useState } from "react";
import axios from "axios";
import { Upload, Github, Code2, Loader2, Sparkles, ArrowRight } from "lucide-react";

export default function Home() {
  const [repoUrl, setRepoUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [error, setError] = useState("");

  const handleAnalyze = async () => {
    if (!repoUrl.trim()) {
      setError("Please enter a GitHub repository URL");
      return;
    }

    setLoading(true);
    setError("");
    setProgress("Connecting to repository...");

    try {
      const response = await axios.post("http://localhost:8000/analyze", {
        url: repoUrl,
      });

      setSessionId(response.data.session_id);
      setProgress("Analyzing codebase structure...");
      
      await new Promise(resolve => setTimeout(resolve, 2000));
      window.location.href = `/dashboard?session=${response.data.session_id}`;
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : "Failed to analyze repository";
      setError(`Analysis failed: ${errorMessage}`);
      setLoading(false);
    }
  };

  const sampleRepos = [
    { name: "React", url: "facebook/react" },
    { name: "Next.js", url: "vercel/next.js" },
    { name: "FastAPI", url: "tiangoto/fastapi" },
  ];

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-8">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-20 w-64 h-64 bg-blue-500/10 rounded-full blur-3xl animate-float" />
        <div className="absolute bottom-20 right-20 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl animate-float" style={{ animationDelay: "1s" }} />
        <div className="absolute top-1/2 left-1/2 w-80 h-80 bg-indigo-500/10 rounded-full blur-3xl animate-float" style={{ animationDelay: "2s" }} />
      </div>

      <div className="relative z-10 max-w-2xl w-full space-y-12">
        <div className="text-center space-y-6">
          <div className="inline-flex items-center gap-3 px-4 py-2 rounded-full glass">
            <Sparkles className="w-4 h-4 text-blue-400" />
            <span className="text-sm text-gray-300">AI-Powered Codebase Analysis</span>
          </div>
          
          <h1 className="text-6xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent animate-gradient">
            CodePilot
          </h1>
          
          <p className="text-xl text-gray-400 max-w-md mx-auto">
            Transform any codebase into an interactive, guided experience. 
            Understand architecture in minutes, not hours.
          </p>
        </div>

        <div className="glass rounded-2xl p-8 space-y-6">
          <div className="flex items-center gap-3">
            <Github className="w-5 h-5 text-gray-400" />
            <span className="text-gray-300 font-medium">Enter GitHub Repository</span>
          </div>
          
          <div className="flex gap-3">
            <input
              type="text"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              placeholder="owner/repository or https://github.com/owner/repo"
              className="flex-1 px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              onKeyDown={(e) => e.key === "Enter" && handleAnalyze()}
            />
            <button
              onClick={handleAnalyze}
              disabled={loading}
              className="px-6 py-3 rounded-xl bg-gradient-to-r from-blue-500 to-purple-600 text-white font-medium flex items-center gap-2 hover:opacity-90 transition-all disabled:opacity-50"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Analyzing
                </>
              ) : (
                <>
                  <Code2 className="w-4 h-4" />
                  Analyze
                </>
              )}
            </button>
          </div>

          {loading && (
            <div className="space-y-2">
              <div className="h-1 bg-white/10 rounded-full overflow-hidden">
                <div className="h-full bg-gradient-to-r from-blue-500 to-purple-600 animate-pulse-glow" style={{ width: "60%" }} />
              </div>
              <p className="text-sm text-gray-400">{progress}</p>
            </div>
          )}

          {error && (
            <p className="text-red-400 text-sm">{error}</p>
          )}

          <div className="flex items-center gap-2">
            <div className="flex-1 h-px bg-white/10" />
            <span className="text-gray-500 text-sm">or try a sample</span>
            <div className="flex-1 h-px bg-white/10" />
          </div>

          <div className="flex gap-2 flex-wrap">
            {sampleRepos.map((repo) => (
              <button
                key={repo.name}
                onClick={() => setRepoUrl(repo.url)}
                className="px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-gray-300 hover:bg-white/10 transition-all text-sm"
              >
                {repo.name}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4">
          {[
            { icon: Upload, title: "Clone Repos", desc: "GitHub URLs or uploads" },
            { icon: Code2, title: "Map Structure", desc: "Visual dependency graphs" },
            { icon: Sparkles, title: "Guided Tour", desc: "Step-by-step onboarding" },
          ].map((feature, i) => (
            <div key={i} className="glass rounded-xl p-4 text-center hover:scale-105 transition-transform">
              <feature.icon className="w-6 h-6 mx-auto mb-2 text-blue-400" />
              <h3 className="font-medium text-white text-sm">{feature.title}</h3>
              <p className="text-xs text-gray-400 mt-1">{feature.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}