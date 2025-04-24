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

# Attribution text for credits button
credit_text = "This app was developed by Peter Sommer Ulriksen and colleagues from the Department of Radiology, Rigshospitalet."

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

import pandas as pd
import json
import gspread
from gspread_dataframe import set_with_dataframe
from google.oauth2.service_account import Credentials
from datetime import datetime

if st.button("Get Info"):
    middle_box = []
    right_box = []
    referral_risk, age_risk = calculate_risks(age if age else None, referral_reason)

    # Store inputs
    input_data = {
        "Timestamp": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        "Age": [age],
        "Referral Reason": [referral_reason],
        "CT Performed": [ct_performed],
        "Size (cm)": [size_cm if ct_performed else None],
        "HU Non-Enhanced": [HU_non if ct_performed else None],
        "Growth Rate": [growth_rate if ct_performed else None],
        "Bilateral": [bilateral if ct_performed else None],
        "Heterogenicity": [heterogenicity if ct_performed else None],
        "Macroscopic Fat": [fat if ct_performed else None],
        "Cystic": [cystic if ct_performed else None],
        "Calcification": [calcification if ct_performed else None],
        "Contrast Exam": [contrast_exam],
        "HU Venous": [HU_venous if contrast_exam else None],
        "HU Delayed": [HU_delayed if contrast_exam else None]
    }
    df = pd.DataFrame(input_data)

    # Save input data locally
ss_input_log.csv"), index=False)
    except Exception as e:
        st.warning(f"Could not save data: {e}")

    st.markdown("### Results")
    if csv_download:
        st.download_button(
            label="Download this case's input as CSV",
            data=csv_download,
            file_name=f"adrenal_mass_case_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    col1, col2, col3 = st.columns([1, 2, 2])

    with col1:
        st.markdown("#### Input")
        st.write("Inputs are shown in sidebar.")

    with col2:
        st.markdown("#### Analysis")
        shown_benign = False
        for text, importance in sorted(middle_box, key=lambda x: -x[1]):
            if "Very probably benign finding, No follow up needed" in text:
                if not shown_benign:
                    st.success(text)
                    shown_benign = True
            elif importance >= 9:
                st.error(text)
            elif importance >= 5:
                st.warning(text)
            else:
                st.info(text)

    with col3:
        st.markdown("#### Final Conclusion")
        if right_box:
            # Get the text and corresponding importance from the analysis box
            most_important_finding = max(middle_box, key=lambda x: x[1])
            final_text = most_important_finding[0]
            # Red for probable malignancy, Yellow for follow-up, Blue otherwise
            if any(term in final_text.lower() for term in ["carcinoma", "metastasis", "malignancy", "pheochromocytoma", "hypervascular"]):
                st.error(final_text)
            elif any(term in final_text.lower() for term in ["mdt", "planning", "follow-up", "check", "consider"]):
                st.warning(final_text)
            else:
                st.info(final_text)
        else:
            st.info("No critical rule applied.")

if st.button("Reset"):
    st.experimental_rerun()

# Credits section at the bottom
if st.button("Credits"):
    st.markdown(f"<div style='color: gray; font-size: small;'>{credit_text}</div>", unsafe_allow_html=True)
