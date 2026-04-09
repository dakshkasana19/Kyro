import { IntakeForm } from "@/components/patient-intake/IntakeForm";

export default function IntakePage() {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center py-12 px-4 relative overflow-hidden">
      {/* Background decorations */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#e0e7ff_1px,transparent_1px),linear-gradient(to_bottom,#e0e7ff_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] opacity-20"></div>
      <div className="absolute top-0 left-0 w-96 h-96 bg-blue-400 rounded-full mix-blend-multiply filter blur-[128px] opacity-10 pointer-events-none animation-delay-2000"></div>
      <div className="absolute bottom-0 right-0 w-96 h-96 bg-pink-400 rounded-full mix-blend-multiply filter blur-[128px] opacity-10 pointer-events-none"></div>
      
      <div className="w-full z-10">
        <IntakeForm />
      </div>
    </div>
  );
}
