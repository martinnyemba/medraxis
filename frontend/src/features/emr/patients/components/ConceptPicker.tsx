import * as React from "react";
import { Check, Search } from "lucide-react";
import { useConceptSearch } from "../../queries";
import type { Concept } from "../../types";
import { useDebounce } from "@/lib/hooks";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";

/** Searchable concept dropdown shared by observation/allergy/condition/diagnosis entry. */
export function ConceptPicker({
  label = "Concept *",
  placeholder = "Search concepts…",
  onSelect,
}: {
  label?: string;
  placeholder?: string;
  onSelect: (c: Concept) => void;
}) {
  const [term, setTerm] = React.useState("");
  const debounced = useDebounce(term, 300);
  const { data: concepts, isFetching } = useConceptSearch(debounced);

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
        ) : concepts && concepts.length > 0 ? (
          concepts.map((c) => (
            <button
              key={c.id}
              type="button"
              onClick={() => onSelect(c)}
              className={cn(
                "flex w-full items-center justify-between px-3 py-2 text-left text-sm hover:bg-accent",
              )}
            >
              <span className="font-medium">{c.name}</span>
              <Badge variant="secondary" className="text-[10px]">
                {c.datatype_name}
              </Badge>
            </button>
          ))
        ) : (
          <p className="p-3 text-sm text-muted-foreground">No concepts found.</p>
        )}
      </div>
    </div>
  );
}

export function SelectedConcept({ concept, onClear }: { concept: Concept; onClear: () => void }) {
  return (
    <div className="flex items-center justify-between rounded-md border bg-accent/40 px-3 py-2">
      <div className="flex items-center gap-2">
        <Check className="size-4 text-success" />
        <div>
          <p className="text-sm font-medium">{concept.name}</p>
          <p className="text-xs text-muted-foreground">{concept.datatype_name}</p>
        </div>
      </div>
      <Button type="button" variant="ghost" size="sm" onClick={onClear}>
        Change
      </Button>
    </div>
  );
}
