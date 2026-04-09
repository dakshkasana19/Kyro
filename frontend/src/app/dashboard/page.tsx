'use client'

import { Card, CardContent } from '@/components/ui/card'
import { QueueTable } from '@/components/dashboard/QueueTable'
import { DoctorPanel } from '@/components/dashboard/DoctorPanel'
import { Activity, Users, Clock, AlertTriangle } from 'lucide-react'

export default function DashboardOverview() {
  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      {/* Header Section */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
            Dashboard <span className="text-blue-600 font-medium">Overview</span>
          </h1>
          <p className="text-slate-500 font-medium mt-1">
            Real-time monitoring for emergency triage operations.
          </p>
        </div>
        
        <div className="flex items-center gap-2 bg-white px-4 py-2 rounded-2xl border border-slate-100 shadow-sm">
          <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-sm font-bold text-slate-600 uppercase tracking-widest">System Live</span>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[
          { label: 'Total Waiting', value: '12', icon: Clock, color: 'text-blue-600', bg: 'bg-blue-50' },
          { label: 'Critical Cases', value: '3', icon: AlertTriangle, color: 'text-rose-600', bg: 'bg-rose-50' },
          { label: 'Active Staff', value: '8', icon: Users, color: 'text-emerald-600', bg: 'bg-emerald-50' },
          { label: 'Triage Speed', value: '4.2m', icon: Activity, color: 'text-pink-600', bg: 'bg-pink-50' },
        ].map((stat, idx) => (
          <Card key={idx} className="border-none shadow-sm hover:shadow-md transition-shadow duration-300 overflow-hidden bg-white">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className={`${stat.bg} p-3 rounded-xl shadow-sm`}>
                  <stat.icon className={`w-6 h-6 ${stat.color}`} />
                </div>
                <div className="text-2xl font-black text-slate-900">{stat.value}</div>
              </div>
              <p className="text-sm font-bold text-slate-500 uppercase tracking-wider">{stat.label}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Queue Section */}
        <div className="lg:col-span-2 space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-extrabold text-slate-900">Priority Triage Queue</h2>
            <div className="text-xs font-bold text-blue-600 bg-blue-50 px-3 py-1 rounded-full border border-blue-100 uppercase tracking-wide">
              Live Feed
            </div>
          </div>
          <QueueTable />
        </div>

        {/* Staff Sidebar Section */}
        <div className="space-y-6">
          <DoctorPanel />
          
          <Card className="border-none bg-gradient-to-br from-blue-600 to-indigo-700 text-white shadow-xl shadow-blue-200">
            <CardContent className="p-6">
              <h4 className="text-lg font-bold mb-2">Need Support?</h4>
              <p className="text-blue-100 text-sm mb-4 leading-relaxed">
                If the queue depth exceeds capacity, contact the on-call administrator immediately.
              </p>
              <button className="w-full bg-white/20 hover:bg-white/30 backdrop-blur-md text-white font-bold py-2 rounded-xl transition-all border border-white/30 truncate">
                Contact Admin
              </button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
