import React from 'react';
import { Separator } from './ui/separator';
import { Heart, Code, Zap } from 'lucide-react';

const Footer = () => {
  return (
    <footer className="bg-gray-50 border-t border-gray-200 mt-16">
      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* About */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Brand Campaign Agent</h3>
            <p className="text-sm text-gray-600">
              AI-powered tool for generating comprehensive brand campaigns with text, visuals, and brand elements.
            </p>
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <span>Made with</span>
              <Heart className="h-4 w-4 text-red-500" />
              <span>using OpenAI</span>
            </div>
          </div>

          {/* Features */}
          <div className="space-y-4">
            <h4 className="font-semibold text-gray-900">Features</h4>
            <ul className="space-y-2 text-sm text-gray-600">
              <li className="flex items-center gap-2">
                <Code className="h-4 w-4" />
                AI Content Generation
              </li>
              <li className="flex items-center gap-2">
                <Zap className="h-4 w-4" />
                Visual Asset Creation
              </li>
              <li className="flex items-center gap-2">
                <Heart className="h-4 w-4" />
                Brand Element Design
              </li>
            </ul>
          </div>

          {/* Technology */}
          <div className="space-y-4">
            <h4 className="font-semibold text-gray-900">Technology</h4>
            <ul className="space-y-2 text-sm text-gray-600">
              <li>OpenAI GPT-4</li>
              <li>DALL-E Image Generation</li>
              <li>React Frontend</li>
              <li>Python Backend</li>
            </ul>
          </div>

          {/* Links */}
          <div className="space-y-4">
            <h4 className="font-semibold text-gray-900">Resources</h4>
            <ul className="space-y-2 text-sm text-gray-600">
              <li>
                <a href="/docs" className="hover:text-blue-600 transition-colors">
                  Documentation
                </a>
              </li>
              <li>
                <a href="/api" className="hover:text-blue-600 transition-colors">
                  API Reference
                </a>
              </li>
              <li>
                <a href="/examples" className="hover:text-blue-600 transition-colors">
                  Examples
                </a>
              </li>
              <li>
                <a href="/support" className="hover:text-blue-600 transition-colors">
                  Support
                </a>
              </li>
            </ul>
          </div>
        </div>

        <Separator className="my-8" />

        <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
          <div className="text-sm text-gray-600">
            © 2025 Brand Campaign Agent. All rights reserved.
          </div>
          <div className="flex space-x-6 text-sm text-gray-600">
            <a href="/privacy" className="hover:text-blue-600 transition-colors">
              Privacy Policy
            </a>
            <a href="/terms" className="hover:text-blue-600 transition-colors">
              Terms of Service
            </a>
            <a href="/contact" className="hover:text-blue-600 transition-colors">
              Contact
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;

