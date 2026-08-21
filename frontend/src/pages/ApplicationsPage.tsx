/**
 * LEDGER — Applications Page (Underwriter Case Workbench)
 * Purpose: "Which customer do I investigate?"
 * Case triage, multi-dimensional filtering, search, and deep-dive links into Financial Twins.
 */
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { demoApi } from '../lib/api'

const PERSONA_META: Record<string, { color: string; label: string; tag: string }> = {
  thin_file_ntc:            { color: '#00d4e0', label: 'Thin File / NTC',        tag: 'NTC' },
  high_income_unstable:     { color: '#f59e0b', label: 'High Income, Volatile',  tag: 'VOLATILE' },
  moderate_disciplined:     { color: '#10b981', label: 'Moderate, Disciplined',  tag: 'PRIME' },
  high_volatility_suspicious: { color: '#ef4444', label: 'High Volatility',      tag: 'ANOMALY' },
  ambiguous_ntc:            { color: '#8b5cf6', label: 'Ambiguous / NTC',        tag: 'REVIEW' },
}

const PATHWAY_CONFIG: Record<string, { color: string; label: string; bg: string }> = {
  full_approval:        { color: '#10b981', label: 'Full Approval',        bg: 'rgba(16,185,129,0.1)' },
  conditional_approval: { color: '#00d4e0', label: 'Conditional Approval', bg: 'rgba(0,212,224,0.1)' },
  request_evidence:     { color: '#f59e0b', label: 'Request Evidence',     bg: 'rgba(245,158,11,0.1)' },
  human_review:         { color: '#8b5cf6', label: 'Human Review',         bg: 'rgba(139,92,246,0.1)' },
  reduced_exposure:     { color: '#f97316', label: 'Reduced Exposure',     bg: 'rgba(249,115,22,0.1)' },
  transparent_decline:  { color: '#ef4444', label: 'Transparent Decline',  bg: 'rgba(239,68,68,0.1)' },
}

export default function ApplicationsPage() {
  const navigate = useNavigate()
  const [scenarios, setScenarios] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedPathway, setSelectedPathway] = useState('all')
  const [selectedPersona, setSelectedPersona] = useState('all')
  const [selectedRiskBand, setSelectedRiskBand] = useState('all')

  useEffect(() => {
    const load = async () => {
      try {
        const res = await demoApi.status()
        setScenarios(res.data.seeded_scenarios || [])
      } catch {}
      setLoading(false)
    }
    load()
  }, [])

  const filteredScenarios = scenarios.filter((s: any) => {
    const q = searchQuery.toLowerCase()
    const matchesSearch = !searchQuery ||
      s.customer.toLowerCase().includes(q) ||
      s.persona_tag.toLowerCase().includes(q) ||
      (s.scenario || '').toLowerCase().includes(q)

    const matchesPathway = selectedPathway === 'all' || s.pathway === selectedPathway
    const matchesPersona = selectedPersona === 'all' || s.persona_tag === selectedPersona

    const risk = parseFloat(s.risk_probability)
    const matchesRisk = selectedRiskBand === 'all' ||
      (selectedRiskBand === 'low' && risk < 0.35) ||
      (selectedRiskBand === 'medium' && risk >= 0.35 && risk < 0.60) ||
      (selectedRiskBand === 'high' && risk >= 0.60)

    return matchesSearch && matchesPathway && matchesPersona && matchesRisk
  })

  return (
    <div className="w-full">
      <div className="max-w-5xl mx-auto px-6 py-8">

        {/* ── Header ─────────────────────────────────────── */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35 }}
          className="mb-6"
        >
          <div className="flex items-center justify-between">
            <div>
              <div className="text-[10px] uppercase tracking-widest font-semibold mb-1" style={{ color: 'var(--color-accent-cyan)' }}>
                Underwriter Case Workbench
              </div>
              <h1 className="text-2xl font-bold tracking-tight">
                Applications Queue
              </h1>
              <p className="text-xs mt-1" style={{ color: 'var(--color-text-secondary)' }}>
                Triage active cases, inspect continuous Financial Twins, and progress credit pathways with evidence.
              </p>
            </div>
            <div className="text-right">
              <span className="text-xs px-2.5 py-1 rounded-full bg-slate-800 border border-slate-700 text-slate-300 font-mono">
                {filteredScenarios.length} of {scenarios.length} Cases Active
              </span>
            </div>
          </div>
        </motion.div>

        {/* ── Search and Multi-Filter Controls ───────────── */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, delay: 0.05 }}
          className="card p-4 mb-6 space-y-3"
        >
          {/* Search bar */}
          <div className="relative">
            <input
              type="text"
              placeholder="Search applicant name, persona tag, or scenario (e.g. 'Ananya', 'NTC', 'Volatile')…"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-slate-900/80 border border-slate-700 rounded-xl px-4 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400 transition-colors"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-slate-400 hover:text-slate-200"
              >
                ✕
              </button>
            )}
          </div>

          {/* Filter Pills */}
          <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-slate-800/80">
            <span className="text-[10px] uppercase font-semibold text-slate-400 mr-1">Pathway:</span>
            {[
              { id: 'all', label: 'All' },
              { id: 'request_evidence', label: 'Request Evidence' },
              { id: 'conditional_approval', label: 'Conditional Approval' },
              { id: 'full_approval', label: 'Full Approval' },
              { id: 'human_review', label: 'Human Review' },
              { id: 'reduced_exposure', label: 'Reduced Exposure' },
            ].map(p => (
              <button
                key={p.id}
                onClick={() => setSelectedPathway(p.id)}
                className={`text-[11px] px-2.5 py-1 rounded-lg font-medium transition-all ${
                  selectedPathway === p.id
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
                    : 'bg-slate-800/60 text-slate-400 hover:text-slate-200 border border-slate-700/50'
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>

          {/* Secondary Filters */}
          <div className="flex flex-wrap items-center justify-between gap-2 pt-1 text-[11px]">
            <div className="flex items-center gap-1.5">
              <span className="text-[10px] uppercase font-semibold text-slate-400 mr-1">Persona:</span>
              {[
                { id: 'all', label: 'All' },
                { id: 'thin_file_ntc', label: 'Thin-File / NTC' },
                { id: 'high_income_unstable', label: 'Volatile Income' },
                { id: 'moderate_disciplined', label: 'Prime' },
                { id: 'high_volatility_suspicious', label: 'Anomaly' },
              ].map(per => (
                <button
                  key={per.id}
                  onClick={() => setSelectedPersona(per.id)}
                  className={`px-2 py-0.5 rounded text-[10px] transition-colors ${
                    selectedPersona === per.id
                      ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                      : 'text-slate-400 hover:text-slate-300'
                  }`}
                >
                  {per.label}
                </button>
              ))}
            </div>

            <div className="flex items-center gap-1.5">
              <span className="text-[10px] uppercase font-semibold text-slate-400 mr-1">Risk:</span>
              {[
                { id: 'all', label: 'All' },
                { id: 'low', label: '< 35%' },
                { id: 'medium', label: '35–60%' },
                { id: 'high', label: '> 60%' },
              ].map(r => (
                <button
                  key={r.id}
                  onClick={() => setSelectedRiskBand(r.id)}
                  className={`px-2 py-0.5 rounded text-[10px] transition-colors ${
                    selectedRiskBand === r.id
                      ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                      : 'text-slate-400 hover:text-slate-300'
                  }`}
                >
                  {r.label}
                </button>
              ))}
            </div>
          </div>
        </motion.div>

        {/* ── Applications Workbench Cards ───────────────── */}
        {loading ? (
          <div className="card p-12 text-center">
            <div className="w-8 h-8 rounded-full border-2 border-cyan-400 border-t-transparent animate-spin mx-auto mb-3" />
            <p className="text-xs text-slate-400">Loading cases…</p>
          </div>
        ) : filteredScenarios.length === 0 ? (
          <div className="card p-12 text-center">
            <div className="text-3xl mb-2">🔍</div>
            <p className="text-sm font-semibold text-slate-300 mb-1">No matching applications</p>
            <p className="text-xs text-slate-400 mb-4">Try clearing filters or adjusting your search term.</p>
            <button
              onClick={() => { setSearchQuery(''); setSelectedPathway('all'); setSelectedPersona('all'); setSelectedRiskBand('all') }}
              className="text-xs px-3 py-1.5 rounded-lg bg-slate-800 text-cyan-400 border border-slate-700 hover:bg-slate-700 transition-colors"
            >
              Reset All Filters
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredScenarios.map((sc: any, idx: number) => {
              const persona = PERSONA_META[sc.persona_tag] || { color: '#94a3b8', label: sc.persona_tag, tag: 'FILE' }
              const pathway = PATHWAY_CONFIG[sc.pathway] || { color: '#94a3b8', label: sc.pathway, bg: 'rgba(148,163,184,0.1)' }
              const risk = sc.risk_probability != null && !isNaN(parseFloat(sc.risk_probability)) ? parseFloat(sc.risk_probability) : null
              const conf = sc.confidence != null && !isNaN(parseFloat(sc.confidence)) ? parseFloat(sc.confidence) : null
              const isHero = sc.scenario === 'A'

              return (
                <motion.div
                  key={sc.application_id}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: idx * 0.04 }}
                  onClick={() => navigate(`/applications/${sc.application_id}`)}
                  className={`card p-4 hover:border-cyan-500/40 cursor-pointer transition-all duration-200 group relative ${
                    isHero ? 'border-cyan-500/30 bg-gradient-to-r from-cyan-950/20 via-slate-900 to-slate-900' : ''
                  }`}
                >
                  <div className="flex items-center justify-between gap-4">
                    {/* Left: Applicant Identity */}
                    <div className="flex items-center gap-3 min-w-[200px]">
                      <div
                        className="w-10 h-10 rounded-xl flex items-center justify-center text-sm font-bold text-white shadow-sm flex-shrink-0 group-hover:scale-105 transition-transform"
                        style={{ background: `linear-gradient(135deg, ${persona.color}, #3b82f6)` }}
                      >
                        {sc.customer[0]}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="text-sm font-bold text-slate-100 group-hover:text-cyan-300 transition-colors">
                            {sc.customer}
                          </h3>
                          {isHero && (
                            <span className="text-[9px] px-1.5 py-0.2 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 font-semibold uppercase">
                              Hero NTC Demo
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-2 mt-0.5">
                          <span
                            className="text-[10px] font-semibold px-2 py-0.5 rounded"
                            style={{ background: `${persona.color}18`, color: persona.color }}
                          >
                            {persona.label}
                          </span>
                          <span className="text-[10px] text-slate-400 font-mono">
                            Scenario {sc.scenario || '—'}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Middle: Real ML Scores */}
                    <div className="grid grid-cols-2 gap-4 text-center px-4 border-x border-slate-800">
                      <div>
                        <div className="text-[10px] text-slate-400 font-medium mb-0.5">Risk Probability</div>
                        <div className="text-base font-bold font-mono" style={{
                          color: risk == null ? '#94a3b8' : risk < 0.35 ? '#10b981' : risk < 0.60 ? '#f59e0b' : '#ef4444'
                        }}>
                          {risk != null ? `${(risk * 100).toFixed(1)}%` : '—'}
                        </div>
                      </div>
                      <div>
                        <div className="text-[10px] text-slate-400 font-medium mb-0.5">Confidence</div>
                        <div className="text-base font-bold font-mono text-cyan-400">
                          {conf != null ? `${(conf * 100).toFixed(1)}%` : '—'}
                        </div>
                      </div>
                    </div>

                    {/* Right: Pathway Decision & CTA */}
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <div className="text-[10px] text-slate-400 mb-0.5">Credit Pathway</div>
                        <span
                          className="text-xs font-semibold px-2.5 py-1 rounded-lg border inline-block"
                          style={{
                            background: pathway.bg,
                            color: pathway.color,
                            borderColor: `${pathway.color}40`,
                          }}
                        >
                          {pathway.label}
                        </span>
                      </div>

                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          navigate(`/applications/${sc.application_id}`)
                        }}
                        className="px-3.5 py-2 rounded-xl text-xs font-semibold bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 group-hover:bg-cyan-500 group-hover:text-slate-950 transition-all duration-150 flex items-center gap-1.5 flex-shrink-0"
                      >
                        Open Twin →
                      </button>
                    </div>
                  </div>
                </motion.div>
              )
            })}
          </div>
        )}

      </div>
    </div>
  )
}
