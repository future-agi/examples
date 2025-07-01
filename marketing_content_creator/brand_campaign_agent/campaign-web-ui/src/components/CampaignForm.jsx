import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { Label } from './ui/label';
import { Checkbox } from './ui/checkbox';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Badge } from './ui/badge';
import { X, Plus } from 'lucide-react';
import { toast } from 'sonner';

const campaignSchema = z.object({
  productName: z.string().min(1, 'Product name is required'),
  productCategory: z.string().min(1, 'Product category is required'),
  productDescription: z.string().min(10, 'Description must be at least 10 characters'),
  pricePoint: z.string().min(1, 'Price point is required'),
  ageMin: z.number().min(13).max(100),
  ageMax: z.number().min(13).max(100),
  incomeLevel: z.string().min(1, 'Income level is required'),
  educationLevel: z.string().min(1, 'Education level is required'),
  budgetRange: z.string().optional(),
  timeline: z.string().optional(),
  additionalContext: z.string().optional(),
});

const CampaignForm = ({ onStartGeneration, onCampaignGenerated }) => {
  const [keyFeatures, setKeyFeatures] = useState([]);
  const [usps, setUsps] = useState([]);
  const [locations, setLocations] = useState(['United States']);
  const [interests, setInterests] = useState([]);
  const [values, setValues] = useState([]);
  const [objectives, setObjectives] = useState([]);
  const [platforms, setPlatforms] = useState([]);
  const [newFeature, setNewFeature] = useState('');
  const [newUsp, setNewUsp] = useState('');
  const [newLocation, setNewLocation] = useState('');
  const [newInterest, setNewInterest] = useState('');
  const [newValue, setNewValue] = useState('');

  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
    watch
  } = useForm({
    resolver: zodResolver(campaignSchema),
    defaultValues: {
      ageMin: 25,
      ageMax: 45,
      pricePoint: 'mid-range',
      incomeLevel: 'medium',
      educationLevel: 'college'
    }
  });

  const objectiveOptions = [
    { id: 'awareness', label: 'Brand Awareness' },
    { id: 'conversion', label: 'Conversion' },
    { id: 'retention', label: 'Customer Retention' },
    { id: 'engagement', label: 'Engagement' }
  ];

  const platformOptions = [
    { id: 'facebook', label: 'Facebook' },
    { id: 'instagram', label: 'Instagram' },
    { id: 'twitter', label: 'Twitter' },
    { id: 'linkedin', label: 'LinkedIn' },
    { id: 'google_ads', label: 'Google Ads' },
    { id: 'email', label: 'Email' },
    { id: 'website', label: 'Website' },
    { id: 'print', label: 'Print' }
  ];

  const addItem = (item, setItems, items, setNewItem) => {
    if (item.trim() && !items.includes(item.trim())) {
      setItems([...items, item.trim()]);
      setNewItem('');
    }
  };

  const removeItem = (index, setItems, items) => {
    setItems(items.filter((_, i) => i !== index));
  };

  const toggleSelection = (id, selected, setSelected) => {
    if (selected.includes(id)) {
      setSelected(selected.filter(item => item !== id));
    } else {
      setSelected([...selected, id]);
    }
  };

  const onSubmit = async (data) => {
    if (keyFeatures.length === 0) {
      toast.error('Please add at least one key feature');
      return;
    }
    if (objectives.length === 0) {
      toast.error('Please select at least one campaign objective');
      return;
    }
    if (platforms.length === 0) {
      toast.error('Please select at least one platform');
      return;
    }

    const campaignBrief = {
      product_info: {
        name: data.productName,
        category: data.productCategory,
        description: data.productDescription,
        key_features: keyFeatures,
        price_point: data.pricePoint,
        unique_selling_propositions: usps,
        competitors: []
      },
      demographics: {
        age_range: [data.ageMin, data.ageMax],
        gender_distribution: { male: 50.0, female: 50.0 },
        income_level: data.incomeLevel,
        geographic_location: locations,
        education_level: data.educationLevel,
        interests: interests,
        values: values
      },
      objectives: objectives,
      platforms: platforms,
      budget_range: data.budgetRange || null,
      timeline: data.timeline || null,
      additional_context: data.additionalContext || null
    };

    onStartGeneration();
    
    // Simulate API call - in real implementation, this would call your Python backend
    setTimeout(() => {
      const mockCampaignData = {
        campaign_id: 'demo-' + Date.now(),
        brief: campaignBrief,
        text_content: {
          headlines: [
            `Revolutionize Your ${data.productCategory} Experience`,
            `The Future of ${data.productCategory} is Here`,
            `Discover ${data.productName} - Innovation Redefined`
          ],
          taglines: [
            'Innovation Meets Excellence',
            'Your Perfect Solution',
            'Beyond Expectations'
          ],
          ad_copy: {
            facebook: [
              `Transform your daily routine with ${data.productName}. Experience the difference that quality makes.`,
              `Join thousands who've already discovered the power of ${data.productName}. Your journey starts here.`
            ],
            instagram: [
              `✨ Elevate your lifestyle with ${data.productName} ✨ #Innovation #Quality #Lifestyle`,
              `Ready to experience something extraordinary? ${data.productName} delivers. 📸 #GameChanger`
            ]
          },
          product_descriptions: [
            `${data.productName} represents the pinnacle of ${data.productCategory} innovation. ${data.productDescription}`,
            `Experience unmatched quality with ${data.productName}. Designed for those who demand excellence in every detail.`
          ],
          call_to_actions: [
            'Shop Now',
            'Learn More',
            'Get Started Today',
            'Join the Revolution',
            'Discover More'
          ]
        },
        brand_elements: {
          color_palette: {
            primary: '#2563eb',
            secondary: '#64748b',
            accent: '#f59e0b',
            neutral: '#6b7280',
            background: '#ffffff',
            text: '#1f2937',
            psychology: 'Professional blue conveys trust and reliability, while warm accent colors add energy and optimism.'
          },
          typography: {
            primary_font: 'Inter',
            secondary_font: 'Merriweather',
            heading_style: 'Bold, modern sans-serif for impact and clarity',
            body_style: 'Clean, readable serif for trust and professionalism',
            font_pairing_rationale: 'Modern sans-serif paired with classic serif creates perfect balance between innovation and trust'
          },
          logo_concepts: [
            'Modern wordmark with clean typography and subtle geometric elements',
            'Icon-based logo featuring abstract representation of key product benefits',
            'Combination mark balancing text and symbol for versatile brand applications'
          ],
          visual_style: 'Clean, modern aesthetic with professional photography and minimalist design elements',
          brand_personality: 'Innovative, trustworthy, and customer-focused with a commitment to quality and excellence'
        },
        visual_assets: [
          {
            filename: 'hero_image_1.png',
            asset_type: 'hero_image',
            description: 'Lifestyle hero image showcasing product in use',
            dimensions: [1024, 1024],
            platform_optimized: ['website', 'facebook']
          }
        ],
        campaign_summary: `This comprehensive campaign for ${data.productName} targets ${data.ageMin}-${data.ageMax} year olds with a focus on ${objectives.join(', ')}. The campaign leverages multiple platforms including ${platforms.join(', ')} to maximize reach and engagement.`,
        recommendations: [
          'A/B test headlines across different platforms to optimize performance',
          'Implement retargeting campaigns for users who engage with initial content',
          'Monitor brand sentiment and adjust messaging based on audience feedback',
          'Create platform-specific content calendars for consistent posting',
          'Track conversion metrics and optimize budget allocation accordingly'
        ],
        created_at: new Date().toISOString()
      };
      
      onCampaignGenerated(mockCampaignData);
      toast.success('Campaign generated successfully!');
    }, 3000);
  };

  return (
    <Card className="w-full max-w-4xl mx-auto">
      <CardHeader>
        <CardTitle>Create Your Campaign Brief</CardTitle>
        <CardDescription>
          Fill out the form below to generate a comprehensive brand campaign
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          <Tabs defaultValue="product" className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="product">Product</TabsTrigger>
              <TabsTrigger value="audience">Audience</TabsTrigger>
              <TabsTrigger value="campaign">Campaign</TabsTrigger>
              <TabsTrigger value="additional">Additional</TabsTrigger>
            </TabsList>

            <TabsContent value="product" className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="productName">Product Name *</Label>
                  <Input
                    id="productName"
                    {...register('productName')}
                    placeholder="e.g., EcoSmart Water Bottle"
                  />
                  {errors.productName && (
                    <p className="text-sm text-red-600">{errors.productName.message}</p>
                  )}
                </div>
                <div>
                  <Label htmlFor="productCategory">Category *</Label>
                  <Input
                    id="productCategory"
                    {...register('productCategory')}
                    placeholder="e.g., sustainable lifestyle product"
                  />
                  {errors.productCategory && (
                    <p className="text-sm text-red-600">{errors.productCategory.message}</p>
                  )}
                </div>
              </div>

              <div>
                <Label htmlFor="productDescription">Product Description *</Label>
                <Textarea
                  id="productDescription"
                  {...register('productDescription')}
                  placeholder="Describe your product or service..."
                  rows={3}
                />
                {errors.productDescription && (
                  <p className="text-sm text-red-600">{errors.productDescription.message}</p>
                )}
              </div>

              <div>
                <Label htmlFor="pricePoint">Price Positioning *</Label>
                <Select onValueChange={(value) => setValue('pricePoint', value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select price point" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="budget">Budget</SelectItem>
                    <SelectItem value="mid-range">Mid-range</SelectItem>
                    <SelectItem value="premium">Premium</SelectItem>
                    <SelectItem value="luxury">Luxury</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label>Key Features *</Label>
                <div className="flex gap-2 mb-2">
                  <Input
                    value={newFeature}
                    onChange={(e) => setNewFeature(e.target.value)}
                    placeholder="Add a key feature..."
                    onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addItem(newFeature, setKeyFeatures, keyFeatures, setNewFeature))}
                  />
                  <Button
                    type="button"
                    onClick={() => addItem(newFeature, setKeyFeatures, keyFeatures, setNewFeature)}
                    size="sm"
                  >
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {keyFeatures.map((feature, index) => (
                    <Badge key={index} variant="secondary" className="flex items-center gap-1">
                      {feature}
                      <X
                        className="h-3 w-3 cursor-pointer"
                        onClick={() => removeItem(index, setKeyFeatures, keyFeatures)}
                      />
                    </Badge>
                  ))}
                </div>
              </div>

              <div>
                <Label>Unique Selling Propositions</Label>
                <div className="flex gap-2 mb-2">
                  <Input
                    value={newUsp}
                    onChange={(e) => setNewUsp(e.target.value)}
                    placeholder="Add a USP..."
                    onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addItem(newUsp, setUsps, usps, setNewUsp))}
                  />
                  <Button
                    type="button"
                    onClick={() => addItem(newUsp, setUsps, usps, setNewUsp)}
                    size="sm"
                  >
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {usps.map((usp, index) => (
                    <Badge key={index} variant="secondary" className="flex items-center gap-1">
                      {usp}
                      <X
                        className="h-3 w-3 cursor-pointer"
                        onClick={() => removeItem(index, setUsps, usps)}
                      />
                    </Badge>
                  ))}
                </div>
              </div>
            </TabsContent>

            <TabsContent value="audience" className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="ageMin">Minimum Age *</Label>
                  <Input
                    id="ageMin"
                    type="number"
                    {...register('ageMin', { valueAsNumber: true })}
                    min="13"
                    max="100"
                  />
                </div>
                <div>
                  <Label htmlFor="ageMax">Maximum Age *</Label>
                  <Input
                    id="ageMax"
                    type="number"
                    {...register('ageMax', { valueAsNumber: true })}
                    min="13"
                    max="100"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="incomeLevel">Income Level *</Label>
                  <Select onValueChange={(value) => setValue('incomeLevel', value)}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select income level" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="low">Low</SelectItem>
                      <SelectItem value="medium">Medium</SelectItem>
                      <SelectItem value="high">High</SelectItem>
                      <SelectItem value="luxury">Luxury</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="educationLevel">Education Level *</Label>
                  <Select onValueChange={(value) => setValue('educationLevel', value)}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select education level" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="high-school">High School</SelectItem>
                      <SelectItem value="college">College</SelectItem>
                      <SelectItem value="graduate">Graduate</SelectItem>
                      <SelectItem value="mixed">Mixed</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div>
                <Label>Target Locations</Label>
                <div className="flex gap-2 mb-2">
                  <Input
                    value={newLocation}
                    onChange={(e) => setNewLocation(e.target.value)}
                    placeholder="Add a location..."
                    onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addItem(newLocation, setLocations, locations, setNewLocation))}
                  />
                  <Button
                    type="button"
                    onClick={() => addItem(newLocation, setLocations, locations, setNewLocation)}
                    size="sm"
                  >
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {locations.map((location, index) => (
                    <Badge key={index} variant="secondary" className="flex items-center gap-1">
                      {location}
                      <X
                        className="h-3 w-3 cursor-pointer"
                        onClick={() => removeItem(index, setLocations, locations)}
                      />
                    </Badge>
                  ))}
                </div>
              </div>

              <div>
                <Label>Interests</Label>
                <div className="flex gap-2 mb-2">
                  <Input
                    value={newInterest}
                    onChange={(e) => setNewInterest(e.target.value)}
                    placeholder="Add an interest..."
                    onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addItem(newInterest, setInterests, interests, setNewInterest))}
                  />
                  <Button
                    type="button"
                    onClick={() => addItem(newInterest, setInterests, interests, setNewInterest)}
                    size="sm"
                  >
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {interests.map((interest, index) => (
                    <Badge key={index} variant="secondary" className="flex items-center gap-1">
                      {interest}
                      <X
                        className="h-3 w-3 cursor-pointer"
                        onClick={() => removeItem(index, setInterests, interests)}
                      />
                    </Badge>
                  ))}
                </div>
              </div>

              <div>
                <Label>Values</Label>
                <div className="flex gap-2 mb-2">
                  <Input
                    value={newValue}
                    onChange={(e) => setNewValue(e.target.value)}
                    placeholder="Add a value..."
                    onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addItem(newValue, setValues, values, setNewValue))}
                  />
                  <Button
                    type="button"
                    onClick={() => addItem(newValue, setValues, values, setNewValue)}
                    size="sm"
                  >
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {values.map((value, index) => (
                    <Badge key={index} variant="secondary" className="flex items-center gap-1">
                      {value}
                      <X
                        className="h-3 w-3 cursor-pointer"
                        onClick={() => removeItem(index, setValues, values)}
                      />
                    </Badge>
                  ))}
                </div>
              </div>
            </TabsContent>

            <TabsContent value="campaign" className="space-y-4">
              <div>
                <Label>Campaign Objectives *</Label>
                <div className="grid grid-cols-2 gap-2 mt-2">
                  {objectiveOptions.map((objective) => (
                    <div key={objective.id} className="flex items-center space-x-2">
                      <Checkbox
                        id={objective.id}
                        checked={objectives.includes(objective.id)}
                        onCheckedChange={() => toggleSelection(objective.id, objectives, setObjectives)}
                      />
                      <Label htmlFor={objective.id}>{objective.label}</Label>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <Label>Target Platforms *</Label>
                <div className="grid grid-cols-2 gap-2 mt-2">
                  {platformOptions.map((platform) => (
                    <div key={platform.id} className="flex items-center space-x-2">
                      <Checkbox
                        id={platform.id}
                        checked={platforms.includes(platform.id)}
                        onCheckedChange={() => toggleSelection(platform.id, platforms, setPlatforms)}
                      />
                      <Label htmlFor={platform.id}>{platform.label}</Label>
                    </div>
                  ))}
                </div>
              </div>
            </TabsContent>

            <TabsContent value="additional" className="space-y-4">
              <div>
                <Label htmlFor="budgetRange">Budget Range</Label>
                <Input
                  id="budgetRange"
                  {...register('budgetRange')}
                  placeholder="e.g., $10,000 - $50,000"
                />
              </div>

              <div>
                <Label htmlFor="timeline">Timeline</Label>
                <Input
                  id="timeline"
                  {...register('timeline')}
                  placeholder="e.g., 6 weeks"
                />
              </div>

              <div>
                <Label htmlFor="additionalContext">Additional Context</Label>
                <Textarea
                  id="additionalContext"
                  {...register('additionalContext')}
                  placeholder="Any additional information about your campaign..."
                  rows={3}
                />
              </div>
            </TabsContent>
          </Tabs>

          <div className="flex justify-end">
            <Button type="submit" size="lg" className="px-8">
              Generate Campaign
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
};

export default CampaignForm;

