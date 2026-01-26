pipeline {
    agent any
    environment {
        DOCKER_HUB_REPO = "rubybriggs/studybuddy"
        DOCKER_HUB_CREDENTIALS_ID = "dockerhub-token"
        IMAGE_TAG = "v${BUILD_NUMBER}"
    }
    stages {
        // STAGE 1 (Checkout) is automatic! No need to write it.

        stage('Build Docker Image') {
            steps {
                script {
                    // This uses the Docker pipeline plugin
                    dockerImage = docker.build("${DOCKER_HUB_REPO}:${IMAGE_TAG}")
                }
            }
        }

        stage('Push Image to DockerHub') {
            steps {
                script {
                    docker.withRegistry('https://index.docker.io/v1/', "${DOCKER_HUB_CREDENTIALS_ID}") {
                        dockerImage.push("${IMAGE_TAG}")
                        dockerImage.push("latest") // Good practice to keep 'latest' updated
                    }
                }
            }
        }

        stage('Update Manifests') {
            steps {
                script {
                    // Update the YAML and push back to Git
                    withCredentials([usernamePassword(credentialsId: 'github-token', usernameVariable: 'GIT_USER', passwordVariable: 'GIT_PASS')]) {
                        sh """
                        sed -i 's|image: ${DOCKER_HUB_REPO}:.*|image: ${DOCKER_HUB_REPO}:${IMAGE_TAG}|' manifests/deployment.yaml
                        git config user.name "rubybriggs"
                        git config user.email "rubybriggs@gmail.com"
                        git add manifests/deployment.yaml
                        git commit -m "chore: update image tag to ${IMAGE_TAG} [skip ci]" || echo "No changes"
                        git push https://${GIT_USER}:${GIT_PASS}@github.com/rubybriggs/Study-Buddy-AI.git HEAD:main
                        """
                    }
                }
            }
        }

        stage('Sync ArgoCD') {
            steps {
                // Assumes kubectl and argocd are already on the Jenkins Path
                script {
                    kubeconfig(credentialsId: 'kubeconfig', serverUrl: 'https://192.168.49.2:8443') {
                        sh '''
                        PASS=$(kubectl get secret -n argocd argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)
                        argocd login 34.61.123.87:31704 --username admin --password $PASS --insecure
                        argocd app sync study
                        '''
                    }
                }
            }
        }
    }
}