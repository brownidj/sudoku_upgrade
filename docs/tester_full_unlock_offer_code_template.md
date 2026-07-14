# Tester Full Unlock Message Template (App Store Offer Codes)

Use this template to grant Full Version access to selected testers after release.

## Admin checklist

1. In App Store Connect, create an **Offer Code** for the `full_unlock` non-consumable IAP.
2. Generate one-time codes (one per tester).
3. Fill in each tester’s unique code and redemption URL.
4. Send the message below.
5. Track redemption status.

---

## Message template

Subject: Your Full Version Unlock Code

Hi {{tester_name}},

Thanks again for helping test **{{app_name}}**.

As promised, here is your free **Full Version** unlock code:

- Code: `{{offer_code}}`
- Redemption link: {{redemption_url}}
- Expiry date: {{expiry_date}}

### How to redeem

1. Open the redemption link above (or redeem the code in the App Store).
2. Complete redemption with your Apple ID.
3. Open **{{app_name}}**.
4. If Full Version does not appear immediately, go to:
   - App menu → **Restore Purchases**

After redemption, Full Version should stay tied to your Apple ID like a normal purchase.

Thanks again,
{{your_name}}

---

## Optional quick follow-up template

Hi {{tester_name}} — just checking whether your Full Version code redeemed successfully.  
If it didn’t unlock right away, please open the app and use **Restore Purchases**.
