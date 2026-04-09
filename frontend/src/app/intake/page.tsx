import { IntakeForm } from "@/components/patient-intake/IntakeForm";

export default function IntakePage() {
  return (
    <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center py-12 px-4 relative overflow-hidden">
      {/* Background decorations */}
      <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 mix-blend-overlay pointer-events-none"></div>
      <div className="absolute -top-40 -left-40 w-96 h-96 bg-purple-600 rounded-full mix-blend-multiply filter blur-[128px] opacity-20 pointer-events-none"></div>
      <div className="absolute bottom-0 right-0 w-96 h-96 bg-blue-600 rounded-full mix-blend-multiply filter blur-[128px] opacity-20 pointer-events-none"></div>
      
      <div className="w-full z-10">
        <IntakeForm />
      </div>
    </div>
  );
}
