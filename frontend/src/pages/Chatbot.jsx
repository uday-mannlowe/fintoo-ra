// src/pages/Chatbot.jsx
import React, { useState, useEffect, useRef, useCallback } from 'react'
import { sendChatMessage, confirmChatChange, getChatHistory } from '../api'
import { Send, CheckCircle, XCircle, Loader, Bot, User } from 'lucide-react'

const SUGGESTIONS = [
  'My salary is now 1.2 lakh',
  'I took a home loan of 40 lakhs at 8.5%',
  'I started a SIP of 10000/month',
  'I want to retire at 57',
  'Am I on track for retirement?',
  'My EMI reduced to 25000',
]

export default function Chatbot({ userId }) {
  const [messages,    setMessages]    = useState([])
  const [input,       setInput]       = useState('')
  const [loading,     setLoading]     = useState(false)
  const [histLoading, setHistLoading] = useState(true)
  const [pending,     setPending]     = useState(null)   // { interactionId, intent, entities }
  const bottomRef = useRef(null)

  // Load history on mount
  useEffect(() => {
    getChatHistory(userId, 30)
      .then(res => {
        const hist = res.messages || []
        const mapped = hist.flatMap(h => {
          const msgs = []
          if (h.user_message)    msgs.push({ role: 'user',      text: h.user_message,    id: h.interaction_id + 'u' })
          if (h.assistant_reply) msgs.push({ role: 'assistant', text: h.assistant_reply, id: h.interaction_id + 'a', ledToUpdate: h.led_to_update })
          return msgs
        })
        if (mapped.length === 0) {
          setMessages([{
            role: 'assistant',
            id: 'welcome',
            text: "Hello! I'm your Retirement CFO. Tell me about any changes in your life — salary, investments, loans, or just ask me anything about your retirement plan.",
          }])
        } else {
          setMessages(mapped)
        }
      })
      .catch(() => {
        setMessages([{
          role: 'assistant', id: 'welcome',
          text: "Hello! I'm your Retirement CFO. How can I help you today?",
        }])
      })
      .finally(() => setHistLoading(false))
  }, [userId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const addMsg = (role, text, extra = {}) => {
    setMessages(m => [...m, { role, text, id: Date.now() + role, ...extra }])
  }

  const handleSend = async (text = input.trim()) => {
    if (!text || loading) return
    setInput('')
    addMsg('user', text)
    setLoading(true)
    try {
      const res = await sendChatMessage(userId, text)

      if (res.status === 'confirmation_required') {
        setPending({ interactionId: res.interaction_id, intent: res.intent, entities: res.entities })
        addMsg('assistant', res.message, { needsConfirm: true, interactionId: res.interaction_id })
      } else if (res.status === 'clarification_needed') {
        addMsg('assistant', res.message, { isClarification: true })
      } else {
        addMsg('assistant', res.message)
      }
    } catch (e) {
      addMsg('assistant', `Sorry, something went wrong: ${e.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleConfirm = async (interactionId, confirmed) => {
    // Remove the confirm buttons from that message
    setMessages(m => m.map(msg =>
      msg.interactionId === interactionId ? { ...msg, confirmed: true, confirmedValue: confirmed } : msg
    ))
    setPending(null)
    setLoading(true)
    try {
      const res = await confirmChatChange(userId, interactionId, confirmed)
      addMsg('assistant', res.message, { isResult: true, updated: res.db_updated, calc: res.updated_calculation })
    } catch (e) {
      addMsg('assistant', `Sorry, could not apply the change: ${e.message}`)
    } finally {
      setLoading(false)
    }
  }

  if (histLoading) return (
    <div className="flex items-center justify-center h-screen">
      <div className="w-6 h-6 rounded-full border-2 animate-spin"
        style={{ borderColor: 'var(--gold)', borderTopColor: 'transparent' }} />
    </div>
  )

  return (
    <div className="flex flex-col h-screen max-w-3xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-4 px-8 py-5 border-b flex-shrink-0"
        style={{ borderColor: 'var(--border)' }}>
        <div className="relative">
          <div className="w-10 h-10 rounded-full flex items-center justify-center"
            style={{ background: 'var(--ink)' }}>
            <Bot size={18} style={{ color: 'var(--gold)' }} />
          </div>
          <div className="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full pulse-dot"
            style={{ background: '#1a6b3c', border: '2px solid var(--paper)' }} />
        </div>
        <div>
          <h1 className="font-medium text-sm" style={{ color: 'var(--ink)' }}>CFO Assistant</h1>
          <p className="text-xs" style={{ color: 'var(--muted)' }}>Updates your plan in real time</p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-8 py-6 space-y-5">
        {messages.map((msg) => (
          <div key={msg.id}
            className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
            {/* Avatar */}
            <div className={`w-7 h-7 rounded-full flex-shrink-0 flex items-center justify-center mt-1`}
              style={{ background: msg.role === 'user' ? 'var(--ink)' : 'var(--cream)' }}>
              {msg.role === 'user'
                ? <User size={13} style={{ color: 'var(--gold)' }} />
                : <Bot  size={13} style={{ color: 'var(--muted)' }} />
              }
            </div>

            <div className={`flex flex-col gap-2 max-w-md ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
              {/* Bubble */}
              <div className={`px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-line
                ${msg.role === 'user'
                  ? 'rounded-tr-sm'
                  : 'rounded-tl-sm'
                }`}
                style={{
                  background: msg.role === 'user'
                    ? 'var(--ink)'
                    : msg.isResult && msg.updated
                      ? '#f0fdf4'
                      : 'white',
                  color: msg.role === 'user'
                    ? 'var(--paper)'
                    : msg.isResult && msg.updated ? 'var(--green)' : 'var(--ink)',
                  border: msg.role === 'user' ? 'none' : '1px solid var(--border)',
                }}>
                {msg.text}
              </div>

              {/* Confirmation buttons */}
              {msg.needsConfirm && !msg.confirmed && (
                <div className="flex gap-2 mt-1">
                  <button
                    onClick={() => handleConfirm(msg.interactionId, true)}
                    className="flex items-center gap-1.5 px-4 py-2 rounded-full text-xs font-medium
                      transition-all hover:shadow-sm hover:-translate-y-0.5"
                    style={{ background: '#1a6b3c', color: 'white' }}>
                    <CheckCircle size={12} /> Yes, update it
                  </button>
                  <button
                    onClick={() => handleConfirm(msg.interactionId, false)}
                    className="flex items-center gap-1.5 px-4 py-2 rounded-full text-xs font-medium
                      border transition-all hover:bg-white"
                    style={{ borderColor: 'var(--border)', color: 'var(--muted)' }}>
                    <XCircle size={12} /> No thanks
                  </button>
                </div>
              )}

              {/* After confirm — show mini calc update */}
              {msg.isResult && msg.updated && msg.calc && (
                <div className="grid grid-cols-3 gap-2 mt-1 w-full">
                  {[
                    { label: 'Readiness', value: `${Math.round(msg.calc.readiness_score ?? 0)}%` },
                    { label: 'Gap', value: fmtShort(msg.calc.corpus_gap) },
                    { label: 'Lasts until', value: msg.calc.money_lasts_until_age ? `Age ${msg.calc.money_lasts_until_age}` : '—' },
                  ].map(({ label, value }) => (
                    <div key={label} className="px-3 py-2 rounded-xl text-center"
                      style={{ background: 'var(--cream)', border: '1px solid var(--border)' }}>
                      <p className="text-xs" style={{ color: 'var(--muted)' }}>{label}</p>
                      <p className="font-medium text-sm" style={{ color: 'var(--ink)' }}>{value}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Typing indicator */}
        {loading && (
          <div className="flex gap-3">
            <div className="w-7 h-7 rounded-full flex items-center justify-center"
              style={{ background: 'var(--cream)' }}>
              <Bot size={13} style={{ color: 'var(--muted)' }} />
            </div>
            <div className="px-4 py-3 rounded-2xl rounded-tl-sm"
              style={{ background: 'white', border: '1px solid var(--border)' }}>
              <div className="flex gap-1 items-center h-4">
                {[0, 1, 2].map(i => (
                  <div key={i} className="w-1.5 h-1.5 rounded-full animate-bounce"
                    style={{ background: 'var(--muted)', animationDelay: `${i * 0.15}s` }} />
                ))}
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Suggestions (only when no pending) */}
      {!pending && messages.length <= 2 && (
        <div className="px-8 pb-3 flex flex-wrap gap-2">
          {SUGGESTIONS.map(s => (
            <button key={s} onClick={() => handleSend(s)}
              className="text-xs px-3 py-1.5 rounded-full border transition-all hover:bg-white"
              style={{ borderColor: 'var(--border)', color: 'var(--muted)' }}>
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div className="px-8 py-5 border-t flex-shrink-0" style={{ borderColor: 'var(--border)' }}>
        <form onSubmit={e => { e.preventDefault(); handleSend() }}
          className="flex gap-3 items-end">
          <textarea
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() }}}
            placeholder="Tell me about a change, or ask anything…"
            rows={1}
            className="flex-1 px-4 py-3 rounded-2xl text-sm outline-none border resize-none
              transition-all focus:border-yellow-600 focus:ring-2 focus:ring-yellow-600/10"
            style={{
              background: 'white',
              borderColor: 'var(--border)',
              color: 'var(--ink)',
              maxHeight: '120px',
            }}
          />
          <button type="submit" disabled={!input.trim() || loading}
            className="w-11 h-11 rounded-2xl flex items-center justify-center flex-shrink-0
              transition-all hover:opacity-80 disabled:opacity-30"
            style={{ background: 'var(--ink)' }}>
            <Send size={15} style={{ color: 'var(--gold)' }} />
          </button>
        </form>
      </div>
    </div>
  )
}

function fmtShort(n) {
  if (!n && n !== 0) return '—'
  const abs = Math.abs(n)
  const sign = n < 0 ? '-' : '+'
  if (abs >= 10000000) return `${sign}₹${(abs / 10000000).toFixed(1)}Cr`
  if (abs >= 100000)   return `${sign}₹${(abs / 100000).toFixed(1)}L`
  return `${sign}₹${Math.round(abs).toLocaleString('en-IN')}`
}
