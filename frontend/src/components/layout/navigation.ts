import {
  Stethoscope,
  FlaskConical,
  Pill,
  ShoppingCart,
  Boxes,
  ReceiptText,
  Landmark,
  LayoutDashboard,
  type LucideIcon,
} from "lucide-react";

export interface NavItem {
  label: string;
  /** Backend vertical this maps to (see docs/packaging_architecture.md §3.3). */
  to: string;
  icon: LucideIcon;
  /** Verticals not yet built render as disabled "coming soon" entries. */
  enabled: boolean;
}

export const NAV_ITEMS: NavItem[] = [
  { label: "Dashboard", to: "/", icon: LayoutDashboard, enabled: true },
  { label: "EMR", to: "/emr/patients", icon: Stethoscope, enabled: true },
  { label: "Laboratory", to: "/lis", icon: FlaskConical, enabled: false },
  { label: "Pharmacy", to: "/pharmacy", icon: Pill, enabled: false },
  { label: "Point of Sale", to: "/pos", icon: ShoppingCart, enabled: false },
  { label: "Inventory", to: "/inventory", icon: Boxes, enabled: false },
  { label: "Billing", to: "/billing", icon: ReceiptText, enabled: false },
  { label: "Finance", to: "/finance", icon: Landmark, enabled: false },
];
