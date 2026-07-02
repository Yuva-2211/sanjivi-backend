"use client";

import React from "react";
import { motion } from "framer-motion";
import { Star, Quote } from "lucide-react";

export default function TrustSection() {
  const testimonials = [
    {
      quote: "Sanjivi AI solves a major clinical gap: it cross-references remedies across systems to verify there are no toxic herb conflicts. It is an invaluable safety guard.",
      author: "Dr. Sanjivi Kumar",
      credentials: "BAMS, MD (Ayurveda) • Senior Ayurvedic Physician",
      stars: 5,
    },
    {
      quote: "By coordinating yoga protocols alongside clinical safety checks, Sanjivi AI guides patients through balanced, drugless healing pathways that safely support their main care.",
      author: "Dr. Anjali Sharma",
      credentials: "DNYS, MS (Yoga Therapy) • Wellness Specialist",
      stars: 5,
    },
    {
      quote: "Modern clinical safety checks combined with Unani humoral evaluations mean patients can explore traditional medicines without anxiety about interactions.",
      author: "Dr. Tariq Mahmood",
      credentials: "BUMS, MD (Unani) • Clinical Consultant",
      stars: 5,
    },
  ];

  return (
    <section id="trust" className="relative py-24 px-4 md:px-8 lg:px-16 bg-white overflow-hidden border-t border-neutral-100">
      {/* Background elements */}
      <div className="absolute top-0 right-0 w-80 h-80 rounded-full bg-emerald-50/40 blur-[80px] pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-96 h-96 rounded-full bg-indigo-50/20 blur-[100px] pointer-events-none" />

      <div className="w-full max-w-7xl mx-auto z-10 relative">
        
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-20">
          <span className="text-[11px] font-extrabold uppercase tracking-widest text-primary bg-emerald-50 px-4 py-2 rounded-full border border-emerald-100/40">
            Clinical Endorsements
          </span>
          <h2 className="text-3xl md:text-5xl font-black text-brand-text tracking-tight mt-6 mb-4 font-serif">
            Trusted by <span className="text-primary">Clinical Practitioners</span>
          </h2>
          <p className="text-sm md:text-base text-brand-muted leading-relaxed">
            Sanjivi AI's safety framework and multi-agent consensus architecture are endorsed by certified practitioners across all five traditional systems.
          </p>
        </div>

        {/* Grid of quotes */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {testimonials.map((item, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-100px" }}
              transition={{ duration: 0.6, delay: idx * 0.1, ease: [0.22, 1, 0.36, 1] }}
              className="relative p-8 rounded-[28px] bg-brand-bg border border-neutral-200/50 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between gap-6"
            >
              <div className="absolute top-6 right-8 text-neutral-200 pointer-events-none">
                <Quote className="w-12 h-12 stroke-[1.5]" />
              </div>

              {/* Stars */}
              <div className="flex gap-1 relative z-10">
                {Array.from({ length: item.stars }).map((_, sIdx) => (
                  <Star key={sIdx} className="w-4 h-4 fill-gold text-gold" />
                ))}
              </div>

              {/* Quote text */}
              <p className="text-xs md:text-sm text-brand-text leading-relaxed font-serif italic relative z-10">
                "{item.quote}"
              </p>

              {/* Author info */}
              <div className="border-t border-neutral-200/50 pt-4 text-left">
                <h4 className="text-sm font-extrabold text-brand-text">{item.author}</h4>
                <span className="text-[10px] font-semibold text-brand-muted uppercase tracking-wider block mt-0.5">
                  {item.credentials}
                </span>
              </div>
            </motion.div>
          ))}
        </div>

      </div>
    </section>
  );
}
