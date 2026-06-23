import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Mail, MessageCircle, Send, Smartphone, Globe } from "lucide-react";
import { lisApi } from "../api";
import type { DeliveryChannel, DeliveryRecipient, ReportDelivery } from "../types";
import { ApiError } from "@/lib/api/types";
import { formatDateTime } from "@/lib/format";
import { useToast } from "@/components/ui/toast";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Spinner } from "@/components/ui/spinner";
import { StatusBadge } from "@/components/common/StatusBadge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

const CHANNELS: { value: DeliveryChannel; label: string; icon: React.ReactNode }[] = [
  { value: "whatsapp", label: "WhatsApp", icon: <MessageCircle className="size-3.5" /> },
  { value: "sms", label: "SMS", icon: <Smartphone className="size-3.5" /> },
  { value: "email", label: "Email", icon: <Mail className="size-3.5" /> },
  { value: "portal", label: "Patient portal", icon: <Globe className="size-3.5" /> },
];

const RECIPIENTS: { value: DeliveryRecipient; label: string }[] = [
  { value: "PATIENT", label: "Patient" },
  { value: "REFERRER", label: "Referring doctor" },
  { value: "CLIENT", label: "B2B client" },
];

function channelMeta(channel: DeliveryChannel) {
  return CHANNELS.find((c) => c.value === channel) ?? CHANNELS[0];
}

/** Dispatch a finished report over WhatsApp/SMS/Email/portal and track delivery. */
export function ReportDeliveryPanel({ orderId }: { orderId: number }) {
  const { data, isLoading } = useQuery({
    queryKey: ["lab-deliveries", { order: orderId }],
    queryFn: () => lisApi.listDeliveries({ test_order: orderId, ordering: "-created_at" }),
  });

  const deliveries = data?.results ?? [];

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-2 text-base">
          <Send className="size-4 text-primary" /> Report delivery
        </CardTitle>
        <DispatchDialog orderId={orderId} />
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Loading deliveries…</p>
        ) : deliveries.length === 0 ? (
          <p className="py-2 text-sm text-muted-foreground">
            No report sent yet. Dispatch the report over WhatsApp, SMS, email or the patient portal.
          </p>
        ) : (
          <ul className="space-y-2">
            {deliveries.map((d) => (
              <DeliveryRow key={d.id} delivery={d} />
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

function DeliveryRow({ delivery }: { delivery: ReportDelivery }) {
  const meta = channelMeta(delivery.channel);
  return (
    <li className="flex flex-wrap items-center justify-between gap-3 rounded-md border p-3">
      <div className="space-y-0.5">
        <p className="flex items-center gap-1.5 text-sm font-medium">
          {meta.icon} {meta.label}
          <span className="text-muted-foreground">→ {delivery.recipient_type.toLowerCase()}</span>
        </p>
        <p className="text-xs text-muted-foreground">
          {delivery.recipient_address || "—"}
          {delivery.sent_at ? ` · ${formatDateTime(delivery.sent_at)}` : ""}
          {delivery.error ? ` · ${delivery.error}` : ""}
        </p>
      </div>
      <StatusBadge status={delivery.status} />
    </li>
  );
}

function DispatchDialog({ orderId }: { orderId: number }) {
  const [open, setOpen] = React.useState(false);
  const [channel, setChannel] = React.useState<DeliveryChannel>("whatsapp");
  const [recipientType, setRecipientType] = React.useState<DeliveryRecipient>("PATIENT");
  const [address, setAddress] = React.useState("");
  const [formError, setFormError] = React.useState<string | null>(null);
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const dispatch = useMutation({
    mutationFn: () =>
      lisApi.dispatchReport({
        test_order: orderId,
        channel,
        recipient_type: recipientType,
        recipient_address: address,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["lab-deliveries", { order: orderId }] });
      toast({ title: "Report dispatched", variant: "success" });
      setOpen(false);
      setAddress("");
    },
    onError: (err) =>
      setFormError(err instanceof ApiError ? err.toUserMessage() : "Could not dispatch report."),
  });

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm">
          <Send className="size-3" /> Send report
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Send report</DialogTitle>
        </DialogHeader>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            setFormError(null);
            dispatch.mutate();
          }}
          className="space-y-4"
        >
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label>Channel</Label>
              <Select value={channel} onValueChange={(v) => setChannel(v as DeliveryChannel)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {CHANNELS.map((c) => (
                    <SelectItem key={c.value} value={c.value}>
                      {c.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Recipient</Label>
              <Select
                value={recipientType}
                onValueChange={(v) => setRecipientType(v as DeliveryRecipient)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {RECIPIENTS.map((r) => (
                    <SelectItem key={r.value} value={r.value}>
                      {r.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="address">
              {channel === "email" ? "Email address" : "Phone / address"}
            </Label>
            <Input
              id="address"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              placeholder={
                channel === "email" ? "patient@example.com" : "+260…"
              }
            />
            <p className="text-xs text-muted-foreground">
              Leave blank to use the recipient's stored contact details.
            </p>
          </div>
          {formError && (
            <p className="whitespace-pre-line rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {formError}
            </p>
          )}
          <DialogFooter>
            <Button type="submit" disabled={dispatch.isPending}>
              {dispatch.isPending ? <Spinner className="size-4" /> : "Dispatch"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
