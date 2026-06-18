import type { Metadata } from "next";
import { Inter, Space_Grotesk, JetBrains_Mono } from "next/font/google";
import Sidebar from "../components/Sidebar";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-space-grotesk",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Setu — Unified Identity Trust SOC Dashboard",
  description: "Bank of Baroda 2026 Cybersecurity Identity Graph Analyzer & Insider Threat Prevention Engine",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${inter.variable} ${spaceGrotesk.variable} ${jetbrainsMono.variable}`}>
      <body className="bg-soc-bg text-soc-textPrimary font-sans antialiased min-h-screen">
        <div className="flex">
          {/* Static SOC Navigation Sidebar */}
          <Sidebar />
          
          {/* Main Content Pane */}
          <main className="flex-1 min-h-screen pl-16">
            <div className="cyber-grid min-h-screen w-full">
              {children}
            </div>
          </main>
        </div>
      </body>
    </html>
  );
}
