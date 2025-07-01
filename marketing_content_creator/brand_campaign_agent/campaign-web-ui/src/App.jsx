import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'sonner';
import CampaignForm from './components/CampaignForm';
import CampaignResults from './components/CampaignResults';
import Header from './components/Header';
import Footer from './components/Footer';
import './App.css';

function App() {
  const [campaignData, setCampaignData] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);

  const handleCampaignGenerated = (data) => {
    setCampaignData(data);
    setIsGenerating(false);
  };

  const handleStartGeneration = () => {
    setIsGenerating(true);
    setCampaignData(null);
  };

  const handleReset = () => {
    setCampaignData(null);
    setIsGenerating(false);
  };

  return (
    <Router>
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        <Header />
        
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route 
              path="/" 
              element={
                <div className="max-w-6xl mx-auto">
                  {!campaignData && !isGenerating && (
                    <div className="text-center mb-8">
                      <h1 className="text-4xl font-bold text-gray-900 mb-4">
                        AI Brand Campaign Generator
                      </h1>
                      <p className="text-xl text-gray-600 max-w-3xl mx-auto">
                        Create comprehensive brand campaigns with AI-generated content, 
                        visuals, and brand elements tailored to your target audience.
                      </p>
                    </div>
                  )}
                  
                  {!campaignData && !isGenerating && (
                    <CampaignForm 
                      onStartGeneration={handleStartGeneration}
                      onCampaignGenerated={handleCampaignGenerated}
                    />
                  )}
                  
                  {isGenerating && (
                    <div className="text-center py-16">
                      <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
                      <h2 className="text-2xl font-semibold text-gray-900 mb-2">
                        Generating Your Campaign
                      </h2>
                      <p className="text-gray-600">
                        This may take a few minutes as we create your custom content and visuals...
                      </p>
                    </div>
                  )}
                  
                  {campaignData && (
                    <CampaignResults 
                      campaignData={campaignData}
                      onReset={handleReset}
                    />
                  )}
                </div>
              } 
            />
          </Routes>
        </main>
        
        <Footer />
        <Toaster position="top-right" />
      </div>
    </Router>
  );
}

export default App;

