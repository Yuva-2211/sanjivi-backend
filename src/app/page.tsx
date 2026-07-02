import React from "react";
import Header from "@/components/Header";
import Hero from "@/components/Hero";
import ProblemSection from "@/components/ProblemSection";
import AYUSHSection from "@/components/AYUSHSection";
import SafetyFoundation from "@/components/SafetyFoundation";
import CTABanner from "@/components/CTABanner";
import Footer from "@/components/Footer";
import ThreeParticles from "@/components/ThreeParticles";

export default function Home() {
  return (
    <div className="relative min-h-screen w-full flex flex-col overflow-hidden">
      {/* Subtle floating particle background (Three.js canvas) */}
      <ThreeParticles />

      {/* Premium Glassmorphic Header */}
      <Header />

      {/* Main Sections */}
      <main className="flex-1 w-full flex flex-col relative z-10">
        {/* Section 1: Hero Showcase */}
        <Hero />

        {/* Section 2: The Problem It Solves */}
        <ProblemSection />

        {/* Section 3: The Pillars of AYUSH Care */}
        <AYUSHSection />

        {/* Section 5: Safety is the Foundation */}
        <SafetyFoundation />

        {/* Section 6: Early Access Signup */}
        <CTABanner />
      </main>

      {/* Footer */}
      <Footer />
    </div>
  );
}
