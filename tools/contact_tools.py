from fuzzywuzzy import fuzz


async def check_discrepancy(provided, pan, aadhar, government, field_name):
    mismatched_fields = []
    
    pan_match = provided == pan
    aadhar_match = provided == aadhar
    government_match = provided == government

    if not pan_match:
        mismatched_fields.append("PAN")
    if not aadhar_match:
        mismatched_fields.append("Aadhaar")
    if not government_match:
        mismatched_fields.append("Government")

    if mismatched_fields:
        return False, pan_match, aadhar_match, government_match, f"{field_name} does not match the one associated with {', '.join(mismatched_fields)}."
    return True, pan_match, aadhar_match, government_match, f"{field_name} is consistent across all check points."

async def check_discrepancy_1(provided_name, pan, aadhar, tax, field_name):
    mismatched_fields = []
    pan_match = fuzz.token_sort_ratio(provided_name, pan) >= 85
    aadhar_match = fuzz.token_sort_ratio(provided_name, aadhar) >= 85
    tax_match = fuzz.token_sort_ratio(provided_name, tax) >= 85

    
    #pan_match = provided == pan
    #aadhar_match = provided == aadhar
    #tax_match = provided == tax

    if not pan_match:
        mismatched_fields.append("PAN")
    if not aadhar_match:
        mismatched_fields.append("Aadhaar")
    if not tax_match:
        mismatched_fields.append("Tax Return")

    if mismatched_fields:
        return False, pan_match, aadhar_match, tax_match, f"{field_name} does not match the one associated with {', '.join(mismatched_fields)}."
    return True, pan_match, aadhar_match, tax_match, f"{field_name} is consistent across all check points."

async def check_discrepancy_address(provided_address, pan, aadhar, government, field_name):
    mismatched_fields = []
    
    pan_match = fuzz.token_sort_ratio(provided_address, pan) >= 60
    aadhar_match = fuzz.token_sort_ratio(provided_address, aadhar) >= 60
    government_match = fuzz.token_sort_ratio(provided_address, government) >= 60

    if not pan_match:
        mismatched_fields.append("PAN")
    if not aadhar_match:
        mismatched_fields.append("Aadhaar")
    if not government_match:
        mismatched_fields.append("Government")

    if mismatched_fields:
        return False, pan_match, aadhar_match, government_match, f"{field_name} does not match the one associated with {', '.join(mismatched_fields)}."
    return True, pan_match, aadhar_match, government_match, f"{field_name} is consistent across all check points."