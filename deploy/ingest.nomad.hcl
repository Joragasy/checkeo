# Télécharge les données SNCF et (re)construit le schéma checkeo de la base PostgreSQL.
# Job batch : `nomad job run` le relance, c'est aussi ainsi qu'on rafraîchit les données.
# Le nouveau schéma ne remplace l'ancien qu'une fois entièrement chargé : un échec n'y touche pas.
#
# DSN de la base, à enregistrer une fois pour chacun des deux jobs (un job ne lit que ses variables) :
#
#   nomad var put nomad/jobs/checkeo-ingest  database_url='postgresql://utilisateur:motdepasse@hôte:5432/base'
#   nomad var put nomad/jobs/checkeo-backend database_url='postgresql://utilisateur:motdepasse@hôte:5432/base'

variable "image" {
  type = string
}

job "checkeo-ingest" {
  datacenters = ["dc1"]
  type        = "batch"

  group "ingest" {
    count = 1

    restart {
      attempts = 2
      interval = "30m"
      delay    = "1m"
      mode     = "fail"
    }

    reschedule {
      attempts  = 0
      unlimited = false
    }

    task "ingest" {
      driver = "docker"

      config {
        image              = var.image
        dns_servers        = ["172.17.0.1"]
        dns_search_domains = ["default.service.nomad"]
      }

      template {
        destination = "secrets/db.env"
        env         = true
        data        = <<-EOT
          {{ with nomadVar "nomad/jobs/checkeo-ingest" }}CHECKEO_DATABASE_URL={{ .database_url }}{{ end }}
        EOT
      }

      # Données brutes téléchargées dans le répertoire de l'allocation (pas de volume persistant).
      env {
        CHECKEO_DATA_DIR = "${NOMAD_ALLOC_DIR}/data"
      }

      # cpu est une réservation, pas un plafond : l'ingestion utilise le CPU libre du nœud.
      # Pic mesuré : ~620 Mo (avant PostgreSQL, à revérifier).
      resources {
        cpu    = 150
        memory = 786
      }
    }
  }
}
