# DB Guard - User Flow Diagram

## Application Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         START APPLICATION                        │
│                         localhost:3000                           │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                        LOGIN PAGE (/)                            │
│                                                                  │
│  ┌──────────────────┐              ┌──────────────────┐        │
│  │  CLIENT LOGIN    │              │    DBA LOGIN     │        │
│  │                  │              │                  │        │
│  │  Enter Client ID │              │   Enter PIN      │        │
│  │  (any number)    │              │   (default:1234) │        │
│  └────────┬─────────┘              └────────┬─────────┘        │
│           │                                 │                   │
└───────────┼─────────────────────────────────┼──────────────────┘
            │                                 │
            │                                 │
            ▼                                 ▼
┌─────────────────────────┐      ┌───────────────────────────────┐
│  CLIENT DASHBOARD       │      │     DBA DASHBOARD             │
│  (/client-dashboard)    │      │     (/dba-dashboard)          │
│                         │      │                               │
│  ┌──────────────────┐   │      │  ┌──────────────────────┐    │
│  │ Query Console    │   │      │  │ Metrics Cards        │    │
│  │ • SQL Input      │   │      │  │ • Total Queries      │    │
│  │ • Execute Button │   │      │  │ • Slow Queries       │    │
│  │ • Console Output │   │      │  │ • Avg Time           │    │
│  └──────────────────┘   │      │  │ • Active Clients     │    │
│                         │      │  └──────────────────────┘    │
│  ┌──────────────────┐   │      │                               │
│  │ Alerts (0)       │   │      │  ┌──────────────────────┐    │
│  │ • No alerts      │   │      │  │ Charts               │    │
│  └──────────────────┘   │      │  │ • Timeline           │    │
│                         │      │  │ • Client Activity    │    │
│  ┌──────────────────┐   │      │  │ • Query Types        │    │
│  │ Query Details    │   │      │  └──────────────────────┘    │
│  │ • Status         │   │      │                               │
│  │ • Execution Time │   │      │  ┌──────────────────────┐    │
│  │ • Rows Affected  │   │      │  │ Recent Alerts        │    │
│  │ • Root Causes    │   │      │  └──────────────────────┘    │
│  └──────────────────┘   │      │                               │
│                         │      │  ┌──────────────────────┐    │
│  ┌──────────────────┐   │      │  │ All Queries Preview  │    │
│  │ Query History    │   │      │  └──────────────────────┘    │
│  │ • Last 10 Queries│   │      │                               │
│  └──────────────────┘   │      │  ┌──────────────────────┐    │
│                         │      │  │ Clients Grid         │    │
│  [Logout]               │      │  │ ┌───┐ ┌───┐ ┌───┐   │    │
│                         │      │  │ │ 1 │ │ 2 │ │ 3 │   │    │
└─────────────────────────┘      │  │ └─┬─┘ └───┘ └───┘   │    │
                                 │  └───┼────────────────────┘    │
                                 │      │                         │
                                 │  ┌───▼──────────────────┐    │
                                 │  │ Activity Logs Table  │    │
                                 │  │ • All client logs    │    │
                                 │  └──────────────────────┘    │
                                 │                               │
                                 │  [Logout]                     │
                                 └───────────────┬───────────────┘
                                                 │ Click Client
                                                 ▼
                                 ┌───────────────────────────────┐
                                 │  CLIENT DETAILS               │
                                 │  (/client/:clientId)          │
                                 │                               │
                                 │  ┌──────────────────────┐    │
                                 │  │ Client Statistics    │    │
                                 │  │ • Total Queries      │    │
                                 │  │ • Slow Queries       │    │
                                 │  └──────────────────────┘    │
                                 │                               │
                                 │  ┌──────────────────────┐    │
                                 │  │ Alert Banners        │    │
                                 │  └──────────────────────┘    │
                                 │                               │
                                 │  ┌──────────────────────┐    │
                                 │  │ Query Table          │    │
                                 │  │ • Timestamp          │    │
                                 │  │ • Query              │    │
                                 │  │ • Result             │    │
                                 │  │ • Status             │    │
                                 │  │ • Score              │    │
                                 │  │ • Root Causes        │    │
                                 │  │ • Alert              │    │
                                 │  └──────────────────────┘    │
                                 │                               │
                                 │  [← Back to Dashboard]        │
                                 └───────────────────────────────┘
```

## Access Control

```
┌─────────────────────────────────────────────────────────────────┐
│                      AUTHENTICATION FLOW                         │
└─────────────────────────────────────────────────────────────────┘

DBA Login:
  Input: PIN (1234)
  Session: userType = "dba"
  Access:
    ✅ DBA Dashboard (full access)
    ✅ Client Details (all clients)
    ✅ Activity Logs
    ✅ All Metrics
    ❌ Client Dashboard (not relevant)

Client Login:
  Input: Client ID (any number)
  Session: userType = "client", clientId = <number>
  Access:
    ✅ Client Dashboard (query console only)
    ❌ DBA Dashboard
    ❌ Other client details
    ❌ Activity Logs
```

## Component Hierarchy

```
App.js
├── Login.jsx (/)
│   ├── Client Login Form
│   └── DBA Login Form
│
├── DBADashboard.jsx (/dba-dashboard)
│   ├── Header + Logout
│   ├── Metrics Grid (4 cards)
│   ├── Timeline Chart
│   ├── Client Activity Chart
│   ├── Query Type Chart
│   ├── Alerts Section
│   ├── Queries Preview
│   ├── Clients Grid
│   └── Logs Table
│
├── ClientDashboard.jsx (/client-dashboard)
│   ├── Header + Logout
│   ├── Console Section
│   │   ├── Alert Box
│   │   ├── Query Input Panel
│   │   └── Console Output
│   └── Sidebar
│       ├── Alerts Section
│       ├── Query Details
│       └── Query History
│
└── ClientDetails.jsx (/client/:clientId)
    ├── Header + Back Button
    ├── Alert Banners
    ├── Statistics Cards
    ├── Charts
    └── Query Table
```

## Color Coding

```
STATUS INDICATORS:
┌─────────────────────────────────────────┐
│ SUCCESS    │ #4dff88  │ Green          │
│ NORMAL     │ #26c6da  │ Cyan           │
│ NEAR SLOW  │ #ffb84d  │ Orange         │
│ SLOW       │ #ef5350  │ Red            │
│ ALERT      │ #ff4444  │ Bright Red     │
└─────────────────────────────────────────┘

BACKGROUNDS:
┌─────────────────────────────────────────┐
│ Primary    │ #0a0a0a  │ Black          │
│ Card       │ #1a1a1a  │ Dark Grey      │
│ Secondary  │ #2a2a2a  │ Medium Grey    │
│ Console    │ #000000  │ Pure Black     │
└─────────────────────────────────────────┘
```

## Data Flow

```
FRONTEND                    BACKEND
────────                    ───────

Login Page
    │
    ├──── POST /api/connect ────────────► Server
    │                                      │
    │     ◄──────────── {status} ──────────┤
    │
    └──── Redirect to Dashboard

DBA Dashboard
    │
    ├──── GET /api/dashboard ──────────► Server
    │     ◄──────────── {metrics} ────────┤
    │
    ├──── GET /api/logs ───────────────► Server
    │     ◄──────────── {logs} ───────────┤
    │
    └──── GET /api/all_queries ────────► Server
          ◄──────────── {queries} ────────┤

Client Dashboard
    │
    ├──── POST /api/connect ───────────► Server
    │     ◄──────────── {status} ─────────┤
    │
    └──── POST /api/execute_query ─────► Server
          ◄──────────── {result} ─────────┤

Client Details
    │
    └──── GET /api/client/:id ─────────► Server
          ◄──────────── {clientData} ────┤
```

## Session Management

```
sessionStorage Keys:
┌──────────────────────────────────────────┐
│ userType   │ "dba" or "client"          │
│ clientId   │ Stored for client users    │
└──────────────────────────────────────────┘

On Page Load:
1. Check sessionStorage for userType
2. If missing → Redirect to Login
3. If present → Allow access to respective dashboard

On Logout:
1. Clear sessionStorage
2. Redirect to Login (/)
```
