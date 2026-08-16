import * as TooltipPrimitive from "@radix-ui/react-tooltip";
import { cn } from "@/lib/utils";

export const TooltipProvider = TooltipPrimitive.Provider;
export const Tooltip = TooltipPrimitive.Root;
export const TooltipTrigger = TooltipPrimitive.Trigger;

export function TooltipContent({ className, sideOffset = 6, ...props }) {
  return (
    <TooltipPrimitive.Portal>
      <TooltipPrimitive.Content
        sideOffset={sideOffset}
        className={cn(
          "z-50 overflow-hidden rounded-lg border border-border bg-popover px-3 py-1.5 text-xs text-popover-foreground shadow-xl transition-opacity duration-150 data-[state=closed]:opacity-0",
          className
        )}
        {...props}
      />
    </TooltipPrimitive.Portal>
  );
}
