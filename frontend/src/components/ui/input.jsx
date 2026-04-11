import { cn } from "@/lib/utils";

export function Input({ className, ...props }) {
  return (
    <input
      className={cn(
        "flex h-9 w-full rounded-lg border border-input bg-card px-3 py-1 text-sm text-foreground shadow-sm placeholder:text-muted-foreground focus:ring-1 focus:ring-ring transition-colors",
        className
      )}
      {...props}
    />
  );
}
