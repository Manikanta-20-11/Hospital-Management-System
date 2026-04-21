# 🏥 MediCare Hospital Management System (HMS)

> A comprehensive, role-based relational database application designed to digitalize and streamline the daily operations of a modern healthcare facility.

## 📖 Overview
MediCore (now **MediCare**) is a full-stack Hospital Management System built to eradicate the inefficiencies of manual record-keeping. It provides a highly secure, centralized platform that manages the entire patient lifecycle—from initial registration and doctor appointment booking to real-time inpatient ward admissions and automated financial billing.

This project was developed as a comprehensive Database Management Systems (DBMS - CSE209) academic project, demonstrating advanced SQL implementation, strict referential integrity, and a fully normalized database architecture.

## ✨ Key Features
The system is divided into three distinct, role-based access portals:

* **👨‍💼 Administrator Portal:** Master control hub featuring an executive dashboard for monitoring hospital KPIs (total patients, active staff, total revenue). Admins manage the hospital's workforce by securely adding new Doctors and Staff.
* **👩‍💻 Receptionist/Staff Portal:** The operational core. Staff can register new patients, book appointments with specialists, assign admitted patients to unoccupied rooms, and execute automated discharge and billing calculations.
* **🩺 Doctor Portal:** A restricted, focused medical view tailored for daily workflows, allowing doctors to view their specific appointment schedules and access registered patient records.

## 🛠️ Tech Stack
* **Frontend:** HTML5, CSS3, Vanilla JavaScript (Asynchronous Fetch API for SPA-like responsiveness)
* **Backend:** Python, Flask 
* **Database:** MySQL (Normalized to 3NF)

## 🗄️ Database Architecture
The backbone of MediCare is a highly structured MySQL database designed to prevent data redundancy and anomalies:
* **Third Normal Form (3NF):** Completely normalized schema utilizing surrogate primary keys across all transaction tables.
* **Advanced SQL:** Utilizes complex `JOIN`s for cross-referencing patient demographics with financial records, aggregate functions (`SUM`) for revenue tracking, and subqueries to filter available hospital beds.
* **Referential Integrity:** Strict Foreign Key constraints ensure data reliability (e.g., a patient cannot be billed without a corresponding admission record).
* **Database Views:** Implements virtual tables like `Active_Inpatients_View` and `Pending_Invoices_View` to optimize frequent operational queries.

## 🚀 Installation & Setup

**1. Clone the repository**
```bash
git clone
