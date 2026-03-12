
# QR + Voice Attendance System

A **secure and contactless attendance system** that combines **QR code scanning** with **AI-based voice verification** to prevent proxy attendance.  
The system uses **OpenCV**, **SpeechRecognition**, and **Resemblyzer** for authentication and **Firebase Firestore** for real-time cloud storage.

Developed by **A.E. Harsha Vardhan Goud**

---

# Abstract

Traditional attendance systems such as manual entry, RFID cards, and biometric fingerprint devices face several challenges including proxy attendance, hardware dependency, maintenance costs, and long queues.  

This project proposes a **hybrid attendance system** that integrates **QR code scanning and voice authentication** to ensure secure identity verification.

The system uses **OpenCV** for QR detection, **SpeechRecognition** for capturing voice input, and **Resemblyzer** for converting voice samples into embedding vectors for similarity comparison. Attendance data and student profiles are stored in **Firebase Firestore**, enabling real-time monitoring and report generation.

This approach eliminates proxy attendance, reduces hardware dependency, and provides a scalable solution suitable for **educational institutions and remote authentication environments**.

---

# Features

- QR Code based student identification
- AI-powered voice verification
- Prevents proxy attendance
- Contactless attendance system
- Real-time cloud database storage
- Automatic QR code generation
- Email notification for registration
- Attendance report generation
- Scalable and low-cost implementation

---

# Technologies Used

| Technology | Purpose |
|-----------|--------|
| Python | Core programming language |
| OpenCV | QR code detection using webcam |
| SpeechRecognition | Capturing voice input |
| Resemblyzer | Voice embedding & verification |
| Firebase Firestore | Cloud database |
| SMTP | Email notification for QR code |

---

# System Architecture

1. Student Registration
2. Voice Recording
3. QR Code Generation
4. QR Code Email Delivery
5. QR Scan during attendance
6. Voice Verification
7. Attendance Marked in Firebase

---

# Authentication Flow

1. Student registers with:
   - Student ID
   - Name
   - Email

2. System performs:
   - Voice recording
   - QR code generation

3. QR code is sent to student email.

4. During attendance:
   - Student scans QR code
   - Student speaks for 5 seconds

5. Voice embedding is compared with stored embedding.

6. If similarity ≥ **0.75**, attendance is marked **Present**.

---

# Data Captured

The system records the following information:

- Hall Ticket Number
- Student Name
- Email
- Voice Embedding Vector
- Date
- Time
- Session (Morning / Afternoon)
- Attendance Status

---

# Firebase Firestore Structure

## Users Collection
```

users
└─ student_id
├─ name
├─ email
├─ voice_path

```

## Attendance Collection
```

attendance
└─ auto_id
├─ student_id
├─ date
├─ session
├─ time
├─ status

```

## Attendance Statistics
```

attendance_stats
└─ student_id
├─ total_days_present
├─ total_days_attended
├─ attendance_percentage

```

---

# Results

- Voice verification accuracy: **>90%**
- QR scanning time: **< 2 seconds**
- False positive rate: **<6%**
- Proxy attendance prevention: **High**

The system successfully reduces hardware costs while improving security and scalability.

---

# Advantages

- Prevents proxy attendance
- Contactless authentication
- Low hardware dependency
- Cloud-based data storage
- Easy integration in institutions
- Fast authentication process

---

# Applications

- Educational institutions
- Online learning environments
- Corporate attendance systems
- Secure authentication platforms

---

# Future Improvements

- Mobile app integration
- Offline voice verification
- Multi-factor authentication
- Advanced analytics dashboard

---

# License

This project is licensed under the **Apache License 2.0**.

You are free to:

- Use
- Modify
- Distribute

the code according to the Apache License terms.

---

# Project Ownership & Attribution

This project **QR + Voice Attendance System** was developed by:

**A.E. Harsha Vardhan Goud**

If you use or modify this project, proper **credit must be given to the original author**.

Misrepresenting this project as your own work or redistributing it without attribution is strictly discouraged.

Unauthorized misuse or misleading redistribution may result in action under **GitHub DMCA policies**.

---

# Author

**A.E. Harsha Vardhan Goud**  
MCA 

---

⭐ If you found this project useful, consider giving it a **star** on GitHub.

