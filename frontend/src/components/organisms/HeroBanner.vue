<script setup lang="ts">
// overlap : la carte de recherche chevauche le bas du bandeau (page de l'application).
withDefaults(defineProps<{ overlap?: boolean }>(), { overlap: true })
</script>

<template>
  <section class="hero" :class="{ 'hero--overlap': overlap }">
    <div class="hero-bg" role="img" aria-label="TGV Duplex sur le viaduc de Cize-Bolozon, au-dessus de l'Ain" />
    <div class="hero-inner page mx-auto">
      <h1 class="hero-title">Votre trajet, en un coup d'œil</h1>
      <p class="hero-sub">Trains directs et ponctualité réelle.</p>
      <slot />
    </div>
    <a
      class="hero-credit"
      href="https://commons.wikimedia.org/wiki/File:SNCF_TGV_Duplex_Viaduc_de_Cize_-_Bolozon.jpg"
      target="_blank" rel="noopener"
    >Photo : Kabelleger / David Gubler</a>
  </section>
</template>

<style scoped>
.page {
  max-width: 1280px;
}
/* Bandeau photo : la carte de recherche vient chevaucher son bas. */
.hero {
  position: relative;
  height: 320px;
  overflow: hidden;
  color: #fff;
}
.hero-bg {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(to bottom, rgba(0, 0, 0, 0.05) 0%, rgba(0, 0, 0, 0.2) 45%, rgba(0, 0, 0, 0.6) 100%),
    url('/hero-viaduc-cize.jpg');
  background-size: cover;
  background-position: center 55%;
}
.hero-inner {
  position: relative;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  padding: 0 16px 40px;
}
.hero--overlap .hero-inner {
  padding-bottom: 96px;
}
.hero-title {
  font-size: clamp(1.6rem, 4vw, 2.75rem);
  font-weight: 800;
  line-height: 1.1;
  text-shadow: 0 2px 12px rgba(0, 0, 0, 0.45);
  max-width: 18em;
}
.hero-sub {
  margin-top: 6px;
  font-size: clamp(0.95rem, 1.6vw, 1.15rem);
  text-shadow: 0 1px 8px rgba(0, 0, 0, 0.5);
}
.hero-credit {
  position: absolute;
  right: 8px;
  top: 6px;
  font-size: 10px;
  color: rgba(255, 255, 255, 0.85) !important;
  text-decoration: none;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.7);
}
.hero-credit:hover {
  text-decoration: underline;
}
@media (max-width: 599px) {
  .hero {
    height: 250px;
  }
  .hero-bg {
    background-image:
      linear-gradient(to bottom, rgba(0, 0, 0, 0.05) 0%, rgba(0, 0, 0, 0.25) 45%, rgba(0, 0, 0, 0.65) 100%),
      url('/hero-viaduc-cize-960.jpg');
    background-position: 40% 55%;
  }
  .hero-inner {
    padding-bottom: 28px;
  }
  .hero--overlap .hero-inner {
    padding-bottom: 88px;
  }
}
a {
  color: rgb(var(--v-theme-primary));
}
</style>
