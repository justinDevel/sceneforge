import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  horizontalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { useAppStore, Frame } from '@/stores/appStore';
import { 
  GripVertical, 
  ZoomIn, 
  Trash2, 
  MessageSquare,
  Play,
  Pause,
  SkipBack,
  SkipForward,
  Maximize2,
  Sparkles
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { RefineDialog } from './RefineDialog';
import { useToast } from '@/hooks/use-toast';

interface SortableFrameProps {
  frame: Frame;
  index: number;
  isSelected: boolean;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
  onUpdateNotes: (id: string, notes: string) => void;
  onRefine: (frame: Frame, index: number) => void;
}

const SortableFrame = ({
  frame,
  index,
  isSelected,
  onSelect,
  onDelete,
  onUpdateNotes,
  onRefine,
}: SortableFrameProps) => {
  const [isEditingNotes, setIsEditingNotes] = useState(false);
  const [notes, setNotes] = useState(frame.notes || '');

  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: frame.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  const handleSaveNotes = () => {
    onUpdateNotes(frame.id, notes);
    setIsEditingNotes(false);
  };

  console.log("frame details ::", frame.imageUrl);
  return (
    <motion.div
      ref={setNodeRef}
      style={style}
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ 
        opacity: isDragging ? 0.5 : 1, 
        scale: isDragging ? 1.05 : 1,
        zIndex: isDragging ? 10 : 1,
      }}
      className={`frame-card flex-shrink-0 w-80 h-fit ${isSelected ? 'active' : ''}`}
      onClick={() => onSelect(frame.id)}
    >
      {/* Frame number */}
      <div className="absolute top-2 left-2 z-10 px-2 py-1 rounded bg-background/80 backdrop-blur text-xs font-mono">
        #{index + 1}
      </div>

      {/* Drag handle */}
      <div
        {...attributes}
        {...listeners}
        className="absolute top-2 right-2 z-10 p-1.5 rounded bg-background/80 backdrop-blur cursor-grab hover:bg-primary/20 transition-colors"
      >
        <GripVertical className="w-4 h-4" />
      </div>

      {/* Image */}
      <div className="aspect-video relative overflow-hidden rounded-t-lg bg-muted/20">
        <img
          src={
            frame.imageUrl === '/placeholder.svg' 
              ? '/placeholder.svg'
              : frame.imageUrl.startsWith('/uploads/') 
                ? `http://localhost:8000${frame.imageUrl}` 
                : frame.imageUrl
          }
          alt={`Frame ${index + 1}`}
          className="w-full h-full object-cover transition-transform duration-300 hover:scale-105"
          loading="lazy"
          onError={(e) => {
            
            const target = e.target as HTMLImageElement;
            target.src = '/placeholder.svg';
          }}
        />
        
        {/* Loading state overlay */}
        {!frame.imageUrl || frame.imageUrl === '' ? (
          <div className="absolute inset-0 flex items-center justify-center bg-muted/50 backdrop-blur-sm">
            <div className="text-xs text-muted-foreground">Generating...</div>
          </div>
        ) : null}
        
        {/* Overlay on hover */}
        <div className="absolute inset-0 bg-gradient-to-t from-background/90 via-transparent to-transparent opacity-0 hover:opacity-100 transition-opacity flex items-end justify-center pb-3 gap-2">
          <Button 
            size="icon" 
            variant="ghost" 
            className="w-8 h-8 bg-background/50 backdrop-blur hover:bg-primary/20"
            onClick={(e) => {
              e.stopPropagation();
              onRefine(frame, index);
            }}
            title="Refine frame"
          >
            <Sparkles className="w-4 h-4" />
          </Button>
          <Button 
            size="icon" 
            variant="ghost" 
            className="w-8 h-8 bg-background/50 backdrop-blur"
            title="Zoom in"
          >
            <ZoomIn className="w-4 h-4" />
          </Button>
          <Button 
            size="icon" 
            variant="ghost" 
            className="w-8 h-8 bg-destructive/50 backdrop-blur hover:bg-destructive"
            onClick={(e) => {
              e.stopPropagation();
              onDelete(frame.id);
            }}
            title="Delete frame"
          >
            <Trash2 className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Notes section */}
      <div className="p-3 space-y-2">
        {isEditingNotes ? (
          <div className="flex gap-2">
            <Input
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add notes..."
              className="h-8 text-xs bg-muted/30"
              autoFocus
              onBlur={handleSaveNotes}
              onKeyDown={(e) => e.key === 'Enter' && handleSaveNotes()}
            />
          </div>
        ) : (
          <button
            onClick={(e) => {
              e.stopPropagation();
              setIsEditingNotes(true);
            }}
            className="w-full text-left text-xs text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1"
          >
            <MessageSquare className="w-3 h-3" />
            {frame.notes || 'Add notes...'}
          </button>
        )}

        {/* Params preview */}
        <div className="flex gap-2 text-xs font-mono text-muted-foreground">
          <span className="text-primary">FOV: {frame.params.fov.toFixed(0)}°</span>
          <span className="text-secondary">HDR: {frame.params.hdrBloom}%</span>
        </div>
      </div>
    </motion.div>
  );
};

interface StoryboardTimelineProps {
  zoom?: number;
}

export const StoryboardTimeline = ({ zoom = 1 }: StoryboardTimelineProps) => {
  const { currentProject, selectedFrameId, setSelectedFrameId, deleteFrame, updateFrame, reorderFrames, demoMode } = useAppStore();
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentFrameIndex, setCurrentFrameIndex] = useState(0);
  const [playbackSpeed] = useState(2000); 
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [refineDialogOpen, setRefineDialogOpen] = useState(false);
  const [frameToRefine, setFrameToRefine] = useState<{ frame: Frame; index: number } | null>(null);
  const { toast } = useToast();

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragEnd = useCallback(
    (event: DragEndEvent) => {
      const { active, over } = event;
      
      if (over && active.id !== over.id && currentProject) {
        const oldIndex = currentProject.frames.findIndex((f) => f.id === active.id);
        const newIndex = currentProject.frames.findIndex((f) => f.id === over.id);
        
        const newFrames = arrayMove(currentProject.frames, oldIndex, newIndex);
        reorderFrames(newFrames);
      }
    },
    [currentProject, reorderFrames]
  );

  const handleUpdateNotes = useCallback(
    (id: string, notes: string) => {
      const frame = currentProject?.frames.find((f) => f.id === id);
      if (frame) {
        updateFrame({ ...frame, notes });
      }
    },
    [currentProject, updateFrame]
  );

  const handleOpenRefine = useCallback((frame: Frame, index: number) => {
    setFrameToRefine({ frame, index });
    setRefineDialogOpen(true);
  }, []);

  const handleRefine = useCallback(async (frameId: string, refinementPrompt: string) => {
    if (demoMode) {
      
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const frame = currentProject?.frames.find(f => f.id === frameId);
      if (frame) {
        
        updateFrame({ 
          ...frame, 
          timestamp: Date.now(),
          notes: frame.notes ? `${frame.notes} (refined)` : 'Refined in demo mode'
        });
      }
      
      toast({
        title: 'Frame Refined (Demo)',
        description: 'In live mode, this would refine the frame using Bria V2 API.',
      });
      return;
    }

    
    try {
      const response = await fetch('http://localhost:8000/api/v1/generation/refine', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          frame_id: frameId,
          refinement_prompt: refinementPrompt,
        }),
      });

      if (!response.ok) {
        throw new Error('Refinement failed');
      }

      const result = await response.json();
      
      
      const pollRefinement = async (jobId: string) => {
        const maxAttempts = 30;
        let attempts = 0;

        while (attempts < maxAttempts) {
          const jobResponse = await fetch(`http://localhost:8000/api/v1/generation/jobs/${jobId}`);
          if (jobResponse.ok) {
            const job = await jobResponse.json();
            
            if (job.status === 'completed') {
              
              if (currentProject?.backendId) {
                const projectResponse = await fetch(`http://localhost:8000/api/v1/generation/projects/${currentProject.backendId}`);
                if (projectResponse.ok) {
                  const projectData = await projectResponse.json();
                  const refinedFrame = projectData.frames.find((f: any) => f.id === frameId);
                  
                  if (refinedFrame) {
                    
                    updateFrame({
                      id: refinedFrame.id,
                      imageUrl: refinedFrame.image_url,
                      prompt: refinedFrame.prompt,
                      params: {
                        fov: refinedFrame.params.fov || 50,
                        lighting: refinedFrame.params.lighting || 60,
                        hdrBloom: refinedFrame.params.hdr_bloom || refinedFrame.params.hdrBloom || 30,
                        colorTemp: refinedFrame.params.color_temp || refinedFrame.params.colorTemp || 5500,
                        contrast: refinedFrame.params.contrast || 50,
                        cameraAngle: refinedFrame.params.camera_angle || refinedFrame.params.cameraAngle || 'eye-level',
                        composition: refinedFrame.params.composition || 'rule-of-thirds',
                      },
                      timestamp: Date.now(),
                      notes: refinedFrame.notes,
                    });
                  }
                }
              }
              return;
            } else if (job.status === 'failed') {
              throw new Error(job.error_message || 'Refinement failed');
            }
          }
          
          await new Promise(resolve => setTimeout(resolve, 1000));
          attempts++;
        }
        
        throw new Error('Refinement timeout');
      };

      await pollRefinement(result.id);
      
    } catch (error) {
      console.error('Refinement error:', error);
      throw error;
    }
  }, [demoMode, currentProject, updateFrame, toast]);

  
  const handlePlay = useCallback(() => {
    if (!currentProject || currentProject.frames.length === 0) return;
    
    setIsPlaying(!isPlaying);
    
    if (!isPlaying) {
      
      const playInterval = setInterval(() => {
        setCurrentFrameIndex((prevIndex) => {
          const nextIndex = (prevIndex + 1) % currentProject.frames.length;
          setSelectedFrameId(currentProject.frames[nextIndex].id);
          return nextIndex;
        });
      }, playbackSpeed);
      
      
      (window as any).playbackInterval = playInterval;
    } else {
      
      if ((window as any).playbackInterval) {
        clearInterval((window as any).playbackInterval);
        (window as any).playbackInterval = null;
      }
    }
  }, [isPlaying, currentProject, playbackSpeed, setSelectedFrameId]);

  const handlePrevious = useCallback(() => {
    if (!currentProject || currentProject.frames.length === 0) return;
    
    const prevIndex = currentFrameIndex > 0 ? currentFrameIndex - 1 : currentProject.frames.length - 1;
    setCurrentFrameIndex(prevIndex);
    setSelectedFrameId(currentProject.frames[prevIndex].id);
  }, [currentFrameIndex, currentProject, setSelectedFrameId]);

  const handleNext = useCallback(() => {
    if (!currentProject || currentProject.frames.length === 0) return;
    
    const nextIndex = (currentFrameIndex + 1) % currentProject.frames.length;
    setCurrentFrameIndex(nextIndex);
    setSelectedFrameId(currentProject.frames[nextIndex].id);
  }, [currentFrameIndex, currentProject, setSelectedFrameId]);

  const handleFullscreen = useCallback(() => {
    setIsFullscreen(!isFullscreen);
  }, [isFullscreen]);

  
  React.useEffect(() => {
    if (currentProject && selectedFrameId) {
      const index = currentProject.frames.findIndex(f => f.id === selectedFrameId);
      if (index !== -1) {
        setCurrentFrameIndex(index);
      }
    }
  }, [selectedFrameId, currentProject]);

  
  React.useEffect(() => {
    return () => {
      if ((window as any).playbackInterval) {
        clearInterval((window as any).playbackInterval);
      }
    };
  }, []);

  if (!currentProject || currentProject.frames.length === 0) {
    return (
      <div className="glass-panel p-8 text-center">
        <p className="text-muted-foreground">
          No frames yet. Generate a storyboard to see your timeline here.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Timeline header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold gradient-text">
          Storyboard Timeline
        </h3>
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">
            {currentProject.frames.length} frames
          </span>
        </div>
      </div>

      {/* Playback controls */}
      <div className="glass-panel p-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">
            Frame {currentFrameIndex + 1} of {currentProject.frames.length}
          </span>
        </div>
        
        <div className="flex items-center gap-4">
          <Button 
            size="icon" 
            variant="ghost" 
            className="w-9 h-9"
            onClick={handlePrevious}
            disabled={currentProject.frames.length === 0}
          >
            <SkipBack className="w-4 h-4" />
          </Button>
          <Button
            size="icon"
            variant="default"
            className="w-10 h-10 rounded-full bg-primary hover:bg-primary/90"
            onClick={handlePlay}
            disabled={currentProject.frames.length === 0}
          >
            {isPlaying ? (
              <Pause className="w-4 h-4" />
            ) : (
              <Play className="w-4 h-4 ml-0.5" />
            )}
          </Button>
          <Button 
            size="icon" 
            variant="ghost" 
            className="w-9 h-9"
            onClick={handleNext}
            disabled={currentProject.frames.length === 0}
          >
            <SkipForward className="w-4 h-4" />
          </Button>
        </div>
        
        <div className="flex items-center gap-2">
          <Button 
            size="icon" 
            variant="ghost" 
            className="w-9 h-9"
            onClick={handleFullscreen}
          >
            <Maximize2 className="w-4 h-4" />
          </Button>
          <span className="text-xs text-muted-foreground">
            {playbackSpeed / 1000}s/frame
          </span>
        </div>
      </div>

      {/* Timeline track */}
      <div className="relative">
        <div className="timeline-track-container p-6 overflow-x-auto overflow-y-hidden border border-border/50 rounded-lg bg-card/50 backdrop-blur-sm">
          <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragEnd={handleDragEnd}
          >
            <SortableContext
              items={currentProject.frames.map((f) => f.id)}
              strategy={horizontalListSortingStrategy}
            >
              <div 
                className="flex gap-6 min-w-max h-full items-start py-4"
                style={{ 
                  transform: `scale(${zoom})`,
                  transformOrigin: 'left center',
                  transition: 'transform 0.2s ease-out'
                }}
              >
                <AnimatePresence>
                  {currentProject.frames.map((frame, index) => (
                    <SortableFrame
                      key={frame.id}
                      frame={frame}
                      index={index}
                      isSelected={selectedFrameId === frame.id}
                      onSelect={setSelectedFrameId}
                      onDelete={deleteFrame}
                      onUpdateNotes={handleUpdateNotes}
                      onRefine={handleOpenRefine}
                    />
                  ))}
                </AnimatePresence>
              </div>
            </SortableContext>
          </DndContext>
        </div>
      </div>

      {/* Timeline ruler */}
      <div className="flex justify-between text-xs text-muted-foreground px-4">
        {currentProject.frames.map((_, i) => (
          <span key={i} className="font-mono">
            {(i * 2).toString().padStart(2, '0')}s
          </span>
        ))}
      </div>

      {/* Refine Dialog */}
      {frameToRefine && (
        <RefineDialog
          frame={frameToRefine.frame}
          frameIndex={frameToRefine.index}
          isOpen={refineDialogOpen}
          onClose={() => {
            setRefineDialogOpen(false);
            setFrameToRefine(null);
          }}
          onRefine={handleRefine}
        />
      )}
    </div>
  );
};
