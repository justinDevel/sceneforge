import type { Frame, FrameParams, SceneProject } from '@/stores/appStore';


export const demoFrameImages = [
  'https://images.unsplash.com/photo-1534447677768-be436bb09401?w=800&h=450&fit=crop', 
  'https://images.unsplash.com/photo-1519608487953-e999c86e7455?w=800&h=450&fit=crop', 
  'https://images.unsplash.com/photo-1478760329108-5c3ed9d495a0?w=800&h=450&fit=crop', 
  'https://images.unsplash.com/photo-1493246507139-91e8fad9978e?w=800&h=450&fit=crop', 
  'https://images.unsplash.com/photo-1504253163759-c23fccaebb55?w=800&h=450&fit=crop', 
  'https://images.unsplash.com/photo-1517483000871-1dbf64a6e1c6?w=800&h=450&fit=crop', 
];

export const genreOptions = [
  { value: 'noir', label: 'Film Noir', icon: '🎬' },
  { value: 'scifi', label: 'Sci-Fi', icon: '🚀' },
  { value: 'horror', label: 'Horror', icon: '👻' },
  { value: 'action', label: 'Action', icon: '💥' },
  { value: 'drama', label: 'Drama', icon: '🎭' },
  { value: 'fantasy', label: 'Fantasy', icon: '✨' },
  { value: 'thriller', label: 'Thriller', icon: '🔪' },
  { value: 'western', label: 'Western', icon: '🤠' },
];

export const cameraAngles = [
  { value: 'eye-level', label: 'Eye Level' },
  { value: 'low-angle', label: 'Low Angle' },
  { value: 'high-angle', label: 'High Angle' },
  { value: 'dutch-angle', label: 'Dutch Angle' },
  { value: 'birds-eye', label: "Bird's Eye" },
  { value: 'worms-eye', label: "Worm's Eye" },
  { value: 'over-shoulder', label: 'Over Shoulder' },
  { value: 'pov', label: 'POV' },
];

export const compositions = [
  { value: 'rule-of-thirds', label: 'Rule of Thirds' },
  { value: 'centered', label: 'Centered' },
  { value: 'symmetrical', label: 'Symmetrical' },
  { value: 'leading-lines', label: 'Leading Lines' },
  { value: 'frame-within-frame', label: 'Frame Within Frame' },
  { value: 'negative-space', label: 'Negative Space' },
  { value: 'golden-ratio', label: 'Golden Ratio' },
];

export const defaultParams: FrameParams = {
  fov: 50,
  lighting: 60,
  hdrBloom: 30,
  colorTemp: 5500,
  contrast: 50,
  cameraAngle: 'eye-level',
  composition: 'rule-of-thirds',
};

export const generationSteps = [
  { step: 1, message: 'Analyzing scene description...' },
  { step: 2, message: 'Breaking down narrative beats...' },
  { step: 3, message: 'Structuring JSON parameters...' },
  { step: 4, message: 'Optimizing camera placement...' },
  { step: 5, message: 'Generating HDR frames...' },
  { step: 6, message: 'Applying post-processing...' },
  { step: 7, message: 'Finalizing storyboard...' },
];

export const samplePrompts = [
  "A tense noir chase through rainy neon streets at midnight",
  "Astronaut discovers alien artifact in abandoned space station",
  "Western showdown at sunset in a ghost town",
  "Detective interrogation scene with dramatic shadows",
  "Car chase through Tokyo with neon reflections",
  "Underwater discovery of ancient sunken temple",
];


export const generateMockFrames = (count: number = 6): Frame[] => {
  return Array.from({ length: count }, (_, i) => ({
    id: `frame-${Date.now()}-${i}`,
    imageUrl: demoFrameImages[i % demoFrameImages.length],
    prompt: samplePrompts[i % samplePrompts.length],
    params: {
      ...defaultParams,
      fov: 24 + Math.floor(Math.random() * 96),
      lighting: 30 + Math.floor(Math.random() * 70),
      hdrBloom: 10 + Math.floor(Math.random() * 60),
    },
    timestamp: Date.now() + i * 1000,
    notes: i === 0 ? 'Opening shot - establish mood' : undefined,
  }));
};

export const demoProject: SceneProject = {
  id: 'demo-project-1',
  backendId: 'demo-backend-uuid-1234', 
  name: 'Neon Noir Chase',
  description: 'A tense noir chase through rainy neon streets at midnight. Detective follows suspect through crowded alleys.',
  genre: 'noir',
  frames: generateMockFrames(6),
  createdAt: Date.now() - 86400000,
  updatedAt: Date.now(),
};


export const mockGenerateResponse = async (
  prompt: string,
  params: FrameParams,
  onProgress: (step: number, message: string) => void
): Promise<Frame[]> => {
  const frames: Frame[] = [];
  
  
  for (let i = 0; i < generationSteps.length; i++) {
    onProgress(i + 1, generationSteps[i].message);
    
    const delay = i === 4 ? 1500 : 600 + Math.random() * 400; 
    await new Promise((resolve) => setTimeout(resolve, delay));
  }

  
  const frameCount = 6;
  const framePrompts = [
    `${prompt} - Opening establishing shot`,
    `${prompt} - Medium shot with character focus`,
    `${prompt} - Close-up detail shot`,
    `${prompt} - Wide angle dramatic moment`,
    `${prompt} - Over-shoulder perspective`,
    `${prompt} - Final climactic frame`,
  ];

  for (let i = 0; i < frameCount; i++) {
    frames.push({
      id: `frame-${Date.now()}-${i}`,
      imageUrl: demoFrameImages[i % demoFrameImages.length],
      prompt: framePrompts[i],
      params: {
        ...params,
        fov: Math.max(24, Math.min(120, params.fov + (Math.random() - 0.5) * 15)),
        lighting: Math.max(0, Math.min(100, params.lighting + (Math.random() - 0.5) * 20)),
        hdrBloom: Math.max(0, Math.min(100, params.hdrBloom + (Math.random() - 0.5) * 15)),
        cameraAngle: i === 0 ? 'eye-level' : i === 3 ? 'low-angle' : i === 4 ? 'over-shoulder' : params.cameraAngle,
      },
      timestamp: Date.now() + i * 100,
      notes: i === 0 ? 'Opening shot - establish mood and setting' : undefined,
    });
  }

  return frames;
};

export const paramsToJson = (params: FrameParams): Record<string, unknown> => ({
  camera: {
    fov: params.fov,
    angle: params.cameraAngle,
    position: { x: 0, y: 1.7, z: 5 },
  },
  lighting: {
    intensity: params.lighting / 100,
    temperature: params.colorTemp,
    hdr: {
      enabled: true,
      bloom: params.hdrBloom / 100,
    },
  },
  composition: {
    rule: params.composition,
    contrast: params.contrast / 100,
  },
  output: {
    format: 'EXR',
    resolution: { width: 3840, height: 2160 },
    bitDepth: 16,
  },
});
