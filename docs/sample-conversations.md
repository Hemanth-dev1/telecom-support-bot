# Sample Conversations

Real transcripts from Dialogflow CX simulator.

## 1. Check plan
User: What plan am I on?
Bot:  Please share your registered mobile number so I can look up your account.
User: +919000000001
Bot:  Your current plan is Unlimited Pro. It renews on 2026-05-21. Status: active.

## 2. Check data usage
User: How much data do I have left?
Bot:  Please share your registered mobile number so I can look up your account.
User: +919000000002
Bot:  Data usage for Rahul Verma:
      Used: 4.1 GB of 20 GB (20%)
      Remaining: 15.9 GB
      Resets on: 2026-04-01

## 3. Renew plan
User: Renew my plan
Bot:  Please share your registered mobile number so I can look up your account.
User: +919000000001
Bot:  I will renew your current plan for one month. Confirm? (yes / no)
User: yes
Bot:  Done! Your Unlimited Pro plan is renewed until 2026-05-24.

## 4. Upgrade plan
User: Upgrade my plan
Bot:  Which plan would you like? Basic Plan, Unlimited Pro, or Family Pack.
User: Family Pack
Bot:  Upgraded to Family Pack! You now have 150GB at Rs.999/month.

## 5. Policy question (RAG — Vertex AI Search + Gemini)
User: What is the refund policy?
Bot:  If you cancel a 30-day plan that costs Rs.599 on day 10, your refund
      would be Rs.399 (20/30 x 599). Non-refundable items include add-on data
      packs, international roaming charges, and plans renewed within 48 hours
      of their renewal date.
