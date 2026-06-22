import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Users,
  Stethoscope,
  FlaskConical,
  ShoppingCart,
  ArrowRight,
  type LucideIcon,
} from "lucide-react";
import { emrApi } from "@/features/emr/api";
import { lisApi } from "@/features/lis/api";
import { posApi } from "@/features/pos/api";
import { useAuth } from "@/features/auth/AuthContext";
import { useTenant } from "@/features/tenancy/TenantContext";
import { PageHeader } from "@/components/common/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export function DashboardPage() {
  const { user } = useAuth();
  const { current } = useTenant();

  const patients = useQuery({
    queryKey: ["patients", { page: 1, count: true }],
    queryFn: () => emrApi.listPatients({ page: 1, page_size: 1 }),
  });
  const labOrders = useQuery({
    queryKey: ["lab-orders", { count: true }],
    queryFn: () => lisApi.listOrders({ page: 1, page_size: 1 }),
  });
  const sales = useQuery({
    queryKey: ["sales", { count: true }],
    queryFn: () => posApi.listSales({ page: 1, page_size: 1 }),
  });

  const greeting = user?.first_name ? `Welcome back, ${user.first_name}` : "Welcome back";

  return (
    <div>
      <PageHeader
        title={greeting}
        description={current ? `You are working in ${current.name}.` : undefined}
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <StatCard
          icon={Users}
          label="Registered patients"
          value={patients.data?.count ?? "—"}
          to="/emr/patients"
          cta="View patients"
        />
        <StatCard
          icon={FlaskConical}
          label="Lab orders"
          value={labOrders.data?.count ?? "—"}
          to="/lis/worklist"
          cta="Open worklist"
        />
        <StatCard
          icon={ShoppingCart}
          label="Sales"
          value={sales.data?.count ?? "—"}
          to="/pos/sales"
          cta="View sales"
        />
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-3">
        <ModuleCard
          icon={Stethoscope}
          title="EMR"
          to="/emr/patients"
          cta="Go to EMR"
          description="Register patients, open visits, document encounters and capture observations against the shared concept dictionary."
        />
        <ModuleCard
          icon={FlaskConical}
          title="Laboratory"
          to="/lis/worklist"
          cta="Go to lab"
          description="Order tests, accession specimens, and run the result worksheet through enter → verify → release onto the patient chart."
        />
        <ModuleCard
          icon={ShoppingCart}
          title="Point of Sale"
          to="/pos/sales"
          cta="Go to POS"
          description="Ring up product sales, draw down stock on completion, take payments and print GST-ready receipts."
        />
      </div>

      <p className="mt-6 text-sm text-muted-foreground">
        Pharmacy, Inventory, Billing and Finance share the same patient timeline and stock ledger
        and are coming next.
      </p>
    </div>
  );
}

function StatCard({
  icon: Icon,
  label,
  value,
  to,
  cta,
}: {
  icon: LucideIcon;
  label: string;
  value: number | string;
  to: string;
  cta: string;
}) {
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle>
        <Icon className="size-4 text-primary" />
      </CardHeader>
      <CardContent>
        <div className="text-3xl font-semibold">{value}</div>
        <Button asChild variant="link" className="mt-1 h-auto p-0 text-sm">
          <Link to={to}>
            {cta} <ArrowRight className="size-3" />
          </Link>
        </Button>
      </CardContent>
    </Card>
  );
}

function ModuleCard({
  icon: Icon,
  title,
  description,
  to,
  cta,
}: {
  icon: LucideIcon;
  title: string;
  description: string;
  to: string;
  cta: string;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Icon className="size-4 text-primary" /> {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-sm text-muted-foreground">{description}</p>
        <Button asChild variant="outline" size="sm">
          <Link to={to}>
            {cta} <ArrowRight className="size-4" />
          </Link>
        </Button>
      </CardContent>
    </Card>
  );
}
