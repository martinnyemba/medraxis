/** Notification domain types mirroring apps/notifications/api/serializers.py. */

export type NotificationChannel = "email" | "sms" | "in_app" | "whatsapp";
export type NotificationStatus = "pending" | "queued" | "sent" | "failed" | "read";

export interface Notification {
  id: number;
  channel: NotificationChannel;
  subject: string;
  body: string;
  status: NotificationStatus;
  scheduled_for: string | null;
  sent_at: string | null;
  created_at: string;
}
