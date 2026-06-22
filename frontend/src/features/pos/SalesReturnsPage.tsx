import * as React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, RotateCcw, Undo2 } from "lucide-react";
import { posApi } from "./api";
import { ApiError } from "@/lib/api/types";
import { money, formatDate } from "@/lib/format";
import { useToast } from "@/components/ui/toast";
import { PageHeader } from "@/components/common/PageHeader";
import { Pagination } from "@/components/common/Pagination";
import { EmptyState, ErrorState } from "@/components/common/states";
import { StatusBadge } from "@/components/common/StatusBadge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { PageLoader, Spinner } from "@/components/ui/spinner";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export function SalesReturnsPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [page, setPage] = React.useState(1);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["sales-returns", { page }],
    queryFn: () => posApi.listSalesReturns({ page, ordering: "-return_date" }),
    placeholderData: (prev) => prev,
  });

  const process = useMutation({
    mutationFn: (id: number) => posApi.processSalesReturn(id),
    onSuccess: () => {
      toast({ title: "Return processed — stock and ledger updated", variant: "success" });
      queryClient.invalidateQueries({ queryKey: ["sales-returns"] });
    },
    onError: (err) =>
      toast({
        title: "Could not process return",
        description: err instanceof ApiError ? err.toUserMessage() : undefined,
        variant: "error",
      }),
  });

  return (
    <div>
      <Button variant="ghost" size="sm" asChild className="mb-2 -ml-2">
        <Link to="/pos/sales">
          <ArrowLeft className="size-4" /> Back to sales
        </Link>
      </Button>
      <PageHeader
        title="Sales returns"
        description="Credit notes for returned goods — restocks inventory and credits the billing party."
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
                  <TableHead>Return #</TableHead>
                  <TableHead>Invoice</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead className="text-right">Total</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.results.map((sr) => (
                  <TableRow key={sr.id}>
                    <TableCell className="font-mono text-xs">{sr.return_number}</TableCell>
                    <TableCell>
                      <button
                        className="text-primary hover:underline"
                        onClick={() => navigate(`/pos/sales/${sr.sale}`)}
                      >
                        {sr.sale_invoice_number}
                      </button>
                    </TableCell>
                    <TableCell>{formatDate(sr.return_date)}</TableCell>
                    <TableCell className="text-right font-medium">{money(sr.total)}</TableCell>
                    <TableCell>
                      <StatusBadge status={sr.status} />
                    </TableCell>
                    <TableCell className="text-right">
                      {sr.status === "DRAFT" && (
                        <Button
                          size="sm"
                          variant="outline"
                          disabled={process.isPending}
                          onClick={() => process.mutate(sr.id)}
                        >
                          {process.isPending ? (
                            <Spinner className="size-4" />
                          ) : (
                            <Undo2 className="size-4" />
                          )}
                          Process
                        </Button>
                      )}
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
            icon={<RotateCcw className="size-8" />}
            title="No sales returns yet"
            description="Returns created from a completed sale will appear here."
          />
        )}
      </Card>
    </div>
  );
}
