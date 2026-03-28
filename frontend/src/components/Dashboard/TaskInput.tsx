import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Sparkles, Zap, Globe, Mail, Plane } from 'lucide-react'
import { useMindStore } from '../../store/useMindStore'

const EXAMPLE_TASKS = [
  {
    icon: Globe,
    label: 'Research AI News',
    task: 'Research the top 5 AI news stories today and compile a summary doc',
  },
  {
    icon: Mail,
    label: 'Draft Email Reply',
    task: 'Draft a reply to this email thread and send it',
  },
  {
    icon: Plane,
    label: 'Find Flights',
    task: 'Find flight prices LHR→JFK next week and screenshot the cheapest options',
  },
]

export function TaskInput() {
  const [task, setTask] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const setStoreTask = useMindStore((s) => s.setTask)
  const reset = useMindStore((s) => s.reset)
  const taskStatus = useMindStore((s) => s.task.status)

  const handleSubmit = async () => {
    if (!task.trim() || isSubmitting) return

    setIsSubmitting(true)
    reset()
    setStoreTask({ masterTask: task, status: 'decomposing' })

    try {
      await fetch('/api/v1/tasks/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task: task.trim() }),
      })
      setTask('')
    } catch (err) {
      console.error('Submit failed:', err)
      setStoreTask({ status: 'failed' })
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="space-y-3">
      <div className="relative">
        <div className="glass rounded-2xl overflow-hidden glow-purple">
          <div className="flex items-center gap-3 p-1.5">
            <div className="flex-1 relative">
              <input
                type="text"
                value={task}
                onChange={(e) => setTask(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
                placeholder="Describe a task for the swarm..."
                disabled={isSubmitting || taskStatus === 'running'}
                className="w-full px-4 py-3 bg-transparent text-sm text-white
                           placeholder:text-zinc-500 focus:outline-none disabled:opacity-50"
              />
            </div>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleSubmit}
              disabled={!task.trim() || isSubmitting || taskStatus === 'running'}
              className="flex items-center gap-2 px-5 py-3 rounded-xl
                         bg-gradient-to-r from-purple-600 to-indigo-600
                         hover:from-purple-500 hover:to-indigo-500
                         disabled:opacity-40 disabled:cursor-not-allowed
                         text-sm font-medium text-white transition-all
                         shadow-lg shadow-purple-600/20"
            >
              {isSubmitting ? (
                <Zap className="w-4 h-4 animate-pulse" />
              ) : (
                <Send className="w-4 h-4" />
              )}
              <span className="hidden sm:inline">Deploy Swarm</span>
            </motion.button>
          </div>
        </div>
      </div>

      <AnimatePresence>
        {taskStatus === 'idle' && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="flex gap-2 flex-wrap"
          >
            {EXAMPLE_TASKS.map((example) => (
              <button
                key={example.label}
                onClick={() => setTask(example.task)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl
                           bg-white/5 hover:bg-white/10 border border-white/5
                           hover:border-purple-500/30 text-xs text-zinc-400
                           hover:text-zinc-200 transition-all group"
              >
                <example.icon className="w-3 h-3 text-zinc-500 group-hover:text-purple-400 transition-colors" />
                {example.label}
              </button>
            ))}
            <div className="flex items-center gap-1 text-[10px] text-zinc-600 ml-1">
              <Sparkles className="w-3 h-3" />
              Try an example
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
