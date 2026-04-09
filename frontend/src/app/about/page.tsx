import Link from 'next/link';
import { buttonVariants } from '@/components/ui/button';

export default function About() {
  return (
    <div className="min-h-screen bg-slate-900 flex flex-col items-center justify-center text-white relative">
      <div className="z-10 text-center space-y-6 max-w-xl px-4 p-8 bg-slate-800/50 rounded-2xl border border-slate-700 shadow-2xl backdrop-blur-sm">
        <h1 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-emerald-400 to-cyan-500">
          Routing Configured!
        </h1>
        <p className="text-lg text-slate-300">
          This page demonstrates that the Next.js App Router is working perfectly. You navigated here from the home page.
        </p>
        
        <div className="pt-6">
          <Link href="/" className={buttonVariants({ variant: "default", className: "bg-gradient-to-r from-emerald-500 to-cyan-600 hover:from-emerald-400 hover:to-cyan-500 text-white border-0 shadow-lg shadow-cyan-900/50 font-medium" })}>
            ← Back to Home
          </Link>
        </div>
      </div>
    </div>
  );
}
