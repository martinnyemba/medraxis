import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Users,
  Stethoscope,
  FlaskConical,
  ShoppingCart,
  Pill,
  Boxes,
  ReceiptText,
  Landmark,
  ArrowRight,
  type LucideIcon,
} from "lucide-react";
import { emrApi } from "@/features/emr/api";
import { lisApi } from "@/features/lis/api";
import { posApi } from "@/features/pos/api";
import { pharmacyApi } from "@/features/pharmacy/api";
import { inventoryApi } from "@/features/inventory/api";
import { billingApi } from "@/features/billing/api";
import { financeApi } from "@/features/finance/api";
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
  const prescriptions = useQuery({
    queryKey: ["drug-orders", { count: true }],
    queryFn: () => pharmacyApi.listDrugOrders({ page: 1, page_size: 1 }),
  });
  const products = useQuery({
    queryKey: ["products", { count: true }],
    queryFn: () => inventoryApi.listProducts({ page: 1, page_size: 1 }),
  });
  const services = useQuery({
    queryKey: ["billing", "services", { count: true }],
    queryFn: () => billingApi.listServices({ page: 1, page_size: 1 }),
  });
  const accounts = useQuery({
    queryKey: ["finance", "accounts", { count: true }],
    queryFn: () => financeApi.listAccounts({ page: 1, page_size: 1 }),
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
        <StatCard
          icon={Pill}
          label="Prescriptions"
          value={prescriptions.data?.count ?? "—"}
          to="/pharmacy/prescriptions"
          cta="View prescriptions"
        />
        <StatCard
          icon={Boxes}
          label="Products"
          value={products.data?.count ?? "—"}
          to="/inventory/products"
          cta="View inventory"
        />
        <StatCard
          icon={ReceiptText}
          label="Billable services"
          value={services.data?.count ?? "—"}
          to="/billing/services"
          cta="View billing"
        />
        <StatCard
          icon={Landmark}
          label="Finance accounts"
          value={accounts.data?.count ?? "—"}
          to="/finance/accounts"
          cta="View finance"
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
        <ModuleCard
          icon={Pill}
          title="Pharmacy"
          to="/pharmacy/prescriptions"
          cta="Go to pharmacy"
          description="Prescribe medications on the patient timeline and dispense against prescriptions, issuing stock from the shared ledger."
        />
        <ModuleCard
          icon={Boxes}
          title="Inventory"
          to="/inventory/products"
          cta="Go to inventory"
          description="Manage products, receive stock into batches, track the append-only stock ledger, suppliers and purchase orders."
        />
        <ModuleCard
          icon={ReceiptText}
          title="Billing"
          to="/billing/services"
          cta="Go to billing"
          description="Price chargeable clinical services and manage the insurance schemes and patient policies that pay for them."
        />
        <ModuleCard
          icon={Landmark}
          title="Finance"
          to="/finance/accounts"
          cta="Go to finance"
          description="Track cash/bank accounts, record expenses and supplier payments, and watch every customer's and supplier's running balance."
        />
      </div>
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
