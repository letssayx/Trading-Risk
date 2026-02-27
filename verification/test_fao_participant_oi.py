
import sys
import os

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.web.api.data.view_routes import get_model_for_type
from backend.ingest import nse_models as models

def test_fao_participant_oi_mapping():
    print("Testing 'fao_participant_oi' mapping...")
    model = get_model_for_type('fao_participant_oi')

    if model == models.FAOParticipantOI:
        print("SUCCESS: 'fao_participant_oi' maps to FAOParticipantOI correctly.")
    else:
        print(f"FAILURE: 'fao_participant_oi' mapped to {model}, expected FAOParticipantOI")
        sys.exit(1)

    print("Testing 'participant_oi' legacy mapping...")
    legacy_model = get_model_for_type('participant_oi')
    if legacy_model == models.FAOParticipantOI:
        print("SUCCESS: 'participant_oi' (legacy) maps to FAOParticipantOI correctly.")
    else:
        print(f"FAILURE: 'participant_oi' mapped to {legacy_model}, expected FAOParticipantOI")
        sys.exit(1)

if __name__ == "__main__":
    test_fao_participant_oi_mapping()
