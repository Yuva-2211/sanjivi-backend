"use client";

import React from "react";
import { motion } from "framer-motion";
import { HelpCircle, AlertTriangle, ShieldCheck } from "lucide-react";

interface ProblemPanelProps {
  title: string;
  problem: string;
  solution: string;
  icon: React.ReactNode;
  delay: number;
}

function ProblemPanel({ title, problem, solution, icon, delay }: ProblemPanelProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-100px" }}
      transition={{ duration: 0.8, delay, ease: [0.22, 1, 0.36, 1] }}
      className="group relative rounded-[28px] p-8 bg-white border border-neutral-100 shadow-sm hover:shadow-xl transition-all duration-500 overflow-hidden flex flex-col gap-6"
    >
      {/* Sleek diagonal white gloss shine sweep on hover */}
      <div className="absolute inset-0 pointer-events-none z-0">
        <div className="absolute top-0 -left-[100%] w-[40%] h-full bg-gradient-to-r from-transparent via-emerald-50/20 to-transparent skew-x-[-25deg] group-hover:left-[150%] transition-all duration-[1000ms] ease-out" />
      </div>

      {/* Card Header: Icon with custom background */}
      <div className="relative z-10 w-14 h-14 rounded-2xl bg-brand-bg border border-neutral-200/50 flex items-center justify-center text-primary shadow-sm group-hover:scale-110 group-hover:border-primary/20 transition-all duration-500">
        {icon}
      </div>

      {/* Card Body */}
      <div className="relative z-10 flex flex-col gap-4 flex-1 justify-between">
        <div className="flex flex-col gap-2">
          <h3 className="text-lg md:text-xl font-bold text-brand-text group-hover:text-primary transition-colors duration-300">
            {title}
          </h3>
          <p className="text-xs md:text-sm text-brand-muted leading-relaxed italic border-l-2 border-neutral-200 pl-3">
            "{problem}"
          </p>
        </div>
        
        <div className="bg-emerald-50/50 rounded-2xl p-4 border border-emerald-100/50">
          <span className="text-[9.5px] font-extrabold uppercase tracking-wider text-primary block mb-1">
            Sanjivi AI Solution
          </span>
          <p className="text-xs text-brand-muted leading-relaxed">
            {solution}
          </p>
        </div>
      </div>

      {/* Decorative organic bubble in background */}
      <div className="absolute -bottom-8 -right-8 w-24 h-24 rounded-full bg-emerald-50/30 opacity-40 group-hover:scale-125 transition-transform duration-700 pointer-events-none" />
    </motion.div>
  );
}

export default function ProblemSection() {
  const panels = [
    {
      title: "Confusion Between Systems",
      problem: "Should I take Ayurvedic herbs, Unani formulations, or practice specific Yoga asanas for my sleep cycles? I don't know which system is best for me.",
      solution: "Sanjivi AI runs your query through five specialized SLMs (Ayurveda, Yoga, Unani, Siddha, Homeopathy) in parallel, cross-referencing and consolidating them into one clear protocol.",
      icon: <HelpCircle className="w-6 h-6 text-emerald-600 animate-pulse-slow" />,
    },
    {
      title: "Fear of Wrong Remedies",
      problem: "Traditional herbs are natural, but can I combine them safely? What if a digestive leaf interacts negatively with my blood pressure medications?",
      solution: "Every synthesized advice card is processed by our Safety Validation Agent. It cross-checks remedies against contraindications, allergies, and drug interactions.",
      icon: <AlertTriangle className="w-6 h-6 text-amber-500" />,
    },
    {
      title: "When to Seek Hospital Care",
      problem: "I feel chest discomfort or high fever, but I'd prefer a natural remedy first. Is it safe to treat this at home, or do I need a hospital immediately?",
      solution: "Our system screens for clinical red flags first. If an emergency symptom is detected, Sanjivi AI stops the advice flow and provides an instant local hospital referral.",
      icon: <ShieldCheck className="w-6 h-6 text-primary" />,
    },
  ];

  return (
    <section
      id="problems"
      className="relative py-24 px-4 md:px-8 lg:px-16 bg-brand-bg overflow-hidden border-t border-neutral-100"
    >
      {/* Decorative blurred backdrops */}
      <div className="absolute top-1/3 left-10 w-96 h-96 rounded-full bg-emerald-100/20 blur-[100px] pointer-events-none" />
      <div className="absolute bottom-10 right-20 w-80 h-80 rounded-full bg-amber-100/10 blur-[90px] pointer-events-none" />

      <div className="w-full max-w-7xl mx-auto z-10 relative">
        
        {/* Section Title */}
        <div className="mb-16">
          <span className="text-[11px] font-extrabold uppercase tracking-widest text-primary bg-emerald-50 px-4 py-2 rounded-full border border-emerald-100/40">
            The Problem We Solve
          </span>
          <h2 className="text-3xl md:text-5xl font-black text-brand-text tracking-tight mt-6 leading-tight font-serif">
            Bridging the Gap in <span className="text-primary">Traditional Healing</span>
          </h2>
        </div>

        {/* 3 Panels Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {panels.map((panel, index) => (
            <ProblemPanel
              key={panel.title}
              title={panel.title}
              problem={panel.problem}
              solution={panel.solution}
              icon={panel.icon}
              delay={index * 0.1}
            />
          ))}
        </div>

      </div>
    </section>
  );
}
