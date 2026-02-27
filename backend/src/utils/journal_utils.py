"""Journal-related utility functions."""



# High-impact journal patterns
HIGH_IMPACT_PATTERNS = {
    "nature": ["nature", "nat "],
    "science": ["science"],
    "cell": ["cell"],
    "jama": ["jama", "journal of the american medical association"],
    "nejm": ["new england journal", "nejm", "n engl j med"],
    "lancet": ["lancet"],
    "bmj": ["bmj", "british medical journal"],
    "brain": ["brain"],
    "neurology": ["neurology"],
    "alzheimers": ["alzheimer's & dementia", "alzheimers dementia", "alzheimer's and dementia"],
    "molecular": ["molecular psychiatry", "molecular neurodegeneration"],
    "imaging": ["neuroimage", "human brain mapping", "cerebral cortex"],
    "radiology": ["radiology", "ajnr", "american journal of neuroradiology"],
    "mri": ["magnetic resonance in medicine", "mrm", "jmri",
           "journal of magnetic resonance imaging"],
    "pnas": ["proceedings of the national academy", "pnas"],
    "neuroscience": ["journal of neuroscience", "j neurosci"],
    "psychiatry": ["american journal of psychiatry", "biological psychiatry"],
    "npj": ["npj"],
    "communications": ["nature communications", "science advances"]
}


def is_high_impact_journal(journal_name: str) -> bool:
    """
    Check if a journal is considered high-impact.
    
    Args:
        journal_name: Name of the journal
    
    Returns:
        True if the journal is high-impact, False otherwise
    """
    if not journal_name:
        return False

    journal_lower = journal_name.lower()

    # Check against all patterns
    for category, patterns in HIGH_IMPACT_PATTERNS.items():
        for pattern in patterns:
            if pattern in journal_lower:
                return True

    return False


def get_journal_category(journal_name: str) -> str:
    """
    Get the category of a journal.
    
    Args:
        journal_name: Name of the journal
    
    Returns:
        Category name or 'other'
    """
    if not journal_name:
        return "other"

    journal_lower = journal_name.lower()

    for category, patterns in HIGH_IMPACT_PATTERNS.items():
        for pattern in patterns:
            if pattern in journal_lower:
                return category

    return "other"


def get_high_impact_journal_list() -> list[str]:
    """
    Get a list of all high-impact journal patterns.
    
    Returns:
        List of journal patterns
    """
    all_patterns = []
    for patterns in HIGH_IMPACT_PATTERNS.values():
        all_patterns.extend(patterns)
    return sorted(set(all_patterns))
