import { Building2 } from "lucide-react";
import { useTenant } from "@/features/tenancy/TenantContext";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export function OrgSwitcher() {
  const { organizations, current, setCurrent, isLoading } = useTenant();

  if (isLoading) {
    return <div className="h-9 w-28 animate-pulse rounded-md bg-muted sm:w-44" />;
  }
  if (organizations.length === 0) {
    return (
      <div className="flex min-w-0 items-center gap-2 text-sm text-muted-foreground">
        <Building2 className="size-4 shrink-0" />
        <span className="hidden truncate sm:inline">No facility</span>
      </div>
    );
  }

  return (
    <Select value={current?.slug ?? undefined} onValueChange={setCurrent}>
      <SelectTrigger className="w-28 sm:w-52">
        <span className="flex items-center gap-2 truncate">
          <Building2 className="size-4 shrink-0 text-muted-foreground" />
          <SelectValue placeholder="Select facility" />
        </span>
      </SelectTrigger>
      <SelectContent>
        {organizations.map((org) => (
          <SelectItem key={org.slug} value={org.slug}>
            {org.name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
