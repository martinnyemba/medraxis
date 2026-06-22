import type { ReactNode } from "react";
import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Boxes, Package } from "lucide-react";
import { inventoryApi } from "./api";
import { money, formatDate, formatDateTime } from "@/lib/format";
import { useTenant } from "@/features/tenancy/TenantContext";
import { PageHeader } from "@/components/common/PageHeader";
import { ErrorState } from "@/components/common/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PageLoader } from "@/components/ui/spinner";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ReceiveStockDialog } from "./components/ReceiveStockDialog";

export function ProductDetailPage() {
  const { productId } = useParams<{ productId: string }>();
  const id = Number(productId);
  const { current } = useTenant();
  const currency = current?.currency;

  const product = useQuery({
    queryKey: ["product", id],
    queryFn: () => inventoryApi.getProduct(id),
    enabled: Number.isFinite(id),
  });

  const batches = useQuery({
    queryKey: ["batches", { product: id }],
    queryFn: () => inventoryApi.listBatches({ product: id, ordering: "expiry_date" }),
    enabled: Number.isFinite(id),
  });

  const transactions = useQuery({
    queryKey: ["transactions", { product: id }],
    queryFn: () => inventoryApi.listTransactions({ product: id }),
    enabled: Number.isFinite(id),
  });

  if (product.isLoading) return <PageLoader />;
  if (product.isError || !product.data)
    return <ErrorState error={product.error} onRetry={product.refetch} />;

  const p = product.data;
  const low = p.quantity_on_hand <= Number(p.reorder_level);

  return (
    <div className="space-y-6">
      <div>
        <Button variant="ghost" size="sm" asChild className="mb-2 -ml-2">
          <Link to="/inventory/products">
            <ArrowLeft className="size-4" /> Back to inventory
          </Link>
        </Button>
        <PageHeader
          title={p.name}
          description={p.sku}
          actions={<ReceiveStockDialog product={p} />}
        />
      </div>

      <Card>
        <CardContent className="grid gap-4 pt-6 sm:grid-cols-2 lg:grid-cols-4">
          <Field label="On hand">
            <span className={low ? "text-warning" : ""}>{p.quantity_on_hand}</span>
          </Field>
          <Field label="Reorder level">{p.reorder_level}</Field>
          <Field label="Sale price">{money(p.sale_price, currency)}</Field>
          <Field label="Cost price">{money(p.cost_price, currency)}</Field>
          <Field label="Type">
            {p.is_drug ? <Badge variant="secondary">Drug</Badge> : <Badge variant="outline">Good</Badge>}
            {p.is_controlled && <Badge variant="destructive" className="ml-1">Controlled</Badge>}
          </Field>
          <Field label="Strength">{p.strength || "—"}</Field>
          <Field label="Barcode">{p.barcode || "—"}</Field>
          <Field label="Tracks expiry">{p.track_expiry ? "Yes" : "No"}</Field>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Package className="size-4 text-primary" /> Batches
          </CardTitle>
        </CardHeader>
        <CardContent>
          {batches.isLoading ? (
            <p className="text-sm text-muted-foreground">Loading…</p>
          ) : batches.data && batches.data.results.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Batch</TableHead>
                  <TableHead>Expiry</TableHead>
                  <TableHead className="text-right">On hand</TableHead>
                  <TableHead className="text-right">Cost</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {batches.data.results.map((b) => (
                  <TableRow key={b.id}>
                    <TableCell className="font-mono text-xs">{b.batch_number || "—"}</TableCell>
                    <TableCell>{formatDate(b.expiry_date)}</TableCell>
                    <TableCell className="text-right">{b.quantity_on_hand}</TableCell>
                    <TableCell className="text-right">{money(b.cost_price, currency)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <p className="py-2 text-sm text-muted-foreground">No batches in stock.</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Boxes className="size-4 text-primary" /> Stock movements
          </CardTitle>
        </CardHeader>
        <CardContent>
          {transactions.isLoading ? (
            <p className="text-sm text-muted-foreground">Loading…</p>
          ) : transactions.data && transactions.data.results.length > 0 ? (
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
                {transactions.data.results.map((t) => (
                  <TableRow key={t.id}>
                    <TableCell>{formatDateTime(t.created_at)}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{t.transaction_type.replace(/_/g, " ")}</Badge>
                    </TableCell>
                    <TableCell className="text-right">{t.quantity}</TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {t.reference_type || "—"}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <p className="py-2 text-sm text-muted-foreground">No stock movements yet.</p>
          )}
        </CardContent>
      </Card>
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
