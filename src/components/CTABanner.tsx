"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle, Mail, User, ShieldCheck } from "lucide-react";

export default function CTABanner() {
  const [formData, setFormData] = useState({ name: "", email: "" });
  const [status, setStatus] = useState<"idle" | "submitting" | "success" | "error">("idle");
  const [message, setMessage] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus("submitting");
    setMessage("");

    try {
      const response = await fetch("/api/early-access", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Unable to join early access right now.");
      }

      setStatus("success");
      setMessage(data.message || "You are on the early access list.");
      setFormData({ name: "", email: "" });
    } catch (err) {
      setStatus("error");
      setMessage(err instanceof Error ? err.message : "Unable to join early access right now.");
    }
  };

  return (
    <section
      id="contact"
      className="relative py-24 w-full flex items-center justify-center overflow-hidden border-t border-neutral-100 bg-brand-bg"
    >
      <div className="absolute inset-0 bg-gradient-to-br from-[#1B5E20]/5 via-transparent to-[#F9A825]/5 opacity-90 pointer-events-none" />

      <div className="w-full max-w-2xl mx-auto z-10 relative px-4 md:px-8">
        <div className="text-center mb-10">
          <span className="text-[11px] font-extrabold uppercase tracking-widest text-primary bg-emerald-50 px-4 py-2 rounded-full border border-emerald-100/40">
            Early Access
          </span>
          <h2 className="text-3xl md:text-5xl font-black text-brand-text tracking-tight mt-6 mb-4 font-serif">
            Join Sanjivi AI early access
          </h2>
          <p className="text-sm md:text-base text-brand-muted leading-relaxed">
            Leave your email and we will notify you when your access is ready. No payment method required.
          </p>
        </div>

        <div className="bg-white border border-neutral-200/60 rounded-2xl p-6 md:p-8 shadow-sm">
          <AnimatePresence mode="wait">
            {status !== "success" ? (
              <motion.form
                key="form"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.25 }}
                onSubmit={handleSubmit}
                className="flex flex-col gap-5"
              >
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="flex flex-col gap-1.5">
                    <label className="text-[10px] font-extrabold uppercase tracking-wider text-brand-muted">Full Name</label>
                    <div className="relative">
                      <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-400" />
                      <input
                        type="text"
                        required
                        value={formData.name}
                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                        placeholder="Your name"
                        className="w-full pl-10 pr-4 py-3 rounded-xl bg-brand-bg border border-neutral-200 text-brand-text placeholder-neutral-400 text-xs focus:bg-white focus:outline-none focus:border-primary transition-all font-medium"
                      />
                    </div>
                  </div>

                  <div className="flex flex-col gap-1.5">
                    <label className="text-[10px] font-extrabold uppercase tracking-wider text-brand-muted">Email Address</label>
                    <div className="relative">
                      <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-400" />
                      <input
                        type="email"
                        required
                        value={formData.email}
                        onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                        placeholder="you@example.com"
                        className="w-full pl-10 pr-4 py-3 rounded-xl bg-brand-bg border border-neutral-200 text-brand-text placeholder-neutral-400 text-xs focus:bg-white focus:outline-none focus:border-primary transition-all font-medium"
                      />
                    </div>
                  </div>
                </div>

                {status === "error" && (
                  <p className="text-xs font-semibold text-rose-600 bg-rose-50 border border-rose-100 rounded-xl px-3 py-2">
                    {message}
                  </p>
                )}

                <button
                  type="submit"
                  disabled={status === "submitting"}
                  className="relative w-full py-4 bg-primary hover:bg-[#1b5e20] text-white text-xs font-extrabold uppercase tracking-widest rounded-xl shadow-md hover:shadow-lg transition-all duration-300 hover:scale-[1.01] active:scale-[0.98] cursor-pointer disabled:opacity-70 flex items-center justify-center gap-2"
                >
                  <ShieldCheck className="w-4 h-4 text-emerald-300" />
                  <span>{status === "submitting" ? "Joining..." : "Join Early Access"}</span>
                </button>
              </motion.form>
            ) : (
              <motion.div
                key="success"
                initial={{ opacity: 0, scale: 0.96 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.96 }}
                className="flex flex-col items-center justify-center py-8 text-center"
              >
                <div className="w-14 h-14 rounded-full bg-emerald-50 border border-emerald-100 flex items-center justify-center mb-5">
                  <CheckCircle className="w-8 h-8 text-primary" />
                </div>
                <h3 className="text-xl font-bold text-brand-text font-serif">You are on the list</h3>
                <p className="text-xs text-brand-muted mt-2 max-w-sm leading-relaxed">{message}</p>
                <button
                  onClick={() => setStatus("idle")}
                  className="mt-6 px-5 py-2.5 border border-neutral-300 hover:border-primary text-brand-muted hover:text-primary rounded-xl text-[10px] font-extrabold uppercase tracking-wider transition-all"
                >
                  Add another email
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </section>
  );
}
