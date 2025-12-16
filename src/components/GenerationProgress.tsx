import { motion } from 'framer-motion';
import { Check, Loader2 } from 'lucide-react';

interface GenerationProgressProps {
  currentStep: number;
  message: string;
  isComplete: boolean;
}

const steps = [
  { id: 1, label: 'Analyzing scene structure' },
  { id: 2, label: 'Converting to technical parameters' },
  { id: 3, label: 'Ensuring consistency' },
  { id: 4, label: 'Generating HDR frames' },
  { id: 5, label: 'Finalizing storyboard' },
];

export const GenerationProgress = ({
  currentStep,
  message,
  isComplete,
}: GenerationProgressProps) => {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="glass-panel p-8 space-y-6"
    >
      <div className="text-center space-y-2">
        <h3 className="text-2xl font-bold gradient-text">
          {isComplete ? 'Generation Complete!' : 'Generating Storyboard...'}
        </h3>
        <p className="text-muted-foreground">{message}</p>
      </div>

      <div className="space-y-4">
        {steps.map((step) => {
         
          const isCompleted = step.id < currentStep || (isComplete && step.id <= currentStep);
          const isCurrent = step.id === currentStep && !isComplete;
          const isPending = step.id > currentStep && !isComplete;

          return (
            <motion.div
              key={step.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: step.id * 0.1 }}
              className={`flex items-center gap-4 p-4 rounded-lg border transition-all ${
                isCompleted
                  ? 'border-primary/50 bg-primary/10'
                  : isCurrent
                  ? 'border-primary bg-primary/20 shadow-lg shadow-primary/20'
                  : 'border-border/30 bg-muted/20'
              }`}
            >
              <div
                className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center transition-all ${
                  isCompleted
                    ? 'bg-primary text-primary-foreground'
                    : isCurrent
                    ? 'bg-primary/50 text-primary-foreground'
                    : 'bg-muted text-muted-foreground'
                }`}
              >
                {isCompleted ? (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ type: 'spring', stiffness: 200, damping: 10 }}
                  >
                    <Check className="w-4 h-4" />
                  </motion.div>
                ) : isCurrent ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <span className="text-sm font-mono">{step.id}</span>
                )}
              </div>

              <div className="flex-1">
                <p
                  className={`text-sm font-medium ${
                    isCompleted || isCurrent
                      ? 'text-foreground'
                      : 'text-muted-foreground'
                  }`}
                >
                  {step.label}
                </p>
              </div>

              {isCompleted && (
                <motion.div
                  initial={{ scale: 0, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ type: 'spring', stiffness: 200, damping: 10 }}
                  className="text-xs text-primary font-mono"
                >
                  ✓ Done
                </motion.div>
              )}
            </motion.div>
          );
        })}
      </div>

      {/* Progress bar */}
      <div className="space-y-2">
        <div className="h-2 bg-muted/30 rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-neon-gradient"
            initial={{ width: 0 }}
            animate={{ width: `${isComplete ? 100 : (currentStep / steps.length) * 100}%` }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
          />
        </div>
        <div className="flex justify-between text-xs text-muted-foreground">
          <span>Step {isComplete ? steps.length : currentStep} of {steps.length}</span>
          <span>{isComplete ? 100 : Math.round((currentStep / steps.length) * 100)}%</span>
        </div>
      </div>
    </motion.div>
  );
};
