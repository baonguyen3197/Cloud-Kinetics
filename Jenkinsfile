pipeline {
    agent any

    environment {
        DOCKER_IMAGE = 'index.docker.io/nhqb3197/nhqb-cloud-kinetics:latest'
        GITHUB_CREDENTIALS_ID = 'github-cloud-kinetics'
        DOCKER_CREDENTIALS_ID = 'dockerhub-creds'
    }

    stages {
        stage("Cleanup Workspace") {
            steps {
                cleanWs()
            }
        }

        stage("Checkout from SCM") {
            steps {
                git branch: 'main', credentialsId: "${GITHUB_CREDENTIALS_ID}", url: 'https://github.com/baonguyen3197/Cloud-Kinetics.git'
            }
        }

        stage("Build Docker Image") {
            steps {
                script {
                    sh "docker build -t ${env.DOCKER_IMAGE} ."
                }
            }
        }

        stage("Push Docker Image") {
            steps {
                script {
                    withCredentials([usernamePassword(credentialsId: "${DOCKER_CREDENTIALS_ID}")]) {
                        // sh "docker login -u ${DOCKERHUB_USERNAME} -p ${DOCKERHUB_PASSWORD}"
                        sh "docker push ${env.DOCKER_IMAGE}"
                    }
                }
            }
        }
    }
}