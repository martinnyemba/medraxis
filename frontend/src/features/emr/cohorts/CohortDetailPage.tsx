import * as React from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation, useQueries, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Layers, Plus, UserMinus } from "lucide-react";
import { emrApi } from "../api";
import { patientName, preferredIdentifier, formatDate } from "@/lib/format";
import { ApiError } from "@/lib/api/types";
import { useAuth } from "@/features/auth/AuthContext";
import { useToast } from "@/components/ui/toast";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { PageLoader, Spinner } from "@/components/ui/spinner";
import { ErrorState, EmptyState } from "@/components/common/states";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { PatientPicker, SelectedPatient } from "../patients/components/PatientPicker";
import type { Patient } from "../types";

export function CohortDetailPage() {
  const { cohortId } = useParams<{ cohortId: string }>();
  const id = Number(cohortId);
  const { can } = useAuth();
  const canManage = can("Manage Cohorts");

  const { data: cohort, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["cohort", id],
    queryFn: () => emrApi.getCohort(id),
    enabled: Number.isFinite(id),
  });

  const { data: memberships, isLoading: loadingMembers } = useQuery({
    queryKey: ["cohort-memberships", { cohort: id }],
    queryFn: () => emrApi.listCohortMemberships({ cohort: id, page_size: 200 }),
    enabled: Number.isFinite(id),
  });

  const activeMemberships = memberships?.results.filter((m) => !m.end_date) ?? [];

  const patientQueries = useQueries({
    queries: activeMemberships.map((m) => ({
      queryKey: ["patient", m.patient],
      queryFn: () => emrApi.getPatient(m.patient),
    })),
  });

  if (isLoading) return <PageLoader />;
  if (isError || !cohort) return <ErrorState error={error} onRetry={refetch} />;

  return (
    <div>
      <Button variant="ghost" size="sm" asChild className="mb-2 -ml-2">
        <Link to="/emr/cohorts">
          <ArrowLeft className="size-4" /> Back to cohorts
        </Link>
      </Button>

      <Card className="mb-6">
        <CardContent className="space-y-2 pt-6">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-semibold tracking-tight">{cohort.name}</h1>
            {cohort.retired ? (
              <Badge variant="secondary">Retired</Badge>
            ) : (
              <Badge variant="success">Active</Badge>
            )}
          </div>
          <p className="text-sm text-muted-foreground">{cohort.description || "No description."}</p>
        </CardContent>
      </Card>

      <Card>
        <div className="flex items-center justify-between p-4">
          <h2 className="flex items-center gap-2 text-base font-semibold">
            <Layers className="size-4" /> Members ({cohort.member_count})
          </h2>
          {canManage && <AddMemberDialog cohortId={id} />}
        </div>
        <CardContent className="pt-0">
          {loadingMembers ? (
            <p className="text-sm text-muted-foreground">Loading…</p>
          ) : activeMemberships.length > 0 ? (
            <ul className="divide-y">
              {activeMemberships.map((m, idx) => {
                const patient = patientQueries[idx]?.data;
                return (
                  <li key={m.id} className="flex flex-wrap items-center justify-between gap-2 py-2 text-sm">
                    <div>
                      <Link to={`/emr/patients/${m.patient}`} className="font-medium hover:underline">
                        {patient ? patientName(patient) : `Patient #${m.patient}`}
                      </Link>
                      {patient && (
                        <span className="ml-2 font-mono text-xs text-muted-foreground">
                          {preferredIdentifier(patient) ?? "—"}
                        </span>
                      )}
                      <span className="ml-2 text-xs text-muted-foreground">
                        Since {formatDate(m.start_date)}
                      </span>
                    </div>
                    {canManage && <RemoveMemberButton cohortId={id} membershipId={m.id} />}
                  </li>
                );
              })}
            </ul>
          ) : (
            <EmptyState icon={<Layers className="size-8" />} title="No members in this cohort yet" />
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function AddMemberDialog({ cohortId }: { cohortId: number }) {
  const [open, setOpen] = React.useState(false);
  const [picked, setPicked] = React.useState<Patient | null>(null);
  const [formError, setFormError] = React.useState<string | null>(null);

  const queryClient = useQueryClient();
  const { toast } = useToast();

  function reset() {
    setPicked(null);
    setFormError(null);
  }

  const create = useMutation({
    mutationFn: () => {
      if (!picked) throw new Error("No patient selected");
      return emrApi.addCohortMember({
        cohort: cohortId,
        patient: picked.id,
        start_date: new Date().toISOString().slice(0, 10),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cohort-memberships", { cohort: cohortId }] });
      queryClient.invalidateQueries({ queryKey: ["cohort", cohortId] });
      toast({ title: "Member added", variant: "success" });
      setOpen(false);
      reset();
    },
    onError: (err) =>
      setFormError(err instanceof ApiError ? err.toUserMessage() : "Could not add member."),
  });

  function submit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    if (!picked) {
      setFormError("Select a patient to add.");
      return;
    }
    create.mutate();
  }

  return (
    <Dialog open={open} onOpenChange={(o) => { setOpen(o); if (!o) reset(); }}>
      <DialogTrigger asChild>
        <Button size="sm" variant="outline">
          <Plus className="size-4" /> Add member
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add cohort member</DialogTitle>
        </DialogHeader>
        <form onSubmit={submit} className="space-y-4">
          {picked ? (
            <SelectedPatient patient={picked} onClear={() => setPicked(null)} />
          ) : (
            <PatientPicker onSelect={setPicked} />
          )}
          {formError && (
            <p className="whitespace-pre-line rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {formError}
            </p>
          )}
          <DialogFooter>
            <Button type="submit" disabled={create.isPending}>
              {create.isPending ? <Spinner className="size-4" /> : "Add to cohort"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function RemoveMemberButton({ cohortId, membershipId }: { cohortId: number; membershipId: number }) {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const end = useMutation({
    mutationFn: () => emrApi.endCohortMembership(membershipId, new Date().toISOString().slice(0, 10)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cohort-memberships", { cohort: cohortId }] });
      queryClient.invalidateQueries({ queryKey: ["cohort", cohortId] });
      toast({ title: "Member removed", variant: "success" });
    },
    onError: (err) =>
      toast({
        title: "Could not remove member",
        description: err instanceof ApiError ? err.toUserMessage() : undefined,
        variant: "error",
      }),
  });

  return (
    <Button size="sm" variant="ghost" onClick={() => end.mutate()} disabled={end.isPending}>
      {end.isPending ? <Spinner className="size-4" /> : <UserMinus className="size-4" />}
    </Button>
  );
}
