"""Skeleton loader component for showing loading state while fetching papers."""

import random

import streamlit as st


class SkeletonLoader:
    """Creates skeleton loading animations for paper cards."""

    @staticmethod
    def show_skeleton_papers(num_papers: int = 5, container=None):
        """
        Show skeleton loading animations for paper cards.
        
        Args:
            num_papers: Number of skeleton cards to show
            container: Streamlit container to render in (optional)
        """
        target = container if container else st

        # Custom CSS for skeleton animation
        st.markdown("""
        <style>
        .skeleton {
            background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
            background-size: 200% 100%;
            animation: loading 1.5s infinite;
        }
        
        @keyframes loading {
            0% {
                background-position: 200% 0;
            }
            100% {
                background-position: -200% 0;
            }
        }
        
        .skeleton-title {
            height: 20px;
            margin-bottom: 10px;
            border-radius: 4px;
        }
        
        .skeleton-text {
            height: 12px;
            margin-bottom: 6px;
            border-radius: 3px;
        }
        
        .skeleton-authors {
            height: 14px;
            margin-bottom: 8px;
            border-radius: 3px;
            width: 70%;
        }
        
        .skeleton-meta {
            height: 10px;
            border-radius: 2px;
            width: 50%;
        }
        </style>
        """, unsafe_allow_html=True)

        for i in range(num_papers):
            with target.container(border=True):
                # Title skeleton
                st.markdown('<div class="skeleton skeleton-title"></div>', unsafe_allow_html=True)

                # Authors skeleton
                st.markdown('<div class="skeleton skeleton-authors"></div>', unsafe_allow_html=True)

                # Abstract text skeletons (random lengths for realism)
                num_lines = random.randint(3, 5)
                for j in range(num_lines):
                    width = "100%" if j < num_lines - 1 else f"{random.randint(30, 80)}%"
                    st.markdown(f'<div class="skeleton skeleton-text" style="width: {width};"></div>', unsafe_allow_html=True)

                # Meta info skeleton
                st.markdown('<div class="skeleton skeleton-meta"></div>', unsafe_allow_html=True)

    @staticmethod
    def show_growing_content(progress_info: dict, papers_fetched: list = None):
        """
        Show content area that grows as papers are fetched.
        
        Args:
            progress_info: Dict with source progress information
            papers_fetched: List of papers fetched so far
        """
        # Show progress summary
        total_sources = len(progress_info)
        completed_sources = sum(1 for info in progress_info.values() if info.get("status") == "completed")

        st.markdown(f"**📄 Papers Found: {len(papers_fetched) if papers_fetched else 0}**")

        # Show fetching progress
        if completed_sources < total_sources:
            estimated_papers = max(len(papers_fetched) if papers_fetched else 0,
                                 completed_sources * 20)  # Estimate 20 papers per source

            # Show skeleton papers for estimated remaining papers
            remaining_estimates = max(0, estimated_papers - (len(papers_fetched) if papers_fetched else 0))
            if remaining_estimates > 0:
                st.markdown("---")
                st.markdown("**🔄 Loading more papers...**")
                SkeletonLoader.show_skeleton_papers(min(remaining_estimates, 8))

        # Show actual papers if any
        if papers_fetched:
            st.markdown("---")
            for paper in papers_fetched[-5:]:  # Show last 5 papers
                with st.container(border=True):
                    st.markdown(f"**{paper.get('title', 'Loading...')}**")
                    if paper.get("authors"):
                        st.caption(f"👥 {paper['authors']}")
                    if paper.get("source"):
                        st.badge(paper["source"])

    @staticmethod
    def show_progressive_loading(source_names: list[str], current_progress: dict = None):
        """
        Show progressive loading with realistic paper card animations.
        
        Args:
            source_names: List of active source names
            current_progress: Current progress state for each source
        """
        if not current_progress:
            current_progress = {source: {"status": "fetching", "count": 0} for source in source_names}

        # Show compact progress header
        with st.container(border=True):
            st.markdown("**🔄 Fetching Papers**")

            cols = st.columns(len(source_names))
            for idx, source in enumerate(source_names):
                with cols[idx]:
                    status = current_progress.get(source, {})
                    count = status.get("count", 0)
                    state = status.get("status", "fetching")

                    if state == "completed":
                        st.success(f"📚 {source.upper()}\n✅ {count} papers")
                    else:
                        st.info(f"📚 {source.upper()}\n🔍 Searching...")

        # Show growing content area
        total_papers = sum(status.get("count", 0) for status in current_progress.values())
        if total_papers > 0:
            st.markdown("---")
            st.markdown(f"**📄 {total_papers} papers found so far...**")

            # Show some skeleton cards to indicate more loading
            active_sources = [s for s, info in current_progress.items()
                            if info.get("status") != "completed"]
            if active_sources:
                SkeletonLoader.show_skeleton_papers(min(3, len(active_sources) * 2))
