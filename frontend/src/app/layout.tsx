import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import { ThemeProvider } from "@/components/ThemeProvider";
import { Header } from "@/components/Header";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "RecSys Lab — Recommendation Systems Research Harness",
  description:
    "Side-by-side comparison and offline evaluation of six recommendation algorithms across MovieLens-100K and Microsoft MIND-small.",
};

const themeScript = `(function(){try{var t=localStorage.getItem('theme');var d=t?t==='dark':true;if(d){document.documentElement.classList.add('dark');}else{document.documentElement.classList.remove('dark');}document.documentElement.style.colorScheme=d?'dark':'light';}catch(e){document.documentElement.classList.add('dark');}})();`;

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable}`} suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body className="min-h-screen bg-bg text-fg antialiased">
        <ThemeProvider>
          <Header />
          <main className="mx-auto w-full max-w-[1400px] px-6 pb-24 pt-6 lg:px-10">
            {children}
          </main>
        </ThemeProvider>
      </body>
    </html>
  );
}
