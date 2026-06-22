import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "@/features/auth/AuthContext";
import { ProtectedRoute } from "@/features/auth/ProtectedRoute";
import { LoginPage } from "@/features/auth/LoginPage";
import { AppShell } from "@/components/layout/AppShell";
import { DashboardPage } from "@/features/dashboard/DashboardPage";
import { PatientsListPage } from "@/features/emr/patients/PatientsListPage";
import { PatientRegisterPage } from "@/features/emr/patients/PatientRegisterPage";
import { PatientDetailPage } from "@/features/emr/patients/PatientDetailPage";
import { ComingSoonPage } from "@/features/placeholder/ComingSoonPage";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />

          <Route element={<ProtectedRoute />}>
            <Route element={<AppShell />}>
              <Route index element={<DashboardPage />} />

              {/* EMR vertical */}
              <Route path="emr">
                <Route index element={<Navigate to="/emr/patients" replace />} />
                <Route path="patients" element={<PatientsListPage />} />
                <Route path="patients/new" element={<PatientRegisterPage />} />
                <Route path="patients/:patientId" element={<PatientDetailPage />} />
              </Route>

              {/* Verticals on the roadmap (backend exists; UI pending). */}
              <Route path="lis" element={<ComingSoonPage title="Laboratory (LIS)" />} />
              <Route path="pharmacy" element={<ComingSoonPage title="Pharmacy" />} />
              <Route path="pos" element={<ComingSoonPage title="Point of Sale" />} />
              <Route path="inventory" element={<ComingSoonPage title="Inventory" />} />
              <Route path="billing" element={<ComingSoonPage title="Billing" />} />
              <Route path="finance" element={<ComingSoonPage title="Finance" />} />

              <Route path="*" element={<ComingSoonPage title="Page not found" />} />
            </Route>
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
