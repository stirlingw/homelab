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

  depends_on = [helm_release.kuberay_operator]
}   
