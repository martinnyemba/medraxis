import * as React from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, BookOpen, Search } from "lucide-react";
import { financeApi } from "./api";
import type { PartyType } from "./types";
import { inventoryApi } from "@/features/inventory/api";
import { posApi } from "@/features/pos/api";
import { money, formatDate } from "@/lib/format";
import { PageHeader } from "@/components/common/PageHeader";
import { EmptyState, ErrorState } from "@/components/common/states";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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

const PARTY_TYPES: { value: PartyType; label: string }[] = [
  { value: "customer", label: "Customer" },
  { value: "supplier", label: "Supplier" },
];

export function PartyLedgerPage() {
  const [partyType, setPartyType] = React.useState<PartyType>("supplier");
  const [partyId, setPartyId] = React.useState("");
  const [lookedUp, setLookedUp] = React.useState<{ type: PartyType; id: number } | null>(null);

  const suppliers = useQuery({
    queryKey: ["suppliers", { all: true }],
    queryFn: () => inventoryApi.listSuppliers({ page_size: 200 }),
    enabled: partyType === "supplier",
    select: (p) => p.results,
  });
  const customers = useQuery({
    queryKey: ["customers", { all: true }],
    queryFn: () => posApi.listCustomers({ page_size: 200 }),
    enabled: partyType === "customer",
    select: (p) => p.results,
  });

  const parties = partyType === "supplier" ? suppliers.data : customers.data;

  const statement = useQuery({
    queryKey: ["finance", "party-ledger", lookedUp],
    queryFn: () => financeApi.partyStatement(lookedUp!.type, lookedUp!.id),
    enabled: !!lookedUp,
  });

  function lookup() {
    if (!partyId) return;
    setLookedUp({ type: partyType, id: Number(partyId) });
  }

  return (
    <div>
      <Button variant="ghost" size="sm" asChild className="mb-2 -ml-2">
        <Link to="/finance/accounts">
          <ArrowLeft className="size-4" /> Back to finance
        </Link>
      </Button>
      <PageHeader
        title="Party ledger"
        description="Outstanding receivable/payable balance and statement for a customer or supplier."
      />

      <Card className="mb-4">
        <CardContent className="flex flex-wrap items-end gap-4 pt-6">
          <div className="space-y-2">
            <Label>Party type</Label>
            <Select
              value={partyType}
              onValueChange={(v) => {
                setPartyType(v as PartyType);
                setPartyId("");
              }}
            >
              <SelectTrigger className="w-44">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {PARTY_TYPES.map((t) => (
                  <SelectItem key={t.value} value={t.value}>
                    {t.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>{partyType === "supplier" ? "Supplier" : "Customer"}</Label>
            <Select value={partyId} onValueChange={setPartyId}>
              <SelectTrigger className="w-64">
                <SelectValue placeholder="Select" />
              </SelectTrigger>
              <SelectContent>
                {parties?.map((p) => (
                  <SelectItem key={p.id} value={String(p.id)}>
                    {p.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <Button onClick={lookup} disabled={!partyId}>
            <Search className="size-4" /> Look up
          </Button>
        </CardContent>
      </Card>

      {!lookedUp ? (
        <EmptyState icon={<BookOpen className="size-8" />} title="Select a party to view its ledger" />
      ) : statement.isLoading ? (
        <PageLoader />
      ) : statement.isError ? (
        <ErrorState error={statement.error} onRetry={statement.refetch} />
      ) : statement.data ? (
        <>
          <Card className="mb-4">
            <CardHeader>
              <CardTitle className="text-base">Outstanding balance</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-semibold">{money(statement.data.balance)}</p>
              <p className="text-sm text-muted-foreground">
                Positive means the party owes money; negative means there is a credit balance.
              </p>
            </CardContent>
          </Card>

          <Card>
            {statement.data.entries.length > 0 ? (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Narration</TableHead>
                    <TableHead className="text-right">Debit</TableHead>
                    <TableHead className="text-right">Credit</TableHead>
                    <TableHead className="text-right">Balance</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {statement.data.entries.map((e) => (
                    <TableRow key={e.id}>
                      <TableCell>{formatDate(e.entry_date)}</TableCell>
                      <TableCell>{e.entry_type.replace(/_/g, " ")}</TableCell>
                      <TableCell className="text-muted-foreground">{e.narration || "—"}</TableCell>
                      <TableCell className="text-right">{Number(e.debit) ? money(e.debit) : "—"}</TableCell>
                      <TableCell className="text-right">{Number(e.credit) ? money(e.credit) : "—"}</TableCell>
                      <TableCell className="text-right">{money(e.balance)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : (
              <p className="p-6 text-sm text-muted-foreground">No ledger entries yet.</p>
            )}
          </Card>
        </>
      ) : null}
    </div>
  );
}
