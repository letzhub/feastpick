/* FeastPick SPA */
(function () {
  const NAME_KEY = 'feastpick_name'
  const app = document.getElementById('app')
  const toastEl = document.getElementById('toast')
  let toastTimer = null
  let pollTimer = null
  let currentEvent = null
  let lastJson = ''
  let metaCache = null

  const DEFAULT_ICONS = ['🍽️', '🥂', '🍷', '🍺', '☕', '🥤', '🥗', '🍲', '🥘', '🍖', '🦃', '🍝', '🍰', '🥧', '🍮', '🧀', '🥖', '🍿', '🎄', '✨', '🔥', '❄️', '🎁', '⭐']
  const DEFAULT_TAGS = [
    { id: 'vegan', label: 'Vegan', icon: '🌱' },
    { id: 'alcoholic', label: 'Alcohol', icon: '🍷' },
    { id: 'fish', label: 'Fish', icon: '🐟' },
    { id: 'meat', label: 'Meat', icon: '🥩' }
  ]

  function toast (msg, isErr) {
    toastEl.textContent = msg
    toastEl.classList.toggle('err', !!isErr)
    toastEl.classList.add('show')
    clearTimeout(toastTimer)
    toastTimer = setTimeout(() => toastEl.classList.remove('show'), 2800)
  }

  function getName () {
    return (localStorage.getItem(NAME_KEY) || '').trim()
  }
  function setName (n) {
    localStorage.setItem(NAME_KEY, n.trim())
  }

  function esc (s) {
    return String(s ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
  }

  async function loadMeta () {
    if (metaCache) return metaCache
    try {
      metaCache = await api('/api/meta')
    } catch {
      metaCache = { category_icons: DEFAULT_ICONS, tags: DEFAULT_TAGS }
    }
    return metaCache
  }

  function tagMeta (id) {
    const tags = (metaCache && metaCache.tags) || DEFAULT_TAGS
    return tags.find(t => t.id === id) || { id, label: id, icon: '🏷️' }
  }

  function tagsHtml (tags) {
    if (!tags || !tags.length) return ''
    return tags.map(id => {
      const t = tagMeta(id)
      return `<span class="tag tag-${esc(id)}" title="${esc(t.label)}">${esc(t.icon)} ${esc(t.label)}</span>`
    }).join('')
  }

  function iconPickerHtml (selected, nameAttr) {
    const icons = (metaCache && metaCache.category_icons) || DEFAULT_ICONS
    const sel = selected || '🍽️'
    return `
      <div class="icon-picker" data-name="${esc(nameAttr || 'icon')}">
        ${icons.map(ic => `
          <button type="button" class="icon-pick ${ic === sel ? 'selected' : ''}" data-icon="${esc(ic)}" title="${esc(ic)}">${ic}</button>
        `).join('')}
        <input type="hidden" class="icon-value" name="${esc(nameAttr || 'icon')}" value="${esc(sel)}" />
      </div>`
  }

  function tagPickerHtml (selected, className) {
    const tags = (metaCache && metaCache.tags) || DEFAULT_TAGS
    const set = new Set(selected || [])
    return `
      <div class="tag-picker ${className || ''}">
        ${tags.map(t => `
          <button type="button" class="tag-pick ${set.has(t.id) ? 'selected' : ''}" data-tag="${esc(t.id)}">
            <span class="ti">${esc(t.icon)}</span>${esc(t.label)}
          </button>
        `).join('')}
      </div>`
  }

  function bindIconPicker (root) {
    root.querySelectorAll('.icon-picker').forEach(picker => {
      picker.querySelectorAll('.icon-pick').forEach(btn => {
        btn.addEventListener('click', () => {
          picker.querySelectorAll('.icon-pick').forEach(b => b.classList.remove('selected'))
          btn.classList.add('selected')
          const hidden = picker.querySelector('.icon-value')
          if (hidden) hidden.value = btn.dataset.icon
        })
      })
    })
  }

  function bindTagPicker (root) {
    root.querySelectorAll('.tag-picker').forEach(picker => {
      picker.querySelectorAll('.tag-pick').forEach(btn => {
        btn.addEventListener('click', () => btn.classList.toggle('selected'))
      })
    })
  }

  function selectedTags (picker) {
    if (!picker) return []
    return [...picker.querySelectorAll('.tag-pick.selected')].map(b => b.dataset.tag)
  }

  function route () {
    const path = location.pathname.replace(/\/+$/, '') || '/'
    stopPoll()
    if (path === '/' || path === '') return renderHome()
    if (path === '/new') return renderCreate()
    const m = path.match(/^\/e\/([^/]+)$/)
    if (m) return renderEvent(m[1])
    app.innerHTML = `<div class="card"><h2>Not found</h2><p class="desc"><a href="/">Back home</a></p></div>`
  }

  async function api (path, opts = {}) {
    const res = await fetch(path, {
      headers: { 'Content-Type': 'application/json', ...(opts.headers || {}) },
      ...opts
    })
    let data = null
    const text = await res.text()
    try { data = text ? JSON.parse(text) : null } catch { data = { detail: text } }
    if (!res.ok) {
      const detail = data?.detail
      const msg = typeof detail === 'string' ? detail : (detail?.msg || res.statusText || 'Request failed')
      const err = new Error(msg)
      err.status = res.status
      throw err
    }
    return data
  }

  function topbar (extra = '') {
    return `
      <header class="topbar">
        <a class="brand" href="/"><span class="logo">🍽️</span> FeastPick</a>
        <span class="pill">Family feast planner</span>
        ${extra}
      </header>`
  }

  function renderHome () {
    document.title = 'FeastPick'
    app.innerHTML = `
      ${topbar()}
      <section class="hero">
        <h1>Plan the menu together.<br/>Vote. Claim. Feast.</h1>
        <p class="lead">
          Everyone proposes dishes, marks vegan / alcohol / fish / meat,
          votes for favourites, and sees who added what — and who will bring it.
        </p>
        <div class="hero-actions">
          <a class="btn btn-primary" href="/new">Create a feast</a>
          <a class="btn btn-ghost" href="/e/christmas-eve-demo">Open Christmas demo</a>
        </div>
      </section>
      <div class="features">
        <div class="feature">
          <h3>Category icons & briefs</h3>
          <p>Give each category an icon and a short description so guests know the vibe.</p>
        </div>
        <div class="feature">
          <h3>Dish badges</h3>
          <p>Tag options as 🌱 vegan, 🍷 alcohol, 🐟 fish, or 🥩 meat at a glance.</p>
        </div>
        <div class="feature">
          <h3>Fair voting</h3>
          <p>Each person picks up to 2 options per category. Live tally of who chose what.</p>
        </div>
      </div>
      <p class="footer-note">FeastPick · built for family gatherings</p>
    `
  }

  async function renderCreate () {
    document.title = 'New feast · FeastPick'
    await loadMeta()
    const defaultDate = new Date()
    defaultDate.setMonth(11)
    defaultDate.setDate(24)
    if (defaultDate < new Date()) defaultDate.setFullYear(defaultDate.getFullYear() + 1)
    const d = defaultDate.toISOString().slice(0, 10)

    app.innerHTML = `
      ${topbar(`<a class="btn btn-ghost btn-sm" href="/">Home</a>`)}
      <div class="card">
        <h2>Create a feast</h2>
        <p class="desc">Share one link with the family. They join with just a first name.</p>
        <form id="create-form">
          <div class="field-row">
            <div class="field">
              <label>Title</label>
              <input name="title" required maxlength="120" placeholder="Christmas Eve Family Meal" value="Family Feast" />
            </div>
            <div class="field">
              <label>Date</label>
              <input name="date" type="date" required value="${d}" />
            </div>
          </div>
          <div class="field">
            <label>Max votes per category (per person)</label>
            <select name="max_votes">
              <option value="1">1</option>
              <option value="2" selected>2</option>
              <option value="3">3</option>
            </select>
          </div>
          <label>Categories</label>
          <div id="cat-list"></div>
          <button type="button" class="btn btn-ghost btn-sm" id="add-cat">+ Category</button>
          <div style="margin-top:1.25rem">
            <button type="submit" class="btn btn-primary">Create & open board</button>
          </div>
        </form>
      </div>
    `

    const list = document.getElementById('cat-list')
    const starters = [
      { name: 'Drinks', description: 'What should we pour? Soft drinks, wine, coffee…', icon: '🥂' },
      { name: 'Main dishes', description: 'Centrepiece courses. Tag meat / fish / vegan on each option.', icon: '🍽️' },
      { name: 'Desserts', description: 'Sweet finish — pies, cakes, fruit.', icon: '🍰' },
      { name: 'Sides & extras', description: 'Salads, breads, cheeses, snacks.', icon: '🥗' }
    ]

    function catRow (c = { name: '', description: '', icon: '🍽️' }) {
      const el = document.createElement('div')
      el.className = 'cat-editor'
      el.innerHTML = `
        <button type="button" class="btn btn-danger btn-sm rm" title="Remove">✕</button>
        <div class="field">
          <label>Icon</label>
          ${iconPickerHtml(c.icon || '🍽️')}
        </div>
        <div class="field">
          <label>Name</label>
          <input class="cn" required maxlength="80" value="${esc(c.name)}" placeholder="Category name" />
        </div>
        <div class="field" style="margin-bottom:0">
          <label>Description</label>
          <textarea class="cd" maxlength="500" placeholder="Optional brief for guests">${esc(c.description)}</textarea>
        </div>
      `
      el.querySelector('.rm').onclick = () => {
        if (list.children.length <= 1) { toast('Keep at least one category', true); return }
        el.remove()
      }
      list.appendChild(el)
      bindIconPicker(el)
    }
    starters.forEach(catRow)
    document.getElementById('add-cat').onclick = () => catRow()

    document.getElementById('create-form').onsubmit = async (e) => {
      e.preventDefault()
      const fd = new FormData(e.target)
      const categories = [...list.querySelectorAll('.cat-editor')].map(row => ({
        name: row.querySelector('.cn').value.trim(),
        description: row.querySelector('.cd').value.trim(),
        icon: row.querySelector('.icon-value')?.value || '🍽️'
      })).filter(c => c.name)
      if (!categories.length) { toast('Add a category', true); return }
      try {
        const ev = await api('/api/events', {
          method: 'POST',
          body: JSON.stringify({
            title: fd.get('title'),
            event_date: fd.get('date'),
            max_votes: Number(fd.get('max_votes')),
            categories
          })
        })
        location.href = `/e/${ev.slug}`
      } catch (err) {
        toast(err.message || 'Could not create', true)
      }
    }
  }

  function votesUsed (event, categoryId, name) {
    if (!name) return 0
    const cat = event.categories.find(c => c.id === categoryId)
    if (!cat) return 0
    const lower = name.toLowerCase()
    let n = 0
    for (const o of cat.options) {
      if (o.voters.some(v => v.toLowerCase() === lower)) n++
    }
    return n
  }

  function hasVoted (opt, name) {
    if (!name) return false
    const lower = name.toLowerCase()
    return opt.voters.some(v => v.toLowerCase() === lower)
  }

  function formatDate (iso) {
    try {
      const d = new Date(iso + 'T12:00:00')
      return d.toLocaleDateString(undefined, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
    } catch {
      return iso
    }
  }

  function legendHtml () {
    const tags = (metaCache && metaCache.tags) || DEFAULT_TAGS
    return `<div class="legend" aria-label="Badge legend">
      ${tags.map(t => `<span>${esc(t.icon)} ${esc(t.label)}</span>`).join('')}
    </div>`
  }

  function renderEventView (event, name) {
    currentEvent = event
    document.title = `${event.title} · FeastPick`
    const shareUrl = `${location.origin}/e/${event.slug}`

    const catsHtml = event.categories.map(cat => {
      const used = votesUsed(event, cat.id, name)
      const icon = cat.icon || '🍽️'
      const optionsHtml = cat.options.length
        ? cat.options.map(opt => {
          const voted = hasVoted(opt, name)
          const canVote = !!name && (voted || used < event.max_votes)
          const isBringer = name && opt.brought_by && opt.brought_by.toLowerCase() === name.toLowerCase()
          const canBring = name && !opt.brought_by
          const canDelete = name && opt.added_by.toLowerCase() === name.toLowerCase() && !opt.brought_by
          const canEditTags = false
          return `
            <div class="option" data-opt="${esc(opt.id)}">
              <div class="vote-badge ${opt.vote_count > 0 ? 'hot' : ''}">${opt.vote_count}</div>
              <div>
                <p class="option-title">${esc(opt.name)}
                  ${tagsHtml(opt.tags)}
                  ${opt.brought_by ? `<span class="tag tag-bring">🙋 ${esc(opt.brought_by)}</span>` : ''}
                </p>
                <p class="option-meta">
                  Added by <span class="who">${esc(opt.added_by)}</span>
                  ${opt.voters.length
                    ? ` · Chose: <span class="who">${opt.voters.map(esc).join(', ')}</span>`
                    : ' · No votes yet'}
                </p>
              </div>
              <div class="option-actions">
                ${name ? `
                  <button type="button" class="btn btn-sm ${voted ? 'btn-mint active' : 'btn-ghost'} btn-vote"
                    data-id="${esc(opt.id)}" data-vote="${voted ? '0' : '1'}"
                    ${!canVote && !voted ? 'disabled' : ''}
                    title="${voted ? 'Remove vote' : (canVote ? 'Vote' : 'Vote limit reached')}">
                    ${voted ? 'Voted' : 'Vote'}
                  </button>
                  ${canBring ? `<button type="button" class="btn btn-sm btn-ghost btn-bring" data-id="${esc(opt.id)}" data-bring="1">I'll bring</button>` : ''}
                  ${isBringer ? `<button type="button" class="btn btn-sm btn-mint btn-bring" data-id="${esc(opt.id)}" data-bring="0">Release</button>` : ''}
                  ${canDelete ? `<button type="button" class="btn btn-sm btn-danger btn-del" data-id="${esc(opt.id)}">Delete</button>` : ''}
                ` : `<span class="meta">Join to vote</span>`}
              </div>
            </div>`
        }).join('')
        : `<p class="empty">No options yet — be the first to add one.</p>`

      return `
        <section class="card" data-cat="${esc(cat.id)}">
          <div class="cat-head">
            <div>
              <div class="cat-title-row">
                <span class="cat-icon" aria-hidden="true">${esc(icon)}</span>
                <h2>${esc(cat.name)}</h2>
              </div>
              ${cat.description ? `<p class="desc">${esc(cat.description)}</p>` : `<p class="desc" style="opacity:.6">No description</p>`}
            </div>
            ${name ? `<div class="votes-used">Your votes <em>${used}/${event.max_votes}</em></div>` : ''}
          </div>
          ${optionsHtml}
          ${name ? `
            <div class="add-block">
              <div class="add-row">
                <input class="new-opt" maxlength="120" placeholder="Add a choice…" />
                <button type="button" class="btn btn-primary btn-sm btn-add-opt" data-cat="${esc(cat.id)}">Add</button>
              </div>
              <label style="margin-top:0.55rem">Badges (optional)</label>
              ${tagPickerHtml([], 'new-opt-tags')}
            </div>
          ` : ''}
        </section>`
    }).join('')

    app.innerHTML = `
      ${topbar(`<a class="btn btn-ghost btn-sm" href="/new">New feast</a>`)}
      <section class="hero" style="padding:1.35rem 1.5rem">
        <h1 style="font-size:1.55rem">${esc(event.title)}</h1>
        <p class="meta" style="margin:0.35rem 0 0">${esc(formatDate(event.event_date))} · up to <strong>${event.max_votes}</strong> vote(s) per category</p>
        <div class="share-box">
          <input readonly value="${esc(shareUrl)}" id="share-url" />
          <button type="button" class="btn btn-ghost btn-sm" id="copy-link">Copy link</button>
        </div>
      </section>

      <div class="identity" id="identity">
        ${name ? `
          <span>Signed in as <strong>${esc(name)}</strong></span>
          <button type="button" class="btn btn-ghost btn-sm" id="logout">Change name</button>
        ` : `
          <label style="margin:0">Your name</label>
          <input id="name-input" maxlength="60" placeholder="First name" />
          <button type="button" class="btn btn-primary btn-sm" id="login">Join board</button>
        `}
      </div>

      ${legendHtml()}

      ${name ? `
        <div class="card">
          <h2 style="font-size:1rem">Add a category</h2>
          <p class="desc" style="margin-bottom:0.75rem">Pick an icon and optional description.</p>
          <div class="field">
            <label>Icon</label>
            ${iconPickerHtml('🍽️', 'new-cat-icon')}
          </div>
          <div class="field-row">
            <div class="field"><label>Name</label><input id="new-cat-name" maxlength="80" placeholder="e.g. Appetizers" /></div>
            <div class="field"><label>Description</label><input id="new-cat-desc" maxlength="500" placeholder="Optional brief" /></div>
          </div>
          <button type="button" class="btn btn-ghost btn-sm" id="add-category">Add category</button>
        </div>
      ` : ''}

      ${catsHtml || '<div class="card"><p class="empty">No categories yet.</p></div>'}
      <p class="footer-note">Polling quietly for updates · FeastPick</p>
    `

    bindEventHandlers(event)
  }

  function bindEventHandlers (event) {
    const name = getName()
    bindIconPicker(app)
    bindTagPicker(app)

    document.getElementById('copy-link')?.addEventListener('click', async () => {
      const url = document.getElementById('share-url').value
      try {
        await navigator.clipboard.writeText(url)
        toast('Link copied')
      } catch {
        document.getElementById('share-url').select()
        toast('Select and copy the link')
      }
    })

    document.getElementById('login')?.addEventListener('click', () => {
      const n = document.getElementById('name-input').value.trim()
      if (!n) { toast('Enter your name', true); return }
      setName(n)
      renderEventView(currentEvent || event, n)
    })
    document.getElementById('name-input')?.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') document.getElementById('login').click()
    })
    document.getElementById('logout')?.addEventListener('click', () => {
      setName('')
      renderEventView(currentEvent || event, '')
    })

    document.getElementById('add-category')?.addEventListener('click', async () => {
      const nm = document.getElementById('new-cat-name').value.trim()
      const ds = document.getElementById('new-cat-desc').value.trim()
      const icon = app.querySelector('#add-category')?.closest('.card')?.querySelector('.icon-value')?.value || '🍽️'
      if (!nm) { toast('Category name required', true); return }
      try {
        const ev = await api(`/api/events/${event.id}/categories`, {
          method: 'POST',
          body: JSON.stringify({ name: nm, description: ds, icon })
        })
        lastJson = JSON.stringify(ev)
        renderEventView(ev, getName())
        toast('Category added')
      } catch (err) { toast(err.message, true) }
    })

    app.querySelectorAll('.btn-add-opt').forEach(btn => {
      btn.addEventListener('click', async () => {
        const catId = btn.dataset.cat
        const card = btn.closest('.card')
        const input = card.querySelector('.new-opt')
        const oname = input.value.trim()
        if (!oname) { toast('Name the option', true); return }
        const tags = selectedTags(card.querySelector('.new-opt-tags'))
        try {
          const ev = await api(`/api/categories/${catId}/options`, {
            method: 'POST',
            body: JSON.stringify({ name: oname, added_by: getName(), tags })
          })
          lastJson = JSON.stringify(ev)
          renderEventView(ev, getName())
          toast('Option added')
        } catch (err) { toast(err.message, true) }
      })
    })
    app.querySelectorAll('.new-opt').forEach(inp => {
      inp.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault()
          inp.closest('.add-block, .add-row')?.querySelector('.btn-add-opt')?.click()
        }
      })
    })

    app.querySelectorAll('.btn-vote').forEach(btn => {
      btn.addEventListener('click', async () => {
        try {
          const ev = await api(`/api/options/${btn.dataset.id}/vote`, {
            method: 'POST',
            body: JSON.stringify({ voter: getName(), vote: btn.dataset.vote === '1' })
          })
          lastJson = JSON.stringify(ev)
          renderEventView(ev, getName())
        } catch (err) { toast(err.message, true) }
      })
    })

    app.querySelectorAll('.btn-bring').forEach(btn => {
      btn.addEventListener('click', async () => {
        try {
          const ev = await api(`/api/options/${btn.dataset.id}/bring`, {
            method: 'POST',
            body: JSON.stringify({ person: getName(), bring: btn.dataset.bring === '1' })
          })
          lastJson = JSON.stringify(ev)
          renderEventView(ev, getName())
        } catch (err) { toast(err.message, true) }
      })
    })

    app.querySelectorAll('.btn-del').forEach(btn => {
      btn.addEventListener('click', async () => {
        if (!confirm('Delete this option?')) return
        try {
          const ev = await api(`/api/options/${btn.dataset.id}`, { method: 'DELETE' })
          lastJson = JSON.stringify(ev)
          renderEventView(ev, getName())
        } catch (err) { toast(err.message, true) }
      })
    })
  }

  function stopPoll () {
    if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
  }

  async function renderEvent (slug) {
    app.innerHTML = `${topbar()}<p class="meta">Loading board…</p>`
    await loadMeta()
    try {
      const ev = await api(`/api/events/${encodeURIComponent(slug)}`)
      lastJson = JSON.stringify(ev)
      renderEventView(ev, getName())
      stopPoll()
      pollTimer = setInterval(async () => {
        if (document.visibilityState === 'hidden') return
        try {
          const fresh = await api(`/api/events/${encodeURIComponent(slug)}`)
          const j = JSON.stringify(fresh)
          if (j !== lastJson) {
            lastJson = j
            const ae = document.activeElement
            if (ae && (ae.tagName === 'INPUT' || ae.tagName === 'TEXTAREA')) return
            renderEventView(fresh, getName())
          }
        } catch { /* silent */ }
      }, 5000)
    } catch (err) {
      app.innerHTML = `
        ${topbar()}
        <div class="card">
          <h2>Board not found</h2>
          <p class="desc">${esc(err.message)}</p>
          <a class="btn btn-primary" href="/">Home</a>
        </div>`
    }
  }

  window.addEventListener('popstate', route)
  document.addEventListener('click', (e) => {
    const a = e.target.closest('a')
    if (!a) return
    const href = a.getAttribute('href')
    if (!href || href.startsWith('http') || href.startsWith('mailto:') || a.target === '_blank') return
    if (href.startsWith('/')) {
      e.preventDefault()
      history.pushState(null, '', href)
      route()
    }
  })

  loadMeta().finally(route)
})()
