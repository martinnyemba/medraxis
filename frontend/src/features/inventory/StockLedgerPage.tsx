import * as React from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Landmark } from "lucide-react";
import { inventoryApi, type TxnType } from "./api";
import { formatDateTime } from "@/lib/format";
import { PageHeader } from "@/components/common/PageHeader";
import { Pagination } from "@/components/common/Pagination";
import { EmptyState, ErrorState } from "@/components/common/states";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { PageLoader } from "@/components/ui/spinner";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

const TXN_TYPES: { key: string; label: string; query?: TxnType }[] = [
  { key: "ALL", label: "All movements" },
  { key: "RECEIPT", label: "Receipts", query: "RECEIPT" },
  { key: "SALE", label: "Sales", query: "SALE" },
  { key: "DISPENSE", label: "Dispenses", query: "DISPENSE" },
  { key: "ADJUSTMENT", label: "Adjustments", query: "ADJUSTMENT" },
  { key: "RETURN", label: "Returns", query: "RETURN" },
];

const OUTFLOW = new Set<TxnType>(["SALE", "DISPENSE", "TRANSFER_OUT", "WASTAGE"]);

export function StockLedgerPage() {
  const [page, setPage] = React.useState(1);
  const [typeKey, setTypeKey] = React.useState("ALL");
  const active = TXN_TYPES.find((t) => t.key === typeKey) ?? TXN_TYPES[0];

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["transactions", { page, typeKey }],
    queryFn: () =>
      inventoryApi.listTransactions({
        page,
        ...(active.query ? { transaction_type: active.query } : {}),
      }),
    placeholderData: (prev) => prev,
  });

  return (
    <div>
      <Button variant="ghost" size="sm" asChild className="mb-2 -ml-2">
        <Link to="/inventory/products">
          <ArrowLeft className="size-4" /> Back to inventory
        </Link>
      </Button>
      <PageHeader title="Stock ledger" description="Append-only record of every stock movement." />

      <div className="mb-4">
        <Select
          value={typeKey}
          onValueChange={(v) => {
            setTypeKey(v);
            setPage(1);
          }}
        >
          <SelectTrigger className="w-56">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {TXN_TYPES.map((t) => (
              <SelectItem key={t.key} value={t.key}>
                {t.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <Card>
        {isLoading ? (
          <PageLoader />
        ) : isError ? (
          <ErrorState error={error} onRetry={refetch} />
        ) : data && data.results.length > 0 ? (
          <>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead className="text-right">Qty</TableHead>
                  <TableHead>Reference</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.results.map((t) => {
                  const out = OUTFLOW.has(t.transaction_type);
                  return (
                    <TableRow key={t.id}>
                      <TableCell>{formatDateTime(t.created_at)}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{t.transaction_type.replace(/_/g, " ")}</Badge>
                      </TableCell>
                      <TableCell className={`text-right ${out ? "text-destructive" : "text-success"}`}>
                        {out ? "-" : "+"}
                        {t.quantity}
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground">
                        {[t.reference_type, t.reference_id].filter(Boolean).join(" #") || "—"}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
            <div className="px-4">
              <Pagination
                page={data.current_page}
                totalPages={data.total_pages}
                count={data.count}
                onPageChange={setPage}
              />
            </div>
          </>
        ) : (
          <EmptyState icon={<Landmark className="size-8" />} title="No stock movements" />
        )}
      </Card>
    </div>
  );
}
