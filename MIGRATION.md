# Moving emr-inc.net off Wix

This moves the site to Vercel, DNS to Cloudflare, and then the domain registration
to Cloudflare. Gmail keeps running the whole time.

## Where things stand (checked 2026-09-25)

| | Today |
|---|---|
| Site | Wix, Premium plan, served from `185.230.63.x` |
| DNS | Wix (`ns2.wixdns.net`, `ns3.wixdns.net`) |
| Registrar | Almost certainly Wix. Wix hosts the zone and has DNSSEC on, and the domain is not set up in Wix as an outside ("connected") domain. To confirm, open Wix > Domains: a **Transfer away from Wix** option means Wix is the registrar. |
| DNSSEC | **On**, at Wix (key tag 38644) |
| Email | Google Workspace: 5 MX records plus an SPF TXT record |
| Other | `command-center.emr-inc.net` points to a Lovable app. `en.emr-inc.net` is a Wix language subdomain. |

`dns/emr-inc.net.cloudflare.zone` is an exact copy of the Wix zone.

The steps below come in an order that matters. Two of them will take the domain
offline, email included, if you do them out of order. Both are marked ⚠.

---

## Phase 1: Get the new site live on Vercel (no DNS changes)

1. In Vercel, **Add New > Project** and import `emergency-medical-resolutions/emr-inc-site`.
   Framework preset: **Other**. Leave the build command and output directory empty.
   It's a static site, and `vercel.json` handles clean URLs.
2. Open the `*.vercel.app` URL and click through every page.
3. **Before cutover, fix the missing pages.** The nav links to `call-sign.html`,
   `contact.html` and `open-data.html`, and none of them exist yet, so each one is a 404.
4. Make a list of the current Wix page URLs (for example `/about` and `/contact`).
   Any that are indexed or shared need a redirect in `vercel.json` so the old links
   keep working.
5. Before you cancel Wix, export anything stored in Wix apps. **Forms** submissions,
   **Bookings** and **Invoices** stay behind when you leave.

## Phase 2: Move DNS to Cloudflare (site stays on Wix; email untouched)

6. Create a free Cloudflare account, choose **Add a domain**, enter `emr-inc.net`, and pick the Free plan.
7. Cloudflare scans for records and will miss some. Delete whatever it found, then go to
   **DNS > Records > Import and Export** and import `dns/emr-inc.net.cloudflare.zone`.
   **Clear "Proxy imported records"**, because every record must be grey-cloud (DNS only).
8. Compare the Cloudflare record list with the zone file line by line: 5 MX records,
   2 root TXT records, 3 A records, the www CNAME, the en CNAME, and the two command-center records.
9. ⚠ **Turn DNSSEC off at Wix first.** Go to Wix > Domains > emr-inc.net > Advanced > DNSSEC and turn it off.
   Then wait at least **24 hours**. If the nameservers change while DNSSEC is on,
   resolvers reject every answer Cloudflare gives, and the site and **all email** go
   dark until the fix propagates.
   To check it's cleared, enter `emr-inc.net` at <https://dnsviz.net> or
   <https://dnschecker.org/ds-record-lookup.php>. The DS record should be gone.
10. At Wix > Domains > emr-inc.net > **Change nameservers**, enter the two
    `*.ns.cloudflare.com` nameservers that Cloudflare assigned to the domain.
11. Wait for Cloudflare to show the zone as **Active**. That usually takes minutes, and can take up to 24 hours.
12. Test: send an email to and from an @emr-inc.net address, and load the site, which is still on Wix.

## Phase 3: Point the site at Vercel

13. In the Vercel project, open **Settings > Domains** and add `emr-inc.net` and `www.emr-inc.net`.
    Make one of them the primary and have the other redirect to it.
14. In Cloudflare DNS, replace **only** the website records, using the values Vercel shows.
    Vercel's defaults are listed below, but use Vercel's values if they differ:
    - Delete the three `@` A records that point to `185.230.63.x`. Add `@ A 76.76.21.21`.
    - Change `www` to `CNAME cname.vercel-dns.com`.
    - Delete the `en` CNAME. It only existed for Wix.
    - Keep them grey-cloud (DNS only) so Vercel can issue the SSL certificate.
    - **Leave the MX, TXT and command-center records alone.**
15. Wait for Vercel to show both domains as valid and issue the certificate. Then load
    `https://emr-inc.net` and `https://www.emr-inc.net`.
16. In Cloudflare, go to **DNS > Settings > DNSSEC** and **Enable**. Cloudflare then shows a DS record.
    Add it at the registrar: at Wix for now, and it's automatic once the domain moves in phase 4.

## Phase 4: Move the registration to Cloudflare Registrar

17. At Wix > Domains: turn off auto-renew, **unlock the domain** (disable transfer lock),
    and request the **authorization (EPP) code**.
    Make sure the domain contact email reaches you, because the transfer approval goes there.
18. In Cloudflare, go to **Domain Registration > Transfer Domains**, select emr-inc.net,
    enter the code, and pay for one year. Cloudflare charges the wholesale price, and the year is added to your current expiry date.
19. Approve the transfer email. Transfers take up to 5 days, and Wix can release it sooner.
    DNS doesn't change during the transfer, because it's already on Cloudflare.
20. ⚠ **Cancel the Wix Premium plan only after the transfer shows as complete.**
    If the domain was bundled free with the plan, cancelling early can put it at risk.

---

## Recommended while you're in there (optional)

Google Workspace currently has SPF but no **DKIM** or **DMARC**, so mail from
@emr-inc.net is more likely to land in spam. Once the domain is on Cloudflare:

- DKIM: Google Admin > Apps > Google Workspace > Gmail > **Authenticate email**. Generate the key
  and add the `google._domainkey` TXT record it gives you, then click **Start authentication**.
- DMARC: add `_dmarc TXT "v=DMARC1; p=none; rua=mailto:<your address>"`. After a few
  weeks of clean reports, tighten it to `p=quarantine`.

## If something goes wrong

- **Email stopped:** In Cloudflare, check that the 5 MX records are there and grey-cloud.
  If the problem started right after the nameserver change, check whether a DS record is still published (step 9).
- **Site down after phase 3:** Put the three Wix A records and the `www → cdn3.wixdns.net`
  CNAME back. That rolls the site back to Wix while it's still paid for.
