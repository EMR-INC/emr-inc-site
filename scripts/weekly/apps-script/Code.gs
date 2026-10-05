/**
 * Field Notes sender. Google Apps Script, bound to the EMR Contact CRM sheet.
 *
 * Why this exists: the Gmail API path strips every <img> tag out of the HTML it
 * sends, so the figure never reaches the inbox. MailApp does not sanitise, so
 * the email arrives as built.
 *
 * It refuses to send until the things that make a bulk send lawful and honest
 * are actually in place. See assertSendable_(). That is deliberate: this list
 * was collected from a stretcher survey and column Q of every row reads
 * "Not recorded (survey did not ask)". Nobody on it asked for a newsletter.
 *
 * First run: setup(). Then sendIssue() with DRY_RUN true and read the log.
 */

// ---------------------------------------------------------------- config ---

var CONFIG = {
  ISSUE_ID:      'issue-01',
  SUBJECT:       'Your engine has a better file than your firefighters',

  // The built email. Kept in Drive, not in the public repo: the site root is
  // served by GitHub Pages, so anything committed there is world readable.
  HTML_FILE_ID:  '',          // Drive file id of 01-email.html
  TEXT_FILE_ID:  '',          // Drive file id of 01-email.txt

  CONTACTS_SHEET: 'Contacts',
  EMAIL_HEADER:   'Email',
  SOURCE_HEADER:  'Source',

  // Why each recipient is getting this, keyed by the CRM Source column. The list
  // is not one cohort: rows 102 to 128 are EMS World attendees and the rest came
  // from the off road stretcher survey, so a single hardcoded sentence would be
  // a false statement to one group or the other.
  //
  // Keys are matched case insensitively as substrings of the Source cell. The
  // first dry run logs every distinct Source it saw with a count, so fill this in
  // from that rather than from a guess.
  PROVENANCE: {
    'off-road transport survey':
      'You are receiving this because you took part in the EMR Inc. off road transport survey.',
    'ems world':
      'You are receiving this because we met at EMS World Expo.'
  },
  PROVENANCE_DEFAULT:
    'You are receiving this because you are on the EMR Inc. contact list.',

  SENDER_NAME:    'EMR Inc. Field Notes',
  REPLY_TO:       '',         // a mailbox a person actually reads

  // CAN-SPAM 15 USC 7704(a)(5): a commercial message must carry a valid
  // physical postal address. There is no lawful send without this.
  POSTAL_ADDRESS: '',         // e.g. 'EMR Inc., 1234 Example Blvd, Lakewood Ranch, FL 34202'

  // Deployed web app url of this script, which is what the unsubscribe link
  // points at. Fill it after the first Deploy.
  WEBAPP_URL:     '',

  DRY_RUN:        true,       // writes the log, sends nothing
  MAX_PER_RUN:    90,         // Workspace allows 1500 a day, consumer 100
  THROTTLE_MS:    1200
};

var LOG_SHEET = 'Field Notes Log';
var UNSUB_SHEET = 'Field Notes Unsubscribed';

// ----------------------------------------------------------------- setup ---

function setup() {
  var ss = SpreadsheetApp.getActive();
  ensureSheet_(ss, LOG_SHEET, ['Timestamp', 'Issue', 'Email', 'Status', 'Source']);
  ensureSheet_(ss, UNSUB_SHEET, ['Email', 'Timestamp', 'Source']);

  var props = PropertiesService.getScriptProperties();
  if (!props.getProperty('UNSUB_SECRET')) {
    props.setProperty('UNSUB_SECRET', Utilities.getUuid() + Utilities.getUuid());
  }
  Logger.log('Sheets ready. Unsubscribe secret set. Fill CONFIG, deploy as a web '
           + 'app (execute as me, access anyone), then paste the url into WEBAPP_URL.');
}

function ensureSheet_(ss, name, headers) {
  var sh = ss.getSheetByName(name);
  if (!sh) {
    sh = ss.insertSheet(name);
    sh.appendRow(headers);
    sh.setFrozenRows(1);
  }
  return sh;
}

// ------------------------------------------------------------ fail closed ---

/**
 * Everything that must be true before a single message goes out. Each check is
 * here because its absence is a real problem, not a style preference.
 */
function assertSendable_(html, text) {
  var problems = [];

  if (!CONFIG.POSTAL_ADDRESS) {
    problems.push('POSTAL_ADDRESS is empty. CAN-SPAM requires a valid physical '
                + 'postal address in every commercial message.');
  }
  if (!CONFIG.WEBAPP_URL) {
    problems.push('WEBAPP_URL is empty, so the unsubscribe link has nowhere to go. '
                + 'Deploy this script as a web app first.');
  }
  if (!CONFIG.REPLY_TO) {
    problems.push('REPLY_TO is empty. A bulk send needs a monitored reply address.');
  }
  if (!CONFIG.HTML_FILE_ID || !CONFIG.TEXT_FILE_ID) {
    problems.push('HTML_FILE_ID or TEXT_FILE_ID is empty.');
  }
  if (html.indexOf('{{UNSUBSCRIBE_URL}}') === -1) {
    problems.push('The HTML has no {{UNSUBSCRIBE_URL}} placeholder, so recipients '
                + 'would get no way out.');
  }
  if (html.indexOf('{{POSTAL_ADDRESS}}') === -1) {
    problems.push('The HTML has no {{POSTAL_ADDRESS}} placeholder.');
  }
  if (html.indexOf('{{WHY_YOU_GET_THIS}}') === -1
      || text.indexOf('{{WHY_YOU_GET_THIS}}') === -1) {
    problems.push('Both parts need a {{WHY_YOU_GET_THIS}} placeholder. The list is '
                + 'more than one cohort, so the provenance line is per recipient.');
  }
  if (text.indexOf('{{UNSUBSCRIBE_URL}}') === -1) {
    problems.push('The plain text part has no {{UNSUBSCRIBE_URL}} placeholder.');
  }

  // The scope guard travels with the figure. If it is gone, the email states a
  // Florida only finding with nothing marking it as Florida only.
  if (html.toLowerCase().indexOf('florida only') === -1
      || html.toLowerCase().indexOf('not a national record') === -1) {
    problems.push('The scope guard is missing from the HTML. This data is Florida '
                + 'only and must never be described as a national record.');
  }

  if (problems.length) {
    throw new Error('Refusing to send:\n  - ' + problems.join('\n  - '));
  }
}

// ------------------------------------------------------------- recipients ---

function getRecipients_() {
  var ss = SpreadsheetApp.getActive();
  var sh = ss.getSheetByName(CONFIG.CONTACTS_SHEET);
  if (!sh) throw new Error('No sheet named ' + CONFIG.CONTACTS_SHEET);

  var values = sh.getDataRange().getValues();
  var headers = values[0].map(function (h) { return String(h).trim(); });
  var emailCol = headers.indexOf(CONFIG.EMAIL_HEADER);
  if (emailCol === -1) throw new Error('No "' + CONFIG.EMAIL_HEADER + '" column');
  var sourceCol = headers.indexOf(CONFIG.SOURCE_HEADER);

  var unsub = readColumnSet_(ss, UNSUB_SHEET, 0);
  var already = readSentSet_(ss);

  var seen = {}, out = [], sources = {}, skipped = {blank: 0, invalid: 0, dupe: 0,
                                      unsubscribed: 0, alreadySent: 0};
  for (var i = 1; i < values.length; i++) {
    var raw = String(values[i][emailCol] || '').trim().toLowerCase();
    if (!raw) { skipped.blank++; continue; }
    if (!/^[^@\s]+@[^@\s.]+\.[^@\s]+$/.test(raw)) { skipped.invalid++; continue; }
    if (seen[raw]) { skipped.dupe++; continue; }
    seen[raw] = true;
    if (unsub[raw]) { skipped.unsubscribed++; continue; }
    if (already[raw]) { skipped.alreadySent++; continue; }
    var src = sourceCol === -1 ? '' : String(values[i][sourceCol] || '').trim();
    sources[src || '(blank)'] = (sources[src || '(blank)'] || 0) + 1;
    out.push({email: raw, source: src});
  }
  return {recipients: out, skipped: skipped, sources: sources};
}

/** Match the Source cell against the provenance map, case insensitively. */
function provenanceFor_(source) {
  var s = String(source || '').toLowerCase();
  for (var key in CONFIG.PROVENANCE) {
    if (s.indexOf(key.toLowerCase()) !== -1) return CONFIG.PROVENANCE[key];
  }
  return CONFIG.PROVENANCE_DEFAULT;
}

function readColumnSet_(ss, sheetName, col) {
  var sh = ss.getSheetByName(sheetName);
  var set = {};
  if (!sh || sh.getLastRow() < 2) return set;
  sh.getRange(2, col + 1, sh.getLastRow() - 1, 1).getValues().forEach(function (r) {
    var v = String(r[0] || '').trim().toLowerCase();
    if (v) set[v] = true;
  });
  return set;
}

/** Only this issue counts, so a later issue is not blocked by an earlier one. */
function readSentSet_(ss) {
  var sh = ss.getSheetByName(LOG_SHEET);
  var set = {};
  if (!sh || sh.getLastRow() < 2) return set;
  sh.getRange(2, 1, sh.getLastRow() - 1, 4).getValues().forEach(function (r) {
    if (String(r[1]).trim() === CONFIG.ISSUE_ID && String(r[3]).trim() === 'sent') {
      set[String(r[2]).trim().toLowerCase()] = true;
    }
  });
  return set;
}

// ------------------------------------------------------------ unsubscribe ---

function unsubToken_(email) {
  var secret = PropertiesService.getScriptProperties().getProperty('UNSUB_SECRET');
  if (!secret) throw new Error('No UNSUB_SECRET. Run setup() first.');
  var sig = Utilities.computeHmacSha256Signature(email.toLowerCase(), secret);
  return Utilities.base64EncodeWebSafe(sig).replace(/=+$/, '');
}

function unsubUrl_(email) {
  return CONFIG.WEBAPP_URL
       + '?e=' + encodeURIComponent(email)
       + '&t=' + encodeURIComponent(unsubToken_(email));
}

/** One click unsubscribe endpoint. Deploy: execute as me, access anyone. */
function doGet(e) {
  var email = String((e.parameter && e.parameter.e) || '').trim().toLowerCase();
  var token = String((e.parameter && e.parameter.t) || '').trim();
  var ok = email && token && token === unsubToken_(email);

  if (ok) {
    var ss = SpreadsheetApp.getActive();
    var sh = ensureSheet_(ss, UNSUB_SHEET, ['Email', 'Timestamp', 'Source']);
    if (!readColumnSet_(ss, UNSUB_SHEET, 0)[email]) {
      sh.appendRow([email, new Date(), 'one click, ' + CONFIG.ISSUE_ID]);
    }
  }
  var msg = ok
    ? '<h1>Unsubscribed</h1><p>' + escapeHtml_(email)
      + ' will not receive Field Notes again.</p>'
    : '<h1>That link did not work</h1><p>Reply to the email and we will remove '
      + 'you by hand.</p>';
  return HtmlService.createHtmlOutput(
    '<meta name="viewport" content="width=device-width,initial-scale=1">'
    + '<div style="font-family:Arial,sans-serif;max-width:34em;margin:3em auto;'
    + 'padding:0 1em;color:#10213B">' + msg + '<p style="font-size:13px;color:#555">'
    + escapeHtml_(CONFIG.POSTAL_ADDRESS) + '</p></div>');
}

function escapeHtml_(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;')
                  .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// ------------------------------------------------------------------ send ---

function sendIssue() {
  var html = DriveApp.getFileById(CONFIG.HTML_FILE_ID).getBlob().getDataAsString('UTF-8');
  var text = DriveApp.getFileById(CONFIG.TEXT_FILE_ID).getBlob().getDataAsString('UTF-8');
  assertSendable_(html, text);

  var r = getRecipients_();
  var ss = SpreadsheetApp.getActive();
  var log = ensureSheet_(ss, LOG_SHEET, ['Timestamp', 'Issue', 'Email', 'Status', 'Source']);

  var quota = MailApp.getRemainingDailyQuota();
  var limit = Math.min(CONFIG.MAX_PER_RUN, r.recipients.length, quota);

  Logger.log('%s candidates, sending %s. Skipped: %s. Quota left today: %s. DRY_RUN=%s',
             r.recipients.length, limit, JSON.stringify(r.skipped), quota, CONFIG.DRY_RUN);
  // Shows exactly which Source strings exist, so PROVENANCE can be filled from
  // the data instead of guessed at.
  Logger.log('Sources seen: %s', JSON.stringify(r.sources));
  for (var k in r.sources) {
    if (provenanceFor_(k) === CONFIG.PROVENANCE_DEFAULT && k !== '(blank)') {
      Logger.log('NOTE: Source "%s" has no PROVENANCE entry, so %s recipients would '
               + 'get the generic line.', k, r.sources[k]);
    }
  }

  var rows = [];
  for (var i = 0; i < limit; i++) {
    var to = r.recipients[i].email;
    var why = provenanceFor_(r.recipients[i].source);
    var body = html.replace(/\{\{UNSUBSCRIBE_URL\}\}/g, unsubUrl_(to))
                   .replace(/\{\{POSTAL_ADDRESS\}\}/g, escapeHtml_(CONFIG.POSTAL_ADDRESS))
                   .replace(/\{\{WHY_YOU_GET_THIS\}\}/g, escapeHtml_(why));
    var plain = text.replace(/\{\{UNSUBSCRIBE_URL\}\}/g, unsubUrl_(to))
                    .replace(/\{\{POSTAL_ADDRESS\}\}/g, CONFIG.POSTAL_ADDRESS)
                    .replace(/\{\{WHY_YOU_GET_THIS\}\}/g, why);
    try {
      if (!CONFIG.DRY_RUN) {
        MailApp.sendEmail({
          to: to,
          subject: CONFIG.SUBJECT,
          body: plain,
          htmlBody: body,
          name: CONFIG.SENDER_NAME,
          replyTo: CONFIG.REPLY_TO
        });
        Utilities.sleep(CONFIG.THROTTLE_MS);
      }
      rows.push([new Date(), CONFIG.ISSUE_ID, to,
                 CONFIG.DRY_RUN ? 'dry-run' : 'sent', r.recipients[i].source]);
    } catch (err) {
      rows.push([new Date(), CONFIG.ISSUE_ID, to, 'failed', String(err)]);
    }
  }
  if (rows.length) {
    log.getRange(log.getLastRow() + 1, 1, rows.length, 5).setValues(rows);
  }
  Logger.log('Done. %s rows written to "%s".', rows.length, LOG_SHEET);
}

/** Send one copy to yourself using the real pipeline, before the list. */
function sendTestToSelf() {
  var html = DriveApp.getFileById(CONFIG.HTML_FILE_ID).getBlob().getDataAsString('UTF-8');
  var text = DriveApp.getFileById(CONFIG.TEXT_FILE_ID).getBlob().getDataAsString('UTF-8');
  assertSendable_(html, text);
  var me = Session.getActiveUser().getEmail();
  MailApp.sendEmail({
    to: me,
    subject: '[TEST] ' + CONFIG.SUBJECT,
    body: text.replace(/\{\{UNSUBSCRIBE_URL\}\}/g, unsubUrl_(me))
              .replace(/\{\{POSTAL_ADDRESS\}\}/g, CONFIG.POSTAL_ADDRESS)
              .replace(/\{\{WHY_YOU_GET_THIS\}\}/g, CONFIG.PROVENANCE_DEFAULT),
    htmlBody: html.replace(/\{\{UNSUBSCRIBE_URL\}\}/g, unsubUrl_(me))
                  .replace(/\{\{POSTAL_ADDRESS\}\}/g, escapeHtml_(CONFIG.POSTAL_ADDRESS))
                  .replace(/\{\{WHY_YOU_GET_THIS\}\}/g,
                           escapeHtml_(CONFIG.PROVENANCE_DEFAULT)),
    name: CONFIG.SENDER_NAME,
    replyTo: CONFIG.REPLY_TO
  });
  Logger.log('Test sent to %s', me);
}
