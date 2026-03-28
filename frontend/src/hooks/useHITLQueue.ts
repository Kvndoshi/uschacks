import { useCallback } from 'react'
import { useMindStore } from '../store/useMindStore'

const API_BASE = '/api/v1/hitl'

export function useHITLQueue() {
  const hitlQueue = useMindStore((s) => s.hitlQueue)
  const resolveHITL = useMindStore((s) => s.resolveHITL)

  const approve = useCallback(async (hitlId: string) => {
    try {
      await fetch(`${API_BASE}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ hitl_id: hitlId }),
      })
      resolveHITL(hitlId)
    } catch (err) {
      console.error('Failed to approve:', err)
    }
  }, [resolveHITL])

  const reject = useCallback(async (hitlId: string) => {
    try {
      await fetch(`${API_BASE}/reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ hitl_id: hitlId }),
      })
      resolveHITL(hitlId)
    } catch (err) {
      console.error('Failed to reject:', err)
    }
  }, [resolveHITL])

  const edit = useCallback(async (hitlId: string, editedValue: string) => {
    try {
      await fetch(`${API_BASE}/edit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ hitl_id: hitlId, edited_value: editedValue }),
      })
      resolveHITL(hitlId)
    } catch (err) {
      console.error('Failed to edit:', err)
    }
  }, [resolveHITL])

  return { hitlQueue, approve, reject, edit }
}
