import { Bell, CheckCheck } from "lucide-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { notificationsApi } from "@/features/notifications/api";
import { formatDateTime } from "@/lib/format";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const POLL_INTERVAL = 30_000;

export function NotificationBell() {
  const queryClient = useQueryClient();

  const { data } = useQuery({
    queryKey: ["notifications", "unread"],
    queryFn: () => notificationsApi.unread({ page_size: 10 }),
    refetchInterval: POLL_INTERVAL,
  });

  const markRead = useMutation({
    mutationFn: (id: number) => notificationsApi.markRead(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });

  const notifications = data?.results ?? [];
  const unreadCount = data?.count ?? 0;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger className="relative flex size-9 items-center justify-center rounded-full text-muted-foreground outline-none hover:bg-accent hover:text-accent-foreground focus-visible:ring-2 focus-visible:ring-ring">
        <Bell className="size-5" />
        {unreadCount > 0 && (
          <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-destructive px-1 text-[10px] font-semibold leading-none text-destructive-foreground">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-80">
        <DropdownMenuLabel>Notifications</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {notifications.length === 0 ? (
          <p className="px-2 py-4 text-center text-sm text-muted-foreground">
            No new notifications
          </p>
        ) : (
          notifications.map((n) => (
            <DropdownMenuItem
              key={n.id}
              className="flex-col items-start gap-0.5 whitespace-normal"
              onClick={() => markRead.mutate(n.id)}
            >
              <div className="flex w-full items-start justify-between gap-2">
                <span className="text-sm font-medium">{n.subject || "Notification"}</span>
                <CheckCheck className="mt-0.5 size-3.5 shrink-0 text-muted-foreground" />
              </div>
              <p className="line-clamp-2 text-xs text-muted-foreground">{n.body}</p>
              <span className="text-[11px] text-muted-foreground">
                {formatDateTime(n.created_at)}
              </span>
            </DropdownMenuItem>
          ))
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
