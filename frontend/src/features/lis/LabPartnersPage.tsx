import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Building2, Plus, Stethoscope, Truck } from "lucide-react";
import { lisApi } from "./api";
import type { Client, ClientType, CollectionCenter, ReferringDoctor } from "./types";
import { ApiError } from "@/lib/api/types";
import { money } from "@/lib/format";
import { useToast } from "@/components/ui/toast";
import { PageHeader } from "@/components/common/PageHeader";
import { EmptyState } from "@/components/common/states";
import { LisTabs } from "./components/LisTabs";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PageLoader, Spinner } from "@/components/ui/spinner";
import { Checkbox } from "@/components/ui/checkbox";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

const CLIENT_TYPES: { value: ClientType; label: string }[] = [
  { value: "HOSPITAL", label: "Hospital" },
  { value: "CORPORATE", label: "Corporate" },
  { value: "COLLECTION_CENTER", label: "Collection center" },
  { value: "CAMP", label: "Health camp" },
  { value: "OTHER", label: "Other" },
];

export function LabPartnersPage() {
  return (
    <div>
      <PageHeader
        title="Clients &amp; partners"
        description="B2B accounts, referring doctors and collection centres that feed the lab."
      />
      <LisTabs />
      <Tabs defaultValue="clients">
        <TabsList>
          <TabsTrigger value="clients">
            <Building2 className="size-4" /> B2B clients
          </TabsTrigger>
          <TabsTrigger value="doctors">
            <Stethoscope className="size-4" /> Referring doctors
          </TabsTrigger>
          <TabsTrigger value="centers">
            <Truck className="size-4" /> Collection centres
          </TabsTrigger>
        </TabsList>
        <TabsContent value="clients">
          <ClientsTab />
        </TabsContent>
        <TabsContent value="doctors">
          <DoctorsTab />
        </TabsContent>
        <TabsContent value="centers">
          <CentersTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}

// --- B2B clients ----------------------------------------------------------

function ClientsTab() {
  const { data, isLoading } = useQuery({
    queryKey: ["lab-clients"],
    queryFn: () => lisApi.listClients({ page_size: 100 }),
  });
  const rows = data?.results ?? [];

  return (
    <Card className="mt-4">
      <div className="flex justify-end p-4 pb-0">
        <ClientDialog />
      </div>
      {isLoading ? (
        <PageLoader />
      ) : rows.length === 0 ? (
        <EmptyState
          icon={<Building2 className="size-8" />}
          title="No B2B clients"
          description="Add hospitals, corporates or camps that send work on account."
          action={<ClientDialog />}
        />
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Code</TableHead>
              <TableHead>Name</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Billing</TableHead>
              <TableHead className="text-right">Credit limit</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((c) => (
              <TableRow key={c.id}>
                <TableCell className="font-mono text-xs">{c.code}</TableCell>
                <TableCell className="font-medium">{c.name}</TableCell>
                <TableCell>
                  {CLIENT_TYPES.find((t) => t.value === c.client_type)?.label ?? c.client_type}
                </TableCell>
                <TableCell>
                  {c.is_credit ? <Badge variant="warning">On account</Badge> : <Badge>Prepaid</Badge>}
                </TableCell>
                <TableCell className="text-right">{money(c.credit_limit)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </Card>
  );
}

function ClientDialog() {
  const [open, setOpen] = React.useState(false);
  const [form, setForm] = React.useState<Partial<Client>>({
    name: "",
    code: "",
    client_type: "HOSPITAL",
    is_credit: false,
  });
  const [formError, setFormError] = React.useState<string | null>(null);
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const create = useMutation({
    mutationFn: () => lisApi.createClient(form),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["lab-clients"] });
      toast({ title: "Client added", variant: "success" });
      setOpen(false);
      setForm({ name: "", code: "", client_type: "HOSPITAL", is_credit: false });
    },
    onError: (err) =>
      setFormError(err instanceof ApiError ? err.toUserMessage() : "Could not add client."),
  });

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm">
          <Plus className="size-3" /> Add client
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add B2B client</DialogTitle>
        </DialogHeader>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            setFormError(null);
            if (!form.name?.trim()) return setFormError("Name is required.");
            if (!form.code?.trim()) return setFormError("Code is required.");
            create.mutate();
          }}
          className="space-y-4"
        >
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Name *">
              <Input
                value={form.name ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                autoFocus
              />
            </Field>
            <Field label="Code *">
              <Input
                value={form.code ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, code: e.target.value }))}
              />
            </Field>
            <Field label="Type">
              <Select
                value={form.client_type}
                onValueChange={(v) => setForm((f) => ({ ...f, client_type: v as ClientType }))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {CLIENT_TYPES.map((t) => (
                    <SelectItem key={t.value} value={t.value}>
                      {t.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </Field>
            <Field label="Credit limit">
              <Input
                type="number"
                step="any"
                value={form.credit_limit ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, credit_limit: e.target.value }))}
              />
            </Field>
          </div>
          <label className="flex items-center gap-2 text-sm">
            <Checkbox
              checked={!!form.is_credit}
              onCheckedChange={(v) => setForm((f) => ({ ...f, is_credit: !!v }))}
            />
            Billed on account (credit) rather than prepaid
          </label>
          {formError && (
            <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {formError}
            </p>
          )}
          <DialogFooter>
            <Button type="submit" disabled={create.isPending}>
              {create.isPending ? <Spinner className="size-4" /> : "Add client"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// --- Referring doctors ----------------------------------------------------

function DoctorsTab() {
  const { data, isLoading } = useQuery({
    queryKey: ["lab-referring-doctors"],
    queryFn: () => lisApi.listReferringDoctors({ page_size: 100 }),
  });
  const rows = data?.results ?? [];

  return (
    <Card className="mt-4">
      <div className="flex justify-end p-4 pb-0">
        <DoctorDialog />
      </div>
      {isLoading ? (
        <PageLoader />
      ) : rows.length === 0 ? (
        <EmptyState
          icon={<Stethoscope className="size-8" />}
          title="No referring doctors"
          description="Track external doctors who refer patients, with commission."
          action={<DoctorDialog />}
        />
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Code</TableHead>
              <TableHead>Name</TableHead>
              <TableHead>Specialty</TableHead>
              <TableHead>Hospital</TableHead>
              <TableHead className="text-right">Commission</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((d) => (
              <TableRow key={d.id}>
                <TableCell className="font-mono text-xs">{d.code}</TableCell>
                <TableCell className="font-medium">{d.name}</TableCell>
                <TableCell>{d.specialty || "—"}</TableCell>
                <TableCell>{d.hospital || "—"}</TableCell>
                <TableCell className="text-right">{d.commission_percent}%</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </Card>
  );
}

function DoctorDialog() {
  const [open, setOpen] = React.useState(false);
  const [form, setForm] = React.useState<Partial<ReferringDoctor>>({ name: "", code: "" });
  const [formError, setFormError] = React.useState<string | null>(null);
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const create = useMutation({
    mutationFn: () => lisApi.createReferringDoctor(form),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["lab-referring-doctors"] });
      toast({ title: "Referring doctor added", variant: "success" });
      setOpen(false);
      setForm({ name: "", code: "" });
    },
    onError: (err) =>
      setFormError(err instanceof ApiError ? err.toUserMessage() : "Could not add doctor."),
  });

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm">
          <Plus className="size-3" /> Add doctor
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add referring doctor</DialogTitle>
        </DialogHeader>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            setFormError(null);
            if (!form.name?.trim()) return setFormError("Name is required.");
            if (!form.code?.trim()) return setFormError("Code is required.");
            create.mutate();
          }}
          className="space-y-4"
        >
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Name *">
              <Input
                value={form.name ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                autoFocus
              />
            </Field>
            <Field label="Code *">
              <Input
                value={form.code ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, code: e.target.value }))}
              />
            </Field>
            <Field label="Specialty">
              <Input
                value={form.specialty ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, specialty: e.target.value }))}
              />
            </Field>
            <Field label="Hospital">
              <Input
                value={form.hospital ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, hospital: e.target.value }))}
              />
            </Field>
            <Field label="Commission %">
              <Input
                type="number"
                step="any"
                value={form.commission_percent ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, commission_percent: e.target.value }))}
              />
            </Field>
            <Field label="Phone">
              <Input
                value={form.phone ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))}
              />
            </Field>
          </div>
          {formError && (
            <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {formError}
            </p>
          )}
          <DialogFooter>
            <Button type="submit" disabled={create.isPending}>
              {create.isPending ? <Spinner className="size-4" /> : "Add doctor"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// --- Collection centres ---------------------------------------------------

function CentersTab() {
  const { data, isLoading } = useQuery({
    queryKey: ["lab-collection-centers"],
    queryFn: () => lisApi.listCollectionCenters({ page_size: 100 }),
  });
  const rows = data?.results ?? [];

  return (
    <Card className="mt-4">
      <div className="flex justify-end p-4 pb-0">
        <CenterDialog />
      </div>
      {isLoading ? (
        <PageLoader />
      ) : rows.length === 0 ? (
        <EmptyState
          icon={<Truck className="size-8" />}
          title="No collection centres"
          description="Add branches and home-collection points that route samples to a processing lab."
          action={<CenterDialog />}
        />
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Code</TableHead>
              <TableHead>Name</TableHead>
              <TableHead>Phone</TableHead>
              <TableHead>Home collection</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((c) => (
              <TableRow key={c.id}>
                <TableCell className="font-mono text-xs">{c.code}</TableCell>
                <TableCell className="font-medium">{c.name}</TableCell>
                <TableCell>{c.phone || "—"}</TableCell>
                <TableCell>
                  {c.is_home_collection ? <Badge variant="success">Yes</Badge> : "—"}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </Card>
  );
}

function CenterDialog() {
  const [open, setOpen] = React.useState(false);
  const [form, setForm] = React.useState<Partial<CollectionCenter>>({
    name: "",
    code: "",
    is_home_collection: false,
  });
  const [formError, setFormError] = React.useState<string | null>(null);
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const create = useMutation({
    mutationFn: () => lisApi.createCollectionCenter(form),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["lab-collection-centers"] });
      toast({ title: "Collection centre added", variant: "success" });
      setOpen(false);
      setForm({ name: "", code: "", is_home_collection: false });
    },
    onError: (err) =>
      setFormError(err instanceof ApiError ? err.toUserMessage() : "Could not add centre."),
  });

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm">
          <Plus className="size-3" /> Add centre
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add collection centre</DialogTitle>
        </DialogHeader>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            setFormError(null);
            if (!form.name?.trim()) return setFormError("Name is required.");
            if (!form.code?.trim()) return setFormError("Code is required.");
            create.mutate();
          }}
          className="space-y-4"
        >
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Name *">
              <Input
                value={form.name ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                autoFocus
              />
            </Field>
            <Field label="Code *">
              <Input
                value={form.code ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, code: e.target.value }))}
              />
            </Field>
            <Field label="Phone">
              <Input
                value={form.phone ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))}
              />
            </Field>
          </div>
          <label className="flex items-center gap-2 text-sm">
            <Checkbox
              checked={!!form.is_home_collection}
              onCheckedChange={(v) => setForm((f) => ({ ...f, is_home_collection: !!v }))}
            />
            Supports home collection
          </label>
          {formError && (
            <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {formError}
            </p>
          )}
          <DialogFooter>
            <Button type="submit" disabled={create.isPending}>
              {create.isPending ? <Spinner className="size-4" /> : "Add centre"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      {children}
    </div>
  );
}
