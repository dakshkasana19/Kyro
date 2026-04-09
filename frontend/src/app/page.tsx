import Link from 'next/link';
import { buttonVariants } from '@/components/ui/button';
import { createClient } from '@/utils/supabase/server';
import { logout } from './auth/actions';

export default async function Home() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center text-slate-900 relative overflow-hidden">
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#e0e7ff_1px,transparent_1px),linear-gradient(to_bottom,#e0e7ff_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] opacity-20"></div>
      <div className="absolute top-0 left-0 w-96 h-96 bg-blue-400 rounded-full mix-blend-multiply filter blur-[128px] opacity-10 animate-blob"></div>
      <div className="absolute bottom-0 right-0 w-96 h-96 bg-pink-400 rounded-full mix-blend-multiply filter blur-[128px] opacity-10 animate-blob animation-delay-4000"></div>
      
      <main className="z-10 text-center space-y-8 flex flex-col items-center max-w-2xl px-4">
        <h1 className="text-6xl font-black tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600">
          Kyro<span className="text-slate-900 font-light">Health</span>
        </h1>
        <p className="text-xl text-slate-500 font-medium max-w-lg">
          Intelligent AI Triage & Patient Management System
        </p>
        
        <div className="flex flex-col gap-6 items-center">
          <div className="flex flex-wrap gap-4 pt-4 justify-center">
            {user?.user_metadata?.role === 'Doctor' && (
              <Link href="/doctor/dashboard" className={buttonVariants({ size: "lg", className: "bg-pink-600 text-white hover:bg-pink-700 shadow-lg shadow-pink-500/20 transition-all font-black" })}>
                Open Doctor Portal
              </Link>
            )}
            <Link href="/dashboard" className={buttonVariants({ size: "lg", className: "bg-blue-600 text-white hover:bg-blue-700 shadow-lg shadow-blue-500/20 transition-all font-bold" })}>
              Open Admin Dashboard
            </Link>
            <Link href="/intake" className={buttonVariants({ variant: "outline", size: "lg", className: "border-slate-200 hover:bg-slate-50 text-slate-900 transition-all bg-white font-medium shadow-sm" })}>
              New Patient Intake
            </Link>
          </div>
          
          {user && (
            <div className="flex flex-col items-center gap-4 animate-in fade-in slide-in-from-top-4 duration-700 delay-300">
              <p className="text-slate-400 text-sm">
                Signed in as <span className="text-purple-400 font-medium">{user.email}</span>
              </p>
              <form action={logout}>
                <button className="text-xs text-slate-500 hover:text-red-400 transition-colors uppercase tracking-widest font-bold">
                  Logout
                </button>
              </form>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
