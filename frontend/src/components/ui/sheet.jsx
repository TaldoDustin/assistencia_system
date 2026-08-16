import * as DialogPrimitive from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

export const Sheet = DialogPrimitive.Root;
export const SheetTrigger = DialogPrimitive.Trigger;
export const SheetClose = DialogPrimitive.Close;
export const SheetPortal = DialogPrimitive.Portal;

export function SheetOverlay({ className, ...props }) {
  return (
    <DialogPrimitive.Overlay
      className={cn(
        "fixed inset-0 z-50 bg-black/60 backdrop-blur-sm transition-opacity duration-200 data-[state=closed]:opacity-0",
        className
      )}
      {...props}
    />
  );
}

const sideClasses = {
  right:
    "inset-y-0 right-0 h-full w-3/4 max-w-sm border-l border-border data-[state=closed]:translate-x-full data-[state=open]:translate-x-0",
  left:
    "inset-y-0 left-0 h-full w-3/4 max-w-sm border-r border-border data-[state=closed]:-translate-x-full data-[state=open]:translate-x-0",
  top:
    "inset-x-0 top-0 border-b border-border data-[state=closed]:-translate-y-full data-[state=open]:translate-y-0",
  bottom:
    "inset-x-0 bottom-0 border-t border-border data-[state=closed]:translate-y-full data-[state=open]:translate-y-0",
};

export function SheetContent({ side = "right", className, children, ...props }) {
  return (
    <SheetPortal>
      <SheetOverlay />
      <DialogPrimitive.Content
        className={cn(
          "fixed z-50 flex flex-col bg-card text-card-foreground shadow-xl transition-transform duration-200 ease-out focus:outline-none",
          sideClasses[side],
          className
        )}
        {...props}
      >
        {children}
        <DialogPrimitive.Close className="absolute right-4 top-4 rounded-sm opacity-70 hover:opacity-100 focus:outline-none focus:ring-1 focus:ring-ring transition-opacity">
          <X className="h-4 w-4" />
          <span className="sr-only">Fechar</span>
        </DialogPrimitive.Close>
      </DialogPrimitive.Content>
    </SheetPortal>
  );
}

export function SheetHeader({ className, ...props }) {
  return <div className={cn("flex flex-col space-y-1.5 p-6", className)} {...props} />;
}

export function SheetFooter({ className, ...props }) {
  return (
    <div
      className={cn("flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2 gap-2 p-6 pt-0", className)}
      {...props}
    />
  );
}

export function SheetTitle({ className, ...props }) {
  return (
    <DialogPrimitive.Title className={cn("text-lg font-semibold text-card-foreground", className)} {...props} />
  );
}

export function SheetDescription({ className, ...props }) {
  return <DialogPrimitive.Description className={cn("text-sm text-muted-foreground", className)} {...props} />;
}
