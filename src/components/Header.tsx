"use client";

import React, { useState, useEffect } from "react";
import SanjiviLogo from "./SanjiviLogo";
import { Menu, X } from "lucide-react";
import { useRouter } from "next/navigation";

export default function Header() {
  const router = useRouter();
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const navItems = [
    { label: "Home", href: "#home" },
    { label: "Problem", href: "#problems" },
    { label: "How It Works", href: "#agentic-flow" },
    { label: "AYUSH Systems", href: "#ayush" },
    { label: "Safety First", href: "#safety-foundation" },
  ];

  const handleScrollTo = (e: React.MouseEvent<HTMLAnchorElement>, href: string) => {
    e.preventDefault();
    setIsMobileMenuOpen(false);
    const target = document.querySelector(href);
    if (target) {
      target.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <>
      <header
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ease-[cubic-bezier(0.22,1,0.36,1)] ${
          isScrolled
            ? "py-3 px-4 md:px-8 mt-2 mx-auto max-w-7xl rounded-2xl border border-white/20 shadow-lg bg-white/60 backdrop-blur-xl"
            : "py-6 px-6 md:px-12 bg-transparent"
        }`}
      >
        <div className="flex items-center justify-between w-full">
          {/* Logo */}
          <a href="#home" className="cursor-pointer">
            <SanjiviLogo />
          </a>

          {/* Desktop Navigation */}
          <nav className="hidden lg:flex items-center gap-8">
            {navItems.map((item) => (
              <a
                key={item.label}
                href={item.href}
                onClick={(e) => handleScrollTo(e, item.href)}
                className="text-sm font-medium text-brand-muted hover:text-primary transition-colors duration-300 relative group py-2"
              >
                {item.label}
                <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-primary transition-all duration-300 group-hover:w-full" />
              </a>
            ))}
          </nav>

          {/* Action Buttons */}
          <div className="hidden sm:flex items-center gap-4">
            <button
              onClick={() => router.push("/chat")}
              className="px-4 py-2 border border-neutral-200 hover:border-primary text-brand-text hover:text-primary text-xs font-semibold rounded-full shadow-sm transition-all duration-300 hover:scale-[1.03] active:scale-[0.98] cursor-pointer"
            >
              Open Chat
            </button>
          </div>

          {/* Mobile Menu Toggle */}
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="lg:hidden p-2 rounded-xl bg-white/60 border border-white/40 shadow-sm hover:bg-white transition-colors"
          >
            {isMobileMenuOpen ? (
              <X className="w-6 h-6 text-brand-text" />
            ) : (
              <Menu className="w-6 h-6 text-brand-text" />
            )}
          </button>
        </div>
      </header>

      {/* Mobile Navigation Drawer */}
      <div
        className={`fixed inset-0 z-40 lg:hidden transition-all duration-500 ease-[cubic-bezier(0.22,1,0.36,1)] ${
          isMobileMenuOpen ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"
        }`}
      >
        {/* Backdrop overlay */}
        <div
          onClick={() => setIsMobileMenuOpen(false)}
          className="absolute inset-0 bg-brand-text/10 backdrop-blur-md"
        />

        {/* Drawer Panel */}
        <div
          className={`absolute top-0 right-0 w-[80%] max-w-sm h-full bg-white/95 backdrop-blur-2xl shadow-2xl p-8 flex flex-col justify-between border-l border-white/20 transition-transform duration-500 ease-[cubic-bezier(0.22,1,0.36,1)] ${
            isMobileMenuOpen ? "translate-x-0" : "translate-x-full"
          }`}
        >
          <div className="flex flex-col gap-8 mt-16">
            <SanjiviLogo />
            <div className="h-px bg-emerald-100/50 my-2" />
            <nav className="flex flex-col gap-6">
              {navItems.map((item) => (
                <a
                  key={item.label}
                  href={item.href}
                  onClick={(e) => handleScrollTo(e, item.href)}
                  className="text-lg font-medium text-brand-muted hover:text-primary transition-colors py-1 flex items-center justify-between"
                >
                  <span>{item.label}</span>
                  <span className="w-1.5 h-1.5 rounded-full bg-gold opacity-0 hover:opacity-100 transition-opacity" />
                </a>
              ))}
            </nav>
          </div>

          <div className="flex flex-col gap-4 mt-auto">
            <button
              onClick={() => {
                setIsMobileMenuOpen(false);
                router.push("/chat");
              }}
              className="w-full flex items-center justify-center p-3 rounded-2xl bg-white border border-neutral-300 text-sm font-semibold text-brand-text hover:border-primary hover:text-primary transition-all cursor-pointer"
            >
              Open Chat
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
