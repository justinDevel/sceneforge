import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useAppStore, FrameParams } from '@/stores/appStore';
import { paramsToJson } from '@/api/mockData';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Copy, Check, RefreshCw, Edit3, Save, X, Sliders, Code2 } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { useGenerator } from '@/hooks/useGenerator';
import { VisualParamEditor } from './VisualParamEditor';

export const JsonEditor = () => {
  const { currentProject, selectedFrameId, updateFrame } = useAppStore();
  const [copied, setCopied] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editedJson, setEditedJson] = useState('');
  const [jsonError, setJsonError] = useState('');
  const { regenerateFrame, isGenerating } = useGenerator();
  const { toast } = useToast();

  const selectedFrame = currentProject?.frames.find(
    (f) => f.id === selectedFrameId
  );

  const jsonContent = selectedFrame
    ? paramsToJson(selectedFrame.params)
    : null;

  
  useEffect(() => {
    if (jsonContent && !isEditing) {
      setEditedJson(JSON.stringify(jsonContent, null, 2));
      setJsonError('');
    }
  }, [jsonContent, selectedFrameId, isEditing]);

  const handleCopy = async () => {
    if (!jsonContent) return;
    
    await navigator.clipboard.writeText(JSON.stringify(jsonContent, null, 2));
    setCopied(true);
    toast({
      title: 'Copied!',
      description: 'JSON copied to clipboard',
    });
    setTimeout(() => setCopied(false), 2000);
  };

  const handleRegenerate = async () => {
    if (!selectedFrame) return;
    
    try {
      await regenerateFrame(selectedFrame.id, selectedFrame.params);
      toast({
        title: 'Regenerated!',
        description: 'Frame has been updated',
      });
    } catch {
      toast({
        title: 'Error',
        description: 'Failed to regenerate frame',
        variant: 'destructive',
      });
    }
  };

  const handleStartEdit = () => {
    setIsEditing(true);
    setJsonError('');
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    setEditedJson(JSON.stringify(jsonContent, null, 2));
    setJsonError('');
  };

  const handleSaveEdit = async () => {
    if (!selectedFrame) return;

    try {
      
      const parsedJson = JSON.parse(editedJson);
      
      
      const updatedParams: FrameParams = {
        fov: parsedJson.fov || selectedFrame.params.fov,
        lighting: parsedJson.lighting || selectedFrame.params.lighting,
        hdrBloom: parsedJson.hdrBloom || parsedJson.hdr_bloom || selectedFrame.params.hdrBloom,
        colorTemp: parsedJson.colorTemp || parsedJson.color_temp || selectedFrame.params.colorTemp,
        contrast: parsedJson.contrast || selectedFrame.params.contrast,
        cameraAngle: parsedJson.cameraAngle || parsedJson.camera_angle || selectedFrame.params.cameraAngle,
        composition: parsedJson.composition || selectedFrame.params.composition,
      };

      
      const updatedFrame = {
        ...selectedFrame,
        params: updatedParams,
        timestamp: Date.now(),
      };

      updateFrame(updatedFrame);
      setIsEditing(false);
      setJsonError('');

      toast({
        title: 'Parameters Updated!',
        description: 'Frame parameters have been saved. Click Regenerate to apply changes.',
      });

    } catch (error) {
      setJsonError('Invalid JSON format. Please check your syntax.');
      toast({
        title: 'Invalid JSON',
        description: 'Please check your JSON syntax and try again.',
        variant: 'destructive',
      });
    }
  };

  const syntaxHighlight = (json: string) => {
    return json.replace(
      /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?)/g,
      (match) => {
        let cls = 'json-number';
        if (/^"/.test(match)) {
          if (/:$/.test(match)) {
            cls = 'json-key';
          } else {
            cls = 'json-string';
          }
        } else if (/true|false/.test(match)) {
          cls = 'json-boolean';
        }
        return `<span class="${cls}">${match}</span>`;
      }
    );
  };

  if (!selectedFrame) {
    return (
      <div className="glass-panel p-6 h-full flex items-center justify-center">
        <p className="text-muted-foreground text-center">
          Select a frame to view and edit its JSON parameters
        </p>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      className="glass-panel p-4 h-full flex flex-col overflow-hidden"
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold gradient-text">
          Frame #{currentProject?.frames.findIndex((f) => f.id === selectedFrameId)! + 1} JSON
        </h3>
        <div className="flex gap-2">
          {!isEditing ? (
            <>
              <Button
                size="sm"
                variant="outline"
                onClick={handleCopy}
                className="gap-2 border-border/50 hover:border-primary"
              >
                {copied ? (
                  <>
                    <Check className="w-3 h-3" />
                    Copied
                  </>
                ) : (
                  <>
                    <Copy className="w-3 h-3" />
                    Copy
                  </>
                )}
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={handleStartEdit}
                className="gap-2 border-border/50 hover:border-accent"
              >
                <Edit3 className="w-3 h-3" />
                Edit
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={handleRegenerate}
                disabled={isGenerating}
                className="gap-2 border-border/50 hover:border-secondary"
              >
                <RefreshCw className={`w-3 h-3 ${isGenerating ? 'animate-spin' : ''}`} />
                Regenerate
              </Button>
            </>
          ) : (
            <>
              <Button
                size="sm"
                variant="outline"
                onClick={handleCancelEdit}
                className="gap-2 border-border/50 hover:border-destructive"
              >
                <X className="w-3 h-3" />
                Cancel
              </Button>
              <Button
                size="sm"
                variant="default"
                onClick={handleSaveEdit}
                className="gap-2 bg-neon-gradient hover:opacity-90"
              >
                <Save className="w-3 h-3" />
                Save
              </Button>
            </>
          )}
        </div>
      </div>

      <Tabs defaultValue="visual" className="flex-1 flex flex-col overflow-hidden">
        <TabsList className="grid w-full grid-cols-2 bg-muted/30 flex-shrink-0">
          <TabsTrigger value="visual" className="gap-2 data-[state=active]:bg-primary/20">
            <Sliders className="w-4 h-4" />
            Visual Editor
          </TabsTrigger>
          <TabsTrigger value="json" className="gap-2 data-[state=active]:bg-primary/20">
            <Code2 className="w-4 h-4" />
            JSON Editor
          </TabsTrigger>
        </TabsList>

        <TabsContent value="visual" className="mt-4 flex-1 overflow-y-auto">
          <VisualParamEditor
            params={selectedFrame.params}
            onChange={(newParams) => {
              const updatedFrame = {
                ...selectedFrame,
                params: newParams,
              };
              updateFrame(updatedFrame);
            }}
            onSave={handleRegenerate}
          />
        </TabsContent>

        <TabsContent value="json" className="mt-4 flex-1 overflow-hidden flex flex-col">
          <div className="json-editor overflow-y-auto rounded-lg flex-1">
            {isEditing ? (
              <div className="space-y-2">
                <Textarea
                  value={editedJson}
                  onChange={(e) => setEditedJson(e.target.value)}
                  className="min-h-[400px] font-mono text-xs leading-relaxed resize-none"
                  placeholder="Edit JSON parameters..."
                />
                {jsonError && (
                  <p className="text-xs text-destructive">{jsonError}</p>
                )}
              </div>
            ) : (
              <pre
                className="text-xs leading-relaxed"
                dangerouslySetInnerHTML={{
                  __html: syntaxHighlight(JSON.stringify(jsonContent, null, 2)),
                }}
              />
            )}
          </div>
        </TabsContent>
      </Tabs>

      <div className="mt-4 pt-4 border-t border-border/50">
        <p className="text-xs text-muted-foreground">
          Use the Visual Editor for intuitive parameter control, or switch to JSON Editor for advanced editing. Click Regenerate to apply changes.
        </p>
      </div>
    </motion.div>
  );
};
