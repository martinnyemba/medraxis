import * as React from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { CheckCheck, ClipboardCheck, Send } from "lucide-react";
import { lisApi } from "../api";
import { useConcept } from "../queries";
import type { LabResult } from "../types";
import { ApiError } from "@/lib/api/types";
import { useToast } from "@/components/ui/toast";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { StatusBadge } from "@/components/common/StatusBadge";
import { TableCell, TableRow } from "@/components/ui/table";

const FLAG_LABELS: Record<string, { label: string; variant: "success" | "warning" | "destructive" }> = {
  N: { label: "Normal", variant: "success" },
  H: { label: "High", variant: "warning" },
  L: { label: "Low", variant: "warning" },
  HH: { label: "Critical high", variant: "destructive" },
  LL: { label: "Critical low", variant: "destructive" },
  A: { label: "Abnormal", variant: "warning" },
};

export function ResultRow({ result, orderId }: { result: LabResult; orderId: number }) {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const concept = useConcept(result.analyte);
  const isNumeric = (concept.data?.datatype_name ?? "").toLowerCase().includes("numeric");

  const [numericValue, setNumericValue] = React.useState(
    result.value_numeric != null ? String(result.value_numeric) : "",
  );
  const [textValue, setTextValue] = React.useState(result.value_text ?? "");

  const editable = result.status === "PENDING";

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ["lab-results", { order: orderId }] });
    queryClient.invalidateQueries({ queryKey: ["lab-order", orderId] });
  }

  function onError(err: unknown) {
    toast({
      title: "Action failed",
      description: err instanceof ApiError ? err.toUserMessage() : undefined,
      variant: "error",
    });
  }

  // PENDING → save the value then mark ENTERED (the backend enter action
  // requires a value to already be present).
  const enter = useMutation({
    mutationFn: async () => {
      await lisApi.updateResult(result.id, {
        value_numeric: isNumeric && numericValue !== "" ? Number(numericValue) : null,
        value_text: isNumeric ? "" : textValue,
      });
      return lisApi.enterResult(result.id);
    },
    onSuccess: () => {
      toast({ title: "Result entered", variant: "success" });
      invalidate();
    },
    onError,
  });

  const verify = useMutation({
    mutationFn: () => lisApi.verifyResult(result.id),
    onSuccess: () => {
      toast({ title: "Result verified", variant: "success" });
      invalidate();
    },
    onError,
  });

  const release = useMutation({
    mutationFn: () => lisApi.releaseResult(result.id),
    onSuccess: () => {
      toast({ title: "Result released to chart", variant: "success" });
      invalidate();
    },
    onError,
  });

  const busy = enter.isPending || verify.isPending || release.isPending;
  const flag = result.flag ? FLAG_LABELS[result.flag] : null;

  return (
    <TableRow>
      <TableCell className="font-medium">
        {concept.data?.name ?? `Analyte #${result.analyte}`}
      </TableCell>
      <TableCell>
        {editable ? (
          isNumeric ? (
            <Input
              type="number"
              step="any"
              className="h-8 w-32"
              value={numericValue}
              onChange={(e) => setNumericValue(e.target.value)}
              placeholder="Value"
            />
          ) : (
            <Input
              className="h-8 w-44"
              value={textValue}
              onChange={(e) => setTextValue(e.target.value)}
              placeholder="Result"
            />
          )
        ) : (
          <span className="font-medium">
            {result.value_numeric ?? (result.value_text || "—")}
          </span>
        )}
      </TableCell>
      <TableCell className="text-muted-foreground">
        {result.units || concept.data?.units || "—"}
      </TableCell>
      <TableCell className="text-xs text-muted-foreground">
        {result.reference_range ||
          (concept.data?.low_normal != null || concept.data?.hi_normal != null
            ? `${concept.data?.low_normal ?? "—"}–${concept.data?.hi_normal ?? "—"}`
            : "—")}
      </TableCell>
      <TableCell>{flag ? <Badge variant={flag.variant}>{flag.label}</Badge> : "—"}</TableCell>
      <TableCell>
        <StatusBadge status={result.status} />
      </TableCell>
      <TableCell className="text-right">
        {result.status === "PENDING" && (
          <Button size="sm" onClick={() => enter.mutate()} disabled={busy}>
            {enter.isPending ? <Spinner className="size-3" /> : <ClipboardCheck className="size-3" />}
            Enter
          </Button>
        )}
        {result.status === "ENTERED" && (
          <Button size="sm" variant="outline" onClick={() => verify.mutate()} disabled={busy}>
            {verify.isPending ? <Spinner className="size-3" /> : <CheckCheck className="size-3" />}
            Verify
          </Button>
        )}
        {result.status === "VERIFIED" && (
          <Button size="sm" onClick={() => release.mutate()} disabled={busy}>
            {release.isPending ? <Spinner className="size-3" /> : <Send className="size-3" />}
            Release
          </Button>
        )}
        {result.status === "RELEASED" && (
          <span className="text-xs text-muted-foreground">On chart</span>
        )}
      </TableCell>
    </TableRow>
  );
}
