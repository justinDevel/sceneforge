import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface Frame {
  id: string;
  imageUrl: string;
  prompt: string;
  params: FrameParams;
  timestamp: number;
  notes?: string;
}

export interface FrameParams {
  fov: number;
  lighting: number;
  hdrBloom: number;
  colorTemp: number;
  contrast: number;
  cameraAngle: string;
  composition: string;
}

export interface SceneProject {
  id: string;
  name: string;
  description: string;
  genre: string;
  frames: Frame[];
  createdAt: number;
  updatedAt: number;
  backendId?: string; 
}

interface GenerationProgress {
  step: number;
  totalSteps: number;
  message: string;
  isComplete: boolean;
}

interface AppState {
  
  demoMode: boolean;
  setDemoMode: (enabled: boolean) => void;

  
  currentProject: SceneProject | null;
  setCurrentProject: (project: SceneProject | null) => void;

  
  isGenerating: boolean;
  setIsGenerating: (generating: boolean) => void;
  generationProgress: GenerationProgress | null;
  setGenerationProgress: (progress: GenerationProgress | null) => void;

  
  selectedFrameId: string | null;
  setSelectedFrameId: (id: string | null) => void;

  
  jsonEditorContent: Record<string, unknown>;
  setJsonEditorContent: (content: Record<string, unknown>) => void;

  
  projects: SceneProject[];
  addProject: (project: SceneProject) => void;
  updateProject: (project: SceneProject) => void;
  deleteProject: (id: string) => void;
  createProject: (name: string, description: string, genre: string) => SceneProject;

  
  addFrame: (frame: Frame) => void;
  updateFrame: (frame: Frame) => void;
  deleteFrame: (id: string) => void;
  reorderFrames: (frames: Frame[]) => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      
      demoMode: false,
      setDemoMode: (enabled) => set({ demoMode: enabled }),

      
      currentProject: null,
      setCurrentProject: (project) => set({ currentProject: project }),

      
      isGenerating: false,
      setIsGenerating: (generating) => set({ isGenerating: generating }),
      generationProgress: null,
      setGenerationProgress: (progress) => set({ generationProgress: progress }),

      
      selectedFrameId: null,
      setSelectedFrameId: (id) => set({ selectedFrameId: id }),

      
      jsonEditorContent: {},
      setJsonEditorContent: (content) => set({ jsonEditorContent: content }),

      
      projects: [],
      addProject: (project) =>
        set((state) => ({ projects: [...state.projects, project] })),
      updateProject: (project) =>
        set((state) => ({
          projects: state.projects.map((p) =>
            p.id === project.id ? project : p
          ),
          currentProject:
            state.currentProject?.id === project.id
              ? project
              : state.currentProject,
        })),
      deleteProject: (id) =>
        set((state) => ({
          projects: state.projects.filter((p) => p.id !== id),
          currentProject:
            state.currentProject?.id === id ? null : state.currentProject,
        })),
      createProject: (name, description, genre) => {
        const project: SceneProject = {
          id: `project-${Date.now()}`,
          name,
          description,
          genre,
          frames: [],
          createdAt: Date.now(),
          updatedAt: Date.now(),
        };
        get().addProject(project);
        return project;
      },

      
      addFrame: (frame) =>
        set((state) => {
          if (!state.currentProject) return state;
          const updatedProject = {
            ...state.currentProject,
            frames: [...state.currentProject.frames, frame],
            updatedAt: Date.now(),
          };
          return {
            currentProject: updatedProject,
            projects: state.projects.map((p) =>
              p.id === updatedProject.id ? updatedProject : p
            ),
          };
        }),
      updateFrame: (frame) =>
        set((state) => {
          if (!state.currentProject) return state;
          const updatedProject = {
            ...state.currentProject,
            frames: state.currentProject.frames.map((f) =>
              f.id === frame.id ? frame : f
            ),
            updatedAt: Date.now(),
          };
          return {
            currentProject: updatedProject,
            projects: state.projects.map((p) =>
              p.id === updatedProject.id ? updatedProject : p
            ),
          };
        }),
      deleteFrame: (id) =>
        set((state) => {
          if (!state.currentProject) return state;
          const updatedProject = {
            ...state.currentProject,
            frames: state.currentProject.frames.filter((f) => f.id !== id),
            updatedAt: Date.now(),
          };
          return {
            currentProject: updatedProject,
            projects: state.projects.map((p) =>
              p.id === updatedProject.id ? updatedProject : p
            ),
            selectedFrameId:
              state.selectedFrameId === id ? null : state.selectedFrameId,
          };
        }),
      reorderFrames: (frames) =>
        set((state) => {
          if (!state.currentProject) return state;
          const updatedProject = {
            ...state.currentProject,
            frames,
            updatedAt: Date.now(),
          };
          return {
            currentProject: updatedProject,
            projects: state.projects.map((p) =>
              p.id === updatedProject.id ? updatedProject : p
            ),
          };
        }),
    }),
    {
      name: 'sceneforge-storage',
      partialize: (state) => ({
        demoMode: state.demoMode,
        projects: state.projects,
      }),
    }
  )
);
