import { Suspense, lazy, type ComponentType } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "@/features/auth/AuthContext";
import { ProtectedRoute } from "@/features/auth/ProtectedRoute";
import { LoginPage } from "@/features/auth/LoginPage";
import { AppShell } from "@/components/layout/AppShell";
import { PageLoader } from "@/components/ui/spinner";

// Page-level components are code-split per vertical so each module's bundle
// loads on demand (mirrors the backend's vertical boundaries).
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const named = <T extends Record<string, ComponentType<any>>>(
  loader: () => Promise<T>,
  key: keyof T,
) => lazy(() => loader().then((m) => ({ default: m[key] })));

const DashboardPage = named(() => import("@/features/dashboard/DashboardPage"), "DashboardPage");
const PatientsListPage = named(() => import("@/features/emr/patients/PatientsListPage"), "PatientsListPage");
const PatientRegisterPage = named(() => import("@/features/emr/patients/PatientRegisterPage"), "PatientRegisterPage");
const PatientDetailPage = named(() => import("@/features/emr/patients/PatientDetailPage"), "PatientDetailPage");
const CohortsListPage = named(() => import("@/features/emr/cohorts/CohortsListPage"), "CohortsListPage");
const CohortDetailPage = named(() => import("@/features/emr/cohorts/CohortDetailPage"), "CohortDetailPage");
const LabWorklistPage = named(() => import("@/features/lis/LabWorklistPage"), "LabWorklistPage");
const NewLabOrderPage = named(() => import("@/features/lis/NewLabOrderPage"), "NewLabOrderPage");
const LabOrderDetailPage = named(() => import("@/features/lis/LabOrderDetailPage"), "LabOrderDetailPage");
const TestCatalogPage = named(() => import("@/features/lis/TestCatalogPage"), "TestCatalogPage");
const SalesListPage = named(() => import("@/features/pos/SalesListPage"), "SalesListPage");
const NewSalePage = named(() => import("@/features/pos/NewSalePage"), "NewSalePage");
const SaleDetailPage = named(() => import("@/features/pos/SaleDetailPage"), "SaleDetailPage");
const CustomersPage = named(() => import("@/features/pos/CustomersPage"), "CustomersPage");
const SalesReturnsPage = named(() => import("@/features/pos/SalesReturnsPage"), "SalesReturnsPage");
const PrescriptionsListPage = named(() => import("@/features/pharmacy/PrescriptionsListPage"), "PrescriptionsListPage");
const NewPrescriptionPage = named(() => import("@/features/pharmacy/NewPrescriptionPage"), "NewPrescriptionPage");
const PrescriptionDetailPage = named(() => import("@/features/pharmacy/PrescriptionDetailPage"), "PrescriptionDetailPage");
const ProductsListPage = named(() => import("@/features/inventory/ProductsListPage"), "ProductsListPage");
const ProductDetailPage = named(() => import("@/features/inventory/ProductDetailPage"), "ProductDetailPage");
const SuppliersPage = named(() => import("@/features/inventory/SuppliersPage"), "SuppliersPage");
const StockLedgerPage = named(() => import("@/features/inventory/StockLedgerPage"), "StockLedgerPage");
const ExpiringBatchesPage = named(() => import("@/features/inventory/ExpiringBatchesPage"), "ExpiringBatchesPage");
const PurchaseOrdersPage = named(() => import("@/features/inventory/PurchaseOrdersPage"), "PurchaseOrdersPage");
const BillableServicesPage = named(() => import("@/features/billing/BillableServicesPage"), "BillableServicesPage");
const InsurancePage = named(() => import("@/features/billing/InsurancePage"), "InsurancePage");
const AccountsPage = named(() => import("@/features/finance/AccountsPage"), "AccountsPage");
const ExpensesPage = named(() => import("@/features/finance/ExpensesPage"), "ExpensesPage");
const PurchaseBillsPage = named(() => import("@/features/finance/PurchaseBillsPage"), "PurchaseBillsPage");
const SupplierPaymentsPage = named(() => import("@/features/finance/SupplierPaymentsPage"), "SupplierPaymentsPage");
const PartyLedgerPage = named(() => import("@/features/finance/PartyLedgerPage"), "PartyLedgerPage");
const ComingSoonPage = named(() => import("@/features/placeholder/ComingSoonPage"), "ComingSoonPage");

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />

          <Route element={<ProtectedRoute />}>
            <Route
              element={
                <AppShell />
              }
            >
              <Route
                index
                element={
                  <Suspense fallback={<PageLoader />}>
                    <DashboardPage />
                  </Suspense>
                }
              />

              {/* EMR vertical */}
              <Route
                path="emr/*"
                element={
                  <Suspense fallback={<PageLoader />}>
                    <Routes>
                      <Route index element={<Navigate to="patients" replace />} />
                      <Route path="patients" element={<PatientsListPage />} />
                      <Route path="patients/new" element={<PatientRegisterPage />} />
                      <Route path="patients/:patientId" element={<PatientDetailPage />} />
                      <Route path="cohorts" element={<CohortsListPage />} />
                      <Route path="cohorts/:cohortId" element={<CohortDetailPage />} />
                    </Routes>
                  </Suspense>
                }
              />

              {/* LIS vertical */}
              <Route
                path="lis/*"
                element={
                  <Suspense fallback={<PageLoader />}>
                    <Routes>
                      <Route index element={<Navigate to="worklist" replace />} />
                      <Route path="worklist" element={<LabWorklistPage />} />
                      <Route path="orders/new" element={<NewLabOrderPage />} />
                      <Route path="orders/:orderId" element={<LabOrderDetailPage />} />
                      <Route path="catalog" element={<TestCatalogPage />} />
                    </Routes>
                  </Suspense>
                }
              />

              {/* POS vertical */}
              <Route
                path="pos/*"
                element={
                  <Suspense fallback={<PageLoader />}>
                    <Routes>
                      <Route index element={<Navigate to="sales" replace />} />
                      <Route path="sales" element={<SalesListPage />} />
                      <Route path="sales/new" element={<NewSalePage />} />
                      <Route path="sales/:saleId" element={<SaleDetailPage />} />
                      <Route path="returns" element={<SalesReturnsPage />} />
                      <Route path="customers" element={<CustomersPage />} />
                    </Routes>
                  </Suspense>
                }
              />

              {/* Pharmacy vertical */}
              <Route
                path="pharmacy/*"
                element={
                  <Suspense fallback={<PageLoader />}>
                    <Routes>
                      <Route index element={<Navigate to="prescriptions" replace />} />
                      <Route path="prescriptions" element={<PrescriptionsListPage />} />
                      <Route path="prescriptions/new" element={<NewPrescriptionPage />} />
                      <Route path="prescriptions/:orderId" element={<PrescriptionDetailPage />} />
                    </Routes>
                  </Suspense>
                }
              />

              {/* Inventory vertical */}
              <Route
                path="inventory/*"
                element={
                  <Suspense fallback={<PageLoader />}>
                    <Routes>
                      <Route index element={<Navigate to="products" replace />} />
                      <Route path="products" element={<ProductsListPage />} />
                      <Route path="products/:productId" element={<ProductDetailPage />} />
                      <Route path="suppliers" element={<SuppliersPage />} />
                      <Route path="ledger" element={<StockLedgerPage />} />
                      <Route path="expiring-batches" element={<ExpiringBatchesPage />} />
                      <Route path="purchase-orders" element={<PurchaseOrdersPage />} />
                    </Routes>
                  </Suspense>
                }
              />

              {/* Billing vertical */}
              <Route
                path="billing/*"
                element={
                  <Suspense fallback={<PageLoader />}>
                    <Routes>
                      <Route index element={<Navigate to="services" replace />} />
                      <Route path="services" element={<BillableServicesPage />} />
                      <Route path="insurance" element={<InsurancePage />} />
                    </Routes>
                  </Suspense>
                }
              />

              {/* Finance vertical */}
              <Route
                path="finance/*"
                element={
                  <Suspense fallback={<PageLoader />}>
                    <Routes>
                      <Route index element={<Navigate to="accounts" replace />} />
                      <Route path="accounts" element={<AccountsPage />} />
                      <Route path="expenses" element={<ExpensesPage />} />
                      <Route path="purchase-bills" element={<PurchaseBillsPage />} />
                      <Route path="supplier-payments" element={<SupplierPaymentsPage />} />
                      <Route path="party-ledger" element={<PartyLedgerPage />} />
                    </Routes>
                  </Suspense>
                }
              />

              <Route
                path="*"
                element={
                  <Suspense fallback={<PageLoader />}>
                    <ComingSoonPage title="Page not found" />
                  </Suspense>
                }
              />
            </Route>
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
