# Setu — Unified Identity Trust Graph Schema
This document defines the schema of the Neo4j graph database for **Setu**, a Unified Identity Trust & Fraud Prevention platform designed for the Bank of Baroda 2026 cybersecurity hackathon.

---

## 🔵 1. Node Types & Properties

| Node Label | Property Name | Data Type | Constraint / Description |
| :--- | :--- | :--- | :--- |
| **`Customer`** | `id` | `String` | **Unique Constraint**. Format: `CUST_XXXX` |
| | `name` | `String` | Full name of the customer |
| | `risk_baseline` | `Float` | Baseline risk score (0.0 to 1.0) calculated at onboarding |
| | `onboarding_aadhaar_verified` | `Boolean` | Flag indicating if Aadhaar e-KYC was verified during signup |
| | `account_age_days` | `Integer` | Number of days since the customer onboarded |
| **`Device`** | `fingerprint` | `String` | **Unique Constraint**. Hardware identifier of the device |
| | `os` | `String` | Operating System (e.g., Windows, macOS, Android, iOS) |
| | `browser` | `String` | Browser client (e.g., Chrome, Safari, Firefox, Edge) |
| | `is_new` | `Boolean` | Flag indicating if this device is new to this account |
| | `trust_score` | `Float` | Device trust reputation score (0.0 to 1.0) |
| **`Session`** | `id` | `String` | **Unique Constraint**. Format: `SESS_XXXX` or `SESS_FRD_XXX` |
| | `timestamp` | `DateTime` | ISO-8601 Timestamp of when the session started |
| | `ip` | `String` | IP address of the session connection |
| | `city` | `String` | City location mapped from the IP address |
| | `geolocation_lat` | `Float` | Latitude coordinate of the session IP |
| | `geolocation_lng` | `Float` | Longitude coordinate of the session IP |
| | `duration_seconds` | `Integer` | Active session duration in seconds |
| | `sim_swap_flag` | `Boolean` | Carrier-level alert indicating a recent SIM-swap event |
| | `label` | `String` | Target label: `"LEGITIMATE"` or `"FRAUD"` (for fraud ML models) |
| **`Employee`** | `id` | `String` | **Unique Constraint**. Format: `EMP_XXX` or `EMP_INS_XXX` |
| | `name` | `String` | Full name of the employee |
| | `role` | `String` | Access role: `"TELLER"`, `"BRANCH_OFFICER"`, `"KYC_ANALYST"`, `"MANAGER"` |
| | `access_level` | `Integer` | Internal security privilege level (1 to 5) |
| | `department` | `String` | Department name (e.g., Retail Operations, Compliance) |
| | `label` | `String` | Target label: `"LEGITIMATE"` or `"INSIDER"` (for insider ML models) |
| **`Account`** | `id` | `String` | **Unique Constraint**. Format: `ACC_XXXX` |
| | `balance_tier` | `String` | Balance tier classification: `"LOW"`, `"MID"`, `"HIGH"` |
| | `account_type` | `String` | Type of account: `"SAVINGS"`, `"CURRENT"` |
| | `is_frozen` | `Boolean` | Flag indicating if the account is currently locked |
| **`Beneficiary`** | `id` | `String` | **Unique Constraint**. Format: `BEN_XXXX` or `BEN_FRD_XXX` |
| | `bank_ifsc` | `String` | Indian Financial System Code (IFSC) of the recipient bank |
| | `is_first_time` | `Boolean` | Flag indicating if this is the customer's first transfer to this beneficiary |
| | `amount` | `Float` | Amount associated with the transaction node |

---

## 🟢 2. Relationship / Edge Types & Properties

| Edge Type | Source Node | Target Node | Edge Properties | Description |
| :--- | :--- | :--- | :--- | :--- |
| **`OWNS`** | `Customer` | `Account` | *None* | Links a customer to their bank accounts. |
| **`LOGGED_IN_FROM`**| `Customer` | `Device` | `timestamp` (`DateTime`) | Logs device registration and historical access per customer. |
| **`INITIATED`** | `Customer` | `Session` | `timestamp` (`DateTime`) | Links the customer to their active transaction/web sessions. |
| **`USED_DEVICE`** | `Session` | `Device` | `geovelocity_jump_km` (`Float`) | Records the device used for a session and calculates the speed/distance difference from the last session. |
| **`TRANSFERRED_TO`**| `Session` | `Beneficiary` | `amount` (`Float`), `timestamp` (`DateTime`) | Tracks fund transfers from a session to a beneficiary. |
| **`ACCESSED`** | `Employee` | `Account` | `timestamp` (`DateTime`), `action_type` (`String`), `outside_hours` (`Boolean`) | Tracks employee operations on client bank accounts. |
| **`VIEWED_KYC`** | `Employee` | `Customer` | `timestamp` (`DateTime`) | Tracks when an employee inspects a customer's KYC details. |
| **`RECOVERY_ATTEMPTED`**| `Account` | `Customer` | `timestamp` (`DateTime`), `new_device` (`Boolean`) | Records credentials recovery attempts made on an account. |

---

## 🔴 3. Integrity Constraints

To maintain referential integrity and ensure optimal query latency, the following constraints are defined:

1. **`Customer(id)`** is unique.
2. **`Device(fingerprint)`** is unique.
3. **`Session(id)`** is unique.
4. **`Employee(id)`** is unique.
5. **`Account(id)`** is unique.
6. **`Beneficiary(id)`** is unique.

---

## 🔍 4. Fraud and Insider Threat Mappings

### Fraud Scenario Indicators (25 cases)
- Labeled on `Session.label` as `"FRAUD"`.
- Co-occurrence criteria (occurring together in at least 15 of these cases):
  1. `Session.sim_swap_flag = true`
  2. `Device.is_new = true`
  3. `USED_DEVICE.geovelocity_jump_km > 800.0`
  4. `TRANSFERRED_TO.amount > 50000.0` on a recipient where `Beneficiary.is_first_time = true`.

### Insider Threat Scenario Indicators (15 cases)
- Labeled on `Employee.label` as `"INSIDER"`.
- Scenario pattern:
  1. Same employee node with role `"BRANCH_OFFICER"` or `"KYC_ANALYST"`.
  2. Accesses 3 or more distinct `"HIGH"` balance accounts (`Account.balance_tier = "HIGH"`) in under 60 minutes.
  3. Edge property `outside_hours = true` (before 9am or after 7pm).
  4. Within 2 hours of those accesses, a `RECOVERY_ATTEMPTED` edge fires from those accounts back to the customer owner.
