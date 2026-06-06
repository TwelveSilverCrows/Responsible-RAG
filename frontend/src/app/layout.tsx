import type { Metadata } from "next";
import { DM_Sans, Fraunces } from "next/font/google";
import { Geist_Mono } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/components/ui/sonner";
import { Providers } from "@/components/Providers";
import { ErrorBoundary } from "@/components/ErrorBoundary";

const dmSans = DM_Sans({
  variable: "--font-dm-sans",
  subsets: ["latin"],
  display: "swap",
});

const fraunces = Fraunces({
  variable: "--font-fraunces",
  subsets: ["latin"],
  display: "swap",
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Responsible AI RAG",
  description: "A responsible AI communication system with privacy-first design, adaptive responses, and transparent consent.",
  keywords: ["RAG", "AI", "Accessibility", "Privacy", "Consent", "Research"],
  authors: [{ name: "Responsible AI Team" }],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${dmSans.variable} ${fraunces.variable} ${geistMono.variable} font-sans antialiased bg-background text-foreground`}
        suppressHydrationWarning
      >
        <ErrorBoundary>
          <Providers>
            {children}
            <Toaster richColors position="bottom-right" />
          </Providers>
        </ErrorBoundary>
      </body>
    </html>
  );
}
