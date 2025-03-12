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

            def imageName = "nhqb3197/nhqb-cloud-kinetics:${env.BUILD_NUMBER}"
            def dockerImage = docker.build(imageName, '-f Dockerfile .')
            dockerImage.push()
            // dockerImage.push('latest')
          }
        }
      }
    }
  }
}

// pipeline {
//   agent any
//   stages {
//     stage('Build Docker Image') {
//       steps {
//         script {
//             docker.withRegistry('https://index.docker.io/v1/', 'dockerhub-creds') {
//               def previousCommit = env.GIT_PREVIOUS_SUCCESSFUL_COMMIT ?: 'HEAD'
//               def currentCommit = env.GIT_COMMIT
//               def commitDetails = sh(script: "git log --pretty=format:\"%s - %an (<https://github.com/baonguyen3197/Cloud-Kinetics/commit/%h|details>)\" ${previousCommit}..${currentCommit} | nl -n ln -w1 -s'. '", returnStdout: true).trim()
//               env.commitDetails = commitDetails
//               def dockerImage = docker.build('nhqb3197/nhqb-cloud-kinetics', '-f Dockerfile .')
//               dockerImage.push('latest')
//             }
//         }
//       }
//     }
//   }
// }