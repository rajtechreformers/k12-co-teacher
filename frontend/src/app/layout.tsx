import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
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
  title: "K12-CoTeacher",
  description: "Assistant for tailored lesson plans",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-[#f9f9f9] text-[#1e1e1e]`}
      >
        {/* Top Navigation Bar */}
        <header className="bg-white shadow sticky top-0 z-50">
          <div className="max-w-screen-xl mx-auto px-6 py-4 flex items-center justify-between">
            <h1 className="text-xl font-bold tracking-tight text-blue-600">
              K12-CoTeacher
            </h1>
            <nav className="space-x-6 text-sm font-medium"></nav>
          </div>
        </header>

        {/* Main content area */}
        <main className="max-w-screen-xl mx-auto px-6 py-10">{children}</main>
      </body>
    </html>
  );
}
