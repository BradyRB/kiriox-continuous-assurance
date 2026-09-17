import type { ButtonHTMLAttributes, ReactNode } from "react";
import { ArrowRight, Check, CircleAlert, LoaderCircle } from "lucide-react";

export function Button({ children, variant = "primary", icon, ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "secondary" | "ghost" | "danger"; icon?: ReactNode }) {
  return <button className={`ui-button ui-button-${variant}`} {...props}>{children}{icon ?? (variant === "primary" ? <ArrowRight size={16} aria-hidden="true" /> : null)}</button>;
}

export function Card({ children, className = "", id }: { children: ReactNode; className?: string; id?: string }) {
  return <section id={id} className={`ui-card ${className}`}>{children}</section>;
}

export function DataTable({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <div className={`data-table ${className}`}>{children}</div>;
}

export function StatusBadge({ status }: { status: string }) {
  const normalized = status.toLowerCase();
  return <span className={`status-badge status-${normalized}`}><i />{status.replaceAll("_", " ")}</span>;
}

export function EmptyState({ title, description, action }: { title: string; description: string; action?: ReactNode }) {
  return <div className="ui-empty"><div className="ui-empty-symbol"><CircleAlert size={24} strokeWidth={1.5} aria-hidden="true" /></div><h3>{title}</h3><p>{description}</p>{action}</div>;
}

export function PageHeader({ eyebrow, title, description, action }: { eyebrow: string; title: string; description: string; action?: ReactNode }) {
  return <header className="page-header"><div><p className="eyebrow">{eyebrow}</p><h1>{title}</h1><p className="sub">{description}</p></div>{action}</header>;
}

export function Stepper({ steps, current }: { steps: string[]; current: number }) {
  return <div className="ui-stepper" aria-label="Progreso del wizard">{steps.map((step, index) => <div className={`ui-step ${index === current ? "current" : ""} ${index < current ? "done" : ""}`} key={step}><span>{index < current ? <Check size={13} aria-hidden="true" /> : String(index + 1).padStart(2, "0")}</span><small>{step}</small>{index < steps.length - 1 && <i />}</div>)}</div>;
}

export function MetricCard({ label, value, note, tone = "default" }: { label: string; value: string | number; note?: string; tone?: string }) {
  return <div className={`metric-card metric-${tone}`}><span>{label}</span><strong>{value}</strong>{note && <small>{note}</small>}</div>;
}

export function LoadingState({ label = "Cargando" }: { label?: string }) {
  return <div className="loading-state"><LoaderCircle size={16} className="spin" aria-hidden="true" /> {label}</div>;
}
