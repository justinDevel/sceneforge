import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Sparkles, 
  Wand2, 
  Camera, 
  Sun, 
  Palette, 
  Layers,
  Shuffle,
  ChevronDown,
  Code2
} from 'lucide-react';
import { useAppStore, FrameParams } from '@/stores/appStore';
import { useGenerator } from '@/hooks/useGenerator';
import { 
  genreOptions, 
  cameraAngles, 
  compositions, 
  defaultParams,
  samplePrompts,
  paramsToJson
} from '@/api/mockData';
import { GenerationProgress } from './GenerationProgress';

export const SceneForm = () => {
  const [prompt, setPrompt] = useState('');
  const [genre, setGenre] = useState('noir');
  const [params, setParams] = useState<FrameParams>(defaultParams);
  const [showJson, setShowJson] = useState(false);
  const [isSurprising, setIsSurprising] = useState(false);
  
  const { currentProject, setCurrentProject, addProject } = useAppStore();
  const { generate, isGenerating, generationProgress } = useGenerator();

  const handleSurpriseMe = useCallback(async () => {
    const { demoMode } = useAppStore.getState();
    setIsSurprising(true);
    
    try {
      if (demoMode) {
        
        await new Promise(resolve => setTimeout(resolve, 800));
        const randomPrompt = samplePrompts[Math.floor(Math.random() * samplePrompts.length)];
        setPrompt(randomPrompt);
        setGenre(genreOptions[Math.floor(Math.random() * genreOptions.length)].value);
        setParams({
          ...params,
          fov: 24 + Math.floor(Math.random() * 96),
          lighting: 30 + Math.floor(Math.random() * 70),
          hdrBloom: 10 + Math.floor(Math.random() * 60),
        });
      } else {
        
        try {
          const response = await fetch('http://localhost:8000/api/v1/generation/surprise-me', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
              current_genre: genre,
              style_preference: 'cinematic'
            }),
          });

          if (response.ok) {
            const result = await response.json();
            setPrompt(result.scene_description);
            setGenre(result.genre);
            setParams({
              ...params,
              ...result.suggested_params,
            });
          } else {
            
            const randomPrompt = samplePrompts[Math.floor(Math.random() * samplePrompts.length)];
            setPrompt(randomPrompt);
            setGenre(genreOptions[Math.floor(Math.random() * genreOptions.length)].value);
          }
        } catch (error) {
          console.error('Surprise Me API failed:', error);
          
          const randomPrompt = samplePrompts[Math.floor(Math.random() * samplePrompts.length)];
          setPrompt(randomPrompt);
          setGenre(genreOptions[Math.floor(Math.random() * genreOptions.length)].value);
        }
      }
    } finally {
      setIsSurprising(false);
    }
  }, [params, genre]);

  const handleGenerate = async () => {
    if (!prompt.trim()) return;

    
    if (!currentProject) {
      const newProject = {
        id: `project-${Date.now()}`,
        name: prompt.slice(0, 50),
        description: prompt,
        genre,
        frames: [],
        createdAt: Date.now(),
        updatedAt: Date.now(),
      };
      addProject(newProject);
      setCurrentProject(newProject);
    }

    await generate(prompt, params, genre);
  };

  const updateParam = <K extends keyof FrameParams>(key: K, value: FrameParams[K]) => {
    setParams((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <div className="w-full max-w-4xl mx-auto">
      <AnimatePresence mode="wait">
        {isGenerating && generationProgress ? (
          <GenerationProgress
            currentStep={generationProgress.step}
            message={generationProgress.message}
            isComplete={generationProgress.isComplete}
          />
        ) : (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-6"
          >
            {/* Main Input */}
            <div className="glass-panel p-6 space-y-4">
              <div className="flex items-center justify-between">
                <Label className="text-lg font-semibold flex items-center gap-2">
                  <Wand2 className="w-5 h-5 text-primary" />
                  Scene Description
                </Label>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleSurpriseMe}
                  disabled={isSurprising}
                  className="gap-2 border-primary/30 hover:border-primary hover:bg-primary/10"
                >
                  {isSurprising ? (
                    <>
                      <Sparkles className="w-4 h-4 animate-spin" />
                      Surprising...
                    </>
                  ) : (
                    <>
                      <Shuffle className="w-4 h-4" />
                      Surprise Me
                    </>
                  )}
                </Button>
              </div>
              
              <div className="relative">
                <Textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="Describe your scene in vivid detail... e.g., 'A tense noir chase through rainy neon streets at midnight'"
                  className={`min-h-[120px] bg-muted/30 border-border/50 focus:border-primary resize-none text-lg ${
                    isSurprising ? 'animate-pulse' : ''
                  }`}
                  disabled={isSurprising}
                />
                {isSurprising && (
                  <div className="absolute inset-0 flex items-center justify-center bg-background/50 backdrop-blur-sm rounded-md">
                    <div className="flex items-center gap-2 text-primary">
                      <Sparkles className="w-5 h-5 animate-spin" />
                      <span className="text-sm font-medium">Generating creative prompt...</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Genre Select */}
              <div className="flex items-center gap-4">
                <Label className="text-sm text-muted-foreground">Genre:</Label>
                <Select value={genre} onValueChange={setGenre}>
                  <SelectTrigger className="w-48 bg-muted/30 border-border/50">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-card border-border">
                    {genreOptions.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        <span className="flex items-center gap-2">
                          <span>{option.icon}</span>
                          <span>{option.label}</span>
                        </span>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Parameters */}
            <div className="glass-panel p-6">
              <Tabs defaultValue="camera" className="w-full">
                <TabsList className="grid grid-cols-4 gap-2 bg-muted/30 p-1">
                  <TabsTrigger value="camera" className="gap-2 data-[state=active]:bg-primary/20">
                    <Camera className="w-4 h-4" />
                    <span className="hidden sm:inline">Camera</span>
                  </TabsTrigger>
                  <TabsTrigger value="lighting" className="gap-2 data-[state=active]:bg-primary/20">
                    <Sun className="w-4 h-4" />
                    <span className="hidden sm:inline">Lighting</span>
                  </TabsTrigger>
                  <TabsTrigger value="color" className="gap-2 data-[state=active]:bg-primary/20">
                    <Palette className="w-4 h-4" />
                    <span className="hidden sm:inline">Color</span>
                  </TabsTrigger>
                  <TabsTrigger value="composition" className="gap-2 data-[state=active]:bg-primary/20">
                    <Layers className="w-4 h-4" />
                    <span className="hidden sm:inline">Composition</span>
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="camera" className="mt-6 space-y-6">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <Label>Field of View</Label>
                      <span className="text-sm font-mono text-primary">{params.fov}°</span>
                    </div>
                    <Slider
                      value={[params.fov]}
                      onValueChange={([v]) => updateParam('fov', v)}
                      min={24}
                      max={120}
                      step={1}
                      className="slider-neon"
                    />
                    <div className="flex justify-between text-xs text-muted-foreground">
                      <span>24° (Telephoto)</span>
                      <span>120° (Ultra Wide)</span>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <Label>Camera Angle</Label>
                    <Select
                      value={params.cameraAngle}
                      onValueChange={(v) => updateParam('cameraAngle', v)}
                    >
                      <SelectTrigger className="bg-muted/30 border-border/50">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-card border-border">
                        {cameraAngles.map((angle) => (
                          <SelectItem key={angle.value} value={angle.value}>
                            {angle.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </TabsContent>

                <TabsContent value="lighting" className="mt-6 space-y-6">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <Label>Intensity</Label>
                      <span className="text-sm font-mono text-primary">{params.lighting}%</span>
                    </div>
                    <Slider
                      value={[params.lighting]}
                      onValueChange={([v]) => updateParam('lighting', v)}
                      min={0}
                      max={100}
                      step={1}
                      className="slider-neon"
                    />
                  </div>

                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <Label>HDR Bloom</Label>
                      <span className="text-sm font-mono text-secondary">{params.hdrBloom}%</span>
                    </div>
                    <Slider
                      value={[params.hdrBloom]}
                      onValueChange={([v]) => updateParam('hdrBloom', v)}
                      min={0}
                      max={100}
                      step={1}
                      className="slider-neon"
                    />
                  </div>
                </TabsContent>

                <TabsContent value="color" className="mt-6 space-y-6">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <Label>Color Temperature</Label>
                      <span className="text-sm font-mono text-accent">{params.colorTemp}K</span>
                    </div>
                    <Slider
                      value={[params.colorTemp]}
                      onValueChange={([v]) => updateParam('colorTemp', v)}
                      min={2700}
                      max={10000}
                      step={100}
                      className="slider-neon"
                    />
                    <div className="flex justify-between text-xs text-muted-foreground">
                      <span>🔥 Warm (2700K)</span>
                      <span>❄️ Cool (10000K)</span>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <Label>Contrast</Label>
                      <span className="text-sm font-mono text-primary">{params.contrast}%</span>
                    </div>
                    <Slider
                      value={[params.contrast]}
                      onValueChange={([v]) => updateParam('contrast', v)}
                      min={0}
                      max={100}
                      step={1}
                      className="slider-neon"
                    />
                  </div>
                </TabsContent>

                <TabsContent value="composition" className="mt-6 space-y-6">
                  <div className="space-y-3">
                    <Label>Composition Rule</Label>
                    <Select
                      value={params.composition}
                      onValueChange={(v) => updateParam('composition', v)}
                    >
                      <SelectTrigger className="bg-muted/30 border-border/50">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-card border-border">
                        {compositions.map((comp) => (
                          <SelectItem key={comp.value} value={comp.value}>
                            {comp.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </TabsContent>
              </Tabs>
            </div>

            {/* JSON Preview Toggle */}
            <motion.div 
              className="glass-panel overflow-hidden"
              animate={{ height: showJson ? 'auto' : '56px' }}
            >
              <button
                onClick={() => setShowJson(!showJson)}
                className="w-full px-6 py-4 flex items-center justify-between hover:bg-muted/20 transition-colors"
              >
                <span className="flex items-center gap-2 text-sm font-medium">
                  <Code2 className="w-4 h-4 text-primary" />
                  JSON Preview
                </span>
                <ChevronDown
                  className={`w-4 h-4 transition-transform ${showJson ? 'rotate-180' : ''}`}
                />
              </button>
              
              <AnimatePresence>
                {showJson && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="px-6 pb-6"
                  >
                    <pre className="json-editor text-xs overflow-x-auto">
                      <code>
                        {JSON.stringify(paramsToJson(params), null, 2)}
                      </code>
                    </pre>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>

            {/* Generate Button */}
            <motion.div
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.99 }}
            >
              <Button
                onClick={handleGenerate}
                disabled={!prompt.trim() || isGenerating}
                className="w-full h-14 text-lg font-semibold bg-neon-gradient hover:opacity-90 transition-opacity gap-3"
              >
                <Sparkles className="w-5 h-5" />
                Generate Storyboard
              </Button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
