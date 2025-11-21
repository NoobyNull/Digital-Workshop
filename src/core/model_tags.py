"""Centralized tag constants for model metadata.

These tags are stored in the model_metadata.keywords column as a
comma-separated list, alongside user-defined keywords.
"""

# Reserved/system tags
TAG_DIRTY = (
    "dirty"  # Model metadata has changes that are not yet fully organized/synced
)
TAG_RECENT = "recent"  # Model appears in the MRU list
TAG_FAVORITE = "favorite"  # Model is starred/favorited by the user
TAG_DOWNLOADED = "downloaded"  # Model originated from an automated URL download
