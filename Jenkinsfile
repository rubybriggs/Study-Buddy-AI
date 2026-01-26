pipeline {
    agent any
    environment {
        DOCKER_HUB_REPO = "rubybriggs/studybuddy"
        IMAGE_TAG = "v${BUILD_NUMBER}"
        ARGO_SERVER = "34.61.123.87:31704"
        DOCKER_REGISTRY = "https://registry.hub.docker.com"
    }
    stages {
        stage('Checkout Github') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    echo "Building Docker image: ${DOCKER_HUB_REPO}:${IMAGE_TAG}"
                    sh "docker build -t ${DOCKER_HUB_REPO}:${IMAGE_TAG} ."
                    sh "docker tag ${DOCKER_HUB_REPO}:${IMAGE_TAG} ${DOCKER_HUB_REPO}:latest"
                }
            }
        }

        stage('Push Docker Image') {
            steps {
                script {
                    // First, verify the repository exists by trying to list tags
                    echo "Verifying Docker Hub repository access..."
                    sh """
                        # Test if we can access the repository
                        if curl -s "https://hub.docker.com/v2/repositories/${DOCKER_HUB_REPO}/" | grep -q "not found"; then
                            echo "ERROR: Repository ${DOCKER_HUB_REPO} does not exist on Docker Hub!"
                            echo "Please create it at: https://hub.docker.com/repository/create"
                            exit 1
                        fi
                    """
                    
                    // Push with Docker credentials
                    docker.withRegistry("${DOCKER_REGISTRY}", 'dockerhub-token') {
                        echo "Pushing Docker image ${DOCKER_HUB_REPO}:${IMAGE_TAG}"
                        sh "docker push ${DOCKER_HUB_REPO}:${IMAGE_TAG}"
                        echo "Pushing Docker image ${DOCKER_HUB_REPO}:latest"
                        sh "docker push ${DOCKER_HUB_REPO}:latest"
                    }
                }
            }
        }

        stage('Update Deployment YAML') {
            steps {
                script {
                    echo "Updating deployment.yaml with new image tag: ${IMAGE_TAG}"
                    sh "sed -i 's|image: ${DOCKER_HUB_REPO}:.*|image: ${DOCKER_HUB_REPO}:${IMAGE_TAG}|g' manifests/deployment.yaml"
                    
                    // Verify the change
                    sh "grep 'image:' manifests/deployment.yaml"
                }
            }
        }

        stage('Commit Updated YAML') {
            steps {
                script {
                    withCredentials([usernamePassword(credentialsId: 'github-token', passwordVariable: 'GIT_PASS', usernameVariable: 'GIT_USER')]) {
                        sh '''
                        git config user.name "rubybriggs"
                        git config user.email "rubybriggs07@gmail.com"
                        
                        # Check if there are changes
                        if git diff --quiet manifests/deployment.yaml; then
                            echo "No changes to commit"
                        else
                            git add manifests/deployment.yaml
                            git commit -m "Update image tag to ${IMAGE_TAG}"
                            git push https://${GIT_USER}:${GIT_PASS}@github.com/rubybriggs/Study-Buddy-AI.git HEAD:main
                        fi
                        '''
                    }
                }
            }
        }

        stage('Sync App with ArgoCD') {
            steps {
                withKubeConfig([credentialsId: 'kubeconfig', serverUrl: 'https://192.168.49.2:8443']) {
                    script {
                        echo "Syncing application with ArgoCD..."
                        sh '''
                        # Install ArgoCD CLI if not present
                        if ! command -v argocd &> /dev/null; then
                            echo "Installing ArgoCD CLI..."
                            curl -sSL -o argocd-linux-amd64 https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
                            chmod +x argocd-linux-amd64
                            sudo mv argocd-linux-amd64 /usr/local/bin/argocd
                        fi

                        # Get ArgoCD admin password
                        ARGO_PWD=$(kubectl get secret argocd-initial-admin-secret -n argocd -o jsonpath='{.data.password}' | base64 -d)
                        
                        # Login to ArgoCD
                        argocd login ${ARGO_SERVER} --username admin --password "${ARGO_PWD}" --insecure --grpc-web
                        
                        # Sync the application
                        argocd app sync study --force
                        
                        # Wait for sync to complete
                        argocd app wait study --health --timeout 300
                        '''
                    }
                }
            }
        }
    }
    
    post {
        failure {
            echo "Pipeline failed! Check the following:"
            echo "1. Does the Docker Hub repository 'rubybriggs/studybuddy' exist?"
            echo "2. Are Docker Hub credentials correct in Jenkins?"
            echo "3. Check Docker Hub URL: https://hub.docker.com/r/rubybriggs/studybuddy"
        }
        success {
            echo "Pipeline completed successfully!"
            echo "New image: ${DOCKER_HUB_REPO}:${IMAGE_TAG}"
            echo "ArgoCD sync initiated for application 'study'"
        }
    }
}