pipeline {
    agent any
    environment {
        DOCKER_HUB_REPO = "rubybriggs/studybuddy"
        DOCKER_HUB_CREDENTIALS_ID = "dockerhub-token"
        IMAGE_TAG = "v${BUILD_NUMBER}"
    }
    stages {
        stage('Checkout Github') {
            steps {
                echo 'Checking out code from GitHub...'
                checkout scmGit(branches: [[name: '*/main']], extensions: [], userRemoteConfigs: [[credentialsId: 'github-token', url: 'https://github.com/rubybriggs/Study-Buddy-AI.git']])
            }
        }        
        
        stage('Build Docker Image') {
            steps {
                script {
                    echo 'Building Docker image...'
                    // Using the "def" keyword to avoid the memory leak warning you saw in logs
                    def dockerImage = docker.build("${DOCKER_HUB_REPO}:${IMAGE_TAG}")
                    
                    echo 'Pushing Docker image to DockerHub...'
                    docker.withRegistry('https://registry.hub.docker.com' , "${DOCKER_HUB_CREDENTIALS_ID}") {
                        dockerImage.push("${IMAGE_TAG}")
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
                withCredentials([usernamePassword(credentialsId: 'github-token', usernameVariable: 'GIT_USER', passwordVariable: 'GIT_PASS')]) {
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

        stage('Install CLI Tools') {
            steps {
                sh '''
                if ! command -v kubectl &> /dev/null; then
                    echo "Installing Kubectl..."
                    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
                    chmod +x kubectl
                    mv kubectl /usr/local/bin/
                fi
                
                if ! command -v argocd &> /dev/null; then
                    echo "Installing ArgoCD CLI..."
                    curl -sSL -o /usr/local/bin/argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
                    chmod +x /usr/local/bin/argocd
                fi
                '''
            }
        }

        stage('Sync App with ArgoCD') {
            steps {
                // withKubeConfig handles the 'context not found' error by setting up a temp config
                withKubeConfig([credentialsId: 'kubeconfig', serverUrl: 'https://192.168.49.2:8443']) {
                    sh '''
                    # Retrieve the password from the cluster
                    ARGO_PWD=$(kubectl get secret -n argocd argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)
                    
                    # Login to ArgoCD
                    argocd login 34.61.123.87:31704 --username admin --password "$ARGO_PWD" --insecure
                    
                    # Sync the application
                    argocd app sync study
                    '''
                }
            }
        }
    }
}