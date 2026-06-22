import * as React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, FolderPlus, Layers } from "lucide-react";
import { emrApi } from "../api";
import { ApiError } from "@/lib/api/types";
import { useAuth } from "@/features/auth/AuthContext";
import { PageHeader } from "@/components/common/PageHeader";
import { EmptyState, ErrorState } from "@/components/common/states";
import { useToast } from "@/components/ui/toast";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { PageLoader } from "@/components/ui/spinner";
import { Spinner } from "@/components/ui/spinner";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export function CohortsListPage() {
  const navigate = useNavigate();
  const { can } = useAuth();
  const canManage = can("Manage Cohorts");

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["cohorts"],
    queryFn: () => emrApi.listCohorts({ page_size: 100 }),
  });

  return (
    <div>
      <Button variant="ghost" size="sm" asChild className="mb-2 -ml-2">
        <Link to="/emr/patients">
          <ArrowLeft className="size-4" /> Back to patients
        </Link>
      </Button>

      <PageHeader
        title="Cohorts"
        description="Group patients for outreach, reporting, or care coordination."
        actions={canManage && <CreateCohortDialog />}
      />

      <Card>
        {isLoading ? (
          <PageLoader />
        ) : isError ? (
          <ErrorState error={error} onRetry={refetch} />
        ) : data && data.results.length > 0 ? (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Description</TableHead>
                <TableHead>Members</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.results.map((cohort) => (
                <TableRow
                  key={cohort.id}
                  className="cursor-pointer"
                  onClick={() => navigate(`/emr/cohorts/${cohort.id}`)}
                >
                  <TableCell className="font-medium">{cohort.name}</TableCell>
                  <TableCell className="text-muted-foreground">{cohort.description || "—"}</TableCell>
                  <TableCell>{cohort.member_count}</TableCell>
                  <TableCell>
                    {cohort.retired ? (
                      <Badge variant="secondary">Retired</Badge>
                    ) : (
                      <Badge variant="success">Active</Badge>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        ) : (
          <EmptyState
            icon={<Layers className="size-8" />}
            title="No cohorts yet"
            description="Create a cohort to group patients for a program or campaign."
            action={canManage ? <CreateCohortDialog /> : undefined}
          />
        )}
      </Card>
    </div>
  );
}

function CreateCohortDialog() {
  const [open, setOpen] = React.useState(false);
  const [name, setName] = React.useState("");
  const [description, setDescription] = React.useState("");
  const [formError, setFormError] = React.useState<string | null>(null);

  const queryClient = useQueryClient();
  const { toast } = useToast();
  const navigate = useNavigate();

  function reset() {
    setName("");
    setDescription("");
    setFormError(null);
  }

  const create = useMutation({
    mutationFn: () => emrApi.createCohort({ name, description }),
    onSuccess: (cohort) => {
      queryClient.invalidateQueries({ queryKey: ["cohorts"] });
      toast({ title: "Cohort created", variant: "success" });
      setOpen(false);
      reset();
      navigate(`/emr/cohorts/${cohort.id}`);
    },
    onError: (err) =>
      setFormError(err instanceof ApiError ? err.toUserMessage() : "Could not create cohort."),
  });

  function submit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    if (!name) {
      setFormError("Cohort name is required.");
      return;
    }
    create.mutate();
  }

  return (
    <Dialog open={open} onOpenChange={(o) => { setOpen(o); if (!o) reset(); }}>
      <DialogTrigger asChild>
        <Button>
          <FolderPlus className="size-4" /> New cohort
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create cohort</DialogTitle>
        </DialogHeader>
        <form onSubmit={submit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="cohort-name">Name *</Label>
            <Input id="cohort-name" value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="cohort-description">Description</Label>
            <textarea
              id="cohort-description"
              className="flex min-h-16 w-full rounded-md border border-input bg-card px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>
          {formError && (
            <p className="whitespace-pre-line rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {formError}
            </p>
          )}
          <DialogFooter>
            <Button type="submit" disabled={create.isPending}>
              {create.isPending ? <Spinner className="size-4" /> : "Create"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
