import os
import csv
import xml.etree.ElementTree as ET
import datetime

from GUI_for_updating_deliverable2 import MultiStepApp

def extract_sleep_data(xml_file_path):
    if not xml_file_path or not os.path.isfile(xml_file_path):
        return {}

    results = {}
    tree = ET.parse(xml_file_path)
    root = tree.getroot()

    sleep_sessions = []
    current_session = None

    for record in root.findall(".//Record[@type='HKCategoryTypeIdentifierSleepAnalysis']"):
        start_str = record.get('startDate')
        end_str = record.get('endDate')
        value = record.get('value')  # 0 = In Bed, 1 = Asleep

        # Skip records with 'HKCategoryValueSleepAnalysisInBed'
        if value == "HKCategoryValueSleepAnalysisInBed":
            continue

        if not start_str or not end_str:
            continue

        try:
            # Parse start and end times
            start_time = datetime.datetime.fromisoformat(start_str)
            end_time = datetime.datetime.fromisoformat(end_str)
            date = start_time.date()

            # Convert to decimal hours
            start_decimal = start_time.hour + start_time.minute / 60 + start_time.second / 3600
            end_decimal = end_time.hour + end_time.minute / 60 + end_time.second / 3600

            # Handle session continuity
            if current_session is None:
                # Start a new session
                current_session = {
                    "start_time": start_decimal,
                    "end_time": end_decimal,
                    "end_date": date
                }
            else:
                # Check if this entry is part of the ongoing session
                if abs(current_session["end_time"] - start_decimal) < 1e-6:  # Match end time with start time
                    current_session["end_time"] = end_decimal  # Extend the session
                    current_session["end_date"] = date  # Update the session's end date
                else:
                    # Finalize the current session and start a new one
                    sleep_sessions.append({
                        "date": current_session["end_date"],
                        "start_time": current_session["start_time"],
                        "end_time": current_session["end_time"]
                    })
                    current_session = {
                        "start_time": start_decimal,
                        "end_time": end_decimal,
                        "end_date": date
                    }
        except Exception as e:
            print(f"Error processing record: {e}")  # Debugging info

    # Add the last session if any
    if current_session is not None:
        sleep_sessions.append({
            "date": current_session["end_date"],
            "start_time": current_session["start_time"],
            "end_time": current_session["end_time"]
        })

    # Calculate duration and format results
    for session in sleep_sessions:
        duration = session["end_time"] - session["start_time"]
        if duration < 0:
            duration += 24  # Adjust for crossing midnight

        results[session["date"]] = {
            "sleep_start": f"{session['start_time']:.2f}",
            "sleep_end": f"{session['end_time']:.2f}",
            "duration": f"{duration:.2f}"
        }

    return results


def generate_csv_report(user_data):
    """
    1) Extract sleep data from the XML file named at user_data['health_data_file'].
    2) For each day in `user_data['day_data']`, use day_item['date'] (a Python datetime.date)
       to find the matching record in sleep_dict and build the CSV.
    """
    print('user_data=', user_data)
    xml_path    = user_data.get("health_data_file","")
    sleep_dict  = extract_sleep_data(xml_path)
    print(xml_path)
    print('sleep_dict =', sleep_dict)

    csv_filename = "output_sleep_cycle_productivity.csv"
    need_header  = not os.path.isfile(csv_filename)

    with open(csv_filename, mode='a', newline='') as f:
        writer = csv.writer(f)

        if need_header:
            writer.writerow([
                "Date","Person_ID","Age","Gender","Sleep Start Time","Sleep End Time","Total Sleep Hours",
                "Sleep Quality","Exercise (mins/day)","Caffeine Intake (mg)",
                "Screen Time Before Bed (mins)","Work Hours (hrs/day)",
                "Productivity Score","Mood Score","Stress Level"
            ])

        person_id = user_data.get("person_id","")
        age       = user_data.get("age","")
        gender    = user_data.get("gender","")

        for day_item in user_data.get("day_data", []):
            dt_obj = day_item.get("date", None)
            if not isinstance(dt_obj, datetime.date):
                continue

            # Look up in sleep_dict
            rec = sleep_dict.get(dt_obj, {})
            s_start = rec.get("sleep_start","")
            s_end   = rec.get("sleep_end","")
            s_dur   = rec.get("duration","")

            sleep_quality  = day_item.get("sleep_quality","")
            exercise_mins  = day_item.get("exercise_minutes","")
            caffeine_mg = day_item.get("caffeine_intake", 0)

            screen_mins   = day_item.get("screen_time_minutes","")
            work_hrs      = day_item.get("work_hours","")
            productivity  = day_item.get("productivity","")
            mood_score    = day_item.get("mood","")
            stress_level  = day_item.get("stress","")

            row_date = dt_obj.strftime("%Y-%m-%d")

            row = [
                row_date,         # Date (yyyy-mm-dd)
                person_id,        # Person_ID
                age,              # Age
                gender,           # Gender
                s_start,          # Sleep Start Time
                s_end,            # Sleep End Time
                s_dur,            # Total Sleep Hours
                sleep_quality,    # Sleep Quality
                exercise_mins,    # Exercise (mins/day)
                caffeine_mg,      # Caffeine Intake (mg) from espresso shots
                screen_mins,      # Screen Time Before Bed (mins)
                work_hrs,         # Work Hours (hrs/day)
                productivity,     # Productivity Score
                mood_score,       # Mood Score
                stress_level      # Stress Level
            ]

            writer.writerow(row)

    print(f"[INFO] CSV updated => {csv_filename}")

class MyApp(MultiStepApp):
    """
    Subclass your existing MultiStepApp from GUI_deliverable2.py 
    to override `submit_all()` so we can run our CSV logic.
    """
    def submit_all(self):
        # Gather the data from the GUI the same way your original code does.
        info = {
            "age": self.age.get(),
            "gender": self.gender.get(),
            "person_id": self.person_id.get(),
            "num_days": self.num_days.get(),
            "day_data": self.day_data,
            "health_data_file": self.health_data_file.get()
        }
        
        # 1) Generate CSV
        generate_csv_report(info)

        # 2) Do original behavior (print to console, show messagebox, etc.)
        print('q_info =', info)
        from tkinter import messagebox
        messagebox.showinfo("Submitted", "Your data has been processed and CSV updated.")


def main():
    # Launch your updated MyApp
    app = MyApp()
    app.title("Sleep vs Productivity - Combined Program")
    app.mainloop()

if __name__ == "__main__":
    main()