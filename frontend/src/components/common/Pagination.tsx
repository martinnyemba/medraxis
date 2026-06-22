import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";

interface PaginationProps {
  page: number;
  totalPages: number;
  count: number;
  onPageChange: (page: number) => void;
}

export function Pagination({ page, totalPages, count, onPageChange }: PaginationProps) {
  if (count === 0) return null;
  return (
    <div className="flex items-center justify-between border-t px-1 py-3 text-sm text-muted-foreground">
      <span>
        Page {page} of {totalPages} · {count} record{count === 1 ? "" : "s"}
      </span>
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
        >
          <ChevronLeft className="size-4" /> Prev
        </Button>
        <Button
          variant="outline"
          size="sm"
          disabled={page >= totalPages}
          onClick={() => onPageChange(page + 1)}
        >
          Next <ChevronRight className="size-4" />
        </Button>
      </div>
    </div>
  );
}
