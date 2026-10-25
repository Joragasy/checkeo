variable "image" {
  type = string
}

job "checkeo-frontend" {
  datacenters = ["dc1"]
  type        = "service"

  group "web" {
    count = 1

    network {
      port "http" {
        to     = 8080
        static = 8410
      }
    }

    shutdown_delay = "5s"

    service {
      provider = "nomad"
      name     = "checkeo-frontend"
      port     = "http"

      tags = [
        "traefik.enable=true",

        # Router
        "traefik.http.routers.checkeo.rule=Host(`checkeo.enopt.ovh`)",
        "traefik.http.routers.checkeo.entrypoints=web",

        # Service
        "traefik.http.services.checkeo.loadbalancer.server.port=8410",
      ]
    }

    task "web" {
      driver = "docker"

      config {
        image              = var.image
        dns_servers        = ["172.17.0.1"]
        dns_search_domains = ["default.service.nomad"]
        ports              = ["http"]
      }

      resources {
        cpu    = 50
        memory = 32
      }
    }
  }
}
