import * as React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Pill, Plus } from "lucide-react";
import { pharmacyApi } from "./api";
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

const STATUS_FILTERS: { key: string; label: string; query?: string }[] = [
  { key: "ALL", label: "All prescriptions" },
  { key: "NEW", label: "To dispense", query: "" },
  { key: "COMPLETED", label: "Dispensed", query: "COMPLETED" },
];

export function PrescriptionsListPage() {
  const navigate = useNavigate();
  const [page, setPage] = React.useState(1);
  const [statusKey, setStatusKey] = React.useState("ALL");
  const activeFilter = STATUS_FILTERS.find((f) => f.key === statusKey) ?? STATUS_FILTERS[0];

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["drug-orders", { page, statusKey }],
    queryFn: () =>
      pharmacyApi.listDrugOrders({
        page,
        ordering: "-date_activated",
        ...(activeFilter.query !== undefined ? { fulfiller_status: activeFilter.query } : {}),
      }),
    placeholderData: (prev) => prev,
  });

  return (
    <div>
      <PageHeader
        title="Prescriptions"
        description="Medication orders and their dispensing status."
        actions={
          <Button asChild>
            <Link to="/pharmacy/prescriptions/new">
              <Plus className="size-4" /> New prescription
            </Link>
          </Button>
        }
      />

      <div className="mb-4">
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
                  <TableHead>Drug</TableHead>
                  <TableHead>Dosing</TableHead>
                  <TableHead className="text-right">Qty / Dispensed</TableHead>
                  <TableHead>Ordered</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.results.map((rx) => (
                  <TableRow
                    key={rx.id}
                    className="cursor-pointer"
                    onClick={() => navigate(`/pharmacy/prescriptions/${rx.id}`)}
                  >
                    <TableCell className="font-mono text-xs">{rx.order_number}</TableCell>
                    <TableCell className="font-medium">{rx.drug_name}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {[rx.dose && `${rx.dose}${rx.dose_units}`, rx.frequency, rx.route]
                        .filter(Boolean)
                        .join(" · ") || "—"}
                    </TableCell>
                    <TableCell className="text-right">
                      {rx.quantity_dispensed} / {rx.quantity}
                    </TableCell>
                    <TableCell>{formatDateTime(rx.date_activated)}</TableCell>
                    <TableCell>
                      <StatusBadge status={rx.fulfiller_status || "PENDING"} />
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
            icon={<Pill className="size-8" />}
            title="No prescriptions"
            description="Create a prescription to start the dispensing workflow."
            action={
              <Button asChild>
                <Link to="/pharmacy/prescriptions/new">
                  <Plus className="size-4" /> New prescription
                </Link>
              </Button>
            }
          />
        )}
      </Card>
    </div>
  );
}
