/**
 * LEDGER — App Shell / Layout
 * Navigation sidebar, top bar, protected routes.
 */
import { Outlet, Link, useLocation, Navigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useAuthStore } from '../store/authStore'

const NAV_ITEMS = [
  { path: '/dashboard', label: 'Command Center', icon: '⬡' },
  { path: '/applications', label: 'Applications', icon: '◈' },
]

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore()
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function AppShell() {
  const { user, logout } = useAuthStore()
  const location = useLocation()

  return (
    <div className="flex h-screen overflow-hidden" style={{ background: 'var(--color-bg-primary)' }}>
      {/* Sidebar */}
      <aside className="w-56 flex flex-col flex-shrink-0"
        style={{ background: 'var(--color-bg-secondary)', borderRight: '1px solid var(--color-border)' }}>

        {/* Logo */}
        <div className="px-5 py-5" style={{ borderBottom: '1px solid var(--color-border)' }}>
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0"
              style={{ background: 'linear-gradient(135deg, #0891b2, #3b82f6)', boxShadow: '0 0 14px rgba(0,212,224,0.25)' }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5">
                <path d="M2 12h5M7 7l5 5-5 5M17 7l5 5-5 5" />
              </svg>
            </div>
            <div>
              <div className="text-sm font-bold tracking-tight text-gradient">LEDGER</div>
              <div className="text-[10px]" style={{ color: 'var(--color-text-tertiary)' }}>Credit Intelligence</div>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 p-3 space-y-0.5">
          {NAV_ITEMS.map((item) => {
            const active = location.pathname.startsWith(item.path)
            return (
              <Link
                key={item.path}
                to={item.path}
                className="flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm font-medium transition-all"
                style={{
                  color: active ? 'var(--color-accent-cyan)' : 'var(--color-text-secondary)',
                  background: active ? 'var(--color-accent-cyan-dim)' : 'transparent',
                }}
              >
                <span className="text-base leading-none">{item.icon}</span>
                {item.label}
              </Link>
            )
          })}

          <div className="pt-3" style={{ borderTop: '1px solid var(--color-border)' }}>
            <p className="px-3 text-[10px] font-semibold uppercase tracking-widest mb-2"
              style={{ color: 'var(--color-text-tertiary)' }}>
              System
            </p>
            {user?.role === 'demo_admin' && (
              <Link
                to="/demo"
                className="flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm font-medium transition-all"
                style={{
                  color: location.pathname === '/demo' ? 'var(--color-accent-amber)' : 'var(--color-text-secondary)',
                  background: location.pathname === '/demo' ? 'rgba(245,158,11,0.08)' : 'transparent',
                }}
              >
                <span className="text-base leading-none">⚙</span>
                Demo Panel
              </Link>
            )}
          </div>
        </nav>

        {/* User */}
        <div className="p-3" style={{ borderTop: '1px solid var(--color-border)' }}>
          <div className="flex items-center gap-2.5 px-2 py-2 rounded-lg"
            style={{ background: 'var(--color-bg-tertiary)' }}>
            <div className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0"
              style={{ background: 'linear-gradient(135deg, #0891b2, #3b82f6)', color: 'white' }}>
              {user?.display_name?.[0] ?? 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-xs font-medium truncate">{user?.display_name}</div>
              <div className="text-[10px] truncate" style={{ color: 'var(--color-text-tertiary)' }}>
                {user?.role?.replace('_', ' ')}
              </div>
            </div>
            <button
              id="logout-btn"
              onClick={logout}
              className="btn-ghost p-1.5"
              title="Sign out"
            >
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9" />
              </svg>
            </button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        <motion.div
          key={location.pathname}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.2 }}
          className="min-h-full"
        >
          <Outlet />
        </motion.div>
      </main>
    </div>
  )
}
