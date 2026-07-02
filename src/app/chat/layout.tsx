import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Sanjivi AI — Chat",
  description: "Multi-agent AYUSH health intelligence chat interface.",
};

export default function ChatLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="h-screen w-screen overflow-hidden">
      {children}
    </div>
  );
}
