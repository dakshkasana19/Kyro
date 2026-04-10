import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Toaster } from 'sonner';
import { SSEListener } from '@/components/auth/SSEListener';
import { createClient } from '@/utils/supabase/server';
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Kyro — Intelligent Clinical Triage",
  description: "Next-generation healthcare triage and staff management.",
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()
  const hospitalId = user?.user_metadata?.hospital_id || null

  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
          {children}
          <SSEListener hospitalId={hospitalId} />
          <Toaster position="top-right" richColors theme="light" />
      </body>
    </html>
  );
}
