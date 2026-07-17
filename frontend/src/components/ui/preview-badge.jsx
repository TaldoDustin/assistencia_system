import { Sparkles } from "lucide-react";

export function PreviewBadge() {
  return (
    <span className="inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full border bg-blue-500/20 text-blue-400 border-blue-500/30">
      <Sparkles className="h-3 w-3" />
      Preview
    </span>
  );
}
