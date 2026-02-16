// src/api.js — All API calls in one place
const BASE = import.meta.env.VITE_API_BASE || '/api/v1'

async function req(method, path, body) {
  const res = await fetch(BASE + path, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Network error' }))
    let msg = 'Request failed'
    if (typeof err?.detail === 'string') {
      msg = err.detail
    } else if (Array.isArray(err?.detail)) {
      msg = err.detail.map((d) => {
        const loc = Array.isArray(d?.loc) ? d.loc.slice(1).join('.') : ''
        return loc ? `${loc}: ${d?.msg}` : d?.msg
      }).filter(Boolean).join(', ')
    } else if (err?.message) {
      msg = err.message
    }
    throw new Error(msg)
  }
  return res.json()
}

// ── Onboarding ───────────────────────────────────────────────────────────────
export const checkEmail = (email) =>
  req('POST', '/onboarding/check-email', { email })

export const completeOnboarding = (data) =>
  req('POST', '/onboarding/complete', data)

// 🔐 Auth (OTP)
export const requestOtp = (email) =>
  req('POST', '/auth/request-otp', { email })

export const verifyOtp = (email, otp) =>
  req('POST', '/auth/verify-otp', { email, otp })

export const getOnboardingStatus = (userId) =>
  req('GET', `/onboarding/status/${userId}`)

export const getSnapshot = (userId) =>
  req('GET', `/onboarding/snapshot/${userId}`)

export const updateIncome = (userId, data) =>
  req('POST', `/onboarding/income/${userId}`, data)

export const updateExpense = (userId, data) =>
  req('POST', `/onboarding/expenses/${userId}`, data)

export const addAssets = (userId, data) =>
  req('POST', `/onboarding/assets/${userId}`, data)

export const updateAsset = (userId, assetId, data) =>
  req('PUT', `/onboarding/assets/${userId}/${assetId}`, data)

export const addLoans = (userId, data) =>
  req('POST', `/onboarding/loans/${userId}`, data)

export const updateLoan = (userId, loanId, data) =>
  req('PUT', `/onboarding/loans/${userId}/${loanId}`, data)

export const addPostRetirementIncome = (userId, data) =>
  req('POST', `/onboarding/post-retirement-income/${userId}`, data)

// ── Calculations ─────────────────────────────────────────────────────────────
export const runCalculation = (userId) =>
  req('POST', `/calculations/run/${userId}`)

export const getLatestCalculation = (userId) =>
  req('GET', `/calculations/latest/${userId}`)

export const getCalculationHistory = (userId, limit = 10) =>
  req('GET', `/calculations/history/${userId}?limit=${limit}`)

export const getActiveAssumptions = () =>
  req('GET', '/calculations/assumptions/active')

// ── Chatbot ───────────────────────────────────────────────────────────────────
export const sendChatMessage = (userId, message) =>
  req('POST', `/chatbot/message/${userId}`, { message })

export const confirmChatChange = (userId, interactionId, confirmed) =>
  req('POST', `/chatbot/confirm/${userId}/${interactionId}`, { confirmed })

export const getChatHistory = (userId, limit = 30) =>
  req('GET', `/chatbot/history/${userId}?limit=${limit}`)
