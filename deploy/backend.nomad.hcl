variable "image" {
  type = string
}

job "checkeo-backend" {
  datacenters = ["dc1"]
  type        = "service"

  group "api" {
    count = 1

    network {
      port "http" {
        to     = 8000
        static = 8411
      }
    }

    shutdown_delay = "5s"

    # Au premier déploiement, le schéma n'existe qu'une fois l'ingestion terminée : on réessaie.
    restart {
      attempts = 10
      interval = "30m"
      delay    = "30s"
      mode     = "delay"
    }

    service {
      provider = "nomad"
      name     = "checkeo-backend"
      port     = "http"

      tags = [
        "traefik.enable=true",

        # Router (règle plus longue que celle du frontend : prioritaire sur le même hôte)
        "traefik.http.routers.checkeo-api.rule=Host(`checkeo.enopt.ovh`) && (PathPrefix(`/api`) || Path(`/docs`) || Path(`/openapi.json`))",
        "traefik.http.routers.checkeo-api.entrypoints=web",

        # Service
        "traefik.http.services.checkeo-api.loadbalancer.server.port=8411",
      ]

      check {
        type     = "http"
        path     = "/api/health"
        interval = "10s"
        timeout  = "2s"
      }
    }

    task "api" {
      driver = "docker"

      config {
        image              = var.image
        dns_servers        = ["172.17.0.1"]
        dns_search_domains = ["default.service.nomad"]
        ports              = ["http"]
      }

      # DSN de la base (voir deploy/ingest.nomad.hcl) et identifiant client OAuth Google.
      template {
        destination = "secrets/db.env"
        env         = true
        data        = <<-EOT
          {{ with nomadVar "nomad/jobs/checkeo-backend" }}
          CHECKEO_DATABASE_URL={{ .database_url }}
          CHECKEO_GOOGLE_CLIENT_ID={{ .google_client_id }}
          {{ end }}
        EOT
      }

      env {
        CHECKEO_CORS = "https://checkeo.enopt.ovh"
      }

      resources {
        cpu    = 100
        memory = 256
      }
    }
  }
}
