// src/pages/Onboarding.jsx
import React, { useState } from 'react'
import { checkEmail, completeOnboarding, requestOtp, verifyOtp } from '../api'

const MARITAL = ['single', 'married', 'divorced', 'widowed']

export default function Onboarding({ onSuccess }) {
  const [step, setStep]     = useState(1)   // 1=email, 2=profile, 3=otp
  const [email, setEmail]   = useState('')
  const [name,  setName]    = useState('')
  const [phone, setPhone]   = useState('')
  const [otp, setOtp]       = useState('')
  const [debugOtp, setDebugOtp] = useState('')
  const [form,  setForm]    = useState({
    current_age: '', desired_retirement_age: '',
    monthly_income: '', monthly_expense: '',
    marital_status: 'single', number_of_dependents: 0,
  })
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState('')

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  // Step 1: email check
  const handleEmailNext = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await checkEmail(email)
      if (res?.exists) {
        const otpRes = await requestOtp(email)
        if (!otpRes?.success) {
          throw new Error(otpRes?.message || 'Failed to send OTP')
        }
        setDebugOtp(otpRes?.debug_otp || '')
        setStep(3)
      } else {
        setStep(2)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // Step 2: complete onboarding
  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const payload = {
        email, full_name: name, phone,
        current_age:              parseInt(form.current_age),
        desired_retirement_age:   parseInt(form.desired_retirement_age),
        monthly_income:           parseFloat(form.monthly_income),
        monthly_expense:          parseFloat(form.monthly_expense),
        marital_status:           form.marital_status,
        number_of_dependents:     parseInt(form.number_of_dependents),
      }
      const res = await completeOnboarding(payload)
      onSuccess(res.user?.user_id || res.data?.user_id || res.user_id)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // Step 3: OTP login
  const handleOtpVerify = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await verifyOtp(email, otp)
      if (!res?.success) {
        throw new Error(res?.message || 'Invalid OTP')
      }
      onSuccess(res.user?.user_id || res.user_id)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleResendOtp = async () => {
    setError('')
    setLoading(true)
    try {
      const otpRes = await requestOtp(email)
      if (!otpRes?.success) {
        throw new Error(otpRes?.message || 'Failed to send OTP')
      }
      setDebugOtp(otpRes?.debug_otp || '')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex" style={{ background: 'var(--ink)' }}>
      {/* Left panel */}
      <div className="hidden lg:flex flex-col justify-between w-1/2 p-16 relative overflow-hidden"
        style={{ background: 'linear-gradient(135deg, #111 0%, #1a1a0a 100%)' }}>
        {/* Decorative circles */}
        <div className="absolute -top-32 -left-32 w-96 h-96 rounded-full opacity-10"
          style={{ background: 'radial-gradient(circle, var(--gold) 0%, transparent 70%)' }} />
        <div className="absolute bottom-0 right-0 w-64 h-64 rounded-full opacity-5"
          style={{ background: 'radial-gradient(circle, var(--gold-light) 0%, transparent 70%)' }} />

        <div className="fade-up">
          <div className="w-10 h-10 rounded-full flex items-center justify-center mb-8"
            style={{ background: 'linear-gradient(135deg, var(--gold), var(--gold-light))' }}>
            <span className="text-black font-bold">F</span>
          </div>
          <h1 className="font-display text-6xl font-light leading-tight mb-6"
            style={{ color: 'var(--paper)' }}>
            Your Personal<br />
            <span className="shimmer">Retirement CFO</span>
          </h1>
          <p className="text-white/40 text-lg leading-relaxed max-w-sm">
            A living financial intelligence that continuously ensures your future income
            safely sustains your lifestyle.
          </p>
        </div>

        <div className="fade-up delay-2 space-y-6">
          {['Setup in under 3 minutes', 'No financial jargon', 'Updates as your life changes'].map((t, i) => (
            <div key={i} className="flex items-center gap-3">
              <div className="w-1.5 h-1.5 rounded-full" style={{ background: 'var(--gold)' }} />
              <span className="text-white/50 text-sm">{t}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Right panel */}
      <div className="flex-1 flex items-center justify-center p-8"
        style={{ background: 'var(--paper)' }}>
        <div className="w-full max-w-md">
          {step === 1 ? (
            <form onSubmit={handleEmailNext} className="fade-up space-y-6">
              <div>
                <h2 className="font-display text-4xl font-light mb-2" style={{ color: 'var(--ink)' }}>
                  Get started
                </h2>
                <p className="text-sm" style={{ color: 'var(--muted)' }}>
                  New users will continue onboarding. Existing users sign in with OTP.
                </p>
              </div>

              <Field label="Email" type="email" value={email} onChange={setEmail} placeholder="ravi@example.com" required />

              {error && <p className="text-sm px-3 py-2 rounded-lg bg-red-50" style={{ color: 'var(--red)' }}>{error}</p>}

              <button type="submit" disabled={loading}
                className="w-full py-3.5 rounded-xl font-medium text-sm tracking-wide transition-all
                  hover:shadow-lg hover:-translate-y-0.5 disabled:opacity-50"
                style={{ background: 'var(--ink)', color: 'var(--gold)' }}>
                {loading ? 'Checking…' : 'Continue →'}
              </button>
            </form>
          ) : step === 2 ? (
            <form onSubmit={handleSubmit} className="fade-up space-y-5">
              <div>
                <h2 className="font-display text-4xl font-light mb-1" style={{ color: 'var(--ink)' }}>
                  About you
                </h2>
                <p className="text-sm" style={{ color: 'var(--muted)' }}>
                  Takes about 2 minutes. No guessing needed.
                </p>
              </div>

              <Field label="Full Name" value={name} onChange={setName} placeholder="Ravi Shankar" required />
              <Field label="Phone (optional)" value={phone} onChange={setPhone} placeholder="+91 98765 43210" />

              <div className="grid grid-cols-2 gap-4">
                <Field label="Current Age" type="number" value={form.current_age}
                  onChange={v => set('current_age', v)} placeholder="32" required min={18} max={80} />
                <Field label="Retirement Age" type="number" value={form.desired_retirement_age}
                  onChange={v => set('desired_retirement_age', v)} placeholder="60" required min={40} max={75} />
              </div>

              <Field label="Monthly Income (₹)" type="number" value={form.monthly_income}
                onChange={v => set('monthly_income', v)} placeholder="75000" required min={1} />

              <Field label="Monthly Expenses (₹)" type="number" value={form.monthly_expense}
                onChange={v => set('monthly_expense', v)} placeholder="45000" required min={1} />

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-medium uppercase tracking-widest" style={{ color: 'var(--muted)' }}>
                    Marital Status
                  </label>
                  <select value={form.marital_status} onChange={e => set('marital_status', e.target.value)}
                    className="w-full px-4 py-3 rounded-xl text-sm outline-none transition-all border focus:border-yellow-600"
                    style={{ background: 'var(--cream)', borderColor: 'var(--border)', color: 'var(--ink)' }}>
                    {MARITAL.map(s => <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>)}
                  </select>
                </div>
                <Field label="Dependents" type="number" value={form.number_of_dependents}
                  onChange={v => set('number_of_dependents', v)} placeholder="2" min={0} max={10} />
              </div>

              {error && <p className="text-sm px-3 py-2 rounded-lg bg-red-50" style={{ color: 'var(--red)' }}>{error}</p>}

              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setStep(1)}
                  className="px-5 py-3 rounded-xl text-sm font-medium border transition-colors hover:bg-white"
                  style={{ borderColor: 'var(--border)', color: 'var(--muted)' }}>
                  ← Back
                </button>
                <button type="submit" disabled={loading}
                  className="flex-1 py-3 rounded-xl font-medium text-sm tracking-wide transition-all
                    hover:shadow-lg hover:-translate-y-0.5 disabled:opacity-50"
                  style={{ background: 'var(--ink)', color: 'var(--gold)' }}>
                  {loading ? 'Creating your plan…' : 'Create Retirement Plan'}
                </button>
              </div>
            </form>
          ) : (
            <form onSubmit={handleOtpVerify} className="fade-up space-y-6">
              <div>
                <h2 className="font-display text-4xl font-light mb-1" style={{ color: 'var(--ink)' }}>
                  Sign in
                </h2>
                <p className="text-sm" style={{ color: 'var(--muted)' }}>
                  We sent an OTP to your email.
                </p>
              </div>

              <Field label="Email" type="email" value={email} onChange={setEmail} required />
              <Field label="OTP" value={otp} onChange={setOtp} placeholder="1234" required />

              {debugOtp && (
                <p className="text-xs px-3 py-2 rounded-lg bg-yellow-50" style={{ color: 'var(--muted)' }}>
                  Dev OTP: <strong>{debugOtp}</strong>
                </p>
              )}

              {error && <p className="text-sm px-3 py-2 rounded-lg bg-red-50" style={{ color: 'var(--red)' }}>{error}</p>}

              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setStep(1)}
                  className="px-5 py-3 rounded-xl text-sm font-medium border transition-colors hover:bg-white"
                  style={{ borderColor: 'var(--border)', color: 'var(--muted)' }}>
                  ← Back
                </button>
                <button type="button" onClick={handleResendOtp} disabled={loading}
                  className="px-5 py-3 rounded-xl text-sm font-medium border transition-colors hover:bg-white disabled:opacity-50"
                  style={{ borderColor: 'var(--border)', color: 'var(--muted)' }}>
                  Resend OTP
                </button>
                <button type="submit" disabled={loading}
                  className="flex-1 py-3 rounded-xl font-medium text-sm tracking-wide transition-all
                    hover:shadow-lg hover:-translate-y-0.5 disabled:opacity-50"
                  style={{ background: 'var(--ink)', color: 'var(--gold)' }}>
                  {loading ? 'Verifying…' : 'Verify OTP'}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}

function Field({ label, value, onChange, type = 'text', placeholder, required, min, max }) {
  return (
    <div className="space-y-1.5">
      <label className="text-xs font-medium uppercase tracking-widest" style={{ color: 'var(--muted)' }}>
        {label}
      </label>
      <input
        type={type}
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        required={required}
        min={min}
        max={max}
        className="w-full px-4 py-3 rounded-xl text-sm outline-none transition-all border
          focus:border-yellow-600 focus:ring-2 focus:ring-yellow-600/10"
        style={{ background: 'var(--cream)', borderColor: 'var(--border)', color: 'var(--ink)' }}
      />
    </div>
  )
}
