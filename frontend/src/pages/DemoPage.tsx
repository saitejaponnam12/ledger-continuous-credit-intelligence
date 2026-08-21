/**
 * LEDGER — Demo Control Panel
 * Admin-only: scenario management, event simulation, deterministic reset.
 */
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { demoApi, eventsApi } from '../lib/api'
import { useAuthStore } from '../store/authStore'

const DEMO_EVENTS = [
  {
    type: 'income_verified',
    label: 'Verified Income Event',
    description: 'New verified salary credit received',
    amount: 45000,
    category: 'income',
    direction: 'credit',
    merchant: 'TechCorp Solutions',
    color: '#10b981',
  },
  {
    type: 'salary_credited',
    label: 'Salary Credited',
    description: 'Monthly salary credited to account',
    amount: 52000,
    category: 'income',
    direction: 'credit',
    merchant: 'Employer - Direct Deposit',
    color: '#10b981',
  },
  {
    type: 'emi_payment',
    label: 'EMI Payment Made',
    description: 'Regular loan EMI payment detected',
    amount: 8500,
    category: 'emi',
    direction: 'debit',
    merchant: 'Bank EMI',
    color: '#3b82f6',
  },
  {
    type: 'suspicious_activity',
    label: 'Suspicious Activity',
    description: 'Unusual velocity transaction pattern',
    amount: 95000,
    category: 'transfer',
    direction: 'debit',
    merchant: 'Unknown Transfer',
    color: '#ef4444',
  },
]

export default function DemoPage() {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const [scenarios, setScenarios] = useState<any[]>([])
  const [status, setStatus] = useState<any[]>([])
  const [actionResult, setActionResult] = useState<string | null>(null)
  const [seeding, setSeeding] = useState(false)
  const [selectedApp, setSelectedApp] = useState<string | null>(null)
  const [eventLoading, setEventLoading] = useState(false)

  useEffect(() => {
    if (user?.role !== 'demo_admin') {
      navigate('/dashboard')
      return
    }
    load()
  }, [user])

  const load = async () => {
    try {
      const [scenariosRes, statusRes] = await Promise.all([
        demoApi.scenarios(),
        demoApi.status(),
      ])
      setScenarios(scenariosRes.data.scenarios || [])
      setStatus(statusRes.data.seeded_scenarios || [])
    } catch {}
  }

  const seedAll = async () => {
    setSeeding(true)
    try {
      await demoApi.seedAll()
      setActionResult('All 5 scenarios seeded successfully!')
      await load()
    } catch (e: any) {
      setActionResult(`Error: ${e.response?.data?.detail || 'Seed failed'}`)
    }
    setSeeding(false)
  }

  const resetScenario = async (scenario: string) => {
    try {
      const res = await demoApi.reset(scenario)
      setActionResult(`Scenario ${scenario} reset: ${res.data.application_id}`)
      await load()
    } catch (e: any) {
      setActionResult(`Error resetting ${scenario}`)
    }
  }

  const simulateEvent = async (event: typeof DEMO_EVENTS[0]) => {
    if (!selectedApp) {
      setActionResult('Select an application first')
      return
    }
    const app = status.find(s => s.application_id === selectedApp)
    if (!app) return

    setEventLoading(true)
    try {
      const res = await eventsApi.simulate({
        customer_id: app.customer_id || selectedApp,
        application_id: selectedApp,
        event_type: event.type,
        amount: event.amount,
        category: event.category,
        direction: event.direction,
        merchant: event.merchant,
        description: event.description,
      })
      setActionResult(`Event "${event.label}" → Pathway: ${res.data.pathway?.pathway} | Risk: ${(res.data.risk_probability * 100).toFixed(1)}%`)
    } catch (e: any) {
      setActionResult(`Error: ${e.response?.data?.detail || 'Event failed'}`)
    }
    setEventLoading(false)
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-1">
          <div className="w-6 h-6 rounded flex items-center justify-center text-sm"
            style={{ background: 'rgba(245,158,11,0.1)', color: '#f59e0b' }}>⚙</div>
          <h1 className="text-xl font-semibold">Demo Control Panel</h1>
          <span className="badge badge-amber text-[10px]">Admin Only</span>
        </div>
        <p className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>
          Deterministic scenario management. All resets are reproducible.
        </p>
      </div>

      {/* Action result */}
      <AnimatePresence>
        {actionResult && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mb-4 p-3 rounded-lg text-xs font-mono"
            style={{ background: 'rgba(0,212,224,0.08)', border: '1px solid var(--color-accent-cyan-border)', color: 'var(--color-accent-cyan)' }}
          >
            {actionResult}
            <button onClick={() => setActionResult(null)} className="ml-3 text-[10px] opacity-50 hover:opacity-100">×</button>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="grid grid-cols-2 gap-4 mb-6">
        {/* Scenarios */}
        <div className="card p-4">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold">Scenarios</h2>
            <button onClick={seedAll} disabled={seeding} className="btn-primary text-xs py-1.5 px-3">
              {seeding ? 'Seeding...' : 'Seed All'}
            </button>
          </div>
          <div className="space-y-2">
            {scenarios.map((s: any) => {
              const seeded = status.find((st: any) => st.persona_tag === s.persona_tag)
              return (
                <div key={s.scenario} className="flex items-center gap-3 p-2.5 rounded-lg"
                  style={{ background: 'var(--color-bg-tertiary)' }}>
                  <span className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0"
                    style={{ background: 'var(--color-bg-elevated)', color: 'var(--color-accent-cyan)' }}>
                    {s.scenario}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-medium truncate">{s.display_name}</div>
                    <div className="text-[10px]" style={{ color: 'var(--color-text-tertiary)' }}>
                      {s.persona_tag.replace(/_/g, ' ')}
                    </div>
                  </div>
                  <div className="flex items-center gap-1.5">
                    {seeded && (
                      <button
                        onClick={() => setSelectedApp(seeded.application_id)}
                        className="text-[10px] px-2 py-1 rounded"
                        style={{
                          background: selectedApp === seeded.application_id ? 'var(--color-accent-cyan-dim)' : 'var(--color-bg-elevated)',
                          color: selectedApp === seeded.application_id ? 'var(--color-accent-cyan)' : 'var(--color-text-tertiary)',
                        }}
                      >
                        Select
                      </button>
                    )}
                    <button
                      onClick={() => resetScenario(s.scenario)}
                      className="text-[10px] px-2 py-1 rounded"
                      style={{ background: 'var(--color-bg-elevated)', color: 'var(--color-text-tertiary)' }}
                    >
                      Reset
                    </button>
                    {seeded && (
                      <button
                        onClick={() => navigate(`/applications/${seeded.application_id}`)}
                        className="text-[10px] px-2 py-1 rounded"
                        style={{ background: 'rgba(0,212,224,0.08)', color: 'var(--color-accent-cyan)' }}
                      >
                        View →
                      </button>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Event simulation */}
        <div className="card p-4">
          <div className="mb-3">
            <h2 className="text-sm font-semibold mb-1">Simulate Event</h2>
            {selectedApp ? (
              <div className="text-[10px] font-mono" style={{ color: 'var(--color-accent-cyan)' }}>
                Target: {selectedApp.slice(0, 12)}...
              </div>
            ) : (
              <div className="text-[10px]" style={{ color: 'var(--color-text-tertiary)' }}>
                Select a scenario first
              </div>
            )}
          </div>

          <div className="space-y-2">
            {DEMO_EVENTS.map((event) => (
              <button
                key={event.type}
                onClick={() => simulateEvent(event)}
                disabled={eventLoading || !selectedApp}
                className="w-full flex items-start gap-3 p-3 rounded-lg text-left transition-all"
                style={{
                  background: 'var(--color-bg-tertiary)',
                  border: `1px solid ${event.color}30`,
                  opacity: !selectedApp ? 0.4 : 1,
                }}
              >
                <div className="w-2 h-2 rounded-full mt-1 flex-shrink-0" style={{ background: event.color }} />
                <div>
                  <div className="text-xs font-medium">{event.label}</div>
                  <div className="text-[10px]" style={{ color: 'var(--color-text-tertiary)' }}>
                    {event.description} — ₹{event.amount.toLocaleString('en-IN')}
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* System status */}
      <div className="card p-4">
        <h2 className="text-sm font-semibold mb-3">Seeded Applications</h2>
        <div className="space-y-1">
          {status.map((s: any) => (
            <div key={s.application_id} className="flex items-center gap-3 py-2"
              style={{ borderBottom: '1px solid var(--color-border)' }}>
              <div className="text-xs font-medium w-32 truncate">{s.customer}</div>
              <div className="text-[10px] flex-1" style={{ color: 'var(--color-text-tertiary)' }}>
                {s.persona_tag.replace(/_/g, ' ')}
              </div>
              <div className="text-[10px] font-mono" style={{ color: 'var(--color-text-tertiary)' }}>
                {s.application_id.slice(0, 8)}...
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full" style={{ background: s.status === 'decisioned' ? '#10b981' : '#f59e0b' }} />
                <span className="text-[10px]" style={{ color: 'var(--color-text-tertiary)' }}>{s.status}</span>
              </div>
              <button
                onClick={() => navigate(`/applications/${s.application_id}`)}
                className="text-[10px] px-2 py-1 rounded"
                style={{ background: 'rgba(0,212,224,0.08)', color: 'var(--color-accent-cyan)' }}
              >
                Open
              </button>
            </div>
          ))}
          {status.length === 0 && (
            <div className="text-xs text-center py-4" style={{ color: 'var(--color-text-tertiary)' }}>
              No scenarios seeded. Click "Seed All" above.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
