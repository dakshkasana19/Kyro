'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { LayoutDashboard, Users, ClipboardList, Settings, LogOut, Activity, History } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { logout } from '@/app/auth/actions'
import { createClient } from '@/utils/supabase/client'
import { useEffect, useState } from 'react'
import { Stethoscope } from 'lucide-react'

const navItems = [
  { icon: LayoutDashboard, label: 'Overview', href: '/dashboard' },
  { icon: ClipboardList, label: 'Triage Queue', href: '/dashboard/queue' },
  { icon: Users, label: 'Doctors', href: '/dashboard/doctors' },
  { icon: Settings, label: 'Settings', href: '/dashboard/settings' },
]

export function Sidebar() {
  const pathname = usePathname()
  const [role, setRole] = useState<string | null>(null)

  useEffect(() => {
    const checkUser = async () => {
      const supabase = createClient()
      const { data: { user } } = await supabase.auth.getUser()
      setRole(user?.user_metadata?.role || null)
    }
    checkUser()
  }, [])

  const dynamicNavItems = [
    ...navItems,
    ...(role === 'Doctor' ? [{ icon: Stethoscope, label: 'My Patients', href: '/doctor/dashboard' }] : []),
    ...(role === 'Admin' || role === 'Doctor' ? [{ icon: History, label: 'Audit Trail', href: '/dashboard/audit' }] : [])
  ]

  return (
    <div className="w-20 lg:w-64 h-screen bg-white border-r border-slate-100 flex flex-col items-center lg:items-stretch py-8 shadow-[1px_0_10px_rgba(0,0,0,0.02)] fixed left-0 top-0 z-50">
      <div className="px-4 mb-10 flex items-center gap-3">
        <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-200">
          <Activity className="text-white w-6 h-6" />
        </div>
        <span className="hidden lg:block text-xl font-bold text-slate-900 tracking-tight">
          Kyro<span className="text-blue-600">Health</span>
        </span>
        <div className="ml-auto hidden lg:flex items-center gap-2 px-2 py-1 bg-emerald-50 rounded-full border border-emerald-100">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-[10px] font-bold text-emerald-600 uppercase tracking-tight">Live</span>
        </div>
      </div>

      <nav className="flex-1 px-4 space-y-2 w-full">
        {dynamicNavItems.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link key={item.href} href={item.href}>
              <div className={cn(
                "group flex items-center gap-3 px-3 py-3 rounded-xl transition-all duration-200 cursor-pointer",
                isActive 
                  ? "bg-blue-50 text-blue-600 shadow-sm" 
                  : "text-slate-400 hover:bg-slate-50 hover:text-slate-600"
              )}>
                <item.icon className={cn(
                  "w-5 h-5 transition-transform group-hover:scale-110",
                  isActive ? "text-blue-600" : "text-slate-400 group-hover:text-slate-600"
                )} />
                <span className={cn(
                  "hidden lg:block font-medium",
                  isActive ? "text-blue-700" : "text-slate-500"
                )}>
                  {item.label}
                </span>
                {isActive && (
                  <div className="ml-auto w-1.5 h-1.5 rounded-full bg-pink-500 shadow-[0_0_8px_rgba(236,72,153,0.5)] animate-pulse hidden lg:block" />
                )}
              </div>
            </Link>
          )
        })}
      </nav>

      <div className="px-4 mt-auto w-full">
        <form action={logout}>
          <Button variant="ghost" className="w-full flex items-center justify-center lg:justify-start gap-3 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-xl py-6 transition-all">
            <LogOut className="w-5 h-5" />
            <span className="hidden lg:block font-medium">Logout</span>
          </Button>
        </form>
      </div>
    </div>
  )
}
