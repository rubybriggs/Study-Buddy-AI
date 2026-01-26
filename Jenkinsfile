pipeline {
    agent any
    environment {
        DOCKER_HUB_REPO = "rubybriggs/studybuddy"
        IMAGE_TAG = "v${BUILD_NUMBER}"
        ARGO_SERVER = "34.61.123.87:31704"
    }
    stages {
        stage('Checkout Github') {
            steps {
                checkout scm
            }
        }

        stage('Build and Push Docker Image') {
            steps {
                script {
                    sh "docker build -t ${DOCKER_HUB_REPO}:${IMAGE_TAG} ."
                    docker.withRegistry('https://registry.hub.docker.com', 'dockerhub-token') {
                        sh "docker push ${DOCKER_HUB_REPO}:${IMAGE_TAG}"
                    }
                }
            }
        }

        stage('Update Deployment YAML') {
            steps {
                sh "sed -i 's|image: ${DOCKER_HUB_REPO}:.*|image: ${DOCKER_HUB_REPO}:${IMAGE_TAG}|' manifests/deployment.yaml"
            }
        }

        stage('Commit Updated YAML') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'github-token', passwordVariable: 'GIT_PASS', usernameVariable: 'GIT_USER')]) {
                    sh '''
                    git config user.name "rubybriggs"
                    git config user.email "rubybriggs07@gmail.com"
                    git add manifests/deployment.yaml
                    git commit -m "Update image tag to ${IMAGE_TAG}" || echo "No changes to commit"
                    git push https://${GIT_USER}:${GIT_PASS}@github.com/rubybriggs/Study-Buddy-AI.git HEAD:main
                    '''
                }
            }
        }

        stage('Sync App with ArgoCD') {
            steps {
                // Ensure 'kubeconfig' is the ID of your credential in Jenkins
                withKubeConfig([credentialsId: 'kubeconfig', serverUrl: 'https://192.168.49.2:8443']) {
                    script {
                        sh '''
                        # Ensure ArgoCD CLI is available
                        if ! command -v argocd &> /dev/null; then
                            curl -sSL -o /usr/local/bin/argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
                            chmod +x /usr/local/bin/argocd
                        fi

                        # Securely get ArgoCD password, stripping any potential bad characters
                        ENCODED_PASS=$(kubectl get secret argocd-initial-admin-secret -n argocd -o jsonpath="{.data.password}")
                        ARGO_PWD=$(echo $ENCODED_PASS | tr -d '[:space:]' | base64 -d)

                        # Login and Sync
                        argocd login ${ARGO_SERVER} --username admin --password "${ARGO_PWD}" --insecure
                        argocd app sync study --force
                        '''
                    }
                }
            }
        }
    }
}