pipeline {
    agent any
    environment {
        DOCKER_HUB_REPO = "rubybriggs/studybuddy"
        DOCKER_HUB_CREDENTIALS_ID = "dockerhub-token"
        IMAGE_TAG = "v${BUILD_NUMBER}"
    }
    stages {
        stage('Cleanup & Checkout') {
            steps {
                cleanWs() 
                echo 'Checking out code from GitHub...'
                // Simplified git checkout to avoid YAML/DSL parser errors
                git branch: 'main', 
                    credentialsId: 'github-token', 
                    url: 'https://github.com/rubybriggs/Study-Buddy-AI.git'
            }
        }        
        stage('Build Docker Image') {
            steps {
                script {
                    echo 'Building Docker image...'
                    dockerImage = docker.build("${DOCKER_HUB_REPO}:${IMAGE_TAG}")
                }
            }
        }
        stage('Push Image to DockerHub') {
            steps {
                script {
                    echo 'Pushing Docker image to DockerHub...'
                    docker.withRegistry('https://registry.hub.docker.com' , "${DOCKER_HUB_CREDENTIALS_ID}") {
                        dockerImage.push("${IMAGE_TAG}")
                    }
                }
            }
        }
        stage('Update Deployment YAML with New Tag') {
            steps {
                script {
                    // Updates the image tag in your manifest file
                    sh """
                    sed -i 's|image: rubybriggs/studybuddy:.*|image: rubybriggs/studybuddy:${IMAGE_TAG}|' manifests/deployment.yaml
                    """
                }
            }
        }
    stage('Commit Updated YAML') {
            steps {
                script {
                    withCredentials([usernamePassword(credentialsId: 'github-token', usernameVariable: 'GIT_USER', passwordVariable: 'GIT_PASS')]) {
                        sh """
                        git config user.name "rubybriggs"
                        git config user.email "rubybriggs@gmail.com"
                        git add manifests/deployment.yaml
                        git commit -m "Update image tag to ${IMAGE_TAG}" || echo "No changes to commit"
                        git push https://${GIT_USER}:${GIT_PASS}@github.com/rubybriggs/Study-Buddy-AI.git HEAD:main
                        """
                    }
                }
            }
        }
        stage('Install Kubectl & ArgoCD CLI Setup') {
            steps {
                sh '''
                echo 'Installing tools...'
                curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
                chmod +x kubectl
                mv kubectl /usr/local/bin/kubectl
                curl -sSL -o /usr/local/bin/argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
                chmod +x /usr/local/bin/argocd
                '''
            }
        }
        stage('Apply Kubernetes & Sync App with ArgoCD') {
            steps {
                script {
                    withKubeConfig([credentialsId: 'kubeconfig', serverUrl: 'https://192.168.49.2:8443']) {
                        sh '''
                        kubectl config use-context minikube
                        
                        # Apply individual files to avoid concatenation errors
                        kubectl apply -f manifests/

                        ARGOCD_PWD=$(kubectl get secret -n argocd argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)
                        
                        argocd login 34.61.123.87:31704 --username admin --password ${ARGOCD_PWD} --insecure
                        argocd app sync study
                        '''
                    }
                }
            }
        }
    }
}