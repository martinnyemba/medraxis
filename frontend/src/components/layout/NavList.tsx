import { NavLink } from "react-router-dom";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { NAV_ITEMS } from "./navigation";

export function NavList({ onNavigate }: { onNavigate?: () => void }) {
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
