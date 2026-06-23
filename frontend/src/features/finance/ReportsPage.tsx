import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { BarChart3, BookOpen, Scale } from "lucide-react";
import { financeApi } from "./api";
import { money, formatDateTime } from "@/lib/format";
import { useTenant } from "@/features/tenancy/TenantContext";
import { PageHeader } from "@/components/common/PageHeader";
import { ErrorState } from "@/components/common/states";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { PageLoader } from "@/components/ui/spinner";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

function today() {
  return new Date().toISOString().slice(0, 10);
}
function monthStart() {
  const d = new Date();
  return new Date(d.getFullYear(), d.getMonth(), 1).toISOString().slice(0, 10);
}

export function ReportsPage() {
  return (
    <div>
      <PageHeader
        title="Business reports"
        description="Period summary, daily cash book and outstanding balances."
      />
      <Tabs defaultValue="summary">
        <TabsList>
          <TabsTrigger value="summary">
            <BarChart3 className="size-4" /> Summary
          </TabsTrigger>
          <TabsTrigger value="daybook">
            <BookOpen className="size-4" /> Day book
          </TabsTrigger>
          <TabsTrigger value="outstanding">
            <Scale className="size-4" /> Outstanding
          </TabsTrigger>
        </TabsList>
        <TabsContent value="summary">
          <SummaryTab />
        </TabsContent>
        <TabsContent value="daybook">
          <DayBookTab />
        </TabsContent>
        <TabsContent value="outstanding">
          <OutstandingTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}

function Stat({ label, value, accent }: { label: string; value: string; accent?: "pos" | "neg" }) {
  return (
    <Card>
      <CardContent className="pt-6">
        <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</p>
        <p
          className={
            "mt-1 text-2xl font-semibold " +
            (accent === "neg" ? "text-destructive" : accent === "pos" ? "text-success" : "")
          }
        >
          {value}
        </p>
      </CardContent>
    </Card>
  );
}

function SummaryTab() {
  const { current } = useTenant();
  const currency = current?.currency;
  const [from, setFrom] = React.useState(monthStart());
  const [to, setTo] = React.useState(today());

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["finance", "report-summary", { from, to }],
    queryFn: () => financeApi.reportSummary({ from, to }),
    placeholderData: (prev) => prev,
  });

  return (
    <div className="mt-4 space-y-4">
      <div className="flex flex-wrap items-end gap-3">
        <div className="space-y-1.5">
          <Label className="text-xs">From</Label>
          <Input type="date" value={from} onChange={(e) => setFrom(e.target.value)} />
        </div>
        <div className="space-y-1.5">
          <Label className="text-xs">To</Label>
          <Input type="date" value={to} onChange={(e) => setTo(e.target.value)} />
        </div>
      </div>

      {isLoading ? (
        <PageLoader />
      ) : isError ? (
        <ErrorState error={error} onRetry={refetch} />
      ) : data ? (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Stat label="Revenue billed" value={money(data.revenue, currency)} />
            <Stat label="Collected" value={money(data.collected, currency)} accent="pos" />
            <Stat label="Expenses" value={money(data.expenses, currency)} accent="neg" />
            <Stat
              label="Net cash"
              value={money(data.net_cash, currency)}
              accent={Number(data.net_cash) < 0 ? "neg" : "pos"}
            />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <Stat label="Sales count" value={String(data.sales_count)} />
            <Stat label="Supplier payments" value={money(data.supplier_payments, currency)} />
          </div>
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Expenses by category</CardTitle>
            </CardHeader>
            <CardContent>
              {data.expenses_by_category.length === 0 ? (
                <p className="text-sm text-muted-foreground">No expenses in this period.</p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Category</TableHead>
                      <TableHead className="text-right">Amount</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {data.expenses_by_category.map((row, i) => (
                      <TableRow key={i}>
                        <TableCell>{row.category ?? "Uncategorised"}</TableCell>
                        <TableCell className="text-right">{money(row.amount, currency)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </>
      ) : null}
    </div>
  );
}

function DayBookTab() {
  const { current } = useTenant();
  const currency = current?.currency;
  const [date, setDate] = React.useState(today());

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["finance", "report-daybook", { date }],
    queryFn: () => financeApi.reportDayBook(date),
    placeholderData: (prev) => prev,
  });

  return (
    <div className="mt-4 space-y-4">
      <div className="space-y-1.5">
        <Label className="text-xs">Date</Label>
        <Input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
      </div>

      {isLoading ? (
        <PageLoader />
      ) : isError ? (
        <ErrorState error={error} onRetry={refetch} />
      ) : data ? (
        <>
          <div className="grid gap-4 sm:grid-cols-3">
            <Stat label="Money in" value={money(data.money_in, currency)} accent="pos" />
            <Stat label="Money out" value={money(data.money_out, currency)} accent="neg" />
            <Stat
              label="Net"
              value={money(data.net, currency)}
              accent={Number(data.net) < 0 ? "neg" : "pos"}
            />
          </div>
          <Card>
            <CardContent className="pt-6">
              {data.entries.length === 0 ? (
                <p className="text-sm text-muted-foreground">No money movements on this day.</p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Time</TableHead>
                      <TableHead>Account</TableHead>
                      <TableHead>Reference</TableHead>
                      <TableHead>Direction</TableHead>
                      <TableHead className="text-right">Amount</TableHead>
                      <TableHead className="text-right">Balance</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {data.entries.map((e) => (
                      <TableRow key={e.id}>
                        <TableCell className="text-muted-foreground">
                          {formatDateTime(e.occurred_at)}
                        </TableCell>
                        <TableCell>{e.account}</TableCell>
                        <TableCell className="text-xs text-muted-foreground">
                          {[e.reference_type, e.reference_id].filter(Boolean).join(" ") ||
                            e.note ||
                            "—"}
                        </TableCell>
                        <TableCell>
                          {e.direction === "IN" ? (
                            <Badge variant="success">In</Badge>
                          ) : (
                            <Badge variant="warning">Out</Badge>
                          )}
                        </TableCell>
                        <TableCell className="text-right">{money(e.amount, currency)}</TableCell>
                        <TableCell className="text-right text-muted-foreground">
                          {money(e.balance_after, currency)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </>
      ) : null}
    </div>
  );
}

function OutstandingTab() {
  const { current } = useTenant();
  const currency = current?.currency;

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["finance", "report-outstanding"],
    queryFn: () => financeApi.reportOutstanding(),
  });

  if (isLoading) return <div className="mt-4"><PageLoader /></div>;
  if (isError) return <div className="mt-4"><ErrorState error={error} onRetry={refetch} /></div>;
  if (!data) return null;

  return (
    <div className="mt-4 grid gap-4 lg:grid-cols-2">
      <OutstandingCard
        title="Receivables (owed to us)"
        total={money(data.receivable_total, currency)}
        rows={data.receivables}
        currency={currency}
      />
      <OutstandingCard
        title="Payables (we owe)"
        total={money(data.payable_total, currency)}
        rows={data.payables}
        currency={currency}
      />
    </div>
  );
}

function OutstandingCard({
  title,
  total,
  rows,
  currency,
}: {
  title: string;
  total: string;
  rows: { party_id: number; party_name: string; party_type: string; balance: string }[];
  currency?: string;
}) {
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="text-base">{title}</CardTitle>
        <span className="text-lg font-semibold">{total}</span>
      </CardHeader>
      <CardContent>
        {rows.length === 0 ? (
          <p className="text-sm text-muted-foreground">Nothing outstanding.</p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Party</TableHead>
                <TableHead className="text-right">Balance</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((r) => (
                <TableRow key={`${r.party_type}-${r.party_id}`}>
                  <TableCell>
                    {r.party_name}{" "}
                    <span className="text-xs text-muted-foreground">({r.party_type})</span>
                  </TableCell>
                  <TableCell className="text-right font-medium">
                    {money(r.balance, currency)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
