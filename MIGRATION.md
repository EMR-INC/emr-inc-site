# Moving emr-inc.net off Wix

The site, DNS and registration all move to Vercel. Gmail (Google Workspace)
keeps running the whole time. This file records what was done and what's left.

## Starting point (2026-09-25)

| | Before |
|---|---|
| Site | Wix, Premium plan, served from `185.230.63.x` |
| DNS | Wix (`ns2.wixdns.net`, `ns3.wixdns.net`) |
| Registrar | Wix |
| DNSSEC | On, at Wix |
| Email | Google Workspace: 5 MX records plus an SPF TXT record |
| Other | `command-center.emr-inc.net` points to a Lovable app. `en.emr-inc.net` is a Wix language subdomain. |

`dns/emr-inc.net.cloudflare.zone` is an exact copy of that Wix zone. It's kept
as the reference for every record that has to survive the move. (It was first
written for a Cloudflare import, and the plan changed to Vercel afterwards.)

Wix does not let you change the nameservers on a domain it registered. The only
way to move DNS off Wix is to transfer the registration. That's why the order
below matters.

## Steps

1. ✅ **Site on Vercel.** Project `emr-inc-site`, deployed from this repo.
   Framework: Other, no build step.
2. ✅ **Point the site while DNS is still at Wix.** In the Wix DNS editor:
   - the apex `A` record now points to `76.76.21.21`
   - `www` is a `CNAME` to `cname.vercel-dns.com`
   - MX and TXT were left alone

   `emr-inc.net` and `www.emr-inc.net` are added to the Vercel project, and
   `www` redirects to the apex.
3. ✅ **DNSSEC off at Wix.** Domains → ⋯ → Edit contact info → Privacy and
   DNSSEC protection → Show more → Turn off protection.
4. ✅ **Records pre-loaded in Vercel DNS.**
   - 5 Google MX records
   - SPF and Google site-verification TXT records
   - `command-center` A record and `_lovable.command-center` TXT record

   All checked against `ns1.vercel-dns.com`. Vercel adds the apex and `www`
   records itself, because the domain is attached to the project.
5. ⏳ **Registrar transfer, Wix → Vercel.**
   - At Wix, choose **Transfer away from Wix** to get the auth code.
   - In Vercel, go to **Domains → Transfer In**.
   - Approve the confirmation email. The transfer takes up to 5 days, and
     approving Wix's release email makes it faster.
6. ☐ **After the transfer completes:**
   - Confirm the domain uses Vercel's nameservers.
   - Confirm the apex, `www`, the MX records and `command-center` all resolve.
   - Send a test email.
7. ☐ **Cancel Wix Premium.** Only after step 6. Before cancelling, export
   anything you need from Wix Forms, Bookings and Invoices.

## Still to do on the site

- `open-data.html` and `call-sign.html` are linked from the nav and footer but
  don't exist yet.
- Workspace has SPF but no DKIM or DMARC.
  - **DKIM:** Google Admin → Gmail → Authenticate email. Add the
    `google._domainkey` TXT record in Vercel DNS.
  - **DMARC:** start with `_dmarc TXT "v=DMARC1; p=none; rua=mailto:<you>"`.

## If something goes wrong

- **Email stopped after the transfer:** check the 5 MX records under Vercel →
  Domains → emr-inc.net → DNS Records, then compare them against
  `dns/emr-inc.net.cloudflare.zone`.
- **Site down:** check that both domains show as valid under the project's
  **Settings → Domains**.
