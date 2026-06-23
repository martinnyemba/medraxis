import * as DialogPrimitive from "@radix-ui/react-dialog";
import { Activity, X } from "lucide-react";
import { NavList } from "./NavList";

export function MobileNav({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  return (
    <DialogPrimitive.Root open={open} onOpenChange={onOpenChange}>
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-black/50 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 md:hidden" />
        <DialogPrimitive.Content
          className="fixed inset-y-0 left-0 z-50 flex h-full w-72 max-w-[85vw] flex-col border-r bg-card shadow-lg duration-200 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:slide-out-to-left data-[state=open]:slide-in-from-left md:hidden"
        >
          <DialogPrimitive.Title className="sr-only">Navigation</DialogPrimitive.Title>
          <div className="flex h-16 items-center gap-2 border-b px-6">
            <div className="flex size-8 items-center justify-center rounded-md bg-primary text-primary-foreground">
              <Activity className="size-5" />
            </div>
            <div className="leading-tight">
              <p className="text-sm font-semibold">Medraxis</p>
              <p className="text-xs text-muted-foreground">Health Platform</p>
            </div>
            <DialogPrimitive.Close className="ml-auto rounded-sm opacity-70 transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring">
              <X className="size-5" />
              <span className="sr-only">Close</span>
            </DialogPrimitive.Close>
          </div>

          <NavList onNavigate={() => onOpenChange(false)} />

          <div className="border-t p-4 text-xs text-muted-foreground">
            OpenMRS-inspired · v0.1
          </div>
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  );
}
