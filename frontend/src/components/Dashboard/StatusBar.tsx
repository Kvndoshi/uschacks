import { motion } from 'framer-motion'
import { Activity, Users, CheckCircle, AlertTriangle, XCircle } from 'lucide-react'
import { useMindStore } from '../../store/useMindStore'
import { HITLBadge } from '../HITL/HITLBadge'

export function StatusBar() {
  const agents = useMindStore((s) => s.agents)
  const task = useMindStore((s) => s.task)
  const hitlQueue = useMindStore((s) => s.hitlQueue)

  const agentList = Object.values(agents)
  const running = agentList.filter((a) => a.status === 'running' || a.status === 'planning').length
  const completed = agentList.filter((a) => a.status === 'completed').length
  const failed = agentList.filter((a) => a.status === 'error').length

  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-1.5">
          <Users className="w-3.5 h-3.5 text-zinc-500" />
          <span className="text-xs text-zinc-400">
            <span className="text-white font-medium">{agentList.length}</span> agents
          </span>
        </div>

        {running > 0 && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            className="flex items-center gap-1.5"
          >
            <Activity className="w-3.5 h-3.5 text-blue-400 animate-pulse" />
            <span className="text-xs text-zinc-400">
              <span className="text-blue-300 font-medium">{running}</span> active
            </span>
          </motion.div>
        )}

        {completed > 0 && (
          <div className="flex items-center gap-1.5">
            <CheckCircle className="w-3.5 h-3.5 text-green-400" />
            <span className="text-xs text-zinc-400">
              <span className="text-green-300 font-medium">{completed}</span> done
            </span>
          </div>
        )}

        {failed > 0 && (
          <div className="flex items-center gap-1.5">
            <XCircle className="w-3.5 h-3.5 text-red-400" />
            <span className="text-xs text-zinc-400">
              <span className="text-red-300 font-medium">{failed}</span> failed
            </span>
          </div>
        )}
      </div>

      <div className="flex items-center gap-3">
        <HITLBadge count={hitlQueue.length} />

        {task.status === 'completed' && task.finalResult && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            className="flex items-center gap-1.5 px-3 py-1 rounded-full
                       bg-green-500/15 border border-green-500/30"
          >
            <CheckCircle className="w-3.5 h-3.5 text-green-400" />
            <span className="text-xs font-medium text-green-300">Task Complete</span>
          </motion.div>
        )}
      </div>
    </div>
  )
}
