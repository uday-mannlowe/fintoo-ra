// src/pages/Updates.jsx
import React, { useState } from 'react'
import {
  addAssets,
  addLoans,
  addPostRetirementIncome,
  updateIncome,
  updateExpense,
} from '../api'
import { Coins, CreditCard, PiggyBank, RefreshCw } from 'lucide-react'

const ASSET_TYPES = ['epf', 'ppf', 'nps', 'mutual_fund', 'stocks', 'fd', 'other']
const LOAN_TYPES = ['home', 'vehicle', 'personal', 'education', 'other']
const POST_TYPES = ['pension', 'rental', 'annuity', 'business', 'other']

const todayStr = () => new Date().toISOString().slice(0, 10)

export default function Updates({ userId }) {
  // Quick updates
  const [income, setIncome] = useState('')
  const [expense, setExpense] = useState('')
  const [quickStatus, setQuickStatus] = useState({ type: '', msg: '' })
  const [quickLoading, setQuickLoading] = useState(false)

  // Assets
  const [asset, setAsset] = useState({
    asset_type: 'epf',
    asset_name: '',
    current_value: '',
    monthly_contribution: '',
  })
  const [assetStatus, setAssetStatus] = useState({ type: '', msg: '' })
  const [assetLoading, setAssetLoading] = useState(false)

  // Loans
  const [loan, setLoan] = useState({
    loan_type: 'home',
    principal_amount: '',
    outstanding_balance: '',
    monthly_emi: '',
    interest_rate: '',
    start_date: todayStr(),
    end_date: todayStr(),
  })
  const [loanStatus, setLoanStatus] = useState({ type: '', msg: '' })
  const [loanLoading, setLoanLoading] = useState(false)

  // Post-retirement income
  const [post, setPost] = useState({
    income_type: 'pension',
    monthly_amount: '',
    start_age: 60,
    is_guaranteed: false,
  })
  const [postStatus, setPostStatus] = useState({ type: '', msg: '' })
  const [postLoading, setPostLoading] = useState(false)

  const set = (obj, setter, key, value) => setter({ ...obj, [key]: value })

  const submitQuick = async (e) => {
    e.preventDefault()
    setQuickStatus({ type: '', msg: '' })
    setQuickLoading(true)
    try {
      if (income) {
        await updateIncome(userId, { new_monthly_income: Number(income) })
      }
      if (expense) {
        await updateExpense(userId, { new_monthly_expense: Number(expense) })
      }
      setQuickStatus({ type: 'ok', msg: 'Updates saved successfully.' })
      setIncome('')
      setExpense('')
    } catch (err) {
      setQuickStatus({ type: 'err', msg: err.message })
    } finally {
      setQuickLoading(false)
    }
  }

  const submitAsset = async (e) => {
    e.preventDefault()
    setAssetStatus({ type: '', msg: '' })
    setAssetLoading(true)
    try {
      const payload = {
        assets: [{
          asset_type: asset.asset_type,
          asset_name: asset.asset_name || asset.asset_type.toUpperCase(),
          current_value: Number(asset.current_value),
          monthly_contribution: Number(asset.monthly_contribution || 0),
        }],
      }
      await addAssets(userId, payload)
      setAssetStatus({ type: 'ok', msg: 'Asset added successfully.' })
      setAsset({
        asset_type: 'epf',
        asset_name: '',
        current_value: '',
        monthly_contribution: '',
      })
    } catch (err) {
      setAssetStatus({ type: 'err', msg: err.message })
    } finally {
      setAssetLoading(false)
    }
  }

  const submitLoan = async (e) => {
    e.preventDefault()
    setLoanStatus({ type: '', msg: '' })
    setLoanLoading(true)
    try {
      const payload = {
        loans: [{
          loan_type: loan.loan_type,
          principal_amount: Number(loan.principal_amount),
          outstanding_balance: Number(loan.outstanding_balance),
          monthly_emi: Number(loan.monthly_emi),
          interest_rate: Number(loan.interest_rate),
          start_date: loan.start_date,
          end_date: loan.end_date,
        }],
      }
      await addLoans(userId, payload)
      setLoanStatus({ type: 'ok', msg: 'Loan added successfully.' })
      setLoan({
        loan_type: 'home',
        principal_amount: '',
        outstanding_balance: '',
        monthly_emi: '',
        interest_rate: '',
        start_date: todayStr(),
        end_date: todayStr(),
      })
    } catch (err) {
      setLoanStatus({ type: 'err', msg: err.message })
    } finally {
      setLoanLoading(false)
    }
  }

  const submitPost = async (e) => {
    e.preventDefault()
    setPostStatus({ type: '', msg: '' })
    setPostLoading(true)
    try {
      const payload = {
        incomes: [{
          income_type: post.income_type,
          monthly_amount: Number(post.monthly_amount),
          start_age: Number(post.start_age),
          is_guaranteed: Boolean(post.is_guaranteed),
        }],
      }
      await addPostRetirementIncome(userId, payload)
      setPostStatus({ type: 'ok', msg: 'Post-retirement income added.' })
      setPost({
        income_type: 'pension',
        monthly_amount: '',
        start_age: 60,
        is_guaranteed: false,
      })
    } catch (err) {
      setPostStatus({ type: 'err', msg: err.message })
    } finally {
      setPostLoading(false)
    }
  }

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="mb-10 fade-up">
        <p className="text-xs uppercase tracking-widest mb-1" style={{ color: 'var(--muted)' }}>
          Update Your Plan
        </p>
        <h1 className="font-display text-4xl font-light" style={{ color: 'var(--ink)' }}>
          Assets, Loans, and Income
        </h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SectionCard title="Quick Updates" icon={<RefreshCw size={16} />}>
          <form onSubmit={submitQuick} className="space-y-4">
            <Field label="New Monthly Income (₹)" type="number" value={income}
              onChange={(v) => setIncome(v)} placeholder="e.g. 75000" />
            <Field label="New Monthly Expense (₹)" type="number" value={expense}
              onChange={(v) => setExpense(v)} placeholder="e.g. 45000" />
            <StatusBox status={quickStatus} />
            <button type="submit" disabled={quickLoading}
              className="w-full py-3 rounded-xl text-sm font-medium transition-all hover:shadow-md disabled:opacity-50"
              style={{ background: 'var(--ink)', color: 'var(--gold)' }}>
              {quickLoading ? 'Saving…' : 'Save Updates'}
            </button>
          </form>
        </SectionCard>

        <SectionCard title="Add Retirement Asset" icon={<Coins size={16} />}>
          <form onSubmit={submitAsset} className="space-y-4">
            <SelectField label="Asset Type" value={asset.asset_type}
              onChange={(v) => set(asset, setAsset, 'asset_type', v)}
              options={ASSET_TYPES} />
            <Field label="Asset Name" value={asset.asset_name}
              onChange={(v) => set(asset, setAsset, 'asset_name', v)} placeholder="e.g. EPF Account" />
            <Field label="Current Value (₹)" type="number" value={asset.current_value}
              onChange={(v) => set(asset, setAsset, 'current_value', v)} required />
            <Field label="Monthly Contribution (₹)" type="number" value={asset.monthly_contribution}
              onChange={(v) => set(asset, setAsset, 'monthly_contribution', v)} />
            <StatusBox status={assetStatus} />
            <button type="submit" disabled={assetLoading}
              className="w-full py-3 rounded-xl text-sm font-medium transition-all hover:shadow-md disabled:opacity-50"
              style={{ background: 'var(--ink)', color: 'var(--gold)' }}>
              {assetLoading ? 'Adding…' : 'Add Asset'}
            </button>
          </form>
        </SectionCard>

        <SectionCard title="Add Loan" icon={<CreditCard size={16} />}>
          <form onSubmit={submitLoan} className="space-y-4">
            <SelectField label="Loan Type" value={loan.loan_type}
              onChange={(v) => set(loan, setLoan, 'loan_type', v)}
              options={LOAN_TYPES} />
            <div className="grid grid-cols-2 gap-4">
              <Field label="Principal (₹)" type="number" value={loan.principal_amount}
                onChange={(v) => set(loan, setLoan, 'principal_amount', v)} required />
              <Field label="Outstanding (₹)" type="number" value={loan.outstanding_balance}
                onChange={(v) => set(loan, setLoan, 'outstanding_balance', v)} required />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <Field label="Monthly EMI (₹)" type="number" value={loan.monthly_emi}
                onChange={(v) => set(loan, setLoan, 'monthly_emi', v)} required />
              <Field label="Interest Rate (%)" type="number" value={loan.interest_rate}
                onChange={(v) => set(loan, setLoan, 'interest_rate', v)} required />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <Field label="Start Date" type="date" value={loan.start_date}
                onChange={(v) => set(loan, setLoan, 'start_date', v)} required />
              <Field label="End Date" type="date" value={loan.end_date}
                onChange={(v) => set(loan, setLoan, 'end_date', v)} required />
            </div>
            <StatusBox status={loanStatus} />
            <button type="submit" disabled={loanLoading}
              className="w-full py-3 rounded-xl text-sm font-medium transition-all hover:shadow-md disabled:opacity-50"
              style={{ background: 'var(--ink)', color: 'var(--gold)' }}>
              {loanLoading ? 'Adding…' : 'Add Loan'}
            </button>
          </form>
        </SectionCard>

        <SectionCard title="Post‑Retirement Income" icon={<PiggyBank size={16} />}>
          <form onSubmit={submitPost} className="space-y-4">
            <SelectField label="Income Type" value={post.income_type}
              onChange={(v) => set(post, setPost, 'income_type', v)}
              options={POST_TYPES} />
            <Field label="Monthly Amount (₹)" type="number" value={post.monthly_amount}
              onChange={(v) => set(post, setPost, 'monthly_amount', v)} required />
            <Field label="Start Age" type="number" value={post.start_age}
              onChange={(v) => set(post, setPost, 'start_age', v)} required min={40} max={100} />
            <label className="flex items-center gap-2 text-sm" style={{ color: 'var(--muted)' }}>
              <input
                type="checkbox"
                checked={post.is_guaranteed}
                onChange={(e) => set(post, setPost, 'is_guaranteed', e.target.checked)}
              />
              Guaranteed income
            </label>
            <StatusBox status={postStatus} />
            <button type="submit" disabled={postLoading}
              className="w-full py-3 rounded-xl text-sm font-medium transition-all hover:shadow-md disabled:opacity-50"
              style={{ background: 'var(--ink)', color: 'var(--gold)' }}>
              {postLoading ? 'Adding…' : 'Add Income Source'}
            </button>
          </form>
        </SectionCard>
      </div>
    </div>
  )
}

function SectionCard({ title, icon, children }) {
  return (
    <div className="rounded-2xl p-6 fade-up" style={{ background: 'white', border: '1px solid var(--border)' }}>
      <div className="flex items-center gap-2 mb-5">
        <div className="w-7 h-7 rounded-lg flex items-center justify-center"
          style={{ background: 'var(--cream)' }}>
          {icon}
        </div>
        <h2 className="text-sm font-medium uppercase tracking-widest" style={{ color: 'var(--muted)' }}>
          {title}
        </h2>
      </div>
      {children}
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
        onChange={(e) => onChange(e.target.value)}
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

function SelectField({ label, value, onChange, options }) {
  return (
    <div className="space-y-1.5">
      <label className="text-xs font-medium uppercase tracking-widest" style={{ color: 'var(--muted)' }}>
        {label}
      </label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full px-4 py-3 rounded-xl text-sm outline-none transition-all border focus:border-yellow-600"
        style={{ background: 'var(--cream)', borderColor: 'var(--border)', color: 'var(--ink)' }}
      >
        {options.map((o) => (
          <option key={o} value={o}>{o.replace('_', ' ')}</option>
        ))}
      </select>
    </div>
  )
}

function StatusBox({ status }) {
  if (!status?.msg) return null
  const isOk = status.type === 'ok'
  return (
    <div className="text-sm px-3 py-2 rounded-lg"
      style={{ background: isOk ? '#f0fdf4' : '#fef2f2', color: isOk ? 'var(--green)' : 'var(--red)' }}>
      {status.msg}
    </div>
  )
}
