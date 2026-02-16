// src/pages/History.jsx
import React, { useState, useEffect } from 'react'
import { getCalculationHistory } from '../api'
import {
  LineChart, Line, XAxis, YAxis, Tooltip,
  ResponsiveContainer, ReferenceLine, Area, AreaChart
} from 'recharts'
import { TrendingUp, TrendingDown, Calendar } from 'lucide-react'

const fmt = (n) => {
  if (!n && n !== 0) return '—'
  if (Math.abs(n) >= 10000000) return `₹${(n / 10000000).toFixed(1)}Cr`
  if (Math.abs(n) >= 100000)   return `₹${(n / 100000).toFixed(1)}L`
  return `₹${Math.round(n).toLocaleString('en-IN')}`
}

const riskColors  = { safe: '#1a6b3c', medium: '#b87c00', risky: '#c0392b' }

export default function History({ userId }) {
  const [history, setHistory]   = useState([])
  const [loading, setLoading]   = useState(true)
  const [error,   setError]     = useState('')

  useEffect(() => {
    setLoading(true)
    getCalculationHistory(userId, 20)
      .then(res => {
        const data = res.data || res
        setHistory(Array.isArray(data) ? data : [])
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [userId])

  if (loading) return (
    <div className="flex items-center justify-center h-screen">
      <div className="w-6 h-6 rounded-full border-2 animate-spin"
        style={{ borderColor: 'var(--gold)', borderTopColor: 'transparent' }} />
    </div>
  )

  const chartData = history.map((h, i) => ({
    label: new Date(h.calculation_date).toLocaleDateString('en-IN', { month: 'short', day: 'numeric' }),
    readiness: Math.round(h.readiness_score ?? 0),
    required:  Math.round((h.total_corpus_required ?? 0) / 100000),
    projected: Math.round((h.projected_corpus     ?? 0) / 100000),
    gap:       Math.round((h.corpus_gap           ?? 0) / 100000),
    risk:      h.risk_level,
  }))

  const latest   = history[0]
  const previous = history[1]
  const scoreDelta = latest && previous
    ? Math.round((latest.readiness_score ?? 0) - (previous.readiness_score ?? 0))
    : null

  return (
    <div className="p-8 max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-10 fade-up">
        <p className="text-xs uppercase tracking-widest mb-1" style={{ color: 'var(--muted)' }}>
          Retirement Timeline
        </p>
        <h1 className="font-display text-4xl font-light" style={{ color: 'var(--ink)' }}>
          How You've Progressed
        </h1>
      </div>

      {error && (
        <div className="mb-6 px-4 py-3 rounded-xl text-sm" style={{ background: '#fef2f2', color: 'var(--red)' }}>
          {error}
        </div>
      )}

      {history.length === 0 && !loading && (
        <div className="text-center py-20">
          <p className="font-display text-2xl font-light mb-2" style={{ color: 'var(--muted)' }}>
            No history yet
          </p>
          <p className="text-sm" style={{ color: 'var(--muted)' }}>
            Run a calculation from the Dashboard to start tracking your progress.
          </p>
        </div>
      )}

      {history.length > 0 && (
        <>
          {/* ── Summary Strip ─────────────────────────────────────── */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8 fade-up delay-1">
            <SummaryCard label="Calculations Run" value={history.length} />
            <SummaryCard
              label="Latest Readiness"
              value={`${Math.round(latest?.readiness_score ?? 0)}%`}
              delta={scoreDelta}
            />
            <SummaryCard
              label="Latest Corpus Gap"
              value={fmt(Math.abs(latest?.corpus_gap ?? 0))}
              sub={(latest?.corpus_gap ?? 0) >= 0 ? 'surplus' : 'shortfall'}
              subColor={(latest?.corpus_gap ?? 0) >= 0 ? 'var(--green)' : 'var(--red)'}
            />
            <SummaryCard
              label="Money Lasts Until"
              value={latest?.money_lasts_until_age ? `Age ${latest.money_lasts_until_age}` : '—'}
            />
          </div>

          {/* ── Readiness Chart ───────────────────────────────────── */}
          {chartData.length > 1 && (
            <div className="fade-up delay-2 rounded-2xl p-6 mb-6"
              style={{ background: 'white', border: '1px solid var(--border)' }}>
              <div className="flex items-center justify-between mb-6">
                <div>
                  <p className="text-xs uppercase tracking-widest" style={{ color: 'var(--muted)' }}>
                    Readiness Score Over Time
                  </p>
                </div>
                <div className="flex items-center gap-1.5 text-xs" style={{ color: 'var(--muted)' }}>
                  <Calendar size={12} />
                  Last {history.length} calculations
                </div>
              </div>
              <ResponsiveContainer width="100%" height={220}>
                <AreaChart data={chartData} margin={{ top: 5, right: 5, bottom: 5, left: 0 }}>
                  <defs>
                    <linearGradient id="scoreGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor="var(--gold)" stopOpacity={0.15} />
                      <stop offset="95%" stopColor="var(--gold)" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="label" tick={{ fontSize: 10, fill: 'var(--muted)' }}
                    axisLine={false} tickLine={false} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: 'var(--muted)' }}
                    axisLine={false} tickLine={false} tickFormatter={v => `${v}%`} width={35} />
                  <Tooltip
                    contentStyle={{ background: 'var(--ink)', border: 'none', borderRadius: '12px',
                      color: 'var(--paper)', fontSize: '12px' }}
                    formatter={(v) => [`${v}%`, 'Readiness']}
                  />
                  <ReferenceLine y={80} stroke="var(--green)" strokeDasharray="4 4" strokeOpacity={0.4} />
                  <Area type="monotone" dataKey="readiness"
                    stroke="var(--gold)" strokeWidth={2}
                    fill="url(#scoreGrad)" dot={{ r: 4, fill: 'var(--gold)', strokeWidth: 0 }}
                    activeDot={{ r: 6, fill: 'var(--gold)' }}
                  />
                </AreaChart>
              </ResponsiveContainer>
              <p className="text-xs text-right mt-1" style={{ color: 'var(--muted)' }}>
                Green dashed line = 80% target
              </p>
            </div>
          )}

          {/* ── Corpus Chart ──────────────────────────────────────── */}
          {chartData.length > 1 && (
            <div className="fade-up delay-3 rounded-2xl p-6 mb-6"
              style={{ background: 'white', border: '1px solid var(--border)' }}>
              <p className="text-xs uppercase tracking-widest mb-6" style={{ color: 'var(--muted)' }}>
                Corpus Required vs Projected (₹ Lakhs)
              </p>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={chartData} margin={{ top: 5, right: 5, bottom: 5, left: 0 }}>
                  <XAxis dataKey="label" tick={{ fontSize: 10, fill: 'var(--muted)' }}
                    axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 10, fill: 'var(--muted)' }}
                    axisLine={false} tickLine={false} tickFormatter={v => `${v}L`} width={40} />
                  <Tooltip
                    contentStyle={{ background: 'var(--ink)', border: 'none', borderRadius: '12px',
                      color: 'var(--paper)', fontSize: '12px' }}
                    formatter={(v, name) => [`₹${v}L`, name === 'required' ? 'Required' : 'Projected']}
                  />
                  <Line type="monotone" dataKey="required" stroke="var(--red)" strokeWidth={2}
                    strokeDasharray="4 4" dot={false} />
                  <Line type="monotone" dataKey="projected" stroke="var(--green)" strokeWidth={2}
                    dot={{ r: 3, fill: 'var(--green)', strokeWidth: 0 }}
                    activeDot={{ r: 5 }}
                  />
                </LineChart>
              </ResponsiveContainer>
              <div className="flex gap-6 mt-3">
                <div className="flex items-center gap-2 text-xs" style={{ color: 'var(--muted)' }}>
                  <div className="w-6 border-t-2 border-dashed" style={{ borderColor: 'var(--red)' }} />
                  Required corpus
                </div>
                <div className="flex items-center gap-2 text-xs" style={{ color: 'var(--muted)' }}>
                  <div className="w-6 border-t-2" style={{ borderColor: 'var(--green)' }} />
                  Projected corpus
                </div>
              </div>
            </div>
          )}

          {/* ── History Table ─────────────────────────────────────── */}
          <div className="fade-up delay-4 rounded-2xl overflow-hidden"
            style={{ border: '1px solid var(--border)' }}>
            <div className="px-6 py-4 border-b" style={{ borderColor: 'var(--border)', background: 'var(--cream)' }}>
              <p className="text-xs uppercase tracking-widest" style={{ color: 'var(--muted)' }}>
                All Calculations
              </p>
            </div>
            <div className="divide-y" style={{ divideColor: 'var(--border)' }}>
              {history.map((h, i) => {
                const date    = new Date(h.calculation_date)
                const score   = Math.round(h.readiness_score ?? 0)
                const risk    = h.risk_level ?? 'risky'
                const gap     = h.corpus_gap ?? 0
                const isFirst = i === 0
                return (
                  <div key={h.calculation_id || i}
                    className={`flex items-center gap-6 px-6 py-4 ${isFirst ? 'bg-yellow-50/30' : 'bg-white'}`}>
                    {/* Date */}
                    <div className="w-28 flex-shrink-0">
                      <p className="text-xs font-medium" style={{ color: 'var(--ink)' }}>
                        {date.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
                      </p>
                      <p className="text-xs mt-0.5" style={{ color: 'var(--muted)' }}>
                        {date.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}
                      </p>
                    </div>

                    {/* Score bar */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs" style={{ color: 'var(--muted)' }}>Readiness</span>
                        <span className="text-xs font-medium" style={{ color: riskColors[risk] }}>{score}%</span>
                      </div>
                      <div className="h-1.5 rounded-full" style={{ background: 'var(--cream)' }}>
                        <div className="h-full rounded-full transition-all"
                          style={{ width: `${score}%`, background: riskColors[risk] }} />
                      </div>
                    </div>

                    {/* Gap */}
                    <div className="w-28 text-right flex-shrink-0">
                      <div className="flex items-center justify-end gap-1">
                        {gap < 0
                          ? <TrendingDown size={12} style={{ color: 'var(--red)' }} />
                          : <TrendingUp   size={12} style={{ color: 'var(--green)' }} />
                        }
                        <span className="text-sm font-medium" style={{ color: gap < 0 ? 'var(--red)' : 'var(--green)' }}>
                          {fmt(Math.abs(gap))}
                        </span>
                      </div>
                      <p className="text-xs mt-0.5" style={{ color: 'var(--muted)' }}>
                        {gap < 0 ? 'shortfall' : 'surplus'}
                      </p>
                    </div>

                    {/* Risk badge */}
                    <div className="w-24 flex-shrink-0 text-right">
                      <span className="text-xs px-2.5 py-1 rounded-full font-medium"
                        style={{ background: `${riskColors[risk]}15`, color: riskColors[risk] }}>
                        {risk}
                      </span>
                    </div>

                    {/* Latest badge */}
                    {isFirst && (
                      <div className="flex-shrink-0">
                        <span className="text-xs px-2 py-1 rounded-full"
                          style={{ background: 'var(--ink)', color: 'var(--gold)' }}>
                          Latest
                        </span>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        </>
      )}
    </div>
  )
}

function SummaryCard({ label, value, delta, sub, subColor }) {
  return (
    <div className="rounded-2xl p-5 fade-up"
      style={{ background: 'white', border: '1px solid var(--border)' }}>
      <p className="text-xs uppercase tracking-widest mb-2" style={{ color: 'var(--muted)' }}>
        {label}
      </p>
      <p className="font-display text-2xl font-light" style={{ color: 'var(--ink)' }}>{value}</p>
      {delta !== null && delta !== undefined && (
        <div className="flex items-center gap-1 mt-1 text-xs">
          {delta >= 0
            ? <TrendingUp  size={12} style={{ color: 'var(--green)' }} />
            : <TrendingDown size={12} style={{ color: 'var(--red)' }} />
          }
          <span style={{ color: delta >= 0 ? 'var(--green)' : 'var(--red)' }}>
            {delta >= 0 ? '+' : ''}{delta}% from last
          </span>
        </div>
      )}
      {sub && (
        <p className="text-xs mt-1 font-medium" style={{ color: subColor || 'var(--muted)' }}>{sub}</p>
      )}
    </div>
  )
}
