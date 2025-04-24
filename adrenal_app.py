import streamlit as st
import pandas as pd
import datetime

st.set_page_config(layout="wide")

# Title
st.title("Adrenal Mass Assessment App")
st.caption("Developed by: Peter Sommer Ulriksen et al.\nDepartment of Radiology, Rigshospitalet")

# Sidebar Inputs
st.sidebar.header("Input Parameters")
age = st.sidebar.number_input("Age", min_value=0, max_value=120)
referral = st.sidebar.selectbox("Referral Reason", ["Cancer work-up", "Hormonal imbalance", "Incidentaloma"])
ct_done = st.sidebar.checkbox("CT Performed?")

size = hu_non = growth = bilateral = heterogenicity = fat = cystic = calcification = None
if ct_done:
    size = st.sidebar.number_input("Tumor Size (cm)", min_value=0.0, step=0.1)
    hu_non = st.sidebar.number_input("HU (non-enhanced)", step=0.1)
    growth = st.sidebar.selectbox("Growth over time", ["Unknown", "<5 mm/year", ">5 mm/year"])
    bilateral = st.sidebar.checkbox("Bilateral finding")
    heterogenicity = st.sidebar.checkbox("Heterogenicity")
    fat = st.sidebar.checkbox("Macroscopic fat")
    cystic = st.sidebar.checkbox("Cystic")
    calcification = st.sidebar.checkbox("Calcification")

contrast_done = st.sidebar.checkbox("Contrast Performed?")

hu_venous = hu_delayed = None
if contrast_done:
    hu_venous = st.sidebar.number_input("HU (venous phase)", step=0.1)
    hu_delayed = st.sidebar.number_input("HU (delayed phase)", step=0.1)

# Helper function to apply rules
def apply_rules():
    rules = []
    def add_rule(desc, imp, color):
        rules.append((desc, imp, color))

    # Malignancy Risks
    if referral == "Cancer work-up":
        add_rule("Referral: Cancer → 43% risk", 1, "red")
    else:
        add_rule("Referral: Not cancer → 3% risk", 1, "red")

    if age < 18:
        add_rule("Age <18 → 62% risk", 1, "red")
    elif age <= 39:
        add_rule("Age 18–39 → 4% risk", 1, "red")
    elif age <= 65:
        add_rule("Age 40–65 → 6% risk", 1, "red")
    else:
        add_rule("Age >65 → 11% risk", 1, "red")

    # Size
    if size is not None:
        if size < 1:
            add_rule("Size <1 cm → Very probably benign", 4, "blue")
        elif size < 4:
            add_rule("Size <4 cm → 2% risk", 2, "blue")
        elif size <= 6:
            add_rule("Size 4–6 cm → 6% risk", 6, "yellow")
        else:
            add_rule("Size >6 cm → 25% carcinoma, 18% metastasis", 9, "red")
    else:
        add_rule("Tumor size not filled", 5, "yellow")

    # HU non-enhanced
    if hu_non is not None:
        if hu_non < 10:
            add_rule("HU <10 → Very probably benign", 9, "red")
        elif hu_non <= 20:
            if size is not None and size < 4:
                add_rule("HU 11–20 & Size <4 cm → Thorax CT follow-up", 3, "blue")
            else:
                add_rule("HU 11–20 & Size >4 cm → Individual planning", 3, "blue")
        else:
            add_rule("HU >20 → Check p-metanephrines", 8, "yellow")
    elif hu_venous is not None and hu_venous < 10:
        add_rule("Missing HU non, using venous <10 → Very probably benign", 2, "blue")

    # Contrast washout
    if contrast_done:
        if hu_venous and hu_venous > 120:
            add_rule("Venous >120 → Hypervascular", 10, "red")
        if hu_delayed and hu_delayed > 120:
            add_rule("Delayed >120 → Hypervascular", 10, "red")
        if hu_non and hu_venous and hu_delayed:
            rel_washout = ((hu_venous - hu_delayed) / (hu_venous - hu_non)) * 100
            if rel_washout > 58 and size and size < 4:
                add_rule(f"Relative washout {rel_washout:.1f}% <4 cm → Benign", 10, "red")
            elif rel_washout <= 58:
                add_rule(f"Relative washout {rel_washout:.1f}% ≤58% → Individual planning", 10, "red")

    # Other features
    if bilateral:
        add_rule("Bilateral → Consider pheochromocytoma", 7, "yellow")
    if fat:
        add_rule("Macroscopic fat → Myelolipoma", 10, "red")

    rules.sort(key=lambda x: x[1], reverse=True)
    return rules

# Generate rules and output
rules = apply_rules()

# Layout columns
col1, col2, col3 = st.columns([1, 2, 2])

with col1:
    st.subheader("Input Summary")
    st.write("**Age:**", age)
    st.write("**Referral Reason:**", referral)
    if ct_done:
        st.write(f"**Size:** {size} cm")
        st.write(f"**HU (non-enhanced):** {hu_non}")
        st.write(f"**Growth:** {growth}")
        st.write("**Bilateral:**", bilateral)
        st.write("**Heterogenicity:**", heterogenicity)
        st.write("**Fat:**", fat)
        st.write("**Cystic:**", cystic)
        st.write("**Calcification:**", calcification)
    if contrast_done:
        st.write(f"**HU (venous):** {hu_venous}")
        st.write(f"**HU (delayed):** {hu_delayed}")

with col2:
    st.subheader("Analysis")
    for r in rules:
        st.markdown(f"<span style='color:{r[2]}'>{r[0]}</span>", unsafe_allow_html=True)

with col3:
    st.subheader("Final Conclusion")
    if rules:
        top = rules[0]
        st.markdown(f"<span style='color:{top[2]}; font-size: 20px'><strong>{top[0]}</strong></span>", unsafe_allow_html=True)

# Save to CSV
if st.button("Save Case"):
    input_data = {
        'datetime': datetime.datetime.now().isoformat(),
        'age': age,
        'referral': referral,
        'size': size,
        'hu_non': hu_non,
        'hu_venous': hu_venous,
        'hu_delayed': hu_delayed,
        'growth': growth,
        'bilateral': bilateral,
        'fat': fat
    }
    df = pd.DataFrame([input_data])
    try:
        existing = pd.read_csv("adrenal_mass_input_log.csv")
        df = pd.concat([existing, df], ignore_index=True)
    except FileNotFoundError:
        pass
    df.to_csv("adrenal_mass_input_log.csv", index=False)
    st.success("Case saved.")

# Download current case
st.download_button("Download Current Case", data=df.to_csv(index=False), file_name="adrenal_case.csv", mime="text/csv")

# Credits
st.markdown("<div style='position: fixed; bottom: 10px; right: 10px;'>Developed by: Peter Sommer Ulriksen et al.</div>", unsafe_allow_html=True)
