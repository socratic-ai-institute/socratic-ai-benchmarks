#!/usr/bin/env python3
"""
Generate Test Scenarios for Socratic AI Benchmark

Creates 120 test scenarios combining:
- 10 student profiles (ages 14-18, varying depth preferences)
- 4 content segments (Richmond/Tredegar history)
- 3 question positions (Q1, Q2, Q3)

Output: test_scenarios.json
"""

import json
from typing import List, Dict

# 10 Student Profiles
STUDENT_PROFILES = [
    {"age": 14, "grade": 9, "depth_preference": "surface"},
    {"age": 15, "grade": 9, "depth_preference": "moderate"},
    {"age": 15, "grade": 10, "depth_preference": "moderate"},
    {"age": 16, "grade": 10, "depth_preference": "deep"},
    {"age": 16, "grade": 11, "depth_preference": "moderate"},
    {"age": 17, "grade": 11, "depth_preference": "deep"},
    {"age": 17, "grade": 12, "depth_preference": "deep"},
    {"age": 18, "grade": 12, "depth_preference": "moderate"},
    {"age": 14, "grade": 9, "depth_preference": "deep"},
    {"age": 18, "grade": 12, "depth_preference": "surface"},
]

# 4 Content Segments (Richmond/Tredegar Iron Works History)
CONTENT_SEGMENTS = [
    {
        "id": 1,
        "title": "Founding and Early Years",
        "summary": "Tredegar Iron Works was founded in Richmond, Virginia in 1837 by Francis B. Deane Jr. Located along the James River, it became the South's largest ironworks. The facility produced railroad equipment, including locomotives, rails, and spikes. Richmond's strategic location near water transportation and coal deposits made it ideal for industrial development during America's early Industrial Revolution.",
        "key_concepts": [
            "Industrial Revolution",
            "Richmond's geographic advantages",
            "Railroad expansion",
            "Southern industrialization",
        ],
        "difficulty_level": "introductory",
        "time_period": "1837-1860",
    },
    {
        "id": 2,
        "title": "Civil War Era Production",
        "summary": "During the Civil War (1861-1865), Tredegar became the Confederacy's most important industrial asset. The facility produced cannons, artillery shells, railroad iron, and naval armor plating. At its peak, Tredegar employed over 2,500 workers, including both enslaved laborers and free workers. The ironworks' capacity to produce weapons was critical to Confederate military operations, though Union forces repeatedly attempted to capture or destroy it.",
        "key_concepts": [
            "Confederate war industry",
            "Munitions production",
            "Enslaved labor in industry",
            "Strategic military importance",
        ],
        "difficulty_level": "intermediate",
        "time_period": "1861-1865",
    },
    {
        "id": 3,
        "title": "Reconstruction and Labor History",
        "summary": "After the Civil War, Tredegar struggled to adapt to peacetime production and the end of slavery. The facility faced labor disputes, including significant strikes in the 1870s and 1880s as workers organized for better wages and conditions. The transition from enslaved to wage labor created new tensions and dynamics. Richmond's industrial landscape changed dramatically as the city rebuilt its economy without slavery as its foundation.",
        "key_concepts": [
            "Post-war economic transition",
            "Labor movements and strikes",
            "Wage labor vs. enslaved labor",
            "Reconstruction challenges",
        ],
        "difficulty_level": "intermediate",
        "time_period": "1865-1900",
    },
    {
        "id": 4,
        "title": "Preservation and Historical Memory",
        "summary": "Tredegar Iron Works ceased operations in 1957 after 120 years of production. In 2000, the American Civil War Museum opened at the historic site, transforming the former industrial complex into a place for understanding Civil War history and its lasting impacts. The museum presents multiple perspectives on the war, including the experiences of soldiers, civilians, enslaved people, and free African Americans. Debates continue about how to interpret and present this complex history.",
        "key_concepts": [
            "Historical preservation",
            "Public memory and commemoration",
            "Multiple historical perspectives",
            "Museums and interpretation",
        ],
        "difficulty_level": "advanced",
        "time_period": "1957-present",
    },
]

# Synthetic Q&A for Q2 and Q3 scenarios
SAMPLE_QA_EXCHANGES = {
    1: [
        {
            "question": "What geographical features made Richmond a good location for an ironworks?",
            "answer": "Richmond was near the James River for transportation and had access to coal deposits needed for iron production.",
        },
        {
            "question": "Based on your answer about location, why might controlling Richmond have been strategically important during the Civil War?",
            "answer": "Because Tredegar was there and it was the South's main source of weapons and military supplies.",
        },
    ],
    2: [
        {
            "question": "What types of weapons did Tredegar produce during the Civil War?",
            "answer": "They made cannons, artillery shells, and armor for ships. Also railroad materials for moving troops.",
        },
        {
            "question": "You mentioned multiple products. Which do you think was most critical to Confederate military operations and why?",
            "answer": "Probably the cannons because they needed artillery for battles. Without cannons they couldn't fight effectively.",
        },
    ],
    3: [
        {
            "question": "How did the workforce at Tredegar change after the Civil War ended?",
            "answer": "They couldn't use enslaved labor anymore so they had to hire wage workers instead.",
        },
        {
            "question": "What challenges might this transition from enslaved to wage labor have created for both the company and the workers?",
            "answer": "The company had to pay wages now which costs more. Workers had to negotiate for fair pay and might have needed to strike to get better treatment.",
        },
    ],
    4: [
        {
            "question": "Why do you think it's important to preserve historical sites like Tredegar?",
            "answer": "So people can learn about what happened there and understand history better by seeing the actual place.",
        },
        {
            "question": "You mentioned seeing the actual place helps understanding. What specific aspects of the Civil War might be harder to understand if Tredegar hadn't been preserved?",
            "answer": "It would be harder to understand how important industry was to the war, not just battles. Also harder to see where enslaved people worked and how they were part of the war effort.",
        },
    ],
}


def generate_scenarios() -> List[Dict]:
    """Generate all 120 test scenarios"""

    scenarios = []
    scenario_id = 1

    for profile in STUDENT_PROFILES:
        for segment in CONTENT_SEGMENTS:
            for question_num in [1, 2, 3]:
                # Build previous Q&A for Q2 and Q3
                previous_qa = []
                if question_num == 2:
                    previous_qa = [SAMPLE_QA_EXCHANGES[segment["id"]][0]]
                elif question_num == 3:
                    previous_qa = SAMPLE_QA_EXCHANGES[segment["id"]][:2]

                scenario = {
                    "id": f"scenario_{scenario_id:03d}",
                    "student_profile": profile,
                    "content_segment": segment,
                    "question_number": question_num,
                    "previous_qa": previous_qa,
                }

                scenarios.append(scenario)
                scenario_id += 1

    return scenarios


def main():
    print("🔧 Generating test scenarios...")

    scenarios = generate_scenarios()

    print(f"✅ Generated {len(scenarios)} scenarios")
    print(f"   - {len(STUDENT_PROFILES)} student profiles")
    print(f"   - {len(CONTENT_SEGMENTS)} content segments")
    print(f"   - 3 question positions (Q1, Q2, Q3)")
    print(
        f"   - Total: {len(STUDENT_PROFILES)} × {len(CONTENT_SEGMENTS)} × 3 = {len(scenarios)}"
    )

    # Save to JSON
    output_file = "test_scenarios.json"
    with open(output_file, "w") as f:
        json.dump(scenarios, f, indent=2)

    print(f"\n💾 Saved to: {output_file}")
    print(f"📊 File size: {len(json.dumps(scenarios, indent=2)) / 1024:.1f} KB")

    # Print sample
    print(f"\n📋 Sample scenario (Scenario 1):")
    print(json.dumps(scenarios[0], indent=2))

    print("\n✅ Ready to run benchmark.py!")


if __name__ == "__main__":
    main()
