"""
BuildMetrics AI — Accessibility & Responsive CSS Utilities
Injects print-friendly, high-contrast, and reduced-motion CSS into the Streamlit app.
Used via: inject_accessibility_css()
"""

PRINT_CSS = """
@media print {
    /* Hide Streamlit chrome, sidebar, buttons */
    .stSidebar, .stToolbar, footer, header,
    [data-testid="stSidebarNav"], .stDeployButton,
    button:not(.print-keep) { display: none !important; }
    
    /* Expand main area to full width */
    .stApp, .main, .block-container { width: 100% !important; max-width: 100% !important; padding: 0 !important; }
    
    /* Black text on white for print */
    body, .stMarkdown, h1, h2, h3, h4, p { color: #000 !important; background: #fff !important; }
    
    /* Blueprint should print at high resolution */
    img { max-width: 100%; page-break-inside: avoid; }
    
    /* Page break before each main tab content */
    .stTab { page-break-before: always; }
    
    /* Legal disclaimer prominent in print */
    .print-disclaimer { 
        border: 2px solid #000; 
        padding: 12px; 
        font-size: 10pt; 
        margin-top: 20px; 
    }
}
"""

ACCESSIBILITY_CSS = """
/* High contrast focus indicators */
*:focus-visible {
    outline: 3px solid #00F0FF !important;
    outline-offset: 2px !important;
}

/* Reduced motion for users who prefer it */
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }
}

/* Skip to main content link (screen readers) */
.skip-nav {
    position: absolute;
    top: -40px;
    left: 0;
    background: #00F0FF;
    color: #000;
    padding: 8px;
    z-index: 100;
    font-weight: bold;
}
.skip-nav:focus {
    top: 0;
}

/* Better button contrast */
.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 240, 255, 0.3);
    transition: all 0.2s ease;
}

/* Metric card hover effect */
.metric-card:hover {
    border-left-width: 7px;
    transition: border-left-width 0.15s ease;
}

/* Responsive: stack columns on narrow screens */
@media (max-width: 768px) {
    .stColumns { flex-direction: column !important; }
    .stColumn { width: 100% !important; }
    .main-header { font-size: 2rem !important; }
    .sub-header { font-size: 1rem !important; }
}

/* Tooltip improvements */
[data-tooltip]:hover::after {
    content: attr(data-tooltip);
    position: absolute;
    background: rgba(0,0,0,0.85);
    color: #fff;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
    white-space: nowrap;
    z-index: 1000;
}
"""

LOADING_CSS = """
/* Smooth loading animation for blueprint images */
@keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}

.loading-skeleton {
    background: linear-gradient(90deg, #1e293b 25%, #334155 50%, #1e293b 75%);
    background-size: 200% 100%;
    animation: shimmer 1.5s infinite;
    border-radius: 8px;
    height: 400px;
}
"""


def inject_accessibility_css() -> str:
    """Returns combined CSS string to inject via st.markdown."""
    return f"<style>{PRINT_CSS}{ACCESSIBILITY_CSS}{LOADING_CSS}</style>"
