import streamlit as st
from datetime import datetime, timedelta

# --- CONFIG ---
st.set_page_config(page_title="Benefit Calculator", layout="centered")

# --- LOGIN ---
def login():
    st.title("🔐 Benefit Calculator")
    password = st.text_input("Enter Password", type="password")
    if password == "bismillah2025":
        return True
    elif password:
        st.error("Incorrect password")
        return False
    return False

if not login():
    st.stop()

# --- APP FORM ---
st.title("📊 Benefit Calculator")
st.markdown("""---""")

with st.form("calc_form"):
    st.subheader("Case Information")
    case_number = st.text_input("Case Number")
    filing_date = st.date_input("Filing Date")
    pa_start_date = st.date_input("PA Start Date")
    snap_start_date = st.date_input("SNAP Start Date", help="Consider if ESNAP was issued")

    st.subheader("Benefit Amounts")
    shelter = st.number_input("Shelter Amount", min_value=0.0, step=0.01)
    grant = st.number_input("PA Grant Amount", min_value=0.0, step=0.01)
    fs_amount = st.number_input("Food Stamps Amount", min_value=0.0, step=0.01)

    st.subheader("Cycle Options")
    cycle_options = [f"{i}{c}" for i in range(1, 13) for c in ["A", "B"]]
    budget_cycle = st.selectbox("Budget Effective Cycle", cycle_options)

    submitted = st.form_submit_button("Generate Breakdown")

if submitted:
    toe_digit_table = {
        "0": (1, 15), "1": (2, 16), "2": (4, 18), "3": (5, 19),
        "4": (7, 21), "5": (8, 22), "6": (10, 24), "7": (11, 25),
        "8": (13, 27), "9": (14, 28)
    }

    try:
        toe_digit = case_number[-1]
        sd, ed = toe_digit_table[toe_digit]
        f_and_o = round(grant - shelter, 2)

        st.success(f"TOE Digit: {toe_digit} | F&O: ${f_and_o:.2f}")

        # --- F&O CYCLES ---
        f_and_o_cycles = []
        month = pa_start_date.month
        year = pa_start_date.year
        first_cycle_handled = False

        while True:
            cycle_name = f"{month}A"
            start_a = datetime(year, month, sd).date()
            end_a = datetime(year, month, ed).date()

            if not first_cycle_handled:
                if pa_start_date > start_a:
                    days = (end_a - pa_start_date).days + 1
                    partial_amt = round((f_and_o / 15) * days, 2)
                    f_and_o_cycles.append((cycle_name, pa_start_date, end_a, "Partial", partial_amt))
                else:
                    f_and_o_cycles.append((cycle_name, start_a, end_a, "Full", f_and_o))
                first_cycle_handled = True
            else:
                f_and_o_cycles.append((cycle_name, start_a, end_a, "Full", f_and_o))

            if cycle_name == budget_cycle:
                break

            # B Cycle
            cycle_name_b = f"{month}B"
            start_b = end_a + timedelta(days=1)
            next_month = month + 1 if month < 12 else 1
            next_year = year if month < 12 else year + 1
            end_b = datetime(next_year, next_month, sd - 1).date()

            f_and_o_cycles.append((cycle_name_b, start_b, end_b, "Full", f_and_o))

            if cycle_name_b == budget_cycle:
                break

            month = next_month
            year = next_year

        # Mark last as Backup
        last = f_and_o_cycles[-1]
        f_and_o_cycles[-1] = (*last[:3], "Backup", last[4])

        # --- FS CYCLES ---
        fs_cycles = []
        fs_month = snap_start_date.month
        fs_year = snap_start_date.year
        budget_month = int(budget_cycle[:-1])
        first_fs = True

        while True:
            fs_start = datetime(fs_year, fs_month, 1).date()
            if fs_month < 12:
                fs_end = datetime(fs_year, fs_month + 1, 1).date() - timedelta(days=1)
            else:
                fs_end = datetime(fs_year, fs_month, 31).date()

            if first_fs:
                if snap_start_date.day == 1:
                    fs_cycles.append((f"{fs_month}A", snap_start_date, fs_end, "Complete", fs_amount))
                else:
                    fs_cycles.append((f"{fs_month}A", snap_start_date, fs_end, "Incomplete", "Please check SNAP Proration Table, W-129UU"))
                first_fs = False
            else:
                fs_cycles.append((f"{fs_month}A", fs_start, fs_end, "Complete", fs_amount))

            if fs_month == budget_month:
                break

            fs_month += 1
            if fs_month > 12:
                fs_month = 1
                fs_year += 1

        # --- SHELTER CYCLES ---
        shelter_cycles = []
        shelter_start = datetime(filing_date.year, filing_date.month, sd).date()
        budget_half = budget_cycle[-1]
        shelter_cutoff = datetime(2025, budget_month, ed if budget_half == "A" else 28).date()

        current = shelter_start
        while current < shelter_cutoff:
            m, y = current.month, current.year
            sa = datetime(y, m, sd).date()
            ea = datetime(y, m, ed).date()
            if sa >= shelter_cutoff: break
            shelter_cycles.append((f"{m}A", sa, ea, shelter))
            sb = ea + timedelta(days=1)
            if m < 12:
                eb = datetime(y, m + 1, sd - 1).date()
            else:
                eb = datetime(y + 1, 1, sd - 1).date()
            if sb >= shelter_cutoff: break
            shelter_cycles.append((f"{m}B", sb, eb, shelter))
            current = eb + timedelta(days=1)

        # --- DISPLAY ---
        st.markdown("""---""")
        st.subheader("F&O Breakdown")
        for c, s, e, t, a in f_and_o_cycles:
            st.markdown(f"`{c}`: {s.strftime('%m/%d')} - {e.strftime('%m/%d')} | {t} | **${a}**")

        st.subheader("Food Stamps")
        for c, s, e, t, a in fs_cycles:
            st.markdown(f"`{c}`: {s.strftime('%m/%d')} - {e.strftime('%m/%d')} | {t} | **{a}**")

        st.subheader("Shelter Grant")
        for c, s, e, a in shelter_cycles:
            st.markdown(f"`{c}`: {s.strftime('%m/%d')} - {e.strftime('%m/%d')} | **${a}**")

    except Exception as e:
        st.error(f"An error occurred: {e}")
