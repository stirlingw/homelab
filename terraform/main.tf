terraform {
  required_providers {
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
  }
}

provider "kubernetes" {
  config_path = "~/.kube/config"
}

provider "helm" {
  kubernetes {
    config_path = "~/.kube/config"
  }
  repository_config_path = "/home/stirling/.config/helm/repositories.yaml"
  repository_cache       = "/home/stirling/.cache/helm/repository"
}

# ArgoCD
resource "helm_release" "argocd" {
  name             = "argocd"
  repository       = "https://argoproj.github.io/argo-helm"
  chart            = "argo-cd"
  namespace        = "argocd"
  create_namespace = true
  version          = "7.8.26"
}

# KubeRay Operator (installs CRDs first)
resource "helm_release" "kuberay_operator" {
  name             = "kuberay-operator"
  repository       = "https://ray-project.github.io/kuberay-helm/"
  chart            = "kuberay-operator"
  namespace        = "ray"
  create_namespace = true
  version          = "1.3.0"
}

# Ray Cluster (depends on operator being ready first)
resource "helm_release" "ray" {
  name             = "ray"
  repository       = "https://ray-project.github.io/kuberay-helm/"
  chart            = "ray-cluster"
  namespace        = "ray"
  create_namespace = true
  version          = "1.3.0"
  
  set {
    name  = "head.image.repository"
    value = "stirlingw/ray-xgboost"
  }
  set {
    name  = "head.image.tag"
    value = "2.41.0"
  }
  set {
    name  = "worker.image.repository"
    value = "stirlingw/ray-xgboost"
  }
  set {
    name  = "worker.image.tag"
    value = "2.41.0"
  }

  depends_on = [helm_release.kuberay_operator]
}   

# PostgreSQL for MLflow
resource "helm_release" "postgresql" {
  name             = "postgresql"
  repository       = "oci://registry-1.docker.io/bitnamicharts"
  chart            = "postgresql"
  namespace        = "mlflow"
  create_namespace = true
  version          = "18.5.6"

  set {
    name  = "extraEnvVars.MLFLOW_ALLOW_ORIGIN"
    value = "*"
  }
  set {
    name  = "extraEnvVars.MLFLOW_APP_ALLOWED_HOSTS"
    value = "*"
  }
  set {
    name  = "auth.username"
    value = "mlflow"
  }
  set {
    name  = "auth.password"
    value = "mlflow123"
  }
  set {
    name  = "auth.database"
    value = "mlflow"
  }
}

# MinIO for artifact storage
resource "helm_release" "minio" {
  name             = "minio"
  repository       = "https://charts.min.io/"
  chart            = "minio"
  namespace        = "mlflow"
  create_namespace = true
  version          = "5.4.0"

  set {
    name  = "rootUser"
    value = "minioadmin"
  }
  set {
    name  = "rootPassword"
    value = "minioadmin123"
  }
  set {
    name  = "buckets[0].name"
    value = "mlflow"
  }
  set {
    name  = "buckets[0].policy"
    value = "none"
  }
  set {
    name  = "mode"
    value = "standalone"
  }
  set {
    name  = "resources.requests.memory"
    value = "512Mi"
  }

  depends_on = [helm_release.postgresql]
}

# MLflow
resource "helm_release" "mlflow" {
  name             = "mlflow"
  repository       = "https://community-charts.github.io/helm-charts"
  chart            = "mlflow"
  namespace        = "mlflow"
  create_namespace = true
  version          = "1.8.1"
  
  set {
    name  = "extraEnvVars.MLFLOW_ALLOW_FILESTORE_ARTIFACT_DOWNLOADS"
    value = "true"
  }
  set {
    name  = "extraArgs.gunicorn-opts"
    value = "--forwarded-allow-ips=*"
  }
  set {
    name  = "extraEnvVars.GUNICORN_CMD_ARGS"
    value = "--forwarded-allow-ips=*"
  }

  set {
    name  = "backendStore.postgres.enabled"
    value = "true"
  }
  set {
    name  = "backendStore.postgres.host"
    value = "postgresql.mlflow.svc.cluster.local"
  }
  set {
    name  = "backendStore.postgres.port"
    value = "5432"
  }
  set {
    name  = "backendStore.postgres.database"
    value = "mlflow"
  }
  set {
    name  = "backendStore.postgres.user"
    value = "mlflow"
  }
  set {
    name  = "backendStore.postgres.password"
    value = "mlflow123"
  }
  set {
    name  = "artifactRoot.s3.enabled"
    value = "true"
  }
  set {
    name  = "artifactRoot.s3.bucket"
    value = "mlflow"
  }
  set {
    name  = "artifactRoot.s3.awsAccessKeyId"
    value = "minioadmin"
  }
  set {
    name  = "artifactRoot.s3.awsSecretAccessKey"
    value = "minioadmin123"
  }
  set {
    name  = "extraEnvVars.MLFLOW_S3_ENDPOINT_URL"
    value = "http://minio.mlflow.svc.cluster.local:9000"
  }

  depends_on = [helm_release.minio]
}

resource "helm_release" "prometheus_stack" {
  name             = "prometheus-stack"
  repository       = "https://prometheus-community.github.io/helm-charts"
  chart            = "kube-prometheus-stack"
  namespace        = "monitoring"
  create_namespace = true
  version          = "82.10.4"

  set {
    name  = "grafana.adminPassword"
    value = "homelab123"
  }
  set {
    name  = "prometheus.prometheusSpec.scrapeInterval"
    value = "15s"
  }
  set {
    name  = "grafana.service.type"
    value = "NodePort"
  }
  set {
    name  = "grafana.service.nodePort"
    value = "30300"
  }
  set {
    name  = "prometheus.service.type"
    value = "NodePort"
  }
  set {
    name  = "prometheus.service.nodePort"
    value = "30090"
  }
}

resource "helm_release" "pushgateway" {
  name             = "pushgateway"
  repository       = "https://prometheus-community.github.io/helm-charts"
  chart            = "prometheus-pushgateway"
  namespace        = "monitoring"
  create_namespace = false
  version          = "2.14.0"

  set {
    name  = "service.type"
    value = "ClusterIP"
  }
}
