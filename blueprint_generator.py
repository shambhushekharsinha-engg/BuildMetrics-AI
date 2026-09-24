import matplotlib.pyplot as plt
import numpy as np
import squarify
from matplotlib import patches


def generate_blueprint(area, bedrooms, bathrooms):
    # Base sizes in percentage of total area
    rooms = {
        'Living Room': 30,
        'Kitchen & Dining': 20,
    }
    
    for i in range(bedrooms):
        rooms[f'Bedroom {i+1}'] = 25 / bedrooms if bedrooms > 0 else 0
        
    for i in range(bathrooms):
        rooms[f'Bathroom {i+1}'] = 10 / bathrooms if bathrooms > 0 else 0
        
    total_alloc = sum(rooms.values())
    if total_alloc < 100:
        rooms['Corridor / Utility'] = 100 - total_alloc
        
    labels = list(rooms.keys())
    sizes = [(val / 100.0) * area for val in rooms.values()]
    
    # Calculate dimensions: assume 4:3 aspect ratio for the house
    width = (area * (4/3)) ** 0.5
    height = area / width
    
    # Get rectangles from squarify
    # squarify.normalize_sizes normalizes sizes to total area
    norm_sizes = squarify.normalize_sizes(sizes, width, height)
    rects = squarify.squarify(norm_sizes, 0, 0, width, height)
    
    # Create the plot - Professional Blueprint Style
    fig, ax = plt.subplots(figsize=(10, 8), facecolor='#003366') # Dark blue background
    ax.set_facecolor('#003366')
    
    # Draw Grid
    ax.grid(color='#ffffff', linestyle='-', linewidth=0.5, alpha=0.3)
    ax.set_xticks(np.arange(0, width+1, 5))
    ax.set_yticks(np.arange(0, height+1, 5))
    ax.tick_params(colors='white', labelsize=8)
    
    # Plot each room
    for rect, label in zip(rects, labels):
        x, y, dx, dy = rect['x'], rect['y'], rect['dx'], rect['dy']
        
        # Room boundaries (walls)
        wall = patches.Rectangle(
            (x, y), dx, dy, 
            linewidth=3, edgecolor='white', facecolor='none'
        )
        ax.add_patch(wall)
        
        # Inner fill (slightly lighter blue for rooms)
        inner = patches.Rectangle(
            (x+0.5, y+0.5), dx-1, dy-1, 
            linewidth=1, edgecolor='#66b2ff', facecolor='#004c99', alpha=0.5
        )
        ax.add_patch(inner)
        
        # Room Label and Dimensions
        dim_text = f"{label}\n{int(dx)}' x {int(dy)}'\n({int(dx*dy)} sq.ft)"
        ax.text(
            x + dx/2, y + dy/2, dim_text,
            color='white', ha='center', va='center', 
            fontsize=10, fontweight='bold', fontfamily='monospace'
        )

    # Title Block
    title_block = patches.Rectangle(
        (0, -height*0.15), width, height*0.1, 
        linewidth=2, edgecolor='white', facecolor='#002244'
    )
    ax.add_patch(title_block)
    ax.text(
        width*0.05, -height*0.1, 
        "PROJECT: BUILDMETRICS AI RESIDENTIAL DESIGN",
        color='white', ha='left', va='center', fontsize=12, fontweight='bold', fontfamily='monospace'
    )
    ax.text(
        width*0.95, -height*0.1, 
        f"TOTAL AREA: {area} SQ.FT",
        color='white', ha='right', va='center', fontsize=12, fontweight='bold', fontfamily='monospace'
    )

    ax.set_xlim(-width*0.05, width*1.05)
    ax.set_ylim(-height*0.2, height*1.05)
    ax.set_aspect('equal')
    plt.tight_layout()
    
    return fig
