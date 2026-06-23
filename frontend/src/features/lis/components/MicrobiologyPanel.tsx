import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bug, Plus, Trash2 } from "lucide-react";
import { lisApi } from "../api";
import type { Interpretation, MicroGrowth, SensitivityResult } from "../types";
import { ApiError } from "@/lib/api/types";
import { useToast } from "@/components/ui/toast";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Spinner } from "@/components/ui/spinner";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

const GROWTH: { value: MicroGrowth; label: string }[] = [
  { value: "NO_GROWTH", label: "No growth" },
  { value: "GROWTH", label: "Growth" },
  { value: "MIXED", label: "Mixed flora" },
  { value: "CONTAMINATED", label: "Contaminated" },
];

const SIR: Record<Interpretation, { label: string; variant: "success" | "warning" | "destructive" }> = {
  S: { label: "S", variant: "success" },
  I: { label: "I", variant: "warning" },
  R: { label: "R", variant: "destructive" },
};

/** Culture & sensitivity entry/display for a microbiology order. */
export function MicrobiologyPanel({ orderId }: { orderId: number }) {
  const results = useQuery({
    queryKey: ["lab-microbiology", { order: orderId }],
    queryFn: () => lisApi.listMicrobiology({ test_order: orderId }),
  });
  const organisms = useQuery({
    queryKey: ["lab-organisms"],
    queryFn: () => lisApi.listOrganisms({ page_size: 200, retired: false }),
    staleTime: 5 * 60_000,
  });
  const antibiotics = useQuery({
    queryKey: ["lab-antibiotics"],
    queryFn: () => lisApi.listAntibiotics({ page_size: 200, retired: false }),
    staleTime: 5 * 60_000,
  });

  const organismById = new Map((organisms.data?.results ?? []).map((o) => [o.id, o]));
  const antibioticById = new Map((antibiotics.data?.results ?? []).map((a) => [a.id, a]));
  const rows = results.data?.results ?? [];

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-2 text-base">
          <Bug className="size-4 text-primary" /> Microbiology — culture &amp; sensitivity
        </CardTitle>
        <CultureDialog
          orderId={orderId}
          organisms={organisms.data?.results ?? []}
          antibiotics={antibiotics.data?.results ?? []}
        />
      </CardHeader>
      <CardContent>
        {results.isLoading ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : rows.length === 0 ? (
          <p className="py-2 text-sm text-muted-foreground">
            No culture recorded yet. Record growth and the antibiogram once plated.
          </p>
        ) : (
          <ul className="space-y-4">
            {rows.map((r) => (
              <li key={r.id} className="rounded-md border p-3">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant="outline">
                    {GROWTH.find((g) => g.value === r.growth)?.label ?? r.growth}
                  </Badge>
                  {r.organism != null && (
                    <span className="text-sm font-medium">
                      {organismById.get(r.organism)?.name ?? `Organism #${r.organism}`}
                    </span>
                  )}
                  {r.colony_count && (
                    <span className="text-xs text-muted-foreground">{r.colony_count}</span>
                  )}
                  <span className="ml-auto text-xs text-muted-foreground">{r.status}</span>
                </div>
                {r.sensitivities.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {r.sensitivities.map((s, i) => {
                      const meta = SIR[s.interpretation];
                      return (
                        <Badge key={i} variant={meta.variant} className="font-mono">
                          {antibioticById.get(s.antibiotic)?.abbreviation ||
                            antibioticById.get(s.antibiotic)?.name ||
                            `#${s.antibiotic}`}
                          : {meta.label}
                          {s.mic ? ` (${s.mic})` : ""}
                        </Badge>
                      );
                    })}
                  </div>
                )}
                {r.comments && (
                  <p className="mt-2 text-xs text-muted-foreground">{r.comments}</p>
                )}
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

function CultureDialog({
  orderId,
  organisms,
  antibiotics,
}: {
  orderId: number;
  organisms: { id: number; name: string }[];
  antibiotics: { id: number; name: string }[];
}) {
  const [open, setOpen] = React.useState(false);
  const [growth, setGrowth] = React.useState<MicroGrowth>("NO_GROWTH");
  const [organism, setOrganism] = React.useState<string>("");
  const [colonyCount, setColonyCount] = React.useState("");
  const [comments, setComments] = React.useState("");
  const [sens, setSens] = React.useState<SensitivityResult[]>([]);
  const [formError, setFormError] = React.useState<string | null>(null);
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const hasGrowth = growth === "GROWTH" || growth === "MIXED";

  function reset() {
    setGrowth("NO_GROWTH");
    setOrganism("");
    setColonyCount("");
    setComments("");
    setSens([]);
  }

  const create = useMutation({
    mutationFn: () =>
      lisApi.createMicrobiology({
        test_order: orderId,
        growth,
        organism: hasGrowth && organism ? Number(organism) : null,
        colony_count: colonyCount,
        comments,
        status: "FINAL",
        sensitivities: hasGrowth ? sens.filter((s) => s.antibiotic) : [],
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["lab-microbiology", { order: orderId }] });
      toast({ title: "Culture recorded", variant: "success" });
      setOpen(false);
      reset();
    },
    onError: (err) =>
      setFormError(err instanceof ApiError ? err.toUserMessage() : "Could not save culture."),
  });

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm">
          <Plus className="size-3" /> Record culture
        </Button>
      </DialogTrigger>
      <DialogContent className="max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Record culture &amp; sensitivity</DialogTitle>
        </DialogHeader>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            setFormError(null);
            create.mutate();
          }}
          className="space-y-4"
        >
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label>Growth</Label>
              <Select value={growth} onValueChange={(v) => setGrowth(v as MicroGrowth)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {GROWTH.map((g) => (
                    <SelectItem key={g.value} value={g.value}>
                      {g.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {hasGrowth && (
              <div className="space-y-2">
                <Label>Organism</Label>
                <Select value={organism} onValueChange={setOrganism}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select organism" />
                  </SelectTrigger>
                  <SelectContent>
                    {organisms.map((o) => (
                      <SelectItem key={o.id} value={String(o.id)}>
                        {o.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
          </div>

          {hasGrowth && (
            <div className="space-y-2">
              <Label htmlFor="colony">Colony count</Label>
              <Input
                id="colony"
                value={colonyCount}
                onChange={(e) => setColonyCount(e.target.value)}
                placeholder="e.g. >10^5 CFU/mL"
              />
            </div>
          )}

          {hasGrowth && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label>Antibiogram</Label>
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  onClick={() =>
                    setSens((s) => [...s, { antibiotic: 0, interpretation: "S", mic: "" }])
                  }
                >
                  <Plus className="size-3" /> Add antibiotic
                </Button>
              </div>
              {sens.map((row, i) => (
                <div key={i} className="flex items-center gap-2">
                  <Select
                    value={row.antibiotic ? String(row.antibiotic) : ""}
                    onValueChange={(v) =>
                      setSens((s) =>
                        s.map((r, j) => (j === i ? { ...r, antibiotic: Number(v) } : r)),
                      )
                    }
                  >
                    <SelectTrigger className="flex-1">
                      <SelectValue placeholder="Antibiotic" />
                    </SelectTrigger>
                    <SelectContent>
                      {antibiotics.map((a) => (
                        <SelectItem key={a.id} value={String(a.id)}>
                          {a.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Select
                    value={row.interpretation}
                    onValueChange={(v) =>
                      setSens((s) =>
                        s.map((r, j) =>
                          j === i ? { ...r, interpretation: v as Interpretation } : r,
                        ),
                      )
                    }
                  >
                    <SelectTrigger className="w-28">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="S">Sensitive</SelectItem>
                      <SelectItem value="I">Intermediate</SelectItem>
                      <SelectItem value="R">Resistant</SelectItem>
                    </SelectContent>
                  </Select>
                  <Button
                    type="button"
                    size="icon"
                    variant="ghost"
                    onClick={() => setSens((s) => s.filter((_, j) => j !== i))}
                  >
                    <Trash2 className="size-4" />
                  </Button>
                </div>
              ))}
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="comments">Comments</Label>
            <Input
              id="comments"
              value={comments}
              onChange={(e) => setComments(e.target.value)}
            />
          </div>

          {formError && (
            <p className="whitespace-pre-line rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {formError}
            </p>
          )}
          <DialogFooter>
            <Button type="submit" disabled={create.isPending}>
              {create.isPending ? <Spinner className="size-4" /> : "Save culture"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
