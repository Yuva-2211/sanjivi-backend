"use client";

import React from "react";
import { motion } from "framer-motion";
import { Leaf, Award, Compass, HeartHandshake } from "lucide-react";

interface BenefitCardProps {
  title: string;
  description: string;
  icon: React.ReactNode;
  delay: number;
}

function BenefitCard({ title, description, icon, delay }: BenefitCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-100px" }}
      transition={{ duration: 0.8, delay, ease: [0.22, 1, 0.36, 1] }}
      className="group relative rounded-[28px] p-8 glass-panel hover:bg-white/75 border border-white/40 shadow-sm hover:shadow-xl transition-all duration-500 overflow-hidden cursor-pointer flex flex-col gap-6"
    >
      {/* Sleek diagonal white gloss shine sweep on hover */}
      <div className="absolute inset-0 pointer-events-none z-0">
        <div className="absolute top-0 -left-[100%] w-[40%] h-full bg-gradient-to-r from-transparent via-white/35 to-transparent skew-x-[-25deg] group-hover:left-[150%] transition-all duration-[1000ms] ease-out" />
      </div>

      {/* Card Header: Icon with custom background */}
      <div className="relative z-10 w-14 h-14 rounded-2xl bg-white border border-emerald-100 flex items-center justify-center text-primary shadow-sm group-hover:scale-110 group-hover:border-primary/20 transition-all duration-500">
        {icon}
      </div>

      {/* Card Body */}
      <div className="relative z-10 flex flex-col gap-2">
        <h3 className="text-xl font-bold text-brand-text group-hover:text-primary transition-colors duration-300">
          {title}
        </h3>
        <p className="text-xs md:text-sm text-brand-muted leading-relaxed">
          {description}
        </p>
      </div>

      {/* Decorative organic bubble in background */}
      <div className="absolute -bottom-8 -right-8 w-24 h-24 rounded-full bg-emerald-50 opacity-40 group-hover:scale-125 transition-transform duration-700 pointer-events-none" />
    </motion.div>
  );
}

export default function WhyChoose() {
  const benefits = [
    {
      title: "Traditional Remedy Guidance",
      description: "Every recommendation is grounded in traditional AYUSH references and structured to support safer, more transparent wellness guidance.",
      icon: (
        <div className="relative w-7 h-7">
          <Leaf className="absolute inset-0 text-primary animate-float-slow" />
          <Leaf className="absolute inset-0 text-emerald-400 opacity-60 scale-75 translate-x-2 -translate-y-1 animate-float-reverse" />
        </div>
      ),
    },
    {
      title: "Trusted AYUSH Experts",
      description: "Our panel comprises highly qualified, government-registered doctors across Ayurveda, Yoga, Unani, Siddha and Homeopathy with decades of combined clinical success.",
      icon: (
        <div className="relative w-7 h-7 flex items-center justify-center">
          <HeartHandshake className="w-7 h-7 text-primary group-hover:animate-pulse-slow" />
        </div>
      ),
    },
    {
      title: "Holistic Health Care",
      description: "We don't just treat symptoms. We isolate and address root causes through personalized lifestyle consults, dietary guidelines, and tailored therapy plans.",
      icon: (
        <div className="relative w-7 h-7">
          <Compass className="w-7 h-7 text-primary animate-spin" style={{ animationDuration: "20s" }} />
        </div>
      ),
    },
    {
      title: "Ayush Certified Standards",
      description: "Our clinics and therapies strictly adhere to standard AYUSH guidelines, operating under full certification to ensure premium and authentic healthcare delivery.",
      icon: (
        <div className="relative w-7 h-7">
          <Award className="w-7 h-7 text-primary group-hover:scale-110 transition-transform" />
        </div>
      ),
    },
  ];

  return (
    <section
      id="why-choose"
      className="relative py-24 px-4 md:px-8 lg:px-16 bg-brand-bg overflow-hidden"
    >
      {/* Decorative blurred backdrops */}
      <div className="absolute top-1/3 left-10 w-96 h-96 rounded-full bg-emerald-100/30 blur-[100px] pointer-events-none" />
      <div className="absolute bottom-10 right-20 w-80 h-80 rounded-full bg-amber-100/20 blur-[90px] pointer-events-none" />

      <div className="w-full max-w-7xl mx-auto z-10 relative">
        
        {/* Section Title */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-end mb-16">
          <div className="lg:col-span-8">
            <span className="text-[11px] font-extrabold uppercase tracking-widest text-primary bg-emerald-50 px-4 py-2 rounded-full border border-emerald-100/40">
              Why Sanjivi
            </span>
            <h2 className="text-3xl md:text-5xl font-black text-brand-text tracking-tight mt-6 leading-tight">
              A Premium Standard of <span className="text-primary">Natural Healing</span>
            </h2>
          </div>
          <div className="lg:col-span-4">
            <p className="text-sm text-brand-muted leading-relaxed">
              We bridge traditional wellness practices with contemporary medical precision, delivering custom recovery programs that stand for excellence.
            </p>
          </div>
        </div>

        {/* 4 Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {benefits.map((benefit, index) => (
            <BenefitCard
              key={benefit.title}
              title={benefit.title}
              description={benefit.description}
              icon={benefit.icon}
              delay={index * 0.1}
            />
          ))}
        </div>

      </div>
    </section>
  );
}
