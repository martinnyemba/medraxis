import * as React from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, HandCoins, Plus } from "lucide-react";
import { financeApi } from "./api";
import { useFinancialAccounts } from "./queries";
import type { SupplierPayment } from "./types";
import { inventoryApi } from "@/features/inventory/api";
import { ApiError } from "@/lib/api/types";
import { money, formatDate } from "@/lib/format";
import { useToast } from "@/components/ui/toast";
import { PageHeader } from "@/components/common/PageHeader";
import { Pagination } from "@/components/common/Pagination";
import { EmptyState, ErrorState } from "@/components/common/states";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { PageLoader, Spinner } from "@/components/ui/spinner";
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
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

const METHODS = ["CASH", "BANK_TRANSFER", "MOBILE_MONEY", "CARD", "CHEQUE"];

export function SupplierPaymentsPage() {
  const [page, setPage] = React.useState(1);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["finance", "supplier-payments", { page }],
    queryFn: () => financeApi.listSupplierPayments({ page, ordering: "-id" }),
    placeholderData: (prev) => prev,
  });

  return (
    <div>
      <Button variant="ghost" size="sm" asChild className="mb-2 -ml-2">
        <Link to="/finance/accounts">
          <ArrowLeft className="size-4" /> Back to finance
        </Link>
      </Button>
      <PageHeader
        title="Supplier payments"
        description="Payments made to suppliers against outstanding purchase bills."
        actions={<SupplierPaymentDialog />}
      />

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
                  <TableHead>Number</TableHead>
                  <TableHead>Supplier</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Method</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.results.map((p) => (
                  <TableRow key={p.id}>
                    <TableCell className="font-mono text-xs">{p.number}</TableCell>
                    <TableCell className="font-medium">{p.supplier_name}</TableCell>
                    <TableCell>{formatDate(p.paid_on)}</TableCell>
                    <TableCell>{p.method}</TableCell>
                    <TableCell className="text-right">{money(p.amount)}</TableCell>
                  </TableRow>
                ))}
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
          <EmptyState
            icon={<HandCoins className="size-8" />}
            title="No supplier payments yet"
            action={<SupplierPaymentDialog />}
          />
        )}
      </Card>
    </div>
  );
}

function SupplierPaymentDialog() {
  const [open, setOpen] = React.useState(false);
  const [form, setForm] = React.useState<Partial<SupplierPayment>>({
    supplier: undefined, account: null, amount: "", paid_on: "", method: "CASH",
    reference: "", note: "",
  });
  const [formError, setFormError] = React.useState<string | null>(null);
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const accounts = useFinancialAccounts();

  const suppliers = useQuery({
    queryKey: ["suppliers", { all: true }],
    queryFn: () => inventoryApi.listSuppliers({ page_size: 200 }),
    enabled: open,
    select: (p) => p.results,
  });

  function reset() {
    setForm({ supplier: undefined, account: null, amount: "", paid_on: "", method: "CASH",
      reference: "", note: "" });
    setFormError(null);
  }

  const create = useMutation({
    mutationFn: () => financeApi.createSupplierPayment({
      ...form,
      paid_on: form.paid_on || undefined,
    }),
    onSuccess: (payment) => {
      queryClient.invalidateQueries({ queryKey: ["finance", "supplier-payments"] });
      queryClient.invalidateQueries({ queryKey: ["finance", "accounts"] });
      toast({ title: `Payment ${payment.number} recorded`, variant: "success" });
      setOpen(false);
      reset();
    },
    onError: (err) =>
      setFormError(err instanceof ApiError ? err.toUserMessage() : "Could not record payment."),
  });

  function submit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    if (!form.supplier) return setFormError("Select a supplier.");
    if (!form.amount) return setFormError("Amount is required.");
    create.mutate();
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(o) => {
        setOpen(o);
        if (!o) reset();
      }}
    >
      <DialogTrigger asChild>
        <Button>
          <Plus className="size-4" /> Record payment
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Record supplier payment</DialogTitle>
        </DialogHeader>
        <form onSubmit={submit} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label>Supplier *</Label>
              <Select
                value={form.supplier ? String(form.supplier) : ""}
                onValueChange={(v) => setForm((f) => ({ ...f, supplier: Number(v) }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select" />
                </SelectTrigger>
                <SelectContent>
                  {suppliers.data?.map((s) => (
                    <SelectItem key={s.id} value={String(s.id)}>
                      {s.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="amount">Amount *</Label>
              <Input
                id="amount"
                type="number"
                step="any"
                value={form.amount ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, amount: e.target.value }))}
              />
            </div>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label>From account</Label>
              <Select
                value={form.account ? String(form.account) : ""}
                onValueChange={(v) => setForm((f) => ({ ...f, account: v ? Number(v) : null }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="None" />
                </SelectTrigger>
                <SelectContent>
                  {accounts.data?.map((a) => (
                    <SelectItem key={a.id} value={String(a.id)}>
                      {a.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="paidOn">Paid on</Label>
              <Input
                id="paidOn"
                type="date"
                value={form.paid_on ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, paid_on: e.target.value }))}
                placeholder="Defaults to today"
              />
            </div>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label>Method</Label>
              <Select
                value={form.method}
                onValueChange={(v) => setForm((f) => ({ ...f, method: v }))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {METHODS.map((m) => (
                    <SelectItem key={m} value={m}>
                      {m.replace(/_/g, " ")}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="reference">Reference</Label>
              <Input
                id="reference"
                value={form.reference ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, reference: e.target.value }))}
              />
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="note">Note</Label>
            <Input
              id="note"
              value={form.note ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, note: e.target.value }))}
            />
          </div>
          {formError && (
            <p className="whitespace-pre-line rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {formError}
            </p>
          )}
          <DialogFooter>
            <Button type="submit" disabled={create.isPending}>
              {create.isPending ? <Spinner className="size-4" /> : "Record payment"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
