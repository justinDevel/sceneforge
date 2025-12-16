import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { ParticlesBackground } from '@/components/ParticlesBackground';
import { TypewriterText } from '@/components/TypewriterText';
import { DemoModeToggle } from '@/components/DemoModeToggle';
import { useAppStore } from '@/stores/appStore';
import { 
  Sparkles, 
  ArrowRight, 
  Film, 
  Zap, 
  Layers, 
  Camera,
  Play
} from 'lucide-react';

const heroTexts = [
  "Transform scripts into cinematic storyboards",
  "AI-powered pre-visualization for filmmakers",
  "From concept to production-ready frames",
  "Deterministic JSON control for VFX pipelines",
];

const features = [
  {
    icon: Camera,
    title: 'Precise Camera Control',
    description: 'FOV, angles, and composition with deterministic JSON parameters',
    color: 'text-primary',
  },
  {
    icon: Zap,
    title: '16-bit HDR Output',
    description: 'Enterprise-grade EXR sequences ready for VFX pipelines',
    color: 'text-secondary',
  },
  {
    icon: Layers,
    title: 'Agentic Pipeline',
    description: 'Automated scene breakdown and intelligent frame generation',
    color: 'text-accent',
  },
];

export const HeroSection = () => {
  const { demoMode, setCurrentProject } = useAppStore();

  const handleGetStarted = () => {
    
    setCurrentProject(null);
  };

  return (
    <section className="relative min-h-screen flex flex-col">
      <ParticlesBackground />
      
      {/* Header */}
      <header className="relative z-10 flex items-center justify-between px-6 py-4 lg:px-12">
        <motion.div 
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="flex items-center gap-3"
        >
          <div className="w-10 h-10 rounded-lg bg-neon-gradient flex items-center justify-center">
            <Film className="w-5 h-5 text-primary-foreground" />
          </div>
          <span className="text-xl font-bold gradient-text">SceneForge</span>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="flex items-center gap-4"
        >
          <DemoModeToggle />
        </motion.div>
      </header>

      {/* Hero Content */}
      <div className="relative z-10 flex-1 flex items-center justify-center px-6 py-12">
        <div className="max-w-5xl mx-auto text-center space-y-8">
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass-panel text-sm">
              <Sparkles className="w-4 h-4 text-primary" />
              <span className="text-muted-foreground">Powered by FIBO AI</span>
              <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
            </span>
          </motion.div>

          {/* Main Heading */}
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="text-4xl md:text-6xl lg:text-7xl font-bold leading-tight"
          >
            <span className="text-foreground">Revolutionize</span>
            <br />
            <span className="gradient-text">Pre-Visualization</span>
            <br />
            <span className="text-foreground">with AI</span>
          </motion.h1>

          {/* Typewriter Subtitle */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto"
          >
            <TypewriterText 
              texts={heroTexts}
              className="text-muted-foreground"
              speed={40}
            />
          </motion.div>

          {/* CTA Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            <Link to="/generator" onClick={handleGetStarted}>
              <Button variant="hero" size="xl" className="gap-3">
                <Sparkles className="w-5 h-5" />
                Start Creating
                <ArrowRight className="w-5 h-5" />
              </Button>
            </Link>
            <Button variant="glass" size="lg" className="gap-2">
              <Play className="w-4 h-4" />
              Watch Demo
            </Button>
          </motion.div>

          {/* Demo Mode Indicator */}
          {demoMode && (
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5 }}
              className="text-sm text-muted-foreground"
            >
              Demo mode active - experience all features with mock data
            </motion.p>
          )}
        </div>
      </div>

      {/* Features Grid */}
      <div className="relative z-10 px-6 pb-16 lg:px-12">
        <div className="max-w-5xl mx-auto grid md:grid-cols-3 gap-6">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 + index * 0.1 }}
              whileHover={{ y: -5 }}
              className="glass-panel p-6 group cursor-default"
            >
              <feature.icon className={`w-8 h-8 ${feature.color} mb-4 group-hover:scale-110 transition-transform`} />
              <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
              <p className="text-sm text-muted-foreground">{feature.description}</p>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Gradient fade at bottom */}
      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-background to-transparent pointer-events-none" />
    </section>
  );
};
