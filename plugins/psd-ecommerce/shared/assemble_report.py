#!/usr/bin/env python3
"""Deterministically assemble a PSD report from locked parts.

The agent never authors CSS or the header/footer. It writes only:
  - a BODY fragment (modules picked from report-template.html, {{tokens}} filled), and
  - a tokens.json of header/footer values.
This script welds those onto the fixed shell + canonical CSS, and FAILS CLOSED if
anything is missing — so the stylesheet and uniform header can't be re-authored.

Contract:
  assemble_report.py --css report.css --shell report-shell.html \\
                     --body body.html --tokens tokens.json --out report.html

Steps:
  1. read the shell,
  2. replace  /*__CSS__*/       with the verbatim contents of report.css,
  3. replace  <!--__BODY__-->   with the body fragment file,
  4. substitute every {{KEY}} from tokens.json,
  5. FAIL (exit 1) if any {{...}} remains unfilled, and
  6. assert the output contains the CSS fingerprint + the canonical header markers.
"""
import argparse, json, re, sys

CSS_MARKER = "/*__CSS__*/"
BODY_MARKER = "<!--__BODY__-->"
FINGERPRINT = "/* PSD-REPORT-CSS */"
TOKEN_RE = re.compile(r"\{\{.*?\}\}", re.DOTALL)


def die(msg):
    sys.stderr.write("assemble_report: ERROR: " + msg + "\n")
    sys.exit(1)


def read(path, what):
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except OSError as e:
        die("cannot read %s (%s): %s" % (what, path, e))


def main():
    ap = argparse.ArgumentParser(description="Assemble a PSD report from locked parts.")
    ap.add_argument("--css", required=True, help="path to report.css (canonical CSS)")
    ap.add_argument("--shell", required=True, help="path to report-shell.html (fixed shell)")
    ap.add_argument("--body", required=True, help="path to the agent's body fragment")
    ap.add_argument("--tokens", required=True, help="path to tokens.json (header/footer values)")
    ap.add_argument("--out", required=True, help="path to write the assembled report")
    args = ap.parse_args()

    shell = read(args.shell, "shell")
    css = read(args.css, "css")
    body = read(args.body, "body")
    raw_tokens = read(args.tokens, "tokens")

    # the CSS must be the canonical, fingerprinted stylesheet
    if FINGERPRINT not in css:
        die("%s is missing the %r fingerprint — not the canonical stylesheet." % (args.css, FINGERPRINT))

    try:
        tokens = json.loads(raw_tokens)
    except json.JSONDecodeError as e:
        die("tokens JSON is invalid: %s" % e)
    if not isinstance(tokens, dict):
        die("tokens JSON must be an object of KEY -> value.")

    # 2 + 3: inject CSS and body (literal string replacement)
    if CSS_MARKER not in shell:
        die("shell is missing the CSS marker %r." % CSS_MARKER)
    if BODY_MARKER not in shell:
        die("shell is missing the body marker %r." % BODY_MARKER)
    doc = shell.replace(CSS_MARKER, css).replace(BODY_MARKER, body)

    # 4: substitute every provided token
    for key, val in tokens.items():
        doc = doc.replace("{{%s}}" % key, str(val))

    # 5: fail closed if any placeholder remains (shell OR body)
    leftover = TOKEN_RE.findall(doc)
    if leftover:
        uniq = sorted(set(leftover))
        die("unfilled placeholders remain (%d): %s\n"
            "  → fill these in tokens.json (header/footer) or in the body fragment (modules), then re-run."
            % (len(uniq), ", ".join(uniq)))

    # 6: assert the CSS + canonical header survived assembly
    for needle in (FINGERPRINT, 'class="flagstrip"', 'class="hero"'):
        if needle not in doc:
            die("assembled output is missing required marker %r — header/CSS not present." % needle)

    try:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(doc)
    except OSError as e:
        die("cannot write --out %s: %s" % (args.out, e))

    sys.stderr.write("assemble_report: OK -> %s (%d bytes)\n" % (args.out, len(doc)))


if __name__ == "__main__":
    main()
