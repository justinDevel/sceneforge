import { motion } from 'framer-motion';
import { Link, useLocation } from 'react-router-dom';
import { useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Home, ArrowLeft } from 'lucide-react';

const NotFound = () => {
  const location = useLocation();

  useEffect(() => {
    console.error("404 Error: User attempted to access non-existent route:", location.pathname);
  }, [location.pathname]);

  return (
    <div className="min-h-screen flex items-center justify-center px-6 bg-background">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center space-y-6"
      >
        <div className="text-8xl font-bold gradient-text">404</div>
        <h1 className="text-2xl font-semibold text-foreground">Scene Not Found</h1>
        <p className="text-muted-foreground max-w-md">
          This frame doesn't exist in your storyboard. Let's get you back to creating amazing scenes.
        </p>
        <div className="flex items-center justify-center gap-4 pt-4">
          <Button variant="outline" onClick={() => window.history.back()} className="gap-2">
            <ArrowLeft className="w-4 h-4" />
            Go Back
          </Button>
          <Link to="/">
            <Button variant="neon" className="gap-2">
              <Home className="w-4 h-4" />
              Home
            </Button>
          </Link>
        </div>
      </motion.div>
    </div>
  );
};

export default NotFound;
