variable "image" {
  type = string
}

job "checkeo-backend" {
  datacenters = ["dc1"]
  type        = "service"

  group "api" {
    count = 1

    # La base est lue sur le host volume rempli par le job checkeo-database.
    volume "checkeo_data" {
      type            = "host"
      source          = "checkeo-data"
      access_mode     = "single-node-multi-writer"
      attachment_mode = "file-system"
      read_only       = true
    }

    network {
      port "http" {
        to     = 8000
        static = 8411
      }
    }

    shutdown_delay = "5s"

    # Au premier déploiement, la base n'existe qu'une fois l'ingestion terminée : on réessaie.
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

      volume_mount {
        volume      = "checkeo_data"
        destination = "/data"
        read_only   = true
      }

      env {
        CHECKEO_DATA_DIR = "/data"
        CHECKEO_CORS     = "http://checkeo.enopt.ovh"
      }

      resources {
        cpu    = 100
        memory = 256
      }
    }
  }
}
