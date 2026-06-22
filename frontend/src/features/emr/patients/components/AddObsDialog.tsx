import * as React from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { emrApi } from "../../api";
import type { Concept, Encounter, Obs, Patient } from "../../types";
import { ApiError } from "@/lib/api/types";
import { useToast } from "@/components/ui/toast";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Spinner } from "@/components/ui/spinner";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { ConceptPicker, SelectedConcept } from "./ConceptPicker";

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
            <ConceptPicker
              placeholder="Search concepts (e.g. weight, temperature)…"
              onSelect={setConcept}
            />
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
