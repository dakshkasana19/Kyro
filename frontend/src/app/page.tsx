import Link from 'next/link';
import { buttonVariants } from '@/components/ui/button';

export default function Home() {
  return (
    <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center text-white relative overflow-hidden">
      <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 mix-blend-overlay"></div>
      <div className="absolute -top-40 -right-40 w-96 h-96 bg-purple-600 rounded-full mix-blend-multiply filter blur-[128px] opacity-50 animate-blob"></div>
      <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-blue-600 rounded-full mix-blend-multiply filter blur-[128px] opacity-50 animate-blob animation-delay-2000"></div>
      
      <main className="z-10 text-center space-y-8 flex flex-col items-center max-w-2xl px-4">
        <h1 className="text-6xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-blue-500 drop-shadow-sm">
          Next.js + Tailwind + Shadcn
        </h1>
        <p className="text-xl text-slate-300 font-light max-w-lg">
          Your modern web application environment is fully configured and ready for development.
        </p>
        
        <div className="flex gap-4 pt-4">
          <Link href="/about" className={buttonVariants({ size: "lg", className: "bg-white text-slate-950 hover:bg-slate-200 shadow-lg shadow-white/10 transition-all font-medium" })}>
            Test Routing (About Page)
          </Link>
          <a href="https://ui.shadcn.com" target="_blank" rel="noopener noreferrer" className={buttonVariants({ variant: "outline", size: "lg", className: "border-slate-700 hover:bg-slate-800 text-white transition-all bg-transparent font-medium" })}>
            View Shadcn Docs
          </a>
        </div>
      </main>
    </div>
  );
}
