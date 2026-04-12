import type { Metadata } from "next";
import { Geist } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const geist = Geist({ variable: "--font-geist", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Poomsae Wiki — WT Taekwondo Forms Reference",
  description:
    "Interactive reference for all 17 official WT/KKW poomsae forms. Click any move to see the exact video segment with technique details.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${geist.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col bg-gray-50 text-gray-900">
        <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
          <nav className="max-w-7xl mx-auto px-4 h-14 flex items-center gap-6">
            <Link href="/" className="font-bold text-lg tracking-tight">
              Poomsae Wiki
            </Link>
            <Link
              href="/"
              className="text-sm text-gray-600 hover:text-gray-900"
            >
              Forms
            </Link>
            <Link
              href="/techniques"
              className="text-sm text-gray-600 hover:text-gray-900"
            >
              Techniques
            </Link>
          </nav>
        </header>
        <main className="flex-1">{children}</main>
        <footer className="border-t border-gray-200 py-6 text-center text-xs text-gray-400">
          Sources:{" "}
          <a
            href="https://www.youtube.com/playlist?list=PLSFr5pEwo7gSwvfg4bjxoF3liyfJkCLAj"
            target="_blank"
            rel="noopener noreferrer"
            className="underline hover:text-gray-600"
          >
            Kukkiwon / World Taekwondo Academy
          </a>
          {" "}&middot;{" "}
          <a
            href="https://www.worldtaekwondo.org/att_file/documents/Poomsae_Competition_Rules_and_Interpretation_(In_force_as_of_September_30_2024).pdf"
            target="_blank"
            rel="noopener noreferrer"
            className="underline hover:text-gray-600"
          >
            WT Poomsae Competition Rules (Sept 2024)
          </a>
        </footer>
      </body>
    </html>
  );
}
