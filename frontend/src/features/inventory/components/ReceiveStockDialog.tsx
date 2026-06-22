import * as React from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { PackagePlus } from "lucide-react";
import { inventoryApi, type Product } from "../api";
import { useLocations } from "@/features/emr/queries";
import { ApiError } from "@/lib/api/types";
import { useToast } from "@/components/ui/toast";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Spinner } from "@/components/ui/spinner";
import { ProductCombobox } from "@/components/common/ProductCombobox";
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

/** Receive stock into a batch. When `product` is given the picker is hidden
 *  (used on a product's detail page); otherwise the user searches for one. */
export function ReceiveStockDialog({
  product: fixedProduct,
  variant = "default",
}: {
  product?: Product;
  variant?: "default" | "outline";
}) {
  const [open, setOpen] = React.useState(false);
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const locations = useLocations();

  const [picked, setPicked] = React.useState<Product | null>(null);
  const [locationId, setLocationId] = React.useState("");
  const [form, setForm] = React.useState({
    quantity: "",
    unit_cost: "",
    batch_number: "",
    expiry_date: "",
  });
  const [formError, setFormError] = React.useState<string | null>(null);

  const product = fixedProduct ?? picked;

  React.useEffect(() => {
    if (open && !locationId && locations.data && locations.data.length > 0) {
      setLocationId(String(locations.data[0].id));
    }
  }, [open, locationId, locations.data]);

  function reset() {
    setPicked(null);
    setForm({ quantity: "", unit_cost: "", batch_number: "", expiry_date: "" });
    setFormError(null);
  }

  const receive = useMutation({
    mutationFn: () =>
      inventoryApi.receiveStock({
        product: product!.id,
        location: Number(locationId),
        quantity: form.quantity,
        unit_cost: form.unit_cost || "0",
        batch_number: form.batch_number,
        expiry_date: form.expiry_date || null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["products"] });
      queryClient.invalidateQueries({ queryKey: ["batches"] });
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      if (product) queryClient.invalidateQueries({ queryKey: ["product", product.id] });
      toast({ title: "Stock received", variant: "success" });
      setOpen(false);
      reset();
    },
    onError: (err) =>
      setFormError(err instanceof ApiError ? err.toUserMessage() : "Could not receive stock."),
  });

  function submit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    if (!product) return setFormError("Select a product.");
    if (!locationId) return setFormError("Select a location.");
    if (!form.quantity || Number(form.quantity) <= 0) return setFormError("Enter a quantity.");
    receive.mutate();
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
        <Button variant={variant}>
          <PackagePlus className="size-4" /> Receive stock
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Receive stock</DialogTitle>
        </DialogHeader>
        <form onSubmit={submit} className="space-y-4">
          {fixedProduct ? (
            <div className="rounded-md border bg-accent/40 px-3 py-2 text-sm font-medium">
              {fixedProduct.name}
            </div>
          ) : (
            <div className="space-y-2">
              <Label>Product *</Label>
              <ProductCombobox value={picked} onSelect={setPicked} />
            </div>
          )}

          <div className="space-y-2">
            <Label>Location *</Label>
            <Select value={locationId} onValueChange={setLocationId}>
              <SelectTrigger>
                <SelectValue placeholder="Select location" />
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

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="quantity">Quantity *</Label>
              <Input
                id="quantity"
                type="number"
                step="any"
                value={form.quantity}
                onChange={(e) => setForm((f) => ({ ...f, quantity: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="unit_cost">Unit cost</Label>
              <Input
                id="unit_cost"
                type="number"
                step="any"
                value={form.unit_cost}
                onChange={(e) => setForm((f) => ({ ...f, unit_cost: e.target.value }))}
              />
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="batch">Batch number</Label>
              <Input
                id="batch"
                value={form.batch_number}
                onChange={(e) => setForm((f) => ({ ...f, batch_number: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="expiry">Expiry date</Label>
              <Input
                id="expiry"
                type="date"
                value={form.expiry_date}
                onChange={(e) => setForm((f) => ({ ...f, expiry_date: e.target.value }))}
              />
            </div>
          </div>

          {formError && (
            <p className="whitespace-pre-line rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {formError}
            </p>
          )}
          <DialogFooter>
            <Button type="submit" disabled={receive.isPending}>
              {receive.isPending ? <Spinner className="size-4" /> : "Receive"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
