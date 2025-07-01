"""
Command-line interface for the Brand Campaign Agent
"""
import os
import json
import yaml
from typing import List, Optional
import typer
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from dotenv import load_dotenv

from .models import (
    CampaignBrief, ProductInfo, Demographics, CampaignObjective, 
    PlatformType, GenerationConfig
)
from .campaign_orchestrator import CampaignOrchestrator

# Load environment variables
load_dotenv()

app = typer.Typer(help="Brand Campaign Agent - Generate comprehensive brand campaigns using AI")
console = Console()


def load_config(config_path: str = "config/config.yaml") -> GenerationConfig:
    """Load configuration from YAML file"""
    try:
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # Get OpenAI API key from environment
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            console.print("[red]Error: OPENAI_API_KEY environment variable not set[/red]")
            raise typer.Exit(1)
        
        return GenerationConfig(
            openai_api_key=api_key,
            model_text=config_data['openai']['model_text'],
            model_image=config_data['openai']['model_image'],
            max_tokens=config_data['openai']['max_tokens'],
            temperature=config_data['openai']['temperature'],
            image_size=config_data['image_generation']['size'],
            image_quality=config_data['image_generation']['quality'],
            output_directory=config_data['output']['directory'],
            enable_image_generation=config_data['image_generation']['enabled'],
            enable_brand_analysis=config_data['brand_analysis']['enabled'],
            max_headlines=config_data['content_limits']['max_headlines'],
            max_taglines=config_data['content_limits']['max_taglines'],
            max_ad_copy_variants=config_data['content_limits']['max_ad_copy_variants']
        )
    except FileNotFoundError:
        console.print(f"[red]Config file not found: {config_path}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error loading config: {e}[/red]")
        raise typer.Exit(1)


def interactive_campaign_brief() -> CampaignBrief:
    """Create campaign brief through interactive prompts"""
    console.print(Panel.fit("🚀 Brand Campaign Generator", style="bold blue"))
    console.print("Let's create your campaign brief step by step.\n")
    
    # Product Information
    console.print("[bold cyan]Product Information[/bold cyan]")
    product_name = Prompt.ask("Product/Service name")
    product_category = Prompt.ask("Product category (e.g., 'tech gadget', 'fashion', 'food')")
    product_description = Prompt.ask("Brief product description")
    
    # Key features
    console.print("\nEnter key features (press Enter after each, empty line to finish):")
    key_features = []
    while True:
        feature = Prompt.ask("Feature", default="")
        if not feature:
            break
        key_features.append(feature)
    
    price_point = Prompt.ask(
        "Price positioning", 
        choices=["budget", "mid-range", "premium", "luxury"],
        default="mid-range"
    )
    
    # USPs
    console.print("\nEnter unique selling propositions (press Enter after each, empty line to finish):")
    usps = []
    while True:
        usp = Prompt.ask("USP", default="")
        if not usp:
            break
        usps.append(usp)
    
    product_info = ProductInfo(
        name=product_name,
        category=product_category,
        description=product_description,
        key_features=key_features,
        price_point=price_point,
        unique_selling_propositions=usps
    )
    
    # Demographics
    console.print("\n[bold cyan]Target Demographics[/bold cyan]")
    age_min = typer.prompt("Minimum age", type=int, default=18)
    age_max = typer.prompt("Maximum age", type=int, default=65)
    
    income_level = Prompt.ask(
        "Income level",
        choices=["low", "medium", "high", "luxury"],
        default="medium"
    )
    
    education_level = Prompt.ask(
        "Education level",
        choices=["high-school", "college", "graduate", "mixed"],
        default="college"
    )
    
    # Geographic locations
    console.print("\nEnter target locations (press Enter after each, empty line to finish):")
    locations = []
    while True:
        location = Prompt.ask("Location", default="")
        if not location:
            break
        locations.append(location)
    
    if not locations:
        locations = ["United States"]
    
    # Interests
    console.print("\nEnter target interests (press Enter after each, empty line to finish):")
    interests = []
    while True:
        interest = Prompt.ask("Interest", default="")
        if not interest:
            break
        interests.append(interest)
    
    # Values
    console.print("\nEnter target values (press Enter after each, empty line to finish):")
    values = []
    while True:
        value = Prompt.ask("Value", default="")
        if not value:
            break
        values.append(value)
    
    demographics = Demographics(
        age_range=(age_min, age_max),
        income_level=income_level,
        geographic_location=locations,
        education_level=education_level,
        interests=interests,
        values=values
    )
    
    # Campaign Objectives
    console.print("\n[bold cyan]Campaign Objectives[/bold cyan]")
    console.print("Select campaign objectives:")
    
    objective_choices = {
        "1": CampaignObjective.AWARENESS,
        "2": CampaignObjective.CONVERSION,
        "3": CampaignObjective.RETENTION,
        "4": CampaignObjective.ENGAGEMENT
    }
    
    console.print("1. Awareness")
    console.print("2. Conversion")
    console.print("3. Retention")
    console.print("4. Engagement")
    
    selected_objectives = []
    while True:
        choice = Prompt.ask("Select objective (1-4, or 'done' to finish)", default="done")
        if choice.lower() == 'done':
            break
        if choice in objective_choices:
            obj = objective_choices[choice]
            if obj not in selected_objectives:
                selected_objectives.append(obj)
                console.print(f"Added: {obj.value}")
            else:
                console.print("Already selected")
        else:
            console.print("Invalid choice")
    
    if not selected_objectives:
        selected_objectives = [CampaignObjective.AWARENESS]
    
    # Platforms
    console.print("\n[bold cyan]Target Platforms[/bold cyan]")
    console.print("Select target platforms:")
    
    platform_choices = {
        "1": PlatformType.FACEBOOK,
        "2": PlatformType.INSTAGRAM,
        "3": PlatformType.TWITTER,
        "4": PlatformType.LINKEDIN,
        "5": PlatformType.GOOGLE_ADS,
        "6": PlatformType.EMAIL,
        "7": PlatformType.WEBSITE,
        "8": PlatformType.PRINT
    }
    
    for key, platform in platform_choices.items():
        console.print(f"{key}. {platform.value.title()}")
    
    selected_platforms = []
    while True:
        choice = Prompt.ask("Select platform (1-8, or 'done' to finish)", default="done")
        if choice.lower() == 'done':
            break
        if choice in platform_choices:
            platform = platform_choices[choice]
            if platform not in selected_platforms:
                selected_platforms.append(platform)
                console.print(f"Added: {platform.value}")
            else:
                console.print("Already selected")
        else:
            console.print("Invalid choice")
    
    if not selected_platforms:
        selected_platforms = [PlatformType.FACEBOOK, PlatformType.INSTAGRAM]
    
    # Additional context
    console.print("\n[bold cyan]Additional Information[/bold cyan]")
    budget_range = Prompt.ask("Budget range (optional)", default="")
    timeline = Prompt.ask("Timeline (optional)", default="")
    additional_context = Prompt.ask("Additional context (optional)", default="")
    
    return CampaignBrief(
        product_info=product_info,
        demographics=demographics,
        objectives=selected_objectives,
        platforms=selected_platforms,
        budget_range=budget_range if budget_range else None,
        timeline=timeline if timeline else None,
        additional_context=additional_context if additional_context else None
    )


@app.command()
def generate(
    config_file: str = typer.Option("config/config.yaml", help="Configuration file path"),
    brief_file: Optional[str] = typer.Option(None, help="JSON file with campaign brief"),
    interactive: bool = typer.Option(True, help="Use interactive mode"),
    output_dir: Optional[str] = typer.Option(None, help="Output directory override")
):
    """Generate a complete brand campaign"""
    
    # Load configuration
    config = load_config(config_file)
    
    if output_dir:
        config.output_directory = output_dir
    
    # Get campaign brief
    if brief_file:
        try:
            with open(brief_file, 'r') as f:
                brief_data = json.load(f)
            brief = CampaignBrief(**brief_data)
            console.print(f"[green]Loaded campaign brief from {brief_file}[/green]")
        except Exception as e:
            console.print(f"[red]Error loading brief file: {e}[/red]")
            raise typer.Exit(1)
    elif interactive:
        brief = interactive_campaign_brief()
    else:
        console.print("[red]Either provide a brief file or use interactive mode[/red]")
        raise typer.Exit(1)
    
    # Display brief summary
    console.print("\n" + "="*60)
    console.print("[bold green]Campaign Brief Summary[/bold green]")
    console.print(f"Product: {brief.product_info.name}")
    console.print(f"Category: {brief.product_info.category}")
    console.print(f"Target Age: {brief.demographics.age_range[0]}-{brief.demographics.age_range[1]}")
    console.print(f"Objectives: {', '.join([obj.value for obj in brief.objectives])}")
    console.print(f"Platforms: {', '.join([p.value for p in brief.platforms])}")
    console.print("="*60 + "\n")
    
    if not Confirm.ask("Proceed with campaign generation?"):
        console.print("Campaign generation cancelled.")
        raise typer.Exit(0)
    
    # Generate campaign
    try:
        orchestrator = CampaignOrchestrator(config)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Generating campaign...", total=None)
            campaign_output = orchestrator.generate_complete_campaign(brief)
        
        # Display results summary
        console.print("\n[bold green]✅ Campaign Generated Successfully![/bold green]")
        
        # Create results table
        table = Table(title="Campaign Results")
        table.add_column("Component", style="cyan")
        table.add_column("Count", style="magenta")
        table.add_column("Details", style="green")
        
        table.add_row("Headlines", str(len(campaign_output.text_content.headlines)), 
                     ", ".join(campaign_output.text_content.headlines[:2]) + "...")
        table.add_row("Taglines", str(len(campaign_output.text_content.taglines)),
                     ", ".join(campaign_output.text_content.taglines))
        table.add_row("Ad Copy Platforms", str(len(campaign_output.text_content.ad_copy)),
                     ", ".join(campaign_output.text_content.ad_copy.keys()))
        table.add_row("Visual Assets", str(len(campaign_output.visual_assets)),
                     f"{len([a for a in campaign_output.visual_assets if a.asset_type == 'hero_image'])} hero, "
                     f"{len([a for a in campaign_output.visual_assets if a.asset_type == 'social_media'])} social")
        table.add_row("Brand Colors", "6", 
                     f"Primary: {campaign_output.brand_elements.color_palette.primary}")
        
        console.print(table)
        
        # Show output location
        output_path = os.path.join(config.output_directory, f"campaign_{campaign_output.campaign_id}")
        console.print(f"\n[bold blue]📁 Campaign files saved to:[/bold blue] {output_path}")
        console.print(f"[dim]View campaign_summary.md for a complete overview[/dim]")
        
    except Exception as e:
        console.print(f"[red]❌ Campaign generation failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def example():
    """Generate an example campaign brief file"""
    example_brief = {
        "product_info": {
            "name": "EcoSmart Water Bottle",
            "category": "sustainable lifestyle product",
            "description": "A smart water bottle that tracks hydration and is made from recycled materials",
            "key_features": [
                "Smart hydration tracking",
                "Made from 100% recycled materials",
                "Temperature control technology",
                "Mobile app integration"
            ],
            "price_point": "premium",
            "unique_selling_propositions": [
                "First fully recycled smart water bottle",
                "AI-powered hydration coaching",
                "Carbon-neutral manufacturing"
            ],
            "competitors": ["Hydro Flask", "S'well", "Yeti"]
        },
        "demographics": {
            "age_range": [25, 45],
            "gender_distribution": {"male": 40.0, "female": 60.0},
            "income_level": "high",
            "geographic_location": ["United States", "Canada", "Western Europe"],
            "education_level": "college",
            "interests": ["fitness", "sustainability", "technology", "wellness"],
            "values": ["environmental responsibility", "health consciousness", "innovation"]
        },
        "objectives": ["awareness", "conversion"],
        "platforms": ["instagram", "facebook", "google_ads", "website"],
        "budget_range": "$50,000 - $100,000",
        "timeline": "6 weeks",
        "additional_context": "Launching during Earth Day season to maximize environmental messaging impact"
    }
    
    filename = "example_campaign_brief.json"
    with open(filename, 'w') as f:
        json.dump(example_brief, f, indent=2)
    
    console.print(f"[green]✅ Example campaign brief saved to {filename}[/green]")
    console.print(f"[dim]Use: python -m src.cli generate --brief-file {filename} --interactive false[/dim]")


@app.command()
def config():
    """Show current configuration"""
    try:
        config = load_config()
        
        table = Table(title="Current Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Text Model", config.model_text)
        table.add_row("Image Model", config.model_image)
        table.add_row("Max Tokens", str(config.max_tokens))
        table.add_row("Temperature", str(config.temperature))
        table.add_row("Image Size", config.image_size)
        table.add_row("Output Directory", config.output_directory)
        table.add_row("Image Generation", "Enabled" if config.enable_image_generation else "Disabled")
        table.add_row("Max Headlines", str(config.max_headlines))
        table.add_row("Max Taglines", str(config.max_taglines))
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error loading configuration: {e}[/red]")


if __name__ == "__main__":
    app()

