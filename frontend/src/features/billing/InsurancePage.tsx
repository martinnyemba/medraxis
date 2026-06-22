import * as React from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Plus, ShieldCheck } from "lucide-react";
import { billingApi } from "./api";
import { useInsuranceSchemes } from "./queries";
import type { InsuranceScheme, PatientInsurance } from "./types";
import { PatientCombobox } from "@/components/common/PatientCombobox";
import type { Patient } from "@/features/emr/types";
import { ApiError } from "@/lib/api/types";
import { formatDate } from "@/lib/format";
import { useToast } from "@/components/ui/toast";
import { PageHeader } from "@/components/common/PageHeader";
import { Pagination } from "@/components/common/Pagination";
import { EmptyState, ErrorState } from "@/components/common/states";
import { StatusBadge } from "@/components/common/StatusBadge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { PageLoader, Spinner } from "@/components/ui/spinner";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
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

export function InsurancePage() {
  return (
    <div>
      <Button variant="ghost" size="sm" asChild className="mb-2 -ml-2">
        <Link to="/billing/services">
          <ArrowLeft className="size-4" /> Back to billing
        </Link>
      </Button>
      <PageHeader
        title="Insurance"
        description="Payer schemes and patient policy enrolments used to route claims at the point of sale."
      />
      <Tabs defaultValue="schemes">
        <TabsList>
          <TabsTrigger value="schemes">Schemes</TabsTrigger>
          <TabsTrigger value="policies">Patient policies</TabsTrigger>
        </TabsList>
        <TabsContent value="schemes">
          <SchemesTab />
        </TabsContent>
        <TabsContent value="policies">
          <PoliciesTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}

function SchemesTab() {
  const [page, setPage] = React.useState(1);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["billing", "insurance-schemes", { page }],
    queryFn: () => billingApi.listSchemes({ page }),
    placeholderData: (prev) => prev,
  });

  return (
    <div>
      <div className="mb-4 flex justify-end">
        <SchemeDialog />
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
                  <TableHead>Scheme</TableHead>
                  <TableHead>Payer</TableHead>
                  <TableHead className="text-right">Coverage</TableHead>
                  <TableHead>Contact</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.results.map((s) => (
                  <TableRow key={s.id}>
                    <TableCell className="font-medium">{s.name}</TableCell>
                    <TableCell>{s.payer_name || "—"}</TableCell>
                    <TableCell className="text-right">{s.coverage_percent}%</TableCell>
                    <TableCell>{s.contact || "—"}</TableCell>
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
          <EmptyState
            icon={<ShieldCheck className="size-8" />}
            title="No insurance schemes yet"
            action={<SchemeDialog />}
          />
        )}
      </Card>
    </div>
  );
}

function SchemeDialog() {
  const [open, setOpen] = React.useState(false);
  const [form, setForm] = React.useState<Partial<InsuranceScheme>>({
    name: "", payer_name: "", coverage_percent: "", contact: "",
  });
  const [formError, setFormError] = React.useState<string | null>(null);
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const create = useMutation({
    mutationFn: () => billingApi.createScheme(form),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["billing", "insurance-schemes"] });
      toast({ title: "Insurance scheme added", variant: "success" });
      setOpen(false);
      setForm({ name: "", payer_name: "", coverage_percent: "", contact: "" });
    },
    onError: (err) =>
      setFormError(err instanceof ApiError ? err.toUserMessage() : "Could not add scheme."),
  });

  function submit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    if (!form.name?.trim()) return setFormError("Name is required.");
    create.mutate();
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="size-4" /> Add scheme
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add insurance scheme</DialogTitle>
        </DialogHeader>
        <form onSubmit={submit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Scheme name *</Label>
            <Input
              id="name"
              value={form.name ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              autoFocus
            />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="payer">Payer name</Label>
              <Input
                id="payer"
                value={form.payer_name ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, payer_name: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="coverage">Coverage %</Label>
              <Input
                id="coverage"
                type="number"
                step="any"
                value={form.coverage_percent ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, coverage_percent: e.target.value }))}
              />
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="contact">Contact</Label>
            <Input
              id="contact"
              value={form.contact ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, contact: e.target.value }))}
            />
          </div>
          {formError && (
            <p className="whitespace-pre-line rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {formError}
            </p>
          )}
          <DialogFooter>
            <Button type="submit" disabled={create.isPending}>
              {create.isPending ? <Spinner className="size-4" /> : "Add scheme"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function PoliciesTab() {
  const [page, setPage] = React.useState(1);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["billing", "patient-insurance", { page }],
    queryFn: () => billingApi.listPatientInsurance({ page, ordering: "-id" }),
    placeholderData: (prev) => prev,
  });

  return (
    <div>
      <div className="mb-4 flex justify-end">
        <PolicyDialog />
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
                  <TableHead>Patient</TableHead>
                  <TableHead>Scheme</TableHead>
                  <TableHead>Policy #</TableHead>
                  <TableHead>Valid</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.results.map((p: PatientInsurance) => (
                  <TableRow key={p.id}>
                    <TableCell className="font-medium">{p.patient_name}</TableCell>
                    <TableCell>{p.scheme_name}</TableCell>
                    <TableCell className="font-mono text-xs">{p.policy_number}</TableCell>
                    <TableCell>
                      {p.valid_from ? formatDate(p.valid_from) : "—"}
                      {p.valid_to ? ` – ${formatDate(p.valid_to)}` : ""}
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={p.is_active ? "ACTIVE" : "INACTIVE"} />
                    </TableCell>
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
          <EmptyState
            icon={<ShieldCheck className="size-8" />}
            title="No patient policies yet"
            action={<PolicyDialog />}
          />
        )}
      </Card>
    </div>
  );
}

function PolicyDialog() {
  const [open, setOpen] = React.useState(false);
  const [patient, setPatient] = React.useState<Patient | null>(null);
  const [scheme, setScheme] = React.useState("");
  const [policyNumber, setPolicyNumber] = React.useState("");
  const [validFrom, setValidFrom] = React.useState("");
  const [validTo, setValidTo] = React.useState("");
  const [formError, setFormError] = React.useState<string | null>(null);
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const schemes = useInsuranceSchemes();

  function reset() {
    setPatient(null);
    setScheme("");
    setPolicyNumber("");
    setValidFrom("");
    setValidTo("");
    setFormError(null);
  }

  const create = useMutation({
    mutationFn: () =>
      billingApi.createPatientInsurance({
        patient: patient!.id,
        scheme: Number(scheme),
        policy_number: policyNumber,
        valid_from: validFrom || null,
        valid_to: validTo || null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["billing", "patient-insurance"] });
      toast({ title: "Patient policy added", variant: "success" });
      setOpen(false);
      reset();
    },
    onError: (err) =>
      setFormError(err instanceof ApiError ? err.toUserMessage() : "Could not add policy."),
  });

  function submit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    if (!patient) return setFormError("Select a patient.");
    if (!scheme) return setFormError("Select a scheme.");
    if (!policyNumber.trim()) return setFormError("Policy number is required.");
    create.mutate();
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(o) => {
        setOpen(o);
        if (!o) reset();
      }}
    >
      <DialogTrigger asChild>
        <Button>
          <Plus className="size-4" /> Add policy
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add patient policy</DialogTitle>
        </DialogHeader>
        <form onSubmit={submit} className="space-y-4">
          <div className="space-y-2">
            <Label>Patient *</Label>
            <PatientCombobox value={patient} onSelect={setPatient} />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label>Scheme *</Label>
              <Select value={scheme} onValueChange={setScheme}>
                <SelectTrigger>
                  <SelectValue placeholder="Select" />
                </SelectTrigger>
                <SelectContent>
                  {schemes.data?.map((s) => (
                    <SelectItem key={s.id} value={String(s.id)}>
                      {s.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="policy">Policy number *</Label>
              <Input
                id="policy"
                value={policyNumber}
                onChange={(e) => setPolicyNumber(e.target.value)}
              />
            </div>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="from">Valid from</Label>
              <Input
                id="from"
                type="date"
                value={validFrom}
                onChange={(e) => setValidFrom(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="to">Valid to</Label>
              <Input
                id="to"
                type="date"
                value={validTo}
                onChange={(e) => setValidTo(e.target.value)}
              />
            </div>
          </div>
          {formError && (
            <p className="whitespace-pre-line rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {formError}
            </p>
          )}
          <DialogFooter>
            <Button type="submit" disabled={create.isPending}>
              {create.isPending ? <Spinner className="size-4" /> : "Add policy"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
