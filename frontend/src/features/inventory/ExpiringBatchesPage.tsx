import * as React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, CalendarClock } from "lucide-react";
import { inventoryApi } from "./api";
import { formatDate, money } from "@/lib/format";
import { PageHeader } from "@/components/common/PageHeader";
import { Pagination } from "@/components/common/Pagination";
import { EmptyState, ErrorState } from "@/components/common/states";
import { Button } from "@/components/ui/button";
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

const WINDOWS = [
  { label: "30 days", value: 30 },
  { label: "90 days", value: 90 },
  { label: "180 days", value: 180 },
];

function daysUntil(expiryDate: string | null): number | null {
  if (!expiryDate) return null;
  const ms = new Date(expiryDate).getTime() - Date.now();
  return Math.ceil(ms / (1000 * 60 * 60 * 24));
}

export function ExpiringBatchesPage() {
  const navigate = useNavigate();
  const [page, setPage] = React.useState(1);
  const [days, setDays] = React.useState(90);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["expiring-batches", { page, days }],
    queryFn: () => inventoryApi.expiringBatches({ page, days }),
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
        title="Expiring batches"
        description="Stock batches nearing their expiry date — review before they go to waste."
      />

      <div className="mb-4 flex flex-wrap items-center gap-2">
        {WINDOWS.map((w) => (
          <Button
            key={w.value}
            variant={days === w.value ? "default" : "outline"}
            onClick={() => {
              setDays(w.value);
              setPage(1);
            }}
          >
            {w.label}
          </Button>
        ))}
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
                  <TableHead>Product</TableHead>
                  <TableHead>Batch #</TableHead>
                  <TableHead>Expiry date</TableHead>
                  <TableHead className="text-right">On hand</TableHead>
                  <TableHead className="text-right">Cost price</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.results.map((b) => {
                  const remaining = daysUntil(b.expiry_date);
                  return (
                    <TableRow
                      key={b.id}
                      className="cursor-pointer"
                      onClick={() => navigate(`/inventory/products/${b.product}`)}
                    >
                      <TableCell className="font-medium">{b.product_name}</TableCell>
                      <TableCell className="font-mono text-xs">{b.batch_number || "—"}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {formatDate(b.expiry_date)}
                          {remaining !== null && (
                            <Badge variant={remaining <= 30 ? "destructive" : "warning"}>
                              {remaining <= 0 ? "Expired" : `${remaining}d left`}
                            </Badge>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="text-right">{b.quantity_on_hand}</TableCell>
                      <TableCell className="text-right">{money(b.cost_price)}</TableCell>
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
            icon={<CalendarClock className="size-8" />}
            title="No batches expiring soon"
            description={`Nothing is due to expire within ${days} days.`}
          />
        )}
      </Card>
    </div>
  );
}
