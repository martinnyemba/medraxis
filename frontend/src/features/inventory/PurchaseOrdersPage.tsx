import * as React from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Plus, ScrollText, Trash2 } from "lucide-react";
import { inventoryApi, type Product, type PurchaseOrderItem } from "./api";
import { useLocations } from "@/features/emr/queries";
import { ApiError } from "@/lib/api/types";
import { money, formatDate } from "@/lib/format";
import { useToast } from "@/components/ui/toast";
import { PageHeader } from "@/components/common/PageHeader";
import { Pagination } from "@/components/common/Pagination";
import { EmptyState, ErrorState } from "@/components/common/states";
import { StatusBadge } from "@/components/common/StatusBadge";
import { ProductCombobox } from "@/components/common/ProductCombobox";
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

export function PurchaseOrdersPage() {
  const [page, setPage] = React.useState(1);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["purchase-orders", { page }],
    queryFn: () => inventoryApi.listPurchaseOrders({ page, ordering: "-id" }),
    placeholderData: (prev) => prev,
  });

  return (
    <div>
      <Button variant="ghost" size="sm" asChild className="mb-2 -ml-2">
        <Link to="/inventory/products">
          <ArrowLeft className="size-4" /> Back to inventory
        </Link>
      </Button>
      <PageHeader
        title="Purchase orders"
        description="Orders raised to suppliers for stock replenishment."
        actions={<PurchaseOrderDialog />}
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
                  <TableHead>PO #</TableHead>
                  <TableHead>Expected</TableHead>
                  <TableHead className="text-right">Items</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.results.map((po) => (
                  <TableRow key={po.id}>
                    <TableCell className="font-mono text-xs">{po.po_number}</TableCell>
                    <TableCell>{formatDate(po.expected_date)}</TableCell>
                    <TableCell className="text-right">{po.items.length}</TableCell>
                    <TableCell>
                      <StatusBadge status={po.status} />
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
            icon={<ScrollText className="size-8" />}
            title="No purchase orders"
            action={<PurchaseOrderDialog />}
          />
        )}
      </Card>
    </div>
  );
}

interface DraftItem extends PurchaseOrderItem {
  productName: string;
}

function PurchaseOrderDialog() {
  const [open, setOpen] = React.useState(false);
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const locations = useLocations();

  const [supplier, setSupplier] = React.useState("");
  const [locationId, setLocationId] = React.useState("");
  const [expected, setExpected] = React.useState("");
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
    setExpected("");
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
        quantity_ordered: qty,
        unit_cost: cost || picked.cost_price || "0",
      },
    ]);
    setPicked(null);
    setQty("");
    setCost("");
  }

  const create = useMutation({
    mutationFn: () =>
      inventoryApi.createPurchaseOrder({
        supplier: Number(supplier),
        location: locationId ? Number(locationId) : null,
        expected_date: expected || null,
        items: items.map(({ product, quantity_ordered, unit_cost }) => ({
          product,
          quantity_ordered,
          unit_cost,
        })),
      }),
    onSuccess: (po) => {
      queryClient.invalidateQueries({ queryKey: ["purchase-orders"] });
      toast({ title: `Purchase order ${po.po_number} created`, variant: "success" });
      setOpen(false);
      reset();
    },
    onError: (err) =>
      setFormError(err instanceof ApiError ? err.toUserMessage() : "Could not create purchase order."),
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
          <Plus className="size-4" /> New purchase order
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>New purchase order</DialogTitle>
        </DialogHeader>
        <form onSubmit={submit} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-3">
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
              <Label>Location</Label>
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
            <div className="space-y-2">
              <Label htmlFor="expected">Expected date</Label>
              <Input
                id="expected"
                type="date"
                value={expected}
                onChange={(e) => setExpected(e.target.value)}
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
                    <TableCell className="text-right">{it.quantity_ordered}</TableCell>
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
              {create.isPending ? <Spinner className="size-4" /> : "Create purchase order"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
