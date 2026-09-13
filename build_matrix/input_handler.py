"""
BUILD-MATRIX.ai Input Handler & Prompt Parser
Processes user natural language prompts and numerical plot parameters into structured architectural building configurations.
"""

import os
import re
import math
import json
from typing import Dict, List, Tuple, Any
from .models import PlotDimensions, ArchitecturalStyle





class InputHandler:
    """Parses natural language prompts and user plot parameters into normalized architectural constraints."""

    WORD_TO_NUM = {
        "one": 1, "a": 1, "single": 1,
        "two": 2, "double": 2, "twin": 2,
        "three": 3, "triple": 3,
        "four": 4, "quad": 4,
        "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
        "eleven": 11, "twelve": 12,
    }

    STYLE_KEYWORDS = {
        ArchitecturalStyle.MODERN: ["modern", "contemporary", "sleek", "glass", "minimal", "open plan"],
        ArchitecturalStyle.MINIMALIST: ["minimalist", "clean lines", "uncluttered"],
        ArchitecturalStyle.CLASSIC: ["classic", "traditional", "colonial", "georgian", "victorian"],
        ArchitecturalStyle.INDUSTRIAL: ["industrial", "loft", "exposed beam", "brick", "raw steel", "warehouse"],
        ArchitecturalStyle.BRUTALIST: ["brutalist", "concrete", "monolithic", "heavy", "geometric block"],
        ArchitecturalStyle.LUXURY_VILLA: ["luxury", "villa", "mansion", "estate", "patio", "pool villa"],
        ArchitecturalStyle.CRAFTSMAN: ["craftsman", "wood", "stone", "timber"],
        ArchitecturalStyle.JAPANDI: ["japandi", "zen", "wabi sabi", "japanese", "bamboo"],
        ArchitecturalStyle.SCANDINAVIAN: ["scandinavian", "nordic", "hygge", "nordic light"],
        ArchitecturalStyle.TROPICAL: ["tropical", "eco", "resort", "biophilic", "bali"],
        ArchitecturalStyle.MEDITERRANEAN: ["mediterranean", "coastal", "spanish", "tuscana", "greek"],
    }

    ROOM_KEYWORDS = {
        "Living Room": ["living", "hall", "lounge", "family room", "great room", "drawing room", "reception"],
        "Master Bedroom": ["master bedroom", "master suite", "primary bedroom", "main bedroom"],
        "Bedroom": ["bedroom", "bed room", "guest room", "nursery", "kids room"],
        "Kitchen": ["kitchen", "pantry", "cooking area", "scullery"],
        "Dining Room": ["dining", "eating area", "dinette", "breakfast nook"],
        "Bathroom": ["bathroom", "bath", "restroom", "toilet", "washroom", "powder room", "ensuite"],
        "Home Office": ["office", "study", "workspace", "library"],
        "Gym": ["gym", "fitness", "workout room"],
        "Home Theater": ["theater", "theatre", "cinema", "media room"],
        "Laundry": ["laundry", "utility room", "washing room"],
        "Store Room": ["store", "storage", "pantry store"],
        "Prayer Room": ["prayer room", "mandir", "meditation room"],
        "Garage": ["garage", "carport", "parking", "car parking"],
        "Balcony / Patio": ["balcony", "patio", "terrace", "deck", "veranda", "porch"],
        "Courtyard": ["courtyard", "atrium", "garden courtyard"],
    }

    @classmethod
    def parse_prompt(cls, prompt: str) -> Dict[str, Any]:
        """Extract architectural constraints using LLM, or fallback to regex."""
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel("gemini-2.5-flash")
                system_prompt = f'''
You are an expert architectural prompt parser. Extract the following from the user prompt into JSON:
{{
  "style": "<One of: Modern, Minimalist, Classic / Traditional, Industrial, Brutalist, Luxury Villa, Contemporary, Craftsman, Japandi (Zen Fusion), Scandinavian (Nordic Light), Tropical Eco-Villa, Mediterranean Coastal>",
  "num_floors": <integer>,
  "num_pillars": <integer or null>,
  "num_beams": <integer or null>,
  "explicit_length": <float or null>,
  "explicit_width": <float or null>,
  "rooms": [
    {{"name": "Room Name (e.g. Master Bedroom, Bedroom 2)", "type": "Room Type (e.g. Master Bedroom, Bedroom, Living Room, Kitchen, Bathroom, Home Office, Balcony / Patio)"}}
  ],
  "include_main_gate": <boolean>,
  "main_gate_type": "<double_swing, sliding, modern_slat, wrought_iron>",
  "include_garden": <boolean>,
  "garden_type": "<front_lawn, courtyard, wrap_around>"
}}
Return ONLY valid JSON.
'''
                response = model.generate_content(f"{system_prompt}\nUser Prompt: {prompt}")
                text = response.text.strip()
                if text.startswith("```json"):
                    text = text[7:]
                if text.endswith("```"):
                    text = text[:-3]
                
                data = json.loads(text.strip())
                
                # Convert style string to enum
                style_str = data.get("style", "Modern")
                matched_style = ArchitecturalStyle.MODERN
                for s in ArchitecturalStyle:
                    if s.value == style_str:
                        matched_style = s
                        break
                data["style"] = matched_style
                data["raw_prompt"] = prompt
                
                return data
            except Exception as e:
                print(f"LLM parsing failed, falling back to regex. Error: {e}")
        
        return cls._parse_prompt_regex(prompt)

    @classmethod
    def _parse_prompt_regex(cls, prompt: str) -> Dict[str, Any]:
        """Extract architectural style, room requirements, floor hints, BHK configuration, area conversions, and layout constraints from prompt text using Regex."""
        prompt_lower = prompt.lower()

        # 1. Architectural Style Detection
        detected_style = ArchitecturalStyle.MODERN
        for style, keywords in cls.STYLE_KEYWORDS.items():
            if any(kw in prompt_lower for kw in keywords):
                detected_style = style
                break

        # 2. Dwelling Type & Floor Count Hints
        num_floors = 1
        if "duplex" in prompt_lower or "townhouse" in prompt_lower:
            num_floors = 2
        elif "penthouse" in prompt_lower or "triple" in prompt_lower:
            num_floors = 2
        elif "bungalow" in prompt_lower or "cottage" in prompt_lower:
            num_floors = 1
        else:
            floor_match = re.search(r'(\d+|one|two|three|four|five|six|seven|eight|ten|twelve|fifteen|twenty|fifty|hundred)\s*[-_\s]*(story|stories|floor|floors|level|levels)', prompt_lower)
            if floor_match:
                val_str = floor_match.group(1)
                val = cls.WORD_TO_NUM.get(val_str, int(val_str) if val_str.isdigit() else 1)
                num_floors = max(1, min(100, val))

        # 3. Unit Conversion Engine: Area parsing in sq ft / sq m

        explicit_len, explicit_wid = None, None

        # Check for explicit length x width (e.g., "25x15m")
        dim_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:x|by|\*)\s*(\d+(?:\.\d+)?)\s*(?:m|meters|ft|feet)?', prompt_lower)
        if dim_match:
            try:
                explicit_len = float(dim_match.group(1))
                explicit_wid = float(dim_match.group(2))
            except ValueError:
                pass

        # Check for area in sq ft / square feet (e.g., "1500 sq ft")
        if not explicit_len:
            sqft_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:sq\s*ft|sqft|square\s*feet|sq\.?\s*ft\.?)', prompt_lower)
            if sqft_match:
                try:
                    area_sqft = float(sqft_match.group(1))
                    area_m2 = area_sqft * 0.092903
                    explicit_len = round(math.sqrt(area_m2 * 1.25), 1)
                    explicit_wid = round(area_m2 / explicit_len, 1)
                except ValueError:
                    pass

        # 4. BHK Real Estate Configuration Parsing (e.g., "3 BHK", "2.5 BHK", "1BHK")
        detected_rooms: List[Dict[str, Any]] = []

        bhk_match = re.search(r'(\d+(?:\.5)?)\s*bhk', prompt_lower)
        if bhk_match:
            bhk_val = float(bhk_match.group(1))
            n_beds = int(bhk_val)
            has_half = (bhk_val - n_beds) >= 0.4

            # Add BHK Rooms
            detected_rooms.append({"name": "Living Room", "type": "Living Room"})
            detected_rooms.append({"name": "Master Bedroom", "type": "Master Bedroom"})
            for i in range(1, n_beds):
                detected_rooms.append({"name": f"Bedroom {i+1}", "type": "Bedroom"})

            detected_rooms.append({"name": "Kitchen", "type": "Kitchen"})

            for i in range(max(1, n_beds)):
                detected_rooms.append({"name": f"Bathroom {i+1}", "type": "Bathroom"})

            if has_half:
                detected_rooms.append({"name": "Home Office / Study", "type": "Home Office"})

            detected_rooms.append({"name": "Balcony", "type": "Balcony / Patio"})

        elif "studio" in prompt_lower:
            detected_rooms = [
                {"name": "Studio Living & Bedroom", "type": "Living Room"},
                {"name": "Kitchenette", "type": "Kitchen"},
                {"name": "Bathroom", "type": "Bathroom"},
            ]

        else:
            # Standard Room Detection & Keyword Counts
            for room_type, keywords in cls.ROOM_KEYWORDS.items():
                count = 0
                for kw in keywords:
                    matches = re.findall(rf'(\d+|one|two|three|four|five|six|seven|eight)\s*[-_\s]*{kw}', prompt_lower)
                    if matches:
                        for m in matches:
                            count += cls.WORD_TO_NUM.get(m, int(m) if m.isdigit() else 1)
                    elif kw in prompt_lower and count == 0:
                        count = 1

                if count > 0:
                    for i in range(count):
                        r_label = f"{room_type} {i+1}" if count > 1 else room_type
                        detected_rooms.append({"name": r_label, "type": room_type})

        # Zero-Failure Fallback: Default room template if prompt is brief or unmapped
        if not detected_rooms:
            detected_rooms = [
                {"name": "Living Room", "type": "Living Room"},
                {"name": "Master Bedroom", "type": "Master Bedroom"},
                {"name": "Bedroom 2", "type": "Bedroom"},
                {"name": "Kitchen & Dining", "type": "Kitchen"},
                {"name": "Bathroom 1", "type": "Bathroom"},
                {"name": "Bathroom 2", "type": "Bathroom"},
            ]

        # 5. Pillar & Beam Layout Hints
        pillar_match = re.search(r'(\d+|one|two|three|four|five|six|eight|ten|twelve)\s*pillars?', prompt_lower)
        num_pillars = None
        if pillar_match:
            p_val = pillar_match.group(1)
            num_pillars = cls.WORD_TO_NUM.get(p_val, int(p_val) if p_val.isdigit() else None)

        beam_match = re.search(r'(\d+|one|two|three|four|five|six|eight|ten|twelve)\s*beams?', prompt_lower)
        num_beams = None
        if beam_match:
            b_val = beam_match.group(1)
            num_beams = cls.WORD_TO_NUM.get(b_val, int(b_val) if b_val.isdigit() else None)

        # 6. Main Gate & Garden Area Detection
        has_gate = any(kw in prompt_lower for kw in ["gate", "main gate", "maingate", "maingain", "entrance gate", "front gate", "sliding gate", "compound gate"])
        gate_type = "double_swing"
        if "sliding" in prompt_lower:
            gate_type = "sliding"
        elif "slat" in prompt_lower or "modern gate" in prompt_lower:
            gate_type = "modern_slat"
        elif "wrought" in prompt_lower or "iron" in prompt_lower or "classic gate" in prompt_lower:
            gate_type = "wrought_iron"

        has_garden = any(kw in prompt_lower for kw in ["garden", "garden area", "lawn", "landscaping", "front yard", "yard", "park", "trees", "courtyard garden"])
        garden_type = "front_lawn"
        if "courtyard" in prompt_lower:
            garden_type = "courtyard"
        elif "wrap" in prompt_lower or "around" in prompt_lower:
            garden_type = "wrap_around"

        return {
            "style": detected_style,
            "num_floors": num_floors,
            "num_pillars": num_pillars,
            "num_beams": num_beams,
            "explicit_length": explicit_len,
            "explicit_width": explicit_wid,
            "rooms": detected_rooms,
            "include_main_gate": has_gate,
            "main_gate_type": gate_type,
            "include_garden": has_garden,
            "garden_type": garden_type,
            "raw_prompt": prompt,
        }



    @classmethod
    def create_plot_dimensions(
        cls,
        length: float,
        width: float,
        max_height: float = 300.0,
        num_floors: int = 2,
        wall_thickness: float = 0.25,
        margin: float = 1.0,
    ) -> PlotDimensions:
        """Validate and construct PlotDimensions object."""
        length = max(5.0, min(1000.0, float(length)))
        width = max(5.0, min(1000.0, float(width)))
        num_floors = max(1, min(100, int(num_floors)))
        max_height = max(3.0, float(num_floors * 3.5))
        wall_thickness = max(0.1, min(1.0, float(wall_thickness)))
        margin = max(0.0, min(min(length, width) / 4, float(margin)))

        floor_h = 3.2

        return PlotDimensions(
            length=length,
            width=width,
            max_height=max_height,
            num_floors=num_floors,
            floor_height=floor_h,
            wall_thickness=wall_thickness,
            margin=margin,
        )


