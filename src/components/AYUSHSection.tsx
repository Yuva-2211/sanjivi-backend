"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { Leaf, Sun, Beaker, Shield, Activity, Star } from "lucide-react";

interface AyushCard {
  id: string;
  title: string;
  letter: string;
  description: string;
  icon: React.ReactNode;
  bgGradient: string;
  hoverEffect: "leaves" | "glow" | "gold-particles" | "energy-ring" | "medicine-particles";
  benefits: string[];
}

export default function AYUSHSection() {
  const [hoveredCard, setHoveredCard] = useState<string | null>(null);

  const cards: AyushCard[] = [
    {
      id: "ayurveda",
      title: "Ayurveda",
      letter: "A",
      description: "The ancient science of life focusing on diet, herbal remedies, and lifestyle practices to balance your unique body constitution (Doshas).",
      icon: <Leaf className="w-8 h-8 text-emerald-600" />,
      bgGradient: "from-emerald-500/20 via-emerald-100/10 to-transparent",
      hoverEffect: "leaves",
      benefits: ["Panchakarma Detox", "Dosha Balancing", "Herbal Therapy"],
    },
    {
      id: "yoga",
      title: "Yoga & Naturopathy",
      letter: "Y",
      description: "Harmonizing mind and body through physical postures (asanas), breathing exercises (pranayama), and natural drugless therapies.",
      icon: <Sun className="w-8 h-8 text-amber-500" />,
      bgGradient: "from-amber-500/20 via-amber-100/10 to-transparent",
      hoverEffect: "glow",
      benefits: ["Mindfulness Meditation", "Stress Relief Asanas", "Hydrotherapy"],
    },
    {
      id: "unani",
      title: "Unani",
      letter: "U",
      description: "A traditional system based on the balance of four humors (blood, phlegm, yellow bile, black bile) to restore natural immunity and health.",
      icon: <Beaker className="w-8 h-8 text-yellow-600" />,
      bgGradient: "from-yellow-600/20 via-yellow-100/10 to-transparent",
      hoverEffect: "gold-particles",
      benefits: ["Humor Balancing", "Kushta Formulations", "Regimental Therapy"],
    },
    {
      id: "siddha",
      title: "Siddha",
      letter: "S",
      description: "One of the oldest traditional medicine systems focusing on mineral-herbal preparations and rejuvenation of the inner life force.",
      icon: <Shield className="w-8 h-8 text-teal-600" />,
      bgGradient: "from-teal-500/20 via-teal-100/10 to-transparent",
      hoverEffect: "energy-ring",
      benefits: ["Mineral Therapeutics", "Kayakalpa Rejuvenation", "Pulse Diagnosis"],
    },
    {
      id: "homeopathy",
      title: "Homeopathy",
      letter: "H",
      description: "Gentle healing system using highly diluted natural substances to trigger the body's self-healing mechanisms and build natural defense.",
      icon: <Activity className="w-8 h-8 text-indigo-600" />,
      bgGradient: "from-indigo-500/20 via-indigo-100/10 to-transparent",
      hoverEffect: "medicine-particles",
      benefits: ["Constitutional Care", "Chronic Disorder Support", "Side-effect-free remedies"],
    },
  ];

  return (
    <section
      id="ayush"
      className="relative py-24 px-4 md:px-8 lg:px-16 bg-white overflow-hidden"
    >
      {/* Decorative background elements */}
      <div className="absolute top-0 right-0 w-80 h-80 rounded-full bg-emerald-50/50 blur-[80px] pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-96 h-96 rounded-full bg-amber-50/40 blur-[100px] pointer-events-none" />

      <div className="w-full max-w-7xl mx-auto z-10 relative">
        
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-20">
          <span className="text-[11px] font-extrabold uppercase tracking-widest text-primary bg-emerald-50 px-4 py-2 rounded-full border border-emerald-100/40">
            Traditional Wisdom
          </span>
          <h2 className="text-3xl md:text-5xl font-black text-brand-text tracking-tight mt-6 mb-4">
            The Pillars of <span className="text-primary">AYUSH</span> Care
          </h2>
          <p className="text-sm md:text-base text-brand-muted leading-relaxed">
            Our expert clinics combine the five streams of ancient healthcare, bringing you side-effect-free treatments for lifelong rejuvenation.
          </p>
        </div>

        {/* 5 Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 xl:gap-8 items-stretch">
          {cards.map((card, idx) => {
            const isHovered = hoveredCard === card.id;

            return (
              <motion.div
                key={card.id}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-100px" }}
                transition={{ duration: 0.6, delay: idx * 0.1, ease: [0.22, 1, 0.36, 1] }}
                onMouseEnter={() => setHoveredCard(card.id)}
                onMouseLeave={() => setHoveredCard(null)}
                className="relative rounded-[28px] overflow-hidden neumorphic-container bg-white border border-neutral-100/70 p-6 flex flex-col justify-between transition-all duration-500 ease-[cubic-bezier(0.22,1,0.36,1)] hover:scale-[1.04] hover:shadow-xl group min-h-[460px] cursor-pointer"
              >
                
                {/* Background Glow Overlay */}
                <div
                  className={`absolute inset-0 bg-gradient-to-b ${card.bgGradient} opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none`}
                />

                {/* Big letter in background */}
                <span className="absolute top-4 right-6 text-7xl md:text-8xl font-black text-neutral-100/40 font-sans group-hover:text-primary/5 transition-colors duration-500 select-none">
                  {card.letter}
                </span>

                {/* Card Top */}
                <div className="relative z-10 flex flex-col items-start gap-4">
                  {/* Icon with glass shape */}
                  <div className="w-16 h-16 rounded-2xl bg-brand-bg flex items-center justify-center border border-neutral-200/50 shadow-sm group-hover:bg-white group-hover:border-primary/20 transition-all duration-500">
                    {card.icon}
                  </div>

                  <h3 className="text-xl font-bold text-brand-text mt-4 group-hover:text-primary transition-colors">
                    {card.title}
                  </h3>
                  
                  <p className="text-xs text-brand-muted leading-relaxed mt-2">
                    {card.description}
                  </p>
                </div>

                {/* Hover Particles Simulation Overlay */}
                {isHovered && (
                  <div className="absolute inset-0 pointer-events-none overflow-hidden z-0">
                    {/* Ayurveda Hover: leaf particles */}
                    {card.hoverEffect === "leaves" && (
                      <>
                        <div className="absolute top-1/2 left-10 w-2.5 h-2 bg-emerald-500/30 rounded-full animate-float-slow" />
                        <div className="absolute bottom-20 right-10 w-3 h-2 bg-emerald-400/40 rounded-full animate-float-reverse" />
                        <div className="absolute top-12 left-1/3 w-2 h-1.5 bg-emerald-300/30 rounded-full animate-float-slow" />
                      </>
                    )}

                    {/* Yoga Hover: slow glow pulse rings */}
                    {card.hoverEffect === "glow" && (
                      <div className="absolute inset-0 flex items-center justify-center">
                        <div className="w-40 h-40 rounded-full border border-amber-300/20 animate-pulse-slow scale-110" />
                        <div className="w-28 h-28 rounded-full border border-amber-300/10 animate-pulse-slow" />
                      </div>
                    )}

                    {/* Unani Hover: golden particle dots */}
                    {card.hoverEffect === "gold-particles" && (
                      <>
                        <div className="absolute bottom-12 left-1/4 w-1.5 h-1.5 bg-gold/50 rounded-full animate-float-slow" />
                        <div className="absolute top-1/3 right-1/4 w-2 h-2 bg-yellow-400/40 rounded-full animate-float-reverse" />
                        <div className="absolute bottom-24 right-12 w-1 h-1 bg-amber-500/60 rounded-full animate-float-slow" />
                      </>
                    )}

                    {/* Siddha Hover: spinning ring of light */}
                    {card.hoverEffect === "energy-ring" && (
                      <div className="absolute inset-0 flex items-center justify-center opacity-60">
                        <div className="w-32 h-32 rounded-full border border-dashed border-teal-500/30 animate-spin" style={{ animationDuration: "12s" }} />
                        <div className="w-24 h-24 rounded-full border border-teal-500/20 animate-spin" style={{ animationDuration: "8s", animationDirection: "reverse" }} />
                      </div>
                    )}

                    {/* Homeopathy Hover: small medical spheres */}
                    {card.hoverEffect === "medicine-particles" && (
                      <>
                        <div className="absolute top-1/4 left-1/3 w-2 h-2 bg-indigo-300/40 rounded-full animate-float-slow" />
                        <div className="absolute bottom-16 right-1/4 w-1.5 h-1.5 bg-indigo-400/30 rounded-full animate-float-reverse" />
                        <div className="absolute bottom-32 left-12 w-2.5 h-2.5 bg-indigo-200/50 rounded-full animate-float-slow" />
                      </>
                    )}
                  </div>
                )}

                {/* Card Bottom: list benefits */}
                <div className="relative z-10 mt-8 pt-4 border-t border-neutral-100">
                  <div className="flex flex-col gap-2">
                    {card.benefits.map((benefit, bIdx) => (
                      <div key={bIdx} className="flex items-center gap-2">
                        <Star className="w-3 h-3 text-gold shrink-0 fill-gold/20" />
                        <span className="text-[10px] font-semibold text-brand-muted">
                          {benefit}
                        </span>
                      </div>
                    ))}
                  </div>
                  
                  {/* Learn More slide in indicator */}
                  <div className="mt-4 flex items-center gap-1 text-[10px] font-bold text-primary opacity-0 group-hover:opacity-100 group-hover:translate-x-1 transition-all duration-300">
                    <span>Treatments</span>
                    <span>→</span>
                  </div>
                </div>

              </motion.div>
            );
          })}
        </div>

      </div>
    </section>
  );
}
