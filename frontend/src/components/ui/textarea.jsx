import { cn } from "@/lib/utils";

export function Textarea({ className, ...props }) {
  return (
    <textarea
      className={cn(
        "flex w-full rounded-lg border border-input bg-card px-3 py-2 text-sm text-foreground shadow-sm placeholder:text-muted-foreground focus:ring-1 focus:ring-ring transition-colors min-h-[80px] resize-none",
        className
      )}
      {...props}
    />
  );
}
