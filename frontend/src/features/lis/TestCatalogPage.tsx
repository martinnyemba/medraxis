import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { FlaskConical, Search } from "lucide-react";
import { lisApi } from "./api";
import { useLabSections } from "./queries";
import { useDebounce } from "@/lib/hooks";
import { PageHeader } from "@/components/common/PageHeader";
import { Pagination } from "@/components/common/Pagination";
import { EmptyState, ErrorState } from "@/components/common/states";
import { LisTabs } from "./components/LisTabs";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { PageLoader } from "@/components/ui/spinner";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export function TestCatalogPage() {
  const sections = useLabSections();
  const [page, setPage] = React.useState(1);
  const [searchInput, setSearchInput] = React.useState("");
  const search = useDebounce(searchInput, 350);

  function handleSearch(value: string) {
    setSearchInput(value);
    setPage(1);
  }

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["lab-tests", { search, page }],
    queryFn: () => lisApi.listTests({ search, page }),
    placeholderData: (prev) => prev,
  });

  const sectionName = (id: number) => sections.data?.find((s) => s.id === id)?.name ?? `#${id}`;

  return (
    <div>
      <PageHeader title="Test catalog" description="Orderable tests and panels." />

      <LisTabs />

      <div className="mb-4 relative max-w-md">
        <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Search by name, code or LOINC…"
          className="pl-9"
          value={searchInput}
          onChange={(e) => handleSearch(e.target.value)}
        />
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
                  <TableHead>Code</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Section</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>TAT</TableHead>
                  <TableHead className="text-right">Price</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.results.map((t) => (
                  <TableRow key={t.id}>
                    <TableCell className="font-mono text-xs">{t.test_code}</TableCell>
                    <TableCell className="font-medium">{t.name}</TableCell>
                    <TableCell>{sectionName(t.section)}</TableCell>
                    <TableCell>
                      {t.is_panel ? (
                        <Badge variant="secondary">Panel</Badge>
                      ) : (
                        <Badge variant="outline">Single</Badge>
                      )}
                    </TableCell>
                    <TableCell>{t.turnaround_hours}h</TableCell>
                    <TableCell className="text-right">{t.price}</TableCell>
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
          <EmptyState icon={<FlaskConical className="size-8" />} title="No tests found" />
        )}
      </Card>
    </div>
  );
}
