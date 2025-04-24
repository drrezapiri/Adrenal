import streamlit as st

st.set_page_config(layout="wide")

# --- Sidebar Input ---
st.sidebar.header("Patient Information")
age = st.sidebar.number_input("Age", min_value=0, max_value=120, step=1)
referral_reason = st.sidebar.selectbox("Reason for Referral", ["", "Cancer work-up", "Hormonal imbalance", "Incidentaloma"])

show_ct_inputs = st.sidebar.checkbox("Is there a CT scan performed?")
if show_ct_inputs:
    size_cm = st.sidebar.number_input("Tumor Size (cm)", min_value=0.0, step=0.1)
    HUnon = st.sidebar.number_input("HU (Non-contrast)")
    growth_rate = st.sidebar.selectbox("Growth rate?", ["No prior scanning", "Increased > 5 mm/year", "Increased < 5 mm/year", "In doubt"])
    bilateral = st.sidebar.checkbox("Bilateral finding")
    heterogeneity = st.sidebar.selectbox("Heterogenicity", ["", "Homogen", "Heterogen"])
    macroscopic_fat = st.sidebar.checkbox("Sign for macroscopic fat")
    cystic = st.sidebar.checkbox("Cystic")
    calcification = st.sidebar.checkbox("Calcification")

show_contrast = st.sidebar.checkbox("Examination with contrast")
if show_contrast:
    HUportal = st.sidebar.number_input("HU (Venous phase)")
    HUdelayed = st.sidebar.number_input("HU (Delayed phase)")

# --- Placeholders for boxes ---
col1, col2, col3 = st.columns([1, 2, 2])

with col2:
    middle_box = st.empty()
with col3:
    final_box = st.empty()

# --- Utility Functions ---
def calculate_washouts(HUportal, HUdelayed, HUnon):
    abs_wash = ((HUportal - HUdelayed) / (HUportal - HUnon)) * 100 if (HUportal - HUnon) else 0
    rel_wash = ((HUportal - HUdelayed) / HUportal) * 100 if HUportal else 0
    return round(abs_wash, 1), round(rel_wash, 1)

def get_malignancy_risks(age, referral_reason):
    referral_risks = {"Cancer work-up": 43, "Hormonal imbalance": 3, "Incidentaloma": 3}
    age_risk = None
    if age:
        if age < 18:
            age_risk = 62
        elif age <= 39:
            age_risk = 4
        elif age <= 65:
            age_risk = 6
        else:
            age_risk = 11
    referral_risk = referral_risks.get(referral_reason, None)
    return age_risk, referral_risk

# --- Main Logic ---
if st.sidebar.button("Get Info"):
    mid_texts = []
    final_text = ""

    age_risk, ref_risk = get_malignancy_risks(age, referral_reason)
    if ref_risk is not None:
        mid_texts.append(f"The risk of malignancy because of the referral reason is {ref_risk}%")
    if age_risk is not None:
        mid_texts.append(f"Age related risk of malignancy is {age_risk}%")

    if show_ct_inputs:
        if size_cm:
            if size_cm < 1:
                mid_texts.append("Very probably benign finding, No follow up needed.")
                final_text = "Very probably benign finding, No follow up needed."
            elif size_cm < 4:
                mid_texts.append("Probability of adrenal carcinoma is very low due to size < 5 cm.")
                mid_texts.append("Size related risk of malignancy is 2%.")
            elif size_cm <= 6:
                mid_texts.append("Size related risk of malignancy is 6%.")
            else:
                mid_texts.append("Size related risk of malignancy is 25% for carcinoma and 18% for metastasis.")

        if growth_rate == "Increased < 5 mm/year":
            mid_texts.append("Due to the size < 5 mm, very probably benign finding, No follow up needed.")
            final_text = "Due to the size < 5 mm, very probably benign finding, No follow up needed."
        elif growth_rate == "Increased > 5 mm/year":
            mid_texts.append("Individual decision making / MDT")
            final_text = "Individual decision making / MDT"
        elif growth_rate == "In doubt":
            mid_texts.append("Repeat CT scan without contrast in 6-12 months")

        if HUnon:
            if HUnon < 10:
                mid_texts.append("Very probably benign finding, No follow up needed.")
                final_text = "Very probably benign finding, No follow up needed."
            elif 11 <= HUnon <= 20:
                if size_cm and size_cm < 4:
                    mid_texts.append("Supply with Thorax CT scan, if normal no follow-up. If positive, individual planning.")
                elif size_cm and size_cm >= 4:
                    mid_texts.append("Individual planning.")
            elif HUnon > 20:
                mid_texts.append("Due to hetrogenicity or HU > 20 check p-metanephrines and evt. individual planning.")

        if macroscopic_fat:
            mid_texts.append("Probably myelilipoma, so no follow-up needed.")
            final_text = "Probably myelilipoma, so no follow-up needed."

        if bilateral:
            mid_texts.append("Due to bilateral finings consider Pheochromocytoma, Bilateral macronodular hyperplasia, Congenital adrenal hyperplasia, ACTH dependent Cushing, lymphoma, infection, bleeding, metastasis, granulomatous disease or 21-hydroxylase deficit.")

    if show_contrast and HUnon:
        mid_texts.append("CT scan with contrast is recommended.")
        abs_wash, rel_wash = calculate_washouts(HUportal, HUdelayed, HUnon)
        mid_texts.append(f"Absolute washout: {abs_wash}%")
        mid_texts.append(f"Relative washout: {rel_wash}%")

        if HUportal > 120 or HUdelayed > 120:
            mid_texts.append("Hypervascular tumors like RCC, HCC or pheochromocytoma should be considered.")
            final_text = "Hypervascular tumors like RCC, HCC or pheochromocytoma should be considered."
        if (size_cm < 4 and rel_wash > 58) or (heterogeneity == "Heterogen" and size_cm < 4 and rel_wash > 58):
            mid_texts.append("The relative washout indicates tumor is probably benign (sensitivity 100%, specificity 15%, PPV 100% and NPV 32%, if pheochromocytoma is ruled out)")
            final_text = "The relative washout indicates tumor is probably benign (sensitivity 100%, specificity 15%, PPV 100% and NPV 32%, if pheochromocytoma is ruled out)"
        elif rel_wash <= 58:
            mid_texts.append("Individual planning.")
            final_text = "Individual planning."
        if HUnon > 20 and HUportal > 20 and HUdelayed > 20 and max(abs(HUportal - HUnon), abs(HUportal - HUdelayed), abs(HUdelayed - HUnon)) < 6:
            mid_texts.append("Probably hematoma, no follow-up needed.")
            final_text = "Probably hematoma, no follow-up needed."

    # Remove duplicates of "Very probably benign finding..."
    mid_texts = list(dict.fromkeys(mid_texts))
    if mid_texts.count("Very probably benign finding, No follow up needed.") > 1:
        mid_texts = [t for t in mid_texts if t != "Very probably benign finding, No follow up needed."] + ["Very probably benign finding, No follow up needed."]

    middle_box.write("\n".join(mid_texts))
    final_box.write(final_text)

if st.button("Reset"):
    st.experimental_rerun()
