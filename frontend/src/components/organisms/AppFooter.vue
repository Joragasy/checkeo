<script setup lang="ts">
import { useHashView } from '../../composables/useHashView'

const { hrefOf } = useHashView()
const year = new Date().getFullYear()
</script>

<template>
  <v-footer border color="surface" class="d-block py-8 px-4">
    <div class="page mx-auto">
      <div class="footer-top">
        <nav class="links" aria-label="Informations légales">
          <a :href="hrefOf('legal')">Mentions légales</a>
          <a :href="hrefOf('privacy')">Confidentialité</a>
        </nav>
      </div>

      <v-divider class="my-5" />

      <p class="text-caption text-medium-emphasis mb-0 footer-bottom">
        © {{ year }} Checkeo. Tous droits réservés.
      </p>
    </div>
  </v-footer>
</template>

<style scoped>
.page {
  max-width: 1280px;
}
.footer-top {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
}
.brand {
  max-width: 420px;
}
.links {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 24px;
  padding-top: 4px;
}
.links a {
  font-size: 0.875rem;
  font-weight: 500;
  color: rgb(var(--v-theme-on-surface));
  opacity: 0.8;
  text-decoration: none;
}
.links a:hover,
.links a:focus-visible {
  color: rgb(var(--v-theme-primary));
  opacity: 1;
  text-decoration: underline;
}
@media (max-width: 599px) {
  .footer-top,
  .footer-bottom {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
  .brand > div {
    justify-content: center;
  }
  .links {
    justify-content: center;
  }
}
</style>
