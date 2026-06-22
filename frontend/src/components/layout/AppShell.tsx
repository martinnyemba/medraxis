import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { OrgSwitcher } from "./OrgSwitcher";
import { UserMenu } from "./UserMenu";
import { TenantProvider } from "@/features/tenancy/TenantContext";

export function AppShell() {
  return (
    <TenantProvider>
      <div className="flex h-screen overflow-hidden bg-background">
        <Sidebar />
        <div className="flex flex-1 flex-col overflow-hidden">
          <header className="flex h-16 shrink-0 items-center justify-between gap-4 border-b bg-card px-6">
            <div className="md:hidden">
              <span className="font-semibold">Medraxis</span>
            </div>
            <div className="ml-auto flex items-center gap-4">
              <OrgSwitcher />
              <UserMenu />
            </div>
          </header>
          <main className="flex-1 overflow-y-auto">
            <div className="mx-auto max-w-7xl px-6 py-8">
              <Outlet />
            </div>
          </main>
        </div>
      </div>
    </TenantProvider>
  );
}
