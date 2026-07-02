"use client";

import React, { useRef } from "react";
import { motion, useScroll, useTransform } from "framer-motion";
import { CalendarRange, UserCheck, ClipboardList, Activity } from "lucide-react";

interface Step {
  number: string;
  title: string;
  description: string;
  icon: React.ReactNode;
}

export default function Journey() {
  const containerRef = useRef<HTMLDivElement>(null);
  
  // Track scroll progress of the container
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start center", "end center"],
  });

  // Grow vertical line height from 0% to 100%
  const lineHeight = useTransform(scrollYProgress, [0, 1], ["0%", "100%"]);

  const steps: Step[] = [
    {
      number: "01",
      title: "Book Appointment",
      description: "Schedule your consultation online or via telephone. Choose your preferred stream of AYUSH or let our coordinators guide you based on symptoms.",
      icon: <CalendarRange className="w-6 h-6" />,
    },
    {
      number: "02",
      title: "Consult Expert Doctor",
      description: "Undergo a deep diagnostic evaluation covering your physical humors (Dosha/Humor), pulse readings, and medical history with our certified specialists.",
      icon: <UserCheck className="w-6 h-6" />,
    },
    {
      number: "03",
      title: "Receive Personalized Plan",
      description: "Get a customized treatment regimen combining premium herbal remedies, therapeutic yoga protocols, dietary adjustments, and session schedules.",
      icon: <ClipboardList className="w-6 h-6" />,
    },
    {
      number: "04",
      title: "Start Healing Journey",
      description: "Embark on natural recovery. Experience periodic check-ins, holistic therapy sessions, and progressive health improvements under professional guidance.",
      icon: <Activity className="w-6 h-6" />,
    },
  ];

  return (
    <section
      id="journey"
      ref={containerRef}
      className="relative py-24 px-4 md:px-8 lg:px-16 bg-white overflow-hidden"
    >
      <div className="w-full max-w-5xl mx-auto z-10 relative">
        
        {/* Section Header */}
        <div className="text-center max-w-2xl mx-auto mb-20">
          <span className="text-[11px] font-extrabold uppercase tracking-widest text-primary bg-emerald-50 px-4 py-2 rounded-full border border-emerald-100/40">
            Our Process
          </span>
          <h2 className="text-3xl md:text-5xl font-black text-brand-text mt-6 mb-4">
            Your Path to <span className="text-primary">Complete Recovery</span>
          </h2>
          <p className="text-sm text-brand-muted leading-relaxed">
            From initial diagnostics to continuous natural wellness, see how easy it is to start your custom natural healing regimen.
          </p>
        </div>

        {/* Timeline Content */}
        <div className="relative">
          
          {/* Timeline Center Line (Background grey line) */}
          <div className="absolute left-[30px] md:left-1/2 top-8 bottom-8 w-1 bg-neutral-100 -translate-x-1/2 rounded-full pointer-events-none" />

          {/* Timeline Growing Line (Scroll-linked green line) */}
          <motion.div
            style={{ height: lineHeight }}
            className="absolute left-[30px] md:left-1/2 top-8 w-1 bg-primary -translate-x-1/2 rounded-full origin-top pointer-events-none z-10"
          />

          {/* Steps */}
          <div className="flex flex-col gap-16 relative">
            {steps.map((step, idx) => {
              const isEven = idx % 2 === 0;

              return (
                <div
                  key={step.number}
                  className="flex flex-col md:flex-row items-start md:items-center relative w-full"
                >
                  
                  {/* Left Column (Desktop) */}
                  <div className={`w-full md:w-1/2 flex justify-start md:justify-end pr-0 md:pr-16 order-2 md:order-1 ${
                    isEven ? "md:opacity-100" : "md:opacity-100"
                  }`}>
                    {isEven ? (
                      <motion.div
                        initial={{ opacity: 0, x: -30 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        viewport={{ once: true, margin: "-50px" }}
                        transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
                        className="glass-panel p-6 sm:p-8 rounded-[28px] border border-neutral-100 shadow-sm max-w-md w-full"
                      >
                        <span className="text-sm font-bold text-gold">{step.number}</span>
                        <h3 className="text-xl font-bold text-brand-text mt-2 mb-3">
                          {step.title}
                        </h3>
                        <p className="text-xs sm:text-sm text-brand-muted leading-relaxed">
                          {step.description}
                        </p>
                      </motion.div>
                    ) : (
                      // Spacer for desktop if odd (renders description on right)
                      <div className="hidden md:block w-full" />
                    )}
                  </div>

                  {/* Timeline Badge/Dot (Center) */}
                  <div className="absolute left-[30px] md:left-1/2 top-2 md:top-auto -translate-x-1/2 z-20 order-1 md:order-2">
                    <motion.div
                      initial={{ scale: 0.8, opacity: 0 }}
                      whileInView={{ scale: 1, opacity: 1 }}
                      viewport={{ once: true }}
                      transition={{ duration: 0.5, delay: 0.1 }}
                      className="w-[60px] h-[60px] rounded-full bg-white border-2 border-emerald-100 text-primary flex items-center justify-center shadow-md group hover:border-primary hover:text-white hover:bg-primary transition-all duration-300"
                    >
                      {step.icon}
                    </motion.div>
                  </div>

                  {/* Right Column (Desktop) */}
                  <div className="w-full md:w-1/2 flex justify-start pl-16 md:pl-16 order-3">
                    {!isEven ? (
                      <motion.div
                        initial={{ opacity: 0, x: 30 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        viewport={{ once: true, margin: "-50px" }}
                        transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
                        className="glass-panel p-6 sm:p-8 rounded-[28px] border border-neutral-100 shadow-sm max-w-md w-full"
                      >
                        <span className="text-sm font-bold text-gold">{step.number}</span>
                        <h3 className="text-xl font-bold text-brand-text mt-2 mb-3">
                          {step.title}
                        </h3>
                        <p className="text-xs sm:text-sm text-brand-muted leading-relaxed">
                          {step.description}
                        </p>
                      </motion.div>
                    ) : (
                      // Spacer for desktop if even (renders description on left)
                      <div className="hidden md:block w-full" />
                    )}
                  </div>

                </div>
              );
            })}
          </div>

        </div>

      </div>
    </section>
  );
}
