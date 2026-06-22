import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Home, IdCard, Plus, Tag, User } from "lucide-react";
import { emrApi } from "../../api";
import { usePatientIdentifierTypes, usePersonAttributeTypes } from "../../queries";
import type { Patient } from "../../types";
import { ApiError } from "@/lib/api/types";
import { useToast } from "@/components/ui/toast";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { EmptyState } from "@/components/common/states";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export function DemographicsTab({ patient }: { patient: Patient }) {
  return (
    <div className="space-y-6">
      <NamesSection patient={patient} />
      <IdentifiersSection patient={patient} />
      <AddressesSection personId={patient.person_id} />
      <AttributesSection personId={patient.person_id} />
    </div>
  );
}

function NamesSection({ patient }: { patient: Patient }) {
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-2 text-base">
          <User className="size-4" /> Names
        </CardTitle>
        <AddNameDialog personId={patient.person_id} />
      </CardHeader>
      <CardContent>
        {patient.names.length > 0 ? (
          <ul className="divide-y">
            {patient.names.map((n) => (
              <li key={n.id} className="flex flex-wrap items-center justify-between gap-2 py-2 text-sm">
                <span className="font-medium">
                  {[n.prefix, n.given_name, n.middle_name, n.family_name, n.family_name_suffix]
                    .filter(Boolean)
                    .join(" ")}
                </span>
                {n.preferred && <Badge variant="success">Preferred</Badge>}
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState icon={<User className="size-8" />} title="No names recorded" />
        )}
      </CardContent>
    </Card>
  );
}

function AddNameDialog({ personId }: { personId: number }) {
  const [open, setOpen] = React.useState(false);
  const [givenName, setGivenName] = React.useState("");
  const [middleName, setMiddleName] = React.useState("");
  const [familyName, setFamilyName] = React.useState("");
  const [preferred, setPreferred] = React.useState(false);
  const [formError, setFormError] = React.useState<string | null>(null);

  const queryClient = useQueryClient();
  const { toast } = useToast();

  function reset() {
    setGivenName("");
    setMiddleName("");
    setFamilyName("");
    setPreferred(false);
    setFormError(null);
  }

  const create = useMutation({
    mutationFn: () =>
      emrApi.createPersonName({
        person: personId,
        given_name: givenName,
        middle_name: middleName,
        family_name: familyName,
        preferred,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["patient"] });
      toast({ title: "Name added", variant: "success" });
      setOpen(false);
      reset();
    },
    onError: (err) =>
      setFormError(err instanceof ApiError ? err.toUserMessage() : "Could not add name."),
  });

  function submit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    if (!givenName || !familyName) {
      setFormError("Given name and family name are required.");
      return;
    }
    create.mutate();
  }

  return (
    <Dialog open={open} onOpenChange={(o) => { setOpen(o); if (!o) reset(); }}>
      <DialogTrigger asChild>
        <Button size="sm" variant="outline">
          <Plus className="size-4" /> Add name
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add a name</DialogTitle>
        </DialogHeader>
        <form onSubmit={submit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="name-given">Given name *</Label>
              <Input id="name-given" value={givenName} onChange={(e) => setGivenName(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="name-middle">Middle name</Label>
              <Input id="name-middle" value={middleName} onChange={(e) => setMiddleName(e.target.value)} />
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="name-family">Family name *</Label>
            <Input id="name-family" value={familyName} onChange={(e) => setFamilyName(e.target.value)} />
          </div>
          <div className="flex items-center gap-2">
            <Checkbox id="name-preferred" checked={preferred} onCheckedChange={(c) => setPreferred(!!c)} />
            <Label htmlFor="name-preferred">Preferred name</Label>
          </div>
          {formError && (
            <p className="whitespace-pre-line rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {formError}
            </p>
          )}
          <DialogFooter>
            <Button type="submit" disabled={create.isPending}>
              {create.isPending ? <Spinner className="size-4" /> : "Save name"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function IdentifiersSection({ patient }: { patient: Patient }) {
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-2 text-base">
          <IdCard className="size-4" /> Identifiers
        </CardTitle>
        <AddIdentifierDialog patientId={patient.id} />
      </CardHeader>
      <CardContent>
        {patient.identifiers.length > 0 ? (
          <ul className="divide-y">
            {patient.identifiers.map((i) => (
              <li key={i.id} className="flex flex-wrap items-center justify-between gap-2 py-2 text-sm">
                <div>
                  <span className="font-mono font-medium">{i.identifier}</span>
                  <span className="ml-2 text-muted-foreground">{i.identifier_type_name}</span>
                </div>
                {i.preferred && <Badge variant="success">Preferred</Badge>}
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState icon={<IdCard className="size-8" />} title="No identifiers recorded" />
        )}
      </CardContent>
    </Card>
  );
}

function AddIdentifierDialog({ patientId }: { patientId: number }) {
  const [open, setOpen] = React.useState(false);
  const [identifierType, setIdentifierType] = React.useState("");
  const [identifier, setIdentifier] = React.useState("");
  const [formError, setFormError] = React.useState<string | null>(null);

  const queryClient = useQueryClient();
  const { toast } = useToast();
  const identifierTypes = usePatientIdentifierTypes();

  function reset() {
    setIdentifierType("");
    setIdentifier("");
    setFormError(null);
  }

  const create = useMutation({
    mutationFn: () =>
      emrApi.createPatientIdentifier({
        patient: patientId,
        identifier_type: Number(identifierType),
        identifier,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["patient"] });
      toast({ title: "Identifier added", variant: "success" });
      setOpen(false);
      reset();
    },
    onError: (err) =>
      setFormError(err instanceof ApiError ? err.toUserMessage() : "Could not add identifier."),
  });

  function submit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    if (!identifierType || !identifier) {
      setFormError("Select a type and enter the identifier value.");
      return;
    }
    create.mutate();
  }

  return (
    <Dialog open={open} onOpenChange={(o) => { setOpen(o); if (!o) reset(); }}>
      <DialogTrigger asChild>
        <Button size="sm" variant="outline">
          <Plus className="size-4" /> Add identifier
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add identifier</DialogTitle>
        </DialogHeader>
        <form onSubmit={submit} className="space-y-4">
          <div className="space-y-2">
            <Label>Identifier type *</Label>
            <Select value={identifierType} onValueChange={setIdentifierType}>
              <SelectTrigger><SelectValue placeholder="Select type" /></SelectTrigger>
              <SelectContent>
                {identifierTypes.data?.map((t) => (
                  <SelectItem key={t.id} value={String(t.id)}>{t.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="identifier-value">Identifier *</Label>
            <Input id="identifier-value" value={identifier} onChange={(e) => setIdentifier(e.target.value)} />
          </div>
          {formError && (
            <p className="whitespace-pre-line rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {formError}
            </p>
          )}
          <DialogFooter>
            <Button type="submit" disabled={create.isPending}>
              {create.isPending ? <Spinner className="size-4" /> : "Save identifier"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function AddressesSection({ personId }: { personId: number }) {
  const { data, isLoading } = useQuery({
    queryKey: ["person-addresses", { person: personId }],
    queryFn: () => emrApi.listPersonAddresses({ person: personId }),
  });

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-2 text-base">
          <Home className="size-4" /> Addresses
        </CardTitle>
        <AddAddressDialog personId={personId} />
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : data && data.results.length > 0 ? (
          <ul className="divide-y">
            {data.results.map((a) => (
              <li key={a.id} className="flex flex-wrap items-center justify-between gap-2 py-2 text-sm">
                <span>
                  {[a.address1, a.address2, a.city_village, a.state_province, a.country]
                    .filter(Boolean)
                    .join(", ") || "—"}
                </span>
                {a.preferred && <Badge variant="success">Preferred</Badge>}
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState
            icon={<Home className="size-8" />}
            title="No address on file"
            description="Add a postal or physical address for this patient."
          />
        )}
      </CardContent>
    </Card>
  );
}

function AddAddressDialog({ personId }: { personId: number }) {
  const [open, setOpen] = React.useState(false);
  const [address1, setAddress1] = React.useState("");
  const [address2, setAddress2] = React.useState("");
  const [cityVillage, setCityVillage] = React.useState("");
  const [stateProvince, setStateProvince] = React.useState("");
  const [country, setCountry] = React.useState("");
  const [postalCode, setPostalCode] = React.useState("");
  const [preferred, setPreferred] = React.useState(false);
  const [formError, setFormError] = React.useState<string | null>(null);

  const queryClient = useQueryClient();
  const { toast } = useToast();

  function reset() {
    setAddress1("");
    setAddress2("");
    setCityVillage("");
    setStateProvince("");
    setCountry("");
    setPostalCode("");
    setPreferred(false);
    setFormError(null);
  }

  const create = useMutation({
    mutationFn: () =>
      emrApi.createPersonAddress({
        person: personId,
        address1,
        address2,
        city_village: cityVillage,
        state_province: stateProvince,
        country,
        postal_code: postalCode,
        preferred,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["person-addresses", { person: personId }] });
      toast({ title: "Address added", variant: "success" });
      setOpen(false);
      reset();
    },
    onError: (err) =>
      setFormError(err instanceof ApiError ? err.toUserMessage() : "Could not add address."),
  });

  function submit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    create.mutate();
  }

  return (
    <Dialog open={open} onOpenChange={(o) => { setOpen(o); if (!o) reset(); }}>
      <DialogTrigger asChild>
        <Button size="sm" variant="outline">
          <Plus className="size-4" /> Add address
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add address</DialogTitle>
        </DialogHeader>
        <form onSubmit={submit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="addr1">Address line 1</Label>
            <Input id="addr1" value={address1} onChange={(e) => setAddress1(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="addr2">Address line 2</Label>
            <Input id="addr2" value={address2} onChange={(e) => setAddress2(e.target.value)} />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="addr-city">City / Village</Label>
              <Input id="addr-city" value={cityVillage} onChange={(e) => setCityVillage(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="addr-state">State / Province</Label>
              <Input id="addr-state" value={stateProvince} onChange={(e) => setStateProvince(e.target.value)} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="addr-country">Country</Label>
              <Input id="addr-country" value={country} onChange={(e) => setCountry(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="addr-postal">Postal code</Label>
              <Input id="addr-postal" value={postalCode} onChange={(e) => setPostalCode(e.target.value)} />
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Checkbox id="addr-preferred" checked={preferred} onCheckedChange={(c) => setPreferred(!!c)} />
            <Label htmlFor="addr-preferred">Preferred address</Label>
          </div>
          {formError && (
            <p className="whitespace-pre-line rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {formError}
            </p>
          )}
          <DialogFooter>
            <Button type="submit" disabled={create.isPending}>
              {create.isPending ? <Spinner className="size-4" /> : "Save address"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function AttributesSection({ personId }: { personId: number }) {
  const { data, isLoading } = useQuery({
    queryKey: ["person-attributes", { person: personId }],
    queryFn: () => emrApi.listPersonAttributes({ person: personId }),
  });

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-2 text-base">
          <Tag className="size-4" /> Custom attributes
        </CardTitle>
        <AddAttributeDialog personId={personId} />
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : data && data.results.length > 0 ? (
          <ul className="divide-y">
            {data.results.map((a) => (
              <li key={a.id} className="flex flex-wrap items-center justify-between gap-2 py-2 text-sm">
                <span className="font-medium">{a.attribute_type_name}</span>
                <span className="text-muted-foreground">{a.value || "—"}</span>
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState
            icon={<Tag className="size-8" />}
            title="No custom attributes"
            description="Attach extra demographic fields like occupation or next of kin."
          />
        )}
      </CardContent>
    </Card>
  );
}

function AddAttributeDialog({ personId }: { personId: number }) {
  const [open, setOpen] = React.useState(false);
  const [attributeType, setAttributeType] = React.useState("");
  const [value, setValue] = React.useState("");
  const [formError, setFormError] = React.useState<string | null>(null);

  const queryClient = useQueryClient();
  const { toast } = useToast();
  const attributeTypes = usePersonAttributeTypes();

  function reset() {
    setAttributeType("");
    setValue("");
    setFormError(null);
  }

  const create = useMutation({
    mutationFn: () =>
      emrApi.createPersonAttribute({
        person: personId,
        attribute_type: Number(attributeType),
        value,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["person-attributes", { person: personId }] });
      toast({ title: "Attribute added", variant: "success" });
      setOpen(false);
      reset();
    },
    onError: (err) =>
      setFormError(err instanceof ApiError ? err.toUserMessage() : "Could not add attribute."),
  });

  function submit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    if (!attributeType) {
      setFormError("Select an attribute type.");
      return;
    }
    create.mutate();
  }

  return (
    <Dialog open={open} onOpenChange={(o) => { setOpen(o); if (!o) reset(); }}>
      <DialogTrigger asChild>
        <Button size="sm" variant="outline">
          <Plus className="size-4" /> Add attribute
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add custom attribute</DialogTitle>
        </DialogHeader>
        <form onSubmit={submit} className="space-y-4">
          <div className="space-y-2">
            <Label>Attribute type *</Label>
            <Select value={attributeType} onValueChange={setAttributeType}>
              <SelectTrigger><SelectValue placeholder="Select type" /></SelectTrigger>
              <SelectContent>
                {attributeTypes.data?.map((t) => (
                  <SelectItem key={t.id} value={String(t.id)}>{t.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="attr-value">Value</Label>
            <Input id="attr-value" value={value} onChange={(e) => setValue(e.target.value)} />
          </div>
          {formError && (
            <p className="whitespace-pre-line rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {formError}
            </p>
          )}
          <DialogFooter>
            <Button type="submit" disabled={create.isPending}>
              {create.isPending ? <Spinner className="size-4" /> : "Save attribute"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
