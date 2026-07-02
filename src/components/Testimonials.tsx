"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Quote, ChevronLeft, ChevronRight, Star } from "lucide-react";

interface Testimonial {
  id: number;
  name: string;
  location: string;
  treatment: string;
  quote: string;
  rating: number;
}

export default function Testimonials() {
  const [currentIndex, setCurrentIndex] = useState(0);

  const testimonials: Testimonial[] = [
    {
      id: 1,
      name: "Ramesh Krishnan",
      location: "Chennai, India",
      treatment: "Joint Care & Spine Therapy",
      quote: "Years of constant lower back pain were resolved in just 3 weeks. The Kati Basti oils and yoga poses suggested by the Sanjivi specialists did wonders for me. Highly recommended!",
      rating: 5,
    },
    {
      id: 2,
      name: "Aishwarya Rai",
      location: "Bangalore, India",
      treatment: "Stress Management Program",
      quote: "Sirodhara therapy is pure bliss. It helped me reset my sleep schedule and eliminated chronic work anxiety. The doctors are incredibly caring and professional.",
      rating: 5,
    },
    {
      id: 3,
      name: "David Miller",
      location: "London, UK",
      treatment: "Digestive Wellness (Panchakarma)",
      quote: "I traveled to Sanjivi for their digestive detox. The personalized nutrition plan and herbal mixtures cured my chronic IBS symptoms. Outstanding natural healthcare system.",
      rating: 5,
    },
  ];

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % testimonials.length);
    }, 5500); // Auto-scroll every 5.5s
    return () => clearInterval(timer);
  }, [testimonials.length]);

  const handleNext = () => {
    setCurrentIndex((prev) => (prev + 1) % testimonials.length);
  };

  const handlePrev = () => {
    setCurrentIndex((prev) => (prev - 1 + testimonials.length) % testimonials.length);
  };

  return (
    <section className="relative py-24 px-4 md:px-8 lg:px-16 bg-white overflow-hidden">
      {/* Decorative Blur Backgrounds */}
      <div className="absolute top-1/4 left-10 w-96 h-96 rounded-full bg-emerald-50 blur-[100px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-10 w-96 h-96 rounded-full bg-amber-50 blur-[100px] pointer-events-none" />

      <div className="w-full max-w-4xl mx-auto z-10 relative">
        
        {/* Section Header */}
        <div className="text-center max-w-xl mx-auto mb-16">
          <span className="text-[11px] font-extrabold uppercase tracking-widest text-primary bg-emerald-50 px-4 py-2 rounded-full border border-emerald-100/40">
            Success Stories
          </span>
          <h2 className="text-3xl md:text-5xl font-black text-brand-text mt-6 mb-4">
            Words From Our <span className="text-primary">Healthy Patients</span>
          </h2>
        </div>

        {/* Testimonial Active Slide Container */}
        <div className="relative min-h-[340px] flex items-center justify-center">
          
          <AnimatePresence mode="wait">
            <motion.div
              key={currentIndex}
              initial={{ opacity: 0, scale: 0.96 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.96 }}
              transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
              className="w-full"
            >
              {/* Floating Glass Testimonial Card */}
              <div className="glass-panel p-8 sm:p-12 rounded-[28px] border border-white/50 shadow-lg relative animate-float-slow">
                
                {/* Large Quote Emblem */}
                <div className="absolute top-6 right-8 text-neutral-200/50 pointer-events-none">
                  <Quote className="w-16 h-16 transform rotate-180 text-emerald-100" />
                </div>

                <div className="flex flex-col gap-6">
                  {/* Rating Stars */}
                  <div className="flex gap-1">
                    {Array.from({ length: testimonials[currentIndex].rating }).map((_, i) => (
                      <Star key={i} className="w-4 h-4 text-gold fill-gold" />
                    ))}
                  </div>

                  {/* Quote text */}
                  <blockquote className="text-base sm:text-xl text-brand-text font-medium leading-relaxed italic text-balance">
                    "{testimonials[currentIndex].quote}"
                  </blockquote>

                  {/* Author profile */}
                  <div className="flex items-center justify-between border-t border-neutral-100 pt-6 mt-2">
                    <div className="flex flex-col leading-none">
                      <cite className="not-italic text-base font-bold text-brand-text">
                        {testimonials[currentIndex].name}
                      </cite>
                      <span className="text-xs text-brand-muted mt-1.5 font-semibold">
                        {testimonials[currentIndex].location}
                      </span>
                    </div>

                    <span className="px-3.5 py-1.5 text-[9px] font-extrabold uppercase tracking-widest bg-emerald-50 text-primary rounded-full border border-emerald-100/50">
                      {testimonials[currentIndex].treatment}
                    </span>
                  </div>

                </div>
              </div>
            </motion.div>
          </AnimatePresence>

          {/* Navigation Controls on Desktop/Sides */}
          <div className="absolute left-[-20px] sm:left-[-60px] top-1/2 -translate-y-1/2 z-20">
            <button
              onClick={handlePrev}
              className="w-11 h-11 rounded-full bg-white border border-neutral-200 shadow-sm flex items-center justify-center text-brand-muted hover:text-primary hover:border-primary transition-all duration-300 hover:scale-105 active:scale-95"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
          </div>
          <div className="absolute right-[-20px] sm:right-[-60px] top-1/2 -translate-y-1/2 z-20">
            <button
              onClick={handleNext}
              className="w-11 h-11 rounded-full bg-white border border-neutral-200 shadow-sm flex items-center justify-center text-brand-muted hover:text-primary hover:border-primary transition-all duration-300 hover:scale-105 active:scale-95"
            >
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>

        </div>

        {/* Bullet Progress Indicator Dots */}
        <div className="flex justify-center gap-2.5 mt-8">
          {testimonials.map((_, index) => (
            <button
              key={index}
              onClick={() => setCurrentIndex(index)}
              className={`w-2.5 h-2.5 rounded-full transition-all duration-300 ${
                currentIndex === index ? "bg-primary w-6" : "bg-neutral-200"
              }`}
            />
          ))}
        </div>

      </div>
    </section>
  );
}
