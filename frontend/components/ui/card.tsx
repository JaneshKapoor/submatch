import { cn } from "@/lib/utils";

export function Card({ children, className, glow }: {
  children: React.ReactNode;
  className?: string;
  glow?: boolean;
}) {
  return (
    <div className={cn(
      "glass rounded-2xl p-6 transition-all duration-300",
      glow && "glow-card hover:shadow-xl hover:shadow-violet-500/10",
      className,
    )}>
      {children}
    </div>
  );
}

export function CardHeader({ children, className }: { children: React.ReactNode; className?: string }) {
  return <div className={cn("mb-4", className)}>{children}</div>;
}

export function CardTitle({ children, className }: { children: React.ReactNode; className?: string }) {
  return <h3 className={cn("font-semibold text-slate-100 text-base", className)}>{children}</h3>;
}

export function CardDescription({ children, className }: { children: React.ReactNode; className?: string }) {
  return <p className={cn("text-sm text-slate-400 mt-1", className)}>{children}</p>;
}
