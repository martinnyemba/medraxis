import * as React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { ArrowLeft, Pill } from "lucide-react";
import { pharmacyApi } from "./api";
import type { DurationUnit } from "./types";
import type { Patient } from "@/features/emr/types";
import type { Product } from "@/features/inventory/api";
import { ApiError } from "@/lib/api/types";
import { useToast } from "@/components/ui/toast";
import { PageHeader } from "@/components/common/PageHeader";
import { PatientCombobox } from "@/components/common/PatientCombobox";
import { ProductCombobox } from "@/components/common/ProductCombobox";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export function NewPrescriptionPage() {
  const navigate = useNavigate();
  const { toast } = useToast();

  const [patient, setPatient] = React.useState<Patient | null>(null);
  const [drug, setDrug] = React.useState<Product | null>(null);
  const [form, setForm] = React.useState({
    dose: "",
    dose_units: "mg",
    frequency: "",
    route: "PO",
    duration: "",
    duration_units: "DAYS" as DurationUnit,
    quantity: "",
    dosing_instructions: "",
  });
  const [formError, setFormError] = React.useState<string | null>(null);

  function update<K extends keyof typeof form>(key: K, value: (typeof form)[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  const create = useMutation({
    mutationFn: () =>
      pharmacyApi.prescribe({
        patient: patient!.id,
        drug: drug!.id,
        dose: form.dose || null,
        dose_units: form.dose_units,
        frequency: form.frequency,
        route: form.route,
        duration: form.duration ? Number(form.duration) : null,
        duration_units: form.duration_units,
        quantity: form.quantity || "0",
        dosing_instructions: form.dosing_instructions,
      }),
    onSuccess: (rx) => {
      toast({ title: `Prescription ${rx.order_number} created`, variant: "success" });
      navigate(`/pharmacy/prescriptions/${rx.id}`);
    },
    onError: (err) =>
      setFormError(err instanceof ApiError ? err.toUserMessage() : "Could not create prescription."),
  });

  function submit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    if (!patient) return setFormError("Select a patient.");
    if (!drug) return setFormError("Select a drug.");
    create.mutate();
  }

  return (
    <div className="mx-auto max-w-2xl">
      <Button variant="ghost" size="sm" asChild className="mb-2 -ml-2">
        <Link to="/pharmacy/prescriptions">
          <ArrowLeft className="size-4" /> Back to prescriptions
        </Link>
      </Button>
      <PageHeader title="New prescription" description="Prescribe a medication for a patient." />

      <Card>
        <CardContent className="pt-6">
          <form onSubmit={submit} className="space-y-5">
            <div className="space-y-2">
              <Label>Patient *</Label>
              <PatientCombobox value={patient} onSelect={setPatient} />
            </div>

            <div className="space-y-2">
              <Label>Drug *</Label>
              <ProductCombobox value={drug} onSelect={setDrug} drugsOnly />
              {drug && drug.drug_concept === null && (
                <p className="text-xs text-warning">
                  This product has no clinical drug concept set; prescribing may be rejected.
                </p>
              )}
            </div>

            <div className="grid gap-4 sm:grid-cols-3">
              <div className="space-y-2">
                <Label htmlFor="dose">Dose</Label>
                <Input
                  id="dose"
                  value={form.dose}
                  onChange={(e) => update("dose", e.target.value)}
                  placeholder="500"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="dose_units">Units</Label>
                <Input
                  id="dose_units"
                  value={form.dose_units}
                  onChange={(e) => update("dose_units", e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="frequency">Frequency</Label>
                <Input
                  id="frequency"
                  value={form.frequency}
                  onChange={(e) => update("frequency", e.target.value)}
                  placeholder="TDS"
                />
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-4">
              <div className="space-y-2">
                <Label htmlFor="route">Route</Label>
                <Input
                  id="route"
                  value={form.route}
                  onChange={(e) => update("route", e.target.value)}
                  placeholder="PO"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="duration">Duration</Label>
                <Input
                  id="duration"
                  type="number"
                  value={form.duration}
                  onChange={(e) => update("duration", e.target.value)}
                  placeholder="5"
                />
              </div>
              <div className="space-y-2">
                <Label>Period</Label>
                <Select
                  value={form.duration_units}
                  onValueChange={(v) => update("duration_units", v as DurationUnit)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="DAYS">Days</SelectItem>
                    <SelectItem value="WEEKS">Weeks</SelectItem>
                    <SelectItem value="MONTHS">Months</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="quantity">Quantity *</Label>
                <Input
                  id="quantity"
                  type="number"
                  value={form.quantity}
                  onChange={(e) => update("quantity", e.target.value)}
                  placeholder="15"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="instructions">Dosing instructions</Label>
              <textarea
                id="instructions"
                className="flex min-h-16 w-full rounded-md border border-input bg-card px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                value={form.dosing_instructions}
                onChange={(e) => update("dosing_instructions", e.target.value)}
                placeholder="e.g. Take after meals"
              />
            </div>

            {formError && (
              <p className="whitespace-pre-line rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
                {formError}
              </p>
            )}

            <div className="flex justify-end gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => navigate("/pharmacy/prescriptions")}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={create.isPending}>
                {create.isPending ? (
                  <Spinner className="size-4" />
                ) : (
                  <>
                    <Pill className="size-4" /> Prescribe
                  </>
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
