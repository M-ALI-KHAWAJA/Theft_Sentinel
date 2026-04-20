# Troubleshooting: Guard Pages Showing Nothing

## Issue
When clicking "My Incidents" or "Feedback" in Guard role, the pages navigate correctly but appear to show nothing.

---

## ✅ What's Actually Happening

The pages **ARE loading correctly**! Here's what's likely happening:

### Option 1: Empty State (Most Likely) ✅
- The pages are working fine
- They're just showing **empty states** because there's no data yet
- You need to create/assign some incidents to the guard first

### Option 2: API Errors (Check Browser Console)
- Backend might not support the query parameters
- Authentication issues
- Backend endpoint doesn't exist yet

---

## 🔍 How to Diagnose

### Step 1: Open Browser DevTools
```
Press F12 or Right-click → Inspect
```

### Step 2: Check Console Tab
Look for:
- ✅ **No errors** = Pages working, just no data
- ❌ **401 Unauthorized** = Login/auth issue
- ❌ **404 Not Found** = Backend endpoint missing
- ❌ **400 Bad Request** = Parameter issue

### Step 3: Check Network Tab
1. Navigate to `/incidents/my`
2. Look for request to `/api/incidents/?my_incidents=true`
3. Check the response:
   - Status 200 with empty `[]` = Working, no data
   - Status 404 = Backend doesn't support this query param
   - Status 401 = Not authenticated
   - Status 500 = Backend error

---

## 🔧 Solutions

### Solution 1: Verify You're Logged In as Guard

1. Check browser console for user role:
```javascript
// In browser console, type:
localStorage.getItem('access_token')
// Should show a token

// Check user data:
JSON.parse(localStorage.getItem('user'))
// Should show role: "GUARD"
```

2. If not logged in or wrong role:
   - Logout
   - Login with a Guard account
   - Try again

---

### Solution 2: Create Test Data

The pages need data to display. Create some test data:

#### For "My Incidents":
1. Login as **Admin** or **Security Incharge**
2. Create an alert (or let the system create one)
3. Create an incident from the alert
4. **Assign the incident to your Guard user**
5. Logout and login as Guard
6. Navigate to "My Incidents" - should now show the assigned incident

#### For "My Feedback":
1. Login as **Guard**
2. Navigate to "Feedback" → "Create New Feedback"
3. Submit some feedback
4. Navigate to "My Feedback" - should now show your feedback

---

### Solution 3: Backend Doesn't Support Query Params

If backend doesn't support `my_incidents=true`, we need to modify the component to get all incidents and filter client-side:

<function_calls>
<invoke name="write">
<parameter name="contents"># Alternative Implementation (if backend doesn't support query params)

## For MyIncidents.jsx

If the backend returns 404 or doesn't filter by `my_incidents=true`, modify the component:

```javascript
const fetchMyIncidents = async () => {
  setLoading(true);
  try {
    // Get all incidents
    const response = await listIncidents();
    
    // Get current user ID from auth state or localStorage
    const currentUserId = user?.id; // from Recoil state
    // OR: const userData = JSON.parse(localStorage.getItem('user'));
    // const currentUserId = userData?.id;
    
    // Filter to only show incidents assigned to current user
    const myIncidents = response.data.filter(
      incident => incident.assigned_to === currentUserId
    );
    
    setIncidents(myIncidents);
  } catch (error) {
    console.error('Error fetching my incidents:', error);
    toast.error('Failed to load your incidents');
  } finally {
    setLoading(false);
  }
};
```

## For MyFeedback.jsx

If backend doesn't filter feedback by current user:

```javascript
const fetchMyFeedback = async () => {
  setLoading(true);
  try {
    // Get all feedback
    const response = await listFeedback();
    
    // Get current user ID
    const currentUserId = user?.id;
    
    // Filter to only show feedback created by current user
    const myFeedback = response.data.filter(
      feedback => feedback.user === currentUserId || feedback.created_by === currentUserId
    );
    
    setFeedback(myFeedback);
  } catch (error) {
    console.error('Error fetching my feedback:', error);
    toast.error('Failed to load your feedback');
  } finally {
    setLoading(false);
  }
};
```


