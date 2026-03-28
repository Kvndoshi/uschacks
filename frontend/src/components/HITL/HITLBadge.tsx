import { motion } from 'framer-motion'
import { AlertTriangle } from 'lucide-react'

interface HITLBadgeProps {
  count: number
}

export function HITLBadge({ count }: HITLBadgeProps) {
  if (count === 0) return null

  return (
    <motion.div
      initial={{ scale: 0, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      className="flex items-center gap-2 px-3 py-1.5 rounded-full
                 bg-yellow-500/15 border border-yellow-500/30"
    >
      <motion.div
        animate={{ rotate: [0, -10, 10, -10, 0] }}
        transition={{ duration: 0.5, repeat: Infinity, repeatDelay: 2 }}
      >
        <AlertTriangle className="w-4 h-4 text-yellow-400" />
      </motion.div>
      <span className="text-sm font-medium text-yellow-300">
        {count} Action{count !== 1 ? 's' : ''} Needed
      </span>
    </motion.div>
  )
}
