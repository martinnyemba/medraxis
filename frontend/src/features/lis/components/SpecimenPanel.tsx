import type { ReactNode } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { TestTube, Printer, PackageCheck, Hand } from "lucide-react";
import { lisApi } from "../api";
import type { TestOrder } from "../types";
import { ApiError } from "@/lib/api/types";
import { openAuthenticatedFile } from "@/lib/api/client";
import { formatDateTime } from "@/lib/format";
import { useToast } from "@/components/ui/toast";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { StatusBadge } from "@/components/common/StatusBadge";

export function SpecimenPanel({ order }: { order: TestOrder }) {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const { data, isLoading } = useQuery({
    queryKey: ["specimens", { order: order.id }],
    queryFn: () => lisApi.listSpecimens({ orders: order.id }),
  });

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ["specimens", { order: order.id }] });
  }

  function onError(err: unknown) {
    toast({
      title: "Specimen action failed",
      description: err instanceof ApiError ? err.toUserMessage() : undefined,
      variant: "error",
    });
  }

  const accession = useMutation({
    mutationFn: () => lisApi.createSpecimen({ patient: order.patient, orders: [order.id] }),
    onSuccess: (s) => {
      toast({ title: `Specimen ${s.accession_number} accessioned`, variant: "success" });
      invalidate();
    },
    onError,
  });

  const specimens = data?.results ?? [];

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-2 text-base">
          <TestTube className="size-4 text-primary" /> Specimens
        </CardTitle>
        <Button size="sm" onClick={() => accession.mutate()} disabled={accession.isPending}>
          {accession.isPending ? <Spinner className="size-3" /> : <TestTube className="size-3" />}
          Accession specimen
        </Button>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Loading specimens…</p>
        ) : specimens.length === 0 ? (
          <p className="py-2 text-sm text-muted-foreground">
            No specimen accessioned yet. Accession one to collect and receive the sample.
          </p>
        ) : (
          <ul className="space-y-3">
            {specimens.map((s) => (
              <li
                key={s.id}
                className="flex flex-wrap items-center justify-between gap-3 rounded-md border p-3"
              >
                <div className="space-y-0.5">
                  <p className="font-mono text-sm font-medium">{s.accession_number}</p>
                  <p className="text-xs text-muted-foreground">
                    {s.collected_at ? `Collected ${formatDateTime(s.collected_at)}` : "Not collected"}
                    {s.received_at ? ` · Received ${formatDateTime(s.received_at)}` : ""}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <StatusBadge status={s.status} />
                  {s.status === "ORDERED" && (
                    <SpecimenAction
                      label="Collect"
                      icon={<Hand className="size-3" />}
                      mutationFn={() => lisApi.collectSpecimen(s.id)}
                      onDone={invalidate}
                      onError={onError}
                    />
                  )}
                  {s.status === "COLLECTED" && (
                    <SpecimenAction
                      label="Receive"
                      icon={<PackageCheck className="size-3" />}
                      mutationFn={() => lisApi.receiveSpecimen(s.id)}
                      onDone={invalidate}
                      onError={onError}
                    />
                  )}
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => openAuthenticatedFile(lisApi.specimenLabelUrl(s.id)).catch(onError)}
                  >
                    <Printer className="size-3" /> Label
                  </Button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

function SpecimenAction({
  label,
  icon,
  mutationFn,
  onDone,
  onError,
}: {
  label: string;
  icon: ReactNode;
  mutationFn: () => Promise<unknown>;
  onDone: () => void;
  onError: (err: unknown) => void;
}) {
  const m = useMutation({ mutationFn, onSuccess: onDone, onError });
  return (
    <Button size="sm" variant="outline" onClick={() => m.mutate()} disabled={m.isPending}>
      {m.isPending ? <Spinner className="size-3" /> : icon}
      {label}
    </Button>
  );
}
