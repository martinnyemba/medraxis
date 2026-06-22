import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Users } from "lucide-react";
import { emrApi } from "../../api";
import { useRelationshipTypes } from "../../queries";
import type { Patient } from "../../types";
import { ApiError } from "@/lib/api/types";
import { useToast } from "@/components/ui/toast";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
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
import { PatientPicker, SelectedPatient } from "./PatientPicker";

export function RelationshipsTab({ patient }: { patient: Patient }) {
  const personId = patient.person_id;

  const { data: asA, isLoading: loadingA } = useQuery({
    queryKey: ["relationships", { person_a: personId }],
    queryFn: () => emrApi.listRelationships({ person_a: personId }),
  });
  const { data: asB, isLoading: loadingB } = useQuery({
    queryKey: ["relationships", { person_b: personId }],
    queryFn: () => emrApi.listRelationships({ person_b: personId }),
  });
  const { data: relationshipTypes } = useRelationshipTypes();

  const isLoading = loadingA || loadingB;
  const relationships = [
    ...(asA?.results.map((r) => ({ rel: r, otherPersonId: r.person_b, asA: true })) ?? []),
    ...(asB?.results.map((r) => ({ rel: r, otherPersonId: r.person_a, asA: false })) ?? []),
  ];

  function relationshipLabel(typeId: number, asA: boolean) {
    const type = relationshipTypes?.find((t) => t.id === typeId);
    if (!type) return "—";
    return asA ? type.a_is_to_b : type.b_is_to_a;
  }

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-2 text-base">
          <Users className="size-4" /> Relationships
        </CardTitle>
        <AddRelationshipDialog patient={patient} />
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : relationships.length > 0 ? (
          <ul className="divide-y">
            {relationships.map(({ rel, otherPersonId, asA }) => (
              <li key={rel.id} className="flex flex-wrap items-center justify-between gap-2 py-2 text-sm">
                <div>
                  <Badge variant="secondary" className="mr-2">
                    {relationshipLabel(rel.relationship_type, asA)}
                  </Badge>
                  <span className="text-muted-foreground">Person #{otherPersonId}</span>
                </div>
                {!rel.end_date && <Badge variant="success">Active</Badge>}
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState
            icon={<Users className="size-8" />}
            title="No relationships recorded"
            description="Link this patient to a guardian, next of kin, or other related person."
          />
        )}
      </CardContent>
    </Card>
  );
}

function AddRelationshipDialog({ patient }: { patient: Patient }) {
  const [open, setOpen] = React.useState(false);
  const [other, setOther] = React.useState<Patient | null>(null);
  const [relationshipType, setRelationshipType] = React.useState("");
  const [startDate, setStartDate] = React.useState("");
  const [formError, setFormError] = React.useState<string | null>(null);

  const queryClient = useQueryClient();
  const { toast } = useToast();
  const relationshipTypes = useRelationshipTypes();

  function reset() {
    setOther(null);
    setRelationshipType("");
    setStartDate("");
    setFormError(null);
  }

  const create = useMutation({
    mutationFn: () => {
      if (!other) throw new Error("No person selected");
      return emrApi.createRelationship({
        person_a: patient.person_id,
        person_b: other.person_id,
        relationship_type: Number(relationshipType),
        start_date: startDate || null,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["relationships"] });
      toast({ title: "Relationship added", variant: "success" });
      setOpen(false);
      reset();
    },
    onError: (err) =>
      setFormError(err instanceof ApiError ? err.toUserMessage() : "Could not add relationship."),
  });

  function submit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    if (!other || !relationshipType) {
      setFormError("Select the related person and a relationship type.");
      return;
    }
    create.mutate();
  }

  return (
    <Dialog open={open} onOpenChange={(o) => { setOpen(o); if (!o) reset(); }}>
      <DialogTrigger asChild>
        <Button size="sm" variant="outline">
          <Plus className="size-4" /> Add relationship
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add relationship</DialogTitle>
        </DialogHeader>
        <form onSubmit={submit} className="space-y-4">
          {other ? (
            <SelectedPatient patient={other} onClear={() => setOther(null)} />
          ) : (
            <PatientPicker exclude={patient.id} onSelect={setOther} />
          )}
          <div className="space-y-2">
            <Label>Relationship type *</Label>
            <Select value={relationshipType} onValueChange={setRelationshipType}>
              <SelectTrigger><SelectValue placeholder="Select type" /></SelectTrigger>
              <SelectContent>
                {relationshipTypes.data?.map((t) => (
                  <SelectItem key={t.id} value={String(t.id)}>
                    {t.a_is_to_b} / {t.b_is_to_a}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="rel-start">Start date</Label>
            <input
              id="rel-start"
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="flex h-9 w-full rounded-md border border-input bg-card px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
          {formError && (
            <p className="whitespace-pre-line rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {formError}
            </p>
          )}
          <DialogFooter>
            <Button type="submit" disabled={create.isPending}>
              {create.isPending ? <Spinner className="size-4" /> : "Save relationship"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
