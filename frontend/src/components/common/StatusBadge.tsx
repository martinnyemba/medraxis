import { Badge, type BadgeProps } from "@/components/ui/badge";

type Variant = NonNullable<BadgeProps["variant"]>;

/** Map a workflow status string to a badge variant + label. */
const STATUS_STYLES: Record<string, { variant: Variant; label?: string }> = {
  // Lab result / order
  PENDING: { variant: "secondary" },
  ENTERED: { variant: "warning" },
  VERIFIED: { variant: "default" },
  RELEASED: { variant: "success" },
  REJECTED: { variant: "destructive" },
  // Specimen
  ORDERED: { variant: "secondary" },
  COLLECTED: { variant: "warning" },
  RECEIVED: { variant: "default" },
  IN_PROGRESS: { variant: "warning", label: "In progress" },
  DISPOSED: { variant: "secondary" },
  // Order fulfiller
  EXCEPTION: { variant: "destructive" },
  COMPLETED: { variant: "success" },
  DECLINED: { variant: "destructive" },
  // Sales / quotation / payment
  DRAFT: { variant: "secondary" },
  PARTIALLY_PAID: { variant: "warning", label: "Partially paid" },
  PAID: { variant: "success" },
  VOID: { variant: "destructive" },
  REFUNDED: { variant: "secondary" },
  SENT: { variant: "default" },
  ACCEPTED: { variant: "success" },
  CONVERTED: { variant: "success" },
  EXPIRED: { variant: "secondary" },
  CANCELLED: { variant: "destructive" },
  FAILED: { variant: "destructive" },
};

function humanize(status: string): string {
  return status
    .toLowerCase()
    .replace(/_/g, " ")
    .replace(/^\w/, (c) => c.toUpperCase());
}

export function StatusBadge({ status }: { status: string }) {
  if (!status) return <Badge variant="secondary">—</Badge>;
  const style = STATUS_STYLES[status] ?? { variant: "secondary" as Variant };
  return <Badge variant={style.variant}>{style.label ?? humanize(status)}</Badge>;
}
