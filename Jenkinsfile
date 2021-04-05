pipeline {
  agent {
    label 'ROAST'
  }
  environment {
    def PIP_CONF = fileExists('/etc/pip.conf')
  }
  options {
    buildDiscarder(logRotator(numToKeepStr: '20'))
  }
  stages {
    stage ('Setup') {
      steps {
        slackSend (channel: '#roast-dev', color: '#FFFF00', message: "STARTED: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL})")
        sh "rm -rf ${WORKSPACE}/test-results"
        sh "docker container prune -f"
        script {
          if (PIP_CONF) {
            sh "cp /etc/pip.conf ${WORKSPACE}"
          }
        }
      }
    }
    stage('Run Linter') {
      steps {
        sh "docker run --rm -v ${WORKSPACE}:/src --name roast-pylint pylint --exit-zero --disable=all --enable=F,E,unreachable,duplicate-key,unnecessary-semicolon,global-variable-not-assigned,unused-variable,binary-op-exception,bad-format-string,anomalous-backslash-in-string,bad-open-mode *.py"
      }
    }
    stage('Run Unit Tests') {
      steps {
        sh "docker run -v ${WORKSPACE}:/src --name roast-tox tox -p"
      }
      post {
        always {
          sh "mkdir ${WORKSPACE}/test-results"
          sh "docker cp roast-tox:/app/test-results/. ${WORKSPACE}/test-results/."
          sh "docker container rm roast-tox"
          junit '**/junit-*.xml'
        }
      }
    }
  }
  post {
    success {
      slackSend (channel: '#roast-dev', color: '#00FF00', message: "SUCCESSFUL: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL})")
    }
    failure {
      slackSend (channel: '#roast-dev', color: '#FF0000', message: "FAILED: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL})")
    }
    always {
      emailext (subject: "[${JOB_NAME}] Build #${BUILD_NUMBER} - ${currentBuild.currentResult}", to: 'chinghwa@xilinx.com', body: "Check console output at ${BUILD_URL} to view the results.", recipientProviders: [developers(), requestor()])
    }
  }
}
