import * as React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Boxes, Search, Landmark, ScrollText, Truck, CalendarClock } from "lucide-react";
import { inventoryApi } from "./api";
import { money } from "@/lib/format";
import { useDebounce } from "@/lib/hooks";
import { useTenant } from "@/features/tenancy/TenantContext";
import { PageHeader } from "@/components/common/PageHeader";
import { Pagination } from "@/components/common/Pagination";
import { EmptyState, ErrorState } from "@/components/common/states";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { PageLoader } from "@/components/ui/spinner";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ProductFormDialog } from "./components/ProductFormDialog";
import { ReceiveStockDialog } from "./components/ReceiveStockDialog";

export function ProductsListPage() {
  const navigate = useNavigate();
  const { current } = useTenant();
  const currency = current?.currency;
  const [page, setPage] = React.useState(1);
  const [searchInput, setSearchInput] = React.useState("");
  const [lowStockOnly, setLowStockOnly] = React.useState(false);
  const search = useDebounce(searchInput, 350);

  function handleSearch(value: string) {
    setSearchInput(value);
    setPage(1);
  }

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["products", { search, page, lowStockOnly }],
    queryFn: () =>
      lowStockOnly
        ? inventoryApi.lowStock({ page })
        : inventoryApi.listProducts({ search, page, ordering: "name" }),
    placeholderData: (prev) => prev,
  });

  return (
    <div>
      <PageHeader
        title="Inventory"
        description="Products, stock levels and replenishment."
        actions={
          <div className="flex flex-wrap gap-2">
            <Button asChild variant="outline">
              <Link to="/inventory/suppliers">
                <Truck className="size-4" /> Suppliers
              </Link>
            </Button>
            <Button asChild variant="outline">
              <Link to="/inventory/purchase-orders">
                <ScrollText className="size-4" /> Purchase orders
              </Link>
            </Button>
            <Button asChild variant="outline">
              <Link to="/inventory/ledger">
                <Landmark className="size-4" /> Stock ledger
              </Link>
            </Button>
            <Button asChild variant="outline">
              <Link to="/inventory/expiring-batches">
                <CalendarClock className="size-4" /> Expiring batches
              </Link>
            </Button>
            <ReceiveStockDialog variant="outline" />
            <ProductFormDialog />
          </div>
        }
      />

      <div className="mb-4 flex flex-wrap items-center gap-3">
        <div className="relative max-w-md flex-1">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search by name, SKU or barcode…"
            className="pl-9"
            value={searchInput}
            onChange={(e) => handleSearch(e.target.value)}
            disabled={lowStockOnly}
          />
        </div>
        <Button
          variant={lowStockOnly ? "default" : "outline"}
          onClick={() => {
            setLowStockOnly((v) => !v);
            setPage(1);
          }}
        >
          Low stock only
        </Button>
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
                  <TableHead>SKU</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead className="text-right">On hand</TableHead>
                  <TableHead className="text-right">Reorder</TableHead>
                  <TableHead className="text-right">Sale price</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.results.map((p) => {
                  const low = p.quantity_on_hand <= Number(p.reorder_level);
                  return (
                    <TableRow
                      key={p.id}
                      className="cursor-pointer"
                      onClick={() => navigate(`/inventory/products/${p.id}`)}
                    >
                      <TableCell className="font-mono text-xs">{p.sku}</TableCell>
                      <TableCell className="font-medium">{p.name}</TableCell>
                      <TableCell>
                        {p.is_drug ? (
                          <Badge variant="secondary">Drug</Badge>
                        ) : (
                          <Badge variant="outline">Good</Badge>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        <span className={low ? "font-semibold text-warning" : ""}>
                          {p.quantity_on_hand}
                        </span>
                      </TableCell>
                      <TableCell className="text-right text-muted-foreground">
                        {p.reorder_level}
                      </TableCell>
                      <TableCell className="text-right">{money(p.sale_price, currency)}</TableCell>
                    </TableRow>
                  );
                })}
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
            icon={<Boxes className="size-8" />}
            title={lowStockOnly ? "No low-stock products" : search ? "No matching products" : "No products yet"}
            description={lowStockOnly ? "Everything is above its reorder level." : undefined}
            action={!lowStockOnly && !search ? <ProductFormDialog /> : undefined}
          />
        )}
      </Card>
    </div>
  );
}
