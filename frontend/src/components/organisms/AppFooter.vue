<script setup lang="ts">
import { useHashView } from '../../composables/useHashView'

const { hrefOf } = useHashView()
const year = new Date().getFullYear()
</script>

<template>
  <v-footer border color="surface" class="d-block py-3 px-4">
    <div class="page mx-auto">
      <div class="footer-top">
        <nav class="links" aria-label="Informations légales">
          <a :href="hrefOf('legal')">Mentions légales</a>
          <a :href="hrefOf('privacy')">Confidentialité</a>
        </nav>

        <p class="text-caption text-medium-emphasis mb-0 copyright">
          © {{ year }} Checkeo. Tous droits réservés.
        </p>
      </div>
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
  align-items: baseline;
  justify-content: space-between;
  gap: 8px 24px;
}
.links {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 24px;
}
.copyright {
  margin-left: auto;
  text-align: right;
}
.links a,
.copyright {
  line-height: 1.5;
}
.links a {
  font-size: 0.8125rem;
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
  .footer-top {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
  .links {
    justify-content: center;
  }
  .copyright {
    margin-left: 0;
    text-align: center;
  }
}
</style>
