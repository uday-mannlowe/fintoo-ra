// src/components/Layout.jsx
import React, { useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { LayoutDashboard, MessageSquare, TrendingUp, LogOut, Menu, X, FilePlus2 } from 'lucide-react'

const nav = [
  { to: '/',        icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/updates', icon: FilePlus2,       label: 'Updates'   },
  { to: '/chat',    icon: MessageSquare,   label: 'CFO Chat'  },
  { to: '/history', icon: TrendingUp,      label: 'History'   },
]

export default function Layout({ children, userId, onLogout }) {
  const [open, setOpen] = useState(false)
  const navigate = useNavigate()

  const doLogout = () => { onLogout(); navigate('/') }

  return (
    <div className="min-h-screen flex" style={{ background: 'var(--paper)' }}>
      {/* ── Sidebar ───────────────────────────────────────────────────── */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 flex flex-col transition-all duration-300
          ${open ? 'w-56' : 'w-16'}`}
        style={{ background: 'var(--ink)', borderRight: '1px solid #1e1e1e' }}
      >
        {/* Logo */}
        <div className="flex items-center gap-3 px-4 py-6 border-b border-white/10">
          <div className="w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center"
            style={{ background: 'linear-gradient(135deg, var(--gold), var(--gold-light))' }}>
            <span className="text-black font-bold text-xs">F</span>
          </div>
          {open && (
            <span className="font-display text-lg font-light tracking-wider"
              style={{ color: 'var(--gold)' }}>Fintoo</span>
          )}
        </div>

        {/* Toggle */}
        <button onClick={() => setOpen(o => !o)}
          className="absolute -right-3 top-7 w-6 h-6 rounded-full flex items-center justify-center
            text-white/60 hover:text-white transition-colors"
          style={{ background: '#1a1a1a', border: '1px solid #333' }}>
          {open ? <X size={12} /> : <Menu size={12} />}
        </button>

        {/* Nav */}
        <nav className="flex-1 flex flex-col gap-1 pt-4 px-2">
          {nav.map(({ to, icon: Icon, label }) => (
            <NavLink key={to} to={to} end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-3 rounded-lg transition-all duration-200 group
                 ${isActive
                   ? 'text-white'
                   : 'text-white/40 hover:text-white/70'}`
              }
              style={({ isActive }) => isActive ? {
                background: 'linear-gradient(135deg, rgba(201,168,76,0.15), rgba(201,168,76,0.05))',
                borderLeft: '2px solid var(--gold)'
              } : {}}
            >
              <Icon size={18} className="flex-shrink-0" />
              {open && <span className="text-sm font-medium">{label}</span>}
            </NavLink>
          ))}
        </nav>

        {/* Logout */}
        <div className="p-2 border-t border-white/10">
          <button onClick={doLogout}
            className="w-full flex items-center gap-3 px-3 py-3 rounded-lg
              text-white/30 hover:text-red-400 transition-colors">
            <LogOut size={18} className="flex-shrink-0" />
            {open && <span className="text-sm">Sign out</span>}
          </button>
        </div>
      </aside>

      {/* ── Main content ──────────────────────────────────────────────── */}
      <main className={`flex-1 transition-all duration-300 ${open ? 'ml-56' : 'ml-16'} min-h-screen`}>
        {children}
      </main>
    </div>
  )
}
