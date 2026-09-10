import type { Metadata } from 'next';
import './globals.css';
import Sidebar from '@/components/Sidebar';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'NexPharmAI — Smart Pharmaceutical Manufacturing Platform',
  description: 'AI-Powered Pharmaceutical Smart Manufacturing, Production Scheduling, Predictive Maintenance and Factory Optimization Platform',
  icons: {
    icon: '/favicon.ico',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <div className="app-container">
          <header className="navbar">
            <div className="brand-badge">
              <Link href="/dashboard" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', textDecoration: 'none' }}>
                <div className="brand-icon">NP</div>
                <div>
                  <div className="brand-title">NexPharmAI</div>
                  <div className="brand-subtitle">Smart Manufacturing OS • v2.0</div>
                </div>
              </Link>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                <span className="pulse-indicator"></span>
                <span style={{ fontWeight: 500, color: 'var(--status-running)' }}>OR-Tools Engine Live</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                <span className="pulse-indicator" style={{ background: 'var(--primary)' }}></span>
                <span style={{ fontWeight: 500, color: 'var(--primary)' }}>ML Fleet Active</span>
              </div>
              <span className="badge badge-running" style={{ padding: '0.35rem 0.75rem', fontSize: '0.8rem' }}>21 Modules Verified</span>
            </div>
          </header>
          <div className="layout-wrapper">
            <Sidebar />
            <main className="main-content">
              {children}
            </main>
          </div>
        </div>
      </body>
    </html>
  );
}
