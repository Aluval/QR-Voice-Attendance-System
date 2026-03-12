import os
import cv2
import datetime
import numpy as np
import speech_recognition as sr
import qrcode
from resemblyzer import VoiceEncoder, preprocess_wav
import firebase_admin
from firebase_admin import credentials, firestore
from collections import defaultdict
from fpdf import FPDF
import smtplib
from email.message import EmailMessage

# Firebase setup
cred = credentials.Certificate("firebase_config.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

encoder = VoiceEncoder()
os.makedirs("voices", exist_ok=True)
os.makedirs("qr_codes", exist_ok=True)

# ------------------ Email Sender ------------------ #
def send_qr_to_email(name, email, qr_path):
    try:
        msg = EmailMessage()
        msg['Subject'] = f"Your Attendance QR Code"
        msg['From'] = "sunriseseditsoffical249@gmail.com"  # ✅ Replace
        msg['To'] = email
        msg.set_content(f"Hello {name},\n\nAttached is your QR code for the attendance system.\n\nBest regards.")

        with open(qr_path, 'rb') as f:
            qr_data = f.read()
            msg.add_attachment(qr_data, maintype='image', subtype='png', filename=os.path.basename(qr_path))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login("sunriseseditsoffical249@gmail.com", "lucymqnpdsvfdmyy")  # ✅ Replace
            smtp.send_message(msg)

        print(f"📧 QR Code sent to {email}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

# ------------------ QR & VOICE REGISTRATION ------------------ #
def record_voice(file_path):
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    print("🎤 Please speak your name or hall ticket number...")
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
    with open(file_path, "wb") as f:
        f.write(audio.get_wav_data())
    print(f"✅ Voice recorded and saved to {file_path}")

def generate_qr_and_register():
    student_id = input("Enter Hall Ticket Number: ").strip()
    name = input("Enter Full Name: ").strip()
    email = input("Enter Email Address: ").strip()

    existing = db.collection("users").document(student_id).get()
    if existing.exists:
        print(f"⚠️ Student already registered: {student_id}")
        return

    qr_path = f"qr_codes/{student_id}.png"
    qrcode.make(student_id).save(qr_path)
    print(f"✅ QR Code saved at: {qr_path}")

    voice_path = f"voices/{student_id}.wav"
    record_voice(voice_path)

    db.collection("users").document(student_id).set({
        "student_id": student_id,
        "name": name,
        "email": email,
        "voice_path": voice_path
    })

    send_qr_to_email(name, email, qr_path)
    print(f"✅ Registered {name} ({student_id}) in Firestore")

# ------------------ QR & VOICE VERIFICATION ------------------ #
def scan_qr_code():
    cap = cv2.VideoCapture(0)
    detector = cv2.QRCodeDetector()
    student_id = None
    print("📷 Scanning QR...")
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        data, bbox, _ = detector.detectAndDecode(frame)
        if data:
            student_id = data.strip()
            print("✅ QR Detected:", student_id)
            break
        cv2.imshow("QR Scanner - Press Q to cancel", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()
    return student_id

def record_live_voice(path):
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    print("🎤 Speak for verification...")
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
    with open(path, "wb") as f:
        f.write(audio.get_wav_data())
    print("✅ Voice recorded.")

def match_voice(student_id):
    reference_path = f"voices/{student_id}.wav"
    live_path = "voices/live_input.wav"
    if not os.path.exists(reference_path):
        print("❌ No reference voice found.")
        return False
    record_live_voice(live_path)
    ref = preprocess_wav(reference_path)
    live = preprocess_wav(live_path)
    ref_embed = encoder.embed_utterance(ref)
    live_embed = encoder.embed_utterance(live)
    similarity = np.dot(ref_embed, live_embed) / (np.linalg.norm(ref_embed) * np.linalg.norm(live_embed))
    print(f"🧠 Cosine Similarity: {similarity:.2f}")
    return similarity >= 0.75

# ------------------ ATTENDANCE ------------------ #
def is_within_time_slot():
    now = datetime.datetime.now()
    morning_start = now.replace(hour=8, minute=30, second=0, microsecond=0)
    morning_end = now.replace(hour=9, minute=0, second=0, microsecond=0)
    afternoon_start = now.replace(hour=16, minute=30, second=0, microsecond=0)
    afternoon_end = now.replace(hour=23, minute=0, second=0, microsecond=0)
    return (morning_start <= now < morning_end) or (afternoon_start <= now < afternoon_end)

def mark_attendance(student_id, status="Present", mode="QR+Voice"):
    now = datetime.datetime.now()
    session = "Morning" if now.hour < 12 else "Afternoon"
    today = now.date().isoformat()

    if not is_within_time_slot():
        print("⏰ Not in valid attendance time slot.")
        return

    existing = db.collection("attendance") \
        .where("student_id", "==", student_id) \
        .where("date", "==", today) \
        .where("session", "==", session) \
        .stream()

    if any(existing):
        print(f"⚠️ Attendance already marked for today’s {session} session.")
        return

    db.collection("attendance").add({
        "student_id": student_id,
        "time": now.isoformat(),
        "status": status,
        "mode": mode,
        "session": session,
        "date": today
    })

    stats_ref = db.collection("attendance_stats").document(student_id)
    stats = stats_ref.get()
    data = stats.to_dict() if stats.exists else {"total_days_present": 0, "total_days_attended": 0}
    if status == "Present":
        data["total_days_present"] += 1
    data["total_days_attended"] += 1
    data["attendance_percentage"] = round((data["total_days_present"] / data["total_days_attended"]) * 100, 2)
    stats_ref.set(data)

    print(f"🎉 Attendance marked: {student_id} as {status} ({session})")

# ------------------ EXPORTS ------------------ #
def export_monthly_report_for_student(student_id, month):
    records = db.collection("attendance") \
                .where("student_id", "==", student_id) \
                .where("date", ">=", f"{month}-01") \
                .where("date", "<=", f"{month}-31") \
                .stream()
    records = sorted([r.to_dict() for r in records], key=lambda x: x["date"])
    present = sum(1 for r in records if r.get("status", "").lower() == "present")
    total = len(records)
    absent = total - present
    percent = round((present / total) * 100, 2) if total > 0 else 0

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, f"Monthly Attendance Report - {student_id}", ln=True, align="C")
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, f"Month: {month}", ln=True)
    pdf.cell(0, 10, f"Total Sessions: {total}", ln=True)
    pdf.cell(0, 10, f"Present: {present}  |  Absent: {absent}", ln=True)
    pdf.cell(0, 10, f"Attendance Percentage: {percent}%", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", 'B', 11)
    pdf.cell(40, 10, "Date", 1)
    pdf.cell(30, 10, "Session", 1)
    pdf.cell(30, 10, "Status", 1)
    pdf.cell(70, 10, "Mode", 1)
    pdf.ln()

    pdf.set_font("Arial", '', 10)
    for r in records:
        pdf.cell(40, 10, r.get("date", ""), 1)
        pdf.cell(30, 10, r.get("session", ""), 1)
        pdf.cell(30, 10, r.get("status", ""), 1)
        pdf.cell(70, 10, r.get("mode", ""), 1)
        pdf.ln()

    filename = f"monthly_report_{student_id}_{month}.pdf"
    pdf.output(filename)
    print(f"✅ Exported PDF for {student_id}: {filename}")

def export_monthly_report_all_students(month):
    records = db.collection("attendance") \
                .where("date", ">=", f"{month}-01") \
                .where("date", "<=", f"{month}-31") \
                .stream()
    all_data = defaultdict(list)
    for r in records:
        data = r.to_dict()
        all_data[data["student_id"]].append(data)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, f"Monthly Attendance Report - All Students ({month})", ln=True, align="C")
    pdf.ln(5)

    for student_id, recs in all_data.items():
        recs = sorted(recs, key=lambda x: x["date"])
        present = sum(1 for r in recs if r.get("status", "").lower() == "present")
        total = len(recs)
        absent = total - present
        percent = round((present / total) * 100, 2) if total > 0 else 0

        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, f"Student ID: {student_id}  |  Present: {present}  |  Absent: {absent}  |  %: {percent}%", ln=True)

        pdf.set_font("Arial", 'B', 10)
        pdf.cell(40, 8, "Date", 1)
        pdf.cell(30, 8, "Session", 1)
        pdf.cell(30, 8, "Status", 1)
        pdf.cell(70, 8, "Mode", 1)
        pdf.ln()

        pdf.set_font("Arial", '', 9)
        for r in recs:
            pdf.cell(40, 8, r.get("date", ""), 1)
            pdf.cell(30, 8, r.get("session", ""), 1)
            pdf.cell(30, 8, r.get("status", ""), 1)
            pdf.cell(70, 8, r.get("mode", ""), 1)
            pdf.ln()

        pdf.ln(4)

    filename = f"monthly_report_ALL_{month}.pdf"
    pdf.output(filename)
    print(f"✅ Exported all-student PDF: {filename}")

def export_registered_users_list():
    users = db.collection("users").stream()
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "Registered Students List", ln=True, align="C")
    pdf.ln(5)

    pdf.set_font("Arial", 'B', 11)
    pdf.cell(50, 10, "Student ID", 1)
    pdf.cell(60, 10, "Name", 1)
    pdf.cell(70, 10, "Email", 1)
    pdf.ln()

    pdf.set_font("Arial", '', 10)
    for user in users:
        data = user.to_dict()
        pdf.cell(50, 10, data.get("student_id", ""), 1)
        pdf.cell(60, 10, data.get("name", ""), 1)
        pdf.cell(70, 10, data.get("email", ""), 1)
        pdf.ln()

    filename = "registered_students_list.pdf"
    pdf.output(filename)
    print(f"✅ Exported Registered Students List: {filename}")

# ------------------ MAIN MENU ------------------ #
def main_menu():
    print("\n📋 Main Menu : QR + Voice Attendance System :")
    print("1. Register Student (QR + Voice)")
    print("2. Mark Attendance (QR + Voice)")
    print("3. Export Attendance")
    print("4. Export Registered Students")
    choice = input("Select option (1-4): ").strip()

    if choice == "1":
        generate_qr_and_register()
    elif choice == "2":
        sid = scan_qr_code()
        if sid:
            if match_voice(sid):
                mark_attendance(sid)
            else:
                print("❌ Voice did not match!")
                mark_attendance(sid, status="Absent", mode="VoiceMismatch")
    elif choice == "3":
        print("\n📤 Export Menu:")
        print("1. Monthly Report (Single Student as PDF)")
        print("2. Monthly Report (All Students as PDF)")
        export_choice = input("Select export option (1-2): ").strip()
        month = input("Enter Month (YYYY-MM): ").strip()
        if export_choice == "1":
            sid = input("Enter Student ID: ").strip()
            export_monthly_report_for_student(sid, month)
        elif export_choice == "2":
            export_monthly_report_all_students(month)
        else:
            print("❌ Invalid choice.")
    elif choice == "4":
        export_registered_users_list()
    else:
        print("❌ Invalid choice.")

if __name__ == "__main__":
    main_menu()
