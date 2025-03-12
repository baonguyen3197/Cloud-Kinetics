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
                    sh "docker build -t ${DOCKER_IMAGE} ."
                }
            }
        }

        stage("Push Docker Image") {
            steps {
                script {
                    withCredentials([usernamePassword(credentialsId: "${DOCKER_CREDENTIALS_ID}", usernameVariable: 'DOCKERHUB_USERNAME', passwordVariable: 'DOCKERHUB_PASSWORD')]) {
                        sh "docker login -u ${DOCKERHUB_USERNAME} -p ${DOCKERHUB_PASSWORD}"
                        sh "docker push ${DOCKER_IMAGE}"
                    }
                }
            }
        }

        // stage('Build & Push with Kaniko') {
        //     steps {
        //         container(name: 'kaniko', shell: '/busybox/sh') {
        //             sh '''#!/busybox/sh
        //             /kaniko/executor --dockerfile `pwd`/Dockerfile --context `pwd` --destination=${DOCKER_IMAGE}
        //             '''
        //         }
        //     }
        // }
        
        // stage('Trigger ArgoCD Sync') {
        //     steps {
        //         withCredentials([string(credentialsId: 'argocd-cred', variable: 'ARGOCD_AUTH_TOKEN')]) {
        //             sh """
        //             curl -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer ${ARGOCD_AUTH_TOKEN}" -d '{"syncOptions": ["Force=true", "Replace=true"]}' http://${ARGOCD_SERVER}/api/v1/applications/${ARGOCD_APP_NAME}/sync
        //             """
        //         }
        //     }
        // }
    }
}