import * as React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowLeft, Minus, Plus, Search, ShoppingCart, Trash2 } from "lucide-react";
import { posApi } from "./api";
import type { LineType, SaleLine } from "./types";
import { inventoryApi } from "@/features/inventory/api";
import { lisApi } from "@/features/lis/api";
import { billingApi } from "@/features/billing/api";
import { useLocations } from "@/features/emr/queries";
import type { Patient } from "@/features/emr/types";
import { ApiError } from "@/lib/api/types";
import { money } from "@/lib/format";
import { useDebounce } from "@/lib/hooks";
import { useTenant } from "@/features/tenancy/TenantContext";
import { useToast } from "@/components/ui/toast";
import { PageHeader } from "@/components/common/PageHeader";
import { PatientCombobox } from "@/components/common/PatientCombobox";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

type ItemKind = "product" | "lab_test" | "service";

interface CartItem {
  kind: ItemKind;
  id: number;
  name: string;
  price: number;
  quantity: number;
}

const LINE_TYPE: Record<ItemKind, LineType> = {
  product: "PRODUCT",
  lab_test: "LAB_TEST",
  service: "SERVICE",
};

function itemKey(kind: ItemKind, id: number) {
  return `${kind}-${id}`;
}

export function NewSalePage() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { current } = useTenant();
  const currency = current?.currency;

  const locations = useLocations();
  const [patient, setPatient] = React.useState<Patient | null>(null);
  const [cart, setCart] = React.useState<CartItem[]>([]);
  const [note, setNote] = React.useState("");
  const [locationId, setLocationId] = React.useState<string>("");
  const [formError, setFormError] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (!locationId && locations.data && locations.data.length > 0) {
      setLocationId(String(locations.data[0].id));
    }
  }, [locationId, locations.data]);

  function addItem(item: Omit<CartItem, "quantity">) {
    setCart((prev) => {
      const existing = prev.find((i) => i.kind === item.kind && i.id === item.id);
      if (existing) {
        return prev.map((i) =>
          i.kind === item.kind && i.id === item.id ? { ...i, quantity: i.quantity + 1 } : i,
        );
      }
      return [...prev, { ...item, quantity: 1 }];
    });
  }

  function setQuantity(key: string, quantity: number) {
    setCart((prev) =>
      quantity <= 0
        ? prev.filter((i) => itemKey(i.kind, i.id) !== key)
        : prev.map((i) => (itemKey(i.kind, i.id) === key ? { ...i, quantity } : i)),
    );
  }

  const estimatedTotal = cart.reduce((sum, i) => sum + i.price * i.quantity, 0);
  const hasLab = cart.some((i) => i.kind === "lab_test");

  const create = useMutation({
    mutationFn: () => {
      const lines: SaleLine[] = cart.map((i) => ({
        line_type: LINE_TYPE[i.kind],
        product: i.kind === "product" ? i.id : null,
        lab_test: i.kind === "lab_test" ? i.id : null,
        billable_service: i.kind === "service" ? i.id : null,
        description: i.name,
        quantity: String(i.quantity),
      }));
      return posApi.createSale({
        lines,
        note,
        patient: patient ? patient.id : null,
        location: locationId ? Number(locationId) : null,
      });
    },
    onSuccess: (sale) => {
      toast({ title: `Sale ${sale.invoice_number} created`, variant: "success" });
      navigate(`/pos/sales/${sale.id}`);
    },
    onError: (err) =>
      setFormError(err instanceof ApiError ? err.toUserMessage() : "Could not create sale."),
  });

  function submit() {
    setFormError(null);
    if (cart.length === 0) return setFormError("Add at least one item.");
    if (hasLab && !patient)
      return setFormError("Select a patient — lab tests open a lab order on the patient's chart.");
    create.mutate();
  }

  return (
    <div>
      <Button variant="ghost" size="sm" asChild className="mb-2 -ml-2">
        <Link to="/pos/sales">
          <ArrowLeft className="size-4" /> Back to sales
        </Link>
      </Button>
      <PageHeader
        title="New sale"
        description="Bill products, lab tests and services on one invoice."
      />

      <div className="grid gap-6 lg:grid-cols-[1fr_22rem]">
        <ItemSearch onAdd={addItem} currency={currency} />

        <Card className="h-fit lg:sticky lg:top-4">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <ShoppingCart className="size-4 text-primary" /> Cart ({cart.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {cart.length === 0 ? (
              <p className="py-6 text-center text-sm text-muted-foreground">Add items to begin.</p>
            ) : (
              <ul className="space-y-3">
                {cart.map((item) => {
                  const key = itemKey(item.kind, item.id);
                  return (
                    <li key={key} className="flex items-center gap-2">
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-medium">{item.name}</p>
                        <p className="text-xs text-muted-foreground">
                          {money(item.price, currency)} each · {KIND_LABEL[item.kind]}
                        </p>
                      </div>
                      <div className="flex items-center gap-1">
                        <Button size="icon" variant="outline" className="size-7"
                          onClick={() => setQuantity(key, item.quantity - 1)}>
                          <Minus className="size-3" />
                        </Button>
                        <span className="w-7 text-center text-sm">{item.quantity}</span>
                        <Button size="icon" variant="outline" className="size-7"
                          onClick={() => setQuantity(key, item.quantity + 1)}>
                          <Plus className="size-3" />
                        </Button>
                        <Button size="icon" variant="ghost" className="size-7 text-destructive"
                          onClick={() => setQuantity(key, 0)}>
                          <Trash2 className="size-3" />
                        </Button>
                      </div>
                    </li>
                  );
                })}
              </ul>
            )}

            <div className="space-y-2 border-t pt-4">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Estimated subtotal</span>
                <span className="font-medium">{money(estimatedTotal, currency)}</span>
              </div>
              <p className="text-xs text-muted-foreground">
                Final totals (tax, catalogue/rate-card pricing) are calculated by the server.
              </p>
            </div>

            <div className="space-y-1.5">
              <Label className="text-xs">
                Patient {hasLab && <span className="text-destructive">*</span>}
              </Label>
              <PatientCombobox value={patient} onSelect={setPatient} />
              {hasLab && (
                <p className="text-xs text-muted-foreground">
                  Required: lab tests open an order on the patient's chart.
                </p>
              )}
            </div>

            <div className="space-y-1.5">
              <Label className="text-xs">Sales location (stock source)</Label>
              <Select value={locationId} onValueChange={setLocationId}>
                <SelectTrigger>
                  <SelectValue placeholder="Select location" />
                </SelectTrigger>
                <SelectContent>
                  {locations.data?.map((l) => (
                    <SelectItem key={l.id} value={String(l.id)}>
                      {l.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <Input
              placeholder="Note (optional)"
              value={note}
              onChange={(e) => setNote(e.target.value)}
            />

            {formError && (
              <p className="whitespace-pre-line rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
                {formError}
              </p>
            )}

            <Button className="w-full" disabled={cart.length === 0 || create.isPending} onClick={submit}>
              {create.isPending ? <Spinner className="size-4" /> : "Create sale"}
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

const KIND_LABEL: Record<ItemKind, string> = {
  product: "Product",
  lab_test: "Lab test",
  service: "Service",
};

function ItemSearch({
  onAdd,
  currency,
}: {
  onAdd: (item: Omit<CartItem, "quantity">) => void;
  currency?: string;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Catalogue</CardTitle>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="product">
          <TabsList>
            <TabsTrigger value="product">Products</TabsTrigger>
            <TabsTrigger value="lab_test">Lab tests</TabsTrigger>
            <TabsTrigger value="service">Services</TabsTrigger>
          </TabsList>
          <TabsContent value="product">
            <ProductResults onAdd={onAdd} currency={currency} />
          </TabsContent>
          <TabsContent value="lab_test">
            <LabTestResults onAdd={onAdd} currency={currency} />
          </TabsContent>
          <TabsContent value="service">
            <ServiceResults onAdd={onAdd} currency={currency} />
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}

function SearchBox({ value, onChange, placeholder }: {
  value: string; onChange: (v: string) => void; placeholder: string;
}) {
  return (
    <div className="relative my-4">
      <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
      <Input autoFocus placeholder={placeholder} className="pl-9"
        value={value} onChange={(e) => onChange(e.target.value)} />
    </div>
  );
}

function ResultRow({ name, sub, badge, onAdd }: {
  name: string; sub: string; badge?: React.ReactNode; onAdd: () => void;
}) {
  return (
    <li className="flex items-center justify-between gap-3 py-2.5">
      <div className="min-w-0">
        <p className="truncate text-sm font-medium">{name}</p>
        <p className="text-xs text-muted-foreground">{sub}</p>
      </div>
      <div className="flex items-center gap-2">
        {badge}
        <Button size="sm" variant="outline" onClick={onAdd}>
          <Plus className="size-3" /> Add
        </Button>
      </div>
    </li>
  );
}

function ProductResults({ onAdd, currency }: {
  onAdd: (i: Omit<CartItem, "quantity">) => void; currency?: string;
}) {
  const [input, setInput] = React.useState("");
  const search = useDebounce(input, 300);
  const { data, isFetching } = useQuery({
    queryKey: ["products", { search }],
    queryFn: () => inventoryApi.listProducts({ search, page_size: 20 }),
  });
  return (
    <>
      <SearchBox value={input} onChange={setInput} placeholder="Search products by name, SKU or barcode…" />
      <ResultList isFetching={isFetching} count={data?.results.length}>
        {data?.results.map((p) => (
          <ResultRow key={p.id} name={p.name}
            sub={`${p.sku || "—"} · ${money(p.sale_price, currency)} · stock ${p.quantity_on_hand}`}
            badge={p.quantity_on_hand <= 0 ? <Badge variant="warning">No stock</Badge> : undefined}
            onAdd={() => onAdd({ kind: "product", id: p.id, name: p.name, price: Number(p.sale_price) })}
          />
        ))}
      </ResultList>
    </>
  );
}

function LabTestResults({ onAdd, currency }: {
  onAdd: (i: Omit<CartItem, "quantity">) => void; currency?: string;
}) {
  const [input, setInput] = React.useState("");
  const search = useDebounce(input, 300);
  const { data, isFetching } = useQuery({
    queryKey: ["lab-tests-search", { search }],
    queryFn: () => lisApi.listTests({ search, page_size: 20, retired: false }),
  });
  return (
    <>
      <SearchBox value={input} onChange={setInput} placeholder="Search lab tests by name or code…" />
      <ResultList isFetching={isFetching} count={data?.results.length}>
        {data?.results.map((t) => (
          <ResultRow key={t.id} name={t.name}
            sub={`${t.test_code} · ${money(t.price, currency)}`}
            onAdd={() => onAdd({ kind: "lab_test", id: t.id, name: t.name, price: Number(t.price) })}
          />
        ))}
      </ResultList>
    </>
  );
}

function ServiceResults({ onAdd, currency }: {
  onAdd: (i: Omit<CartItem, "quantity">) => void; currency?: string;
}) {
  const [input, setInput] = React.useState("");
  const search = useDebounce(input, 300);
  const { data, isFetching } = useQuery({
    queryKey: ["billing-services-search", { search }],
    queryFn: () => billingApi.listServices({ search, page_size: 20 }),
  });
  return (
    <>
      <SearchBox value={input} onChange={setInput} placeholder="Search services by name or code…" />
      <ResultList isFetching={isFetching} count={data?.results.length}>
        {data?.results.map((s) => (
          <ResultRow key={s.id} name={s.name}
            sub={`${s.service_code} · ${money(s.price, currency)}`}
            onAdd={() => onAdd({ kind: "service", id: s.id, name: s.name, price: Number(s.price) })}
          />
        ))}
      </ResultList>
    </>
  );
}

function ResultList({ isFetching, count, children }: {
  isFetching: boolean; count?: number; children: React.ReactNode;
}) {
  if (isFetching && !count)
    return <p className="py-6 text-center text-sm text-muted-foreground">Searching…</p>;
  if (!count)
    return <p className="py-6 text-center text-sm text-muted-foreground">No matches. Search to add items.</p>;
  return <ul className="divide-y">{children}</ul>;
}
