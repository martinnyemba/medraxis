import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Users, Stethoscope, ArrowRight } from "lucide-react";
import { emrApi } from "@/features/emr/api";
import { useAuth } from "@/features/auth/AuthContext";
import { useTenant } from "@/features/tenancy/TenantContext";
import { PageHeader } from "@/components/common/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export function DashboardPage() {
  const { user } = useAuth();
  const { current } = useTenant();

  const { data: patients } = useQuery({
    queryKey: ["patients", { page: 1, count: true }],
    queryFn: () => emrApi.listPatients({ page: 1, page_size: 1 }),
  });

  const greeting = user?.first_name ? `Welcome back, ${user.first_name}` : "Welcome back";

  return (
    <div>
      <PageHeader
        title={greeting}
        description={current ? `You are working in ${current.name}.` : undefined}
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader className="flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Registered patients
            </CardTitle>
            <Users className="size-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-semibold">{patients?.count ?? "—"}</div>
            <Button asChild variant="link" className="mt-1 h-auto p-0 text-sm">
              <Link to="/emr/patients">
                View patients <ArrowRight className="size-3" />
              </Link>
            </Button>
          </CardContent>
        </Card>

        <Card className="sm:col-span-2 lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Stethoscope className="size-4 text-primary" /> Electronic Medical Records
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-muted-foreground">
            <p>
              The EMR module is live: register patients, open visits, document encounters and
              capture observations against the shared OpenMRS-style concept dictionary.
            </p>
            <p>
              Laboratory, Pharmacy, POS, Inventory, Billing and Finance modules share the same
              patient timeline and stock ledger and are coming next.
            </p>
            <Button asChild>
              <Link to="/emr/patients">
                Go to EMR <ArrowRight className="size-4" />
              </Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
