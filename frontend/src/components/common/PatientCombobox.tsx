import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { Check, Search, X } from "lucide-react";
import { emrApi } from "@/features/emr/api";
import type { Patient } from "@/features/emr/types";
import { patientName, preferredIdentifier, genderLabel, ageFromBirthdate } from "@/lib/format";
import { useDebounce } from "@/lib/hooks";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

/** Reusable patient picker used by lab ordering and POS. */
export function PatientCombobox({
  value,
  onSelect,
}: {
  value: Patient | null;
  onSelect: (patient: Patient | null) => void;
}) {
  const [term, setTerm] = React.useState("");
  const search = useDebounce(term, 300);

  const { data, isFetching } = useQuery({
    queryKey: ["patients", { search, page: 1, picker: true }],
    queryFn: () => emrApi.listPatients({ search, page_size: 8 }),
    enabled: search.length >= 2 && !value,
  });

  if (value) {
    return (
      <div className="flex items-center justify-between rounded-md border bg-accent/40 px-3 py-2">
        <div className="flex items-center gap-2">
          <Check className="size-4 text-success" />
          <div>
            <p className="text-sm font-medium">{patientName(value)}</p>
            <p className="text-xs text-muted-foreground">
              {preferredIdentifier(value) ?? "—"} · {genderLabel(value.gender)}
              {ageFromBirthdate(value.birthdate) !== null
                ? ` · ${ageFromBirthdate(value.birthdate)} yr`
                : ""}
            </p>
          </div>
        </div>
        <Button type="button" variant="ghost" size="sm" onClick={() => onSelect(null)}>
          <X className="size-4" /> Change
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          autoFocus
          placeholder="Search patient by name or identifier…"
          className="pl-9"
          value={term}
          onChange={(e) => setTerm(e.target.value)}
        />
      </div>
      {search.length >= 2 && (
        <div className="max-h-56 overflow-y-auto rounded-md border">
          {isFetching ? (
            <p className="p-3 text-sm text-muted-foreground">Searching…</p>
          ) : data && data.results.length > 0 ? (
            data.results.map((p) => (
              <button
                key={p.id}
                type="button"
                onClick={() => onSelect(p)}
                className="flex w-full items-center justify-between px-3 py-2 text-left text-sm hover:bg-accent"
              >
                <span className="font-medium">{patientName(p)}</span>
                <span className="font-mono text-xs text-muted-foreground">
                  {preferredIdentifier(p) ?? "—"}
                </span>
              </button>
            ))
          ) : (
            <p className="p-3 text-sm text-muted-foreground">No patients found.</p>
          )}
        </div>
      )}
    </div>
  );
}
