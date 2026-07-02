"use client";

import React from "react";
import SanjiviLogo from "./SanjiviLogo";

export default function Footer() {
  const handleScrollTo = (e: React.MouseEvent<HTMLAnchorElement>, href: string) => {
    e.preventDefault();
    const target = document.querySelector(href);
    if (target) {
      target.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <footer className="relative bg-brand-bg pt-20 pb-10 border-t border-neutral-200/50 overflow-hidden">

      {/* Subtle animated floating particles inside footer */}
      <div className="absolute inset-0 pointer-events-none opacity-40">
        <div className="absolute bottom-10 left-[15%] w-2 h-2 bg-emerald-300 rounded-full animate-float-slow" />
        <div className="absolute bottom-20 right-[25%] w-1.5 h-1.5 bg-amber-300 rounded-full animate-float-reverse" />
        <div className="absolute top-10 right-[10%] w-2 h-2 bg-emerald-400 rounded-full animate-float-slow" />
      </div>

      <div className="w-full max-w-7xl mx-auto px-4 md:px-8 z-10 relative">
        <div className="flex flex-col md:flex-row justify-between items-start gap-12 mb-16">

          {/* Column 1: Brand Info */}
          <div className="flex flex-col gap-6 max-w-md">
            <div className="flex flex-col gap-1">
              <SanjiviLogo />
              <p className="text-[10px] font-extrabold text-primary uppercase tracking-wider pl-1 mt-0.5">
                Sanjivi A product of 1729 labs
              </p>
            </div>
            <p className="text-xs text-brand-muted leading-relaxed">
              Sanjivi Ayush Healthcare combines the ancient wisdom of Ayurveda, Yoga, Siddha, Unani, and Homeopathy with modern precision to deliver authentic, natural healthcare solutions.
            </p>
            {/* Social Links */}
            <div className="flex flex-col gap-3">
              <div className="text-xs text-brand-muted">
                <a href="mailto:sanjivi.ai.care@zohomail.in" className="hover:text-primary transition-colors">
                  sanjivi.ai.care@zohomail.in
                </a>
              </div>
              <div className="flex gap-3">
                {[
                  {
                    icon: (
                      <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z" />
                        <rect x="2" y="9" width="4" height="12" />
                        <circle cx="4" cy="4" r="2" />
                      </svg>
                    ),
                    href: "https://www.linkedin.com/company/agilisum/posts/?feedView=all",
                  },
                  {
                    icon: (
                      <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M23 3a10.9 10.9 0 0 1-3.14.86 4.48 4.48 0 0 0 1.94-2.48 9 9 0 0 1-2.84 1.08A4.48 4.48 0 0 0 16.5 2a4.48 4.48 0 0 0-4.47 4.48c0 .35.04.7.11 1.03a12.8 12.8 0 0 1-9.29-4.7 4.48 4.48 0 0 0 1.39 6 4.49 4.49 0 0 1-2.03-.56v.06A4.48 4.48 0 0 0 4.5 12a4.49 4.49 0 0 1-2.02.08 4.48 4.48 0 0 0 4.18 3.11A9 9 0 0 1 2 18.57a12.8 12.8 0 0 0 6.93 2.03c8.3 0 12.83-6.88 12.83-12.84 0-.2 0-.39-.01-.58A9.18 9.18 0 0 0 23 3z" />
                      </svg>
                    ),
                    href: "https://x.com/SanjiviAI",
                  },
                ].map((item, idx) => (
                  <a
                    key={idx}
                    href={item.href}
                    target="_blank"
                    rel="noreferrer noopener"
                    className="w-8 h-8 rounded-lg bg-white border border-neutral-200 flex items-center justify-center text-brand-muted hover:text-primary hover:border-primary transition-all duration-300 hover:scale-105"
                  >
                    {item.icon}
                  </a>
                ))}
              </div>
            </div>
          </div>

          {/* Column 2: Quick Links */}
          <div className="flex flex-col gap-5 min-w-[180px]">
            <h4 className="text-xs font-bold uppercase tracking-widest text-brand-text">
              Quick Links
            </h4>
            <ul className="flex flex-col gap-3 text-xs text-brand-muted font-medium">
              <li>
                <a href="#problems" onClick={(e) => handleScrollTo(e, "#problems")} className="hover:text-primary transition-colors">
                  The Problem
                </a>
              </li>
              <li>
                <a href="#agentic-flow" onClick={(e) => handleScrollTo(e, "#agentic-flow")} className="hover:text-primary transition-colors">
                  AI Agentic Flow
                </a>
              </li>
              <li>
                <a href="#safety-foundation" onClick={(e) => handleScrollTo(e, "#safety-foundation")} className="hover:text-primary transition-colors">
                  Safety First
                </a>
              </li>
              <li>
                <a href="#contact" onClick={(e) => handleScrollTo(e, "#contact")} className="hover:text-primary transition-colors">
                  Join Early Access
                </a>
              </li>
            </ul>
          </div>

        </div>

        {/* Divider */}
        <div className="h-px bg-neutral-200/50 w-full my-6" />

        {/* Copyright info */}
        <div className="flex flex-col sm:flex-row justify-between items-center text-[10px] text-brand-muted font-semibold gap-4">
          <div className="flex flex-col sm:flex-row items-center gap-1 sm:gap-2 text-center sm:text-left">
            <span>
              © {new Date().getFullYear()} Sanjivi Ayush Healthcare. All Rights Reserved.
            </span>
            <span className="hidden sm:inline text-neutral-300">|</span>
            <span>
              Sanjivi A product of 1729 labs
            </span>
          </div>
          <div className="flex gap-6">
            <a href="/privacy" className="hover:text-primary transition-colors">Privacy Policy</a>
            <a href="/terms" className="hover:text-primary transition-colors">Terms of Service</a>
            <a href="/ayush-disclaimers" className="hover:text-primary transition-colors">AYUSH Disclaimers</a>
          </div>
        </div>

      </div>
    </footer>
  );


}
