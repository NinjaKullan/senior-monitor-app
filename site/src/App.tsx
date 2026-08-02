import { Hero } from "@/sections/Hero";
import { Scenarios } from "@/sections/Scenarios";
import { KettleStory } from "@/sections/KettleStory";
import { ThreeFields } from "@/sections/ThreeFields";
import { HowItWorks } from "@/sections/HowItWorks";
import { Waitlist } from "@/sections/Waitlist";
import { Footer } from "@/sections/Footer";

/**
 * The landing page, top to bottom (spec 006 §3).
 *
 * One idea per viewport, beats far apart, and nothing between them. There is no
 * router: this is one page plus a static privacy placeholder, and adding a
 * router would be adding a thing to go wrong on the only page anyone sees.
 */
export default function App() {
  return (
    <main className="bg-canvas font-sans text-ink">
      <Hero />
      <Scenarios />
      <KettleStory />
      <ThreeFields />
      <HowItWorks />
      <Waitlist />
      <Footer />
    </main>
  );
}
