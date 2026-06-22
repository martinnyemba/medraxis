import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CalendarPlus, CheckCircle2, Stethoscope } from "lucide-react";
import { emrApi } from "../../api";
import { useVisitTypes, useLocations } from "../../queries";
import type { Visit } from "../../types";
import { ApiError } from "@/lib/api/types";
import { formatDateTime } from "@/lib/format";
import { useToast } from "@/components/ui/toast";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Spinner, PageLoader } from "@/components/ui/spinner";
import { EmptyState, ErrorState } from "@/components/common/states";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
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

export function VisitsTab({ patientId }: { patientId: number }) {
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["visits", { patient: patientId }],
    queryFn: () => emrApi.listVisits({ patient: patientId, ordering: "-started_at" }),
  });

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <StartVisitDialog patientId={patientId} />
      </div>

      <Card>
        {isLoading ? (
          <PageLoader />
        ) : isError ? (
          <ErrorState error={error} onRetry={refetch} />
        ) : data && data.results.length > 0 ? (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Started</TableHead>
                <TableHead>Stopped</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.results.map((visit) => (
                <VisitRow key={visit.id} visit={visit} patientId={patientId} />
              ))}
            </TableBody>
          </Table>
        ) : (
          <EmptyState
            icon={<Stethoscope className="size-8" />}
            title="No visits recorded"
            description="Start a visit to begin documenting care."
          />
        )}
      </Card>
    </div>
  );
}

function VisitRow({ visit, patientId }: { visit: Visit; patientId: number }) {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const stop = useMutation({
    mutationFn: () => emrApi.stopVisit(visit.id, new Date().toISOString()),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["visits", { patient: patientId }] });
      toast({ title: "Visit closed", variant: "success" });
    },
    onError: (err) =>
      toast({
        title: "Could not close visit",
        description: err instanceof ApiError ? err.toUserMessage() : undefined,
        variant: "error",
      }),
  });

  const active = !visit.stopped_at;

  return (
    <TableRow>
      <TableCell>{formatDateTime(visit.started_at)}</TableCell>
      <TableCell>{visit.stopped_at ? formatDateTime(visit.stopped_at) : "—"}</TableCell>
      <TableCell>
        {active ? (
          <div className="flex items-center gap-3">
            <Badge variant="success">Active</Badge>
            <Button
              size="sm"
              variant="outline"
              onClick={() => stop.mutate()}
              disabled={stop.isPending}
            >
              {stop.isPending ? <Spinner className="size-3" /> : <CheckCircle2 className="size-3" />}
              End visit
            </Button>
          </div>
        ) : (
          <Badge variant="secondary">Closed</Badge>
        )}
      </TableCell>
    </TableRow>
  );
}

function StartVisitDialog({ patientId }: { patientId: number }) {
  const [open, setOpen] = React.useState(false);
  const [visitType, setVisitType] = React.useState<string>("");
  const [location, setLocation] = React.useState<string>("");
  const [formError, setFormError] = React.useState<string | null>(null);

  const queryClient = useQueryClient();
  const { toast } = useToast();
  const visitTypes = useVisitTypes();
  const locations = useLocations();

  const create = useMutation({
    mutationFn: () =>
      emrApi.createVisit({
        patient: patientId,
        visit_type: Number(visitType),
        location: location ? Number(location) : null,
        started_at: new Date().toISOString(),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["visits", { patient: patientId }] });
      toast({ title: "Visit started", variant: "success" });
      setOpen(false);
      setVisitType("");
      setLocation("");
    },
    onError: (err) =>
      setFormError(err instanceof ApiError ? err.toUserMessage() : "Could not start visit."),
  });

  function submit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    if (!visitType) {
      setFormError("Select a visit type.");
      return;
    }
    create.mutate();
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <CalendarPlus className="size-4" /> Start visit
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Start a visit</DialogTitle>
        </DialogHeader>
        <form onSubmit={submit} className="space-y-4">
          <div className="space-y-2">
            <Label>Visit type *</Label>
            <Select value={visitType} onValueChange={setVisitType}>
              <SelectTrigger>
                <SelectValue placeholder="Select type" />
              </SelectTrigger>
              <SelectContent>
                {visitTypes.data?.map((t) => (
                  <SelectItem key={t.id} value={String(t.id)}>
                    {t.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>Location</Label>
            <Select value={location} onValueChange={setLocation}>
              <SelectTrigger>
                <SelectValue placeholder="Select location (optional)" />
              </SelectTrigger>
              <SelectContent>
                {locations.data?.map((l) => (
                  <SelectItem key={l.id} value={String(l.id)}>
                    {l.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          {formError && (
            <p className="whitespace-pre-line rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {formError}
            </p>
          )}
          <DialogFooter>
            <Button type="submit" disabled={create.isPending}>
              {create.isPending ? <Spinner className="size-4" /> : "Start visit"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
