"use client";

import React, { useEffect, useState, useRef } from "react";
import { motion, useInView } from "framer-motion";
import { Users, UserRoundCheck, Building2, Smile } from "lucide-react";

// Count Up custom sub-component
function Counter({ target, duration = 2000, suffix = "" }: { target: number; duration?: number; suffix?: string }) {
  const [count, setCount] = useState(0);
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-50px" });

  useEffect(() => {
    if (!isInView) return;

    let start = 0;
    const end = target;
    const totalFrames = Math.min(Math.floor(duration / 16.67), 120); // capping at 60-120 frames
    let frame = 0;

    const counter = () => {
      frame++;
      // Easing out function
      const progress = frame / totalFrames;
      const easeProgress = 1 - Math.pow(1 - progress, 3);
      
      setCount(Math.floor(easeProgress * end));

      if (frame < totalFrames) {
        requestAnimationFrame(counter);
      } else {
        setCount(end);
      }
    };

    requestAnimationFrame(counter);
  }, [isInView, target, duration]);

  return (
    <span ref={ref} className="tabular-nums">
      {count.toLocaleString()}{suffix}
    </span>
  );
}

export default function Stats() {
  const stats = [
    {
      label: "Happy Patients",
      target: 10000,
      suffix: "+",
      icon: <Users className="w-6 h-6 text-emerald-600" />,
      description: "Patients successfully recovered through natural remedies.",
    },
    {
      label: "Certified Doctors",
      target: 500,
      suffix: "+",
      icon: <UserRoundCheck className="w-6 h-6 text-emerald-600" />,
      description: "Professional AYUSH certified clinical consultants.",
    },
    {
      label: "Wellness Centers",
      target: 50,
      suffix: "+",
      icon: <Building2 className="w-6 h-6 text-emerald-600" />,
      description: "Fully-equipped holistic therapy clinics nationwide.",
    },
    {
      label: "Satisfaction Rate",
      target: 98,
      suffix: "%",
      icon: <Smile className="w-6 h-6 text-emerald-600" />,
      description: "Positive clinical outcomes and wellness retention.",
    },
  ];

  return (
    <section className="relative py-20 px-4 md:px-8 lg:px-16 bg-white overflow-hidden border-y border-neutral-100/60">
      {/* Subtle organic light rays */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-7xl h-[120%] bg-gradient-to-r from-emerald-500/2 via-transparent to-amber-500/2 blur-[80px] pointer-events-none" />

      <div className="w-full max-w-7xl mx-auto z-10 relative">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
          {stats.map((stat, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: idx * 0.08 }}
              className="glass-panel p-6 sm:p-8 rounded-[28px] border border-neutral-100 hover:border-primary/20 shadow-sm hover:shadow-lg transition-all duration-500 flex flex-col items-center text-center group cursor-default"
            >
              {/* Icon Container */}
              <div className="w-12 h-12 rounded-2xl bg-brand-bg flex items-center justify-center mb-4 border border-emerald-100 shadow-sm group-hover:scale-110 transition-transform duration-500">
                {stat.icon}
              </div>

              {/* Stat Number */}
              <h3 className="text-3xl sm:text-4xl font-extrabold text-brand-text leading-none tracking-tight mb-2">
                <Counter target={stat.target} suffix={stat.suffix} />
              </h3>

              {/* Stat Label */}
              <span className="text-sm font-bold text-primary mb-2">
                {stat.label}
              </span>

              {/* Stat Description */}
              <p className="text-[11px] text-brand-muted leading-relaxed">
                {stat.description}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
