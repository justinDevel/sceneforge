import { useState, useCallback } from 'react';
import { useAppStore, Frame, FrameParams } from '@/stores/appStore';
import { mockGenerateResponse, generationSteps } from '@/api/mockData';


const pollGenerationJob = async (
  jobId: string, 
  onProgress?: (step: number, message: string) => void
): Promise<Frame[]> => {
  const maxAttempts = 60; 
  let attempts = 0;
  
  while (attempts < maxAttempts) {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/generation/jobs/${jobId}`);
      if (!response.ok) {
        throw new Error(`Failed to get job status: ${response.statusText}`);
      }
      
      const job = await response.json();
      
      if (onProgress && job.progress_message) {
        onProgress(job.progress_step || 0, job.progress_message);
      }
      
      if (job.status === 'completed') {
        
        const projectResponse = await fetch(`http://localhost:8000/api/v1/generation/projects/${job.project_id}`);
        if (projectResponse.ok) {
          const project = await projectResponse.json();
          return project.frames.map((frame: any) => ({
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
          }));
        }
        return [];
      } else if (job.status === 'failed') {
        throw new Error(job.error_message || 'Generation failed');
      }
      
      
      await new Promise(resolve => setTimeout(resolve, 5000));
      attempts++;
      
    } catch (error) {
      console.error('Error polling job status:', error);
      attempts++;
      await new Promise(resolve => setTimeout(resolve, 5000));
    }
  }
  
  throw new Error('Generation timeout - job did not complete in time');
};

interface UseGeneratorOptions {
  onComplete?: (frames: Frame[]) => void;
  onError?: (error: Error) => void;
}

export const useGenerator = (options?: UseGeneratorOptions) => {
  const [error, setError] = useState<Error | null>(null);
  
  const {
    demoMode,
    isGenerating,
    setIsGenerating,
    generationProgress,
    setGenerationProgress,
    addFrame,
    currentProject,
  } = useAppStore();

  const generate = useCallback(
    async (prompt: string, params: FrameParams, genre: string = 'noir') => {
      setIsGenerating(true);
      setError(null);
      setGenerationProgress({
        step: 0,
        totalSteps: generationSteps.length,
        message: 'Initializing...',
        isComplete: false,
      });

      try {
        let frames: Frame[];

        if (demoMode) {
          
          frames = await mockGenerateResponse(prompt, params, (step, message) => {
            setGenerationProgress({
              step,
              totalSteps: generationSteps.length,
              message,
              isComplete: false,
            });
          });
          
          
          const store = useAppStore.getState();
          const projectToUpdate = store.currentProject || currentProject;
          
          if (projectToUpdate) {
            const updatedProject = {
              ...projectToUpdate,
              backendId: `demo-backend-${Date.now()}`, 
            };
            store.updateProject(updatedProject);
            store.setCurrentProject(updatedProject);
          }
        } else {
          
          const response = await fetch('http://localhost:8000/api/v1/generation/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
              scene_description: prompt, 
              genre: genre,
              frame_count: 6, 
              base_params: {
                fov: params.fov,
                lighting: params.lighting,
                hdr_bloom: params.hdrBloom,
                color_temp: params.colorTemp,
                contrast: params.contrast,
                camera_angle: params.cameraAngle,
                composition: params.composition,
              }
            }),
          });

          if (!response.ok) {
            throw new Error(`Generation failed: ${response.statusText}`);
          }

          const jobData = await response.json();
          
          
          if (jobData.project_id) {
            const store = useAppStore.getState();
            const projectToUpdate = store.currentProject || currentProject;
            
            if (projectToUpdate) {
              const updatedProject = {
                ...projectToUpdate,
                backendId: jobData.project_id, 
              };
              store.updateProject(updatedProject);
              store.setCurrentProject(updatedProject);
              
              console.log('Backend ID stored:', jobData.project_id);
            }
          }
          
          
          frames = await pollGenerationJob(jobData.id, (step, message) => {
            setGenerationProgress({
              step,
              totalSteps: generationSteps.length,
              message,
              isComplete: false,
            });
          });
        }

        
        frames.forEach((frame) => addFrame(frame));

        setGenerationProgress({
          step: generationSteps.length,
          totalSteps: generationSteps.length,
          message: 'Complete!',
          isComplete: true,
        });

        options?.onComplete?.(frames);
        return frames;
      } catch (err) {
        const error = err instanceof Error ? err : new Error('Unknown error');
        setError(error);
        options?.onError?.(error);
        throw error;
      } finally {
        setTimeout(() => {
          setIsGenerating(false);
          setGenerationProgress(null);
        }, 1500);
      }
    },
    [demoMode, addFrame, setIsGenerating, setGenerationProgress, options]
  );

  const regenerateFrame = useCallback(
    async (frameId: string, params: FrameParams) => {
      if (!currentProject) return;

      const frame = currentProject.frames.find((f) => f.id === frameId);
      if (!frame) return;

      setIsGenerating(true);
      setError(null);

      try {
        if (demoMode) {
          
          await new Promise((resolve) => setTimeout(resolve, 2000));
          
          const updatedFrame: Frame = {
            ...frame,
            params,
            timestamp: Date.now(),
          };

          useAppStore.getState().updateFrame(updatedFrame);
          return updatedFrame;
        } else {
          const response = await fetch('http://localhost:8000/api/v1/generation/refine', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
              frame_id: frameId, 
              refinement_prompt: "Refine this frame",
              params: {
                fov: params.fov,
                lighting: params.lighting,
                hdr_bloom: params.hdrBloom,
                color_temp: params.colorTemp,
                contrast: params.contrast,
                camera_angle: params.cameraAngle,
                composition: params.composition,
              }
            }),
          });

          if (!response.ok) {
            throw new Error(`Refinement failed: ${response.statusText}`);
          }

          const jobData = await response.json();
          
          
          const refinedFrames = await pollGenerationJob(jobData.id);
          if (refinedFrames.length > 0) {
            const refinedFrame = {
              ...frame,
              ...refinedFrames[0],
              timestamp: Date.now(),
            };
            useAppStore.getState().updateFrame(refinedFrame);
            return refinedFrame;
          }
        }
      } catch (err) {
        const error = err instanceof Error ? err : new Error('Unknown error');
        setError(error);
        throw error;
      } finally {
        setIsGenerating(false);
      }
    },
    [demoMode, currentProject, setIsGenerating]
  );

  return {
    generate,
    regenerateFrame,
    isGenerating,
    generationProgress,
    error,
  };
};
