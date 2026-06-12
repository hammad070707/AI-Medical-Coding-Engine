from typing import List,Dict ,Tuple

class StaticValidator:
    """
    STATION: Legal Compliance Guard
    Maqsad: AI ki ghaltiyon ko pakarna aur claims ko reject hone se bachana.
    """

    @staticmethod
    def validate_claim(patient_data:Dict,encounter_data:Dict,codes:Dict)->Tuple[bool,List[str]]:
        errors=[]
        icd_list=[codes['primary_diagnosis']['code']]+[d['code']for d in codes.get('secondary_diagnoses',[])]
        cpt_list = [p['code'] for p in codes.get('procedures', [])]
        is_gender_ok,msg=StaticValidator.check_gender(patient_data['gender'],icd_list)
        if not is_gender_ok: errors.append(msg)
        is_age_ok, msg = StaticValidator.check_age(patient_data['age'], icd_list)
        if not is_age_ok: errors.append(msg)
        is_lat_ok, msg = StaticValidator.check_laterality(encounter_data['laterality'], icd_list)
        if not is_lat_ok: errors.append(msg)
        is_pos_ok, msg = StaticValidator.check_pos(encounter_data['location'], cpt_list)
        if not is_pos_ok: errors.append(msg)
        is_bundle_ok, msg = StaticValidator.check_bundling(cpt_list)
        if not is_bundle_ok:
            errors.append(msg)
        return (len(errors) == 0, errors)

    @staticmethod
    def check_gender(gender: str, icd_codes: List[str]):
        forbidden = {"M": ["O", "Z34", "N91"], "F": ["C61", "N40"]}
        for code in icd_codes:
            if gender.upper() in forbidden:
                for prefix in forbidden[gender.upper()]:
                    if code.startswith(prefix):
                        return False, f"CRITICAL: Gender Mismatch. Code {code} is invalid for {gender}."
        return True, ""

    @staticmethod
    def check_age(age: int, icd_codes: List[str]):
        if age > 18:
            for code in icd_codes:
                if code.startswith("P"):
                    return False, f"ERROR: Pediatric code {code} used for Adult (Age: {age})."
        return True, ""

    @staticmethod
    def check_laterality(note_lat, icd_codes: List[str]):
        """
        AI agar dictionary ya list bhej de toh usay string mein badal kar check karein.
        """
        if isinstance(note_lat, dict):
            note_lat_str = " ".join(str(v) for v in note_lat.values()).upper()
        elif isinstance(note_lat, list):
            note_lat_str = " ".join(str(v) for v in note_lat).upper()
        else:
            note_lat_str = str(note_lat).upper()
        if "RIGHT" in note_lat_str:
            for code in icd_codes:
                if code.endswith("2"):
                    return False, f"LATERALITY MISMATCH: Note implies Right, but Code {code} is for Left side."
        if "LEFT" in note_lat_str:
            for code in icd_codes:
                if code.endswith("1"):
                    return False, f"LATERALITY MISMATCH: Note implies Left, but Code {code} is for Right side."

        return True, ""

    @staticmethod
    def check_pos(location: str, cpt_codes: List[str]):
        if location.upper() == "CLINIC":
            for cpt in cpt_codes:
                if cpt.startswith("33"):
                    return False, f"POS ERROR: Major Surgery {cpt} cannot be performed in Clinic."
        return True, ""

    @staticmethod
    def check_bundling(cpt_codes: List[str]):
        if "99213" in cpt_codes and "99214" in cpt_codes:
            return False, "NCCI EDIT: Duplicate E&M levels (99213 and 99214) detected. Bundling required."
        return True, ""
