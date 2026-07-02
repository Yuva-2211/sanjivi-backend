"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import Image from "next/image";
import { ChevronRight, Heart, ShieldAlert, Sparkles, Brain, Flower2 } from "lucide-react";

interface Treatment {
  title: string;
  category: string;
  image: string;
  description: string;
  duration: string;
  therapies: string[];
  icon: React.ReactNode;
}

export default function Treatments() {
  const [activeCard, setActiveCard] = useState<number | null>(null);

  const treatments: Treatment[] = [
    {
      title: "Stress & Anxiety Management",
      category: "Mental Wellness",
      image: "/images/yoga_meditation.png",
      description: "Reclaim mental peace through custom pranayama, Sirodhara therapy, herbal nervine tonics, and mindfulness consulting.",
      duration: "7 - 14 Days",
      therapies: ["Sirodhara Oil Drip", "Yoga Nidra Sessions", "Nervine Adaptogens"],
      icon: <Brain className="w-5 h-5 text-emerald-600" />,
    },
    {
      title: "Digestive Wellness",
      category: "Metabolism",
      image: "/images/ayurvedic_herbs.png",
      description: "Restore your digestive fire (Agni) and eliminate toxins (Ama) through tailor-made diets, herbs, and cleansing procedures.",
      duration: "10 - 21 Days",
      therapies: ["Virechana Detox", "Digestive Herbal Elixirs", "Dietary Dinacharya"],
      icon: <Flower2 className="w-5 h-5 text-emerald-600" />,
    },
    {
      title: "Immunity Boost Program",
      category: "Rejuvenation",
      image: "/images/mortar_pestle.png",
      description: "Strengthen biological defense mechanism (Ojas) using traditional immunomodulators, Kayakalpa therapies, and dietary protocols.",
      duration: "14 Days",
      therapies: ["Rasayana Formulations", "Abhyanga Massage", "Immunomodulator Herbs"],
      icon: <ShieldAlert className="w-5 h-5 text-emerald-600" />,
    },
    {
      title: "Women's Health & Care",
      category: "Hormonal Balance",
      image: "/images/doctor_consultation.png",
      description: "Address hormonal fluctuations, menstrual cycles, thyroid care, and maternal health using natural healing streams.",
      duration: "10 - 14 Days",
      therapies: ["Hormonal Balancing Herbs", "Uttar Basti Treatment", "Yoga for Pelvic Health"],
      icon: <Heart className="w-5 h-5 text-emerald-600" />,
    },
    {
      title: "Joint & Spine Care",
      category: "Pain Relief",
      image: "/images/natural_medicine.png",
      description: "Relieve chronic joint, muscle, and spinal pain by restoring lubricant humors and building muscular strength naturally.",
      duration: "14 - 28 Days",
      therapies: ["Kati Basti Warm Oil", "Anti-inflammatory Herbs", "Specific Joint Yoga"],
      icon: <Sparkles className="w-5 h-5 text-emerald-600" />,
    },
  ];

  return (
    <section
      id="treatments"
      className="relative py-24 px-4 md:px-8 lg:px-16 bg-white overflow-hidden"
    >
      <div className="w-full max-w-7xl mx-auto z-10 relative">
        
        {/* Section Header */}
        <div className="text-center max-w-2xl mx-auto mb-16">
          <span className="text-[11px] font-extrabold uppercase tracking-widest text-primary bg-emerald-50 px-4 py-2 rounded-full border border-emerald-100/40">
            Specialized Care
          </span>
          <h2 className="text-3xl md:text-5xl font-black text-brand-text mt-6 mb-4">
            Featured <span className="text-primary">AYUSH Treatments</span>
          </h2>
          <p className="text-sm text-brand-muted leading-relaxed">
            Discover targeted natural clinical therapies designed to address specific chronic disorders and restore organic health.
          </p>
        </div>

        {/* Horizontal scroll on large devices, stack on small */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 items-stretch">
          {treatments.map((treatment, idx) => {
            const isActive = activeCard === idx;

            return (
              <motion.div
                key={treatment.title}
                initial={{ opacity: 0, scale: 0.95 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true, margin: "-100px" }}
                transition={{ duration: 0.7, delay: idx * 0.08, ease: [0.22, 1, 0.36, 1] }}
                onMouseEnter={() => setActiveCard(idx)}
                onMouseLeave={() => setActiveCard(null)}
                className="relative rounded-[28px] overflow-hidden neumorphic-container bg-white border border-neutral-100 shadow-sm flex flex-col h-[520px] cursor-pointer group"
              >
                {/* Image Container with Zoom */}
                <div className="relative w-full h-[60%] overflow-hidden bg-neutral-900">
                  <div className="absolute inset-0 z-10 bg-gradient-to-b from-black/20 via-transparent to-black/60 pointer-events-none" />
                  <Image
                    src={treatment.image}
                    alt={treatment.title}
                    fill
                    className="object-cover group-hover:scale-110 transition-transform duration-700 ease-[cubic-bezier(0.22,1,0.36,1)]"
                  />
                  
                  {/* Floating Category tag */}
                  <span className="absolute top-4 left-4 z-20 px-3 py-1 rounded-full bg-white/70 backdrop-blur-md border border-white/40 text-[9px] font-bold text-primary uppercase tracking-wider">
                    {treatment.category}
                  </span>
                </div>

                {/* Normal Content (Always visible) */}
                <div className="p-5 flex flex-col justify-between flex-1 relative bg-white z-20 group-hover:translate-y-[-20px] transition-transform duration-500 ease-[cubic-bezier(0.22,1,0.36,1)]">
                  <div>
                    <div className="w-9 h-9 rounded-xl bg-emerald-50 border border-emerald-100 flex items-center justify-center mb-3">
                      {treatment.icon}
                    </div>
                    <h3 className="text-base font-bold text-brand-text leading-tight group-hover:text-primary transition-colors">
                      {treatment.title}
                    </h3>
                  </div>
                  
                  <div className="flex items-center justify-between text-[11px] font-semibold text-brand-muted mt-4 border-t border-neutral-100 pt-3">
                    <span>Duration: {treatment.duration}</span>
                    <span className="flex items-center gap-0.5 text-primary">
                      <span>View details</span>
                      <ChevronRight className="w-3.5 h-3.5" />
                    </span>
                  </div>
                </div>

                {/* Slide Up Glass Overlay on Hover */}
                <motion.div
                  initial={{ y: "100%" }}
                  animate={{ y: isActive ? "0%" : "100%" }}
                  transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
                  className="absolute inset-x-0 bottom-0 h-[70%] rounded-t-[28px] border-t border-white/10 p-6 flex flex-col justify-between z-30 shadow-2xl bg-[#1b4322]/95 backdrop-blur-xl"
                >
                  <div className="flex flex-col gap-3">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-bold text-emerald-300 uppercase tracking-wider">
                        Therapy Elements
                      </span>
                      <span className="text-[10px] font-extrabold text-gold uppercase bg-[#14331a] px-2 py-0.5 rounded border border-emerald-800">
                        {treatment.duration}
                      </span>
                    </div>
                    
                    <p className="text-[11px] text-white leading-relaxed font-medium">
                      {treatment.description}
                    </p>

                    <div className="h-px bg-white/10 my-1" />

                    <div className="flex flex-col gap-1.5">
                      {treatment.therapies.map((th, thIdx) => (
                        <div key={thIdx} className="flex items-center gap-2">
                          <span className="w-1.5 h-1.5 rounded-full bg-gold" />
                          <span className="text-[10px] text-neutral-200 font-bold">
                            {th}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      const target = document.querySelector("#contact");
                      if (target) target.scrollIntoView({ behavior: "smooth" });
                    }}
                    className="w-full py-2 bg-gold hover:bg-[#ffb74d] text-brand-text text-[11px] font-bold rounded-xl transition-all text-center flex items-center justify-center gap-1.5 shadow-sm"
                  >
                    <span>Request Therapy</span>
                    <ChevronRight className="w-3.5 h-3.5 text-brand-text" />
                  </button>
                </motion.div>
              </motion.div>
            );
          })}
        </div>

      </div>
    </section>
  );
}
