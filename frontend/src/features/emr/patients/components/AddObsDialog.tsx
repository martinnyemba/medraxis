import * as React from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Check, Plus, Search } from "lucide-react";
import { emrApi } from "../../api";
import { useConceptSearch } from "../../queries";
import type { Concept, Encounter, Obs, Patient } from "../../types";
import { ApiError } from "@/lib/api/types";
import { useDebounce } from "@/lib/hooks";
import { cn } from "@/lib/utils";
import { useToast } from "@/components/ui/toast";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

/** Decide which Obs value_* field a concept's datatype maps to. */
function valueKind(concept: Concept): "numeric" | "boolean" | "text" {
  const dt = concept.datatype_name?.toLowerCase() ?? "";
  if (dt.includes("numeric")) return "numeric";
  if (dt.includes("boolean")) return "boolean";
  return "text";
}

export function AddObsDialog({
  patient,
  encounter,
}: {
  patient: Patient;
  encounter: Encounter;
}) {
  const [open, setOpen] = React.useState(false);
  const [concept, setConcept] = React.useState<Concept | null>(null);
  const [value, setValue] = React.useState("");
  const [formError, setFormError] = React.useState<string | null>(null);

  const queryClient = useQueryClient();
  const { toast } = useToast();

  function reset() {
    setConcept(null);
    setValue("");
    setFormError(null);
  }

  const create = useMutation({
    mutationFn: () => {
      if (!concept) throw new Error("No concept selected");
      const payload: Partial<Obs> = {
        person: patient.id,
        concept: concept.id,
        encounter: encounter.id,
        obs_datetime: new Date().toISOString(),
      };
      const kind = valueKind(concept);
      if (kind === "numeric") payload.value_numeric = Number(value);
      else if (kind === "boolean") payload.value_boolean = value === "true";
      else payload.value_text = value;
      return emrApi.createObs(payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["observations", { encounter: encounter.id }] });
      toast({ title: "Observation recorded", variant: "success" });
      setOpen(false);
      reset();
    },
    onError: (err) =>
      setFormError(err instanceof ApiError ? err.toUserMessage() : "Could not save observation."),
  });

  function submit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    if (!concept) {
      setFormError("Select a concept.");
      return;
    }
    if (!value.trim()) {
      setFormError("Enter a value.");
      return;
    }
    create.mutate();
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(o) => {
        setOpen(o);
        if (!o) reset();
      }}
    >
      <DialogTrigger asChild>
        <Button size="sm" variant="outline">
          <Plus className="size-4" /> Add observation
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add observation</DialogTitle>
        </DialogHeader>
        <form onSubmit={submit} className="space-y-4">
          {concept ? (
            <SelectedConcept concept={concept} onClear={() => { setConcept(null); setValue(""); }} />
          ) : (
            <ConceptPicker onSelect={setConcept} />
          )}

          {concept && (
            <ObsValueField concept={concept} value={value} onChange={setValue} />
          )}

          {formError && (
            <p className="whitespace-pre-line rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {formError}
            </p>
          )}

          <DialogFooter>
            <Button type="submit" disabled={create.isPending || !concept}>
              {create.isPending ? <Spinner className="size-4" /> : "Save observation"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function SelectedConcept({ concept, onClear }: { concept: Concept; onClear: () => void }) {
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

function ConceptPicker({ onSelect }: { onSelect: (c: Concept) => void }) {
  const [term, setTerm] = React.useState("");
  const debounced = useDebounce(term, 300);
  const { data: concepts, isFetching } = useConceptSearch(debounced);

  return (
    <div className="space-y-2">
      <Label>Concept *</Label>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          autoFocus
          placeholder="Search concepts (e.g. weight, temperature)…"
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

function ObsValueField({
  concept,
  value,
  onChange,
}: {
  concept: Concept;
  value: string;
  onChange: (v: string) => void;
}) {
  const kind = valueKind(concept);

  if (kind === "boolean") {
    return (
      <div className="space-y-2">
        <Label>Value</Label>
        <div className="flex gap-2">
          {[
            { v: "true", label: "Yes" },
            { v: "false", label: "No" },
          ].map((opt) => (
            <Button
              key={opt.v}
              type="button"
              variant={value === opt.v ? "default" : "outline"}
              onClick={() => onChange(opt.v)}
            >
              {opt.label}
            </Button>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <Label htmlFor="obs-value">
        Value{concept.units ? ` (${concept.units})` : ""}
      </Label>
      <Input
        id="obs-value"
        type={kind === "numeric" ? "number" : "text"}
        step="any"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={kind === "numeric" ? "Enter a number" : "Enter a value"}
      />
      {kind === "numeric" && (concept.low_normal != null || concept.hi_normal != null) && (
        <p className="text-xs text-muted-foreground">
          Reference range: {concept.low_normal ?? "—"} – {concept.hi_normal ?? "—"}
          {concept.units ? ` ${concept.units}` : ""}
        </p>
      )}
    </div>
  );
}
