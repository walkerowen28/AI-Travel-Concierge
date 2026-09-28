import { useState, type FormEvent } from 'react'
import { useLocation } from 'react-router-dom'
import { ApiError, sendChat } from '../api/client'
import type { ChatMessage, ToolTrace } from '../api/types'

type TranscriptItem =
  | { kind: 'message'; role: 'user' | 'assistant'; content: string }
  | { kind: 'traces'; traces: ToolTrace[] }

type Props = {
  reservationId?: number | null
}

export function ChatPanel({ reservationId = null }: Props) {
  const location = useLocation()
  const [open, setOpen] = useState(false)
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [transcript, setTranscript] = useState<TranscriptItem[]>([])
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Prefer an explicit prop; otherwise look for ?reservation_id= on reservations flows.
  const queryReservation = new URLSearchParams(location.search).get('reservation_id')
  const activeReservationId =
    reservationId ?? (queryReservation ? Number(queryReservation) : null)

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    const content = input.trim()
    if (!content || pending) return

    const nextMessages: ChatMessage[] = [...messages, { role: 'user', content }]
    setMessages(nextMessages)
    setTranscript((prev) => [...prev, { kind: 'message', role: 'user', content }])
    setInput('')
    setPending(true)
    setError(null)

    try {
      const response = await sendChat(
        nextMessages,
        Number.isFinite(activeReservationId as number)
          ? (activeReservationId as number)
          : null,
      )
      setMessages((prev) => [...prev, { role: 'assistant', content: response.message }])
      setTranscript((prev) => {
        const next: TranscriptItem[] = [...prev]
        if (response.tool_traces.length > 0) {
          next.push({ kind: 'traces', traces: response.tool_traces })
        }
        next.push({ kind: 'message', role: 'assistant', content: response.message })
        return next
      })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Chat failed.')
    } finally {
      setPending(false)
    }
  }

  return (
    <>
      <button
        type="button"
        className="chat-fab"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
      >
        {open ? 'Close concierge' : 'AI Concierge'}
      </button>

      {open && (
        <aside className="chat-panel" aria-label="AI Concierge chat">
          <header className="chat-header">
            <div>
              <strong>AI Concierge</strong>
              <p>
                Ask about stays, house rules, nearby spots, or manage a reservation.
                {activeReservationId ? ` Context: reservation #${activeReservationId}` : ''}
              </p>
            </div>
          </header>

          <div className="chat-log">
            {transcript.length === 0 && (
              <p className="chat-empty">
                Try “quiet loft in Austin under $200 for 2” or “what’s nearby for dinner?”
              </p>
            )}
            {transcript.map((item, index) =>
              item.kind === 'message' ? (
                <div key={`${item.role}-${index}`} className={`chat-bubble ${item.role}`}>
                  {item.content}
                </div>
              ) : (
                <ul key={`traces-${index}`} className="chat-traces">
                  {item.traces.map((trace, traceIndex) => (
                    <li key={`${trace.tool}-${traceIndex}`}>
                      tool used: <code>{trace.tool}</code>
                      {trace.detail ? ` — ${trace.detail}` : ''}
                    </li>
                  ))}
                </ul>
              ),
            )}
          </div>

          {error && <p className="status-bad chat-error">{error}</p>}

          <form className="chat-form" onSubmit={onSubmit}>
            <input
              type="text"
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="Ask the concierge…"
              disabled={pending}
            />
            <button type="submit" disabled={pending || !input.trim()}>
              {pending ? 'Thinking…' : 'Send'}
            </button>
          </form>
        </aside>
      )}
    </>
  )
}
