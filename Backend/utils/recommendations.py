def get_recommendations(
    missing_skills: list[str],
    hiring_probability: float,
):
    """
    Recommendations aligned with both skill gaps and overall match score.
    """
    recommendations = []
    missing_count = len(missing_skills)
    for skill in missing_skills:
        recommendations.append(f"Consider learning or improving: {skill}")

    if hiring_probability >= 0.8:

        recommendations.append(
            "Very strong overall fit based on weighted scoring."
        )
    
    elif hiring_probability >= 0.6:
        recommendations.append(
            "Solid fit, but verify competency depth in key areas."
        )
    elif hiring_probability >= 0.4:
        recommendations.append(
            "Borderline fit; focus on closing the most critical gaps."
        )
    else:
        recommendations.append(
            "Low fit; substantial upskilling is recommended before re-evaluation."
        )

    if missing_count >= 5:
        recommendations.append(
            "High skill gap count suggests the role may be a stretch target."
        )
    elif missing_count >= 1:
        recommendations.append(
            "Some role requirements are missing and should be prioritized."
        )
    else:
        recommendations.append(
            "All listed required skills are covered in the candidate profile."
        )
        
    

    if missing_skills:
        focus = ", ".join(missing_skills[:5])
        recommendations.append(f"Priority skills to address: {focus}.")

    return recommendations
