import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, CalendarDays, User, VenetianMask, IdCard } from "lucide-react";
import { emrApi } from "../api";
import {
  patientName,
  preferredIdentifier,
  genderLabel,
  ageFromBirthdate,
  formatDate,
} from "@/lib/format";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { PageLoader } from "@/components/ui/spinner";
import { ErrorState } from "@/components/common/states";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { VisitsTab } from "./components/VisitsTab";
import { EncountersTab } from "./components/EncountersTab";
import { ClinicalTab } from "./components/ClinicalTab";

export function PatientDetailPage() {
  const { patientId } = useParams<{ patientId: string }>();
  const id = Number(patientId);

  const { data: patient, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["patient", id],
    queryFn: () => emrApi.getPatient(id),
    enabled: Number.isFinite(id),
  });

  if (isLoading) return <PageLoader />;
  if (isError || !patient) return <ErrorState error={error} onRetry={refetch} />;

  const age = ageFromBirthdate(patient.birthdate);

  return (
    <div>
      <Button variant="ghost" size="sm" asChild className="mb-2 -ml-2">
        <Link to="/emr/patients">
          <ArrowLeft className="size-4" /> Back to patients
        </Link>
      </Button>

      <Card className="mb-6">
        <CardContent className="flex flex-wrap items-center gap-6 pt-6">
          <div className="flex size-16 items-center justify-center rounded-full bg-primary/10 text-xl font-semibold text-primary">
            {patientName(patient)
              .split(" ")
              .map((p) => p[0])
              .slice(0, 2)
              .join("")
              .toUpperCase()}
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-semibold tracking-tight">{patientName(patient)}</h1>
              {patient.voided ? (
                <Badge variant="destructive">Voided</Badge>
              ) : (
                <Badge variant="success">Active</Badge>
              )}
            </div>
            <div className="flex flex-wrap gap-x-6 gap-y-1 text-sm text-muted-foreground">
              <span className="flex items-center gap-1.5">
                <IdCard className="size-4" />
                <span className="font-mono">{preferredIdentifier(patient) ?? "—"}</span>
              </span>
              <span className="flex items-center gap-1.5">
                <VenetianMask className="size-4" />
                {genderLabel(patient.gender)}
              </span>
              <span className="flex items-center gap-1.5">
                <CalendarDays className="size-4" />
                {formatDate(patient.birthdate)}
                {age !== null ? ` (${age} yr)` : ""}
              </span>
              <span className="flex items-center gap-1.5">
                <User className="size-4" />
                Allergies: {patient.allergy_status || "Unknown"}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="visits">
        <TabsList>
          <TabsTrigger value="visits">Visits</TabsTrigger>
          <TabsTrigger value="encounters">Encounters &amp; Observations</TabsTrigger>
          <TabsTrigger value="clinical">Clinical Records</TabsTrigger>
        </TabsList>
        <TabsContent value="visits">
          <VisitsTab patientId={patient.id} />
        </TabsContent>
        <TabsContent value="encounters">
          <EncountersTab patient={patient} />
        </TabsContent>
        <TabsContent value="clinical">
          <ClinicalTab patient={patient} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
