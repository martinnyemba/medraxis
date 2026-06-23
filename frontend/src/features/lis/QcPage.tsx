import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Activity, Plus } from "lucide-react";
import { lisApi } from "./api";
import type { QCMaterial, QCResult } from "./types";
import { ApiError } from "@/lib/api/types";
import { formatDateTime } from "@/lib/format";
import { useToast } from "@/components/ui/toast";
import { PageHeader } from "@/components/common/PageHeader";
import { EmptyState, ErrorState } from "@/components/common/states";
import { LisTabs } from "./components/LisTabs";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PageLoader, Spinner } from "@/components/ui/spinner";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

export function QcPage() {
  const materials = useQuery({
    queryKey: ["qc-materials"],
    queryFn: () => lisApi.listQcMaterials({ page_size: 100, retired: false }),
  });
  const [selected, setSelected] = React.useState<number | null>(null);

  const list = materials.data?.results ?? [];
  const active = selected ?? list[0]?.id ?? null;

  return (
    <div>
      <PageHeader
        title="Quality control"
        description="Levey-Jennings tracking with Westgard rule evaluation for instrument control runs."
      />
      <LisTabs />

      {materials.isLoading ? (
        <PageLoader />
      ) : materials.isError ? (
        <ErrorState error={materials.error} onRetry={materials.refetch} />
      ) : list.length === 0 ? (
        <Card>
          <EmptyState
            icon={<Activity className="size-8" />}
            title="No QC materials"
            description="Add a control material (lot, target mean & SD) to start tracking QC."
          />
        </Card>
      ) : (
        <div className="grid gap-4 lg:grid-cols-[260px_1fr]">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Control materials</CardTitle>
            </CardHeader>
            <CardContent className="space-y-1">
              {list.map((mat) => (
                <button
                  key={mat.id}
                  onClick={() => setSelected(mat.id)}
                  className={
                    "w-full rounded-md px-3 py-2 text-left text-sm transition-colors " +
                    (active === mat.id ? "bg-accent" : "hover:bg-accent/50")
                  }
                >
                  <span className="font-medium">{mat.name}</span>
                  <span className="block text-xs text-muted-foreground">
                    Lot {mat.lot_number} · μ {mat.target_mean} ± {mat.target_sd}
                  </span>
                </button>
              ))}
            </CardContent>
          </Card>

          {active != null && (
            <QcMaterialDetail material={list.find((m) => m.id === active)!} />
          )}
        </div>
      )}
    </div>
  );
}

function QcMaterialDetail({ material }: { material: QCMaterial }) {
  const results = useQuery({
    queryKey: ["qc-results", { material: material.id }],
    queryFn: () =>
      lisApi.listQcResults({ qc_material: material.id, ordering: "run_at", page_size: 60 }),
  });

  const points = results.data?.results ?? [];

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="text-base">
          {material.name}{" "}
          <span className="text-sm font-normal text-muted-foreground">
            (target {material.target_mean} ± {material.target_sd} {material.units})
          </span>
        </CardTitle>
        <RecordResultDialog material={material} />
      </CardHeader>
      <CardContent className="space-y-4">
        <LeveyJennings material={material} points={points} />
        {results.isLoading ? (
          <p className="text-sm text-muted-foreground">Loading runs…</p>
        ) : points.length === 0 ? (
          <p className="text-sm text-muted-foreground">No control runs recorded yet.</p>
        ) : (
          <div className="space-y-1">
            {[...points].reverse().map((r) => (
              <div
                key={r.id}
                className="flex items-center justify-between border-b py-1.5 text-sm last:border-0"
              >
                <span className="text-muted-foreground">{formatDateTime(r.run_at)}</span>
                <span className="font-mono">{r.measured_value}</span>
                <span className="font-mono text-xs text-muted-foreground">
                  z={r.z_score?.toFixed(2) ?? "—"}
                </span>
                {r.accepted ? (
                  <Badge variant="success">In control</Badge>
                ) : (
                  <Badge variant="destructive">{r.westgard_rule || "Violation"}</Badge>
                )}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

/** Minimal Levey-Jennings chart: ±1/2/3 SD bands and the run series. */
function LeveyJennings({ material, points }: { material: QCMaterial; points: QCResult[] }) {
  const W = 640;
  const H = 200;
  const pad = 28;
  const mean = material.target_mean;
  const sd = material.target_sd || 1;
  const yFor = (v: number) => {
    // Clamp to ±4 SD around the mean for a stable vertical scale.
    const z = Math.max(-4, Math.min(4, (v - mean) / sd));
    return H / 2 - (z / 4) * (H / 2 - pad);
  };
  const xFor = (i: number) =>
    pad + (points.length <= 1 ? 0 : (i / (points.length - 1)) * (W - 2 * pad));

  const bands = [
    { z: 0, label: "x̄", color: "#16a34a" },
    { z: 1, color: "#eab308" },
    { z: 2, color: "#f97316" },
    { z: 3, color: "#dc2626" },
  ];

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full rounded-md border bg-card">
      {bands.map((b) => (
        <g key={b.z}>
          {[b.z, -b.z].filter((_, i) => b.z !== 0 || i === 0).map((z) => (
            <line
              key={z}
              x1={pad}
              x2={W - pad}
              y1={yFor(mean + z * sd)}
              y2={yFor(mean + z * sd)}
              stroke={b.color}
              strokeWidth={b.z === 0 ? 1.5 : 1}
              strokeDasharray={b.z === 0 ? "" : "4 3"}
              opacity={0.6}
            />
          ))}
          <text x={W - pad + 2} y={yFor(mean + b.z * sd) + 3} fontSize="9" fill={b.color}>
            {b.label ?? `+${b.z}s`}
          </text>
          {b.z !== 0 && (
            <text x={W - pad + 2} y={yFor(mean - b.z * sd) + 3} fontSize="9" fill={b.color}>
              -{b.z}s
            </text>
          )}
        </g>
      ))}
      {points.length > 1 && (
        <polyline
          fill="none"
          stroke="#2563eb"
          strokeWidth={1.5}
          points={points.map((p, i) => `${xFor(i)},${yFor(p.measured_value)}`).join(" ")}
        />
      )}
      {points.map((p, i) => (
        <circle
          key={p.id}
          cx={xFor(i)}
          cy={yFor(p.measured_value)}
          r={3}
          fill={p.accepted ? "#2563eb" : "#dc2626"}
        />
      ))}
    </svg>
  );
}

function RecordResultDialog({ material }: { material: QCMaterial }) {
  const [open, setOpen] = React.useState(false);
  const [value, setValue] = React.useState("");
  const [formError, setFormError] = React.useState<string | null>(null);
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const create = useMutation({
    mutationFn: () =>
      lisApi.recordQcResult({
        qc_material: material.id,
        analyzer: material.analyzer,
        measured_value: Number(value),
        run_at: new Date().toISOString(),
      }),
    onSuccess: (r) => {
      queryClient.invalidateQueries({ queryKey: ["qc-results", { material: material.id }] });
      toast({
        title: r.accepted ? "QC in control" : `QC violation: ${r.westgard_rule}`,
        variant: r.accepted ? "success" : "error",
      });
      setOpen(false);
      setValue("");
    },
    onError: (err) =>
      setFormError(err instanceof ApiError ? err.toUserMessage() : "Could not record result."),
  });

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm">
          <Plus className="size-3" /> Record run
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Record QC run — {material.name}</DialogTitle>
        </DialogHeader>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            setFormError(null);
            if (value === "" || Number.isNaN(Number(value)))
              return setFormError("A measured value is required.");
            create.mutate();
          }}
          className="space-y-4"
        >
          <div className="space-y-2">
            <Label htmlFor="value">Measured value</Label>
            <Input
              id="value"
              type="number"
              step="any"
              value={value}
              onChange={(e) => setValue(e.target.value)}
              autoFocus
            />
            <p className="text-xs text-muted-foreground">
              Z-score and Westgard evaluation are computed automatically on save.
            </p>
          </div>
          {formError && (
            <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {formError}
            </p>
          )}
          <DialogFooter>
            <Button type="submit" disabled={create.isPending}>
              {create.isPending ? <Spinner className="size-4" /> : "Record"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
