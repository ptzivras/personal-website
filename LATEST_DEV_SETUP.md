# Latest on DEV : update package

Adds a featured article card above the existing curated DEV selection. Uses the site's current typography and colours. The latest matching curated card is hidden to avoid repetition; it returns automatically when the newest article changes. The curated HTML is preserved.

## Apply in the existing personal-website Codespace

1. Upload `Latest_DEV_Update.zip` to the repository root using the Codespace Explorer.
2. Run these commands from the repository root:

```bash
unzip -o Latest_DEV_Update.zip
python scripts/update_latest_dev.py
```

The script checks the existing layout and adds the article block and styles. It preserves your email, byline, project wording, public metadata and footer. Running it again updates the managed block without inserting a second copy.

3. Review and publish:

```bash
git diff -- public/index.html public/styles.css
git add scripts/update_latest_dev.py .github/workflows/latest-dev.yml data/latest-dev.json public/index.html public/styles.css LATEST_DEV_SETUP.md
git commit -m "Add latest DEV article feature and daily refresh"
git push
```

The ZIP itself does not need to be committed. Keep Cloudflare's build command `exit 0` and output directory `public` unchanged.

## Activate and verify the schedule

The workflow runs daily at 06:17 UTC. Scheduled execution can be delayed; this is not an exact-time delivery guarantee. It also supports manual runs.

After pushing, open the repository on GitHub, select **Actions**, choose **Refresh latest DEV article**, then **Run workflow** on `main`.

If GitHub asks to enable Actions, enable it for this repository. The workflow requests repository-content write permission to commit changes. It uses GitHub's built-in token, so no DEV API key or personal access token is needed. Repository rules or organisation restrictions can still prevent direct pushes; if the push fails, the run log should say so.

Check the first manual run is green. If the article has not changed, no new commit or deployment is expected. When it does change, check that Cloudflare picks up the automated commit and successfully deploys it. Do not treat the whole automatic chain as verified until an article-changing run has reached the live site.

In a public repository, GitHub disables scheduled workflows after 60 days of repository inactivity. Re-enable the workflow if this happens; manual refresh is always available from a Codespace:

```bash
python scripts/update_latest_dev.py
```

Then commit and push any changes.

## Behaviour

- Fetches five public articles for `ptzivras` and chooses the newest publication timestamp.
- Uses title, publication date, DEV description and original DEV URL. It does not fetch or republish the full article body.
- Escapes external text and validates the author and destination URL.
- Normalises long dashes and double hyphens in displayed DEV text to match the site's punctuation preference.
- Stores the last accepted article metadata in `data/latest-dev.json`.
- If DEV fails, returns an error before changing the page. Existing static content remains deployed.
- Refuses to replace a cached article with an older result, or to patch unrecognised/malformed layout markers.
- Makes no commit when the card content has not changed.
- Adds no browser API calls, client JavaScript, dependencies or backend service.

The first article fetched during preparation was **The Map Works. Now Comes the Conversation.**, published 10 November 2026. The script will obtain the actual latest article again when you install it.

## What changes

- `scripts/update_latest_dev.py`: updater, run in Codespaces or GitHub Actions.
- `.github/workflows/latest-dev.yml`: daily and manual refresh.
- `public/index.html`: marked latest article block; managed duplicate visibility.
- `public/styles.css`: marked responsive card styles.
- `data/latest-dev.json`: small public metadata snapshot.

Only the script, workflow and this guide are included in the ZIP. Your current page is patched in place when you run the updater, rather than replaced with an older copy.

## Validation completed before delivery

Tested against the current public repository HTML/CSS: live API extraction, idempotent refresh, text escaping, foreign-URL rejection, API-failure retention, older-response protection, malformed-marker rejection and restoration of the curated card after a newer article appears.

The new card has not yet received a browser layout check or a GitHub-to-Cloudflare end-to-end test. Check it on desktop and mobile after deployment.

References:

- https://developers.forem.com/api/v1
- https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
