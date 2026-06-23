import * as React from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BarChart3, BookOpen, FileText, HandCoins, Landmark, Plus, Receipt } from "lucide-react";
import { financeApi } from "./api";
import type { AccountType, FinancialAccount } from "./types";
import { ApiError } from "@/lib/api/types";
import { money, formatDateTime } from "@/lib/format";
import { useToast } from "@/components/ui/toast";
import { PageHeader } from "@/components/common/PageHeader";
import { Pagination } from "@/components/common/Pagination";
import { EmptyState, ErrorState } from "@/components/common/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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

const ACCOUNT_TYPES: { value: AccountType; label: string }[] = [
  { value: "CASH", label: "Cash" },
  { value: "BANK", label: "Bank" },
  { value: "MOBILE_MONEY", label: "Mobile money" },
  { value: "CARD", label: "Card settlement" },
];

export function AccountsPage() {
  const [page, setPage] = React.useState(1);
  const [selected, setSelected] = React.useState<FinancialAccount | null>(null);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["finance", "accounts", { page }],
    queryFn: () => financeApi.listAccounts({ page }),
    placeholderData: (prev) => prev,
  });

  return (
    <div>
      <PageHeader
        title="Accounts"
        description="Cash drawers and bank accounts money flows through."
        actions={
          <div className="flex flex-wrap gap-2">
            <Button asChild variant="outline">
              <Link to="/finance/expenses">
                <Receipt className="size-4" /> Expenses
              </Link>
            </Button>
            <Button asChild variant="outline">
              <Link to="/finance/purchase-bills">
                <FileText className="size-4" /> Purchase bills
              </Link>
            </Button>
            <Button asChild variant="outline">
              <Link to="/finance/supplier-payments">
                <HandCoins className="size-4" /> Supplier payments
              </Link>
            </Button>
            <Button asChild variant="outline">
              <Link to="/finance/party-ledger">
                <BookOpen className="size-4" /> Party ledger
              </Link>
            </Button>
            <Button asChild variant="outline">
              <Link to="/finance/reports">
                <BarChart3 className="size-4" /> Reports
              </Link>
            </Button>
            <AccountDialog />
          </div>
        }
      />

      <Card className="mb-4">
        {isLoading ? (
          <PageLoader />
        ) : isError ? (
          <ErrorState error={error} onRetry={refetch} />
        ) : data && data.results.length > 0 ? (
          <>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Account</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead className="text-right">Balance</TableHead>
                  <TableHead />
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.results.map((a) => (
                  <TableRow
                    key={a.id}
                    className="cursor-pointer"
                    onClick={() => setSelected(a)}
                    data-state={selected?.id === a.id ? "selected" : undefined}
                  >
                    <TableCell className="font-medium">
                      {a.name} {a.is_default && <Badge variant="secondary">Default</Badge>}
                    </TableCell>
                    <TableCell>{ACCOUNT_TYPES.find((t) => t.value === a.account_type)?.label}</TableCell>
                    <TableCell className="text-right">{money(a.current_balance)}</TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="sm" onClick={() => setSelected(a)}>
                        View transactions
                      </Button>
                    </TableCell>
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
            icon={<Landmark className="size-8" />}
            title="No accounts yet"
            action={<AccountDialog />}
          />
        )}
      </Card>

      {selected && <AccountTransactions account={selected} />}
    </div>
  );
}

function AccountTransactions({ account }: { account: FinancialAccount }) {
  const [page, setPage] = React.useState(1);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["finance", "accounts", account.id, "transactions", { page }],
    queryFn: () => financeApi.accountTransactions(account.id, { page }),
    placeholderData: (prev) => prev,
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{account.name} — transactions</CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        {isLoading ? (
          <PageLoader />
        ) : isError ? (
          <ErrorState error={error} onRetry={refetch} />
        ) : data && data.results.length > 0 ? (
          <>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>When</TableHead>
                  <TableHead>Direction</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                  <TableHead className="text-right">Balance after</TableHead>
                  <TableHead>Note</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.results.map((t) => (
                  <TableRow key={t.id}>
                    <TableCell>{formatDateTime(t.occurred_at)}</TableCell>
                    <TableCell>
                      <Badge variant={t.direction === "IN" ? "success" : "destructive"}>
                        {t.direction === "IN" ? "Money in" : "Money out"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">{money(t.amount)}</TableCell>
                    <TableCell className="text-right">{money(t.balance_after)}</TableCell>
                    <TableCell className="text-muted-foreground">{t.note || "—"}</TableCell>
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
          <p className="p-6 text-sm text-muted-foreground">No transactions yet.</p>
        )}
      </CardContent>
    </Card>
  );
}

function AccountDialog() {
  const [open, setOpen] = React.useState(false);
  const [form, setForm] = React.useState<Partial<FinancialAccount>>({
    name: "", account_type: "CASH", account_number: "", bank_name: "", opening_balance: "0",
  });
  const [formError, setFormError] = React.useState<string | null>(null);
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const create = useMutation({
    mutationFn: () => financeApi.createAccount(form),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["finance", "accounts"] });
      toast({ title: "Account added", variant: "success" });
      setOpen(false);
      setForm({ name: "", account_type: "CASH", account_number: "", bank_name: "", opening_balance: "0" });
    },
    onError: (err) =>
      setFormError(err instanceof ApiError ? err.toUserMessage() : "Could not add account."),
  });

  function submit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    if (!form.name?.trim()) return setFormError("Name is required.");
    create.mutate();
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="size-4" /> Add account
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add account</DialogTitle>
        </DialogHeader>
        <form onSubmit={submit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Name *</Label>
            <Input
              id="name"
              value={form.name ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              autoFocus
            />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label>Type</Label>
              <Select
                value={form.account_type}
                onValueChange={(v) => setForm((f) => ({ ...f, account_type: v as AccountType }))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {ACCOUNT_TYPES.map((t) => (
                    <SelectItem key={t.value} value={t.value}>
                      {t.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="opening">Opening balance</Label>
              <Input
                id="opening"
                type="number"
                step="any"
                value={form.opening_balance ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, opening_balance: e.target.value }))}
              />
            </div>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="bank">Bank name</Label>
              <Input
                id="bank"
                value={form.bank_name ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, bank_name: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="number">Account number</Label>
              <Input
                id="number"
                value={form.account_number ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, account_number: e.target.value }))}
              />
            </div>
          </div>
          {formError && (
            <p className="whitespace-pre-line rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {formError}
            </p>
          )}
          <DialogFooter>
            <Button type="submit" disabled={create.isPending}>
              {create.isPending ? <Spinner className="size-4" /> : "Add account"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
