"""The technical appendix shared by every project page.

Each page passes its own specifics; the structure and markup are common so
the five pages read as one body of work rather than five write-ups.
"""
import html


def _esc(s):
    return html.escape(s, quote=False)


def section(*, stack, steps, code, code_caption, checks, repro, repo_path):
    """Render the Build notes section.

    stack: [(label, description)]      the tools, and why each one
    steps: [str]                       the pipeline, in order
    code:  str                         the load-bearing query or function
    checks:[str]                       what was verified, not assumed
    repro: str                         the commands that rebuild the page
    """
    # dt and dd are the grid items themselves; wrapping them in a div would
    # make the wrapper the item and collapse both into one column
    rows = '\n    '.join(f'<dt>{_esc(l)}</dt><dd>{d}</dd>' for l, d in stack)
    step_items = '\n    '.join(f'<li>{s}</li>' for s in steps)
    check_items = '\n    '.join(f'<li>{c}</li>' for c in checks)

    return f'''<h2>Build notes</h2>
<p>What this page is made of, and how to rebuild it. The source lives in
<a href="https://github.com/samuel13-cell/samuel13-cell.github.io/tree/main/{repo_path}">{repo_path}</a>.</p>

<dl class="stack">
    {rows}
</dl>

<h3 class="sub">Pipeline</h3>
<ol class="steps">
    {step_items}
</ol>

<h3 class="sub">{_esc(code_caption)}</h3>
<pre><code>{code}</code></pre>

<h3 class="sub">What was checked</h3>
<ul class="checks">
    {check_items}
</ul>

<h3 class="sub">Reproducing it</h3>
<pre><code>{_esc(repro)}</code></pre>'''
