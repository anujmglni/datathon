import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Karnataka Police — Crime Intelligence Platform",
  description: "Conversational AI for crime analytics, criminal network analysis, and case intelligence powered by Groq Llama 3.3 70B.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="bg-slate-950 text-slate-100 antialiased selection:bg-blue-500 selection:text-white">
        {children}
      </body>
    </html>
  );
}
