pipeline {
    agent {
        kubernetes {
            yamlFile 'kaniko-builder.yaml'
        }
    }

    environment {
        DOCKER_IMAGE = 'index.docker.io/nhqb3197/nhqb-cloud-kinetics:latest'
        GITHUB_CREDENTIALS_ID = 'github-cloud-kinetics'
        DOCKER_CREDENTIALS_ID = 'dockerhub-creds'
        // ARGOCD_SERVER = '10.10.100.90:32007'
        // ARGOCD_APP_NAME = 'app-web'
        // ARGOCD_AUTH_TOKEN = credentials('argocd-cred')
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

        stage('Build & Push with Kaniko') {
            steps {
                container(name: 'kaniko', shell: '/busybox/sh') {
                    sh '''#!/busybox/sh
                    /kaniko/executor --dockerfile `pwd`/Dockerfile --context `pwd` --destination=${DOCKER_IMAGE}
                    '''
                }
            }
        }
        
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