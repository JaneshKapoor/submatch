import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SubMatch — Audio-Subtitle Mismatch Detector",
  description: "Automatically detect mismatches between spoken audio and on-screen subtitles. Supports Hindi, Kannada, and 8 other Indian language scripts.",
  keywords: ["subtitle", "mismatch", "audio", "hindi", "kannada", "whisper", "OCR", "PlanetRead"],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-gray-950 text-slate-100 antialiased min-h-screen">
        {children}
      </body>
    </html>
  );
}
