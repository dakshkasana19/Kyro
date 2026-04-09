import { Sidebar } from '@/components/dashboard/Sidebar'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen bg-slate-50/50 flex transition-colors duration-500">
      <Sidebar />
      <main className="flex-1 lg:ml-64 p-4 lg:p-8 overflow-auto">
        <div className="max-w-[1400px] mx-auto">
          {children}
        </div>
      </main>
    </div>
  )
}
