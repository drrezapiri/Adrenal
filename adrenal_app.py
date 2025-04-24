import streamlit as st
import re

def calculate_risks(age, referral_reason):
    referral_risks = {
        "Cancer work-up": 43,
        "Hormonal imbalance": 3,
        "Incidentaloma": 3
    }
    age_risk = None
    if age:
        if age < 18:
            age_risk = 62
        elif 18 <= age <= 39:
            age_risk = 4
        elif 40 <= age <= 65:
            age_risk = 6
        else:
            age_risk = 11
    return referral_risks[referral_reason], age_risk

def calculate_washouts(HU_non, HU_venous, HU_delayed):
    if None in (HU_non, HU_venous, HU_delayed):
        return None, None
    abs_washout = ((HU_venous - HU_delayed) / (HU_venous - HU_non)) * 100 if (HU_venous - HU_non) != 0 else None
    rel_washout = ((HU_venous - HU_delayed) / HU_venous) * 100 if HU_venous != 0 else None
    return abs_washout, rel_washout

def extract_importance(text):
    match = re.search(r'Importance (\d+)', text)
    return int(match.group(1)) if match else 0

st.set_page_config(layout="wide")

with st.sidebar:
    st.header("Input")
    age = st.number_input("Patient age", min_value=0, max_value=120, step=1)
    referral_reason = st.selectbox("Reason for referral", ["Cancer work-up", "Hormonal imbalance", "Incidentaloma"])
    ct_performed = st.checkbox("Is there a CT scan performed?")
    if ct_performed:
        size_cm = st.number_input("Tumor size (short axis in cm)", min_value=0.0, step=0.1)
        HU_non = st.number_input("HU non-enhanced")
        growth_rate = st.selectbox("Has it increased in size more than 5 mm per year", ["No prior scanning", "Increased > 5 mm/year", "Increased < 5 mm/year", "In doubt"])
        bilateral = st.checkbox("Bilateral finding")
        heterogenicity = st.selectbox("Heterogenicity", ["Homogen", "Heterogen"])
        fat = st.checkbox("Sign for macroscopic fat")
        cystic = st.checkbox("Cystic")
        calcification = st.checkbox("Calcification")

    contrast_exam = st.checkbox("Examination with contrast")
    if contrast_exam:
        HU_venous = st.number_input("HU venous phase")
        HU_delayed = st.number_input("HU delayed phase")

if st.button("Get Info"):
    middle_box = []
    right_box = []
    referral_risk, age_risk = calculate_risks(age if age else None, referral_reason)

    middle_box.append(f"Risk of malignancy due to referral reason: {referral_risk}%")
    if age:
        middle_box.append(f"Age related risk of malignancy is {age_risk}%")

    if ct_performed:
        if size_cm:
            if size_cm < 4:
                middle_box.append("Size-related malignancy risk: 2%")
            elif 4 <= size_cm <= 6:
                middle_box.append("Size-related malignancy risk: 6%")
            else:
                middle_box.append("Size-related malignancy risk: 25% for carcinoma, 18% for metastasis")

        if growth_rate == "Increased < 5 mm/year":
            middle_box.append("Due to the size < 5 mm/year, very probably benign finding, No follow up needed")
            right_box.append("Importance 5: Very probably benign due to slow growth")
        elif growth_rate == "Increased > 5 mm/year":
            middle_box.append("Increased > 5 mm/year — Individual decision making / MDT")
            right_box.append("Importance 5: Fast growth — MDT needed")
        elif growth_rate == "In doubt":
            middle_box.append("Repeat CT scan without contrast in 6-12 months")

        if size_cm and size_cm < 1:
            middle_box.append("Very probably benign finding, No follow up needed")
            right_box.append("Importance 4: Size < 1 cm — benign")

        if HU_non:
            if HU_non < 10:
                middle_box.append("Very probably benign finding, No follow up needed")
                right_box.append("Importance 9: HU < 10")
            elif 11 <= HU_non <= 20:
                if size_cm and size_cm < 4:
                    middle_box.append("Supply with Thorax CT scan, if normal no follow-up")
                    right_box.append("Importance 3: HU 11-20 and size < 4 cm")
                else:
                    middle_box.append("Individual planning")
                    right_box.append("Importance 3: HU 11-20 and size > 4 cm")
            elif HU_non > 20:
                middle_box.append("HU > 20 — Check p-metanephrines and consider individual planning")
                right_box.append("Importance 8: HU > 20")

        if bilateral:
            middle_box.append("Bilateral findings — consider pheochromocytoma, hyperplasia, metastases, etc.")
            right_box.append("Importance 7: Bilateral findings")

        if fat:
            middle_box.append("Probably myelolipoma, so no follow-up needed")
            right_box.append("Importance 10: Macroscopic fat")

    if contrast_exam and all(v is not None for v in [HU_non, HU_venous, HU_delayed]):
        abs_washout, rel_washout = calculate_washouts(HU_non, HU_venous, HU_delayed)
        if abs_washout is not None and rel_washout is not None:
            middle_box.append(f"Absolute washout: {abs_washout:.2f}%")
            middle_box.append(f"Relative washout: {rel_washout:.2f}%")

    st.markdown("### Results")
    col1, col2, col3 = st.columns([1, 2, 2])

    with col1:
        st.markdown("#### Input")
        st.write("Inputs are shown in sidebar.")

    with col2:
        st.markdown("#### Analysis")
        for text in set(middle_box):
            if text != "Very probably benign finding, No follow up needed":
                st.write("-", text)
        if "Very probably benign finding, No follow up needed" in middle_box:
            st.write("- Very probably benign finding, No follow up needed")

    with col3:
        st.markdown("#### Final Conclusion")
        if right_box:
            st.success(max(right_box, key=extract_importance))
        else:
            st.info("No critical rule applied.")

if st.button("Reset"):
    st.experimental_rerun()
