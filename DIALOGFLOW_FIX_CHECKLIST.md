# Dialogflow CX Session Continuity & Phone Number Extraction - Fix Checklist

## ✅ Fixed in Code

### 1. **Response Extraction (chat.py)**
   - Added defensive checks for `msg.text` object existence
   - Now validates that both `msg.text` exists AND `msg.text.text` has content
   - Prevents crashes from empty response_messages

### 2. **Session Continuity Logging (chat.py)**
   - Added explicit logging for session_id tracking
   - Log messages: `NEW_SESSION`, `EXISTING_SESSION`, `CHAT_REQUEST`, `CHAT_RESPONSE`
   - Helps debug if session_id is changing between turns
   - **Frontend responsibility**: Must store and re-send same session_id across turns

### 3. **Phone Number Fallback Extraction (webhook.py)**
   - Primary: Extracts `phone` from session_params (Dialogflow sets this)
   - Fallback 1: Searches `fulfillmentInfo.fulfillment_response` parameters
   - Fallback 2: Scans all parameters for "phone" key
   - More resilient to different Dialogflow response structures

---

## 🔧 What You MUST Configure in Dialogflow CX Console

### **Issue 1: Session Parameters Not Being Set**
Dialogflow CX must send phone number as a **session parameter** for webhooks to access it.

**Steps to Configure:**
1. Open your Dialogflow CX agent in console
2. Go to the page where you collect the phone number
3. In the **Phone Number Route** or **Page Transition**, find where the `@sys.phone-number` entity is matched
4. Add a **"Set page parameters"** or **"Session parameters"** action:
   - Parameter name: `phone`
   - Parameter value: `$sys.phone-number` (or the actual parameter name from your entity extraction)
5. Save the flow

**Verification:**
- Run a test conversation in Dialogflow console
- Check logs: You should see "SESSION_PARAMS" with `phone` included
- Example: `SESSION_PARAMS: {"phone": "+919000000001"}`

### **Issue 2: Phone Number Entity Not Being Extracted**
If `@sys.phone-number` entity isn't being recognized:

**Steps to Check:**
1. Go to the page where phone is collected
2. Check the **Fulfillment** or **Route** that matches the phone input
3. Ensure the entity reference is correct: `@sys.phone-number` or `projects/.../entities/sys.phone-number`
4. Test intent matching:
   - Go to **Test Agent** tab
   - Type "+ 91 9000000001" or similar phone formats
   - Check if it shows as recognized in the intent output
5. If not recognized, you may need to:
   - Enable the `@sys.phone-number` system entity in Agent settings
   - Or add a custom entity with regex: `^\+?[1-9]\d{1,14}$`

---

## 🧪 Testing Checklist

### Frontend Testing:
- [ ] Send first message WITHOUT session_id → Backend should return NEW session_id
- [ ] Send second message WITH returned session_id → Backend logs should show EXISTING_SESSION
- [ ] Verify logs show same session_id across turns (enables Dialogflow context)

### Backend Logging:
```bash
# In API logs, you should see:
# NEW_SESSION: 123e4567-e89b-12d3-a456-426614174000
# EXISTING_SESSION: 123e4567-e89b-12d3-a456-426614174000
# CHAT_REQUEST session_id=... message=what is my plan
# CHAT_RESPONSE session_id=... replies=['Your plan is...']
```

### Webhook Testing:
- [ ] Send: "My phone is +919000000001"
- [ ] Check webhook logs for: `EXTRACTED tag=... phone=+919000000001`
- [ ] If phone is empty in logs, Dialogflow CX isn't setting session params → Fix in console

### End-to-End Flow:
1. Start chat (no session_id)
2. Say: "What is my current plan?"
3. Dialogflow asks: "Please share your mobile number"
4. Say: "+919000000001"
5. Dialogflow should remember and fetch your plan automatically
6. Check logs: Session should be SAME across all 4 turns

---

## 🐛 Debugging Commands

### Check phone extraction:
```python
# In webhook logs, look for:
# EXTRACTED tag=check-plan phone=+919000000001
# If phone is empty: Dialogflow isn't sending it in session params
```

### Check session consistency:
```bash
# Run this in logs:
grep "EXISTING_SESSION" api.log
# Should show same session_id for multiple chat turns
```

### Check response extraction:
```python
# The code now logs:
# CHAT_RESPONSE replies=['Your plan is... ']
# If replies is empty, Dialogflow isn't returning text messages
```

---

## 📝 Summary of Code Changes

| File | Change | Impact |
|------|--------|--------|
| `api/routes/chat.py` | Added logging + response extraction validation | Session tracking + prevent empty replies |
| `api/routes/webhook.py` | Added phone extraction fallbacks | More resilient parameter extraction |

---

## 🚀 Next Steps

1. **Test session persistence**: Send messages with/without session_id to verify logging
2. **Configure Dialogflow CX**: Set session parameters for phone number in the page flow
3. **Monitor logs**: Watch for `SESSION_PARAMS` to include `phone` key
4. **Verify end-to-end**: Run a complete conversation and check all three issues are resolved

