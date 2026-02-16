// src/pages/Dashboard.jsx
import React, { useState, useEffect, useCallback } from 'react'
import { getLatestCalculation, getSnapshot, runCalculation } from '../api'
import { TrendingUp, TrendingDown, Clock, AlertTriangle, RefreshCw, ChevronRight, Zap, PiggyBank, CreditCard, Coins } from 'lucide-react'
import { RadialBarChart, RadialBar, ResponsiveContainer } from 'recharts'

const fmt = (n) => {
  if (!n && n !== 0) return '—'
  if (Math.abs(n) >= 10000000) return `₹${(n / 10000000).toFixed(1)}Cr`
  if (Math.abs(n) >= 100000)   return `₹${(n / 100000).toFixed(1)}L`
  return `₹${Math.round(n).toLocaleString('en-IN')}`
}

const riskColors = { safe: '#1a6b3c', medium: '#b87c00', risky: '#c0392b' }
const riskLabels = { safe: 'On Track', medium: 'Needs Attention', risky: 'At Risk' }

export default function Dashboard({ userId }) {
  const [calc,     setCalc]     = useState(null)
  const [snapshot, setSnapshot] = useState(null)
  const [loading,  setLoading]  = useState(true)
  const [running,  setRunning]  = useState(false)
  const [error,    setError]    = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [snap, calcRes] = await Promise.allSettled([
        getSnapshot(userId),
        getLatestCalculation(userId),
      ])
      if (snap.status === 'fulfilled')    setSnapshot(snap.value?.data || snap.value)
      if (calcRes.status === 'fulfilled') setCalc(calcRes.value?.data || calcRes.value)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [userId])

  useEffect(() => { load() }, [load])

  const handleRun = async () => {
    setRunning(true)
    setError('')
    try {
      const res = await runCalculation(userId)
      setCalc(res.data || res)
    } catch (e) {
      setError(e.message)
    } finally {
      setRunning(false)
    }
  }

  if (loading) return <LoadingScreen />

  const score    = calc?.readiness_score ?? 0
  const risk     = calc?.risk_level ?? 'risky'
  const gap      = calc?.corpus_gap ?? 0
  const lasts    = calc?.money_lasts_until_age
  const recs     = calc?.recommendations ?? []
  const required = calc?.total_corpus_required ?? 0
  const projected = calc?.projected_corpus ?? 0

  return (
    <div className="p-8 max-w-6xl mx-auto">
      {/* ── Header ──────────────────────────────────────────────────── */}
      <div className="flex items-start justify-between mb-10 fade-up">
        <div>
          <p className="text-xs uppercase tracking-widest mb-1" style={{ color: 'var(--muted)' }}>
            Retirement Intelligence
          </p>
          <h1 className="font-display text-4xl font-light" style={{ color: 'var(--ink)' }}>
            {snapshot?.full_name
              ? `${snapshot.full_name.split(' ')[0]}'s Dashboard`
              : 'Your Dashboard'}
          </h1>
        </div>
        <button onClick={handleRun} disabled={running}
          className="flex items-center gap-2 px-5 py-2.5 rounded-full text-sm font-medium
            transition-all hover:shadow-md hover:-translate-y-0.5 disabled:opacity-50"
          style={{ background: 'var(--ink)', color: 'var(--gold)' }}>
          <RefreshCw size={14} className={running ? 'animate-spin' : ''} />
          {running ? 'Calculating…' : 'Recalculate'}
        </button>
      </div>

      {error && (
        <div className="mb-6 px-4 py-3 rounded-xl text-sm" style={{ background: '#fef2f2', color: 'var(--red)' }}>
          {error}
        </div>
      )}

      {!calc && (
        <div className="text-center py-20 fade-up">
          <p className="font-display text-2xl font-light mb-4" style={{ color: 'var(--muted)' }}>
            No calculation yet
          </p>
          <p className="text-sm mb-8" style={{ color: 'var(--muted)' }}>
            Run your first retirement projection to see your readiness score.
          </p>
          <button onClick={handleRun} disabled={running}
            className="px-8 py-3.5 rounded-full font-medium transition-all hover:shadow-lg"
            style={{ background: 'var(--ink)', color: 'var(--gold)' }}>
            {running ? 'Running…' : 'Run Projection'}
          </button>
        </div>
      )}

      {calc && (
        <>
          {/* ── Row 1: Score + Key Metrics ──────────────────────────── */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
            {/* Readiness score card */}
            <div className="lg:col-span-1 fade-up delay-1 rounded-2xl p-6 relative overflow-hidden"
              style={{ background: 'var(--ink)' }}>
              <div className="absolute top-0 right-0 w-40 h-40 rounded-full opacity-10"
                style={{ background: `radial-gradient(circle, ${riskColors[risk]} 0%, transparent 70%)`,
                  transform: 'translate(30%, -30%)' }} />
              <p className="text-xs uppercase tracking-widest mb-4" style={{ color: 'var(--muted)' }}>
                Readiness Score
              </p>
              <div className="relative">
                <svg viewBox="0 0 120 120" className="w-32 h-32 mx-auto -mt-2">
                  <circle cx="60" cy="60" r="50" fill="none" stroke="#ffffff10" strokeWidth="8" />
                  <circle cx="60" cy="60" r="50" fill="none"
                    stroke={riskColors[risk]} strokeWidth="8"
                    strokeLinecap="round"
                    strokeDasharray="314"
                    strokeDashoffset={314 - (314 * score / 100)}
                    transform="rotate(-90 60 60)"
                    style={{ transition: 'stroke-dashoffset 1.5s ease' }}
                  />
                  <text x="60" y="57" textAnchor="middle" fill="white"
                    style={{ fontFamily: 'Cormorant Garamond', fontSize: '22px', fontWeight: '300' }}>
                    {Math.round(score)}%
                  </text>
                  <text x="60" y="74" textAnchor="middle" fill="rgba(255,255,255,0.4)"
                    style={{ fontSize: '9px', fontFamily: 'Sora' }}>
                    readiness
                  </text>
                </svg>
              </div>
              <div className="mt-2 text-center">
                <span className="text-xs px-3 py-1 rounded-full font-medium"
                  style={{ background: `${riskColors[risk]}22`, color: riskColors[risk] }}>
                  {riskLabels[risk]}
                </span>
              </div>
            </div>

            {/* Right metrics column */}
            <div className="lg:col-span-2 grid grid-cols-2 gap-4 fade-up delay-2">
              <MetricCard
                label="Corpus Required"
                value={fmt(required)}
                sub="at retirement"
                icon={<Clock size={16} />}
                color="var(--ink)"
              />
              <MetricCard
                label="Projected Corpus"
                value={fmt(projected)}
                sub="at current rate"
                icon={<TrendingUp size={16} />}
                color={projected >= required ? 'var(--green)' : 'var(--red)'}
              />
              <MetricCard
                label={gap >= 0 ? 'Surplus' : 'Shortfall'}
                value={fmt(Math.abs(gap))}
                sub={gap >= 0 ? 'you are ahead' : 'needs to be filled'}
                icon={gap >= 0 ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                color={gap >= 0 ? 'var(--green)' : 'var(--red)'}
                highlight={true}
              />
              <MetricCard
                label="Money Lasts Until"
                value={lasts ? `Age ${lasts}` : '—'}
                sub={lasts && lasts >= 80 ? 'strong longevity' : 'may need extension'}
                icon={<AlertTriangle size={16} />}
                color={lasts && lasts >= 80 ? 'var(--green)' : 'var(--red)'}
              />
            </div>
          </div>

          {/* ── Row 2: Corpus Bar ───────────────────────────────────── */}
          <div className="fade-up delay-3 rounded-2xl p-6 mb-6"
            style={{ background: 'white', border: '1px solid var(--border)' }}>
            <p className="text-xs uppercase tracking-widest mb-4" style={{ color: 'var(--muted)' }}>
              Corpus Progress
            </p>
            <div className="relative">
              <div className="flex justify-between text-xs mb-2" style={{ color: 'var(--muted)' }}>
                <span>₹0</span>
                <span>{fmt(required)} required</span>
              </div>
              <div className="h-4 rounded-full overflow-hidden" style={{ background: 'var(--cream)' }}>
                <div className="h-full rounded-full transition-all duration-1000"
                  style={{
                    width: `${Math.min((projected / required) * 100, 100)}%`,
                    background: `linear-gradient(90deg, ${riskColors[risk]}, ${riskColors[risk]}bb)`,
                  }} />
              </div>
              <div className="flex justify-between text-xs mt-2">
                <span className="font-medium" style={{ color: riskColors[risk] }}>
                  {fmt(projected)} projected ({Math.round((projected / required) * 100)}%)
                </span>
                {gap < 0 && (
                  <span style={{ color: 'var(--red)' }}>
                    Gap: {fmt(Math.abs(gap))}
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* ── Row 3: Recommendations ─────────────────────────────── */}
          {snapshot && (
            <div className="fade-up delay-4 mb-6">
              <p className="text-xs uppercase tracking-widest mb-4" style={{ color: 'var(--muted)' }}>
                Current Snapshot
              </p>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <MetricCard
                  label="Current Savings"
                  value={fmt(snapshot.total_retirement_savings)}
                  sub="retirement corpus"
                  icon={<PiggyBank size={16} />}
                  color="var(--ink)"
                />
                <MetricCard
                  label="Current Assets"
                  value={fmt(snapshot.total_monthly_contribution)}
                  sub="monthly contribution"
                  icon={<Coins size={16} />}
                  color="var(--ink)"
                />
                <MetricCard
                  label="Current Loans"
                  value={fmt(snapshot.total_monthly_emi)}
                  sub="monthly EMI"
                  icon={<CreditCard size={16} />}
                  color="var(--red)"
                />
                <MetricCard
                  label="Current Expenses"
                  value={fmt(snapshot.monthly_household_expense)}
                  sub="per month"
                  icon={<TrendingDown size={16} />}
                  color="var(--red)"
                />
              </div>
            </div>
          )}

          {recs.length > 0 && (
            <div className="fade-up delay-4">
              <p className="text-xs uppercase tracking-widest mb-4" style={{ color: 'var(--muted)' }}>
                Recommended Actions
              </p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {recs.map((rec, i) => (
                  <div key={i} className="rounded-2xl p-5 transition-all hover:shadow-md hover:-translate-y-0.5"
                    style={{ background: 'white', border: '1px solid var(--border)' }}>
                    <div className="flex items-start justify-between mb-3">
                      <div className="w-7 h-7 rounded-lg flex items-center justify-center"
                        style={{ background: 'var(--cream)' }}>
                        <Zap size={13} style={{ color: 'var(--gold)' }} />
                      </div>
                      <span className="text-xs px-2 py-0.5 rounded-full"
                        style={{ background: 'var(--cream)', color: 'var(--muted)' }}>
                        Priority {rec.priority}
                      </span>
                    </div>
                    <h3 className="font-medium text-sm mb-2 leading-snug" style={{ color: 'var(--ink)' }}>
                      {rec.action_title}
                    </h3>
                    <p className="text-xs leading-relaxed mb-3" style={{ color: 'var(--muted)' }}>
                      {rec.action_description}
                    </p>
                    {rec.impact_description && (
                      <div className="text-xs px-3 py-2 rounded-lg" style={{ background: '#f0fdf4', color: 'var(--green)' }}>
                        {rec.impact_description}
                      </div>
                    )}
                    {rec.suggested_increase_amount && (
                      <div className="mt-2 font-medium text-sm" style={{ color: 'var(--ink)' }}>
                        +{fmt(rec.suggested_increase_amount)}/mo
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── Row 4: User Info Strip ─────────────────────────────── */}
          {snapshot && (
            <div className="mt-6 fade-up rounded-2xl p-5 flex flex-wrap gap-6"
              style={{ background: 'var(--cream)', border: '1px solid var(--border)' }}>
              {[
                { label: 'Current Age', value: snapshot.current_age },
                { label: 'Retirement Age', value: snapshot.desired_retirement_age },
                { label: 'Monthly Income', value: fmt(snapshot.monthly_income) },
                { label: 'Monthly Expense', value: fmt(snapshot.monthly_household_expense) },
                { label: 'Total Savings', value: fmt(snapshot.total_retirement_savings) },
                { label: 'Monthly SIP', value: fmt(snapshot.total_monthly_contribution) },
              ].map(({ label, value }) => (
                <div key={label}>
                  <p className="text-xs uppercase tracking-widest" style={{ color: 'var(--muted)' }}>{label}</p>
                  <p className="font-medium text-sm mt-0.5" style={{ color: 'var(--ink)' }}>{value}</p>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}

function MetricCard({ label, value, sub, icon, color, highlight }) {
  return (
    <div className={`rounded-2xl p-5 transition-all hover:shadow-sm ${highlight ? 'ring-1' : ''}`}
      style={{
        background: highlight ? `${color}08` : 'white',
        border: `1px solid ${highlight ? color + '30' : 'var(--border)'}`,
      }}>
      <div className="flex items-center justify-between mb-3">
        <p className="text-xs uppercase tracking-widest" style={{ color: 'var(--muted)' }}>{label}</p>
        <div style={{ color }}>{icon}</div>
      </div>
      <p className="font-display text-2xl font-light" style={{ color }}>{value}</p>
      <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>{sub}</p>
    </div>
  )
}

function LoadingScreen() {
  return (
    <div className="flex items-center justify-center h-screen">
      <div className="text-center">
        <div className="w-8 h-8 rounded-full border-2 mx-auto mb-4 animate-spin"
          style={{ borderColor: 'var(--gold)', borderTopColor: 'transparent' }} />
        <p className="text-sm" style={{ color: 'var(--muted)' }}>Loading your plan…</p>
      </div>
    </div>
  )
}
