import { motion } from 'framer-motion';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { useAppStore } from '@/stores/appStore';
import { Sparkles, Zap } from 'lucide-react';

export const DemoModeToggle = () => {
  const { demoMode, setDemoMode } = useAppStore();

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-panel px-4 py-3 flex items-center gap-3"
    >
      <div className="flex items-center gap-2">
        {demoMode ? (
          <Sparkles className="w-4 h-4 text-primary" />
        ) : (
          <Zap className="w-4 h-4 text-accent" />
        )}
        <Label 
          htmlFor="demo-mode" 
          className="text-sm font-medium cursor-pointer select-none"
        >
          {demoMode ? 'Demo Mode' : 'Live Mode'}
        </Label>
      </div>
      <Switch
        id="demo-mode"
        checked={demoMode}
        onCheckedChange={setDemoMode}
        className="data-[state=checked]:bg-primary data-[state=unchecked]:bg-accent"
      />
      <span className="text-xs text-muted-foreground">
        {demoMode ? 'Using mock data' : 'Using live API'}
      </span>
    </motion.div>
  );
};
