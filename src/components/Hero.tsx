"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowRight, Calendar, Leaf, Sparkles, CheckCircle2, Heart } from "lucide-react";
import Image from "next/image";
import { useRouter } from "next/navigation";

// Scene definitions
const scenes = [
  {
    id: 1,
    title: "Ayurvedic Herbs",
    image: "/images/ayurvedic_herbs.png",
    description: "Nurturing balance through authentic organic herbs.",
    badge: "100% Organic",
    overlayEffect: "leaves",
  },
  {
    id: 2,
    title: "Mortar and Pestle",
    image: "/images/mortar_pestle.png",
    description: "Precision grinding of fresh leaves and medicinal plants.",
    badge: "Traditional Wisdom",
    overlayEffect: "smoke",
  },
  {
    id: 3,
    title: "Yoga Meditation",
    image: "/images/yoga_meditation.png",
    description: "Aligning mind, body and breath with nature.",
    badge: "Holistic Health",
    overlayEffect: "glow",
  },
  {
    id: 4,
    title: "Doctor Consultation",
    image: "/images/doctor_consultation.png",
    description: "Expert guidance from our certified AYUSH practitioners.",
    badge: "Trusted Experts",
    overlayEffect: "cards",
  },
  {
    id: 5,
    title: "Natural Medicine Preparation",
    image: "/images/natural_medicine.png",
    description: "Carefully extracted essences for targeted natural healing.",
    badge: "Certified Standards",
    overlayEffect: "droplets",
  },
];

export default function Hero() {
  const router = useRouter();
  const [currentScene, setCurrentScene] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentScene((prev) => (prev + 1) % scenes.length);
    }, 6000); // 6 seconds per scene
    return () => clearInterval(timer);
  }, []);

  const handleScrollTo = (id: string) => {
    if (id === "#contact") {
      router.push("/chat");
      return;
    }
    const target = document.querySelector(id);
    if (target) {
      target.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <section
      id="home"
      className="relative min-h-screen w-full flex items-center justify-center overflow-hidden bg-brand-bg pt-20 px-4 md:px-8 lg:px-16"
    >
      {/* Decorative Blur Backgrounds */}
      <div className="absolute top-1/4 left-10 w-96 h-96 rounded-full bg-emerald-100/40 blur-[120px] pointer-events-none animate-pulse-slow" />
      <div className="absolute bottom-10 right-10 w-80 h-80 rounded-full bg-amber-100/30 blur-[100px] pointer-events-none" />

      {/* Main Grid Layout */}
      <div className="w-full max-w-7xl grid grid-cols-1 lg:grid-cols-12 gap-12 items-center z-10 py-12">
        {/* Left Side: Headline and CTAs */}
        <div className="lg:col-span-6 flex flex-col items-start text-left relative">
          {/* Intro Tiny Badge */}
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-50 border border-emerald-100/50 mb-6"
          >
            <Sparkles className="w-4 h-4 text-primary animate-pulse-slow" />
            <span className="text-[11px] font-bold text-primary tracking-widest uppercase">
              Sanjivi AI • Coordinated Health Intelligence
            </span>
          </motion.div>

          {/* Hero Headline */}
          <motion.h1
            initial={{ opacity: 0, y: 25 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1, delay: 0.1, ease: [0.22, 1, 0.36, 1] }}
            className="text-4xl sm:text-5xl md:text-6xl font-black text-brand-text leading-[1.1] tracking-tight text-balance mb-6 font-serif"
          >
            Five ancient systems.
            <span className="block text-primary">One safe answer.</span>
          </motion.h1>

          {/* Subheadline */}
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1, delay: 0.2, ease: [0.22, 1, 0.36, 1] }}
            className="text-base sm:text-lg text-brand-muted leading-relaxed max-w-xl mb-8"
          >
            Sanjivi AI brings the synchronized wisdom of Ayurveda, Yoga, Siddha, Unani, and Homeopathy into a single conversational interface. Guided by automated safety protocols, we deliver clear, unified, and personalized wellness answers.
          </motion.p>

          {/* CTA Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1, delay: 0.3, ease: [0.22, 1, 0.36, 1] }}
            className="flex flex-col gap-4 w-full"
          >
            <button
              onClick={() => handleScrollTo("#contact")}
              className="w-full sm:w-auto flex items-center justify-center gap-3 px-8 py-4 bg-primary hover:bg-[#1b5e20] text-white font-bold rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-[1.03] active:scale-[0.98] group cursor-pointer"
            >
              <Calendar className="w-5 h-5 text-emerald-300 group-hover:scale-110 transition-transform" />
              <span>Start a Conversation</span>
              <ArrowRight className="w-4 h-4 ml-1 opacity-60 group-hover:translate-x-1 transition-transform" />
            </button>
            <p className="text-[11px] text-brand-muted font-medium max-w-md">
              Free during early access. No card needed. Founding member rates locked for life when pricing launches.
            </p>
          </motion.div>

          {/* Floating badge for mobile */}
          <div className="flex xl:hidden flex-wrap gap-2 mt-8">
            <span className="text-[10px] font-bold bg-white/70 border border-neutral-200 text-primary px-3 py-1.5 rounded-full">
              🌿 5 Systems Coordinated
            </span>
            <span className="text-[10px] font-bold bg-white/70 border border-neutral-200 text-gold px-3 py-1.5 rounded-full">
              🛡️ Emergency Screening
            </span>
            <span className="text-[10px] font-bold bg-white/70 border border-neutral-200 text-brand-muted px-3 py-1.5 rounded-full">
              ✨ Free Early Access
            </span>
          </div>
        </div>

        {/* Right Side: Cinematic Slideshow Showcase */}
        <div className="lg:col-span-6 flex justify-center w-full relative">
          
          {/* Neumorphic Shadow Frame container */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 1.2, ease: [0.22, 1, 0.36, 1] }}
            className="w-full aspect-[4/3] max-w-xl rounded-[28px] overflow-hidden neumorphic-container bg-white p-3 relative border border-white/50"
          >
            {/* The Image Carousel */}
            <div className="relative w-full h-full rounded-[20px] overflow-hidden bg-emerald-950">
              
              <AnimatePresence mode="wait">
                <motion.div
                  key={currentScene}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 1.2, ease: [0.22, 1, 0.36, 1] }}
                  className="absolute inset-0 w-full h-full"
                >
                  {/* Ken Burns zooming effect */}
                  <motion.div
                    initial={{ scale: 1.05 }}
                    animate={{ scale: 1.15 }}
                    transition={{ duration: 7, ease: "linear" }}
                    className="absolute inset-0 w-full h-full"
                  >
                    <Image
                      src={scenes[currentScene].image}
                      alt={scenes[currentScene].title}
                      fill
                      priority
                      className="object-cover brightness-[0.85] contrast-[1.05]"
                    />
                  </motion.div>

                  {/* Gradient Overlay for Cinematic lighting */}
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-black/30 pointer-events-none" />

                  {/* Overlay Animations specific to each scene */}
                  {scenes[currentScene].overlayEffect === "leaves" && (
                    <div className="absolute inset-0 pointer-events-none overflow-hidden z-10">
                      {/* Leaf particle overlay */}
                      <div className="absolute top-10 left-1/4 w-3 h-3 bg-emerald-400/30 rounded-full blur-[1px] animate-float-slow" />
                      <div className="absolute top-20 right-1/4 w-4 h-4 bg-emerald-500/20 rounded-full blur-[2px] animate-float-reverse" />
                      <div className="absolute bottom-20 left-12 w-2 h-2 bg-emerald-300/40 rounded-full animate-float-slow" />
                      {/* Diagonal light ray glow */}
                      <div className="absolute inset-0 bg-gradient-to-br from-white/10 via-transparent to-transparent rotate-12 origin-top-left scale-150 blur-md mix-blend-overlay" />
                    </div>
                  )}

                  {scenes[currentScene].overlayEffect === "smoke" && (
                    <div className="absolute inset-0 pointer-events-none overflow-hidden z-10 flex items-end justify-center">
                      {/* Soft steam/smoke simulation */}
                      <div className="w-[80%] h-32 bg-radial from-white/10 to-transparent blur-xl translate-y-12 animate-pulse-slow mix-blend-screen" />
                    </div>
                  )}

                  {scenes[currentScene].overlayEffect === "glow" && (
                    <div className="absolute inset-0 pointer-events-none overflow-hidden z-10 flex items-center justify-center">
                      {/* Pulse glow representing energy/zen */}
                      <div className="w-48 h-48 rounded-full border border-emerald-300/30 animate-pulse-slow scale-110" />
                      <div className="absolute w-36 h-36 rounded-full border border-gold/20 animate-pulse-slow scale-100" />
                    </div>
                  )}

                  {scenes[currentScene].overlayEffect === "cards" && (
                    <div className="absolute inset-0 pointer-events-none z-10 flex items-end justify-between p-6">
                      {/* Floating UI cards */}
                      <motion.div
                        initial={{ y: 20, opacity: 0 }}
                        animate={{ y: 0, opacity: 1 }}
                        transition={{ delay: 0.4 }}
                        className="glass-panel px-4 py-2.5 rounded-2xl flex items-center gap-2.5 shadow-lg border border-white/40 scale-90 sm:scale-100 origin-bottom-left"
                      >
                        <div className="w-7 h-7 rounded-full bg-primary flex items-center justify-center text-white">
                          <CheckCircle2 className="w-4 h-4 text-white" />
                        </div>
                        <div className="flex flex-col text-left leading-none">
                          <span className="text-[10px] font-bold text-brand-text">Doctor Consulted</span>
                          <span className="text-[8px] text-brand-muted mt-0.5">Verified AYUSH Expert</span>
                        </div>
                      </motion.div>
                      
                      <motion.div
                        initial={{ y: 30, opacity: 0 }}
                        animate={{ y: 0, opacity: 1 }}
                        transition={{ delay: 0.6 }}
                        className="glass-panel px-4 py-2.5 rounded-2xl flex items-center gap-2.5 shadow-lg border border-white/40 scale-90 sm:scale-100 origin-bottom-right"
                      >
                        <Heart className="w-4 h-4 text-rose-500 animate-pulse-slow" />
                        <div className="flex flex-col text-left leading-none">
                          <span className="text-[10px] font-bold text-brand-text">Vital Health Plan</span>
                          <span className="text-[8px] text-brand-muted mt-0.5">100% Personalised</span>
                        </div>
                      </motion.div>
                    </div>
                  )}

                  {scenes[currentScene].overlayEffect === "droplets" && (
                    <div className="absolute inset-0 pointer-events-none overflow-hidden z-10">
                      {/* Golden floating bubbles */}
                      <div className="absolute bottom-10 left-1/3 w-3 h-3 bg-amber-400/40 rounded-full blur-[1px] animate-float-slow" />
                      <div className="absolute bottom-24 right-1/3 w-4.5 h-4.5 bg-yellow-300/30 rounded-full blur-[1px] animate-float-reverse" />
                    </div>
                  )}

                  {/* Scene text labels */}
                  <div className="absolute bottom-0 left-0 right-0 p-6 text-white z-25 bg-gradient-to-t from-black/80 to-transparent">
                    <div className="flex items-center gap-2.5 mb-1.5">
                      <span className="text-xs text-emerald-300 font-bold uppercase tracking-wider">
                        {scenes[currentScene].badge}
                      </span>
                    </div>
                    <h3 className="text-xl font-bold mb-1 font-sans">
                      {scenes[currentScene].title}
                    </h3>
                    <p className="text-xs text-white/80 font-normal max-w-sm">
                      {scenes[currentScene].description}
                    </p>
                  </div>
                </motion.div>
              </AnimatePresence>

              {/* Progress indicators inside the video frame */}
              <div className="absolute top-4 right-4 flex gap-1.5 z-30">
                {scenes.map((_, index) => (
                  <button
                    key={index}
                    onClick={() => setCurrentScene(index)}
                    className="group relative w-7 h-1.5 rounded-full overflow-hidden bg-white/20 transition-all hover:bg-white/40"
                  >
                    <div
                      className={`absolute top-0 left-0 h-full bg-emerald-400 rounded-full transition-all duration-300 ${
                        currentScene === index ? "w-full" : "w-0"
                      }`}
                      style={{
                        transitionDuration: currentScene === index ? "6000ms" : "300ms",
                        transitionTimingFunction: "linear",
                      }}
                    />
                  </button>
                ))}
              </div>
              
            </div>
          </motion.div>
          
        </div>
      </div>
    </section>
  );
}
