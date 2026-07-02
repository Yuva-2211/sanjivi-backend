"use client";

import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  MessageSquare,
  Cpu,
  ShieldAlert,
  Activity,
  Network,
  Sparkles,
  GitMerge,
  ShieldCheck,
  FileText,
  Play,
  RotateCcw,
  Heart,
  ChevronRight,
  AlertTriangle
} from "lucide-react";

// Definitions of flow stages
interface StepDetail {
  id: string;
  title: string;
  subtitle: string;
  icon: React.ReactNode;
  description: string;
  details: string;
  color: string;
  glowColor: string;
}

const steps: StepDetail[] = [
  {
    id: "query",
    title: "User Query Input",
    subtitle: "AYUSH Orchestrator Reception",
    icon: <MessageSquare className="w-5 h-5 text-emerald-600" />,
    description: "Sanjivi AI's portal ingests the user's natural language health queries. It supports multi-lingual voice and text inputs, parsing intent and clinical context.",
    details: "Performs spelling corrections, medical semantic expansion, and maps colloquial symptom terms to standard clinical lexicons across traditional systems.",
    color: "bg-emerald-50 text-emerald-700 border-emerald-200",
    glowColor: "rgba(16,185,129,0.3)"
  },
  {
    id: "orchestrator",
    title: "AYUSH Orchestrator",
    subtitle: "Central Processing Unit",
    icon: <Cpu className="w-5 h-5 text-teal-600" />,
    description: "The core cognitive orchestrator initializing the consultation session. It establishes the workspace, retrieves patient history, and handles routing keys.",
    details: "Coordinates message queues, logs inputs, and acts as the supervisor that delegates sub-tasks to the safety and routing sub-agents.",
    color: "bg-teal-50 text-teal-700 border-teal-200",
    glowColor: "rgba(20,184,166,0.3)"
  },
  {
    id: "emergency",
    title: "Emergency Detection",
    subtitle: "Real-time Safety Check",
    icon: <ShieldAlert className="w-5 h-5 text-rose-600" />,
    description: "Before applying holistic advice, the orchestrator immediately filters the query for critical red-flag symptoms like severe chest pain, extreme dyspnea, or heavy bleeding.",
    details: "If a clinical emergency is identified, it bypasses the AI flow entirely to prompt an instant Hospital Referral with mapped nearby emergency clinics.",
    color: "bg-rose-50 text-rose-700 border-rose-200",
    glowColor: "rgba(244,63,94,0.3)"
  },
  {
    id: "routing",
    title: "Query Routing & Specialist SLMs",
    subtitle: "Small Language Models (SLMs)",
    icon: <Network className="w-5 h-5 text-indigo-600" />,
    description: "Safe queries are processed in parallel by five specialized Small Language Models (SLMs), each trained extensively on ancient scriptures and modern clinical guidelines.",
    details: "Includes domain-specific models: Ayurveda (Dosha balance), Siddha (mineral-herb dynamics), Unani (humoral science), Homeopathy (diluted therapeutics), and Yoga & Naturopathy (mind-body routines).",
    color: "bg-indigo-50 text-indigo-700 border-indigo-200",
    glowColor: "rgba(99,102,241,0.3)"
  },
  {
    id: "consensus",
    title: "Consensus Agent",
    subtitle: "Therapeutic Synthesis Panel",
    icon: <GitMerge className="w-5 h-5 text-amber-600" />,
    description: "Aggregates independent therapies from the five SLMs. It flags discrepancies, filters duplicates, and resolves conflicting dietary guidelines.",
    details: "Ensures synergy. For example, if both Ayurveda and Unani recommend stomach-soothing herbs, it balances the dosages to prevent toxic build-up.",
    color: "bg-amber-50 text-amber-700 border-amber-200",
    glowColor: "rgba(245,158,11,0.3)"
  },
  {
    id: "safety",
    title: "Safety & Validation Agent",
    subtitle: "Contraindication Verification",
    icon: <ShieldCheck className="w-5 h-5 text-emerald-600" />,
    description: "A final validation layer checks the combined advice against known allergies, chronic diseases, drug-herb interactions, and toxicological thresholds.",
    details: "Applies a 'Safety Checked' validator seal. If a minor contraindication is detected, it strips the remedy and appends a warning to see a physical doctor.",
    color: "bg-emerald-50 text-emerald-700 border-emerald-200",
    glowColor: "rgba(16,185,129,0.3)"
  },
  {
    id: "response",
    title: "Final Response",
    subtitle: "Actionable Health Recommendation",
    icon: <FileText className="w-5 h-5 text-blue-600" />,
    description: "Renders the verified, side-effect-free wellness plan to the patient. Includes tailored herbal dosages, specific yoga timelines, and dynamic nutrition guides.",
    details: "Structured with absolute clarity, offering direct actions, warning indicators, and a one-click gateway to book an appointment with a human physician.",
    color: "bg-blue-50 text-blue-700 border-blue-200",
    glowColor: "rgba(59,130,246,0.3)"
  }
];

export default function AgenticWorkflow() {
  const [activeStep, setActiveStep] = useState<string>("query");
  const [isSimulating, setIsSimulating] = useState(false);
  const [simulationIndex, setSimulationIndex] = useState(-1);
  const [typedQuery, setTypedQuery] = useState("");
  const typingTimerRef = useRef<NodeJS.Timeout | null>(null);

  const demoQueryText = "I have chronic digestive issues and high stress from work. Can you recommend a safe natural treatment?";

  const handleStepClick = (stepId: string) => {
    if (isSimulating) {
      // Cancel simulation if user interacts
      setIsSimulating(false);
      setSimulationIndex(-1);
      if (typingTimerRef.current) clearTimeout(typingTimerRef.current);
    }
    setActiveStep(stepId);
  };

  // Run simulation sequence
  const startSimulation = () => {
    setIsSimulating(true);
    setActiveStep("query");
    setSimulationIndex(0);
    setTypedQuery("");

    if (typingTimerRef.current) clearTimeout(typingTimerRef.current);

    // Step 0: Typing simulation
    let charIndex = 0;
    const typeChar = () => {
      if (charIndex < demoQueryText.length) {
        setTypedQuery((prev) => prev + demoQueryText.charAt(charIndex));
        charIndex++;
        typingTimerRef.current = setTimeout(typeChar, 30);
      } else {
        // Typing finished, move to next stage (Orchestrator) after a brief pause
        typingTimerRef.current = setTimeout(() => {
          advanceSimulation(1); // orchestrator
        }, 1500);
      }
    };

    typingTimerRef.current = setTimeout(typeChar, 300);
  };

  const advanceSimulation = (stepIdx: number) => {
    if (stepIdx >= steps.length) {
      setIsSimulating(false);
      setSimulationIndex(-1);
      return;
    }

    setSimulationIndex(stepIdx);
    const stepId = steps[stepIdx].id;
    setActiveStep(stepId);

    // Set timing based on complexity of visual step
    let delay = 3000;
    if (stepId === "routing") delay = 5000; // Give time to look at 5 SLMs
    if (stepId === "consensus") delay = 3500;
    if (stepId === "safety") delay = 3000;

    typingTimerRef.current = setTimeout(() => {
      advanceSimulation(stepIdx + 1);
    }, delay);
  };

  const resetSimulation = () => {
    setIsSimulating(false);
    setSimulationIndex(-1);
    setTypedQuery("");
    setActiveStep("query");
    if (typingTimerRef.current) clearTimeout(typingTimerRef.current);
  };

  useEffect(() => {
    return () => {
      if (typingTimerRef.current) clearTimeout(typingTimerRef.current);
    };
  }, []);

  const activeStepDetail = steps.find(s => s.id === activeStep) || steps[0];

  return (
    <section id="agentic-flow" className="relative py-24 px-4 md:px-8 lg:px-16 bg-white overflow-hidden border-t border-neutral-100">
      {/* Decorative background blurs */}
      <div className="absolute top-1/4 left-10 w-96 h-96 rounded-full bg-emerald-50/60 blur-[120px] pointer-events-none animate-pulse-slow" />
      <div className="absolute bottom-10 right-10 w-80 h-80 rounded-full bg-indigo-50/40 blur-[100px] pointer-events-none" />

      <div className="w-full max-w-7xl mx-auto z-10 relative">

        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <span className="text-[11px] font-extrabold uppercase tracking-widest text-primary bg-emerald-50 px-4 py-2 rounded-full border border-emerald-100/40">
            How It Works
          </span>
          <h2 className="text-3xl md:text-5xl font-black text-brand-text tracking-tight mt-6 mb-4 font-serif">
            A Coordinated Pathway to <span className="text-primary">Natural Care</span>
          </h2>
          <p className="text-sm md:text-base text-brand-muted leading-relaxed">
            Sanjivi AI processes health queries through a coordinated multi-agent loop, combining centuries of traditional pharmacopoeia with modern safety clearance.
          </p>
        </div>

        {/* High-Level Horizontal Flow Explainer */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-16">
          {[
            {
              num: "01",
              title: "Ask Your Question",
              desc: "Enter your symptoms or concerns in any language (text or voice)."
            },
            {
              num: "02",
              title: "Five Systems Analyze",
              desc: "Domain-specific SLMs analyze the query across traditional databases."
            },
            {
              num: "03",
              title: "Consensus & Safety",
              desc: "Discrepancies are merged and emergency/toxic limits are checked."
            },
            {
              num: "04",
              title: "Clear, Safe Answer",
              desc: "Get a verified, structured, non-conflicting wellness recommendation."
            }
          ].map((item, idx) => (
            <div key={idx} className="relative p-6 rounded-2xl bg-brand-bg border border-neutral-200/50 flex flex-col gap-3">
              <span className="text-xs font-black text-primary font-mono">{item.num}</span>
              <h4 className="text-sm font-bold text-brand-text">{item.title}</h4>
              <p className="text-xs text-brand-muted leading-relaxed">{item.desc}</p>
              {idx < 3 && (
                <div className="hidden md:block absolute top-1/2 -right-3 -translate-y-1/2 z-10 text-neutral-300 font-bold text-lg">
                  →
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Action Controller */}
        <div className="flex justify-center gap-4 mb-12">
          {!isSimulating ? (
            <button
              onClick={startSimulation}
              className="flex items-center gap-2 px-6 py-3 bg-primary hover:bg-[#1b5e20] text-white text-xs font-bold rounded-2xl shadow-md hover:shadow-lg hover:scale-[1.02] active:scale-[0.98] transition-all cursor-pointer"
            >
              <Play className="w-4 h-4 fill-white" />
              <span>Simulate Diagnostics Flow</span>
            </button>
          ) : (
            <button
              onClick={resetSimulation}
              className="flex items-center gap-2 px-6 py-3 bg-neutral-100 hover:bg-neutral-200 text-brand-text text-xs font-bold rounded-2xl border border-neutral-300 shadow-sm transition-all cursor-pointer"
            >
              <RotateCcw className="w-4 h-4" />
              <span>Stop & Reset Flow</span>
            </button>
          )}
        </div>

        {/* Split Container: Status Details Panel */}
        <div className="grid grid-cols-1 gap-10 items-stretch">

          {/* Status Details Panel & Live Simulator Display */}
          <div className="lg:col-span-5 flex flex-col gap-6">

            {/* Simulation Query Console */}
            <div className="glass-panel border-white/40 shadow-sm rounded-3xl p-5 flex flex-col gap-4">
              <div className="flex justify-between items-center pb-3 border-b border-neutral-200/50">
                <span className="text-[10px] font-bold uppercase tracking-wider text-brand-muted flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
                  Live Diagnostic Console
                </span>
                <span className="text-[9px] font-semibold text-primary bg-emerald-50 px-2 py-0.5 rounded border border-emerald-100/50">
                  Model: active
                </span>
              </div>

              <div className="flex flex-col gap-3 min-h-[120px] justify-center bg-neutral-900 text-neutral-100 font-mono text-xs p-4 rounded-2xl shadow-inner border border-neutral-800">
                {simulationIndex === 0 ? (
                  <div>
                    <span className="text-emerald-400 font-bold">$ user_query: </span>
                    <span>{typedQuery}</span>
                    <span className="inline-block w-1.5 h-4 bg-emerald-400 animate-pulse ml-0.5" />
                  </div>
                ) : simulationIndex > 0 ? (
                  <div className="flex flex-col gap-2">
                    <div>
                      <span className="text-neutral-500 font-bold">$ user_query: </span>
                      <span className="text-neutral-300">{demoQueryText}</span>
                    </div>

                    {simulationIndex >= 1 && (
                      <div className="text-[11px] text-teal-400">
                        <span className="font-bold">▶ orchestrator: </span>
                        <span>Session init. Tokenizing symptoms [acid reflux, stress].</span>
                      </div>
                    )}

                    {simulationIndex >= 2 && (
                      <div className="text-[11px] text-rose-300">
                        <span className="font-bold">▶ emergency_check: </span>
                        <span className="bg-rose-950/40 text-emerald-300 px-1 py-0.5 rounded border border-emerald-900/50">SAFE (0 red flags)</span>
                      </div>
                    )}

                    {simulationIndex >= 3 && (
                      <div className="text-[11px] text-indigo-300 leading-snug">
                        <span className="font-bold">▶ parallel_routing: </span>
                        <span>Dispatched to 5 Specialist SLMs...</span>
                        <span className="block pl-3 text-neutral-450 text-[10px] mt-0.5">
                          - Ayurveda suggests Pippali/Yashtimadhu<br />
                          - Yoga suggests Vajrasana/Shavasana
                        </span>
                      </div>
                    )}

                    {simulationIndex >= 4 && (
                      <div className="text-[11px] text-amber-300">
                        <span className="font-bold">▶ consensus: </span>
                        <span>Merged diet & herbal recipes. Calibrated dosage.</span>
                      </div>
                    )}

                    {simulationIndex >= 5 && (
                      <div className="text-[11px] text-emerald-400">
                        <span className="font-bold">▶ safety_agent: </span>
                        <span className="text-emerald-400 font-bold">✓ Clearance approved. No contraindications.</span>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-neutral-400 text-center py-6">
                    <Sparkles className="w-5 h-5 text-neutral-500 mx-auto mb-2 animate-pulse-slow" />
                    <p className="text-[11px] font-sans">Click 'Simulate Diagnostics Flow' above to run a mock clinical query sequence.</p>
                  </div>
                )}
              </div>
            </div>

            {/* Selected Node Details Card */}
            <div className="flex-1 flex flex-col justify-between neumorphic-container bg-white border border-neutral-100/70 rounded-3xl p-6 min-h-[280px]">

              <AnimatePresence mode="wait">
                <motion.div
                  key={activeStepDetail.id}
                  initial={{ opacity: 0, y: 15 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -15 }}
                  transition={{ duration: 0.3 }}
                  className="flex flex-col gap-4"
                >
                  <div className="flex items-center gap-3">
                    <div className={`p-2.5 rounded-xl border ${activeStepDetail.color} shadow-sm`}>
                      {activeStepDetail.icon}
                    </div>
                    <div className="flex flex-col">
                      <h4 className="text-base font-extrabold text-brand-text font-sans">
                        {activeStepDetail.title}
                      </h4>
                      <span className="text-[10px] font-semibold text-brand-muted tracking-wider uppercase">
                        {activeStepDetail.subtitle}
                      </span>
                    </div>
                  </div>

                  <p className="text-xs md:text-sm text-brand-muted leading-relaxed font-normal mt-2">
                    {activeStepDetail.description}
                  </p>

                  <div className="bg-neutral-50 rounded-2xl p-4 border border-neutral-200/50">
                    <span className="text-[9px] font-extrabold uppercase tracking-wider text-brand-text block mb-1">
                      Under the Hood
                    </span>
                    <p className="text-[11px] text-brand-muted leading-relaxed">
                      {activeStepDetail.details}
                    </p>
                  </div>
                </motion.div>
              </AnimatePresence>

              {/* Interactive Navigation helper */}
              <div className="mt-8 pt-4 border-t border-neutral-100 flex items-center justify-between text-[10px] font-bold text-brand-muted uppercase">
                <span>Select any node on the left to inspect</span>
                <div className="flex gap-1.5">
                  {steps.map((s) => (
                    <button
                      key={s.id}
                      onClick={() => handleStepClick(s.id)}
                      className={`w-2 h-2 rounded-full transition-colors ${activeStep === s.id ? "bg-primary" : "bg-neutral-200 hover:bg-neutral-300"
                        }`}
                    />
                  ))}
                </div>
              </div>

            </div>

          </div>

        </div>

        {/* Final Response Demo Block (Shows after response node is lit up) */}
        <AnimatePresence>
          {activeStep === "response" && (
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 20 }}
              className="mt-12 w-full max-w-4xl mx-auto glass-panel border-emerald-200/60 rounded-[32px] p-6 md:p-8 shadow-xl"
            >
              <div className="flex flex-wrap justify-between items-center gap-4 pb-4 border-b border-emerald-100/50">
                <div className="flex items-center gap-2">
                  <Heart className="w-5 h-5 text-rose-500 fill-rose-500/20" />
                  <h4 className="text-base md:text-lg font-black text-brand-text">
                    Sanjivi AI Diagnostic Result
                  </h4>
                </div>
                <div className="flex items-center gap-1.5 px-3 py-1 bg-emerald-50 text-primary border border-emerald-100 text-[10px] font-extrabold uppercase tracking-widest rounded-full">
                  <ShieldCheck className="w-3.5 h-3.5" />
                  <span>Safety & Consensus Checked</span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
                <div className="flex flex-col gap-4">
                  <div>
                    <span className="text-[10px] font-extrabold uppercase tracking-widest text-primary">
                      Primary Diagnosis & Root Cause
                    </span>
                    <p className="text-xs md:text-sm text-brand-muted leading-relaxed mt-1">
                      Imbalance of Agni (digestive fire) combined with high cortisol levels resulting in Pitta aggravation. Requires dual cooling/digesting compounds and mental relaxation routines.
                    </p>
                  </div>

                  <div>
                    <span className="text-[10px] font-extrabold uppercase tracking-widest text-primary">
                      Herbal & Natural Remedies
                    </span>
                    <div className="flex flex-col gap-2 mt-2">
                      <div className="flex items-start gap-2.5 text-xs text-brand-muted">
                        <span className="w-1.5 h-1.5 rounded-full bg-gold shrink-0 mt-1.5" />
                        <span><strong>Yashtimadhu (Licorice):</strong> 500mg infusion twice daily post-meals (Soothes esophageal lining).</span>
                      </div>
                      <div className="flex items-start gap-2.5 text-xs text-brand-muted">
                        <span className="w-1.5 h-1.5 rounded-full bg-gold shrink-0 mt-1.5" />
                        <span><strong>Inji Surasam (Siddha Ginger Elixir):</strong> 5ml pre-meals (Eliminates Ama/gastric toxins).</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="flex flex-col gap-4">
                  <div>
                    <span className="text-[10px] font-extrabold uppercase tracking-widest text-primary">
                      Yoga & Naturopathy Prescriptions
                    </span>
                    <div className="flex flex-col gap-2 mt-2">
                      <div className="flex items-start gap-2.5 text-xs text-brand-muted">
                        <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 shrink-0 mt-1.5" />
                        <span><strong>Vajrasana (Thunderbolt pose):</strong> Sit in posture for 8-10 minutes immediately after lunch & dinner.</span>
                      </div>
                      <div className="flex items-start gap-2.5 text-xs text-brand-muted">
                        <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 shrink-0 mt-1.5" />
                        <span><strong>Pranayama (Sheetali & Nadi Shodhana):</strong> 15 minutes in the morning to calm anxiety and cool the system.</span>
                      </div>
                    </div>
                  </div>

                  <div className="mt-4 p-4 bg-emerald-50/50 border border-emerald-100 rounded-2xl flex items-center justify-between gap-4">
                    <p className="text-[10px] text-brand-muted leading-relaxed max-w-sm">
                      Need a physical clinic prescription? Connect with one of our certified AYUSH doctors.
                    </p>
                    <button
                      onClick={() => {
                        const target = document.querySelector("#contact");
                        if (target) target.scrollIntoView({ behavior: "smooth" });
                      }}
                      className="px-4 py-2 bg-primary hover:bg-[#1b5e20] text-white text-[10px] font-extrabold uppercase tracking-wider rounded-xl transition-all shadow-sm shrink-0"
                    >
                      Consult Doctor
                    </button>
                  </div>
                </div>
              </div>

            </motion.div>
          )}
        </AnimatePresence>

      </div>
    </section>
  );
}
