import streamlit as st
import requests
import pandas as pd
import json
import matplotlib.pyplot as plt

st.title("🧪 SHL Test Recommender Evaluation Dashboard")

uploaded_file = st.file_uploader("Upload test_queries.json", type="json")

def jaccard_similarity(set1, set2):
    if not set1 and not set2:
        return 1.0
    return len(set1 & set2) / len(set1 | set2)

if uploaded_file:
    test_cases = json.load(uploaded_file)
    results = []
    precision_scores = []
    recall_scores = []
    top_k = 3
    hits = 0

    for case in test_cases:
        expected_skills = set(map(str.lower, case["expected_skills"]))
        max_duration = case["max_duration"]
        query = case["query"]

        response = requests.post("http://localhost:8000/recommend", json={"query": query})
        recs = response.json().get("recommendations", [])[:top_k]

        correct_in_top_k = 0
        for rank, rec in enumerate(recs, 1):
            rec_skills = set(map(str.lower, rec.get("skills", [])))
            duration = rec.get("duration", 999)
            skill_score = jaccard_similarity(expected_skills, rec_skills)
            duration_ok = duration <= max_duration
            success = skill_score > 0.5 and duration_ok
            if success:
                correct_in_top_k += 1
            if rank == 1:
                results.append({
                    "Query": query,
                    "Expected Skills": ", ".join(expected_skills),
                    "Max Duration": max_duration,
                    "Top Match": rec["name"],
                    "Matched Skills": ", ".join(rec_skills),
                    "Skill Match Score": round(skill_score, 2),
                    "Duration": duration,
                    "Duration OK": duration_ok,
                    "Success": success
                })

        total_relevant = min(top_k, len(expected_skills)) if expected_skills else 1
        precision_scores.append(correct_in_top_k / top_k)
        recall_scores.append(correct_in_top_k / total_relevant)
        if correct_in_top_k > 0:
            hits += 1

    df = pd.DataFrame(results)
    df["Precision@K"] = precision_scores
    df["Recall@K"] = recall_scores
    st.dataframe(df)

    accuracy = hits / len(test_cases)
    avg_precision = sum(precision_scores) / len(precision_scores)
    avg_recall = sum(recall_scores) / len(recall_scores)

    st.subheader(f"✅ Top-1 Accuracy: {accuracy:.2%}")
    st.subheader(f"🎯 Precision@{top_k}: {avg_precision:.2%}")
    st.subheader(f"📌 Recall@{top_k}: {avg_recall:.2%}")

    st.subheader("📊 Precision and Recall per Query")
    fig, ax = plt.subplots(figsize=(10, 4))
    x_labels = [f"Q{i+1}" for i in range(len(df))]
    ax.bar(x_labels, df["Precision@K"], width=0.4, label="Precision@K", align='center')
    ax.bar(x_labels, df["Recall@K"], width=0.4, label="Recall@K", align='edge')
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Score")
    ax.set_title("Precision@K vs Recall@K per Query")
    ax.legend()
    st.pyplot(fig)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download CSV", csv, "evaluation_results.csv", "text/csv")