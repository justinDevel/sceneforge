import { useState } from 'react';
import { motion } from 'framer-motion';
import { useAppStore } from '@/stores/appStore';
import { Button } from '@/components/ui/button';
import { 
  Download, 
  FileVideo, 
  FileImage, 
  FileCode, 
  Film,
  Settings,
  Share2 
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuLabel,
} from '@/components/ui/dropdown-menu';
import { useToast } from '@/hooks/use-toast';

export const ExportOptions = () => {
  const { currentProject, demoMode } = useAppStore();
  const { toast } = useToast();
  const [isExporting, setIsExporting] = useState(false);

  const handleExport = async (format: string) => {
    if (!currentProject) return;

    setIsExporting(true);

    if (demoMode) {
      
      await new Promise((resolve) => setTimeout(resolve, 1500));
      
      
      const mockData = JSON.stringify({
        project: currentProject.name,
        format: format,
        frames: currentProject.frames.length,
        exported_at: new Date().toISOString(),
      }, null, 2);
      
      const blob = new Blob([mockData], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${currentProject.name.replace(/[^a-zA-Z0-9]/g, '_')}_demo.${format === 'json' ? 'json' : 'txt'}`;
      a.click();
      URL.revokeObjectURL(url);
      
      toast({
        title: 'Export Complete (Demo)',
        description: `${format.toUpperCase()} export downloaded. In live mode, this would be a full production file.`,
      });
    } else {
      
      try {
        
        const projectIdToUse = currentProject.backendId || currentProject.id;
        
        
        if (!currentProject.frames || currentProject.frames.length === 0) {
          throw new Error('This project has no frames to export. Please generate a storyboard first.');
        }

        const response = await fetch(`http://localhost:8000/api/v1/generation/export/${projectIdToUse}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            format,
            options: {
              include_metadata: true,
              quality: 'high'
            }
          }),
        });

        if (response.ok) {
          const blob = await response.blob();
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `${currentProject.name.replace(/[^a-zA-Z0-9]/g, '_')}.${format}`;
          a.click();
          URL.revokeObjectURL(url);
          
          toast({
            title: 'Export Complete',
            description: `${format.toUpperCase()} file downloaded successfully.`,
          });
        } else {
          const error = await response.json();
          throw new Error(error.detail || 'Export failed');
        }
      } catch (error) {
        console.error('Export failed:', error);
        toast({
          title: 'Export Failed',
          description: error instanceof Error ? error.message : 'Could not export project. Please try again.',
          variant: 'destructive',
        });
      }
    }

    setIsExporting(false);
  };

  const handleShare = async () => {
    if (!currentProject) return;

    if (demoMode) {
      
      const mockShareUrl = `${window.location.origin}/demo/share/${currentProject.id}`;
      await navigator.clipboard.writeText(mockShareUrl);
      
      toast({
        title: 'Share Link Created (Demo)',
        description: 'Demo link copied to clipboard. In live mode, this would be a real shareable link.',
      });
    } else {
      try {
        
        if (!currentProject.frames || currentProject.frames.length === 0) {
          throw new Error('This project has no frames to share. Please generate a storyboard first.');
        }
        
       
        const projectIdToUse = currentProject.backendId || currentProject.id;
        
        
        const response = await fetch(`http://localhost:8000/api/v1/generation/share/${projectIdToUse}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            expires_in_days: 30,
            allow_public_view: true
          }),
        });

        if (response.ok) {
          const result = await response.json();
          const shareUrl = `${window.location.origin}/share/${result.share_token}`;
          
          
          await navigator.clipboard.writeText(shareUrl);
          
          toast({
            title: 'Share Link Created!',
            description: 'Link copied to clipboard. Valid for 30 days.',
          });
        } else {
          
          const shareUrl = `${window.location.origin}/project/${currentProject.id}`;
          await navigator.clipboard.writeText(shareUrl);
          
          toast({
            title: 'Link Copied!',
            description: 'Project link copied to clipboard.',
          });
        }
      } catch (error) {
        console.error('Share failed:', error);
        toast({
          title: 'Share Failed',
          description: error instanceof Error ? error.message : 'Could not create share link. Please try again.',
          variant: 'destructive',
        });
      }
    }
  };

  if (!currentProject || currentProject.frames.length === 0) {
    return null;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-panel p-4"
    >
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-3">
          <Film className="w-5 h-5 text-primary" />
          <div>
            <h3 className="font-semibold text-sm">{currentProject.name}</h3>
            <p className="text-xs text-muted-foreground">
              {currentProject.frames.length} frames • {currentProject.genre}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleShare}
            className="gap-2 border-border/50 hover:border-primary"
          >
            <Share2 className="w-4 h-4" />
            Share
          </Button>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="default"
                size="sm"
                disabled={isExporting}
                className="gap-2 bg-neon-gradient hover:opacity-90"
              >
                <Download className={`w-4 h-4 ${isExporting ? 'animate-bounce' : ''}`} />
                Export
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56 bg-card border-border">
              <DropdownMenuLabel>Export Format</DropdownMenuLabel>
              <DropdownMenuSeparator />
              
              <DropdownMenuItem onClick={() => handleExport('mp4')} className="gap-3 cursor-pointer">
                <FileVideo className="w-4 h-4 text-primary" />
                <div>
                  <p className="font-medium">MP4 Reel</p>
                  <p className="text-xs text-muted-foreground">Video sequence</p>
                </div>
              </DropdownMenuItem>
              
              <DropdownMenuItem onClick={() => handleExport('exr')} className="gap-3 cursor-pointer">
                <FileImage className="w-4 h-4 text-secondary" />
                <div>
                  <p className="font-medium">EXR Sequence</p>
                  <p className="text-xs text-muted-foreground">16-bit HDR frames</p>
                </div>
              </DropdownMenuItem>
              
              <DropdownMenuItem onClick={() => handleExport('nuke')} className="gap-3 cursor-pointer">
                <FileCode className="w-4 h-4 text-accent" />
                <div>
                  <p className="font-medium">Nuke Script</p>
                  <p className="text-xs text-muted-foreground">Compositing project</p>
                </div>
              </DropdownMenuItem>
              
              <DropdownMenuSeparator />
              
              <DropdownMenuItem onClick={() => handleExport('json')} className="gap-3 cursor-pointer">
                <Settings className="w-4 h-4" />
                <div>
                  <p className="font-medium">JSON Params</p>
                  <p className="text-xs text-muted-foreground">Full project data</p>
                </div>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </motion.div>
  );
};
