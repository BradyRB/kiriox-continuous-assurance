"use client";

import type { ReactNode } from "react";
import { Activity, CalendarClock, Database, History, Settings2, ShieldAlert } from "lucide-react";

const items = [
  { label: "Fuentes de datos", count: true, icon: Database },
  { label: "Explorador PostgreSQL", icon: Activity },
  { label: "Historial de ejecuciones", icon: History },
  { label: "Excepciones", icon: ShieldAlert },
  { label: "Schedules", icon: CalendarClock },
  { label: "Configuración", icon: Settings2 },
];

export function AppShell({ children, active, sourceCount, onNavigate }: { children: ReactNode; active: string; sourceCount: number; onNavigate: (item: string) => void }) {
  return <main className="app-shell">
    <aside className="sidebar">
      <div className="brand-lockup"><div className="brand-wordmark">KIRIOX</div><div className="brand-submark">CONTINUOUS ASSURANCE</div></div>
      <div className="sidebar-context"><span className="status-dot" /> LOCAL INSTANCE <small>CONTROL PLANE</small></div>
      <nav className="sidebar-nav" aria-label="Navegación principal">{items.map(({ label, count, icon: Icon }) => <button aria-current={active === label ? "page" : undefined} className={`nav-item ${active === label ? "active" : ""}`} key={label} onClick={() => onNavigate(label)}><Icon size={17} strokeWidth={1.8} aria-hidden="true" /><span>{label}</span>{count && <b>{sourceCount}</b>}</button>)}</nav>
      <div className="sidebar-footer"><div className="sidebar-footer-line" /><span>DATOS EN ESTE EQUIPO</span><small>Sin telemetría externa</small></div>
    </aside>
    <section className="content"><nav className="mobile-nav" aria-label="Navegación móvil">{items.map(({ label, count, icon: Icon }) => <button className={active === label ? "active" : ""} key={label} onClick={() => onNavigate(label)}><Icon size={15} aria-hidden="true" /> {label}{count && <b>{sourceCount}</b>}</button>)}</nav>{children}<footer><span>Kiriox Continuous Assurance <b>LOCAL</b></span><span>v0.3.0 · Sin telemetría externa</span></footer></section>
  </main>;
}
