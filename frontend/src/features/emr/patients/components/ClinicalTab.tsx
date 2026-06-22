import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, Plus, ShieldAlert, Stethoscope } from "lucide-react";
import { emrApi } from "../../api";
import type {
  AllergyCategory,
  AllergySeverity,
  Concept,
  Condition,
  ConditionClinicalStatus,
  Diagnosis,
  DiagnosisCertainty,
  Patient,
} from "../../types";
import { ApiError } from "@/lib/api/types";
import { formatDate } from "@/lib/format";
import { useToast } from "@/components/ui/toast";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge, type BadgeProps } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { EmptyState } from "@/components/common/states";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ConceptPicker, SelectedConcept } from "./ConceptPicker";

export function ClinicalTab({ patient }: { patient: Patient }) {
  return (
    <div className="space-y-6">
      <AllergiesSection patientId={patient.id} />
      <ConditionsSection patientId={patient.id} />
      <DiagnosesSection patientId={patient.id} />
    </div>
  );
}

const SEVERITY_VARIANT: Record<AllergySeverity, BadgeProps["variant"]> = {
  MILD: "secondary",
  MODERATE: "warning",
  SEVERE: "destructive",
};

const STATUS_VARIANT: Record<ConditionClinicalStatus, BadgeProps["variant"]> = {
  ACTIVE: "warning",
  INACTIVE: "secondary",
  RESOLVED: "success",
};

function AllergiesSection({ patientId }: { patientId: number }) {
  const { data, isLoading } = useQuery({
    queryKey: ["allergies", { patient: patientId }],
    queryFn: () => emrApi.listAllergies({ patient: patientId }),
  });

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-2 text-base">
          <ShieldAlert className="size-4" /> Allergies
        </CardTitle>
        <CreateAllergyDialog patientId={patientId} />
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : data && data.results.length > 0 ? (
          <ul className="divide-y">
            {data.results.map((a) => (
              <li key={a.id} className="flex flex-wrap items-center justify-between gap-2 py-2 text-sm">
                <div>
                  <span className="font-medium">{a.allergen_name}</span>
                  {a.reaction && (
                    <span className="ml-2 text-muted-foreground">— {a.reaction}</span>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="outline">{a.category}</Badge>
                  <Badge variant={SEVERITY_VARIANT[a.severity]}>{a.severity}</Badge>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState
            icon={<ShieldAlert className="size-8" />}
            title="No known allergies recorded"
            description="Record an allergy to flag it across the patient's chart."
          />
        )}
      </CardContent>
    </Card>
  );
}

function CreateAllergyDialog({ patientId }: { patientId: number }) {
  const [open, setOpen] = React.useState(false);
  const [allergen, setAllergen] = React.useState<Concept | null>(null);
  const [category, setCategory] = React.useState<AllergyCategory>("DRUG");
  const [severity, setSeverity] = React.useState<AllergySeverity>("MODERATE");
  const [reaction, setReaction] = React.useState("");
  const [comment, setComment] = React.useState("");
  const [formError, setFormError] = React.useState<string | null>(null);

  const queryClient = useQueryClient();
  const { toast } = useToast();

  function reset() {
    setAllergen(null);
    setCategory("DRUG");
    setSeverity("MODERATE");
    setReaction("");
    setComment("");
    setFormError(null);
  }

  const create = useMutation({
    mutationFn: () => {
      if (!allergen) throw new Error("No allergen selected");
      return emrApi.createAllergy({
        patient: patientId,
        allergen: allergen.id,
        category,
        severity,
        reaction,
        comment,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["allergies", { patient: patientId }] });
      toast({ title: "Allergy recorded", variant: "success" });
      setOpen(false);
      reset();
    },
    onError: (err) =>
      setFormError(err instanceof ApiError ? err.toUserMessage() : "Could not save allergy."),
  });

  function submit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    if (!allergen) {
      setFormError("Select an allergen.");
      return;
    }
    create.mutate();
  }

  return (
    <Dialog open={open} onOpenChange={(o) => { setOpen(o); if (!o) reset(); }}>
      <DialogTrigger asChild>
        <Button size="sm" variant="outline">
          <Plus className="size-4" /> Record allergy
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Record allergy</DialogTitle>
        </DialogHeader>
        <form onSubmit={submit} className="space-y-4">
          {allergen ? (
            <SelectedConcept concept={allergen} onClear={() => setAllergen(null)} />
          ) : (
            <ConceptPicker label="Allergen *" placeholder="Search allergens…" onSelect={setAllergen} />
          )}

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Category</Label>
              <Select value={category} onValueChange={(v) => setCategory(v as AllergyCategory)}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="DRUG">Drug</SelectItem>
                  <SelectItem value="FOOD">Food</SelectItem>
                  <SelectItem value="ENVIRONMENT">Environment</SelectItem>
                  <SelectItem value="OTHER">Other</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Severity</Label>
              <Select value={severity} onValueChange={(v) => setSeverity(v as AllergySeverity)}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="MILD">Mild</SelectItem>
                  <SelectItem value="MODERATE">Moderate</SelectItem>
                  <SelectItem value="SEVERE">Severe</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="allergy-reaction">Reaction</Label>
            <Input
              id="allergy-reaction"
              value={reaction}
              onChange={(e) => setReaction(e.target.value)}
              placeholder="e.g. Anaphylaxis, rash"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="allergy-comment">Comment</Label>
            <textarea
              id="allergy-comment"
              className="flex min-h-16 w-full rounded-md border border-input bg-card px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              value={comment}
              onChange={(e) => setComment(e.target.value)}
            />
          </div>

          {formError && (
            <p className="whitespace-pre-line rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {formError}
            </p>
          )}

          <DialogFooter>
            <Button type="submit" disabled={create.isPending || !allergen}>
              {create.isPending ? <Spinner className="size-4" /> : "Save allergy"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function ConditionsSection({ patientId }: { patientId: number }) {
  const { data, isLoading } = useQuery({
    queryKey: ["conditions", { patient: patientId }],
    queryFn: () => emrApi.listConditions({ patient: patientId }),
  });

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-2 text-base">
          <AlertTriangle className="size-4" /> Conditions
        </CardTitle>
        <CreateConditionDialog patientId={patientId} />
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : data && data.results.length > 0 ? (
          <ul className="divide-y">
            {data.results.map((c: Condition) => (
              <li key={c.id} className="flex flex-wrap items-center justify-between gap-2 py-2 text-sm">
                <div>
                  <span className="font-medium">{c.concept_name}</span>
                  <span className="ml-2 text-muted-foreground">
                    Onset {formatDate(c.onset_date)}
                    {c.end_date ? ` — ended ${formatDate(c.end_date)}` : ""}
                  </span>
                </div>
                <Badge variant={STATUS_VARIANT[c.clinical_status]}>{c.clinical_status}</Badge>
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState
            icon={<AlertTriangle className="size-8" />}
            title="No conditions recorded"
            description="Record a clinical condition to track it over time."
          />
        )}
      </CardContent>
    </Card>
  );
}

function CreateConditionDialog({ patientId }: { patientId: number }) {
  const [open, setOpen] = React.useState(false);
  const [concept, setConcept] = React.useState<Concept | null>(null);
  const [clinicalStatus, setClinicalStatus] = React.useState<ConditionClinicalStatus>("ACTIVE");
  const [onsetDate, setOnsetDate] = React.useState("");
  const [formError, setFormError] = React.useState<string | null>(null);

  const queryClient = useQueryClient();
  const { toast } = useToast();

  function reset() {
    setConcept(null);
    setClinicalStatus("ACTIVE");
    setOnsetDate("");
    setFormError(null);
  }

  const create = useMutation({
    mutationFn: () => {
      if (!concept) throw new Error("No condition concept selected");
      return emrApi.createCondition({
        patient: patientId,
        concept: concept.id,
        clinical_status: clinicalStatus,
        onset_date: onsetDate || null,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conditions", { patient: patientId }] });
      toast({ title: "Condition recorded", variant: "success" });
      setOpen(false);
      reset();
    },
    onError: (err) =>
      setFormError(err instanceof ApiError ? err.toUserMessage() : "Could not save condition."),
  });

  function submit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    if (!concept) {
      setFormError("Select a condition.");
      return;
    }
    create.mutate();
  }

  return (
    <Dialog open={open} onOpenChange={(o) => { setOpen(o); if (!o) reset(); }}>
      <DialogTrigger asChild>
        <Button size="sm" variant="outline">
          <Plus className="size-4" /> Record condition
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Record condition</DialogTitle>
        </DialogHeader>
        <form onSubmit={submit} className="space-y-4">
          {concept ? (
            <SelectedConcept concept={concept} onClear={() => setConcept(null)} />
          ) : (
            <ConceptPicker label="Condition *" placeholder="Search conditions…" onSelect={setConcept} />
          )}

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Clinical status</Label>
              <Select
                value={clinicalStatus}
                onValueChange={(v) => setClinicalStatus(v as ConditionClinicalStatus)}
              >
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="ACTIVE">Active</SelectItem>
                  <SelectItem value="INACTIVE">Inactive</SelectItem>
                  <SelectItem value="RESOLVED">Resolved</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="condition-onset">Onset date</Label>
              <Input
                id="condition-onset"
                type="date"
                value={onsetDate}
                onChange={(e) => setOnsetDate(e.target.value)}
              />
            </div>
          </div>

          {formError && (
            <p className="whitespace-pre-line rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {formError}
            </p>
          )}

          <DialogFooter>
            <Button type="submit" disabled={create.isPending || !concept}>
              {create.isPending ? <Spinner className="size-4" /> : "Save condition"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function DiagnosesSection({ patientId }: { patientId: number }) {
  const { data, isLoading } = useQuery({
    queryKey: ["diagnoses", { patient: patientId }],
    queryFn: () => emrApi.listDiagnoses({ patient: patientId, ordering: "rank" }),
  });

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-2 text-base">
          <Stethoscope className="size-4" /> Diagnoses
        </CardTitle>
        <CreateDiagnosisDialog patientId={patientId} />
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : data && data.results.length > 0 ? (
          <ul className="divide-y">
            {data.results.map((d: Diagnosis) => (
              <li key={d.id} className="flex flex-wrap items-center justify-between gap-2 py-2 text-sm">
                <div>
                  <span className="font-medium">#{d.rank}</span>
                  <span className="ml-2">{d.diagnosis_concept_name}</span>
                </div>
                <Badge variant={d.certainty === "CONFIRMED" ? "success" : "secondary"}>
                  {d.certainty}
                </Badge>
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState
            icon={<Stethoscope className="size-8" />}
            title="No diagnoses recorded"
            description="Record a diagnosis to track the patient's clinical picture."
          />
        )}
      </CardContent>
    </Card>
  );
}

function CreateDiagnosisDialog({ patientId }: { patientId: number }) {
  const [open, setOpen] = React.useState(false);
  const [concept, setConcept] = React.useState<Concept | null>(null);
  const [certainty, setCertainty] = React.useState<DiagnosisCertainty>("PROVISIONAL");
  const [rank, setRank] = React.useState("1");
  const [formError, setFormError] = React.useState<string | null>(null);

  const queryClient = useQueryClient();
  const { toast } = useToast();

  function reset() {
    setConcept(null);
    setCertainty("PROVISIONAL");
    setRank("1");
    setFormError(null);
  }

  const create = useMutation({
    mutationFn: () => {
      if (!concept) throw new Error("No diagnosis concept selected");
      return emrApi.createDiagnosis({
        patient: patientId,
        diagnosis_concept: concept.id,
        certainty,
        rank: Number(rank) || 1,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["diagnoses", { patient: patientId }] });
      toast({ title: "Diagnosis recorded", variant: "success" });
      setOpen(false);
      reset();
    },
    onError: (err) =>
      setFormError(err instanceof ApiError ? err.toUserMessage() : "Could not save diagnosis."),
  });

  function submit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    if (!concept) {
      setFormError("Select a diagnosis.");
      return;
    }
    create.mutate();
  }

  return (
    <Dialog open={open} onOpenChange={(o) => { setOpen(o); if (!o) reset(); }}>
      <DialogTrigger asChild>
        <Button size="sm" variant="outline">
          <Plus className="size-4" /> Record diagnosis
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Record diagnosis</DialogTitle>
        </DialogHeader>
        <form onSubmit={submit} className="space-y-4">
          {concept ? (
            <SelectedConcept concept={concept} onClear={() => setConcept(null)} />
          ) : (
            <ConceptPicker label="Diagnosis *" placeholder="Search diagnoses…" onSelect={setConcept} />
          )}

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Certainty</Label>
              <Select value={certainty} onValueChange={(v) => setCertainty(v as DiagnosisCertainty)}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="PROVISIONAL">Provisional</SelectItem>
                  <SelectItem value="CONFIRMED">Confirmed</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="diagnosis-rank">Rank</Label>
              <Input
                id="diagnosis-rank"
                type="number"
                min={1}
                value={rank}
                onChange={(e) => setRank(e.target.value)}
              />
            </div>
          </div>

          {formError && (
            <p className="whitespace-pre-line rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {formError}
            </p>
          )}

          <DialogFooter>
            <Button type="submit" disabled={create.isPending || !concept}>
              {create.isPending ? <Spinner className="size-4" /> : "Save diagnosis"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
