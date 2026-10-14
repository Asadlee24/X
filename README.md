# 🛑 X (Twitter) Premium Gift Automation — [PROJECT ENDED]

> [!WARNING]
> ### 📢 Official Notice: Project Discontinued & Service Ceased
> **Service Status:** Permanently Closed / Taken Offline  
> **Effective Date:** October 13, 2026  
> 
> On **October 13, 2026**, X (formerly Twitter) launched a unified subscription platform ("The X Subscription") across Grok, Cursor, and X Premium. As part of this major infrastructure update, X has **permanently decommissioned and retired the legacy Premium Gifting GraphQL API** and its associated regional Stripe product SKUs.
> 
> As a result, automated checkout generation and third-party gifting workflows can no longer be fulfilled by the X platform. This repository is now **archived for historical, educational, and reference purposes only**.

---

## 📋 About This Project (Archive Overview)

**XGift / X Premium Bot** was an automated gifting and redemption infrastructure designed to streamline the delivery of X (Twitter) Premium subscriptions. It featured:

* **Telegram Admin Bot**: High-speed command interface for validating Twitter usernames, checking eligibility, and generating official Stripe checkout sessions.
* **Regional Pricing Engine**: Seamless gateway routing to support regional discount catalogs (e.g., 3-month and 6-month gift packages).
* **Guarded Redemption Vault**: AES-256-GCM encrypted credential vault for session tokens, proxy endpoints, and billing records.
* **Stripe Webhook & Session Reconciler**: Automatic status tracking (unpaid, open, paid) and subscription activation verification.

---

## 🏛️ System Architecture (Reference)

```
[ Customer / Admin ]
        │
        ▼
[ Telegram Bot Gateway ]
        │
        ├──> [ Twitter Recipient Lookup ] (kn8hCE6bHstQV2MtfYDTKg / PremiumGiftingQuery)
        │
        ├──> [ Regional Residential Gateway ] (Regional egress routing)
        │
        ▼
[ X API Mutation Engine ] (GqTVJ4S1526tLkxj69xIZw / useOneTimePurchaseGiftMutation)
        │
        ▼
[ Official Stripe Checkout Session ] (cs_live_...)
        │
        ▼
[ Real-Time Payment & Fulfillment ]
```

---

## ⚠️ Reason for Discontinuation

1. **API Retirement:** The mutation endpoint `useOneTimePurchaseGiftMutation` and product identifiers (`prod_TJXJtpzqCpI36N`, `prod_THiwpmlazw8gtM`, etc.) were deactivated server-side by X on October 13, 2026.
2. **Unified Subscription Architecture:** X migrated to account-level direct recurring subscriptions, ending third-party one-time gifting mutations.
3. **Upstream Service Deprecation:** The upstream project and live service endpoints (`xp.kfcv50.today`) were officially taken offline following X's platform update.

---

## 🔒 Security & Privacy Notice

* All active sessions, authentication tokens (`auth_token`, `ct0`), and residential proxies have been completely terminated and wiped.
* All cloud runner workflows and GitHub repository secrets have been revoked and deleted.
* No live credentials or personal customer data remain within this repository.

---

## 📜 License

This project was developed for educational and research purposes under the [MIT License](LICENSE).
