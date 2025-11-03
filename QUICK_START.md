# Quick Start Guide - DB Guard UI

## Application Structure

```
Login Page (/)
    ├── DBA Login (PIN: 1234)
    │   └── DBA Dashboard (/dba-dashboard)
    │       ├── View all metrics & charts
    │       ├── View all clients
    │       ├── View logs
    │       └── Click client → Client Details (/client/:id)
    │
    └── Client Login (Any Client ID)
        └── Client Dashboard (/client-dashboard)
            └── Query Console Only
```

## Key Features Implemented

### ✅ Login System

- **DBA Access**: PIN-based authentication (PIN: 1234)
- **Client Access**: Client ID-based authentication
- Session management with `sessionStorage`

### ✅ DBA Dashboard

- **Metrics Cards**: Total Queries, Slow Queries, Avg Time, Active Clients
- **Charts**:
  - Query Execution Timeline (scatter plot)
  - Client Activity (bar chart)
  - Query Type Distribution (pie chart)
- **Data Sections**:
  - Recent Alerts
  - All Queries preview
  - Clients grid (clickable cards)
  - Activity Logs table
- **Navigation**: Can access any client's detailed information

### ✅ Client Dashboard

- **Console**: SQL query input with execution
- **Output**: Terminal-style output display
- **Sidebar**:
  - Alerts section
  - Query Details (Status, Time, Rows, Root Causes)
  - Query History (last 10 queries)
- **Restricted Access**: Only console, no admin features

### ✅ Client Details Page

- Detailed view of individual client
- Query history with root cause analysis
- Back button to DBA Dashboard

## Component Locations

```
src/
├── components/
│   ├── Login.jsx              (NEW - Login page)
│   ├── DBADashboard.jsx       (NEW - DBA admin view)
│   ├── ClientDashboard.jsx    (NEW - Client console view)
│   └── ClientDetails.jsx      (MODIFIED - Added back button)
│
└── styles/
    ├── Login.css              (NEW)
    ├── DBADashboard.css       (NEW)
    ├── ClientDashboard.css    (NEW)
    └── ClientDetails.css      (MODIFIED)
```

## Testing Steps

1. **Navigate to localhost:3000**

   - You should see the login page

2. **Test DBA Flow**:

   ```
   1. Click "DBA Login" button
   2. Enter PIN: 1234
   3. Click "Login"
   4. → Should redirect to /dba-dashboard
   5. Click on any client number
   6. → Should show client details
   7. Click "Back to Dashboard"
   8. → Should return to DBA dashboard
   ```

3. **Test Client Flow**:
   ```
   1. Go back to homepage (logout)
   2. Click "Client Login" button
   3. Enter any Client ID (e.g., "1")
   4. Click "Login"
   5. → Should redirect to /client-dashboard
   6. → Should only see console, not admin features
   7. Try executing a query (if backend is running)
   ```

## Backend Requirements

The frontend expects these API endpoints:

| Endpoint                | Method | Purpose                          |
| ----------------------- | ------ | -------------------------------- |
| `/api/dashboard`        | GET    | Get metrics, charts data, alerts |
| `/api/logs`             | GET    | Get activity logs                |
| `/api/all_queries`      | GET    | Get all queries from all clients |
| `/api/connect`          | POST   | Connect client to server         |
| `/api/execute_query`    | POST   | Execute SQL query                |
| `/api/client/:clientId` | GET    | Get specific client details      |

## Customization

### Change DBA PIN

**File**: `src/components/Login.jsx`

```javascript
const DBA_PIN = "1234"; // Change this to your desired PIN
```

### Adjust Colors

**Files**: All CSS files in `src/styles/`

- Primary: `#0a0a0a`, `#1a1a1a`, `#2a2a2a`
- Accents: `#26c6da` (cyan), `#ef5350` (red), `#42a5f5` (blue)

### Modify Metrics

**File**: `src/components/DBADashboard.jsx`

- Update state variables for additional metrics
- Modify fetch calls to include new data

## Design Highlights

### Login Page

- Clean, centered card design
- Tab-style toggle between DBA/Client
- Dark theme with subtle gradients
- Responsive on all devices

### DBA Dashboard

- Professional metrics grid layout
- Interactive Plotly charts
- Color-coded slow query indicators
- Scrollable logs table
- Clickable client cards

### Client Dashboard

- Terminal-style console output
- Green text on black background (classic console look)
- Real-time query execution
- Sidebar with query details
- History tracking

### Client Details

- Comprehensive query analysis
- Root cause breakdown
- Alert banners
- Clean tabular data presentation

## Browser Compatibility

- Chrome ✅
- Firefox ✅
- Safari ✅
- Edge ✅

## Mobile Responsive

- ✅ All layouts adjust for mobile
- ✅ Charts resize dynamically
- ✅ Tables scroll horizontally
- ✅ Touch-friendly buttons

## Notes

- No changes made to backend as requested
- All styling is modern and matches screenshots
- Uses React Router for navigation
- Session-based authentication (not production-ready)
- All original functionality preserved
