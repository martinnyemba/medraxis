import * as React from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Plus, Receipt } from "lucide-react";
import { financeApi } from "./api";
import { useExpenseCategories, useFinancialAccounts } from "./queries";
import type { Expense } from "./types";
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

export function ExpensesPage() {
  const [page, setPage] = React.useState(1);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["finance", "expenses", { page }],
    queryFn: () => financeApi.listExpenses({ page, ordering: "-id" }),
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
        title="Expenses"
        description="Business costs settled from an account: rent, salaries, utilities, supplies."
        actions={<ExpenseDialog />}
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
                  <TableHead>Date</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Account</TableHead>
                  <TableHead className="text-right">Total</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.results.map((e) => (
                  <TableRow key={e.id}>
                    <TableCell className="font-mono text-xs">{e.number}</TableCell>
                    <TableCell>{formatDate(e.expense_date)}</TableCell>
                    <TableCell>{e.category_name}</TableCell>
                    <TableCell>{e.account_name || "—"}</TableCell>
                    <TableCell className="text-right">{money(e.total)}</TableCell>
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
            icon={<Receipt className="size-8" />}
            title="No expenses recorded yet"
            action={<ExpenseDialog />}
          />
        )}
      </Card>
    </div>
  );
}

function ExpenseDialog() {
  const [open, setOpen] = React.useState(false);
  const [form, setForm] = React.useState<Partial<Expense>>({
    category: undefined, account: null, amount: "", tax_amount: "0",
    expense_date: "", payment_method: "", note: "",
  });
  const [formError, setFormError] = React.useState<string | null>(null);
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const categories = useExpenseCategories();
  const accounts = useFinancialAccounts();

  function reset() {
    setForm({ category: undefined, account: null, amount: "", tax_amount: "0",
      expense_date: "", payment_method: "", note: "" });
    setFormError(null);
  }

  const create = useMutation({
    mutationFn: () => financeApi.createExpense({
      ...form,
      expense_date: form.expense_date || undefined,
    }),
    onSuccess: (expense) => {
      queryClient.invalidateQueries({ queryKey: ["finance", "expenses"] });
      queryClient.invalidateQueries({ queryKey: ["finance", "accounts"] });
      toast({ title: `Expense ${expense.number} recorded`, variant: "success" });
      setOpen(false);
      reset();
    },
    onError: (err) =>
      setFormError(err instanceof ApiError ? err.toUserMessage() : "Could not record expense."),
  });

  function submit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    if (!form.category) return setFormError("Select a category.");
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
          <Plus className="size-4" /> Record expense
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Record expense</DialogTitle>
        </DialogHeader>
        <form onSubmit={submit} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label>Category *</Label>
              <Select
                value={form.category ? String(form.category) : ""}
                onValueChange={(v) => setForm((f) => ({ ...f, category: Number(v) }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select" />
                </SelectTrigger>
                <SelectContent>
                  {categories.data?.map((c) => (
                    <SelectItem key={c.id} value={String(c.id)}>
                      {c.name}
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
              <Label>Account</Label>
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
              <Label htmlFor="date">Expense date</Label>
              <Input
                id="date"
                type="date"
                value={form.expense_date ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, expense_date: e.target.value }))}
                placeholder="Defaults to today"
              />
            </div>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="tax">Tax amount</Label>
              <Input
                id="tax"
                type="number"
                step="any"
                value={form.tax_amount ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, tax_amount: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="method">Payment method</Label>
              <Input
                id="method"
                value={form.payment_method ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, payment_method: e.target.value }))}
                placeholder="CASH, BANK, ..."
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
              {create.isPending ? <Spinner className="size-4" /> : "Record expense"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
