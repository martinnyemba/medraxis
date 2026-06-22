import { api } from "@/lib/api/client";
import type { Paginated } from "@/lib/api/types";
import type { Notification } from "./types";

type ListParams = Record<string, string | number | boolean | undefined | null>;

export const notificationsApi = {
  list: (params?: ListParams) => api.get<Paginated<Notification>>("/notifications/", params),
  unread: (params?: ListParams) =>
    api.get<Paginated<Notification>>("/notifications/unread/", params),
  markRead: (id: number) => api.post<Notification>(`/notifications/${id}/mark_read/`),
};
