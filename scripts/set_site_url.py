#!/usr/bin/env python3
"""Set the chosen public origin and enable search indexing at launch."""
from pathlib import Path
from urllib.parse import urlsplit
from datetime import date
import json
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: python scripts/set_site_url.py https://your-chosen-host")
parts = urlsplit(sys.argv[1])
if (parts.scheme != "https" or not parts.hostname or parts.username or parts.password
        or parts.query or parts.fragment or parts.path not in ("", "/")
        or not re.fullmatch(r"[A-Za-z0-9.-]+(?::[0-9]+)?", parts.netloc)):
    raise SystemExit("Supply the HTTPS origin only, without a path, query or credentials.")
origin = "https://" + parts.netloc.rstrip("/")
public = Path(__file__).resolve().parents[1] / "public"
index = public / "index.html"
html = index.read_text()
html = re.sub(r'\s*<link rel="canonical"[^>]*>', "", html)
html = re.sub(r'\s*<meta property="og:url"[^>]*>', "", html)
html = re.sub(r'\s*<script type="application/ld\+json">.*?</script>', "", html, flags=re.S)
html = html.replace('content="noindex,nofollow"', 'content="index,follow"')
html = re.sub(r'(<meta property="og:image" content=")[^"]+(">)',
              lambda m: m[1] + origin + "/assets/share-preview.png" + m[2], html)
identity = {
    "@context": "https://schema.org", "@type": "Person",
    "name": "Panagis Tzivras", "url": origin + "/",
    "jobTitle": "Data Engineer and GIS Specialist",
    "sameAs": ["https://github.com/ptzivras", "https://dev.to/ptzivras",
               "https://x.com/Panagis_T", "https://bsky.app/profile/panagist.bsky.social"]
}
metadata = ('  <link rel="canonical" href="' + origin + '/">\n'
            '  <meta property="og:url" content="' + origin + '/">\n'
            '  <script type="application/ld+json">' + json.dumps(identity) + '</script>\n')
html = html.replace("</head>", metadata + "</head>")
index.write_text(html)
(public / "robots.txt").write_text("User-agent: *\nAllow: /\nSitemap: " + origin + "/sitemap.xml\n")
(public / "sitemap.xml").write_text(
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    '<url><loc>' + origin + '/</loc><lastmod>' + date.today().isoformat()
    + '</lastmod></url></urlset>\n')
print("Configured launch origin:", origin)
