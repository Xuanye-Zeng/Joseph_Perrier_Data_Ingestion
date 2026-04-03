"""Dataclass models for the Joseph Perrier data ingestion project."""

from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class Winery:
    """Represents the Joseph Perrier winery/champagne house."""
    name: str
    location: Optional[str] = None
    founded_year: Optional[int] = None
    description: Optional[str] = None
    website_url: Optional[str] = None
    vineyard_hectares: Optional[float] = None
    cellar_description: Optional[str] = None
    awards_honors: Optional[str] = None


@dataclass
class WineryHistory:
    """A single historical event in the winery timeline."""
    year: Optional[int] = None
    event_description: Optional[str] = None


@dataclass
class TeamMember:
    """A member of the Joseph Perrier family or team."""
    name: str
    role: Optional[str] = None
    generation: Optional[str] = None
    bio: Optional[str] = None
    image_url: Optional[str] = None


@dataclass
class TastingNote:
    """Structured tasting notes for a product."""
    color_description: Optional[str] = None
    nose_description: Optional[str] = None
    palate_description: Optional[str] = None
    serving_suggestion: Optional[str] = None


@dataclass
class FoodPairing:
    """A food pairing suggestion for a product."""
    description: str


@dataclass
class ProductFormat:
    """A bottle format/size for a product."""
    format_name: str
    volume_cl: Optional[int] = None


@dataclass
class Media:
    """An image or video asset linked to a product, winery, or article."""
    media_type: str
    url: str
    alt_text: Optional[str] = None
    context: Optional[str] = None


@dataclass
class ProductTechnical:
    """Technical specifications for a champagne product."""
    aging_months: Optional[int] = None
    dosage_gl: Optional[float] = None
    reserve_wines_pct: Optional[float] = None
    serving_temp_min: Optional[int] = None
    serving_temp_max: Optional[int] = None
    aging_potential: Optional[str] = None
    crus: Optional[str] = None

@dataclass
class ProductAward:
    """An award or rating for a product."""
    organization: str
    detail: Optional[str] = None
    year: Optional[str] = None
    medal: Optional[str] = None
    score: Optional[str] = None
    logo_url: Optional[str] = None


@dataclass
class Product:
    """A champagne cuvee product."""
    name: str
    collection: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    grape_blend: Optional[str] = None
    price_eur: Optional[float] = None
    vintage: Optional[str] = None
    is_limited_edition: bool = False
    source_url: Optional[str] = None
    tasting_notes: List[TastingNote] = field(default_factory=list)
    food_pairings: List[FoodPairing] = field(default_factory=list)
    formats: List[ProductFormat] = field(default_factory=list)
    media: List[Media] = field(default_factory=list)
    technical: Optional['ProductTechnical'] = None
    awards: List['ProductAward'] = field(default_factory=list)


@dataclass
class Article:
    """A blog or editorial article from jojo-mag."""
    title: str
    summary: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None
    published_date: Optional[str] = None
    source_url: Optional[str] = None
    image_url: Optional[str] = None
    category: Optional[str] = None
