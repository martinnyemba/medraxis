import * as React from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { inventoryApi } from "../api";
import { useCategories, useUnits, useTaxRates } from "../queries";
import { ApiError } from "@/lib/api/types";
import { useToast } from "@/components/ui/toast";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Spinner } from "@/components/ui/spinner";
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

export function ProductFormDialog() {
  const [open, setOpen] = React.useState(false);
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const categories = useCategories();
  const units = useUnits();
  const taxRates = useTaxRates();

  const [form, setForm] = React.useState({
    name: "",
    sku: "",
    category: "",
    unit: "",
    tax_rate: "",
    sale_price: "",
    cost_price: "",
    reorder_level: "",
    is_drug: false,
  });
  const [formError, setFormError] = React.useState<string | null>(null);

  function reset() {
    setForm({
      name: "",
      sku: "",
      category: "",
      unit: "",
      tax_rate: "",
      sale_price: "",
      cost_price: "",
      reorder_level: "",
      is_drug: false,
    });
    setFormError(null);
  }

  const create = useMutation({
    mutationFn: () =>
      inventoryApi.createProduct({
        name: form.name,
        sku: form.sku,
        category: Number(form.category),
        unit: Number(form.unit),
        tax_rate: form.tax_rate ? Number(form.tax_rate) : null,
        sale_price: form.sale_price || "0",
        cost_price: form.cost_price || "0",
        reorder_level: form.reorder_level || "0",
        is_drug: form.is_drug,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["products"] });
      toast({ title: "Product created", variant: "success" });
      setOpen(false);
      reset();
    },
    onError: (err) =>
      setFormError(err instanceof ApiError ? err.toUserMessage() : "Could not create product."),
  });

  function submit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    if (!form.name.trim()) return setFormError("Name is required.");
    if (!form.sku.trim()) return setFormError("SKU is required.");
    if (!form.category) return setFormError("Select a category.");
    if (!form.unit) return setFormError("Select a unit.");
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
          <Plus className="size-4" /> New product
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>New product</DialogTitle>
        </DialogHeader>
        <form onSubmit={submit} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="name">Name *</Label>
              <Input
                id="name"
                value={form.name}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                autoFocus
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="sku">SKU *</Label>
              <Input
                id="sku"
                value={form.sku}
                onChange={(e) => setForm((f) => ({ ...f, sku: e.target.value }))}
              />
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label>Category *</Label>
              <Select
                value={form.category}
                onValueChange={(v) => setForm((f) => ({ ...f, category: v }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select category" />
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
              <Label>Unit *</Label>
              <Select value={form.unit} onValueChange={(v) => setForm((f) => ({ ...f, unit: v }))}>
                <SelectTrigger>
                  <SelectValue placeholder="Select unit" />
                </SelectTrigger>
                <SelectContent>
                  {units.data?.map((unit) => (
                    <SelectItem key={unit.id} value={String(unit.id)}>
                      {unit.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-3">
            <div className="space-y-2">
              <Label htmlFor="sale_price">Sale price</Label>
              <Input
                id="sale_price"
                type="number"
                step="any"
                value={form.sale_price}
                onChange={(e) => setForm((f) => ({ ...f, sale_price: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="cost_price">Cost price</Label>
              <Input
                id="cost_price"
                type="number"
                step="any"
                value={form.cost_price}
                onChange={(e) => setForm((f) => ({ ...f, cost_price: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="reorder">Reorder level</Label>
              <Input
                id="reorder"
                type="number"
                step="any"
                value={form.reorder_level}
                onChange={(e) => setForm((f) => ({ ...f, reorder_level: e.target.value }))}
              />
            </div>
          </div>

          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              className="size-4 rounded border-input"
              checked={form.is_drug}
              onChange={(e) => setForm((f) => ({ ...f, is_drug: e.target.checked }))}
            />
            This product is a drug / medication
          </label>

          {form.tax_rate || taxRates.data?.length ? (
            <div className="space-y-2">
              <Label>Tax rate</Label>
              <Select
                value={form.tax_rate}
                onValueChange={(v) => setForm((f) => ({ ...f, tax_rate: v }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="No tax" />
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
          ) : null}

          {formError && (
            <p className="whitespace-pre-line rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {formError}
            </p>
          )}
          <DialogFooter>
            <Button type="submit" disabled={create.isPending}>
              {create.isPending ? <Spinner className="size-4" /> : "Create product"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
