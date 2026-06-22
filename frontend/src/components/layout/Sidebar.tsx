import * as DialogPrimitive from "@radix-ui/react-dialog";
import { NavLink } from "react-router-dom";
import { Activity, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { NAV_ITEMS } from "./navigation";

function SidebarBrand() {
  return (
    <div className="flex items-center gap-2">
      <div className="flex size-8 shrink-0 items-center justify-center rounded-md bg-primary text-primary-foreground">
        <Activity className="size-5" />
      </div>
      <div className="leading-tight">
        <p className="text-sm font-semibold">Medraxis</p>
        <p className="text-xs text-muted-foreground">Health Platform</p>
      </div>
    </div>
  );
}

function SidebarNav({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <nav className="flex-1 space-y-1 overflow-y-auto p-3">
      {NAV_ITEMS.map((item) =>
        item.enabled ? (
          <NavLink
            key={item.to}
            to={item.to}
            onClick={onNavigate}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
              )
            }
          >
            <item.icon className="size-4" />
            {item.label}
          </NavLink>
        ) : (
          <div
            key={item.to}
            className="flex cursor-not-allowed items-center justify-between gap-3 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground/50"
            title="Coming soon"
          >
            <span className="flex items-center gap-3">
              <item.icon className="size-4" />
              {item.label}
            </span>
            <Badge variant="secondary" className="text-[10px]">
              Soon
            </Badge>
          </div>
        ),
      )}
    </nav>
  );
}

/** Static sidebar, visible from the md breakpoint up. */
export function Sidebar() {
  return (
    <aside className="hidden w-64 shrink-0 flex-col border-r bg-card md:flex">
      <div className="flex h-16 items-center border-b px-6">
        <SidebarBrand />
      </div>
      <SidebarNav />
      <div className="border-t p-4 text-xs text-muted-foreground">
        OpenMRS-inspired · v0.1
      </div>
    </aside>
  );
}

/** Slide-in navigation drawer for viewports below the md breakpoint. */
export function MobileSidebar({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  return (
    <DialogPrimitive.Root open={open} onOpenChange={onOpenChange}>
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay
          className="fixed inset-0 z-50 bg-black/50 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 md:hidden"
        />
        <DialogPrimitive.Content
          className="fixed inset-y-0 left-0 z-50 flex h-full w-72 max-w-[85vw] flex-col border-r bg-card shadow-lg duration-200 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:slide-out-to-left data-[state=open]:slide-in-from-left md:hidden"
          aria-describedby={undefined}
        >
          <DialogPrimitive.Title className="sr-only">Navigation</DialogPrimitive.Title>
          <div className="flex h-16 shrink-0 items-center justify-between border-b px-4">
            <SidebarBrand />
            <DialogPrimitive.Close className="rounded-sm p-1.5 text-muted-foreground opacity-70 transition-opacity hover:bg-accent hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring">
              <X className="size-4" />
              <span className="sr-only">Close menu</span>
            </DialogPrimitive.Close>
          </div>
          <SidebarNav onNavigate={() => onOpenChange(false)} />
          <div className="border-t p-4 text-xs text-muted-foreground">
            OpenMRS-inspired · v0.1
          </div>
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  );
}
