/**
 * Field Notes sender. Google Apps Script, bound to the EMR Contact CRM sheet.
 *
 * Why this exists: the Gmail API path strips every <img> tag out of the HTML it
 * sends, so the figure never reaches the inbox. MailApp does not sanitise, so
 * the email arrives as built.
 *
 * This is a weekly sender, not a one shot. Nothing about an individual issue
 * lives in this file. An issue is a row on the "Field Notes Issues" sheet plus
 * two files in a Drive folder, named by convention:
 *
 *     field-notes-<issue>.html
 *     field-notes-<issue>.txt
 *
 * Shipping next week means dropping two files in the folder and typing one row.
 * No code edit, no redeploy. A time driven trigger fires sendScheduledIssue()
 * once a week, it takes the oldest issue whose send date has passed, and it
 * stops when there is nothing due.
 *
 * It refuses to send until the things that make a bulk send lawful and honest
 * are actually in place. See assertSendable_(). That is deliberate: this list
 * was collected from a stretcher survey and column Q of every row reads
 * "Not recorded (survey did not ask)". Nobody on it asked for a newsletter.
 *
 * First run: setup(), then installWeeklyTrigger(). Check it with listIssues()
 * and dryRunNextIssue() before DRY_RUN comes off.
 */

// ---------------------------------------------------------------- config ---

var CONFIG = {
  // The Drive folder holding every built issue. Files are found by name, so a
  // new issue needs no config change. "Field Notes issues", beside the CRM.
  ISSUES_FOLDER_ID: '1uctXc8UgDpEZLHOUkf285UWeIWTAlpZf',

  // When the weekly trigger fires. Apps Script triggers are not to the minute:
  // atHour(9) means some time in the 9am hour, in the script's timezone (File,
  // Project properties). Change these, then run installWeeklyTrigger() again.
  SEND_WEEKDAY:   'TUESDAY',
  SEND_HOUR:      9,

  // Where importFigure() fetches a figure from, keyed by issue id. raw
  // .githubusercontent.com sends "content-security-policy: default-src 'none';
  // sandbox", which stops a BROWSER rendering it and is why it cannot be used as
  // an <img> src. UrlFetchApp is a server side fetch, so that header does not
  // apply: it reads the bytes fine. The figure then lives in Drive and travels
  // inside the message, so nothing at send time depends on GitHub.
  FIGURE_SOURCE: {
    'issue-01': 'https://raw.githubusercontent.com/EMR-INC/emr-inc-site/main/'
              + 'assets/field-notes/issue-01-figure.png'
  },

  CONTACTS_SHEET: 'Contacts',
  EMAIL_HEADER:   'Email',
  SOURCE_HEADER:  'Source',
  CONSENT_HEADER: 'Consent to be contacted',

  // Why each recipient is getting this, keyed by the CRM Source column. The list
  // is not one cohort: part of it came from the EMS World booth and the rest from
  // the off road stretcher survey, so a single hardcoded sentence would be a
  // false statement to one group or the other.
  //
  // Keys are matched case insensitively as substrings of the Source cell. Filled
  // from a dry run against the real sheet, not guessed. The EMS World cohort
  // carries Source "MyLEADS Mobile", which is the badge scanner used at the
  // booth, so that is the string that has to match.
  PROVENANCE: {
    'off-road transport survey':
      'You are receiving this because you took part in the EMR Inc. off road transport survey.',
    'myleads':
      'You are receiving this because we met at EMS World Expo.',
    'ems world':
      'You are receiving this because we met at EMS World Expo.',
    'contact form':
      'You are receiving this because you contacted EMR Inc. through our website.'
  },
  PROVENANCE_DEFAULT:
    'You are receiving this because you are on the EMR Inc. contact list.',

  SENDER_NAME:    'EMR Inc. Field Notes',
  REPLY_TO:       'michael.harvey@emr-inc.net',
  SITE_URL:       'https://emr-inc.net',

  // CAN-SPAM 15 USC 7704(a)(5): a commercial message must carry a valid physical
  // postal address. A website is not one, so emr-inc.net does not satisfy this.
  // This is the registered agent address on the Delaware filing, File No.
  // 10300393. It goes in the footer of every issue and on the unsubscribe page,
  // so it is public once the first issue ships.
  POSTAL_ADDRESS: 'EMR Inc., 131 Continental Drive, Suite 305, Newark, DE 19713',

  // The unsubscribe endpoint. This has to be THIS script's own deployment url
  // (script.google.com/macros/s/.../exec), not emr-inc.net: the apex is static
  // GitHub Pages and cannot record an unsubscribe. Deploy, New deployment, Web
  // app, execute as me, access anyone, then paste the url it gives you.
  // Deployed 2026-10-05. If you ever create a NEW deployment rather than a new
  // version of this one, Google mints a different url and every unsubscribe link
  // in already sent issues points at the old one. Update in place instead:
  // Deploy, Manage deployments, pencil, Version: New version.
  WEBAPP_URL:     'https://script.google.com/macros/s/AKfycbzwr0NTMUCgIjtwnQbsDWSWF6u10illXvlsnd0dRk0jIwHMWQ50zoB9MX4JjnPSawx9Ow/exec',

  DRY_RUN:        true,       // writes the log, sends nothing
  MAX_PER_RUN:    90,         // Workspace allows 1500 a day, consumer 100
  THROTTLE_MS:    1200
};

var LOG_SHEET    = 'Field Notes Log';
var UNSUB_SHEET  = 'Field Notes Unsubscribed';
var ISSUES_SHEET = 'Field Notes Issues';

// The content id the HTML references as <img src="cid:figure">. Set by
// build_issue01.py; the two have to agree or the figure silently vanishes,
// which is what assertSendable_ checks.
var FIGURE_CID = 'figure';

// The masthead image, optional, and whatever format the export produced. A
// header comes out of an image tool rather than a build script, so insisting on
// .png would mean renaming a .jpg every week and eventually forgetting.
var HEADER_CID = 'header';
var HEADER_EXTS = ['.jpg', '.jpeg', '.png'];

// 1,200,000 bytes, about 1.1 MB. Generous enough for a real photographic
// masthead and far below the 7.25 MB a full resolution render came in at.
var HEADER_MAX_BYTES = 1200000;

// Column order on the Issues sheet. Read by name, not by index, so a reordered
// or extra column does not silently send the wrong thing.
var ISSUE_HEADERS = ['Issue', 'Subject', 'Send on', 'Status', 'Sent', 'Last run'];

// ----------------------------------------------------------------- setup ---

function setup() {
  var ss = SpreadsheetApp.getActive();
  ensureSheet_(ss, LOG_SHEET, ['Timestamp', 'Issue', 'Email', 'Status', 'Source']);
  ensureSheet_(ss, UNSUB_SHEET, ['Email', 'Timestamp', 'Source']);
  var issues = ensureSheet_(ss, ISSUES_SHEET, ISSUE_HEADERS);

  // Seed the first row so the shape of an issue is obvious without reading this
  // file. Only when the sheet is empty, so setup() stays safe to run again.
  if (issues.getLastRow() < 2) {
    issues.appendRow(['issue-01',
                      'Your engine has a better file than your firefighters',
                      '', 'hold', '', '']);
    issues.getRange(2, 3).setNumberFormat('yyyy-mm-dd');
  }

  var props = PropertiesService.getScriptProperties();
  if (!props.getProperty('UNSUB_SECRET')) {
    props.setProperty('UNSUB_SECRET', Utilities.getUuid() + Utilities.getUuid());
  }
  Logger.log('Sheets ready. Unsubscribe secret set. Next: fill POSTAL_ADDRESS, '
           + 'deploy as a web app (execute as me, access anyone), paste the url '
           + 'into WEBAPP_URL, then run installWeeklyTrigger().');
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

// --------------------------------------------------------------- trigger ---

/**
 * Install the weekly trigger. Safe to run again: it clears the old one first,
 * so changing SEND_WEEKDAY or SEND_HOUR does not leave two triggers firing.
 */
function installWeeklyTrigger() {
  removeTriggers_();
  var day = ScriptApp.WeekDay[CONFIG.SEND_WEEKDAY];
  if (!day) {
    throw new Error('SEND_WEEKDAY must be a day name like TUESDAY, got "'
                  + CONFIG.SEND_WEEKDAY + '"');
  }
  ScriptApp.newTrigger('sendScheduledIssue')
    .timeBased().onWeekDay(day).atHour(CONFIG.SEND_HOUR).create();
  Logger.log('Weekly trigger installed: %s around %s:00, script timezone %s. '
           + 'It sends whichever issue is due and does nothing when none is.',
             CONFIG.SEND_WEEKDAY, CONFIG.SEND_HOUR,
             Session.getScriptTimeZone());
}

function removeTriggers_() {
  var n = 0;
  ScriptApp.getProjectTriggers().forEach(function (t) {
    var fn = t.getHandlerFunction();
    if (fn === 'sendScheduledIssue' || fn === 'resumeIssue') {
      ScriptApp.deleteTrigger(t); n++;
    }
  });
  return n;
}

/** Stop the weekly send without touching anything else. */
function uninstallTriggers() {
  Logger.log('Removed %s trigger(s). Nothing will send until '
           + 'installWeeklyTrigger() runs again.', removeTriggers_());
}

/**
 * A single catch up run, a day out. The daily mail quota is the reason this
 * exists: a list longer than MAX_PER_RUN cannot go in one firing, and waiting a
 * whole week for the rest would ship half an issue.
 */
function scheduleResume_() {
  ScriptApp.newTrigger('resumeIssue').timeBased().after(25 * 60 * 60 * 1000).create();
}

function resumeIssue() {
  // One shot. Clear it first so a failure cannot leave a trigger behind.
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'resumeIssue') ScriptApp.deleteTrigger(t);
  });
  sendScheduledIssue();
}

// ---------------------------------------------------------------- issues ---

/**
 * The oldest issue whose send date has passed and which is not finished or on
 * hold. Returns null when nothing is due, which is the normal state on most
 * firings and must not be an error.
 */
function dueIssue_() {
  var ss = SpreadsheetApp.getActive();
  var sh = ss.getSheetByName(ISSUES_SHEET);
  if (!sh) throw new Error('No sheet named "' + ISSUES_SHEET + '". Run setup().');

  // Headers are checked before the empty check, not after. A renamed or deleted
  // column on an otherwise empty sheet would otherwise read as "nothing due",
  // and the first you would hear of it is a Tuesday that quietly did nothing.
  var values = sh.getDataRange().getValues();
  var col = headerIndex_(values[0], ISSUE_HEADERS, ISSUES_SHEET);
  if (values.length < 2) return null;

  var now = new Date(), best = null;

  for (var i = 1; i < values.length; i++) {
    var id = String(values[i][col['Issue']] || '').trim();
    if (!id) continue;
    var status = String(values[i][col['Status']] || '').trim().toLowerCase();
    if (status === 'sent' || status === 'hold' || status === 'skip') continue;

    var when = values[i][col['Send on']];
    if (!(when instanceof Date)) continue;   // no date set means not scheduled
    if (when.getTime() > now.getTime()) continue;

    if (!best || when.getTime() < best.sendOn.getTime()) {
      best = {
        row:     i + 1,
        id:      id,
        subject: String(values[i][col['Subject']] || '').trim(),
        sendOn:  when,
        status:  status,
        col:     col
      };
    }
  }
  return best;
}

/** Map header name to column index, failing loudly on a missing column. */
function headerIndex_(headerRow, required, sheetName) {
  var headers = headerRow.map(function (h) { return String(h).trim(); });
  var col = {};
  required.forEach(function (name) {
    var i = headers.indexOf(name);
    if (i === -1) {
      throw new Error('Sheet "' + sheetName + '" has no "' + name + '" column. '
                    + 'Expected: ' + required.join(', '));
    }
    col[name] = i;
  });
  return col;
}

/**
 * The two built files for an issue, found by name. Convention rather than a
 * pasted file id: a hardcoded id is one more thing to edit every week, and
 * getting it wrong sends last week's email to the whole list.
 */
function issueFiles_(issueId) {
  if (!CONFIG.ISSUES_FOLDER_ID) {
    throw new Error('ISSUES_FOLDER_ID is empty.');
  }
  var folder = DriveApp.getFolderById(CONFIG.ISSUES_FOLDER_ID);
  return {
    html:   readOne_(folder, 'field-notes-' + issueId + '.html'),
    text:   readOne_(folder, 'field-notes-' + issueId + '.txt'),
    image:  imageOrNull_(folder, 'field-notes-' + issueId + '.png', FIGURE_CID),
    header: headerOrNull_(folder, issueId)
  };
}

/** The masthead, under whichever extension the export produced. */
function headerOrNull_(folder, issueId) {
  var base = 'field-notes-' + issueId + '-header', found = null;
  for (var i = 0; i < HEADER_EXTS.length; i++) {
    var blob = imageOrNull_(folder, base + HEADER_EXTS[i], HEADER_CID);
    if (blob) {
      if (found) {
        throw new Error('Two headers for ' + issueId + ' in the issues folder, '
                      + 'under different extensions. Delete one: there is no way '
                      + 'to tell which you meant.');
      }
      found = blob;
    }
  }
  return found;
}

/**
 * The figure, carried inside the message rather than linked.
 *
 * A linked image has two failure modes neither we nor the recipient control.
 * It has to be published, and assets pushed to main do not reach emr-inc.net:
 * the site deploys only from the open_data_daily workflow. The figure sat on
 * main, unpublished and 404ing, while the email pointed at it. And even a
 * working url is blocked by default in Gmail and Outlook for a large share of
 * recipients, so it would vanish silently for people we never hear from.
 *
 * Null is allowed, for an issue with no figure. assertSendable_ is what insists
 * the two agree.
 */
function imageOrNull_(folder, name, cid) {
  var it = folder.getFilesByName(name);
  if (!it.hasNext()) return null;
  var file = it.next();
  if (it.hasNext()) {
    throw new Error('More than one file named "' + name + '" in the issues '
                  + 'folder. Delete the duplicate.');
  }
  var blob = file.getBlob();
  blob.setName(cid);
  return blob;
}

function readOne_(folder, name) {
  var it = folder.getFilesByName(name);
  if (!it.hasNext()) {
    throw new Error('No file named "' + name + '" in the issues folder. Build the '
                  + 'issue and upload both parts before the send date.');
  }
  var file = it.next();
  if (it.hasNext()) {
    throw new Error('More than one file named "' + name + '" in the issues folder. '
                  + 'Delete the duplicate: there is no way to tell which is the '
                  + 'one you meant.');
  }
  return file.getBlob().getDataAsString('UTF-8');
}

/** What is scheduled, and whether its files are actually there yet. */
function listIssues() {
  var ss = SpreadsheetApp.getActive();
  var sh = ss.getSheetByName(ISSUES_SHEET);
  if (!sh || sh.getLastRow() < 2) { Logger.log('No issues scheduled.'); return; }

  var values = sh.getDataRange().getValues();
  var col = headerIndex_(values[0], ISSUE_HEADERS, ISSUES_SHEET);
  for (var i = 1; i < values.length; i++) {
    var id = String(values[i][col['Issue']] || '').trim();
    if (!id) continue;
    var files = 'both parts present';
    try { issueFiles_(id); } catch (err) { files = 'PROBLEM: ' + err.message; }
    var when = values[i][col['Send on']];
    Logger.log('%s | %s | %s | sent %s | %s',
               id,
               when instanceof Date
                 ? Utilities.formatDate(when, Session.getScriptTimeZone(), 'yyyy-MM-dd')
                 : '(no date)',
               String(values[i][col['Status']] || '(ready)'),
               String(values[i][col['Sent']] || 0),
               files);
  }
  var due = dueIssue_();
  Logger.log(due ? 'Due now: ' + due.id : 'Nothing due right now.');
}

// ------------------------------------------------------------ fail closed ---

/**
 * Everything that must be true before a single message goes out. Each check is
 * here because its absence is a real problem, not a style preference.
 */
function assertSendable_(issue, html, text, image, header) {
  var problems = [];

  if (!CONFIG.POSTAL_ADDRESS) {
    problems.push('POSTAL_ADDRESS is empty. CAN-SPAM requires a valid physical '
                + 'postal address in every commercial message.');
  }
  if (!CONFIG.WEBAPP_URL) {
    problems.push('WEBAPP_URL is empty, so the unsubscribe link has nowhere to go. '
                + 'Deploy this script as a web app first.');
  } else if (!/^https:\/\/script\.google\.com\/macros\/s\/[A-Za-z0-9_-]+\/exec$/
               .test(CONFIG.WEBAPP_URL)) {
    // Shape only. It cannot prove the endpoint answers, but it catches the two
    // url forms that silently do not: the /macros/u/<n>/s/... form the browser
    // shows when several Google accounts are signed in, which is per account and
    // not the deployment url, and a url with the /exec suffix missing. Either
    // one would send the whole list an unsubscribe link that goes nowhere, and
    // nothing downstream would notice.
    problems.push('WEBAPP_URL is not a web app exec url. It must look exactly '
                + 'like https://script.google.com/macros/s/<id>/exec, with no '
                + '"/u/<number>/" in it and ending in /exec. Got: '
                + CONFIG.WEBAPP_URL);
  }
  if (!CONFIG.REPLY_TO) {
    problems.push('REPLY_TO is empty. A bulk send needs a monitored reply address.');
  }
  if (!issue.subject) {
    problems.push('Issue ' + issue.id + ' has no Subject on the issues sheet.');
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

  // The figure and the HTML have to agree. A cid reference with no attachment is
  // a broken image in every inbox, and an attachment nothing points at is dead
  // weight on 127 messages. Neither announces itself, so both are checked here.
  var wantsFigure = html.indexOf('cid:' + FIGURE_CID) !== -1;
  if (wantsFigure && !image) {
    problems.push('The HTML references cid:' + FIGURE_CID + ' but there is no '
                + 'field-notes-' + issue.id + '.png in the issues folder, so the '
                + 'figure would be a broken image.');
  }
  if (!wantsFigure && image) {
    problems.push('There is a field-notes-' + issue.id + '.png in the issues '
                + 'folder but the HTML never references cid:' + FIGURE_CID + ', '
                + 'so it would ride along unseen on every message.');
  }

  var wantsHeader = html.indexOf('cid:' + HEADER_CID) !== -1;
  if (wantsHeader && !header) {
    problems.push('The HTML references cid:' + HEADER_CID + ' but there is no '
                + 'field-notes-' + issue.id + '-header file in the issues folder '
                + '(' + HEADER_EXTS.join(', ') + '), so the masthead would be a '
                + 'broken image.');
  }
  if (!wantsHeader && header) {
    problems.push('There is a header image for ' + issue.id + ' in the issues '
                + 'folder but the HTML never references cid:' + HEADER_CID + ', '
                + 'so it would ride along unseen on every message.');
  }
  // A header is the heaviest thing in the message and it ships 127 times. This
  // is a warning threshold, not a client limit: Gmail's 102,400 byte clip is on
  // the HTML part only and does not count attachments.
  if (header && header.getBytes().length > HEADER_MAX_BYTES) {
    problems.push('The header is ' + header.getBytes().length + ' bytes, over the '
                + HEADER_MAX_BYTES + ' this refuses to send. Export it narrower '
                + 'or at a lower quality. The full resolution render is for '
                + 'archive, not for 127 inboxes.');
  }

  // The scope guard travels with the figure. If it is gone, the email states a
  // Florida only finding with nothing marking it as Florida only. This check
  // applies to every issue drawing on that table, which is why it lives in the
  // sender rather than in one issue's build script.
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

function getRecipients_(issueId) {
  var ss = SpreadsheetApp.getActive();
  var sh = ss.getSheetByName(CONFIG.CONTACTS_SHEET);
  if (!sh) throw new Error('No sheet named ' + CONFIG.CONTACTS_SHEET);

  var values = sh.getDataRange().getValues();
  var headers = values[0].map(function (h) { return String(h).trim(); });
  var emailCol = headers.indexOf(CONFIG.EMAIL_HEADER);
  if (emailCol === -1) throw new Error('No "' + CONFIG.EMAIL_HEADER + '" column');
  var sourceCol = headers.indexOf(CONFIG.SOURCE_HEADER);
  var consentCol = headers.indexOf(CONFIG.CONSENT_HEADER);

  var unsub = readColumnSet_(ss, UNSUB_SHEET, 0);
  var already = readSentSet_(ss, issueId);

  var seen = {}, out = [], sources = {}, skipped = {blank: 0, invalid: 0, dupe: 0,
                                      unsubscribed: 0, alreadySent: 0,
                                      consentRefused: 0};
  for (var i = 1; i < values.length; i++) {
    var raw = String(values[i][emailCol] || '').trim().toLowerCase();
    if (!raw) { skipped.blank++; continue; }
    if (!/^[^@\s]+@[^@\s.]+\.[^@\s]+$/.test(raw)) { skipped.invalid++; continue; }
    if (seen[raw]) { skipped.dupe++; continue; }
    seen[raw] = true;
    if (unsub[raw]) { skipped.unsubscribed++; continue; }
    if (already[raw]) { skipped.alreadySent++; continue; }
    // An unchecked consent box is a refusal and outranks everything else here.
    if (consentCol !== -1 && consentRefused_(values[i][consentCol])) {
      skipped.consentRefused++; continue;
    }
    var src = sourceCol === -1 ? '' : String(values[i][sourceCol] || '').trim();
    sources[src || '(blank)'] = (sources[src || '(blank)'] || 0) + 1;
    out.push({email: raw, source: src});
  }
  return {recipients: out, skipped: skipped, sources: sources};
}

/**
 * True only for an explicit refusal. "Not recorded" means the question was never
 * asked, which is a different thing and is not treated as a no here.
 */
function consentRefused_(consent) {
  var c = String(consent || '').trim().toLowerCase();
  if (!c) return false;
  if (c.indexOf('not recorded') === 0) return false;
  return /(not given|declined|opt[\s-]?out|unsubscrib|^no\b)/.test(c);
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

/**
 * Who already got THIS issue. Scoped to one issue on purpose: it is what makes a
 * part sent issue resumable, and what stops week two being blocked by week one.
 */
function readSentSet_(ss, issueId) {
  var sh = ss.getSheetByName(LOG_SHEET);
  var set = {};
  if (!sh || sh.getLastRow() < 2) return set;
  sh.getRange(2, 1, sh.getLastRow() - 1, 4).getValues().forEach(function (r) {
    if (String(r[1]).trim() === issueId && String(r[3]).trim() === 'sent') {
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

/**
 * One click unsubscribe endpoint. Deploy: execute as me, access anyone.
 *
 * The token is an HMAC of the address, so it is per recipient and not guessable,
 * and it stays valid across issues. That is the point: an unsubscribe link in a
 * year old email still works.
 */
function doGet(e) {
  var email = String((e.parameter && e.parameter.e) || '').trim().toLowerCase();
  var token = String((e.parameter && e.parameter.t) || '').trim();
  var ok = email && token && token === unsubToken_(email);

  if (ok) {
    var ss = SpreadsheetApp.getActive();
    var sh = ensureSheet_(ss, UNSUB_SHEET, ['Email', 'Timestamp', 'Source']);
    if (!readColumnSet_(ss, UNSUB_SHEET, 0)[email]) {
      sh.appendRow([email, new Date(), 'one click']);
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

/**
 * The trigger entry point. Finds the due issue, sends what the quota allows,
 * and books a catch up run if the list did not fit.
 *
 * Doing nothing is the common case and is not a failure: an unconditional throw
 * here would mail a Google error report every single week.
 */
function sendScheduledIssue() {
  var issue = dueIssue_();
  if (!issue) {
    Logger.log('Nothing due. Checked "%s" for a row with a past send date and no '
             + 'sent, hold or skip status.', ISSUES_SHEET);
    return;
  }
  Logger.log('Due: %s ("%s"), scheduled %s', issue.id, issue.subject,
             Utilities.formatDate(issue.sendOn, Session.getScriptTimeZone(),
                                  'yyyy-MM-dd'));
  sendIssue_(issue);
}

/** Send a named issue now, ignoring its date. For a manual catch up. */
function sendIssueNow(issueId) {
  // This one keeps requiring an argument, unlike sendTestToSelf. The Run button
  // passing none is the safety: a real send to the whole list should not be one
  // misclick away in the editor.
  if (!issueId) throw new Error('sendIssueNow needs an issue id, e.g. "issue-01". '
                              + 'The editor Run button cannot pass one, which is '
                              + 'deliberate: set the Send on date and let the '
                              + 'trigger do it, or call this from another function.');
  return sendIssue_(issueByIdOrThrow_(issueId));
}

function sendIssue_(issue) {
  var files = issueFiles_(issue.id);
  var html = files.html, text = files.text;
  assertSendable_(issue, html, text, files.image, files.header);

  var r = getRecipients_(issue.id);
  var ss = SpreadsheetApp.getActive();
  var log = ensureSheet_(ss, LOG_SHEET, ['Timestamp', 'Issue', 'Email', 'Status', 'Source']);

  var quota = MailApp.getRemainingDailyQuota();
  var limit = Math.min(CONFIG.MAX_PER_RUN, r.recipients.length, quota);
  var remaining = r.recipients.length - limit;

  Logger.log('%s: %s candidates, sending %s, %s left for a catch up run. '
           + 'Skipped: %s. Quota left today: %s. DRY_RUN=%s',
             issue.id, r.recipients.length, limit, remaining,
             JSON.stringify(r.skipped), quota, CONFIG.DRY_RUN);
  Logger.log('Sources seen: %s', JSON.stringify(r.sources));
  for (var k in r.sources) {
    if (provenanceFor_(k) === CONFIG.PROVENANCE_DEFAULT && k !== '(blank)') {
      Logger.log('NOTE: Source "%s" has no PROVENANCE entry, so %s recipients would '
               + 'get the generic line.', k, r.sources[k]);
    }
  }

  var rows = [], sent = 0;
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
        var message = {
          to: to,
          subject: issue.subject,
          body: plain,
          htmlBody: body,
          name: CONFIG.SENDER_NAME,
          replyTo: CONFIG.REPLY_TO
        };
        var imgs = inlineImages_(files);
        if (Object.keys(imgs).length) message.inlineImages = imgs;
        MailApp.sendEmail(message);
        Utilities.sleep(CONFIG.THROTTLE_MS);
      }
      sent++;
      rows.push([new Date(), issue.id, to,
                 CONFIG.DRY_RUN ? 'dry-run' : 'sent', r.recipients[i].source]);
    } catch (err) {
      rows.push([new Date(), issue.id, to, 'failed', String(err)]);
    }
  }
  if (rows.length) {
    log.getRange(log.getLastRow() + 1, 1, rows.length, 5).setValues(rows);
  }

  // Status on the issues sheet is the record of what shipped. A dry run must not
  // write it, or the real send would see "sent" and skip the issue entirely.
  if (!CONFIG.DRY_RUN) {
    markIssue_(issue, remaining > 0 ? 'sending' : 'sent', sent,
               remaining > 0
                 ? sent + ' sent, ' + remaining + ' queued for a catch up run'
                 : sent + ' sent, issue complete');
    if (remaining > 0) scheduleResume_();
  }
  Logger.log('Done. %s rows written to "%s".%s', rows.length, LOG_SHEET,
             remaining > 0 && !CONFIG.DRY_RUN
               ? ' Catch up run booked for about 25 hours out.' : '');
}

/** The inlineImages map MailApp wants, keyed by the cids the HTML references. */
function inlineImages_(files) {
  var map = {};
  if (files.image) map[FIGURE_CID] = files.image;
  if (files.header) map[HEADER_CID] = files.header;
  return map;
}

/** Write status, a running sent count and a note back onto the issues sheet. */
function markIssue_(issue, status, sentThisRun, note) {
  var sh = SpreadsheetApp.getActive().getSheetByName(ISSUES_SHEET);
  var prior = Number(sh.getRange(issue.row, issue.col['Sent'] + 1).getValue()) || 0;
  sh.getRange(issue.row, issue.col['Status'] + 1).setValue(status);
  sh.getRange(issue.row, issue.col['Sent'] + 1).setValue(prior + sentThisRun);
  sh.getRange(issue.row, issue.col['Last run'] + 1).setValue(
    Utilities.formatDate(new Date(), Session.getScriptTimeZone(),
                         'yyyy-MM-dd HH:mm') + ' | ' + note);
}

/** Every gate and every selection decision, writing nothing and sending nothing. */
function dryRunNextIssue() {
  var issue = dueIssue_();
  if (!issue) { Logger.log('Nothing due. Set a past date on an issues row.'); return; }
  var was = CONFIG.DRY_RUN;
  CONFIG.DRY_RUN = true;
  try { sendIssue_(issue); } finally { CONFIG.DRY_RUN = was; }
}

/**
 * Fetch an issue's figure into the Drive issues folder, so nobody has to find
 * the file and drag it in. No argument means the newest row on the sheet,
 * because the editor's Run button cannot pass one.
 *
 * It verifies what came back rather than trusting a 200: a redirect to a login
 * page or an error page is still a 200 with a body, and saved as a .png it would
 * be a broken image in 127 inboxes that nothing downstream would catch.
 */
function importFigure(issueId) {
  var issue = issueId ? issueByIdOrThrow_(issueId) : newestIssueOrThrow_();
  var url = CONFIG.FIGURE_SOURCE[issue.id];
  if (!url) {
    throw new Error('No FIGURE_SOURCE entry for "' + issue.id + '". Add the url '
                  + 'to CONFIG.FIGURE_SOURCE, or put the png in the issues '
                  + 'folder by hand as field-notes-' + issue.id + '.png');
  }

  var res = UrlFetchApp.fetch(url, {muteHttpExceptions: true});
  var code = res.getResponseCode();
  if (code !== 200) {
    throw new Error('Fetching the figure returned HTTP ' + code + ' from ' + url);
  }

  var bytes = res.getBlob().getBytes();
  // PNG magic number. Anything else means we were handed a page, not an image.
  var MAGIC = [-119, 80, 78, 71, 13, 10, 26, 10];
  if (bytes.length < MAGIC.length) {
    throw new Error('The figure came back empty from ' + url);
  }
  for (var i = 0; i < MAGIC.length; i++) {
    if (bytes[i] !== MAGIC[i]) {
      throw new Error('What came back from ' + url + ' is not a PNG. First bytes: '
                    + bytes.slice(0, 8).join(',') + '. Saving it would be a broken '
                    + 'image in every inbox.');
    }
  }

  var name = 'field-notes-' + issue.id + '.png';
  var folder = DriveApp.getFolderById(CONFIG.ISSUES_FOLDER_ID);
  // Replace rather than add. Two files of one name is a refusal at send time.
  var existing = folder.getFilesByName(name), replaced = 0;
  while (existing.hasNext()) { existing.next().setTrashed(true); replaced++; }

  var blob = res.getBlob().setName(name);
  folder.createFile(blob);
  Logger.log('Imported %s into the issues folder: %s bytes%s. Run listIssues() '
           + 'to confirm, then sendTestToSelf().', name, bytes.length,
             replaced ? ', replacing ' + replaced + ' older copy' : '');
}

/** A row on the issues sheet, by id. Throws rather than guessing. */
function issueByIdOrThrow_(issueId) {
  var sh = SpreadsheetApp.getActive().getSheetByName(ISSUES_SHEET);
  if (!sh) throw new Error('No sheet named "' + ISSUES_SHEET + '". Run setup().');
  var values = sh.getDataRange().getValues();
  var col = headerIndex_(values[0], ISSUE_HEADERS, ISSUES_SHEET);
  for (var i = 1; i < values.length; i++) {
    if (String(values[i][col['Issue']] || '').trim() === issueId) {
      return issueFromRow_(values[i], i + 1, col);
    }
  }
  throw new Error('No row for "' + issueId + '" on the ' + ISSUES_SHEET + ' sheet.');
}

/** The last row carrying an issue id. What you almost always mean by "this one". */
function newestIssueOrThrow_() {
  var sh = SpreadsheetApp.getActive().getSheetByName(ISSUES_SHEET);
  if (!sh) throw new Error('No sheet named "' + ISSUES_SHEET + '". Run setup().');
  var values = sh.getDataRange().getValues();
  var col = headerIndex_(values[0], ISSUE_HEADERS, ISSUES_SHEET);
  for (var i = values.length - 1; i >= 1; i--) {
    if (String(values[i][col['Issue']] || '').trim()) {
      return issueFromRow_(values[i], i + 1, col);
    }
  }
  throw new Error('The ' + ISSUES_SHEET + ' sheet has no issues on it yet.');
}

function issueFromRow_(row, rowNumber, col) {
  return {
    row:     rowNumber,
    id:      String(row[col['Issue']] || '').trim(),
    subject: String(row[col['Subject']] || '').trim(),
    sendOn:  row[col['Send on']],
    status:  String(row[col['Status']] || '').trim().toLowerCase(),
    col:     col
  };
}

/** Send one copy to yourself using the real pipeline, before the list. */
function sendTestToSelf(issueId) {
  // No argument is the normal case, because the editor's Run button cannot pass
  // one. So the default has to be something sensible rather than an error: the
  // newest row on the sheet, whatever its date or status. A test is exactly when
  // the issue is still on hold with no date, so requiring a DUE issue here made
  // the function unrunnable at the one moment it is wanted.
  var issue = issueId ? issueByIdOrThrow_(issueId) : newestIssueOrThrow_();
  Logger.log('Testing %s ("%s"). %s', issue.id, issue.subject,
             issueId ? 'Asked for by id.'
                     : 'Newest row on the sheet, since no id was given.');

  var files = issueFiles_(issue.id);
  assertSendable_(issue, files.html, files.text, files.image, files.header);
  var me = Session.getActiveUser().getEmail();
  var message = {
    to: me,
    subject: '[TEST] ' + issue.subject,
    body: files.text.replace(/\{\{UNSUBSCRIBE_URL\}\}/g, unsubUrl_(me))
              .replace(/\{\{POSTAL_ADDRESS\}\}/g, CONFIG.POSTAL_ADDRESS)
              .replace(/\{\{WHY_YOU_GET_THIS\}\}/g, CONFIG.PROVENANCE_DEFAULT),
    htmlBody: files.html.replace(/\{\{UNSUBSCRIBE_URL\}\}/g, unsubUrl_(me))
                  .replace(/\{\{POSTAL_ADDRESS\}\}/g, escapeHtml_(CONFIG.POSTAL_ADDRESS))
                  .replace(/\{\{WHY_YOU_GET_THIS\}\}/g,
                           escapeHtml_(CONFIG.PROVENANCE_DEFAULT)),
    name: CONFIG.SENDER_NAME,
    replyTo: CONFIG.REPLY_TO
  };
  var imgs = inlineImages_(files);
  if (Object.keys(imgs).length) message.inlineImages = imgs;
  MailApp.sendEmail(message);
  Logger.log('Test of %s sent to %s. Figure %s, header %s. Nothing was written '
           + 'to the issues sheet.', issue.id, me,
             files.image ? 'attached inline' : 'ABSENT',
             files.header ? files.header.getBytes().length + ' bytes inline' : 'none');
}
