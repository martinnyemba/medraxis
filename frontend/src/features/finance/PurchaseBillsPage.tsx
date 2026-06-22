import * as React from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, FileText, Plus, Trash2 } from "lucide-react";
import { financeApi } from "./api";
import type { PurchaseBillItemInput } from "./types";
import { inventoryApi } from "@/features/inventory/api";
import type { Product } from "@/features/inventory/api";
import { useLocations } from "@/features/emr/queries";
import { ProductCombobox } from "@/components/common/ProductCombobox";
import { ApiError } from "@/lib/api/types";
import { money, formatDate } from "@/lib/format";
import { useToast } from "@/components/ui/toast";
import { PageHeader } from "@/components/common/PageHeader";
import { Pagination } from "@/components/common/Pagination";
import { EmptyState, ErrorState } from "@/components/common/states";
import { StatusBadge } from "@/components/common/StatusBadge";
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

export function PurchaseBillsPage() {
  const [page, setPage] = React.useState(1);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["finance", "purchase-bills", { page }],
    queryFn: () => financeApi.listPurchaseBills({ page, ordering: "-id" }),
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
        title="Purchase bills"
        description="Supplier invoices. Recording one posts a payable and receives the billed stock."
        actions={<PurchaseBillDialog />}
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
                  <TableHead>Bill #</TableHead>
                  <TableHead>Supplier</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead className="text-right">Total</TableHead>
                  <TableHead className="text-right">Balance due</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.results.map((b) => (
                  <TableRow key={b.id}>
                    <TableCell className="font-mono text-xs">{b.bill_number}</TableCell>
                    <TableCell className="font-medium">{b.supplier_name}</TableCell>
                    <TableCell>{formatDate(b.bill_date)}</TableCell>
                    <TableCell className="text-right">{money(b.grand_total)}</TableCell>
                    <TableCell className="text-right">{money(b.balance_due)}</TableCell>
                    <TableCell>
                      <StatusBadge status={b.status} />
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
            icon={<FileText className="size-8" />}
            title="No purchase bills yet"
            action={<PurchaseBillDialog />}
          />
        )}
      </Card>
    </div>
  );
}

interface DraftItem extends PurchaseBillItemInput {
  productName: string;
}

function PurchaseBillDialog() {
  const [open, setOpen] = React.useState(false);
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const locations = useLocations();

  const [supplier, setSupplier] = React.useState("");
  const [locationId, setLocationId] = React.useState("");
  const [billDate, setBillDate] = React.useState("");
  const [invoiceNo, setInvoiceNo] = React.useState("");
  const [items, setItems] = React.useState<DraftItem[]>([]);
  const [picked, setPicked] = React.useState<Product | null>(null);
  const [qty, setQty] = React.useState("");
  const [cost, setCost] = React.useState("");
  const [formError, setFormError] = React.useState<string | null>(null);

  const suppliers = useQuery({
    queryKey: ["suppliers", { all: true }],
    queryFn: () => inventoryApi.listSuppliers({ page_size: 200 }),
    enabled: open,
    select: (p) => p.results,
  });

  function reset() {
    setSupplier("");
    setBillDate("");
    setInvoiceNo("");
    setItems([]);
    setPicked(null);
    setQty("");
    setCost("");
    setFormError(null);
  }

  function addItem() {
    if (!picked || !qty || Number(qty) <= 0) return;
    setItems((prev) => [
      ...prev,
      {
        product: picked.id,
        productName: picked.name,
        quantity: qty,
        unit_cost: cost || picked.cost_price || "0",
      },
    ]);
    setPicked(null);
    setQty("");
    setCost("");
  }

  const create = useMutation({
    mutationFn: () =>
      financeApi.createPurchaseBill({
        supplier: Number(supplier),
        location: locationId ? Number(locationId) : null,
        bill_date: billDate || undefined,
        supplier_invoice_no: invoiceNo,
        items: items.map(({ product, quantity, unit_cost }) => ({
          product, quantity, unit_cost,
        })),
      }),
    onSuccess: (bill) => {
      queryClient.invalidateQueries({ queryKey: ["finance", "purchase-bills"] });
      queryClient.invalidateQueries({ queryKey: ["products"] });
      toast({ title: `Purchase bill ${bill.bill_number} recorded`, variant: "success" });
      setOpen(false);
      reset();
    },
    onError: (err) =>
      setFormError(err instanceof ApiError ? err.toUserMessage() : "Could not record purchase bill."),
  });

  React.useEffect(() => {
    if (open && !locationId && locations.data && locations.data.length > 0) {
      setLocationId(String(locations.data[0].id));
    }
  }, [open, locationId, locations.data]);

  function submit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    if (!supplier) return setFormError("Select a supplier.");
    if (!locationId) return setFormError("Select a location.");
    if (items.length === 0) return setFormError("Add at least one item.");
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
          <Plus className="size-4" /> New purchase bill
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>New purchase bill</DialogTitle>
        </DialogHeader>
        <form onSubmit={submit} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label>Supplier *</Label>
              <Select value={supplier} onValueChange={setSupplier}>
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
              <Label>Location *</Label>
              <Select value={locationId} onValueChange={setLocationId}>
                <SelectTrigger>
                  <SelectValue placeholder="Select" />
                </SelectTrigger>
                <SelectContent>
                  {locations.data?.map((l) => (
                    <SelectItem key={l.id} value={String(l.id)}>
                      {l.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="billDate">Bill date</Label>
              <Input
                id="billDate"
                type="date"
                value={billDate}
                onChange={(e) => setBillDate(e.target.value)}
                placeholder="Defaults to today"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="invoice">Supplier invoice #</Label>
              <Input
                id="invoice"
                value={invoiceNo}
                onChange={(e) => setInvoiceNo(e.target.value)}
              />
            </div>
          </div>

          <div className="space-y-2 rounded-md border p-3">
            <Label>Add item</Label>
            <ProductCombobox value={picked} onSelect={setPicked} />
            {picked && (
              <div className="flex items-end gap-2">
                <div className="flex-1 space-y-1">
                  <Label className="text-xs">Quantity</Label>
                  <Input
                    type="number"
                    step="any"
                    value={qty}
                    onChange={(e) => setQty(e.target.value)}
                  />
                </div>
                <div className="flex-1 space-y-1">
                  <Label className="text-xs">Unit cost</Label>
                  <Input
                    type="number"
                    step="any"
                    value={cost}
                    onChange={(e) => setCost(e.target.value)}
                    placeholder={picked.cost_price}
                  />
                </div>
                <Button type="button" variant="outline" onClick={addItem}>
                  Add
                </Button>
              </div>
            )}
          </div>

          {items.length > 0 && (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Product</TableHead>
                  <TableHead className="text-right">Qty</TableHead>
                  <TableHead className="text-right">Unit cost</TableHead>
                  <TableHead />
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.map((it, idx) => (
                  <TableRow key={idx}>
                    <TableCell className="font-medium">{it.productName}</TableCell>
                    <TableCell className="text-right">{it.quantity}</TableCell>
                    <TableCell className="text-right">{money(it.unit_cost)}</TableCell>
                    <TableCell className="text-right">
                      <Button
                        type="button"
                        size="icon"
                        variant="ghost"
                        className="size-7 text-destructive"
                        onClick={() => setItems((prev) => prev.filter((_, i) => i !== idx))}
                      >
                        <Trash2 className="size-3" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}

          {formError && (
            <p className="whitespace-pre-line rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {formError}
            </p>
          )}
          <DialogFooter>
            <Button type="submit" disabled={create.isPending}>
              {create.isPending ? <Spinner className="size-4" /> : "Record purchase bill"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
