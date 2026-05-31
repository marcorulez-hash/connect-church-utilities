import streamlit as st
import pandas as pd
import altair as alt
import base64
from openai import OpenAI

client = OpenAI()

st.set_page_config(page_title="Connect Church Utility Dashboard", layout="wide")
st.title("🏛️ Connect Church Utility Dashboard (AI‑Powered)")

# ---------------------------------------------------
# Predefined empty tables
# ---------------------------------------------------
def empty_utility_df():
    return pd.DataFrame({
        "Invoice Date": pd.to_datetime([]),
        "Total Charge (Excl HST)": [],
        "Connect 30%": []
    })

def empty_totals_df():
    return pd.DataFrame({
        "Year": [],
        "Utility": [],
        "Total": [],
        "Connect 30%": []
    })

def empty_payments_df():
    return pd.DataFrame({
        "Amount Paid": [],
        "Payment Date": pd.to_datetime([])
    })

gas_df = empty_utility_df()
hydro_df = empty_utility_df()
water_df = empty_utility_df()
snow_df = empty_utility_df()

# ---------------------------------------------------
# AI Extraction Function
# ---------------------------------------------------
def extract_bill_data(file_bytes):
    encoded = base64.b64encode(file_bytes).decode("utf-8")

    prompt = """
    You are an expert at reading utility bills. 
    Extract ONLY the following fields from the bill:

    - utility_type (Gas, Hydro, Water, Snow)
    - invoice_date (YYYY-MM-DD)
    - total_charge (numeric, before tax)

    Return JSON only.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "Extract the bill data."},
                    {
                        "type": "input_image",
                        "image_url": f"data:application/pdf;base64,{encoded}"
                    }
                ]
            }
        ]
    )

    return response.choices[0].message["content"]

# ---------------------------------------------------
# Upload Bill
# ---------------------------------------------------
st.subheader("📄 Upload a Utility Bill (AI Auto‑Extract)")

uploaded_bill = st.file_uploader(
    "Upload a bill (PDF, JPG, PNG)",
    type=["pdf", "jpg", "jpeg", "png"]
)

if uploaded_bill:
    st.success(f"Uploaded: {uploaded_bill.name}")

    bill_bytes = uploaded_bill.read()

    with st.spinner("AI reading the bill…"):
        extracted = extract_bill_data(bill_bytes)

    st.subheader("🔍 Extracted Data")
    st.write(extracted)

    # Convert AI JSON to Python dict
    try:
        data = eval(extracted)
        util = data["utility_type"]
        date = pd.to_datetime(data["invoice_date"])
        total = float(data["total_charge"])
        connect30 = total * 0.30

        new_row = {
            "Invoice Date": date,
            "Total Charge (Excl HST)": total,
            "Connect 30%": connect30
        }

        if util.lower() == "hydro":
            hydro_df.loc[len(hydro_df)] = new_row
            st.success("Hydro tab updated.")
        elif util.lower() == "gas":
            gas_df.loc[len(gas_df)] = new_row
            st.success("Gas tab updated.")
        elif util.lower() == "water":
            water_df.loc[len(water_df)] = new_row
            st.success("Water tab updated.")
        elif util.lower() == "snow":
            snow_df.loc[len(snow_df)] = new_row
            st.success("Snow Removal tab updated.")
        else:
            st.error("AI could not determine utility type.")

    except Exception as e:
        st.error(f"Error parsing AI output: {e}")

# ---------------------------------------------------
# Tabs
# ---------------------------------------------------
tabs = st.tabs(["Gas", "Hydro", "Water", "Snow Removal"])

with tabs[0]:
    st.header("Gas")
    st.dataframe(gas_df, use_container_width=True)

with tabs[1]:
    st.header("Hydro")
    st.dataframe(hydro_df, use_container_width=True)

with tabs[2]:
    st.header("Water")
    st.dataframe(water_df, use_container_width=True)

with tabs[3]:
    st.header("Snow Removal")
    st.dataframe(snow_df, use_container_width=True)

# ---------------------------------------------------
# Chart
# ---------------------------------------------------
st.subheader("📊 Utility Costs Over Time")

chart_data = pd.DataFrame()

for util_name, df in {
    "Gas": gas_df,
    "Hydro": hydro_df,
    "Water": water_df,
    "Snow Removal": snow_df
}.items():
    if not df.empty:
        temp = df.copy()
        temp["Utility"] = util_name
        chart_data = pd.concat([chart_data, temp])

if chart_data.empty:
    st.info("Upload bills to generate a chart.")
else:
    chart = (
        alt.Chart(chart_data)
        .mark_line(point=True)
        .encode(
            x="Invoice Date:T",
            y="Total Charge (Excl HST):Q",
            color="Utility:N",
            tooltip=["Utility", "Invoice Date", "Total Charge (Excl HST)"]
        )
        .properties(height=400)
    )
    st.altair_chart(chart, use_container_width=True)

