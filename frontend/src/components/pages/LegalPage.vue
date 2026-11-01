<script setup lang="ts">
import { computed } from 'vue'
import DefaultLayout from '../templates/DefaultLayout.vue'
import { useHashView } from '../../composables/useHashView'

// Les passages « à compléter » (identité de l'éditeur, hébergeur, contact) sont surlignés.
const props = defineProps<{ kind: 'legal' | 'privacy' }>()

const { closeView, hrefOf } = useHashView()
const UPDATED = '1er novembre 2026'
const title = computed(() => (props.kind === 'legal' ? 'Mentions légales' : 'Politique de confidentialité'))
</script>

<template>
  <DefaultLayout>
    <v-container class="py-8 py-md-12">
      <v-card class="legal mx-auto pa-6 pa-sm-10">
        <v-btn variant="text" prepend-icon="mdi-arrow-left" class="mb-4 ml-n3" @click="closeView">Retour</v-btn>
        <h1 class="text-h5 font-weight-bold mb-1">{{ title }}</h1>
        <p class="text-caption text-medium-emphasis mb-8">Dernière mise à jour : {{ UPDATED }}</p>

        <template v-if="kind === 'legal'">

          <section>
            <h2>Données utilisées</h2>
            <p>
              Les horaires et les indicateurs de ponctualité proviennent des jeux de données ouverts publiés
              par SNCF, réutilisés conformément à leurs licences respectives. Checkeo est un service
              indépendant, sans lien avec SNCF. Les informations affichées sont fournies à titre indicatif
              et ne sauraient engager la responsabilité de l'éditeur.
            </p>
            <p>
              Fonds de carte : © contributeurs OpenStreetMap et CARTO.
            </p>
          </section>

          <section>
            <h2>Crédits photographiques</h2>
            <p>
              Photo du bandeau : TGV Duplex sur le viaduc de Cize-Bolozon, par Kabelleger / David Gubler,
              sous licence
              <a href="https://creativecommons.org/licenses/by-sa/3.0/" target="_blank" rel="noopener">CC BY-SA 3.0</a>
              (recadrée).
            </p>
          </section>

          <section>
            <h2>Propriété intellectuelle</h2>
            <p>
              La structure du site, ses textes et son interface sont la propriété de l'éditeur, sauf mention
              contraire. Toute reproduction non autorisée est interdite.
            </p>
          </section>

          <section>
            <h2>Données personnelles</h2>
            <p>
              Le traitement de vos données est décrit dans la
              <a :href="hrefOf('privacy')">politique de confidentialité</a>.
            </p>
          </section>
        </template>

        <template v-else>
          <section>
            <h2>Responsable du traitement</h2>
            <p>
              <mark>Checkeo</mark>, joignable à <mark>joragasy@gmail.com</mark>, est
              responsable des traitements décrits ci-dessous.
            </p>
          </section>

          <section>
            <h2>Données collectées</h2>
            <p>Lorsque vous créez un compte ou vous connectez, nous enregistrons :</p>
            <ul>
              <li>votre adresse e-mail et, si vous l'indiquez, votre nom ;</li>
              <li>
                si vous utilisez votre mot de passe : une empreinte chiffrée de celui-ci (scrypt), jamais
                le mot de passe lui-même ;
              </li>
              <li>si vous utilisez Google : votre identifiant Google, votre nom et votre photo de profil ;</li>
              <li>les dates de création du compte et de dernière connexion.</li>
            </ul>
            <p>
              Les trajets que vous recherchez ne sont pas associés à votre compte.
            </p>
          </section>

          <section>
            <h2>Finalité et base légale</h2>
            <p>
              Ces données servent uniquement à créer votre compte, à vous authentifier et à sécuriser
              l'accès au service. Le traitement repose sur l'exécution du service que vous demandez.
              Elles ne sont ni vendues ni utilisées à des fins publicitaires.
            </p>
          </section>

          <section>
            <h2>Cookies</h2>
            <p>
              Checkeo dépose un seul cookie, <code>checkeo_session</code>, strictement nécessaire pour
              maintenir votre session. Il est inaccessible aux scripts de la page et expire après 30 jours
              ou à la déconnexion. Aucun cookie publicitaire ni de mesure d'audience n'est utilisé.
            </p>
          </section>

          <section>
            <h2>Services tiers</h2>
            <ul>
              <li>
                <strong>Google Identity Services</strong> : le bouton « Se connecter avec Google » est
                fourni par Google, qui traite les données de connexion selon sa propre
                <a href="https://policies.google.com/privacy" target="_blank" rel="noopener">politique de confidentialité</a>.
              </li>
              <li>
                <strong>CARTO / OpenStreetMap</strong> : les fonds de carte sont chargés depuis leurs
                serveurs, qui reçoivent votre adresse IP.
              </li>
            </ul>
          </section>

          <section>
            <h2>Durée de conservation</h2>
            <p>
              Les données de compte sont conservées tant que le compte existe. Les sessions expirées sont
              supprimées automatiquement.
            </p>
          </section>

          <section>
            <h2>Vos droits</h2>
            <p>
              Conformément au RGPD, vous pouvez accéder à vos données, les rectifier, demander leur
              suppression ou la suppression de votre compte, et vous opposer à leur traitement, en écrivant à
              <mark>joragasy@gmail.com</mark>. Vous pouvez également introduire une réclamation
              auprès de la <a href="https://www.cnil.fr" target="_blank" rel="noopener">CNIL</a>.
            </p>
          </section>
        </template>
      </v-card>
    </v-container>
  </DefaultLayout>
</template>

<style scoped>
.legal {
  max-width: 820px;
}
section + section {
  margin-top: 28px;
}
h2 {
  font-size: 1.05rem;
  font-weight: 700;
  margin-bottom: 8px;
}
p,
li {
  font-size: 0.95rem;
  line-height: 1.65;
}
p + p {
  margin-top: 8px;
}
ul {
  padding-left: 1.25rem;
  margin: 8px 0;
}
a {
  color: rgb(var(--v-theme-primary));
}
mark {
  background: rgba(var(--v-theme-warning), 0.18);
  color: inherit;
  border-radius: 4px;
  padding: 0 4px;
}
code {
  font-size: 0.875em;
}
</style>
