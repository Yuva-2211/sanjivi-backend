import React from "react";
import Image from "next/image";

interface LogoProps {
  className?: string;
  showText?: boolean;
  light?: boolean;
}

export default function SanjiviLogo({ className = "", showText = true, light = false }: LogoProps) {
  return (
    <div className={`flex items-center gap-3 select-none ${className}`}>
      {/* Official Image-based Lotus Emblem */}
      <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-white shadow-sm border border-neutral-100 overflow-hidden shrink-0">
        <Image
          src="/images/sanjivi_emblem.jpg"
          alt="Sanjivi Lotus Emblem"
          width={36}
          height={36}
          className="object-contain"
          priority
        />
      </div>

      {/* Brand Text */}
      {showText && (
        <div className="flex flex-col leading-none">
          <span
            className={`font-black tracking-wide text-lg ${
              light ? "text-white" : "text-primary"
            }`}
            style={{ fontFamily: "var(--font-roboto)" }}
          >
            Sanjivi
          </span>
          <span
            className={`font-extrabold tracking-widest text-[8px] mt-0.5 ${
              light ? "text-emerald-300" : "text-gold"
            }`}
          >
            AYUSH HEALTHCARE
          </span>
        </div>
      )}
    </div>
  );
}
