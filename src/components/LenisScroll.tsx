"use client";

import React from "react";
import { ReactLenis } from "@studio-freight/react-lenis";

interface LenisScrollProps {
  children: React.ReactNode;
}

export default function LenisScroll({ children }: LenisScrollProps) {
  return (
    <ReactLenis
      root
      options={{
        duration: 1.2,
        lerp: 0.08,
        easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)), // Apple-like easing curve
        wheelMultiplier: 1.1,
        touchMultiplier: 1.5,
      }}
    >
      {children as any}
    </ReactLenis>
  );
}
