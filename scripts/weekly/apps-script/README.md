# Field Notes sender

Google Apps Script, bound to the **EMR Contact CRM** sheet
(`1AXD1l_d2LNnsSjDNyqcvgb8-0scMnQT6jbSIe7UVSRs`).

## Why Apps Script and not the Gmail API

The Gmail API path strips every `<img>` tag out of the HTML it sends. Three test
sends confirmed it: reading each message back showed the element absent from the
stored body, not merely unloaded, with a CID attachment, with a GitHub raw URL,
and with the figure served from emr-inc.net. The same sanitizer drops
`role="presentation"` and `opacity:0`, and rewrites `href="#"` to
`javascript:void(0)`.

`MailApp` does not sanitize. The email arrives as built.

## Setup

1. Open the CRM sheet, Extensions, Apps Script. Paste `Code.gs`.
2. Run `setup()` once. It creates the log and unsubscribe sheets and generates
   the HMAC secret used to sign unsubscribe links.
3. Deploy, New deployment, Web app. Execute as **me**, access **anyone**. Copy
   the url into `CONFIG.WEBAPP_URL`. This is what the unsubscribe link hits.
4. Upload `01-email.html` and `01-email.txt` to Drive, put their file ids into
   `CONFIG.HTML_FILE_ID` and `CONFIG.TEXT_FILE_ID`. They live in Drive rather
   than the repo because the site root is public.
5. Fill `POSTAL_ADDRESS` and `REPLY_TO`.
6. Run `sendTestToSelf()`. Confirm the figure renders and the unsubscribe link
   works.
7. Run `sendIssue()` with `DRY_RUN: true`, read the log sheet, then flip it.

## What it refuses to do

`assertSendable_()` throws rather than send when any of these is missing:

- `POSTAL_ADDRESS`. CAN-SPAM, 15 USC 7704(a)(5), requires a valid physical
  postal address in every commercial message.
- `WEBAPP_URL`, or the `{{UNSUBSCRIBE_URL}}` placeholder in either part. Without
  both, recipients have no way out.
- `REPLY_TO`. A bulk send needs a monitored reply address.
- The scope guard. If "Florida only" and "not a national record" are not both in
  the HTML, the email states a Florida finding with nothing marking it as one.

It also dedupes on lowercased email, skips malformed addresses, skips anyone on
the unsubscribe sheet, and skips anyone already logged `sent` **for this issue**,
so a re-run after a failure resumes rather than double sending.

## Dry run against the real sheet, 2026-10-05

127 deliverable contacts out of 128 rows. No blanks, no malformed addresses, no
duplicates. One exclusion, covered below.

| Source | Count | Line they get |
| --- | --- | --- |
| `Off-Road Transport Survey` | 105 | took part in the off road transport survey |
| `MyLEADS Mobile` | 21 | we met at EMS World Expo |
| `Contact form` | 1 | contacted EMR Inc. through our website |

**The EMS World cohort carries Source `MyLEADS Mobile`**, the badge scanner used
at the booth, not the string "EMS World". That is why the map is filled from a
dry run rather than from a guess.

Row 102 to 128 is close but not exact: that range holds 20 MyLEADS rows, 5 survey
rows and 1 contact form row, and a 21st MyLEADS row sits at 129. Source is the
reliable discriminator, not the row number.

## The list is more than one cohort A single hardcoded "why you are getting this"
sentence would therefore be a false statement to one group or the other, so the
line is per recipient: `{{WHY_YOU_GET_THIS}}` is filled from the CRM `Source`
column through the `PROVENANCE` map in `CONFIG`.

Matching is a case insensitive substring test, so `EMS World`, `EMS World Expo
2026` and `ems world expo booth scan` all resolve to the same line. Anything
unmatched falls back to `PROVENANCE_DEFAULT` rather than failing the send.

The first dry run logs every distinct `Source` value it saw with a count, and
names any that fell through to the default. Fill `PROVENANCE` from that output
rather than from a guess about what the cells contain.

## One contact is excluded outright

Row 107 came through the contact form with Consent reading
**"Not given (box not checked)"**. That is an explicit refusal, so
`consentRefused_()` drops them before anything else is considered. "Not recorded"
is treated differently: it means the question was never asked, which is not the
same as a no.

Of 128 rows, exactly **one** reads "Yes".

## The consent problem, which is not a code problem

Column Q of every row in `Contacts` reads **"Not recorded (survey did not ask)"**.

The survey cohort gave an address to answer questions about stretchers in
September 2025. None of them asked for a newsletter. The EMS World rows are a
different and generally stronger basis, since handing over a badge at a booth is
a deliberate act, but check how that consent was captured before leaning on it.

US CAN-SPAM does not require prior consent, so a send with a working unsubscribe
and a postal address is lawful. That is a floor, not a judgment. The footer says
plainly why they are receiving it, which is the least that is owed and is also
what keeps spam complaints down. Anyone on the list outside the US, or any future
contact from a jurisdiction with an opt in rule, is a different question and this
script does not answer it.

`docs/limits.md` in the design repo requires a human who knows the category to
approve anything external before it ships. This script does not clear anything.

## Quota

`MailApp` allows 1,500 recipients a day on Workspace and 100 on a consumer
account. `MAX_PER_RUN` defaults to 90 so a consumer account cannot overrun, and
the script also reads `MailApp.getRemainingDailyQuota()` and takes the lower of
the two.
