import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { Check, Search, X } from "lucide-react";
import { inventoryApi, type Product } from "@/features/inventory/api";
import { money } from "@/lib/format";
import { useDebounce } from "@/lib/hooks";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

/** Single-select product picker (used by pharmacy prescribing). */
export function ProductCombobox({
  value,
  onSelect,
  drugsOnly = false,
  currency,
}: {
  value: Product | null;
  onSelect: (product: Product | null) => void;
  drugsOnly?: boolean;
  currency?: string;
}) {
  const [term, setTerm] = React.useState("");
  const search = useDebounce(term, 300);

  const { data, isFetching } = useQuery({
    queryKey: ["products", { search, drugsOnly, picker: true }],
    queryFn: () =>
      inventoryApi.listProducts({
        search,
        page_size: 10,
        ...(drugsOnly ? { is_drug: true } : {}),
      }),
    enabled: search.length >= 2 && !value,
  });

  if (value) {
    return (
      <div className="flex items-center justify-between rounded-md border bg-accent/40 px-3 py-2">
        <div className="flex items-center gap-2">
          <Check className="size-4 text-success" />
          <div>
            <p className="text-sm font-medium">{value.name}</p>
            <p className="text-xs text-muted-foreground">
              {value.sku} · stock {value.quantity_on_hand}
            </p>
          </div>
        </div>
        <Button type="button" variant="ghost" size="sm" onClick={() => onSelect(null)}>
          <X className="size-4" /> Change
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          autoFocus
          placeholder={drugsOnly ? "Search drugs…" : "Search products…"}
          className="pl-9"
          value={term}
          onChange={(e) => setTerm(e.target.value)}
        />
      </div>
      {search.length >= 2 && (
        <div className="max-h-56 overflow-y-auto rounded-md border">
          {isFetching ? (
            <p className="p-3 text-sm text-muted-foreground">Searching…</p>
          ) : data && data.results.length > 0 ? (
            data.results.map((p) => (
              <button
                key={p.id}
                type="button"
                onClick={() => onSelect(p)}
                className="flex w-full items-center justify-between px-3 py-2 text-left text-sm hover:bg-accent"
              >
                <span className="min-w-0">
                  <span className="block truncate font-medium">{p.name}</span>
                  <span className="text-xs text-muted-foreground">
                    {p.sku} · {money(p.sale_price, currency)}
                  </span>
                </span>
                {p.quantity_on_hand <= 0 ? (
                  <Badge variant="warning">No stock</Badge>
                ) : (
                  <span className="text-xs text-muted-foreground">{p.quantity_on_hand}</span>
                )}
              </button>
            ))
          ) : (
            <p className="p-3 text-sm text-muted-foreground">No products found.</p>
          )}
        </div>
      )}
    </div>
  );
}
