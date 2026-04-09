'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from '@/components/ui/table'
import { 
  History, 
  Search, 
  Filter, 
  User, 
  Activity, 
  Key,
  ChevronDown,
  Info
} from 'lucide-react'
import { authenticatedFetch } from '@/utils/api-client'
import { format } from 'date-fns'

interface AuditLog {
  id: string
  actor: string
  action: string
  resource: string
  resource_id: string
  metadata: any
  created_at: string
}

export default function AuditLogPage() {
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [loading, setLoading] = useState(true)
  const [filterAction, setFilterAction] = useState('')
  const [filterActor, setFilterActor] = useState('')

  const fetchLogs = async () => {
    setLoading(true)
    try {
      let url = '/api/v1/audit?limit=100'
      if (filterAction) url += `&action=${filterAction}`
      if (filterActor) url += `&actor=${filterActor}`
      
      const data = await authenticatedFetch<AuditLog[]>(url)
      setLogs(data)
    } catch (error) {
      console.error('Failed to fetch audit logs:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchLogs()
  }, [filterAction, filterActor])

  const getActionColor = (action: string) => {
    switch (action) {
      case 'LOGIN':
      case 'SIGNUP': return 'bg-indigo-50 text-indigo-600 border-indigo-100'
      case 'TRIAGE_COMPLETED': return 'bg-pink-50 text-pink-600 border-pink-100'
      case 'CASE_RESOLVED': return 'bg-emerald-50 text-emerald-600 border-emerald-100'
      case 'LOAD_ADJUSTED': return 'bg-blue-50 text-blue-600 border-blue-100'
      default: return 'bg-slate-50 text-slate-600 border-slate-100'
    }
  }

  const getActionIcon = (action: string) => {
    switch (action) {
      case 'LOGIN':
      case 'SIGNUP': return <Key className="w-3.5 h-3.5" />
      case 'TRIAGE_COMPLETED': return <Activity className="w-3.5 h-3.5" />
      case 'CASE_RESOLVED': return <Info className="w-3.5 h-3.5" />
      default: return <History className="w-3.5 h-3.5" />
    }
  }

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-blue-600 font-bold uppercase tracking-widest text-[10px] mb-2">
            <div className="w-1.5 h-1.5 rounded-full bg-blue-600" />
            Compliance & Transparency
          </div>
          <h1 className="text-3xl font-black text-slate-900 tracking-tight">Audit <span className="text-blue-600">Trail</span></h1>
          <p className="text-slate-500 font-medium">Monitoring system-wide clinical and administrative events.</p>
        </div>
      </div>

      <Card className="border-slate-100 shadow-sm bg-white overflow-hidden">
        <CardHeader className="bg-slate-50/50 border-b border-slate-50 py-4">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <Input 
                placeholder="Filter by Actor (email)..." 
                value={filterActor}
                onChange={(e) => setFilterActor(e.target.value)}
                className="pl-10 bg-white border-slate-200 rounded-xl focus:ring-blue-500 focus:border-blue-500 h-11"
              />
            </div>
            <div className="relative flex-1">
              <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <select 
                value={filterAction}
                onChange={(e) => setFilterAction(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-white border border-slate-200 rounded-xl focus:ring-blue-500 focus:border-blue-500 h-11 appearance-none text-sm font-medium text-slate-700"
              >
                <option value="">All Actions</option>
                <option value="LOGIN">Authentication: LOGIN</option>
                <option value="SIGNUP">Authentication: SIGNUP</option>
                <option value="TRIAGE_COMPLETED">Clinical: TRIAGE</option>
                <option value="CASE_RESOLVED">Clinical: RESOLUTION</option>
                <option value="LOAD_ADJUSTED">Staff: LOAD SYNC</option>
              </select>
              <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="bg-slate-50/30 hover:bg-slate-50/30 border-slate-100">
                  <TableHead className="font-bold text-slate-900 py-4 pl-6 w-[20%]">Timestamp</TableHead>
                  <TableHead className="font-bold text-slate-900 py-4 w-[25%]">Actor</TableHead>
                  <TableHead className="font-bold text-slate-900 py-4 w-[20%]">Action</TableHead>
                  <TableHead className="font-bold text-slate-900 py-4 w-[15%]">Resource</TableHead>
                  <TableHead className="font-bold text-slate-900 py-4 pr-6 text-right">Details</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  Array.from({ length: 5 }).map((_, i) => (
                    <TableRow key={i} className="animate-pulse">
                      <TableCell colSpan={5} className="py-6 pl-6 pr-6"><div className="h-6 bg-slate-50 rounded-lg w-full" /></TableCell>
                    </TableRow>
                  ))
                ) : logs.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} className="h-40 text-center text-slate-400 font-medium">
                      No matching audit logs found.
                    </TableCell>
                  </TableRow>
                ) : (
                  logs.map((log) => (
                    <TableRow key={log.id} className="group hover:bg-slate-50/50 border-slate-50 transition-colors">
                      <TableCell className="py-4 pl-6 font-mono text-xs text-slate-400">
                        {format(new Date(log.created_at), 'MMM dd, HH:mm:ss')}
                      </TableCell>
                      <TableCell className="py-4">
                        <div className="flex items-center gap-2">
                          <div className="w-7 h-7 bg-slate-100 rounded-lg flex items-center justify-center">
                            <User className="w-3.5 h-3.5 text-slate-500" />
                          </div>
                          <span className="text-sm font-bold text-slate-700 truncate max-w-[180px]">
                            {log.actor}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell className="py-4">
                        <Badge className={`flex w-fit items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-wider border shadow-none ${getActionColor(log.action)}`}>
                          {getActionIcon(log.action)}
                          {log.action.replace('_', ' ')}
                        </Badge>
                      </TableCell>
                      <TableCell className="py-4">
                        <span className="text-xs font-bold text-slate-500 uppercase tracking-widest">{log.resource}</span>
                      </TableCell>
                      <TableCell className="py-4 pr-6 text-right">
                        <button className="text-[10px] font-black text-blue-600 uppercase tracking-widest hover:text-blue-700 underline underline-offset-4 decoration-blue-100 transition-colors">
                          Inspect Metadata
                        </button>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
