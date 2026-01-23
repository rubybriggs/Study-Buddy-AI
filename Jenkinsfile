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
                // This wipes the workspace to remove the corrupted deployment.yaml
                cleanWs() 
                echo 'Checking out code from GitHub...'
                checkout scmGit(branches: [[name: '*/main']], extensions: [], userRemoteConfigs: [[credentialsId: 'github-token', url: 'https://github.com/rubybriggs/Study-Buddy-AI.git']])
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
                    // Corrected to match 'rubybriggs/studybuddy' as seen in your GitHub screenshot
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
                        sh '''
                        git config user.name "rubybriggs"
                        git config user.email "rubybriggs@gmail.com"
                        git add manifests/deployment.yaml
                        git commit -m "Update image tag to ${IMAGE_TAG}" || echo "No changes to commit"
                        git push https://${GIT_USER}:${GIT_PASS}@github.com/rubybriggs/STUDY-BUDDY-AI.git HEAD:main
                        '''
                    }
                }
            }
        }
        stage('Install Kubectl & ArgoCD CLI Setup') {
            steps {
                sh '''
                echo 'installing Kubectl & ArgoCD cli...'
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
                    ARGOCD_PWD=$(kubectl get secret -n argocd argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)
                    argocd login 34.61.123.87:31704 --username admin --password ${ARGOCD_PWD} --insecure
                    rgocd app sync study
                        '''
                    }
                }
            }
        }
    }
}