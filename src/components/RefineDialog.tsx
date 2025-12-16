import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Sparkles, Loader2, AlertCircle } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { Frame } from '@/stores/appStore';

interface RefineDialogProps {
  frame: Frame;
  frameIndex: number;
  isOpen: boolean;
  onClose: () => void;
  onRefine: (frameId: string, refinementPrompt: string) => Promise<void>;
}

export const RefineDialog = ({
  frame,
  frameIndex,
  isOpen,
  onClose,
  onRefine,
}: RefineDialogProps) => {
  const [refinementPrompt, setRefinementPrompt] = useState('');
  const [isRefining, setIsRefining] = useState(false);
  const { toast } = useToast();

  const handleRefine = async () => {
    if (!refinementPrompt.trim()) {
      toast({
        title: 'Refinement prompt required',
        description: 'Please describe how you want to refine this frame.',
        variant: 'destructive',
      });
      return;
    }

    setIsRefining(true);

    try {
      
      await onRefine(frame.id, refinementPrompt);
      
      toast({
        title: 'Frame Refined!',
        description: 'Your frame has been successfully refined and updated.',
      });
      
      setRefinementPrompt('');
      
      
      setTimeout(() => {
        onClose();
      }, 300);
    } catch (error) {
      console.error('Refinement failed:', error);
      toast({
        title: 'Refinement Failed',
        description: error instanceof Error ? error.message : 'Could not refine frame. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setIsRefining(false);
    }
  };

  const suggestionPrompts = [
    'Make the lighting more dramatic and volumetric',
    'Increase the HDR bloom for a more cinematic look',
    'Change the camera angle to low-angle for more impact',
    'Add more contrast and deeper shadows',
    'Make the colors warmer and more inviting',
    'Adjust the composition to follow the golden ratio',
  ];

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[600px] max-h-[90vh] bg-card border-border flex flex-col">
        <DialogHeader className="flex-shrink-0">
          <DialogTitle className="text-xl gradient-text flex items-center gap-2">
            <Sparkles className="w-5 h-5" />
            Refine Frame #{frameIndex + 1}
          </DialogTitle>
          <DialogDescription>
            Describe how you want to improve this frame. The AI will use Bria's V2 API to refine the image while maintaining consistency.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4 overflow-y-auto flex-1">
          {/* Current Frame Preview */}
          <div className="space-y-2">
            <Label className="text-sm text-muted-foreground">Current Frame</Label>
            <div className="relative aspect-video rounded-lg overflow-hidden border border-border/50 bg-muted/20">
              <img
                src={
                  frame.imageUrl === '/placeholder.svg'
                    ? '/placeholder.svg'
                    : frame.imageUrl.startsWith('/uploads/')
                    ? `http://localhost:8000${frame.imageUrl}`
                    : frame.imageUrl
                }
                alt={`Frame ${frameIndex + 1}`}
                className="w-full h-full object-cover"
              />
            </div>
            <p className="text-xs text-muted-foreground line-clamp-1">
              {frame.prompt}
            </p>
          </div>

          {/* Refinement Prompt */}
          <div className="space-y-2">
            <Label htmlFor="refinement-prompt">Refinement Instructions</Label>
            <Textarea
              id="refinement-prompt"
              value={refinementPrompt}
              onChange={(e) => setRefinementPrompt(e.target.value)}
              placeholder="e.g., Make the lighting more volumetric, increase HDR bloom..."
              className="min-h-[80px] bg-muted/30 border-border/50 focus:border-primary resize-none"
              disabled={isRefining}
            />
          </div>

          {/* Quick Suggestions */}
          <div className="space-y-2">
            <Label className="text-sm text-muted-foreground">Quick Suggestions</Label>
            <div className="flex flex-wrap gap-2">
              {suggestionPrompts.slice(0, 4).map((suggestion, index) => (
                <Button
                  key={index}
                  variant="outline"
                  size="sm"
                  onClick={() => setRefinementPrompt(suggestion)}
                  disabled={isRefining}
                  className="text-xs border-border/50 hover:border-primary hover:bg-primary/10"
                >
                  {suggestion}
                </Button>
              ))}
            </div>
          </div>

          {/* Info Box */}
          <div className="flex items-start gap-2 p-3 rounded-lg bg-primary/10 border border-primary/20">
            <AlertCircle className="w-4 h-4 text-primary flex-shrink-0 mt-0.5" />
            <p className="text-xs text-muted-foreground">
              Uses Bria V2 API to refine while maintaining consistency
            </p>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-end gap-3 pt-3 border-t border-border/50 flex-shrink-0">
          <Button
            variant="outline"
            onClick={onClose}
            disabled={isRefining}
            className="border-border/50"
          >
            Cancel
          </Button>
          <Button
            onClick={handleRefine}
            disabled={!refinementPrompt.trim() || isRefining}
            className="gap-2 bg-neon-gradient hover:opacity-90"
          >
            {isRefining ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Refining...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                Refine Frame
              </>
            )}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};
