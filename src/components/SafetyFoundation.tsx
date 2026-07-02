"use client";

import React from "react";
import { motion } from "framer-motion";
import { ShieldCheck, ShieldAlert, HeartHandshake, PhoneCall } from "lucide-react";

export default function SafetyFoundation() {
  return (
    <section id="safety-foundation" className="relative py-24 px-4 md:px-8 lg:px-16 bg-brand-bg overflow-hidden border-t border-neutral-100">
      {/* Background Decorative Glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] rounded-full bg-rose-50/40 blur-[120px] pointer-events-none" />

      <div className="w-full max-w-7xl mx-auto z-10 relative">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          
          {/* Left Column: Visual Alert Demonstration Card */}
          <div className="lg:col-span-5 order-2 lg:order-1">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
              className="glass-panel border-rose-200/50 bg-white/70 shadow-xl rounded-[32px] p-6 md:p-8 flex flex-col gap-6"
            >
              {/* Demo alert header */}
              <div className="flex items-center gap-3 pb-4 border-b border-rose-100">
                <div className="w-10 h-10 rounded-full bg-rose-100 flex items-center justify-center text-rose-600 animate-pulse-slow">
                  <ShieldAlert className="w-5 h-5" />
                </div>
                <div className="text-left">
                  <h4 className="text-sm font-extrabold text-rose-950 font-sans">Emergency Bypass Triggered</h4>
                  <span className="text-[10px] font-semibold text-rose-700 uppercase tracking-widest">Active Safety Protection</span>
                </div>
              </div>

              {/* Sample Warning Copy */}
              <p className="text-xs text-rose-950/80 leading-relaxed font-mono bg-rose-50/50 border border-rose-100 p-4 rounded-2xl">
                SYSTEM NOTE: User query contains high-risk symptom "severe shortness of breath". Traditional pharmacopoeias are bypassed. Recommending emergency clinic.
              </p>

              {/* Action options */}
              <div className="flex flex-col gap-3">
                <div className="flex items-center justify-between p-3.5 bg-rose-600 text-white rounded-2xl shadow-md">
                  <div className="flex items-center gap-2">
                    <PhoneCall className="w-4 h-4" />
                    <span className="text-xs font-bold font-sans">Call Emergency Services</span>
                  </div>
                  <span className="text-xs font-mono font-bold">102 / 112</span>
                </div>

                <div className="p-4 bg-white border border-rose-100 rounded-2xl text-left">
                  <span className="text-[9.5px] font-black text-rose-800 uppercase tracking-wider block mb-1">Nearest Mapped Hospital</span>
                  <p className="text-xs font-bold text-brand-text">Apollo Specialty Trauma Center</p>
                  <p className="text-[10px] text-brand-muted mt-0.5">Distance: 1.8 km • Directions available in chat</p>
                </div>
              </div>

              <span className="text-[10px] font-bold text-rose-700/60 text-center uppercase tracking-widest">Sanjivi safety protocol demo</span>
            </motion.div>
          </div>

          {/* Right Column: Reassuring Explainer Content */}
          <div className="lg:col-span-7 text-left order-1 lg:order-2">
            <span className="text-[11px] font-extrabold uppercase tracking-widest text-rose-600 bg-rose-50 px-4 py-2 rounded-full border border-rose-100/50">
              Safety is the Foundation
            </span>
            
            <h2 className="text-3xl md:text-5xl font-black text-brand-text tracking-tight mt-6 mb-6 font-serif">
              Our Safety Check is <span className="text-rose-600">Immediate</span> and Uncompromising
            </h2>

            <p className="text-sm md:text-base text-brand-muted leading-relaxed mb-8">
              Traditional wellness streams offer excellent pathways to balance and chronic recovery, but they are not replacement diagnostics for acute crises. Our emergency screening acts as our core barrier to safeguard your health.
            </p>

            {/* List of safeguards */}
            <div className="flex flex-col gap-6">
              {[
                {
                  title: "Emergency Bypass screening",
                  desc: "Before any herbal compound or yoga routine is selected, our system evaluates query strings for critical cardiovascular, pulmonary, or trauma indicators.",
                  icon: <ShieldAlert className="w-5 h-5 text-rose-600" />
                },
                {
                  title: "Contraindication Engine",
                  desc: "Our validation layer cross-references suggested remedies with active user prescriptions, conditions, or allergies to eliminate dangerous drug-herb interactions.",
                  icon: <ShieldCheck className="w-5 h-5 text-emerald-600" />
                },
                {
                  title: "Grounded Wellness Borders",
                  desc: "Sanjivi AI operates strictly within educational guidelines. We build confidence with Persona C (Caregivers) and Persona D by prioritizing physical triage over digital speculation.",
                  icon: <HeartHandshake className="w-5 h-5 text-indigo-600" />
                }
              ].map((item, idx) => (
                <div key={idx} className="flex gap-4 items-start">
                  <div className="w-10 h-10 rounded-xl bg-white border border-neutral-200/50 flex items-center justify-center shrink-0 shadow-sm">
                    {item.icon}
                  </div>
                  <div className="flex flex-col gap-1">
                    <h4 className="text-sm font-extrabold text-brand-text font-sans">{item.title}</h4>
                    <p className="text-xs text-brand-muted leading-relaxed">{item.desc}</p>
                  </div>
                </div>
              ))}
            </div>

          </div>

        </div>
      </div>
    </section>
  );
}
