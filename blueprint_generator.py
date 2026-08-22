import matplotlib.pyplot as plt
import squarify
import numpy as np

def generate_blueprint(area, bedrooms, bathrooms):
    # Base sizes in percentage of total area (approximate)
    # This is a very simplified logic for proportional room sizes
    
    rooms = {
        'Living Room': 30,
        'Kitchen': 15,
        'Hallway': 5,
    }
    
    for i in range(bedrooms):
        rooms[f'Bedroom {i+1}'] = 20 / bedrooms if bedrooms > 0 else 0
        
    for i in range(bathrooms):
        rooms[f'Bathroom {i+1}'] = 10 / bathrooms if bathrooms > 0 else 0
        
    # Add Remaining as Balcony/Utility if less than 100
    total_alloc = sum(rooms.values())
    if total_alloc < 100:
        rooms['Balcony / Utility'] = 100 - total_alloc
        
    # Scale values to actual area
    labels = list(rooms.keys())
    sizes = [(val / 100.0) * area for val in rooms.values()]
    
    # Calculate aspect ratio of the house (e.g., 1.2 : 1)
    # Assuming width * height = area, width/height = 1.2
    # width = 1.2 * height => 1.2 * height^2 = area => height = sqrt(area/1.2)
    height = (area / 1.2) ** 0.5
    width = area / height
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Custom color palette (blueprint style)
    colors = ['#1f77b4', '#aec7e8', '#ff7f0e', '#ffbb78', '#2ca02c', '#98df8a', '#d62728', '#ff9896', '#9467bd', '#c5b0d5']
    # Extend colors if needed
    colors = (colors * ((len(labels) // len(colors)) + 1))[:len(labels)]
    
    squarify.plot(sizes=sizes, label=labels, color=colors, alpha=0.8, ax=ax, edgecolor='white', linewidth=2)
    
    ax.set_title(f'Procedural 2D Blueprint Concept - Total Area: {area} sqft', fontsize=14, fontweight='bold')
    ax.axis('off')
    
    return fig
