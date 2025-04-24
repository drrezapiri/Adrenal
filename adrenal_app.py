import streamlit as st

st.set_page_config(page_title="Adrenal Mass Assessment Tool", layout="wide")
st.title("🧠 Adrenal Mass Assessment Tool")

with st.form("assessment_form"):
    st.header("Patient Data Input")
    age = st.number_input("Age", min_value=0, max_value=120, step=1)
    referral = st.selectbox("Reason for referral", ["", "Cancer work-up", "Hormonal imbalance", "Incidentaloma"])
    ct = st.checkbox("CT scan performed?")

    size = HU_non = growth = bilateral = hetero = macrofat = cystic = calcification = None
    if ct:
        size = st.number_input("Tumor size (cm)", min_value=0.0, step=0.1)
        HU_non = st.number_input("Non-contrast HU", step=1.0)
        growth = st.selectbox("Growth over time", ["", "No prior scanning", ">5mm", "<5mm", "In doubt"])
        bilateral = st.checkbox("Bilateral finding")
        hetero = st.selectbox("Heterogeneity", ["", "Homogeneous", "Heterogeneous"])
        macrofat = st.checkbox("Sign of macroscopic fat")
        cystic = st.checkbox("Cystic")
        calcification = st.checkbox("Calcification")

    contrast = st.checkbox("Examination with contrast")
    HU_portal = HU_delayed = None
    if contrast:
        HU_portal = st.number_input("Venous phase HU", step=1.0)
        HU_delayed = st.number_input("Delayed phase HU", step=1.0)

    submitted = st.form_submit_button("Assess")

if submitted:
    referral_map = {"Cancer work-up": "cancer", "Hormonal imbalance": "hormonal", "Incidentaloma": "incidentaloma"}
    approach = []
    conclusion = {"text": "", "level": 0}
    benignMessageGiven = False

    if referral:
        referral_code = referral_map.get(referral)
        referralRisks = {"cancer": 43, "hormonal": 3, "incidentaloma": 3}
        approach.append(f"Referral reason: Risk of malignancy is {referralRisks[referral_code]}%.")
        if referralRisks[referral_code] > 20:
            conclusion = {"text": "High risk of malignancy based on referral reason. Individual planning recommended.", "level": 1}

    if age:
        ageRisk = 62 if age < 18 else 4 if age < 40 else 6 if age <= 65 else 11
        approach.append(f"Age: Risk of malignancy is {ageRisk}%.")
        if ageRisk > 20 and ageRisk > conclusion['level']:
            conclusion = {"text": "Age-related risk suggests need for further evaluation.", "level": ageRisk}

    if ct:
        if size:
            if size < 1 and 4 > conclusion['level']:
                conclusion = {"text": "Very probably benign finding, no follow-up needed.", "level": 4}
                benignMessageGiven = True
            if size < 4:
                approach.append("Size: Risk of malignancy is 2%.")
                if growth == "<5mm" and 5 > conclusion['level']:
                    conclusion = {"text": "Very probably benign finding, no follow-up needed.", "level": 5}
                    benignMessageGiven = True
            elif 4 <= size <= 6 and 6 > conclusion['level']:
                approach.append("Size: Risk of malignancy is 6%.")
                conclusion = {"text": "Moderate risk of malignancy. Individual planning recommended.", "level": 6}
            elif size > 6 and 25 > conclusion['level']:
                approach.append("Size: Risk of malignancy is 25% adrenal carcinoma and 18% metastasis.")
                conclusion = {"text": "High risk of malignancy (25% adrenal carcinoma, 18% metastasis). Urgent evaluation needed.", "level": 25}

        if growth == ">5mm" and 5 > conclusion['level']:
            approach.append("Growth: > 5 mm/year suggests need for further evaluation.")
            conclusion = {"text": "Individual decision making / MDT recommended.", "level": 5}

        if growth == "In doubt":
            approach.append("Growth: Consider repeat CT scan without contrast in 6–12 months.")

        if HU_non is not None:
            if HU_non < 10 and 9 > conclusion['level']:
                approach.append("Non-contrast HU: < 10 suggests benign finding.")
                conclusion = {"text": "Very probably benign finding, no follow-up needed.", "level": 9}
                benignMessageGiven = True
            elif HU_non > 20 and 8 > conclusion['level']:
                approach.append("Non-contrast HU: > 20 suggests need for further evaluation.")
                conclusion = {"text": "Due to HU > 20, check p-metanephrines and consider individual planning.", "level": 8}
            elif 11 <= HU_non <= 20:
                approach.append("Non-contrast HU: 11-20 suggests indeterminate finding.")
                if size and size < 4 and 3 > conclusion['level']:
                    conclusion = {"text": "Supply with Thorax CT scan, if normal no follow-up. If positive, individual planning.", "level": 3}
                elif size and size >= 4 and 3 > conclusion['level']:
                    conclusion = {"text": "Individual planning recommended.", "level": 3}

        if hetero == "Heterogeneous" and 8 > conclusion['level']:
            approach.append("Heterogeneity: Suggests need for further evaluation.")
            conclusion = {"text": "Due to heterogeneity, check p-metanephrines and consider individual planning.", "level": 8}

        if macrofat and 10 > conclusion['level']:
            approach.append("Macroscopic fat: Suggests myelolipoma.")
            conclusion = {"text": "Probably myelolipoma, no follow-up needed.", "level": 10}

        if bilateral and 7 > conclusion['level']:
            approach.append("Bilateral findings: Consider additional differential diagnoses.")
            conclusion = {"text": "Due to bilateral findings, consider additional differential diagnoses.", "level": 7}

    if contrast and HU_non is not None and HU_portal is not None and HU_delayed is not None:
        absWashout = ((HU_portal - HU_delayed) / (HU_portal - HU_non)) * 100 if (HU_portal - HU_non) != 0 else 0
        relWashout = ((HU_portal - HU_delayed) / HU_portal) * 100 if HU_portal != 0 else 0
        approach.append(f"Absolute washout: {absWashout:.2f}%")
        approach.append(f"Relative washout: {relWashout:.2f}%")

        if HU_portal > 120 or HU_delayed > 120:
            approach.append("Contrast enhancement: Hypervascular tumors should be considered.")
            if 10 > conclusion['level']:
                conclusion = {"text": "Hypervascular tumors should be considered.", "level": 10}

        if HU_non > 20 and HU_portal > 20 and HU_delayed > 20 and abs(HU_portal - HU_delayed) < 6:
            approach.append("Pattern: Suggests hematoma.")
            if 11 > conclusion['level']:
                conclusion = {"text": "Probably hematoma, no follow-up needed.", "level": 11}

        if relWashout <= 58:
            approach.append("Washout: Relative washout < 58% suggests need for further evaluation.")
            if 10 > conclusion['level']:
                conclusion = {"text": "Relative washout < 58%, individual planning recommended.", "level": 10}
        elif size and size < 4 and relWashout > 58:
            if 10 > conclusion['level']:
                conclusion = {"text": "The relative washout indicates tumor is probably benign.", "level": 10}

    st.subheader("🔍 Diagnostic Approach")
    for a in approach:
        st.markdown(f"- {a}")

    st.subheader("✅ Final Conclusion")
    st.markdown(conclusion['text'] if conclusion['text'] else "No definitive conclusion could be reached with the provided data.")
