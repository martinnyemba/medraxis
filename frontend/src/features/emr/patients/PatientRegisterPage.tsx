import * as React from "react";
import { useNavigate, Link } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, UserPlus } from "lucide-react";
import { emrApi } from "../api";
import type { Gender, Patient, PatientRegistrationInput } from "../types";
import { ApiError } from "@/lib/api/types";
import { useToast } from "@/components/ui/toast";
import { PageHeader } from "@/components/common/PageHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Spinner } from "@/components/ui/spinner";
import { Card, CardContent } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const GENDERS: { value: Gender; label: string }[] = [
  { value: "F", label: "Female" },
  { value: "M", label: "Male" },
  { value: "O", label: "Other" },
  { value: "U", label: "Unknown" },
];

export function PatientRegisterPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const [form, setForm] = React.useState<PatientRegistrationInput>({
    given_name: "",
    family_name: "",
    gender: undefined,
    birthdate: "",
  });
  const [fieldError, setFieldError] = React.useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: (input: PatientRegistrationInput) => emrApi.registerPatient(input),
    onSuccess: (patient: Patient) => {
      queryClient.invalidateQueries({ queryKey: ["patients"] });
      toast({ title: "Patient registered", variant: "success" });
      navigate(`/emr/patients/${patient.id}`);
    },
    onError: (err) => {
      setFieldError(err instanceof ApiError ? err.toUserMessage() : "Registration failed.");
    },
  });

  function update<K extends keyof PatientRegistrationInput>(
    key: K,
    value: PatientRegistrationInput[K],
  ) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setFieldError(null);
    mutation.mutate({
      ...form,
      birthdate: form.birthdate || null,
    });
  }

  return (
    <div className="mx-auto max-w-2xl">
      <Button variant="ghost" size="sm" asChild className="mb-2 -ml-2">
        <Link to="/emr/patients">
          <ArrowLeft className="size-4" /> Back to patients
        </Link>
      </Button>

      <PageHeader
        title="Register patient"
        description="A facility identifier is generated automatically on save."
      />

      <Card>
        <CardContent className="pt-6">
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="given_name">Given name *</Label>
                <Input
                  id="given_name"
                  value={form.given_name}
                  onChange={(e) => update("given_name", e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="family_name">Family name *</Label>
                <Input
                  id="family_name"
                  value={form.family_name}
                  onChange={(e) => update("family_name", e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label>Gender</Label>
                <Select
                  value={form.gender}
                  onValueChange={(v) => update("gender", v as Gender)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select gender" />
                  </SelectTrigger>
                  <SelectContent>
                    {GENDERS.map((g) => (
                      <SelectItem key={g.value} value={g.value}>
                        {g.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="birthdate">Date of birth</Label>
                <Input
                  id="birthdate"
                  type="date"
                  max={new Date().toISOString().slice(0, 10)}
                  value={form.birthdate ?? ""}
                  onChange={(e) => update("birthdate", e.target.value)}
                />
              </div>
            </div>

            {fieldError && (
              <p className="whitespace-pre-line rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
                {fieldError}
              </p>
            )}

            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="outline" onClick={() => navigate("/emr/patients")}>
                Cancel
              </Button>
              <Button type="submit" disabled={mutation.isPending}>
                {mutation.isPending ? (
                  <Spinner className="size-4" />
                ) : (
                  <>
                    <UserPlus className="size-4" /> Register
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
