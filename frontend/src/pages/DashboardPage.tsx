/**
 * LEDGER — Command Center (Portfolio-Level Underwriting Intelligence)
 * Purpose: "What is happening across the portfolio?"
 * Portfolio KPI metrics, pathway allocation, risk distribution, anomaly alerts, and recent events.
 */
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { demoApi } from '../lib/api'

const PATHWAY_META: Record<string, { label: string; color: string; bg: string }> = {
  request_evidence:     { label: 'Request Evidence',     color: '#f59e0b', bg: 'rgba(245,158,11,0.12)' },
  conditional_approval: { label: 'Conditional Approval', color: '#00d4e0', bg: 'rgba(0,212,224,0.12)' },
  full_approval:        { label: 'Full Approval',        color: '#10b981', bg: 'rgba(16,185,129,0.12)' },
  human_review:         { label: 'Human Review',         color: '#8b5cf6', bg: 'rgba(139,92,246,0.12)' },
  reduced_exposure:     { label: 'Reduced Exposure',     color: '#f97316', bg: 'rgba(249,115,22,0.12)' },
  transparent_decline:  { label: 'Transparent Decline',  color: '#ef4444', bg: 'rgba(239,68,68,0.12)' },
}

export default function DashboardPage() {
  const navigate = useNavigate()
  const [scenarios, setScenarios] = useState<any[]>([])

  useEffect(() => {
    const load = async () => {
      try {
        const res = await demoApi.status()
        setScenarios(res.data.seeded_scenarios || [])
      } catch {}
    }
    load()
  }, [])

  // Portfolio aggregates
  const totalApps = scenarios.length
  const ntcCount = scenarios.filter((s: any) => s.persona_tag.includes('ntc') || s.persona_tag.includes('thin_file')).length
  const evidencePendingCount = scenarios.filter((s: any) => s.pathway === 'request_evidence').length
  const humanReviewCount = scenarios.filter((s: any) => s.pathway === 'human_review' || s.persona_tag === 'high_volatility_suspicious').length

  // Pathway distribution
  const pathwayCounts: Record<string, number> = {}
  scenarios.forEach((s: any) => {
    const p = s.pathway || 'request_evidence'
    pathwayCounts[p] = (pathwayCounts[p] || 0) + 1
  })

  // Risk distribution
  const lowRiskCount = scenarios.filter((s: any) => parseFloat(s.risk_probability) < 0.35).length
  const medRiskCount = scenarios.filter((s: any) => parseFloat(s.risk_probability) >= 0.35 && parseFloat(s.risk_probability) < 0.60).length
  const highRiskCount = scenarios.filter((s: any) => parseFloat(s.risk_probability) >= 0.60).length

  return (
    <div className="w-full">
      <div className="max-w-5xl mx-auto px-6 py-8">

        {/* ── Top Bar ──────────────────────────────────────── */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35 }}
          className="mb-6 flex items-center justify-between"
        >
          <div>
            <div className="text-[10px] uppercase tracking-widest font-semibold mb-1" style={{ color: 'var(--color-text-tertiary)' }}>
              Executive Command Center
            </div>
            <h1 className="text-2xl font-bold tracking-tight">
              Portfolio Credit Intelligence
            </h1>
            <p className="text-xs mt-1" style={{ color: 'var(--color-text-secondary)' }}>
              Real-time underwriting posture, multimodal pipeline throughput, and risk distribution across thin-file segments.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              Live Engine
            </div>
            <button
              onClick={() => navigate('/applications')}
              className="text-xs px-3.5 py-1.5 rounded-lg bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 hover:bg-cyan-500 hover:text-slate-950 transition-all font-semibold"
            >
              Case Workbench →
            </button>
          </div>
        </motion.div>

        {/* ── Key Portfolio KPI Cards ─────────────────────── */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, delay: 0.05 }}
          className="grid grid-cols-4 gap-4 mb-6"
        >
          <div className="card p-4">
            <div className="text-[10px] uppercase font-semibold text-slate-400 mb-1">Total Applications</div>
            <div className="text-2xl font-bold font-mono text-slate-100">{totalApps || '—'}</div>
            <div className="text-[10px] text-slate-500 mt-1 flex items-center gap-1">
              <span className="text-cyan-400 font-bold">100%</span> active continuous monitoring
            </div>
          </div>

          <div className="card p-4 border-cyan-500/20 bg-gradient-to-b from-cyan-950/20 to-transparent">
            <div className="text-[10px] uppercase font-semibold text-cyan-400 mb-1">NTC / Thin-File Share</div>
            <div className="text-2xl font-bold font-mono text-cyan-300">
              {totalApps ? `${Math.round((ntcCount / totalApps) * 100)}%` : '—'}
            </div>
            <div className="text-[10px] text-cyan-400/80 mt-1">
              {ntcCount} thin-file applicants expanded
            </div>
          </div>

          <div className="card p-4 border-amber-500/20">
            <div className="text-[10px] uppercase font-semibold text-amber-400 mb-1">Evidence Pending Gate</div>
            <div className="text-2xl font-bold font-mono text-amber-300">{evidencePendingCount}</div>
            <div className="text-[10px] text-amber-400/80 mt-1">
              Awaiting statements / alt-data
            </div>
          </div>

          <div className="card p-4 border-purple-500/20">
            <div className="text-[10px] uppercase font-semibold text-purple-400 mb-1">Human Review Alerts</div>
            <div className="text-2xl font-bold font-mono text-purple-300">{humanReviewCount}</div>
            <div className="text-[10px] text-purple-400/80 mt-1">
              Anomalies flagged by rules
            </div>
          </div>
        </motion.div>

        {/* ── Product Thesis Banner ───────────────────────── */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, delay: 0.1 }}
          className="mb-6 rounded-2xl p-5 relative overflow-hidden"
          style={{
            background: 'linear-gradient(135deg, rgba(0,212,224,0.06) 0%, rgba(59,130,246,0.06) 50%, rgba(139,92,246,0.06) 100%)',
            border: '1px solid rgba(0,212,224,0.15)',
          }}
        >
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2 mb-1.5">
                <span className="text-[9px] uppercase tracking-widest font-semibold px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300">
                  Continuous Underwriting Intelligence
                </span>
              </div>
              <div className="text-xl font-black tracking-tight text-gradient mb-1">
                UNKNOWN ≠ UNTRUSTWORTHY
              </div>
              <p className="text-xs text-slate-300 max-w-2xl leading-relaxed">
                Legacy systems reject thin-file applicants for lack of bureau history. LEDGER ingests real-time behavioral streams, 
                extracts multimodal bank statements, and guides applicants across progressive credit pathways.
              </p>
            </div>

            <button
              onClick={() => navigate('/applications')}
              className="px-4 py-2 rounded-xl text-xs font-semibold bg-cyan-500 text-slate-950 hover:bg-cyan-400 transition-colors flex-shrink-0 shadow-sm"
            >
              Open Workbench →
            </button>
          </div>
        </motion.div>

        {/* ── Portfolio Analytics: Pathway & Risk Distribution ── */}
        <div className="grid grid-cols-2 gap-6 mb-6">

          {/* Pathway Allocation */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, delay: 0.15 }}
            className="card p-5"
          >
            <div className="flex items-center justify-between mb-3">
              <div>
                <h2 className="text-sm font-semibold">Credit Pathway Allocation</h2>
                <p className="text-[11px] text-slate-400 mt-0.5">Distribution across deterministic policy gates</p>
              </div>
              <span className="text-[10px] font-mono text-slate-400">{totalApps} total</span>
            </div>

            <div className="space-y-3">
              {[
                'request_evidence',
                'conditional_approval',
                'full_approval',
                'human_review',
                'reduced_exposure',
                'transparent_decline',
              ].map(pKey => {
                const pMeta = PATHWAY_META[pKey] || { label: pKey, color: '#94a3b8', bg: 'rgba(148,163,184,0.1)' }
                const count = pathwayCounts[pKey] || 0
                const pct = totalApps ? Math.round((count / totalApps) * 100) : 0

                return (
                  <div key={pKey}>
                    <div className="flex items-center justify-between text-xs mb-1">
                      <div className="flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full" style={{ background: pMeta.color }} />
                        <span className="text-slate-300 font-medium text-[11px]">{pMeta.label}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-slate-400 font-mono text-[10px]">{count} cases</span>
                        <span className="font-bold font-mono text-[11px]" style={{ color: pMeta.color }}>{pct}%</span>
                      </div>
                    </div>
                    <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-500"
                        style={{ width: `${pct}%`, background: pMeta.color }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          </motion.div>

          {/* Risk Distribution */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, delay: 0.2 }}
            className="card p-5"
          >
            <div className="flex items-center justify-between mb-3">
              <div>
                <h2 className="text-sm font-semibold">Risk Band Distribution</h2>
                <p className="text-[11px] text-slate-400 mt-0.5">Calibrated XGBoost default risk across portfolio</p>
              </div>
              <span className="text-[10px] text-emerald-400 font-mono">Calibrated</span>
            </div>

            <div className="grid grid-cols-3 gap-3 mb-4 text-center">
              <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                <div className="text-[10px] uppercase font-semibold text-emerald-400">Low Risk</div>
                <div className="text-xs text-slate-400 font-mono mt-0.5">&lt; 35%</div>
                <div className="text-xl font-bold font-mono text-emerald-300 mt-1">{lowRiskCount}</div>
                <div className="text-[10px] text-slate-500 mt-0.5">{totalApps ? Math.round((lowRiskCount / totalApps) * 100) : 0}% share</div>
              </div>

              <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20">
                <div className="text-[10px] uppercase font-semibold text-amber-400">Medium Risk</div>
                <div className="text-xs text-slate-400 font-mono mt-0.5">35–60%</div>
                <div className="text-xl font-bold font-mono text-amber-300 mt-1">{medRiskCount}</div>
                <div className="text-[10px] text-slate-500 mt-0.5">{totalApps ? Math.round((medRiskCount / totalApps) * 100) : 0}% share</div>
              </div>

              <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20">
                <div className="text-[10px] uppercase font-semibold text-rose-400">High Risk</div>
                <div className="text-xs text-slate-400 font-mono mt-0.5">&gt; 60%</div>
                <div className="text-xl font-bold font-mono text-rose-300 mt-1">{highRiskCount}</div>
                <div className="text-[10px] text-slate-500 mt-0.5">{totalApps ? Math.round((highRiskCount / totalApps) * 100) : 0}% share</div>
              </div>
            </div>

            {/* Persona Breakdown Pills */}
            <div className="space-y-2 pt-2 border-t border-slate-800">
              <div className="text-[10px] uppercase font-semibold text-slate-400">Active Persona Segments:</div>
              <div className="flex flex-wrap gap-1.5">
                {scenarios.map((s: any) => (
                  <button
                    key={s.application_id}
                    onClick={() => navigate(`/applications/${s.application_id}`)}
                    className="text-[10px] px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700/60 flex items-center gap-1.5 transition-colors"
                  >
                    <span className="w-1.5 h-1.5 rounded-full" style={{
                      background: parseFloat(s.risk_probability) < 0.35 ? '#10b981' : parseFloat(s.risk_probability) < 0.6 ? '#f59e0b' : '#ef4444'
                    }} />
                    <span>{s.customer}</span>
                    <span className="text-[9px] text-slate-500">({(parseFloat(s.risk_probability) * 100).toFixed(0)}%)</span>
                  </button>
                ))}
              </div>
            </div>
          </motion.div>
        </div>

        {/* ── Recent Portfolio Activity & Anomaly Alerts ──── */}
        <div className="grid grid-cols-2 gap-6">

          {/* Anomaly Alerts */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, delay: 0.25 }}
            className="card p-5"
          >
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <span className="text-amber-400">⚠</span>
                <h2 className="text-sm font-semibold">Human Review & Anomaly Alerts</h2>
              </div>
              <span className="text-[10px] px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20 font-medium">
                Active Monitoring
              </span>
            </div>

            <div className="space-y-2.5">
              {scenarios.filter((s: any) => s.pathway === 'human_review' || s.persona_tag === 'high_volatility_suspicious' || s.persona_tag === 'ambiguous_ntc').length > 0 ? (
                scenarios
                  .filter((s: any) => s.pathway === 'human_review' || s.persona_tag === 'high_volatility_suspicious' || s.persona_tag === 'ambiguous_ntc')
                  .map((s: any) => (
                    <div
                      key={s.application_id}
                      onClick={() => navigate(`/applications/${s.application_id}`)}
                      className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-amber-500/30 cursor-pointer transition-colors flex items-center justify-between"
                    >
                      <div>
                        <div className="text-xs font-semibold text-slate-200">{s.customer}</div>
                        <div className="text-[10px] text-amber-400 mt-0.5">
                          {s.persona_tag === 'high_volatility_suspicious' ? 'Extreme Balance Volatility Detected' : 'Ambiguous NTC File — Needs Review'}
                        </div>
                      </div>
                      <span className="text-[10px] text-cyan-400 font-semibold flex items-center gap-1">
                        Inspect →
                      </span>
                    </div>
                  ))
              ) : (
                <div className="p-4 rounded-xl bg-slate-900/40 text-center text-xs text-slate-500">
                  Zero active high-severity anomalies in current queue.
                </div>
              )}
            </div>
          </motion.div>

          {/* Recent Events Feed */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, delay: 0.3 }}
            className="card p-5"
          >
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <span className="text-cyan-400">⚡</span>
                <h2 className="text-sm font-semibold">Continuous Evidence Feed</h2>
              </div>
              <span className="text-[10px] text-slate-500 font-mono">Live WebSocket</span>
            </div>

            <div className="space-y-2.5">
              {[
                { actor: 'Ananya Sharma', event: '6M Bank Statement Ingested & Verified', time: 'Hero Ready', tag: 'MULTIMODAL' },
                { actor: 'Rahul Verma', event: 'Payroll Stream Recalibrated', time: 'Active', tag: 'STREAM' },
                { actor: 'Priya Nair', event: 'Initial Request Evidence Gate Established', time: 'Seeded', tag: 'GATE' },
              ].map((ev, i) => (
                <div key={i} className="p-2.5 rounded-xl bg-slate-900/40 border border-slate-800/80 flex items-center justify-between text-xs">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-slate-200">{ev.actor}</span>
                      <span className="text-[9px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 font-mono">
                        {ev.tag}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-400 mt-0.5">{ev.event}</div>
                  </div>
                  <span className="text-[10px] text-cyan-400 font-mono">{ev.time}</span>
                </div>
              ))}
            </div>
          </motion.div>

        </div>

      </div>
    </div>
  )
}
