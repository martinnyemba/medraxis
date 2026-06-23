import type { ReactNode } from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, FileText, ListChecks } from "lucide-react";
import { lisApi } from "./api";
import { useLabSections, useLabTests } from "./queries";
import { ApiError } from "@/lib/api/types";
import { openAuthenticatedFile } from "@/lib/api/client";
import { formatDateTime } from "@/lib/format";
import { useToast } from "@/components/ui/toast";
import { PageHeader } from "@/components/common/PageHeader";
import { StatusBadge } from "@/components/common/StatusBadge";
import { ErrorState, EmptyState } from "@/components/common/states";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PageLoader, Spinner } from "@/components/ui/spinner";
import {
  Table,
  TableBody,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { SpecimenPanel } from "./components/SpecimenPanel";
import { ResultRow } from "./components/ResultRow";
import { ReportDeliveryPanel } from "./components/ReportDeliveryPanel";
import { MicrobiologyPanel } from "./components/MicrobiologyPanel";

export function LabOrderDetailPage() {
  const { orderId } = useParams<{ orderId: string }>();
  const id = Number(orderId);
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const tests = useLabTests();
  const sections = useLabSections();

  const order = useQuery({
    queryKey: ["lab-order", id],
    queryFn: () => lisApi.getOrder(id),
    enabled: Number.isFinite(id),
  });

  const results = useQuery({
    queryKey: ["lab-results", { order: id }],
    queryFn: () => lisApi.listResults({ test_order: id, ordering: "id" }),
    enabled: Number.isFinite(id),
  });

  const buildWorksheet = useMutation({
    mutationFn: () => lisApi.buildWorksheet(id),
    onSuccess: () => {
      toast({ title: "Worksheet generated", variant: "success" });
      queryClient.invalidateQueries({ queryKey: ["lab-results", { order: id }] });
    },
    onError: (err) =>
      toast({
        title: "Could not generate worksheet",
        description: err instanceof ApiError ? err.toUserMessage() : undefined,
        variant: "error",
      }),
  });

  if (order.isLoading) return <PageLoader />;
  if (order.isError || !order.data) return <ErrorState error={order.error} onRetry={order.refetch} />;

  const o = order.data;
  const test = tests.data?.byId.get(o.lab_test);
  const resultRows = results.data?.results ?? [];
  const sectionName =
    sections.data?.find((s) => s.id === test?.section)?.name?.toLowerCase() ?? "";
  const isMicrobiology = sectionName.includes("micro");

  return (
    <div className="space-y-6">
      <div>
        <Button variant="ghost" size="sm" asChild className="mb-2 -ml-2">
          <Link to="/lis/worklist">
            <ArrowLeft className="size-4" /> Back to worklist
          </Link>
        </Button>
        <PageHeader
          title={test?.name ?? `Lab order ${o.order_number}`}
          description={`Order ${o.order_number}`}
          actions={
            <Button
              variant="outline"
              onClick={() => openAuthenticatedFile(lisApi.reportUrl(o.id)).catch(() => {})}
            >
              <FileText className="size-4" /> Report PDF
            </Button>
          }
        />
      </div>

      <Card>
        <CardContent className="grid gap-4 pt-6 sm:grid-cols-2 lg:grid-cols-4">
          <Field label="Status">
            <StatusBadge status={o.fulfiller_status || "PENDING"} />
          </Field>
          <Field label="Urgency">{o.urgency || "Routine"}</Field>
          <Field label="Ordered">{formatDateTime(o.date_activated)}</Field>
          <Field label="Test code">{test?.test_code ?? "—"}</Field>
          {o.clinical_history && (
            <div className="sm:col-span-2 lg:col-span-4">
              <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Clinical history
              </p>
              <p className="text-sm">{o.clinical_history}</p>
            </div>
          )}
        </CardContent>
      </Card>

      <SpecimenPanel order={o} />

      <Card>
        <CardHeader className="flex-row items-center justify-between space-y-0">
          <CardTitle className="flex items-center gap-2 text-base">
            <ListChecks className="size-4 text-primary" /> Result worksheet
          </CardTitle>
          {resultRows.length === 0 && (
            <Button size="sm" onClick={() => buildWorksheet.mutate()} disabled={buildWorksheet.isPending}>
              {buildWorksheet.isPending ? <Spinner className="size-3" /> : <ListChecks className="size-3" />}
              Generate worksheet
            </Button>
          )}
        </CardHeader>
        <CardContent>
          {results.isLoading ? (
            <p className="text-sm text-muted-foreground">Loading results…</p>
          ) : resultRows.length === 0 ? (
            <EmptyState
              icon={<ListChecks className="size-8" />}
              title="No worksheet yet"
              description="Generate the worksheet to create result rows for this order's analytes."
            />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Analyte</TableHead>
                  <TableHead>Value</TableHead>
                  <TableHead>Units</TableHead>
                  <TableHead>Reference</TableHead>
                  <TableHead>Flag</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {resultRows.map((r) => (
                  <ResultRow key={r.id} result={r} orderId={id} />
                ))}
              </TableBody>
            </Table>
          )}
          <p className="mt-3 text-xs text-muted-foreground">
            Workflow: enter → verify (two-person rule) → release. Released results post to the
            patient chart as observations.
          </p>
        </CardContent>
      </Card>

      {isMicrobiology && <MicrobiologyPanel orderId={id} />}

      <ReportDeliveryPanel orderId={id} />
    </div>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="space-y-1">
      <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</p>
      <div className="text-sm font-medium">{children}</div>
    </div>
  );
}
