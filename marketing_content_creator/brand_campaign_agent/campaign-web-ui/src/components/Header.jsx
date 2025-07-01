import React from 'react';
import { Button } from './ui/button';
import { Sparkles, Github, ExternalLink } from 'lucide-react';

const Header = () => {
  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="flex items-center justify-center w-10 h-10 bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg">
              <Sparkles className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">Brand Campaign Agent</h1>
              <p className="text-sm text-gray-600">AI-Powered Campaign Generation</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <Button variant="ghost" size="sm" asChild>
              <a 
                href="https://github.com/your-repo/brand-campaign-agent" 
                target="_blank" 
                rel="noopener noreferrer"
                className="flex items-center gap-2"
              >
                <Github className="h-4 w-4" />
                GitHub
              </a>
            </Button>
            
            <Button variant="ghost" size="sm" asChild>
              <a 
                href="/docs" 
                target="_blank" 
                rel="noopener noreferrer"
                className="flex items-center gap-2"
              >
                <ExternalLink className="h-4 w-4" />
                Docs
              </a>
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;

