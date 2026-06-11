import { cn } from "@/lib/cn";

type Variant = "primary" | "secondary" | "ghost" | "outline";
type Size = "sm" | "md";

export function Button({
  variant = "secondary",
  size = "md",
  className,
  children,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant; size?: Size }) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-1.5 rounded-md font-medium transition-all duration-150 disabled:cursor-not-allowed disabled:opacity-50",
        size === "sm" && "h-7 px-2.5 text-[12px]",
        size === "md" && "h-9 px-3.5 text-[13px]",
        variant === "primary" &&
          "bg-accent text-white shadow-sm hover:brightness-110 active:brightness-95",
        variant === "secondary" &&
          "border border-border bg-bg-elevated text-fg hover:border-border-strong hover:bg-surface",
        variant === "outline" &&
          "border border-border-strong bg-transparent text-fg hover:bg-bg-elevated",
        variant === "ghost" &&
          "text-fg-muted hover:bg-bg-elevated hover:text-fg",
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}
