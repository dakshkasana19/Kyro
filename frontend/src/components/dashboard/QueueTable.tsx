'use client'

import { useEffect, useState } from 'react'
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { TriageQueueItem } from '@/types/dashboard'
import { authenticatedFetch } from '@/utils/api-client'
import { useSocket } from '@/hooks/use-socket'
import { formatDistanceToNow } from 'date-fns'
import { AlertCircle, Clock,User } from 'lucide-react'

export function QueueTable() {
  const [queue, setQueue] = useState<TriageQueueItem[]>([])
  const [loading, setLoading] = useState(true)
  const { socket } = useSocket()

  const fetchQueue = async () => {
    try {
      const data = await authenticatedFetch<TriageQueueItem[]>('/api/queue')
      setQueue(data)
    } catch (error) {
      console.error('Failed to fetch queue:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchQueue()
  }, [])

  useEffect(() => {
    if (!socket) return

    socket.on('queue:update', () => {
      console.log('Queue update received via socket')
      fetchQueue()
    })

    return () => {
      socket.off('queue:update')
    }
  }, [socket])

  const getSeverityColor = (level: number) => {
    switch (level) {
      case 3: return 'bg-rose-100 text-rose-600 border-rose-200' // Critical
      case 2: return 'bg-amber-100 text-amber-600 border-amber-200' // High
      case 1: return 'bg-blue-100 text-blue-600 border-blue-200' // Medium
      default: return 'bg-slate-100 text-slate-600 border-slate-200' // Low
    }
  }

  if (loading) {
    return (
      <div className="space-y-4">
        {[...Array(5)].map((_, i) => (
          <Skeleton key={i} className="h-16 w-full rounded-xl bg-slate-50" />
        ))}
      </div>
    )
  }

  return (
    <div className="bg-white rounded-2xl border border-slate-100 overflow-hidden shadow-sm">
      <Table>
        <TableHeader className="bg-slate-50/50">
          <TableRow className="hover:bg-transparent border-slate-100">
            <TableHead className="font-semibold text-slate-900 py-4">Patient</TableHead>
            <TableHead className="font-semibold text-slate-900 py-4 text-center">Severity</TableHead>
            <TableHead className="font-semibold text-slate-900 py-4">Assigned Doctor</TableHead>
            <TableHead className="font-semibold text-slate-900 py-4 text-right">Waiting Since</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {queue.length === 0 ? (
            <TableRow>
              <TableCell colSpan={4} className="h-32 text-center text-slate-400">
                No patients in queue
              </TableCell>
            </TableRow>
          ) : (
            queue.map((item) => (
              <TableRow key={item.patient_id} className="group hover:bg-slate-50/50 border-slate-50 transition-colors">
                <TableCell className="py-4">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-full bg-blue-50 flex items-center justify-center">
                      <User className="w-5 h-5 text-blue-500" />
                    </div>
                    <div>
                      <div className="font-medium text-slate-900">{item.patient_name}</div>
                      <div className="text-xs text-slate-500 font-mono">{item.patient_id.slice(0, 8)}</div>
                    </div>
                  </div>
                </TableCell>
                <TableCell className="text-center py-4">
                  <Badge className={`px-3 py-1 rounded-full font-semibold border ${getSeverityColor(item.severity_level)} shadow-none`}>
                    {item.severity_level === 3 && <AlertCircle className="w-3 h-3 mr-1" />}
                    {item.severity_label}
                  </Badge>
                </TableCell>
                <TableCell className="py-4">
                  <div className="flex items-center gap-2">
                    {item.assigned_doctor ? (
                      <>
                        <div className="w-2 h-2 rounded-full bg-emerald-500" />
                        <span className="text-slate-700 font-medium">{item.assigned_doctor}</span>
                      </>
                    ) : (
                      <span className="text-slate-400 italic text-sm">Awaiting assignment</span>
                    )}
                  </div>
                </TableCell>
                <TableCell className="text-right py-4">
                  <div className="flex items-center justify-end gap-2 text-slate-500 text-sm">
                    <Clock className="w-4 h-4" />
                    {formatDistanceToNow(new Date(item.created_at), { addSuffix: true })}
                  </div>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>
  )
}
