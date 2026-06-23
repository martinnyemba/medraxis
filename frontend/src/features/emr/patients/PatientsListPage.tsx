import * as React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Layers, Search, UserPlus, Users } from "lucide-react";
import { emrApi } from "../api";
import { patientName, preferredIdentifier, genderLabel, ageFromBirthdate } from "@/lib/format";
import { useDebounce } from "@/lib/hooks";
import { useAuth } from "@/features/auth/AuthContext";
import { PageHeader } from "@/components/common/PageHeader";
import { Pagination } from "@/components/common/Pagination";
import { EmptyState, ErrorState } from "@/components/common/states";
import { Button } from "@/components/ui/button";
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

export function PatientsListPage() {
  const navigate = useNavigate();
  const { can } = useAuth();
  const [page, setPage] = React.useState(1);
  const [searchInput, setSearchInput] = React.useState("");
  const search = useDebounce(searchInput, 350);

  // Reset to the first page whenever the search term changes.
  function handleSearchChange(value: string) {
    setSearchInput(value);
    setPage(1);
  }

  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ["patients", { search, page }],
    queryFn: () => emrApi.listPatients({ search, page }),
    placeholderData: (prev) => prev,
  });

  const canRegister = can("Add Patients");

  return (
    <div>
      <PageHeader
        title="Patients"
        description="Register and search the patient master index."
        actions={
          <div className="flex items-center gap-2">
            <Button variant="outline" asChild>
              <Link to="/emr/cohorts">
                <Layers className="size-4" /> Cohorts
              </Link>
            </Button>
            {canRegister && (
              <Button asChild>
                <Link to="/emr/patients/new">
                  <UserPlus className="size-4" /> Register patient
                </Link>
              </Button>
            )}
          </div>
        }
      />

      <div className="mb-4 relative w-full sm:max-w-md">
        <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Search by name or identifier…"
          className="pl-9"
          value={searchInput}
          onChange={(e) => handleSearchChange(e.target.value)}
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
                  <TableHead>Identifier</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Gender</TableHead>
                  <TableHead>Age</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.results.map((patient) => {
                  const age = ageFromBirthdate(patient.birthdate);
                  return (
                    <TableRow
                      key={patient.id}
                      className="cursor-pointer"
                      onClick={() => navigate(`/emr/patients/${patient.id}`)}
                    >
                      <TableCell className="font-mono text-xs">
                        {preferredIdentifier(patient) ?? "—"}
                      </TableCell>
                      <TableCell className="font-medium">{patientName(patient)}</TableCell>
                      <TableCell>{genderLabel(patient.gender)}</TableCell>
                      <TableCell>{age !== null ? `${age} yr` : "—"}</TableCell>
                      <TableCell>
                        {patient.voided ? (
                          <Badge variant="destructive">Voided</Badge>
                        ) : (
                          <Badge variant="success">Active</Badge>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
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
          <EmptyState
            icon={<Users className="size-8" />}
            title={search ? "No matching patients" : "No patients yet"}
            description={
              search
                ? "Try a different name or identifier."
                : "Register the first patient to get started."
            }
            action={
              canRegister && !search ? (
                <Button asChild>
                  <Link to="/emr/patients/new">
                    <UserPlus className="size-4" /> Register patient
                  </Link>
                </Button>
              ) : undefined
            }
          />
        )}
      </Card>

      {isFetching && !isLoading && (
        <p className="mt-2 text-xs text-muted-foreground">Updating…</p>
      )}
    </div>
  );
}
