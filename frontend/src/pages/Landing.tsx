import { HUDNav } from '../components/ui/HUDNav';
import { ScrollSections } from '../components/ui/ScrollSections';
import { PostFX } from '../components/effects/PostFX';
import { useScrollProgress } from '../hooks/useScrollProgress';
import { Scene } from '../components/3d/Scene';

export function Landing() {
  const { progress, velocity } = useScrollProgress();

  return (
    <div style={{ position: 'relative', height: '400vh', background: 'var(--obsidian)' }}>
      {/* 3D Scene */}
      <Scene scrollProgress={progress} />



      {/* CSS postprocessing: vignette + chromatic aberration */}
      <PostFX scrollVelocity={velocity} />

      {/* Fixed glassmorphism nav */}
      <HUDNav />

      {/* Scroll-linked HTML sections */}
      <ScrollSections scrollProgress={progress} />
    </div>
  );
}
