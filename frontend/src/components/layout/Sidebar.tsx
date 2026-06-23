import { Activity } from "lucide-react";
import { NavList } from "./NavList";

export function Sidebar() {
  return (
    <aside className="hidden w-64 shrink-0 flex-col border-r bg-card md:flex">
      <div className="flex h-16 items-center gap-2 border-b px-6">
        <div className="flex size-8 items-center justify-center rounded-md bg-primary text-primary-foreground">
          <Activity className="size-5" />
        </div>
        <div className="leading-tight">
          <p className="text-sm font-semibold">Medraxis</p>
          <p className="text-xs text-muted-foreground">Health Platform</p>
        </div>
      </div>

      <NavList />

      <div className="border-t p-4 text-xs text-muted-foreground">
        OpenMRS-inspired · v0.1
      </div>
    </aside>
  );
}
