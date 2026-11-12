#!/usr/bin/env python3
"""Refresh one static DEV card. Standard library only; existing content survives errors."""
from datetime import datetime
from html import escape, unescape
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
import argparse
import json
import re
import sys

START = '<!-- latest-dev:start -->'
END = '<!-- latest-dev:end -->'
ANCHOR = '<div class="articles">'
CSS_START = '/* latest-dev:start */'
CSS_END = '/* latest-dev:end */'
CSS = '''/* latest-dev:start */
.latest-dev{display:grid;grid-template-columns:180px minmax(0,1fr);gap:30px;border:1px solid var(--paper-line);border-radius:4px;padding:28px;margin:0 0 36px;background:rgba(255,255,255,.28);color:var(--dark)}
.latest-dev:hover{color:var(--paper-link);border-color:var(--paper-link)}
.latest-dev-label{font-family:var(--mono);font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:var(--paper-link);margin-bottom:13px;display:block}
.latest-dev-meta{font-family:var(--mono);font-size:10px;color:var(--paper-muted);line-height:1.8;display:block}
.latest-dev h3{font-size:29px;line-height:1.25;letter-spacing:-.7px;margin:0 0 13px;overflow-wrap:anywhere}
.latest-dev p{font-size:14px;color:var(--paper-muted);line-height:1.8;margin:0 0 19px;overflow-wrap:anywhere}
.latest-dev .article-link{display:inline-block}
.articles{grid-template-columns:repeat(auto-fit,minmax(min(100%,250px),1fr))}
@media(max-width:720px){.latest-dev{grid-template-columns:1fr;gap:17px;padding:22px;margin-bottom:30px}.latest-dev-label{margin-bottom:7px}.latest-dev h3{font-size:25px}.latest-dev p{font-size:13px}.articles{grid-template-columns:1fr}}
/* latest-dev:end */'''


def text(value, maximum):
    if not isinstance(value, str):
        raise ValueError('Missing text field in DEV response')
    value = ' '.join(unescape(value).split())
    value = value.replace('—', ':').replace('–', '-').replace('--', ':')
    if len(value) > maximum:
        value = value[:maximum - 1].rstrip() + '…'
    return value


def published(value):
    if not isinstance(value, str):
        raise ValueError('Missing publication timestamp')
    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if dt.tzinfo is None:
        raise ValueError('Publication timestamp has no timezone')
    return dt


def normalise(rows):
    if not isinstance(rows, list) or not rows:
        raise ValueError('DEV returned no published articles')
    valid = []
    for row in rows:
        if not isinstance(row, dict) or row.get('user', {}).get('username') != 'ptzivras':
            continue
        if not row.get('published_at'):
            continue
        dt = published(row['published_at'])
        url = row.get('url', '')
        parts = urlsplit(url)
        if parts.scheme != 'https' or parts.netloc != 'dev.to' or not parts.path.startswith('/ptzivras/'):
            raise ValueError('Unexpected article URL')
        item = {'title': text(row.get('title'), 240),
                'description': text(row.get('description', ''), 360),
                'url': url, 'published_at': dt.isoformat()}
        if not item['title']:
            raise ValueError('Empty article title')
        valid.append(item)
    if not valid:
        raise ValueError('No valid published article for ptzivras')
    return max(valid, key=lambda item: published(item['published_at']))


def fetch():
    req = Request('https://dev.to/api/articles?username=ptzivras&per_page=5&page=1',
                  headers={'Accept': 'application/vnd.forem.api-v1+json',
                           'User-Agent': 'ptzivras-personal-website/1.0'})
    with urlopen(req, timeout=20) as response:
        data = response.read(1_000_001)
        if len(data) > 1_000_000:
            raise ValueError('DEV response exceeds expected size')
    return json.loads(data)


def render(item):
    dt = published(item['published_at'])
    date = f'{dt.day} {dt.strftime("%b %Y")}'
    url = escape(item['url'], quote=True)
    title = escape(item['title'])
    desc = escape(item['description'])
    return f'''{START}
      <a class="latest-dev" href="{url}">
        <div><span class="latest-dev-label">Latest on DEV</span><time class="latest-dev-meta" datetime="{dt.date().isoformat()}">{date}</time></div>
        <div><h3>{title}</h3><p>{desc}</p><span class="article-link">Read on DEV <svg class="arrow-icon" aria-hidden="true" viewBox="0 0 16 16"><path d="M3 13 13 3M4 3h9v9"/></svg></span></div>
      </a>
      {END}'''


def patch_html(source, item):
    if source.count(START) != source.count(END) or source.count(START) > 1:
        raise ValueError('Latest DEV markers are malformed; no files changed')
    if source.count(ANCHOR) != 1 or 'id="writing"' not in source:
        raise ValueError('Expected one curated articles grid; no files changed')
    block = render(item)
    if START in source:
        pattern = re.escape(START) + r'.*?' + re.escape(END)
        source = re.sub(pattern, lambda match: block, source, count=1, flags=re.S)
    else:
        source = source.replace(ANCHOR, block + '\n      ' + ANCHOR, 1)
    def mark(match):
        opening = match.group(0)
        managed = 'data-dev-duplicate="true"' in opening
        if managed:
            opening = opening.replace(' data-dev-duplicate="true"', '')
            opening = re.sub(r'\s+hidden(?:="[^"]*")?', '', opening)
        href = re.search(r'href="([^"]+)"', opening)
        if href and unescape(href[1]) == item['url'] and not re.search(r'\shidden(?:\s|=|>)', opening):
            opening = opening[:-1] + ' hidden data-dev-duplicate="true">'
        return opening
    return re.sub(r'<a\b(?=[^>]*\bclass="article")[^>]*>', mark, source)


def refresh(root, rows=None):
    index = root / 'public/index.html'
    styles = root / 'public/styles.css'
    cache = root / 'data/latest-dev.json'
    source = index.read_text()
    css = styles.read_text()
    item = normalise(fetch() if rows is None else rows)
    if cache.exists():
        previous = json.loads(cache.read_text())
        if published(item['published_at']) < published(previous['published_at']):
            raise ValueError('DEV response is older than the cached article; keeping existing card')
    output = patch_html(source, item)
    if css.count(CSS_START) != css.count(CSS_END) or css.count(CSS_START) > 1:
        raise ValueError('Latest DEV CSS markers are malformed; no files changed')
    if CSS_START in css:
        css = re.sub(re.escape(CSS_START) + '.*?' + re.escape(CSS_END), lambda m: CSS, css, flags=re.S)
    else:
        css = css.rstrip() + '\n\n' + CSS + '\n'
    serialised = json.dumps(item, ensure_ascii=False, indent=2) + '\n'
    changed = source != output or styles.read_text() != css or not cache.exists() or cache.read_text() != serialised
    # All fetch/validation/rendering work finishes before any existing file is touched.
    if source != output:
        index.write_text(output)
    if styles.read_text() != css:
        styles.write_text(css)
    cache.parent.mkdir(parents=True, exist_ok=True)
    if not cache.exists() or cache.read_text() != serialised:
        cache.write_text(serialised)
    return changed, item


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        changed, item = refresh(args.root)
    except Exception as error:
        print(f'Latest DEV refresh failed; previous content retained: {error}', file=sys.stderr)
        return 1
    print(('Updated: ' if changed else 'Unchanged: ') + item['title'])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
