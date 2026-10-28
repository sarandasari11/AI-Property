"""
Input validation module for AI Property Video Generator.
Guarantees graceful error reporting when property details or images are missing/invalid.
"""
from pathlib import Path
from typing import List, Optional, Tuple
from pydantic import BaseModel, Field, field_validator
from PIL import Image

from config import MIN_PROPERTY_IMAGES, MAX_PROPERTY_IMAGES


class PropertyInput(BaseModel):
    """Structured data model for a real estate listing."""
    name: str = Field(..., description="Property name / title (e.g. 'Emerald Bay Penthouse')")
    location: str = Field(..., description="Location / City / Neighborhood")
    price: str = Field(..., description="Asking price (e.g. '$1,250,000' or '₹2.8 Cr')")
    property_type: str = Field(..., description="Type (e.g. '3-BHK Luxury Apartment', 'Villa', 'Condo')")
    features: List[str] = Field(..., min_length=1, description="List of key features / highlights")
    contact_cta: str = Field(..., description="Contact / Call to action (e.g. 'Call +1-555-0199 or visit example.com')")
    image_paths: List[str] = Field(..., description="Paths to 4-8 property photos")

    @field_validator("name", "location", "price", "property_type", "contact_cta")
    @classmethod
    def ensure_non_empty(cls, v: str, info) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError(f"'{info.field_name.replace('_', ' ').title()}' cannot be empty.")
        return trimmed

    @field_validator("features")
    @classmethod
    def ensure_valid_features(cls, features: List[str]) -> List[str]:
        cleaned = [f.strip() for f in features if f.strip()]
        if not cleaned:
            raise ValueError("At least one key property feature must be provided.")
        return cleaned


def validate_property_input(
    name: str,
    location: str,
    price: str,
    property_type: str,
    features: List[str],
    contact_cta: str,
    image_paths: List[str],
) -> Tuple[bool, Optional[PropertyInput], List[str]]:
    """
    Validates all property input fields and image files gracefully.
    Returns:
        (is_valid: bool, property_data: PropertyInput | None, errors: List[str])
    """
    errors: List[str] = []

    # 1. Image count check (4-8 images as specified in assignment)
    if not image_paths:
        errors.append(f"No property images provided. Please provide between {MIN_PROPERTY_IMAGES} and {MAX_PROPERTY_IMAGES} images.")
    elif len(image_paths) < MIN_PROPERTY_IMAGES:
        errors.append(
            f"Insufficient images: Found {len(image_paths)}, but a minimum of {MIN_PROPERTY_IMAGES} images is required to construct a coherent property tour."
        )
    elif len(image_paths) > MAX_PROPERTY_IMAGES:
        errors.append(
            f"Too many images: Found {len(image_paths)}. Please provide at most {MAX_PROPERTY_IMAGES} images for an optimal 20-40 second video."
        )

    # 2. Check if each image file exists and is a valid image
    valid_images: List[str] = []
    if image_paths:
        for idx, img_path in enumerate(image_paths, 1):
            p = Path(img_path)
            if not p.exists():
                errors.append(f"Image #{idx} does not exist: '{img_path}'.")
                continue
            if not p.is_file():
                errors.append(f"Image #{idx} path is not a file: '{img_path}'.")
                continue
            try:
                with Image.open(p) as img:
                    img.verify()
                valid_images.append(str(p.resolve()))
            except Exception as e:
                errors.append(f"Image #{idx} ('{p.name}') is corrupt or not a supported image format ({e}).")

    # 3. Model validation
    try:
        validated_model = PropertyInput(
            name=name,
            location=location,
            price=price,
            property_type=property_type,
            features=features,
            contact_cta=contact_cta,
            image_paths=valid_images if not errors else image_paths,
        )
    except Exception as e:
        if hasattr(e, "errors"):
            for err in e.errors():
                loc = " -> ".join(str(l) for l in err.get("loc", []))
                errors.append(f"Field error [{loc}]: {err.get('msg')}")
        else:
            errors.append(str(e))
        validated_model = None

    if errors:
        return False, None, errors

    return True, validated_model, []
