"use client";
import { cn } from "@/lib/utils";

export function AuroraBackground({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={cn("relative min-h-screen aurora-bg overflow-hidden", className)}>
      {/* Blob 1 */}
      <div className="pointer-events-none absolute -top-60 -left-60 w-[700px] h-[700px] rounded-full bg-violet-700/20 blur-[120px] animate-float" />
      {/* Blob 2 */}
      <div className="pointer-events-none absolute top-1/3 -right-40 w-[500px] h-[500px] rounded-full bg-indigo-600/15 blur-[100px]" style={{ animationDelay: "2s" }} />
      {/* Blob 3 */}
      <div className="pointer-events-none absolute bottom-0 left-1/3 w-[400px] h-[400px] rounded-full bg-blue-700/10 blur-[100px] animate-float" style={{ animationDelay: "4s" }} />
      {/* Dot grid */}
      <div className="pointer-events-none absolute inset-0 dot-grid opacity-40" />
      <div className="relative z-10">{children}</div>
    </div>
  );
}
