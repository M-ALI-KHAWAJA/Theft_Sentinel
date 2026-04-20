# Theft Sentinel - System Architecture

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLIENT APPLICATIONS                           │
│  (Web Dashboard / Mobile App / AI Detection System)              │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTPS/REST API
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     DJANGO REST API                              │
│                                                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  Auth    │  │ Cameras  │  │  Alerts  │  │Incidents │       │
│  │  (JWT)   │  │  CRUD    │  │  Mgmt    │  │ Workflow │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
│                                                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │Surveil-  │  │ Tracking │  │  Mobile  │  │Dashboard │       │
│  │ lance    │  │ Service  │  │ Notify   │  │Analytics │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
│                                                                   │
└────────┬──────────────────────┬──────────────────┬──────────────┘
         │                      │                  │
         ▼                      ▼                  ▼
┌──────────────────┐   ┌──────────────┐   ┌──────────────┐
│    MongoDB       │   │   Twilio     │   │  SMTP Email  │
│  (Database)      │   │   (SMS)      │   │   Service    │
└──────────────────┘   └──────────────┘   └──────────────┘
```

## 🔄 Request Flow

### 1. Authentication Flow
```
User → POST /api/auth/login/
       ↓
    [Validate Credentials]
       ↓
    [Generate JWT Tokens]
       ↓
    Response: {access, refresh, user}
       ↓
User stores tokens
       ↓
All subsequent requests include:
Header: Authorization: Bearer <access_token>
```

### 2. AI Event Processing Flow
```
AI System → POST /api/surveillance/ingest/
           {camera_id, event_type, ai_data}
              ↓
         [Validate Request]
              ↓
         [Save SurveillanceEvent]
              ↓
         [SurveillanceService.process_event()]
              ↓
         ┌────┴────┐
         ▼         ▼
    [Should      [Determine
     Create?]     Severity]
         │         │
         ▼         ▼
    [Create     [HIGH/MEDIUM/LOW]
     Alert]         │
         │          ▼
         └──→ [Should Create Incident?]
                    │
                    ▼
              [Create Incident]
                    │
                    ▼
              [Send Notifications]
                    │
                    ▼
              Response: {event, alert, incident}
```

### 3. Incident Management Flow
```
Alert Created
    ↓
Incident Auto-Created (if HIGH severity)
    ↓
Admin/Incharge assigns to Guard
    ↓
CREATED → ASSIGNED → ACKNOWLEDGED → RESOLVED
    │         │            │              │
    └─────────┴────────────┴──────────────┘
              [Notifications sent at each stage]
```

## 📊 Database Schema Relationships

```
User ─┬─→ Personnel (1:1)
      │
      ├─→ Incident (assigned_to) (1:M)
      │
      ├─→ Notification (1:M)
      │
      └─→ Feedback (1:M)

Camera ─┬─→ Alert (1:M)
        │
        ├─→ SurveillanceEvent (1:M)
        │
        └─→ TrackingRecord (1:M)

Alert ──→ Incident (1:M)

Personnel ──→ assigned_zones (Array)
```

## 🔐 Security Layers

```
Layer 1: Network Security
         ├─ HTTPS/SSL
         ├─ Firewall Rules
         └─ CORS Configuration

Layer 2: Authentication
         ├─ JWT Tokens
         ├─ Token Blacklisting
         └─ Password Hashing

Layer 3: Authorization
         ├─ Role-Based Access (RBAC)
         ├─ Permission Classes
         └─ Object-Level Permissions

Layer 4: Data Security
         ├─ Input Validation
         ├─ SQL Injection Prevention (ORM)
         └─ Environment Variables for Secrets
```

## 📱 API Endpoint Organization

```
/api/
├── auth/
│   ├── register/
│   ├── login/
│   ├── refresh/
│   ├── logout/
│   └── profile/
│
├── cameras/
│   ├── / (list/create)
│   ├── /{id}/ (detail)
│   ├── /{id}/status/
│   └── /zone/{zone}/
│
├── alerts/
│   ├── / (list/create)
│   ├── /{id}/ (detail)
│   ├── /{id}/acknowledge/
│   ├── /active/
│   └── /recent/
│
├── incidents/
│   ├── / (list/create)
│   ├── /{id}/ (detail)
│   ├── /{id}/status/
│   ├── /{id}/assign/
│   ├── /my-incidents/
│   └── /unassigned/
│
├── surveillance/
│   ├── /ingest/
│   ├── /events/
│   └── /events/{id}/
│
├── tracking/
│   ├── /ingest/
│   ├── /records/
│   ├── /records/{id}/
│   └── /person/{id}/path/
│
├── mobile/
│   ├── /notifications/
│   ├── /send-sms/
│   ├── /send-email/
│   └── /send-bulk/
│
├── dashboard/
│   ├── /overview/
│   ├── /alerts-stats/
│   ├── /incidents-stats/
│   ├── /cameras-stats/
│   └── /recent-activity/
│
├── feedback/
│   ├── / (list/create)
│   ├── /{id}/ (detail)
│   ├── /me/
│   └── /stats/
│
└── personnel/
    ├── / (list/create)
    ├── /{id}/ (detail)
    └── /me/
```

## 🎯 Service Layer Architecture

```
┌─────────────────────────────────────────┐
│         Views (API Endpoints)            │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│          Serializers                     │
│    (Validation & Transformation)         │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│         Business Logic Services          │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │  SurveillanceService               │ │
│  │  - process_event()                 │ │
│  │  - create_alert()                  │ │
│  │  - create_incident()               │ │
│  └────────────────────────────────────┘ │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │  NotificationService               │ │
│  │  - send_sms()                      │ │
│  │  - send_email()                    │ │
│  │  - send_bulk()                     │ │
│  └────────────────────────────────────┘ │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │  TrackingService                   │ │
│  │  - generate_person_id()            │ │
│  │  - find_similar_vectors()          │ │
│  │  - track_across_cameras()          │ │
│  └────────────────────────────────────┘ │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│         Models (Database Layer)          │
└─────────────────────────────────────────┘
```

## 🔄 State Machines

### Incident Status State Machine
```
     ┌─────────┐
     │ CREATED │
     └────┬────┘
          │
          ▼
     ┌─────────┐
     │ASSIGNED │
     └────┬────┘
          │
          ▼
     ┌──────────────┐
     │ACKNOWLEDGED  │
     └──────┬───────┘
            │
            ▼
     ┌─────────┐
     │RESOLVED │
     └─────────┘
```

### Alert Status State Machine
```
     ┌────────┐
     │ ACTIVE │
     └───┬────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌──────┐  ┌──────────┐
│ACKED │  │RESOLVED  │
└──────┘  └──────────┘
```

## 📈 Scalability Considerations

```
Current MVP:
├── Single Server
├── MongoDB (Single Instance)
└── Synchronous Processing

Future Scaling:
├── Load Balancer
│   ├── App Server 1
│   ├── App Server 2
│   └── App Server N
│
├── Database Cluster
│   ├── MongoDB Primary
│   └── MongoDB Replicas
│
├── Caching Layer
│   └── Redis Cluster
│
├── Message Queue
│   └── Celery + RabbitMQ
│       (for async notifications)
│
└── File Storage
    └── AWS S3 / Azure Blob
        (for frame images)
```

## 🧩 Module Dependencies

```
config
 └── settings.py (imports all apps)

apps.accounts (Base - No dependencies)
 ├── Custom User Model
 └── JWT Authentication

apps.personnel → depends on: accounts
 └── User profiles

apps.cameras (Independent)
 └── Camera management

apps.alerts → depends on: cameras
 └── Alert system

apps.incidents → depends on: alerts, accounts
 └── Incident workflow

apps.surveillance → depends on: cameras, alerts, incidents
 └── AI event processing

apps.tracking → depends on: cameras
 └── Person tracking

apps.mobile → depends on: accounts, personnel
 └── Notifications

apps.dashboard → depends on: ALL
 └── Analytics aggregation

apps.feedback → depends on: accounts
 └── User feedback
```

## 🔌 External Integrations

```
┌─────────────────────────────────────┐
│     Theft Sentinel Backend          │
└───────┬──────────────┬──────────────┘
        │              │
        ▼              ▼
┌──────────────┐  ┌──────────────┐
│   Twilio     │  │  SMTP Server │
│   SMS API    │  │   (Email)    │
└──────────────┘  └──────────────┘
        │              │
        ▼              ▼
┌──────────────┐  ┌──────────────┐
│  Guard's     │  │  Staff       │
│  Phone       │  │  Inbox       │
└──────────────┘  └──────────────┘


┌─────────────────────────────────────┐
│   AI Detection System (External)    │
└──────────────┬──────────────────────┘
               │ REST API
               ▼
┌─────────────────────────────────────┐
│  POST /api/surveillance/ingest/     │
│  {camera_id, event_type, ai_data}   │
└─────────────────────────────────────┘
```

## 📊 Data Flow Example: Complete Alert Lifecycle

```
1. AI Detection
   AI System detects theft
        ↓
2. Event Ingestion
   POST /surveillance/ingest/
   {camera_id: 1, event_type: "theft_detected", confidence: 0.95}
        ↓
3. Event Processing
   SurveillanceService validates and stores event
        ↓
4. Alert Creation
   High confidence → Create Alert (severity: HIGH, status: ACTIVE)
        ↓
5. Incident Creation
   HIGH severity → Auto-create Incident (status: CREATED)
        ↓
6. Notification
   NotificationService sends SMS + Email to admins
        ↓
7. Assignment
   Admin assigns incident to Guard (status: ASSIGNED)
        ↓
8. Guard Notification
   SMS + Email sent to assigned guard
        ↓
9. Acknowledgment
   Guard arrives on-site, updates status (ACKNOWLEDGED)
        ↓
10. Resolution
    Guard resolves issue, updates status (RESOLVED)
        ↓
11. Alert Closure
    Alert status updated to RESOLVED
        ↓
12. Analytics Update
    Dashboard stats refreshed with latest data
```

---

**This architecture supports:**
- ✅ Scalability (horizontal & vertical)
- ✅ Security (multi-layer)
- ✅ Maintainability (modular design)
- ✅ Extensibility (plugin architecture)
- ✅ Real-time processing
- ✅ High availability (with proper deployment)

