import * as React from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, CheckCircle2, CreditCard, Receipt } from "lucide-react";
import { posApi } from "./api";
import type { PaymentMethod } from "./types";
import { ApiError } from "@/lib/api/types";
import { openAuthenticatedFile } from "@/lib/api/client";
import { money, formatDateTime } from "@/lib/format";
import { useToast } from "@/components/ui/toast";
import { PageHeader } from "@/components/common/PageHeader";
import { StatusBadge } from "@/components/common/StatusBadge";
import { ErrorState } from "@/components/common/states";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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

const PAYMENT_METHODS: { value: PaymentMethod; label: string }[] = [
  { value: "CASH", label: "Cash" },
  { value: "CARD", label: "Card" },
  { value: "MOBILE_MONEY", label: "Mobile money" },
  { value: "BANK_TRANSFER", label: "Bank transfer" },
  { value: "INSURANCE", label: "Insurance" },
  { value: "CREDIT", label: "Credit / account" },
];

export function SaleDetailPage() {
  const { saleId } = useParams<{ saleId: string }>();
  const id = Number(saleId);
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const { data: sale, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["sale", id],
    queryFn: () => posApi.getSale(id),
    enabled: Number.isFinite(id),
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["sale", id] });
    queryClient.invalidateQueries({ queryKey: ["sales"] });
  };

  const complete = useMutation({
    mutationFn: () => posApi.completeSale(id),
    onSuccess: () => {
      toast({ title: "Sale completed — stock issued", variant: "success" });
      invalidate();
    },
    onError: (err) =>
      toast({
        title: "Could not complete sale",
        description: err instanceof ApiError ? err.toUserMessage() : undefined,
        variant: "error",
      }),
  });

  if (isLoading) return <PageLoader />;
  if (isError || !sale) return <ErrorState error={error} onRetry={refetch} />;

  const isDraft = sale.status === "DRAFT";
  const canPay = ["COMPLETED", "PARTIALLY_PAID"].includes(sale.status);

  return (
    <div className="space-y-6">
      <div>
        <Button variant="ghost" size="sm" asChild className="mb-2 -ml-2">
          <Link to="/pos/sales">
            <ArrowLeft className="size-4" /> Back to sales
          </Link>
        </Button>
        <PageHeader
          title={`Invoice ${sale.invoice_number}`}
          description={formatDateTime(sale.created_at)}
          actions={
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                onClick={() => openAuthenticatedFile(posApi.receiptUrl(sale.id)).catch(() => {})}
              >
                <Receipt className="size-4" /> Receipt
              </Button>
              {isDraft && (
                <Button onClick={() => complete.mutate()} disabled={complete.isPending}>
                  {complete.isPending ? <Spinner className="size-4" /> : <CheckCircle2 className="size-4" />}
                  Complete sale
                </Button>
              )}
              {canPay && <PaymentDialog saleId={sale.id} balanceDue={sale.balance_due} onPaid={invalidate} />}
            </div>
          }
        />
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <StatusBadge status={sale.status} />
        {isDraft && (
          <span className="text-sm text-muted-foreground">
            Complete the sale to draw down stock, then take payment.
          </span>
        )}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Items</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Description</TableHead>
                <TableHead className="text-right">Qty</TableHead>
                <TableHead className="text-right">Unit price</TableHead>
                <TableHead className="text-right">Tax</TableHead>
                <TableHead className="text-right">Total</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sale.lines.map((line, idx) => (
                <TableRow key={line.id ?? idx}>
                  <TableCell className="font-medium">{line.description}</TableCell>
                  <TableCell className="text-right">{line.quantity}</TableCell>
                  <TableCell className="text-right">{money(line.unit_price, sale.currency)}</TableCell>
                  <TableCell className="text-right">{money(line.tax_amount, sale.currency)}</TableCell>
                  <TableCell className="text-right font-medium">
                    {money(line.line_total, sale.currency)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>

          <div className="mt-4 ml-auto max-w-xs space-y-1.5 text-sm">
            <Row label="Subtotal" value={money(sale.subtotal, sale.currency)} />
            <Row label="Discount" value={`- ${money(sale.discount_total, sale.currency)}`} />
            <Row label="Tax" value={money(sale.tax_total, sale.currency)} />
            <div className="flex justify-between border-t pt-1.5 text-base font-semibold">
              <span>Grand total</span>
              <span>{money(sale.grand_total, sale.currency)}</span>
            </div>
            <Row label="Paid" value={money(sale.amount_paid, sale.currency)} />
            <Row label="Balance due" value={money(sale.balance_due, sale.currency)} emphasize />
          </div>
        </CardContent>
      </Card>

      {sale.payments.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Payments</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Method</TableHead>
                  <TableHead>Reference</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sale.payments.map((p) => (
                  <TableRow key={p.id}>
                    <TableCell>{formatDateTime(p.created_at)}</TableCell>
                    <TableCell>{p.method.replace(/_/g, " ")}</TableCell>
                    <TableCell className="text-muted-foreground">{p.reference || "—"}</TableCell>
                    <TableCell className="text-right font-medium">
                      {money(p.amount, sale.currency)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function Row({ label, value, emphasize }: { label: string; value: string; emphasize?: boolean }) {
  return (
    <div className="flex justify-between">
      <span className="text-muted-foreground">{label}</span>
      <span className={emphasize ? "font-semibold" : ""}>{value}</span>
    </div>
  );
}

function PaymentDialog({
  saleId,
  balanceDue,
  onPaid,
}: {
  saleId: number;
  balanceDue: string;
  onPaid: () => void;
}) {
  const [open, setOpen] = React.useState(false);
  const [method, setMethod] = React.useState<PaymentMethod>("CASH");
  const [amount, setAmount] = React.useState(balanceDue);
  const [reference, setReference] = React.useState("");
  const [formError, setFormError] = React.useState<string | null>(null);
  const { toast } = useToast();

  React.useEffect(() => {
    if (open) {
      setAmount(balanceDue);
      setMethod("CASH");
      setReference("");
      setFormError(null);
    }
  }, [open, balanceDue]);

  const pay = useMutation({
    mutationFn: () => posApi.paySale(saleId, method, amount, reference),
    onSuccess: () => {
      toast({ title: "Payment recorded", variant: "success" });
      setOpen(false);
      onPaid();
    },
    onError: (err) =>
      setFormError(err instanceof ApiError ? err.toUserMessage() : "Could not record payment."),
  });

  function submit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    if (!amount || Number(amount) <= 0) return setFormError("Enter a valid amount.");
    pay.mutate();
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <CreditCard className="size-4" /> Take payment
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Take payment</DialogTitle>
        </DialogHeader>
        <form onSubmit={submit} className="space-y-4">
          <div className="space-y-2">
            <Label>Method</Label>
            <Select value={method} onValueChange={(v) => setMethod(v as PaymentMethod)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {PAYMENT_METHODS.map((m) => (
                  <SelectItem key={m.value} value={m.value}>
                    {m.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="amount">Amount</Label>
            <Input
              id="amount"
              type="number"
              step="any"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="reference">Reference (optional)</Label>
            <Input
              id="reference"
              value={reference}
              onChange={(e) => setReference(e.target.value)}
              placeholder="Transaction / receipt reference"
            />
          </div>
          {formError && (
            <p className="whitespace-pre-line rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {formError}
            </p>
          )}
          <DialogFooter>
            <Button type="submit" disabled={pay.isPending}>
              {pay.isPending ? <Spinner className="size-4" /> : "Record payment"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
