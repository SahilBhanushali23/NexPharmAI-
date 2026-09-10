'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Cpu,
  CalendarDays,
  Boxes,
  Package,
  Wrench,
  AlertTriangle,
  FlaskConical,
  TrendingUp,
  BarChart3,
  Bot
} from 'lucide-react';

const NAV_ITEMS = [
  { label: 'Executive Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { label: 'Machine Fleet & IoT', href: '/machines', icon: Cpu },
  { label: 'AI Production Scheduler', href: '/scheduler', icon: CalendarDays },
  { label: 'Orders & Batch Control', href: '/production', icon: Boxes },
  { label: 'Raw Material Inventory', href: '/inventory', icon: Package },
  { label: 'Maintenance & Work Orders', href: '/maintenance', icon: Wrench },
  { label: 'Alert Notification Center', href: '/alerts', icon: AlertTriangle },
  { label: 'Batch Quality Prediction', href: '/quality', icon: FlaskConical },
  { label: 'Demand Forecasting', href: '/forecasting', icon: TrendingUp },
  { label: 'OEE & Factory Analytics', href: '/analytics', icon: BarChart3 },
  { label: 'AI Decision Assistant', href: '/assistant', icon: Bot },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="sidebar">
      <div className="sidebar-title">Manufacturing OS</div>
      <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href || (item.href !== '/dashboard' && pathname.startsWith(item.href));
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`nav-link ${isActive ? 'active' : ''}`}
            >
              <Icon size={18} style={{ color: isActive ? 'var(--primary)' : 'inherit' }} />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
