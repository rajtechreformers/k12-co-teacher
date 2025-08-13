def get_students_data(student_profiles):
    # Extract disabilities, accommodations, and teacher notes for each student
    mapping = {}

    for profile in student_profiles:
        item = profile.get("body", {}).get("Item", {})
        # general info
        first = item.get("first_name", "").strip().title()
        last = item.get("last_name", "").strip().title()
        full_name = f"{first} {last}".strip() or "Unknown Student"

        # disabilities
        disabilities = item.get("disabilities", [])
        disability_names = [d.get("name", "").strip() for d in disabilities if isinstance(d, dict)]

        # accommodations
        accommodations = item.get("accommodations", [])
        accommodation_list = [a.get("S", "").strip() if isinstance(a, dict) else str(a) for a in accommodations]
        mapping[full_name] = {
            "disabilities": disability_names,
            "accommodations": accommodation_list,
        }
    return mapping

 
def format_student_profile(profile, teacher_id=None):
    """formats student profile into more readable format for llm"""
    def listify(lst, indent="- "):
        return "\n".join(f"{indent}{item['S'] if isinstance(item, dict) and 'S' in item else item}" for item in lst)

    def flatten_disabilities(disabilities):
        return "\n".join(f"- {d.get('type', 'N/A').replace('_', ' ').title()}: {d.get('name', 'N/A')}" for d in disabilities)

    def format_services(services):
        return "\n".join(
            f"- {s.get('type')} ({s.get('frequency')}, {s.get('start_date')} to {s.get('end_date')})"
            for s in services
        )

    return f"""Student: {profile.get("first_name", "Unknown")} {profile.get("last_name", "")}
                Grade: {profile.get("grade_level", "N/A")}  
                Age: {profile.get("age", "N/A")}  
                Gender: {profile.get("gender", "N/A")}  
                Primary Language: {profile.get("primary_language", "N/A")}  
                Ethnicity: {profile.get("ethnicity", "N/A")}  
                Placement: {profile.get("placement", "N/A")}
                ---

                **Disabilities**  
                {flatten_disabilities(profile.get("disabilities", [])) or "- None listed"}

                ---

                **IEP Goals**  
                {listify(profile.get("iep_goals", [])) or "- None listed"}

                ---

                **Accommodations**  
                {listify(profile.get("accommodations", [])) or "- None listed"}

                ---

                **Learning Styles**  
                {listify(profile.get("learning_styles", [])) or "- None listed"}

                ---

                **Services**  
                {format_services(profile.get("services", [])) or "- None listed"}

                ---

                **Interview Notes**  
                - Parent: {profile.get("interviews", {}).get("parent", "N/A")}
                - Teacher: {profile.get("interviews", {}).get("teacher", "N/A")}

                ---

                **Observation (Psychologist)**  
                {profile.get("observations", {}).get("psychologist", "N/A")}
                

                **Teacher Comments**  
                {(profile.get("teacherComments") or {}).get(teacher_id)}
                

                """.strip()
