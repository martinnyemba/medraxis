import * as React from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, ReceiptText, Search, ShieldCheck } from "lucide-react";
import { billingApi } from "./api";
import type { BillableService } from "./types";
import { useTaxRates } from "@/features/inventory/queries";
import { ApiError } from "@/lib/api/types";
import { money } from "@/lib/format";
import { useDebounce } from "@/lib/hooks";
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

export function BillableServicesPage() {
  const [page, setPage] = React.useState(1);
  const [searchInput, setSearchInput] = React.useState("");
  const search = useDebounce(searchInput, 350);

  function handleSearch(value: string) {
    setSearchInput(value);
    setPage(1);
  }

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["billing", "services", { search, page }],
    queryFn: () => billingApi.listServices({ search, page }),
    placeholderData: (prev) => prev,
  });

  return (
    <div>
      <PageHeader
        title="Billable services"
        description="Chargeable clinical services priced for the POS catalogue (consultations, procedures, bed-days)."
        actions={
          <div className="flex flex-wrap gap-2">
            <Button asChild variant="outline">
              <Link to="/billing/insurance">
                <ShieldCheck className="size-4" /> Insurance
              </Link>
            </Button>
            <ServiceDialog />
          </div>
        }
      />

      <div className="mb-4 relative max-w-md">
        <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Search services…"
          className="pl-9"
          value={searchInput}
          onChange={(e) => handleSearch(e.target.value)}
        />
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
                  <TableHead>Code</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead className="text-right">Price</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.results.map((s) => (
                  <TableRow key={s.id}>
                    <TableCell className="font-mono text-xs">{s.service_code}</TableCell>
                    <TableCell className="font-medium">{s.name}</TableCell>
                    <TableCell className="text-right">{money(s.price)}</TableCell>
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
            icon={<ReceiptText className="size-8" />}
            title={search ? "No matching services" : "No billable services yet"}
            action={!search ? <ServiceDialog /> : undefined}
          />
        )}
      </Card>
    </div>
  );
}

function ServiceDialog() {
  const [open, setOpen] = React.useState(false);
  const [form, setForm] = React.useState<Partial<BillableService>>({
    name: "", service_code: "", price: "",
  });
  const [formError, setFormError] = React.useState<string | null>(null);
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const taxRates = useTaxRates();

  const create = useMutation({
    mutationFn: () => billingApi.createService(form),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["billing", "services"] });
      toast({ title: "Billable service added", variant: "success" });
      setOpen(false);
      setForm({ name: "", service_code: "", price: "" });
    },
    onError: (err) =>
      setFormError(err instanceof ApiError ? err.toUserMessage() : "Could not add service."),
  });

  function submit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    if (!form.name?.trim()) return setFormError("Name is required.");
    if (!form.service_code?.trim()) return setFormError("Service code is required.");
    create.mutate();
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="size-4" /> Add service
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add billable service</DialogTitle>
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
              <Label htmlFor="code">Service code *</Label>
              <Input
                id="code"
                value={form.service_code ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, service_code: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="price">Price *</Label>
              <Input
                id="price"
                type="number"
                step="any"
                value={form.price ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, price: e.target.value }))}
              />
            </div>
          </div>
          <div className="space-y-2">
            <Label>Tax rate</Label>
            <Select
              value={form.tax_rate ? String(form.tax_rate) : ""}
              onValueChange={(v) => setForm((f) => ({ ...f, tax_rate: v ? Number(v) : null }))}
            >
              <SelectTrigger>
                <SelectValue placeholder="None" />
              </SelectTrigger>
              <SelectContent>
                {taxRates.data?.map((t) => (
                  <SelectItem key={t.id} value={String(t.id)}>
                    {t.name} ({t.rate_percent}%)
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          {formError && (
            <p className="whitespace-pre-line rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {formError}
            </p>
          )}
          <DialogFooter>
            <Button type="submit" disabled={create.isPending}>
              {create.isPending ? <Spinner className="size-4" /> : "Add service"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
