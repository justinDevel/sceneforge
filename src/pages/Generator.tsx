import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Link, useParams } from 'react-router-dom';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import { ParticlesBackground } from '@/components/ParticlesBackground';
import { DemoModeToggle } from '@/components/DemoModeToggle';
import { SceneForm } from '@/components/SceneForm';
import { StoryboardTimeline } from '@/components/StoryboardTimeline';
import { JsonEditor } from '@/components/JsonEditor';
import { ResizableTimelinePanel } from '@/components/ResizableTimelinePanel';
import { useAppStore } from '@/stores/appStore';
import { demoProject } from '@/api/mockData';
import { 
  Film, 
  Home, 
  ChevronLeft,
  GripVertical
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/use-toast';

const GeneratorPage = () => {
  const { currentProject, setCurrentProject, demoMode, addProject, createProject } = useAppStore();
  const [showTimeline, setShowTimeline] = useState(false);
  const [isLoadingProject, setIsLoadingProject] = useState(false);
  const { projectId, shareToken } = useParams();
  const { toast } = useToast();

  
  useEffect(() => {
    const loadProjectFromUrl = async () => {
      if (projectId && !demoMode) {
        setIsLoadingProject(true);
        try {
          const response = await fetch(`http://localhost:8000/api/v1/generation/projects/${projectId}`);
          if (response.ok) {
            const projectData = await response.json();
            
            
            const project = {
              id: projectData.id,
              name: projectData.name,
              description: projectData.description,
              genre: projectData.genre,
              status: projectData.status,
              createdAt: new Date(projectData.created_at).getTime(),
              updatedAt: new Date(projectData.updated_at).getTime(),
              frames: projectData.frames.map((frame: any) => ({
                id: frame.id,
                imageUrl: frame.image_url,
                prompt: frame.prompt,
                params: {
                  fov: frame.params.fov || 50,
                  lighting: frame.params.lighting || 60,
                  hdrBloom: frame.params.hdr_bloom || frame.params.hdrBloom || 30,
                  colorTemp: frame.params.color_temp || frame.params.colorTemp || 5500,
                  contrast: frame.params.contrast || 50,
                  cameraAngle: frame.params.camera_angle || frame.params.cameraAngle || 'eye-level',
                  composition: frame.params.composition || 'rule-of-thirds',
                },
                timestamp: new Date(frame.created_at).getTime(),
                notes: frame.notes,
              })),
            };
            
            
            addProject(project);
            setCurrentProject(project);
            
            toast({
              title: 'Project Loaded',
              description: `Loaded "${project.name}" with ${project.frames.length} frames.`,
            });
          } else {
            throw new Error('Project not found');
          }
        } catch (error) {
          console.error('Failed to load project:', error);
          toast({
            title: 'Failed to Load Project',
            description: 'The project could not be loaded. It may not exist or be inaccessible.',
            variant: 'destructive',
          });
        } finally {
          setIsLoadingProject(false);
        }
      } else if (shareToken && !demoMode) {
        
        setIsLoadingProject(true);
        try {
          const response = await fetch(`http://localhost:8000/api/v1/generation/share/${shareToken}`);
          if (response.ok) {
            const projectData = await response.json();
            
           
            const project = {
              id: projectData.id,
              name: projectData.name,
              description: projectData.description,
              genre: projectData.genre,
              status: projectData.status,
              createdAt: new Date(projectData.created_at).getTime(),
              updatedAt: new Date(projectData.updated_at).getTime(),
              frames: projectData.frames.map((frame: any) => ({
                id: frame.id,
                imageUrl: frame.image_url,
                prompt: frame.prompt,
                params: {
                  fov: frame.params.fov || 50,
                  lighting: frame.params.lighting || 60,
                  hdrBloom: frame.params.hdr_bloom || frame.params.hdrBloom || 30,
                  colorTemp: frame.params.color_temp || frame.params.colorTemp || 5500,
                  contrast: frame.params.contrast || 50,
                  cameraAngle: frame.params.camera_angle || frame.params.cameraAngle || 'eye-level',
                  composition: frame.params.composition || 'rule-of-thirds',
                },
                timestamp: new Date(frame.created_at).getTime(),
                notes: frame.notes,
              })),
            };
            
            
            addProject(project);
            setCurrentProject(project);
            
            toast({
              title: 'Shared Project Loaded',
              description: `Viewing "${project.name}" (${projectData.share_info?.view_count || 0} views)`,
            });
          } else if (response.status === 410) {
            throw new Error('This share link has expired');
          } else if (response.status === 403) {
            throw new Error('This share link is not publicly accessible');
          } else {
            throw new Error('Share link not found');
          }
        } catch (error) {
          console.error('Failed to load shared project:', error);
          toast({
            title: 'Failed to Load Shared Project',
            description: error instanceof Error ? error.message : 'The share link may be invalid or expired.',
            variant: 'destructive',
          });
        } finally {
          setIsLoadingProject(false);
        }
      }
    };

    loadProjectFromUrl();
  }, [projectId, shareToken, demoMode, addProject, setCurrentProject, toast]);

  
  useEffect(() => {
    if (demoMode && !currentProject) {
      
      const existingDemo = useAppStore.getState().projects.find(p => p.id === demoProject.id);
      if (!existingDemo) {
        addProject(demoProject);
      }
      setCurrentProject(demoProject);
    }
  }, [demoMode, currentProject, setCurrentProject, addProject]);

  
  useEffect(() => {
    if (currentProject && currentProject.frames.length > 0) {
      setShowTimeline(true);
    }
  }, [currentProject?.frames.length]);

  return (
    <div className="h-screen flex flex-col relative overflow-hidden">
      <ParticlesBackground />
      
      {/* Header */}
      <header className="relative z-10 flex items-center justify-between px-4 py-3 lg:px-6 border-b border-border/50 bg-background/80 backdrop-blur flex-shrink-0">
        <div className="flex items-center gap-4">
          <Link to="/">
            <Button variant="ghost" size="sm" className="gap-2">
              <ChevronLeft className="w-4 h-4" />
              <Home className="w-4 h-4" />
            </Button>
          </Link>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-neon-gradient flex items-center justify-center">
              <Film className="w-4 h-4 text-primary-foreground" />
            </div>
            <span className="text-lg font-bold gradient-text hidden sm:block">SceneForge</span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <DemoModeToggle />
        </div>
      </header>

      {/* Main Content */}
      <main className="relative z-10 flex-1 overflow-hidden">
        {isLoadingProject ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center space-y-4">
              <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto"></div>
              <p className="text-muted-foreground">Loading project...</p>
            </div>
          </div>
        ) : (
          <PanelGroup direction="horizontal" className="h-full">
            {/* Left Panel - Generator Form */}
            <Panel defaultSize={showTimeline ? 50 : 100} minSize={30}>
              <div className="h-full overflow-y-auto p-6">
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="space-y-6"
                >
                  <div className="text-center mb-8">
                    <h1 className="text-2xl lg:text-3xl font-bold gradient-text mb-2">
                      Scene Generator
                    </h1>
                    <p className="text-muted-foreground">
                      {currentProject ? `Editing: ${currentProject.name}` : 'Describe your vision and let AI create your storyboard'}
                    </p>
                  </div>

                  <SceneForm />
                </motion.div>
              </div>
            </Panel>

            {/* Resize Handle */}
            {showTimeline && (
              <PanelResizeHandle className="w-2 bg-border/30 hover:bg-primary/30 transition-colors flex items-center justify-center">
                <GripVertical className="w-4 h-4 text-muted-foreground" />
              </PanelResizeHandle>
            )}

            {/* Right Panel - JSON Editor */}
            {showTimeline && (
              <Panel defaultSize={50} minSize={25}>
                <div className="h-full overflow-y-auto p-6">
                  <JsonEditor />
                </div>
              </Panel>
            )}
          </PanelGroup>
        )}
      </main>

      {/* Bottom Panel - Resizable Timeline & Export */}
      {showTimeline && <ResizableTimelinePanel />}
    </div>
  );
};

export default GeneratorPage;
