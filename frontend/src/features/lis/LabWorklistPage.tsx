import * as React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { FlaskConical, Plus, FileText } from "lucide-react";
import { lisApi } from "./api";
import { useLabTests } from "./queries";
import { formatDateTime } from "@/lib/format";
import { PageHeader } from "@/components/common/PageHeader";
import { Pagination } from "@/components/common/Pagination";
import { EmptyState, ErrorState } from "@/components/common/states";
import { StatusBadge } from "@/components/common/StatusBadge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { PageLoader } from "@/components/ui/spinner";
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

// Sentinel filter keys → the fulfiller_status query value they map to.
const STATUS_FILTERS: { key: string; label: string; query?: string }[] = [
  { key: "ALL", label: "All orders" },
  { key: "NEW", label: "New (unfulfilled)", query: "" },
  { key: "IN_PROGRESS", label: "In progress", query: "IN_PROGRESS" },
  { key: "COMPLETED", label: "Completed", query: "COMPLETED" },
];

export function LabWorklistPage() {
  const navigate = useNavigate();
  const tests = useLabTests();
  const [page, setPage] = React.useState(1);
  const [statusKey, setStatusKey] = React.useState("ALL");
  const activeFilter = STATUS_FILTERS.find((f) => f.key === statusKey) ?? STATUS_FILTERS[0];

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["lab-orders", { page, statusKey }],
    queryFn: () =>
      lisApi.listOrders({
        page,
        ordering: "-date_activated",
        ...(activeFilter.query !== undefined ? { fulfiller_status: activeFilter.query } : {}),
      }),
    placeholderData: (prev) => prev,
  });

  return (
    <div>
      <PageHeader
        title="Laboratory worklist"
        description="Track lab orders from request through result release."
        actions={
          <Button asChild>
            <Link to="/lis/orders/new">
              <Plus className="size-4" /> New lab order
            </Link>
          </Button>
        }
      />

      <div className="mb-4 flex flex-wrap items-center gap-3">
        <Select
          value={statusKey}
          onValueChange={(v) => {
            setStatusKey(v);
            setPage(1);
          }}
        >
          <SelectTrigger className="w-56">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {STATUS_FILTERS.map((f) => (
              <SelectItem key={f.key} value={f.key}>
                {f.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Button asChild variant="outline">
          <Link to="/lis/catalog">
            <FileText className="size-4" /> Test catalog
          </Link>
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
                  <TableHead>Order #</TableHead>
                  <TableHead>Test</TableHead>
                  <TableHead>Ordered</TableHead>
                  <TableHead>Urgency</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.results.map((order) => (
                  <TableRow
                    key={order.id}
                    className="cursor-pointer"
                    onClick={() => navigate(`/lis/orders/${order.id}`)}
                  >
                    <TableCell className="font-mono text-xs">{order.order_number}</TableCell>
                    <TableCell className="font-medium">
                      {tests.data?.byId.get(order.lab_test)?.name ?? `Test #${order.lab_test}`}
                    </TableCell>
                    <TableCell>{formatDateTime(order.date_activated)}</TableCell>
                    <TableCell>{order.urgency || "Routine"}</TableCell>
                    <TableCell>
                      <StatusBadge status={order.fulfiller_status || "PENDING"} />
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
            icon={<FlaskConical className="size-8" />}
            title="No lab orders"
            description="Create a lab order to start the workflow."
            action={
              <Button asChild>
                <Link to="/lis/orders/new">
                  <Plus className="size-4" /> New lab order
                </Link>
              </Button>
            }
          />
        )}
      </Card>
    </div>
  );
}
