import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Separator } from './ui/separator';
import { ScrollArea } from './ui/scroll-area';
import { 
  Download, 
  RefreshCw, 
  Copy, 
  Palette, 
  Type, 
  Image, 
  FileText,
  Target,
  TrendingUp,
  Users,
  Calendar
} from 'lucide-react';
import { toast } from 'sonner';

const CampaignResults = ({ campaignData, onReset }) => {
  const [copiedText, setCopiedText] = useState('');

  const copyToClipboard = (text, label) => {
    navigator.clipboard.writeText(text);
    setCopiedText(label);
    toast.success(`${label} copied to clipboard!`);
    setTimeout(() => setCopiedText(''), 2000);
  };

  const downloadCampaignData = () => {
    const dataStr = JSON.stringify(campaignData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `campaign_${campaignData.campaign_id}.json`;
    link.click();
    URL.revokeObjectURL(url);
    toast.success('Campaign data downloaded!');
  };

  const ColorSwatch = ({ color, label }) => (
    <div className="flex items-center space-x-2">
      <div 
        className="w-8 h-8 rounded border border-gray-300"
        style={{ backgroundColor: color }}
      ></div>
      <div>
        <p className="text-sm font-medium">{label}</p>
        <p className="text-xs text-gray-500">{color}</p>
      </div>
    </div>
  );

  const ContentCard = ({ title, content, icon: Icon, copyLabel }) => (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg">
          <Icon className="h-5 w-5" />
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {Array.isArray(content) ? (
            content.map((item, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="flex-1">{item}</span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => copyToClipboard(item, `${copyLabel} ${index + 1}`)}
                  className="ml-2"
                >
                  <Copy className="h-4 w-4" />
                </Button>
              </div>
            ))
          ) : (
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="flex-1">{content}</span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => copyToClipboard(content, copyLabel)}
                className="ml-2"
              >
                <Copy className="h-4 w-4" />
              </Button>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="w-full max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-2xl">
                {campaignData.brief.product_info.name} Campaign
              </CardTitle>
              <CardDescription>
                Campaign ID: {campaignData.campaign_id} • Generated on {new Date(campaignData.created_at).toLocaleDateString()}
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={downloadCampaignData}>
                <Download className="h-4 w-4 mr-2" />
                Download
              </Button>
              <Button variant="outline" onClick={onReset}>
                <RefreshCw className="h-4 w-4 mr-2" />
                New Campaign
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="flex items-center gap-2">
              <Users className="h-5 w-5 text-blue-600" />
              <div>
                <p className="text-sm font-medium">Target Age</p>
                <p className="text-sm text-gray-600">
                  {campaignData.brief.demographics.age_range[0]}-{campaignData.brief.demographics.age_range[1]} years
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Target className="h-5 w-5 text-green-600" />
              <div>
                <p className="text-sm font-medium">Objectives</p>
                <p className="text-sm text-gray-600">
                  {campaignData.brief.objectives.length} selected
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-purple-600" />
              <div>
                <p className="text-sm font-medium">Platforms</p>
                <p className="text-sm text-gray-600">
                  {campaignData.brief.platforms.length} channels
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Calendar className="h-5 w-5 text-orange-600" />
              <div>
                <p className="text-sm font-medium">Timeline</p>
                <p className="text-sm text-gray-600">
                  {campaignData.brief.timeline || 'Not specified'}
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Campaign Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Campaign Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-700 leading-relaxed">{campaignData.campaign_summary}</p>
        </CardContent>
      </Card>

      {/* Main Content Tabs */}
      <Tabs defaultValue="content" className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="content">Content</TabsTrigger>
          <TabsTrigger value="brand">Brand</TabsTrigger>
          <TabsTrigger value="visuals">Visuals</TabsTrigger>
          <TabsTrigger value="recommendations">Strategy</TabsTrigger>
          <TabsTrigger value="brief">Brief</TabsTrigger>
        </TabsList>

        <TabsContent value="content" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ContentCard
              title="Headlines"
              content={campaignData.text_content.headlines}
              icon={FileText}
              copyLabel="Headline"
            />
            
            <ContentCard
              title="Taglines"
              content={campaignData.text_content.taglines}
              icon={FileText}
              copyLabel="Tagline"
            />
          </div>

          <ContentCard
            title="Product Descriptions"
            content={campaignData.text_content.product_descriptions}
            icon={FileText}
            copyLabel="Description"
          />

          <ContentCard
            title="Call-to-Actions"
            content={campaignData.text_content.call_to_actions}
            icon={FileText}
            copyLabel="CTA"
          />

          {/* Platform-specific Ad Copy */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Platform Ad Copy
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue={Object.keys(campaignData.text_content.ad_copy)[0]} className="w-full">
                <TabsList>
                  {Object.keys(campaignData.text_content.ad_copy).map((platform) => (
                    <TabsTrigger key={platform} value={platform}>
                      {platform.charAt(0).toUpperCase() + platform.slice(1)}
                    </TabsTrigger>
                  ))}
                </TabsList>
                {Object.entries(campaignData.text_content.ad_copy).map(([platform, copy]) => (
                  <TabsContent key={platform} value={platform} className="space-y-2">
                    {copy.map((text, index) => (
                      <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <span className="flex-1">{text}</span>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => copyToClipboard(text, `${platform} ad copy ${index + 1}`)}
                          className="ml-2"
                        >
                          <Copy className="h-4 w-4" />
                        </Button>
                      </div>
                    ))}
                  </TabsContent>
                ))}
              </Tabs>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="brand" className="space-y-6">
          {/* Color Palette */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Palette className="h-5 w-5" />
                Color Palette
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
                <ColorSwatch color={campaignData.brand_elements.color_palette.primary} label="Primary" />
                <ColorSwatch color={campaignData.brand_elements.color_palette.secondary} label="Secondary" />
                <ColorSwatch color={campaignData.brand_elements.color_palette.accent} label="Accent" />
                <ColorSwatch color={campaignData.brand_elements.color_palette.neutral} label="Neutral" />
                <ColorSwatch color={campaignData.brand_elements.color_palette.background} label="Background" />
                <ColorSwatch color={campaignData.brand_elements.color_palette.text} label="Text" />
              </div>
              <Separator className="my-4" />
              <div>
                <h4 className="font-medium mb-2">Color Psychology</h4>
                <p className="text-gray-700">{campaignData.brand_elements.color_palette.psychology}</p>
              </div>
            </CardContent>
          </Card>

          {/* Typography */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Type className="h-5 w-5" />
                Typography Guide
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h4 className="font-medium mb-2">Primary Font</h4>
                  <p className="text-lg font-semibold">{campaignData.brand_elements.typography.primary_font}</p>
                  <p className="text-sm text-gray-600">{campaignData.brand_elements.typography.heading_style}</p>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Secondary Font</h4>
                  <p className="text-lg">{campaignData.brand_elements.typography.secondary_font}</p>
                  <p className="text-sm text-gray-600">{campaignData.brand_elements.typography.body_style}</p>
                </div>
              </div>
              <Separator />
              <div>
                <h4 className="font-medium mb-2">Font Pairing Rationale</h4>
                <p className="text-gray-700">{campaignData.brand_elements.typography.font_pairing_rationale}</p>
              </div>
            </CardContent>
          </Card>

          {/* Brand Elements */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Brand Personality</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-700">{campaignData.brand_elements.brand_personality}</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Visual Style</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-700">{campaignData.brand_elements.visual_style}</p>
              </CardContent>
            </Card>
          </div>

          {/* Logo Concepts */}
          <Card>
            <CardHeader>
              <CardTitle>Logo Concepts</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {campaignData.brand_elements.logo_concepts.map((concept, index) => (
                  <div key={index} className="p-4 bg-gray-50 rounded-lg">
                    <h4 className="font-medium mb-2">Concept {index + 1}</h4>
                    <p className="text-gray-700">{concept}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="visuals" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Image className="h-5 w-5" />
                Visual Assets
              </CardTitle>
              <CardDescription>
                Generated visual assets for your campaign
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {campaignData.visual_assets.map((asset, index) => (
                  <Card key={index}>
                    <CardContent className="p-4">
                      <div className="aspect-square bg-gray-100 rounded-lg mb-3 flex items-center justify-center">
                        <Image className="h-12 w-12 text-gray-400" />
                      </div>
                      <h4 className="font-medium mb-1">{asset.asset_type.replace('_', ' ').toUpperCase()}</h4>
                      <p className="text-sm text-gray-600 mb-2">{asset.description}</p>
                      <div className="flex flex-wrap gap-1">
                        {asset.platform_optimized.map((platform) => (
                          <Badge key={platform} variant="secondary" className="text-xs">
                            {platform}
                          </Badge>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
              <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                <p className="text-sm text-blue-800">
                  <strong>Note:</strong> This is a demo version. In the full implementation, actual images would be generated using DALL-E and displayed here.
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="recommendations" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Implementation Recommendations</CardTitle>
              <CardDescription>
                Strategic recommendations for campaign implementation and optimization
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {campaignData.recommendations.map((recommendation, index) => (
                  <div key={index} className="flex items-start gap-3 p-4 bg-gray-50 rounded-lg">
                    <div className="flex-shrink-0 w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-medium">
                      {index + 1}
                    </div>
                    <p className="text-gray-700">{recommendation}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="brief" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Original Campaign Brief</CardTitle>
              <CardDescription>
                The input parameters used to generate this campaign
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {/* Product Info */}
                <div>
                  <h3 className="text-lg font-semibold mb-3">Product Information</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Name</p>
                      <p>{campaignData.brief.product_info.name}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-600">Category</p>
                      <p>{campaignData.brief.product_info.category}</p>
                    </div>
                    <div className="md:col-span-2">
                      <p className="text-sm font-medium text-gray-600">Description</p>
                      <p>{campaignData.brief.product_info.description}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-600">Price Point</p>
                      <p className="capitalize">{campaignData.brief.product_info.price_point}</p>
                    </div>
                  </div>
                  
                  {campaignData.brief.product_info.key_features.length > 0 && (
                    <div className="mt-4">
                      <p className="text-sm font-medium text-gray-600 mb-2">Key Features</p>
                      <div className="flex flex-wrap gap-2">
                        {campaignData.brief.product_info.key_features.map((feature, index) => (
                          <Badge key={index} variant="outline">{feature}</Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                <Separator />

                {/* Demographics */}
                <div>
                  <h3 className="text-lg font-semibold mb-3">Target Demographics</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Age Range</p>
                      <p>{campaignData.brief.demographics.age_range[0]} - {campaignData.brief.demographics.age_range[1]} years</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-600">Income Level</p>
                      <p className="capitalize">{campaignData.brief.demographics.income_level}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-600">Education</p>
                      <p className="capitalize">{campaignData.brief.demographics.education_level}</p>
                    </div>
                  </div>
                  
                  <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <p className="text-sm font-medium text-gray-600 mb-2">Locations</p>
                      <div className="flex flex-wrap gap-1">
                        {campaignData.brief.demographics.geographic_location.map((location, index) => (
                          <Badge key={index} variant="secondary" className="text-xs">{location}</Badge>
                        ))}
                      </div>
                    </div>
                    
                    {campaignData.brief.demographics.interests.length > 0 && (
                      <div>
                        <p className="text-sm font-medium text-gray-600 mb-2">Interests</p>
                        <div className="flex flex-wrap gap-1">
                          {campaignData.brief.demographics.interests.map((interest, index) => (
                            <Badge key={index} variant="secondary" className="text-xs">{interest}</Badge>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {campaignData.brief.demographics.values.length > 0 && (
                      <div>
                        <p className="text-sm font-medium text-gray-600 mb-2">Values</p>
                        <div className="flex flex-wrap gap-1">
                          {campaignData.brief.demographics.values.map((value, index) => (
                            <Badge key={index} variant="secondary" className="text-xs">{value}</Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                <Separator />

                {/* Campaign Details */}
                <div>
                  <h3 className="text-lg font-semibold mb-3">Campaign Details</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm font-medium text-gray-600 mb-2">Objectives</p>
                      <div className="flex flex-wrap gap-1">
                        {campaignData.brief.objectives.map((objective, index) => (
                          <Badge key={index} variant="outline" className="capitalize">{objective}</Badge>
                        ))}
                      </div>
                    </div>
                    
                    <div>
                      <p className="text-sm font-medium text-gray-600 mb-2">Platforms</p>
                      <div className="flex flex-wrap gap-1">
                        {campaignData.brief.platforms.map((platform, index) => (
                          <Badge key={index} variant="outline" className="capitalize">{platform.replace('_', ' ')}</Badge>
                        ))}
                      </div>
                    </div>
                    
                    {campaignData.brief.budget_range && (
                      <div>
                        <p className="text-sm font-medium text-gray-600">Budget Range</p>
                        <p>{campaignData.brief.budget_range}</p>
                      </div>
                    )}
                    
                    {campaignData.brief.timeline && (
                      <div>
                        <p className="text-sm font-medium text-gray-600">Timeline</p>
                        <p>{campaignData.brief.timeline}</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default CampaignResults;

