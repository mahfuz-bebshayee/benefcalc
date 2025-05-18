import streamlit as st
from datetime import datetime, timedelta

def login():
    st.title("🔐 Benefit Calculator Login")
    password = st.text_input("Enter Password", type="password")
    if password == "09101993":
        return True
    elif password:
        st.error("Incorrect password.")
    return False

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
            # Validate and convert dates
            filing_date = datetime.strptime(filing_date_str.strip(), "%m/%d/%Y")
            pa_start_date = datetime.strptime(pa_start_str.strip(), "%m/%d/%Y")
            snap_start_date = datetime.strptime(snap_start_str.strip(), "%m/%d/%Y")

            toe_digit_table = {
                "0": (1, 15), "1": (2, 16), "2": (4, 18), "3": (5, 19),
                "4": (7, 21), "5": (8, 22), "6": (10, 24), "7": (11, 25),
                "8": (13, 27), "9": (14, 28)
            }

            toe_digit = toe_input.strip()
            st.info(f"🧩 Processing Toe Digit: '{toe_digit}'")  # Debug display

            if toe_digit not in toe_digit_table:
                st.error("❗ Invalid Toe Digit. Please enter a single digit from 0 to 9.")
                return

            sd, ed = toe_digit_table.get(toe_digit)
            f_and_o = round(pa_grant - shelter_amt, 2)
            f_and_o_cycles = []

            # First cycle check (could fall in previous month's B cycle)
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
                end_b = datetime(next_year, next_month, sd - 1)

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

            # Food Stamps
            fs_cycles = []
            fs_month = snap_start_date.month
            fs_year = snap_start_date.year
            budget_month = int(budget_effective[:-1])
            first_fs = True

            while True:
                fs_start = datetime(fs_year, fs_month, 1)
                fs_end = datetime(fs_year, fs_month + 1, 1) - timedelta(days=1) if fs_month < 12 else datetime(fs_year, fs_month, 31)
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

            # Shelter Grants
            shelter_cycles = []
            shelter_cutoff = datetime(2025, budget_month, ed if budget_effective.endswith("A") else 28)
            current = datetime(filing_date.year, filing_date.month, sd)

            while current < shelter_cutoff:
                m, y = current.month, current.year
                sa = datetime(y, m, sd)
                ea = datetime(y, m, ed)
                if sa >= shelter_cutoff: break
                shelter_cycles.append((f"{m}A", sa, ea, shelter_amt))
                sb = ea + timedelta(days=1)
                nm, ny = (m + 1, y) if m < 12 else (1, y + 1)
                eb = datetime(ny, nm, sd - 1)
                if sb >= shelter_cutoff: break
                shelter_cycles.append((f"{m}B", sb, eb, shelter_amt))
                current = eb + timedelta(days=1)

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

        except ValueError:
            st.error("⚠️ Please enter all dates in MM/DD/YYYY format.")
        except Exception as e:
            st.error(f"❌ Unexpected error: {e}")

if login():
    run_app()
