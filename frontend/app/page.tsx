"use client";
import "@/components/landing/landing.css";
import { Channels } from "@/components/landing/channels";
import { Hero, Navbar } from "@/components/landing/hero";
import { useReveal } from "@/components/landing/hooks";
import { BrandVoice, FinalCTA, Footer, HowItWorks, OneToMany, VideoShowcase } from "@/components/landing/more";
import { Studio } from "@/components/landing/studio";
import { Transformation } from "@/components/landing/transformation";

export default function Home() {
  useReveal();
  return (
    <div className="lp">
      <a href="#studio" className="sr-only focus:not-sr-only focus:fixed focus:left-3 focus:top-3 focus:z-[60] focus:rounded-full focus:bg-[var(--lime)] focus:px-4 focus:py-2 focus:text-[var(--lime-ink)]">Skip to the studio</a>
      <Navbar />
      <main>
        <Hero />
        <Transformation />
        <Studio />
        <Channels />
        <VideoShowcase />
        <OneToMany />
        <BrandVoice />
        <HowItWorks />
        <FinalCTA />
      </main>
      <Footer />
    </div>
  );
}
