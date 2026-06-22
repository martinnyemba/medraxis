import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ClipboardPlus, FilePlus2, NotebookPen } from "lucide-react";
import { emrApi } from "../../api";
import { useEncounterTypes, useLocations } from "../../queries";
import type { Encounter, Patient } from "../../types";
import { ApiError } from "@/lib/api/types";
import { formatDateTime } from "@/lib/format";
import { useToast } from "@/components/ui/toast";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Spinner, PageLoader } from "@/components/ui/spinner";
import { EmptyState, ErrorState } from "@/components/common/states";
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
import { AddObsDialog } from "./AddObsDialog";

export function EncountersTab({ patient }: { patient: Patient }) {
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["encounters", { patient: patient.id }],
    queryFn: () =>
      emrApi.listEncounters({ patient: patient.id, ordering: "-encounter_datetime" }),
  });

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <CreateEncounterDialog patientId={patient.id} />
      </div>

      {isLoading ? (
        <PageLoader />
      ) : isError ? (
        <ErrorState error={error} onRetry={refetch} />
      ) : data && data.results.length > 0 ? (
        <div className="space-y-4">
          {data.results.map((enc) => (
            <EncounterCard key={enc.id} encounter={enc} patient={patient} />
          ))}
        </div>
      ) : (
        <Card>
          <EmptyState
            icon={<NotebookPen className="size-8" />}
            title="No encounters yet"
            description="Create an encounter to record observations such as vitals and diagnoses."
          />
        </Card>
      )}
    </div>
  );
}

function EncounterCard({ encounter, patient }: { encounter: Encounter; patient: Patient }) {
  const encounterTypes = useEncounterTypes();
  const typeName =
    encounterTypes.data?.find((t) => t.id === encounter.encounter_type)?.name ??
    `Type #${encounter.encounter_type}`;

  const { data: obs, isLoading } = useQuery({
    queryKey: ["observations", { encounter: encounter.id }],
    queryFn: () => emrApi.listObs({ encounter: encounter.id, ordering: "-obs_datetime" }),
  });

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <div>
          <CardTitle className="text-base">{typeName}</CardTitle>
          <p className="text-sm text-muted-foreground">
            {formatDateTime(encounter.encounter_datetime)}
          </p>
        </div>
        <AddObsDialog patient={patient} encounter={encounter} />
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Loading observations…</p>
        ) : obs && obs.results.length > 0 ? (
          <ul className="divide-y">
            {obs.results.map((o) => (
              <li key={o.id} className="flex items-center justify-between py-2 text-sm">
                <span className="text-muted-foreground">Concept #{o.concept}</span>
                <span className="font-medium">{o.display_value || "—"}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="py-2 text-sm text-muted-foreground">
            No observations recorded for this encounter.
          </p>
        )}
      </CardContent>
    </Card>
  );
}

function CreateEncounterDialog({ patientId }: { patientId: number }) {
  const [open, setOpen] = React.useState(false);
  const [encounterType, setEncounterType] = React.useState("");
  const [location, setLocation] = React.useState("");
  const [formError, setFormError] = React.useState<string | null>(null);

  const queryClient = useQueryClient();
  const { toast } = useToast();
  const encounterTypes = useEncounterTypes();
  const locations = useLocations();

  const create = useMutation({
    mutationFn: () =>
      emrApi.createEncounter({
        patient: patientId,
        encounter_type: Number(encounterType),
        location: location ? Number(location) : null,
        encounter_datetime: new Date().toISOString(),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["encounters", { patient: patientId }] });
      toast({ title: "Encounter created", variant: "success" });
      setOpen(false);
      setEncounterType("");
      setLocation("");
    },
    onError: (err) =>
      setFormError(err instanceof ApiError ? err.toUserMessage() : "Could not create encounter."),
  });

  function submit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    if (!encounterType) {
      setFormError("Select an encounter type.");
      return;
    }
    create.mutate();
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <FilePlus2 className="size-4" /> New encounter
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>New encounter</DialogTitle>
        </DialogHeader>
        <form onSubmit={submit} className="space-y-4">
          <div className="space-y-2">
            <Label>Encounter type *</Label>
            <Select value={encounterType} onValueChange={setEncounterType}>
              <SelectTrigger>
                <SelectValue placeholder="Select type" />
              </SelectTrigger>
              <SelectContent>
                {encounterTypes.data?.map((t) => (
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
              {create.isPending ? <Spinner className="size-4" /> : <><ClipboardPlus className="size-4" /> Create</>}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
