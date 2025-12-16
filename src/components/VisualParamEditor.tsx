import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Camera, 
  Sun, 
  Palette, 
  Layers,
  RotateCcw,
  Save
} from 'lucide-react';
import { FrameParams } from '@/stores/appStore';
import { cameraAngles, compositions } from '@/api/mockData';

interface VisualParamEditorProps {
  params: FrameParams;
  onChange: (params: FrameParams) => void;
  onSave?: () => void;
  onReset?: () => void;
}

export const VisualParamEditor = ({
  params,
  onChange,
  onSave,
  onReset,
}: VisualParamEditorProps) => {
  const [localParams, setLocalParams] = useState<FrameParams>(params);
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    setLocalParams(params);
    setHasChanges(false);
  }, [params]);

  const updateParam = <K extends keyof FrameParams>(key: K, value: FrameParams[K]) => {
    const newParams = { ...localParams, [key]: value };
    setLocalParams(newParams);
    setHasChanges(true);
    onChange(newParams);
  };

  const handleSave = () => {
    if (onSave) {
      onSave();
      setHasChanges(false);
    }
  };

  const handleReset = () => {
    setLocalParams(params);
    onChange(params);
    setHasChanges(false);
    if (onReset) {
      onReset();
    }
  };

  return (
    <div className="glass-panel p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold gradient-text">Visual Parameters</h3>
        <div className="flex items-center gap-2">
          {hasChanges && (
            <motion.span
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              className="text-xs text-primary font-medium"
            >
              Unsaved changes
            </motion.span>
          )}
          <Button
            size="sm"
            variant="outline"
            onClick={handleReset}
            disabled={!hasChanges}
            className="gap-2 border-border/50"
          >
            <RotateCcw className="w-3 h-3" />
            Reset
          </Button>
          {onSave && (
            <Button
              size="sm"
              onClick={handleSave}
              disabled={!hasChanges}
              className="gap-2 bg-primary hover:bg-primary/90"
            >
              <Save className="w-3 h-3" />
              Apply
            </Button>
          )}
        </div>
      </div>

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
              <span className="text-sm font-mono text-primary">{localParams.fov}°</span>
            </div>
            <Slider
              value={[localParams.fov]}
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
              value={localParams.cameraAngle}
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
              <span className="text-sm font-mono text-primary">{localParams.lighting}%</span>
            </div>
            <Slider
              value={[localParams.lighting]}
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
              <span className="text-sm font-mono text-secondary">{localParams.hdrBloom}%</span>
            </div>
            <Slider
              value={[localParams.hdrBloom]}
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
              <span className="text-sm font-mono text-accent">{localParams.colorTemp}K</span>
            </div>
            <Slider
              value={[localParams.colorTemp]}
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
              <span className="text-sm font-mono text-primary">{localParams.contrast}%</span>
            </div>
            <Slider
              value={[localParams.contrast]}
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
              value={localParams.composition}
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

      {/* Parameter Summary */}
      <div className="pt-4 border-t border-border/50">
        <div className="grid grid-cols-2 gap-3 text-xs">
          <div className="flex justify-between">
            <span className="text-muted-foreground">FOV:</span>
            <span className="font-mono text-primary">{localParams.fov}°</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Lighting:</span>
            <span className="font-mono text-primary">{localParams.lighting}%</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">HDR Bloom:</span>
            <span className="font-mono text-secondary">{localParams.hdrBloom}%</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Color Temp:</span>
            <span className="font-mono text-accent">{localParams.colorTemp}K</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Contrast:</span>
            <span className="font-mono text-primary">{localParams.contrast}%</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Angle:</span>
            <span className="font-mono text-primary text-xs truncate">
              {cameraAngles.find(a => a.value === localParams.cameraAngle)?.label}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
