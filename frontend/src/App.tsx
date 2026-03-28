import { useState, useCallback, useEffect, useRef } from 'react'
import { useWebSocket } from './store/useWebSocket'
import { useMindStore } from './store/useMindStore'
import { MindGraph } from './components/MindMap/HiveGraph'
import { HITLPanel } from './components/HITL/HITLPanel'
import { AgentLogPanel } from './components/Dashboard/AgentLogPanel'
import { VoiceIndicator } from './components/Dashboard/VoiceIndicator'
import { CommandBar } from './components/Dashboard/CommandBar'
import { EventFeed } from './components/Dashboard/EventFeed'
import { TabChips } from './components/Tabs/TabChips'
import { TabPanel } from './components/Tabs/TabPanel'
import { TabGridPanel } from './components/Tabs/TabGridPanel'
import { AnimatePresence, motion } from 'framer-motion'
import { Brain, Activity, Layers, Terminal, Sparkles, X, GripHorizontal, ChevronRight, History } from 'lucide-react'

function App() {
  useWebSocket()
  const agents = useMindStore((s) => s.agents)
  const task = useMindStore((s) => s.task)
  const hitlQueue = useMindStore((s) => s.hitlQueue)
  const selectedAgentId = useMindStore((s) => s.selectedAgentId)
  const selectAgent = useMindStore((s) => s.selectAgent)

  const completedTasks = useMindStore((s) => s.completedTasks)

  const [showTabPanel, setShowTabPanel] = useState(false)
  const [showLogPanel, setShowLogPanel] = useState(false)
  const [showResults, setShowResults] = useState(false)
  const [showGrid, setShowGrid] = useState(false)
  const [showHistory, setShowHistory] = useState(false)

  // Resizable results panel
  const [resultsHeight, setResultsHeight] = useState(280)
  const [resultTab, setResultTab] = useState<'summary' | string>('summary')
  const resultsDragRef = useRef<{ startY: number; startH: number } | null>(null)

  const onResultsDragStart = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    resultsDragRef.current = { startY: e.clientY, startH: resultsHeight }
    const onMove = (ev: MouseEvent) => {
      if (!resultsDragRef.current) return
      const delta = resultsDragRef.current.startY - ev.clientY
      setResultsHeight(Math.max(120, Math.min(window.innerHeight * 0.8, resultsDragRef.current.startH + delta)))
    }
    const onUp = () => {
      resultsDragRef.current = null
      document.removeEventListener('mousemove', onMove)
      document.removeEventListener('mouseup', onUp)
    }
    document.addEventListener('mousemove', onMove)
    document.addEventListener('mouseup', onUp)
  }, [resultsHeight])

  const agentList = Object.values(agents)
  const runningCount = agentList.filter((a) => a.status === 'running').length
  const hitlCount = hitlQueue.length

  // Auto-show log panel when agents spawn
  useEffect(() => {
    if (agentList.length > 0 && !showLogPanel) {
      setShowLogPanel(true)
    }
  }, [agentList.length])

  // Auto-show results when task completes
  useEffect(() => {
    if (task.status === 'completed' && task.finalResult) {
      setShowResults(true)
    }
  }, [task.status, task.finalResult])

  // Close log panel if no agents
  useEffect(() => {
    if (agentList.length === 0) {
      setShowLogPanel(false)
      setShowResults(false)
    }
  }, [agentList.length])

  // Keyboard shortcuts
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return
      if (e.ctrlKey || e.metaKey) return
      if (e.key === 'l' || e.key === 'L') { setShowLogPanel((p) => !p); setShowTabPanel(false) }
      if (e.key === 't' || e.key === 'T') { setShowTabPanel((p) => !p); setShowLogPanel(false) }
      if (e.key === 'g' || e.key === 'G') { setShowGrid((p) => !p) }
      if (e.key === 'v' || e.key === 'V') {
        // Toggle live voice via store — CommandBar will detect the change
        const store = useMindStore.getState()
        if (store.isLiveVoice) {
          store.setLiveVoice(false, 'idle', '')
        }
        // If not active, we can't start it here (needs MediaRecorder setup in CommandBar)
        // So we just signal the toggle via a custom event that CommandBar listens to
        window.dispatchEvent(new CustomEvent('mindd:toggle-live-voice'))
      }
      if (e.key === 'Escape') {
        setShowTabPanel(false)
        setShowLogPanel(false)
        setShowGrid(false)
        selectAgent(null)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [selectAgent])

  const isActive = task.status === 'running' || task.status === 'decomposing'

  return (
    <div className="h-screen w-screen flex flex-col overflow-hidden" style={{ background: '#060810' }}>
      {/* ─── Top Header Bar ──────────────────────────────────── */}
      <header
        className="shrink-0 flex items-center gap-3 px-4 h-11"
        style={{ borderBottom: '1px solid rgba(0,212,255,0.07)', background: 'rgba(6,8,16,0.95)' }}
      >
        {/* Logo */}
        <div className="flex items-center gap-2 shrink-0">
          <motion.div
            animate={isActive ? {
              boxShadow: [
                '0 0 8px rgba(0,212,255,0.3)',
                '0 0 20px rgba(0,212,255,0.5)',
                '0 0 8px rgba(0,212,255,0.3)',
              ]
            } : {}}
            transition={{ duration: 2, repeat: Infinity }}
            className="w-7 h-7 rounded-lg flex items-center justify-center"
            style={{
              background: 'linear-gradient(135deg, rgba(0,212,255,0.12), rgba(139,92,246,0.12))',
              border: '1px solid rgba(0,212,255,0.2)',
            }}
          >
            <Brain className="w-4 h-4" style={{ color: '#00d4ff' }} />
          </motion.div>
          <span className="text-sm font-bold terminal-text text-gradient-cyan tracking-wide">
            MINDD
          </span>
          <span
            className="terminal-text text-[9px] px-1.5 py-0.5 rounded"
            style={{ background: 'rgba(0,212,255,0.06)', color: 'rgba(0,212,255,0.4)', border: '1px solid rgba(0,212,255,0.1)' }}
          >
            v1.0
          </span>
        </div>

        {/* Divider */}
        <div className="w-px h-4 mx-1" style={{ background: 'rgba(0,212,255,0.1)' }} />

        {/* Active task name */}
        {task.masterTask && (
          <motion.div
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            className="hidden md:flex items-center gap-1.5 min-w-0 flex-1 max-w-xs"
          >
            {isActive && (
              <motion.div
                animate={{ opacity: [0.4, 1, 0.4] }}
                transition={{ duration: 1, repeat: Infinity }}
                className="w-1.5 h-1.5 rounded-full shrink-0"
                style={{ background: '#00d4ff' }}
              />
            )}
            <span className="terminal-text text-[10px] truncate" style={{ color: 'rgba(255,255,255,0.4)' }}>
              {task.masterTask}
            </span>
          </motion.div>
        )}

        <div className="flex-1" />

        {/* Tab chips */}
        <TabChips onOpenPanel={() => { setShowTabPanel(true); setShowLogPanel(false) }} />

        {/* Divider */}
        <div className="w-px h-4 mx-2" style={{ background: 'rgba(255,255,255,0.06)' }} />

        {/* Action buttons */}
        <div className="flex items-center gap-1.5 shrink-0">
          {/* HITL indicator */}
          <AnimatePresence>
            {hitlCount > 0 && (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                exit={{ scale: 0 }}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg terminal-text text-[10px]"
                style={{
                  background: 'rgba(245,185,66,0.1)',
                  border: '1px solid rgba(245,185,66,0.25)',
                  color: '#f5b942',
                }}
              >
                <motion.div
                  animate={{ opacity: [0.5, 1, 0.5] }}
                  transition={{ duration: 0.8, repeat: Infinity }}
                  className="w-1.5 h-1.5 rounded-full"
                  style={{ background: '#f5b942' }}
                />
                {hitlCount} review{hitlCount !== 1 ? 's' : ''}
              </motion.div>
            )}
          </AnimatePresence>

          {/* Agent count */}
          <AnimatePresence>
            {agentList.length > 0 && (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                exit={{ scale: 0 }}
                className="flex items-center gap-1 px-2 py-1 rounded-lg terminal-text text-[10px]"
                style={{
                  background: 'rgba(0,212,255,0.06)',
                  border: '1px solid rgba(0,212,255,0.12)',
                  color: 'rgba(0,212,255,0.6)',
                }}
              >
                <Activity className="w-3 h-3" />
                {agentList.length} agent{agentList.length !== 1 ? 's' : ''}
                {runningCount > 0 && (
                  <motion.span
                    animate={{ opacity: [0.5, 1, 0.5] }}
                    transition={{ duration: 0.8, repeat: Infinity }}
                    className="ml-1"
                  >
                    · {runningCount} live
                  </motion.span>
                )}
              </motion.div>
            )}
          </AnimatePresence>

          {/* Panel toggles */}
          <button
            onClick={() => { setShowLogPanel((p) => !p); setShowTabPanel(false) }}
            title="Toggle Logs (L)"
            className="w-7 h-7 rounded-lg flex items-center justify-center transition-all"
            style={{
              background: showLogPanel ? 'rgba(139,92,246,0.15)' : 'rgba(255,255,255,0.04)',
              border: showLogPanel ? '1px solid rgba(139,92,246,0.3)' : '1px solid rgba(255,255,255,0.06)',
              color: showLogPanel ? '#8b5cf6' : 'rgba(255,255,255,0.3)',
            }}
          >
            <Terminal className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => { setShowTabPanel((p) => !p); setShowLogPanel(false) }}
            title="Toggle Tabs (T)"
            className="w-7 h-7 rounded-lg flex items-center justify-center transition-all"
            style={{
              background: showTabPanel ? 'rgba(0,212,255,0.1)' : 'rgba(255,255,255,0.04)',
              border: showTabPanel ? '1px solid rgba(0,212,255,0.25)' : '1px solid rgba(255,255,255,0.06)',
              color: showTabPanel ? '#00d4ff' : 'rgba(255,255,255,0.3)',
            }}
          >
            <Layers className="w-3.5 h-3.5" />
          </button>
        </div>
      </header>

      {/* ─── Tab Grid Overlay ────────────────────────────────── */}
      {showGrid && <TabGridPanel onClose={() => setShowGrid(false)} />}

      {/* ─── Main Canvas Area ─────────────────────────────────── */}
      <div className="flex-1 relative min-h-0">
        <MindGraph />

        {/* HITL panel (top-right overlay) */}
        <AnimatePresence>
          {hitlCount > 0 && <HITLPanel />}
        </AnimatePresence>

        {/* Log panel (right side drawer) */}
        <AnimatePresence>
          {showLogPanel && agentList.length > 0 && (
            <AgentLogPanel onClose={() => { setShowLogPanel(false); selectAgent(null) }} />
          )}
        </AnimatePresence>

        {/* Tab panel (right side drawer) */}
        <AnimatePresence>
          {showTabPanel && (
            <TabPanel onClose={() => setShowTabPanel(false)} />
          )}
        </AnimatePresence>

        {/* Results panel (resizable, per-agent output) */}
        <AnimatePresence>
          {showResults && task.finalResult && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 20 }}
              className="absolute bottom-4 left-4 right-4 z-30 flex flex-col"
              style={{ height: resultsHeight }}
            >
              <div
                className="rounded-2xl overflow-hidden flex flex-col h-full"
                style={{
                  background: 'rgba(10,13,22,0.97)',
                  border: '1px solid rgba(16,217,160,0.2)',
                  backdropFilter: 'blur(20px)',
                  boxShadow: '0 0 30px rgba(16,217,160,0.08)',
                }}
              >
                {/* Drag handle */}
                <div
                  className="h-3 cursor-row-resize flex items-center justify-center shrink-0 hover:bg-white/5 transition-colors rounded-t-2xl"
                  onMouseDown={onResultsDragStart}
                >
                  <GripHorizontal className="w-4 h-2.5" style={{ color: 'rgba(255,255,255,0.15)' }} />
                </div>

                {/* Header with tab switcher */}
                <div
                  className="px-4 py-2 flex items-center justify-between shrink-0"
                  style={{ borderBottom: '1px solid rgba(16,217,160,0.1)' }}
                >
                  <div className="flex items-center gap-2 overflow-x-auto min-w-0">
                    <Sparkles className="w-4 h-4 shrink-0" style={{ color: '#10d9a0' }} />
                    <span className="text-xs font-semibold text-white shrink-0">Task Complete</span>

                    {/* Tab buttons */}
                    <div className="flex items-center gap-1 ml-2">
                      <button
                        onClick={() => setResultTab('summary')}
                        className="px-2 py-0.5 rounded text-[10px] terminal-text transition-all"
                        style={{
                          background: resultTab === 'summary' ? 'rgba(16,217,160,0.15)' : 'rgba(255,255,255,0.04)',
                          border: `1px solid ${resultTab === 'summary' ? 'rgba(16,217,160,0.3)' : 'rgba(255,255,255,0.06)'}`,
                          color: resultTab === 'summary' ? '#10d9a0' : 'rgba(255,255,255,0.4)',
                        }}
                      >
                        Summary
                      </button>
                      {task.agentResults.map((r, i) => (
                        <button
                          key={r.agentId}
                          onClick={() => setResultTab(r.agentId)}
                          className="px-2 py-0.5 rounded text-[10px] terminal-text transition-all"
                          style={{
                            background: resultTab === r.agentId ? 'rgba(139,92,246,0.15)' : 'rgba(255,255,255,0.04)',
                            border: `1px solid ${resultTab === r.agentId ? 'rgba(139,92,246,0.3)' : 'rgba(255,255,255,0.06)'}`,
                            color: resultTab === r.agentId ? '#8b5cf6' : 'rgba(255,255,255,0.4)',
                          }}
                        >
                          Agent {i + 1}
                          <span className="ml-1 opacity-50">({r.stepsTaken}s)</span>
                        </button>
                      ))}

                      {/* History toggle */}
                      {completedTasks.length > 1 && (
                        <button
                          onClick={() => setShowHistory((p) => !p)}
                          className="px-2 py-0.5 rounded text-[10px] terminal-text transition-all ml-1"
                          style={{
                            background: showHistory ? 'rgba(0,212,255,0.1)' : 'rgba(255,255,255,0.04)',
                            border: `1px solid ${showHistory ? 'rgba(0,212,255,0.2)' : 'rgba(255,255,255,0.06)'}`,
                            color: showHistory ? '#00d4ff' : 'rgba(255,255,255,0.3)',
                          }}
                        >
                          <History className="w-2.5 h-2.5 inline mr-0.5" />
                          {completedTasks.length}
                        </button>
                      )}
                    </div>
                  </div>
                  <button onClick={() => setShowResults(false)} className="shrink-0 ml-2" title="Close results">
                    <X className="w-4 h-4" style={{ color: 'rgba(255,255,255,0.3)' }} />
                  </button>
                </div>

                {/* Content area */}
                <div className="flex-1 overflow-y-auto p-4 min-h-0">
                  {showHistory ? (
                    <div className="space-y-3">
                      {[...completedTasks].reverse().map((ct, i) => (
                        <div key={ct.taskId + i} className="rounded-lg p-3" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
                          <div className="flex items-center gap-2 mb-1.5">
                            <ChevronRight className="w-3 h-3" style={{ color: '#10d9a0' }} />
                            <span className="terminal-text text-[11px] font-medium" style={{ color: 'rgba(255,255,255,0.8)' }}>
                              {ct.masterTask.length > 80 ? ct.masterTask.slice(0, 80) + '...' : ct.masterTask}
                            </span>
                            <span className="terminal-text text-[9px]" style={{ color: 'rgba(255,255,255,0.3)' }}>
                              {ct.agentResults.length} agent{ct.agentResults.length !== 1 ? 's' : ''}
                            </span>
                          </div>
                          <p className="terminal-text text-[11px] leading-relaxed whitespace-pre-wrap" style={{ color: 'rgba(255,255,255,0.55)' }}>
                            {ct.finalResult.length > 300 ? ct.finalResult.slice(0, 300) + '...' : ct.finalResult}
                          </p>
                        </div>
                      ))}
                    </div>
                  ) : resultTab === 'summary' ? (
                    <p className="terminal-text text-xs leading-relaxed whitespace-pre-wrap" style={{ color: 'rgba(255,255,255,0.7)' }}>
                      {task.finalResult}
                    </p>
                  ) : (
                    (() => {
                      const agentResult = task.agentResults.find((r) => r.agentId === resultTab)
                      if (!agentResult) return null
                      const agentState = agents[resultTab]
                      return (
                        <div>
                          <div className="flex items-center gap-2 mb-3">
                            <span className="terminal-text text-[10px] px-2 py-0.5 rounded" style={{ background: 'rgba(139,92,246,0.1)', color: '#8b5cf6', border: '1px solid rgba(139,92,246,0.2)' }}>
                              {agentResult.stepsTaken} steps
                            </span>
                            {agentState?.taskDescription && (
                              <span className="terminal-text text-[10px] truncate" style={{ color: 'rgba(255,255,255,0.4)' }}>
                                {agentState.taskDescription.slice(0, 100)}
                              </span>
                            )}
                          </div>
                          <p className="terminal-text text-xs leading-relaxed whitespace-pre-wrap" style={{ color: 'rgba(255,255,255,0.7)' }}>
                            {agentResult.result}
                          </p>
                        </div>
                      )
                    })()
                  )}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Voice indicator */}
        <VoiceIndicator />
      </div>

      {/* ─── Event Feed ──────────────────────────────────────── */}
      <EventFeed />

      {/* ─── Command Bar ─────────────────────────────────────── */}
      <CommandBar
        onOpenTabs={() => { setShowTabPanel(true); setShowLogPanel(false) }}
        onOpenLogs={() => { setShowLogPanel(true); setShowTabPanel(false) }}
      />
    </div>
  )
}

export default App
