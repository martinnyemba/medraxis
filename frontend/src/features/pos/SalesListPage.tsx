import * as React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ShoppingCart, Plus, RotateCcw, Users } from "lucide-react";
import { posApi } from "./api";
import { money, formatDateTime } from "@/lib/format";
import { PageHeader } from "@/components/common/PageHeader";
import { Pagination } from "@/components/common/Pagination";
import { EmptyState, ErrorState } from "@/components/common/states";
import { StatusBadge } from "@/components/common/StatusBadge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { PageLoader } from "@/components/ui/spinner";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export function SalesListPage() {
  const navigate = useNavigate();
  const [page, setPage] = React.useState(1);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["sales", { page }],
    queryFn: () => posApi.listSales({ page, ordering: "-created_at" }),
    placeholderData: (prev) => prev,
  });

  return (
    <div>
      <PageHeader
        title="Sales"
        description="Point-of-sale invoices and their payment status."
        actions={
          <div className="flex gap-2">
            <Button asChild variant="outline">
              <Link to="/pos/returns">
                <RotateCcw className="size-4" /> Returns
              </Link>
            </Button>
            <Button asChild variant="outline">
              <Link to="/pos/customers">
                <Users className="size-4" /> Customers
              </Link>
            </Button>
            <Button asChild>
              <Link to="/pos/sales/new">
                <Plus className="size-4" /> New sale
              </Link>
            </Button>
          </div>
        }
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
                  <TableHead>Invoice</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Items</TableHead>
                  <TableHead className="text-right">Total</TableHead>
                  <TableHead className="text-right">Balance</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.results.map((sale) => (
                  <TableRow
                    key={sale.id}
                    className="cursor-pointer"
                    onClick={() => navigate(`/pos/sales/${sale.id}`)}
                  >
                    <TableCell className="font-mono text-xs">{sale.invoice_number}</TableCell>
                    <TableCell>{formatDateTime(sale.created_at)}</TableCell>
                    <TableCell>{sale.lines.length}</TableCell>
                    <TableCell className="text-right font-medium">
                      {money(sale.grand_total, sale.currency)}
                    </TableCell>
                    <TableCell className="text-right">
                      {money(sale.balance_due, sale.currency)}
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={sale.status} />
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
            icon={<ShoppingCart className="size-8" />}
            title="No sales yet"
            description="Ring up the first sale to get started."
            action={
              <Button asChild>
                <Link to="/pos/sales/new">
                  <Plus className="size-4" /> New sale
                </Link>
              </Button>
            }
          />
        )}
      </Card>
    </div>
  );
}
