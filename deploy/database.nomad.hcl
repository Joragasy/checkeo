# Host volume partagé par checkeo-database (écriture) et checkeo-backend (lecture seule).
# Créez-le une fois, avant le premier lancement de ce job :
#
#   sed -n 's/^#> //p' deploy/database.nomad.hcl | nomad volume create -
#
#> name      = "checkeo-data"
#> type      = "host"
#> plugin_id = "mkdir"
#> node_pool = "default"
#>
#> capability {
#>   access_mode     = "single-node-multi-writer"
#>   attachment_mode = "file-system"
#> }

variable "image" {
  type = string
}

job "checkeo-database" {
  datacenters = ["dc1"]
  type        = "service"

  group "database" {
    count = 1

    volume "checkeo_data" {
      type            = "host"
      source          = "checkeo-data"
      access_mode     = "single-node-multi-writer"
      attachment_mode = "file-system"
    }

    network {
      port "ui" {
        to     = 4214
        static = 8412
      }
    }

    shutdown_delay = "5s"

    service {
      provider = "nomad"
      name     = "checkeo-db"
      port     = "ui"

      tags = [
        "traefik.enable=true",

        # Router
        "traefik.http.routers.checkeo-db.rule=Host(`checkeo-db.enopt.ovh`)",
        "traefik.http.routers.checkeo-db.entrypoints=web",
        "traefik.http.routers.checkeo-db.middlewares=registry-whitelist@file,checkeo-db-headers",

        # L'interface DuckDB n'accepte que des requêtes adressées à localhost
        "traefik.http.middlewares.checkeo-db-headers.headers.customrequestheaders.Host=localhost:4213",
        "traefik.http.middlewares.checkeo-db-headers.headers.customrequestheaders.Origin=http://localhost:4213",

        # Service
        "traefik.http.services.checkeo-db.loadbalancer.server.port=8412",
      ]
    }

    # Télécharge les données SNCF et (re)construit /data/checkeo.duckdb à chaque démarrage.
    # Un échec de téléchargement ne bloque pas le démarrage si une base existe déjà.
    task "ingest" {
      driver = "docker"

      lifecycle {
        hook    = "prestart"
        sidecar = false
      }

      config {
        image              = var.image
        dns_servers        = ["172.17.0.1"]
        dns_search_domains = ["default.service.nomad"]
        command            = "sh"
        args               = ["-c", "python -m checkeo.ingest.run || test -f /data/checkeo.duckdb"]
      }

      volume_mount {
        volume      = "checkeo_data"
        destination = "/data"
      }

      resources {
        cpu    = 1000
        memory = 2048
      }
    }

    task "ui" {
      driver = "docker"

      config {
        image              = var.image
        dns_servers        = ["172.17.0.1"]
        dns_search_domains = ["default.service.nomad"]
        ports              = ["ui"]
      }

      volume_mount {
        volume      = "checkeo_data"
        destination = "/data"
        read_only   = true
      }

      resources {
        cpu    = 300
        memory = 512
      }
    }
  }
}
