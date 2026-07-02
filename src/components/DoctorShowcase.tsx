"use client";

import React, { useRef } from "react";
import { motion } from "framer-motion";
import Image from "next/image";
import { ArrowLeft, ArrowRight, Award, Star, Heart } from "lucide-react";

interface Doctor {
  name: string;
  specialty: string;
  degree: string;
  experience: string;
  rating: string;
  image: string;
  badgeColor: string;
}

export default function DoctorShowcase() {
  const scrollRef = useRef<HTMLDivElement>(null);

  const doctors: Doctor[] = [
    {
      name: "Dr. Sanjivi Kumar",
      specialty: "Senior Ayurvedic Physician",
      degree: "BAMS, MD (Ayurveda)",
      experience: "18+ Yrs Experience",
      rating: "4.9",
      image: "/images/doctor_male.png",
      badgeColor: "bg-emerald-500 text-white",
    },
    {
      name: "Dr. Anjali Sharma",
      specialty: "Yoga & Naturopathy Expert",
      degree: "DNYS, MS (Yoga Therapy)",
      experience: "12+ Yrs Experience",
      rating: "4.8",
      image: "/images/doctor_consultation.png", // Cropped circular focus
      badgeColor: "bg-amber-500 text-brand-text",
    },
    {
      name: "Dr. Tariq Mahmood",
      specialty: "Unani Medicine Specialist",
      degree: "BUMS, MD (Unani)",
      experience: "15+ Yrs Experience",
      rating: "4.9",
      image: "/images/doctor_male.png", // Reused with styling variations
      badgeColor: "bg-yellow-600 text-white",
    },
    {
      name: "Dr. Meenakshi Pillai",
      specialty: "Siddha Practitioner",
      degree: "BSMS (Siddha)",
      experience: "14+ Yrs Experience",
      rating: "4.7",
      image: "/images/doctor_consultation.png",
      badgeColor: "bg-teal-500 text-white",
    },
    {
      name: "Dr. Sarah Joseph",
      specialty: "Homeopathy Consultant",
      degree: "BHMS, MD (Homeopathy)",
      experience: "11+ Yrs Experience",
      rating: "4.8",
      image: "/images/doctor_consultation.png",
      badgeColor: "bg-indigo-500 text-white",
    },
  ];

  const scroll = (direction: "left" | "right") => {
    if (scrollRef.current) {
      const { scrollLeft, clientWidth } = scrollRef.current;
      const scrollTo = direction === "left" ? scrollLeft - 320 : scrollLeft + 320;
      scrollRef.current.scrollTo({ left: scrollTo, behavior: "smooth" });
    }
  };

  return (
    <section
      id="doctors"
      className="relative py-24 px-4 md:px-8 lg:px-16 bg-brand-bg overflow-hidden"
    >
      <div className="w-full max-w-7xl mx-auto z-10 relative">
        
        {/* Section Header */}
        <div className="flex flex-col md:flex-row items-start md:items-end justify-between mb-16 gap-8">
          <div>
            <span className="text-[11px] font-extrabold uppercase tracking-widest text-primary bg-emerald-50 px-4 py-2 rounded-full border border-emerald-100/40">
              Our Experts
            </span>
            <h2 className="text-3xl md:text-5xl font-black text-brand-text tracking-tight mt-6">
              Meet Our Certified <span className="text-primary">AYUSH Doctors</span>
            </h2>
          </div>
          
          {/* Scroll Control Buttons */}
          <div className="flex gap-4">
            <button
              onClick={() => scroll("left")}
              className="w-12 h-12 rounded-full bg-white border border-neutral-200 shadow-sm flex items-center justify-center text-brand-muted hover:text-primary hover:border-primary transition-all duration-300 hover:scale-105 active:scale-95"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <button
              onClick={() => scroll("right")}
              className="w-12 h-12 rounded-full bg-white border border-neutral-200 shadow-sm flex items-center justify-center text-brand-muted hover:text-primary hover:border-primary transition-all duration-300 hover:scale-105 active:scale-95"
            >
              <ArrowRight className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Horizontal Scroll Area */}
        <div
          ref={scrollRef}
          className="flex gap-8 overflow-x-auto pb-12 pt-4 px-2 no-scrollbar snap-x snap-mandatory"
          style={{ scrollBehavior: "smooth" }}
        >
          {doctors.map((doc, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-50px" }}
              transition={{ duration: 0.8, delay: idx * 0.05, ease: [0.22, 1, 0.36, 1] }}
              className="flex-shrink-0 w-[300px] sm:w-[320px] rounded-[28px] bg-white p-5 border border-neutral-100/70 shadow-sm hover:shadow-2xl transition-all duration-500 hover:translate-y-[-10px] relative snap-start group"
            >
              {/* Card content wrapper */}
              <div className="flex flex-col items-center">
                
                {/* Circular image with double gold ring border */}
                <div className="relative w-36 h-36 rounded-full p-1.5 border border-gold/40 group-hover:border-primary/50 transition-colors duration-500 mb-8 bg-neutral-50 overflow-hidden">
                  <div className="relative w-full h-full rounded-full overflow-hidden">
                    <Image
                      src={doc.image}
                      alt={doc.name}
                      fill
                      className="object-cover scale-105 group-hover:scale-110 transition-transform duration-700 ease-[cubic-bezier(0.22,1,0.36,1)]"
                    />
                  </div>
                  
                  {/* Heart badge (favourite icon) */}
                  <div className="absolute top-1 right-1 w-7 h-7 rounded-full bg-white border border-neutral-100 flex items-center justify-center shadow-sm text-rose-500 hover:scale-115 transition-transform">
                    <Heart className="w-4 h-4 fill-rose-500" />
                  </div>
                </div>

                {/* Rating Badge */}
                <div className="absolute top-5 left-5 flex items-center gap-1 bg-amber-50 border border-amber-100/60 rounded-full px-2.5 py-1">
                  <Star className="w-3 h-3 text-gold fill-gold" />
                  <span className="text-[10px] font-bold text-brand-text">{doc.rating}</span>
                </div>

                {/* Experience Badge on Side */}
                <span className={`absolute top-5 right-5 text-[8.5px] font-extrabold uppercase tracking-widest px-2.5 py-1 rounded-full ${doc.badgeColor}`}>
                  {doc.experience}
                </span>

                {/* Floating Glass Card Details (Overlapping structure) */}
                <div className="w-full glass-panel border border-white/50 rounded-2xl p-4 text-center mt-2 group-hover:border-primary/20 transition-all duration-500 shadow-sm">
                  <h3 className="text-lg font-bold text-brand-text group-hover:text-primary transition-colors leading-tight">
                    {doc.name}
                  </h3>
                  <p className="text-[11px] font-semibold text-primary mt-1">
                    {doc.specialty}
                  </p>
                  
                  <div className="h-px bg-neutral-200/50 my-2.5" />
                  
                  <p className="text-[10px] text-brand-muted font-bold flex items-center justify-center gap-1">
                    <Award className="w-3.5 h-3.5 text-gold" />
                    <span>{doc.degree}</span>
                  </p>
                </div>

                {/* Consultation trigger CTA */}
                <button
                  onClick={() => {
                    const target = document.querySelector("#contact");
                    if (target) target.scrollIntoView({ behavior: "smooth" });
                  }}
                  className="mt-5 w-full py-2 bg-emerald-50 hover:bg-primary border border-emerald-100 text-primary hover:text-white text-xs font-bold rounded-xl transition-all duration-300 flex items-center justify-center gap-1.5 shadow-sm group-hover:shadow-md"
                >
                  <span>Request Consult</span>
                </button>

              </div>
            </motion.div>
          ))}
        </div>

      </div>
    </section>
  );
}
