import hashlib
from datetime import datetime
from backend.domain.common.license import License, LicenseStatus, LicenseValidationResult

# Mock secret for signature verification (In production, use Asymmetric Keys)
SECRET_KEY = "SUPER_SECRET_VENDOR_KEY"

def generate_signature(license_data: License) -> str:
    """Generates a mock signature for the license data."""
    # Concatenate key fields
    raw = f"{license_data.id}|{license_data.client_name}|{license_data.expires_at.isoformat()}|{license_data.hardware_binding}|{SECRET_KEY}"
    return hashlib.sha256(raw.encode()).hexdigest()

def validate_license(license_obj: License, current_hardware_id: str = None) -> LicenseValidationResult:
    """
    Validates the license against expiration, signature, and hardware binding.
    """
    now = datetime.now()

    # 1. Check Expiration
    if now > license_obj.expires_at:
        return LicenseValidationResult(
            status=LicenseStatus.EXPIRED,
            message="License has expired.",
            license_details=license_obj
        )

    # 2. Check Signature (Tamper Detection)
    expected_sig = generate_signature(license_obj)
    # Note: license_obj.signature is the one provided in the file.
    # In this mock, we assume the object was loaded and we re-verify.
    # If the object was created with a signature that doesn't match current data + secret, it fails.
    if license_obj.signature != expected_sig:
        return LicenseValidationResult(
            status=LicenseStatus.TAMPERED,
            message="License signature mismatch. File may be corrupted or tampered.",
            license_details=license_obj
        )

    # 3. Check Hardware Binding (if applicable)
    if license_obj.hardware_binding:
        if not current_hardware_id:
             return LicenseValidationResult(
                status=LicenseStatus.INVALID,
                message="License requires hardware binding but no ID provided.",
                license_details=license_obj
            )

        # Hash the provided HW ID to compare
        # Assuming hardware_binding in license is the direct ID or a hash?
        # Let's assume it stores the literal ID for this simple mock.
        if license_obj.hardware_binding != current_hardware_id:
             return LicenseValidationResult(
                status=LicenseStatus.INVALID,
                message=f"Hardware ID mismatch. Bound to {license_obj.hardware_binding}.",
                license_details=license_obj
            )

    return LicenseValidationResult(
        status=LicenseStatus.ACTIVE,
        message="License is valid.",
        license_details=license_obj
    )
