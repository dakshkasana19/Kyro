# TRIAGE-AI — Phase 3 & Phase 4 Implementation Plan

This document outlines the structured execution roadmap for Phase 3 and Phase 4 of the TRIAGE-AI system.

---

# 👥 Team Structure

| Member    | Focus Area |
|-----------|------------|
| Saivats  | Backend Systems, Real-Time Infrastructure, Security, Optimization |
| Daksh     | Frontend Development, UI/UX, Integration, Testing |

---

# 🚀 Phase 3 — Real-Time UI, Authentication & System Integration  
**Estimated Duration:** 3–4 Weeks

---

## Week 1–2: Core UI & Authentication

### 3.1 Frontend Setup  
**Owner:** Daksh  
- Initialize React / Next.js project  
- Configure routing  
- Setup Tailwind CSS  
- Configure component library  

### 3.2 Patient Intake Form UI  
**Owner:** Daksh  
- Multi-step form:
  - Demographics
  - Vitals
  - Symptoms
  - Medical history  
- Client-side validation  

### 3.3 Supabase Authentication (Backend)  
**Owner:** Saivats  
- JWT middleware integration  
- Role-based access control (Admin / Doctor / Nurse)  
- Login & signup API endpoints  

### 3.4 Supabase Authentication (Frontend)  
**Owner:** Daksh  
- Login/signup UI  
- Token management  
- Protected routes  

### 3.5 WebSocket Server Setup (Flask-SocketIO)  
**Owner:** Saivats  
- Real-time queue broadcasting  
- Doctor load updates  
- New patient alerts  

### 3.6 Redis Caching Layer  
**Owner:** Saivats  
- Cache queue state  
- Cache doctor loads  
- Cache recent predictions  
- Optimize read latency  

---

## Week 3–4: Dashboards & Live Updates

### 3.7 Admin Dashboard UI  
**Owner:** Daksh  
- Live queue table (severity-sorted)  
- Patient cards  
- Doctor availability panel  

### 3.8 Doctor Portal UI  
**Owner:** Daksh  
- Assigned patients list  
- Triage details view  
- SHAP explanation display  

### 3.9 Real-Time Queue Integration  
**Owner:** Daksh  
- WebSocket listener  
- Auto-refresh queue  
- Severity color coding  

### 3.10 Audit Log API + Viewer  
**Owner:** Saivats  
- `/api/audit` endpoint  
- Filterable admin log viewer  

### 3.11 Model Retraining Endpoint  
**Owner:** Saivats  
- `/api/admin/retrain`  
- CSV upload support  
- Model swap logic  
- Retraining logs  

### 3.12 Doctor CRUD UI  
**Owner:** Daksh  
- Add / Edit / Remove doctors  
- Specialization management  
- Availability toggling  

### 3.13 Notification System  
**Owner:** Saivats  
- Critical patient WebSocket alerts  
- Optional email/SMS stub  

### 3.14 Integration Testing  
**Owner:** Saivats  
- End-to-end validation:
  - Intake → Prediction → Assignment → Queue update → UI refresh  

---

## ✅ Phase 3 Deliverables

- Fully functional UI with authentication  
- Real-time queue dashboard  
- Doctor portal with SHAP explanations  
- WebSocket-based live updates  
- Redis caching layer  
- Model retraining functionality  

---

# 🏥 Phase 4 — Multi-Tenancy & Production Hardening  
**Estimated Duration:** 3–4 Weeks  

---

## Week 1–2: Multi-Tenancy & Security

### 4.1 Multi-Tenant Database Schema  
**Owner:** Saivats  
- Add `hospital_id` to all tables  
- Configure Supabase Row Level Security (RLS)  

### 4.2 Tenant-Aware API Middleware  
**Owner:** Saivats  
- Extract `hospital_id` from JWT  
- Scope all queries by tenant  

### 4.3 Hospital Onboarding Flow  
**Owner:** Saivats  
- `/api/admin/hospitals`  
- Seed admin user  
- Configure hospital settings  

### 4.4 Hospital Switcher UI  
**Owner:** Daksh  
- Dropdown-based hospital context switching  
- Super-admin controls  

### 4.5 Security Hardening  
**Owner:** Saivats  
- Encrypt PII at rest  
- Audit logging for all access  
- Rate limiting  
- Input sanitization  

### 4.6 Role Management UI (RBAC Panel)  
**Owner:** Daksh  
- Assign roles  
- Invite users  
- Permission management  

---

## Week 3–4: Scaling, Optimization & Analytics

### 4.7 Analytics Dashboard  
**Owner:** Daksh  
- Severity distribution charts  
- Average wait time  
- Doctor utilization  
- Daily trends visualization  

### 4.8 Advanced Doctor Assignment (LP Solver)  
**Owner:** Saivats  
- Replace greedy logic with:
  - `scipy.optimize.linprog` or PuLP  
- Multi-objective optimization:
  - Minimize wait time  
  - Balance doctor workload  

### 4.9 Kubernetes Deployment Configuration  
**Owner:** Saivats  
- Helm charts  
- Horizontal Pod Autoscaling  
- Health probes  

### 4.10 Monitoring & Observability  
**Owner:** Saivats  
- Prometheus metrics  
- Grafana dashboards  
- API latency tracking  
- Prediction throughput monitoring  
- Model drift alerts  

### 4.11 EMR/EHR Integration Stub  
**Owner:** Saivats  
- FHIR-compatible import/export endpoints  

### 4.12 Accessibility & Mobile Optimization  
**Owner:** Daksh  
- WCAG 2.1 AA compliance  
- Responsive layouts  
- Touch-friendly components  

### 4.13 Final Testing & Documentation  
**Owner:** Both  
- Load testing  
- Penetration testing  
- API documentation (Swagger)  
- End-user documentation  

---

## ✅ Phase 4 Deliverables

- Multi-hospital data isolation  
- Hardened security architecture  
- Advanced doctor assignment optimization  
- Production-ready Kubernetes deployment  
- Monitoring & alerting stack  
- Analytics & reporting dashboard  
- Complete technical documentation  

---

# 🧭 Overall Execution Strategy

Phase 3 focuses on:

- Real-time functionality  
- UI integration  
- Authentication  
- System cohesion  

Phase 4 focuses on:

- Scalability  
- Security  
- Multi-tenancy  
- Production readiness  

---

TRIAGE-AI evolves from a functional AI engine into a scalable, secure, real-time hospital-grade system by the completion of these phases.