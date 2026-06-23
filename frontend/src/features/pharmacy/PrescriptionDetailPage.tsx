import * as React from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Ban, PackageMinus, Pill, Undo2 } from "lucide-react";
import { pharmacyApi } from "./api";
import { useLocations } from "@/features/emr/queries";
import { ApiError } from "@/lib/api/types";
import { money, formatDateTime } from "@/lib/format";
import { useToast } from "@/components/ui/toast";
import { PageHeader } from "@/components/common/PageHeader";
import { StatusBadge } from "@/components/common/StatusBadge";
import { ErrorState } from "@/components/common/states";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PageLoader, Spinner } from "@/components/ui/spinner";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export function PrescriptionDetailPage() {
  const { orderId } = useParams<{ orderId: string }>();
  const id = Number(orderId);
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const order = useQuery({
    queryKey: ["drug-order", id],
    queryFn: () => pharmacyApi.getDrugOrder(id),
    enabled: Number.isFinite(id),
  });

  const dispenses = useQuery({
    queryKey: ["dispenses", { order: id }],
    queryFn: () => pharmacyApi.listDispenses({ drug_order: id, ordering: "-created_at" }),
    enabled: Number.isFinite(id),
  });

  const discontinue = useMutation({
    mutationFn: () => pharmacyApi.discontinue(id),
    onSuccess: () => {
      toast({ title: "Prescription discontinued", variant: "success" });
      queryClient.invalidateQueries({ queryKey: ["drug-order", id] });
      queryClient.invalidateQueries({ queryKey: ["drug-orders"] });
    },
    onError: (err) =>
      toast({
        title: "Could not discontinue",
        description: err instanceof ApiError ? err.toUserMessage() : undefined,
        variant: "error",
      }),
  });

  if (order.isLoading) return <PageLoader />;
  if (order.isError || !order.data) return <ErrorState error={order.error} onRetry={order.refetch} />;

  const rx = order.data;
  const dispensed = Number(rx.quantity_dispensed);
  const remaining = Math.max(Number(rx.quantity) - dispensed, 0);
  const discontinued = rx.order_action === "DISCONTINUE" || rx.date_stopped != null;

  return (
    <div className="space-y-6">
      <div>
        <Button variant="ghost" size="sm" asChild className="mb-2 -ml-2">
          <Link to="/pharmacy/prescriptions">
            <ArrowLeft className="size-4" /> Back to prescriptions
          </Link>
        </Button>
        <PageHeader
          title={rx.drug_name}
          description={`Prescription ${rx.order_number}`}
          actions={
            <div className="flex items-center gap-2">
              {discontinued ? (
                <StatusBadge status="DISCONTINUE" />
              ) : remaining > 0 ? (
                <>
                  <Button
                    variant="outline"
                    onClick={() => discontinue.mutate()}
                    disabled={discontinue.isPending}
                  >
                    {discontinue.isPending ? <Spinner className="size-4" /> : <Ban className="size-4" />}
                    Discontinue
                  </Button>
                  <DispenseDialog orderId={rx.id} remaining={remaining} />
                </>
              ) : (
                <StatusBadge status="COMPLETED" />
              )}
            </div>
          }
        />
      </div>

      <Card>
        <CardContent className="grid gap-4 pt-6 sm:grid-cols-2 lg:grid-cols-4">
          <Field label="Status">
            <StatusBadge status={rx.fulfiller_status || "PENDING"} />
          </Field>
          <Field label="Dose">
            {rx.dose ? `${rx.dose} ${rx.dose_units}` : "—"}
          </Field>
          <Field label="Frequency">{rx.frequency || "—"}</Field>
          <Field label="Route">{rx.route || "—"}</Field>
          <Field label="Duration">
            {rx.duration ? `${rx.duration} ${rx.duration_units.toLowerCase()}` : "—"}
          </Field>
          <Field label="Quantity">{rx.quantity}</Field>
          <Field label="Dispensed">{dispensed}</Field>
          <Field label="Remaining">{remaining}</Field>
          {rx.dosing_instructions && (
            <div className="sm:col-span-2 lg:col-span-4">
              <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Instructions
              </p>
              <p className="text-sm">{rx.dosing_instructions}</p>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Pill className="size-4 text-primary" /> Dispensing history
          </CardTitle>
        </CardHeader>
        <CardContent>
          {dispenses.isLoading ? (
            <p className="text-sm text-muted-foreground">Loading…</p>
          ) : dispenses.data && dispenses.data.results.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Product</TableHead>
                  <TableHead className="text-right">Qty</TableHead>
                  <TableHead className="text-right">Total</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {dispenses.data.results.map((d) => (
                  <TableRow key={d.id}>
                    <TableCell>{formatDateTime(d.created_at)}</TableCell>
                    <TableCell>{d.product_name}</TableCell>
                    <TableCell className="text-right">{d.quantity}</TableCell>
                    <TableCell className="text-right">{money(d.line_total)}</TableCell>
                    <TableCell>
                      <StatusBadge status={d.status} />
                    </TableCell>
                    <TableCell className="text-right">
                      {d.status === "DISPENSED" && <ReverseButton dispenseId={d.id} orderId={id} />}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <p className="py-2 text-sm text-muted-foreground">
              Nothing dispensed yet. Use “Dispense” to issue stock against this prescription.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1">
      <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</p>
      <div className="text-sm font-medium">{children}</div>
    </div>
  );
}

function ReverseButton({ dispenseId, orderId }: { dispenseId: number; orderId: number }) {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const reverse = useMutation({
    mutationFn: () => pharmacyApi.reverseDispense(dispenseId),
    onSuccess: () => {
      toast({ title: "Dispense returned — stock restocked", variant: "success" });
      queryClient.invalidateQueries({ queryKey: ["dispenses", { order: orderId }] });
      queryClient.invalidateQueries({ queryKey: ["drug-order", orderId] });
    },
    onError: (err) =>
      toast({
        title: "Could not return dispense",
        description: err instanceof ApiError ? err.toUserMessage() : undefined,
        variant: "error",
      }),
  });
  return (
    <Button size="sm" variant="ghost" onClick={() => reverse.mutate()} disabled={reverse.isPending}>
      {reverse.isPending ? <Spinner className="size-3" /> : <Undo2 className="size-3" />}
      Return
    </Button>
  );
}

function DispenseDialog({ orderId, remaining }: { orderId: number; remaining: number }) {
  const [open, setOpen] = React.useState(false);
  const [locationId, setLocationId] = React.useState("");
  const [quantity, setQuantity] = React.useState(String(remaining));
  const [formError, setFormError] = React.useState<string | null>(null);

  const queryClient = useQueryClient();
  const { toast } = useToast();
  const locations = useLocations();

  React.useEffect(() => {
    if (open) {
      setQuantity(String(remaining));
      setFormError(null);
      if (!locationId && locations.data && locations.data.length > 0) {
        setLocationId(String(locations.data[0].id));
      }
    }
  }, [open, remaining, locationId, locations.data]);

  const dispense = useMutation({
    mutationFn: () =>
      pharmacyApi.dispense({
        drug_order: orderId,
        location: Number(locationId),
        quantity,
      }),
    onSuccess: () => {
      toast({ title: "Dispensed — stock issued", variant: "success" });
      queryClient.invalidateQueries({ queryKey: ["drug-order", orderId] });
      queryClient.invalidateQueries({ queryKey: ["dispenses", { order: orderId }] });
      queryClient.invalidateQueries({ queryKey: ["drug-orders"] });
      setOpen(false);
    },
    onError: (err) =>
      setFormError(err instanceof ApiError ? err.toUserMessage() : "Could not dispense."),
  });

  function submit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    if (!locationId) return setFormError("Select a location.");
    if (!quantity || Number(quantity) <= 0) return setFormError("Enter a valid quantity.");
    dispense.mutate();
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <PackageMinus className="size-4" /> Dispense
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Dispense medication</DialogTitle>
        </DialogHeader>
        <form onSubmit={submit} className="space-y-4">
          <div className="space-y-2">
            <Label>Dispense from location</Label>
            <Select value={locationId} onValueChange={setLocationId}>
              <SelectTrigger>
                <SelectValue placeholder="Select location" />
              </SelectTrigger>
              <SelectContent>
                {locations.data?.map((l) => (
                  <SelectItem key={l.id} value={String(l.id)}>
                    {l.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="qty">Quantity (remaining: {remaining})</Label>
            <Input
              id="qty"
              type="number"
              step="any"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
            />
          </div>
          {formError && (
            <p className="whitespace-pre-line rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {formError}
            </p>
          )}
          <DialogFooter>
            <Button type="submit" disabled={dispense.isPending}>
              {dispense.isPending ? <Spinner className="size-4" /> : "Dispense"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
