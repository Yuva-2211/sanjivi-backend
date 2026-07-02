import type { Metadata } from "next";
import { Roboto } from "next/font/google";
import "./globals.css";
import LenisScroll from "@/components/LenisScroll";

const roboto = Roboto({
  weight: ["300", "400", "500", "700", "900"],
  subsets: ["latin"],
  variable: "--font-roboto",
});

export const metadata: Metadata = {
  title: "Sanjivi Ayush Healthcare - Healing Naturally, Living Better",
  description: "Experience the wisdom of Ayurveda, Yoga, Siddha, Unani and Homeopathy through modern premium healthcare solutions. 100% natural, side-effect-free, and certified doctor consultations.",
  keywords: ["Sanjivi Ayush", "Ayurveda", "Yoga", "Siddha", "Unani", "Homeopathy", "Natural healing", "Holistic healthcare", "India doctor consult"],
  authors: [{ name: "Sanjivi Ayush Healthcare Team" }],
  openGraph: {
    title: "Sanjivi Ayush Healthcare - Healing Naturally, Living Better",
    description: "Experience the wisdom of Ayurveda, Yoga, Siddha, Unani and Homeopathy through modern premium healthcare solutions.",
    type: "website",
    locale: "en_IN",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${roboto.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col bg-brand-bg text-brand-text">
        <LenisScroll>
          {children}
        </LenisScroll>
      </body>
    </html>
  );
}
