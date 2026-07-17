<script lang="ts">
  import SiteFooter from "../components/SiteFooter.svelte";
</script>

<main class="privacy-page">
  <header>
    <p class="eyebrow">Privacy</p>
    <h1>Useful signals, without personal profiles.</h1>
    <p>
      Webwoven uses a self-hosted, cookie-free analytics service to understand
      whether the game works—not to identify the people playing it.
    </p>
  </header>

  <section>
    <h2>What is collected</h2>
    <p>
      Anonymous page views may include the page path, referring site, browser,
      operating system, device class, screen size, language, and coarse country.
      URL query strings and hashes are excluded.
    </p>
    <p>
      The game also sends a small fixed set of aggregate events: selected mode,
      round start, round completion, hint use, and route abandonment. Event
      properties are limited to mode, difficulty, atlas category, hint type, and
      coarse completion buckets.
    </p>
  </section>

  <section>
    <h2>What is not collected</h2>
    <p>
      Analytics does not receive names, guest or session identifiers, entity
      identifiers, free-form text, precise route histories, or URL parameters.
      Webwoven does not enable advertising profiles, cross-site tracking,
      heatmaps, session replay, or analytics identity calls.
    </p>
  </section>

  <section>
    <h2>Storage and control</h2>
    <p>
      The analytics service and its database run on Webwoven’s own Hetzner VPS.
      It sets no tracking cookie and stores no raw IP address. Detailed
      analytics are automatically removed after 90 days. If your browser sends
      Do Not Track, Webwoven does not load the analytics script at all.
    </p>
  </section>
</main>

<SiteFooter />
