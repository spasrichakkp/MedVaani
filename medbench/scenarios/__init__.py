from .diagnosis import run_case as run_diagnosis
from .drug_interactions import run_case as run_drug
from .summarization import run_case as run_summarization
from .cds import run_case as run_cds
from .imaging import run_case as run_imaging, has_imaging_deps

# Import scenario handlers
from . import diagnosis
from . import drug_interactions
from . import summarization
from . import cds
from . import imaging

# Create SCENARIOS dictionary for easy access
SCENARIOS = {
    "diagnosis": diagnosis,
    "drug_interactions": drug_interactions,
    "summarization": summarization,
    "cds": cds,
    "imaging": imaging
}

