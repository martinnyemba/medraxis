import { api } from "@/lib/api/client";
import type { Paginated } from "@/lib/api/types";
import type {
  AccountTransaction,
  Expense,
  ExpenseCategory,
  FinancialAccount,
  PartyStatement,
  PartyType,
  PurchaseBill,
  SupplierPayment,
} from "./types";

type ListParams = Record<string, string | number | boolean | undefined | null>;

export const financeApi = {
  // Accounts -----------------------------------------------------------------
  listAccounts: (params?: ListParams) =>
    api.get<Paginated<FinancialAccount>>("/finance/accounts/", params),
  createAccount: (data: Partial<FinancialAccount>) =>
    api.post<FinancialAccount>("/finance/accounts/", data),
  accountTransactions: (id: number, params?: ListParams) =>
    api.get<Paginated<AccountTransaction>>(`/finance/accounts/${id}/transactions/`, params),

  // Expense categories ---------------------------------------------------------
  listExpenseCategories: () =>
    api.get<Paginated<ExpenseCategory>>("/finance/expense-categories/", { page_size: 200 }),
  createExpenseCategory: (data: { name: string; description?: string }) =>
    api.post<ExpenseCategory>("/finance/expense-categories/", data),

  // Expenses --------------------------------------------------------------------
  listExpenses: (params?: ListParams) => api.get<Paginated<Expense>>("/finance/expenses/", params),
  createExpense: (data: Partial<Expense>) => api.post<Expense>("/finance/expenses/", data),

  // Supplier payments -------------------------------------------------------------
  listSupplierPayments: (params?: ListParams) =>
    api.get<Paginated<SupplierPayment>>("/finance/supplier-payments/", params),
  createSupplierPayment: (data: Partial<SupplierPayment>) =>
    api.post<SupplierPayment>("/finance/supplier-payments/", data),

  // Purchase bills (inventory app, surfaced here for the payables workflow) ------
  listPurchaseBills: (params?: ListParams) =>
    api.get<Paginated<PurchaseBill>>("/inventory/purchase-bills/", params),
  createPurchaseBill: (data: Partial<PurchaseBill>) =>
    api.post<PurchaseBill>("/inventory/purchase-bills/", data),

  // Party ledger -----------------------------------------------------------------
  partyBalance: (partyType: PartyType, partyId: number) =>
    api.get<{ balance: string }>("/finance/party-ledger/balance/", {
      party_type: partyType, party_id: partyId,
    }),
  partyStatement: (partyType: PartyType, partyId: number) =>
    api.get<PartyStatement>("/finance/party-ledger/statement/", {
      party_type: partyType, party_id: partyId,
    }),
};
