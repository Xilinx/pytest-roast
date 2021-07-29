pipeline {
  agent {
    label 'ROAST'
  }
  options {
    buildDiscarder(logRotator(numToKeepStr: '20'))
  }
  stages {
    stage ('Setup') {
      steps {
        slackSend (channel: '#roast-dev', color: '#FFFF00', message: "STARTED: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL})")
        sh "rm -rf ${WORKSPACE}/test-results"
        sh "rm -rf ${WORKSPACE}/dist"
        sh "mkdir ${WORKSPACE}/test-results"
      }
    }
    stage('Run Linter') {
      steps {
        sh "docker run --rm -v ${WORKSPACE}:/src -v /etc/pip.conf:/etc/pip.conf xcoartifactory.xilinx.com/docker-images/pylint --exit-zero --disable=all --enable=F,E,unreachable,duplicate-key,unnecessary-semicolon,global-variable-not-assigned,unused-variable,binary-op-exception,bad-format-string,anomalous-backslash-in-string,bad-open-mode *.py > test-results/pylint.log"
      }
      post {
        always {
          recordIssues(tools: [pyLint(pattern: '**/pylint.log')])
        }
      }
    }
    stage('Run Unit Tests') {
      steps {
        sh "docker run --rm -v ${WORKSPACE}:/src -v ${WORKSPACE}/test-results:/app/test-results -v /etc/pip.conf:/etc/pip.conf xcoartifactory.xilinx.com/docker-images/tox -p"
      }
      post {
        always {
          junit '**/junit-*.xml'
          cobertura autoUpdateHealth: false, autoUpdateStability: false, coberturaReportFile: '**/coverage.xml', conditionalCoverageTargets: '70, 0, 0', failUnhealthy: false, failUnstable: false, lineCoverageTargets: '80, 0, 0', maxNumberOfBuilds: 0, methodCoverageTargets: '80, 0, 0', onlyStable: false, sourceEncoding: 'ASCII', zoomCoverageChart: false
        }
      }
    }
    stage('Build Package') {
      when {
        anyOf {
          branch 'master'
        }
      }
      steps {
        sh "mkdir ${WORKSPACE}/dist"
        sh "docker run --rm -v ${WORKSPACE}:/src -v ${WORKSPACE}/dist:/app/dist -v /group/siv_roast_bkup/staff/sivteam1/.pypirc:/home/sivteam1/.pypirc -v /etc/pki/tls/cert.pem:/.pyenv/versions/3.9.4/lib/python3.9/site-packages/certifi/cacert.pem -e REPO=dev-local xcoartifactory.xilinx.com/docker-images/python-setuptools"
      }
      post {
        always {
          archiveArtifacts artifacts: 'dist/*', fingerprint: true
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
      emailext (subject: '$DEFAULT_SUBJECT', to: 'chinghwa@xilinx.com', body: '$DEFAULT_CONTENT', recipientProviders: [developers(), requestor()])
    }
  }
}
