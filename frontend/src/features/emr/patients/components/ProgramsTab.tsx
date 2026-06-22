import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ClipboardList, Plus } from "lucide-react";
import { emrApi } from "../../api";
import { usePrograms, useProgramWorkflowStates, useProgramWorkflows } from "../../queries";
import type { Patient, PatientProgram } from "../../types";
import { ApiError } from "@/lib/api/types";
import { formatDate } from "@/lib/format";
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

export function ProgramsTab({ patient }: { patient: Patient }) {
  const { data, isLoading } = useQuery({
    queryKey: ["patient-programs", { patient: patient.id }],
    queryFn: () => emrApi.listPatientPrograms({ patient: patient.id }),
  });

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-2 text-base">
          <ClipboardList className="size-4" /> Program enrolments
        </CardTitle>
        <EnrolDialog patientId={patient.id} />
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : data && data.results.length > 0 ? (
          <ul className="divide-y">
            {data.results.map((p) => (
              <li key={p.id} className="flex flex-wrap items-center justify-between gap-2 py-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{p.program_name}</span>
                    {p.date_completed ? (
                      <Badge variant="secondary">Completed</Badge>
                    ) : (
                      <Badge variant="success">Active</Badge>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Enrolled {formatDate(p.date_enrolled)}
                    {p.date_completed ? ` · Completed ${formatDate(p.date_completed)}` : ""}
                  </p>
                  {p.states.length > 0 && (
                    <div className="flex flex-wrap gap-1 pt-1">
                      {p.states.map((s) => (
                        <Badge key={s.id} variant="outline" className="text-[10px]">
                          {s.state_name}
                          {s.end_date ? "" : " (current)"}
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
                <AddStateDialog patientProgram={p} />
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState
            icon={<ClipboardList className="size-8" />}
            title="No program enrolments"
            description="Enrol this patient in a care program to track their workflow state."
          />
        )}
      </CardContent>
    </Card>
  );
}

function EnrolDialog({ patientId }: { patientId: number }) {
  const [open, setOpen] = React.useState(false);
  const [program, setProgram] = React.useState("");
  const [dateEnrolled, setDateEnrolled] = React.useState("");
  const [formError, setFormError] = React.useState<string | null>(null);

  const queryClient = useQueryClient();
  const { toast } = useToast();
  const programs = usePrograms();

  function reset() {
    setProgram("");
    setDateEnrolled("");
    setFormError(null);
  }

  const create = useMutation({
    mutationFn: () =>
      emrApi.enrolPatientInProgram({
        patient: patientId,
        program: Number(program),
        date_enrolled: dateEnrolled || new Date().toISOString().slice(0, 10),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["patient-programs", { patient: patientId }] });
      toast({ title: "Patient enrolled", variant: "success" });
      setOpen(false);
      reset();
    },
    onError: (err) =>
      setFormError(err instanceof ApiError ? err.toUserMessage() : "Could not enrol patient."),
  });

  function submit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    if (!program) {
      setFormError("Select a program.");
      return;
    }
    create.mutate();
  }

  return (
    <Dialog open={open} onOpenChange={(o) => { setOpen(o); if (!o) reset(); }}>
      <DialogTrigger asChild>
        <Button size="sm" variant="outline">
          <Plus className="size-4" /> Enrol in program
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Enrol in program</DialogTitle>
        </DialogHeader>
        <form onSubmit={submit} className="space-y-4">
          <div className="space-y-2">
            <Label>Program *</Label>
            <Select value={program} onValueChange={setProgram}>
              <SelectTrigger><SelectValue placeholder="Select program" /></SelectTrigger>
              <SelectContent>
                {programs.data?.map((p) => (
                  <SelectItem key={p.id} value={String(p.id)}>{p.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="enrol-date">Date enrolled</Label>
            <input
              id="enrol-date"
              type="date"
              value={dateEnrolled}
              onChange={(e) => setDateEnrolled(e.target.value)}
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
              {create.isPending ? <Spinner className="size-4" /> : "Enrol"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function AddStateDialog({ patientProgram }: { patientProgram: PatientProgram }) {
  const [open, setOpen] = React.useState(false);
  const [workflow, setWorkflow] = React.useState("");
  const [state, setState] = React.useState("");
  const [startDate, setStartDate] = React.useState("");
  const [formError, setFormError] = React.useState<string | null>(null);

  const queryClient = useQueryClient();
  const { toast } = useToast();
  const workflows = useProgramWorkflows(patientProgram.program);
  const states = useProgramWorkflowStates(workflow ? Number(workflow) : undefined);

  function reset() {
    setWorkflow("");
    setState("");
    setStartDate("");
    setFormError(null);
  }

  const create = useMutation({
    mutationFn: () =>
      emrApi.addPatientState({
        patient_program: patientProgram.id,
        state: Number(state),
        start_date: startDate || new Date().toISOString().slice(0, 10),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["patient-programs"] });
      toast({ title: "State added", variant: "success" });
      setOpen(false);
      reset();
    },
    onError: (err) =>
      setFormError(err instanceof ApiError ? err.toUserMessage() : "Could not add state."),
  });

  function submit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    if (!state) {
      setFormError("Select a state.");
      return;
    }
    create.mutate();
  }

  return (
    <Dialog open={open} onOpenChange={(o) => { setOpen(o); if (!o) reset(); }}>
      <DialogTrigger asChild>
        <Button size="sm" variant="ghost">
          <Plus className="size-4" /> Add state
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add workflow state</DialogTitle>
        </DialogHeader>
        <form onSubmit={submit} className="space-y-4">
          <div className="space-y-2">
            <Label>Workflow *</Label>
            <Select value={workflow} onValueChange={(v) => { setWorkflow(v); setState(""); }}>
              <SelectTrigger><SelectValue placeholder="Select workflow" /></SelectTrigger>
              <SelectContent>
                {workflows.data?.map((w) => (
                  <SelectItem key={w.id} value={String(w.id)}>{w.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>State *</Label>
            <Select value={state} onValueChange={setState} disabled={!workflow}>
              <SelectTrigger><SelectValue placeholder="Select state" /></SelectTrigger>
              <SelectContent>
                {states.data?.map((s) => (
                  <SelectItem key={s.id} value={String(s.id)}>{s.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="state-start">Start date</Label>
            <input
              id="state-start"
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
              {create.isPending ? <Spinner className="size-4" /> : "Add state"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
