import { NavLink } from "react-router-dom";
import { cn } from "@/lib/utils";

const TABS = [
  { to: "/lis/worklist", label: "Worklist" },
  { to: "/lis/catalog", label: "Catalog" },
  { to: "/lis/qc", label: "Quality control" },
  { to: "/lis/partners", label: "Clients & partners" },
];

/** Secondary navigation across the LIS sub-sections. */
export function LisTabs() {
  return (
    <div className="mb-4 flex flex-wrap gap-1 border-b">
      {TABS.map((t) => (
        <NavLink
          key={t.to}
          to={t.to}
          className={({ isActive }) =>
            cn(
              "border-b-2 px-3 py-2 text-sm font-medium transition-colors",
              isActive
                ? "border-primary text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground",
            )
          }
        >
          {t.label}
        </NavLink>
      ))}
    </div>
  );
}
