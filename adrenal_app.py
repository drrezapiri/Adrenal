import streamlit as st

# Diagnostic logic function
def calculate_diagnostic_approach(age, referral, ct, contrast, size, HU_non, HU_portal, HU_delayed,
                                  growth, bilateral, hetero, macrofat, cystic, calcification):
    approach = []
    referral_risks = {"Cancer work-up": 43, "Hormonal imbalance": 3, "Incidentaloma": 3}
    if referral:
        approach.append(f"**Referral reason:** Risk of malignancy is {referral_risks.get(referral, 0)}%.")
    if age is not None:
        if age < 18: age_risk = 62
        elif age < 40: age_risk = 4
        elif age <= 65: age_risk = 6
        else: age_risk = 11
        approach.append(f"**Age:** Risk of malignancy is {age_risk}%.")

    if ct:
        if size is not None:
            if size < 1:
                approach.append("**Size:** < 1 cm suggests very probably benign.")
            elif size < 4:
                approach.append("**Size:** Risk of malignancy is 2%.")
                if growth == "Increased < 5 mm/year":
                    approach.append("**Growth:** < 5 mm/year suggests benign.")
            elif size <= 6:
                approach.append("**Size:** Risk of malignancy is 6%.")
            else:
                approach.append("**Size:** Risk is 25% adrenal carcinoma and 18% metastasis.")
        if growth == "Increased > 5 mm/year":
            approach.append("**Growth:** > 5 mm/year suggests need for evaluation.")
        elif growth == "In doubt":
            approach.append("**Growth:** Consider repeat CT in 6–12 months.")
        if HU_non is not None:
            if HU_non < 10:
                approach.append("**Non-contrast HU:** < 10 suggests benign.")
            elif HU_non > 20:
                approach.append("**Non-contrast HU:** > 20 suggests evaluation.")
            else:
                approach.append("**Non-contrast HU:** 11–20 is indeterminate.")
        if hetero == "Heterogeneous":
            approach.append("**Heterogeneity:** Evaluation advised.")
        if macrofat:
            approach.append("**Macroscopic fat:** Suggests myelolipoma.")
        if bilateral:
            approach.append("**Bilateral:** Consider differential diagnoses.")

    if contrast and HU_non and HU_portal and HU_delayed:
        abs_washout = ((HU_portal - HU_delayed) / (HU_portal - HU_non)) * 100
        rel_washout = ((HU_portal - HU_delayed) / HU_portal) * 100
        approach.append(f"**Absolute washout:** {abs_washout:.2f}%")
        approach.append(f"**Relative washout:** {rel_washout:.2f}%")
        if HU_portal > 120 or HU_delayed > 120:
            approach.append("**Enhancement:** Hypervascular tumor considered.")
        if HU_non > 20 and HU_portal > 20 and HU_delayed > 20 and abs(HU_portal - HU_delayed) < 6:
            approach.append("**Pattern:** Suggests hematoma.")
        if rel_washout <= 58:
            approach.append("**Washout:** < 58% needs evaluation.")

    return approach

# Final conclusion logic
def determine_final_conclusion(age, referral, ct, contrast, size, HU_non, HU_portal, HU_delayed,
                               growth, bilateral, hetero, macrofat):
    conclusion = {"text": "", "level": 0}
    referral_risks = {"Cancer work-up": 43, "Hormonal imbalance": 3, "Incidentaloma": 3}
    if referral in referral_risks and referral_risks[referral] > 20:
        conclusion = {"text": "High malignancy risk due to referral reason.", "level": 1}
    if age is not None:
        age_risk = 62 if age < 18 else 4 if age < 40 else 6 if age <= 65 else 11
        if age_risk > 20 and age_risk > conclusion["level"]:
            conclusion = {"text": "Age suggests need for evaluation.", "level": age_risk}
    if ct:
        if size:
            if size < 1 and 4 > conclusion["level"]:
                conclusion = {"text": "Very probably benign. No follow-up needed.", "level": 4}
            elif size < 4 and growth == "Increased < 5 mm/year" and 5 > conclusion["level"]:
                conclusion = {"text": "Very probably benign. No follow-up needed.", "level": 5}
            elif 4 <= size <= 6 and 6 > conclusion["level"]:
                conclusion = {"text": "Moderate malignancy risk. Plan individually.", "level": 6}
            elif size > 6 and 25 > conclusion["level"]:
                conclusion = {"text": "High malignancy risk. Urgent evaluation needed.", "level": 25}
        if HU_non is not None:
            if HU_non < 10 and 9 > conclusion["level"]:
                conclusion = {"text": "Very probably benign. No follow-up.", "level": 9}
            if HU_non > 20 or hetero == "Heterogeneous":
                if 8 > conclusion["level"]:
                    conclusion = {"text": "Suggests p-metanephrines check and planning.", "level": 8}
            if 11 <= HU_non <= 20 and 3 > conclusion["level"]:
                conclusion = {"text": "Thorax CT advised. Follow-up based on results.", "level": 3}
        if macrofat and 10 > conclusion["level"]:
            conclusion = {"text": "Probably myelolipoma. No follow-up needed.", "level": 10}
        if bilateral and 7 > conclusion["level"]:
            conclusion = {"text": "Consider additional differential diagnoses.", "level": 7}
    if contrast and HU_non and HU_portal and HU_delayed:
        rel_washout = ((HU_portal - HU_delayed) / HU_portal) * 100
        if rel_washout > 58 and 10 > conclusion["level"]:
            conclusion = {"text": "Washout suggests benign tumor.", "level": 10}
        elif rel_washout <= 58 and 10 > conclusion["level"]:
            conclusion = {"text": "Low washout. Plan individually.", "level": 10}
    return conclusion

# UI
st.set_page_config("Adrenal Mass Tool", layout="wide")
st.title("Adrenal Mass Assessment Tool")

with st.form("adrenal_form"):
    age = st.number_input("Age", 0, 120)
    referral = st.selectbox("Reason for referral", ["", "Cancer work-up", "Hormonal imbalance", "Incidentaloma"])
    ct = st.checkbox("CT scan performed?")
    if ct:
        size = st.number_input("Tumor size (cm)", step=0.1)
        HU_non = st.number_input("Non-contrast HU")
        growth = st.selectbox("Growth", ["", "No prior scanning", "Increased > 5 mm/year", "Increased < 5 mm/year", "In doubt"])
        bilateral = st.checkbox("Bilateral finding")
        hetero = st.selectbox("Heterogeneity", ["", "Homogeneous", "Heterogeneous"])
        macrofat = st.checkbox("Macroscopic fat")
        cystic = st.checkbox("Cystic")
        calcification = st.checkbox("Calcification")
    else:
        size = HU_non = growth = bilateral = hetero = macrofat = cystic = calcification = None
    contrast = st.checkbox("Contrast-enhanced scan")
    if contrast:
        HU_portal = st.number_input("Venous HU")
        HU_delayed = st.number_input("Delayed HU")
    else:
        HU_portal = HU_delayed = None
    submit = st.form_submit_button("Assess")
    reset = st.form_submit_button("Reset")

if reset:
    st.experimental_rerun()

if submit:
    st.subheader("Diagnostic Approach")
    for line in calculate_diagnostic_approach(age, referral, ct, contrast, size, HU_non, HU_portal, HU_delayed,
                                              growth, bilateral, hetero, macrofat, cystic, calcification):
        st.markdown(f"- {line}")

    st.subheader("Final Conclusion")
    result = determine_final_conclusion(age, referral, ct, contrast, size, HU_non, HU_portal, HU_delayed,
                                        growth, bilateral, hetero, macrofat)
    st.markdown(f"**{result['text']}**" if result['text'] else "No conclusion based on current inputs.")
