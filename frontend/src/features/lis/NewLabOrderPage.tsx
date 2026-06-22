import * as React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { ArrowLeft, FlaskConical } from "lucide-react";
import { lisApi } from "./api";
import { useLabTests } from "./queries";
import type { LabTest } from "./types";
import type { Patient } from "@/features/emr/types";
import { ApiError } from "@/lib/api/types";
import { useToast } from "@/components/ui/toast";
import { PageHeader } from "@/components/common/PageHeader";
import { PatientCombobox } from "@/components/common/PatientCombobox";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export function NewLabOrderPage() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const tests = useLabTests();

  const [patient, setPatient] = React.useState<Patient | null>(null);
  const [testFilter, setTestFilter] = React.useState("");
  const [selectedTest, setSelectedTest] = React.useState<LabTest | null>(null);
  const [urgency, setUrgency] = React.useState("ROUTINE");
  const [clinicalHistory, setClinicalHistory] = React.useState("");
  const [formError, setFormError] = React.useState<string | null>(null);

  const filteredTests = (tests.data?.list ?? []).filter((t) =>
    `${t.name} ${t.test_code}`.toLowerCase().includes(testFilter.toLowerCase()),
  );

  const create = useMutation({
    mutationFn: () =>
      lisApi.createOrder({
        patient: patient!.id,
        lab_test: selectedTest!.id,
        urgency,
        clinical_history: clinicalHistory,
      }),
    onSuccess: (order) => {
      toast({ title: `Lab order ${order.order_number} created`, variant: "success" });
      navigate(`/lis/orders/${order.id}`);
    },
    onError: (err) =>
      setFormError(err instanceof ApiError ? err.toUserMessage() : "Could not create order."),
  });

  function submit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    if (!patient) return setFormError("Select a patient.");
    if (!selectedTest) return setFormError("Select a test.");
    create.mutate();
  }

  return (
    <div className="mx-auto max-w-2xl">
      <Button variant="ghost" size="sm" asChild className="mb-2 -ml-2">
        <Link to="/lis/worklist">
          <ArrowLeft className="size-4" /> Back to worklist
        </Link>
      </Button>
      <PageHeader title="New lab order" description="Request a test for a patient." />

      <Card>
        <CardContent className="pt-6">
          <form onSubmit={submit} className="space-y-5">
            <div className="space-y-2">
              <Label>Patient *</Label>
              <PatientCombobox value={patient} onSelect={setPatient} />
            </div>

            <div className="space-y-2">
              <Label>Test *</Label>
              {selectedTest ? (
                <div className="flex items-center justify-between rounded-md border bg-accent/40 px-3 py-2">
                  <div>
                    <p className="text-sm font-medium">{selectedTest.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {selectedTest.test_code}
                      {selectedTest.is_panel ? " · panel" : ""} · TAT{" "}
                      {selectedTest.turnaround_hours}h
                    </p>
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => setSelectedTest(null)}
                  >
                    Change
                  </Button>
                </div>
              ) : (
                <>
                  <Input
                    placeholder="Search tests by name or code…"
                    value={testFilter}
                    onChange={(e) => setTestFilter(e.target.value)}
                  />
                  <div className="max-h-52 overflow-y-auto rounded-md border">
                    {tests.isLoading ? (
                      <p className="p-3 text-sm text-muted-foreground">Loading catalogue…</p>
                    ) : filteredTests.length > 0 ? (
                      filteredTests.slice(0, 30).map((t) => (
                        <button
                          key={t.id}
                          type="button"
                          onClick={() => setSelectedTest(t)}
                          className="flex w-full items-center justify-between px-3 py-2 text-left text-sm hover:bg-accent"
                        >
                          <span className="font-medium">{t.name}</span>
                          <span className="flex items-center gap-2">
                            {t.is_panel && (
                              <Badge variant="secondary" className="text-[10px]">
                                Panel
                              </Badge>
                            )}
                            <span className="font-mono text-xs text-muted-foreground">
                              {t.test_code}
                            </span>
                          </span>
                        </button>
                      ))
                    ) : (
                      <p className="p-3 text-sm text-muted-foreground">No tests match.</p>
                    )}
                  </div>
                </>
              )}
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label>Urgency</Label>
                <Select value={urgency} onValueChange={setUrgency}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ROUTINE">Routine</SelectItem>
                    <SelectItem value="STAT">STAT</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="history">Clinical history / notes</Label>
              <textarea
                id="history"
                className="flex min-h-20 w-full rounded-md border border-input bg-card px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                value={clinicalHistory}
                onChange={(e) => setClinicalHistory(e.target.value)}
              />
            </div>

            {formError && (
              <p className="whitespace-pre-line rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
                {formError}
              </p>
            )}

            <div className="flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={() => navigate("/lis/worklist")}>
                Cancel
              </Button>
              <Button type="submit" disabled={create.isPending}>
                {create.isPending ? (
                  <Spinner className="size-4" />
                ) : (
                  <>
                    <FlaskConical className="size-4" /> Create order
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
