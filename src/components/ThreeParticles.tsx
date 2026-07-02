"use client";

import React, { useEffect, useRef } from "react";
import * as THREE from "three";

export default function ThreeParticles() {
  const containerRef = useRef<HTMLDivElement>(null);
  const mouseRef = useRef({ x: 0, y: 0 });

  useEffect(() => {
    if (!containerRef.current) return;

    const container = containerRef.current;
    
    // 1. Scene setup
    const scene = new THREE.Scene();
    
    // 2. Camera setup
    const camera = new THREE.PerspectiveCamera(
      60,
      container.clientWidth / container.clientHeight,
      0.1,
      100
    );
    camera.position.z = 30;

    // 3. Renderer setup
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    // 4. Create Particles
    const particleCount = 120;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);
    const sizes = new Float32Array(particleCount);
    const speeds = new Float32Array(particleCount);
    const shifts = new Float32Array(particleCount);

    const colorGreen = new THREE.Color("#66BB6A"); // Accent Green
    const colorGold = new THREE.Color("#F9A825"); // Secondary Gold
    const colorPrimary = new THREE.Color("#2E7D32"); // Primary Green
    const colorPalette = [colorGreen, colorGold, colorPrimary];

    for (let i = 0; i < particleCount; i++) {
      // Random coordinates within a box
      positions[i * 3] = (Math.random() - 0.5) * 60;     // X
      positions[i * 3 + 1] = (Math.random() - 0.5) * 60; // Y
      positions[i * 3 + 2] = (Math.random() - 0.5) * 40; // Z

      // Random color from brand palette
      const randColor = colorPalette[Math.floor(Math.random() * colorPalette.length)];
      colors[i * 3] = randColor.r;
      colors[i * 3 + 1] = randColor.g;
      colors[i * 3 + 2] = randColor.b;

      // Particle size & motion variables
      sizes[i] = Math.random() * 0.4 + 0.1;
      speeds[i] = Math.random() * 0.05 + 0.01;
      shifts[i] = Math.random() * Math.PI * 2;
    }

    geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));

    // Particle texture (drawn dynamically on canvas for circular glow)
    const createCircleTexture = () => {
      const canvas = document.createElement("canvas");
      canvas.width = 16;
      canvas.height = 16;
      const ctx = canvas.getContext("2d");
      if (ctx) {
        const gradient = ctx.createRadialGradient(8, 8, 0, 8, 8, 8);
        gradient.addColorStop(0, "rgba(255, 255, 255, 1)");
        gradient.addColorStop(0.3, "rgba(255, 255, 255, 0.8)");
        gradient.addColorStop(1, "rgba(255, 255, 255, 0)");
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, 16, 16);
      }
      return new THREE.CanvasTexture(canvas);
    };

    const material = new THREE.PointsMaterial({
      size: 1.5,
      sizeAttenuation: true,
      vertexColors: true,
      transparent: true,
      opacity: 0.7,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      map: createCircleTexture(),
    });

    const particles = new THREE.Points(geometry, material);
    scene.add(particles);

    // 5. Interaction
    const handleMouseMove = (event: MouseEvent) => {
      // Normalize mouse positions
      mouseRef.current.x = (event.clientX / window.innerWidth) - 0.5;
      mouseRef.current.y = (event.clientY / window.innerHeight) - 0.5;
    };

    window.addEventListener("mousemove", handleMouseMove);

    // 6. Handle resizing
    const handleResize = () => {
      if (!container) return;
      camera.aspect = container.clientWidth / container.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(container.clientWidth, container.clientHeight);
    };

    window.addEventListener("resize", handleResize);

    // 7. Animation Loop
    let animationFrameId: number;
    let clock = new THREE.Clock();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      const elapsedTime = clock.getElapsedTime();

      // Read current positions
      const positionAttr = geometry.getAttribute("position") as THREE.BufferAttribute;
      const posArray = positionAttr.array as Float32Array;

      for (let i = 0; i < particleCount; i++) {
        // Move particles upwards
        posArray[i * 3 + 1] += speeds[i]; // Increment Y coordinate

        // Apply a gentle sway based on sine wave
        posArray[i * 3] += Math.sin(elapsedTime * 0.5 + shifts[i]) * 0.01;

        // If particle goes above threshold, reset it to the bottom
        if (posArray[i * 3 + 1] > 30) {
          posArray[i * 3 + 1] = -30;
          posArray[i * 3] = (Math.random() - 0.5) * 60;
        }
      }
      positionAttr.needsUpdate = true;

      // Mouse parallax rotation (soft easing)
      particles.rotation.y += (mouseRef.current.x * 0.15 - particles.rotation.y) * 0.05;
      particles.rotation.x += (mouseRef.current.y * 0.15 - particles.rotation.x) * 0.05;

      renderer.render(scene, camera);
    };

    animate();

    // 8. Cleanup
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("resize", handleResize);
      cancelAnimationFrame(animationFrameId);
      
      // Dispose materials/geometry to prevent memory leaks
      geometry.dispose();
      material.dispose();
      renderer.dispose();
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, []);

  return (
    <div
      ref={containerRef}
      className="absolute inset-0 pointer-events-none z-[1] overflow-hidden"
      style={{ mixBlendMode: "multiply" }}
    />
  );
}
