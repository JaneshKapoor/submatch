import { cn } from "@/lib/utils";

type BadgeVariant = "ok" | "marginal" | "review" | "missing" | "default";

const variants: Record<BadgeVariant, string> = {
  ok:       "bg-emerald-500/15 text-emerald-300 border border-emerald-500/25 ring-1 ring-emerald-500/10",
  marginal: "bg-amber-500/15 text-amber-300 border border-amber-500/25 ring-1 ring-amber-500/10",
  review:   "bg-red-500/15 text-red-300 border border-red-500/25 ring-1 ring-red-500/10",
  missing:  "bg-slate-500/15 text-slate-400 border border-slate-600/25",
  default:  "bg-violet-500/15 text-violet-300 border border-violet-500/25",
};

export function Badge({ variant = "default", children, className }: {
  variant?: BadgeVariant;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <span className={cn("inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-semibold tracking-wide", variants[variant], className)}>
      {children}
    </span>
  );
}
