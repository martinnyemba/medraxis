import type { ReactNode } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, ArrowRightLeft, ShoppingCart } from "lucide-react";
import { posApi } from "./api";
import { ApiError } from "@/lib/api/types";
import { money, formatDate } from "@/lib/format";
import { useTenant } from "@/features/tenancy/TenantContext";
import { useToast } from "@/components/ui/toast";
import { PageHeader } from "@/components/common/PageHeader";
import { StatusBadge } from "@/components/common/StatusBadge";
import { ErrorState } from "@/components/common/states";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PageLoader, Spinner } from "@/components/ui/spinner";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export function QuotationDetailPage() {
  const { quotationId } = useParams<{ quotationId: string }>();
  const id = Number(quotationId);
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const { current } = useTenant();
  const currency = current?.currency;

  const quotation = useQuery({
    queryKey: ["quotation", id],
    queryFn: () => posApi.getQuotation(id),
    enabled: Number.isFinite(id),
  });

  const convert = useMutation({
    mutationFn: () => posApi.convertQuotation(id),
    onSuccess: (sale) => {
      toast({ title: `Converted to sale ${sale.invoice_number}`, variant: "success" });
      queryClient.invalidateQueries({ queryKey: ["quotation", id] });
      queryClient.invalidateQueries({ queryKey: ["quotations"] });
      navigate(`/pos/sales/${sale.id}`);
    },
    onError: (err) =>
      toast({
        title: "Could not convert quotation",
        description: err instanceof ApiError ? err.toUserMessage() : undefined,
        variant: "error",
      }),
  });

  if (quotation.isLoading) return <PageLoader />;
  if (quotation.isError || !quotation.data)
    return <ErrorState error={quotation.error} onRetry={quotation.refetch} />;

  const q = quotation.data;
  const converted = q.status === "CONVERTED" || q.converted_sale != null;

  return (
    <div className="space-y-6">
      <div>
        <Button variant="ghost" size="sm" asChild className="mb-2 -ml-2">
          <Link to="/pos/quotations">
            <ArrowLeft className="size-4" /> Back to quotations
          </Link>
        </Button>
        <PageHeader
          title={q.quotation_number}
          description="Estimate detail"
          actions={
            converted ? (
              q.converted_sale != null ? (
                <Button asChild variant="outline">
                  <Link to={`/pos/sales/${q.converted_sale}`}>
                    <ShoppingCart className="size-4" /> View sale
                  </Link>
                </Button>
              ) : undefined
            ) : (
              <Button onClick={() => convert.mutate()} disabled={convert.isPending}>
                {convert.isPending ? (
                  <Spinner className="size-4" />
                ) : (
                  <ArrowRightLeft className="size-4" />
                )}
                Convert to sale
              </Button>
            )
          }
        />
      </div>

      <Card>
        <CardContent className="grid gap-4 pt-6 sm:grid-cols-2 lg:grid-cols-4">
          <Field label="Status">
            <StatusBadge status={q.status} />
          </Field>
          <Field label="Created">{formatDate(q.created_at)}</Field>
          <Field label="Valid until">{formatDate(q.valid_until)}</Field>
          <Field label="Grand total">{money(q.grand_total, currency)}</Field>
          {q.note && (
            <div className="sm:col-span-2 lg:col-span-4">
              <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Note
              </p>
              <p className="text-sm">{q.note}</p>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Lines</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Item</TableHead>
                <TableHead className="text-right">Qty</TableHead>
                <TableHead className="text-right">Unit price</TableHead>
                <TableHead className="text-right">Disc %</TableHead>
                <TableHead className="text-right">Tax %</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {q.lines.map((ln, i) => (
                <TableRow key={ln.id ?? i}>
                  <TableCell className="font-medium">{ln.description || ln.line_type}</TableCell>
                  <TableCell className="text-right">{ln.quantity}</TableCell>
                  <TableCell className="text-right">{money(ln.unit_price, currency)}</TableCell>
                  <TableCell className="text-right">{ln.discount_percent ?? "0"}</TableCell>
                  <TableCell className="text-right">{ln.tax_percent ?? "0"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          <dl className="mt-4 ml-auto max-w-xs space-y-1 text-sm">
            <Row label="Subtotal" value={money(q.subtotal, currency)} />
            <Row label="Discount" value={money(q.discount_total, currency)} />
            <Row label="Tax" value={money(q.tax_total, currency)} />
            <Row label="Grand total" value={money(q.grand_total, currency)} bold />
          </dl>
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

function Row({ label, value, bold }: { label: string; value: string; bold?: boolean }) {
  return (
    <div className={`flex justify-between ${bold ? "border-t pt-1 font-semibold" : ""}`}>
      <dt className="text-muted-foreground">{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}
