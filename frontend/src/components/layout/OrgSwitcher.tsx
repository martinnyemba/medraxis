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
    return <div className="h-9 w-44 animate-pulse rounded-md bg-muted" />;
  }
  if (organizations.length === 0) {
    return (
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Building2 className="size-4" /> No facility
      </div>
    );
  }

  return (
    <Select value={current?.slug ?? undefined} onValueChange={setCurrent}>
      <SelectTrigger className="w-52">
        <span className="flex items-center gap-2 truncate">
          <Building2 className="size-4 text-muted-foreground" />
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
