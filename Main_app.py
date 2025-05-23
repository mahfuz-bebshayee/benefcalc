import streamlit as st
from datetime import datetime, timedelta

def get_last_day_of_month(year, month):
    if month == 12:
        return datetime(year + 1, 1, 1) - timedelta(days=1)
    return datetime(year, month + 1, 1) - timedelta(days=1)

def login():
    st.title("🔐 Benefit Calculator Login")
    password = st.text_input("Enter Password", type="password")
    if password == "09101993":
        return True
    elif password:
        st.error("Incorrect password.")
    return False

def generate_shelter_cycles(filing_date, toe_digit, budget_effective, shelter_amt):
    toe_digit_table = {
        "0": (1, 15), "1": (2, 16), "2": (4, 18), "3": (5, 19),
        "4": (7, 21), "5": (8, 22), "6": (10, 24), "7": (11, 25),
        "8": (13, 27), "9": (14, 28)
    }
    sd, ed = toe_digit_table[toe_digit]

    # Calculate shelter cutoff
    budget_month = int(budget_effective[:-1])
    budget_half = budget_effective[-1]
    if budget_half == "A":
        shelter_cutoff = datetime(2025, budget_month, ed)
    else:
        next_month = budget_month + 1 if budget_month < 12 else 1
        next_year = 2025 if budget_month < 12 else 2026
        shelter_cutoff = datetime(next_year, next_month, max(sd - 1, 1))

    # Generate shelter cycles
    shelter_cycles = []
    current_year = filing_date.year
    current_month = filing_date.month

    while True:
        # A cycle
        start_a = datetime(current_year, current_month, sd)
        end_a = datetime(current_year, current_month, ed)
        if start_a > shelter_cutoff:
            break
        shelter_cycles.append((f"{current_month}A", start_a, end_a, shelter_amt))

        # B cycle
        start_b = end_a + timedelta(days=1)
        next_month = current_month + 1 if current_month < 12 else 1
        next_year = current_year if current_month < 12 else current_year + 1
        end_b = datetime(next_year, next_month, max(sd - 1, 1))
        if start_b > shelter_cutoff:
            break
        shelter_cycles.append((f"{current_month}B", start_b, end_b, shelter_amt))

        current_month = next_month
        current_year = next_year

    return shelter_cycles

def run_app():
    st.title("📊 Benefit Cycle Calculator")
    st.caption("Built for private use by Mahfuz bhai")

    st.subheader("📝 Case Information")
    toe_input = st.text_input("Toe Digit (0–9 only)")
    filing_date_str = st.text_input("Filing Date (MM/DD/YYYY)")
    pa_start_str = st.text_input("PA Start Date (MM/DD/YYYY)")
    snap_start_str = st.text_input("SNAP Start Date (MM/DD/YYYY)")

    st.subheader("💵 Benefit Amounts")
    shelter_amt = st.number_input("Shelter Amount", step=1.0)
    pa_grant = st.number_input("PA Grant Amount", step=1.0)
    fs_amt = st.number_input("Food Stamps Amount", step=1.0)

    st.subheader("🔁 Budget Effective Cycle")
    cycles = [f"{i}{c}" for i in range(1, 13) for c in ["A", "B"]]
    budget_effective = st.selectbox("Select Budget Cycle", cycles)

    if st.button("Calculate"):
        try:
            filing_date = datetime.strptime(filing_date_str.strip(), "%m/%d/%Y")
            pa_start_date = datetime.strptime(pa_start_str.strip(), "%m/%d/%Y")
            snap_start_date = datetime.strptime(snap_start_str.strip(), "%m/%d/%Y")

            toe_digit = toe_input.strip()
            toe_digit_table = {
                "0": (1, 15), "1": (2, 16), "2": (4, 18), "3": (5, 19),
                "4": (7, 21), "5": (8, 22), "6": (10, 24), "7": (11, 25),
                "8": (13, 27), "9": (14, 28)
            }

            if toe_digit not in toe_digit_table:
                st.error("❗ Invalid Toe Digit. Please enter a single digit from 0 to 9.")
                return

            sd, ed = toe_digit_table[toe_digit]
            f_and_o = round(pa_grant - shelter_amt, 2)
            f_and_o_cycles = []

            month = pa_start_date.month
            year = pa_start_date.year
            a_start = datetime(year, month, sd)
            if pa_start_date < a_start:
                month = 12 if month == 1 else month - 1
                year = year - 1 if month == 12 else year

            first = True
            while True:
                cycle_name = f"{month}A"
                start_a = datetime(year, month, sd)
                end_a = datetime(year, month, ed)

                if first:
                    if pa_start_date > end_a:
                        pass
                    elif pa_start_date > start_a:
                        days = (end_a - pa_start_date).days + 1
                        amt = round((f_and_o / 15.213) * days, 2)
                        f_and_o_cycles.append((cycle_name, pa_start_date, end_a, "Partial", amt))
                        first = False
                    else:
                        f_and_o_cycles.append((cycle_name, start_a, end_a, "Full", f_and_o))
                        first = False
                else:
                    f_and_o_cycles.append((cycle_name, start_a, end_a, "Full", f_and_o))

                if cycle_name == budget_effective:
                    break

                cycle_name_b = f"{month}B"
                start_b = end_a + timedelta(days=1)
                next_month = month + 1 if month < 12 else 1
                next_year = year if month < 12 else year + 1
                end_b = datetime(next_year, next_month, max(sd - 1, 1))

                if first:
                    if pa_start_date > end_b:
                        pass
                    elif pa_start_date > start_b:
                        days = (end_b - pa_start_date).days + 1
                        amt = round((f_and_o / 15.213) * days, 2)
                        f_and_o_cycles.append((cycle_name_b, pa_start_date, end_b, "Partial", amt))
                        first = False
                    else:
                        f_and_o_cycles.append((cycle_name_b, start_b, end_b, "Full", f_and_o))
                        first = False
                else:
                    f_and_o_cycles.append((cycle_name_b, start_b, end_b, "Full", f_and_o))

                if cycle_name_b == budget_effective:
                    break

                month = next_month
                year = next_year

            f_and_o_cycles[-1] = (*f_and_o_cycles[-1][:3], "Backup", f_and_o_cycles[-1][4])

            # FS (Food Stamps)
            fs_cycles = []
            fs_month = snap_start_date.month
            fs_year = snap_start_date.year
            budget_month = int(budget_effective[:-1])
            first_fs = True

            while True:
                fs_start = datetime(fs_year, fs_month, 1)
                fs_end = get_last_day_of_month(fs_year, fs_month)
                if first_fs:
                    if snap_start_date.day == 1:
                        fs_cycles.append((f"{fs_month}A", snap_start_date, fs_end, "Complete", fs_amt))
                    else:
                        fs_cycles.append((f"{fs_month}A", snap_start_date, fs_end, "Incomplete", "Refer to SNAP Proration Table (W-129UU)"))
                    first_fs = False
                else:
                    fs_cycles.append((f"{fs_month}A", fs_start, fs_end, "Complete", fs_amt))

                if fs_month == budget_month:
                    break

                fs_month += 1
                if fs_month > 12:
                    fs_month = 1
                    fs_year += 1

            # Shelter
            shelter_cycles = generate_shelter_cycles(filing_date, toe_digit, budget_effective, shelter_amt)

            # Output
            st.markdown("---")
            st.subheader("📦 F&O Cycles")
            for c, s, e, t, a in f_and_o_cycles:
                st.write(f"**{c}**: {s.strftime('%m/%d')} - {e.strftime('%m/%d')} | {t} | ${a}")

            st.subheader("🥫 Food Stamps")
            for c, s, e, t, a in fs_cycles:
                st.write(f"**{c}**: {s.strftime('%m/%d')} - {e.strftime('%m/%d')} | {t} | {a}")

            st.subheader("🏠 Shelter Grants")
            for c, s, e, a in shelter_cycles:
                st.write(f"**{c}**: {s.strftime('%m/%d')} - {e.strftime('%m/%d')} | ${a}")

        except ValueError as ve:
            st.error(f"⚠️ ValueError occurred: {ve}")
        except Exception as e:
            st.error(f"❌ Unexpected error: {e}")

if login():
    run_app()
