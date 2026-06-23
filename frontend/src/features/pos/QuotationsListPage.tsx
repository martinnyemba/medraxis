import * as React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { FileText, Plus, ShoppingCart } from "lucide-react";
import { posApi } from "./api";
import { money, formatDate } from "@/lib/format";
import { useTenant } from "@/features/tenancy/TenantContext";
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

export function QuotationsListPage() {
  const navigate = useNavigate();
  const { current } = useTenant();
  const [page, setPage] = React.useState(1);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["quotations", { page }],
    queryFn: () => posApi.listQuotations({ page, ordering: "-created_at" }),
    placeholderData: (prev) => prev,
  });

  return (
    <div>
      <PageHeader
        title="Quotations"
        description="Non-binding estimates that convert into a sale once accepted."
        actions={
          <div className="flex gap-2">
            <Button asChild variant="outline">
              <Link to="/pos/sales">
                <ShoppingCart className="size-4" /> Sales
              </Link>
            </Button>
            <Button asChild>
              <Link to="/pos/quotations/new">
                <Plus className="size-4" /> New quotation
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
                  <TableHead>Quotation</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Valid until</TableHead>
                  <TableHead className="text-right">Total</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.results.map((q) => (
                  <TableRow
                    key={q.id}
                    className="cursor-pointer"
                    onClick={() => navigate(`/pos/quotations/${q.id}`)}
                  >
                    <TableCell className="font-mono text-xs">{q.quotation_number}</TableCell>
                    <TableCell>{formatDate(q.created_at)}</TableCell>
                    <TableCell>{formatDate(q.valid_until)}</TableCell>
                    <TableCell className="text-right font-medium">
                      {money(q.grand_total, current?.currency)}
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={q.status} />
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
            title="No quotations"
            description="Create an estimate to quote a customer before they commit."
            action={
              <Button asChild>
                <Link to="/pos/quotations/new">
                  <Plus className="size-4" /> New quotation
                </Link>
              </Button>
            }
          />
        )}
      </Card>
    </div>
  );
}
