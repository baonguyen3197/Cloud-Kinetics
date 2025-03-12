// pipeline {
//     agent any

//     environment {
//         DOCKER_IMAGE = 'index.docker.io/nhqb3197/nhqb-cloud-kinetics:latest'
//         GITHUB_CREDENTIALS_ID = 'github-cloud-kinetics'
//         DOCKER_CREDENTIALS_ID = 'dockerhub-creds'
//     }

//     stages {
//         stage("Cleanup Workspace") {
//             steps {
//                 cleanWs()
//             }
//         }

//         stage("Checkout from SCM") {
//             steps {
//                 git branch: 'main', credentialsId: "${GITHUB_CREDENTIALS_ID}", url: 'https://github.com/baonguyen3197/Cloud-Kinetics.git'
//             }
//         }

//         stage("Build Docker Image") {
//             steps {
//                 script {
//                     sh "docker build -t ${env.DOCKER_IMAGE} ."
//                 }
//             }
//         }

//         stage("Push Docker Image") {
//             steps {
//                 script {
//                     withCredentials([usernamePassword(credentialsId: "${DOCKER_CREDENTIALS_ID}")]) {
//                         // sh "docker login -u ${DOCKERHUB_USERNAME} -p ${DOCKERHUB_PASSWORD}"
//                         sh "docker push ${env.DOCKER_IMAGE}"
//                     }
//                 }
//             }
//         }
//     }
// }

pipeline {
  agent any
  stages {
    stage('Build Docker Image') {
      steps {
        script {
            docker.withRegistry('https://index.docker.io/v1/', 'dockerhub-creds') {
              def previousCommit = env.GIT_PREVIOUS_SUCCESSFUL_COMMIT ?: 'HEAD'
              def currentCommit = env.GIT_COMMIT
              def commitDetails = sh(script: "git log --pretty=format:\"%s - %an (<https://github.com/baonguyen3197/Cloud-Kinetics/commit/%h|details>)\" ${previousCommit}..${currentCommit} | nl -n ln -w1 -s'. '", returnStdout: true).trim()
              env.commitDetails = commitDetails
              def dockerImage = docker.build('nhqb3197/nhqb-cloud-kinetics', '-f Dockerfile .')
              dockerImage.push('latest')
            }
        }
      }
    }
  }
}