import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from fpdf import FPDF
import io
import datetime
import os

st.set_page_config(page_title="Cybersecurity Maturity Self-Assessment", layout="wide")

# Default company logo (Tools of Tech P.C.)
default_logo = "tools_of_tech_logo.png"
if os.path.exists(default_logo):
    st.image(default_logo, width=150)

# CMM rubric descriptions
cmm_rubric = {
    0: "Non-existent: No recognized practices.",
    1: "Ad hoc: Processes are informal and undocumented.",
    2: "Repeatable: Some practices are established but inconsistently applied.",
    3: "Defined: Practices are documented and communicated.",
    4: "Managed: Practices are monitored, measured and improved.",
    5: "Optimized: Best practices are followed and continuously improved."
}

# Recommendations based on score
def recommendation(score):
    if score < 2:
        return "High priority for corrective action. Establish basic controls."
    elif score < 3:
        return "Moderate risk. Document and formalize processes."
    elif score < 4:
        return "Develop structured monitoring and review."
    elif score < 5:
        return "Consider optimization and automation."
    else:
        return "Maintain and share best practices."

# NIS2 sectors with extended criteria
nis2_domains = {
    "Governance": [
        "Cybersecurity strategy aligned with organizational goals.",
        "Cyber roles and responsibilities assigned and reviewed.",
        "Executive oversight of cybersecurity established.",
        "Cybersecurity integrated into governance and compliance."
    ],
    "Risk Management": [
        "Risk management framework implemented and maintained.",
        "Cyber risk assessments conducted and updated periodically.",
        "Third-party risks integrated into risk management.",
        "Risk treatment plans reviewed and acted upon."
    ],
    "Operational Security": [
        "IT assets inventoried and classified.",
        "Access control policies enforced and reviewed.",
        "System vulnerabilities are patched promptly.",
        "Network segmentation and monitoring deployed."
    ],
    "Incident Management": [
        "Incident response plan documented, tested, and updated.",
        "Reporting channels and detection tools established.",
        "Coordination with national CSIRTs or sector CSIRTs ensured.",
        "Post-incident review and continuous improvement cycle in place."
    ]
}

# Apply the same domains to each sector
nis2_sectors = [
    "Energy", "Transport", "Banking", "Financial Market Infrastructure",
    "Health", "Drinking Water", "Waste Water", "Digital Infrastructure",
    "ICT Service Management", "Public Administration", "Space"
]
sector_domains = {sector: nis2_domains for sector in nis2_sectors}

st.title("\U0001F512 Cybersecurity Maturity Self-Assessment Tool")

st.sidebar.title("Navigation")
sector = st.sidebar.selectbox("Select Sector", options=nis2_sectors)
section = st.sidebar.radio("Go to", ("Assessment", "Summary", "Download Report"))

if 'scores' not in st.session_state:
    st.session_state.scores = {}

if section == "Assessment":
    st.header("Assessment Form")
    st.markdown("Use the CMM scale to evaluate maturity.\n- 0: Non-existent\n- 1: Ad hoc\n- 2: Repeatable\n- 3: Defined\n- 4: Managed\n- 5: Optimized")
    for domain, items in sector_domains[sector].items():
        with st.expander(f"{domain} → {len(items)} criteria"):
            domain_scores = []
            for item in items:
                col1, col2 = st.columns([3, 2])
                with col1:
                    st.markdown(f"**{item}**")
                with col2:
                    level = st.selectbox("Select maturity level", options=list(cmm_rubric.keys()), format_func=lambda x: f"{x} - {cmm_rubric[x]}", key=f"{domain}-{item}")
                    domain_scores.append(level)
            st.session_state.scores[domain] = domain_scores

elif section == "Summary":
    st.header("\U0001F4CA Results Summary")
    domain_averages = {d: sum(s)/len(s) for d, s in st.session_state.scores.items()}
    all_scores = [s for scores in st.session_state.scores.values() for s in scores]
    avg_score = sum(all_scores)/len(all_scores) if all_scores else 0
    st.metric("Overall Maturity Score", f"{avg_score:.2f} / 5")

    col1, col2 = st.columns(2)
    with col1:
        fig1, ax1 = plt.subplots(figsize=(6, 4))
        ax1.bar(domain_averages.keys(), domain_averages.values(), color='teal')
        ax1.set_title("Maturity by Domain")
        ax1.set_ylim(0, 5)
        st.pyplot(fig1)

    with col2:
        df = pd.DataFrame.from_dict(st.session_state.scores, orient='index')
        fig2, ax2 = plt.subplots(figsize=(6, 4))
        sns.heatmap(df, cmap="YlGnBu", annot=True, cbar=False, ax=ax2)
        ax2.set_title("Heatmap of Scores")
        st.pyplot(fig2)

    st.subheader("\U0001F4DD Recommendations Table")
    recs = pd.DataFrame({
        "Domain": domain_averages.keys(),
        "Avg Score": domain_averages.values(),
        "Recommendation": [recommendation(s) for s in domain_averages.values()]
    })
    st.dataframe(recs)

    st.session_state.fig_summary = fig1
    st.session_state.fig_heatmap = fig2
    st.session_state.recs_table = recs

elif section == "Download Report":
    st.header("\U0001F4BE Download PDF Report")
    org = st.text_input("Organization:", "Tools of Tech P.C.")
    assessor = st.text_input("Assessor:", "")
    date = st.date_input("Date of Assessment", datetime.date.today())

    if st.button("Generate Report"):
        pdf = FPDF()
        pdf.add_page()
        if os.path.exists(default_logo):
            pdf.image(default_logo, x=10, y=10, w=30)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 40, 'Cybersecurity Maturity Report', ln=True, align='C')
        pdf.set_font("Arial", '', 12)
        pdf.cell(0, 10, f"Organization: {org}", ln=True)
        pdf.cell(0, 10, f"Assessor: {assessor}", ln=True)
        pdf.cell(0, 10, f"Date: {date}", ln=True)

        for fig, name in [(st.session_state.fig_summary, "summary.png"), (st.session_state.fig_heatmap, "heatmap.png")]:
            buf = io.BytesIO()
            fig.savefig(buf, format='png', bbox_inches='tight')
            buf.seek(0)
            with open(name, 'wb') as f:
                f.write(buf.read())
            pdf.add_page()
            pdf.image(name, x=10, y=20, w=180)

        pdf.add_page()
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Domain Recommendations", ln=True)
        pdf.set_font("Arial", '', 10)
        for index, row in st.session_state.recs_table.iterrows():
            pdf.multi_cell(0, 8, f"{row['Domain']}: {row['Recommendation']} ({row['Avg Score']:.2f})")

        output = pdf.output(dest='S').encode('latin1')
        st.download_button("Download PDF", output, file_name="maturity_report.pdf", mime="application/pdf")
