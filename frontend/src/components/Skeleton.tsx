import { cn } from "@/lib/cn";

export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "shimmer-bg animate-shimmer rounded-md",
        className,
      )}
    />
  );
}

export function SkeletonStack({ rows = 4, className }: { rows?: number; className?: string }) {
  return (
    <div className={cn("flex flex-col gap-2", className)}>
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton
          key={i}
          className={cn("h-4", i % 3 === 2 ? "w-2/3" : "w-full")}
        />
      ))}
    </div>
  );
}
