import * as React from "react";
import { Check, Search } from "lucide-react";
import { usePatientSearch } from "../../queries";
import type { Patient } from "../../types";
import { patientName, preferredIdentifier } from "@/lib/format";
import { useDebounce } from "@/lib/hooks";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";

/** Searchable patient dropdown, used for picking the other party in a relationship. */
export function PatientPicker({
  label = "Patient *",
  placeholder = "Search by name or identifier…",
  exclude,
  onSelect,
}: {
  label?: string;
  placeholder?: string;
  /** Patient id to exclude from results (e.g. the patient already in context). */
  exclude?: number;
  onSelect: (p: Patient) => void;
}) {
  const [term, setTerm] = React.useState("");
  const debounced = useDebounce(term, 300);
  const { data: patients, isFetching } = usePatientSearch(debounced);
  const results = patients?.filter((p) => p.id !== exclude);

  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          autoFocus
          placeholder={placeholder}
          className="pl-9"
          value={term}
          onChange={(e) => setTerm(e.target.value)}
        />
      </div>
      <div className="max-h-52 overflow-y-auto rounded-md border">
        {debounced.length < 2 ? (
          <p className="p-3 text-sm text-muted-foreground">Type at least 2 characters to search.</p>
        ) : isFetching ? (
          <p className="p-3 text-sm text-muted-foreground">Searching…</p>
        ) : results && results.length > 0 ? (
          results.map((p) => (
            <button
              key={p.id}
              type="button"
              onClick={() => onSelect(p)}
              className={cn(
                "flex w-full items-center justify-between px-3 py-2 text-left text-sm hover:bg-accent",
              )}
            >
              <span className="font-medium">{patientName(p)}</span>
              <Badge variant="secondary" className="text-[10px] font-mono">
                {preferredIdentifier(p) ?? "—"}
              </Badge>
            </button>
          ))
        ) : (
          <p className="p-3 text-sm text-muted-foreground">No patients found.</p>
        )}
      </div>
    </div>
  );
}

export function SelectedPatient({ patient, onClear }: { patient: Patient; onClear: () => void }) {
  return (
    <div className="flex items-center justify-between rounded-md border bg-accent/40 px-3 py-2">
      <div className="flex items-center gap-2">
        <Check className="size-4 text-success" />
        <div>
          <p className="text-sm font-medium">{patientName(patient)}</p>
          <p className="text-xs text-muted-foreground font-mono">
            {preferredIdentifier(patient) ?? "—"}
          </p>
        </div>
      </div>
      <Button type="button" variant="ghost" size="sm" onClick={onClear}>
        Change
      </Button>
    </div>
  );
}
