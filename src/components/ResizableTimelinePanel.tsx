import { useState, useCallback, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { GripHorizontal, ZoomIn, ZoomOut } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { StoryboardTimeline } from './StoryboardTimeline';
import { ExportOptions } from './ExportOptions';

export const ResizableTimelinePanel = () => {
  const [panelHeight, setPanelHeight] = useState(500);
  const [isResizing, setIsResizing] = useState(false);
  const [zoom, setZoom] = useState(1);
  const panelRef = useRef<HTMLDivElement>(null);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);

    const startY = e.clientY;
    const startHeight = panelHeight;

    const handleMouseMove = (e: MouseEvent) => {
      const deltaY = startY - e.clientY; 
      const newHeight = Math.max(300, Math.min(800, startHeight + deltaY));
      setPanelHeight(newHeight);
    };

    const handleMouseUp = () => {
      setIsResizing(false);
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  }, [panelHeight]);

  const handleZoomIn = useCallback(() => {
    setZoom((prev) => Math.min(2, prev + 0.1));
  }, []);

  const handleZoomOut = useCallback(() => {
    setZoom((prev) => Math.max(0.5, prev - 0.1));
  }, []);

  return (
    <motion.div
      ref={panelRef}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="relative border-t border-border/50 bg-background/80 backdrop-blur flex-shrink-0"
      style={{ height: `${panelHeight}px` }}
    >
      {/* Resize Handle */}
      <div
        onMouseDown={handleMouseDown}
        className={`absolute top-0 left-0 right-0 h-2 cursor-ns-resize group hover:bg-primary/20 transition-colors z-50 ${
          isResizing ? 'bg-primary/40' : 'bg-transparent'
        }`}
      >
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <GripHorizontal className="w-6 h-6 text-primary" />
        </div>
      </div>

      {/* Content */}
      <div className="h-full overflow-hidden flex flex-col pt-2">
        {/* Toolbar */}
        <div className="px-4 lg:px-6 pb-2 flex items-center justify-between flex-shrink-0">
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Timeline Zoom:</span>
            <Button
              size="icon"
              variant="ghost"
              className="w-8 h-8"
              onClick={handleZoomOut}
              disabled={zoom <= 0.5}
            >
              <ZoomOut className="w-4 h-4" />
            </Button>
            <span className="text-xs font-mono text-primary min-w-[3rem] text-center">
              {Math.round(zoom * 100)}%
            </span>
            <Button
              size="icon"
              variant="ghost"
              className="w-8 h-8"
              onClick={handleZoomIn}
              disabled={zoom >= 2}
            >
              <ZoomIn className="w-4 h-4" />
            </Button>
          </div>
          
          <div className="text-xs text-muted-foreground">
            Drag the top edge to resize
          </div>
        </div>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-auto px-4 lg:px-6 pb-4">
          <div className="space-y-4">
            <ExportOptions />
            <StoryboardTimeline zoom={zoom} />
          </div>
        </div>
      </div>
    </motion.div>
  );
};
