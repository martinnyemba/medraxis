import * as React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowLeft, FileText, Minus, Plus, Search, Trash2 } from "lucide-react";
import { posApi } from "./api";
import type { QuotationLine } from "./types";
import { inventoryApi, type Product } from "@/features/inventory/api";
import { useLocations } from "@/features/emr/queries";
import { ApiError } from "@/lib/api/types";
import { money } from "@/lib/format";
import { useDebounce } from "@/lib/hooks";
import { useTenant } from "@/features/tenancy/TenantContext";
import { useToast } from "@/components/ui/toast";
import { PageHeader } from "@/components/common/PageHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface CartItem {
  product: Product;
  quantity: number;
}

export function NewQuotationPage() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { current } = useTenant();
  const currency = current?.currency;

  const locations = useLocations();
  const [cart, setCart] = React.useState<CartItem[]>([]);
  const [note, setNote] = React.useState("");
  const [validUntil, setValidUntil] = React.useState("");
  const [locationId, setLocationId] = React.useState<string>("");

  React.useEffect(() => {
    if (!locationId && locations.data && locations.data.length > 0) {
      setLocationId(String(locations.data[0].id));
    }
  }, [locationId, locations.data]);

  function addProduct(product: Product) {
    setCart((prev) => {
      const existing = prev.find((i) => i.product.id === product.id);
      if (existing) {
        return prev.map((i) =>
          i.product.id === product.id ? { ...i, quantity: i.quantity + 1 } : i,
        );
      }
      return [...prev, { product, quantity: 1 }];
    });
  }

  function setQuantity(productId: number, quantity: number) {
    if (quantity <= 0) {
      setCart((prev) => prev.filter((i) => i.product.id !== productId));
    } else {
      setCart((prev) =>
        prev.map((i) => (i.product.id === productId ? { ...i, quantity } : i)),
      );
    }
  }

  const estimatedTotal = cart.reduce(
    (sum, i) => sum + Number(i.product.sale_price) * i.quantity,
    0,
  );

  const create = useMutation({
    mutationFn: () => {
      const lines: QuotationLine[] = cart.map((i) => ({
        line_type: "PRODUCT",
        product: i.product.id,
        description: i.product.name,
        quantity: String(i.quantity),
      }));
      return posApi.createQuotation({
        lines,
        note,
        valid_until: validUntil || null,
        location: locationId ? Number(locationId) : null,
      });
    },
    onSuccess: (q) => {
      toast({ title: `Quotation ${q.quotation_number} created`, variant: "success" });
      navigate(`/pos/quotations/${q.id}`);
    },
    onError: (err) =>
      toast({
        title: "Could not create quotation",
        description: err instanceof ApiError ? err.toUserMessage() : undefined,
        variant: "error",
      }),
  });

  return (
    <div>
      <Button variant="ghost" size="sm" asChild className="mb-2 -ml-2">
        <Link to="/pos/quotations">
          <ArrowLeft className="size-4" /> Back to quotations
        </Link>
      </Button>
      <PageHeader title="New quotation" description="Build an estimate to send to a customer." />

      <div className="grid gap-6 lg:grid-cols-[1fr_22rem]">
        <ProductSearch onAdd={addProduct} currency={currency} />

        <Card className="h-fit lg:sticky lg:top-4">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <FileText className="size-4 text-primary" /> Estimate ({cart.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {cart.length === 0 ? (
              <p className="py-6 text-center text-sm text-muted-foreground">
                Add products to begin.
              </p>
            ) : (
              <ul className="space-y-3">
                {cart.map((item) => (
                  <li key={item.product.id} className="flex items-center gap-2">
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium">{item.product.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {money(item.product.sale_price, currency)} each
                      </p>
                    </div>
                    <div className="flex items-center gap-1">
                      <Button
                        size="icon"
                        variant="outline"
                        className="size-7"
                        onClick={() => setQuantity(item.product.id, item.quantity - 1)}
                      >
                        <Minus className="size-3" />
                      </Button>
                      <span className="w-7 text-center text-sm">{item.quantity}</span>
                      <Button
                        size="icon"
                        variant="outline"
                        className="size-7"
                        onClick={() => setQuantity(item.product.id, item.quantity + 1)}
                      >
                        <Plus className="size-3" />
                      </Button>
                      <Button
                        size="icon"
                        variant="ghost"
                        className="size-7 text-destructive"
                        onClick={() => setQuantity(item.product.id, 0)}
                      >
                        <Trash2 className="size-3" />
                      </Button>
                    </div>
                  </li>
                ))}
              </ul>
            )}

            <div className="space-y-2 border-t pt-4">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Estimated subtotal</span>
                <span className="font-medium">{money(estimatedTotal, currency)}</span>
              </div>
              <p className="text-xs text-muted-foreground">
                Final totals (tax, catalogue pricing) are calculated by the server on creation.
              </p>
            </div>

            <div className="space-y-1.5">
              <Label className="text-xs">Location</Label>
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

            <div className="space-y-1.5">
              <Label className="text-xs">Valid until</Label>
              <Input
                type="date"
                value={validUntil}
                onChange={(e) => setValidUntil(e.target.value)}
              />
            </div>

            <Input
              placeholder="Note (optional)"
              value={note}
              onChange={(e) => setNote(e.target.value)}
            />

            <Button
              className="w-full"
              disabled={cart.length === 0 || create.isPending}
              onClick={() => create.mutate()}
            >
              {create.isPending ? <Spinner className="size-4" /> : "Create quotation"}
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function ProductSearch({
  onAdd,
  currency,
}: {
  onAdd: (p: Product) => void;
  currency?: string;
}) {
  const [searchInput, setSearchInput] = React.useState("");
  const search = useDebounce(searchInput, 300);

  const { data, isFetching } = useQuery({
    queryKey: ["products", { search }],
    queryFn: () => inventoryApi.listProducts({ search, page_size: 20 }),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Products</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            autoFocus
            placeholder="Search products by name, SKU or barcode…"
            className="pl-9"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
          />
        </div>

        {isFetching && !data ? (
          <p className="py-6 text-center text-sm text-muted-foreground">Searching…</p>
        ) : data && data.results.length > 0 ? (
          <ul className="divide-y">
            {data.results.map((p) => (
              <li key={p.id} className="flex items-center justify-between gap-3 py-2.5">
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium">{p.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {p.sku || "—"} · {money(p.sale_price, currency)} · stock {p.quantity_on_hand}
                  </p>
                </div>
                <Button size="sm" variant="outline" onClick={() => onAdd(p)}>
                  <Plus className="size-3" /> Add
                </Button>
              </li>
            ))}
          </ul>
        ) : (
          <p className="py-6 text-center text-sm text-muted-foreground">
            {searchInput ? "No products found." : "Search to add products to the estimate."}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
