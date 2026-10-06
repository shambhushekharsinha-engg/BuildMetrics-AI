"""
BuildMetrics AI — Notification / Toast System
Provides helper functions for styled toast messages in the Streamlit app.
Wraps st.toast() with consistent icons and duration for a polished UX.
"""
import streamlit as st


def toast_success(msg: str, duration: int = 3) -> None:
    """Show a success toast notification."""
    st.toast(f"✅ {msg}", icon="✅")


def toast_error(msg: str, duration: int = 5) -> None:
    """Show an error toast notification."""
    st.toast(f"❌ {msg}", icon="❌")


def toast_info(msg: str) -> None:
    """Show an info toast notification."""
    st.toast(f"ℹ️ {msg}", icon="ℹ️")


def toast_warning(msg: str) -> None:
    """Show a warning toast notification."""
    st.toast(f"⚠️ {msg}", icon="⚠️")


def progress_banner(label: str, steps: list[str]) -> None:
    """
    Show a visual multi-step progress banner.
    
    Usage:
        progress_banner("Generating Blueprint", ["Parsing prompt", "Layout engine", "Rendering 3D"])
    """
    n = len(steps)
    cols = st.columns(n)
    for i, (col, step) in enumerate(zip(cols, steps)):
        with col:
            status = "🟢" if i < n - 1 else "⏳"
            st.markdown(
                f"<div style='text-align:center; font-size:0.8rem; color:#94A3B8;'>{status} {step}</div>",
                unsafe_allow_html=True
            )
